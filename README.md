<div align="center">

# Free Telegram Proxy

**Every proxy here relayed a real request to a real Telegram datacenter — three times — before it was published.**

[فارسی](README_FA.md) · [Live dashboard](https://0xradikal.github.io/Free-Telegram-Proxy/) · [Telegram @Raydikalx](https://t.me/Raydikalx)

</div>

## Start here — one line

Fewest links, most resilient: **one proxy per real server**, sorted by speed.

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top50.txt
```

On a phone, just tap any line in that file — Telegram opens and asks *Connect proxy?*.

## Live numbers

<!-- LIVE:BEGIN -->
**Last update:** `2026-10-26T17:41:48Z` · tested from `US` (Cloudflare colo `ORD`)

| Stage | Count |
|---|---:|
| links collected from all sources | 3,251 |
| unique servers (IP:port) probed | 1,487 |
| **verified in all 3 rounds** (links) | **1,688** |
| the same, counted as **real servers** | **388** (360 IPs) |
| largest single operator's share of verified links | 454 (26.9%) |

`resilient` 360 · `fast` 1 · `stable` 0 · `verified` 1688 · `faketls` 119 · `secure` 86 · `classic` 163 · `all` 3251

[🇩🇪 DE 108](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt) [🇮🇷 IR 99](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt) [🇫🇮 FI 59](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FI.txt) [🇳🇱 NL 30](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt) [🇷🇺 RU 13](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt) [🇺🇸 US 11](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/US.txt) [🇵🇱 PL 9](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/PL.txt) [🇫🇷 FR 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FR.txt) [🇸🇪 SE 5](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SE.txt) [🇨🇭 CH 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/CH.txt) [🇸🇬 SG 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SG.txt) [🇬🇧 GB 2](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/GB.txt)
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
| **`resilient/`** | verified · **one link per server IP** (lowest latency kept) — *recommended* |
| `fast/` | resilient · median round-trip through the proxy ≤ 100 ms *from the test runner* |
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

If `raw.githubusercontent.com` is blocked, replace the prefix with `https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main` (jsDelivr caches up to 12 h; raw caches 5 min).

## How a proxy is tested

```
collect  →  parse (TDLib rules)  →  resolve DNS  →  dedup by IP:port:secret
        →  TCP  →  FakeTLS HMAC (ee only)  →  obfuscated2 + req_pq_multi  →  resPQ with our nonce
        →  ×3 rounds  →  history  →  tiers
```

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

## License

MIT. For educational and research use; follow your local laws.
