"""Add ?v=<content hash> to every local CSS/JS reference in docs/**/*.html.

GitHub Pages serves everything with Cache-Control: max-age=600 and no version
in the file name. Measured (Chrome 151): after a deploy, a reload re-fetched the
HTML but reused the cached app.js, so the new page ran old code for up to 10
minutes. A content hash in the URL makes the new HTML load the new file at once.

Run after editing anything under docs/:  python tools/stamp_assets.py
tests/test_site.py::test_local_css_and_js_are_stamped_with_their_content_hash
fails if a stamp is missing or out of date.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
REF = re.compile(r'(?P<attr>\b(?:href|src))="(?P<url>(?![a-z][a-z0-9+.-]*:|//)[^"?#]+\.(?:css|js))(?:\?v=[0-9a-f]*)?"')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def stamp_html(html_path: Path) -> tuple[str, list[str]]:
    text = html_path.read_text(encoding="utf-8")
    missing: list[str] = []

    def sub(m: re.Match) -> str:
        target = (html_path.parent / m.group("url")).resolve()
        if not target.is_file() or DOCS.resolve() not in target.parents:
            missing.append(m.group("url"))
            return m.group(0)
        return f'{m.group("attr")}="{m.group("url")}?v={digest(target)}"'

    return REF.sub(sub, text), missing


def main(check: bool = False) -> int:
    changed, problems = [], []
    for html_path in sorted(DOCS.rglob("*.html")):
        new, missing = stamp_html(html_path)
        problems += [f"{html_path.relative_to(DOCS)}: {u}" for u in missing]
        if new != html_path.read_text(encoding="utf-8"):
            changed.append(str(html_path.relative_to(DOCS)))
            if not check:
                html_path.write_text(new, encoding="utf-8")
    for p in problems:
        print("missing local asset:", p, file=sys.stderr)
    for c in changed:
        print(("stale: " if check else "stamped: ") + c)
    return 1 if problems or (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv[1:]))
