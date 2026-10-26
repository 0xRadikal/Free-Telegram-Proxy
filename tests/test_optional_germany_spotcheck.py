"""Offline tests only. NO actual sockets or MTProto handshakes."""
import asyncio
import json

import pytest

from tgproxy.probe import ProbeResult
from tgproxy.secret import Secret
from tools.optional_germany_spotcheck import load_candidates, select_diverse, spotcheck, main


def entry(ip, asn, secret="00" * 16):
    return {"ip": ip, "port": 443, "secret": secret, "asn": asn}


def test_rejects_private_bad_ports_and_secrets(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps([entry("1.1.1.1", 1), entry("127.0.0.1", 2),
                             entry("10.0.0.1", 3), entry("8.8.8.8", 4, "BAD"),
                             {**entry("9.9.9.9", 5), "port": 99999}, entry("1.1.1.1", 9)]))
    out = load_candidates(p)
    assert len(out) == 1 and out[0]["ip"] == "1.1.1.1"


def test_diverse_asn_sampling():
    rows = [{"ip": f"1.1.1.{n}", "port": 443, "asn": (n % 3),
             "secret": Secret.from_link("00" * 16)} for n in range(1, 16)]
    chosen = select_diverse(rows, 3)
    assert len(chosen) == 3
    assert len({p["asn"] for p in chosen}) == 3
    assert select_diverse(rows, 3) == chosen


def test_default_is_offline_and_no_secrets_disclosed(tmp_path, capsys):
    f = tmp_path / "in.json"
    f.write_text(json.dumps([entry("1.1.1.1", 1337, "11" * 16)]))
    assert main(["--source", str(f)]) == 0
    report = capsys.readouterr().out
    assert '"mode": "dry-run"' in report
    assert "1.1.1.1" not in report and "1111111111" not in report


def test_bounded_real_probe_behaviour_with_fake_prober():
    seen = []

    async def stub(ip, port, secret, *, dc, timeout, connect_host):
        seen.append((ip, port, dc, connect_host))
        assert dc == 2 and connect_host == ip
        return ProbeResult(level="dc" if ip == "1.1.1.1" else "tcp", rtt_ms=20)

    sample = [{"ip": "1.1.1.1", "port": 443, "secret": Secret.from_link("00" * 16), "asn": 1},
              {"ip": "8.8.8.8", "port": 443, "secret": Secret.from_link("00" * 16), "asn": 2}]
    result = asyncio.run(spotcheck(sample, rounds=2, timeout=4, concurrency=2, prober=stub))
    assert result["probed"] == 2 and result["fully_verified"] == 1
    assert result["failure_levels"] == {"tcp": 1}
    assert len(seen) == 3  # fail-fast after first rejected probe
    assert result["rtt_median_ms"] == 20


def test_out_of_bounds_rejected(tmp_path):
    with pytest.raises(SystemExit) as e:
        main(["--max-proxies", "100", "--live"])
    assert e.value.code == 2


def test_unknown_asn_grouped_by_prefix():
    s = Secret.from_link("00" * 16)
    rows = [{"ip": f"191.44.90.{n}", "port": 443, "asn": None, "secret": s} for n in range(1, 30)]
    rows.append({"ip": "8.8.8.8", "port": 443, "asn": None, "secret": s})
    first_two = select_diverse(rows, 2)
    assert {p["ip"].rsplit(".", 1)[0] for p in first_two} == {"191.44.90", "8.8.8"}


def test_runs_as_plain_script(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    f = tmp_path / "in.json"
    f.write_text(json.dumps([entry("1.1.1.1", 1)]))
    tool = Path(__file__).resolve().parent.parent / "tools" / "optional_germany_spotcheck.py"
    r = subprocess.run([sys.executable, str(tool), "--source", str(f)], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert '"mode": "dry-run"' in r.stdout
