"""版本/实例列表门面。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import modules.config as cfg
from modules.services.base import ServiceResult, err, ok


def list_version_names() -> List[str]:
    data = cfg.read() or {}
    mc_dir = data.get("minecraft_dir") or ""
    versions_dir = os.path.join(mc_dir, "versions") if mc_dir else ""
    if not versions_dir or not os.path.isdir(versions_dir):
        return []
    try:
        return sorted(
            [
                name
                for name in os.listdir(versions_dir)
                if os.path.isdir(os.path.join(versions_dir, name))
            ]
        )
    except Exception:
        return []


def list_versions_detail() -> ServiceResult[List[Dict[str, Any]]]:
    """返回结构化版本列表（名称、路径、是否存在 json）。"""
    try:
        data = cfg.read() or {}
        mc_dir = str(data.get("minecraft_dir") or "")
        versions_dir = os.path.join(mc_dir, "versions") if mc_dir else ""
        if not versions_dir or not os.path.isdir(versions_dir):
            return ok([])
        items: List[Dict[str, Any]] = []
        for name in sorted(os.listdir(versions_dir)):
            vdir = os.path.join(versions_dir, name)
            if not os.path.isdir(vdir):
                continue
            json_path = os.path.join(vdir, f"{name}.json")
            jar_path = os.path.join(vdir, f"{name}.jar")
            bl_json = os.path.join(vdir, "bl.json")
            items.append(
                {
                    "name": name,
                    "path": vdir,
                    "has_json": os.path.isfile(json_path),
                    "has_jar": os.path.isfile(jar_path),
                    "has_bl_json": os.path.isfile(bl_json),
                }
            )
        return ok(items)
    except Exception as e:
        return err(str(e), "versions_list_failed")


def resolve_version_directory(version_name: str) -> ServiceResult[Dict[str, Any]]:
    """Compatibility name for the single validated version-directory resolver."""
    return get_version_path(version_name)


def get_version_path(version_name: str) -> ServiceResult[Dict[str, Any]]:
    if not version_name:
        return err("version required", "invalid_version")
    data = cfg.read() or {}
    mc_dir = str(data.get("minecraft_dir") or "")
    if not mc_dir:
        return err("minecraft_dir not set", "no_minecraft_dir")
    if not isinstance(version_name, str) or not version_name.strip():
        return err("invalid version path", "invalid_version")
    if version_name != os.path.basename(version_name) or "/" in version_name or "\\" in version_name:
        return err("invalid version path", "invalid_version")
    versions_root = Path(mc_dir, "versions").resolve()
    candidate = versions_root / version_name
    try:
        vdir = candidate.resolve(strict=True)
        vdir.relative_to(versions_root)
    except (FileNotFoundError, OSError, ValueError):
        return err("invalid version path", "invalid_version")
    if not vdir.is_dir() or candidate.is_symlink():
        return err("invalid version path", "invalid_version")
    return ok({"name": version_name, "path": str(vdir), "minecraft_dir": mc_dir})
