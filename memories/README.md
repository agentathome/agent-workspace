# Memories

本目录存放跨 agent 共享的长期记忆，存于轻量 SQLite 数据库 `memory.db`（由 `scripts/mem.py` 管理，无需安装额外依赖）。

## 使用

```bash
python3 scripts/mem.py list                # 列出分类与小节
python3 scripts/mem.py dump [分类]         # 输出全文（供 Agent 阅读）
python3 scripts/mem.py get <分类> [小节]   # 读取
python3 scripts/mem.py set <分类> <小节> -c "内容" [-i 重要性] [-o origin]   # 写入/更新（或从 stdin 读）
python3 scripts/mem.py search <文本> [-n 条数]   # 全文搜索（FTS5 + 时间衰减 + importance 排序）
python3 scripts/mem.py rm <分类> [小节]    # 删除
```

## 检索机制（借鉴 OpenClaw）

- **全文索引**：`topics_fts` 是 FTS5（trigram tokenizer）虚拟表，经触发器随 `topics` 自动增删改同步，中英文都可子串匹配
- **排序**：`BM25 相关度 × 时间衰减（30 天半衰期）× importance 权重`；importance 1-10 在写时用 `-i` 标注，缺省按中性 5 处理
- **短词回退**：查询词 <3 字符或 FTS 无命中时，自动回退到 `LIKE` 匹配
- **溯源**：`set` 可用 `-o` 标 origin（owner/agent/untrusted/system），缺省 agent

## 约定

- 分类名小写英文，如 `computer-setup`、`email-and-backup`
- 每个分类下以"小节"（topic）组织内容，如 `WireGuard VPN（服务端）`
- 如无必要不增加记忆条目，保持精简
- `memory.db` 提交到 git；`memory.db-wal` / `memory.db-shm` 为临时文件，由 `.gitignore` 排除