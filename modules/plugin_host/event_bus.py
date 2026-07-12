"""全局事件总线：同步 emit / on / once。"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from modules.log import log

Listener = Callable[..., Any]


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[dict]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[dict] = []
        self._history_limit = 100

    def on(self, event: str, callback: Listener, plugin_id: Optional[str] = None, once: bool = False) -> Callable:
        """订阅事件，返回取消订阅函数。"""
        entry = {"cb": callback, "plugin_id": plugin_id, "once": once}
        with self._lock:
            self._listeners[event].append(entry)
        log(f"[PluginHost] EventBus.on {event} (plugin={plugin_id or 'core'})")

        def unsubscribe():
            with self._lock:
                lst = self._listeners.get(event, [])
                if entry in lst:
                    lst.remove(entry)

        return unsubscribe

    def once(self, event: str, callback: Listener, plugin_id: Optional[str] = None) -> Callable:
        return self.on(event, callback, plugin_id=plugin_id, once=True)

    def off_plugin(self, plugin_id: str) -> int:
        """移除某插件的全部监听。"""
        removed = 0
        with self._lock:
            for event, lst in list(self._listeners.items()):
                before = len(lst)
                self._listeners[event] = [e for e in lst if e.get("plugin_id") != plugin_id]
                removed += before - len(self._listeners[event])
        if removed:
            log(f"[PluginHost] EventBus 移除插件 {plugin_id} 的 {removed} 个监听")
        return removed

    def emit(self, event: str, *args, **kwargs) -> List[Any]:
        """同步广播事件，返回各监听器返回值列表。"""
        with self._lock:
            listeners = list(self._listeners.get(event, []))
            self._history.append({"event": event, "args_len": len(args), "kwargs_keys": list(kwargs.keys())})
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit :]

        if not listeners:
            return []

        log(f"[PluginHost] EventBus.emit {event} -> {len(listeners)} listener(s)")
        results = []
        to_remove = []
        for entry in listeners:
            cb = entry["cb"]
            plugin_id = entry.get("plugin_id") or "core"
            try:
                results.append(cb(*args, **kwargs))
            except Exception as e:
                log(f"[PluginHost] EventBus 监听器失败 event={event} plugin={plugin_id}: {e}")
                results.append(None)
            if entry.get("once"):
                to_remove.append(entry)

        if to_remove:
            with self._lock:
                lst = self._listeners.get(event, [])
                for entry in to_remove:
                    if entry in lst:
                        lst.remove(entry)
        return results

    def history(self) -> List[dict]:
        with self._lock:
            return list(self._history)


# 进程级单例
_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
