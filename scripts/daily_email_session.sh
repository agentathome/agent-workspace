#!/bin/bash
# daily_email_session.sh — 每日状态邮件（会话驱动版）
# cron 每日 08:30 触发：启动一个"新会话"，由 Agent 做系统检查、更新 handoff、再发状态邮件。
# 与 check_due.py 共享 tmp/agent.lock，避免与延续会话并发。
set -u

WORKSPACE=/home/home/workspace
LOCK=$WORKSPACE/tmp/agent.lock
LOG=$WORKSPACE/logs/daily-email-$(date +%Y%m%d-%H%M%S).log
CRONLOG=$WORKSPACE/logs/cron.log

export HOME=/home/home
export PATH="/home/home/.opencode/bin:/usr/local/bin:/usr/bin:/bin"

mkdir -p "$WORKSPACE/logs"

exec 9>"$LOCK"
flock -n 9 || { echo "$(date '+%F %T') daily email session already running, skip" >> "$CRONLOG"; exit 1; }

echo "$(date '+%F %T') daily email session start" >> "$LOG"
/home/home/.opencode/bin/opencode run \
  --dir "$WORKSPACE" \
  --auto \
  --title "daily-email-$(date +%Y%m%d-%H%M%S)" \
  "你是这台电脑的管理 Agent（身份与权限见 workspace/agent.md）。这是每日状态邮件的定时会话，新会话、无对话历史。请按顺序完成：

1. 阅读 workspace/handoff.md 与 workspace/memories/ 下的记忆，恢复当前状态与待办；
2. 快速系统检查并写入 handoff.md「当前状态」：磁盘(df -h /)、内存(free -h)、网络与公网 IP、关键服务/定时任务是否正常，以及今日安全更新情况；
3. 处理「下次任务」中的待办（只做不依赖 sudo 的操作；需要 sudo 的记入 handoff.md「需要 sudo 的事项」）；
4. 调用 scripts/send_status.py 发送每日状态邮件（收件人默认来自 secrets/agentmail.env）；
5. 更新 handoff.md：更新时间、状态、当前状态、下次任务、下次运行（下次邮件由 cron 触发，无需继续则清空）；
6. 简要汇报本次邮件与检查结果。" >> "$LOG" 2>&1
rc=$?

echo "$(date '+%F %T') daily email session end rc=$rc" >> "$LOG"
exit $rc