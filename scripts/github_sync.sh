#!/bin/bash
# github_sync.sh — 用 git 把工作区备份到 GitHub（secrets/ 由 .gitignore 排除，绝不推送）
# 用法: bash scripts/github_sync.sh [提交信息]
set -euo pipefail

WORKSPACE=/home/home/workspace
cd "$WORKSPACE"

msg="${1:-sync: $(date '+%Y-%m-%d %H:%M')}"

if [ -z "$(git status --porcelain)" ]; then
  echo "工作区无改动，跳过"
  exit 0
fi

git add -A
git commit -q -m "$msg" || { echo "提交失败"; exit 1; }
git push -q origin main
echo "已推送到 https://github.com/agentathome/agent-workspace"

if git status --porcelain | grep -q .; then
  echo "注意：仍有未提交/未推送文件"
fi