#!/bin/bash
# github_sync.sh — 用 GitHub REST API 把工作区关键文件备份到私有仓库（无需本地 git）
set -uo pipefail

WORKSPACE=/home/home/workspace
SECRETS=$WORKSPACE/secrets/github.env
REPO=${GITHUB_REPO:-agent-workspace}
API=https://api.github.com

# 加载凭据
if [ ! -f "$SECRETS" ]; then
  echo "缺少 $SECRETS" >&2
  exit 1
fi
GITHUB_USER=$(grep '^GITHUB_USER=' "$SECRETS" | cut -d= -f2- | tr -d ' ')
GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' "$SECRETS" | cut -d= -f2- | tr -d ' ')
if [ -z "$GITHUB_TOKEN" ]; then
  echo "github.env 缺少 GITHUB_TOKEN（需 fine-grained PAT）" >&2
  exit 1
fi

auth() {
  curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" "$@"
}

# 1. 确保仓库存在（私有）
if ! auth "$API/repos/$GITHUB_USER/$REPO" | jq -e '.name' >/dev/null 2>&1; then
  echo "创建私有仓库 $REPO"
  auth -X POST "$API/user/repos" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$REPO\",\"private\":true,\"auto_init\":true}" >/dev/null || {
    echo "创建仓库失败" >&2; exit 1; }
fi

# 2. 需要读取的文件（存在才推送）。注意：secrets/ 目录绝不包含在内
mapfile -t FILES < <(
  {
    echo "$WORKSPACE/handoff.md"
    echo "$WORKSPACE/agent.md"
    find "$WORKSPACE/memories" -type f -name '*.md' 2>/dev/null
    echo "$WORKSPACE/scripts/send_status.py"
    echo "$WORKSPACE/scripts/check_due.py"
    echo "$WORKSPACE/scripts/run_session.sh"
  } 2>/dev/null | sort -u
)

# 3. 逐个上传（contents API，存在则带 sha 覆盖更新）
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  rel=${f#$WORKSPACE/}
  base64 -w0 < "$f" > /tmp/opencode/gh_content.b64 || base64 < "$f" > /tmp/opencode/gh_content.b64
  content=$(cat /tmp/opencode/gh_content.b64)
  msg="sync: $rel ($(date '+%F %T'))"
  sha=$(auth "$API/repos/$GITHUB_USER/$REPO/contents/$rel" | jq -r '.sha // empty')
  body=$(jq -n --arg m "$msg" --arg c "$content" --arg s "$sha" \
    '{message:$m, content:$c, sha:$s} | if .sha=="" then del(.sha) else . end')
  resp=$(auth -X PUT "$API/repos/$GITHUB_USER/$REPO/contents/$rel" \
    -H "Content-Type: application/json" \
    -d "$body")
  if echo "$resp" | jq -e '.commit.sha // .content.name' >/dev/null 2>&1; then
    echo "OK   $rel"
  else
    echo "FAIL $rel: $(echo "$resp" | jq -r '.message')"
  fi
done
rm -f /tmp/opencode/gh_content.b64

echo "同步完成: https://github.com/$GITHUB_USER/$REPO"