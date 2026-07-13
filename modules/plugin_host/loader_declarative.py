"""加载声明式贡献：theme / nav / settings / toolbar / i18n / prompts。"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from modules.log import log
from modules.plugin_host.api import PluginAPI
from modules.plugin_host.manifest import resolve_path
from modules.plugin_host.permissions import has_permission
from modules.plugin_host.registry import get_registry


def _load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"[PluginHost] 读取 JSON 失败 {path}: {e}")
        return None


def _load_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log(f"[PluginHost] 读取文本失败 {path}: {e}")
        return ""


def apply_declarative(manifest: dict, api: PluginAPI) -> None:
    """根据 contributes 注册声明式资源（不执行任意代码）。"""
    contributes = manifest.get("contributes") or {}
    plugin_id = manifest["id"]
    plugin_dir = manifest["path"]
    perms = api.permissions
    registry = get_registry()

    # nav
    nav_items = contributes.get("nav") or []
    if isinstance(nav_items, dict):
        nav_items = [nav_items]
    if nav_items and has_permission(perms, "ui.nav"):
        for item in nav_items:
            if not isinstance(item, dict):
                continue
            page = item.get("page") or item.get("qml") or ""
            page_path = resolve_path(plugin_dir, page)
            registry.add_nav(
                {
                    "id": item.get("id") or f"{plugin_id}-nav",
                    "plugin_id": plugin_id,
                    "title": item.get("title") or manifest.get("name") or plugin_id,
                    "page": page_path,
                    "icon": item.get("icon") or "ic_fluent_puzzle_piece_20_regular",
                    "position": item.get("position") or "top",
                    "source": resolve_path(plugin_dir, item["source"]) if item.get("source") else "",
                }
            )

    # settings
    settings_items = contributes.get("settings") or []
    if isinstance(settings_items, dict):
        settings_items = [settings_items]
    if settings_items and has_permission(perms, "ui.settings"):
        for item in settings_items:
            if not isinstance(item, dict):
                continue
            qml = item.get("qml") or item.get("page") or ""
            registry.add_settings(
                {
                    "id": item.get("id") or f"{plugin_id}-settings",
                    "plugin_id": plugin_id,
                    "title": item.get("title") or manifest.get("name") or plugin_id,
                    "qml": resolve_path(plugin_dir, qml),
                    "icon": item.get("icon") or "ic_fluent_puzzle_piece_20_regular",
                }
            )

    # home cards
    home_items = contributes.get("home") or []
    if isinstance(home_items, dict):
        home_items = [home_items]
    if home_items and has_permission(perms, "ui.home"):
        for item in home_items:
            if not isinstance(item, dict):
                continue
            qml = item.get("qml") or item.get("page") or ""
            registry.add_home(
                {
                    "id": item.get("id") or f"{plugin_id}-home",
                    "plugin_id": plugin_id,
                    "title": item.get("title") or manifest.get("name") or plugin_id,
                    "qml": resolve_path(plugin_dir, qml),
                    "icon": item.get("icon") or "ic_fluent_news_20_regular",
                    "order": int(item.get("order", 100)),
                }
            )

    # tools cards
    tools_items = contributes.get("tools") or []
    if isinstance(tools_items, dict):
        tools_items = [tools_items]
    if tools_items and has_permission(perms, "ui.tools"):
        for item in tools_items:
            if not isinstance(item, dict):
                continue
            qml = item.get("qml") or item.get("page") or ""
            registry.add_tools(
                {
                    "id": item.get("id") or f"{plugin_id}-tools",
                    "plugin_id": plugin_id,
                    "title": item.get("title") or manifest.get("name") or plugin_id,
                    "qml": resolve_path(plugin_dir, qml),
                    "icon": item.get("icon") or "ic_fluent_wrench_20_regular",
                    "order": int(item.get("order", 100)),
                }
            )

    # theme
    theme_spec = contributes.get("theme")
    if theme_spec and has_permission(perms, "ui.theme"):
        theme_data = {}
        if isinstance(theme_spec, str):
            path = resolve_path(plugin_dir, theme_spec)
            loaded = _load_json(path)
            if isinstance(loaded, dict):
                theme_data = loaded
        elif isinstance(theme_spec, dict):
            if theme_spec.get("path"):
                path = resolve_path(plugin_dir, theme_spec["path"])
                loaded = _load_json(path)
                if isinstance(loaded, dict):
                    theme_data = loaded
            else:
                theme_data = dict(theme_spec)
            if theme_spec.get("accent") and "accent" not in theme_data:
                theme_data["accent"] = theme_spec["accent"]
        if theme_data:
            theme_data.setdefault("name", manifest.get("name") or plugin_id)
            theme_data.setdefault("plugin_id", plugin_id)
            registry.set_theme(plugin_id, theme_data)
            try:
                from modules.plugin_host import state as plugin_state
                if not plugin_state.get_active_theme_plugin():
                    plugin_state.set_active_theme_plugin(plugin_id)
                    log(f"[PluginHost] 自动激活主题插件: {plugin_id}")
            except Exception as e:
                log(f"[PluginHost] 自动激活主题失败: {e}")
            log(f"[PluginHost] 声明式主题已加载: {plugin_id}")

    # toolbar（声明式仅注册元数据；回调需 Python 或 action 字符串）
    toolbar_items = contributes.get("toolbar") or []
    if isinstance(toolbar_items, dict):
        toolbar_items = [toolbar_items]
    if toolbar_items and has_permission(perms, "ui.toolbar"):
        for item in toolbar_items:
            if not isinstance(item, dict):
                continue
            action = item.get("action") or ""
            callback = None
            if action.startswith("python:"):
                # 由 python loader 之后解析；这里先存 action
                pass
            icon = item.get("icon") or ""
            registry.add_toolbar(
                {
                    "id": item.get("id") or f"{plugin_id}-tb",
                    "plugin_id": plugin_id,
                    "label": item.get("label") or item.get("title") or "Plugin",
                    "icon": resolve_path(plugin_dir, icon) if icon else "",
                    "action": action,
                    "callback": callback,
                }
            )

    # i18n
    i18n_items = contributes.get("i18n") or []
    if isinstance(i18n_items, dict):
        i18n_items = [i18n_items]
    for item in i18n_items:
        if not isinstance(item, dict):
            continue
        path = resolve_path(plugin_dir, item.get("path") or "")
        data = _load_json(path)
        if isinstance(data, dict):
            registry.add_i18n(
                {
                    "plugin_id": plugin_id,
                    "locale": item.get("locale") or "zh-cn",
                    "path": path,
                    "data": data,
                }
            )

    # prompts
    prompts = contributes.get("prompts") or {}
    if isinstance(prompts, dict):
        mapping = {
            "bloriko_append": ("bloriko", "agent.bloriko"),
            "blrpe_append": ("blrpe", "agent.blrpe"),
            "bloriko": ("bloriko", "agent.bloriko"),
            "blrpe": ("blrpe", "agent.blrpe"),
        }
        for key, (target, perm) in mapping.items():
            rel = prompts.get(key)
            if not rel or not has_permission(perms, perm):
                continue
            path = resolve_path(plugin_dir, rel)
            text = _load_text(path)
            if text:
                registry.add_prompt_append(target, {"plugin_id": plugin_id, "text": text})

    # agent_tools 声明（module + export 列表需 Python 侧）
    agent_tools = contributes.get("agent_tools") or {}
    if isinstance(agent_tools, dict):
        for target, specs in agent_tools.items():
            if not isinstance(specs, list):
                specs = [specs]
            perm = "agent.blrpe" if target in ("blrpe", "agent", "copilot") else "agent.bloriko"
            if not has_permission(perms, perm):
                continue
            for spec in specs:
                if not isinstance(spec, dict):
                    continue
                # 延迟：实际工具在 python 激活时由插件 register_agent_tool
                # 若 export 可从模块加载
                module_rel = spec.get("module") or ""
                export_name = spec.get("export") or "TOOLS"
                if not module_rel:
                    continue
                try:
                    from modules.plugin_host.loader_python import load_python_module

                    mod = load_python_module(f"{plugin_id}_tools_{target}", plugin_dir, module_rel)
                    if not mod:
                        continue
                    tools = getattr(mod, export_name, None)
                    executors = getattr(mod, "TOOL_EXECUTORS", {}) or getattr(mod, "EXECUTORS", {})
                    if isinstance(tools, list):
                        for tdef in tools:
                            name = ""
                            if isinstance(tdef, dict):
                                if tdef.get("type") == "function":
                                    name = tdef.get("function", {}).get("name", "")
                                else:
                                    name = tdef.get("name", "")
                            executor = None
                            if isinstance(executors, dict):
                                executor = executors.get(name)
                            if not callable(executor):
                                # 尝试模块级函数
                                executor = getattr(mod, f"exec_{name}", None) or getattr(mod, name, None)

                            def _make_exec(ex):
                                def _run(*args, **kwargs):
                                    if not callable(ex):
                                        return "错误：工具执行器未定义"
                                    try:
                                        return ex(*args, **kwargs)
                                    except TypeError:
                                        # 兼容 (working_dir, **kwargs) 或 (**kwargs)
                                        return ex(**kwargs)

                                return _run

                            registry.add_agent_tool(
                                target,
                                {
                                    "plugin_id": plugin_id,
                                    "name": name,
                                    "definition": tdef
                                    if isinstance(tdef, dict) and tdef.get("type") == "function"
                                    else {
                                        "type": "function",
                                        "function": tdef.get("function")
                                        if isinstance(tdef, dict) and "function" in tdef
                                        else {
                                            "name": name,
                                            "description": (tdef or {}).get("description", ""),
                                            "parameters": (tdef or {}).get(
                                                "parameters", {"type": "object", "properties": {}}
                                            ),
                                        },
                                    },
                                    "executor": _make_exec(executor),
                                    "kind": spec.get("kind") or "read",
                                },
                            )
                except Exception as e:
                    log(f"[PluginHost] 加载 agent_tools 失败 {plugin_id}: {e}")

    log(f"[PluginHost] 声明式贡献已应用: {plugin_id}")
