from tgproxy.links import extract, normalize_server, parse_link, parse_query, to_int32, url_decode

S = "dd" + "00112233445566778899aabbccddeeff"


def test_three_link_forms():
    for pre in ("tg://proxy?", "https://t.me/proxy?", "https://telegram.me/proxy?", "t.me/proxy?"):
        got = extract(f"x {pre}server=a.b&port=443&secret={S} y")
        assert len(got) == 1 and got[0].server == "a.b" and got[0].port == 443


def test_html_escaped_ampersands_from_tme_preview():
    html = f'<a href="https://t.me/proxy?server=h.io&amp;port=8443&amp;secret={S}">x</a>'
    (p,) = extract(html)
    assert (p.server, p.port) == ("h.io", 8443)


def test_first_key_wins_like_tdlib():
    p = parse_link(f"tg://proxy?server=first&server=second&port=1&secret={S}")
    assert p.server == "first"


def test_port_parsing_matches_to_integer():
    assert to_int32("443abc") == 443
    assert to_int32("") == 0
    assert to_int32("-5") == -5
    assert parse_link(f"tg://proxy?server=a&port=0&secret={S}") is None
    assert parse_link(f"tg://proxy?server=a&port=65536&secret={S}") is None
    assert parse_link(f"tg://proxy?server=a&port=65535&secret={S}").port == 65535
    assert parse_link(f"tg://proxy?server=a&port=443%20&secret={S}").port == 443


def test_url_decode_edge_cases():
    assert url_decode("a+b") == "a b"
    assert url_decode("%41") == "A"            # C++: from_i + 2 < n  → 0 + 2 < 3, decoded
    assert url_decode("%4") == "%4"            # 0 + 2 < 2 is false → kept literally
    assert url_decode("%41x") == "Ax"
    assert url_decode("%zz") == "%zz"
    assert url_decode("100%") == "100%"


def test_url_encoded_base64_secret():
    p = parse_link("https://t.me/proxy?server=s&port=443&secret=3RBEYoISSb16xRkTAiDCXQk%3D")
    assert p is not None and p.secret.kind == "secure"


def test_normalize_server():
    assert normalize_server("Host.Example.") == "host.example"
    assert normalize_server("[2001:db8::1]") == "2001:db8::1"


def test_missing_args():
    assert parse_link("tg://proxy?server=a&port=1") is None
    assert parse_query("a=1&&b=2&=x") == {"a": "1", "b": "2"}


def test_json_shapes():
    j1 = f'[{{"server":"x","port":443,"secret":"{S}"}}]'
    j2 = f'[{{"scheme":"https","query":{{"server":"y","port":"8443","secret":"{S}"}}}}]'
    j3 = f'{{"proxies":[{{"host":"z","port":1,"secret":"{S}"}}]}}'
    j4 = f'[{{"link":"tg://proxy?server=w&port=2&secret={S}"}}]'
    assert [p.server for p in extract(j1)] == ["x"]
    assert [p.server for p in extract(j2)] == ["y"]
    assert [p.server for p in extract(j3)] == ["z"]
    assert [p.server for p in extract(j4)] == ["w"]


def test_invalid_secret_dropped():
    assert extract("tg://proxy?server=a&port=1&secret=nothex!") == []
