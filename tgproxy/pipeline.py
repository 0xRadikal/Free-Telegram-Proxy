"""collect → dedup → resolve → probe ×N → enrich → rank → (publish)."""
from __future__ import annotations

import asyncio
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import aiohttp

from .fetch import SourceReport, fetch_all, merge
from .links import Proxy
from .netinfo import Geo, is_public, resolve_all
from .probe import ProbeResult, probe
from .sources import SOURCES
from .state import State, proxy_id


@dataclass
class Config:
    rounds: int = 3
    gap: float = 20.0           # seconds between rounds
    timeout: float = 8.0
    concurrency: int = 300
    per_ip: int = 12            # simultaneous connections to one IP (be polite)
    dc: int = 2


@dataclass
class Record:
    """One published proxy (link identity)."""

    proxy: Proxy
    id: str
    ip: str | None
    target: tuple | None        # (ip, port, secret) of the representative address
    rounds: list = field(default_factory=list)  # list[ProbeResult]
    reject: str | None = None   # why it never got probed
    country: str | None = None
    asn: int | None = None
    asn_org: str | None = None
    hist: dict = field(default_factory=dict)
    targets: list = field(default_factory=list)  # every (ip, port, secret) a client may dial

    @property
    def verified(self) -> bool:
        return bool(self.rounds) and all(r.ok for r in self.rounds)

    @property
    def passed_any(self) -> bool:
        return any(r.ok for r in self.rounds)

    @property
    def rtt(self) -> int | None:
        v = [r.rtt_ms for r in self.rounds if r.ok and r.rtt_ms is not None]
        return int(statistics.median(v)) if v else None

    @property
    def level(self) -> str:
        if not self.rounds:
            return "none"
        order = {"none": 0, "tcp": 1, "tls": 2, "dc": 3}
        return max((r.level for r in self.rounds), key=order.__getitem__)

    @property
    def fail_reason(self) -> str | None:
        if self.reject:
            return self.reject
        bad = [r for r in self.rounds if not r.ok]
        if not bad:
            return None
        if self.passed_any:
            return "flaky"
        err = bad[0].error or "unknown"
        return err.split("@")[0]


@dataclass
class RunResult:
    records: list[Record]
    reports: list[SourceReport]
    timings: dict
    per_round_ok: list[int]
    targets: int
    started: int
    geo: bool


MAX_ADDRESSES = 64  # largest answer seen on 2026-10-26 was 33 addresses


def select_addresses(ips: list[str]) -> tuple[list[str], str | None]:
    """Addresses a Telegram client may actually dial for one hostname.

    TDLib (IPAddress::init_host_port, prefer_ipv6=false by default) takes the
    FIRST IPv4 address its resolver returns, and round-robin DNS rotates that
    order between users. So a link is only usable by everyone if EVERY IPv4
    address works. Measured 2026-10-26: 239 verified hostnames had several
    addresses; on 14 of them one address refused MTProto in 3 of 3 retries
    while the address we used to test (the first one) worked.
    IPv6 is only used when there is no IPv4 at all (same rule as TDLib).
    Any non-public address in the answer rejects the link: some clients would
    be sent to a private/reserved network.
    """
    if not ips:
        return [], "dns"
    if not all(is_public(i) for i in ips):
        return [], "non-public-ip"
    v4 = [i for i in ips if ":" not in i]
    addrs = v4 or list(ips)
    if len(addrs) > MAX_ADDRESSES:
        return [], "too-many-addresses"
    return addrs, None


def _combine(results: list[ProbeResult]) -> ProbeResult:
    """One round of a multi-address link: ok only if every address passed.

    RTT is the slowest address, because a client may be handed any of them.
    """
    if all(r.ok for r in results):
        rtts = [r.rtt_ms for r in results if r.rtt_ms is not None]
        tcps = [r.tcp_ms for r in results if r.tcp_ms is not None]
        return ProbeResult("dc", None, max(tcps) if tcps else None, max(rtts) if rtts else None)
    order = {"none": 0, "tcp": 1, "tls": 2, "dc": 3}
    worst = min((r for r in results if not r.ok), key=lambda r: order[r.level])
    if any(r.ok for r in results):
        return ProbeResult(worst.level, "multi-ip:some-addresses-fail", worst.tcp_ms, None)
    return worst


async def _probe_targets(targets: list[tuple], cfg: Config, prober=probe) -> dict[tuple, ProbeResult]:
    sem = asyncio.Semaphore(cfg.concurrency)
    ip_sems: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(cfg.per_ip))

    async def one(t):
        ip, port, secret = t
        async with sem, ip_sems[ip]:
            return t, await prober(ip, port, secret, dc=cfg.dc, timeout=cfg.timeout, connect_host=ip)

    return dict(await asyncio.gather(*(one(t) for t in targets)))


def _tkey(t: tuple) -> tuple:
    return (t[0], t[1], t[2].raw)


async def probe_records(records: list[Record], cfg: Config, prober=probe) -> tuple[list[int], int]:
    """Probe every distinct (ip, port, secret) once per round, shared by all
    links that resolve to it, and give each link one combined result per round.

    A link that fails a round can no longer be `verified`; addresses needed
    only by failed links are not dialled again (fewer connections to hosts).
    Returns (targets that passed per round, distinct targets dialled).
    """
    alive = [r for r in records if r.targets]
    targets = {_tkey(t): t for r in alive for t in r.targets}
    per_round_ok: list[int] = []
    for i in range(cfg.rounds):
        if not alive:
            per_round_ok.append(0)
            continue
        if i:
            await asyncio.sleep(cfg.gap)
        need = {_tkey(t): t for r in alive for t in r.targets}
        res = await _probe_targets(list(need.values()), cfg, prober)
        by_key = {_tkey(t): pr for t, pr in res.items()}
        per_round_ok.append(sum(1 for pr in by_key.values() if pr.ok))
        nxt = []
        for r in alive:
            combined = _combine([by_key[_tkey(t)] for t in r.targets])
            r.rounds.append(combined)
            if combined.ok:
                nxt.append(r)
        alive = nxt
    return per_round_ok, len(targets)


async def runner_location() -> dict:
    """Country/colo of the machine running the test (never its IP)."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.cloudflare.com/cdn-cgi/trace", timeout=aiohttp.ClientTimeout(total=10)) as r:
                kv = dict(line.split("=", 1) for line in (await r.text()).splitlines() if "=" in line)
        return {"loc": kv.get("loc"), "colo": kv.get("colo")}
    except Exception:  # noqa: BLE001 — informational only
        return {"loc": None, "colo": None}


async def run(cfg: Config | None = None, state: State | None = None, sources=SOURCES, geo: Geo | None = None) -> RunResult:
    cfg = cfg or Config()
    geo = geo or Geo()
    started = int(time.time())
    timings = {}

    t = time.monotonic()
    reports = await fetch_all(sources)
    pool = merge(reports)
    timings["fetch"] = round(time.monotonic() - t, 2)

    t = time.monotonic()
    resolved = await resolve_all({p.server for p in pool.values()})
    timings["dns"] = round(time.monotonic() - t, 2)

    records: list[Record] = []
    for key, p in pool.items():
        addrs, reject = select_addresses(resolved.get(p.server, []))
        ip = addrs[0] if addrs else (resolved.get(p.server) or [None])[0]
        rec = Record(p, proxy_id(key), ip, None)
        if reject:
            rec.reject = reject
        else:
            # The hostname only matters for DNS; on the wire the proxy sees
            # (ip, port, secret). Probing per target avoids hammering one
            # server through hundreds of sub-domain aliases.
            rec.targets = [(a, p.port, p.secret) for a in addrs]
            rec.target = rec.targets[0]
        records.append(rec)

    t = time.monotonic()
    per_round_ok, n_targets = await probe_records(records, cfg)
    timings["probe"] = round(time.monotonic() - t, 2)

    for r in records:
        if r.ip:
            r.country = geo.country(r.ip)
            r.asn, r.asn_org = geo.asn(r.ip)

    if state is not None:
        now = int(time.time())
        for r in records:
            if r.rounds:
                state.record(r.id, r.verified, now, r.rtt)
            r.hist = state.stats(r.id)
        src_found = Counter()
        src_ok = Counter()
        for r in records:
            for s in r.proxy.sources:
                src_found[s] += 1
                src_ok[s] += r.verified
        for rep in reports:
            state.record_source(rep.id, src_found[rep.id], src_ok[rep.id], now)
        state.finish_run(now)

    return RunResult(records, reports, timings, per_round_ok, n_targets, started, geo.available)
