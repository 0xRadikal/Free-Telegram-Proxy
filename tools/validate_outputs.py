"""Validate generated outputs before they are published (fail-closed).

Checks:
  * every line of every tg.txt / tme.txt re-parses with the TDLib-exact parser
  * tg.txt and tme.txt of a tier describe the same proxies in the same order
  * proxies.json rows match tg.txt (same identity, same order)
  * no tier file is empty; index.json advertises exactly the files that exist
  * resilient/fast/... contain at most one link per IP
  * top100.txt: subset of resilient, no repeated link/IP, at most
    top100_info.network_cap links per network; top50.txt = its first 50 lines
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from types import SimpleNamespace  # noqa: E402

from tgproxy.links import from_args, parse_link  # noqa: E402
from tgproxy.publish import TOP_ALIAS_N, network_of  # noqa: E402

PER_IP_TIERS = ("resilient", "fast", "stable", "faketls", "secure", "classic")


def row_key(r: dict):
    """Identity of a proxies.json row, validated with the same rules as links
    (built from fields, so no URL escaping is involved)."""
    p = from_args(r.get("server"), r.get("port"), r.get("secret"))
    return p.key if p else None


def fail(msg):
    print(f"::error::{msg}")
    return 1


def _top_lines(root: Path, name: str, advertised) -> tuple[int, list | None]:
    """Parse a top-level list file; checks advertised <-> exists."""
    p = root / name
    if not advertised:
        return (fail(f"{name} exists but index.json says it is null"), None) if p.exists() else (0, None)
    if not p.exists() or p.stat().st_size == 0:
        return fail(f"{name} advertised but missing/empty"), None
    lines = p.read_text().splitlines()
    parsed = [parse_link(x) for x in lines]
    if any(x is None for x in parsed):
        return fail(f"{name}: {sum(x is None for x in parsed)} unparsable lines"), None
    return 0, [x.key for x in parsed]


def check_top(root: Path, idx: dict) -> int:
    """top100.txt is what most users subscribe to; top50.txt is its prefix."""
    errors = 0
    e100, k100 = _top_lines(root, "top100.txt", idx.get("top100"))
    e50, k50 = _top_lines(root, "top50.txt", idx.get("top50"))
    errors += e100 + e50
    if bool(idx.get("top100")) != bool(idx.get("top50")):
        errors += fail("index.json: top100 and top50 must be both set or both null")
    if k100 is None:
        return errors
    res_rows = {}
    rp = root / "resilient" / "proxies.json"
    if rp.exists():
        for r in json.loads(rp.read_text()):
            res_rows[row_key(r)] = r
    if any(k not in res_rows for k in k100):
        errors += fail("top100.txt contains links that are not in resilient/")
    rows = [res_rows[k] for k in k100 if k in res_rows]
    ips = [r.get("ip") for r in rows]
    if len(ips) != len(set(ips)) or len(k100) != len(set(k100)):
        errors += fail("top100.txt repeats a link or an IP")
    info = idx.get("top100_info") or {}
    if info.get("count") != len(k100):
        errors += fail(f"top100.txt has {len(k100)} lines, top100_info.count says {info.get('count')}")
    cap = info.get("network_cap")
    nets = Counter(network_of(SimpleNamespace(asn=r.get("asn"), ip=r.get("ip"))) for r in rows)
    if not isinstance(cap, int) or cap < (info.get("base_network_cap") or 0):
        errors += fail(f"top100_info.network_cap is invalid: {cap!r}")
    elif nets and max(nets.values()) > cap:
        net, n = nets.most_common(1)[0]
        errors += fail(f"top100.txt: network {net} has {n} links, above network_cap {cap}")
    if info.get("networks") != len(nets):
        errors += fail(f"top100_info.networks says {info.get('networks')}, file has {len(nets)}")
    if k50 is not None and k50 != k100[:TOP_ALIAS_N]:
        errors += fail(f"top50.txt is not the first {TOP_ALIAS_N} lines of top100.txt")
    return errors


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
                keys[fname] = [row_key(r) for r in rows]
                if None in keys[fname]:
                    errors += fail(f"{name}/proxies.json: {keys[fname].count(None)} invalid rows")
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
    errors += check_top(root, idx)

    for cc, meta in idx.get("countries", {}).items():
        p = root / "countries" / f"{cc}.txt"
        if not p.exists() or len(p.read_text().splitlines()) != meta["count"]:
            errors += fail(f"countries/{cc}.txt missing or count mismatch")
    print("outputs valid" if not errors else f"{errors} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
