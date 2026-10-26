"""Research extractor: pull (server, port, secret) out of any text/JSON/HTML blob."""
import html, json, re, urllib.parse as up

LINK_RE = re.compile(r'(?:tg://proxy|https?://(?:www\.)?(?:t\.me|telegram\.me|telegram\.dog)/proxy)\?[^\s"\'<>`\\]+', re.I)


def _from_query(q):
    q = html.unescape(q)
    args = {}
    for part in q.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            k = up.unquote_plus(k)
            if k and k not in args:
                args[k] = up.unquote_plus(v)
    return args.get('server'), args.get('port'), args.get('secret')


def _walk_json(o, out):
    if isinstance(o, dict):
        q = o.get('query') if isinstance(o.get('query'), dict) else o
        s = q.get('server') or q.get('host') or q.get('ip')
        p = q.get('port')
        sec = q.get('secret')
        if s and p and sec:
            out.append((str(s), str(p), str(sec)))
        for v in o.values():
            _walk_json(v, out)
    elif isinstance(o, list):
        for v in o:
            _walk_json(v, out)
    elif isinstance(o, str) and 'proxy?' in o:
        out.extend(extract_text(o))


def extract_text(text):
    out = []
    text = html.unescape(text)
    for m in LINK_RE.finditer(text):
        s, p, sec = _from_query(m.group(0).split('?', 1)[1])
        if s and p and sec:
            out.append((s, p, sec))
    return out


def extract(blob):
    blob = blob.strip()
    if blob[:1] in '[{':
        try:
            out = []
            _walk_json(json.loads(blob), out)
            return out
        except ValueError:
            pass
    return extract_text(blob)
