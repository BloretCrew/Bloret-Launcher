"""
Bloriko Agent Telegram 连接器

通过 Telegram Bot API 连接，支持：
- 长轮询接收消息
- 发送文字消息（Markdown 格式）

纯 REST API，无额外 SDK 依赖。

获取 Bot Token: 在 Telegram 中找 @BotFather，发送 /newbot
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import requests

from . import BaseConnector, register_connector

log = logging.getLogger(__name__)

# ── Telegram Bot API 常量 ──────────────────────────────────────

TELEGRAM_API = "https://api.telegram.org"

LONG_POLL_TIMEOUT = 30
API_TIMEOUT = 15
MAX_MESSAGE_LENGTH = 4096


@register_connector
class TelegramConnector(BaseConnector):
    """Telegram Bot 连接器"""

    platform_id = "telegram"
    platform_name = "Telegram"
    platform_icon = "✈️"
    requires_sdk = None

    config_fields = [
        {"name": "bot_token", "label": "Bot Token", "placeholder": "从 @BotFather 获取的 Token"},
    ]

    def __init__(self, **kwargs):
        self._bot_token: str = ""
        self._bot_info: Dict[str, Any] = {}
        self._offset: int = 0
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._bot_token)

    def get_account_info(self) -> Dict[str, str]:
        return {
            "bot_id": str(self._bot_info.get("id", "")),
            "username": self._bot_info.get("username", ""),
            "first_name": self._bot_info.get("first_name", ""),
            "connected": str(self.is_connected),
        }

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._bot_token = ""
        self._bot_info = {}

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

    def _api_call(self, method: str, data: Optional[Dict] = None, timeout: int = API_TIMEOUT) -> Dict[str, Any]:
        url = f"{TELEGRAM_API}/bot{self._bot_token}/{method}"
        try:
            resp = requests.post(url, json=data or {}, timeout=timeout)
            result = resp.json()
            if not result.get("ok"):
                log.warning("[Telegram] API %s 失败: %s", method, result.get("description", ""))
            return result
        except requests.RequestException as e:
            log.error("[Telegram] API %s 异常: %s", method, e)
            return {"ok": False, "error": str(e)}

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not self._bot_token:
            return False

        result = self._api_call("getMe")
        if not result.get("ok"):
            self._fire_error(f"Telegram Bot Token 无效: {result.get('error', result.get('description', ''))}")
            return False

        self._bot_info = result.get("result", {})
        log.info("[Telegram] Bot 已验证: @%s", self._bot_info.get("username", "unknown"))
        return True

    def _do_stop(self) -> None:
        pass

    def _poll_loop(self) -> None:
        log.info("[Telegram] 轮询线程已启动")
        self._set_status(self.STATUS_CONNECTED)
        consecutive_failures = 0

        while self._running:
            try:
                result = self._api_call(
                    "getUpdates",
                    data={
                        "offset": self._offset,
                        "timeout": LONG_POLL_TIMEOUT,
                        "allowed_updates": ["message"],
                    },
                    timeout=LONG_POLL_TIMEOUT + 10,
                )

                if not result.get("ok"):
                    consecutive_failures += 1
                    log.warning("[Telegram] getUpdates 失败 (%d): %s",
                                consecutive_failures, result.get("description", ""))
                    if consecutive_failures >= 5:
                        self._set_status(self.STATUS_ERROR)
                        return  # 触发重连
                    for _ in range(5):
                        if not self._running:
                            return
                        time.sleep(1)
                    continue

                consecutive_failures = 0
                if self._status != self.STATUS_CONNECTED:
                    self._set_status(self.STATUS_CONNECTED)

                for update in result.get("result", []):
                    if not self._running:
                        return
                    self._offset = update["update_id"] + 1
                    self._process_update(update)

            except Exception as e:
                consecutive_failures += 1
                log.error("[Telegram] 轮询异常 (%d): %s", consecutive_failures, e)
                if consecutive_failures >= 5:
                    self._set_status(self.STATUS_ERROR)
                    return
                for _ in range(5):
                    if not self._running:
                        return
                    time.sleep(1)

    # ── 消息处理 ──────────────────────────────────────────────

    def _process_update(self, update: Dict[str, Any]) -> None:
        message = update.get("message")
        if not message:
            return

        msg_id = str(message.get("message_id", ""))
        if self._is_duplicate(msg_id):
            return

        text = message.get("text", "")
        if not text:
            return

        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        sender = message.get("from", {})
        sender_id = str(sender.get("id", ""))
        sender_name = sender.get("first_name", "unknown")

        if not chat_id or not sender_id:
            return

        log.info("[Telegram] 收到消息 from=%s text='%s'", sender_name, text[:50])
        self._fire_message(chat_id, sender_id, text)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self.is_connected:
            log.warning("[Telegram] 未连接，无法发送")
            return False

        result = self._api_call("sendMessage", data={
            "chat_id": chat_id,
            "text": text[:MAX_MESSAGE_LENGTH],
        })
        return result.get("ok", False)
