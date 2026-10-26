#!/bin/bash
# Install the trigger on the always-on server. Usage: sudo ./install.sh <token-file>
# The token file is COPIED to /etc/tgproxy-trigger/token (mode 600, root only).
set -euo pipefail
src="${1:?usage: install.sh <file containing only the GitHub token>}"
here="$(cd "$(dirname "$0")" && pwd)"
install -d -m 755 /opt/tgproxy-trigger
install -m 755 "$here/tgproxy-trigger.py" /opt/tgproxy-trigger/
install -d -m 700 /etc/tgproxy-trigger
install -m 600 "$src" /etc/tgproxy-trigger/token
install -m 644 "$here/tgproxy-trigger.service" "$here/tgproxy-trigger.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now tgproxy-trigger.timer
systemctl list-timers tgproxy-trigger.timer --no-pager
