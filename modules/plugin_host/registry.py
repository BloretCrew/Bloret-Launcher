"""贡献点注册表：nav / theme / toolbar / agent / settings / home / tools / i18n / web。"""

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
