# NOTE: research script as run on 2026-10-26; paths refer to the research sandbox.
"""Sample our VERIFIED set (and a NOT-verified sample) and ask real TDLib (sequential-ish, 8 at a time)."""
import json,sys,os,time,random
import tdjson
from collections import Counter
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id()
a=json.load(open('//webapp/Free-Telegram-Proxy/_out/all/proxies.json'))
rng=random.Random(11)
ver=[r for r in a if r['verified']]; nv=[r for r in a if not r['verified'] and r['level']!='none']
# sample per-IP to avoid hitting the one big operator 100 times
byip={}
for r in ver: byip.setdefault(r['ip'],r)
S=[('V',r) for r in rng.sample(list(byip.values()),120)]+[('N',r) for r in rng.sample(nv,60)]
def run(batch):
    for i,(t,r) in batch:
        tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":str(i),"proxy":{"@type":"proxy","server":r['server'],"port":r['port'],"type":{"@type":"proxyTypeMtproto","secret":r['secret']}},"dc_id":2,"timeout":12}).encode())
    out={}; t0=time.time()
    while len(out)<len(batch) and time.time()-t0<30:
        x=tdjson.td_receive(0.5)
        if x:
            o=json.loads(x); e=o.get('@extra')
            if isinstance(e,str) and e.isdigit(): out[int(e)]=o.get('message') or o['@type']
    return out
res={}
items=list(enumerate(S))
for k in range(0,len(items),8): res.update(run(items[k:k+8]))
m=Counter(); bad=[]
for i,(t,r) in enumerate(S):
    v=res.get(i,'lost'); m[(t,v=='ok')]+=1
    if t=='V' and v!='ok': bad.append((r['server'],r['port'],r['type'],v[:40]))
print('(ours, tdlib_ok):',dict(m),flush=True)
print('verified-but-tdlib-failed reasons',Counter(b[3] for b in bad),flush=True)
json.dump(bad,open('//webapp/tg-research/vfail.json','w'))
sys.stdout.flush(); os._exit(0)
