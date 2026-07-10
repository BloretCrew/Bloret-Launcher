"""
Mods 页络可推荐专用工具（独立于主 Agent 工具集）。

OpenAI function-calling 格式 + 执行器，仅由迷你 Agent 注入。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict

from modules.log import log as app_log
from modules.modrinth import search_mods_structured, get_project_summary

_log = logging.getLogger(__name__)


MOD_RECOMMEND_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_modrinth",
            "description": (
                "Search real Minecraft mods on Modrinth. "
                "Always use this before recommending mods. "
                "Returns existing projects with slugs suitable for install."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords (mod name or feature, e.g. sodium, performance, minimap)",
                    },
                    "game_version": {
                        "type": "string",
                        "description": "Minecraft version filter, e.g. 1.21.1. Prefer the player's version.",
                    },
                    "loader": {
                        "type": "string",
                        "description": "Mod loader, default fabric",
                        "default": "fabric",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results 1-15, default 8",
                        "default": 8,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_modrinth_project",
            "description": (
                "Fetch a Modrinth project by slug or id to verify it exists and check loaders/versions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug_or_id": {
                        "type": "string",
                        "description": "Modrinth project slug or project id",
                    },
                },
                "required": ["slug_or_id"],
            },
        },
    },
]


def _exec_search_modrinth(working_dir: Path, **kwargs) -> str:
    query = (kwargs.get("query") or "").strip()
    if not query:
        return json.dumps({"ok": False, "error": "query is required"}, ensure_ascii=False)

    game_version = (kwargs.get("game_version") or "").strip() or None
    loader = (kwargs.get("loader") or "fabric").strip() or "fabric"
    try:
        limit = int(kwargs.get("limit") or 8)
    except (TypeError, ValueError):
        limit = 8
    limit = max(1, min(limit, 15))

    app_log(
        f"[ModTool] search_modrinth query={query!r} version={game_version} loader={loader} limit={limit}",
        logging.INFO,
    )
    hits = search_mods_structured(query, game_version=game_version, loader=loader, limit=limit)
    payload = {
        "ok": True,
        "query": query,
        "game_version": game_version,
        "loader": loader,
        "count": len(hits),
        "hits": hits,
    }
    text = json.dumps(payload, ensure_ascii=False)
    if len(text) > 12000:
        text = text[:12000] + "...(truncated)"
    return text


def _exec_get_modrinth_project(working_dir: Path, **kwargs) -> str:
    slug = (kwargs.get("slug_or_id") or kwargs.get("slug") or "").strip()
    if not slug:
        return json.dumps({"ok": False, "error": "slug_or_id is required"}, ensure_ascii=False)
    app_log(f"[ModTool] get_modrinth_project slug={slug!r}", logging.INFO)
    summary = get_project_summary(slug)
    return json.dumps(summary, ensure_ascii=False)


MOD_RECOMMEND_TOOL_EXECUTORS: Dict[str, Callable[..., str]] = {
    "search_modrinth": _exec_search_modrinth,
    "get_modrinth_project": _exec_get_modrinth_project,
}


def summarize_tool_for_status(tool_name: str, args_json: str, result: str | None = None) -> str:
    """生成简短中文状态行，供思考过程展示。"""
    try:
        args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
    except json.JSONDecodeError:
        args = {}

    if tool_name == "search_modrinth":
        q = args.get("query", "")
        ver = args.get("game_version") or ""
        base = f'🔍 搜索 Modrinth: "{q}"'
        if ver:
            base += f" @ {ver}"
        if result is None:
            return base + " …"
        try:
            data = json.loads(result)
            n = data.get("count", 0)
            return f'{base} → 找到 {n} 个结果'
        except Exception:
            return base + " → 完成"

    if tool_name == "get_modrinth_project":
        slug = args.get("slug_or_id") or args.get("slug") or ""
        base = f"🔎 校验项目: {slug}"
        if result is None:
            return base + " …"
        try:
            data = json.loads(result)
            if data.get("ok"):
                return f"{base} → 存在 ({data.get('title') or slug})"
            return f"{base} → 未找到"
        except Exception:
            return base + " → 完成"

    if result is None:
        return f"⚙ 调用工具: {tool_name} …"
    return f"⚙ 工具完成: {tool_name}"
