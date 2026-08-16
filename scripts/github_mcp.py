#!/usr/bin/env python3
"""github_mcp.py — 零依赖 GitHub 查询 MCP 服务器（stdio / JSON-RPC 2.0）。

用途：供 opencode 等 MCP 客户端查询 GitHub（搜仓库/文件/代码）。只走
api.github.com（https），token 从环境变量或 workspace/secrets/github.env 读取。

工具：
  search_repos(q[, n])     搜索仓库，返回 名称/描述/星标/地址
  get_repo(owner/repo)     仓库元信息（语言、默认分支、说明、更新时间）
  list_repo_files(owner/repo[, path])   列目录（根目录或指定子目录）
  get_file(owner/repo, path)            取文件内容（文本，base64 自动解码）

协议：MCP stdio transport = 换行分隔 JSON-RPC 2.0。
"""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.github.com"
UA = "agent-home-github-mcp/1.0"


def load_token():
    t = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if t:
        return t
    env_file = "/home/home/workspace/secrets/github.env"
    try:
        for line in open(env_file, encoding="utf-8"):
            line = line.strip()
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return None


TOKEN = load_token()


def gh_get(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:500]
        except OSError:
            pass
        return e.code, {"message": body or e.reason}
    except urllib.error.URLError as e:
        return 0, {"message": f"network error: {e.reason}"}


def fmt_repo(r):
    return {
        "name": r.get("full_name"),
        "stars": r.get("stargazers_count"),
        "language": r.get("language"),
        "description": r.get("description"),
        "url": r.get("html_url"),
    }


def tool_search_repos(args):
    q = args.get("q", "").strip()
    n = int(args.get("n", 5))
    if not q:
        return {"isError": True, "content": [{"type": "text", "text": "需要 q 参数"}]}
    status, data = gh_get("/search/repositories", {"q": q, "per_page": n})
    if status != 200:
        return {"isError": True, "content": [{"type": "text", "text": f"HTTP {status}: {data.get('message')}"}]}
    out = [fmt_repo(r) for r in data.get("items", [])]
    return {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2)}]}


def tool_get_repo(args):
    repo = args.get("repo", "").strip()
    if not repo:
        return {"isError": True, "content": [{"type": "text", "text": "需要 repo 参数（owner/repo）"}]}
    status, data = gh_get(f"/repos/{urllib.parse.quote(repo, safe='/')}")
    if status != 200:
        return {"isError": True, "content": [{"type": "text", "text": f"HTTP {status}: {data.get('message')}"}]}
    return {"content": [{"type": "text", "text": json.dumps(fmt_repo(data), ensure_ascii=False, indent=2)}]}


def tool_list_repo_files(args):
    repo = args.get("repo", "").strip()
    path = args.get("path", "")
    if not repo:
        return {"isError": True, "content": [{"type": "text", "text": "需要 repo 参数（owner/repo）"}]}
    api_path = f"/repos/{urllib.parse.quote(repo, safe='/')}/contents"
    if path:
        api_path += "/" + urllib.parse.quote(path.strip("/"), safe="/")
    status, data = gh_get(api_path)
    if status != 200:
        return {"isError": True, "content": [{"type": "text", "text": f"HTTP {status}: {data.get('message')}"}]}
    if isinstance(data, list):
        out = [{"type": e.get("type"), "name": e.get("name"), "path": e.get("path")} for e in data]
    else:
        out = {"type": data.get("type"), "name": data.get("name"), "path": data.get("path"), "size": data.get("size")}
    return {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2)}]}


def tool_get_file(args):
    repo = args.get("repo", "").strip()
    path = args.get("path", "").strip()
    if not repo or not path:
        return {"isError": True, "content": [{"type": "text", "text": "需要 repo（owner/repo）与 path 参数"}]}
    api_path = f"/repos/{urllib.parse.quote(repo, safe='/')}/contents/{urllib.parse.quote(path, safe='/')}"
    status, data = gh_get(api_path)
    if status != 200:
        return {"isError": True, "content": [{"type": "text", "text": f"HTTP {status}: {data.get('message')}"}]}
    if data.get("type") != "file":
        return {"isError": True, "content": [{"type": "text", "text": "不是文件，用 list_repo_files 看目录"}]}
    try:
        text = base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"解码失败: {e}"}]}
    if len(text) > 20000:
        text = text[:20000] + "\n…（内容过长已截断）"
    return {"content": [{"type": "text", "text": text}]}


TOOLS = [
    {
        "name": "search_repos",
        "description": "按关键字搜索 GitHub 仓库，返回名称/星标/语言/描述。参数: q(查询词), n(条数, 默认5)",
        "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}, "n": {"type": "integer"}}, "required": ["q"]},
    },
    {
        "name": "get_repo",
        "description": "获取单个仓库元信息（owner/repo）。参数: repo",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}, "required": ["repo"]},
    },
    {
        "name": "list_repo_files",
        "description": "列出仓库目录内容（owner/repo 与可选 path）。参数: repo, path",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "path": {"type": "string"}}, "required": ["repo"]},
    },
    {
        "name": "get_file",
        "description": "获取仓库内文件内容（自动 base64 解码，截断 20KB）。参数: repo, path",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "path": {"type": "string"}}, "required": ["repo", "path"]},
    },
]


def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        method = msg.get("method")
        msg_id = msg.get("id")
        if method == "initialize":
            respond(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "github-mcp", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            respond(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {}) or {}
            handler = {"search_repos": tool_search_repos, "get_repo": tool_get_repo,
                       "list_repo_files": tool_list_repo_files, "get_file": tool_get_file}.get(name)
            if handler:
                respond(msg_id, handler(args))
            else:
                respond(msg_id, {"isError": True, "content": [{"type": "text", "text": f"未知工具: {name}"}]})
        elif method == "ping":
            respond(msg_id, {})
        sys.stdout.flush()


def respond(msg_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()