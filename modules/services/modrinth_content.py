"""Modrinth API 扩展：版本详情、依赖、hash 反查、更新检查。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Sequence

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from modules.log import log

API = "https://api.modrinth.com/v2"
USER_AGENT = "Bloret-Launcher/content (support@bloret.net)"


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_project_versions(
    slug_or_id: str,
    *,
    loaders: Optional[Sequence[str]] = None,
    game_versions: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    if not slug_or_id:
        return []
    url = f"{API}/project/{requests.utils.quote(str(slug_or_id), safe='')}/version"
    parts = []
    if loaders:
        loaders_list = [loaders] if isinstance(loaders, str) else list(loaders)
        parts.append(f"loaders={requests.utils.quote(json.dumps(loaders_list))}")
    if game_versions:
        gv = [game_versions] if isinstance(game_versions, str) else list(game_versions)
        parts.append(f"game_versions={requests.utils.quote(json.dumps(gv))}")
    if parts:
        url += "?" + "&".join(parts)
    try:
        resp = _session().get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
        log(f"get_project_versions fail {slug_or_id}: {resp.status_code}", logging.WARNING)
        return []
    except Exception as e:
        log(f"get_project_versions error {slug_or_id}: {e}", logging.ERROR)
        return []


def get_version(version_id: str) -> Optional[Dict[str, Any]]:
    if not version_id:
        return None
    url = f"{API}/version/{requests.utils.quote(str(version_id), safe='')}"
    try:
        resp = _session().get(url, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, dict) else None
        return None
    except Exception as e:
        log(f"get_version error {version_id}: {e}", logging.ERROR)
        return None


def get_versions_by_hashes(
    hashes: Sequence[str],
    algorithm: str = "sha1",
) -> Dict[str, Dict[str, Any]]:
    """POST /version_files — 返回 {hash: version_object}。"""
    cleaned = [h for h in hashes if h and isinstance(h, str)]
    if not cleaned:
        return {}
    # API 单次建议别太大
    out: Dict[str, Dict[str, Any]] = {}
    session = _session()
    for i in range(0, len(cleaned), 64):
        chunk = cleaned[i : i + 64]
        try:
            resp = session.post(
                f"{API}/version_files",
                json={"hashes": chunk, "algorithm": algorithm},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, dict):
                            out[k] = v
            else:
                log(f"version_files HTTP {resp.status_code}", logging.WARNING)
        except Exception as e:
            log(f"version_files error: {e}", logging.ERROR)
    return out


def primary_file(version_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    files = version_obj.get("files") or []
    if not files:
        return None
    primary = next((f for f in files if f.get("primary")), None)
    if primary:
        return primary
    # 优先 jar
    for f in files:
        name = str(f.get("filename") or "")
        if name.endswith(".jar"):
            return f
    return files[0]


def pick_best_version(
    versions: List[Dict[str, Any]],
    *,
    game_version: Optional[str] = None,
    loaders: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    if not versions:
        return None
    loaders_l = {str(x).lower() for x in (loaders or [])}
    ranked: List[Dict[str, Any]] = []
    for v in versions:
        if not isinstance(v, dict):
            continue
        gvs = [str(x) for x in (v.get("game_versions") or [])]
        lds = [str(x).lower() for x in (v.get("loaders") or [])]
        if game_version and gvs and game_version not in gvs:
            continue
        if loaders_l and lds and not (loaders_l & set(lds)):
            continue
        ranked.append(v)
    pool = ranked or list(versions)
    # 已按 API 时间倒序；取第一个 release 优先
    for pref in ("release", "beta", "alpha"):
        for v in pool:
            if str(v.get("version_type") or "").lower() == pref:
                return v
    return pool[0] if pool else None


def resolve_download_info(
    slug_or_id: str,
    *,
    loaders: Optional[Sequence[str]] = None,
    game_versions: Optional[Sequence[str]] = None,
    version_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    解析可下载文件信息。
    返回: {
      project_id, version_id, title, filename, url, sha1, sha512, size,
      dependencies, loaders, game_versions, project_type?
    }
    """
    version_obj = None
    if version_id:
        version_obj = get_version(version_id)
    if not version_obj:
        versions = get_project_versions(slug_or_id, loaders=loaders, game_versions=game_versions)
        gv = None
        if game_versions:
            gv = game_versions[0] if not isinstance(game_versions, str) else game_versions
        version_obj = pick_best_version(versions, game_version=gv, loaders=loaders)
    if not version_obj:
        return None
    f = primary_file(version_obj)
    if not f or not f.get("url"):
        return None
    hashes = f.get("hashes") or {}
    return {
        "project_id": version_obj.get("project_id") or "",
        "version_id": version_obj.get("id") or "",
        "title": version_obj.get("name") or slug_or_id,
        "filename": f.get("filename") or f"{slug_or_id}.jar",
        "url": f.get("url"),
        "sha1": hashes.get("sha1") or "",
        "sha512": hashes.get("sha512") or "",
        "size": int(f.get("size") or 0),
        "dependencies": version_obj.get("dependencies") or [],
        "loaders": version_obj.get("loaders") or [],
        "game_versions": version_obj.get("game_versions") or [],
        "version_number": version_obj.get("version_number") or "",
    }


def collect_required_dependencies(
    version_obj_or_deps: Any,
    *,
    loaders: Optional[Sequence[str]] = None,
    game_versions: Optional[Sequence[str]] = None,
    max_depth: int = 5,
) -> List[Dict[str, Any]]:
    """
    递归收集 dependency_type == required 的依赖下载信息。
    返回 resolve_download_info 风格的 list（已去重 project_id）。
    """
    if isinstance(version_obj_or_deps, dict) and "dependencies" in version_obj_or_deps:
        deps = version_obj_or_deps.get("dependencies") or []
    elif isinstance(version_obj_or_deps, list):
        deps = version_obj_or_deps
    else:
        deps = []

    seen: set = set()
    result: List[Dict[str, Any]] = []

    def walk(dep_list: List[Any], depth: int) -> None:
        if depth > max_depth:
            return
        for dep in dep_list or []:
            if not isinstance(dep, dict):
                continue
            # 只装 required；embedded 已打进主 jar，optional/incompatible 跳过
            if str(dep.get("dependency_type") or "").lower() != "required":
                continue
            pid = dep.get("project_id") or ""
            vid = dep.get("version_id") or ""
            if not pid and not vid:
                continue
            key = pid or vid
            if key in seen:
                continue
            seen.add(key)
            info = resolve_download_info(
                pid or vid,
                loaders=loaders,
                game_versions=game_versions,
                version_id=vid or None,
            )
            if not info:
                continue
            # 再按实际 project_id 去重
            real_pid = info.get("project_id") or key
            if real_pid in {r.get("project_id") for r in result}:
                continue
            result.append(info)
            walk(info.get("dependencies") or [], depth + 1)

    walk(list(deps), 0)
    return result


def latest_for_project(
    project_id: str,
    *,
    loaders: Optional[Sequence[str]] = None,
    game_versions: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    return resolve_download_info(project_id, loaders=loaders, game_versions=game_versions)


def meta_from_version_file(version_obj: Dict[str, Any]) -> Dict[str, Any]:
    """把 version_files 返回的对象压成索引可用的 meta。"""
    return {
        "project_id": version_obj.get("project_id") or "",
        "version_id": version_obj.get("id") or "",
        "title": version_obj.get("name") or "",
        "version_number": version_obj.get("version_number") or "",
        "project_type": "",  # version 对象不含 project_type
    }
