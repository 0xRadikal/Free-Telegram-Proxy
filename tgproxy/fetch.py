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


async def read_capped(stream: aiohttp.StreamReader, cap: int) -> bytes | None:
    """Read the whole body, or None if it exceeds `cap`.

    `StreamReader.read(n)` returns as soon as ANY data is buffered — it is not
    "read up to n". Using it once silently truncated chunked responses
    (measured: tgmtproxy 359/733 of 900 links, weltimistar 212/340 of 946 in
    published runs; reproduced with a local chunked server: 10 000 of 200 000
    bytes). Loop until EOF instead.
    """
    buf = bytearray()
    while True:
        chunk = await stream.read(64 * 1024)
        if not chunk:
            return bytes(buf)
        buf += chunk
        if len(buf) > cap:
            return None


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
                raw = await read_capped(r.content, MAX_BYTES)
                if raw is None:
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
