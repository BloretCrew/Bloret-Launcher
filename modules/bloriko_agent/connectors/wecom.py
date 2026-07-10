"""
Bloriko Agent 企业微信连接器

通过企业微信 AI Bot WebSocket 接口连接，支持：
- WebSocket 接收消息
- 发送消息（markdown/text）

获取凭据：企业微信管理后台 → 应用管理 → 智能机器人

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

# ── 企业微信 API 常量 ──────────────────────────────────────────

WECOM_API_BASE = "https://qyapi.weixin.qq.com"
WECOM_WS_BASE = "wss://openws.work.weixin.qq.com"
API_TIMEOUT = 15

try:
    import websocket as ws_lib
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


@register_connector
class WeComConnector(BaseConnector):
    """企业微信 AI Bot 连接器"""

    platform_id = "wecom"
    platform_name = "企业微信"
    platform_icon = "🏢"
    requires_sdk = "websocket"

    config_fields = [
        {"name": "bot_id", "label": "Bot ID", "placeholder": "企业微信 AI Bot ID"},
        {"name": "secret", "label": "Secret", "placeholder": "应用密钥"},
    ]

    def __init__(self, **kwargs):
        self._bot_id: str = ""
        self._secret: str = ""
        self._access_token: str = ""
        self._token_expires: float = 0
        self._ws: Any = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._bot_id and self._secret)

    def get_account_info(self) -> Dict[str, str]:
        return {"bot_id": self._bot_id, "connected": str(self.is_connected)}

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._bot_id = ""
        self._secret = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._bot_id = config.get("bot_id", "")
            self._secret = config.get("secret", "")
            return bool(self._bot_id and self._secret)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        bot_id = config.get("bot_id", "").strip()
        secret = config.get("secret", "").strip()
        if not bot_id or not secret:
            return False
        self._save_json_config({"bot_id": bot_id, "secret": secret})
        self._bot_id = bot_id
        self._secret = secret
        return True

    # ── Token 管理 ────────────────────────────────────────────

    def _refresh_token(self) -> bool:
        if self._access_token and time.time() < self._token_expires - 60:
            return True
        try:
            resp = requests.get(
                f"{WECOM_API_BASE}/cgi-bin/gettoken",
                params={"corpid": self._bot_id, "corpsecret": self._secret},
                timeout=API_TIMEOUT,
            )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            self._token_expires = time.time() + int(data.get("expires_in", 7200))
            return bool(self._access_token)
        except Exception as e:
            log.error("[WeCom] 刷新 Token 失败: %s", e)
            return False

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not WS_AVAILABLE:
            self._fire_error("websocket-client 未安装")
            return False

        try:
            ws_url = f"{WECOM_WS_BASE}/ws/aibot_subscribe?v=1&bot_id={self._bot_id}&secret={self._secret}"
            self._ws = ws_lib.WebSocketApp(
                ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )
            threading.Thread(target=self._ws.run_forever, daemon=True, name="wecom-ws").start()
            return True
        except Exception as e:
            self._fire_error(f"企业微信连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _poll_loop(self) -> None:
        log.info("[WeCom] WebSocket 线程已启动")
        while self._running:
            time.sleep(1)

    # ── WebSocket 回调 ────────────────────────────────────────

    def _on_ws_open(self, ws):
        log.info("[WeCom] WebSocket 已连接")
        self._set_status(self.STATUS_CONNECTED)

    def _on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("msg_type", "")

            if msg_type == "heartbeat":
                # 回复心跳
                ws.send(json.dumps({"msg_type": "heartbeat", "data": {}}))
                return

            if msg_type == "user_msg":
                self._handle_user_msg(data)

        except Exception as e:
            log.error("[WeCom] 处理消息异常: %s", e)

    def _on_ws_error(self, ws, error):
        log.error("[WeCom] WebSocket 错误: %s", error)
        self._fire_error(f"企业微信 WebSocket 错误: {error}")

    def _on_ws_close(self, ws, *args):
        log.info("[WeCom] WebSocket 关闭")
        if self._running:
            self._set_status(self.STATUS_ERROR)

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_user_msg(self, data: Dict[str, Any]) -> None:
        msg_id = data.get("msg_id", "")
        if self._is_duplicate(msg_id):
            return

        content = data.get("content", {})
        text = content.get("text", "")
        if not text:
            return

        from_user = data.get("from", {})
        sender_id = from_user.get("userid", "") or from_user.get("open_kfid", "")
        chat_id = data.get("session_id", "") or sender_id

        log.info("[WeCom] 收到消息 from=%s text='%s'", sender_id[:8], text[:50])
        self._fire_message(chat_id, sender_id, text)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self._refresh_token():
            return False

        try:
            resp = requests.post(
                f"{WECOM_API_BASE}/cgi-bin/aibot/send",
                params={"access_token": self._access_token},
                json={
                    "session_id": chat_id,
                    "msg_type": "markdown",
                    "content": {"markdown": text[:4096]},
                },
                timeout=API_TIMEOUT,
            )
            result = resp.json()
            return result.get("errcode", -1) == 0
        except Exception as e:
            log.error("[WeCom] 发送消息失败: %s", e)
            return False
