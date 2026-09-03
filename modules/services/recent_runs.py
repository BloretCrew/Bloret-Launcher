"""Atomic, thread-safe recent launch history."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from typing import Any, List

_lock = threading.RLock()
_MAX_RUNS = 20


def _path(datapath: str) -> str:
    return os.path.join(datapath, "recent_runs.json")


def read(datapath: str) -> List[Any]:
    with _lock:
        try:
            with open(_path(datapath), "r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []


def replace(datapath: str, items: List[Any]) -> List[Any]:
    with _lock:
        target = _path(datapath)
        items = list(items)[:_MAX_RUNS]
        os.makedirs(os.path.dirname(target), exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=".recent-runs-", suffix=".tmp", dir=os.path.dirname(target))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(items, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
        return items


def record(datapath: str, item: Any) -> List[Any]:
    with _lock:
        items = read(datapath)
        items.insert(0, item)
        items = items[:_MAX_RUNS]
        target = _path(datapath)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=".recent-runs-", suffix=".tmp", dir=os.path.dirname(target))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(items, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
        return items
