# Contributing

Thanks for helping. By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). Questions go to [SUPPORT.md](SUPPORT.md), and vulnerabilities go privately through [SECURITY.md](SECURITY.md), never in a public issue.

## The one rule

Every claim in this repository is measured, not assumed. If you change how proxies are tested, ranked or described, include the numbers: the command, its output, and where it ran. A bug fix needs a test that fails without the fix.

## Set up

```bash
git clone https://github.com/0xRadikal/Free-Telegram-Proxy.git
cd Free-Telegram-Proxy
python3.12 -m venv .venv && . .venv/bin/activate      # CI uses Python 3.12
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q -rs
```

`pytest` runs three kinds of tests:

- unit tests;
- a differential test of secret parsing against the real TDLib (`tdjson`);
- live tests against a pinned reference MTProxy server (`tests/refserver`) and real Telegram data centres.

If Telegram is blocked where you are, run `TGPROXY_OFFLINE=1 python -m pytest -q -rs`. The live tests are then skipped and listed (`-rs`), and CI still runs them on GitHub's runner for every pull request.

To run the whole pipeline locally without publishing anything:

```bash
python -m tgproxy --out /tmp/out --rounds 2 --gap 5
python tools/validate_outputs.py /tmp/out
```

## What to edit, and what not to

| You want to change | Edit | Do not edit |
|---|---|---|
| README text (any language) | `templates/README.md`, `templates/README_FA.md`, `templates/README_RU.md` | `README*.md` in the root. They are regenerated on every run, and only the `<!-- LIVE -->` block is filled in automatically. |
| The website | `docs/`, then run `python tools/stamp_assets.py` (cache-busting `?v=` stamps) and `python -m pytest -q tests/test_site.py`. See [ACCESSIBILITY.md](ACCESSIBILITY.md) for the keyboard, contrast and motion rules. | |
| Testing / ranking | `tgproxy/` plus a test in `tests/` | |
| Published lists | nothing. The bot owns them. | `verified/`, `fast/`, `stable/`, `resilient/`, `faketls/`, `secure/`, `classic/`, `all/`, `countries/`, `top100.txt`, `top50.txt`, `index.json`, `health.json`, `state.json` |

The bot publishes the generated files as a single rolling commit on `main`. A human commit that touches them would be overwritten, and it would confuse the publisher's anchor.

## Pull requests

- Use Conventional Commits (`fix(probe): …`, `feat(site): …`, `docs: …`). Never include the string `[auto-output]`: it marks bot commits.
- Keep a PR to one topic, and fill in the template, especially the *Evidence* section.
- CI must be green: unit, TDLib differential, live integration and an end-to-end pipeline run. All actions are pinned to commit SHAs. If you add an action, pin it the same way, with the version in a comment.

## Sources

To propose a new proxy source, open the *Suggest a source* issue. A source is added only if it contributes verified servers that no other source has (`health.json → sources[].exclusive_verified_servers`).

## Licence

Contributions are accepted under the repository's [MIT License](LICENSE). Country and ASN data comes from DB-IP (CC BY 4.0), and the site fonts are under the SIL OFL (`docs/fonts/`).
