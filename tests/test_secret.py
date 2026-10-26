"""Secret parsing must match TDLib exactly.

Two layers:
 1. hand-written cases from the C++ source (always run)
 2. differential test against the real TDLib binary via `tdjson`
    on the corpus of every secret we ever collected (runs if tdjson installed)
"""
import base64
import json
import random
import time
from pathlib import Path

import pytest

from tgproxy.secret import MAX_DOMAIN_LENGTH, Secret, SecretError

K = bytes(range(16))
CORPUS = json.loads((Path(__file__).parent / "fixtures" / "secrets_corpus.json").read_text())


@pytest.mark.parametrize("enc,kind,n", [
    (K.hex(), "classic", 16),
    (K.hex().upper(), "classic", 16),
    ("dd" + K.hex(), "secure", 17),
    ("ee" + K.hex() + "61", "faketls", 18),
    ("ee" + K.hex() + "61" * MAX_DOMAIN_LENGTH, "faketls", 17 + MAX_DOMAIN_LENGTH),
    (base64.b64encode(K).decode(), "classic", 16),
    (base64.urlsafe_b64encode(b"\xee" + K + b"x.com").decode().rstrip("="), "faketls", 22),
    (base64.b64encode(b"\xdd" + K).decode(), "secure", 17),
    # a 22-char base64 of a 16-byte key that *starts with* "ee" — parsed as base64url → classic
    ("eeNEgYdJvXrFGRMCIMJdCQ", "classic", 16),
])
def test_accepts(enc, kind, n):
    s = Secret.from_link(enc)
    assert s.kind == kind and len(s.raw) == n


@pytest.mark.parametrize("enc,msg", [
    ("", "Wrong proxy secret"),
    ("ab" * 15, "Wrong proxy secret"),                      # 15 bytes
    ("ee" + K.hex(), "Unsupported proxy secret"),           # 17 bytes but 0xee
    ("de" + K.hex(), "Unsupported proxy secret"),
    ("ee" + K.hex() + "61" * (MAX_DOMAIN_LENGTH + 1), "Wrong proxy secret"),  # too long → all decoders fail? no: hex ok, then too long
    (" " + K.hex(), "Wrong proxy secret"),
    (K.hex() + "\n", "Wrong proxy secret"),
    ("A" * 21, "Wrong proxy secret"),
    ("7nnnAQIAAQAH8AMDhuJMOt0=", "Unsupported proxy secret"),
])
def test_rejects(enc, msg):
    with pytest.raises(SecretError):
        Secret.from_link(enc)


def test_too_long_message_matches_tdlib():
    with pytest.raises(SecretError, match="Too long secret"):
        Secret.from_link("ee" + K.hex() + "61" * (MAX_DOMAIN_LENGTH + 1))


def test_domain_is_raw_bytes_not_ascii():
    # Real proxies use non-ASCII bytes before the SNI (seen in the wild, TDLib accepts them)
    s = Secret.from_link("ee" + K.hex() + "16" + "www.cloudflare.com".encode().hex())
    assert s.domain == b"\x16www.cloudflare.com"
    assert s.domain_text is None  # not printable → hidden from humans, still probed


def test_hex_roundtrip_is_canonical():
    for enc in CORPUS:
        try:
            s = Secret.from_link(enc)
        except SecretError:
            continue
        assert Secret.from_link(s.hex()) == s
        assert Secret.from_link(s.encoded()) == s


tdjson = pytest.importorskip("tdjson", reason="differential test needs the real TDLib")


def _tdlib_verdicts(secrets):
    tdjson.td_execute(json.dumps({"@type": "setLogVerbosityLevel", "new_verbosity_level": 0}).encode())
    cid = tdjson.td_create_client_id()
    for i, s in enumerate(secrets):
        tdjson.td_send(cid, json.dumps({
            "@type": "testProxy", "@extra": f"s{i}", "dc_id": 2, "timeout": 1,
            "proxy": {"@type": "proxy", "server": "127.0.0.1", "port": 1,
                      "type": {"@type": "proxyTypeMtproto", "secret": s}}}).encode())
    out, t0 = {}, time.time()
    while len(out) < len(secrets) and time.time() - t0 < 90:
        r = tdjson.td_receive(0.5)
        if r:
            o = json.loads(r)
            e = o.get("@extra")
            if isinstance(e, str) and e.startswith("s"):
                m = o.get("message") or o["@type"]
                out[int(e[1:])] = "ecret" not in m  # TDLib's parse errors all mention "secret"
    return out


def test_differential_against_tdlib():
    rng = random.Random(1)
    extra = []
    for _ in range(200):
        b = bytes(rng.randrange(256) for _ in range(rng.choice([15, 16, 17, 18, 40, 199, 200])))
        b = rng.choice([b, b"\xee" + b[1:], b"\xdd" + b[1:]])
        extra.append(rng.choice([b.hex(), base64.b64encode(b).decode(),
                                 base64.urlsafe_b64encode(b).decode().rstrip("=")]))
    cases = list(dict.fromkeys(CORPUS + extra))
    td = _tdlib_verdicts(cases)
    assert len(td) == len(cases), "TDLib did not answer every request"
    mismatches = []
    for i, s in enumerate(cases):
        try:
            Secret.from_link(s)
            mine = True
        except SecretError:
            mine = False
        if mine != td[i]:
            mismatches.append((s, mine, td[i]))
    assert not mismatches, mismatches[:10]
