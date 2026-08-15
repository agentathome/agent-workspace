# 工作区 (Workspace)

这是 opencode 的管理基地。

## 目录结构

| 目录 | 用途 |
|------|------|
| `projects/` | 各类项目，每个项目一个子目录 |
| `scripts/` | 工具脚本 |
| `memories/` | 长期记忆，供不同 agent 共享 |
| `tmp/` | 临时文件，可随时清理 |

## 约定

- 新项目的目录名用小写英文，如 `projects/my-project/`
- `memories/` 下的文件以 `.md` 结尾，便于读取和共享
- `tmp/` 定期清理
