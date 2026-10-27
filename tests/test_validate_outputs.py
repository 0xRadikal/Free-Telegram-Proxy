"""The publish gate must reject what it claims to reject (negative controls)."""
import subprocess
import sys
from pathlib import Path

from test_publish import rec, result

from tgproxy.publish import write_outputs

TOOL = Path(__file__).resolve().parent.parent / "tools" / "validate_outputs.py"


def _run(d):
    return subprocess.run([sys.executable, str(TOOL), str(d)], capture_output=True, text=True)


def _good(tmp_path):
    write_outputs(result([rec("a.example", "1.1.1.1"), rec("b.example", "8.8.8.8")]), tmp_path, runner={})
    return tmp_path


def test_good_outputs_pass(tmp_path):
    assert _run(_good(tmp_path)).returncode == 0


import json  # noqa: E402

import pytest  # noqa: E402


@pytest.mark.parametrize("f", ["top100.txt", "top50.txt"])
def test_corrupt_top_line_rejected(tmp_path, f):
    d = _good(tmp_path)
    with open(d / f, "a") as fh:
        fh.write("tg://proxy?server=bad&port=0&secret=zz\n")
    r = _run(d)
    assert r.returncode == 1 and f.split(".")[0] in r.stdout


def test_top100_not_from_resilient_rejected(tmp_path):
    d = _good(tmp_path)
    (d / "top100.txt").write_text("tg://proxy?server=c.example&port=443&secret=" + "00" * 16 + "\n")
    r = _run(d)
    assert r.returncode == 1 and "top100" in r.stdout


@pytest.mark.parametrize("f", ["top100.txt", "top50.txt"])
def test_top_advertised_but_missing_rejected(tmp_path, f):
    d = _good(tmp_path)
    (d / f).unlink()
    r = _run(d)
    assert r.returncode == 1 and f.split(".")[0] in r.stdout


def test_top100_duplicate_ip_rejected(tmp_path):
    d = _good(tmp_path)
    line = (d / "top100.txt").read_text().splitlines()[0]
    (d / "top100.txt").write_text(line + "\n" + line + "\n")
    r = _run(d)
    assert r.returncode == 1 and "top100" in r.stdout


def test_top50_must_be_prefix_of_top100(tmp_path):
    d = _good(tmp_path)
    lines = (d / "top100.txt").read_text().splitlines()
    (d / "top50.txt").write_text("\n".join(reversed(lines)) + "\n")
    r = _run(d)
    assert r.returncode == 1 and "top50" in r.stdout


def test_top_file_present_but_index_null_rejected(tmp_path):
    d = _good(tmp_path)
    idx = json.loads((d / "index.json").read_text())
    idx["top100"] = None
    (d / "index.json").write_text(json.dumps(idx))
    r = _run(d)
    assert r.returncode == 1 and "top100" in r.stdout


def _many(tmp_path, n_nets, per_net):
    from test_publish import _net
    write_outputs(result(_net(n_nets, per_net)), tmp_path, runner={})
    return tmp_path


def test_network_cap_exceeded_rejected(tmp_path):
    d = _many(tmp_path, 30, 6)                         # 180 candidates, cap 5 suffices
    idx = json.loads((d / "index.json").read_text())
    assert idx["top100_info"]["network_cap"] == 5
    idx["top100_info"]["network_cap"] = 4               # claim a tighter cap than published
    (d / "index.json").write_text(json.dumps(idx))
    r = _run(d)
    assert r.returncode == 1 and "network" in r.stdout


def test_raised_cap_passes(tmp_path):
    d = _many(tmp_path, 3, 60)
    assert json.loads((d / "index.json").read_text())["top100_info"]["network_cap"] == 34
    r = _run(d)
    assert r.returncode == 0, r.stdout


def test_top_info_count_mismatch_rejected(tmp_path):
    d = _good(tmp_path)
    idx = json.loads((d / "index.json").read_text())
    idx["top100_info"]["count"] += 1
    (d / "index.json").write_text(json.dumps(idx))
    r = _run(d)
    assert r.returncode == 1 and "top100" in r.stdout


def test_server_needing_url_escaping_validates(tmp_path):
    write_outputs(result([rec("a#b.example", "1.1.1.1"), rec("c&d", "8.8.8.8")]), tmp_path, runner={})
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_invalid_json_row_is_reported_not_crash(tmp_path):
    import json
    d = _good(tmp_path)
    p = d / "verified" / "proxies.json"
    rows = json.loads(p.read_text())
    rows[0]["secret"] = "zz"
    p.write_text(json.dumps(rows))
    r = _run(d)
    assert r.returncode == 1 and "invalid rows" in r.stdout and "Traceback" not in r.stderr
