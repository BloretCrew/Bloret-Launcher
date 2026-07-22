import os
import json
import time
import threading
from datetime import datetime, timedelta

_lock = threading.Lock()
_data_path = None
_stats_path = None

SESSION_PAGE_SIZE = 20


def _ensure_path():
    global _data_path, _stats_path
    if _data_path is None:
        from modules.globals import datapath
        _data_path = os.path.join(datapath, 'play_time.json')
        _stats_path = os.path.join(datapath, 'play_statistics.json')


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


def _read_stats():
    _ensure_path()
    try:
        if os.path.exists(_stats_path):
            with open(_stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"sessions": [], "daily": {}}


def _write_stats(data):
    _ensure_path()
    try:
        os.makedirs(os.path.dirname(_stats_path), exist_ok=True)
        with open(_stats_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── Legacy API (backward compatible) ──

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


# ── New Detailed Statistics API ──

def start_detailed_session(version_name):
    session_id = f"{int(time.time() * 1000)}"
    return {
        "id": session_id,
        "version": version_name,
        "start": time.time(),
        "end": None,
        "foreground": 0,
        "background": 0,
        "unknown": 0,
        "total": 0,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "start_time": datetime.now().strftime("%H:%M:%S"),
        "end_time": "",
        "is_active": True,
    }


def update_session_focus(session, is_foreground):
    if not session or not session.get("is_active"):
        return
    now = time.time()
    last_check = session.get("_last_focus_check", session["start"])
    delta = now - last_check
    session["_last_focus_check"] = now

    if is_foreground is True:
        session["foreground"] += delta
    elif is_foreground is False:
        session["background"] += delta
    else:
        # The desktop compositor did not expose global focus state.
        session["unknown"] = session.get("unknown", 0) + delta


def end_detailed_session(session):
    if not session or not session.get("start"):
        return session or {}

    elapsed = time.time() - session["start"]
    session["end"] = time.time()
    session["total"] = elapsed
    session["is_active"] = False
    session["end_time"] = datetime.now().strftime("%H:%M:%S")

    foreground = session.get("foreground", 0)
    background = session.get("background", 0)
    unknown = session.get("unknown", 0)
    classified = foreground + background + unknown
    if classified < elapsed:
        # Include the short interval between the final focus poll and process
        # exit as unknown instead of fabricating a foreground/background split.
        session["unknown"] = unknown + (elapsed - classified)

    version = session.get("version", "")
    date = session.get("date", datetime.now().strftime("%Y-%m-%d"))

    session_record = {
        "id": session["id"],
        "version": version,
        "date": date,
        "start_time": session["start_time"],
        "end_time": session["end_time"],
        "foreground": round(session["foreground"], 1),
        "background": round(session["background"], 1),
        "unknown": round(session.get("unknown", 0), 1),
        "total": round(elapsed, 1),
    }

    with _lock:
        stats = _read_stats()

        stats["sessions"].append(session_record)

        if date not in stats["daily"]:
            stats["daily"][date] = {"foreground": 0, "background": 0, "unknown": 0, "total": 0, "sessions": 0}
        stats["daily"][date]["foreground"] += session_record["foreground"]
        stats["daily"][date]["background"] += session_record["background"]
        stats["daily"][date]["unknown"] = stats["daily"][date].get("unknown", 0) + session_record["unknown"]
        stats["daily"][date]["total"] += session_record["total"]
        stats["daily"][date]["sessions"] += 1

        _write_stats(stats)

        data = _read()
        data[version] = data.get(version, 0) + elapsed
        _write(data)

    session["total"] = elapsed
    return session


def get_sessions(date_filter=None, version_filter=None, page=1, page_size=SESSION_PAGE_SIZE):
    with _lock:
        stats = _read_stats()
        sessions = stats.get("sessions", [])

    if date_filter:
        sessions = [s for s in sessions if s.get("date") == date_filter]
    if version_filter:
        sessions = [s for s in sessions if s.get("version") == version_filter]

    sessions.sort(key=lambda x: x.get("id", ""), reverse=True)
    total = len(sessions)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    return {
        "sessions": sessions[start_idx:end_idx],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_daily_stats(date_from=None, date_to=None):
    with _lock:
        stats = _read_stats()
        daily = stats.get("daily", {})

    if date_from:
        daily = {k: v for k, v in daily.items() if k >= date_from}
    if date_to:
        daily = {k: v for k, v in daily.items() if k <= date_to}

    sorted_dates = sorted(daily.keys(), reverse=True)
    return [{"date": d, **daily[d]} for d in sorted_dates]


def get_version_stats():
    with _lock:
        data = _read()
        stats = _read_stats()
        sessions = stats.get("sessions", [])

    version_totals = {}
    for s in sessions:
        v = s.get("version", "")
        if v not in version_totals:
            version_totals[v] = {"total": 0, "foreground": 0, "background": 0, "unknown": 0, "sessions": 0}
        version_totals[v]["total"] += s.get("total", 0)
        version_totals[v]["foreground"] += s.get("foreground", 0)
        version_totals[v]["background"] += s.get("background", 0)
        version_totals[v]["unknown"] += s.get("unknown", 0)
        version_totals[v]["sessions"] += 1

    for v, t in data.items():
        if v not in version_totals:
            version_totals[v] = {"total": t, "foreground": 0, "background": 0, "unknown": 0, "sessions": 0}

    result = []
    for v, t in sorted(version_totals.items(), key=lambda x: x[1]["total"], reverse=True):
        result.append({
            "version": v,
            "total": round(t["total"], 1),
            "foreground": round(t["foreground"], 1),
            "background": round(t["background"], 1),
            "unknown": round(t.get("unknown", 0), 1),
            "sessions": t["sessions"],
        })
    return result


def get_overview_stats():
    with _lock:
        stats = _read_stats()
        sessions = stats.get("sessions", [])
        daily = stats.get("daily", {})
        data = _read()

    total_foreground = 0
    total_background = 0
    total_unknown = 0
    total_all = 0
    total_sessions = len(sessions)

    for s in sessions:
        total_foreground += s.get("foreground", 0)
        total_background += s.get("background", 0)
        total_unknown += s.get("unknown", 0)
        total_all += s.get("total", 0)

    today = datetime.now().strftime("%Y-%m-%d")
    today_stats = daily.get(today, {"foreground": 0, "background": 0, "total": 0, "sessions": 0})

    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    week_foreground = 0
    week_background = 0
    week_total = 0
    week_sessions = 0
    for d, v in daily.items():
        if d >= week_start:
            week_foreground += v.get("foreground", 0)
            week_background += v.get("background", 0)
            week_total += v.get("total", 0)
            week_sessions += v.get("sessions", 0)

    month_start = datetime.now().strftime("%Y-%m-01")
    month_foreground = 0
    month_background = 0
    month_total = 0
    month_sessions = 0
    for d, v in daily.items():
        if d >= month_start:
            month_foreground += v.get("foreground", 0)
            month_background += v.get("background", 0)
            month_total += v.get("total", 0)
            month_sessions += v.get("sessions", 0)

    unique_days = len(daily)
    avg_per_day = total_all / unique_days if unique_days > 0 else 0

    play_days = [d for d, v in daily.items() if v.get("total", 0) > 0]
    longest_day = ""
    longest_day_time = 0
    for d in play_days:
        if daily[d]["total"] > longest_day_time:
            longest_day_time = daily[d]["total"]
            longest_day = d

    return {
        "total_foreground": round(total_foreground, 1),
        "total_background": round(total_background, 1),
        "total_unknown": round(total_unknown, 1),
        "total": round(total_all, 1),
        "total_sessions": total_sessions,
        "unique_days": unique_days,
        "avg_per_day": round(avg_per_day, 1),
        "longest_day": longest_day,
        "longest_day_time": round(longest_day_time, 1),
        "today": {
            "foreground": round(today_stats.get("foreground", 0), 1),
            "background": round(today_stats.get("background", 0), 1),
            "total": round(today_stats.get("total", 0), 1),
            "sessions": today_stats.get("sessions", 0),
        },
        "this_week": {
            "foreground": round(week_foreground, 1),
            "background": round(week_background, 1),
            "total": round(week_total, 1),
            "sessions": week_sessions,
        },
        "this_month": {
            "foreground": round(month_foreground, 1),
            "background": round(month_background, 1),
            "total": round(month_total, 1),
            "sessions": month_sessions,
        },
    }


def get_all_dates():
    with _lock:
        stats = _read_stats()
        daily = stats.get("daily", {})
    return sorted(daily.keys(), reverse=True)


def get_all_versions():
    with _lock:
        stats = _read_stats()
        sessions = stats.get("sessions", [])
    versions = list(set(s.get("version", "") for s in sessions if s.get("version")))
    return sorted(versions)


# ── Formatting utilities ──

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


def format_duration_full(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours} 小时 {minutes} 分钟 {secs} 秒"
    if minutes > 0:
        return f"{minutes} 分钟 {secs} 秒"
    return f"{secs} 秒"
