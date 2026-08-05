"""从 MultiMC / PrismLauncher 导入实例。"""

from __future__ import annotations

import configparser
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules.services.base import ServiceResult, err, ok
from modules.services.paths_util import minecraft_dir, safe_version_dir, versions_root


def _read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def _parse_cfg(path: Path) -> Dict[str, str]:
    raw = _read_text(path)
    # MultiMC instance.cfg 类似 ini 但常无 section
    if raw and not re.search(r"^\s*\[", raw, re.M):
        raw = "[instance]\n" + raw
    parser = configparser.ConfigParser()
    try:
        parser.read_string(raw)
    except Exception:
        return {}
    out: Dict[str, str] = {}
    for section in parser.sections():
        for k, v in parser.items(section):
            out[k] = v
    return out


def is_valid_mmc_instance(instance_path: str) -> bool:
    p = Path(instance_path)
    return (p / "instance.cfg").is_file() or (p / "mmc-pack.json").is_file()


def list_importable_instances(base_path: str) -> ServiceResult[List[Dict[str, Any]]]:
    base = Path(base_path)
    if not base.is_dir():
        return err("path not found", "not_found")
    # 直接指向 instances 目录，或启动器根目录
    candidates = []
    if (base / "instances").is_dir():
        root = base / "instances"
    else:
        root = base
    try:
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if is_valid_mmc_instance(str(child)):
                cfg = _parse_cfg(child / "instance.cfg") if (child / "instance.cfg").is_file() else {}
                name = cfg.get("name") or child.name
                candidates.append(
                    {
                        "folder": child.name,
                        "name": name,
                        "path": str(child),
                        "minecraft_version": cfg.get("ManagedVersion") or cfg.get("MinecraftVersion") or "",
                    }
                )
    except Exception as e:
        return err(str(e), "list_failed")
    return ok(candidates)


def _detect_components(instance_path: Path) -> Dict[str, str]:
    """从 mmc-pack.json 解析 minecraft / fabric / forge / quilt 版本。"""
    out = {"minecraft": "", "loader": "vanilla", "loader_version": ""}
    pack = instance_path / "mmc-pack.json"
    if not pack.is_file():
        cfg = _parse_cfg(instance_path / "instance.cfg")
        out["minecraft"] = cfg.get("ManagedVersion") or cfg.get("IntendedVersion") or ""
        return out
    try:
        data = json.loads(_read_text(pack))
    except Exception:
        return out
    for comp in data.get("components") or []:
        if not isinstance(comp, dict):
            continue
        uid = str(comp.get("uid") or "").lower()
        ver = str(comp.get("version") or "")
        if uid in ("net.minecraft", "minecraft"):
            out["minecraft"] = ver
        elif "fabric" in uid and "loader" in uid:
            out["loader"] = "fabric"
            out["loader_version"] = ver
        elif "quilt" in uid and "loader" in uid:
            out["loader"] = "quilt"
            out["loader_version"] = ver
        elif "neoforge" in uid or "neoforged" in uid:
            out["loader"] = "neoforge"
            out["loader_version"] = ver
        elif "minecraftforge" in uid or uid.endswith("forge"):
            if "neoforge" not in out["loader"]:
                out["loader"] = "forge"
                out["loader_version"] = ver
    return out


def _copy_tree(src: Path, dst: Path, skip_names: Optional[set] = None) -> int:
    skip = skip_names or set()
    count = 0
    if not src.exists():
        return 0
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return 1
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        # 过滤
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        for name in files:
            if name in skip or name.startswith("."):
                continue
            s = Path(root) / name
            if rel_root in (".", ""):
                d = dst / name
            else:
                d = dst / rel_path_safe(rel_root) / name
            d.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(s, d)
                count += 1
            except Exception:
                pass
    return count


def rel_path_safe(p: str) -> Path:
    parts = [x for x in Path(p).parts if x not in (".", "..")]
    return Path(*parts) if parts else Path()


def import_mmc_instance(
    instance_path: str,
    *,
    target_name: Optional[str] = None,
    mc_dir: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    """
    导入 MultiMC/Prism 实例到 Bloret versions/<name>。

    策略：复制 .minecraft 内容（mods/config/saves/...）到新 version 目录；
    若已有完整 version JSON 则一并带上；否则只导入内容，用户需自行有对应 loader 版本，
    或依赖后续安装流程。
    """
    src = Path(instance_path)
    if not is_valid_mmc_instance(str(src)):
        return err("不是有效的 MultiMC/Prism 实例", "invalid_instance")

    cfg = _parse_cfg(src / "instance.cfg") if (src / "instance.cfg").is_file() else {}
    components = _detect_components(src)
    name = target_name or cfg.get("name") or src.name
    # 清理非法文件夹名
    name = re.sub(r'[<>:"/\\|?*]', "_", name).strip() or src.name

    root = mc_dir or minecraft_dir()
    if not root:
        return err("minecraft_dir not set", "no_minecraft_dir")
    vroot = versions_root(root)
    dest = Path(vroot) / name
    if dest.exists():
        return err(f"目标版本已存在: {name}", "already_exists")

    # MMC 的 .minecraft 可能在 instance/.minecraft 或 instance/minecraft
    dot_mc = src / ".minecraft"
    if not dot_mc.is_dir():
        dot_mc = src / "minecraft"
    if not dot_mc.is_dir():
        # 有些把内容直接放实例根
        dot_mc = src

    try:
        dest.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return err(f"目标版本已存在: {name}", "already_exists")
    except Exception as e:
        return err(str(e), "mkdir_failed")

    skip = {"cache", "libraries", "assets", "versions", "webcache2", "logs", ".cache"}
    copied = _copy_tree(dot_mc, dest, skip_names=skip)

    # 图标
    for icon_name in ("minecraft.png", "icon.png", "instance.png"):
        icon = src / icon_name
        if icon.is_file():
            try:
                shutil.copy2(icon, dest / "icon.png")
            except Exception:
                pass
            break

    # 写 bl 侧车与 instance-settings 种子
    mc_ver = components.get("minecraft") or cfg.get("ManagedVersion") or ""
    loader = components.get("loader") or "vanilla"
    try:
        from modules.install import update_bl_json

        update_bl_json(root, name, fabric_loader=(loader == "fabric"), icon_path=None)
        # 补充 loader 字段
        bl_path = os.path.join(root, "versions", ".BL.json")
        if os.path.isfile(bl_path):
            with open(bl_path, "r", encoding="utf-8") as f:
                bl = json.load(f)
            entry = (bl.get("versions") or {}).get(name) or {}
            entry["version"] = mc_ver or entry.get("version") or name
            entry["loader"] = loader
            entry["Fabric"] = loader == "fabric"
            entry["Quilt"] = loader == "quilt"
            entry["Forge"] = loader == "forge"
            entry["NeoForge"] = loader == "neoforge"
            entry["imported_from"] = "prism" if "prism" in str(src).lower() else "multimc"
            bl.setdefault("versions", {})[name] = entry
            with open(bl_path, "w", encoding="utf-8") as f:
                json.dump(bl, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

    # JVM 参数
    jvm = cfg.get("JvmArgs") or cfg.get("jvmargs") or ""
    if jvm:
        try:
            from modules.services import instance_settings

            instance_settings.save(name, {"jvm_args": jvm}, mc_dir=root)
        except Exception:
            pass

    # 扫描内容索引
    try:
        from modules.services import content_index

        content_index.scan_filesystem(name, mc_dir=root, compute_hash=False)
    except Exception:
        pass

    note = ""
    if not any(dest.glob("*.json")):
        note = (
            "已导入 mods/config/saves 等内容，但未包含可启动的 version JSON。"
            "请在下载页安装对应 MC + Loader，或把已有版本 JSON/JAR 拷入该目录后启动。"
        )

    return ok(
        {
            "name": name,
            "path": str(dest),
            "copied_files": copied,
            "minecraft": mc_ver,
            "loader": loader,
            "loader_version": components.get("loader_version") or "",
            "note": note,
        }
    )


def default_prism_path() -> Optional[str]:
    candidates = []
    data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    candidates.append(os.path.join(data, "PrismLauncher"))
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, "PrismLauncher"))
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or ""
        if appdata:
            candidates.append(os.path.join(appdata, "PrismLauncher"))
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def default_multimc_path() -> Optional[str]:
    candidates = []
    data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    candidates += [os.path.join(data, "multimc"), os.path.join(data, "MultiMC")]
    home = os.path.expanduser("~")
    candidates += [os.path.join(home, "MultiMC"), os.path.join(home, "multimc")]
    if os.name == "nt":
        for base in filter(None, [os.environ.get("USERPROFILE"), "C:\\"]):
            candidates += [
                os.path.join(base, "MultiMC"),
                os.path.join(base, "Desktop", "MultiMC"),
            ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "multimc.cfg")) or os.path.isdir(os.path.join(c, "instances")):
            return c
    return None
