#!/usr/bin/env python3
"""mem.py — 长期记忆 SQLite 数据库（memories/memory.db）管理 CLI。

设计（借鉴 OpenClaw 记忆引擎）：
  - categories: 分类（原 .md 文件名），description 存标题
  - topics:     每个 "## 小节" 一条，content 为正文；importance(1-10) 写时加权，origin 溯源（owner/agent/untrusted/system）
  - topics_fts: FTS5(trigram) 全文索引，经触发器自动同步
  - 检索排序 = BM25 × 时间衰减(30 天半衰期) × importance 权重

用法：
  python3 scripts/mem.py dump [category]       # 输出可读全文（供 Agent 阅读）
  python3 scripts/mem.py list                  # 列出分类与小节
  python3 scripts/mem.py get <category> [topic]
  python3 scripts/mem.py set <category> <topic> [-c 内容 | 从 stdin 读] [-i 重要性1-10] [-o origin]
  python3 scripts/mem.py rm <category> [topic]
  python3 scripts/mem.py search <文本> [-n 条数]
  python3 scripts/mem.py meta get <key> | meta set <key> <value>
  python3 scripts/mem.py migrate               # 从 memories/*.md 导入（一次性）

依赖：python3 标准库（sqlite3，FTS5 trigram）。
"""
import argparse
import os
import re
import sqlite3
import sys

WORKSPACE = "/home/home/workspace"
DB = os.path.join(WORKSPACE, "memories", "memory.db")
MEMORIES_DIR = os.path.join(WORKSPACE, "memories")
SCHEMA_VERSION = "2"

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
    importance INTEGER,
    origin TEXT NOT NULL DEFAULT 'agent',
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(category, topic)
);
CREATE VIRTUAL TABLE IF NOT EXISTS topics_fts USING fts5(
    category, topic, content,
    content=topics, content_rowid=id,
    tokenize='trigram'
);
CREATE TRIGGER IF NOT EXISTS topics_ai AFTER INSERT ON topics BEGIN
    INSERT INTO topics_fts(rowid, category, topic, content)
    VALUES (new.id, new.category, new.topic, new.content);
END;
CREATE TRIGGER IF NOT EXISTS topics_ad AFTER DELETE ON topics BEGIN
    INSERT INTO topics_fts(topics_fts, rowid, category, topic, content)
    VALUES ('delete', old.id, old.category, old.topic, old.content);
END;
CREATE TRIGGER IF NOT EXISTS topics_au AFTER UPDATE ON topics BEGIN
    INSERT INTO topics_fts(topics_fts, rowid, category, topic, content)
    VALUES ('delete', old.id, old.category, old.topic, old.content);
    INSERT INTO topics_fts(rowid, category, topic, content)
    VALUES (new.id, new.category, new.topic, new.content);
END;
"""


def connect():
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    version = row[0] if row else None
    if version is None:
        conn.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
    elif version == "1":
        conn.execute("ALTER TABLE topics ADD COLUMN importance INTEGER")
        conn.execute("ALTER TABLE topics ADD COLUMN origin TEXT NOT NULL DEFAULT 'agent'")
        conn.execute("INSERT INTO topics_fts(topics_fts) VALUES('rebuild')")
        conn.execute("UPDATE meta SET value=? WHERE key='schema_version'", (SCHEMA_VERSION,))
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


def upsert_topic(conn, category, topic, content, importance=None, origin="agent"):
    conn.execute(
        "INSERT INTO topics(category, topic, content, importance, origin, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(category, topic) DO UPDATE SET content=excluded.content, "
        "importance=excluded.importance, origin=excluded.origin, "
        "updated_at=excluded.updated_at",
        (category, topic, content, importance, origin, now()),
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
    if args.importance is not None and not 1 <= args.importance <= 10:
        print("错误: importance 需在 1-10 之间")
        return 2
    conn.execute(
        "INSERT INTO categories(category, description) VALUES(?, ?) "
        "ON CONFLICT(category) DO NOTHING",
        (args.category, args.category),
    )
    upsert_topic(
        conn, args.category, args.topic, content,
        importance=args.importance, origin=args.origin,
    )
    print(f"已写入 {args.category}/{args.topic}"
          + (f" (importance={args.importance}, origin={args.origin})"
             if args.importance is not None else ""))
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


def fts_search(conn, text, limit=10):
    tokens = [
        re.sub(r'["*\\]', "", t)
        for t in re.split(r"\s+", text.strip())
        if len(t) >= 3
    ]
    if tokens:
        match = " AND ".join(f'"{t}"' for t in tokens)
        try:
            rows = conn.execute(
                "SELECT t.category, t.topic, t.content, "
                "(-bm25(topics_fts, 1.0, 2.0, 1.0)) * "
                "pow(0.5, (julianday('now','localtime') - julianday(t.updated_at)) / 30.0) * "
                "COALESCE(t.importance, 5) / 5.0 AS score "
                "FROM topics_fts f JOIN topics t ON t.id = f.rowid "
                "WHERE topics_fts MATCH ? ORDER BY score DESC LIMIT ?",
                (match, limit),
            ).fetchall()
            if rows:
                return rows
        except sqlite3.OperationalError:
            pass
    like = f"%{text}%"
    return conn.execute(
        "SELECT category, topic, content, 0.0 AS score FROM topics "
        "WHERE content LIKE ? OR topic LIKE ? "
        "ORDER BY updated_at DESC LIMIT ?",
        (like, like, limit),
    ).fetchall()


def cmd_search(args):
    conn = connect()
    rows = fts_search(conn, args.text, limit=args.n)
    if not rows:
        print("无匹配")
        return 0
    for category, topic, content, score in rows:
        print(f"{category}/{topic}" + (f"  (score {score:.2f})" if score else ""))
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
            p.add_argument("-i", "--importance", type=int,
                          help="重要性 1-10（影响搜索排序，默认中性 5）")
            p.add_argument("-o", "--origin", default="agent",
                          help="溯源：owner/agent/untrusted/system")
        elif name == "rm":
            p.add_argument("category")
            p.add_argument("topic", nargs="?")
        elif name == "search":
            p.add_argument("text")
            p.add_argument("-n", type=int, default=10)
        elif name == "meta":
            p.add_argument("sub", choices=("get", "set"))
            p.add_argument("key")
            p.add_argument("value", nargs="?")
    args = ap.parse_args()
    return globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())