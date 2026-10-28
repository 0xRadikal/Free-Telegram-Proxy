"""Community files must state only what the repository actually does.

Each test ties a sentence in CODE_OF_CONDUCT.md, SECURITY.md, ACCESSIBILITY.md
or CONTRIBUTING.md to the code or configuration that makes it true, so a later
change to a workflow, a host or the site cannot silently turn a claim false.
"""
import re
from pathlib import Path

import pytest
import yaml

from tgproxy.pipeline import select_addresses

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
DOCS = ["CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "SECURITY.md", "ACCESSIBILITY.md", "SUPPORT.md"]


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


# ------------------------------------------------------------------ all files
@pytest.mark.parametrize("name", DOCS)
def test_relative_links_resolve(name):
    for target in re.findall(r"\]\((?!https?://|mailto:|#)([^)#\s]+)", _read(name)):
        assert (ROOT / target).exists(), (name, target)


# ------------------------------------------------------------ code of conduct
CC21_HEADINGS = ["## Our Pledge", "## Our Standards", "## Enforcement Responsibilities", "## Scope",
                 "## Enforcement", "## Enforcement Guidelines", "### 1. Correction", "### 2. Warning",
                 "### 3. Temporary Ban", "### 4. Permanent Ban", "## Attribution"]


def test_code_of_conduct_is_the_full_contributor_covenant():
    # The full text is kept so the rules are readable in the repository itself.
    # Note: GitHub's detector still reports "other" for 2.1 - its catalogue
    # (GET /codes_of_conduct) only has Contributor Covenant 2.0 (checked 2026-10-28).
    s = _read("CODE_OF_CONDUCT.md")
    for h in CC21_HEADINGS:
        assert re.search(rf"^{re.escape(h)}\s*$", s, re.M), h
    assert "version 2.1" in s
    assert "[INSERT CONTACT METHOD]" not in s


def test_conduct_reports_do_not_go_to_the_vulnerability_form():
    s = _read("CODE_OF_CONDUCT.md")
    contact = s[s.index("## Enforcement\n"):s.index("## Enforcement Guidelines")]
    assert "https://" in contact
    assert "Report a vulnerability" not in s and "security/advisories" not in s


# ------------------------------------------------------------------- security
def _permissions():
    """(workflow file, scope, permission) for every write grant."""
    out = []
    for f in sorted(WF.glob("*.yml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        scopes = [("workflow", d.get("permissions") or {})]
        scopes += [(f"job {j}", (v or {}).get("permissions") or {}) for j, v in d["jobs"].items()]
        for scope, perms in scopes:
            for k, v in (perms.items() if isinstance(perms, dict) else []):
                if v == "write":
                    out.append((f.name, scope, k))
    return out


def test_security_lists_every_write_permission():
    s = _read("SECURITY.md")
    grants = _permissions()
    assert grants  # the publisher needs contents: write; an empty list means the parser broke
    for name, _scope, perm in grants:
        row = next((line for line in s.splitlines() if f"`{name}`" in line), "")
        assert f"`{perm}: write`" in row, (name, perm)


def test_every_workflow_sets_explicit_permissions():
    for f in sorted(WF.glob("*.yml")):
        assert "permissions" in yaml.safe_load(f.read_text(encoding="utf-8")), f.name


# Hosts that appear in code but are never connected to.
NOT_CONTACTED = {"github.com": "User-Agent string and links only"}


def _hosts():
    files = list((ROOT / "tgproxy").glob("*.py")) + list((ROOT / "tools").glob("*.py")) + \
        list((ROOT / "tools" / "server").glob("*.py")) + list(WF.glob("*.yml"))
    hosts = set()
    for f in files:
        hosts |= set(re.findall(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})", f.read_text(encoding="utf-8")))
    return hosts - set(NOT_CONTACTED)


def test_security_names_every_contacted_host():
    s = _read("SECURITY.md")
    hosts = _hosts()
    assert {"raw.githubusercontent.com", "download.db-ip.com"} <= hosts
    for h in sorted(hosts):
        assert h in s, h


def test_security_does_not_call_telegram_end_to_end():
    # telegram.org/faq: cloud chats use server-client encryption; only Secret
    # Chats are end-to-end.
    s = " ".join(_read("SECURITY.md").lower().split())
    for claim in ("encrypted end-to-end", "end-to-end by mtproto", "end-to-end encrypted by"):
        assert claim not in s, claim
    assert "server-client" in s and "secret chats" in s


@pytest.mark.parametrize("ip", ["10.1.2.3", "172.16.0.1", "192.168.1.1", "127.0.0.1", "169.254.1.1",
                                "100.64.0.1", "0.0.0.0", "192.0.2.1", "::1", "fe80::1", "fc00::1"])
def test_non_public_addresses_are_never_probed(ip):
    assert select_addresses([ip]) == ([], "non-public-ip")
    assert select_addresses(["1.1.1.1", ip]) == ([], "non-public-ip")


def test_every_action_is_pinned_to_a_full_commit_sha():
    for f in sorted(WF.glob("*.yml")):
        for ref in re.findall(r"uses:\s*([^\s#]+)", f.read_text(encoding="utf-8")):
            assert ref.startswith("./") or re.search(r"@[0-9a-f]{40}$", ref), (f.name, ref)


def test_site_scripts_never_inject_html_or_store_anything():
    # SECURITY.md: third-party proxy data is rendered as text; no cookies, storage or trackers.
    for f in sorted((ROOT / "docs").glob("*.js")):
        js = f.read_text(encoding="utf-8")
        for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(",
                    "new Function", "document.cookie", "localStorage", "sessionStorage"):
            assert bad not in js, (f.name, bad)


def test_security_states_supported_version_and_policy_links():
    s = _read("SECURITY.md")
    assert "## Supported versions" in s and "`main`" in s
    assert "https://github.com/0xRadikal/Free-Telegram-Proxy/security/advisories/new" in s


# -------------------------------------------------------------- accessibility
def test_accessibility_statement_is_written_not_a_template():
    s = _read("ACCESSIBILITY.md")
    assert "<!--" not in s
    sections = re.split(r"^## ", s, flags=re.M)[1:]
    assert len(sections) >= 5
    for sec in sections:
        title, _, body = sec.partition("\n")
        assert len(body.split()) >= 15, title
    assert re.search(r"\b20\d\d-\d\d-\d\d\b", s)  # dated evaluation, not a timeless claim
    assert "template=accessibility.yml" in s


def test_accessibility_issue_form():
    p = ROOT / ".github" / "ISSUE_TEMPLATE" / "accessibility.yml"
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert "accessibility" in d["labels"]
    for el in d["body"]:
        label = (el.get("attributes") or {}).get("label", "").lower()
        if (el.get("validations") or {}).get("required"):
            assert "disab" not in label and "assistive" not in label, label  # never require disclosure


# --------------------------------------------------------------- contributing
def test_contributing_explains_generated_readmes_and_offline_tests():
    s = _read("CONTRIBUTING.md")
    assert "templates/README.md" in s
    assert "TGPROXY_OFFLINE=1" in s
    assert "python -m pytest -q -rs" in s
    for f in ("CODE_OF_CONDUCT.md", "SECURITY.md", "ACCESSIBILITY.md"):
        assert f"({f})" in s, f
