"""python -m tgproxy --out . [--rounds 3] [--gap 20]"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .pipeline import Config, run, runner_location
from .publish import write_outputs
from .readme import write_readmes
from .state import State


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tgproxy")
    ap.add_argument("--out", default=".")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--gap", type=float, default=20.0)
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--concurrency", type=int, default=300)
    ap.add_argument("--min-verified", type=int, default=20,
                    help="refuse to write outputs if fewer verified links (fail-closed)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    state = State.load(out / "state.json")
    cfg = Config(rounds=a.rounds, gap=a.gap, timeout=a.timeout, concurrency=a.concurrency)

    async def go():
        loc, res = await asyncio.gather(runner_location(), run(cfg, state))
        return loc, res

    loc, res = asyncio.run(go())
    n_ver = sum(r.verified for r in res.records)
    print(f"collected={len(res.records)} targets={res.targets} rounds_ok={res.per_round_ok} verified={n_ver} "
          f"timings={res.timings}", file=sys.stderr)
    if n_ver < a.min_verified:
        print(f"refusing to publish: only {n_ver} verified (< {a.min_verified}); previous outputs untouched",
              file=sys.stderr)
        return 2
    r = write_outputs(res, out, loc, state.dump())
    write_readmes(r["index"], Path(__file__).resolve().parent.parent, out)
    print(json.dumps(r["index"]["funnel"], indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
