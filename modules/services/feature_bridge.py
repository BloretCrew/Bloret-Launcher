"""Backend 用的 P0–P2 能力桥接（避免把 Bloret-Launcher.py 再堆几千行）。"""

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Dict, List, Optional


def install_mod_with_deps(
    version_name: str,
    project_id: str,
    *,
    project_type: str = "mod",
    with_dependencies: bool = True,
    progress_cb=None,
) -> Dict[str, Any]:
    from modules.services.content_lifecycle import install_project

    res = install_project(
        version_name,
        project_id,
        with_dependencies=with_dependencies,
        project_type=project_type,
        progress_cb=progress_cb,
    )
    return res.to_dict()


def check_content_updates(version_name: str) -> Dict[str, Any]:
    from modules.services.content_lifecycle import check_updates

    return check_updates(version_name).to_dict()


def update_all_content(version_name: str, progress_cb=None) -> Dict[str, Any]:
    from modules.services.content_lifecycle import update_projects

    return update_projects(version_name, progress_cb=progress_cb).to_dict()


def update_selected_content(version_name: str, project_ids: List[str], progress_cb=None) -> Dict[str, Any]:
    from modules.services.content_lifecycle import update_projects

    return update_projects(version_name, project_ids, progress_cb=progress_cb).to_dict()


def scan_and_enrich(version_name: str) -> Dict[str, Any]:
    from modules.services.content_lifecycle import enrich_from_modrinth

    return enrich_from_modrinth(version_name).to_dict()


def list_indexed_content(version_name: str, kind: str = "") -> Dict[str, Any]:
    from modules.services.content_lifecycle import list_content

    return list_content(version_name, kind=kind or None, refresh=True).to_dict()


def get_instance_settings(version_name: str) -> Dict[str, Any]:
    from modules.services.instance_settings import get

    return get(version_name).to_dict()


def save_instance_settings(version_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    from modules.services.instance_settings import save

    return save(version_name, patch or {}).to_dict()


def list_worlds(version_name: str) -> Dict[str, Any]:
    from modules.services.worlds_service import list_worlds as _lw

    return _lw(version_name).to_dict()


def set_quick_play_world(version_name: str, world: str) -> Dict[str, Any]:
    from modules.services.worlds_service import set_quick_play_world as _s

    return _s(version_name, world).to_dict()


def set_quick_play_server(version_name: str, address: str, port: int = 0) -> Dict[str, Any]:
    from modules.services.worlds_service import set_quick_play_server as _s

    return _s(version_name, address, port=port or None).to_dict()


def clear_quick_play(version_name: str) -> Dict[str, Any]:
    from modules.services.worlds_service import clear_quick_play as _c

    return _c(version_name).to_dict()


def list_skins() -> Dict[str, Any]:
    from modules.services.skins_service import list_skins as _ls

    return _ls().to_dict()


def import_skin(path: str, name: str = "", variant: str = "classic") -> Dict[str, Any]:
    from modules.services.skins_service import import_skin_file

    return import_skin_file(path, name=name, variant=variant).to_dict()


def delete_skin(skin_id: str) -> Dict[str, Any]:
    from modules.services.skins_service import delete_skin as _d

    return _d(skin_id).to_dict()


def equip_skin(skin_id: str, variant: str = "") -> Dict[str, Any]:
    from modules.services.skins_service import equip_skin as _e

    return _e(skin_id, variant=variant or None).to_dict()


def list_crashes(version_name: str) -> Dict[str, Any]:
    from modules.services.runtime_extras import list_crash_reports

    return list_crash_reports(version_name).to_dict()


def read_crash_log(path: str) -> Dict[str, Any]:
    from modules.services.runtime_extras import read_log_file

    return read_log_file(path).to_dict()


def list_importable(base_path: str) -> Dict[str, Any]:
    from modules.services.instance_import import list_importable_instances

    return list_importable_instances(base_path).to_dict()


def import_instance(path: str, target_name: str = "") -> Dict[str, Any]:
    from modules.services.instance_import import import_mmc_instance

    return import_mmc_instance(path, target_name=target_name or None).to_dict()


def default_import_paths() -> Dict[str, Any]:
    from modules.services.instance_import import default_multimc_path, default_prism_path

    return {
        "ok": True,
        "prism": default_prism_path() or "",
        "multimc": default_multimc_path() or "",
    }


def mrpack_export_candidates(instance_path: str) -> Dict[str, Any]:
    from modules.mrpack_export import get_export_candidates

    try:
        return {"ok": True, "data": get_export_candidates(instance_path)}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def apply_pending_launch_side_effects(proc, launch_env: Optional[dict] = None):
    """合并实例 env、post-exit hook、Discord RPC。返回最终 env。

    - proc is None：只合并 env，不消费 pending
    - proc 有值：挂 post-exit / Discord，并清空 pending
    """
    import modules.globals as BLglobals

    pending = getattr(BLglobals, "_pending_launch_hooks", None) or {}
    env = dict(launch_env) if launch_env else dict(os.environ)
    for k, v in (pending.get("env_vars") or {}).items():
        if k:
            env[str(k)] = str(v)

    if proc is None:
        return env

    post = str(pending.get("post_exit") or "").strip()
    if post:
        try:
            from modules.services.runtime_extras import spawn_post_exit_hook

            spawn_post_exit_hook(
                post,
                instance_name=str(pending.get("instance_name") or ""),
                instance_dir=str(pending.get("instance_dir") or ""),
                java_path=str(pending.get("java_path") or ""),
                process_obj=proc,
            )
        except Exception:
            pass

    try:
        from modules.services.runtime_extras import discord_set_playing, discord_is_enabled

        if discord_is_enabled():
            discord_set_playing(str(pending.get("instance_name") or "Minecraft"))
    except Exception:
        pass

    try:
        BLglobals._pending_launch_hooks = None
    except Exception:
        pass
    return env


def set_discord_rpc(enabled: bool) -> None:
    from modules.services.runtime_extras import discord_set_enabled

    discord_set_enabled(bool(enabled))
