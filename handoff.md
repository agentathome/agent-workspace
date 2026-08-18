# Handoff — 会话交接

更新时间: 2026-08-18T08:32:00
下次运行: 
状态: idle              # idle | paused

## 当前状态

**今日系统检查（2026-08-18 08:31）**
- 磁盘：/ 233G，已用 13G（6%），可用 209G — 正常
- 内存：3.2G 总，已用 1.5G，可用 1.7G；交换 3.7G（用 670M）— 正常（RAM 偏小注意）
- 网络：enx000ec65c1161 以太网 192.168.0.116/24 UP，网关 192.168.0.1；wg0 10.0.0.1 UP；wlan0 DOWN（备用）；公网 IP **36.27.54.137**（ifconfig.me/icanhazip.com 双源确认，**较上次 36.24.251.10 有变化**）
- 服务：cron active、wg-quick@wg0 active、ssh active；负载 0.16，运行 2天13小时
- 定时任务：`* * * * * check_due.py` 与 `30 8 * * * daily_email_session.sh` 均在 crontab，cron 正常
- 今日安全更新：**7 个更新仍被 phased rollout 推迟**（grub-common、grub2-common、nautilus、nautilus-data、libnautilus-extension4、software-properties-common、python3-software-properties），无新增，未强制安装（见「需要 sudo 的事项」）
- 其他：wireguard 连接未现场验证（需 sudo wg show）

**历史状态**
- **公网 IP 已变化并同步**：36.24.251.10 → 36.27.54.137（2026-08-18）。secrets/wireguard/client.conf 与 client-qr.png 已更新为新 Endpoint（备份为 .bak），服务端 wg0.conf 无需改；记忆库已记录
- **GitHub 查询 MCP 已安装**：`scripts/github_mcp.py`（零依赖，走 GitHub REST API，token 自读 secrets/github.env），已注册到 `~/.config/opencode/opencode.jsonc` 的 `mcp.github`；**需重启 opencode 后生效**。工具：search_repos / get_repo / list_repo_files / get_file
- **记忆检索已升级**：mem.py 增加 FTS5(trigram) 索引 + BM25×时间衰减×importance 排序 + origin 溯源；schema v2（importance/origin 列，触发器同步索引）
- **记忆已迁移到 SQLite**：memories/*.md 已删除，改存 `memories/memory.db`，读写用 `scripts/mem.py`（dump/list/get/set/search）；README 与各会话 prompt 已同步
- **每日状态邮件已改为会话驱动**：08:30 cron 触发 `scripts/daily_email_session.sh` 启动新会话，Agent 做系统检查→更新 handoff→调 `send_status.py` 发信；`send_status.py` 只负责 SMTP 收发
- 修复 `scripts/check_due.py` 正则 bug：`下次运行` 为空时误跨行匹配到「状态:」，导致每分钟刷 `bad next_run`（改 `\s*` 为 `[ \t]*`）
- 系统更新：检查发现 7 个安全更新（grub-common/grub2-common、nautilus、software-properties-common），属 phased rollout 被 `apt-get upgrade` 推迟，暂未安装
- GitHub 备份：**弃用同步脚本，直接 git**（`git add -A && git commit -m "..." && git push`），工作区=仓库(main)，凭据 secrets/git-credentials(600)，secrets/tmp/logs 由 .gitignore 排除
- WireGuard VPN 已部署并验证通过：外部设备握手成功，服务端开机自启，详见记忆库（`python3 scripts/mem.py get computer-setup "WireGuard VPN（服务端）"`）
- 每日状态邮件现包含公网 IP（send_status.py 顶部，多服务源容错）
- 默认模型已改为 opencode/deepseek-v4-flash-free（OpenCode Zen 免费），交互与定时会话一致
- 邮件链路已通：每日 08:30 状态邮件发至 zyx20031020@gmail.com（AgentMail agentathome@agentmail.to 发送）
- GitHub 备份已激活：**公开仓库** agentathome/agent-workspace，Stevenkerman27 已加为合作者（待接受邀请）；secrets/ 绝不推送
- commit 策略：大更改/阶段性成果才 git commit + push，小改动不刷屏
- sudo：已配 apt 白名单免密（/etc/sudoers.d/agent-apt），git 2.53.0 已装
- 凭据位置：workspace/secrets/（600，勿外泄）
## 下次任务

（无待办事项。公网 IP 变化已处理：client.conf/QR 已同步更新）

## 需要 sudo 的事项

- （可选）强制安装被 phased rollout 推迟的 7 个安全更新：`sudo apt-get install -y grub-common grub2-common nautilus nautilus-data libnautilus-extension4 software-properties-common python3-software-properties`；不急可等自动推送
- （可选）验证 WireGuard 连接：`sudo wg show`（确认服务端在公网 IP 36.27.54.137 变化后仍正常握手）；若客户端使用旧 QR 需重新同步 client-qr.png

## 说明

- 每次会话结束前必须更新：更新时间、状态、当前状态、下次任务、下次运行
- 定时会话是与当前会话相同的电脑管理 Agent 的新会话（身份见 agent.md），靠本文件 + 记忆库 memories/memory.db（scripts/mem.py）恢复状态