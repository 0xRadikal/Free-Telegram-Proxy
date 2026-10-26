import asyncio, json, time, re, sys, aiohttp, socket
import extract, probe
from collections import defaultdict, Counter
async def fetch(sess, url):
    t0=time.time()
    try:
        async with sess.get(url, timeout=aiohttp.ClientTimeout(total=25), headers={'User-Agent':'Mozilla/5.0'}) as r:
            body = await r.text(errors='ignore'); return r.status, body, round(time.time()-t0,1)
    except Exception as e: return type(e).__name__, '', 0
async def main():
    urls=[l.strip() for l in open('cand/gh_cands.txt') if l.strip()]+[l.strip() for l in open('cand/tg_channels.txt') if l.strip()]
    async with aiohttp.ClientSession() as s:
        res = await asyncio.gather(*(fetch(s,u) for u in urls))
    per = {}
    for u,(st,body,dt) in zip(urls,res):
        items=set()
        for h,p,sec in extract.extract(body):
            try: items.add((h.strip().rstrip('.').lower(), int(p), sec.strip()))
            except ValueError: pass
        per[u]={'status':st,'n':len(items),'items':items}
    allitems=set().union(*[v['items'] for v in per.values()])
    print('union', len(allitems), flush=True)
    sem=asyncio.Semaphore(250)
    async def one(t):
        async with sem: return t,(await probe.probe(*t,timeout=8))
    pr=dict(await asyncio.gather(*(one(t) for t in allitems)))
    ok={t for t,r in pr.items() if r['level']=='dc'}
    # resolve server identity
    loop=asyncio.get_event_loop()
    async def res(h):
        try: return h,(await loop.getaddrinfo(h,None,type=socket.SOCK_STREAM))[0][4][0]
        except Exception: return h,None
    R=dict(await asyncio.gather(*(res(h) for h in {t[0] for t in allitems})))
    ep=lambda t:(R.get(t[0]) or t[0], t[1])
    rows=[]
    for u,v in per.items():
        mine_ok={t for t in v['items'] if t in ok}
        others_ok=set().union(*[w['items'] for k,w in per.items() if k!=u]) & ok
        excl=mine_ok-others_ok
        excl_ep={ep(t) for t in excl} - {ep(t) for t in others_ok}
        rows.append((u.replace('https://raw.githubusercontent.com/','gh:').replace('https://t.me/s/','tg:'), v['status'], v['n'], len(mine_ok), len({ep(t) for t in mine_ok}), len(excl), len(excl_ep)))
    rows.sort(key=lambda r:-r[6])
    print(f"{'source':80} st   n   ok okEP exclOK exclEP")
    for r in rows: print(f"{r[0][:80]:80} {str(r[1]):4} {r[2]:4} {r[3]:4} {r[4]:4} {r[5]:5} {r[6]:5}")
    print('TOTAL ok links',len(ok),'ok endpoints',len({ep(t) for t in ok}))
    json.dump({'rows':rows,'ok':[list(t) for t in ok],'R':R},open('source_measure.json','w'))
asyncio.run(main())
