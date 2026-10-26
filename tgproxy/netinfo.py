"""DNS resolution, server identity, GeoIP country and ASN.

Why resolve at all: on 2026-10-26, 958 of 1394 working links from competing
lists pointed at ONE IPv4 address via hundreds of sub-domains. Counting links
inflates the list; counting (ip, port) tells you how many *servers* you have.

GeoIP: DB-IP Lite (country + ASN), CC-BY-4.0, monthly, no key required.
Attribution is printed in the README and on the dashboard as required.
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
from pathlib import Path

CACHE = Path(os.environ.get("TGPROXY_CACHE", ".cache"))


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def is_public(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return a.is_global


async def resolve_all(hosts, concurrency: int = 64, timeout: float = 6.0) -> dict[str, list[str]]:
    """host -> sorted unique IPv4 then IPv6 addresses ([] if NXDOMAIN/timeout)."""
    loop = asyncio.get_running_loop()
    sem = asyncio.Semaphore(concurrency)

    async def one(h: str):
        if is_ip(h):
            return h, [h]
        async with sem:
            try:
                infos = await asyncio.wait_for(loop.getaddrinfo(h, None, type=socket.SOCK_STREAM), timeout)
            except (OSError, asyncio.TimeoutError, UnicodeError):
                return h, []
        v4 = sorted({i[4][0] for i in infos if i[0] == socket.AF_INET})
        v6 = sorted({i[4][0] for i in infos if i[0] == socket.AF_INET6})
        return h, v4 + v6

    return dict(await asyncio.gather(*(one(h) for h in set(hosts))))


class Geo:
    """Thin wrapper; degrades to None lookups if the databases are missing."""

    def __init__(self, country_db: Path | None = None, asn_db: Path | None = None):
        self._c = self._a = None
        try:
            import maxminddb  # type: ignore
        except ImportError:  # pragma: no cover
            return
        c = country_db or CACHE / "dbip-country-lite.mmdb"
        a = asn_db or CACHE / "dbip-asn-lite.mmdb"
        if c.exists() and c.stat().st_size > 1_000_000:
            self._c = maxminddb.open_database(str(c))
        if a.exists() and a.stat().st_size > 1_000_000:
            self._a = maxminddb.open_database(str(a))

    @property
    def available(self) -> bool:
        return self._c is not None

    def country(self, ip: str | None) -> str | None:
        if not ip or self._c is None:
            return None
        rec = self._c.get(ip) or {}
        return (rec.get("country") or {}).get("iso_code")

    def asn(self, ip: str | None) -> tuple[int | None, str | None]:
        if not ip or self._a is None:
            return None, None
        rec = self._a.get(ip) or {}
        return rec.get("autonomous_system_number"), rec.get("autonomous_system_organization")


def flag(cc: str | None) -> str:
    if not cc or len(cc) != 2 or not cc.isalpha():
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc.upper())
