# NOTE: research script as run on 2026-10-26; paths refer to the research sandbox.
import json,sys,os,time,asyncio,random
sys.path.insert(0,'//webapp/Free-Telegram-Proxy')
import tdjson
from tgproxy.probe import probe
from tgproxy.secret import Secret
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id()
a=json.load(open('//webapp/Free-Telegram-Proxy/_out/all/proxies.json'))
# re-probe faketls entries that failed at tcp level, classify with my prober now, then ask TDLib
cands=[r for r in a if r['type']=='faketls' and r['level']=='tcp']
random.Random(3).shuffle(cands)
async def mine(rs): return await asyncio.gather(*(probe(r['server'],r['port'],Secret.from_link(r['secret']),timeout=8) for r in rs))
M=asyncio.run(mine(cands))
bh=[(r,m) for r,m in zip(cands,M) if (m.error or '').startswith('tls:bad-hello')][:40]
print('faketls tcp-level',len(cands),'currently bad-hello',sum((m.error or '').startswith('tls:bad-hello') for m in M),flush=True)
for i,(r,m) in enumerate(bh):
    tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":str(i),"proxy":{"@type":"proxy","server":r['server'],"port":r['port'],"type":{"@type":"proxyTypeMtproto","secret":r['secret']}},"dc_id":2,"timeout":10}).encode())
res={}; t0=time.time()
while len(res)<len(bh) and time.time()-t0<40:
    x=tdjson.td_receive(0.5)
    if x:
        o=json.loads(x)
        if '@extra' in o and o['@extra'].isdigit(): res[int(o['@extra'])]=o.get('message') or o['@type']
from collections import Counter
print('TDLib verdicts on my bad-hello set:',Counter(v[:45] for v in res.values()),flush=True)
for i,v in res.items():
    if v=='ok': print('TDLIB OK BUT MINE bad-hello:',bh[i][0]['server'],bh[i][0]['port'],flush=True)
sys.stdout.flush(); os._exit(0)
