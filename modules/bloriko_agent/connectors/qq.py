"""
Bloriko Agent QQ Bot 连接器

通过 QQ 开放平台官方 API v2 连接，支持：
- WebSocket 接收事件和消息
- REST API 发送消息

获取凭据：https://q.qq.com 创建应用

依赖：requests, websocket-client（可选）
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import threading
from typing import Any, Callable, Dict, Optional

import requests

from . import BaseConnector, register_connector

log = logging.getLogger(__name__)

# ── QQ 开放平台 API 常量 ──────────────────────────────────────

QQ_API_BASE = "https://api.sgroup.qq.com"
QQ_API_SANDBOX = "https://sandbox.api.sgroup.qq.com"
QQ_WS_URL = "wss://api.sgroup.qq.com/websocket"

TOKEN_URL = "https://bots.qq.com/app/getAppAccessToken"
API_TIMEOUT = 15

try:
    import websocket as ws_lib
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


@register_connector
class QQBotConnector(BaseConnector):
    """QQ Bot 连接器（官方 API v2）"""

    platform_id = "qq"
    platform_name = "QQ Bot"
    platform_icon = "🐧"
    requires_sdk = "websocket"

    config_fields = [
        {"name": "app_id", "label": "App ID", "placeholder": "QQ 开放平台 App ID"},
        {"name": "client_secret", "label": "Client Secret", "placeholder": "应用密钥"},
        {"name": "sandbox", "label": "沙箱模式", "placeholder": "true / false（默认 false）"},
    ]

    def __init__(self, **kwargs):
        self._app_id: str = ""
        self._client_secret: str = ""
        self._sandbox: bool = False
        self._access_token: str = ""
        self._token_expires: float = 0
        self._ws: Any = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._session_id: str = ""
        self._last_seq: int = 0
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._app_id and self._client_secret)

    def get_account_info(self) -> Dict[str, str]:
        return {
            "app_id": self._app_id,
            "sandbox": str(self._sandbox),
            "connected": str(self.is_connected),
        }

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._app_id = ""
        self._client_secret = ""
        self._sandbox = False

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._app_id = config.get("app_id", "")
            self._client_secret = config.get("client_secret", "")
            self._sandbox = config.get("sandbox", False)
            return bool(self._app_id and self._client_secret)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        app_id = config.get("app_id", "").strip()
        client_secret = config.get("client_secret", "").strip()
        sandbox = config.get("sandbox", "false").lower() == "true"
        if not app_id or not client_secret:
            return False
        self._save_json_config({
            "app_id": app_id,
            "client_secret": client_secret,
            "sandbox": sandbox,
        })
        self._app_id = app_id
        self._client_secret = client_secret
        self._sandbox = sandbox
        return True

    # ── Token 管理 ────────────────────────────────────────────

    def _refresh_token(self) -> bool:
        if self._access_token and time.time() < self._token_expires - 60:
            return True

        try:
            resp = requests.post(TOKEN_URL, json={
                "appId": self._app_id,
                "clientSecret": self._client_secret,
            }, timeout=API_TIMEOUT)
            data = resp.json()
            self._access_token = data.get("access_token", "")
            expires_in = int(data.get("expires_in", 7200))
            self._token_expires = time.time() + expires_in
            log.info("[QQ] Token 已刷新，有效期 %d 秒", expires_in)
            return bool(self._access_token)
        except Exception as e:
            log.error("[QQ] 刷新 Token 失败: %s", e)
            return False

    def _api_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"QQBot {self._access_token}",
            "Content-Type": "application/json",
        }

    def _api_call(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        if not self._refresh_token():
            return {"code": -1, "error": "token refresh failed"}

        base = QQ_API_SANDBOX if self._sandbox else QQ_API_BASE
        url = f"{base}{path}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=self._api_headers(), timeout=API_TIMEOUT)
            else:
                resp = requests.post(url, headers=self._api_headers(), json=data or {}, timeout=API_TIMEOUT)
            return resp.json()
        except Exception as e:
            log.error("[QQ] API %s %s 失败: %s", method, path, e)
            return {"code": -1, "error": str(e)}

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not WS_AVAILABLE:
            self._fire_error("websocket-client 未安装，请运行: pip install websocket-client")
            return False

        if not self._refresh_token():
            self._fire_error("QQ Bot Token 获取失败，请检查 App ID 和 Secret")
            return False

        # 获取 WebSocket 连接地址
        gateway = self._api_call("GET", "/gateway")
        ws_url = gateway.get("url", QQ_WS_URL)
        log.info("[QQ] WebSocket 地址: %s", ws_url)

        try:
            self._ws = ws_lib.WebSocketApp(
                ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )
            ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True, name="qq-ws")
            ws_thread.start()
            return True
        except Exception as e:
            self._fire_error(f"QQ WebSocket 连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _poll_loop(self) -> None:
        """WebSocket 模式：不需要传统轮询，但需要保持线程存活"""
        log.info("[QQ] WebSocket 线程已启动")
        while self._running:
            time.sleep(1)

    # ── WebSocket 回调 ────────────────────────────────────────

    def _on_ws_open(self, ws):
        log.info("[QQ] WebSocket 已连接")
        self._set_status(self.STATUS_CONNECTED)

    def _on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            op = data.get("op")

            if op == 10:  # Hello
                heartbeat_interval = data.get("d", {}).get("heartbeat_interval", 41250)
                self._start_heartbeat(ws, heartbeat_interval)
                self._identify(ws)

            elif op == 11:  # Heartbeat ACK
                pass

            elif op == 0:  # Dispatch
                self._last_seq = data.get("s", 0)
                event_type = data.get("t", "")
                event_data = data.get("d", {})

                if event_type == "MESSAGE_CREATE":
                    self._handle_message(event_data)
                elif event_type == "DIRECT_MESSAGE_CREATE":
                    self._handle_message(event_data, is_direct=True)

            elif op == 7:  # Reconnect
                log.info("[QQ] 收到重连指令")
                ws.close()

            elif op == 9:  # Invalid Session
                log.warning("[QQ] 会话无效")
                ws.close()

        except Exception as e:
            log.error("[QQ] 处理 WebSocket 消息异常: %s", e)

    def _on_ws_error(self, ws, error):
        log.error("[QQ] WebSocket 错误: %s", error)
        self._fire_error(f"QQ WebSocket 错误: {error}")

    def _on_ws_close(self, ws, close_status_code=None, close_msg=None):
        log.info("[QQ] WebSocket 关闭: code=%s msg=%s", close_status_code, close_msg)
        if self._running:
            self._set_status(self.STATUS_ERROR)

    def _identify(self, ws):
        if not self._refresh_token():
            return
        identify = {
            "op": 2,
            "d": {
                "token": f"QQBot {self._access_token}",
                "intents": (1 << 0) | (1 << 9),  # GUILDS + MESSAGE_CREATE
                "properties": {"$os": "linux", "$browser": "bloriko", "$device": "bloriko"},
            },
        }
        ws.send(json.dumps(identify))
        log.info("[QQ] 已发送 Identify")

    def _start_heartbeat(self, ws, interval_ms: int):
        def heartbeat():
            while self._running and self._ws:
                try:
                    ws.send(json.dumps({"op": 1, "d": self._last_seq}))
                except Exception:
                    break
                time.sleep(interval_ms / 1000)

        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True, name="qq-heartbeat")
        self._heartbeat_thread.start()

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_message(self, data: Dict[str, Any], is_direct: bool = False) -> None:
        msg_id = data.get("id", "")
        if self._is_duplicate(msg_id):
            return

        content = data.get("content", "").strip()
        if not content:
            return

        author = data.get("author", {})
        sender_id = author.get("id", "")
        sender_name = author.get("username", "unknown")

        if is_direct:
            chat_id = data.get("guild_id", "") or data.get("channel_id", "")
        else:
            chat_id = data.get("channel_id", "")

        if not chat_id or not sender_id:
            return

        # 忽略 Bot 自身消息
        if author.get("bot", False):
            return

        log.info("[QQ] 收到消息 from=%s text='%s'", sender_name, content[:50])
        self._fire_message(chat_id, sender_id, content)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self.is_connected:
            log.warning("[QQ] 未连接，无法发送")
            return False

        result = self._api_call("POST", f"/channels/{chat_id}/messages", {"content": text[:2000]})
        return "id" in result
