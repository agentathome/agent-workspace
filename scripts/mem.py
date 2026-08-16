#!/usr/bin/env python3
"""mem.py — 长期记忆 SQLite 数据库（memories/memory.db）管理 CLI。

设计：
  - categories: 分类（原 .md 文件名），description 存标题
  - topics:     每个 "## 小节" 一条，content 为正文（纯文本/列表）
  - meta:       分类级元数据（记录于/更新于/说明等），key = "<category>:<字段>"

用法：
  python3 scripts/mem.py dump [category]       # 输出可读全文（供 Agent 阅读）
  python3 scripts/mem.py list                  # 列出分类与小节
  python3 scripts/mem.py get <category> [topic]
  python3 scripts/mem.py set <category> <topic> [-c 内容 | 从 stdin 读]
  python3 scripts/mem.py rm <category> [topic]
  python3 scripts/mem.py search <文本>
  python3 scripts/mem.py meta get <key> | meta set <key> <value>
  python3 scripts/mem.py migrate               # 从 memories/*.md 导入（一次性）

依赖：python3 标准库（sqlite3）。
"""
import argparse
import os
import re
import sqlite3
import sys

WORKSPACE = "/home/home/workspace"
DB = os.path.join(WORKSPACE, "memories", "memory.db")
MEMORIES_DIR = os.path.join(WORKSPACE, "memories")
SCHEMA_VERSION = "1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS categories (
    category TEXT PRIMARY KEY,
    description TEXT
);
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(category, topic)
);
"""


def connect():
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def now():
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def meta_set(conn, key, value):
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def meta_get(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def upsert_topic(conn, category, topic, content):
    conn.execute(
        "INSERT INTO topics(category, topic, content, updated_at) VALUES(?, ?, ?, ?) "
        "ON CONFLICT(category, topic) DO UPDATE SET content=excluded.content, "
        "updated_at=excluded.updated_at",
        (category, topic, content, now()),
    )
    conn.commit()


def list_categories(conn):
    return conn.execute(
        "SELECT c.category, c.description, COUNT(t.id) "
        "FROM categories c LEFT JOIN topics t ON t.category=c.category "
        "GROUP BY c.category ORDER BY c.category"
    ).fetchall()


def dump_category(conn, category):
    desc = conn.execute(
        "SELECT description FROM categories WHERE category=?", (category,)
    ).fetchone()
    out = [f"# {desc[0] if desc and desc[0] else category}"]
    dates = []
    for key in ("记录于", "更新于"):
        v = meta_get(conn, f"{category}:{key}")
        if v:
            dates.append(f"{key}：{v}")
    note = meta_get(conn, f"{category}:说明")
    if dates or note:
        out.append("")
        out.extend(dates)
        if note:
            out.append(note)
    rows = conn.execute(
        "SELECT topic, content FROM topics WHERE category=? ORDER BY id", (category,)
    ).fetchall()
    if rows:
        out.append("")
        out.append("\n\n".join(f"## {topic}\n{content}" for topic, content in rows))
    return "\n".join(out) + "\n"


def cmd_dump(args):
    conn = connect()
    if args.category:
        rows = conn.execute(
            "SELECT 1 FROM categories WHERE category=?", (args.category,)
        ).fetchone()
        if not rows:
            print(f"错误: 无此分类 {args.category}（可用 list 查看）")
            return 2
        sys.stdout.write(dump_category(conn, args.category))
    else:
        for (category, _d, _n) in list_categories(conn):
            sys.stdout.write(dump_category(conn, category))
            print("---")
    return 0


def cmd_list(_args):
    conn = connect()
    for category, desc, n in list_categories(conn):
        print(f"{category}  ({n} 小节)" + (f"  # {desc}" if desc else ""))
        rows = conn.execute(
            "SELECT topic FROM topics WHERE category=? ORDER BY id", (category,)
        ).fetchall()
        for (topic,) in rows:
            print(f"  - {topic}")
    return 0


def cmd_get(args):
    conn = connect()
    if args.topic:
        row = conn.execute(
            "SELECT content FROM topics WHERE category=? AND topic=?",
            (args.category, args.topic),
        ).fetchone()
        if not row:
            print(f"错误: 无此小节 {args.category}/{args.topic}")
            return 2
        print(row[0])
    else:
        if not conn.execute(
            "SELECT 1 FROM categories WHERE category=?", (args.category,)
        ).fetchone():
            print(f"错误: 无此分类 {args.category}")
            return 2
        sys.stdout.write(dump_category(conn, args.category))
    return 0


def cmd_set(args):
    conn = connect()
    content = args.content
    if content is None:
        content = sys.stdin.read().strip()
    if not content:
        print("错误: 内容为空（用 -c 指定或从 stdin 传入）")
        return 2
    conn.execute(
        "INSERT INTO categories(category, description) VALUES(?, ?) "
        "ON CONFLICT(category) DO NOTHING",
        (args.category, args.category),
    )
    upsert_topic(conn, args.category, args.topic, content)
    print(f"已写入 {args.category}/{args.topic}")
    return 0


def cmd_rm(args):
    conn = connect()
    if args.topic:
        cur = conn.execute(
            "DELETE FROM topics WHERE category=? AND topic=?", (args.category, args.topic)
        )
    else:
        cur = conn.execute("DELETE FROM topics WHERE category=?", (args.category,))
        conn.execute("DELETE FROM categories WHERE category=?", (args.category,))
    conn.commit()
    print(f"已删除 {cur.rowcount} 条（{args.category}"
          + (f"/{args.topic}" if args.topic else "") + "）")
    return 0


def cmd_search(args):
    conn = connect()
    like = f"%{args.text}%"
    rows = conn.execute(
        "SELECT category, topic, content FROM topics WHERE content LIKE ? ORDER BY id",
        (like,),
    ).fetchall()
    if not rows:
        print("无匹配")
        return 0
    for category, topic, content in rows:
        print(f"{category}/{topic}:")
        print(content[:500] + ("…" if len(content) > 500 else ""))
        print()
    return 0


def cmd_meta(args):
    conn = connect()
    if args.sub == "get":
        v = meta_get(conn, args.key)
        print(v if v is not None else "")
        return 0
    if args.sub == "set":
        meta_set(conn, args.key, args.value)
        print(f"meta {args.key} = {args.value}")
        return 0
    print("用法: mem.py meta get|set <key> [value]")
    return 2


def cmd_migrate(_args):
    """从 memories/*.md 导入（跳过 README.md、memory.db）。"""
    conn = connect()
    imported = 0
    for fname in sorted(os.listdir(MEMORIES_DIR)):
        if not fname.endswith(".md") or fname == "README.md":
            continue
        category = fname[:-3]
        text = open(os.path.join(MEMORIES_DIR, fname), encoding="utf-8").read()
        m_title = re.search(r"^# (.+)$", text, re.M)
        if m_title:
            conn.execute(
                "INSERT INTO categories(category, description) VALUES(?, ?) "
                "ON CONFLICT(category) DO UPDATE SET description=excluded.description",
                (category, m_title.group(1).strip()),
            )
        for key in ("记录于", "更新于"):
            m = re.search(rf"^{key}[：:]\s*(\S+)", text, re.M)
            if m:
                meta_set(conn, f"{category}:{key}", m.group(1))
        lines = text.splitlines()
        head = []
        sections = []
        cur = None
        for line in lines:
            m = re.match(r"^## (.+)$", line)
            if m:
                cur = [m.group(1).strip(), []]
                sections.append(cur)
            elif cur is not None:
                cur[1].append(line)
            else:
                head.append(line)
        head = [l for l in head if not l.startswith(("#", "记录于", "更新于"))]
        if "".join(head).strip():
            meta_set(conn, f"{category}:说明", "\n".join(head).strip())
        for topic, content_lines in sections:
            content = "\n".join(content_lines).strip()
            if topic and content:
                upsert_topic(conn, category, topic, content)
                imported += 1
    conn.commit()
    print(f"迁移完成：导入 {imported} 小节，库文件 {DB}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="长期记忆 SQLite 管理")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in (
        ("dump", "输出全文"),
        ("list", "列出分类"),
        ("get", "读取小节/分类"),
        ("set", "写入小节"),
        ("rm", "删除"),
        ("search", "全文搜索"),
        ("meta", "元数据"),
        ("migrate", "从 .md 导入"),
    ):
        p = sub.add_parser(name, help=help_)
        if name == "dump":
            p.add_argument("category", nargs="?")
        elif name == "get":
            p.add_argument("category")
            p.add_argument("topic", nargs="?")
        elif name == "set":
            p.add_argument("category")
            p.add_argument("topic")
            p.add_argument("-c", "--content")
        elif name == "rm":
            p.add_argument("category")
            p.add_argument("topic", nargs="?")
        elif name == "search":
            p.add_argument("text")
        elif name == "meta":
            p.add_argument("sub", choices=("get", "set"))
            p.add_argument("key")
            p.add_argument("value", nargs="?")
    args = ap.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())