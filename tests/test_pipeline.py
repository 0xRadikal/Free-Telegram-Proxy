"""Multi-address hostnames: a link is verified only if EVERY address a client
may be handed works (offline; fake prober, no sockets)."""
import asyncio

from tgproxy.links import Proxy
from tgproxy.pipeline import Config, Record, probe_records, select_addresses
from tgproxy.probe import ProbeResult
from tgproxy.secret import Secret
from tgproxy.state import proxy_id

S = Secret.from_link("00" * 16)
CFG = Config(rounds=3, gap=0)


def rec(server, addrs):
    p = Proxy(server, 443, S, frozenset({"src"}))
    r = Record(p, proxy_id(p.key), addrs[0] if addrs else None, None)
    r.targets = [(a, 443, S) for a in addrs]
    r.target = r.targets[0] if addrs else None
    return r


def fake(bad=(), flaky=None, rtt=None):
    calls = []

    async def prober(ip, port, secret, *, dc, timeout, connect_host):
        calls.append(ip)
        assert connect_host == ip
        n = sum(1 for c in calls if c == ip)
        if ip in bad or (flaky and flaky.get(ip) == n):
            return ProbeResult("tcp", "timeout@tcp", 5, None)
        return ProbeResult("dc", None, 5, (rtt or {}).get(ip, 40))
    return prober, calls


def run(records, prober):
    return asyncio.run(probe_records(records, CFG, prober))


def test_select_addresses_matches_tdlib_rules():
    assert select_addresses([]) == ([], "dns")
    assert select_addresses(["1.1.1.1", "8.8.8.8"]) == (["1.1.1.1", "8.8.8.8"], None)
    # IPv6 only used when there is no IPv4 (TDLib prefer_ipv6=false)
    assert select_addresses(["1.1.1.1", "2606:4700:4700::1111"]) == (["1.1.1.1"], None)
    assert select_addresses(["2606:4700:4700::1111"]) == (["2606:4700:4700::1111"], None)
    # one private address in the answer rejects the link
    assert select_addresses(["1.1.1.1", "10.0.0.1"]) == ([], "non-public-ip")
    assert select_addresses(["127.0.0.1"]) == ([], "non-public-ip")
    assert select_addresses([f"1.1.{i // 250}.{i % 250 + 1}" for i in range(65)])[1] == "too-many-addresses"


def test_all_addresses_ok_is_verified_and_rtt_is_worst():
    r = rec("a", ["1.1.1.1", "8.8.8.8"])
    prober, _ = fake(rtt={"1.1.1.1": 30, "8.8.8.8": 90})
    run([r], prober)
    assert r.verified and r.rtt == 90


def test_one_dead_address_rejects_the_link():
    # this is the case measured on 14 real hostnames: first address works
    r = rec("a", ["1.1.1.1", "8.8.8.8"])
    prober, calls = fake(bad={"8.8.8.8"})
    run([r], prober)
    assert not r.verified and not r.passed_any
    assert r.rounds[0].error == "multi-ip:some-addresses-fail"
    assert r.fail_reason == "multi-ip:some-addresses-fail"
    assert len(r.rounds) == 1 and len(calls) == 2  # not dialled again after failing


def test_flaky_address_in_round_two():
    r = rec("a", ["1.1.1.1", "8.8.8.8"])
    prober, _ = fake(flaky={"8.8.8.8": 2})
    run([r], prober)
    assert not r.verified and r.passed_any and r.fail_reason == "flaky"


def test_shared_target_is_dialled_once_per_round():
    a = rec("a", ["1.1.1.1"])
    b = rec("b", ["1.1.1.1"])
    c = rec("c", ["1.1.1.1", "8.8.8.8"])
    prober, calls = fake(bad={"8.8.8.8"})
    per_round, n = run([a, b, c], prober)
    assert n == 2
    assert a.verified and b.verified and not c.verified
    # round 1: both addresses; rounds 2-3: only 1.1.1.1 (8.8.8.8 only needed by c)
    assert calls.count("1.1.1.1") == 3 and calls.count("8.8.8.8") == 1
    assert per_round == [1, 1, 1]


def test_single_address_behaviour_unchanged():
    r = rec("a", ["1.1.1.1"])
    prober, _ = fake(rtt={"1.1.1.1": 55})
    run([r], prober)
    assert r.verified and r.rtt == 55 and len(r.rounds) == 3


def test_unprobed_records_are_skipped():
    r = rec("a", [])
    prober, calls = fake()
    per_round, n = run([r], prober)
    assert r.rounds == [] and calls == [] and n == 0 and per_round == [0, 0, 0]
