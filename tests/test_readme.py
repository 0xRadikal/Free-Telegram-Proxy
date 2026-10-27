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
