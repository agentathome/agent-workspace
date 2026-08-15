#!/usr/bin/env bash
# wireguard_setup.sh — 部署 WireGuard 服务端（需要 root）
# 用法: sudo bash scripts/wireguard_setup.sh
set -euo pipefail

WG_SRC=/home/home/workspace/secrets/wireguard/wg0.conf
WG_DST=/etc/wireguard/wg0.conf
SYSCTL=/etc/sysctl.d/99-wireguard.conf

echo "==> 安装配置到 /etc/wireguard"
install -m 600 -D "$WG_SRC" "$WG_DST"

echo "==> 开启 IP 转发"
sysctl -w net.ipv4.ip_forward=1 >/dev/null
printf 'net.ipv4.ip_forward = 1\n' > "$SYSCTL"

echo "==> 启动并开机自启 wg-quick@wg0"
systemctl enable --now wg-quick@wg0

echo "==> 状态"
wg show

echo
echo "服务端已就绪。请到路由器配置端口转发:"
echo "  协议 UDP, 外网端口 51820 -> 192.168.0.116:51820"