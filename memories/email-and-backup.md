# 邮件与代码备份

记录于：2026-08-15

## 状态邮件
- 每日 08:30 cron：`python3 /home/home/workspace/scripts/send_status.py` → 把 handoff.md「当前状态」发到 `zyx20031020@gmail.com`
- 发送方：AgentMail `agentathome@agentmail.to`（smtp.agentmail.to:465 SSL，用户名=邮箱，密码=API key）
- 脚本：`scripts/send_status.py`；凭据：`~/.config/opencode/secrets/agentmail.env`（600）

## GitHub 备份
- 账号：`agentathome`（2026-08-15 创建，密码认证已被 GitHub 停用，需 PAT）
- `scripts/github_sync.sh`：REST API 把 handoff.md/agent.md/memories/脚本 备份到私有仓库 `agent-workspace`（本地未装 git，走 contents API）
- 待激活：fine-grained PAT 写入 `~/.config/opencode/secrets/github.env` 的 GITHUB_TOKEN