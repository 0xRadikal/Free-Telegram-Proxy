"""Optional bounded second-vantage MTProto spot check.

Default is OFFLINE dry-run. A live probe requires --live explicitly.
No GitHub credentials, no publishing, no secrets or addresses in the report.
Run by hand on an existing, trusted machine, not as a public self-hosted runner.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import ipaddress
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tgproxy.probe import probe
from tgproxy.secret import Secret, SecretError

MAX_PROXIES = 25
MAX_CONCURRENCY = 4
MAX_ROUNDS = 3


def load_candidates(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, list):
        raise ValueError("expected a proxies.json array")
    valid = []
    seen = set()
    for r in obj:
        if not isinstance(r, dict):
            continue
        try:
            addr = ipaddress.ip_address(r["ip"])
            port = r["port"]
            if not addr.is_global or type(port) is not int or not 1 <= port <= 65535:
                continue
            raw_secret = r["secret"]
            if not isinstance(raw_secret, str):
                continue
            secret = Secret.from_link(raw_secret)
            key = (str(addr), port)
            if key in seen:
                continue
            seen.add(key)
            valid.append({"ip": str(addr), "port": port, "secret": secret,
                          "asn": r.get("asn"), "type": getattr(secret, "kind", "unknown")})
        except (KeyError, ValueError, TypeError, SecretError):
            continue
    return valid


def select_diverse(candidates: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    """Stable pseudo-random order, distinct ASN first, no RTT-based sampling bias."""
    ordered = sorted(candidates, key=lambda r: hashlib.sha256(
        (r["ip"] + ":" + str(r["port"])).encode("ascii")).hexdigest())
    chosen, asns, selected = [], set(), set()
    for p in ordered:
        # Unknown ASNs are NOT one group: selecting one must not exclude others.
        asn = p.get("asn")
        if type(asn) is int and asn not in asns:
            chosen.append(p)
            selected.add((p["ip"], p["port"]))
            if type(asn) is int:
                asns.add(asn)
            if len(chosen) >= n:
                return chosen
    for p in ordered:
        if (p["ip"], p["port"]) not in selected:
            chosen.append(p)
            if len(chosen) >= n:
                break
    return chosen


async def spotcheck(sample: list[dict[str, Any]], *, rounds: int, timeout: float,
                    concurrency: int, prober=probe) -> dict[str, Any]:
    sem = asyncio.Semaphore(concurrency)

    async def one(p: dict[str, Any]):
        success = True
        latencies = []
        failed = None
        for _ in range(rounds):
            async with sem:
                # Fixed DC matches tgproxy.pipeline.Config.dc (2).
                response = await prober(p["ip"], p["port"], p["secret"], dc=2, timeout=timeout,
                                        connect_host=p["ip"])
            if not response.ok:
                success = False
                # Do not emit arbitrary exception or remote-controlled text.
                failed = response.level if response.level in {"none", "tcp", "tls", "dc"} else "unknown"
                break
            if response.rtt_ms is not None:
                latencies.append(response.rtt_ms)
        return success, failed, latencies

    results = await asyncio.gather(*(one(p) for p in sample))
    errors = Counter(level for ok, level, _ in results if not ok)
    latencies = [x for ok, _, xs in results if ok for x in xs]
    return {"probed": len(sample), "fully_verified": sum(ok for ok, _, _ in results),
            "rounds_required": rounds, "failure_levels": dict(errors),
            "rtt_median_ms": int(statistics.median(latencies)) if latencies else None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=Path("resilient/proxies.json"))
    ap.add_argument("--max-proxies", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=6.0)
    ap.add_argument("--live", action="store_true", help="actually make network connections (never default)")
    args = ap.parse_args(argv)
    if not (1 <= args.max_proxies <= MAX_PROXIES and 1 <= args.concurrency <= MAX_CONCURRENCY
            and 1 <= args.rounds <= MAX_ROUNDS and 2.0 <= args.timeout <= 10.0):
        ap.error("out of safety bounds: proxies<=25, concurrency<=4, rounds<=3, timeout 2..10")
    try:
        sample = select_diverse(load_candidates(args.source), args.max_proxies)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Cannot load candidate list: {type(exc).__name__}", file=sys.stderr)
        return 2
    if not sample:
        print("No valid public-IP proxy candidates", file=sys.stderr)
        return 2
    # No output file: prevents accidental version-controlled publication of sampled endpoints.
    result = {"mode": "live" if args.live else "dry-run", "candidate_count": len(sample),
              "sample_asns": len({p["asn"] for p in sample if type(p["asn"]) is int}),
              "origin": "operator-host (location not independently verified)",
              "note": "Only measures MTProto connectivity from the machine running this program; not Iranian/Russian ISP reachability."}
    if args.live:
        result["observed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result.update(asyncio.run(spotcheck(sample, rounds=args.rounds,
                                            timeout=args.timeout, concurrency=args.concurrency)))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
