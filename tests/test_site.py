"""Static checks for the GitHub Pages site (docs/). No network.

Search engines and AI crawlers (GPTBot, ClaudeBot, PerplexityBot do not run
JavaScript - Vercel/MERJ, 2024) only see the raw HTML, so the useful text,
title, canonical URL and structured data must be in the file itself.
"""
import json
import re
import xml.dom.minidom
from html.parser import HTMLParser
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
BASE = "https://0xradikal.github.io/Free-Telegram-Proxy/"


class _P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.links, self.ld, self.text, self.ids = {}, [], [], [], []
        self.h1 = 0
        self._stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content")
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.h1 += 1

    def handle_endtag(self, tag):
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        cur = self._stack[-1] if self._stack else (None, {})
        if cur[0] == "script" and cur[1].get("type") == "application/ld+json":
            self.ld.append(data)
        elif cur[0] not in ("script", "style"):
            self.text.append(data)


def _page():
    p = _P()
    p.feed((DOCS / "index.html").read_text(encoding="utf-8"))
    return p


def test_head_metadata():
    p = _page()
    title = re.search(r"<title>(.*?)</title>", (DOCS / "index.html").read_text()).group(1)
    assert "Telegram Proxy" in title and len(title) <= 65
    d = p.meta["description"]
    assert "Telegram proxy" in d and 70 <= len(d) <= 170
    assert [x["href"] for x in p.links if x.get("rel") == "canonical"] == [BASE]
    assert p.meta["og:url"] == BASE and p.meta["og:image"].startswith(BASE)
    assert p.meta["twitter:card"] == "summary_large_image"
    assert p.h1 == 1
    assert not any(x.get("rel") == "alternate" and x.get("hreflang") for x in p.links)  # no pages to point at


def test_crawlable_text_without_javascript():
    words = " ".join(" ".join(_page().text).split())
    for must in ("Telegram proxies", "MTProto", "top100.txt", "Data and Storage", "Use custom proxy",
                 "Frequently asked questions", "not affiliated with Telegram"):
        assert must in words, must
    assert len(words.split()) > 500


def test_structured_data_parses_and_matches_visible_faq():
    p = _page()
    assert len(p.ld) == 1
    data = json.loads(p.ld[0])
    types = {d["@type"] for d in data}
    assert types == {"Dataset", "SoftwareSourceCode", "FAQPage"}
    ds = next(d for d in data if d["@type"] == "Dataset")
    assert 50 <= len(ds["description"]) <= 5000 and ds["distribution"]
    assert all(x["contentUrl"].startswith("https://") for x in ds["distribution"])
    faq = next(d for d in data if d["@type"] == "FAQPage")["mainEntity"]
    visible = " ".join(" ".join(p.text).split())
    for q in faq:   # structured data must describe content the user can see
        assert q["name"] in visible
        assert " ".join(q["acceptedAnswer"]["text"].split()) in visible


def test_referenced_local_assets_exist():
    p = _page()
    for x in p.links:
        h = x.get("href", "")
        if x.get("rel") in ("icon", "apple-touch-icon"):
            assert (DOCS / h).is_file(), h
    for k in ("og:image", "twitter:image"):
        assert (DOCS / p.meta[k][len(BASE):]).is_file()


def test_sitemap_and_llms():
    dom = xml.dom.minidom.parse(str(DOCS / "sitemap.xml"))
    locs = [n.firstChild.data for n in dom.getElementsByTagName("loc")]
    assert locs == [BASE]
    llms = (DOCS / "llms.txt").read_text(encoding="utf-8")
    assert llms.startswith("# Free Telegram Proxy\n") and "top100.txt" in llms


def test_dashboard_script_still_present():
    s = (DOCS / "index.html").read_text()
    for must in ('id="rows"', 'id="tiers"', 'id="stats"', "loadTop(", "const BASES="):
        assert must in s
