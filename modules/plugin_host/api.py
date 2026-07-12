"""注入给插件的 PluginAPI。"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional

import modules.config as cfg
import modules.globals as BLglobals
from modules.log import log
from modules.plugin_host import state as plugin_state
from modules.plugin_host.event_bus import get_event_bus
from modules.plugin_host.permissions import has_permission
from modules.plugin_host.registry import get_registry


class PermissionError(Exception):
    pass


class PluginAPI:
    """每个插件实例获得独立的 API（绑定 plugin_id 与权限）。"""

    def __init__(self, plugin_id: str, plugin_dir: str, permissions: List[str]):
        self.plugin_id = plugin_id
        self.plugin_dir = plugin_dir
        self.permissions = list(permissions or [])
        self._bus = get_event_bus()
        self._registry = get_registry()

    # ── 基础 ──────────────────────────────────────────────

    def log(self, message: str, level: str = "info") -> None:
        log(f"[Plugin:{self.plugin_id}] {message}")

    @property
    def datapath(self) -> str:
        return str(getattr(BLglobals, "datapath", "") or "")

    def plugin_data_dir(self) -> str:
        path = os.path.join(self.datapath, "PluginData", self.plugin_id)
        os.makedirs(path, exist_ok=True)
        return path

    def require(self, permission: str) -> None:
        if not has_permission(self.permissions, permission):
            raise PermissionError(f"插件 {self.plugin_id} 缺少权限: {permission}")

    def has_perm(self, permission: str) -> bool:
        return has_permission(self.permissions, permission)

    # ── 配置 ──────────────────────────────────────────────

    def get_private_config(self) -> dict:
        return plugin_state.get_plugin_data(self.plugin_id)

    def set_private_config(self, data: dict) -> None:
        plugin_state.set_plugin_data(self.plugin_id, data if isinstance(data, dict) else {})

    def get_config(self, key: Optional[str] = None, default=None):
        self.require("config.read")
        data = cfg.read() or {}
        if key is None:
            return data
        return data.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        self.require("config.write")
        from modules.plugin_host.state import _write_config

        data = cfg.read() or {}
        data[key] = value
        _write_config(data)
        self._bus.emit("config.changed", key, value, plugin_id=self.plugin_id)
        self.log(f"set_config {key}")

    # ── 事件 ──────────────────────────────────────────────

    def emit(self, event: str, *args, **kwargs) -> list:
        self.log(f"emit {event}")
        return self._bus.emit(event, *args, **kwargs)

    def on(self, event: str, callback: Callable) -> Callable:
        return self._bus.on(event, callback, plugin_id=self.plugin_id)

    def once(self, event: str, callback: Callable) -> Callable:
        return self._bus.once(event, callback, plugin_id=self.plugin_id)

    # ── 钩子与贡献 ────────────────────────────────────────

    def register_hook(self, name: str, fn: Callable) -> None:
        from modules.plugin_host.hooks import HOOK_PERMISSIONS

        required = HOOK_PERMISSIONS.get(name)
        if required:
            self.require(required)
        self._registry.add_hook(name, self.plugin_id, fn)
        self.log(f"register_hook {name}")

    def register_nav(self, nav_id: str, title: str, page: str, icon: str = "", position: str = "top") -> None:
        self.require("ui.nav")
        page_path = page
        if page and not os.path.isabs(page):
            page_path = os.path.join(self.plugin_dir, page)
        item = {
            "id": nav_id,
            "plugin_id": self.plugin_id,
            "title": title,
            "page": page_path,
            "icon": icon or "ic_fluent_puzzle_piece_20_regular",
            "position": position or "top",
        }
        self._registry.add_nav(item)

    def register_settings(self, settings_id: str, title: str, qml: str) -> None:
        self.require("ui.settings")
        qml_path = qml if os.path.isabs(qml) else os.path.join(self.plugin_dir, qml)
        self._registry.add_settings(
            {
                "id": settings_id,
                "plugin_id": self.plugin_id,
                "title": title,
                "qml": qml_path,
            }
        )

    def register_toolbar(self, button_id: str, label: str, callback: Callable, icon: str = "") -> None:
        self.require("ui.toolbar")
        icon_path = ""
        if icon:
            icon_path = icon if os.path.isabs(icon) else os.path.join(self.plugin_dir, icon)
        self._registry.add_toolbar(
            {
                "id": button_id,
                "plugin_id": self.plugin_id,
                "label": label,
                "icon": icon_path,
                "callback": callback,
            }
        )

    def apply_theme_override(self, theme: dict) -> None:
        self.require("ui.theme")
        if not isinstance(theme, dict):
            return
        self._registry.set_theme(self.plugin_id, theme)
        plugin_state.set_active_theme_plugin(self.plugin_id)
        self._bus.emit("theme.changed", self.plugin_id, theme)
        self.log(f"apply_theme_override name={theme.get('name')}")

    def register_agent_tool(
        self,
        target: str,
        definition: dict,
        executor: Callable,
        kind: str = "read",
    ) -> None:
        perm = "agent.blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "agent.bloriko"
        self.require(perm)
        # definition 可以是 OpenAI function 格式或裸 function 对象
        name = ""
        tool_def = definition
        if isinstance(definition, dict):
            if definition.get("type") == "function" and isinstance(definition.get("function"), dict):
                name = definition["function"].get("name", "")
                tool_def = definition
            elif "function" in definition:
                name = definition["function"].get("name", "")
            else:
                name = definition.get("name", "")
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": definition.get("description", ""),
                        "parameters": definition.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
        self._registry.add_agent_tool(
            target,
            {
                "plugin_id": self.plugin_id,
                "name": name,
                "definition": tool_def,
                "executor": executor,
                "kind": kind or "read",
            },
        )
        self.log(f"register_agent_tool {target}:{name} kind={kind}")

    def append_system_prompt(self, target: str, text: str) -> None:
        perm = "agent.blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "agent.bloriko"
        self.require(perm)
        if not text:
            return
        self._registry.add_prompt_append(
            target,
            {"plugin_id": self.plugin_id, "text": text},
        )
        self.log(f"append_system_prompt {target} len={len(text)}")

    # ── 通知 / 网络 / 异步 ────────────────────────────────

    def notify(self, title: str, body: str = "", category: str = "plugin") -> None:
        try:
            from modules.notification import send_notification

            send_notification(title, body, category=category)
            self.log(f"notify {title}")
        except Exception as e:
            self.log(f"notify 失败: {e}")

    def http_get(self, url: str, timeout: int = 30) -> dict:
        self.require("net.http")
        import requests

        self.log(f"http_get {url}")
        resp = requests.get(url, timeout=timeout)
        return {
            "status_code": resp.status_code,
            "text": resp.text,
            "headers": dict(resp.headers),
        }

    def http_post(self, url: str, data=None, json_body=None, timeout: int = 30) -> dict:
        self.require("net.http")
        import requests

        self.log(f"http_post {url}")
        resp = requests.post(url, data=data, json=json_body, timeout=timeout)
        return {
            "status_code": resp.status_code,
            "text": resp.text,
            "headers": dict(resp.headers),
        }

    def run_async(self, fn: Callable, *args, **kwargs) -> threading.Thread:
        def runner():
            try:
                fn(*args, **kwargs)
            except Exception as e:
                self.log(f"run_async 异常: {e}")

        t = threading.Thread(target=runner, daemon=True, name=f"plugin-{self.plugin_id}")
        t.start()
        return t

    # ── 启动器能力封装 ────────────────────────────────────

    def list_versions(self) -> List[str]:
        try:
            data = cfg.read() or {}
            mc_dir = data.get("minecraft_dir") or ""
            versions_dir = os.path.join(mc_dir, "versions") if mc_dir else ""
            if not versions_dir or not os.path.isdir(versions_dir):
                return []
            return sorted(
                [
                    name
                    for name in os.listdir(versions_dir)
                    if os.path.isdir(os.path.join(versions_dir, name))
                ]
            )
        except Exception as e:
            self.log(f"list_versions 失败: {e}")
            return []

    def get_minecraft_dir(self) -> str:
        data = cfg.read() or {}
        return str(data.get("minecraft_dir") or "")
