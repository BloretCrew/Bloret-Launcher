"""
Bloriko Agent 钉钉连接器

通过钉钉 Stream SDK 连接，支持：
- Stream 长连接接收消息
- Session Webhook 发送消息

获取凭据：钉钉开放平台 → 应用开发 → 企业内部开发

依赖：dingtalk-stream（可选）, requests
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

API_TIMEOUT = 15

try:
    import dingtalk_stream
    DINGTALK_SDK_AVAILABLE = True
except ImportError:
    DINGTALK_SDK_AVAILABLE = False


@register_connector
class DingTalkConnector(BaseConnector):
    """钉钉连接器（Stream SDK）"""

    platform_id = "dingtalk"
    platform_name = "钉钉"
    platform_icon = "📌"
    requires_sdk = "dingtalk_stream"

    config_fields = [
        {"name": "client_id", "label": "Client ID", "placeholder": "钉钉应用 Client ID"},
        {"name": "client_secret", "label": "Client Secret", "placeholder": "应用密钥"},
    ]

    def __init__(self, **kwargs):
        self._client_id: str = ""
        self._client_secret: str = ""
        self._stream_client: Any = None
        self._webhook_urls: Dict[str, str] = {}  # chat_id -> webhook_url
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    def get_account_info(self) -> Dict[str, str]:
        return {"client_id": self._client_id, "connected": str(self.is_connected)}

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._client_id = ""
        self._client_secret = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._client_id = config.get("client_id", "")
            self._client_secret = config.get("client_secret", "")
            return bool(self._client_id and self._client_secret)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        client_id = config.get("client_id", "").strip()
        client_secret = config.get("client_secret", "").strip()
        if not client_id or not client_secret:
            return False
        self._save_json_config({"client_id": client_id, "client_secret": client_secret})
        self._client_id = client_id
        self._client_secret = client_secret
        return True

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not DINGTALK_SDK_AVAILABLE:
            self._fire_error(
                "dingtalk-stream 未安装，请运行: pip install dingtalk-stream"
            )
            return False

        try:
            self._stream_client = dingtalk_stream.DingTalkStreamClient()
            self._stream_client.connect(
                client_id=self._client_id,
                client_secret=self._client_secret,
            )

            # 注册消息回调
            @self._stream_client.register_callback_handler(
                dingtalk_stream.chatbot.ChatbotMessage.TOPIC
            )
            def on_message(data):
                self._handle_dingtalk_message(data)

            threading.Thread(
                target=self._stream_client.start_forever,
                daemon=True,
                name="dingtalk-stream",
            ).start()

            log.info("[DingTalk] Stream 客户端已启动")
            return True
        except Exception as e:
            self._fire_error(f"钉钉连接失败: {e}")
            return False

    def _do_stop(self) -> None:
        self._stream_client = None

    def _poll_loop(self) -> None:
        log.info("[DingTalk] Stream 线程已启动")
        self._set_status(self.STATUS_CONNECTED)
        while self._running:
            time.sleep(1)

    # ── 消息处理 ──────────────────────────────────────────────

    def _handle_dingtalk_message(self, data: Any) -> None:
        try:
            # dingtalk-stream 回调数据格式
            incoming = data if isinstance(data, dict) else json.loads(str(data))
            msg_id = incoming.get("messageId", "")
            if self._is_duplicate(msg_id):
                return

            text = incoming.get("text", {}).get("content", "")
            if not text:
                return

            sender_id = incoming.get("senderStaffId", "") or incoming.get("senderId", "")
            conversation_id = incoming.get("conversationId", "")
            conversation_type = incoming.get("conversationType", "")

            # 保存 webhook URL 用于回复
            session_webhook = incoming.get("sessionWebhook", "")
            if session_webhook and conversation_id:
                self._webhook_urls[conversation_id] = session_webhook

            log.info("[DingTalk] 收到消息 from=%s text='%s'", sender_id[:8], text[:50])
            self._fire_message(conversation_id, sender_id, text.strip())

        except Exception as e:
            log.error("[DingTalk] 处理消息异常: %s", e)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False

        webhook_url = self._webhook_urls.get(chat_id)
        if not webhook_url:
            log.warning("[DingTalk] 无 webhook URL (chat_id=%s)，无法发送", chat_id[:8])
            return False

        try:
            resp = requests.post(
                webhook_url,
                json={
                    "msgtype": "markdown",
                    "markdown": {"title": "络可回复", "text": text[:4096]},
                },
                timeout=API_TIMEOUT,
            )
            result = resp.json()
            return result.get("errcode", -1) == 0
        except Exception as e:
            log.error("[DingTalk] 发送消息失败: %s", e)
            return False
