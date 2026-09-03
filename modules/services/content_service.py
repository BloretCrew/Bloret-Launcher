"""内容域门面：mods / 资源包 / 服务器列表（只读为主）。"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from modules.services.base import ServiceResult, err, ok


def _safe_version_dir(version_name: str) -> str:
    from modules.services.versions_service import get_version_path

    result = get_version_path(version_name)
    return result.data["path"] if result.ok and result.data else ""


def list_mods(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    if not version_name:
        return err("version required", "invalid_version")
    version_dir = _safe_version_dir(version_name)
    if not version_dir:
        return err("invalid version path", "invalid_version")
    mods_dir = os.path.join(version_dir, "mods")
    if not os.path.isdir(mods_dir):
        return ok([])
    items: List[Dict[str, Any]] = []
    try:
        for name in sorted(os.listdir(mods_dir)):
            path = os.path.join(mods_dir, name)
            if not os.path.isfile(path):
                continue
            lower = name.lower()
            if not (lower.endswith(".jar") or lower.endswith(".jar.disabled") or lower.endswith(".disabled")):
                continue
            enabled = not name.endswith(".disabled")
            items.append({"name": name, "path": path, "enabled": enabled, "size": os.path.getsize(path)})
        return ok(items)
    except Exception as e:
        return err(str(e), "mods_list_failed")


def list_resourcepacks(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    if not version_name:
        return err("version required", "invalid_version")
    version_dir = _safe_version_dir(version_name)
    if not version_dir:
        return err("invalid version path", "invalid_version")
    rp_dir = os.path.join(version_dir, "resourcepacks")
    if not os.path.isdir(rp_dir):
        return ok([])
    items: List[Dict[str, Any]] = []
    try:
        for name in sorted(os.listdir(rp_dir)):
            path = os.path.join(rp_dir, name)
            if os.path.isfile(path) or os.path.isdir(path):
                items.append({"name": name, "path": path, "is_dir": os.path.isdir(path)})
        return ok(items)
    except Exception as e:
        return err(str(e), "resourcepacks_list_failed")
