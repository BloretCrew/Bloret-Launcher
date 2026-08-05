"""
Modrinth Modpack Export Module

对齐官方 Modrinth App（theseus）行为：
- 远程可下载内容 → modrinth.index.json 的 files[]（含 downloads）
- 本地文件 → ZIP 内 overrides/{path}
- 不再使用错误的 ZIP files/ 目录
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from modules.i18n import i18nText
from modules.log import log

NEVER_EXPORT_PREFIXES = (
    "modrinth_logs",
    "logs",
    "crash-reports",
    ".fabric",
    ".quilt",
    "natives",
    "versions",
    "libraries",
    "assets",
    "__MACOSX",
    "content-index.json",
    "instance-settings.json",
    "profile.json",
    "saves",
    "screenshots",
    "resourcepacks/.cache",
)

DEFAULT_SELECTED_PREFIXES = (
    "mods",
    "datapacks",
    "resourcepacks",
    "shaderpacks",
    "config",
)

# 仅对这些路径尝试 Modrinth hash 反查（减少 API 调用）
CDN_LOOKUP_PREFIXES = ("mods/", "resourcepacks/", "shaderpacks/", "datapacks/")

_MODRINTH_SESSION: Optional[requests.Session] = None
_HASH_LOOKUP_CACHE: Dict[str, Optional[Dict[str, Any]]] = {}


def _session() -> requests.Session:
    global _MODRINTH_SESSION
    if _MODRINTH_SESSION is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": "Bloret-Launcher/mrpack-export (https://github.com/Bloret-Crew/Bloret-Launcher)",
                "Accept": "application/json",
            }
        )
        retry = Retry(
            total=2,
            backoff_factor=0.4,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _MODRINTH_SESSION = s
    return _MODRINTH_SESSION


def calculate_hash(file_path, algorithm="sha512"):
    """计算文件的哈希值。"""
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        log(f"计算文件哈希失败 {file_path}: {str(e)}", logging.ERROR)
        return None


def calculate_hashes(file_path) -> Optional[Dict[str, str]]:
    """一次读取同时算 sha1 + sha512。"""
    h1 = hashlib.sha1()
    h512 = hashlib.sha512()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h1.update(chunk)
                h512.update(chunk)
        return {"sha1": h1.hexdigest(), "sha512": h512.hexdigest()}
    except Exception as e:
        log(f"计算文件哈希失败 {file_path}: {str(e)}", logging.ERROR)
        return None


def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def detect_game_version(instance_path) -> str:
    """检测游戏版本：优先 version JSON / .BL.json，其次目录名。"""
    instance = Path(instance_path)
    try:
        for name in (
            f"{instance.name}.json",
            "version.json",
        ):
            data = _read_json(instance / name)
            if not data:
                continue
            # 继承链：优先 id，再尝试从 inheritsFrom
            for key in ("id", "inheritsFrom", "jar"):
                val = data.get(key)
                if isinstance(val, str) and re.match(r"^\d+\.\d+", val):
                    return val
            # fabric/forge 版本 id 常含加载器前缀，尝试解析
            vid = data.get("id")
            if isinstance(vid, str):
                m = re.search(r"(\d+\.\d+(?:\.\d+)?)", vid)
                if m:
                    return m.group(1)

        bl = _read_json(instance / ".BL.json")
        if bl:
            for key in ("minecraft", "game_version", "version", "id"):
                val = bl.get(key)
                if isinstance(val, str) and re.match(r"^\d+\.\d+", val):
                    return val

        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", instance.name)
        if match:
            return match.group(1)
    except Exception as e:
        log(f"检测游戏版本失败：{str(e)}", logging.WARNING)

    return "1.20.1"


def detect_loader(instance_path) -> Optional[Dict[str, str]]:
    """检测加载器类型和版本。返回 {"name": "fabric-loader", "version": "..."}。"""
    instance = Path(instance_path)
    try:
        # 1) version JSON libraries / id
        for name in (f"{instance.name}.json", "version.json"):
            data = _read_json(instance / name)
            if not data:
                continue
            vid = str(data.get("id") or "")
            main = str(data.get("mainClass") or "")
            libs = data.get("libraries") or []
            lib_names = " ".join(
                str((lib or {}).get("name") or "") for lib in libs if isinstance(lib, dict)
            ).lower()

            if "net.fabricmc" in lib_names or "fabric" in main.lower() or "fabric" in vid.lower():
                m = re.search(r"fabric[-_]?loader[-_:]([\w.\-]+)", lib_names + " " + vid, re.I)
                ver = m.group(1) if m else "*"
                # 规范化 fabric-loader:version 形式
                m2 = re.search(r"net\.fabricmc:fabric-loader:([\w.\-]+)", lib_names)
                if m2:
                    ver = m2.group(1)
                return {"name": "fabric-loader", "version": ver}

            if "neoforge" in lib_names or "neoforge" in vid.lower():
                m = re.search(r"neoforge[-_:]([\w.\-]+)", lib_names + " " + vid, re.I)
                return {"name": "neoforge", "version": m.group(1) if m else "*"}

            if "minecraftforge" in lib_names or "forge" in vid.lower():
                m = re.search(r"forge[-_:]([\d.\-]+)", lib_names + " " + vid, re.I)
                return {"name": "forge", "version": m.group(1) if m else "*"}

            if "quilt" in lib_names or "quilt" in main.lower():
                m = re.search(r"quilt[-_]?loader[-_:]([\w.\-]+)", lib_names, re.I)
                return {"name": "quilt-loader", "version": m.group(1) if m else "*"}

        # 2) .BL.json
        bl = _read_json(instance / ".BL.json")
        if bl:
            if bl.get("Fabric") or str(bl.get("loader") or "").lower() == "fabric":
                return {
                    "name": "fabric-loader",
                    "version": str(bl.get("loader_version") or bl.get("fabric_loader") or "*"),
                }
            loader = str(bl.get("loader") or "").lower()
            if loader in ("forge", "neoforge", "quilt"):
                name_map = {
                    "forge": "forge",
                    "neoforge": "neoforge",
                    "quilt": "quilt-loader",
                }
                return {
                    "name": name_map[loader],
                    "version": str(bl.get("loader_version") or "*"),
                }

        # 3) 弱回退：扫 mods 目录（不可靠，仅兜底）
        mods_dir = instance / "mods"
        if mods_dir.is_dir():
            for jar in mods_dir.glob("fabric-loader-*.jar"):
                m = re.search(r"fabric-loader-(\d+\.\d+\.\d+)", jar.name)
                return {
                    "name": "fabric-loader",
                    "version": m.group(1) if m else "*",
                }
    except Exception as e:
        log(f"检测加载器失败：{str(e)}", logging.WARNING)

    return None


def _should_skip_rel(rel: str) -> bool:
    rel = rel.replace("\\", "/").lstrip("./")
    lower = rel.lower()
    if lower.endswith(".ds_store"):
        return True
    if "/." in f"/{lower}" and not lower.startswith("mods/"):
        # 隐藏目录（保留 mods 下 .disabled 由调用方决定）
        parts = lower.split("/")
        if any(p.startswith(".") and p not in (".", "..") for p in parts[:-1]):
            if parts[0] in (".fabric", ".quilt"):
                return True
    for p in NEVER_EXPORT_PREFIXES:
        if lower == p or lower.startswith(p + "/"):
            return True
    return False


def get_export_candidates(instance_path) -> List[Dict[str, Any]]:
    """返回可导出候选文件（供 UI 勾选）。"""
    instance = Path(instance_path)
    candidates: List[Dict[str, Any]] = []
    if not instance.exists():
        return candidates

    def add_file(abs_path: Path, rel: str, default_selected: bool):
        rel = rel.replace(os.sep, "/")
        if _should_skip_rel(rel):
            return
        try:
            st = abs_path.stat()
            size = st.st_size
            mtime = int(st.st_mtime)
        except OSError:
            size, mtime = 0, 0
        disabled = abs_path.name.endswith(".disabled")
        candidates.append(
            {
                "path": rel,
                "type": "file",
                "size": size,
                "modified": mtime,
                "disabled": disabled,
                "default_selected": bool(default_selected) and not disabled,
                "source": str(abs_path),
            }
        )

    scan_roots = (
        "mods",
        "config",
        "resourcepacks",
        "shaderpacks",
        "datapacks",
        "options.txt",
    )
    for prefix in scan_roots:
        target = instance / prefix
        default_sel = any(
            prefix == p or prefix.startswith(p) for p in DEFAULT_SELECTED_PREFIXES
        )
        if target.is_file():
            add_file(target, prefix, default_sel)
            continue
        if not target.is_dir():
            continue
        for f in target.rglob("*"):
            if not f.is_file():
                continue
            rel = f"{prefix}/{f.relative_to(target)}".replace(os.sep, "/")
            add_file(f, rel, default_sel)
    return candidates


def collect_files(instance_path, selected_paths=None) -> List[Dict[str, Any]]:
    """收集实例中的文件。

    selected_paths: 可选，相对路径列表；None 表示使用默认前缀全选；
    空列表视为未选择任何（调用方通常会转成 None）。
    """
    files_list: List[Dict[str, Any]] = []
    instance = Path(instance_path)
    selected: Optional[Set[str]] = None
    if selected_paths is not None:
        selected = {str(p).replace("\\", "/") for p in selected_paths}

    def want(rel: str) -> bool:
        rel = rel.replace("\\", "/")
        if _should_skip_rel(rel):
            return False
        if selected is None:
            return any(rel == p or rel.startswith(p + "/") for p in DEFAULT_SELECTED_PREFIXES)
        return rel in selected

    mods_dir = instance / "mods"
    if mods_dir.exists():
        for mod_file in mods_dir.glob("*.jar"):
            rel_path = f"mods/{mod_file.name}"
            if want(rel_path):
                files_list.append(
                    {
                        "path": rel_path,
                        "source": str(mod_file),
                        "env": {"client": "required", "server": "required"},
                    }
                )
        # 也收集 .jar.disabled 若被显式勾选
        for mod_file in mods_dir.glob("*.jar.disabled"):
            rel_path = f"mods/{mod_file.name}"
            if want(rel_path):
                files_list.append(
                    {
                        "path": rel_path,
                        "source": str(mod_file),
                        "env": {"client": "required", "server": "required"},
                    }
                )

    for folder in ("config", "resourcepacks", "shaderpacks", "datapacks"):
        d = instance / folder
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            rel_path = f"{folder}/{f.relative_to(d)}".replace(os.sep, "/")
            if want(rel_path):
                files_list.append({"path": rel_path, "source": str(f)})

    options = instance / "options.txt"
    if options.is_file() and want("options.txt"):
        files_list.append({"path": "options.txt", "source": str(options)})

    return files_list


def lookup_modrinth_file_by_sha1(sha1: str) -> Optional[Dict[str, Any]]:
    """通过 sha1 反查 Modrinth 文件元数据（含下载 URL）。失败返回 None。"""
    if not sha1:
        return None
    if sha1 in _HASH_LOOKUP_CACHE:
        return _HASH_LOOKUP_CACHE[sha1]
    url = f"https://api.modrinth.com/v2/version_file/{sha1}"
    try:
        resp = _session().get(url, params={"algorithm": "sha1"}, timeout=12)
        if resp.status_code == 404:
            _HASH_LOOKUP_CACHE[sha1] = None
            return None
        if resp.status_code != 200:
            log(f"Modrinth version_file 查询失败: HTTP {resp.status_code}", logging.DEBUG)
            _HASH_LOOKUP_CACHE[sha1] = None
            return None
        data = resp.json()
        if not isinstance(data, dict):
            _HASH_LOOKUP_CACHE[sha1] = None
            return None
        # version 对象含 files[]
        files = data.get("files") or []
        primary = None
        for f in files:
            if not isinstance(f, dict):
                continue
            hashes = f.get("hashes") or {}
            if hashes.get("sha1") == sha1 or f.get("primary"):
                primary = f
                if hashes.get("sha1") == sha1:
                    break
        if primary is None and files:
            primary = files[0] if isinstance(files[0], dict) else None
        if not primary:
            _HASH_LOOKUP_CACHE[sha1] = None
            return None
        download_url = primary.get("url")
        if not download_url:
            _HASH_LOOKUP_CACHE[sha1] = None
            return None
        result = {
            "url": download_url,
            "filename": primary.get("filename"),
            "size": primary.get("size"),
            "hashes": primary.get("hashes") or {},
            "project_id": data.get("project_id"),
            "version_id": data.get("id"),
        }
        _HASH_LOOKUP_CACHE[sha1] = result
        return result
    except Exception as e:
        log(f"Modrinth hash 反查异常: {e}", logging.DEBUG)
        _HASH_LOOKUP_CACHE[sha1] = None
        return None


def _should_try_cdn(rel_path: str) -> bool:
    rel = rel_path.replace("\\", "/").lower()
    return any(rel.startswith(p) for p in CDN_LOOKUP_PREFIXES)


def export_to_mrpack(
    instance_path,
    output_path,
    name,
    version,
    summary="",
    selected_paths=None,
    resolve_cdn: bool = True,
):
    """
    导出 Minecraft 实例为官方兼容的 .mrpack 文件。

    - 能反查 CDN 的内容：只写 index.files[]（含 downloads），不嵌入 ZIP
    - 其余：写入 overrides/{path}
    - 始终写入 modrinth.index.json
    """
    try:
        log(i18nText("开始导出 Modrinth 整合包"), logging.INFO)

        instance = Path(instance_path)
        if not instance.exists():
            log(f"实例路径不存在：{instance_path}", logging.ERROR)
            return False

        game_version = detect_game_version(instance_path)
        loader = detect_loader(instance_path)

        log(f"检测到游戏版本：{game_version}", logging.INFO)
        if loader:
            log(f"检测到加载器：{loader['name']} {loader['version']}", logging.INFO)

        dependencies: Dict[str, str] = {"minecraft": game_version}
        if loader:
            dependencies[loader["name"]] = loader["version"]

        files_list = collect_files(instance_path, selected_paths=selected_paths)
        log(f"收集到 {len(files_list)} 个文件", logging.INFO)
        if not files_list:
            log("没有找到可导出的文件", logging.WARNING)

        index = {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": version,
            "name": name,
            "summary": summary or None,
            "files": [],
            "dependencies": dependencies,
        }
        # summary 为可选；空字符串时省略更干净
        if not index["summary"]:
            index.pop("summary", None)

        override_count = 0
        remote_count = 0

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_info in files_list:
                source_path = Path(file_info["source"])
                target_path = str(file_info["path"]).replace("\\", "/")

                if not source_path.is_file():
                    log(f"文件不存在，跳过：{source_path}", logging.WARNING)
                    continue

                hashes = calculate_hashes(source_path)
                if not hashes:
                    log(f"计算哈希失败，跳过：{source_path}", logging.WARNING)
                    continue

                file_size = source_path.stat().st_size
                cdn_meta = None
                if resolve_cdn and _should_try_cdn(target_path):
                    cdn_meta = lookup_modrinth_file_by_sha1(hashes["sha1"])

                if cdn_meta and cdn_meta.get("url"):
                    # 远程文件：只进 index
                    file_entry: Dict[str, Any] = {
                        "path": target_path,
                        "hashes": {
                            "sha1": hashes["sha1"],
                            "sha512": hashes["sha512"],
                        },
                        "downloads": [cdn_meta["url"]],
                        "fileSize": int(cdn_meta.get("size") or file_size),
                    }
                    # 合并 CDN 侧哈希（若有）
                    for algo in ("sha1", "sha512"):
                        if (cdn_meta.get("hashes") or {}).get(algo):
                            file_entry["hashes"][algo] = cdn_meta["hashes"][algo]
                    if "env" in file_info:
                        file_entry["env"] = file_info["env"]
                    else:
                        file_entry["env"] = {
                            "client": "required",
                            "server": "required",
                        }
                    index["files"].append(file_entry)
                    remote_count += 1
                    log(f"远程引用：{target_path}", logging.DEBUG)
                else:
                    # 本地覆盖：进 overrides/，不进 index.files（与官方一致）
                    arcname = f"overrides/{target_path}"
                    zipf.write(source_path, arcname)
                    override_count += 1
                    log(f"覆盖文件：{target_path}", logging.DEBUG)

            zipf.writestr(
                "modrinth.index.json",
                json.dumps(index, indent=2, ensure_ascii=False),
            )

        log(f"整合包导出成功：{output_path}", logging.INFO)
        log(f"  - 名称：{name}", logging.INFO)
        log(f"  - 版本：{version}", logging.INFO)
        log(f"  - 游戏版本：{game_version}", logging.INFO)
        log(f"  - 远程文件：{remote_count}，覆盖文件：{override_count}", logging.INFO)
        return True

    except Exception as e:
        log(f"导出整合包失败：{str(e)}", logging.ERROR)
        import traceback

        log(traceback.format_exc(), logging.ERROR)
        return False


def get_instance_info(instance_path):
    """获取实例信息用于导出对话框。"""
    try:
        loader = detect_loader(instance_path)
        loader_label = "unknown"
        if loader:
            loader_label = f"{loader['name']} {loader.get('version') or ''}".strip()
        info = {
            "name": Path(instance_path).name,
            "game_version": detect_game_version(instance_path),
            "loader": loader_label,
            "file_count": len(collect_files(instance_path)),
        }
        return info
    except Exception as e:
        log(f"获取实例信息失败：{str(e)}", logging.ERROR)
        return None
