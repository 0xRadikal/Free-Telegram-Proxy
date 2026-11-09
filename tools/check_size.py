"""Bound generated output size, with advance warnings and per-file diagnostics.

The original 4 MiB total / 1 MiB file limits were calibrated on ~1.6 MiB of
output. By 2026-11-08 a valid run reached 4,197,053 B and could not publish.
Use 8 MiB / 2 MiB for growth headroom; warn at 80% so the next capacity issue
is visible before publication stops. These are project budgets, not GitHub
service limits. Never truncate verified lists or discard history to fit.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zlib
from pathlib import Path


def _budget(name: str, default: int) -> int:
    value = int(os.environ.get(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be a positive number of bytes")
    return value


def measure(root: Path) -> list[dict]:
    if not root.is_dir():
        raise ValueError(f"output directory does not exist: {root}")
    files = []
    for directory, dirs, names in os.walk(root):
        # Ignore hidden children, not an absolute root's hidden ancestors
        # (e.g. a runner checkout under .cache or pytest's .pytest_tmp).
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(names):
            path = Path(directory) / name
            size = compressed = 0
            compressor = zlib.compressobj(6)
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    size += len(chunk)
                    compressed += len(compressor.compress(chunk))
            compressed += len(compressor.flush())
            files.append({"path": path.relative_to(root).as_posix(), "bytes": size,
                          "compressed_bytes": compressed})
    if not files or not sum(f["bytes"] for f in files):
        raise ValueError("output directory contains no non-empty files")
    return sorted(files, key=lambda f: (-f["bytes"], f["path"]))


def main(root: str, report: str | None = None) -> int:
    try:
        raw_limit = _budget("SIZE_BUDGET_RAW", 8 * 1024 * 1024)
        file_limit = _budget("SIZE_BUDGET_FILE", 2 * 1024 * 1024)
        files = measure(Path(root))
    except (OSError, ValueError) as exc:
        print(f"::error::{exc}")
        return 1
    total = sum(f["bytes"] for f in files)
    compressed = sum(f["compressed_bytes"] for f in files)
    errors, warnings = [], []
    if total > raw_limit:
        errors.append(f"outputs {total} B exceed budget {raw_limit} B")
    elif total * 5 >= raw_limit * 4:
        warnings.append(f"outputs use {total} / {raw_limit} B (at least 80% of budget)")
    for entry in files:
        name, size = entry["path"], entry["bytes"]
        if size > file_limit:
            errors.append(f"{name} is {size} B (> {file_limit} B per-file budget)")
        elif size * 5 >= file_limit * 4:
            warnings.append(f"{name} uses {size} / {file_limit} B (at least 80% of per-file budget)")
    data = {"total_bytes": total, "compressed_bytes": compressed,
            "budget_raw": raw_limit, "budget_file": file_limit, "files": files,
            "errors": errors, "warnings": warnings}
    print(f"outputs: {total} B raw ({total/1024:.0f} KiB), "
          f"{compressed} B compressed; budget {raw_limit} B")
    print("Largest generated files:")
    for entry in files[:10]:
        print(f"  {entry['bytes']:>10} B  {entry['path']}")
    for kind, messages in (("warning", warnings), ("error", errors)):
        for message in messages:
            print(f"::{kind}::{message}")
    if report:
        Path(report).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        lines = ["### Output size", "", f"{total:,} / {raw_limit:,} B raw; "
                 f"{compressed:,} B compressed. Per-file limit: {file_limit:,} B.", "",
                 "| Largest files | Bytes |", "|---|---:|"]
        lines.extend(f"| `{f['path']}` | {f['bytes']:,} |" for f in files[:10])
        lines.extend(["", *[f"- {message}" for message in errors + warnings], ""])
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--report", help="write a JSON size report outside the output directory")
    args = parser.parse_args()
    sys.exit(main(args.root, args.report))
