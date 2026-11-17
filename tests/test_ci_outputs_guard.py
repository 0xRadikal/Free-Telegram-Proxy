"""Execute ci.yml's `outputs-guard` Bash against real git histories shaped like
this repository's: source commits + one force-replaced [auto-output] commit,
and a PR branch the way Dependabot creates it (from the tip of main)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
UPDATE_YML = (ROOT / ".github/workflows/update.yml").read_text()


def _job() -> dict:
    return yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]["outputs-guard"]


def _env() -> dict:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid", GIT_TERMINAL_PROMPT="0")
    for k in ("GITHUB_OUTPUT", "GH_TOKEN", "GITHUB_TOKEN", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    return env


def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, env=_env(), capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"git {args}: {p.stderr}"
    return p.stdout.strip()


def _commit(repo: Path, files: dict, msg: str) -> str:
    for rel, body in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


OUTPUTS_1 = {"state.json": '{"runs": 1}', "verified/tg.txt": "old\n", "README.md": "readme 1\n",
             "countries/FI.txt": "fi\n", "index.json": "{}\n"}
OUTPUTS_2 = {"state.json": '{"runs": 2}', "verified/tg.txt": "new\n", "README.md": "readme 2\n",
             "countries/FI.txt": "fi 2\n", "index.json": '{"n": 2}\n'}


def _repo(td: Path) -> tuple:
    """origin main: S (source) ← O1 [auto-output]. Returns (author, origin, s, o1)."""
    author, origin = td / "author", td / "origin.git"
    author.mkdir()
    _git(author, "init", "-q", "-b", "main")
    s = _commit(author, {".github/workflows/update.yml": UPDATE_YML, "requirements-dev.txt": "tdjson==1.8.69\n",
                         "templates/README.md": "template\n", "tgproxy/x.py": "x = 1\n"}, "source")
    o1 = _commit(author, OUTPUTS_1, "chore: update proxies [auto-output]")
    _git(td, "init", "-q", "--bare", str(origin))
    _git(author, "push", "-q", str(origin), "HEAD:refs/heads/main")
    return author, origin, s, o1


def _branch(author: Path, origin: Path, base: str, name: str, files: dict) -> str:
    _git(author, "checkout", "-q", "-B", name, base)
    head = _commit(author, files, f"change on {name}")
    _git(author, "push", "-q", "--force", str(origin), f"HEAD:refs/heads/{name}")
    _git(author, "checkout", "-q", "main")
    return head


def _publish(author: Path, origin: Path, s: str) -> None:
    """The publisher replaces the output commit (rolling squash, force-push)."""
    _git(author, "checkout", "-q", "main")
    _git(author, "reset", "-q", "--hard", s)
    _commit(author, OUTPUTS_2, "chore: update proxies [auto-output]")
    _git(author, "push", "-q", "--force", str(origin), "HEAD:refs/heads/main")


def _guard(td: Path, origin: Path, head: str) -> tuple[int, str]:
    """actions/checkout with fetch-depth 0 (all branches), then the step."""
    ws = td / "ws"
    _git(td, "clone", "-q", "--no-checkout", origin.as_uri(), str(ws))
    _git(ws, "checkout", "-q", "--detach", head)
    script = next(s for s in _job()["steps"] if s.get("name") == "No generated output in this PR")["run"]
    env = dict(_env(), BASE_REF="main", HEAD_SHA=head)
    p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
                       cwd=ws, env=env, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


def test_dependabot_style_branch_with_a_replaced_output_commit_fails(tmp_path):
    """#37: branched from the output commit of its day, which was replaced since."""
    author, origin, s, o1 = _repo(tmp_path)
    head = _branch(author, origin, o1, "dependabot/pip/tdjson", {"requirements-dev.txt": "tdjson==1.8.70\n"})
    _publish(author, origin, s)
    rc, out = _guard(tmp_path, origin, head)
    assert rc == 1, out
    assert "::error title=Generated output in this PR::5 generated file(s)" in out, out
    for f in OUTPUTS_1:
        assert f in out, (f, out)
    assert "requirements-dev.txt" not in out.split("Generated files changed by this PR:")[1]


def test_source_only_branch_passes(tmp_path):
    """#36: the same one-line change, branched from the newest source commit."""
    author, origin, s, o1 = _repo(tmp_path)
    head = _branch(author, origin, s, "deps/tdjson", {"requirements-dev.txt": "tdjson==1.8.70\n"})
    _publish(author, origin, s)
    rc, out = _guard(tmp_path, origin, head)
    assert rc == 0, out
    assert "✅ no generated output in this PR" in out


def test_branch_from_the_current_tip_passes(tmp_path):
    """Right after `@dependabot rebase` the base IS the live output commit:
    the diff is the source change only, so merging at that moment is safe."""
    author, origin, s, o1 = _repo(tmp_path)
    head = _branch(author, origin, o1, "dependabot/pip/tdjson", {"requirements-dev.txt": "tdjson==1.8.70\n"})
    rc, out = _guard(tmp_path, origin, head)
    assert rc == 0, out


@pytest.mark.parametrize("path,fails", [("README.md", True), ("templates/README.md", False),
                                        ("countries/DE.txt", True), ("tgproxy/x.py", False),
                                        ("docs/all.md", False), ("allowlist.txt", False)])
def test_only_generated_paths_are_rejected(tmp_path, path, fails):
    author, origin, s, o1 = _repo(tmp_path)
    head = _branch(author, origin, s, "edit", {path: "edited\n"})
    rc, out = _guard(tmp_path, origin, head)
    assert rc == (1 if fails else 0), out
    if fails:
        assert path in out


def test_guard_fails_closed_with_a_clear_error_if_the_list_disappears(tmp_path, monkeypatch):
    """A renamed/moved OUTPUT_PATHS must not silently check nothing."""
    monkeypatch.setattr(sys.modules[__name__], "UPDATE_YML", UPDATE_YML.replace("  OUTPUT_PATHS:", "  OUTPUTS:"))
    author, origin, s, o1 = _repo(tmp_path)
    head = _branch(author, origin, s, "deps/tdjson", {"requirements-dev.txt": "tdjson==1.8.70\n"})
    rc, out = _guard(tmp_path, origin, head)
    assert rc == 1 and "::error::OUTPUT_PATHS not found in .github/workflows/update.yml" in out, out


def test_guard_reads_the_publishers_own_output_list():
    wf = yaml.safe_load(UPDATE_YML)
    script = next(s for s in _job()["steps"] if s.get("name") == "No generated output in this PR")["run"]
    line = next(x for x in script.splitlines() if x.strip().startswith("OUTPUT_PATHS=$(sed"))
    p = subprocess.run(["bash", "-c", line + '\nprintf %s "$OUTPUT_PATHS"'], cwd=ROOT, capture_output=True, text=True)
    assert p.stdout == wf["env"]["OUTPUT_PATHS"]


def test_guard_runs_only_on_pull_requests_with_full_history():
    job = _job()
    assert job["if"] == "github.event_name == 'pull_request'"
    checkout = job["steps"][0]
    assert checkout["uses"].startswith("actions/checkout@") and checkout["with"]["fetch-depth"] == 0
    step = next(s for s in job["steps"] if s.get("name") == "No generated output in this PR")
    assert step["env"] == {"BASE_REF": "${{ github.base_ref }}",
                           "HEAD_SHA": "${{ github.event.pull_request.head.sha }}"}
