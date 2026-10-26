"""Write every output file. Deterministic: same data → same bytes.

Invariants (enforced here, tested in tests/test_publish.py):
  * an empty list is never written — a client or script subscribed to an
    empty file would lose what it had; a 404 makes it keep its old copy
  * index.json lists exactly the files that exist
  * order is stable (sorted by a content-derived key, not network order)
"""
from __future__ import annotations

import csv
import io
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
FAST_MS = 100  # runner→proxy→DC round-trip; per-server p75 was 52 ms, p90 113 ms (2026-10-26, FRA)
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
    p = r.proxy
    return {
        "id": r.id,
        "server": p.server,
        "port": p.port,
        "secret": p.secret.hex(),
        "type": p.secret.kind,
        "sni": p.secret.domain_text,
        "ip": r.ip,
        "country": r.country,
        "asn": r.asn,
        "asn_org": r.asn_org,
        "level": r.level,
        "verified": r.verified,
        "rtt_ms": r.rtt,
        "uptime": r.hist.get("uptime"),
        "checks": r.hist.get("checks", 0),
        "streak": r.hist.get("streak", 0),
        "first_seen": _iso(r.hist["first_seen"]) if r.hist.get("first_seen") else None,
        "sources": sorted(p.sources),
        "tg": p.tg_link(),
        "tme": p.tme_link(),
    }


def tiers(records: list[Record]) -> dict[str, list[Record]]:
    ver = sorted((r for r in records if r.verified), key=_sort_key)
    out: dict[str, list[Record]] = {
        "verified": ver,
        "fast": [r for r in ver if r.rtt is not None and r.rtt <= FAST_MS],
        "stable": [r for r in ver if (r.hist.get("uptime") or 0) >= STABLE_UPTIME
                   and r.hist.get("checks", 0) >= STABLE_MIN_CHECKS],
        "faketls": [r for r in ver if r.proxy.secret.kind == "faketls"],
        "secure": [r for r in ver if r.proxy.secret.kind == "secure"],
        "classic": [r for r in ver if r.proxy.secret.kind == "classic"],
        "all": sorted(records, key=lambda r: (r.proxy.server, r.proxy.port, r.proxy.secret.raw)),
    }
    # resilient: one link per server IP — the list that survives a single
    # operator going down. Best (lowest RTT) link wins for each IP.
    seen: Counter = Counter()
    res = []
    for r in ver:
        if seen[r.ip] < RESILIENT_PER_IP:
            seen[r.ip] += 1
            res.append(r)
    out["resilient"] = res
    return out


def _write(path: Path, text: str, written: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    written.append(path)


def _write_tier(base: Path, name: str, recs: list[Record], written: list) -> dict | None:
    if not recs:
        return None
    d = base / name
    _write(d / "tg.txt", "\n".join(r.proxy.tg_link() for r in recs) + "\n", written)
    _write(d / "tme.txt", "\n".join(r.proxy.tme_link() for r in recs) + "\n", written)
    _write(d / "proxies.json", json.dumps([_row(r) for r in recs], ensure_ascii=False, indent=1) + "\n", written)
    buf = io.StringIO()
    cols = ["server", "port", "secret", "type", "country", "rtt_ms", "uptime", "tme"]
    w = csv.DictWriter(buf, cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in recs:
        w.writerow(_row(r))
    _write(d / "proxies.csv", buf.getvalue(), written)
    return {"count": len(recs), "servers": len({(r.ip, r.proxy.port) for r in recs}),
            "files": {f: f"{RAW}/{name}/{f}" for f in ("tg.txt", "tme.txt", "proxies.json", "proxies.csv")}}


def write_outputs(res: RunResult, out: Path, runner: dict, state_dump: dict | None = None) -> dict:
    # Remove previous generated dirs so a tier that is empty this run
    # disappears (404) instead of serving a stale copy.
    for d in OUTPUT_DIRS:
        shutil.rmtree(out / d, ignore_errors=True)
    written: list[Path] = []
    t = tiers(res.records)
    tier_meta = {}
    for name in ("verified", "fast", "stable", "resilient", "faketls", "secure", "classic", "all"):
        m = _write_tier(out, name, t[name], written)
        if m:
            tier_meta[name] = m

    by_cc: dict[str, list[Record]] = defaultdict(list)
    for r in t["verified"]:
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
            "fast": f"verified and median round-trip through the proxy <= {FAST_MS} ms (measured from the runner)",
            "stable": f"verified and passed >= {int(STABLE_UPTIME*100)}% of the last checks (min {STABLE_MIN_CHECKS})",
            "resilient": "verified, at most one link per server IP (lowest RTT kept)",
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
