"""版本目录路径工具（服务层共用）。"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import modules.config as cfg


def minecraft_dir() -> str:
    data = cfg.read() or {}
    return str(data.get("minecraft_dir") or "")


def versions_root(mc_dir: Optional[str] = None) -> str:
    root = mc_dir if mc_dir is not None else minecraft_dir()
    if not root:
        return ""
    return os.path.join(root, "versions")


def safe_version_dir(version_name: str, mc_dir: Optional[str] = None) -> str:
    """返回 versions/<name> 的绝对路径；越界或不合法时返回空串。"""
    if not version_name or ".." in version_name or "/" in version_name or "\\" in version_name:
        return ""
    root = versions_root(mc_dir)
    if not root:
        return ""
    root_abs = os.path.abspath(root)
    candidate = os.path.abspath(os.path.join(root_abs, version_name))
    try:
        if os.path.commonpath([candidate, root_abs]) != root_abs:
            return ""
    except ValueError:
        return ""
    return candidate


def content_dir(version_name: str, kind: str, mc_dir: Optional[str] = None) -> str:
    """kind: mods | resourcepacks | shaderpacks | datapacks | saves"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return ""
    mapping = {
        "mod": "mods",
        "mods": "mods",
        "resourcepack": "resourcepacks",
        "resourcepacks": "resourcepacks",
        "shader": "shaderpacks",
        "shaderpack": "shaderpacks",
        "shaderpacks": "shaderpacks",
        "datapack": "datapacks",
        "datapacks": "datapacks",
        "saves": "saves",
        "world": "saves",
        "worlds": "saves",
    }
    sub = mapping.get((kind or "").lower())
    if not sub:
        return ""
    return os.path.join(vdir, sub)


def resolve_game_version(version_name: str, mc_dir: Optional[str] = None) -> str:
    """从 .BL.json / 版本 JSON / 文件夹名解析 MC 版本号。"""
    import json
    import re

    root = mc_dir if mc_dir is not None else minecraft_dir()
    if root:
        bl_path = os.path.join(root, "versions", ".BL.json")
        if os.path.isfile(bl_path):
            try:
                with open(bl_path, "r", encoding="utf-8") as f:
                    bl = json.load(f)
                entry = (bl.get("versions") or {}).get(version_name) or {}
                ver = entry.get("version")
                if ver:
                    return str(ver)
            except Exception:
                pass
        vdir = safe_version_dir(version_name, root)
        if vdir:
            for candidate in (
                os.path.join(vdir, f"{version_name}.json"),
                os.path.join(vdir, "version.json"),
            ):
                if not os.path.isfile(candidate):
                    continue
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # inheritsFrom 优先，否则 id
                    inherited = data.get("inheritsFrom")
                    if inherited:
                        return str(inherited)
                    vid = data.get("id") or ""
                    m = re.match(r"^(\d+\.\d+(?:\.\d+)?)", str(vid))
                    if m:
                        return m.group(1)
                    if vid and not any(x in vid.lower() for x in ("fabric", "forge", "quilt", "neoforge")):
                        return str(vid)
                except Exception:
                    pass
    m = re.match(r"^(\d+\.\d+(?:\.\d+)?)", version_name or "")
    return m.group(1) if m else ""


def detect_loader(version_name: str, mc_dir: Optional[str] = None) -> str:
    """返回 fabric | forge | neoforge | quilt | vanilla。"""
    import json

    name_l = (version_name or "").lower()
    if "quilt" in name_l:
        return "quilt"
    if "neoforge" in name_l:
        return "neoforge"
    if "forge" in name_l and "neoforge" not in name_l:
        return "forge"
    if "fabric" in name_l:
        return "fabric"

    root = mc_dir if mc_dir is not None else minecraft_dir()
    if root:
        bl_path = os.path.join(root, "versions", ".BL.json")
        if os.path.isfile(bl_path):
            try:
                with open(bl_path, "r", encoding="utf-8") as f:
                    bl = json.load(f)
                entry = (bl.get("versions") or {}).get(version_name) or {}
                if entry.get("Quilt"):
                    return "quilt"
                if entry.get("NeoForge"):
                    return "neoforge"
                if entry.get("Forge"):
                    return "forge"
                if entry.get("Fabric"):
                    return "fabric"
                loader = str(entry.get("loader") or "").lower()
                if loader in ("fabric", "forge", "neoforge", "quilt"):
                    return loader
            except Exception:
                pass
        vdir = safe_version_dir(version_name, root)
        if vdir:
            jpath = os.path.join(vdir, f"{version_name}.json")
            if os.path.isfile(jpath):
                try:
                    with open(jpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    main = str(data.get("mainClass") or "").lower()
                    libs = " ".join(
                        str(lib.get("name") or "").lower()
                        for lib in (data.get("libraries") or [])
                        if isinstance(lib, dict)
                    )
                    blob = main + " " + libs + " " + str(data.get("id") or "").lower()
                    if "quilt" in blob:
                        return "quilt"
                    if "neoforge" in blob or "neoforged" in blob:
                        return "neoforge"
                    if "minecraftforge" in blob or "net.minecraftforge" in blob:
                        return "forge"
                    if "fabric" in blob:
                        return "fabric"
                except Exception:
                    pass
    return "vanilla"


def pair_version_context(version_name: str, mc_dir: Optional[str] = None) -> Tuple[str, str, str]:
    """(version_dir, game_version, loader)"""
    return (
        safe_version_dir(version_name, mc_dir),
        resolve_game_version(version_name, mc_dir),
        detect_loader(version_name, mc_dir),
    )
