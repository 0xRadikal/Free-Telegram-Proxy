from tgproxy.readme import BEGIN, END, render

IDX = {"updated": "2026-01-01T00:00:00Z", "rounds": 3, "runner": {"loc": "DE", "colo": "FRA"},
       "funnel": {"links_collected": 10, "unique_servers_probed": 5, "verified_links": 4,
                  "verified_servers": 2, "verified_ips": 2, "top_ip_share": {"links": 3, "share": 0.75}},
       "tiers": {"verified": {"count": 4}}, "countries": {"DE": {"count": 4, "flag": "🇩🇪", "url": "u"}}}


def test_only_live_block_changes():
    tpl = f"head\n{BEGIN}\nold\n{END}\ntail"
    out = render(tpl, IDX, "en")
    assert out.startswith("head\n") and out.endswith("\ntail")
    assert "old" not in out and "75.0%" in out and "all 3 rounds" in out
    assert render(out, IDX, "en") == out  # idempotent


def test_farsi_block():
    out = render(f"{BEGIN}{END}", IDX, "fa")
    assert "همهٔ 3 دور" in out and "DE" in out


def test_labels_say_ip_and_network_not_operator():
    idx = {**IDX, "funnel": {**IDX["funnel"], "top_network_share": {"network": "AS24940", "links": 4, "share": 1.0}}}
    en = render(f"{BEGIN}{END}", idx, "en")
    fa = render(f"{BEGIN}{END}", idx, "fa")
    assert "operator" not in en and "اپراتور" not in fa
    assert "single IP" in en and "`AS24940`" in en and "100.0%" in en
    assert "پرتکرارترین IP" in fa and "`AS24940`" in fa


def test_old_index_without_network_share_still_renders():
    assert "network" not in render(f"{BEGIN}{END}", IDX, "en")


def test_russian_block():
    out = render(f"{BEGIN}{END}", IDX, "ru")
    assert "всех 3 раундах" in out and "DE" in out and "75.0%" in out


def test_write_readmes_writes_every_language(tmp_path):
    from pathlib import Path
    from tgproxy.readme import LANGS, write_readmes
    root = Path(__file__).resolve().parent.parent
    write_readmes(IDX, root, tmp_path)
    for tpl, dst, _ in LANGS:
        assert (root / "templates" / tpl).exists(), tpl
        txt = (tmp_path / dst).read_text(encoding="utf-8")
        assert BEGIN in txt and END in txt
        assert IDX["updated"] in txt   # the live block was actually rendered


def test_every_rendered_readme_is_a_publishable_output():
    """The publisher refuses to touch files outside OUTPUT_PATHS; a README the
    renderer writes but the workflow does not list would be silently dropped."""
    import re
    from pathlib import Path
    from tgproxy.readme import LANGS
    wf = (Path(__file__).resolve().parent.parent / ".github/workflows/update.yml").read_text()
    paths = re.search(r'OUTPUT_PATHS: "([^"]+)"', wf).group(1).split()
    for _, dst, _ in LANGS:
        assert dst in paths, dst


# ------------------------------------------------------------------ template links
def _slugs(md):
    """GitHub heading anchors (lower-case, punctuation removed, spaces -> '-')."""
    import re
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    out = set()
    for h in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", md):
        t = re.sub(r"[`*_]", "", h).strip().lower()
        out.add(re.sub(r"[^\w\- ]", "", t).replace(" ", "-"))
    return out


def test_links_to_readme_sections_point_at_existing_headings():
    """docs/, SUPPORT.md and the discussion forms deep-link into the README;
    renaming a heading silently turns those links into 'top of page'."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    slugs = _slugs((root / "templates" / "README.md").read_text(encoding="utf-8"))
    files = [*root.glob("docs/**/*.html"), root / "docs" / "llms.txt", *root.glob("*.md"),
             *root.glob(".github/**/*.yml"), *root.glob(".github/**/*.md")]
    bad = []
    for f in files:
        if f.name.startswith("README"):
            continue
        s = f.read_text(encoding="utf-8")
        # only real links (href / markdown), not JSON-LD "@id" identifiers
        for a in re.findall(r'(?:href="|\]\()https://github\.com/0xRadikal/Free-Telegram-Proxy#([\w-]+)', s):
            if a != "readme" and a not in slugs:   # #readme is GitHub's own README anchor
                bad.append((f.relative_to(root).as_posix(), a))
    assert not bad, bad


def test_template_relative_links_resolve():
    """Every relative link/image in the README templates is either a committed
    source file or a path the publisher writes (OUTPUT_PATHS)."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    wf = (root / ".github/workflows/update.yml").read_text()
    outputs = re.search(r'OUTPUT_PATHS: "([^"]+)"', wf).group(1).split()
    for tpl in (root / "templates").glob("README*.md"):
        s = tpl.read_text(encoding="utf-8")
        refs = re.findall(r'\]\((?!https?://|#|mailto:)([^)\s#]+)', s) + \
            re.findall(r'(?:src|href)="(?!https?://|#|mailto:)([^"#]+)"', s)
        for r in refs:
            top = r.split("/")[0]
            assert (root / r).exists() or top in outputs or r in outputs, (tpl.name, r)


# ------------------------------------------------------------------ README images (assets/readme)
_SVG_DIR = "assets/readme"


def _templates():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    return root, {p.name: p.read_text(encoding="utf-8") for p in (root / "templates").glob("README*.md")}


def test_template_srcset_targets_exist():
    """<source srcset> (mobile variants) is not covered by the src/href check."""
    import re
    root, tpls = _templates()
    for name, s in tpls.items():
        for ref in re.findall(r'srcset="([^"]+)"', s):
            assert not ref.startswith(("http://", "https://")), (name, ref)   # keep relative: works on forks/branches
            assert (root / ref).is_file(), (name, ref)


def test_no_orphan_readme_assets():
    import re
    root, tpls = _templates()
    used = set()
    for s in tpls.values():
        used |= set(re.findall(r'(?:src|srcset)="(assets/readme/[^"]+)"', s))
    files = {p.relative_to(root).as_posix() for p in (root / _SVG_DIR).glob("*")}
    assert files == used, {"unused files": sorted(files - used), "missing files": sorted(used - files)}


def test_readme_svgs_are_safe_and_described():
    """GitHub serves these with a sandbox CSP; keep them self-contained anyway."""
    import re
    import xml.etree.ElementTree as ET
    root, _ = _templates()
    for p in sorted((root / _SVG_DIR).glob("*.svg")):
        s = p.read_text(encoding="utf-8")
        svg = ET.fromstring(s)
        assert svg.tag == "{http://www.w3.org/2000/svg}svg" and svg.get("viewBox"), p.name
        assert svg.find("{http://www.w3.org/2000/svg}title") is not None, p.name
        assert not re.search(r"<script|<foreignObject|\son[a-z]+\s*=|javascript:|@import", s, re.I), p.name
        refs = re.findall(r'(?:href|src)\s*=\s*"([^"]+)"|url\(\s*["\']?([^)"\']+)', s)
        for ref in (a or b for a, b in refs):
            assert ref.startswith(("#", "data:image/png;base64,")), (p.name, ref[:60])


def test_every_readme_animation_stops_under_reduced_motion():
    """SMIL (<animate>) ignores CSS media queries, so each animated element needs a class
    whose rule inside @media (prefers-reduced-motion: reduce) pins the animated property with
    !important (an author !important declaration overrides SMIL - verified in Chromium with
    --force-prefers-reduced-motion). CSS keyframe animations need animation:none there."""
    import re
    import xml.etree.ElementTree as ET
    root, _ = _templates()
    NS = "{http://www.w3.org/2000/svg}"
    for p in sorted((root / _SVG_DIR).glob("*.svg")):
        s = p.read_text(encoding="utf-8")
        media = "".join(re.findall(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", s))
        rules = dict(re.findall(r"\.([\w-]+)\s*\{([^}]*)\}", media))
        if "@keyframes" in s:
            assert "animation:none" in media.replace(" ", ""), p.name
        for el in ET.fromstring(s).iter():
            anims = [c for c in el if c.tag in (NS + "animate", NS + "animateTransform", NS + "animateMotion", NS + "set")]
            if not anims:
                continue
            decl = " ".join(rules.get(c, "") for c in (el.get("class") or "").split()).replace(" ", "")
            for a in anims:
                if a.tag == NS + "animateMotion":
                    raise AssertionError(f"{p.name}: animateMotion cannot be pinned by CSS")
                attr = a.get("attributeName")
                prop = {"cx": "opacity", "cy": "opacity"}.get(attr, attr)   # travelling dots are hidden instead
                assert f"{prop}:" in decl and "!important" in decl, (p.name, el.tag, attr, decl)


def test_qr_codes_point_where_their_link_points():
    """Each QR image's payload (stated in its <desc>, decoded with OpenCV when the files were added)
    must equal the href of the link that wraps it in the README."""
    import re
    root, tpls = _templates()
    seen = 0
    for name, s in tpls.items():
        for href, src in re.findall(r'<a href="([^"]+)"><img src="(assets/readme/qr-[^"]+)"', s):
            desc = re.search(r"<desc>Scannable QR: ([^<]+)</desc>", (root / src).read_text(encoding="utf-8"))
            assert desc and desc.group(1) == href, (name, src, href)
            seen += 1
    qrs = list((root / _SVG_DIR).glob("qr-*.svg"))
    assert seen >= len(qrs)
