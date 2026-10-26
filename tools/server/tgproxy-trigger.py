#!/usr/bin/env python3
"""Send one `repository_dispatch` (update-now) to Free-Telegram-Proxy.

This is the ONLY thing the always-on server does for this project: all
collection, testing and publishing runs on GitHub Actions. Run by a systemd
timer (see tgproxy-trigger.timer). GitHub's own cron is the fallback.

Token: read from a root-only file (default /etc/tgproxy-trigger/token, mode
600), never from argv or the unit file, so it cannot leak via `ps` or
`systemctl show`. Needs repo scope (classic PAT) or Contents: write (fine-grained).

Exit codes: 0 sent · 1 transient failure after retries · 2 permanent (bad token,
repo missing) — systemd logs all of them; nothing is retried forever.
"""
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

REPO = os.environ.get("TGPROXY_REPO", "0xRadikal/Free-Telegram-Proxy")
EVENT = os.environ.get("TGPROXY_EVENT", "update-now")
TOKEN_FILE = os.environ.get("TGPROXY_TOKEN_FILE", "/etc/tgproxy-trigger/token")
ATTEMPTS = 4
PERMANENT = {400, 401, 403, 404, 422}


def read_token() -> str:
    st = os.stat(TOKEN_FILE)
    if st.st_mode & 0o077:
        print(f"refusing: {TOKEN_FILE} must not be readable by group/others (chmod 600)", file=sys.stderr)
        sys.exit(2)
    tok = open(TOKEN_FILE).read().strip()
    if not tok:
        print("refusing: empty token file", file=sys.stderr)
        sys.exit(2)
    return tok


def send(token: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/dispatches",
        data=json.dumps({"event_type": EVENT}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "tgproxy-trigger",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read(200).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        return 0, f"{type(e).__name__}: {e}"


def main() -> int:
    token = read_token()
    for attempt in range(1, ATTEMPTS + 1):
        code, detail = send(token)
        if code == 204:
            print(f"dispatched {EVENT} to {REPO} (attempt {attempt})")
            return 0
        if code in PERMANENT:
            print(f"permanent failure HTTP {code}: {detail}", file=sys.stderr)
            return 2
        print(f"attempt {attempt}: HTTP {code} {detail}", file=sys.stderr)
        if attempt < ATTEMPTS:
            time.sleep(1.5 * 2 ** (attempt - 1) + random.uniform(0, 1.5))
    return 1


if __name__ == "__main__":
    sys.exit(main())
