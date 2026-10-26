import json,time,os,asyncio,sys,tdjson,probe
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id(); n=[0]
def tp(h,p,s,to=10):
    n[0]+=1; e=str(n[0])
    tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":e,"proxy":{"@type":"proxy","server":h,"port":p,"type":{"@type":"proxyTypeMtproto","secret":s}},"dc_id":2,"timeout":to}).encode())
    end=time.time()+to+5
    while time.time()<end:
        r=tdjson.td_receive(1.0)
        if r:
            o=json.loads(r)
            if o.get("@extra")==e: return 'ok' if o["@type"]=='ok' else (o.get("message") or '')[:30]
    return "lost"
want=['web-kook.mosbatbashim.info','Magic.godserver52.info','pub.ultra-fast.cc','tg1-ru3.chadvpn.shop','mt.wexproxy.com']
items={}
for f in ['soli.txt','dub.txt','tgm.txt','argh.txt','pink.txt']:
    for l in open(f,errors='ignore'):
        t=probe.parse_link(l)
        if t and t[0] in want: items[t]=1
for t in items:
    td=[tp(*t) for _ in range(3)]
    my=[asyncio.run(probe.probe(*t,timeout=10)) for _ in range(3)]
    print(t[0],t[1],repr(t[2][:40]),'| tdlib:',td,'| mine:',[(m['level'],m['err']) for m in my],flush=True)
os._exit(0)
