"""配置读写门面（薄封装 modules.config）。"""

from __future__ import annotations

from typing import Any, Optional

import modules.config as cfg
from modules.services.base import ServiceResult, err, ok


def read(key: Optional[str] = None, default: Any = None) -> ServiceResult[Any]:
    try:
        data = cfg.read() or {}
        if key is None:
            return ok(data)
        return ok(data.get(key, default))
    except Exception as e:
        return err(str(e), "config_read_failed")


def update_keys(values: dict) -> ServiceResult[dict]:
    if not isinstance(values, dict) or not values:
        return err("values required", "invalid_values")
    try:
        import modules.config as config_module
        data = config_module.update_keys(**values)
        return ok({key: data.get(key) for key in values})
    except Exception as e:
        return err(str(e), "config_write_failed")


def write_key(key: str, value: Any) -> ServiceResult[Any]:
    if not key:
        return err("key required", "invalid_key")
    try:
        data = cfg.read() or {}
        data[key] = value
        # 真实路径：modules.config.write → 磁盘 + config.changed
        if not cfg.write(data, changed_keys={key: value}):
            return err("write failed", "config_write_failed")
        return ok({key: value})
    except Exception as e:
        return err(str(e), "config_write_failed")


def get_minecraft_dir() -> str:
    data = cfg.read() or {}
    return str(data.get("minecraft_dir") or "")
