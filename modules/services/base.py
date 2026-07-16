"""服务层通用结果类型与工具。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """统一服务返回：ok + data 或 error。"""

    ok: bool
    data: Optional[T] = None
    error: str = ""
    code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        if self.ok:
            payload: Dict[str, Any] = {"status": "success", "ok": True}
            if self.data is not None:
                payload["data"] = self.data
            return payload
        return {
            "status": "error",
            "ok": False,
            "message": self.error or "unknown error",
            "code": self.code or "error",
        }


def ok(data: T = None) -> ServiceResult[T]:  # type: ignore[assignment]
    return ServiceResult(ok=True, data=data)


def err(message: str, code: str = "error") -> ServiceResult[Any]:
    return ServiceResult(ok=False, error=str(message or "error"), code=code)


# 已知 panel 区域（contributes.panels / ui.*）
PANEL_AREAS = frozenset(
    {
        "cores",
        "mods",
        "download",
        "live",
        "passport",
        "bbbs",
        "stats",
        "info",
        "bloriko",
        "rpe",
        "multiplayer",
        "home",  # 兼容：也可走 home 贡献
        "tools",
    }
)

# contributes 键 -> 权限
PANEL_PERMISSIONS: Dict[str, str] = {
    "cores": "ui.cores",
    "mods": "ui.mods",
    "download": "ui.download",
    "live": "ui.live",
    "passport": "ui.passport",
    "bbbs": "ui.bbbs",
    "stats": "ui.stats",
    "info": "ui.info",
    "bloriko": "ui.bloriko",
    "rpe": "ui.rpe",
    "multiplayer": "ui.multiplayer",
}
