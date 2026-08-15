# 邮件与代码备份

记录于：2026-08-15
更新于：2026-08-15

## 状态邮件
- 每日 08:30 cron：`python3 /home/home/workspace/scripts/send_status.py` → 把 handoff.md「当前状态」发到 `zyx20031020@gmail.com`
- 发送方：AgentMail `agentathome@agentmail.to`（smtp.agentmail.to:465 SSL，用户名=邮箱，密码=API key）
- 脚本：`scripts/send_status.py`；凭据：`secrets/agentmail.env`（600，工作区内）

## GitHub 备份
- 账号：`agentathome`（2026-08-15 创建，密码认证已被 GitHub 停用，用 fine-grained PAT）
- 方式：**工作区即为 git 仓库**（main），远端 `https://github.com/agentathome/agent-workspace.git`，用 git 直接 add/commit/push
- `scripts/github_sync.sh`：git 封装脚本（`git add -A && commit && push`），沿用"commit 自己"习惯
- 凭据：git credential store 指向 `secrets/git-credentials`（600，工作区内），`secrets/`、`tmp/`、`logs/` 由 `.gitignore` 排除，绝不推送

## 自行 commit 规则
- **大更改/阶段性成果后才运行 `scripts/github_sync.sh`** 备份到 GitHub（相当于"commit 自己"）
- 小改动不频繁同步，避免刷屏式提交
- secrets/ 绝不推送（脚本白名单已排除）