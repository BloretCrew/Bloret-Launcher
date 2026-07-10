"""
Bloriko Agent 微信连接器

通过腾讯 iLink Bot API 连接个人微信账号，支持：
- QR 扫码登录
- 长轮询接收文字/图片/文件消息
- 发送文字消息

依赖（可选）：
- cryptography：媒体文件 AES 加解密
- qrcode：终端二维码渲染

参考：Hermes Agent gateway/platforms/weixin.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import secrets
import struct
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

# ── iLink API 常量 ──────────────────────────────────────────────

ILINK_BASE_URL = "https://ilinkai.weixin.qq.com"
ILINK_APP_ID = "bot"
CHANNEL_VERSION = "2.2.0"
ILINK_APP_CLIENT_VERSION = (2 << 16) | (2 << 8) | 0

EP_GET_BOT_QR = "ilink/bot/get_bot_qrcode"
EP_GET_QR_STATUS = "ilink/bot/get_qrcode_status"
EP_GET_UPDATES = "ilink/bot/getupdates"
EP_SEND_MESSAGE = "ilink/bot/sendmessage"
EP_GET_CONFIG = "ilink/bot/getconfig"
EP_GET_UPLOAD_URL = "ilink/bot/getuploadurl"

LONG_POLL_TIMEOUT = 35
API_TIMEOUT = 15
QR_TIMEOUT = 35

MAX_RETRIES = 3
RETRY_DELAY = 2
BACKOFF_DELAY = 30

# ── 消息类型常量 ─────────────────────────────────────────────────

ITEM_TEXT = 1
ITEM_IMAGE = 2
ITEM_VOICE = 3
ITEM_FILE = 4
ITEM_VIDEO = 5

MSG_TYPE_USER = 1
MSG_TYPE_BOT = 2
MSG_STATE_FINISH = 2

SESSION_EXPIRED = -14
RATE_LIMITED = -2

# ── 加密相关（可选） ─────────────────────────────────────────────

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    default_backend = None
    Cipher = None
    algorithms = None
    modes = None

# ── 辅助函数 ─────────────────────────────────────────────────────

_WEIXIN_CDN_ALLOWLIST = frozenset({
    "novac2c.cdn.weixin.qq.com",
    "ilinkai.weixin.qq.com",
    "wx.qlogo.cn",
    "thirdwx.qlogo.cn",
    "res.wx.qq.com",
    "mmbiz.qpic.cn",
    "mmbiz.qlogo.cn",
})


def _random_wechat_uin() -> str:
    """生成随机 X-WECHAT-UIN 头"""
    value = struct.unpack(">I", secrets.token_bytes(4))[0]
    return base64.b64encode(str(value).encode("utf-8")).decode("ascii")


def _base_info() -> Dict[str, Any]:
    return {"channel_version": CHANNEL_VERSION}


def _headers(token: Optional[str], body: str) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "Content-Length": str(len(body.encode("utf-8"))),
        "X-WECHAT-UIN": _random_wechat_uin(),
        "iLink-App-Id": ILINK_APP_ID,
        "iLink-App-ClientVersion": str(ILINK_APP_CLIENT_VERSION),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_post(
    base_url: str,
    endpoint: str,
    payload: Dict[str, Any],
    token: Optional[str] = None,
    timeout: int = API_TIMEOUT,
) -> Dict[str, Any]:
    """执行 iLink POST 请求"""
    body = json.dumps({**payload, "base_info": _base_info()}, ensure_ascii=False, separators=(",", ":"))
    url = f"{base_url.rstrip('/')}/{endpoint}"
    try:
        resp = requests.post(url, data=body, headers=_headers(token, body), timeout=timeout)
        if not resp.ok:
            raise RuntimeError(f"iLink POST {endpoint} HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()
    except requests.Timeout:
        return {"ret": -1, "errmsg": "timeout"}
    except requests.RequestException as e:
        raise RuntimeError(f"iLink POST {endpoint} failed: {e}") from e


def _api_get(
    base_url: str,
    endpoint: str,
    timeout: int = API_TIMEOUT,
) -> Dict[str, Any]:
    """执行 iLink GET 请求"""
    url = f"{base_url.rstrip('/')}/{endpoint}"
    headers = {
        "iLink-App-Id": ILINK_APP_ID,
        "iLink-App-ClientVersion": str(ILINK_APP_CLIENT_VERSION),
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if not resp.ok:
            raise RuntimeError(f"iLink GET {endpoint} HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()
    except requests.Timeout:
        return {"ret": -1, "errmsg": "timeout"}
    except requests.RequestException as e:
        raise RuntimeError(f"iLink GET {endpoint} failed: {e}") from e


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _aes128_ecb_encrypt(plaintext: bytes, key: bytes) -> bytes:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography 库未安装，无法加密媒体文件")
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(_pkcs7_pad(plaintext)) + encryptor.finalize()


def _aes128_ecb_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography 库未安装，无法解密媒体文件")
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    if not padded:
        return padded
    pad_len = padded[-1]
    if 1 <= pad_len <= 16 and padded.endswith(bytes([pad_len]) * pad_len):
        return padded[:-pad_len]
    return padded


def _aes_padded_size(size: int) -> int:
    return ((size + 1 + 15) // 16) * 16


def _parse_aes_key(aes_key_b64: str) -> bytes:
    decoded = base64.b64decode(aes_key_b64)
    if len(decoded) == 16:
        return decoded
    if len(decoded) == 32:
        text = decoded.decode("ascii", errors="ignore")
        if text and all(ch in "0123456789abcdefABCDEF" for ch in text):
            return bytes.fromhex(text)
    raise ValueError(f"不支持的 aes_key 格式 ({len(decoded)} decoded bytes)")


def _guess_chat_type(message: Dict[str, Any], account_id: str) -> Tuple[str, str]:
    """判断消息类型：私聊 (dm) 或群聊 (group)"""
    room_id = str(message.get("room_id") or message.get("chat_room_id") or "").strip()
    to_user_id = str(message.get("to_user_id") or "").strip()
    is_group = bool(room_id) or (
        to_user_id and account_id and to_user_id != account_id and message.get("msg_type") == 1
    )
    if is_group:
        return "group", room_id or to_user_id or str(message.get("from_user_id") or "")
    return "dm", str(message.get("from_user_id") or "")


def _extract_text(item_list: List[Dict[str, Any]]) -> str:
    """从消息 item_list 中提取文本内容"""
    for item in item_list:
        if item.get("type") == ITEM_TEXT:
            text = str((item.get("text_item") or {}).get("text") or "")
            # 处理引用消息
            ref = item.get("ref_msg") or {}
            ref_item = ref.get("message_item") or {}
            ref_type = ref_item.get("type")
            if ref_type in {ITEM_IMAGE, ITEM_VIDEO, ITEM_FILE, ITEM_VOICE}:
                title = ref.get("title") or ""
                prefix = f"[引用媒体: {title}]\n" if title else "[引用媒体]\n"
                return f"{prefix}{text}".strip()
            if ref_item:
                parts: List[str] = []
                if ref.get("title"):
                    parts.append(str(ref["title"]))
                ref_text = _extract_text([ref_item])
                if ref_text:
                    parts.append(ref_text)
                if parts:
                    return f"[引用: {' | '.join(parts)}]\n{text}".strip()
            return text
    # 语音消息提取文字（转写文本）
    for item in item_list:
        if item.get("type") == ITEM_VOICE:
            voice_text = str((item.get("voice_item") or {}).get("text") or "")
            if voice_text:
                return voice_text
    return ""


# ── 配置管理 ─────────────────────────────────────────────────────

def _get_config_dir() -> Path:
    """获取微信连接器配置目录"""
    try:
        from modules.globals import datapath
        base = Path(datapath)
    except ImportError:
        base = Path(os.path.expanduser("~")) / ".bloret-launcher"
    config_dir = base / "bloriko-agent" / "wechat"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _config_path() -> Path:
    return _get_config_dir() / "config.json"


def _sync_buf_path() -> Path:
    return _get_config_dir() / "sync_buf.json"


def save_config(account_id: str, token: str, base_url: str = ILINK_BASE_URL, user_id: str = "") -> None:
    """持久化微信连接凭据"""
    config = {
        "account_id": account_id,
        "token": token,
        "base_url": base_url,
        "user_id": user_id,
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = _config_path()
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    log.info("微信配置已保存: account_id=%s", account_id[:8])


def load_config() -> Optional[Dict[str, str]]:
    """读取已保存的微信连接凭据"""
    path = _config_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("读取微信配置失败: %s", e)
        return None


def clear_config() -> None:
    """清除微信配置"""
    path = _config_path()
    if path.exists():
        path.unlink()
    buf_path = _sync_buf_path()
    if buf_path.exists():
        buf_path.unlink()
    log.info("微信配置已清除")


def load_sync_buf() -> str:
    """读取同步缓存游标"""
    path = _sync_buf_path()
    if not path.exists():
        return ""
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("get_updates_buf", "")
    except Exception:
        return ""


def save_sync_buf(sync_buf: str) -> None:
    """保存同步缓存游标"""
    path = _sync_buf_path()
    path.write_text(json.dumps({"get_updates_buf": sync_buf}), encoding="utf-8")


def _generate_qr_image(data: str) -> Optional[str]:
    """
    生成 QR 码 PNG 图片到临时文件，返回 file:// 路径（供 QML Image 加载）。

    Args:
        data: 要编码到二维码中的文本

    Returns:
        file:///path/to/qr.png 或 None（qrcode 库未安装时）
    """
    try:
        import qrcode as qrcode_lib
        from PIL import Image as PilImage
        import tempfile

        qr = qrcode_lib.QRCode(version=1, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="bloriko_qr_")
        img.save(tmp.name)
        log.info("QR 图片已生成: %s", tmp.name)
        return f"file://{tmp.name}"

    except ImportError:
        log.warning("qrcode / Pillow 库未安装，无法生成 QR 图片")
        return None
    except Exception as e:
        log.error("生成 QR 图片失败: %s", e)
        return None


# ── QR 登录 ──────────────────────────────────────────────────────

def qr_login_step(
    timeout_seconds: int = 480,
    on_qr_url: Optional[Callable[[str], None]] = None,
    on_status_update: Optional[Callable[[str, str], None]] = None,
) -> Optional[Dict[str, str]]:
    """
    执行交互式 iLink QR 登录流程（同步、阻塞）。

    Args:
        timeout_seconds: 登录超时时间
        on_qr_url: 二维码图片 URL 回调 (url)
        on_status_update: 状态更新回调 (status, progress_text)

    返回凭据字典或 None。
    """
    log.info("开始微信 QR 登录流程...")

    try:
        qr_resp = _api_get(
            ILINK_BASE_URL,
            f"{EP_GET_BOT_QR}?bot_type=3",
            timeout=QR_TIMEOUT,
        )
    except Exception as e:
        log.error("获取二维码失败: %s", e)
        if on_status_update:
            on_status_update("error", f"获取二维码失败: {e}")
        return None

    qrcode_value = str(qr_resp.get("qrcode") or "")
    qrcode_url = str(qr_resp.get("qrcode_img_content") or "")
    if not qrcode_value:
        log.error("二维码响应缺少 qrcode")
        if on_status_update:
            on_status_update("error", "二维码响应异常")
        return None

    # 本地生成 QR 图片（QML Image 只能加载本地文件，无法直接加载扫码内容 URL）
    qr_scan_data = qrcode_url if qrcode_url else qrcode_value
    if on_qr_url:
        local_qr_path = _generate_qr_image(qr_scan_data)
        if local_qr_path:
            on_qr_url(local_qr_path)
        else:
            # 回退：传递原始 URL 作为纯文本显示
            on_qr_url("")

    if on_status_update:
        on_status_update("wait", "请使用微信扫描二维码")

    result: Dict[str, Any] = {
        "qrcode_url": qrcode_url,
        "qrcode_value": qrcode_value,
    }

    deadline = time.monotonic() + timeout_seconds
    current_base_url = ILINK_BASE_URL
    refresh_count = 0

    while time.monotonic() < deadline:
        try:
            status_resp = _api_get(
                current_base_url,
                f"{EP_GET_QR_STATUS}?qrcode={qrcode_value}",
                timeout=QR_TIMEOUT,
            )
        except Exception as e:
            log.warning("QR 轮询错误: %s", e)
            time.sleep(1)
            continue

        status = str(status_resp.get("status") or "wait")

        if status == "wait":
            if on_status_update:
                on_status_update("wait", "等待扫码...")
        elif status == "scaned":
            if on_status_update:
                on_status_update("scaned", "已扫码，请在手机上确认...")
        elif status == "scaned_but_redirect":
            redirect_host = str(status_resp.get("redirect_host") or "")
            if redirect_host:
                current_base_url = f"https://{redirect_host}"
            if on_status_update:
                on_status_update("scaned", "扫码后重定向...")
        elif status == "expired":
            refresh_count += 1
            if refresh_count > 3:
                log.warning("二维码多次过期，登录失败")
                if on_status_update:
                    on_status_update("expired", "二维码多次过期，请重新开始")
                return result
            try:
                qr_resp = _api_get(
                    ILINK_BASE_URL,
                    f"{EP_GET_BOT_QR}?bot_type=3",
                    timeout=QR_TIMEOUT,
                )
                qrcode_value = str(qr_resp.get("qrcode") or "")
                qrcode_url = str(qr_resp.get("qrcode_img_content") or "")
                result["qrcode_url"] = qrcode_url
                result["qrcode_value"] = qrcode_value
                if on_qr_url:
                    qr_scan_data = qrcode_url if qrcode_url else qrcode_value
                    local_qr_path = _generate_qr_image(qr_scan_data)
                    on_qr_url(local_qr_path or "")
                if on_status_update:
                    on_status_update("expired", f"二维码已刷新 ({refresh_count}/3)")
            except Exception as e:
                log.error("刷新二维码失败: %s", e)
                if on_status_update:
                    on_status_update("error", f"刷新二维码失败: {e}")
                return None
        elif status == "confirmed":
            account_id = str(status_resp.get("ilink_bot_id") or "")
            token = str(status_resp.get("bot_token") or "")
            base_url = str(status_resp.get("baseurl") or ILINK_BASE_URL)
            user_id = str(status_resp.get("ilink_user_id") or "")
            if not account_id or not token:
                log.error("扫码确认但凭据不完整")
                if on_status_update:
                    on_status_update("error", "扫码确认但凭据不完整")
                return result

            save_config(account_id, token, base_url, user_id)
            result["status"] = "confirmed"
            result["account_id"] = account_id
            result["token"] = token
            result["base_url"] = base_url
            result["user_id"] = user_id
            if on_status_update:
                on_status_update("confirmed", f"微信登录成功！账号ID: {account_id[:8]}...")
            log.info("微信 QR 登录成功: account_id=%s", account_id[:8])
            return result

        time.sleep(1)

    if on_status_update:
        on_status_update("timeout", "登录超时，请重试")
    log.warning("微信登录超时")
    return result


# ── 消息发送 ─────────────────────────────────────────────────────

class WechatMessageSender:
    """微信消息发送器"""

    def __init__(self, base_url: str, token: str, account_id: str):
        self._base_url = base_url
        self._token = token
        self._account_id = account_id

    def send_text(self, to_user_id: str, text: str) -> bool:
        """发送文本消息到微信"""
        if not text or not text.strip():
            return False

        message: Dict[str, Any] = {
            "from_user_id": "",
            "to_user_id": to_user_id,
            "client_id": f"bloriko-{secrets.token_hex(8)}",
            "message_type": MSG_TYPE_BOT,
            "message_state": MSG_STATE_FINISH,
            "item_list": [{"type": ITEM_TEXT, "text_item": {"text": text[:2000]}}],
        }

        try:
            resp = _api_post(
                self._base_url,
                EP_SEND_MESSAGE,
                payload={"msg": message},
                token=self._token,
                timeout=API_TIMEOUT,
            )
            ret = resp.get("ret", 0)
            errcode = resp.get("errcode", 0)
            if ret == 0 and errcode == 0:
                return True
            log.warning("发送消息失败: ret=%s errcode=%s errmsg=%s", ret, errcode, resp.get("errmsg", ""))
            return False
        except Exception as e:
            log.error("发送消息异常: %s", e)
            return False

    def send_text_chunks(self, to_user_id: str, text: str, max_len: int = 2000) -> int:
        """分块发送长文本，返回成功发送的块数"""
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            # 在最大长度附近找一个换行符断开
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].strip()

        sent = 0
        for chunk in chunks:
            if self.send_text(to_user_id, chunk):
                sent += 1
                time.sleep(1.5)  # 块间隔避免频率限制
        return sent


# ── 连接器主类 ───────────────────────────────────────────────────

class BlorikoWechatConnector:
    """
    Bloriko Agent 微信连接器

    管理微信登录、长轮询接收、消息发送。
    通过回调函数将收到的消息传递给 Agent。
    """

    STATUS_DISCONNECTED = "disconnected"
    STATUS_CONNECTING = "connecting"
    STATUS_CONNECTED = "connected"
    STATUS_ERROR = "error"

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
        self._sender: Optional[WechatMessageSender] = None

        # 消息去重
        self._dedup_set: set = set()
        self._dedup_lock = threading.Lock()

        # 配置
        self._account_id: str = ""
        self._token: str = ""
        self._base_url: str = ILINK_BASE_URL
        self._user_id: str = ""

        # 自动加载已保存配置
        self._load_saved_config()

    # ── 属性 ───────────────────────────────────────────────────

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == self.STATUS_CONNECTED

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def user_id(self) -> str:
        return self._user_id

    # ── 配置加载 ───────────────────────────────────────────────

    def _load_saved_config(self) -> bool:
        config = load_config()
        if config:
            self._account_id = config.get("account_id", "")
            self._token = config.get("token", "")
            self._base_url = config.get("base_url", ILINK_BASE_URL)
            self._user_id = config.get("user_id", "")
            return bool(self._token and self._account_id)
        return False

    def is_configured(self) -> bool:
        """检查是否已配置（有保存的凭据）"""
        return bool(self._token and self._account_id)

    def get_account_info(self) -> Dict[str, str]:
        """获取当前账号信息"""
        return {
            "account_id": self._account_id,
            "user_id": self._user_id,
            "base_url": self._base_url,
            "connected": self.is_connected,
        }

    def clear_config(self) -> None:
        """清除配置并断开"""
        self.stop()
        clear_config()
        self._account_id = ""
        self._token = ""
        self._base_url = ILINK_BASE_URL
        self._user_id = ""

    # ── 连接管理 ───────────────────────────────────────────────

    def start(self) -> bool:
        """启动微信连接器（基于已保存的凭据）"""
        if self.is_connected:
            log.info("微信连接器已在运行")
            return True

        if not self._token or not self._account_id:
            log.warning("微信连接器未配置，无法启动")
            self._set_status(self.STATUS_ERROR)
            if self._on_error:
                self._on_error("微信连接器未配置，请先扫码登录")
            return False

        self._running = True
        self._sender = WechatMessageSender(self._base_url, self._token, self._account_id)
        self._set_status(self.STATUS_CONNECTING)

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True, name="wechat-poll")
        self._poll_thread.start()
        log.info("微信连接器已启动 (account_id=%s)", self._account_id[:8])
        return True

    def stop(self) -> None:
        """停止微信连接器"""
        self._running = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=5)
            self._poll_thread = None
        self._sender = None
        self._set_status(self.STATUS_DISCONNECTED)
        log.info("微信连接器已停止")

    # ── 状态管理 ───────────────────────────────────────────────

    def _set_status(self, status: str) -> None:
        self._status = status
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception as e:
                log.warning("状态回调异常: %s", e)

    # ── 消息去重 ───────────────────────────────────────────────

    def _is_duplicate(self, message_id: str) -> bool:
        if not message_id:
            return False
        with self._dedup_lock:
            if message_id in self._dedup_set:
                return True
            self._dedup_set.add(message_id)
            # 限制集合大小
            if len(self._dedup_set) > 1000:
                self._dedup_set.clear()
        return False

    # ── 轮询循环 ───────────────────────────────────────────────

    def _poll_loop(self) -> None:
        """后台轮询线程：长轮询 iLink getupdates API"""
        sync_buf = load_sync_buf()
        timeout = LONG_POLL_TIMEOUT
        consecutive_failures = 0

        log.info("微信轮询线程已启动")
        self._set_status(self.STATUS_CONNECTED)

        while self._running:
            try:
                response = _api_post(
                    self._base_url,
                    EP_GET_UPDATES,
                    payload={"get_updates_buf": sync_buf},
                    token=self._token,
                    timeout=timeout + 5,  # 额外缓冲
                )

                suggested_timeout = response.get("longpolling_timeout_ms")
                if isinstance(suggested_timeout, int) and suggested_timeout > 0:
                    timeout = suggested_timeout / 1000

                ret = response.get("ret", 0)
                errcode = response.get("errcode", 0)

                if ret != 0 or errcode != 0:
                    if ret == SESSION_EXPIRED or errcode == SESSION_EXPIRED:
                        log.error("微信会话过期，10分钟后重试")
                        self._set_status(self.STATUS_ERROR)
                        if self._on_error:
                            self._on_error("微信会话过期，10分钟后自动重试")
                        # 暂停10分钟
                        for _ in range(600):
                            if not self._running:
                                return
                            time.sleep(1)
                        consecutive_failures = 0
                        self._set_status(self.STATUS_CONNECTED)
                        continue

                    consecutive_failures += 1
                    log.warning(
                        "getUpdates 失败: ret=%s errcode=%s errmsg=%s (%d/%d)",
                        ret, errcode, response.get("errmsg", ""),
                        consecutive_failures, MAX_RETRIES,
                    )
                    delay = BACKOFF_DELAY if consecutive_failures >= MAX_RETRIES else RETRY_DELAY
                    if consecutive_failures >= MAX_RETRIES:
                        self._set_status(self.STATUS_ERROR)
                    for _ in range(int(delay)):
                        if not self._running:
                            return
                        time.sleep(1)
                    continue

                consecutive_failures = 0
                if self._status != self.STATUS_CONNECTED:
                    self._set_status(self.STATUS_CONNECTED)

                # 更新同步缓存
                new_sync_buf = str(response.get("get_updates_buf") or "")
                if new_sync_buf:
                    sync_buf = new_sync_buf
                    save_sync_buf(sync_buf)

                # 处理消息
                for message in response.get("msgs") or []:
                    if not self._running:
                        return
                    self._process_message(message)

            except Exception as e:
                consecutive_failures += 1
                log.error("轮询异常 (%d/%d): %s", consecutive_failures, MAX_RETRIES, e)
                delay = BACKOFF_DELAY if consecutive_failures >= MAX_RETRIES else RETRY_DELAY
                if consecutive_failures >= MAX_RETRIES:
                    self._set_status(self.STATUS_ERROR)
                for _ in range(int(delay)):
                    if not self._running:
                        return
                    time.sleep(1)

        log.info("微信轮询线程已退出")

    # ── 消息处理 ───────────────────────────────────────────────

    def _process_message(self, message: Dict[str, Any]) -> None:
        """处理接收到的微信消息"""
        sender_id = str(message.get("from_user_id") or "").strip()
        if not sender_id or sender_id == self._account_id:
            return

        # 消息去重
        message_id = str(message.get("message_id") or "").strip()
        if message_id and self._is_duplicate(message_id):
            return

        # 内容去重
        item_list = message.get("item_list") or []
        text = _extract_text(item_list)
        if text:
            content_key = f"content:{sender_id}:{hashlib.md5(text.encode()).hexdigest()}"
            if self._is_duplicate(content_key):
                log.debug("内容去重: 跳过重复消息 from=%s", sender_id[:8])
                return

        # 判断聊天类型
        chat_type, effective_chat_id = _guess_chat_type(message, self._account_id)
        if chat_type == "group":
            # 暂不支持群聊
            log.debug("跳过群聊消息 from=%s", sender_id[:8])
            return

        if not text:
            log.debug("跳过无文本消息 from=%s", sender_id[:8])
            return

        log.info("收到微信消息 from=%s text='%s'", sender_id[:8], text[:50])

        # 回调通知 Agent
        if self._on_message:
            try:
                self._on_message(effective_chat_id, sender_id, text)
            except Exception as e:
                log.error("消息回调异常: %s", e)

    # ── 消息发送 ───────────────────────────────────────────────

    def send_message(self, chat_id: str, text: str) -> bool:
        """发送消息到微信"""
        if not self._sender:
            log.warning("发送器未就绪")
            return False
        if not self.is_connected:
            log.warning("微信未连接，无法发送")
            return False
        return self._sender.send_text(chat_id, text)

    def send_message_chunks(self, chat_id: str, text: str) -> int:
        """分块发送长文本"""
        if not self._sender:
            log.warning("发送器未就绪")
            return 0
        if not self.is_connected:
            log.warning("微信未连接，无法发送")
            return 0
        return self._sender.send_text_chunks(chat_id, text)

    # ── 工具函数 ───────────────────────────────────────────────

    @staticmethod
    def check_requirements() -> Dict[str, bool]:
        """检查依赖是否满足"""
        return {
            "requests": True,  # 必须
            "cryptography": CRYPTO_AVAILABLE,  # 媒体加密可选
        }
