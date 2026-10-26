"""Offline positive and negative controls for the GitHub-only health watchdog."""
import copy
import json
from datetime import datetime, timezone

import pytest

from tools.check_freshness import CheckError, check, main

NOW = 1_800_000_000


def documents(age_minutes=12):
    ts = NOW - age_minutes * 60
    stamp = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    funnel = {"links_collected": 100, "verified_links": 80,
              "verified_servers": 45, "verified_ips": 43}
    index = {"updated": stamp, "updated_unix": ts, "rounds": 3,
             "funnel": funnel, "tiers": {"verified": {"count": 80}}, "runner": {"loc": "US"}}
    health = {"updated": stamp, "funnel": copy.deepcopy(funnel),
              "per_round_ok_targets": [70, 66, 61]}
    return index, health


def test_healthy():
    i, h = documents()
    r = check(i, h, now=NOW)
    assert r["verified_servers"] == 45 and r["age_minutes"] == 12


@pytest.mark.parametrize("age", [66, 120])
def test_stale_rejected(age):
    with pytest.raises(CheckError, match="stale"):
        check(*documents(age), now=NOW)


def test_future_timestamp_rejected():
    with pytest.raises(CheckError, match="future"):
        check(*documents(-6), now=NOW)


def test_clock_skew_tolerance():
    assert check(*documents(-3), now=NOW)["age_minutes"] == 0


@pytest.mark.parametrize("change,pattern", [
    (lambda i,h: i["tiers"]["verified"].update(count=50), "tier count"),
    (lambda i,h: h["funnel"].update(verified_links=79), "disagrees"),
    (lambda i,h: (i["funnel"].update(verified_ips=100), h["funnel"].update(verified_ips=100)), "ordering"),
    (lambda i,h: i.update(updated_unix=123), "updated_unix"),
    (lambda i,h: h.update(per_round_ok_targets=[1]), "per-round"),
    (lambda i,h: i["funnel"].update(verified_links=True), "integer"),
])
def test_corrupt_metadata_rejected(change, pattern):
    i, h = documents()
    change(i, h)
    with pytest.raises(CheckError, match=pattern):
        check(i, h, now=NOW)


def test_too_few_verified_rejected():
    i, h = documents()
    i["funnel"]["verified_links"] = 19
    h["funnel"]["verified_links"] = 19
    i["funnel"]["verified_servers"] = 10
    h["funnel"]["verified_servers"] = 10
    i["funnel"]["verified_ips"] = 9
    h["funnel"]["verified_ips"] = 9
    i["tiers"]["verified"]["count"] = 19
    with pytest.raises(CheckError, match="below safety floor"):
        check(i, h, now=NOW)


def test_bad_json_and_exit_status(tmp_path, monkeypatch):
    index = tmp_path / "index.json"
    health = tmp_path / "health.json"
    i, h = documents()
    index.write_text(json.dumps(i))
    health.write_text(json.dumps(h))
    monkeypatch.setattr("tools.check_freshness.time.time", lambda: NOW)
    assert main(["--index", str(index), "--health", str(health)]) == 0
    index.write_text("NOT JSON")
    assert main(["--index", str(index), "--health", str(health)]) == 1


def test_step_summary_only_optional(tmp_path, monkeypatch):
    i, h = documents()
    ip, hp = tmp_path / "i.json", tmp_path / "h.json"
    ip.write_text(json.dumps(i))
    hp.write_text(json.dumps(h))
    summary = tmp_path / "report.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr("tools.check_freshness.time.time", lambda: NOW)
    assert main(["--index", str(ip), "--health", str(hp)]) == 0
    assert "Publication health: OK" in summary.read_text()


def test_schema_accepts_observed_repository_numbers():
    # Fields and counts recorded from index.json / health.json on 2026-10-26;
    # this is a constructed fixture, NOT a network test of current endpoints.
    i, h = documents()
    i["funnel"].update(links_collected=3209, verified_links=1751,
                       verified_servers=405, verified_ips=377)
    h["funnel"].update(i["funnel"])
    i["tiers"]["verified"]["count"] = 1751
    h["per_round_ok_targets"] = [650, 647, 630]
    got = check(i, h, now=NOW)
    assert got["verified_ips"] == 377 and got["verified_links"] == 1751
