# 邮件与代码备份

记录于：2026-08-15
更新于：2026-08-15

## 状态邮件
- 每日 08:30 cron：`python3 /home/home/workspace/scripts/send_status.py` → 把 handoff.md「当前状态」发到 `zyx20031020@gmail.com`
- 发送方：AgentMail `agentathome@agentmail.to`（smtp.agentmail.to:465 SSL，用户名=邮箱，密码=API key）
- 脚本：`scripts/send_status.py`；凭据：`secrets/agentmail.env`（600，工作区内）

## GitHub 备份
- 账号：`agentathome`（2026-08-15 创建，密码认证已被 GitHub 停用，用 fine-grained PAT）
- `scripts/github_sync.sh`：REST API 把 handoff.md/agent.md/memories/脚本 备份到私有仓库 `agent-workspace`（本地未装 git，走 contents API，**已激活**，8 个文件已同步）
- 凭据：`secrets/github.env` 的 GITHUB_TOKEN（600，工作区内）

## 自行 commit 规则
- **大更改/阶段性成果后才运行 `scripts/github_sync.sh`** 备份到 GitHub（相当于"commit 自己"）
- 小改动不频繁同步，避免刷屏式提交
- secrets/ 绝不推送（脚本白名单已排除）