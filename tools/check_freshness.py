"""Read-only, fail-closed health check for Free-Telegram-Proxy published metadata.

No networking, no git commands, and no file writes except optional GitHub step summary.
Run on a scheduled GitHub-hosted standard runner after checkout of `main`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CheckError(ValueError):
    """Invalid or unhealthy published metadata."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read valid JSON from {path}: {type(exc).__name__}") from exc
    if not isinstance(obj, dict):
        raise CheckError(f"{path} must contain a JSON object")
    return obj


def _positive_int(value: Any, name: str, *, allow_zero: bool = True) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1):
        raise CheckError(f"{name} must be a {'non-negative' if allow_zero else 'positive'} integer")
    return value


def _unix_timestamp(obj: dict[str, Any], name: str) -> int:
    value = obj.get("updated")
    if not isinstance(value, str):
        raise CheckError(f"{name}.updated missing or invalid")
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CheckError(f"{name}.updated is not an ISO8601 UTC timestamp") from exc
    return int(dt.timestamp())


def check(index: dict[str, Any], health: dict[str, Any], *, now: int,
          max_age_minutes: int = 65, min_verified: int = 20) -> dict[str, Any]:
    if max_age_minutes < 1 or min_verified < 0:
        raise CheckError("invalid configured thresholds")
    updated = _unix_timestamp(index, "index")
    health_updated = _unix_timestamp(health, "health")
    if updated != health_updated:
        raise CheckError("index.json and health.json update timestamps differ")
    indexed_unix = _positive_int(index.get("updated_unix"), "index.updated_unix", allow_zero=False)
    if indexed_unix != updated:
        raise CheckError("index.updated_unix does not match index.updated")
    age = now - updated
    if age < -300:
        raise CheckError("published timestamp is more than 5 minutes in the future")
    if age > max_age_minutes * 60:
        raise CheckError(f"stale publication: {age // 60} min old (maximum {max_age_minutes} min)")
    funnel = index.get("funnel")
    if not isinstance(funnel, dict) or not isinstance(health.get("funnel"), dict):
        raise CheckError("missing funnel data")
    # Cross-check only invariant fields, so future additional metrics are compatible.
    names = ("links_collected", "verified_links", "verified_servers", "verified_ips")
    fields = {k: _positive_int(funnel.get(k), f"index.funnel.{k}") for k in names}
    for k in names:
        if type(health["funnel"].get(k)) is not int or health["funnel"][k] != fields[k]:
            raise CheckError(f"health.funnel.{k} disagrees with index")
    if not (0 <= fields["verified_ips"] <= fields["verified_servers"] <= fields["verified_links"] <= fields["links_collected"]):
        raise CheckError("published proxy counts violate ordering invariants")
    if fields["verified_links"] < min_verified:
        raise CheckError(f"verified links fell below safety floor ({fields['verified_links']} < {min_verified})")
    tiers = index.get("tiers")
    if not isinstance(tiers, dict) or not isinstance(tiers.get("verified"), dict):
        raise CheckError("verified tier absent from index")
    if tiers["verified"].get("count") != fields["verified_links"]:
        raise CheckError("verified tier count does not match funnel")
    rounds = _positive_int(index.get("rounds"), "index.rounds", allow_zero=False)
    per_round = health.get("per_round_ok_targets")
    if not isinstance(per_round, list) or len(per_round) != rounds:
        raise CheckError("per-round health length does not match index.rounds")
    for i, value in enumerate(per_round):
        _positive_int(value, f"health.per_round_ok_targets[{i}]")
    # The runner is not required to be anywhere specific: no false claims about user ISPs.
    return {"updated": index["updated"], "age_minutes": round(max(0, age) / 60, 1),
            "verified_links": fields["verified_links"], "verified_servers": fields["verified_servers"],
            "verified_ips": fields["verified_ips"], "rounds": rounds,
            "runner": index.get("runner")}


def _summary(message: str) -> None:
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as stream:
            stream.write(message + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("index.json"))
    parser.add_argument("--health", type=Path, default=Path("health.json"))
    parser.add_argument("--max-age-minutes", type=int, default=65)
    parser.add_argument("--min-verified", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        result = check(_read_json(args.index), _read_json(args.health), now=int(time.time()),
                       max_age_minutes=args.max_age_minutes, min_verified=args.min_verified)
    except CheckError as exc:
        message = f"FAIL publication health: {exc}"
        print(message, file=sys.stderr)
        _summary("## Publication health: FAILED\n\n" + str(exc))
        return 1
    message = (f"OK publication health: updated={result['updated']} "
               f"age={result['age_minutes']}min links={result['verified_links']} "
               f"servers={result['verified_servers']} ips={result['verified_ips']}")
    print(message)
    _summary("## Publication health: OK\n\n" + message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
