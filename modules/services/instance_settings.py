"""实例级设置 overrides（内存 / Java / JVM / 环境 / 窗口 / hooks）。

存储：versions/<name>/instance-settings.json
同时兼容 .BL.json 里的 jvmArgs 字段。
"""

from __future__ import annotations

import json
import os
import shlex
import time
from typing import Any, Dict, List, Optional, Tuple

from modules.services.base import ServiceResult, err, ok
from modules.services.paths_util import minecraft_dir, safe_version_dir

SETTINGS_FILE = "instance-settings.json"
SCHEMA_VERSION = 1

DEFAULTS: Dict[str, Any] = {
    "java_min_memory": None,  # None = 跟随全局
    "java_max_memory": None,
    "java_path": None,
    "jvm_args": "",  # 额外 JVM 参数字符串
    "env_vars": {},  # {KEY: VALUE}
    "resolution_width": None,
    "resolution_height": None,
    "fullscreen": None,
    "quick_play": {
        "type": None,  # None | "singleplayer" | "multiplayer"
        "world": None,
        "server": None,
        "port": None,
    },
    "hooks": {
        "pre_launch": "",
        "wrapper": "",
        "post_exit": "",
    },
    "custom_game_args": "",
}


def settings_path(version_name: str, mc_dir: Optional[str] = None) -> str:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return ""
    return os.path.join(vdir, SETTINGS_FILE)


def _read_bl_jvm(version_name: str, mc_dir: Optional[str] = None) -> str:
    root = mc_dir or minecraft_dir()
    if not root:
        return ""
    bl = os.path.join(root, "versions", ".BL.json")
    if not os.path.isfile(bl):
        return ""
    try:
        with open(bl, "r", encoding="utf-8") as f:
            data = json.load(f)
        entry = (data.get("versions") or {}).get(version_name) or {}
        return str(entry.get("jvmArgs") or "")
    except Exception:
        return ""


def _write_bl_jvm(version_name: str, jvm_args: str, mc_dir: Optional[str] = None) -> None:
    root = mc_dir or minecraft_dir()
    if not root:
        return
    bl = os.path.join(root, "versions", ".BL.json")
    try:
        data: Dict[str, Any] = {"versions": {}}
        if os.path.isfile(bl):
            with open(bl, "r", encoding="utf-8") as f:
                data = json.load(f) or {"versions": {}}
        versions = data.setdefault("versions", {})
        entry = versions.get(version_name) or {}
        entry["jvmArgs"] = jvm_args or ""
        versions[version_name] = entry
        os.makedirs(os.path.dirname(bl), exist_ok=True)
        tmp = bl + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, bl)
    except Exception:
        pass


def load(version_name: str, mc_dir: Optional[str] = None) -> Dict[str, Any]:
    path = settings_path(version_name, mc_dir)
    raw: Dict[str, Any] = {}
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                raw = loaded
        except Exception:
            raw = {}
    out = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS or k in ("schema", "updated_at")}}
    out["hooks"] = {**DEFAULTS["hooks"], **(raw.get("hooks") or {})}
    out["quick_play"] = {**DEFAULTS["quick_play"], **(raw.get("quick_play") or {})}
    out["env_vars"] = dict(raw.get("env_vars") or {})
    # 兼容 .BL.json jvmArgs
    if not out.get("jvm_args"):
        legacy = _read_bl_jvm(version_name, mc_dir)
        if legacy:
            out["jvm_args"] = legacy
    out["schema"] = SCHEMA_VERSION
    return out


def save(version_name: str, patch: Dict[str, Any], mc_dir: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    if not safe_version_dir(version_name, mc_dir):
        return err("invalid version", "invalid_version")
    current = load(version_name, mc_dir)
    for key, value in (patch or {}).items():
        if key in ("hooks", "quick_play", "env_vars") and isinstance(value, dict):
            base = dict(current.get(key) or {})
            base.update(value)
            current[key] = base
        elif key in DEFAULTS or key in current:
            current[key] = value
    current["schema"] = SCHEMA_VERSION
    current["updated_at"] = int(time.time())
    path = settings_path(version_name, mc_dir)
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
        if "jvm_args" in (patch or {}):
            _write_bl_jvm(version_name, str(current.get("jvm_args") or ""), mc_dir)
        return ok(current)
    except Exception as e:
        return err(str(e), "settings_save_failed")


def get(version_name: str, mc_dir: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    if not version_name:
        return err("version required", "invalid_version")
    if not safe_version_dir(version_name, mc_dir):
        return err("invalid version", "invalid_version")
    return ok(load(version_name, mc_dir))


def resolve_launch_overrides(
    version_name: str,
    global_config: Optional[Dict[str, Any]] = None,
    mc_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """合并全局配置与实例 overrides，供 launch.py 使用。"""
    g = dict(global_config or {})
    s = load(version_name, mc_dir)

    min_mem = s.get("java_min_memory")
    max_mem = s.get("java_max_memory")
    if min_mem is None:
        min_mem = g.get("java_min_memory", 512)
    if max_mem is None:
        max_mem = g.get("java_max_memory", 4096)

    java_path = s.get("java_path") or g.get("java_path") or g.get("selected_java") or ""

    extra_jvm: List[str] = []
    jvm_str = str(s.get("jvm_args") or "").strip()
    if jvm_str:
        try:
            extra_jvm = shlex.split(jvm_str, posix=(os.name != "nt"))
        except ValueError:
            extra_jvm = jvm_str.split()

    env = {}
    if isinstance(s.get("env_vars"), dict):
        env = {str(k): str(v) for k, v in s["env_vars"].items() if k}

    hooks = s.get("hooks") or {}
    quick = s.get("quick_play") or {}

    width = s.get("resolution_width")
    height = s.get("resolution_height")
    if width is None:
        width = g.get("game_width")
    if height is None:
        height = g.get("game_height")

    return {
        "java_min_memory": int(min_mem or 512),
        "java_max_memory": int(max_mem or 4096),
        "java_path": java_path,
        "extra_jvm_args": extra_jvm,
        "env_vars": env,
        "resolution": (int(width), int(height)) if width and height else None,
        "fullscreen": s.get("fullscreen"),
        "hooks": {
            "pre_launch": str(hooks.get("pre_launch") or ""),
            "wrapper": str(hooks.get("wrapper") or ""),
            "post_exit": str(hooks.get("post_exit") or ""),
        },
        "quick_play": {
            "type": quick.get("type"),
            "world": quick.get("world"),
            "server": quick.get("server"),
            "port": quick.get("port"),
        },
        "custom_game_args": str(s.get("custom_game_args") or ""),
        "raw": s,
    }


def split_jvm_args(s: str) -> List[str]:
    s = (s or "").strip()
    if not s:
        return []
    try:
        return shlex.split(s, posix=(os.name != "nt"))
    except ValueError:
        return s.split()
