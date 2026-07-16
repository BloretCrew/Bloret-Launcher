"""启动相关门面（列表/运行中实例；实际启动仍走现有 launch 链路）。"""

from __future__ import annotations

from typing import Any, Dict, List

from modules.services.base import ServiceResult, err, ok


def list_running_instances() -> ServiceResult[List[Dict[str, Any]]]:
    try:
        import modules.globals as BLglobals

        try:
            import psutil
        except ImportError:
            psutil = None  # type: ignore

        instances = getattr(BLglobals, "running_instances", None) or {}
        dead = []
        out: List[Dict[str, Any]] = []
        for k, v in list(instances.items()):
            pid = v.get("pid") if isinstance(v, dict) else None
            if psutil is not None and pid and not psutil.pid_exists(pid):
                dead.append(k)
                continue
            if isinstance(v, dict):
                out.append(
                    {
                        "id": k,
                        "name": v.get("name") or k,
                        "pid": pid,
                        "version": v.get("version") or v.get("name") or "",
                    }
                )
        for k in dead:
            try:
                del instances[k]
            except Exception:
                pass
        return ok(out)
    except Exception as e:
        return err(str(e), "running_list_failed")


def get_launch_items_from_config() -> ServiceResult[List[str]]:
    """从配置读取版本名列表（不依赖 UI Backend）。"""
    try:
        from modules.services.versions_service import list_version_names

        return ok(list_version_names())
    except Exception as e:
        return err(str(e), "launch_items_failed")
