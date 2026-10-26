import json,time,os,random,asyncio,sys,tdjson,probe
from collections import Counter
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id()
def tp(i,h,p,s,to=10):
    tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":str(i),"proxy":{"@type":"proxy","server":h,"port":p,"type":{"@type":"proxyTypeMtproto","secret":s}},"dc_id":2,"timeout":to}).encode())
    end=time.time()+to+5
    while time.time()<end:
        r=tdjson.td_receive(1.0)
        if r:
            o=json.loads(r)
            if o.get("@extra")==str(i): return o["@type"],o.get("message")
    return "lost",None
items=[]
for f in ['soli.txt','dub.txt','tgm.txt','argh.txt','pink.txt']:
    for l in open(f,errors='ignore'):
        t=probe.parse_link(l)
        if t: items.append(t)
items=list(dict.fromkeys(items))
# include all non-dc ones from my probe + random dc ones
prev={(r['host'],r['port']):r['level'] for r in json.load(open('probe_results.json'))}
bad=[t for t in items if prev.get((t[0],t[1]))!='dc']
good=random.Random(7).sample([t for t in items if prev.get((t[0],t[1]))=='dc'],60)
sample=bad+good
async def mine(ts):
    return await asyncio.gather(*(probe.probe(*t,timeout=10) for t in ts))
m=Counter(); dis=[]
for i,t in enumerate(sample):
    a=tp(i,*t); b=asyncio.run(mine([t]))[0]
    k=(a[0]=='ok', b['level']=='dc'); m[k]+=1
    if k[0]!=k[1]: dis.append((t[0],t[1],t[2][:14],a,b['level'],b['err']))
print('sample',len(sample),'(non-dc',len(bad),'+ dc',len(good),')',flush=True)
print('matrix (tdlib_ok,mine_ok):',dict(m),flush=True)
for d in dis: print('DIS',d,flush=True)
sys.stdout.flush(); os._exit(0)
