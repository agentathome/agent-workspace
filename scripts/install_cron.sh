#!/bin/bash
# install_cron.sh — 安装/更新定时条目（延续会话 + 每日状态邮件会话），并清理旧条目
set -euo pipefail

WORKSPACE=/home/home/workspace
CHECKDUE='* * * * * /usr/bin/python3 /home/home/workspace/scripts/check_due.py >> /home/home/workspace/logs/cron.log 2>&1'
DAILYEMAIL='30 8 * * * /home/home/workspace/scripts/daily_email_session.sh >> /home/home/workspace/logs/cron.log 2>&1'

mkdir -p "$WORKSPACE/logs"

CUR=$(crontab -l 2>/dev/null || true)
CUR=$(printf '%s\n' "$CUR" | grep -v 'send_status.py' || true)

if printf '%s\n' "$CUR" | grep -qF 'check_due.py'; then
  echo "cron entry already present: check_due.py"
else
  CUR=$(printf '%s\n%s\n' "$CUR" "$CHECKDUE")
  echo "cron entry installed: check_due.py"
fi

if printf '%s\n' "$CUR" | grep -qF 'daily_email_session.sh'; then
  echo "cron entry already present: daily_email_session.sh"
else
  CUR=$(printf '%s\n%s\n' "$CUR" "$DAILYEMAIL")
  echo "cron entry installed: daily_email_session.sh"
fi

CUR=$(printf '%s\n' "$CUR" | sed '/^$/d')
printf '%s\n' "$CUR" | crontab -

crontab -l