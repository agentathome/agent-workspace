# 邮件与代码备份

记录于：2026-08-15
更新于：2026-08-15

## 状态邮件
- **会话驱动**：每日 08:30 cron 触发 `scripts/daily_email_session.sh` 启动新会话，Agent 先做系统检查并更新 handoff.md「当前状态」，再调用 `scripts/send_status.py` 发邮件到 `zyx20031020@gmail.com`
- `send_status.py` 仅负责 SMTP 收发（内容/驱动由会话负责），默认收件人取 `secrets/agentmail.env` 的 `GMAIL_TO`
- 发送方：AgentMail `agentathome@agentmail.to`（smtp.agentmail.to:465 SSL，用户名=邮箱，密码=API key）
- 凭据：`secrets/agentmail.env`（600，工作区内）；cron 条目由 `scripts/install_cron.sh` 统一管理（旧 `30 8 * * * send_status.py` 条目已移除）

## GitHub 备份
- 账号：`agentathome`（2026-08-15 创建，密码认证已被 GitHub 停用，用 fine-grained PAT）
- 方式：**工作区即为 git 仓库**（main），远端 `https://github.com/agentathome/agent-workspace.git`，直接 `git add -A && git commit -m "..." && git push`，不再用同步脚本
- 凭据：git credential store 指向 `secrets/git-credentials`（600，工作区内），`secrets/`、`tmp/`、`logs/` 由 `.gitignore` 排除，绝不推送

## 自行 commit 规则
- **大更改/阶段性成果后才 git commit + push** 备份到 GitHub（相当于"commit 自己"）
- 小改动不频繁同步，避免刷屏式提交
- secrets/ 绝不推送（.gitignore 已排除）