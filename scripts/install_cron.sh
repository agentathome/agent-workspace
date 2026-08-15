#!/bin/bash
# install_cron.sh — 安装/更新定时延续会话的 cron 条目
set -euo pipefail

WORKSPACE=/home/home/workspace
ENTRY='* * * * * /usr/bin/python3 /home/home/workspace/scripts/check_due.py >> /home/home/workspace/logs/cron.log 2>&1'

mkdir -p "$WORKSPACE/logs"

CUR=$(crontab -l 2>/dev/null || true)
if printf '%s\n' "$CUR" | grep -qF 'check_due.py'; then
  echo "cron entry already present"
else
  printf '%s\n%s\n' "$CUR" "$ENTRY" | crontab -
  echo "cron entry installed"
fi

crontab -l