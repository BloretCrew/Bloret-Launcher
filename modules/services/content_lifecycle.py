"""内容安装 / 依赖 / 更新（P0 核心）。"""

from __future__ import annotations

import os
import shutil
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import requests

from modules.services import content_index
from modules.services.base import ServiceResult, err, ok
from modules.services.modrinth_content import (
    collect_required_dependencies,
    get_versions_by_hashes,
    latest_for_project,
    meta_from_version_file,
    resolve_download_info,
)
from modules.services.paths_util import (
    content_dir,
    detect_loader,
    minecraft_dir,
    resolve_game_version,
    safe_version_dir,
)

ProgressCb = Optional[Callable[[float, str], None]]


def _download_url(url: str, dest: str, progress_cb: ProgressCb = None, timeout: int = 120) -> Tuple[bool, str]:
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with requests.get(url, timeout=timeout, stream=True, headers={"User-Agent": "Bloret-Launcher/content"}) as resp:
            if resp.status_code != 200:
                return False, f"HTTP {resp.status_code}"
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(64 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        progress_cb(min(1.0, downloaded / total), f"下载 {os.path.basename(dest)}")
            os.replace(tmp, dest)
        return True, dest
    except Exception as e:
        try:
            if os.path.isfile(dest + ".part"):
                os.remove(dest + ".part")
        except OSError:
            pass
        return False, str(e)


def _folder_for_type(project_type: str) -> str:
    t = (project_type or "mod").lower()
    if t in ("resourcepack", "resourcepacks"):
        return "resourcepacks"
    if t in ("shader", "shaderpack", "shaderpacks"):
        return "shaderpacks"
    if t in ("datapack", "datapacks"):
        return "datapacks"
    return "mods"


def _kind_for_type(project_type: str) -> str:
    t = (project_type or "mod").lower()
    if t.startswith("resource"):
        return "resourcepack"
    if t.startswith("shader"):
        return "shader"
    if t.startswith("data"):
        return "datapack"
    return "mod"


def install_project(
    version_name: str,
    project_id_or_slug: str,
    *,
    with_dependencies: bool = True,
    version_id: Optional[str] = None,
    project_type: str = "mod",
    loaders: Optional[Sequence[str]] = None,
    game_version: Optional[str] = None,
    progress_cb: ProgressCb = None,
    mc_dir: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    """安装 Modrinth 项目（可选依赖）到实例，并写入 content-index。"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return err("invalid version", "invalid_version")
    mc = mc_dir or minecraft_dir()
    gv = game_version or resolve_game_version(version_name, mc)
    loader = detect_loader(version_name, mc)
    if loaders is None:
        if loader == "vanilla":
            loaders = ["fabric", "quilt", "forge", "neoforge"]
        else:
            loaders = [loader]

    if progress_cb:
        progress_cb(0.02, f"解析 {project_id_or_slug}")

    info = resolve_download_info(
        project_id_or_slug,
        loaders=loaders,
        game_versions=[gv] if gv else None,
        version_id=version_id,
    )
    if not info:
        return err(f"未找到可下载版本: {project_id_or_slug}", "not_found")

    plan: List[Dict[str, Any]] = [info]
    if with_dependencies:
        deps = collect_required_dependencies(
            info.get("dependencies") or [],
            loaders=loaders,
            game_versions=[gv] if gv else None,
        )
        # 依赖在前
        plan = deps + [info]

    # project_id 去重，保留最后（主项目优先覆盖同 id 时其实不会）
    dedup: Dict[str, Dict[str, Any]] = {}
    for p in plan:
        pid = p.get("project_id") or p.get("version_id") or p.get("filename")
        dedup[str(pid)] = p
    # 保持依赖优先顺序
    ordered: List[Dict[str, Any]] = []
    seen = set()
    for p in plan:
        pid = str(p.get("project_id") or p.get("version_id") or p.get("filename"))
        if pid in seen:
            continue
        seen.add(pid)
        ordered.append(dedup[pid])

    installed: List[Dict[str, Any]] = []
    failed: List[str] = []
    total = max(1, len(ordered))

    for i, item in enumerate(ordered):
        base = i / total
        span = 1.0 / total
        filename = item.get("filename") or f"{item.get('project_id')}.jar"
        # 主项目用传入 project_type；依赖默认 mod
        ptype = project_type if item is info or item.get("project_id") == info.get("project_id") else "mod"
        folder = _folder_for_type(ptype)
        kind = _kind_for_type(ptype)
        dest_dir = os.path.join(vdir, folder)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        # 若已装同 project_id 的旧文件，先移除
        pid = item.get("project_id") or ""
        if pid:
            existing = content_index.get_by_project(version_name, pid, mc)
            if existing and existing.get("path"):
                old_abs = os.path.join(vdir, existing["path"].replace("/", os.sep))
                if os.path.isfile(old_abs) and os.path.normcase(old_abs) != os.path.normcase(dest):
                    try:
                        os.remove(old_abs)
                    except OSError:
                        pass
                content_index.remove_item(version_name, existing["path"], mc)

        def _cb(frac, status, _b=base, _s=span):
            if progress_cb:
                progress_cb(_b + _s * float(frac) * 0.95, status)

        if progress_cb:
            progress_cb(base, f"下载 {filename} ({i + 1}/{total})")
        ok_dl, msg = _download_url(item["url"], dest, progress_cb=_cb)
        if not ok_dl:
            failed.append(f"{filename}: {msg}")
            continue

        hashes = content_index.file_hashes(dest)
        row = content_index.upsert_item(
            version_name,
            path=dest,
            kind=kind,
            sha1=item.get("sha1") or hashes.get("sha1", ""),
            sha512=item.get("sha512") or hashes.get("sha512", ""),
            project_id=item.get("project_id") or "",
            version_id=item.get("version_id") or "",
            source="modrinth",
            title=item.get("title") or filename,
            file_size=item.get("size") or 0,
            enabled=True,
            extra={"version_number": item.get("version_number") or ""},
            mc_dir=mc,
        )
        installed.append(row)

    if not installed and failed:
        return err("; ".join(failed[:3]), "install_failed")
    return ok(
        {
            "installed": installed,
            "failed": failed,
            "count": len(installed),
            "primary": info.get("project_id"),
        }
    )


def enrich_from_modrinth(version_name: str, mc_dir: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    """扫描 + hash 反查 Modrinth，回填 project_id/version_id。"""
    if not safe_version_dir(version_name, mc_dir):
        return err("invalid version", "invalid_version")
    content_index.scan_filesystem(version_name, mc_dir=mc_dir, compute_hash=True)
    hashes = content_index.hashes_needing_lookup(version_name, mc_dir=mc_dir)
    if not hashes:
        return ok({"looked_up": 0, "updated": 0, "items": content_index.list_indexed(version_name, mc_dir=mc_dir)})
    raw = get_versions_by_hashes(hashes, algorithm="sha1")
    mapping = {h: meta_from_version_file(v) for h, v in raw.items()}
    updated = content_index.apply_modrinth_lookup(version_name, mapping, mc_dir=mc_dir)
    return ok(
        {
            "looked_up": len(hashes),
            "matched": len(mapping),
            "updated": updated,
            "items": content_index.list_indexed(version_name, mc_dir=mc_dir),
        }
    )


def check_updates(
    version_name: str,
    *,
    mc_dir: Optional[str] = None,
    game_version: Optional[str] = None,
    loaders: Optional[Sequence[str]] = None,
) -> ServiceResult[List[Dict[str, Any]]]:
    """检查可更新内容。返回列表，每项含 current / latest。"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return err("invalid version", "invalid_version")
    mc = mc_dir or minecraft_dir()
    # 先尽量补齐元数据
    enrich_from_modrinth(version_name, mc)
    gv = game_version or resolve_game_version(version_name, mc)
    loader = detect_loader(version_name, mc)
    if loaders is None:
        loaders = [loader] if loader != "vanilla" else ["fabric", "forge", "neoforge", "quilt"]

    updates: List[Dict[str, Any]] = []
    for item in content_index.list_indexed(version_name, mc_dir=mc):
        pid = item.get("project_id") or ""
        if not pid:
            continue
        latest = latest_for_project(pid, loaders=loaders, game_versions=[gv] if gv else None)
        if not latest:
            continue
        cur_vid = item.get("version_id") or ""
        new_vid = latest.get("version_id") or ""
        if new_vid and cur_vid and new_vid == cur_vid:
            continue
        # 同 hash 也算最新
        if item.get("sha1") and latest.get("sha1") and item["sha1"] == latest["sha1"]:
            continue
        updates.append(
            {
                "path": item.get("path"),
                "filename": item.get("filename"),
                "title": item.get("title") or item.get("filename"),
                "project_id": pid,
                "current_version_id": cur_vid,
                "latest_version_id": new_vid,
                "latest_version_number": latest.get("version_number") or "",
                "latest_title": latest.get("title") or "",
                "project_type": item.get("project_type") or "mod",
            }
        )
    return ok(updates)


def update_projects(
    version_name: str,
    project_ids: Optional[Sequence[str]] = None,
    *,
    progress_cb: ProgressCb = None,
    mc_dir: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    """更新指定（或全部可更新）项目。"""
    checked = check_updates(version_name, mc_dir=mc_dir)
    if not checked.ok:
        return err(checked.error, checked.code)
    updates = list(checked.data or [])
    if project_ids is not None:
        want = {str(x) for x in project_ids}
        updates = [u for u in updates if u.get("project_id") in want]
    if not updates:
        return ok({"updated": [], "count": 0, "message": "已是最新"})

    done = []
    failed = []
    total = len(updates)
    for i, u in enumerate(updates):
        def _cb(frac, status, _i=i, _t=total):
            if progress_cb:
                progress_cb((_i + frac) / _t, status)

        if progress_cb:
            progress_cb(i / total, f"更新 {u.get('title') or u.get('project_id')}")
        res = install_project(
            version_name,
            u["project_id"],
            with_dependencies=True,
            version_id=u.get("latest_version_id"),
            project_type=u.get("project_type") or "mod",
            progress_cb=_cb,
            mc_dir=mc_dir,
        )
        if res.ok:
            done.append(u["project_id"])
        else:
            failed.append(f"{u.get('project_id')}: {res.error}")
    return ok({"updated": done, "failed": failed, "count": len(done)})


def repair_project(
    version_name: str,
    project_id: str,
    *,
    progress_cb: ProgressCb = None,
    mc_dir: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    """按索引中的 version_id 重下；若无 version_id 则装最新。"""
    item = content_index.get_by_project(version_name, project_id, mc_dir)
    vid = (item or {}).get("version_id") if item else None
    ptype = (item or {}).get("project_type") if item else "mod"
    return install_project(
        version_name,
        project_id,
        with_dependencies=True,
        version_id=vid or None,
        project_type=ptype or "mod",
        progress_cb=progress_cb,
        mc_dir=mc_dir,
    )


def list_content(
    version_name: str,
    kind: Optional[str] = None,
    *,
    refresh: bool = False,
    mc_dir: Optional[str] = None,
) -> ServiceResult[List[Dict[str, Any]]]:
    if not safe_version_dir(version_name, mc_dir):
        return err("invalid version", "invalid_version")
    if refresh:
        content_index.scan_filesystem(version_name, kinds=[kind] if kind else None, mc_dir=mc_dir, compute_hash=False)
    items = content_index.list_indexed(version_name, kind=kind, mc_dir=mc_dir)
    # 附加 abs path
    vdir = safe_version_dir(version_name, mc_dir)
    for it in items:
        rel = it.get("path") or ""
        it["abs_path"] = os.path.join(vdir, rel.replace("/", os.sep)) if vdir and rel else ""
    return ok(items)
