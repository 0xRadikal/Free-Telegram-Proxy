#!/usr/bin/env python3
"""Research prototype: end-to-end MTProxy prober.

Proof levels per proxy:
  tcp   TCP connect succeeded
  tls   (ee only) server's FakeTLS ServerHello HMAC verified with OUR secret
        -> proves the server knows the secret (not just any TLS server)
  dc    proxy relayed req_pq_multi to a real Telegram DC and returned resPQ
        echoing OUR random nonce -> proves a working Telegram path end-to-end

Reference: core.telegram.org/mtproto/mtproto-transports (obfuscation) and
alexbers/mtprotoproxy handle_fake_tls_handshake (server side of FakeTLS).
"""
import asyncio, base64, hashlib, hmac, os, re, struct, sys, time, json
import urllib.parse as up
from Crypto.Cipher import AES
from Crypto.Util import Counter


# ---------------------------------------------------------------- parsing
def parse_secret(s):
    s = up.unquote(s).strip()
    if re.fullmatch(r'[0-9a-fA-F]+', s) and len(s) % 2 == 0:
        return bytes.fromhex(s)
    t = s.replace('-', '+').replace('_', '/')
    t += '=' * (-len(t) % 4)
    return base64.b64decode(t, validate=True)


def classify(sec):
    if len(sec) == 16:
        return 'plain', sec, None
    if len(sec) == 17 and sec[0] == 0xdd:
        return 'dd', sec[1:17], None
    if len(sec) > 17 and sec[0] == 0xee:
        return 'ee', sec[1:17], sec[17:]  # raw bytes, as tdlib does
    raise ValueError('bad secret len=%d first=%02x' % (len(sec), sec[0] if sec else 0))


# ---------------------------------------------------------------- obfs2
def ctr(key, iv):
    return AES.new(key, AES.MODE_CTR,
                   counter=Counter.new(128, initial_value=int.from_bytes(iv, 'big')))


BAD_FIRST = {b'HEAD', b'POST', b'GET ', b'OPTI', b'PVrG', b'\x16\x03\x01\x02',
             b'\xdd\xdd\xdd\xdd', b'\xee\xee\xee\xee'}


def build_init(key16, proto_tag, dc):
    while True:
        init = bytearray(os.urandom(64))
        if init[0] == 0xef or bytes(init[:4]) in BAD_FIRST or init[4:8] == b'\0\0\0\0':
            continue
        break
    init[56:60] = proto_tag
    init[60:62] = struct.pack('<h', dc)
    rev = bytes(init[::-1])
    enc = ctr(hashlib.sha256(bytes(init[8:40]) + key16).digest(), bytes(init[40:56]))
    dec = ctr(hashlib.sha256(rev[8:40] + key16).digest(), rev[40:56])
    encrypted = enc.encrypt(bytes(init))
    return bytes(init[:56]) + encrypted[56:64], enc, dec


# ---------------------------------------------------------------- FakeTLS
def client_hello(key16, domain):
    """Build a ClientHello whose random field carries the MTProxy HMAC digest."""
    def ext(t, data):
        return struct.pack('>HH', t, len(data)) + data
    sni = domain if isinstance(domain, bytes) else domain.encode()
    exts = b''
    exts += ext(0x0000, struct.pack('>HBH', len(sni) + 3, 0, len(sni)) + sni)   # SNI
    exts += ext(0x000a, bytes.fromhex('0006001d00170018'))                      # groups
    exts += ext(0x000b, bytes.fromhex('0100'))                                  # ec point fmt
    exts += ext(0x000d, bytes.fromhex('000804030804040108070805'))              # sig algs
    exts += ext(0x0010, bytes.fromhex('000c02683208687474702f312e31'))          # ALPN h2,http/1.1
    exts += ext(0x002b, bytes.fromhex('0403040303'))                            # versions 1.3,1.2
    exts += ext(0x002d, bytes.fromhex('0101'))                                  # psk modes
    exts += ext(0x0033, struct.pack('>HHH', 36, 0x001d, 32) + os.urandom(32))   # key_share x25519
    ciphers = bytes.fromhex('130113021303c02bc02fc02cc030cca9cca8')
    body = b'\x03\x03' + b'\0' * 32 + b'\x20' + os.urandom(32)
    body += struct.pack('>H', len(ciphers)) + ciphers + b'\x01\x00'
    # padding extension so record payload >= 512 (server requires >=512)
    base_len = len(body) + 2 + len(exts) + 4
    pad = max(0, 517 - 4 - base_len - 4)
    exts += ext(0x0015, b'\0' * pad)
    body += struct.pack('>H', len(exts)) + exts
    hs = b'\x01' + len(body).to_bytes(3, 'big') + body
    rec = b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs
    digest = hmac.new(key16, rec, hashlib.sha256).digest()
    ts = struct.pack('<I', int(time.time()))
    digest = digest[:28] + bytes(a ^ b for a, b in zip(digest[28:], ts))
    return rec[:11] + digest + rec[43:], digest


async def read_tls_record(r):
    hdr = await r.readexactly(5)
    return hdr, await r.readexactly(struct.unpack('>H', hdr[3:5])[0])


# ---------------------------------------------------------------- MTProto
def req_pq_multi(nonce):
    body = struct.pack('<I', 0xbe7e8ef1) + nonce
    msg_id = (int(time.time() * 2**32) // 4) * 4
    return struct.pack('<qqi', 0, msg_id, len(body)) + body


# ---------------------------------------------------------------- probe
async def probe(host, port, secret_str, dc=2, timeout=8.0):
    res = {'host': host, 'port': port, 'level': 'none', 'err': None}
    try:
        kind, key16, domain = classify(parse_secret(secret_str))
    except Exception as e:
        res['err'] = 'secret:' + str(e)
        return res
    res['kind'] = kind
    res['domain'] = domain.decode('latin-1') if isinstance(domain, bytes) else domain
    t0 = time.monotonic()
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    except Exception as e:
        res['err'] = 'tcp:' + type(e).__name__
        return res
    res['level'] = 'tcp'
    res['tcp_ms'] = round((time.monotonic() - t0) * 1000)
    try:
        async def body():
            tls = kind == 'ee'
            if tls:
                hello, cdigest = client_hello(key16, domain)
                w.write(hello)
                await w.drain()
                h1, p1 = await read_tls_record(r)          # ServerHello
                if h1[0] != 0x16:
                    raise RuntimeError('tls:not-handshake %02x' % h1[0])
                h2, p2 = await read_tls_record(r)          # ChangeCipherSpec
                h3, p3 = await read_tls_record(r)          # first AppData (fake cert)
                resp = h1 + p1 + h2 + p2 + h3 + p3
                sdigest = resp[11:43]
                zeroed = resp[:11] + b'\0' * 32 + resp[43:]
                exp = hmac.new(key16, cdigest + zeroed, hashlib.sha256).digest()
                if not hmac.compare_digest(exp, sdigest):
                    raise RuntimeError('tls:hmac-mismatch')
                res['level'] = 'tls'
            tag = b'\xdd' * 4 if kind in ('dd', 'ee') else b'\xee' * 4
            init, enc, dec = build_init(key16, tag, dc)
            nonce = os.urandom(16)
            msg = req_pq_multi(nonce)
            pad = os.urandom(os.urandom(1)[0] % 16) if tag == b'\xdd' * 4 else b''
            frame = struct.pack('<I', len(msg) + len(pad)) + msg + pad
            payload = init + enc.encrypt(frame)
            if tls:
                w.write(b'\x14\x03\x03\x00\x01\x01' + b'\x17\x03\x03' + struct.pack('>H', len(payload)) + payload)
            else:
                w.write(payload)
            await w.drain()
            t1 = time.monotonic()
            buf = b''
            async def need(n):
                nonlocal buf
                while len(buf) < n:
                    if tls:
                        h, p = await read_tls_record(r)
                        if h[0] == 0x14:
                            continue
                        if h[0] != 0x17:
                            raise RuntimeError('tls:rec %02x' % h[0])
                        buf += dec.decrypt(p)
                    else:
                        chunk = await r.read(4096)
                        if not chunk:
                            raise RuntimeError('eof')
                        buf += dec.decrypt(chunk)
                out, buf = buf[:n], buf[n:]
                return out
            ln = struct.unpack('<I', await need(4))[0] & 0x7fffffff
            if ln < 4 or ln > 4096:
                raise RuntimeError('dc:bad-len %d' % ln)
            data = await need(ln)
            if len(data) == 4:
                raise RuntimeError('dc:transport-error %d' % struct.unpack('<i', data)[0])
            ctor = struct.unpack('<I', data[20:24])[0]
            if ctor != 0x05162463:
                raise RuntimeError('dc:unexpected-ctor %08x' % ctor)
            if data[24:40] != nonce:
                raise RuntimeError('dc:nonce-mismatch')
            res['level'] = 'dc'
            res['rtt_ms'] = round((time.monotonic() - t1) * 1000)
        await asyncio.wait_for(body(), timeout)
    except asyncio.TimeoutError:
        res['err'] = 'timeout@' + res['level']
    except asyncio.IncompleteReadError:
        res['err'] = 'eof@' + res['level']
    except Exception as e:
        res['err'] = str(e)[:80] + '@' + res['level']
    finally:
        w.close()
    return res


def parse_link(line):
    line = line.strip()
    if 'server=' not in line:
        return None
    q = up.parse_qs(up.urlparse(line.replace('tg://proxy', 'https://x/proxy')).query, keep_blank_values=True)
    try:
        return q['server'][0].rstrip('.'), int(q['port'][0]), q['secret'][0]
    except Exception:
        return None


async def main(paths, conc=200):
    seen, items = set(), []
    for p in paths:
        for l in open(p, errors='ignore'):
            t = parse_link(l)
            if t and t not in seen:
                seen.add(t)
                items.append(t)
    sem = asyncio.Semaphore(conc)
    async def one(t):
        async with sem:
            return await probe(*t)
    out = await asyncio.gather(*(one(t) for t in items))
    json.dump(out, open('probe_results.json', 'w'), indent=1)
    from collections import Counter
    print('total', len(out))
    print('levels', Counter(o['level'] for o in out))
    print('kind x level', Counter((o.get('kind'), o['level']) for o in out))
    print('errors', Counter(re.sub(r'[0-9a-f]{8}|\d+', 'N', o['err'] or '-') for o in out).most_common(15))


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
