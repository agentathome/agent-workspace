#!/bin/bash
# run_session.sh — 持锁启动一个定时延续会话（同一个电脑管理 Agent 的新会话）
set -u

WORKSPACE=/home/home/workspace
LOCK=$WORKSPACE/tmp/agent.lock
RETRY=$WORKSPACE/tmp/agent.retry
LOG=$WORKSPACE/logs/session-$(date +%Y%m%d-%H%M%S).log

export HOME=/home/home
export PATH="/home/home/.opencode/bin:/usr/local/bin:/usr/bin:/bin"

mkdir -p "$WORKSPACE/logs"

exec 9>"$LOCK"
flock -n 9 || { echo "$(date '+%F %T') session already running, skip" >> "$WORKSPACE/logs/cron.log"; exit 1; }

echo "$(date '+%F %T') session start" >> "$LOG"
/home/home/.opencode/bin/opencode run \
  --dir "$WORKSPACE" \
  --auto \
  --title "scheduled-$(date +%Y%m%d-%H%M%S)" \
  "你是这台电脑的管理 Agent（身份与权限见 workspace/agent.md）。本次是延续上次会话的新会话，没有对话历史。请先用 python3 scripts/mem.py dump 阅读 workspace/memories/（SQLite 记忆库 memory.db）与 workspace/handoff.md，恢复当前状态和任务，然后继续或完成维护工作。只做不依赖 sudo 的操作；需要 sudo 的事项写入 handoff.md 的'需要 sudo 的事项'。完成后更新 handoff.md：更新时间、状态、当前状态、下次任务、下次运行（无需继续则清空），并简要汇报结果。" >> "$LOG" 2>&1
rc=$?

echo "$(date '+%F %T') session end rc=$rc" >> "$LOG"
if [ "$rc" -eq 0 ]; then
  rm -f "$RETRY"
fi
exit $rc