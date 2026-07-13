"""Bloret Launcher 插件宿主。"""

from modules.plugin_host.dispatch import invoke_hook
from modules.plugin_host.event_bus import get_event_bus
from modules.plugin_host.host import PluginHost, bootstrap_plugins, get_plugin_host
from modules.plugin_host.registry import get_registry

__all__ = [
    "PluginHost",
    "get_plugin_host",
    "bootstrap_plugins",
    "get_event_bus",
    "get_registry",
    "invoke_hook",
]
