"""Render README.md / README_FA.md / README_RU.md from templates + the run's real numbers.

The live block between <!-- LIVE:BEGIN --> and <!-- LIVE:END --> is the only
part that changes every run; everything else is hand-written in templates/.
Numbers in the README therefore can never drift from index.json.
"""
from __future__ import annotations

import re
from pathlib import Path

from .publish import RAW

BEGIN, END = "<!-- LIVE:BEGIN -->", "<!-- LIVE:END -->"


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "—"


def live_block(index: dict, lang: str = "en") -> str:
    f = index["funnel"]
    t = index["tiers"]
    r = index.get("runner") or {}
    top = f.get("top_ip_share") or {}
    net = f.get("top_network_share") or {}
    n = lambda k: t.get(k, {}).get("count", 0)  # noqa: E731
    if lang == "fa":
        rows = [
            "| مرحله | تعداد |", "|---|---:|",
            f"| لینک جمع‌آوری‌شده از همهٔ منابع | {f['links_collected']:,} |",
            f"| سرور یکتا (IP:پورت) که تست شد | {f['unique_servers_probed']:,} |",
            f"| **تأییدشده در همهٔ {index.get('rounds', 3)} دور** (لینک) | **{f['verified_links']:,}** |",
            f"| همان‌ها، بر حسب **سرور واقعی** | **{f['verified_servers']:,}** ({f['verified_ips']:,} IP) |",
        ]
        if top:
            rows.append(f"| سهم پرتکرارترین IP از لینک‌های تأییدشده | {top['links']:,} ({top['share']*100:.1f}%) |")
        if net:
            rows.append(f"| سهم بزرگ‌ترین شبکه (`{net['network']}`) از لینک‌های تأییدشده | {net['links']:,} ({net['share']*100:.1f}%) |")
        head = (f"**آخرین به‌روزرسانی:** `{index['updated']}` · محل تست: `{r.get('loc') or '?'}` "
                f"(`{r.get('colo') or '?'}`)\n\n")
        tiers_line = (f"`resilient` {n('resilient')} · `fast` {n('fast')} · `stable` {n('stable')} · "
                      f"`verified` {n('verified')} · `faketls` {n('faketls')} · `secure` {n('secure')} · "
                      f"`classic` {n('classic')} · `all` {n('all')}")
    elif lang == "ru":
        rows = [
            "| Этап | Количество |", "|---|---:|",
            f"| ссылок собрано из всех источников | {f['links_collected']:,} |",
            f"| уникальных серверов (IP:порт) проверено | {f['unique_servers_probed']:,} |",
            f"| **прошли проверку во всех {index.get('rounds', 3)} раундах** (ссылки) | **{f['verified_links']:,}** |",
            f"| то же, в **реальных серверах** | **{f['verified_servers']:,}** ({f['verified_ips']:,} IP) |",
        ]
        if top:
            rows.append(f"| доля самого частого IP среди проверенных ссылок | {top['links']:,} ({top['share']*100:.1f}%) |")
        if net:
            rows.append(f"| доля крупнейшей сети (`{net['network']}`) среди проверенных ссылок | {net['links']:,} ({net['share']*100:.1f}%) |")
        head = (f"**Последнее обновление:** `{index['updated']}` · проверено из `{r.get('loc') or '?'}` "
                f"(`{r.get('colo') or '?'}`)\n\n")
        tiers_line = (f"`resilient` {n('resilient')} · `fast` {n('fast')} · `stable` {n('stable')} · "
                      f"`verified` {n('verified')} · `faketls` {n('faketls')} · `secure` {n('secure')} · "
                      f"`classic` {n('classic')} · `all` {n('all')}")
    else:
        rows = [
            "| Stage | Count |", "|---|---:|",
            f"| links collected from all sources | {f['links_collected']:,} |",
            f"| unique servers (IP:port) probed | {f['unique_servers_probed']:,} |",
            f"| **verified in all {index.get('rounds', 3)} rounds** (links) | **{f['verified_links']:,}** |",
            f"| the same, counted as **real servers** | **{f['verified_servers']:,}** ({f['verified_ips']:,} IPs) |",
        ]
        if top:
            rows.append(f"| largest single IP's share of verified links | {top['links']:,} ({top['share']*100:.1f}%) |")
        if net:
            rows.append(f"| largest network's (`{net['network']}`) share of verified links | {net['links']:,} ({net['share']*100:.1f}%) |")
        head = (f"**Last update:** `{index['updated']}` · tested from `{r.get('loc') or '?'}` "
                f"(Cloudflare colo `{r.get('colo') or '?'}`)\n\n")
        tiers_line = (f"`resilient` {n('resilient')} · `fast` {n('fast')} · `stable` {n('stable')} · "
                      f"`verified` {n('verified')} · `faketls` {n('faketls')} · `secure` {n('secure')} · "
                      f"`classic` {n('classic')} · `all` {n('all')}")
    cc = sorted(index.get("countries", {}).items(), key=lambda kv: -kv[1]["count"])[:12]
    ccline = " ".join(f"[{v['flag']} {k} {v['count']}]({v['url']})" for k, v in cc)
    return "\n".join([BEGIN, head + "\n".join(rows), "", tiers_line, "", ccline, END])


def render(template: str, index: dict, lang: str) -> str:
    block = live_block(index, lang)
    return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block, template, flags=re.S)


# (template in templates/, output file, language). Every output must also be
# listed in OUTPUT_PATHS of .github/workflows/update.yml (tested).
LANGS = (("README.md", "README.md", "en"), ("README_FA.md", "README_FA.md", "fa"), ("README_RU.md", "README_RU.md", "ru"))


def write_readmes(index: dict, root: Path, out: Path) -> None:
    for tpl, dst, lang in LANGS:
        src = root / "templates" / tpl
        if src.exists():
            (out / dst).write_text(render(src.read_text(encoding="utf-8"), index, lang), encoding="utf-8")


__all__ = ["render", "write_readmes", "live_block", "RAW", "LANGS"]
