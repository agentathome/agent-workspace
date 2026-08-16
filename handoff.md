# Handoff — 会话交接

更新时间: 2026-08-16T11:20:00
下次运行: 
状态: idle              # idle | paused

## 当前状态
- **每日状态邮件已改为会话驱动**：08:30 cron 触发 `scripts/daily_email_session.sh` 启动新会话，Agent 做系统检查→更新 handoff→调 `send_status.py` 发信；`send_status.py` 只负责 SMTP 收发
- 修复 `scripts/check_due.py` 正则 bug：`下次运行` 为空时误跨行匹配到「状态:」，导致每分钟刷 `bad next_run`（改 `\s*` 为 `[ \t]*`）
- 系统更新：检查发现 7 个安全更新（grub-common/grub2-common、nautilus、software-properties-common），属 phased rollout 被 `apt-get upgrade` 推迟，暂未安装
- GitHub 备份：**弃用同步脚本，直接 git**（`git add -A && git commit -m "..." && git push`），工作区=仓库(main)，凭据 secrets/git-credentials(600)，secrets/tmp/logs 由 .gitignore 排除
- WireGuard VPN 已部署并验证通过：外部设备握手成功（endpoint 36.28.4.138:58123），服务端开机自启，详见 memories/computer-setup.md
- 每日状态邮件现包含公网 IP（send_status.py 顶部，多服务源容错）
- 默认模型已改为 opencode/deepseek-v4-flash-free（OpenCode Zen 免费），交互与定时会话一致
- 邮件链路已通：每日 08:30 状态邮件发至 zyx20031020@gmail.com（AgentMail agentathome@agentmail.to 发送）
- GitHub 备份已激活：**公开仓库** agentathome/agent-workspace，Stevenkerman27 已加为合作者（待接受邀请）；secrets/ 绝不推送
- commit 策略：大更改/阶段性成果才 git commit + push，小改动不刷屏
- sudo：已配 apt 白名单免密（/etc/sudoers.d/agent-apt），git 2.53.0 已装
- 凭据位置：workspace/secrets/（600，勿外泄）
## 下次任务

（测试任务已完成，无待办事项）

## 需要 sudo 的事项

- （可选）强制安装被 phased rollout 推迟的 7 个安全更新：`sudo apt-get install -y grub-common grub2-common nautilus nautilus-data libnautilus-extension4 software-properties-common python3-software-properties`；不急可等自动推送

## 说明

- 每次会话结束前必须更新：更新时间、状态、当前状态、下次任务、下次运行
- 定时会话是与当前会话相同的电脑管理 Agent 的新会话（身份见 agent.md），靠本文件 + memories/ 恢复状态