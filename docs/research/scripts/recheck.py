# NOTE: research script as run on 2026-10-26; paths refer to the research sandbox.
import json,sys,os,time,asyncio
sys.path.insert(0,'//webapp/Free-Telegram-Proxy')
import tdjson
from tgproxy.probe import probe
from tgproxy.secret import Secret
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id(); n=[0]
def td(h,p,s):
    n[0]+=1; e=str(n[0])
    tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":e,"proxy":{"@type":"proxy","server":h,"port":p,"type":{"@type":"proxyTypeMtproto","secret":s}},"dc_id":2,"timeout":12}).encode())
    t0=time.time()
    while time.time()-t0<18:
        x=tdjson.td_receive(0.5)
        if x:
            o=json.loads(x)
            if o.get('@extra')==e: return 'ok' if o['@type']=='ok' else (o.get('message') or '')[:25]
    return 'lost'
a={(r['server'],r['port']):r for r in json.load(open('//webapp/Free-Telegram-Proxy/_out/all/proxies.json'))}
bad=json.load(open('vfail.json'))
for h,p,t,_ in bad:
    r=a[(h,p)]
    T=[td(h,p,r['secret']) for _ in range(3)]
    M=[asyncio.run(probe(h,p,Secret.from_link(r['secret']),timeout=12)) for _ in range(3)]
    print(h[:30],p,t,'| tdlib',T,'| mine',[m.level for m in M],flush=True)
os._exit(0)
