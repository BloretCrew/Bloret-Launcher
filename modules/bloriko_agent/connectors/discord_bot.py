"""
Bloriko Agent Discord Bot 连接器

通过 Discord Gateway WebSocket 接收消息，REST API 发送消息。

获取凭据：
1. https://discord.com/developers/applications 创建应用
2. Bot → 创建 Bot → 复制 Token
3. 开启 MESSAGE CONTENT Intent

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

DISCORD_API = "https://discord.com/api/v10"
DISCORD_GATEWAY = "wss://gateway.discord.gg/?v=10&encoding=json"
API_TIMEOUT = 15
MAX_MESSAGE_LENGTH = 2000

try:
    import websocket as ws_lib
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


@register_connector
class DiscordConnector(BaseConnector):
    """Discord Bot 连接器"""

    platform_id = "discord"
    platform_name = "Discord"
    platform_icon = "🎮"
    requires_sdk = "websocket"

    config_fields = [
        {"name": "bot_token", "label": "Bot Token", "placeholder": "Discord Bot Token"},
    ]

    def __init__(self, **kwargs):
        self._bot_token: str = ""
        self._ws: Any = None
        self._heartbeat_interval: float = 41.25
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._sequence: Optional[int] = None
        self._user_info: Dict[str, Any] = {}
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._bot_token)

    def get_account_info(self) -> Dict[str, str]:
        return {
            "bot_id": str(self._user_info.get("id", "")),
            "username": self._user_info.get("username", ""),
            "connected": str(self.is_connected),
        }

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._bot_token = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._bot_token = config.get("bot_token", "")
            return bool(self._bot_token)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        token = config.get("bot_token", "").strip()
        if not token:
            return False
        self._save_json_config({"bot_token": token})
        self._bot_token = token
        return True

    # ── API 调用 ──────────────────────────────────────────────

    def _api_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bot {self._bot_token}",
            "Content-Type": "application/json",
        }

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not WS_AVAILABLE:
            self._fire_error("websocket-client 未安装")
            return False

        # 验证 Token
        try:
            resp = requests.get(f"{DISCORD_API}/users/@me", headers=self._api_headers(), timeout=API_TIMEOUT)
            if resp.status_code != 200:
                self._fire_error(f"Discord Bot Token 无效: {resp.status_code}")
                return False
            self._user_info = resp.json()
            log.info("[Discord] Bot 已验证: %s#%s",
                     self._user_info.get("username", ""), self._user_info.get("discriminator", ""))
        except Exception as e:
            self._fire_error(f"Discord Token 验证失败: {e}")
            return False

        try:
            self._ws = ws_lib.WebSocketApp(
                DISCORD_GATEWAY,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )
            threading.Thread(target=self._ws.run_forever, daemon=True, name="discord-ws").start()
            return True
        except Exception as e:
            self._fire_error(f"Discord 连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _poll_loop(self) -> None:
        log.info("[Discord] WebSocket 线程已启动")
        while self._running:
            time.sleep(1)

    # ── WebSocket 回调 ────────────────────────────────────────

    def _on_ws_open(self, ws):
        log.info("[Discord] WebSocket 已连接")

    def _on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            op = data.get("op")
            self._sequence = data.get("s", self._sequence)

            if op == 10:  # Hello
                self._heartbeat_interval = data.get("d", {}).get("heartbeat_interval", 41250) / 1000
                self._start_heartbeat(ws)
                self._identify(ws)

            elif op == 11:  # Heartbeat ACK
                pass

            elif op == 0:  # Dispatch
                event_type = data.get("t", "")
                event_data = data.get("d", {})

                if event_type == "READY":
                    self._user_info = event_data.get("user", {})
                    log.info("[Discord] READY: 用户=%s", self._user_info.get("username", ""))
                    self._set_status(self.STATUS_CONNECTED)

                elif event_type == "MESSAGE_CREATE":
                    self._handle_message(event_data)

            elif op == 7:  # Reconnect
                ws.close()

            elif op == 9:  # Invalid Session
                log.warning("[Discord] 无效会话")
                time.sleep(5)
                self._identify(ws)

        except Exception as e:
            log.error("[Discord] 处理消息异常: %s", e)

    def _on_ws_error(self, ws, error):
        log.error("[Discord] WebSocket 错误: %s", error)
        self._fire_error(f"Discord WebSocket 错误: {error}")

    def _on_ws_close(self, ws, *args):
        log.info("[Discord] WebSocket 关闭")
        if self._running:
            self._set_status(self.STATUS_ERROR)

    def _identify(self, ws):
        identify = {
            "op": 2,
            "d": {
                "token": f"Bot {self._bot_token}",
                "intents": (1 << 0) | (1 << 9) | (1 << 15),  # GUILDS + MESSAGE_CREATE + MESSAGE_CONTENT
                "properties": {"os": "linux", "browser": "bloriko", "device": "bloriko"},
            },
        }
        ws.send(json.dumps(identify))

    def _start_heartbeat(self, ws):
        def heartbeat():
            while self._running and self._ws:
                try:
                    ws.send(json.dumps({"op": 1, "d": self._sequence}))
                except Exception:
                    break
                time.sleep(self._heartbeat_interval)

        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True, name="discord-heartbeat")
        self._heartbeat_thread.start()

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_message(self, data: Dict[str, Any]) -> None:
        msg_id = data.get("id", "")
        if self._is_duplicate(msg_id):
            return

        author = data.get("author", {})
        if author.get("bot", False):
            return

        content = data.get("content", "")
        if not content:
            return

        channel_id = data.get("channel_id", "")
        sender_id = author.get("id", "")
        sender_name = author.get("username", "unknown")

        log.info("[Discord] 收到消息 from=%s text='%s'", sender_name, content[:50])
        self._fire_message(channel_id, sender_id, content)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self.is_connected:
            return False

        try:
            resp = requests.post(
                f"{DISCORD_API}/channels/{chat_id}/messages",
                headers=self._api_headers(),
                json={"content": text[:MAX_MESSAGE_LENGTH]},
                timeout=API_TIMEOUT,
            )
            return resp.status_code in (200, 201)
        except Exception as e:
            log.error("[Discord] 发送消息失败: %s", e)
            return False
