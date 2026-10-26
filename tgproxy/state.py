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


def _int(v) -> bool:
    return type(v) is int


def _valid_proxy(e) -> bool:
    return (isinstance(e, dict) and isinstance(e.get("h"), str) and set(e["h"]) <= {"0", "1"}
            and _int(e.get("first")) and _int(e.get("last_seen"))
            and (e.get("last_ok") is None or _int(e.get("last_ok"))))


def _valid_source(e) -> bool:
    return (isinstance(e, dict) and isinstance(e.get("found"), list) and isinstance(e.get("working"), list)
            and all(_int(x) for x in e["found"] + e["working"]))


class State:
    def __init__(self, data: dict | None = None):
        # state.json is published and read back every run; a corrupt or
        # hand-edited file must cost history, never the whole run. Invalid
        # entries are dropped one by one so good history survives.
        d = data if isinstance(data, dict) and data.get("version") == VERSION else {}
        proxies = d.get("proxies") if isinstance(d.get("proxies"), dict) else {}
        sources = d.get("sources") if isinstance(d.get("sources"), dict) else {}
        self.proxies: dict[str, dict] = {k: v for k, v in proxies.items() if _valid_proxy(v)}
        self.sources: dict[str, dict] = {k: v for k, v in sources.items() if _valid_source(v)}
        self.runs: int = d["runs"] if _int(d.get("runs")) and d["runs"] >= 0 else 0

    @classmethod
    def load(cls, path: Path) -> "State":
        try:
            return cls(json.loads(path.read_text()))
        except (OSError, ValueError):
            return cls()

    # ------------------------------------------------------------ updates
    def record(self, pid: str, ok: bool, now: int, rtt: int | None) -> None:
        # Size control: a proxy that has never passed gets no history entry
        # (measured: ~45% of collected links are dead; tracking them would
        # roughly double state.json for zero user value).
        if not ok and pid not in self.proxies:
            return
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
