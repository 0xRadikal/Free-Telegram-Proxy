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
