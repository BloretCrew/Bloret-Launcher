"""
Bloriko Agent Slack Bot 连接器

通过 Slack Socket Mode WebSocket 接收消息，REST API 发送消息。

获取凭据：
1. https://api.slack.com/apps 创建应用
2. Socket Mode → 启用 → 创建 App Token (xapp-)
3. Event Subscriptions → 启用 → 订阅 message.channels, message.groups, message.im
4. OAuth → 安装到 Workspace → 获取 Bot Token (xoxb-)

依赖：requests, websocket-client（可选）
"""

from __future__ import annotations

import json
import logging
import time
import threading
from typing import Any, Callable, Dict, Optional

import requests

from . import BaseConnector, register_connector

log = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"
SLACK_WSS_CONNECT = "https://slack.com/api/apps.connections.open"
API_TIMEOUT = 15
MAX_MESSAGE_LENGTH = 40000

try:
    import websocket as ws_lib
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


@register_connector
class SlackConnector(BaseConnector):
    """Slack Bot 连接器（Socket Mode）"""

    platform_id = "slack"
    platform_name = "Slack"
    platform_icon = "📡"
    requires_sdk = "websocket"

    config_fields = [
        {"name": "app_token", "label": "App Token (xapp-)", "placeholder": "xapp-..."},
        {"name": "bot_token", "label": "Bot Token (xoxb-)", "placeholder": "xoxb-..."},
    ]

    def __init__(self, **kwargs):
        self._app_token: str = ""
        self._bot_token: str = ""
        self._ws: Any = None
        self._msg_counter: int = 0
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._app_token and self._bot_token)

    def get_account_info(self) -> Dict[str, str]:
        return {
            "app_token": self._app_token[:10] + "..." if self._app_token else "",
            "bot_token": self._bot_token[:10] + "..." if self._bot_token else "",
            "connected": str(self.is_connected),
        }

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._app_token = ""
        self._bot_token = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._app_token = config.get("app_token", "")
            self._bot_token = config.get("bot_token", "")
            return bool(self._app_token and self._bot_token)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        app_token = config.get("app_token", "").strip()
        bot_token = config.get("bot_token", "").strip()
        if not app_token or not bot_token:
            return False
        self._save_json_config({"app_token": app_token, "bot_token": bot_token})
        self._app_token = app_token
        self._bot_token = bot_token
        return True

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not WS_AVAILABLE:
            self._fire_error("websocket-client 未安装")
            return False

        # 获取 Socket Mode WebSocket URL
        try:
            resp = requests.post(
                SLACK_WSS_CONNECT,
                headers={"Authorization": f"Bearer {self._app_token}"},
                timeout=API_TIMEOUT,
            )
            data = resp.json()
            if not data.get("ok"):
                self._fire_error(f"Slack Socket Mode 连接失败: {data.get('error', '')}")
                return False

            ws_url = data.get("url", "")
            if not ws_url:
                self._fire_error("Slack 未返回 WebSocket URL")
                return False

            self._ws = ws_lib.WebSocketApp(
                ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )
            threading.Thread(target=self._ws.run_forever, daemon=True, name="slack-ws").start()
            return True
        except Exception as e:
            self._fire_error(f"Slack 连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _poll_loop(self) -> None:
        log.info("[Slack] WebSocket 线程已启动")
        self._set_status(self.STATUS_CONNECTED)
        while self._running:
            time.sleep(1)

    # ── WebSocket 回调 ────────────────────────────────────────

    def _on_ws_open(self, ws):
        log.info("[Slack] Socket Mode WebSocket 已连接")
        self._set_status(self.STATUS_CONNECTED)

    def _on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "hello":
                log.info("[Slack] Socket Mode 已握手")
                return

            if msg_type == "disconnect":
                log.info("[Slack] 收到断开指令，重新连接")
                ws.close()
                return

            if msg_type == "events_api":
                envelope_id = data.get("envelope_id", "")
                # ACK
                ws.send(json.dumps({"envelope_id": envelope_id}))

                event = data.get("payload", {}).get("event", {})
                self._handle_event(event)

        except Exception as e:
            log.error("[Slack] 处理消息异常: %s", e)

    def _on_ws_error(self, ws, error):
        log.error("[Slack] WebSocket 错误: %s", error)
        self._fire_error(f"Slack WebSocket 错误: {error}")

    def _on_ws_close(self, ws, *args):
        log.info("[Slack] WebSocket 关闭")
        if self._running:
            self._set_status(self.STATUS_ERROR)

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type", "")
        if event_type != "message":
            return

        # 忽略子类型（如 bot_message, message_changed 等）
        if event.get("subtype"):
            return

        channel_id = event.get("channel", "")
        sender_id = event.get("user", "")
        text = event.get("text", "")
        ts = event.get("ts", "")

        if not text or not channel_id or not sender_id:
            return

        if self._is_duplicate(ts):
            return

        log.info("[Slack] 收到消息 from=%s text='%s'", sender_id[:8], text[:50])
        self._fire_message(channel_id, sender_id, text)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False

        try:
            resp = requests.post(
                f"{SLACK_API}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self._bot_token}",
                    "Content-Type": "application/json",
                },
                json={"channel": chat_id, "text": text[:MAX_MESSAGE_LENGTH]},
                timeout=API_TIMEOUT,
            )
            result = resp.json()
            return result.get("ok", False)
        except Exception as e:
            log.error("[Slack] 发送消息失败: %s", e)
            return False
