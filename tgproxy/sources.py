"""Upstream registry.

Every entry was fetched and measured on 2026-10-26 before it was added
(docs/research/03-sources.md has the full table). Columns there:
listed / verified-working / unique servers / *exclusive* verified servers —
the last one is the only number that justifies a source's place here.

Sources that were measured and NOT added are listed at the bottom with the
reason, so nobody re-adds them by accident.

Fields
  id      short stable identifier (appears in proxies.json `sources`)
  url     raw URL (GitHub raw / t.me/s preview)
  kind    "github" | "telegram"
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    url: str
    kind: str = "github"


GH = "https://raw.githubusercontent.com/"
TG = "https://t.me/s/"

SOURCES: tuple[Source, ...] = (
    # ── GitHub lists (ordered by exclusive verified servers, measured) ──────
    Source("tgmtproxy", GH + "tgmtproxy/telegram-mtproto-proxy-list/main/proxies.txt"),
    Source("tgproxypink", GH + "tgproxypink/telegram-proxy-list/main/mtproto.txt"),
    Source("weltimistar", GH + "weltimistar777-crypto/MTProxy/refs/heads/main/proxy.txt"),
    Source("vestranet", GH + "MustafaBaqer/VestraNet-Nodes/main/protocols/mtproto.txt"),
    Source("weltimistar-archive", GH + "weltimistar777-crypto/MTProxy/refs/heads/main/archives.txt"),
    Source("dubblebyte", GH + "dubblebyte/free-mtproto-proxies/main/all_proxies.txt"),
    Source("ryazhapov", GH + "ryazhapov/tg-proxy-list/main/proxy.txt"),
    Source("therealwh-eu", GH + "Therealwh/MTPproxyLIST/refs/heads/main/verified/proxy_eu_verified.txt"),
    Source("surfboard", GH + "Surfboardv2ray/TGProto/refs/heads/main/proxies.txt"),
    Source("argh94-scraper", GH + "Argh94/telegram-proxy-scraper/refs/heads/main/proxy.txt"),
    Source("airuop", GH + "Airuop/MTProtoCollector/main/proxy/mtproto.json"),
    Source("whitegram", GH + "whitegramseo/mtproxy-list/main/mtproto_proxies.json"),
    Source("solispirit", GH + "SoliSpirit/mtproto/master/all_proxies.txt"),
    Source("argh94", GH + "Argh94/Proxy-List/main/MTProto.txt"),
    Source("onlymeoneme", GH + "onlymeoneme/mtproto/refs/heads/main/all_proxies_list.txt"),
    Source("shablin", GH + "shablin/mtproto-proxy/refs/heads/main/data/valid_proxy.txt"),
    # ── Telegram channels (public web preview, no login, no API key) ───────
    Source("tg-proxy_telegramt", TG + "proxy_telegramt", "telegram"),
    Source("tg-ProxyMTProto", TG + "ProxyMTProto", "telegram"),
    Source("tg-proxy_mtm", TG + "proxy_mtm", "telegram"),
    Source("tg-MTPROTO_MTPROXY_Telegram", TG + "MTPROTO_MTPROXY_Telegram", "telegram"),
    Source("tg-TelMTProto", TG + "TelMTProto", "telegram"),
    Source("tg-Myporoxy", TG + "Myporoxy", "telegram"),
    Source("tg-TProxyRU", TG + "TProxyRU", "telegram"),
    Source("tg-mtp4tg", TG + "mtp4tg", "telegram"),
)

# Measured and deliberately NOT included (2026-10-26):
#   ALIILAPRO/MTProtoProxy mtproto.txt   byte-identical to SoliSpirit (`cmp`)
#   Grim1313/mtproto-for-telegram        commits say "sync proxies from SoliSpirit"; 0 exclusive
#   darkvibez456/mtproto-proxy-auto      identical counts to Grim1313; 0 exclusive
#   ferhatacer90/mtproxy-list            same 900 entries as tgmtproxy (different header only)
#   kort0881/telegram-proxy-collector    0 exclusive verified servers
#   Therealwh proxy_all_*                superset of proxy_eu with 0 extra exclusive
#   Telegram-FZ-LLC/Telegram-Proxy       0 exclusive
#   TETRIX8/mtproxy-list-updater         last updated 2026-08-31; 0 exclusive servers
#   nellimonix/mtproxy_list              AES-GCM encrypted payload
#   mtpro.xyz API                        Cloudflare 403 to non-browsers
#   V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB  404 (repository gone)
#   several t.me channels                0 proxies in the public preview at test time
