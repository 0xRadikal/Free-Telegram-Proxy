# Security policy

## Reporting a vulnerability

Report privately through GitHub's form: **[Report a vulnerability](https://github.com/0xRadikal/Free-Telegram-Proxy/security/advisories/new)** (Security tab → *Report a vulnerability*). Do not open a public issue, discussion or pull request for a vulnerability.

Useful to include: what an attacker can do, the affected file or workflow, steps or a proof of concept, and whether it is already public. You can write in English or Persian.

This is a single-maintainer, unpaid project. Reports are handled on a best-effort basis with no fixed response time; you will be credited in the advisory unless you ask not to be. Please give a reasonable time to fix before disclosing.

## Supported versions

Only `main` is supported. There are no releases: the code runs from `main` on GitHub Actions, and the published lists are rebuilt from it about every 15 minutes. A fix is live once it is merged and the next run publishes.

## Scope

In scope:

- Code in `tgproxy/`, `tools/` and `templates/`, and the workflows in `.github/workflows/`. Examples: a source can inject content into the published files or the README; a workflow token can be misused or leaked; a crafted link makes the pipeline connect to a private network.
- The site in `docs/` (https://0xradikal.github.io/Free-Telegram-Proxy/). Examples: third-party proxy data executing as HTML or script.

Out of scope (report to the owner instead):

- The proxies themselves. They are third-party servers this project did not deploy and does not control.
- Telegram, GitHub, jsDelivr and DB-IP.

## What using a listed proxy means

- A proxy operator can see your IP address and when you connect, and can log or block your traffic.
- Telegram encrypts traffic between your app and Telegram's servers (MTProto). A proxy therefore cannot read your messages. This is not end-to-end encryption: cloud chats use server-client encryption, and only Secret Chats are end-to-end ([Telegram FAQ](https://telegram.org/faq)).
- A proxy passing our test means it relayed a real request to Telegram from a GitHub runner. It does not mean the operator is trustworthy, or that it works from your network.

## What the pipeline does

### Outbound connections only

Nothing listens for incoming connections. The hosts contacted:

| Host | Why |
|---|---|
| `raw.githubusercontent.com` | proxy sources hosted on GitHub |
| `t.me` | public Telegram channel pages used as sources (`t.me/s/…`) |
| `download.db-ip.com` | monthly DB-IP Lite country/ASN database (CC BY 4.0) |
| `www.cloudflare.com` | `/cdn-cgi/trace`, to record the runner's country and data centre (never its IP) |
| `purge.jsdelivr.net` | clears the jsDelivr cache of the published files after each update |
| `api.github.com` | only the optional server trigger in `tools/server` (`repository_dispatch`) |
| listed proxies → Telegram DCs | MTProto probes |

`cdn.jsdelivr.net` is written into `index.json` as a mirror and used by the site as a fallback. The pipeline itself does not contact it.

### Probing safeguards

Every proxy hostname is resolved first. The link is rejected without any connection if any of its addresses is not globally routable: private (RFC 1918), loopback, link-local, CGNAT (100.64.0.0/10), documentation, unspecified or IPv6 ULA (`tgproxy/pipeline.py: select_addresses`, tested in `tests/test_community_docs.py`).

### Workflow tokens

Workflows use only the built-in `GITHUB_TOKEN`. No personal tokens are stored in the repository secrets. Every workflow declares its permissions; these are all the write grants:

| Workflow | Write permissions | Used for |
|---|---|---|
| `update.yml` | `contents: write` | the single rolling `[auto-output]` commit with the lists |
| `pages.yml` | `pages: write`, `id-token: write` | deploying `docs/` to GitHub Pages (OIDC is required by `actions/deploy-pages`) |
| `publication-health.yml` | `issues: write` | opening and closing the one "stale output" alert issue |

`ci.yml` is read-only. Every action is pinned to a full commit SHA, and Dependabot proposes updates weekly. CI runs on every pull request.

### Server trigger

The optional server trigger (`tools/server`) reads its token from a root-only file (mode 600). It refuses to start if the file is readable by group or others, and never passes the token on a command line.

## Site

The site is static. It reads the published JSON from `raw.githubusercontent.com`, falling back to jsDelivr, and renders every value as text (no `innerHTML`). It sets no cookies, uses no local storage, and loads no analytics or third-party scripts or fonts.
