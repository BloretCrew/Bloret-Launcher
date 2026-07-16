"""内容域门面：mods / 资源包 / 服务器列表（只读为主）。"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import modules.config as cfg
from modules.services.base import ServiceResult, err, ok


def _versions_root() -> str:
    data = cfg.read() or {}
    mc_dir = str(data.get("minecraft_dir") or "")
    if not mc_dir:
        return ""
    return os.path.join(mc_dir, "versions")


def list_mods(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    if not version_name:
        return err("version required", "invalid_version")
    root = _versions_root()
    if not root:
        return err("minecraft_dir not set", "no_minecraft_dir")
    mods_dir = os.path.join(root, version_name, "mods")
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
            items.append(
                {
                    "name": name,
                    "path": path,
                    "enabled": enabled,
                    "size": os.path.getsize(path),
                }
            )
        return ok(items)
    except Exception as e:
        return err(str(e), "mods_list_failed")


def list_resourcepacks(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    if not version_name:
        return err("version required", "invalid_version")
    root = _versions_root()
    if not root:
        return err("minecraft_dir not set", "no_minecraft_dir")
    rp_dir = os.path.join(root, version_name, "resourcepacks")
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
