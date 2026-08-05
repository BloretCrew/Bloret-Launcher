"""内容域门面：mods / 资源包 / 服务器列表（只读为主）。"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import modules.config as cfg
from modules.services.base import ServiceResult, err, ok


def _safe_version_dir(version_name: str) -> str:
    root = _versions_root()
    if not root or not version_name:
        return ""
    root_abs = os.path.abspath(root)
    candidate = os.path.abspath(os.path.join(root_abs, version_name))
    try:
        if os.path.commonpath([candidate, root_abs]) != root_abs:
            return ""
    except ValueError:
        return ""
    return candidate


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
    return _list_folder_content(version_name, "resourcepacks")


def list_shaderpacks(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    return _list_folder_content(version_name, "shaderpacks")


def list_datapacks(version_name: str) -> ServiceResult[List[Dict[str, Any]]]:
    return _list_folder_content(version_name, "datapacks")


def _list_folder_content(version_name: str, folder: str) -> ServiceResult[List[Dict[str, Any]]]:
    if not version_name:
        return err("version required", "invalid_version")
    root = _versions_root()
    if not root:
        return err("minecraft_dir not set", "no_minecraft_dir")
    version_dir = _safe_version_dir(version_name)
    if not version_dir:
        return err("invalid version path", "invalid_version")
    d = os.path.join(version_dir, folder)
    if not os.path.isdir(d):
        return ok([])
    items: List[Dict[str, Any]] = []
    try:
        for name in sorted(os.listdir(d)):
            path = os.path.join(d, name)
            if os.path.isfile(path) or os.path.isdir(path):
                enabled = not name.endswith(".disabled")
                items.append(
                    {
                        "name": name,
                        "path": path,
                        "is_dir": os.path.isdir(path),
                        "enabled": enabled,
                        "kind": folder.rstrip("s") if folder.endswith("s") else folder,
                    }
                )
        return ok(items)
    except Exception as e:
        return err(str(e), f"{folder}_list_failed")
