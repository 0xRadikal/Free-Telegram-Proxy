"""Use TDLib's testProxy error messages as a secret-parsing oracle (port 1 on localhost: refused fast)."""
import json,time,os,sys,tdjson
tdjson.td_execute(json.dumps({"@type":"setLogVerbosityLevel","new_verbosity_level":0}).encode())
cid=tdjson.td_create_client_id(); N=[0]
def verdict(sec):
    N[0]+=1; e=str(N[0])
    tdjson.td_send(cid,json.dumps({"@type":"testProxy","@extra":e,"proxy":{"@type":"proxy","server":"127.0.0.1","port":1,"type":{"@type":"proxyTypeMtproto","secret":sec}},"dc_id":2,"timeout":2}).encode())
    t0=time.time()
    while time.time()-t0<6:
        r=tdjson.td_receive(0.5)
        if r:
            o=json.loads(r)
            if o.get('@extra')==e:
                m=o.get('message') or o['@type']
                return 'REJECT:'+m if ('ecret' in m) else 'ACCEPT'
    return 'LOST'
if __name__=='__main__':
    for s in sys.argv[1:]: print(repr(s), verdict(s), flush=True)
    sys.stdout.flush(); os._exit(0)
