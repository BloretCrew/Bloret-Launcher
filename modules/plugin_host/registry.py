"""贡献点注册表：nav / theme / toolbar / agent / settings / home / tools / panels / sources / i18n / web。"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional

from modules.log import log


class ContributionRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self.nav: List[dict] = []
        self.settings: List[dict] = []
        self.toolbar: List[dict] = []
        self.home: List[dict] = []
        self.tools: List[dict] = []
        self.themes: Dict[str, dict] = {}  # plugin_id -> theme dict
        self.i18n: List[dict] = []  # {plugin_id, locale, path, data}
        self.web_routes: List[dict] = []
        self.agent_tools: Dict[str, List[dict]] = {"bloriko": [], "blrpe": []}
        self.prompt_appends: Dict[str, List[dict]] = {"bloriko": [], "blrpe": []}
        self.hooks: Dict[str, List[dict]] = {}  # hook_name -> [{plugin_id, fn}]
        self.plugin_modules: Dict[str, Any] = {}  # plugin_id -> module
        # Phase 0 泛化：按区域的 QML 面板
        # area -> [{id, plugin_id, title, qml, icon, order, ...}]
        self.panels: Dict[str, List[dict]] = {}
        # 内容源 / 下载源 / 通知渠道 / AI Provider / 协议 / 托盘 / 热键
        self.sources: Dict[str, List[dict]] = {
            "mods": [],
            "download": [],
        }
        self.channels: List[dict] = []  # notification channels
        self.providers: List[dict] = []  # AI providers
        self.protocols: List[dict] = []
        self.tray_menus: List[dict] = []
        self.hotkeys: List[dict] = []
        self.launch_items: List[dict] = []

    def clear_plugin(self, plugin_id: str) -> None:
        with self._lock:
            self.nav = [x for x in self.nav if x.get("plugin_id") != plugin_id]
            self.settings = [x for x in self.settings if x.get("plugin_id") != plugin_id]
            self.toolbar = [x for x in self.toolbar if x.get("plugin_id") != plugin_id]
            self.home = [x for x in self.home if x.get("plugin_id") != plugin_id]
            self.tools = [x for x in self.tools if x.get("plugin_id") != plugin_id]
            self.themes.pop(plugin_id, None)
            self.i18n = [x for x in self.i18n if x.get("plugin_id") != plugin_id]
            self.web_routes = [x for x in self.web_routes if x.get("plugin_id") != plugin_id]
            for key in self.agent_tools:
                self.agent_tools[key] = [
                    x for x in self.agent_tools[key] if x.get("plugin_id") != plugin_id
                ]
            for key in self.prompt_appends:
                self.prompt_appends[key] = [
                    x for x in self.prompt_appends[key] if x.get("plugin_id") != plugin_id
                ]
            for hook_name, lst in list(self.hooks.items()):
                self.hooks[hook_name] = [x for x in lst if x.get("plugin_id") != plugin_id]
            self.plugin_modules.pop(plugin_id, None)
            for area in list(self.panels.keys()):
                self.panels[area] = [
                    x for x in self.panels[area] if x.get("plugin_id") != plugin_id
                ]
            for key in list(self.sources.keys()):
                self.sources[key] = [
                    x for x in self.sources[key] if x.get("plugin_id") != plugin_id
                ]
            self.channels = [x for x in self.channels if x.get("plugin_id") != plugin_id]
            self.providers = [x for x in self.providers if x.get("plugin_id") != plugin_id]
            self.protocols = [x for x in self.protocols if x.get("plugin_id") != plugin_id]
            self.tray_menus = [x for x in self.tray_menus if x.get("plugin_id") != plugin_id]
            self.hotkeys = [x for x in self.hotkeys if x.get("plugin_id") != plugin_id]
            self.launch_items = [x for x in self.launch_items if x.get("plugin_id") != plugin_id]
        log(f"[PluginHost] Registry 已清除插件贡献: {plugin_id}")

    def add_nav(self, item: dict) -> None:
        with self._lock:
            self.nav.append(item)
        log(f"[PluginHost] 注册导航: {item.get('id')} @ {item.get('plugin_id')}")

    def add_settings(self, item: dict) -> None:
        with self._lock:
            self.settings.append(item)
        log(f"[PluginHost] 注册设置: {item.get('id')} @ {item.get('plugin_id')}")

    def add_toolbar(self, item: dict) -> None:
        with self._lock:
            self.toolbar.append(item)
        log(f"[PluginHost] 注册工具栏按钮: {item.get('id')} @ {item.get('plugin_id')}")

    def add_home(self, item: dict) -> None:
        with self._lock:
            self.home.append(item)
        log(f"[PluginHost] 注册主页卡片: {item.get('id')} @ {item.get('plugin_id')}")

    def add_tools(self, item: dict) -> None:
        with self._lock:
            self.tools.append(item)
        log(f"[PluginHost] 注册小工具卡片: {item.get('id')} @ {item.get('plugin_id')}")

    def add_panel(self, area: str, item: dict) -> None:
        area = (area or "").strip().lower()
        if not area:
            return
        with self._lock:
            self.panels.setdefault(area, []).append(item)
        log(
            f"[PluginHost] 注册面板 area={area} id={item.get('id')} @ {item.get('plugin_id')}"
        )

    def add_source(self, kind: str, item: dict) -> None:
        kind = (kind or "").strip().lower()
        if kind not in ("mods", "download"):
            kind = "mods"
        with self._lock:
            self.sources.setdefault(kind, []).append(item)
        log(f"[PluginHost] 注册源 kind={kind} id={item.get('id')} @ {item.get('plugin_id')}")

    def add_channel(self, item: dict) -> None:
        with self._lock:
            self.channels.append(item)
        log(f"[PluginHost] 注册通知渠道: {item.get('id')} @ {item.get('plugin_id')}")

    def add_provider(self, item: dict) -> None:
        with self._lock:
            self.providers.append(item)
        log(f"[PluginHost] 注册 AI Provider: {item.get('id')} @ {item.get('plugin_id')}")

    def add_protocol(self, item: dict) -> None:
        with self._lock:
            self.protocols.append(item)

    def add_tray_menu(self, item: dict) -> None:
        with self._lock:
            self.tray_menus.append(item)

    def add_hotkey(self, item: dict) -> None:
        with self._lock:
            self.hotkeys.append(item)

    def add_launch_item(self, item: dict) -> None:
        with self._lock:
            self.launch_items.append(item)

    def set_theme(self, plugin_id: str, theme: dict) -> None:
        with self._lock:
            self.themes[plugin_id] = theme
        log(f"[PluginHost] 注册主题: {plugin_id} name={theme.get('name')}")

    def add_i18n(self, item: dict) -> None:
        with self._lock:
            self.i18n.append(item)

    def add_web_route(self, item: dict) -> None:
        with self._lock:
            self.web_routes.append(item)

    def add_agent_tool(self, target: str, item: dict) -> None:
        target = "blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "bloriko"
        with self._lock:
            self.agent_tools[target].append(item)
        log(f"[PluginHost] 注册 Agent 工具 target={target} name={item.get('name')} @ {item.get('plugin_id')}")

    def add_prompt_append(self, target: str, item: dict) -> None:
        target = "blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "bloriko"
        with self._lock:
            self.prompt_appends[target].append(item)

    def add_hook(self, hook_name: str, plugin_id: str, fn: Callable) -> None:
        with self._lock:
            self.hooks.setdefault(hook_name, []).append({"plugin_id": plugin_id, "fn": fn})
        log(f"[PluginHost] 注册钩子 {hook_name} @ {plugin_id}")

    def get_nav(self) -> List[dict]:
        with self._lock:
            return list(self.nav)

    def get_settings(self) -> List[dict]:
        with self._lock:
            return list(self.settings)

    def get_toolbar(self) -> List[dict]:
        with self._lock:
            return list(self.toolbar)

    def get_home(self) -> List[dict]:
        with self._lock:
            items = list(self.home)
        return sorted(items, key=lambda x: (x.get("order", 100), str(x.get("id") or "")))

    def get_tools(self) -> List[dict]:
        with self._lock:
            items = list(self.tools)
        return sorted(items, key=lambda x: (x.get("order", 100), str(x.get("id") or "")))

    def get_panels(self, area: str) -> List[dict]:
        area = (area or "").strip().lower()
        with self._lock:
            items = list(self.panels.get(area, []))
        return sorted(items, key=lambda x: (x.get("order", 100), str(x.get("id") or "")))

    def get_all_panels(self) -> Dict[str, List[dict]]:
        with self._lock:
            return {k: list(v) for k, v in self.panels.items()}

    def get_sources(self, kind: str) -> List[dict]:
        kind = (kind or "").strip().lower()
        with self._lock:
            return list(self.sources.get(kind, []))

    def get_channels(self) -> List[dict]:
        with self._lock:
            return list(self.channels)

    def get_providers(self) -> List[dict]:
        with self._lock:
            return list(self.providers)

    def get_protocols(self) -> List[dict]:
        with self._lock:
            return list(self.protocols)

    def get_tray_menus(self) -> List[dict]:
        with self._lock:
            return list(self.tray_menus)

    def get_hotkeys(self) -> List[dict]:
        with self._lock:
            return list(self.hotkeys)

    def get_launch_items(self) -> List[dict]:
        with self._lock:
            return list(self.launch_items)

    def get_i18n(self) -> List[dict]:
        with self._lock:
            return list(self.i18n)

    def get_web_routes(self) -> List[dict]:
        with self._lock:
            return list(self.web_routes)

    def get_theme(self, plugin_id: str) -> Optional[dict]:
        with self._lock:
            return self.themes.get(plugin_id)

    def get_themes(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self.themes)

    def get_agent_tools(self, target: str) -> List[dict]:
        target = "blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "bloriko"
        with self._lock:
            return list(self.agent_tools.get(target, []))

    def get_prompt_appends(self, target: str) -> List[str]:
        target = "blrpe" if target in ("blrpe", "agent", "copilot", "rpe") else "bloriko"
        with self._lock:
            return [x.get("text", "") for x in self.prompt_appends.get(target, []) if x.get("text")]

    def call_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        with self._lock:
            entries = list(self.hooks.get(hook_name, []))
        results = []
        for entry in entries:
            plugin_id = entry.get("plugin_id", "?")
            fn = entry.get("fn")
            if not callable(fn):
                continue
            try:
                results.append(fn(*args, **kwargs))
            except Exception as e:
                log(f"[PluginHost] 钩子 {hook_name} @ {plugin_id} 异常: {e}")
                results.append(None)
        return results

    def collect_jvm_args(self, version: str, base_args: Optional[List[str]] = None) -> List[str]:
        """调用 launch.jvm_args 钩子，合并追加参数。"""
        from modules.plugin_host.dispatch import invoke_hook

        extra: List[str] = []
        results = invoke_hook("launch.jvm_args", version, list(base_args or []))
        for r in results:
            if isinstance(r, (list, tuple)):
                extra.extend(str(x) for x in r)
            elif isinstance(r, str) and r:
                extra.append(r)
        return extra

    def collect_env(self, version: str, base_env: Optional[dict] = None) -> dict:
        from modules.plugin_host.dispatch import invoke_hook

        env = dict(base_env or {})
        results = invoke_hook("launch.env", version, dict(env))
        for r in results:
            if isinstance(r, dict):
                env.update({str(k): str(v) for k, v in r.items()})
        return env

    def launch_pre_cancel(self, version: str, context: Optional[dict] = None) -> Optional[str]:
        """若任一钩子返回 cancel，返回 reason。

        使用统一派发，使 api.on('launch.pre') 与 register_hook 均可拦截。
        """
        from modules.plugin_host.dispatch import invoke_hook

        results = invoke_hook("launch.pre", version, context or {})
        for r in results:
            if isinstance(r, dict) and r.get("cancel"):
                return str(r.get("reason") or "插件取消启动")
            if r is False:
                return "插件取消启动"
        return None


_registry: Optional[ContributionRegistry] = None


def get_registry() -> ContributionRegistry:
    global _registry
    if _registry is None:
        _registry = ContributionRegistry()
    return _registry
