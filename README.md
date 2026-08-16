# 工作区 (Workspace)

这是 opencode 的管理基地。

## 目录结构

| 目录 | 用途 |
|------|------|
| `projects/` | 各类项目，每个项目一个子目录 |
| `scripts/` | 工具脚本 |
| `memories/` | 长期记忆，存于 SQLite `memory.db`，供不同 agent 共享 |
| `tmp/` | 临时文件，可随时清理 |

## 约定

- 新项目的目录名用小写英文，如 `projects/my-project/`
- 长期记忆存于 `memories/memory.db`（SQLite），用 `scripts/mem.py` 读写（`dump`/`list`/`set`/`search`），不再用 `.md` 文件
- `tmp/` 定期清理
