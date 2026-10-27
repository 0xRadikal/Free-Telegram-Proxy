"""Issue and discussion forms must parse and follow GitHub's form schema.

GitHub silently falls back to a blank form when a template is invalid, and a
discussion form is only used if its file name equals a category slug
(docs: "Syntax for discussion category forms"). Rules checked here are the
ones the docs state: body required with >= 1 non-markdown field; ids use only
[A-Za-z0-9_-] and are unique; dropdown options non-empty and distinct; no form
for the polls category. Validated additionally against the SchemaStore
schemas (github-discussion.json, github-issue-forms.json) when written.
"""
import re
from pathlib import Path

import pytest
import yaml

GH = Path(__file__).resolve().parent.parent / ".github"
# Default category slugs created when Discussions is enabled (verified via the
# GraphQL API on 2026-10-27). Renaming a category in the UI changes its slug.
CATEGORY_SLUGS = {"announcements", "general", "ideas", "polls", "q-a", "show-and-tell"}
TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}

DISCUSSION_FORMS = sorted((GH / "DISCUSSION_TEMPLATE").glob("*.yml"))
ISSUE_FORMS = sorted(p for p in (GH / "ISSUE_TEMPLATE").glob("*.yml") if p.name != "config.yml")


def _check_body(d):
    assert isinstance(d.get("body"), list) and d["body"]
    ids = []
    for el in d["body"]:
        assert el["type"] in TYPES
        assert isinstance(el.get("attributes"), dict)
        if el["type"] == "markdown":
            assert el["attributes"].get("value")
            continue
        assert el["attributes"].get("label")
        if "id" in el:
            assert re.fullmatch(r"[A-Za-z0-9_-]+", el["id"]), el["id"]
            ids.append(el["id"])
        if el["type"] == "dropdown":
            opts = el["attributes"].get("options")
            assert opts and len(opts) == len(set(opts))
        if el["type"] == "checkboxes":
            assert all(o.get("label") for o in el["attributes"]["options"])
    assert len(ids) == len(set(ids))
    assert any(el["type"] != "markdown" for el in d["body"])


def test_discussion_forms_exist():
    assert {p.stem for p in DISCUSSION_FORMS} >= {"q-a", "ideas", "show-and-tell", "general"}


@pytest.mark.parametrize("path", DISCUSSION_FORMS, ids=lambda p: p.name)
def test_discussion_form(path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(d) <= {"title", "labels", "body"}
    assert path.stem in CATEGORY_SLUGS and path.stem != "polls"
    _check_body(d)


@pytest.mark.parametrize("path", ISSUE_FORMS, ids=lambda p: p.name)
def test_issue_form(path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert d.get("name") and d.get("description")
    _check_body(d)


def test_issue_chooser_links_to_discussions():
    cfg = yaml.safe_load((GH / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8"))
    urls = [c["url"] for c in cfg["contact_links"]]
    assert any("/discussions" in u for u in urls)
    assert all(c.get("name") and c.get("about") and c["url"].startswith("https://") for c in cfg["contact_links"])
