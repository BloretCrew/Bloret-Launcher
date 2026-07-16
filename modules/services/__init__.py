"""启动器业务服务门面。

PluginAPI 与 Web API 应优先调用本包，避免在 Backend / web 中重复实现。
Phase 0 仅提供薄封装；后续 Phase 逐步把业务逻辑迁入。
"""

from modules.services import config_service, content_service, launch_service, versions_service

__all__ = [
    "config_service",
    "content_service",
    "launch_service",
    "versions_service",
]
