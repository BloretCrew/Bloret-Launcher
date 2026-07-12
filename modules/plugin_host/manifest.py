"""解析与规范化 plugin.json / cwplugin.json。"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from modules.log import log
from modules.plugin_host.permissions import normalize_permissions

MANIFEST_NAMES = ("plugin.json", "cwplugin.json")


def _safe_id(raw: str, fallback: str) -> str:
    s = (raw or "").strip() or fallback
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s)
    return s.strip("-") or fallback


def load_raw_manifest(plugin_dir: str) -> Dict[str, Any]:
    for name in MANIFEST_NAMES:
        path = os.path.join(plugin_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception as e:
            log(f"[PluginHost] 读取清单失败 {path}: {e}")
    return {}


def normalize_manifest(plugin_dir: str, folder_name: str, raw: Optional[dict] = None) -> dict:
    raw = raw if isinstance(raw, dict) else load_raw_manifest(plugin_dir)
    folder_name = folder_name or os.path.basename(plugin_dir.rstrip(os.sep))

    plugin_id = _safe_id(str(raw.get("id") or folder_name), folder_name)
    name = str(raw.get("name") or folder_name)

    # entry 兼容字符串或对象
    entry_raw = raw.get("entry")
    entry = {"python": "", "process": "", "qml_page": ""}
    if isinstance(entry_raw, str):
        lower = entry_raw.lower()
        if lower.endswith(".py"):
            entry["python"] = entry_raw
        elif lower.endswith(".qml"):
            entry["qml_page"] = entry_raw
        else:
            entry["process"] = entry_raw
    elif isinstance(entry_raw, dict):
        entry["python"] = str(entry_raw.get("python") or "")
        entry["process"] = str(entry_raw.get("process") or "")
        entry["qml_page"] = str(entry_raw.get("qml_page") or entry_raw.get("qml") or "")

    # 回退入口探测
    if not entry["python"]:
        for cand in ("main.py", "plugin.py"):
            if os.path.isfile(os.path.join(plugin_dir, cand)):
                entry["python"] = cand
                break
    if not entry["process"]:
        for cand in ("main.exe", "main"):
            if os.path.isfile(os.path.join(plugin_dir, cand)):
                entry["process"] = cand
                break
    if not entry["qml_page"]:
        for cand in ("main.qml", "ui/Page.qml", "ui/page.qml"):
            if os.path.isfile(os.path.join(plugin_dir, cand)):
                entry["qml_page"] = cand
                break

    permissions = normalize_permissions(raw.get("permissions"))
    contributes = raw.get("contributes") if isinstance(raw.get("contributes"), dict) else {}
    hooks = raw.get("hooks") if isinstance(raw.get("hooks"), dict) else {}

    # 从 contributes 推断权限（若未声明）
    if not permissions:
        inferred = set()
        if contributes.get("nav"):
            inferred.add("ui.nav")
        if contributes.get("theme"):
            inferred.add("ui.theme")
        if contributes.get("settings"):
            inferred.add("ui.settings")
        if contributes.get("toolbar"):
            inferred.add("ui.toolbar")
        if contributes.get("agent_tools") or contributes.get("prompts"):
            tools = contributes.get("agent_tools") or {}
            if isinstance(tools, dict):
                if tools.get("bloriko"):
                    inferred.add("agent.bloriko")
                if tools.get("blrpe"):
                    inferred.add("agent.blrpe")
            else:
                inferred.add("agent.bloriko")
        if contributes.get("web_routes"):
            inferred.add("web.routes")
        for h in hooks:
            if str(h).startswith("launch."):
                inferred.add("launch.hooks")
            if str(h).startswith("download."):
                inferred.add("download.hooks")
        permissions = sorted(inferred)

    icon = str(raw.get("icon") or "")
    icon_path = ""
    for cand in (
        os.path.join(plugin_dir, icon) if icon else "",
        os.path.join(plugin_dir, "icon.png"),
        os.path.join(plugin_dir, "icon.jpg"),
        os.path.join(plugin_dir, "logo.png"),
    ):
        if cand and os.path.isfile(cand):
            icon_path = cand
            break

    return {
        "id": plugin_id,
        "name": name,
        "version": str(raw.get("version") or ""),
        "author": str(raw.get("author") or raw.get("master") or ""),
        "description": str(raw.get("description") or ""),
        "url": str(raw.get("url") or ""),
        "min_launcher_version": str(raw.get("min_launcher_version") or ""),
        "entry": entry,
        "permissions": permissions,
        "contributes": contributes,
        "hooks": hooks,
        "icon": icon,
        "iconPath": icon_path,
        "folderName": folder_name,
        "path": plugin_dir,
        "raw": raw,
    }


def resolve_path(plugin_dir: str, relative: str) -> str:
    if not relative:
        return ""
    if os.path.isabs(relative):
        return relative
    return os.path.normpath(os.path.join(plugin_dir, relative))
