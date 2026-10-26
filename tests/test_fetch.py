"""Fetching must return the complete body even when the server streams slowly.

Regression for a real bug: StreamReader.read(n) returns whatever is buffered,
so a single call truncated chunked upstream files in production.
"""
import asyncio

from aiohttp import web

from tgproxy.fetch import _get, read_capped
from tgproxy.sources import Source

LINK = "tg://proxy?server=h{i}.example&port=443&secret=dd00112233445566778899aabbccddeeff\n"
N = 300


async def _serve(handler):
    app = web.Application()
    app.router.add_get("/", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, f"http://127.0.0.1:{port}/"


async def _slow(req):
    resp = web.StreamResponse()
    await resp.prepare(req)
    for i in range(N):
        await resp.write(LINK.format(i=i).encode())
        if i % 20 == 0:
            await asyncio.sleep(0.02)
    await resp.write_eof()
    return resp


def test_slow_chunked_body_is_read_completely():
    async def go():
        import aiohttp
        runner, url = await _serve(_slow)
        try:
            async with aiohttp.ClientSession() as s:
                rep = await _get(s, Source("t", url))
        finally:
            await runner.cleanup()
        return rep
    rep = asyncio.run(go())
    assert rep.status == "ok" and rep.found == N, (rep.found, rep.error)


def test_cap_is_enforced():
    class Fake:
        def __init__(self):
            self.n = 0

        async def read(self, k):
            self.n += 1
            return b"x" * k if self.n < 100 else b""

    assert asyncio.run(read_capped(Fake(), 10 * 64 * 1024)) is None
