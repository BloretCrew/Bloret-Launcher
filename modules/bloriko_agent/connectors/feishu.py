"""
Bloriko Agent 飞书连接器

通过飞书 Bot API 连接，支持：
- WebSocket 长连接接收消息
- REST API 发送消息

获取凭据：飞书开放平台 → 创建应用 → 启用机器人

依赖：requests, lark-oapi（可选）
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

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
API_TIMEOUT = 15

try:
    import lark_oapi as lark
    LARK_SDK_AVAILABLE = True
except ImportError:
    LARK_SDK_AVAILABLE = False


@register_connector
class FeishuConnector(BaseConnector):
    """飞书 Bot 连接器"""

    platform_id = "feishu"
    platform_name = "飞书"
    platform_icon = "🐦"
    requires_sdk = "lark_oapi"

    config_fields = [
        {"name": "app_id", "label": "App ID", "placeholder": "飞书应用 App ID"},
        {"name": "app_secret", "label": "App Secret", "placeholder": "应用密钥"},
    ]

    def __init__(self, **kwargs):
        self._app_id: str = ""
        self._app_secret: str = ""
        self._tenant_access_token: str = ""
        self._token_expires: float = 0
        self._lark_client: Any = None
        super().__init__(**kwargs)

    # ── 配置管理 ──────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self._app_id and self._app_secret)

    def get_account_info(self) -> Dict[str, str]:
        return {"app_id": self._app_id, "connected": str(self.is_connected)}

    def clear_config(self) -> None:
        self.stop()
        self._delete_json_config()
        self._app_id = ""
        self._app_secret = ""

    def reload_config(self) -> bool:
        with self._dedup_lock:
            self._dedup_set.clear()
        return self._load_saved_config()

    def _load_saved_config(self) -> bool:
        config = self._load_json_config()
        if config:
            self._app_id = config.get("app_id", "")
            self._app_secret = config.get("app_secret", "")
            return bool(self._app_id and self._app_secret)
        return False

    def save_token_config(self, config: Dict[str, str]) -> bool:
        app_id = config.get("app_id", "").strip()
        app_secret = config.get("app_secret", "").strip()
        if not app_id or not app_secret:
            return False
        self._save_json_config({"app_id": app_id, "app_secret": app_secret})
        self._app_id = app_id
        self._app_secret = app_secret
        return True

    # ── Token 管理 ────────────────────────────────────────────

    def _refresh_token(self) -> bool:
        if self._tenant_access_token and time.time() < self._token_expires - 60:
            return True
        try:
            resp = requests.post(
                f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": self._app_id, "app_secret": self._app_secret},
                timeout=API_TIMEOUT,
            )
            data = resp.json()
            self._tenant_access_token = data.get("tenant_access_token", "")
            self._token_expires = time.time() + int(data.get("expire", 7200))
            return bool(self._tenant_access_token)
        except Exception as e:
            log.error("[Feishu] 刷新 Token 失败: %s", e)
            return False

    def _api_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    # ── 生命周期 ──────────────────────────────────────────────

    def _do_start(self) -> bool:
        if not self._refresh_token():
            self._fire_error("飞书 Token 获取失败，请检查 App ID 和 Secret")
            return False

        if LARK_SDK_AVAILABLE:
            try:
                self._lark_client = lark.ws.Client(
                    self._app_id, self._app_secret,
                    event_handler=self._create_event_handler(),
                    log_level=lark.LogLevel.WARNING,
                )
                threading.Thread(
                    target=self._lark_client.start,
                    daemon=True, name="feishu-ws",
                ).start()
                log.info("[Feishu] lark-oapi WebSocket 客户端已启动")
                return True
            except Exception as e:
                log.warning("[Feishu] lark-oapi WebSocket 失败，回退到轮询: %s", e)

        # 回退：长轮询（轮询通过 /im/v1/messages 拉取最新消息）
        log.info("[Feishu] 使用 REST 长轮询模式")
        return True

    def _do_stop(self) -> None:
        self._lark_client = None

    def _create_event_handler(self):
        if not LARK_SDK_AVAILABLE:
            return None

        def handle_message(data):
            try:
                event = json.loads(data) if isinstance(data, str) else data
                message = event.get("event", {}).get("message", {})
                msg_id = message.get("message_id", "")
                if self._is_duplicate(msg_id):
                    return

                chat_id = message.get("chat_id", "")
                sender = event.get("event", {}).get("sender", {}).get("sender_id", {})
                sender_id = sender.get("open_id", "")

                content_raw = message.get("content", "{}")
                try:
                    content = json.loads(content_raw)
                    text = content.get("text", "")
                except (json.JSONDecodeError, TypeError):
                    text = content_raw

                if not text or not chat_id:
                    return

                log.info("[Feishu] 收到消息 from=%s text='%s'", sender_id[:8], text[:50])
                self._fire_message(chat_id, sender_id, text)
            except Exception as e:
                log.error("[Feishu] 处理消息异常: %s", e)

        return handle_message

    def _poll_loop(self) -> None:
        """当使用 lark-oapi SDK 时仅保持线程存活；否则做 REST 轮询"""
        log.info("[Feishu] 轮询线程已启动")
        self._set_status(self.STATUS_CONNECTED)

        if self._lark_client:
            while self._running:
                time.sleep(1)
            return

        # REST 轮询模式
        page_token = ""
        while self._running:
            try:
                if not self._refresh_token():
                    time.sleep(30)
                    continue

                params = {"container_id_type": "chat", "container_id": "", "page_size": 50}
                if page_token:
                    params["page_token"] = page_token

                resp = requests.get(
                    f"{FEISHU_API_BASE}/im/v1/messages",
                    headers=self._api_headers(), params=params, timeout=API_TIMEOUT,
                )
                data = resp.json()
                items = data.get("data", {}).get("items", [])

                for item in items:
                    if not self._running:
                        return
                    self._handle_message_item(item)

                page_token = data.get("data", {}).get("page_token", "")
                has_more = data.get("data", {}).get("has_more", False)
                if not has_more:
                    time.sleep(5)

            except Exception as e:
                log.error("[Feishu] 轮询异常: %s", e)
                time.sleep(10)

    def _handle_message_item(self, item: Dict[str, Any]) -> None:
        msg_id = item.get("message_id", "")
        if self._is_duplicate(msg_id):
            return

        chat_id = item.get("chat_id", "")
        sender = item.get("sender", {}).get("id", "")

        content_raw = item.get("body", {}).get("content", "{}")
        try:
            content = json.loads(content_raw)
            text = content.get("text", "")
        except (json.JSONDecodeError, TypeError):
            text = content_raw

        if not text or not chat_id:
            return

        self._fire_message(chat_id, sender, text)

    # ── 消息发送 ──────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        if not text or not text.strip():
            return False
        if not self._refresh_token():
            return False

        try:
            resp = requests.post(
                f"{FEISHU_API_BASE}/im/v1/messages",
                headers=self._api_headers(),
                params={"receive_id_type": "chat_id"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text[:4096]}),
                },
                timeout=API_TIMEOUT,
            )
            result = resp.json()
            return result.get("code", -1) == 0
        except Exception as e:
            log.error("[Feishu] 发送消息失败: %s", e)
            return False
