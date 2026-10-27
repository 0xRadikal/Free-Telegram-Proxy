<div align="center">

# Free Telegram Proxy List — verified MTProto proxies

**Every proxy here relayed a real request to a real Telegram datacenter — three times — before it was published.**

[![update](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml/badge.svg)](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml)
[![verified links](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_links&label=verified%20links&color=2ea44f)](verified/tg.txt)
[![servers](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_servers&label=real%20servers&color=0088cc)](resilient/tg.txt)
[![collected](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.links_collected&label=links%20collected&color=lightgrey)](health.json)
[![stars](https://img.shields.io/github/stars/0xRadikal/Free-Telegram-Proxy?style=flat)](https://github.com/0xRadikal/Free-Telegram-Proxy)

[فارسی](README_FA.md) · [Русский](README_RU.md) · [Live dashboard](https://0xradikal.github.io/Free-Telegram-Proxy/) · [Discussions](https://github.com/0xRadikal/Free-Telegram-Proxy/discussions) · [Telegram @Raydikalx](https://t.me/Raydikalx)

</div>

A free, open-source **Telegram proxy list**: working **MTProto / MTProxy** proxies (FakeTLS `ee`, secure `dd` and classic), rebuilt about every 15 minutes on GitHub Actions. Tap a link and Telegram connects — no app, no signup. Made for people whose Telegram is blocked or slow — in Iran, Russia, China and other censored networks. Works with Telegram on Android, iPhone and Desktop. Not affiliated with Telegram.

## Start here — one line

100 links, built not to fail together: **one proxy per real server**, **at most 5 per network** (ASN), ranked by **proven uptime** across past checks, then speed.

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top100.txt
```

On a phone, just tap any line in that file — Telegram opens and asks *Connect proxy?*.

The 5-per-network cap is raised only when the list could not be filled otherwise — too few networks, or a proven proxy would be pushed out by an unproven newcomer. The cap actually used is published as `top100_info.network_cap` in `index.json`. Already subscribed to `top50.txt`? It still works: it is the first 50 lines of `top100.txt`.

## How to use a free Telegram proxy

### Android and iPhone (iOS)

1. Open [`top100.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top100.txt) (or [`resilient/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/resilient/tme.txt)) on your phone.
2. Tap any line. Telegram opens and asks **Connect proxy?** — tap **Connect**.
3. Not connecting? Try the next line: censors block some proxies and not others.

To add an MTProto proxy by hand: **Settings → Data and Storage → Proxy → Add Proxy → MTProto**, then paste the server, port and secret.

### Telegram Desktop (Windows, macOS, Linux)

Click a `tg://proxy` or `https://t.me/proxy` link, or open **Settings → Advanced → Connection type → Use custom proxy → Add proxy → MTProto**.

### Pick by type or by server location

* **FakeTLS (`ee`) only** — looks like normal HTTPS, often the hardest to block: [`faketls/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/faketls/tme.txt)
* **Fastest from the test runner**: [`fast/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/fast/tme.txt)
* **By server country** — e.g. [Germany](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt), [Netherlands](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt), [Russia](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt), [Iran](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt). This is where the proxy server is, **not** where it works from; the full list is in [`countries/`](countries).

## Live numbers

<!-- LIVE:BEGIN -->
**Last update:** `2026-10-27T12:07:28Z` · tested from `US` (Cloudflare colo `LAX`)

| Stage | Count |
|---|---:|
| links collected from all sources | 3,190 |
| unique servers (IP:port) probed | 1,796 |
| **verified in all 3 rounds** (links) | **1,784** |
| the same, counted as **real servers** | **392** (361 IPs) |
| largest single IP's share of verified links | 985 (55.2%) |
| largest network's (`79.182.27.0/24`) share of verified links | 985 (55.2%) |

`resilient` 361 · `fast` 92 · `stable` 331 · `verified` 1784 · `faketls` 117 · `secure` 91 · `classic` 159 · `all` 3190

[🇩🇪 DE 109](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt) [🇮🇷 IR 97](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt) [🇫🇮 FI 61](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FI.txt) [🇳🇱 NL 29](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt) [🇷🇺 RU 17](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt) [🇺🇸 US 13](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/US.txt) [🇵🇱 PL 8](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/PL.txt) [🇫🇷 FR 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FR.txt) [🇸🇪 SE 4](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SE.txt) [🇨🇭 CH 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/CH.txt) [🇬🇧 GB 2](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/GB.txt) [🇱🇺 LU 2](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/LU.txt)
<!-- LIVE:END -->

## Why this list is different

Most proxy lists publish a big number. We measured what that number is made of.

| | typical list | this repository |
|---|---|---|
| **What "working" means** | port open, or "handshake" | proxy relayed `req_pq_multi` to a Telegram DC and the DC answered with **our random nonce** |
| **How many times** | once | **every round** (3 by default) — flaky proxies are excluded, not hidden |
| **What is counted** | links | links **and real servers** (DNS-resolved `IP:port`) |
| **One operator, many names** | listed hundreds of times | `resilient/` keeps **one link per IP** |
| **Secret parsing** | regex | a port of TDLib's own parser, **differentially tested against the real TDLib binary** |
| **History** | none | per-proxy uptime over the last ~96 checks (`stable/`) |
| **Why something was dropped** | silent | every rejection has a reason in `health.json` |

### The finding that shaped this project

On 2026-10-26 we merged seven popular lists and resolved every hostname. **958 of 1,394 working links pointed to one single IP address** through hundreds of sub-domains. If that one server goes down, most of those lists die at once. That is why the default here is `resilient/` and why every number above is reported twice — as links and as servers.

## Tiers

| Tier | What gets in |
|---|---|
| **`top100.txt`** | 100 from `resilient` · proven proxies first (the `stable` bar) · ranked by proven uptime, then RTT · **≤ 5 per network**, raised only if needed — *recommended*; `top50.txt` = its first 50 |
| **`resilient/`** | verified · **one link per server IP** (the link with the longest check history is kept, so your saved link does not change between runs) — every real server |
| `fast/` | the fastest 25 % of `resilient`, by round-trip through the proxy *from the test runner* |
| `stable/` | resilient · passed ≥ 90 % of its last checks (appears after ~3 hours of history) |
| `verified/` | passed the full end-to-end test in **every** round |
| `faketls/` · `secure/` · `classic/` | verified, split by secret type (`ee` · `dd` · 16-byte) |
| `countries/XX.txt` | verified, by server location (DB-IP) |
| `all/` | everything collected, including dead ones — for researchers |

Each tier folder contains `tg.txt` (`tg://` links), `tme.txt` (`https://t.me/proxy` links) and `proxies.json` (server, port, secret, type, country, ASN, RTT, uptime, sources). `all/` has `tg.txt` only. A tier that is empty in a run is **removed**, never published empty.

`verified/` lists every working link, including the many aliases of the same server. Every other tier keeps **one link per server IP** — more links to the same machine add size, not reliability.

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/resilient/tme.txt
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/fast/tme.txt
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/verified/proxies.json
```

If `raw.githubusercontent.com` is blocked, use the same path on jsDelivr — e.g. `https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main/top100.txt` (the update job purges jsDelivr after every run; without a purge it may cache up to 12 h. raw caches 5 min).

## How a proxy is tested

```
collect  →  parse (TDLib rules)  →  resolve DNS  →  dedup by IP:port:secret
        →  TCP  →  FakeTLS HMAC (ee only)  →  obfuscated2 + req_pq_multi  →  resPQ with our nonce
        →  ×3 rounds  →  history  →  tiers
```

* **Hostnames with several IPs** (round-robin DNS): a Telegram client connects to whichever IPv4 address its resolver returns first, so **every** IPv4 address must pass, every round. On 2026-10-26, 14 hostnames had one dead address next to a working one — a list that tests only one address would publish them as working for everyone.
* **FakeTLS proxies** must return a ServerHello whose HMAC verifies with the secret — a normal HTTPS server cannot.
* **Every proxy** must then forward an encrypted MTProto request to a Telegram datacenter and return the datacenter's reply containing a 128-bit nonce we generated. A port that merely accepts connections, a masking server, or a proxy with a wrong secret all fail here.
* The test-suite proves both directions on every change: the pinned reference server ([alexbers/mtprotoproxy](https://github.com/alexbers/mtprotoproxy)) must pass in all three secret modes and all five DCs; wrong secrets, a one-bit-flipped secret, a masking server, `google.com`, `1.1.1.1` and `github.com` must all fail.

## Honest limits

* **Tested from one place.** "Verified" means *working from the test runner* (location in `index.json`). It does **not** mean it will open from every ISP in Iran, Russia or elsewhere — censors block some proxies and not others.
* We cannot see whether a proxy shows a sponsored channel; that happens after login.
* A proxy operator sees your IP address and when you connect. Your messages stay encrypted by Telegram's own MTProto — the proxy cannot read them.

## Machine-readable

| File | Contents |
|---|---|
| [`index.json`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/index.json) | counts, criteria, every file URL — read this instead of hard-coding paths |
| [`health.json`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/health.json) | per-source health and exclusive contribution, rejection reasons, top operators |
| `state.json` | rolling per-proxy history (uptime) |

## Sources

Proxies are collected from public GitHub lists and public Telegram channel previews (full list with per-source measurements in [`tgproxy/sources.py`](tgproxy/sources.py) and `health.json`). Thank you to every maintainer. A source is kept only if it contributes verified servers no other source has.

IP geolocation and ASN by [DB-IP](https://db-ip.com) (CC BY 4.0).

## Run it yourself

```bash
pip install -r requirements.txt
python -m tgproxy --out ./output
pytest            # includes live tests against a local reference proxy
```

## FAQ

**Are these Telegram proxies free?**  
Yes. They are public MTProto proxies collected from public lists and Telegram channels; this project only tests and publishes them. No account, app or signup is needed, and the code is open source (MIT).

**How do you know a proxy actually works?**  
The tester does what a Telegram app does: the obfuscated2 handshake (plus the FakeTLS HMAC check for ee secrets), then sends req_pq_multi through the proxy and requires a Telegram datacenter to answer with our random nonce — in every one of 3 rounds. A hostname with several IPv4 addresses must pass on all of them.

**Will they work in Iran, Russia or other censored countries?**  
They are tested from a GitHub Actions runner, not from inside every network. Censors block some proxies and not others, so if one does not connect, try the next. top100.txt spreads its proxies over many networks (at most 5 per network by default) so they do not all fail together.

**Is using a free proxy safe?**  
The proxy operator can see your IP address and when you connect. Your messages stay encrypted by Telegram's own MTProto encryption; the proxy only relays encrypted traffic and cannot read them. Some proxies may pin a sponsored channel in your chat list.

**How often is the list updated?**  
About every 15 minutes. The time of the last update is shown at the top of this page and in index.json.

**What is the difference between MTProto, secure (dd) and FakeTLS (ee) proxies?**  
All of them are MTProto proxies. dd (secure) secrets add random padding to the traffic; ee (FakeTLS) secrets wrap it in a handshake that looks like TLS to a chosen website, which is harder to detect. Each type has its own file.

**raw.githubusercontent.com is blocked. Where else can I get the list?**  
Use the same path on jsDelivr: https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main/top100.txt — its cache is purged after every update.

**Can I use the list in my own app or bot?**  
Yes. index.json lists every file; proxies.json has server, port, secret, type, country, ASN, round-trip time and uptime for each proxy. Keep the MIT notice and the DB-IP (CC BY 4.0) attribution.

How to add a proxy by hand — **Android / iPhone:** Settings → Data and Storage → Proxy → Add Proxy → MTProto. **Telegram Desktop:** Settings → Advanced → Connection type → Use custom proxy → Add proxy → MTProto.

## License

MIT. For educational and research use; follow your local laws.
