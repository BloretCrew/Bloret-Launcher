"""启动器业务服务门面。

PluginAPI 与 Web API 应优先调用本包，避免在 Backend / web 中重复实现。
子模块请直接 `from modules.services import x` 或 `from modules.services.x import ...`；
本包 __init__ 仅 re-export 轻量门面，避免导入时拖入 GUI 依赖。
"""

from modules.services import config_service, content_service, launch_service, versions_service

__all__ = [
    "config_service",
    "content_service",
    "launch_service",
    "versions_service",
]
