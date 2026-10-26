"""Cross-run memory: per-proxy history and per-source yield.

Each run appends one bit per proxy (passed / failed). From that we derive
  uptime     share of the last N runs the proxy passed (only runs where it
             was tested count — a proxy we never saw is not "down")
  streak     consecutive passing runs up to now
  first_seen / last_ok timestamps

This is what lets the `stable/` tier exist: "has worked for most of the last
day" is a far stronger promise than "worked once, a minute ago".

The file is bounded: history is capped at HISTORY runs, and proxies not seen
for FORGET_AFTER seconds are dropped, so state.json cannot grow without limit.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

HISTORY = 96            # ≈ 1 day at a 15-minute cadence
FORGET_AFTER = 7 * 86400
VERSION = 1


def proxy_id(key: tuple) -> str:
    import hashlib
    server, port, raw = key
    return hashlib.sha256(f"{server}|{port}|".encode() + raw).hexdigest()[:12]


class State:
    def __init__(self, data: dict | None = None):
        d = data or {}
        if d.get("version") != VERSION:
            d = {}
        self.proxies: dict[str, dict] = d.get("proxies", {})
        self.sources: dict[str, dict] = d.get("sources", {})
        self.runs: int = d.get("runs", 0)

    @classmethod
    def load(cls, path: Path) -> "State":
        try:
            return cls(json.loads(path.read_text()))
        except (OSError, ValueError):
            return cls()

    # ------------------------------------------------------------ updates
    def record(self, pid: str, ok: bool, now: int, rtt: int | None) -> None:
        e = self.proxies.setdefault(pid, {"h": "", "first": now, "last_ok": None, "last_seen": now})
        e["h"] = (e["h"] + ("1" if ok else "0"))[-HISTORY:]
        e["last_seen"] = now
        if ok:
            e["last_ok"] = now
            if rtt is not None:
                e["rtt"] = rtt

    def record_source(self, sid: str, found: int, working: int, now: int) -> None:
        e = self.sources.setdefault(sid, {"found": [], "working": []})
        e["found"] = (e["found"] + [found])[-HISTORY:]
        e["working"] = (e["working"] + [working])[-HISTORY:]
        e["last"] = now

    def finish_run(self, now: int | None = None) -> None:
        now = now or int(time.time())
        self.runs += 1
        stale = [k for k, v in self.proxies.items() if now - v.get("last_seen", now) > FORGET_AFTER]
        for k in stale:
            del self.proxies[k]

    # ------------------------------------------------------------ queries
    def stats(self, pid: str) -> dict:
        e = self.proxies.get(pid)
        if not e or not e["h"]:
            return {"uptime": None, "checks": 0, "streak": 0, "first_seen": None}
        h = e["h"]
        streak = len(h) - len(h.rstrip("1"))
        return {
            "uptime": round(h.count("1") / len(h), 4),
            "checks": len(h),
            "streak": streak,
            "first_seen": e.get("first"),
        }

    def dump(self) -> dict:
        return {"version": VERSION, "runs": self.runs, "proxies": self.proxies, "sources": self.sources}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.dump(), separators=(",", ":"), sort_keys=True))
