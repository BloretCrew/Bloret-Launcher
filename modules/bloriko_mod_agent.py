"""
Mods 页络可推荐迷你 Agent：Modrinth 工具 + 流式 + 思考过程。
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Callable, Optional

from modules.log import log as app_log
from modules.bloriko_mod_tools import (
    MOD_RECOMMEND_TOOL_DEFINITIONS,
    MOD_RECOMMEND_TOOL_EXECUTORS,
    summarize_tool_for_status,
)

_log = logging.getLogger(__name__)


def build_mod_recommend_system_prompt(language: str | None = None) -> str:
    from modules.Bloriko import (
        _BLORIKO_MOD_PERSONA,
        _language_reply_instruction,
        _resolve_ui_language_code,
    )

    lang = language or _resolve_ui_language_code()
    lang_rule = _language_reply_instruction(lang)
    return (
        f"{_BLORIKO_MOD_PERSONA}\n"
        f"{lang_rule}\n\n"
        "## Tools (required)\n"
        "You have tools to query Modrinth. You MUST use `search_modrinth` before recommending "
        "any mod. Never invent slugs. Only recommend mods that appeared in tool results "
        "(or were verified with `get_modrinth_project`).\n"
        "- Prefer FABRIC loader and the player's Minecraft version in search filters.\n"
        "- You may call search multiple times with different keywords.\n"
        "- Optionally verify important picks with `get_modrinth_project`.\n\n"
        "## Output format\n"
        "After tools, write a short 络可-style recommendation with a bullet list "
        "(display name + why). Then END with a JSON block of Modrinth slugs only:\n"
        "```json\n[\"slug-1\", \"slug-2\"]\n```\n"
        "Recommend 3-8 mods when possible.\n"
    )


def build_mod_recommend_user_message(user_query: str, mc_version: str) -> str:
    return (
        f"Player Minecraft version: {mc_version} (Fabric only).\n"
        f"Player request: {user_query}\n\n"
        f"Please search Modrinth for suitable Fabric mods for {mc_version}, "
        f"then recommend them in character as 络可."
    )


def run_mod_recommendation_agent(
    user_query: str,
    mc_version: str,
    on_text_chunk: Optional[Callable[[str], None]] = None,
    on_status: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[str, list], None]] = None,
    language: str | None = None,
):
    """
    后台启动迷你 Agent。返回 agent 实例（可 .cancel()）。

    on_done(clean_text, slugs)
    """
    from modules.bloriko_agent import resolve_global_ai_config
    from modules.bloriko_agent.agent_loop import BlorikoAgentLoop
    from modules.Bloriko import parse_mod_slugs_from_response
    from modules.modrinth import get_project_summary

    def _status(msg: str):
        app_log(f"[ModAgent] status: {msg}", logging.INFO)
        if on_status:
            try:
                on_status(msg)
            except Exception as e:
                _log.warning("on_status failed: %s", e)

    cfg_ai = resolve_global_ai_config()
    if cfg_ai.get("error"):
        err = cfg_ai["error"]
        _status(f"❌ {err}")
        if on_error:
            on_error(err)
        if on_done:
            on_done(err, [])
        return None

    api_url = cfg_ai["api_url"]
    auth_header = cfg_ai.get("auth_header") or ""
    model = cfg_ai["model"]
    _status(
        f"🌐 使用 AI: {cfg_ai.get('provider_name')} / {model}"
    )
    _status("💭 络可开始想怎么帮你挑 Mod 啦…")

    try:
        from modules.globals import datapath as _datapath
    except Exception:
        _datapath = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), "Bloret-Launcher"
        )
    working_dir = os.path.join(_datapath, "bloriko-agent", "workspace")
    os.makedirs(working_dir, exist_ok=True)

    system_prompt = build_mod_recommend_system_prompt(language)
    user_message = build_mod_recommend_user_message(user_query, mc_version)

    final_box = {"text": "", "error": None}

    def _on_text(text: str):
        final_box["text"] = text or ""
        if on_text_chunk:
            try:
                on_text_chunk(text)
            except Exception as e:
                _log.warning("on_text_chunk failed: %s", e)

    def _on_tool_start(name: str, args_json: str):
        _status(summarize_tool_for_status(name, args_json, result=None))

    def _on_tool_end(name: str, args_json: str, result: str):
        _status(summarize_tool_for_status(name, args_json, result=result))

    def _on_reasoning(text: str):
        # 只推送尾部，避免刷屏；状态区追加标记行
        snippet = (text or "").strip()
        if not snippet:
            return
        tail = snippet[-400:] if len(snippet) > 400 else snippet
        _status("🧠 思考中…\n" + tail)

    def _on_err(msg: str):
        final_box["error"] = msg
        _status(f"❌ {msg}")
        if on_error:
            try:
                on_error(msg)
            except Exception:
                pass

    def _on_agent_done():
        raw = final_box["text"] or ""
        if final_box["error"] and not raw:
            raw = final_box["error"]
        _status("📝 整理推荐结果…")
        clean_text, slugs = parse_mod_slugs_from_response(raw)

        # 二次校验：去掉 API 不存在的 slug
        verified = []
        for slug in slugs:
            summary = get_project_summary(slug)
            if summary.get("ok"):
                verified.append(summary.get("slug") or slug)
            else:
                _status(f"⚠ 丢弃无效 slug: {slug}")
        if slugs and not verified:
            _status("⚠ 未能校验到有效 slug，将使用模型给出的列表（可能不准确）")
            verified = slugs
        elif verified:
            slugs = list(dict.fromkeys(verified))

        app_log(
            f"[ModAgent] 完成: slugs={slugs}, text_len={len(clean_text or '')}",
            logging.INFO,
        )
        _status(f"✅ 完成，共推荐 {len(slugs)} 个 Mod")
        if on_done:
            try:
                on_done(clean_text or raw, slugs)
            except Exception as e:
                _log.error("on_done failed: %s", e, exc_info=True)

    agent = BlorikoAgentLoop(
        working_dir=working_dir,
        api_url=api_url,
        auth_header=auth_header,
        on_text_chunk=_on_text,
        on_tool_call_start=_on_tool_start,
        on_tool_call_end=_on_tool_end,
        on_error=_on_err,
        on_done=_on_agent_done,
        on_permission_request=None,
        on_ask_user=None,
        on_emotion_change=None,
        on_reasoning_chunk=_on_reasoning,
        model=model,
        role="auto",
        tool_executors=MOD_RECOMMEND_TOOL_EXECUTORS,
    )
    agent._tools = MOD_RECOMMEND_TOOL_DEFINITIONS
    agent._system_prompt_override = system_prompt

    def _run():
        try:
            app_log(
                f"[ModAgent] 启动: version={mc_version}, query_len={len(user_query or '')}, "
                f"model={model}, api={api_url}",
                logging.INFO,
            )
            agent.run(user_message, history=None)
        except Exception as e:
            app_log(f"[ModAgent] 异常: {e}", logging.ERROR)
            if on_error:
                on_error(str(e))
            if on_done:
                on_done(f"错误: {e}", [])

    threading.Thread(target=_run, daemon=True).start()
    return agent
