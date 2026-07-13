"""统一钩子派发：同时调用 registry hooks 与 event bus 监听器。

插件可通过以下任一方式订阅标准生命周期事件：
- api.register_hook(name, fn) / manifest hooks
- api.on(name, fn) / api.once(name, fn)

两者都会收到 invoke_hook 广播，避免「只写了 register_hook 却永远不触发」的分裂。
"""

from __future__ import annotations

from typing import Any, List

from modules.log import log
from modules.plugin_host.event_bus import get_event_bus
from modules.plugin_host.registry import get_registry


def invoke_hook(name: str, *args, **kwargs) -> List[Any]:
    """同步派发钩子/事件，返回 registry 与 bus 监听器返回值的合并列表。"""
    if not name:
        return []
    log(f"[PluginHost] invoke_hook {name} args={len(args)} kwargs={list(kwargs.keys())}")
    results: List[Any] = []
    try:
        results.extend(get_registry().call_hooks(name, *args, **kwargs))
    except Exception as e:
        log(f"[PluginHost] invoke_hook registry 失败 {name}: {e}")
    try:
        results.extend(get_event_bus().emit(name, *args, **kwargs))
    except Exception as e:
        log(f"[PluginHost] invoke_hook bus 失败 {name}: {e}")
    return results
