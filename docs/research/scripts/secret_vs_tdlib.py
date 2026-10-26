# NOTE: research script as run on 2026-10-26; paths refer to the research sandbox.
"""Differential test: tgproxy.secret vs the real TDLib (tdjson) on corpus + edge cases.

Oracle trick: testProxy to 127.0.0.1:1. TDLib parses the secret first; a bad secret
returns an error mentioning 'secret', a good one proceeds to connect (refused/timeout).
All requests are sent at once (batched) so accepted secrets don't serialize on timeouts.
"""
import base64, json, os, random, sys, time
sys.path.insert(0, '//webapp/Free-Telegram-Proxy')
import tdjson
from tgproxy.secret import Secret, SecretError

tdjson.td_execute(json.dumps({"@type": "setLogVerbosityLevel", "new_verbosity_level": 0}).encode())
cid = tdjson.td_create_client_id()

rng = random.Random(42)
corpus = json.load(open('all_secrets.json'))
k = bytes(range(16))
edge = ['', 'a', 'ab' * 16, 'AB' * 16, 'ab' * 15, 'ab' * 16 + 'a', 'dd' + 'ab' * 16, 'dd' + 'ab' * 17, 'de' + 'ab' * 16,
        'ee' + 'ab' * 16, 'ee' + 'ab' * 16 + '61', 'ee' + 'ab' * 16 + '61' * 182, 'ee' + 'ab' * 16 + '61' * 183,
        'ef' + 'ab' * 16 + '61', 'ab' * 8 + ' ' + 'ab' * 7 + 'a', ' ' + 'ab' * 16, 'ab' * 16 + '\n',
        base64.b64encode(k).decode(), base64.b64encode(k).decode().rstrip('='),
        base64.urlsafe_b64encode(b'\xee' + k + b'x.com').decode(),
        base64.urlsafe_b64encode(b'\xee' + k + b'x.com').decode().rstrip('='),
        base64.b64encode(b'\xee' + k + b'x.com').decode(),
        base64.b64encode(b'\xdd' + k).decode(), base64.b64encode(b'\xdd' + k).decode().rstrip('='),
        base64.urlsafe_b64encode(b'\xdd' + k).decode().rstrip('='),
        'A' * 22, 'A' * 21, 'A' * 23, 'A' * 22 + '==', 'A' * 22 + '=', 'A' * 21 + 'B', 'A' * 20 + 'B=',
        'eeNEgYdJvXrFGRMCIMJdCQ', 'EERighJJvXrFGRMCIMjdCQ', '7nnnAQIAAQAH8AMDhuJMOt0=', 'AAAAAAAAAAAAAAAAAAAAAA==',
        base64.b64encode(b'\xee' + k + bytes([0xff, 0xfe]) + b'a.b').decode()]
encs = [lambda x: x.hex(), lambda x: base64.b64encode(x).decode(),
        lambda x: base64.urlsafe_b64encode(x).decode().rstrip('='),
        lambda x: base64.b64encode(x).decode().rstrip('='), lambda x: x.hex().upper()]
for _ in range(200):
    n = rng.choice([15, 16, 17, 18, 30, 60, 199, 200])
    b = bytes(rng.randrange(256) for _ in range(n))
    r = rng.random()
    if r < .4:
        b = b'\xee' + b[1:]
    elif r < .6:
        b = b'\xdd' + b[1:]
    edge.append(rng.choice(encs)(b))

allc = list(dict.fromkeys(corpus + edge))
for i, s in enumerate(allc):
    tdjson.td_send(cid, json.dumps({"@type": "testProxy", "@extra": "b%d" % i,
        "proxy": {"@type": "proxy", "server": "127.0.0.1", "port": 1,
                  "type": {"@type": "proxyTypeMtproto", "secret": s}},
        "dc_id": 2, "timeout": 1}).encode())
res = {}
t0 = time.time()
while len(res) < len(allc) and time.time() - t0 < 90:
    r = tdjson.td_receive(0.5)
    if r:
        o = json.loads(r)
        e = o.get('@extra', '')
        if isinstance(e, str) and e.startswith('b'):
            m = o.get('message') or o['@type']
            res[int(e[1:])] = ('REJECT', m) if 'ecret' in m else ('ACCEPT', m)
print('oracle answered', len(res), 'of', len(allc), flush=True)

mism = 0
tally = {}
for i, s in enumerate(allc):
    try:
        Secret.from_link(s)
        mine = 'ACCEPT'
    except SecretError:
        mine = 'REJECT'
    td = res.get(i, ('LOST', ''))
    tally[(mine, td[0])] = tally.get((mine, td[0]), 0) + 1
    if mine != td[0]:
        mism += 1
        print('MISMATCH', repr(s[:70]), 'mine', mine, 'tdlib', td, flush=True)
print('matrix (mine, tdlib):', tally, flush=True)
print('checked', len(allc), '(corpus', len(corpus), ') mismatches', mism, flush=True)
sys.stdout.flush()
os._exit(0)
