"""BBBS API adapter.

The web service has evolved independently from the launcher, so endpoint details
are kept here instead of being spread through QML.  Legacy summary functions
remain compatible with the original launcher integration.
"""

import json
import logging
import os
from urllib.parse import urlencode

import requests

import modules.config as cfg
import modules.globals as BLglobals
from modules.log import log


DEFAULT_TIMEOUT = 15
IMAGE_HOST_BASE_URL = "https://img.bloret.net"
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_COUNT = 9
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


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
        log(f"[BBBS] request {method.upper()} {path} params={params or {}} auth={bool(cookies)}")
        response = requests.request(
            method.upper(), url, params=params, json=body, files=files,
            cookies=cookies, headers=headers, timeout=timeout,
        )
        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError):
            payload = response.text[:2000]
        if response.ok:
            size = len(payload) if isinstance(payload, (list, dict, str)) else type(payload).__name__
            log(f"[BBBS] response {method.upper()} {path} status={response.status_code} payload={size}")
            return {"success": True, "status": response.status_code, "data": payload}
        log(f"[BBBS] response {method.upper()} {path} status={response.status_code} error={_error_message(payload, response.status_code)}", logging.WARNING)
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

def _section_nodes(nodes, parent="", board=""):
    """Flatten the documented sectionsTree while retaining chat/image types."""
    result = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name") or "")
        if not name:
            continue
        full_name = name if not parent or "/" in name else f"{parent}/{name}"
        result.append({
            "name": name,
            "fullName": full_name,
            "section": full_name,
            "type": node.get("type", "text"),
            "board": board,
            "children": _section_nodes(node.get("children", []), full_name, board),
        })
    return result


def fetch_boards():
    return _data(_request("GET", "/api/boards/list"), [])


def fetch_board(board_id):
    boards = fetch_boards()
    for board in boards:
        if board.get("name") == board_id or board.get("alias") == board_id:
            return board
    return {}


def fetch_sections(board_id=None):
    boards = fetch_boards()
    if board_id:
        boards = [board for board in boards if board.get("name") == board_id or board.get("alias") == board_id]
    sections = []
    for board in boards:
        sections.extend(_section_nodes(board.get("sectionsTree", []), "", board.get("name", "")))
    return sections


def fetch_posts(section_id=None, board_id=None, page=1, limit=20, search=""):
    # The public API requires board and section names.  The old client used
    # sectionId/boardId, which returns HTTP 400 and was displayed as an empty list.
    if board_id and section_id:
        # Child sections are represented as "parent/child" in the API.
        result = _request("GET", _with_query("/api/posts", {
            "board": board_id, "section": section_id,
            "sort": "time", "order": "desc",
        }))
    else:
        result = _request("GET", _with_query("/api/all-posts", {
            "limit": min(max(int(limit or 20), 1), 200),
            "board": board_id, "section": section_id,
        }))
    payload = _data(result, [])
    if isinstance(payload, list):
        if search:
            needle = search.casefold()
            payload = [post for post in payload if needle in str(post.get("title", "")).casefold() or needle in str(post.get("content", "")).casefold()]
        return payload
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("posts") or []
    return []


def fetch_post(post_id):
    # The documented detail payload is returned by /api/posts with board and
    # section names; resolve the filename from the lightweight global list first.
    posts = fetch_all_posts()
    target = str(post_id)
    match = next((post for post in posts if str(post.get("id", "")) == target or str(post.get("filename", "")) == target), None)
    if not match:
        return {}
    result = _request("GET", _with_query("/api/posts", {
        "board": match.get("board") or match.get("board_name"),
        "section": match.get("section") or match.get("section_name"),
        "sort": "time", "order": "desc",
    }))
    detailed = _data(result, [])
    if isinstance(detailed, list):
        for post in detailed:
            if str(post.get("filename", "")) == str(match.get("filename", "")) or str(post.get("id", "")) == target:
                return post
    return match


def fetch_comments(post_id, page=1, limit=50):
    post = fetch_post(post_id)
    comments = post.get("comments", []) if isinstance(post, dict) else []
    return comments if isinstance(comments, list) else []


def resolve_chat_room(board, section):
    """Resolve a BBBS chat section to its server-managed room."""
    result = _request("GET", _with_query("/api/chat/by-section", {
        "board": board,
        "section": section,
    }))
    payload = _data(result, {})
    if isinstance(payload, dict):
        room = payload.get("room", payload)
        if isinstance(room, dict):
            return room
    return {}


def fetch_chat_messages(board, section, before=None, limit=100):
    room = resolve_chat_room(board, section)
    room_id = room.get("id")
    if not room_id:
        return []
    result = _request("GET", _with_query(f"/api/chat/rooms/{room_id}/messages", {
        "before": before,
        "limit": min(max(int(limit or 100), 1), 100),
    }))
    payload = _data(result, {})
    if isinstance(payload, dict):
        return payload.get("messages") or []
    return payload if isinstance(payload, list) else []


def send_chat_message(board, section, content, reply_to=None):
    room = resolve_chat_room(board, section)
    room_id = room.get("id")
    if not room_id:
        return {"success": False, "status": 404, "error": "无法打开络聊分区"}
    body = {"content": content}
    if reply_to:
        body["reply_to_id"] = reply_to
    return _request("POST", f"/api/chat/rooms/{room_id}/messages", body=body)


def fetch_chat_rooms(query=""):
    result = _request("GET", _with_query("/api/chat/rooms", {"q": query}))
    payload = _data(result, {})
    if isinstance(payload, dict):
        return payload
    return {"rooms": [], "users": []}


def fetch_chat_room(room_id):
    result = _request("GET", f"/api/chat/rooms/{room_id}")
    return _data(result, {})


def fetch_room_messages(room_id, before=None, after=None, limit=100):
    result = _request("GET", _with_query(f"/api/chat/rooms/{room_id}/messages", {
        "before": before,
        "after": after,
        "limit": min(max(int(limit or 100), 1), 100),
    }))
    payload = _data(result, {})
    return payload if isinstance(payload, dict) else {"messages": []}


def send_room_message(room_id, content, reply_to=None):
    body = {"content": content}
    if reply_to:
        body["reply_to_id"] = reply_to
    return _request("POST", f"/api/chat/rooms/{room_id}/messages", body=body)


def create_direct_message(peer):
    return _request("POST", "/api/chat/dm", body={"peer": peer})


def delete_chat_message(message_id):
    return _request("DELETE", f"/api/messages/{message_id}")


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
    return _request("POST", "/api/comment/add", body={
        "filename": post_id,
        "content": content,
    })


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
    """Upload images to img.bloret.net and return BBBS-ready image records.

    The image host accepts one multipart field named ``image`` per request and
    does not require BBBS session cookies.  The returned URLs are absolute so
    they can be inserted directly into Markdown or sent to BBBS.
    """
    if not paths or len(paths) > MAX_IMAGE_COUNT:
        return {"success": False, "status": 0, "error": "图片数量必须为 1–9 张", "data": None}

    uploaded = []
    for path in paths:
        extension = os.path.splitext(path)[1].lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            return {"success": False, "status": 0, "error": "仅支持 JPG、PNG、GIF 和 WebP 图片", "data": None}
        try:
            size = os.path.getsize(path)
            if size > MAX_IMAGE_SIZE:
                return {"success": False, "status": 0, "error": "单张图片不能超过 10 MB", "data": None}
            with open(path, "rb") as handle:
                response = requests.post(
                    f"{IMAGE_HOST_BASE_URL}/api/upload",
                    files={"image": (os.path.basename(path), handle, "application/octet-stream")},
                    headers={"Accept": "application/json"},
                    timeout=DEFAULT_TIMEOUT,
                )
            try:
                payload = response.json()
            except (ValueError, json.JSONDecodeError):
                payload = {"message": response.text[:500]}
            if not response.ok or not payload.get("success"):
                return {
                    "success": False,
                    "status": response.status_code,
                    "error": _error_message(payload, response.status_code),
                    "data": payload,
                }
            data = payload.get("data") or {}
            original_url = data.get("url", "")
            preview_url = data.get("webpUrl", "")
            uploaded.append({
                "url": original_url if original_url.startswith("http") else f"{IMAGE_HOST_BASE_URL}{original_url}",
                "webpUrl": preview_url if preview_url.startswith("http") else f"{IMAGE_HOST_BASE_URL}{preview_url}",
                "timestamp": data.get("timestamp"),
                "md5": data.get("md5"),
                "filename": data.get("filename") or os.path.basename(path),
            })
        except (OSError, requests.exceptions.RequestException) as exc:
            log(f"[BBBS] image upload failed: {exc}")
            return {"success": False, "status": 0, "error": str(exc), "data": None}
    return {"success": True, "status": 200, "data": uploaded}
