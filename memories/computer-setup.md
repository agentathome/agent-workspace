# 电脑基本配置

记录于：2026-08-15
更新于：2026-08-15

## 系统信息
- 平台：Linux (Ubuntu 26.04 LTS, 内核 7.0.0-29-generic)
- 机型：Lenovo YOGA 720
- 家目录：`/home/home/`
- 磁盘：233G（可用 209G）
- 内存：3.2G（可用约 1.5G）
- 交换：3.7G（已用 885M）

## 网络
- IP：192.168.0.127/24 (wlan0)
- 网关：待探测
- DNS：待探测

## 工作区
- 目录：`/home/home/workspace/`
- 子目录：`projects/`, `scripts/`, `memories/`, `tmp/`, `logs/`, `secrets/`
- secrets/ 存凭据（agentmail.env、github.env），目录 700 文件 600，绝不推送 GitHub
- opencode 数据：`/home/home/.local/share/opencode/opencode.db`
- agent 意图：`/home/home/workspace/agent.md`
- opencode 默认模型：`opencode/deepseek-v4-flash-free`（OpenCode Zen 免费，`~/.config/opencode/opencode.jsonc`）

## 资源约束
- ⚠️ RAM 较小（3.2G，可用约 1.5G）
- 不要运行重任务（编译大项目、多并行进程、大型模型/服务）
- 不要安装重软件（IDE、桌面级 GUI、大型运行时等）
- 优先轻量替代：如 `micro`/`nano` 而非 VS Code，`sqlite` 而非重型 DB

## 已安装工具
- 网络：ip, ss, curl, ping, dig, tcpdump, nc, ncat
- 系统：jq, rsync, strace, lsof, screen, less
- 语言：python3
- 版本控制：git 2.53.0
- 包管理：apt

## Sudo 状态
- 已配置 apt 白名单免密：`/etc/sudoers.d/agent-apt` 放行 `/usr/bin/apt-get, /usr/bin/apt, /usr/bin/dpkg`
- 其余 sudo 命令仍需交互式密码认证
