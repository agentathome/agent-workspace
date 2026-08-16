#!/usr/bin/env python3
# check_due.py — cron 入口：解析 handoff.md，到期则持锁启动延续会话
import datetime
import os
import re
import subprocess
import sys

WORKSPACE = "/home/home/workspace"
HANDOFF = os.path.join(WORKSPACE, "handoff.md")
RETRY = os.path.join(WORKSPACE, "tmp", "agent.retry")
RUN_SESSION = os.path.join(WORKSPACE, "scripts", "run_session.sh")
MAX_RETRY = 3


def read_handoff():
    text = open(HANDOFF, encoding="utf-8").read()
    m_time = re.search(r"^下次运行:[ \t]*(\S+)", text, re.M)
    m_status = re.search(r"^状态:\s*(\S+)", text, re.M)
    next_run = m_time.group(1) if m_time else ""
    status = m_status.group(1) if m_status else "idle"
    return text, next_run, status


def write_handoff(text):
    open(HANDOFF, "w", encoding="utf-8").write(text)


def set_paused(text, note):
    new_text = re.sub(r"^状态:.*$", f"状态: paused", text, count=1, flags=re.M)
    if "暂停原因" not in new_text:
        new_text = re.sub(
            r"^(状态: paused)",
            r"\1\n暂停原因: " + note,
            new_text,
            count=1,
            flags=re.M,
        )
    return new_text


def main():
    try:
        text, next_run, status = read_handoff()
    except FileNotFoundError:
        print("no handoff.md")
        return

    if not next_run or status == "paused":
        return

    try:
        due_time = datetime.datetime.fromisoformat(next_run)
    except ValueError:
        print("bad next_run:", next_run)
        return

    if datetime.datetime.now() < due_time:
        return

    retries = 0
    if os.path.exists(RETRY):
        try:
            retries = int(open(RETRY).read().strip() or "0")
        except ValueError:
            retries = 0

    if retries >= MAX_RETRY:
        print("too many consecutive failures, pausing")
        write_handoff(set_paused(text, "连续失败超过 %d 次" % MAX_RETRY))
        return

    with open(RETRY, "w") as f:
        f.write(str(retries + 1))

    print("due, launching session")
    subprocess.run([RUN_SESSION])


if __name__ == "__main__":
    main()