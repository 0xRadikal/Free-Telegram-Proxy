"""Exercise the actual CLI and independent byte counts, including CI regressions."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "check_size.py"


def check(root, *args, absolute=False, **limits):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("SIZE_BUDGET_") and k != "GITHUB_STEP_SUMMARY"}
    env.update({k: str(v) for k, v in limits.items()})
    return subprocess.run([sys.executable, str(SCRIPT), str(root) if absolute else root.name,
                           *map(str, args)], cwd=root.parent,
                          env=env, capture_output=True, text=True)


def test_observed_production_volume_has_headroom(tmp_path):
    # Run 42522875765: validated outputs failed by just 2,749 bytes.
    for i, size in enumerate([839410] * 4 + [839413]):
        (tmp_path / f"tier-{i}.txt").write_bytes(b"x" * size)
    assert sum(p.stat().st_size for p in tmp_path.iterdir()) == 4197053
    result = check(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "4197053" in result.stdout


@pytest.mark.parametrize("size,code", [(99, 0), (100, 0), (101, 1)])
def test_total_boundary(tmp_path, size, code):
    (tmp_path / "a.txt").write_bytes(b"a" * (size // 2))
    (tmp_path / "b.txt").write_bytes(b"b" * (size - size // 2))
    result = check(tmp_path, SIZE_BUDGET_RAW=100, SIZE_BUDGET_FILE=1000)
    assert result.returncode == code, result.stdout + result.stderr
    if code:
        assert "outputs 101 B exceed budget 100 B" in result.stdout


@pytest.mark.parametrize("size,code", [(99, 0), (100, 0), (101, 1)])
def test_single_file_boundary(tmp_path, size, code):
    (tmp_path / "state.json").write_bytes(b"a" * size)
    result = check(tmp_path, SIZE_BUDGET_RAW=1000, SIZE_BUDGET_FILE=100)
    assert result.returncode == code, result.stdout + result.stderr
    if code:
        assert "state.json" in result.stdout and "per-file" in result.stdout


def test_near_limit_warns_before_blocking_publication(tmp_path):
    (tmp_path / "state.json").write_bytes(b"a" * 80)
    result = check(tmp_path, SIZE_BUDGET_RAW=100, SIZE_BUDGET_FILE=100)
    assert result.returncode == 0
    assert "::warning::outputs" in result.stdout
    assert "::warning::state.json" in result.stdout


@pytest.mark.parametrize("missing", [False, True])
def test_missing_or_empty_outputs_fail_closed(tmp_path, missing):
    root = tmp_path / "absent" if missing else tmp_path
    assert check(root).returncode != 0


def test_hidden_ancestor_does_not_hide_outputs(tmp_path):
    root = tmp_path / ".runner" / "out"
    root.mkdir(parents=True)
    (root / "large.txt").write_bytes(b"x" * 101)
    result = check(root, absolute=True, SIZE_BUDGET_RAW=100, SIZE_BUDGET_FILE=1000)
    assert result.returncode == 1
    assert "101 B" in result.stdout


def test_report_and_summary_survive_size_failure(tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    (root / "state.json").write_bytes(b"x" * 101)
    report, summary = tmp_path / "size.json", tmp_path / "summary.md"
    summary.write_text("Earlier step\n")
    result = check(root, "--report", report, SIZE_BUDGET_RAW=1000,
                   SIZE_BUDGET_FILE=100, GITHUB_STEP_SUMMARY=summary)
    assert result.returncode == 1
    data = json.loads(report.read_text())
    assert data["total_bytes"] == 101
    assert data["files"][0]["path"] == "state.json"
    assert data["files"][0]["bytes"] == 101
    assert data["errors"]
    assert summary.read_text().startswith("Earlier step\n")
    assert "state.json" in summary.read_text()


@pytest.mark.parametrize("value", ["zero", "0", "-1"])
def test_invalid_limit_fails_closed(tmp_path, value):
    (tmp_path / "a.txt").write_text("hello")
    assert check(tmp_path, SIZE_BUDGET_RAW=value).returncode != 0
