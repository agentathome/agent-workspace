# Memories

本目录存放跨 agent 共享的长期记忆，存于轻量 SQLite 数据库 `memory.db`（由 `scripts/mem.py` 管理，无需安装额外依赖）。

## 使用

```bash
python3 scripts/mem.py list                # 列出分类与小节
python3 scripts/mem.py dump [分类]         # 输出全文（供 Agent 阅读）
python3 scripts/mem.py get <分类> [小节]   # 读取
python3 scripts/mem.py set <分类> <小节> -c "内容"   # 写入/更新（或从 stdin 读）
python3 scripts/mem.py search <文本>       # 全文搜索
python3 scripts/mem.py rm <分类> [小节]    # 删除
```

## 约定

- 分类名小写英文，如 `computer-setup`、`email-and-backup`
- 每个分类下以"小节"（topic）组织内容，如 `WireGuard VPN（服务端）`
- 如无必要不增加记忆条目，保持精简
- `memory.db` 提交到 git；`memory.db-wal` / `memory.db-shm` 为临时文件，由 `.gitignore` 排除