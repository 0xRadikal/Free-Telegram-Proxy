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


def test_fast_is_relative_to_runner():
    def at(ms, ip):
        r = rec(f"h{ip}", ip)
        r.rounds = [ProbeResult("dc", None, 5, ms)] * 3
        return r
    # simulate a far-away runner: every RTT >= 139 ms (as measured from the US)
    rs = [at(139 + i, f"10.0.0.{i}") for i in range(40)]
    t = tiers(rs)
    assert len(t["fast"]) == 10 and max(r.rtt for r in t["fast"]) == 148
    assert tiers([])["fast"] == []


def test_top_prefers_proven_over_fast():
    from tgproxy.publish import _top
    veteran = rec("vet", "1.0.0.1")
    veteran.rounds = [ProbeResult("dc", None, 5, 200)] * 3
    veteran.hist = {"uptime": 1.0, "checks": 40}
    newbie = rec("new", "1.0.0.2")
    newbie.rounds = [ProbeResult("dc", None, 5, 10)] * 3
    newbie.hist = {"uptime": 1.0, "checks": 1}
    flaky = rec("flk", "1.0.0.3")
    flaky.rounds = [ProbeResult("dc", None, 5, 5)] * 3
    flaky.hist = {"uptime": 0.5, "checks": 40}
    top, _ = _top([newbie, flaky, veteran])
    assert [r.proxy.server for r in top] == ["vet", "flk", "new"]


def test_top_without_history_falls_back_to_rtt():
    from tgproxy.publish import _top
    a, b = rec("a", "1.0.0.1"), rec("b", "1.0.0.2")
    a.rounds = [ProbeResult("dc", None, 5, 90)] * 3
    b.rounds = [ProbeResult("dc", None, 5, 20)] * 3
    top, _ = _top([a, b])
    assert [r.proxy.server for r in top] == ["b", "a"]


def _net(n_networks, per_net, checks=40, uptime=1.0, start=0):
    """per_net records in each of n_networks distinct ASNs."""
    out = []
    for n in range(n_networks):
        for i in range(per_net):
            r = rec(f"n{n + start}-{i}", f"10.{n + start}.{i // 250}.{i % 250 + 1}")
            r.asn = 64500 + n + start
            r.hist = {"uptime": uptime, "checks": checks}
            out.append(r)
    return out


def test_top_caps_each_network_at_base_when_enough_networks():
    from collections import Counter
    from tgproxy.publish import TOP_N, TOP_NETWORK_CAP, _top, network_of
    rs = _net(1, 80) + _net(40, 3, start=1)       # one dominant network + 40 small ones
    top, cap = _top(rs)
    assert len(top) == TOP_N == 100 and cap == TOP_NETWORK_CAP == 5
    assert max(Counter(network_of(r) for r in top).values()) == 5


def test_top_cap_rises_only_as_far_as_needed():
    from collections import Counter
    from tgproxy.publish import _top, network_of
    rs = _net(3, 60)                               # only 3 networks: 5 per network fills 15
    top, cap = _top(rs)
    assert len(top) == 100 and cap == 34           # smallest cap with 3*cap >= 100
    c = Counter(network_of(r) for r in top)
    assert sorted(c.values()) == [32, 34, 34]       # greedy: higher-ranked networks fill first


def test_top_raises_cap_rather_than_admit_unproven():
    """Proven (stable-tier) proxies first: if the cap would force in unproven
    newcomers while proven ones are left out, the cap is raised instead."""
    from tgproxy.publish import STABLE_MIN_CHECKS, _top
    proven = _net(10, 12)                                        # 120 proven, 10 networks
    newbies = _net(40, 1, checks=STABLE_MIN_CHECKS - 1, start=10)  # 40 unproven, 40 networks
    top, cap = _top(proven + newbies)
    assert cap == 10 and len(top) == 100
    assert all(r.hist["checks"] >= STABLE_MIN_CHECKS for r in top)


def test_top_fills_with_unproven_only_after_proven_run_out():
    from tgproxy.publish import STABLE_MIN_CHECKS, _top
    proven = _net(20, 2)                                         # 40 proven
    newbies = _net(30, 3, checks=1, start=20)                    # 90 unproven
    top, cap = _top(proven + newbies)
    assert len(top) == 100 and cap == 5
    assert all(r.hist["checks"] >= STABLE_MIN_CHECKS for r in top[:40])
    assert all(r.hist["checks"] < STABLE_MIN_CHECKS for r in top[40:])


def test_top_small_and_empty_pools():
    from tgproxy.publish import TOP_NETWORK_CAP, _top
    assert _top([]) == ([], TOP_NETWORK_CAP)
    top, cap = _top(_net(1, 7))                    # fewer candidates than TOP_N
    assert len(top) == 7 and cap == 7


def test_top_is_deterministic_under_input_order():
    import random
    from tgproxy.publish import _top
    rs = _net(1, 80) + _net(40, 3, start=1)
    want = [r.proxy.key for r in _top(rs)[0]]
    for seed in range(5):
        random.Random(seed).shuffle(rs)
        assert [r.proxy.key for r in _top(rs)[0]] == want


def test_top100_and_top50_alias_written(tmp_path):
    from tgproxy.publish import network_of
    rs = _net(1, 80) + _net(40, 3, start=1)
    out = write_outputs(result(rs), tmp_path, runner={})
    t100 = (tmp_path / "top100.txt").read_text().splitlines()
    t50 = (tmp_path / "top50.txt").read_text().splitlines()
    assert len(t100) == 100 and t50 == t100[:50]
    idx = out["index"]
    assert idx["top100"].endswith("/top100.txt") and idx["top50"].endswith("/top50.txt")
    info = idx["top100_info"]
    assert info == {"count": 100, "network_cap": 5, "base_network_cap": 5,
                    "networks": len({network_of(r) for r in out["tiers"]["top100"]}),
                    "proven": 100}


def test_no_top_files_when_nothing_verified(tmp_path):
    (tmp_path / "top100.txt").write_text("stale\n")
    (tmp_path / "top50.txt").write_text("stale\n")
    out = write_outputs(result([rec("a", "1.1.1.1", rounds=(BAD, BAD, BAD))]), tmp_path, runner={})
    assert not (tmp_path / "top100.txt").exists() and not (tmp_path / "top50.txt").exists()
    assert out["index"]["top100"] is None and out["index"]["top50"] is None
    assert out["index"]["top100_info"] is None


def test_alias_choice_is_stable_not_rtt_noise():
    from tgproxy.publish import _one_per_ip
    a = rec("a.example", "9.9.9.9")
    b = rec("b.example", "9.9.9.9")
    a.hist, b.hist = {"checks": 10}, {"checks": 10}
    for rtt_a, rtt_b in ((30, 40), (40, 30)):      # RTT order flips between runs
        a.rounds = [ProbeResult("dc", None, 5, rtt_a)] * 3
        b.rounds = [ProbeResult("dc", None, 5, rtt_b)] * 3
        recs = sorted([a, b], key=lambda r: r.rtt)
        assert [r.proxy.server for r in _one_per_ip(recs)] == ["a.example"]
    b.hist = {"checks": 50}                         # longer history wins
    assert [r.proxy.server for r in _one_per_ip([a, b])] == ["b.example"]


def test_network_share_uses_asn_or_prefix_fallback(tmp_path):
    from tgproxy.publish import network_of
    a = rec("a", "191.44.90.33"); a.asn = None
    b = rec("b", "191.44.90.29"); b.asn = None
    c = rec("c", "1.1.1.1"); c.asn = 13335
    d = rec("d", "2a01:4f8::1"); d.asn = None
    assert network_of(a) == network_of(b) == "191.44.90.0/24"
    assert network_of(c) == "AS13335" and network_of(d) == "2a01:4f8::/48"
    out = write_outputs(result([a, b, c]), tmp_path, runner={})
    f = out["index"]["funnel"]
    assert f["top_ip_share"] == {"links": 1, "share": 0.3333}
    assert f["top_network_share"] == {"network": "191.44.90.0/24", "links": 2, "share": 0.6667}


def test_resilient_criteria_matches_implementation(tmp_path):
    out = write_outputs(result([rec("a", "1.1.1.1")]), tmp_path, runner={})
    txt = out["index"]["criteria"]["resilient"]
    assert "lowest RTT kept" not in txt and "longest check history" in txt


# ── audit round 6 ──────────────────────────────────────────────────────────
import pytest  # noqa: E402


@pytest.mark.parametrize("bad", ['"x"', '{"version":1,"proxies":[]}', '{"version":1,"proxies":{"a":"b"}}',
                                 '{"version":1,"runs":"x"}', '{"version":1,"sources":{"s":{"found":5}}}',
                                 '{"version":1,"proxies":{"a":{"h":5}}}'])
def test_corrupt_state_is_ignored_not_fatal(tmp_path, bad):
    from tgproxy.state import State
    p = tmp_path / "state.json"
    p.write_text(bad)
    s = State.load(p)
    s.record("a", True, 100, 5)
    s.record_source("s", 1, 1, 100)
    s.finish_run(100)
    assert s.stats("a")["checks"] >= 1


def test_good_state_entries_survive_next_to_bad_ones(tmp_path):
    from tgproxy.state import State
    good = {"h": "111", "first": 1, "last_ok": 1, "last_seen": 1}
    s = State({"version": 1, "runs": 3, "proxies": {"g": good, "b": "junk"}, "sources": {}})
    assert s.stats("g")["checks"] == 3 and "b" not in s.proxies and s.runs == 3


def test_servers_probed_counts_every_dialled_address(tmp_path):
    a = rec("multi.example", "1.1.1.1")
    a.targets = [("1.1.1.1", 443, a.proxy.secret), ("8.8.8.8", 443, a.proxy.secret)]
    out = write_outputs(result([a]), tmp_path, runner={})
    assert out["index"]["funnel"]["unique_servers_probed"] == 2
