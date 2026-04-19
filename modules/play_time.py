import os
import json
import time
import threading

_lock = threading.Lock()
_data_path = None


def _ensure_path():
    global _data_path
    if _data_path is None:
        from modules.globals import datapath
        _data_path = os.path.join(datapath, 'play_time.json')


def _read():
    _ensure_path()
    try:
        if os.path.exists(_data_path):
            with open(_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write(data):
    _ensure_path()
    try:
        os.makedirs(os.path.dirname(_data_path), exist_ok=True)
        with open(_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_total_play_time(version_name):
    with _lock:
        data = _read()
        return data.get(version_name, 0)


def get_all_play_times():
    with _lock:
        return _read()


def start_session(version_name):
    return {"version": version_name, "start": time.time()}


def end_session(session):
    if not session or not session.get("start"):
        return 0
    elapsed = time.time() - session["start"]
    version = session.get("version", "")
    if version and elapsed > 0:
        with _lock:
            data = _read()
            data[version] = data.get(version, 0) + elapsed
            _write(data)
    return elapsed


def format_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_duration_long(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
