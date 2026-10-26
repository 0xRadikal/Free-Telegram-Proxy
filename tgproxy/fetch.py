"""Concurrent source fetching with per-source health accounting."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import aiohttp

from .links import Proxy, extract
from .sources import Source

UA = "Mozilla/5.0 (X11; Linux x86_64) Free-Telegram-Proxy (+https://github.com/0xRadikal/Free-Telegram-Proxy)"
MAX_BYTES = 8 * 1024 * 1024


@dataclass
class SourceReport:
    id: str
    url: str
    kind: str
    status: str = "fail"  # ok | empty | fail
    http: int | None = None
    attempts: int = 0
    ms: int | None = None
    found: int = 0
    error: str | None = None
    proxies: list = field(default_factory=list, repr=False)

    def public(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "proxies"}
        return d


async def _get(session: aiohttp.ClientSession, src: Source, retries: int = 3) -> SourceReport:
    rep = SourceReport(src.id, src.url, src.kind)
    t0 = time.monotonic()
    for attempt in range(1, retries + 1):
        rep.attempts = attempt
        try:
            async with session.get(src.url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                rep.http = r.status
                if 400 <= r.status < 500:  # dead URL: report, do not hammer
                    rep.error = f"HTTP {r.status}"
                    break
                if r.status != 200:
                    raise aiohttp.ClientResponseError(r.request_info, (), status=r.status)
                raw = await r.content.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    rep.error = "too large"
                    break
                text = raw.decode("utf-8", "replace")
                found = extract(text)
                rep.proxies = [Proxy(p.server, p.port, p.secret, frozenset({src.id})) for p in found]
                rep.found = len({p.key for p in rep.proxies})
                rep.status = "ok" if rep.found else "empty"
                rep.error = None
                break
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            rep.error = type(e).__name__
            await asyncio.sleep(1.5 * attempt)
    rep.ms = round((time.monotonic() - t0) * 1000)
    return rep


async def fetch_all(sources: tuple[Source, ...] | list[Source]) -> list[SourceReport]:
    conn = aiohttp.TCPConnector(limit=16)
    async with aiohttp.ClientSession(connector=conn, headers={"User-Agent": UA}) as s:
        return list(await asyncio.gather(*(_get(s, src) for src in sources)))


def merge(reports: list[SourceReport]) -> dict[tuple, Proxy]:
    """Union by identity; remember every source that listed each proxy."""
    out: dict[tuple, Proxy] = {}
    for rep in reports:
        for p in rep.proxies:
            cur = out.get(p.key)
            out[p.key] = p if cur is None else Proxy(cur.server, cur.port, cur.secret, cur.sources | p.sources)
    return out
