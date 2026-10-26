"""Write every output file. Deterministic: same data → same bytes.

Invariants (enforced here, tested in tests/test_publish.py):
  * an empty list is never written — a client or script subscribed to an
    empty file would lose what it had; a 404 makes it keep its old copy
  * index.json lists exactly the files that exist
  * order is stable (sorted by a content-derived key, not network order)
"""
from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .netinfo import flag
from .pipeline import Record, RunResult

REPO = "0xRadikal/Free-Telegram-Proxy"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
CDN = f"https://cdn.jsdelivr.net/gh/{REPO}@main"
# `fast` is RELATIVE: the fastest quarter of `resilient`, measured from this
# run's runner. A fixed threshold is location-dependent and broke in practice:
# 100 ms (calibrated from Frankfurt, per-server p75 = 52 ms) gave an EMPTY tier
# from the US runner, whose per-server minimum was ~139 ms (2026-10-26).
FAST_FRACTION = 0.25
STABLE_UPTIME = 0.90
STABLE_MIN_CHECKS = 12
RESILIENT_PER_IP = 1
TOP_N = 50

OUTPUT_DIRS = ("verified", "fast", "stable", "resilient", "faketls", "secure", "classic", "all", "countries")
OUTPUT_FILES = ("top50.txt", "index.json", "health.json", "state.json")


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sort_key(r: Record):
    return (r.rtt if r.rtt is not None else 10**9, r.proxy.server, r.proxy.port, r.proxy.secret.raw)


def _row(r: Record) -> dict:
    """Slim record. Links are derivable from server/port/secret, so they are
    not repeated here (that alone was ~2/3 of the JSON size)."""
    p = r.proxy
    return {
        "server": p.server,
        "port": p.port,
        "secret": p.secret.hex(),
        "type": p.secret.kind,
        "ip": r.ip,
        "country": r.country,
        "asn": r.asn,
        "asn_org": r.asn_org,
        "rtt_ms": r.rtt,
        "uptime": r.hist.get("uptime"),
        "checks": r.hist.get("checks", 0),
        "sources": sorted(p.sources),
    }


def _one_per_ip(recs: list[Record]) -> list[Record]:
    """Keep the first (= lowest RTT, input is sorted) link of every server IP."""
    seen: Counter = Counter()
    out = []
    for r in recs:
        if seen[r.ip] < RESILIENT_PER_IP:
            seen[r.ip] += 1
            out.append(r)
    return out


def _fastest(res: list[Record]) -> list[Record]:
    timed = [r for r in res if r.rtt is not None]
    if not timed:
        return []
    k = max(1, round(len(timed) * FAST_FRACTION))
    cutoff = sorted(r.rtt for r in timed)[k - 1]
    return [r for r in timed if r.rtt <= cutoff]  # ties at the cutoff are kept


def tiers(records: list[Record]) -> dict[str, list[Record]]:
    """`verified` is the complete honest set (every alias). Every other tier is
    one link per server IP: on 2026-10-26 one operator owned ~62% of verified
    links via hundreds of sub-domains, so aliases add size, not resilience."""
    ver = sorted((r for r in records if r.verified), key=_sort_key)
    res = _one_per_ip(ver)
    return {
        "verified": ver,
        "resilient": res,
        "fast": _fastest(res),
        "stable": [r for r in res if (r.hist.get("uptime") or 0) >= STABLE_UPTIME
                   and r.hist.get("checks", 0) >= STABLE_MIN_CHECKS],
        "faketls": _one_per_ip([r for r in ver if r.proxy.secret.kind == "faketls"]),
        "secure": _one_per_ip([r for r in ver if r.proxy.secret.kind == "secure"]),
        "classic": _one_per_ip([r for r in ver if r.proxy.secret.kind == "classic"]),
        "all": sorted(records, key=lambda r: (r.proxy.server, r.proxy.port, r.proxy.secret.raw)),
    }


def _write(path: Path, text: str, written: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    written.append(path)


TIER_FILES = ("tg.txt", "tme.txt", "proxies.json")


def _write_tier(base: Path, name: str, recs: list[Record], written: list, files=TIER_FILES) -> dict | None:
    if not recs:
        return None
    d = base / name
    if "tg.txt" in files:
        _write(d / "tg.txt", "\n".join(r.proxy.tg_link() for r in recs) + "\n", written)
    if "tme.txt" in files:
        _write(d / "tme.txt", "\n".join(r.proxy.tme_link() for r in recs) + "\n", written)
    if "proxies.json" in files:
        _write(d / "proxies.json", json.dumps([_row(r) for r in recs], ensure_ascii=False,
                                              separators=(",", ":")) + "\n", written)
    return {"count": len(recs), "servers": len({(r.ip, r.proxy.port) for r in recs}),
            "files": {f: f"{RAW}/{name}/{f}" for f in files}}


def write_outputs(res: RunResult, out: Path, runner: dict, state_dump: dict | None = None) -> dict:
    # Remove previous generated dirs so a tier that is empty this run
    # disappears (404) instead of serving a stale copy.
    for d in OUTPUT_DIRS:
        shutil.rmtree(out / d, ignore_errors=True)
    written: list[Path] = []
    t = tiers(res.records)
    tier_meta = {}
    for name in ("verified", "fast", "stable", "resilient", "faketls", "secure", "classic", "all"):
        # all/ includes dead links (research use): text only, no JSON.
        m = _write_tier(out, name, t[name], written, ("tg.txt",) if name == "all" else TIER_FILES)
        if m:
            tier_meta[name] = m

    by_cc: dict[str, list[Record]] = defaultdict(list)
    for r in t["resilient"]:
        if r.country:
            by_cc[r.country].append(r)
    countries = {}
    for cc in sorted(by_cc):
        recs = by_cc[cc]
        _write(out / "countries" / f"{cc}.txt", "\n".join(r.proxy.tg_link() for r in recs) + "\n", written)
        countries[cc] = {"count": len(recs), "flag": flag(cc), "url": f"{RAW}/countries/{cc}.txt"}

    top = t["resilient"][:TOP_N]
    if top:
        _write(out / "top50.txt", "\n".join(r.proxy.tg_link() for r in top) + "\n", written)

    funnel = _funnel(res, t)
    now = res.started
    index = {
        "schema": 1,
        "rounds": len(res.per_round_ok),
        "updated": _iso(now),
        "updated_unix": now,
        "runner": runner,
        "funnel": funnel,
        "tiers": tier_meta,
        "countries": countries,
        "top50": f"{RAW}/top50.txt" if top else None,
        "mirror_prefix": CDN,
        "criteria": {
            "verified": f"relayed a real MTProto request to Telegram DC and got our nonce back, in all {len(res.per_round_ok)} rounds",
            "fast": f"fastest {int(FAST_FRACTION*100)}% of resilient by median round-trip through the proxy, measured from the runner",
            "stable": f"verified and passed >= {int(STABLE_UPTIME*100)}% of the last checks (min {STABLE_MIN_CHECKS})",
            "resilient": "verified, at most one link per server IP (lowest RTT kept)",
            "derived_tiers": "fast/stable/faketls/secure/classic/countries are taken from verified with one link per server IP",
            "top50": "first 50 of resilient",
        },
    }
    health = {
        "updated": _iso(now),
        "runner": runner,
        "timings_s": res.timings,
        "geoip": "DB-IP Lite (CC BY 4.0)" if res.geo else None,
        "per_round_ok_targets": res.per_round_ok,
        "funnel": funnel,
        "reasons": dict(Counter(r.fail_reason for r in res.records if r.fail_reason).most_common()),
        "sources": [_source_health(rep, res.records) for rep in res.reports],
        "operators": _operators(t["verified"]),
    }
    _write(out / "index.json", json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True) + "\n", written)
    _write(out / "health.json", json.dumps(health, ensure_ascii=False, indent=1, sort_keys=True) + "\n", written)
    if state_dump is not None:
        _write(out / "state.json", json.dumps(state_dump, separators=(",", ":"), sort_keys=True), written)
    return {"index": index, "health": health, "tiers": t, "written": written}


def _funnel(res: RunResult, t) -> dict:
    recs = res.records
    ver = t["verified"]
    return {
        "links_collected": len(recs),
        "dns_ok": sum(1 for r in recs if r.ip),
        "unique_targets_probed": res.targets,  # distinct (ip, port, secret) actually dialled
        "unique_servers_probed": len({(r.ip, r.proxy.port) for r in recs if r.target}),
        "tcp_ok": sum(1 for r in recs if r.level in ("tcp", "tls", "dc")),
        "dc_ok_any_round": sum(1 for r in recs if r.passed_any),
        "verified_links": len(ver),
        "verified_servers": len({(r.ip, r.proxy.port) for r in ver}),
        "verified_ips": len({r.ip for r in ver}),
        "top_ip_share": _top_share(ver),
    }


def _top_share(ver: list[Record]) -> dict | None:
    if not ver:
        return None
    ip, n = Counter(r.ip for r in ver).most_common(1)[0]
    return {"links": n, "share": round(n / len(ver), 4)}


def _operators(ver: list[Record], n: int = 10) -> list[dict]:
    c = Counter((r.asn, r.asn_org) for r in ver)
    return [{"asn": a, "org": o, "links": k} for (a, o), k in c.most_common(n)]


def _source_health(rep, records) -> dict:
    """Leave-one-out: servers that would disappear if this source were removed.

    A record listed by this source AND another source still counts as
    "covered by others" — testing only `rep.id not in sources` (the first
    version) wrongly treated shared records as exclusive and inflated the
    number roughly 70x for big sources (measured: 147 reported vs 2 real).
    """
    mine = [r for r in records if rep.id in r.proxy.sources]
    ver = [r for r in mine if r.verified]
    others = {(r.ip, r.proxy.port) for r in records if r.verified and (r.proxy.sources - {rep.id})}
    excl = {(r.ip, r.proxy.port) for r in ver} - others
    d = rep.public()
    d.update({"verified": len(ver), "exclusive_verified_servers": len(excl)})
    return d
