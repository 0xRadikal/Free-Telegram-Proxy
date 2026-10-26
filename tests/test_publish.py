import json

from tgproxy.links import Proxy
from tgproxy.pipeline import Record, RunResult
from tgproxy.probe import ProbeResult
from tgproxy.publish import RESILIENT_PER_IP, tiers, write_outputs
from tgproxy.secret import Secret
from tgproxy.state import State, proxy_id

OK = ProbeResult("dc", None, 5, 40)
BAD = ProbeResult("tcp", "timeout@tcp", 5, None)


def rec(server, ip, secret="00" * 16, rounds=(OK, OK, OK), port=443, cc="DE"):
    p = Proxy(server, port, Secret.from_link(secret), frozenset({"src"}))
    r = Record(p, proxy_id(p.key), ip, (ip, port, p.secret), list(rounds))
    r.country = cc
    return r


def result(records):
    return RunResult(records, [], {}, [1, 1, 1], len(records), 1_700_000_000, False)


def test_verified_requires_every_round():
    t = tiers([rec("a", "1.1.1.1"), rec("b", "1.1.1.2", rounds=(OK, BAD, OK))])
    assert [r.proxy.server for r in t["verified"]] == ["a"]


def test_resilient_caps_links_per_ip():
    rs = [rec(f"h{i}", "9.9.9.9") for i in range(50)] + [rec("other", "8.8.8.8")]
    t = tiers(rs)
    assert len(t["verified"]) == 51
    assert len(t["resilient"]) == 2 * RESILIENT_PER_IP


def test_empty_tier_is_not_written(tmp_path):
    out = write_outputs(result([rec("a", "1.1.1.1")]), tmp_path, {"loc": "DE"}, None)
    assert not (tmp_path / "stable").exists()        # no history yet → no file at all
    assert (tmp_path / "verified" / "tg.txt").read_text().count("\n") == 1
    idx = json.loads((tmp_path / "index.json").read_text())
    for name, meta in idx["tiers"].items():
        for f in meta["files"]:
            assert (tmp_path / name / f).exists(), (name, f)
    assert "stable" not in idx["tiers"]
    assert out["index"]["funnel"]["verified_links"] == 1


def test_stale_tier_removed_on_next_run(tmp_path):
    write_outputs(result([rec("a", "1.1.1.1", secret="dd" + "00" * 16)]), tmp_path, {}, None)
    assert (tmp_path / "secure" / "tg.txt").exists()
    write_outputs(result([rec("a", "1.1.1.1")]), tmp_path, {}, None)
    assert not (tmp_path / "secure").exists()


def test_output_is_deterministic(tmp_path):
    rs = [rec(f"h{i}", f"1.1.1.{i}") for i in range(20)]
    a, b = tmp_path / "a", tmp_path / "b"
    write_outputs(result(rs), a, {}, None)
    write_outputs(result(list(reversed(rs))), b, {}, None)
    for f in ("verified/tg.txt", "verified/proxies.json", "index.json", "all/tg.txt"):
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_published_links_reparse_to_same_proxy(tmp_path):
    from tgproxy.links import parse_link
    rs = [rec("a.b", "1.1.1.1", secret="ee" + "11" * 16 + "676f6f676c652e636f6d")]
    write_outputs(result(rs), tmp_path, {}, None)
    for line in (tmp_path / "verified" / "tg.txt").read_text().split():
        assert parse_link(line).key == rs[0].proxy.key


def test_state_skips_never_working_proxies():
    s = State()
    s.record("dead", False, 1, None)
    assert "dead" not in s.proxies
    s.record("x", True, 1, 10)
    s.record("x", False, 2, None)
    assert s.stats("x")["checks"] == 2


def test_state_uptime_and_bounds():
    s = State()
    s.record("x", True, 999, 30)
    for i in range(200):
        s.record("x", i % 4 != 0, 1000 + i, 30)
    st = s.stats("x")
    assert st["checks"] == 96 and 0.70 < st["uptime"] < 0.80
    s.finish_run(1000 + 8 * 86400)
    assert "x" not in s.proxies


def test_source_exclusivity_is_leave_one_out():
    from tgproxy.fetch import SourceReport
    from tgproxy.publish import _source_health

    def r(server, ip, srcs):
        x = rec(server, ip)
        return Record(Proxy(x.proxy.server, 443, x.proxy.secret, frozenset(srcs)), x.id, ip, x.target, x.rounds)

    records = [r("shared", "1.1.1.1", {"A", "B"}), r("onlyA", "2.2.2.2", {"A"})]
    a = _source_health(SourceReport("A", "u", "github"), records)
    b = _source_health(SourceReport("B", "u", "github"), records)
    assert a["exclusive_verified_servers"] == 1   # only 2.2.2.2
    assert b["exclusive_verified_servers"] == 0   # 1.1.1.1 is also in A


def test_derived_tiers_are_one_per_ip(tmp_path):
    rs = [rec(f"h{i}", "9.9.9.9", secret="dd" + "00" * 16) for i in range(30)]
    t = tiers(rs)
    assert len(t["verified"]) == 30
    for name in ("resilient", "fast", "secure"):
        assert len(t[name]) == 1, name


def test_all_tier_is_text_only(tmp_path):
    write_outputs(result([rec("a", "1.1.1.1")]), tmp_path, {}, None)
    assert sorted(p.name for p in (tmp_path / "all").iterdir()) == ["tg.txt"]
    assert not list(tmp_path.rglob("*.csv"))
