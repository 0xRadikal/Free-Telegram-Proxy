"""Validate generated outputs before they are published (fail-closed).

Checks:
  * every line of every tg.txt / tme.txt re-parses with the TDLib-exact parser
  * tg.txt and tme.txt of a tier describe the same proxies in the same order
  * proxies.json rows match tg.txt (same identity, same order)
  * no tier file is empty; index.json advertises exactly the files that exist
  * resilient/fast/... contain at most one link per IP
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tgproxy.links import parse_link  # noqa: E402

PER_IP_TIERS = ("resilient", "fast", "stable", "faketls", "secure", "classic")


def fail(msg):
    print(f"::error::{msg}")
    return 1


def main(root: Path) -> int:
    errors = 0
    idx = json.loads((root / "index.json").read_text())
    for name, meta in idx["tiers"].items():
        d = root / name
        keys = {}
        for fname in meta["files"]:
            p = d / fname
            if not p.exists() or p.stat().st_size == 0:
                errors += fail(f"{name}/{fname} advertised but missing/empty")
                continue
            if fname.endswith(".txt"):
                lines = p.read_text().splitlines()
                parsed = [parse_link(x) for x in lines]
                bad = [x for x, y in zip(lines, parsed) if y is None]
                if bad:
                    errors += fail(f"{name}/{fname}: {len(bad)} unparsable lines, e.g. {bad[0][:80]}")
                keys[fname] = [y.key for y in parsed if y]
            else:
                rows = json.loads(p.read_text())
                keys[fname] = [parse_link(f"tg://proxy?server={r['server']}&port={r['port']}&secret={r['secret']}").key
                               for r in rows]
                if len(rows) != meta["count"]:
                    errors += fail(f"{name}/proxies.json has {len(rows)} rows, index says {meta['count']}")
                if name in PER_IP_TIERS:
                    dup = [ip for ip, n in Counter(r["ip"] for r in rows).items() if n > 1]
                    if dup:
                        errors += fail(f"{name}: {len(dup)} IPs appear more than once")
        vals = list(keys.values())
        if any(v != vals[0] for v in vals[1:]):
            errors += fail(f"{name}: files disagree on content/order")
        extra = {f.name for f in d.iterdir()} - set(meta["files"])
        if extra:
            errors += fail(f"{name}: unadvertised files {sorted(extra)}")
    for cc, meta in idx.get("countries", {}).items():
        p = root / "countries" / f"{cc}.txt"
        if not p.exists() or len(p.read_text().splitlines()) != meta["count"]:
            errors += fail(f"countries/{cc}.txt missing or count mismatch")
    print("outputs valid" if not errors else f"{errors} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
