"""Thread-safe runtime state shared by the UI, web server, and monitors."""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, Optional

_lock = threading.RLock()
_instances: Dict[str, Dict[str, Any]] = {}
_launch_status: Dict[str, Any] = {
    "session_id": None,
    "progress": 0,
    "status": "",
    "detail": "",
    "finished": False,
}


def instances_snapshot() -> Dict[str, Dict[str, Any]]:
    with _lock:
        return copy.deepcopy(_instances)


def register_instance(instance_id: str, entry: Dict[str, Any]) -> None:
    with _lock:
        _instances[str(instance_id)] = copy.deepcopy(entry)


def get_instance(instance_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        entry = _instances.get(str(instance_id))
        return copy.deepcopy(entry) if entry is not None else None


def update_instance(instance_id: str, **changes: Any) -> bool:
    with _lock:
        if str(instance_id) not in _instances:
            return False
        _instances[str(instance_id)].update(copy.deepcopy(changes))
        return True


def remove_instance(instance_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        entry = _instances.pop(str(instance_id), None)
        return copy.deepcopy(entry) if entry is not None else None


def set_launch_status(**changes: Any) -> Dict[str, Any]:
    with _lock:
        _launch_status.update(copy.deepcopy(changes))
        return copy.deepcopy(_launch_status)


def launch_status_snapshot() -> Dict[str, Any]:
    with _lock:
        return copy.deepcopy(_launch_status)


def clear_dead_instances(pid_exists) -> None:
    with _lock:
        dead = [key for key, entry in _instances.items() if not pid_exists(entry.get("pid"))]
        for key in dead:
            _instances.pop(key, None)
