"""Fail if generated outputs exceed the size budget.

Why: every published run replaces the output commit (rolling squash), but
GitHub still has to receive and store each push, and raw/jsDelivr serve every
file. A silent regression (e.g. re-adding links to JSON) could multiply size.
Budget is measured: a real run produced ~1.6 MiB raw after slimming.
"""
import os
import sys
import zlib

BUDGET_RAW = int(os.environ.get("SIZE_BUDGET_RAW", 4 * 1024 * 1024))
BUDGET_FILE = int(os.environ.get("SIZE_BUDGET_FILE", 1024 * 1024))


def main(root: str) -> int:
    total = ztotal = 0
    big = []
    for d, _, fs in os.walk(root):
        if "/." in d or d.startswith(os.path.join(root, ".")):
            continue
        for f in fs:
            p = os.path.join(d, f)
            b = open(p, "rb").read()
            total += len(b)
            ztotal += len(zlib.compress(b, 6))
            if len(b) > BUDGET_FILE:
                big.append((p, len(b)))
    print(f"outputs: {total/1024:.0f} KiB raw, {ztotal/1024:.0f} KiB compressed")
    ok = True
    if total > BUDGET_RAW:
        print(f"::error::outputs {total} B exceed budget {BUDGET_RAW} B")
        ok = False
    for p, n in big:
        print(f"::error::{p} is {n} B (> {BUDGET_FILE} B per-file budget)")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
