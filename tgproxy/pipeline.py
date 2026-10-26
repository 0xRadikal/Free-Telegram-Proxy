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
    target: tuple | None        # (ip, port, secret) actually probed
    rounds: list = field(default_factory=list)  # list[ProbeResult]
    reject: str | None = None   # why it never got probed
    country: str | None = None
    asn: int | None = None
    asn_org: str | None = None
    hist: dict = field(default_factory=dict)

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


async def _probe_targets(targets: list[tuple], cfg: Config) -> dict[tuple, ProbeResult]:
    sem = asyncio.Semaphore(cfg.concurrency)
    ip_sems: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(cfg.per_ip))

    async def one(t):
        ip, port, secret = t
        async with sem, ip_sems[ip]:
            return t, await probe(ip, port, secret, dc=cfg.dc, timeout=cfg.timeout, connect_host=ip)

    return dict(await asyncio.gather(*(one(t) for t in targets)))


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
        ips = resolved.get(p.server, [])
        ip = ips[0] if ips else None
        rec = Record(p, proxy_id(key), ip, None)
        if ip is None:
            rec.reject = "dns"
        elif not is_public(ip):
            rec.reject = "non-public-ip"
        else:
            # The hostname only matters for DNS; on the wire the proxy sees
            # (ip, port, secret). Probing per target avoids hammering one
            # server through hundreds of sub-domain aliases.
            rec.target = (ip, p.port, p.secret)
        records.append(rec)

    by_target: dict[tuple, list[Record]] = defaultdict(list)
    for r in records:
        if r.target:
            by_target[(r.target[0], r.target[1], r.target[2].raw)].append(r)
    live = {k: v[0].target for k, v in by_target.items()}

    per_round_ok = []
    t = time.monotonic()
    for i in range(cfg.rounds):
        if i:
            await asyncio.sleep(cfg.gap)
        res = await _probe_targets(list(live.values()), cfg)
        ok_keys = {}
        for k, tgt in live.items():
            pr = res[tgt]
            for rec in by_target[k]:
                rec.rounds.append(pr)
            if pr.ok:
                ok_keys[k] = tgt
        per_round_ok.append(len(ok_keys))
        # A target that failed a round can no longer be `verified` — stop
        # spending connections on it (its failure is already recorded).
        live = ok_keys
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

    return RunResult(records, reports, timings, per_round_ok, len(by_target), started, geo.available)
