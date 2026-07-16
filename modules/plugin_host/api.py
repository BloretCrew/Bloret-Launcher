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
        data = cfg.read() or {}
        data[key] = value
        # 统一 write：磁盘 + config.changed（含脱敏）
        cfg.write(data, changed_keys={key: value})
        self.log(f"set_config {key}")

    # ── 事件 ──────────────────────────────────────────────

    def _require_event_permission(self, event: str) -> None:
        """标准生命周期事件沿用 hook 权限，避免 event bus 绕过权限检查。"""
        from modules.plugin_host.hooks import HOOK_PERMISSIONS

        required = HOOK_PERMISSIONS.get(event)
        if required:
            self.require(required)

    def emit(self, event: str, *args, **kwargs) -> list:
        from modules.plugin_host.hooks import HOOK_PERMISSIONS

        if event in HOOK_PERMISSIONS:
            raise PermissionError(f"标准生命周期事件只能由启动器派发: {event}")
        self.log(f"emit {event}")
        return self._bus.emit(event, *args, **kwargs)

    def on(self, event: str, callback: Callable) -> Callable:
        self._require_event_permission(event)
        return self._bus.on(event, callback, plugin_id=self.plugin_id)

    def once(self, event: str, callback: Callable) -> Callable:
        self._require_event_permission(event)
        return self._bus.once(event, callback, plugin_id=self.plugin_id)

    # ── 钩子与贡献 ────────────────────────────────────────

    def register_hook(self, name: str, fn: Callable) -> None:
        from modules.plugin_host.hooks import HOOK_PERMISSIONS

        required = HOOK_PERMISSIONS.get(name)
        if required:
            self.require(required)
        self._registry.add_hook(name, self.plugin_id, fn)
        self.log(f"register_hook {name}")

    def _resolve_plugin_resource(self, relative_path: str) -> str:
        from modules.plugin_host.manifest import resolve_path

        return resolve_path(self.plugin_dir, relative_path)

    def register_nav(self, nav_id: str, title: str, page: str, icon: str = "", position: str = "top") -> None:
        self.require("ui.nav")
        page_path = self._resolve_plugin_resource(page)
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
        qml_path = self._resolve_plugin_resource(qml)
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
        icon_path = self._resolve_plugin_resource(icon) if icon else ""
        self._registry.add_toolbar(
            {
                "id": button_id,
                "plugin_id": self.plugin_id,
                "label": label,
                "icon": icon_path,
                "callback": callback,
            }
        )

    def register_home_card(
        self,
        card_id: str,
        title: str,
        qml: str,
        icon: str = "",
        order: int = 100,
    ) -> None:
        """在主页注入 QML 卡片（需 ui.home）。"""
        self.require("ui.home")
        qml_path = self._resolve_plugin_resource(qml)
        self._registry.add_home(
            {
                "id": card_id,
                "plugin_id": self.plugin_id,
                "title": title,
                "qml": qml_path,
                "icon": icon or "ic_fluent_news_20_regular",
                "order": int(order) if order is not None else 100,
            }
        )
        self.log(f"register_home_card {card_id}")

    def register_tools_card(
        self,
        card_id: str,
        title: str,
        qml: str,
        icon: str = "",
        order: int = 100,
    ) -> None:
        """在小工具页注入卡片（需 ui.tools）。"""
        self.require("ui.tools")
        qml_path = self._resolve_plugin_resource(qml)
        self._registry.add_tools(
            {
                "id": card_id,
                "plugin_id": self.plugin_id,
                "title": title,
                "qml": qml_path,
                "icon": icon or "ic_fluent_wrench_20_regular",
                "order": int(order) if order is not None else 100,
            }
        )
        self.log(f"register_tools_card {card_id}")

    def register_panel(
        self,
        area: str,
        panel_id: str,
        title: str,
        qml: str,
        icon: str = "",
        order: int = 100,
    ) -> None:
        """在指定功能页注入 QML 面板（需对应 ui.{area} 权限）。"""
        from modules.services.base import PANEL_PERMISSIONS

        area_key = (area or "").strip().lower()
        perm = PANEL_PERMISSIONS.get(area_key) or f"ui.{area_key}"
        self.require(perm)
        qml_path = self._resolve_plugin_resource(qml)
        self._registry.add_panel(
            area_key,
            {
                "id": panel_id,
                "plugin_id": self.plugin_id,
                "title": title,
                "qml": qml_path,
                "icon": icon or "ic_fluent_puzzle_piece_20_regular",
                "order": int(order) if order is not None else 100,
                "area": area_key,
            },
        )
        self.log(f"register_panel area={area_key} id={panel_id}")

    def register_content_source(
        self,
        kind: str,
        source_id: str,
        title: str,
        *,
        priority: int = 100,
        meta: Optional[dict] = None,
    ) -> None:
        """注册 mods / download 内容源元数据（执行器由后续 Phase 接线）。"""
        kind_key = (kind or "").strip().lower()
        if kind_key == "download":
            self.require("download.source")
        else:
            self.require("mods.source")
            kind_key = "mods"
        self._registry.add_source(
            kind_key,
            {
                "id": source_id,
                "plugin_id": self.plugin_id,
                "title": title,
                "priority": int(priority),
                "meta": meta or {},
            },
        )
        self.log(f"register_content_source kind={kind_key} id={source_id}")

    def apply_theme_override(self, theme: dict) -> None:
        self.require("ui.theme")
        if not isinstance(theme, dict):
            return
        from modules.plugin_host.dispatch import invoke_hook

        self._registry.set_theme(self.plugin_id, theme)
        plugin_state.set_active_theme_plugin(self.plugin_id)
        invoke_hook("theme.changed", self.plugin_id, theme)
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

    # ── 文件系统（限 datapath / PluginData）────────────────

    def _resolve_datapath_target(self, relative_path: str, *, allow_plugin_data_only: bool = False) -> str:
        """将相对路径解析到 datapath 下，并防止路径穿越。"""
        self.require("fs.datapath")
        rel = (relative_path or "").replace("\\", "/").lstrip("/")
        if not rel or ".." in rel.split("/"):
            raise PermissionError("非法路径")
        root = self.datapath
        if not root:
            raise PermissionError("datapath 不可用")
        if allow_plugin_data_only:
            base = os.path.join(root, "PluginData", self.plugin_id)
        else:
            base = root
        target = os.path.normpath(os.path.join(base, rel))
        base_real = os.path.realpath(base)
        target_real = os.path.realpath(target)
        try:
            common = os.path.commonpath([base_real, target_real])
        except ValueError:
            # Windows 不同盘符等情况
            raise PermissionError("路径越界，拒绝访问")
        if os.path.normcase(common) != os.path.normcase(base_real):
            raise PermissionError("路径越界，拒绝访问")
        return target_real

    def read_data_file(self, relative_path: str, encoding: str = "utf-8") -> str:
        """读取 datapath 下的文件（需 fs.datapath）。"""
        path = self._resolve_datapath_target(relative_path)
        self.log(f"read_data_file {relative_path}")
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    def write_data_file(self, relative_path: str, content: str, encoding: str = "utf-8") -> None:
        """写入 datapath 下的文件（需 fs.datapath）。建议优先写 PluginData/{id}/。"""
        path = self._resolve_datapath_target(relative_path)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.log(f"write_data_file {relative_path} bytes={len(content or '')}")
        with open(path, "w", encoding=encoding) as f:
            f.write(content if content is not None else "")

    def read_plugin_data_file(self, relative_path: str, encoding: str = "utf-8") -> str:
        """读取本插件 PluginData 目录下的文件（需 fs.datapath）。"""
        path = self._resolve_datapath_target(relative_path, allow_plugin_data_only=True)
        self.log(f"read_plugin_data_file {relative_path}")
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    def write_plugin_data_file(self, relative_path: str, content: str, encoding: str = "utf-8") -> None:
        """写入本插件 PluginData 目录（需 fs.datapath）。"""
        path = self._resolve_datapath_target(relative_path, allow_plugin_data_only=True)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.log(f"write_plugin_data_file {relative_path}")
        with open(path, "w", encoding=encoding) as f:
            f.write(content if content is not None else "")

    # ── 进程 ──────────────────────────────────────────────

    def exec_process(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        timeout: Optional[float] = 60,
        env: Optional[dict] = None,
    ) -> dict:
        """
        执行外部进程（需 process.exec）。
        cwd 必须在 datapath 或插件目录下；默认 timeout 60s。
        返回 {returncode, stdout, stderr}。
        """
        self.require("process.exec")
        import subprocess

        if not args or not isinstance(args, (list, tuple)):
            raise ValueError("args 必须为非空列表")
        cmd = [str(x) for x in args]
        workdir = cwd or self.plugin_dir
        workdir = os.path.realpath(workdir)
        allowed_roots = []
        if self.datapath:
            allowed_roots.append(os.path.realpath(self.datapath))
        if self.plugin_dir:
            allowed_roots.append(os.path.realpath(self.plugin_dir))
        if not any(workdir == r or workdir.startswith(r + os.sep) for r in allowed_roots):
            raise PermissionError(f"cwd 不在允许范围内: {workdir}")
        self.log(f"exec_process cmd={cmd[:3]}... cwd={workdir} timeout={timeout}")
        try:
            completed = subprocess.run(
                cmd,
                cwd=workdir,
                timeout=timeout,
                capture_output=True,
                text=True,
                env={**os.environ, **{str(k): str(v) for k, v in (env or {}).items()}} if env else None,
                shell=False,
            )
            return {
                "returncode": completed.returncode,
                "stdout": completed.stdout or "",
                "stderr": completed.stderr or "",
            }
        except subprocess.TimeoutExpired as e:
            self.log(f"exec_process 超时: {e}")
            return {"returncode": -1, "stdout": e.stdout or "", "stderr": f"timeout: {e}"}
        except Exception as e:
            self.log(f"exec_process 失败: {e}")
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    def register_web_route(
        self,
        method: str,
        path: str,
        handler: Callable,
        auth: str = "oauth",
    ) -> None:
        """
        注册本地 Web 路由（需 web.routes）。
        最终路径强制为 /api/v1/plugin/{plugin_id}/...
        handler(request_dict) -> dict|str|tuple
        """
        self.require("web.routes")
        method = (method or "GET").upper()
        allowed = ("GET", "POST", "PUT", "DELETE", "PATCH", "ANY", "*")
        if method not in allowed:
            raise ValueError(f"不支持的 HTTP 方法: {method}，允许: {', '.join(allowed)}")
        raw = (path or "").strip()
        if not raw.startswith("/"):
            raw = "/" + raw
        if "?" in raw or "#" in raw or ".." in raw.split("/"):
            raise ValueError("非法 Web 路由路径")
        # 去掉重复前缀
        prefix = f"/api/v1/plugin/{self.plugin_id}"
        if raw.startswith(prefix):
            full = raw
        else:
            full = prefix + (raw if raw.startswith("/") else "/" + raw)
        # 当前所有 /api/v1 路由均在入口统一 OAuth 校验；不接受伪 public 声明。
        auth_mode = (auth or "oauth").lower()
        if auth_mode != "oauth":
            self.log(f"register_web_route auth={auth_mode} 被规范化为 oauth")
            auth_mode = "oauth"
        item = {
            "plugin_id": self.plugin_id,
            "method": method,
            "path": full,
            "handler": handler,
            "auth": auth_mode,
        }
        self._registry.add_web_route(item)
        self.log(f"register_web_route {method} {full}")

    # ── 启动器能力封装 ────────────────────────────────────

    def list_versions(self) -> List[str]:
        """版本名列表。有 versions.read 时走服务层；无权限时仍返回只读列表（兼容 1.x）。"""
        try:
            if self.has_perm("versions.read") or self.has_perm("config.read"):
                from modules.services.versions_service import list_version_names

                return list_version_names()
            from modules.services.versions_service import list_version_names

            return list_version_names()
        except Exception as e:
            self.log(f"list_versions 失败: {e}")
            return []

    def list_versions_detail(self) -> List[dict]:
        """结构化版本列表（需 versions.read）。"""
        self.require("versions.read")
        from modules.services.versions_service import list_versions_detail

        result = list_versions_detail()
        if not result.ok:
            self.log(f"list_versions_detail 失败: {result.error}")
            return []
        return list(result.data or [])

    def get_version_path(self, version_name: str) -> Optional[dict]:
        """版本目录信息（需 versions.read）。"""
        self.require("versions.read")
        from modules.services.versions_service import get_version_path

        result = get_version_path(version_name)
        if not result.ok:
            self.log(f"get_version_path 失败: {result.error}")
            return None
        return result.data

    def list_running_instances(self) -> List[dict]:
        """当前运行中的游戏实例（需 launch.control 或默认只读兼容）。"""
        if not self.has_perm("launch.control"):
            # 只读摘要：仍要求至少 config.read 或 versions.read 之一，避免完全开放
            if not (self.has_perm("versions.read") or self.has_perm("config.read")):
                self.require("launch.control")
        from modules.services.launch_service import list_running_instances

        result = list_running_instances()
        if not result.ok:
            self.log(f"list_running_instances 失败: {result.error}")
            return []
        return list(result.data or [])

    def get_minecraft_dir(self) -> str:
        try:
            from modules.services.config_service import get_minecraft_dir

            return get_minecraft_dir()
        except Exception:
            data = cfg.read() or {}
            return str(data.get("minecraft_dir") or "")

    def list_mods(self, version_name: str) -> List[dict]:
        self.require("mods.read")
        from modules.services.content_service import list_mods

        result = list_mods(version_name)
        if not result.ok:
            self.log(f"list_mods 失败: {result.error}")
            return []
        return list(result.data or [])

    def list_resourcepacks(self, version_name: str) -> List[dict]:
        self.require("content.read")
        from modules.services.content_service import list_resourcepacks

        result = list_resourcepacks(version_name)
        if not result.ok:
            self.log(f"list_resourcepacks 失败: {result.error}")
            return []
        return list(result.data or [])

    def register_notification_channel(self, channel_id: str, handler: Callable, title: str = "") -> None:
        """注册通知渠道（需 notify.channel）。handler(title, body, **kwargs)。"""
        self.require("notify.channel")
        if not callable(handler):
            raise ValueError("handler 必须可调用")
        self._registry.add_channel(
            {
                "id": channel_id,
                "plugin_id": self.plugin_id,
                "title": title or channel_id,
                "handler": handler,
            }
        )
        self.log(f"register_notification_channel {channel_id}")

    def register_protocol_handler(self, path_prefix: str, handler: Callable) -> None:
        """注册 bloret:// 子路径处理器（需 protocol.handle）。"""
        self.require("protocol.handle")
        if not callable(handler):
            raise ValueError("handler 必须可调用")
        self._registry.add_protocol(
            {
                "path": (path_prefix or "").lstrip("/"),
                "plugin_id": self.plugin_id,
                "handler": handler,
            }
        )
        self.log(f"register_protocol_handler {path_prefix}")
