"""Static checks for the GitHub Pages site (docs/). No network.

Search engines and AI crawlers (GPTBot, ClaudeBot, PerplexityBot do not run
JavaScript - Vercel/MERJ, 2024) only see the raw HTML, so the useful text,
title, canonical URL and structured data must be in the file itself.

The site is bilingual (en at /, fa at /fa/) with two guide pages per language.
"""
import html
import json
import re
import struct
import urllib.parse
import xml.dom.minidom
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "https://0xradikal.github.io/Free-Telegram-Proxy/"
PAGES = {"": "en", "fa/": "fa", "methodology/": "en", "fa/methodology/": "fa", "data/": "en", "fa/data/": "fa"}
HOMES = {"": "en", "fa/": "fa"}
PERSIAN = re.compile(r"[\u0600-\u06FF]")


class _P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.links, self.ld, self.text, self.ids, self.tags = {}, [], [], [], [], []
        self.h1 = 0
        self._stack = []
        self.by_id = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag not in ("meta", "link", "img", "input", "br", "source"):
            self._stack.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
            self.by_id[a["id"]] = []
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content")
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.h1 += 1

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        cur = self._stack[-1] if self._stack else (None, {})
        if cur[0] == "script" and cur[1].get("type") == "application/ld+json":
            self.ld.append(data)
        elif cur[0] not in ("script", "style"):
            self.text.append(data)
            for _, a in self._stack:
                if "id" in a and a["id"] in self.by_id:
                    self.by_id[a["id"]].append(data)


def _file(rel):
    return DOCS / rel / "index.html"


def _src(rel=""):
    return _file(rel).read_text(encoding="utf-8")


def _page(rel=""):
    p = _P()
    p.feed(_src(rel))
    return p


def _visible(p):
    return " ".join(" ".join(p.text).split())


def _local_target(href, rel):
    """Map a link on page `rel` to a file under docs/, or None if it leaves the site."""
    if href.startswith(BASE):
        path = href[len(BASE):]
    elif re.match(r"^[a-z][a-z0-9+.-]*:", href) or href.startswith("//"):
        return None
    else:
        path = urllib.parse.urljoin(BASE + rel, href)
        if not path.startswith(BASE):
            return DOCS / "__outside_site__"   # climbed above the project root: broken on Pages
        path = path[len(BASE):]
    path = urllib.parse.urlsplit(path).path
    target = DOCS / path
    if path == "" or path.endswith("/"):
        target = target / "index.html"
    return target


def _translations():
    """TRANSLATIONS = {en:{k:'v',...},fa:{...}} from app.js -> {'en': {...}, 'fa': {...}}"""
    js = (DOCS / "app.js").read_text(encoding="utf-8")
    body = js[js.index("const TRANSLATIONS="):js.index("const TIER_IDS=")]
    out = {}
    for lang in ("en", "fa"):
        start = body.index(lang + ":{") + len(lang) + 2
        depth, i = 1, start
        while depth:
            depth += {"{": 1, "}": -1}.get(body[i], 0) if body[i - 1] != "\\" else 0
            i += 1
        out[lang] = {k: v.replace("\\'", "'") for k, v in re.findall(r"(\w+):'((?:[^'\\]|\\.)*)'", body[start:i - 1])}
    return out


def _graph(p):
    items = []
    for raw in p.ld:
        data = json.loads(raw)
        items.extend(data.get("@graph", [data]) if isinstance(data, dict) else data)
    return items


def _png_size(path):
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


# --------------------------------------------------------------------------- head / SEO

@pytest.mark.parametrize("rel,lang", PAGES.items())
def test_head_metadata(rel, lang):
    p = _page(rel)
    src = _src(rel)
    title = html.unescape(re.search(r"<title>(.*?)</title>", src).group(1))
    assert 20 <= len(title) <= 65, title
    d = p.meta["description"]
    assert 70 <= len(d) <= 170, (len(d), d)
    assert re.search(r'<html[^>]*\blang="%s"' % lang, src)
    assert re.search(r'<html[^>]*\bdir="%s"' % ("rtl" if lang == "fa" else "ltr"), src)
    assert [x["href"] for x in p.links if x.get("rel") == "canonical"] == [BASE + rel]
    assert p.meta["og:url"] == BASE + rel
    assert p.meta["twitter:card"] == "summary_large_image"
    assert p.h1 == 1


def test_english_home_keywords():
    p = _page("")
    title = re.search(r"<title>(.*?)</title>", _src("")).group(1)
    assert "Telegram Proxy" in title
    assert "Telegram proxy" in p.meta["description"]


@pytest.mark.parametrize("rel", PAGES)
def test_hreflang_targets_exist_and_are_reciprocal(rel):
    alts = {x["hreflang"]: x["href"] for x in _page(rel).links if x.get("rel") == "alternate" and x.get("hreflang")}
    assert set(alts) == {"en", "fa", "x-default"}
    assert alts["x-default"] == alts["en"]
    assert BASE + rel in alts.values()
    for href in alts.values():
        target = _local_target(href, rel)
        assert target and target.is_file(), href
        back = {x["href"] for x in _page(href[len(BASE):]).links if x.get("rel") == "alternate"}
        assert BASE + rel in back, (href, rel)


@pytest.mark.parametrize("rel", PAGES)
def test_social_image_exists_and_declared_size_is_real(rel):
    p = _page(rel)
    for k in ("og:image", "twitter:image"):
        assert p.meta[k].startswith(BASE), p.meta[k]
        assert (DOCS / p.meta[k][len(BASE):]).is_file(), p.meta[k]
    w, h = _png_size(DOCS / p.meta["og:image"][len(BASE):])
    assert (p.meta.get("og:image:width"), p.meta.get("og:image:height")) == (str(w), str(h))
    alt = p.meta.get("og:image:alt", "")
    assert "Root-R" not in alt and "electric blue" not in alt  # the card shows neither


# --------------------------------------------------------------------------- links, assets, language switch

@pytest.mark.parametrize("rel", PAGES)
def test_every_local_link_and_asset_exists(rel):
    p = _page(rel)
    missing = []
    for tag, a in p.tags:
        for attr in ("href", "src"):
            v = a.get(attr)
            if not v or (tag == "link" and a.get("rel") in ("preconnect", "dns-prefetch")):
                continue
            if v.startswith("#"):
                if v[1:] and v[1:] not in p.ids:
                    missing.append(v)
                continue
            target = _local_target(v, rel)
            if target is not None and not target.is_file():
                missing.append(v)
    assert not missing, missing


@pytest.mark.parametrize("rel,other", [("", "fa/"), ("fa/", "")])
def test_language_switch_opens_the_other_language(rel, other):
    p = _page(rel)
    lang = next(a for t, a in p.tags if a.get("id") == "lang")
    assert _local_target(lang["href"], rel) == _file(other)
    for f in list(DOCS.glob("*.js")) + [_file(r) for r in PAGES]:
        s = f.read_text(encoding="utf-8")
        assert "Raydikalx_V7_Telegram_Preview" not in s, f
        assert "window.location" not in s, f  # navigation must stay a real link


def test_no_third_party_fonts_and_local_fonts_exist():
    # Google Fonts is a render-blocking third party; when it is unreachable
    # (blocked networks) the browser shows nothing for ~15 s. Fonts are self-hosted.
    files = [_file(r) for r in PAGES] + list(DOCS.glob("*.css"))
    for f in files:
        s = f.read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in s and "fonts.gstatic.com" not in s, f
    css = "".join(f.read_text(encoding="utf-8") for f in DOCS.glob("*.css"))
    urls = re.findall(r"@font-face\s*{[^}]*?url\(['\"]?([^'\")]+)", css)
    assert urls
    for u in urls:
        assert (DOCS / u.lstrip("./")).is_file() or any((f.parent / u).is_file() for f in DOCS.glob("*.css")), u
    for fam in ("Manrope", "Estedad"):
        assert fam in css
    assert any(DOCS.glob("fonts/OFL*.txt"))  # SIL OFL 1.1 requires the licence to ship with the fonts


# --------------------------------------------------------------------------- crawlable content

def test_crawlable_text_without_javascript_en():
    words = _visible(_page(""))
    for must in ("Telegram proxies", "MTProto", "top100.txt", "Data and Storage", "Use custom proxy",
                 "not affiliated with Telegram"):
        assert must in words, must
    assert len(words.split()) > 500


def test_crawlable_text_without_javascript_fa():
    words = _visible(_page("fa/"))
    for must in ("پروکسی", "MTProto", "top100.txt", "Data and Storage", "Use custom proxy", "وابسته به تلگرام نیست"):
        assert must in words, must
    assert len(words.split()) > 500


@pytest.mark.parametrize("rel", PAGES)
def test_no_paragraph_repeated_on_a_page(rel):
    paras = [" ".join(html.unescape(re.sub(r"<[^>]+>", "", m)).split())
             for m in re.findall(r"<p\b[^>]*>(.*?)</p>", _src(rel), re.S)]
    long_ = [x for x in paras if len(x) > 60]
    dup = {x for x in long_ if long_.count(x) > 1}
    assert not dup, dup


@pytest.mark.parametrize("rel,lang", HOMES.items())
def test_structured_data_parses_and_matches_visible_faq(rel, lang):
    p = _page(rel)
    graph = _graph(p)
    types = {g["@type"] for g in graph}
    assert {"WebSite", "WebPage", "SoftwareSourceCode", "FAQPage"} <= types
    src = _src(rel)
    visible_q = [" ".join(html.unescape(x).split()) for x in re.findall(r'<details class="seo-faq-item"><summary>(.*?)</summary>', src, re.S)]
    visible_a = [" ".join(html.unescape(re.sub(r"<[^>]+>", "", x)).split())
                 for x in re.findall(r'<details class="seo-faq-item"><summary>.*?</summary>\s*<p>(.*?)</p>', src, re.S)]
    faq = next(g for g in graph if g["@type"] == "FAQPage")["mainEntity"]
    assert len(faq) == len(visible_q) >= 5
    for q, vq, va in zip(faq, visible_q, visible_a):   # structured data must describe what the user can see
        assert q["name"] == vq
        assert " ".join(q["acceptedAnswer"]["text"].split()) == va
    if lang == "en":
        ds = next(g for g in graph if g["@type"] == "Dataset")
        assert 50 <= len(ds["description"]) <= 5000 and ds["distribution"]
        for x in ds["distribution"]:
            assert x["contentUrl"].startswith("https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/")


@pytest.mark.parametrize("rel", [r for r in PAGES if r not in HOMES])
def test_guide_pages_structured_data(rel):
    graph = _graph(_page(rel))
    assert {"WebPage", "BreadcrumbList"} <= {g["@type"] for g in graph}
    crumbs = next(g for g in graph if g["@type"] == "BreadcrumbList")["itemListElement"]
    for c in crumbs:
        assert _local_target(c["item"], rel).is_file(), c["item"]


# --------------------------------------------------------------------------- language correctness

def test_static_text_matches_translation_table():
    """Text present before JavaScript runs must equal what app.js would render."""
    T = _translations()
    assert set(T["en"]) == set(T["fa"])
    for rel, lang in HOMES.items():
        src = _src(rel)
        for key, text in re.findall(r'data-t="(\w+)"[^>]*>([^<]*)<', src):
            assert key in T[lang], key
            assert html.unescape(text).strip() == T[lang][key].strip(), (rel, key, text)
        for key, text in re.findall(r'data-placeholder="(\w+)"[^>]*placeholder="([^"]*)"', src):
            assert html.unescape(text) == T[lang][key], (rel, key)


def test_persian_page_has_no_english_ui_defaults():
    p = _page("fa/")
    for i in ("sourceText", "emptyTitle", "emptyDesc", "motionLabel"):
        txt = "".join(p.by_id[i]).strip()
        assert PERSIAN.search(txt), (i, txt)
    allowed = {"GitHub", "Telegram", "Raydikalx", "MTProto", "FakeTLS"}
    for rel, lang in PAGES.items():
        if lang != "fa":
            continue
        for tag, a in _page(rel).tags:
            for attr in ("aria-label", "alt", "title"):
                v = a.get(attr) or ""
                latin_words = set(re.findall(r"[A-Za-z][A-Za-z-]{3,}", v)) - allowed
                assert not (latin_words and not PERSIAN.search(v)), (rel, tag, attr, v)


# --------------------------------------------------------------------------- sitemap, llms, dashboard wiring

def test_sitemap_and_llms():
    dom = xml.dom.minidom.parse(str(DOCS / "sitemap.xml"))
    locs = [n.firstChild.data for n in dom.getElementsByTagName("loc")]
    assert sorted(locs) == sorted(BASE + r for r in PAGES)
    llms = (DOCS / "llms.txt").read_text(encoding="utf-8")
    assert llms.startswith("# ") and "Free Telegram Proxy" in llms.splitlines()[0] and "top100.txt" in llms
    for url in re.findall(r"\((https://0xradikal\.github\.io/[^)]+)\)", llms):
        assert _local_target(url, "").is_file(), url


def test_dashboard_wiring():
    js = (DOCS / "app.js").read_text(encoding="utf-8") + (DOCS / "motion.js").read_text(encoding="utf-8")
    used = set(re.findall(r"\$\('([^']+)'\)", js)) | set(re.findall(r"getElementById\('([^']+)'\)", js))
    assert {"tiers", "tableBody", "cardGrid", "search", "country", "sort", "sourceText"} <= used
    for rel in HOMES:
        p = _page(rel)
        assert not (used - set(p.ids)), (rel, used - set(p.ids))
        assert len(p.ids) == len(set(p.ids)), rel
        assert 'id="stats"' in _src(rel)
    assert "https://raw.githubusercontent.com/${REPO}/main" in js
    assert "https://cdn.jsdelivr.net/gh/${REPO}@main" in js


def test_jsdelivr_purge_covers_every_file_the_site_reads():
    # The site falls back to jsDelivr when raw.githubusercontent.com is blocked.
    # jsDelivr caches @main for up to 12 h, so every file the page fetches must be
    # purged after each publish or the fallback shows old proxies as current.
    js = (DOCS / "app.js").read_text(encoding="utf-8")
    tiers = re.search(r"const TIER_IDS=\[([^\]]+)\]", js).group(1)
    needed = {"index.json"} | {f"{t}/proxies.json" for t in re.findall(r"'(\w+)'", tiers)}
    wf = (ROOT / ".github/workflows/update.yml").read_text(encoding="utf-8")
    purge = re.search(r"name: Purge jsDelivr.*?for f in (.*?); do", wf, re.S).group(1).split()
    assert needed <= set(purge), needed - set(purge)
