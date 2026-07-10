"""
Bloriko Agent 多平台连接器框架

提供统一的 BaseConnector 基类和 CONNECTOR_REGISTRY 注册表。
每个平台连接器继承 BaseConnector 并用 @register_connector 装饰器注册。
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional

log = logging.getLogger(__name__)

# ── 注册表 ─────────────────────────────────────────────────────

CONNECTOR_REGISTRY: Dict[str, type] = {}


def register_connector(cls):
    """注册连接器类到全局注册表"""
    CONNECTOR_REGISTRY[cls.platform_id] = cls
    log.info("已注册连接器: %s (%s)", cls.platform_id, cls.platform_name)
    return cls


# ── BaseConnector 基类 ─────────────────────────────────────────

class BaseConnector(ABC):
    """
    多平台连接器基类

    子类必须定义以下类属性：
        platform_id: str       — 唯一标识 (如 "wechat", "telegram")
        platform_name: str     — 显示名称 (如 "个人微信", "Telegram")
        platform_icon: str     — Emoji 图标
        requires_sdk: str|None — 可选 SDK 包名

    子类必须实现以下方法：
        _do_start()  -> bool
        _do_stop()
        _poll_loop()
        send_message(chat_id, text) -> bool
        is_configured() -> bool
        get_account_info() -> dict
        clear_config()
        reload_config() -> bool
    """

    # 子类必须定义
    platform_id: str = ""
    platform_name: str = ""
    platform_icon: str = "💬"
    requires_sdk: Optional[str] = None

    # 状态常量
    STATUS_DISCONNECTED = "disconnected"
    STATUS_CONNECTING = "connecting"
    STATUS_CONNECTED = "connected"
    STATUS_ERROR = "error"

    # 配置字段描述 (子类可覆盖，用于 UI 提示)
    config_fields: list = []  # [{"name": "token", "label": "Bot Token", "placeholder": "..."}]

    def __init__(
        self,
        on_message: Optional[Callable[[str, str, str], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Args:
            on_message: 收到消息回调 (chat_id, sender_id, text)
            on_status_change: 连接状态变化回调 (status)
            on_error: 错误回调 (error_msg)
        """
        self._on_message = on_message
        self._on_status_change = on_status_change
        self._on_error = on_error

        self._status = self.STATUS_DISCONNECTED
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False

        # 消息去重
        self._dedup_set: set = set()
        self._dedup_lock = threading.Lock()

        # 自动加载已保存配置
        self._load_saved_config()

    # ── 属性 ──────────────────────────────────────────────────

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == self.STATUS_CONNECTED

    @property
    def display_name(self) -> str:
        return f"{self.platform_icon} {self.platform_name}"

    @classmethod
    def sdk_available(cls) -> bool:
        """检查可选 SDK 是否已安装"""
        if not cls.requires_sdk:
            return True
        try:
            __import__(cls.requires_sdk.replace("-", "_").split(">=")[0].split("[")[0])
            return True
        except ImportError:
            return False

    # ── 配置管理（子类实现）────────────────────────────────────

    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        ...

    @abstractmethod
    def get_account_info(self) -> Dict[str, str]:
        """获取当前账号信息"""
        ...

    @abstractmethod
    def clear_config(self) -> None:
        """清除配置并断开"""
        ...

    @abstractmethod
    def reload_config(self) -> bool:
        """从磁盘重新加载配置"""
        ...

    def _load_saved_config(self) -> bool:
        """子类覆盖：从磁盘加载已保存的配置"""
        return False

    @abstractmethod
    def save_token_config(self, config: Dict[str, str]) -> bool:
        """保存 Token 配置（从 UI 配置对话框调用）"""
        ...

    # ── 生命周期 ──────────────────────────────────────────────

    def start(self) -> bool:
        """启动连接器（含自动重连包装）"""
        if self.is_connected:
            log.info("%s 连接器已在运行", self.platform_name)
            return True

        if not self.is_configured():
            log.warning("%s 连接器未配置，无法启动", self.platform_name)
            self._set_status(self.STATUS_ERROR)
            if self._on_error:
                self._on_error(f"{self.platform_name}连接器未配置")
            return False

        self._running = True
        self._set_status(self.STATUS_CONNECTING)

        success = self._do_start()
        if not success:
            self._running = False
            self._set_status(self.STATUS_ERROR)
            return False

        self._poll_thread = threading.Thread(
            target=self._poll_loop_wrapper, daemon=True, name=f"{self.platform_id}-poll"
        )
        self._poll_thread.start()
        log.info("%s 连接器已启动", self.platform_name)
        return True

    def stop(self) -> None:
        """停止连接器"""
        self._running = False
        self._do_stop()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=5)
            self._poll_thread = None
        self._set_status(self.STATUS_DISCONNECTED)
        log.info("%s 连接器已停止", self.platform_name)

    # ── 子类实现 ──────────────────────────────────────────────

    @abstractmethod
    def _do_start(self) -> bool:
        """平台特定启动逻辑，返回 True 表示成功"""
        ...

    def _do_stop(self) -> None:
        """平台特定停止逻辑（子类可覆盖）"""
        pass

    @abstractmethod
    def _poll_loop(self) -> None:
        """接收消息的主循环（在后台线程中运行）"""
        ...

    @abstractmethod
    def send_message(self, chat_id: str, text: str) -> bool:
        """发送消息到平台"""
        ...

    # ── 统一接口 ──────────────────────────────────────────────

    def send_message_chunks(self, chat_id: str, text: str, max_len: int = 2000) -> int:
        """分块发送长文本，返回成功发送的块数"""
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].strip()

        sent = 0
        for chunk in chunks:
            if self.send_message(chat_id, chunk):
                sent += 1
                time.sleep(1.5)
        return sent

    # ── 内部方法 ──────────────────────────────────────────────

    def _set_status(self, status: str) -> None:
        """更新连接状态并通知"""
        if self._status == status:
            return
        self._status = status
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception as e:
                log.warning("状态回调异常: %s", e)

    def _fire_message(self, chat_id: str, sender_id: str, text: str) -> None:
        """触发消息回调"""
        if self._on_message:
            try:
                self._on_message(chat_id, sender_id, text)
            except Exception as e:
                log.error("消息回调异常: %s", e)

    def _fire_error(self, error: str) -> None:
        """触发错误回调"""
        log.error("[%s] %s", self.platform_id, error)
        if self._on_error:
            try:
                self._on_error(error)
            except Exception as e:
                log.warning("错误回调异常: %s", e)

    def _is_duplicate(self, message_id: str) -> bool:
        """消息去重"""
        if not message_id:
            return False
        with self._dedup_lock:
            if message_id in self._dedup_set:
                return True
            self._dedup_set.add(message_id)
            if len(self._dedup_set) > 1000:
                self._dedup_set.clear()
        return False

    def _poll_loop_wrapper(self) -> None:
        """包装 _poll_loop 的自动重连逻辑"""
        MAX_RECONNECT_ATTEMPTS = 5
        RECONNECT_DELAYS = [10, 30, 60, 120, 300]

        for attempt in range(MAX_RECONNECT_ATTEMPTS + 1):
            if not self._running:
                break

            if attempt > 0:
                delay = RECONNECT_DELAYS[min(attempt - 1, len(RECONNECT_DELAYS) - 1)]
                log.info("[%s] 第 %d 次重连，等待 %d 秒...", self.platform_id, attempt, delay)
                self._set_status(self.STATUS_CONNECTING)
                for _ in range(int(delay)):
                    if not self._running:
                        return
                    time.sleep(1)

                self._load_saved_config()
                if not self.is_configured():
                    log.warning("[%s] 无凭据，无法重连", self.platform_id)
                    break

                if not self._do_start():
                    continue

            try:
                self._poll_loop()
            except Exception as e:
                log.error("[%s] 轮询异常: %s", self.platform_id, e)
                if not self._running:
                    break
                continue

            if not self._running:
                break

        self._set_status(self.STATUS_DISCONNECTED)
        log.info("[%s] 轮询线程已退出", self.platform_id)

    # ── 配置目录 ──────────────────────────────────────────────

    def _get_config_dir(self) -> Path:
        """获取该连接器的配置目录"""
        try:
            from modules.globals import datapath
            base = Path(datapath)
        except ImportError:
            base = Path(os.path.expanduser("~")) / ".bloret-launcher"
        config_dir = base / "bloriko-agent" / self.platform_id
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _config_path(self) -> Path:
        return self._get_config_dir() / "config.json"

    def _save_json_config(self, data: Dict[str, Any]) -> None:
        """保存 JSON 配置文件"""
        path = self._config_path()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        log.info("[%s] 配置已保存", self.platform_id)

    def _load_json_config(self) -> Optional[Dict[str, Any]]:
        """加载 JSON 配置文件"""
        path = self._config_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning("[%s] 读取配置失败: %s", self.platform_id, e)
            return None

    def _delete_json_config(self) -> None:
        """删除配置文件"""
        path = self._config_path()
        if path.exists():
            path.unlink()
        log.info("[%s] 配置已清除", self.platform_id)

    # ── 工具方法 ──────────────────────────────────────────────

    @staticmethod
    def check_requirements() -> Dict[str, bool]:
        """检查依赖是否满足（子类可覆盖）"""
        return {"requests": True}

    def to_dict(self) -> Dict[str, Any]:
        """导出连接器信息为字典（用于 UI 动态渲染）"""
        return {
            "platform_id": self.platform_id,
            "platform_name": self.platform_name,
            "platform_icon": self.platform_icon,
            "status": self.status,
            "configured": self.is_configured(),
            "connected": self.is_connected,
            "config_fields": self.config_fields,
            "requires_sdk": self.requires_sdk,
            "sdk_available": self.sdk_available(),
        }

    @classmethod
    def to_registry_dict(cls) -> Dict[str, Any]:
        """导出注册表项（不含实例状态）"""
        return {
            "platform_id": cls.platform_id,
            "platform_name": cls.platform_name,
            "platform_icon": cls.platform_icon,
            "requires_sdk": cls.requires_sdk,
            "sdk_available": cls.sdk_available(),
            "config_fields": cls.config_fields,
        }


# ── 便捷函数 ──────────────────────────────────────────────────

def get_all_connectors_info() -> list:
    """获取所有注册连接器的静态信息"""
    return [cls.to_registry_dict() for cls in CONNECTOR_REGISTRY.values()]


def get_all_connectors_info_json() -> str:
    """获取所有注册连接器信息的 JSON 字符串"""
    return json.dumps(get_all_connectors_info(), ensure_ascii=False)


# ── 导入所有连接器（触发注册）─────────────────────────────────

def _import_all_connectors():
    """延迟导入所有连接器模块，触发 @register_connector"""
    from . import wechat  # noqa: F401
    from . import telegram_bot  # noqa: F401
    from . import qq  # noqa: F401
    from . import wecom  # noqa: F401
    from . import dingtalk  # noqa: F401
    from . import feishu  # noqa: F401
    from . import discord_bot  # noqa: F401
    from . import slack_bot  # noqa: F401
    from . import matrix_bot  # noqa: F401


# 延迟导入，避免循环导入
_import_all_connectors()
