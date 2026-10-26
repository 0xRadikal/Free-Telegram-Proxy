# Contributing

- Every claim in this repository must be measured, not assumed. If you change how proxies are tested or ranked, include the numbers.
- `pytest` runs unit tests, a differential test against the real TDLib (`tdjson`) and live tests against a pinned reference proxy. CI runs all of it on GitHub's runner on every PR.
- Do not commit generated outputs (`verified/`, `index.json`, …). The bot publishes them as a single rolling commit on `main`; a human commit that touches them would be overwritten.
- Commit messages: Conventional Commits. Never include the string `[auto-output]`.
- New sources: open the *Suggest a source* issue; a source is added only if it contributes verified servers no other source has (see `health.json → exclusive_verified_servers`).
