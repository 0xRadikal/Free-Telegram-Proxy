# Operations

Everything runs on **GitHub Actions** (US runners). The always-on server only sends a trigger.

## Pipelines

| Workflow | When | What |
|---|---|---|
| `update.yml` | `repository_dispatch: update-now` (server, every 15 min) · cron `*/10` (fallback) · manual | collect → probe ×3 → validate → size budget → rolling-squash publish → jsDelivr purge |
| `ci.yml` | every PR / push touching code | unit + TDLib differential + live integration (`test`) and full pipeline dry-run with validators (`e2e`) |
| `pages.yml` | push to `docs/**` | deploys the dashboard |

**Freshness gate:** cron runs are skipped if `index.json` on `main` is < 13 min old; dispatch runs if < 8 min old.
Back-to-back triggers therefore collapse into one run. `force=true` on manual runs bypasses it.

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
- Squash + rebase merges only, delete branch on merge, wiki off
