"""启动器业务服务门面。

PluginAPI 与 Web API 应优先调用本包，避免在 Backend / web 中重复实现。
服务模块按需导入，保证纯逻辑 helper 可脱离 GUI 依赖使用。
"""

from importlib import import_module


__all__ = [
    "config_service",
    "content_service",
    "launch_service",
    "live_chat",
    "versions_service",
    "runtime_state",
    "recent_runs",
]


def __getattr__(name):
    if name in __all__:
        module = import_module(f"modules.services.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
