"""BBBS API adapter.

The web service has evolved independently from the launcher, so endpoint details
are kept here instead of being spread through QML.  Legacy summary functions
remain compatible with the original launcher integration.
"""

import json
import os
from urllib.parse import urlencode

import requests

import modules.config as cfg
import modules.globals as BLglobals
from modules.log import log


DEFAULT_TIMEOUT = 15
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_COUNT = 9


def _get_base_url():
    return BLglobals.server_ip + ":21111"


def _get_session_cookie():
    """Read both BBBS session cookies without exposing them in logs."""
    config_data = cfg.read()
    cookies = {}
    session = config_data.get("bbbs_session", "")
    session_sig = config_data.get("bbbs_session_sig", "")
    if session:
        cookies["session"] = session
    if session_sig:
        cookies["session.sig"] = session_sig
    return cookies


def is_authenticated():
    return bool(_get_session_cookie().get("session"))


def _error_message(payload, status_code):
    if isinstance(payload, dict):
        for key in ("error", "message", "detail", "msg"):
            value = payload.get(key)
            if value:
                return str(value)
    return f"BBBS request failed ({status_code})"


def _request(method, path, *, params=None, body=None, files=None,
             timeout=DEFAULT_TIMEOUT, authenticated=True):
    """Return a normalized response while preserving the service payload."""
    url = f"{_get_base_url()}{path}"
    cookies = _get_session_cookie() if authenticated else {}
    headers = {"Accept": "application/json"}
    if body is not None and files is None:
        headers["Content-Type"] = "application/json"
    try:
        response = requests.request(
            method.upper(), url, params=params, json=body, files=files,
            cookies=cookies, headers=headers, timeout=timeout,
        )
        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError):
            payload = response.text[:2000]
        if response.ok:
            return {"success": True, "status": response.status_code, "data": payload}
        return {
            "success": False,
            "status": response.status_code,
            "error": _error_message(payload, response.status_code),
            "data": payload,
        }
    except requests.exceptions.RequestException as exc:
        log(f"[BBBS] {method.upper()} {path} network error: {exc}")
        return {"success": False, "status": 0, "error": str(exc), "data": None}


def _data(result, fallback=None):
    if not result or not result.get("success"):
        return fallback
    payload = result.get("data", fallback)
    if isinstance(payload, dict) and payload.get("data") is not None:
        return payload["data"]
    return payload


def _with_query(path, params):
    params = {key: value for key, value in (params or {}).items() if value is not None and value != ""}
    return f"{path}?{urlencode(params)}" if params else path


# Legacy read APIs

def fetch_summary(force_refresh=False):
    return _data(_request("GET", "/api/summary"), None)


def fetch_leaderboard_posts(force_refresh=False):
    return _data(_request("GET", "/api/leaderboard/posts"), [])


def fetch_all_posts(force_refresh=False):
    return _data(_request("GET", "/api/all-posts"), [])


# Read APIs used by the full BBBS workspace

def fetch_boards():
    return _data(_request("GET", "/api/boards"), [])


def fetch_board(board_id):
    return _data(_request("GET", f"/api/boards/{board_id}"), {})


def fetch_sections(board_id=None):
    return _data(_request("GET", _with_query("/api/sections", {"boardId": board_id})), [])


def fetch_posts(section_id=None, board_id=None, page=1, limit=20, search=""):
    result = _request("GET", _with_query("/api/posts", {
        "sectionId": section_id, "boardId": board_id, "page": page,
        "limit": limit, "search": search,
    }))
    return _data(result, {"items": [], "page": page, "hasMore": False})


def fetch_post(post_id):
    return _data(_request("GET", f"/api/posts/{post_id}"), {})


def fetch_comments(post_id, page=1, limit=50):
    return _data(_request("GET", _with_query(f"/api/posts/{post_id}/comments", {
        "page": page, "limit": limit,
    })), [])


def fetch_notifications(page=1, limit=30):
    return _data(_request("GET", _with_query("/api/notifications", {"page": page, "limit": limit})), [])


def fetch_tasks():
    return _data(_request("GET", "/api/tasks"), [])


def fetch_user_settings():
    return _data(_request("GET", "/api/user/settings"), {})


def fetch_statistics():
    return _data(_request("GET", "/api/statistics"), {})


def fetch_permissions():
    return _data(_request("GET", "/api/user/permissions"), {})


def fetch_post_history(post_id):
    return _data(_request("GET", f"/api/posts/{post_id}/history"), [])


def fetch_drafts():
    return _data(_request("GET", "/api/drafts"), [])


# Write APIs.  These deliberately return normalized results so callers can
# display server-side errors and keep the user's input intact.

def create_board(name):
    return _request("POST", "/api/boards", body={"name": name})


def create_section(board_id, name, section_type="text", parent_id=None):
    return _request("POST", "/api/sections", body={
        "boardId": board_id, "name": name, "type": section_type,
        "parentId": parent_id,
    })


def create_post(section_id, title, content, post_type="text", images=None,
                image_caption="", publish_at=None):
    body = {
        "sectionId": section_id, "title": title, "content": content,
        "type": post_type, "imageCaption": image_caption,
        "publishAt": publish_at,
    }
    if images:
        body["images"] = images
    return _request("POST", "/api/posts", body=body)


def update_post(post_id, title, content, images=None):
    body = {"title": title, "content": content}
    if images is not None:
        body["images"] = images
    return _request("PATCH", f"/api/posts/{post_id}", body=body)


def delete_post(post_id):
    return _request("DELETE", f"/api/posts/{post_id}")


def create_comment(post_id, content):
    return _request("POST", f"/api/posts/{post_id}/comments", body={"content": content})


def delete_comment(comment_id):
    return _request("DELETE", f"/api/comments/{comment_id}")


def toggle_like(post_id):
    return _request("POST", f"/api/posts/{post_id}/like")


def report_post(post_id, reason, detail=""):
    return _request("POST", f"/api/posts/{post_id}/reports", body={
        "reason": reason, "detail": detail,
    })


def move_post(post_id, section_id):
    return _request("POST", f"/api/posts/{post_id}/move", body={"sectionId": section_id})


def set_post_pin(post_id, level, duration=None):
    return _request("POST", f"/api/posts/{post_id}/pin", body={
        "level": level, "duration": duration,
    })


def delete_post_pin(post_id):
    return _request("DELETE", f"/api/posts/{post_id}/pin")


def save_draft(draft_id, section_id, title, content):
    body = {"sectionId": section_id, "title": title, "content": content}
    if draft_id:
        return _request("PUT", f"/api/drafts/{draft_id}", body=body)
    return _request("POST", "/api/drafts", body=body)


def delete_draft(draft_id):
    return _request("DELETE", f"/api/drafts/{draft_id}")


def cancel_task(task_id):
    return _request("DELETE", f"/api/tasks/{task_id}")


def save_user_settings(settings):
    return _request("PUT", "/api/user/settings", body=settings)


def upload_images(paths):
    if not paths or len(paths) > MAX_IMAGE_COUNT:
        return {"success": False, "status": 0, "error": "图片数量必须为 1–9 张", "data": None}
    handles = []
    files = []
    try:
        for path in paths:
            size = os.path.getsize(path)
            if size > MAX_IMAGE_SIZE:
                return {"success": False, "status": 0, "error": "单张图片不能超过 10 MB", "data": None}
            handle = open(path, "rb")
            handles.append(handle)
            files.append(("images", (os.path.basename(path), handle, "application/octet-stream")))
        return _request("POST", "/api/uploads/images", files=files)
    except (OSError, TypeError) as exc:
        return {"success": False, "status": 0, "error": str(exc), "data": None}
    finally:
        for handle in handles:
            handle.close()
