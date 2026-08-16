# 电脑基本配置

记录于：2026-08-15
更新于：2026-08-15

## WireGuard VPN（服务端）
- 已部署：本机为服务端，`/etc/wireguard/wg0.conf`，`systemctl enable wg-quick@wg0` 开机自启
- 监听：UDP 51820（IPv4/IPv6），路由器已端口转发 → 192.168.0.116
- VPN 网段：10.0.0.0/24（服务端 10.0.0.1，客户端 10.0.0.2）
- IP 转发已开（/etc/sysctl.d/99-wireguard.conf），NAT 由 wg0.conf 的 PostUp/PreDown 管理
- 客户端配置：workspace/secrets/wireguard/client.conf（含二维码 client-qr.png，600）
- 端点用公网 IP 36.24.251.10（可能变化，建议 DDNS）
- 查看状态：`sudo wg show`
- 主网卡为 enx000ec65c1161（以太网），wlan0 备用

## 系统信息
- 平台：Linux (Ubuntu 26.04 LTS, 内核 7.0.0-29-generic)
- 机型：Lenovo YOGA 720
- 家目录：`/home/home/`
- 磁盘：233G（可用 209G）
- 内存：3.2G（可用约 1.5G）
- 交换：3.7G（已用 885M）

## 网络
- IP：192.168.0.116/24 (enx000ec65c1161，以太网主用；wlan0 备用)
- 网关：192.168.0.1
- DNS：127.0.0.53（systemd-resolved）

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
