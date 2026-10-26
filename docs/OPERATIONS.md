# Operations

Everything runs on **GitHub Actions** (US runners). The always-on server only sends a trigger.

## Pipelines

| Workflow | When | What |
|---|---|---|
| `update.yml` | `repository_dispatch: update-now` (server, every 15 min) · cron `4,19,34,49` (fallback) · manual | collect → probe ×3 → validate → size budget → rolling-squash publish → jsDelivr purge |
| `ci.yml` | every PR / push touching code | unit + TDLib differential + live integration (`test`) and full pipeline dry-run with validators (`e2e`) |
| `pages.yml` | push to `docs/**` | deploys the dashboard |
| `publication-health.yml` | cron `17,47` · manual (`max_age_minutes`) | read-only freshness/consistency check; opens one `stale-output` issue on failure, closes it on recovery |
| CodeQL (default setup) | GitHub-managed | code scanning for Python and Actions |

**Freshness gate:** cron runs are skipped if `index.json` on `main` is < 13 min old; dispatch runs if < 8 min old.
Back-to-back triggers therefore collapse into one run. `force=true` on manual runs bypasses it.

## About GitHub cron (measured, not assumed)

- GitHub documents `schedule` as best-effort: delayed under load, the top of the hour is the busiest time, and queued jobs may be dropped. Minimum interval 5 min. Disabled after 60 days without repository activity in a public repo (the bot's commits count as activity).
- Measured: this repo had **0** `schedule` runs in its first ~5 h; the sibling repo Free-v2ray-Configs gets one every 2–6 h. So the server trigger is the real clock and cron is only a fallback.
- Ticks are off the top of the hour. With the 13-min gate, `4,19,34,49` gives a 15-min cadence when cron does fire (`*/10` would give 20 min — simulated).
- If the server is down **and** cron is slow, `publication-health` opens an issue after 65 min of staleness — when it gets scheduled at all; it shares the same scheduler.

## Size control
- Output is replaced, not appended: `main` = source history + exactly **one** output commit (rolling squash).
- Measured output per run: ~1.4–1.9 MiB raw, ~180–245 KiB compressed. `tools/check_size.py` fails above 4 MiB total / 1 MiB per file.
- `verified/` is the only tier with every alias; other tiers keep one link per server IP; `all/` is text only.
- `state.json` tracks only proxies that passed at least once; history capped at 96 checks, entries forgotten after 7 days.

## Server trigger (`tools/server/`)
Installed as a systemd timer, isolated from everything else on the server.

```bash
sudo tools/server/install.sh /path/to/file-with-token   # copies token to /etc/tgproxy-trigger/token (600)
systemctl list-timers tgproxy-trigger.timer
journalctl -u tgproxy-trigger.service -n 20
sudo systemctl disable --now tgproxy-trigger.timer      # stop
```
The script refuses a token file readable by group/others and never puts the token on a command line.
Exit codes: `0` sent · `1` transient (after 4 tries) · `2` permanent (bad token / repo).

## Repository settings applied
- Pages: source = GitHub Actions
- Ruleset `main`: no deletion, linear history (force-with-lease from the bot still allowed — same as Free-v2ray-Configs)
- Ruleset tags: no delete / update / force-push
- Squash + rebase merges only, delete branch on merge, wiki and projects off, squash commit = PR title + body, "update branch" button on
- Security: secret scanning + push protection, Dependabot alerts + security updates, private vulnerability reporting, CodeQL default setup
- Actions: default `GITHUB_TOKEN` read-only, Actions may not approve PRs, workflows from all outside contributors' PRs need approval, artifacts/logs kept 30 days
- Not available on this plan (API accepted the request but the value stayed `disabled`): secret-scanning non-provider patterns and validity checks
