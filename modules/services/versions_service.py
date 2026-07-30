"""版本/实例列表门面。"""

from __future__ import annotations

import os
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


def get_version_path(version_name: str) -> ServiceResult[Dict[str, Any]]:
    if not version_name:
        return err("version required", "invalid_version")
    data = cfg.read() or {}
    mc_dir = str(data.get("minecraft_dir") or "")
    if not mc_dir:
        return err("minecraft_dir not set", "no_minecraft_dir")
    versions_root = os.path.abspath(os.path.join(mc_dir, "versions"))
    vdir = os.path.abspath(os.path.join(versions_root, version_name))
    try:
        if os.path.commonpath([vdir, versions_root]) != versions_root:
            return err("invalid version path", "invalid_version")
    except ValueError:
        return err("invalid version path", "invalid_version")
    if not os.path.isdir(vdir):
        return err(f"version not found: {version_name}", "not_found")
    return ok({"name": version_name, "path": vdir, "minecraft_dir": mc_dir})
