"""Execute update.yml's own Bash for the queued-run output sync and the
DB-IP month cache, so the logic is tested exactly as the runner sees it.

Sync: real git — a bare `origin`, a workspace built with the same fetch and
checkout commands actions/checkout runs (fetch-depth 2), and a force-pushed
newer publish, as the rolling-squash publisher does.

DB-IP: real gzip/gunzip/stat/mktemp; only `curl` is replaced by a shim that
serves files from a local directory (404 → curl's -f exit code 22) and logs
every URL, so a test can assert what would have been downloaded.
"""
import gzip
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PINNED_CACHE = "55cc8345863c7cc4c66a329aec7e433d2d1c52a9"  # actions/cache v6.1.0


def _workflow() -> dict:
    return yaml.safe_load((ROOT / ".github/workflows/update.yml").read_text())


def _steps() -> list:
    return _workflow()["jobs"]["update"]["steps"]


def _step(step_id: str) -> dict:
    return next(s for s in _steps() if s.get("id") == step_id)


def _index(pred) -> int:
    return next(i for i, s in enumerate(_steps()) if pred(s))


def _env() -> dict:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
               GIT_TERMINAL_PROMPT="0")
    for k in ("GITHUB_OUTPUT", "GH_TOKEN", "GITHUB_TOKEN", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    return env


def _bash(script: str, cwd: Path, env: dict) -> tuple[int, str]:
    """Run a step the way Actions does: `bash --noprofile --norc -eo pipefail`."""
    p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
                       cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout + p.stderr


# ───────────────────────────── queued-run output sync ─────────────────────────────

def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, env=_env(), capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"git {args}: {p.stderr}"
    return p.stdout.strip()


def _write(root: Path, files: dict) -> None:
    for rel, body in files.items():
        full = root / rel
        if body is None:
            shutil.rmtree(full) if full.is_dir() else full.unlink()
            continue
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(body, encoding="utf-8")


def _read(root: Path, rel: str):
    p = root / rel
    return p.read_text(encoding="utf-8") if p.exists() else None


SOURCE = {"tgproxy/__main__.py": "print(1)\n", "templates/README.md": "template v1\n"}
O1 = {"state.json": '{"runs": 1}', "index.json": '{"updated_unix": 1}\n', "verified/tg.txt": "old\n",
      "countries/FI.txt": "fi\n", "top100.txt": "old top\n", "README.md": "readme 1\n"}
NEWER = {"state.json": '{"runs": 2}', "index.json": '{"updated_unix": 2}\n', "verified/tg.txt": "new\n",
         "countries/FI.txt": None, "countries/DE.txt": "de\n", "top100.txt": "new top\n",
         "README.md": "readme 2\n"}


def _fixture(td: Path, *, newer: dict, newer_source: dict | None = None) -> tuple:
    """origin: S (source) ← O1 ([auto-output]). The workspace is checked out at
    O1 the way actions/checkout does it; then origin's main is force-replaced
    by a newer publish: O2 on S, or — with `newer_source` — S2 ← O3.
    Returns (workspace, o1, tip)."""
    author, origin, ws = td / "author", td / "origin.git", td / "ws"
    author.mkdir()
    _git(author, "init", "-q", "-b", "main")
    _write(author, SOURCE)
    _git(author, "add", "-A")
    _git(author, "commit", "-q", "-m", "source")
    _write(author, O1)
    _git(author, "add", "-A")
    _git(author, "commit", "-q", "-m", "chore: update proxies [auto-output]")
    o1 = _git(author, "rev-parse", "HEAD")
    _git(td, "init", "-q", "--bare", str(origin))
    _git(author, "push", "-q", str(origin), "HEAD:refs/heads/main")
    # actions/checkout v7 with fetch-depth: 2
    ws.mkdir()
    _git(ws, "init", "-q")
    _git(ws, "remote", "add", "origin", origin.as_uri())
    _git(ws, "-c", "protocol.version=2", "fetch", "-q", "--no-tags", "--prune", "--no-recurse-submodules",
         "--depth=2", "origin", f"+{o1}:refs/remotes/origin/main")
    _git(ws, "checkout", "-q", "--force", "-B", "main", "refs/remotes/origin/main")
    # While this run waits in the queue, another run publishes (rolling squash).
    _git(author, "reset", "-q", "--hard", "HEAD~1")
    if newer_source:
        _write(author, newer_source)
        _git(author, "add", "-A")
        _git(author, "commit", "-q", "-m", "owner change")
    _write(author, O1)
    _write(author, newer)
    _git(author, "add", "-A")
    _git(author, "commit", "-q", "-m", "chore: update proxies [auto-output]")
    tip = _git(author, "rev-parse", "HEAD")
    _git(author, "push", "-q", "--force", str(origin), "HEAD:refs/heads/main")
    return ws, o1, tip


def _sync(ws: Path) -> tuple[int, str]:
    env = _env()
    env["OUTPUT_PATHS"] = _workflow()["env"]["OUTPUT_PATHS"]
    return _bash(_step("sync_outputs")["run"], ws, env)


def test_sync_runs_after_the_gate_and_before_anything_reads_outputs():
    steps = _steps()
    gate = _index(lambda s: s.get("id") == "gate")
    sync = _index(lambda s: s.get("id") == "sync_outputs")
    collect = _index(lambda s: s.get("id") == "collect")
    assert gate < sync < collect
    s = steps[sync]
    assert s["if"] == "steps.gate.outputs.run == 'true'"
    # A half-applied reset must fail the job, so nothing is published from it.
    assert "continue-on-error" not in s
    assert 0 < s["timeout-minutes"] <= _workflow()["jobs"]["update"]["timeout-minutes"]
    assert 'git reset -q --hard "$TIP"' in s["run"]


def test_sync_and_publish_share_one_output_list():
    """The sync reads the workflow's OUTPUT_PATHS (no private copy), and every
    one of those paths is an output for the publish step's is_output()."""
    sync = _step("sync_outputs")["run"]
    assert "$OUTPUT_PATHS" in sync and "OUTPUT_PATHS=" not in sync
    pub = next(s for s in _steps() if s.get("name") == "Publish (rolling squash)")["run"]
    m = re.search(r"^\s*(is_output\(\) \{.*\})\s*$", pub, re.M)
    assert m, "is_output() not found in the publish step"
    paths = _workflow()["env"]["OUTPUT_PATHS"].split()
    probes = [p if "." in p else f"{p}/x.txt" for p in paths]
    script = m.group(1) + '\nfor p in "$@"; do is_output "$p" && echo "OUT $p" || echo "SRC $p"; done\n'
    out = subprocess.run(["bash", "-c", script, "bash", *probes], capture_output=True, text=True,
                         env=dict(os.environ, OUTPUT_PATHS=" ".join(paths))).stdout.split("\n")
    assert [x for x in out if x] == [f"OUT {p}" for p in probes]


def test_publish_names_the_source_files_that_changed():
    """The publish step's own anchor check, run on a sample diff: REG must list
    the changed source files (is_output() used to overwrite the caller's $p)."""
    pub = next(s for s in _steps() if s.get("name") == "Publish (rolling squash)")["run"]
    func = re.search(r"^\s*(is_output\(\) \{.*\})\s*$", pub, re.M).group(1)
    loop = re.search(r"^\s*(while IFS= read -r p; do .*)$", pub, re.M).group(1)
    diff = '"$(git diff --name-only "$ANCHOR" "$TIP")"'
    assert loop.endswith(diff)
    sample = "tgproxy/probe.py\nverified/tg.txt\ntemplates/README.md\nREADME.md\ncountries/DE.txt\ntools/check_size.py\n"
    script = (f'REG=""\n{func}\n' + loop.replace(diff, '"$(printf %s "$SAMPLE")"') + '\necho "REG=[$REG]"\n')
    env = dict(os.environ, OUTPUT_PATHS=_workflow()["env"]["OUTPUT_PATHS"], SAMPLE=sample)
    rc, out = _bash(script, ROOT, env)
    assert rc == 0, out
    assert "REG=[ tgproxy/probe.py templates/README.md tools/check_size.py]" in out, out


def test_sync_brings_a_queued_checkout_to_the_newest_publish(tmp_path):
    ws, o1, tip = _fixture(tmp_path, newer=NEWER)
    assert _read(ws, "state.json") == '{"runs": 1}'
    rc, out = _sync(ws)
    assert rc == 0, out
    assert "outputs synced" in out and "source identical" in out, out
    assert _git(ws, "rev-parse", "HEAD^{tree}") == _git(ws, "rev-parse", f"{tip}^{{tree}}")
    assert _git(ws, "status", "--porcelain") == ""
    assert _read(ws, "state.json") == '{"runs": 2}', "per-proxy history must never go back a run"
    assert _read(ws, "verified/tg.txt") == "new\n"
    assert _read(ws, "countries/FI.txt") is None, "a file the newest publish dropped must not survive"
    assert _read(ws, "countries/DE.txt") == "de\n"
    assert _read(ws, "tgproxy/__main__.py") == "print(1)\n"


@pytest.mark.parametrize("change", [{"tgproxy/__main__.py": "print(2)\n"},
                                    # README.md is an output; templates/README.md is source.
                                    {"templates/README.md": "template v2\n"},
                                    {"tgproxy/new_module.py": "x = 1\n"}])
def test_sync_keeps_the_checkout_when_the_source_changed(tmp_path, change):
    ws, o1, tip = _fixture(tmp_path, newer=NEWER, newer_source=change)
    rc, out = _sync(ws)
    assert rc == 0, out
    assert "::notice title=Output sync skipped::source changed" in out and next(iter(change)) in out, out
    assert _git(ws, "rev-parse", "HEAD") == o1
    assert _git(ws, "status", "--porcelain") == ""
    assert _read(ws, "state.json") == '{"runs": 1}', "outputs must keep matching this run's code"


def test_sync_is_a_no_op_when_the_run_was_not_queued(tmp_path):
    ws, o1, tip = _fixture(tmp_path, newer=NEWER)
    _git(ws, "fetch", "-q", "--depth=2", "origin", f"+{tip}:refs/remotes/origin/main")
    _git(ws, "checkout", "-q", "--force", "-B", "main", "refs/remotes/origin/main")
    rc, out = _sync(ws)
    assert rc == 0 and "nothing to sync" in out, out
    assert _git(ws, "rev-parse", "HEAD") == tip


def test_sync_fails_open_when_the_tip_cannot_be_fetched(tmp_path):
    ws, o1, tip = _fixture(tmp_path, newer=NEWER)
    _git(ws, "remote", "set-url", "origin", (tmp_path / "missing.git").as_uri())
    rc, out = _sync(ws)
    assert rc == 0, out
    assert "::warning title=Output sync skipped::could not fetch main" in out, out
    assert _git(ws, "rev-parse", "HEAD") == o1
    assert _read(ws, "state.json") == '{"runs": 1}'


def test_sync_fails_the_job_when_the_reset_fails(tmp_path):
    ws, o1, tip = _fixture(tmp_path, newer=NEWER)
    (ws / ".git" / "index.lock").touch()
    rc, out = _sync(ws)
    assert rc != 0, out
    assert "outputs synced" not in out


# ───────────────────────────────── DB-IP month cache ─────────────────────────────────

CURL_SHIM = """#!/bin/bash
# curl stand-in: serve $DBIP_FIXTURES/<basename of URL>, else fail like `curl -f` on 404.
out=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in -o) out="$2"; shift 2;; --retry|--max-time) shift 2;; -*) shift;; *) url="$1"; shift;; esac
done
echo "$url" >> "$DBIP_LOG"
src="$DBIP_FIXTURES/${url##*/}"
[ -f "$src" ] || exit 22
cp "$src" "$out"
"""


def _db(month: str, kind: str, size: int = 1_100_000) -> bytes:
    """A stand-in .mmdb whose first line says which month/kind it is."""
    head = f"{kind} {month}\n".encode()
    return head + b"\0" * (size - len(head))


class DBIP:
    """Workspace + fake DB-IP server for the download step."""

    def __init__(self, tmp: Path):
        self.ws = tmp / "ws"
        self.srv = tmp / "srv"
        self.bin = tmp / "bin"
        self.log = tmp / "curl.log"
        self.out = tmp / "github_output"
        for d in (self.ws, self.srv, self.bin):
            d.mkdir()
        (self.bin / "curl").write_text(CURL_SHIM)
        (self.bin / "curl").chmod(0o755)
        self.log.write_text("")
        self.out.write_text("")

    def publish(self, month: str, kinds=("country", "asn"), size: int = 1_100_000):
        for k in kinds:
            (self.srv / f"dbip-{k}-lite-{month}.mmdb.gz").write_bytes(gzip.compress(_db(month, k, size)))

    def restore(self, month: str, kinds=("country", "asn")):
        """What actions/cache/restore leaves in .cache for an entry of `month`."""
        (self.ws / ".cache").mkdir(exist_ok=True)
        for k in kinds:
            (self.ws / ".cache" / f"dbip-{k}-lite.mmdb").write_bytes(_db(month, k))

    def run(self, ym: str, cache_hit: str = "false", matched: str = "") -> tuple[int, str]:
        env = dict(_env(), PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", DBIP_FIXTURES=str(self.srv),
                   DBIP_LOG=str(self.log), GITHUB_OUTPUT=str(self.out), YM=ym, CACHE_HIT=cache_hit,
                   MATCHED=matched)
        return _bash(_step("dbip")["run"], self.ws, env)

    def month(self, kind: str):
        p = self.ws / ".cache" / f"dbip-{kind}-lite.mmdb"
        return p.read_bytes().split(b"\n", 1)[0].decode().split()[1] if p.exists() else None

    def requested(self) -> list[str]:
        return [u.rsplit("/", 1)[1] for u in self.log.read_text().split()]

    def cacheable(self) -> str:
        found = re.findall(r"^cacheable=(\w+)$", self.out.read_text(), re.M)
        assert len(found) == 1, self.out.read_text()
        return found[0]


def test_dbip_first_run_of_a_month_before_publication_is_not_cached(tmp_path):
    """The 2026-11-01 00:09 UTC case: November not published yet, nothing
    restored. The run may use October, but must not label it November."""
    d = DBIP(tmp_path)
    d.publish("2026-10")
    rc, out = d.run("2026-11")
    assert rc == 0, out
    assert d.month("country") == d.month("asn") == "2026-10"
    assert d.requested() == ["dbip-country-lite-2026-11.mmdb.gz", "dbip-country-lite-2026-10.mmdb.gz",
                             "dbip-asn-lite-2026-11.mmdb.gz", "dbip-asn-lite-2026-10.mmdb.gz"]
    assert d.cacheable() == "false"
    assert "not available (not published yet?) — using 2026-10" in out


def test_dbip_current_month_is_downloaded_and_cacheable(tmp_path):
    d = DBIP(tmp_path)
    d.publish("2026-10")
    d.publish("2026-11")
    rc, out = d.run("2026-11")
    assert rc == 0, out
    assert d.month("country") == d.month("asn") == "2026-11"
    assert d.requested() == ["dbip-country-lite-2026-11.mmdb.gz", "dbip-asn-lite-2026-11.mmdb.gz"]
    assert d.cacheable() == "true"


def test_dbip_exact_cache_hit_downloads_nothing(tmp_path):
    d = DBIP(tmp_path)
    d.publish("2026-11")
    d.restore("2026-11")
    rc, out = d.run("2026-11", cache_hit="true", matched="dbip-v2-2026-11")
    assert rc == 0, out
    assert d.requested() == []
    assert d.month("country") == d.month("asn") == "2026-11"


def test_dbip_restored_older_month_is_kept_without_redownloading_it(tmp_path):
    """Hours into the 1st: last month's entry restored by restore-keys. Only
    this month is asked for (404), last month is NOT downloaded again, and
    nothing is saved under this month's key."""
    d = DBIP(tmp_path)
    d.publish("2026-10")
    d.restore("2026-10")
    rc, out = d.run("2026-11", matched="dbip-v2-2026-10")
    assert rc == 0, out
    assert d.requested() == ["dbip-country-lite-2026-11.mmdb.gz", "dbip-asn-lite-2026-11.mmdb.gz"]
    assert d.month("country") == d.month("asn") == "2026-10"
    assert d.cacheable() == "false"
    assert "not available (not published yet?) — using the cached copy (dbip-v2-2026-10)" in out


def test_dbip_restored_older_month_is_replaced_once_the_new_month_exists(tmp_path):
    d = DBIP(tmp_path)
    d.publish("2026-10")
    d.publish("2026-11")
    d.restore("2026-10")
    rc, out = d.run("2026-11", matched="dbip-v2-2026-10")
    assert rc == 0, out
    assert d.month("country") == d.month("asn") == "2026-11"
    assert d.cacheable() == "true"


@pytest.mark.parametrize("ym,prev", [("2026-03", "2026-02"), ("2027-01", "2026-12"), ("2026-12", "2026-11")])
def test_dbip_fallback_is_the_calendar_previous_month(tmp_path, ym, prev):
    """`date -d 'last month'` on the 31st returns the current month; the
    fallback must not depend on today's date at all."""
    d = DBIP(tmp_path)
    d.publish(prev)
    rc, out = d.run(ym)
    assert rc == 0, out
    assert d.requested() == [f"dbip-country-lite-{ym}.mmdb.gz", f"dbip-country-lite-{prev}.mmdb.gz",
                             f"dbip-asn-lite-{ym}.mmdb.gz", f"dbip-asn-lite-{prev}.mmdb.gz"]
    assert d.month("country") == prev


def test_dbip_half_current_month_is_not_cacheable(tmp_path):
    d = DBIP(tmp_path)
    d.publish("2026-10")
    d.publish("2026-11", kinds=("country",))
    rc, out = d.run("2026-11")
    assert rc == 0, out
    assert (d.month("country"), d.month("asn")) == ("2026-11", "2026-10")
    assert d.cacheable() == "false"


def test_dbip_truncated_download_is_rejected(tmp_path):
    d = DBIP(tmp_path)
    d.publish("2026-11", size=50_000)
    d.publish("2026-10")
    rc, out = d.run("2026-11")
    assert rc == 0, out
    assert d.month("country") == d.month("asn") == "2026-10"
    assert d.cacheable() == "false"
    assert not list((d.ws / ".cache").glob("*.tmp"))


def test_dbip_leaves_no_partial_files_behind(tmp_path):
    """Both months truncated: nothing half-written may stay in .cache (it is
    the cached directory) or in the temp dir."""
    d = DBIP(tmp_path)
    d.publish("2026-11", size=50_000)
    d.publish("2026-10", size=50_000)
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    env_tmp = os.environ.get("TMPDIR")
    os.environ["TMPDIR"] = str(tmpdir)
    try:
        rc, out = d.run("2026-11")
    finally:
        os.environ.pop("TMPDIR") if env_tmp is None else os.environ.__setitem__("TMPDIR", env_tmp)
    assert rc == 0, out
    assert sorted(p.name for p in (d.ws / ".cache").iterdir()) == []
    assert list(tmpdir.iterdir()) == []
    assert d.cacheable() == "false"


def test_dbip_nothing_available_warns_and_still_succeeds(tmp_path):
    d = DBIP(tmp_path)
    rc, out = d.run("2026-11")
    assert rc == 0, out
    assert out.count("::warning::DB-IP") == 2
    assert d.month("country") is None and d.cacheable() == "false"


def test_dbip_cache_steps_are_wired_so_a_month_key_holds_only_that_month():
    steps = _steps()
    uses = [s.get("uses", "") for s in steps]
    assert not any(u.startswith("actions/cache@") for u in uses), \
        "the combined action would save whatever is in .cache under this month's key"
    restore = _step("geocache")
    save = next(s for s in steps if s.get("uses", "").startswith("actions/cache/save@"))
    key = "dbip-v2-${{ steps.geokey.outputs.ym }}"
    assert restore["uses"] == f"actions/cache/restore@{PINNED_CACHE}"
    assert save["uses"] == f"actions/cache/save@{PINNED_CACHE}"
    assert restore["with"]["key"] == save["with"]["key"] == key
    assert restore["with"]["path"] == save["with"]["path"] == ".cache"
    prefix = restore["with"]["restore-keys"].strip()
    assert key.startswith(prefix) and not "dbip-2026-11".startswith(prefix), \
        "the mislabelled pre-fix entry must never be restored"
    assert "steps.dbip.outputs.cacheable == 'true'" in save["if"]
    assert "steps.geocache.outputs.cache-hit != 'true'" in save["if"]
    assert save["continue-on-error"] is True, "publishing must not depend on the cache service"
    dbip = _step("dbip")
    assert dbip["env"]["YM"] == "${{ steps.geokey.outputs.ym }}", "download and key must agree on the month"
    assert "https://download.db-ip.com/free/dbip-$kind-lite-$ym.mmdb.gz" in dbip["run"]
    order = [_index(lambda s: s.get("id") == "geokey"), _index(lambda s: s.get("id") == "geocache"),
             _index(lambda s: s.get("id") == "dbip"), steps.index(save), _index(lambda s: s.get("id") == "collect")]
    assert order == sorted(order), order
