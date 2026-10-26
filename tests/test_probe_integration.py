"""The prober is only trustworthy if it says YES to real proxies and NO to everything else.

Positive: the pinned reference MTProxy server (alexbers/mtprotoproxy @bd5b03c)
in all three secret modes. Negative: wrong secrets, a masking server that
forwards strangers to google.com, closed ports, and real TLS/HTTP servers.
"""
import asyncio

import pytest

from conftest import REF_SECRET
from tgproxy.probe import probe
from tgproxy.secret import Secret

DOMAIN = "www.google.com".encode().hex()
WRONG = "f" * 32


def run(*a, **k):
    return asyncio.run(probe(*a, **k))


@pytest.mark.parametrize("enc", [REF_SECRET, "dd" + REF_SECRET, "ee" + REF_SECRET + DOMAIN])
def test_reference_server_passes_every_mode(refserver, enc):
    r = run("127.0.0.1", refserver, Secret.from_link(enc), timeout=15)
    assert r.level == "dc", r
    assert r.rtt_ms is not None and r.error is None


@pytest.mark.parametrize("enc", [WRONG, "dd" + WRONG, "ee" + WRONG + DOMAIN])
def test_wrong_secret_never_passes(refserver, enc):
    r = run("127.0.0.1", refserver, Secret.from_link(enc), timeout=6)
    assert r.level != "dc", r


@pytest.mark.parametrize("dc", [1, 2, 3, 4, 5])
def test_all_production_dcs(refserver, dc):
    r = run("127.0.0.1", refserver, Secret.from_link("dd" + REF_SECRET), dc=dc, timeout=15)
    assert r.ok, (dc, r)


def test_one_bit_flip_in_secret_fails(refserver):
    raw = bytearray(bytes.fromhex("dd" + REF_SECRET))
    raw[5] ^= 1
    r = run("127.0.0.1", refserver, Secret.from_binary(bytes(raw)), timeout=6)
    assert not r.ok


def test_masking_server_with_wrong_secret_is_rejected(refserver_masked):
    good = run("127.0.0.1", refserver_masked, Secret.from_link("ee" + REF_SECRET + DOMAIN), timeout=15)
    assert good.ok, good
    bad = run("127.0.0.1", refserver_masked, Secret.from_link("ee" + WRONG + DOMAIN), timeout=8)
    assert not bad.ok and bad.error and bad.error.startswith("tls:"), bad


def test_closed_port():
    r = run("127.0.0.1", 1, Secret.from_link(REF_SECRET), timeout=3)
    assert r.level == "none" and r.error.startswith("tcp:")


@pytest.mark.parametrize("host,enc", [
    ("www.google.com", "ee" + "ab" * 16 + DOMAIN),
    ("1.1.1.1", "dd" + "ab" * 16),
    ("github.com", "ab" * 16),
])
def test_real_internet_servers_are_not_proxies(telegram_online, host, enc):
    r = run(host, 443, Secret.from_link(enc), timeout=6)
    assert not r.ok, r
