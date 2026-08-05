"""实例内容索引：path / hash / Modrinth project+version 元数据。

存储：versions/<name>/content-index.json
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from modules.services.base import ServiceResult, err, ok
from modules.services.paths_util import content_dir, minecraft_dir, safe_version_dir

_LOCKS: Dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()

INDEX_VERSION = 1
CONTENT_KINDS = ("mod", "resourcepack", "shader", "datapack")

_KIND_TO_DIR = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
}

_DIR_TO_KIND = {v: k for k, v in _KIND_TO_DIR.items()}

_EXT_OK = {
    "mod": (".jar", ".jar.disabled", ".disabled"),
    "resourcepack": (".zip", ".zip.disabled"),
    "shader": (".zip", ".zip.disabled"),
    "datapack": (".zip", ".zip.disabled"),
}


def _lock_for(path: str) -> threading.RLock:
    key = os.path.normcase(os.path.abspath(path))
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[key] = lock
        return lock


def index_path(version_name: str, mc_dir: Optional[str] = None) -> str:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return ""
    return os.path.join(vdir, "content-index.json")


def empty_index() -> Dict[str, Any]:
    return {"version": INDEX_VERSION, "items": {}, "updated_at": int(time.time())}


def _atomic_write(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def load_index(version_name: str, mc_dir: Optional[str] = None) -> Dict[str, Any]:
    path = index_path(version_name, mc_dir)
    if not path:
        return empty_index()
    lock = _lock_for(path)
    with lock:
        if not os.path.isfile(path):
            return empty_index()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return empty_index()
            if "items" not in data or not isinstance(data["items"], dict):
                data["items"] = {}
            data.setdefault("version", INDEX_VERSION)
            return data
        except Exception:
            return empty_index()


def save_index(version_name: str, data: Dict[str, Any], mc_dir: Optional[str] = None) -> bool:
    path = index_path(version_name, mc_dir)
    if not path:
        return False
    lock = _lock_for(path)
    with lock:
        payload = dict(data or {})
        payload["version"] = INDEX_VERSION
        payload["updated_at"] = int(time.time())
        if "items" not in payload or not isinstance(payload["items"], dict):
            payload["items"] = {}
        try:
            _atomic_write(path, payload)
            return True
        except Exception:
            return False


def file_hashes(file_path: str) -> Dict[str, str]:
    """返回 sha1 / sha512；失败返回空 dict。"""
    h1 = hashlib.sha1()
    h512 = hashlib.sha512()
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h1.update(chunk)
                h512.update(chunk)
        return {"sha1": h1.hexdigest(), "sha512": h512.hexdigest()}
    except Exception:
        return {}


def rel_content_path(kind: str, filename: str) -> str:
    folder = _KIND_TO_DIR.get(kind, "mods")
    name = os.path.basename(filename).replace("\\", "/")
    return f"{folder}/{name}"


def _is_enabled_name(name: str) -> bool:
    return not name.endswith(".disabled")


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(item or {})
    out.setdefault("path", "")
    out.setdefault("filename", os.path.basename(out.get("path") or ""))
    out.setdefault("sha1", "")
    out.setdefault("sha512", "")
    out.setdefault("project_id", "")
    out.setdefault("version_id", "")
    out.setdefault("source", "local")
    out.setdefault("project_type", "mod")
    out.setdefault("enabled", True)
    out.setdefault("title", out.get("filename") or "")
    out.setdefault("file_size", 0)
    out.setdefault("updated_at", int(time.time()))
    return out


def upsert_item(
    version_name: str,
    *,
    path: str,
    kind: str = "mod",
    sha1: str = "",
    sha512: str = "",
    project_id: str = "",
    version_id: str = "",
    source: str = "local",
    title: str = "",
    file_size: int = 0,
    enabled: Optional[bool] = None,
    extra: Optional[Dict[str, Any]] = None,
    mc_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """写入/更新一条内容记录。path 可为绝对路径或 mods/xxx.jar 相对路径。"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return {}

    rel = path.replace("\\", "/")
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, vdir).replace("\\", "/")
        except ValueError:
            rel = rel_content_path(kind, os.path.basename(path))
    if ".." in rel.split("/"):
        return {}

    abs_path = os.path.join(vdir, rel.replace("/", os.sep))
    filename = os.path.basename(rel)
    if enabled is None:
        enabled = _is_enabled_name(filename)
    if not sha1 or not sha512:
        if os.path.isfile(abs_path):
            hashes = file_hashes(abs_path)
            sha1 = sha1 or hashes.get("sha1", "")
            sha512 = sha512 or hashes.get("sha512", "")
    if not file_size and os.path.isfile(abs_path):
        try:
            file_size = os.path.getsize(abs_path)
        except OSError:
            file_size = 0

    item = _normalize_item(
        {
            "path": rel,
            "filename": filename,
            "sha1": sha1,
            "sha512": sha512,
            "project_id": project_id or "",
            "version_id": version_id or "",
            "source": source or ("modrinth" if project_id else "local"),
            "project_type": kind if kind in CONTENT_KINDS else "mod",
            "enabled": bool(enabled),
            "title": title or filename,
            "file_size": int(file_size or 0),
            "updated_at": int(time.time()),
        }
    )
    if extra:
        for k, v in extra.items():
            if k not in item and v is not None:
                item[k] = v

    idx = load_index(version_name, mc_dir)
    # 同 path 覆盖；若旧 path 因改名失效，按 project_id 清掉旧条目
    items = idx.setdefault("items", {})
    if project_id:
        stale = [
            k
            for k, v in items.items()
            if isinstance(v, dict)
            and v.get("project_id") == project_id
            and k != rel
            and v.get("project_type", "mod") == item["project_type"]
        ]
        for k in stale:
            items.pop(k, None)
    items[rel] = item
    save_index(version_name, idx, mc_dir)
    return item


def remove_item(version_name: str, rel_or_abs: str, mc_dir: Optional[str] = None) -> bool:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return False
    rel = rel_or_abs.replace("\\", "/")
    if os.path.isabs(rel_or_abs):
        try:
            rel = os.path.relpath(rel_or_abs, vdir).replace("\\", "/")
        except ValueError:
            rel = os.path.basename(rel_or_abs)
    idx = load_index(version_name, mc_dir)
    items = idx.get("items") or {}
    if rel in items:
        items.pop(rel, None)
        save_index(version_name, idx, mc_dir)
        return True
    # 尝试 basename 匹配
    base = os.path.basename(rel)
    hit = [k for k in list(items.keys()) if os.path.basename(k) == base]
    for k in hit:
        items.pop(k, None)
    if hit:
        save_index(version_name, idx, mc_dir)
        return True
    return False


def mark_enabled(version_name: str, rel_or_abs: str, enabled: bool, mc_dir: Optional[str] = None) -> bool:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return False
    rel = rel_or_abs.replace("\\", "/")
    if os.path.isabs(rel_or_abs):
        try:
            rel = os.path.relpath(rel_or_abs, vdir).replace("\\", "/")
        except ValueError:
            rel = os.path.basename(rel_or_abs)
    idx = load_index(version_name, mc_dir)
    item = (idx.get("items") or {}).get(rel)
    if not isinstance(item, dict):
        # 可能发生 .jar <-> .jar.disabled 改名
        base = os.path.basename(rel).replace(".disabled", "")
        for k, v in list((idx.get("items") or {}).items()):
            if not isinstance(v, dict):
                continue
            kb = os.path.basename(k).replace(".disabled", "")
            if kb == base:
                item = v
                # 迁移 key
                folder = os.path.dirname(k).replace("\\", "/") or "mods"
                new_name = base if enabled else (base if base.endswith(".disabled") else base + ".disabled")
                # 更稳：根据 enabled 构造
                raw = base[:-9] if base.endswith(".disabled") else base
                new_name = raw if enabled else raw + ".disabled"
                new_rel = f"{folder}/{new_name}"
                idx["items"].pop(k, None)
                item = dict(v)
                item["path"] = new_rel
                item["filename"] = new_name
                item["enabled"] = bool(enabled)
                idx["items"][new_rel] = item
                save_index(version_name, idx, mc_dir)
                return True
        return False
    item["enabled"] = bool(enabled)
    item["updated_at"] = int(time.time())
    save_index(version_name, idx, mc_dir)
    return True


def list_indexed(
    version_name: str,
    kind: Optional[str] = None,
    mc_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    idx = load_index(version_name, mc_dir)
    out: List[Dict[str, Any]] = []
    for rel, item in (idx.get("items") or {}).items():
        if not isinstance(item, dict):
            continue
        if kind and item.get("project_type") != kind and not rel.startswith(_KIND_TO_DIR.get(kind, "???") + "/"):
            continue
        row = _normalize_item(item)
        row["path"] = rel
        out.append(row)
    out.sort(key=lambda x: (x.get("path") or "").lower())
    return out


def scan_filesystem(
    version_name: str,
    kinds: Optional[Iterable[str]] = None,
    mc_dir: Optional[str] = None,
    compute_hash: bool = True,
) -> Dict[str, Any]:
    """扫描磁盘内容并与索引合并（不删除索引中已有的 modrinth 元数据）。"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return empty_index()

    kinds_list = list(kinds) if kinds else list(CONTENT_KINDS)
    idx = load_index(version_name, mc_dir)
    items = dict(idx.get("items") or {})
    seen_rels = set()

    for kind in kinds_list:
        folder = _KIND_TO_DIR.get(kind)
        if not folder:
            continue
        abs_dir = os.path.join(vdir, folder)
        if not os.path.isdir(abs_dir):
            continue
        try:
            names = os.listdir(abs_dir)
        except OSError:
            continue
        for name in names:
            path = os.path.join(abs_dir, name)
            if kind == "resourcepack" and os.path.isdir(path):
                # 文件夹资源包
                rel = f"{folder}/{name}"
                seen_rels.add(rel)
                prev_raw = items.get(rel)
                prev: Dict[str, Any] = dict(prev_raw) if isinstance(prev_raw, dict) else {}
                items[rel] = _normalize_item(
                    {
                        **prev,
                        "path": rel,
                        "filename": name,
                        "project_type": kind,
                        "enabled": True,
                        "source": prev.get("source") or "local",
                        "title": prev.get("title") or name,
                        "file_size": 0,
                    }
                )
                continue
            if not os.path.isfile(path):
                continue
            lower = name.lower()
            exts = _EXT_OK.get(kind, ())
            if kind == "mod":
                if not (lower.endswith(".jar") or lower.endswith(".jar.disabled") or lower.endswith(".disabled")):
                    continue
            elif exts and not any(lower.endswith(e) for e in exts) and not os.path.isdir(path):
                # 允许无扩展的目录已处理；文件需 zip
                if not lower.endswith(".zip") and not lower.endswith(".zip.disabled"):
                    continue
            rel = f"{folder}/{name}"
            seen_rels.add(rel)
            prev_raw = items.get(rel)
            prev = dict(prev_raw) if isinstance(prev_raw, dict) else {}
            # 尝试从旧 disabled 键迁移
            if not prev:
                if name.endswith(".disabled"):
                    alt = f"{folder}/{name[:-9]}"
                else:
                    alt = f"{folder}/{name}.disabled"
                alt_raw = items.get(alt)
                if isinstance(alt_raw, dict):
                    prev = dict(items.pop(alt))

            need_hash = compute_hash and (not prev.get("sha1") or not prev.get("sha512"))
            hashes = file_hashes(path) if need_hash else {}
            try:
                size = os.path.getsize(path)
            except OSError:
                size = int(prev.get("file_size") or 0)
            items[rel] = _normalize_item(
                {
                    **prev,
                    "path": rel,
                    "filename": name,
                    "sha1": hashes.get("sha1") or prev.get("sha1") or "",
                    "sha512": hashes.get("sha512") or prev.get("sha512") or "",
                    "project_type": kind,
                    "enabled": _is_enabled_name(name),
                    "source": prev.get("source") or ("modrinth" if prev.get("project_id") else "local"),
                    "title": prev.get("title") or name,
                    "file_size": size,
                    "updated_at": int(time.time()) if need_hash else prev.get("updated_at", int(time.time())),
                }
            )

    # 清理索引中指向已删除文件的 local 条目（保留有 project_id 的也可清——文件没了就没了）
    for rel in list(items.keys()):
        folder = rel.split("/", 1)[0] if "/" in rel else ""
        kind = _DIR_TO_KIND.get(folder)
        if kind and kind in kinds_list and rel not in seen_rels:
            abs_p = os.path.join(vdir, rel.replace("/", os.sep))
            if not os.path.exists(abs_p):
                items.pop(rel, None)

    idx["items"] = items
    save_index(version_name, idx, mc_dir)
    return idx


def get_by_project(version_name: str, project_id: str, mc_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not project_id:
        return None
    for item in list_indexed(version_name, mc_dir=mc_dir):
        if item.get("project_id") == project_id:
            return item
    return None


def get_by_path(version_name: str, rel_or_abs: str, mc_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return None
    rel = rel_or_abs.replace("\\", "/")
    if os.path.isabs(rel_or_abs):
        try:
            rel = os.path.relpath(rel_or_abs, vdir).replace("\\", "/")
        except ValueError:
            rel = os.path.basename(rel_or_abs)
    idx = load_index(version_name, mc_dir)
    item = (idx.get("items") or {}).get(rel)
    return _normalize_item(item) if isinstance(item, dict) else None


def hashes_needing_lookup(version_name: str, mc_dir: Optional[str] = None, limit: int = 64) -> List[str]:
    """返回尚无 project_id 但有 sha1 的条目，供 version_files 反查。"""
    out: List[str] = []
    for item in list_indexed(version_name, mc_dir=mc_dir):
        if item.get("project_id"):
            continue
        sha1 = item.get("sha1") or ""
        if len(sha1) == 40:
            out.append(sha1)
        if len(out) >= limit:
            break
    return out


def apply_modrinth_lookup(
    version_name: str,
    sha1_to_meta: Dict[str, Dict[str, Any]],
    mc_dir: Optional[str] = None,
) -> int:
    """把 hash 反查结果写回索引。返回更新条数。"""
    if not sha1_to_meta:
        return 0
    idx = load_index(version_name, mc_dir)
    items = idx.get("items") or {}
    updated = 0
    for rel, item in items.items():
        if not isinstance(item, dict):
            continue
        sha1 = item.get("sha1") or ""
        meta = sha1_to_meta.get(sha1)
        if not meta:
            continue
        item["project_id"] = meta.get("project_id") or item.get("project_id") or ""
        item["version_id"] = meta.get("version_id") or item.get("version_id") or ""
        item["title"] = meta.get("title") or item.get("title") or item.get("filename")
        item["source"] = "modrinth"
        if meta.get("project_type"):
            item["project_type"] = meta["project_type"]
        item["updated_at"] = int(time.time())
        updated += 1
    if updated:
        save_index(version_name, idx, mc_dir)
    return updated


def service_scan(version_name: str, compute_hash: bool = True) -> ServiceResult[Dict[str, Any]]:
    if not version_name:
        return err("version required", "invalid_version")
    if not safe_version_dir(version_name):
        return err("invalid version path", "invalid_version")
    try:
        idx = scan_filesystem(version_name, compute_hash=compute_hash)
        return ok(
            {
                "count": len(idx.get("items") or {}),
                "items": list_indexed(version_name),
                "updated_at": idx.get("updated_at"),
            }
        )
    except Exception as e:
        return err(str(e), "content_scan_failed")
