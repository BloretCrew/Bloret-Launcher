"""
Bloriko Agent Matrix 连接器

通过 Matrix Client-Server API 连接，支持：
- 长轮询 /sync 接收消息
- REST API 发送消息

获取凭据：
1. 注册 Matrix 账号（如 matrix.org）
2. 获取 Access Token（Element → Settings → Help & About → Access Token）

依赖：requests（无额外 SDK）
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import requests

from . import BaseConnector, register_connector

log = logging.getLogger(__name__)

API_TIMEOUT = 30
SYNC_TIMEOUT_MS = 30000
MAX_MESSAGE_LENGTH = 65536


@register_connector
class MatrixConnector(BaseConnector):
    """Matrix 连接器（Client-Server API）"""

    platform_id = "matrix"
    platform_name = "Matrix"
    platform_icon = "🟢"
    requires_sdk = None  # 纯 REST API

    config_fields = [
        {"name": "server_url", "label": "服务器 URL", "placeholder": "https://matrix.org"},
        {"name": "access_token", "label": "Access Token", "placeholder": "Matrix Access Token"},
        {"name": "user_id", "label": "用户 ID（可选）", "placeholder": "@user:matrix.org"},
    ]

    def __init__(self, **kwargs):
        self._server_url: str = ""
        self._access_token: str = ""
        self._user_id: str = ""
        self._next_batch: str = ""
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._server_url and self._access_token)

    def get_account_info(self) -> Dict[str, str]:
        return {
            "server_url": self._server_url,
            "user_id": self._user_id,
            "connected": str(self.is_connected),
        }

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._server_url = ""
        self._access_token = ""
        self._user_id = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._server_url = config.get("server_url", "")
            self._access_token = config.get("access_token", "")
            self._user_id = config.get("user_id", "")
            return bool(self._server_url and self._access_token)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        server_url = config.get("server_url", "").strip().rstrip("/")
        access_token = config.get("access_token", "").strip()
        user_id = config.get("user_id", "").strip()
        if not server_url or not access_token:
            return False
        self._save_json_config({
            "server_url": server_url,
            "access_token": access_token,
            "user_id": user_id,
        })
        self._server_url = server_url
        self._access_token = access_token
        self._user_id = user_id
        return True

    # ── API 调用 ──────────────────────────────────────────────

    def _api_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _api_url(self, path: str) -> str:
        return f"{self._server_url.rstrip('/')}/_matrix/client/v3{path}"

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        # 验证 Token
        try:
            resp = requests.get(
                self._api_url("/account/whoami"),
                headers=self._api_headers(),
                timeout=API_TIMEOUT,
            )
            if resp.status_code != 200:
                self._fire_error(f"Matrix Token 无效: HTTP {resp.status_code}")
                return False

            data = resp.json()
            self._user_id = data.get("user_id", self._user_id)
            log.info("[Matrix] 已验证: %s", self._user_id)
            return True
        except Exception as e:
            self._fire_error(f"Matrix 连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        pass

    def _poll_loop(self) -> None:
        """长轮询 /sync"""
        log.info("[Matrix] 轮询线程已启动")
        self._set_status(self.STATUS_CONNECTED)
        consecutive_failures = 0

        while self._running:
            try:
                params = {
                    "timeout": SYNC_TIMEOUT_MS,
                    "filter": '{"room":{"timeline":{"limit":50}}}',
                }
                if self._next_batch:
                    params["since"] = self._next_batch

                resp = requests.get(
                    self._api_url("/sync"),
                    headers=self._api_headers(),
                    params=params,
                    timeout=SYNC_TIMEOUT_MS / 1000 + 10,
                )

                if resp.status_code != 200:
                    consecutive_failures += 1
                    log.warning("[Matrix] /sync 失败 (%d): HTTP %d", consecutive_failures, resp.status_code)
                    if consecutive_failures >= 5:
                        self._set_status(self.STATUS_ERROR)
                        return
                    time.sleep(5)
                    continue

                consecutive_failures = 0
                if self._status != self.STATUS_CONNECTED:
                    self._set_status(self.STATUS_CONNECTED)

                data = resp.json()
                self._next_batch = data.get("next_batch", "")

                # 处理房间消息
                rooms = data.get("rooms", {}).get("join", {})
                for room_id, room_data in rooms.items():
                    if not self._running:
                        return
                    timeline = room_data.get("timeline", {})
                    if not timeline.get("limited") and not self._next_batch:
                        continue
                    for event in timeline.get("events", []):
                        self._handle_room_event(room_id, event)

            except requests.Timeout:
                continue
            except Exception as e:
                consecutive_failures += 1
                log.error("[Matrix] 轮询异常 (%d): %s", consecutive_failures, e)
                if consecutive_failures >= 5:
                    self._set_status(self.STATUS_ERROR)
                    return
                time.sleep(5)

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_room_event(self, room_id: str, event: Dict[str, Any]) -> None:
        if event.get("type") != "m.room.message":
            return

        sender = event.get("sender", "")
        if sender == self._user_id:
            return

        event_id = event.get("event_id", "")
        if self._is_duplicate(event_id):
            return

        content = event.get("content", {})
        msgtype = content.get("msgtype", "")
        if msgtype != "m.text":
            return

        text = content.get("body", "")
        if not text:
            return

        log.info("[Matrix] 收到消息 from=%s room=%s text='%s'", sender[:15], room_id[:15], text[:50])
        self._fire_message(room_id, sender, text)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self.is_connected:
            return False

        import secrets
        txn_id = secrets.token_hex(8)

        try:
            resp = requests.put(
                self._api_url(f"/rooms/{chat_id}/send/m.room.message/{txn_id}"),
                headers=self._api_headers(),
                json={
                    "msgtype": "m.text",
                    "body": text[:MAX_MESSAGE_LENGTH],
                },
                timeout=API_TIMEOUT,
            )
            return resp.status_code == 200
        except Exception as e:
            log.error("[Matrix] 发送消息失败: %s", e)
            return False
