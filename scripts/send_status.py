#!/usr/bin/env python3
"""send_status.py — 通过 AgentMail SMTP 把 handoff.md 当前状态发给指定 Gmail。

用法:
    send_status.py [--to user@gmail.com] [--subject 主题]
                    [--file /path/to/report.txt] [--dry-run]

凭据从 ~/.config/opencode/secrets/agentmail.env 读取（权限 600）。
"""
import argparse
import os
import re
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText

WORKSPACE = "/home/home/workspace"
SECRETS = os.path.join(WORKSPACE, "secrets", "agentmail.env")
HANDOFF = os.path.join(WORKSPACE, "handoff.md")
LOG = os.path.join(WORKSPACE, "logs", "status-mail.log")


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


PUBLIC_IP_SERVICES = (
    "https://api.ipify.org",
    "https://ifconfig.me",
    "https://icanhazip.com",
)


def get_public_ip():
    import urllib.request

    for url in PUBLIC_IP_SERVICES:
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                ip = r.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None


def build_body():
    sections = []
    ip = get_public_ip()
    ip_line = f"公网 IP: {ip}" if ip else "公网 IP: （获取失败）"
    sections.append(ip_line)
    if os.path.exists(HANDOFF):
        text = open(HANDOFF, encoding="utf-8").read()
        for title in ("当前状态", "下次任务", "需要 sudo 的事项"):
            m = re.search(rf"^## {title}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m and m.group(1).strip():
                sections.append(f"## {title}\n{m.group(1).strip()}")
    return "\n\n".join(sections) if sections else "（handoff.md 暂无内容）"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to")
    ap.add_argument("--subject")
    ap.add_argument("--file", help="额外附件内容文件（可选）")
    ap.add_argument("--dry-run", action="store_true", help="只打印不发送")
    args = ap.parse_args()

    env = load_env(SECRETS)
    to_addr = args.to or env.get("GMAIL_TO")
    subject = args.subject or f"状态报告 {datetime.now():%Y-%m-%d %H:%M}"

    body = build_body()
    if args.file and os.path.exists(args.file):
        extra = open(args.file, encoding="utf-8").read().strip()
        if extra:
            body += "\n\n---\n\n" + extra

    if not to_addr:
        print("错误: 未提供收件人 (--to 或 agentmail.env 的 GMAIL_TO)")
        sys.exit(2)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = env["AGENTMAIL_INBOX"]
    msg["To"] = to_addr

    if args.dry_run:
        print(f"[dry-run] 收件人={to_addr}\n主题={subject}\n正文:\n{body}")
        return

    if not env.get("AGENTMAIL_API_KEY"):
        print("错误: agentmail.env 缺少 AGENTMAIL_API_KEY")
        sys.exit(2)

    try:
        with smtplib.SMTP_SSL(
            env["AGENTMAIL_SMTP_HOST"], int(env["AGENTMAIL_SMTP_PORT"]), timeout=30
        ) as server:
            server.login(env["AGENTMAIL_INBOX"], env["AGENTMAIL_API_KEY"])
            server.send_message(msg)
    except Exception as e:
        log(f"FAIL to={to_addr} subject={subject} err={e}")
        print(f"发送失败: {e}")
        sys.exit(1)

    log(f"OK to={to_addr} subject={subject}")
    print(f"已发送到 {to_addr}")


if __name__ == "__main__":
    main()