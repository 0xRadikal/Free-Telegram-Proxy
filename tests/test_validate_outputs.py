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


def test_corrupt_top50_line_rejected(tmp_path):
    d = _good(tmp_path)
    with open(d / "top50.txt", "a") as f:
        f.write("tg://proxy?server=bad&port=0&secret=zz\n")
    r = _run(d)
    assert r.returncode == 1 and "top50" in r.stdout


def test_top50_not_from_resilient_rejected(tmp_path):
    d = _good(tmp_path)
    (d / "top50.txt").write_text("tg://proxy?server=c.example&port=443&secret=" + "00" * 16 + "\n")
    r = _run(d)
    assert r.returncode == 1 and "top50" in r.stdout


def test_top50_advertised_but_missing_rejected(tmp_path):
    d = _good(tmp_path)
    (d / "top50.txt").unlink()
    r = _run(d)
    assert r.returncode == 1 and "top50" in r.stdout


def test_top50_duplicate_ip_rejected(tmp_path):
    d = _good(tmp_path)
    line = (d / "top50.txt").read_text().splitlines()[0]
    (d / "top50.txt").write_text(line + "\n" + line + "\n")
    r = _run(d)
    assert r.returncode == 1 and "top50" in r.stdout


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
