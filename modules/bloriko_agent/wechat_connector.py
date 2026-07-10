"""
Bloriko Agent 微信连接器 — 向后兼容垫片

所有实际代码已迁移到 connectors/wechat.py。
此文件仅重新导出原有接口，保持 backend.py 等旧代码无需修改即可运行。
"""

# 从新位置导入所有公开符号
from .connectors.wechat import (
    # 连接器类
    WechatConnector as BlorikoWechatConnector,
    WechatMessageSender,
    # QR 登录
    qr_login_step,
    # 配置管理
    load_config,
    clear_config,
    load_sync_buf,
    save_sync_buf,
    # 常量
    ILINK_BASE_URL,
    ILINK_APP_ID,
    CHANNEL_VERSION,
    ILINK_APP_CLIENT_VERSION,
    EP_GET_BOT_QR,
    EP_GET_QR_STATUS,
    EP_GET_UPDATES,
    EP_SEND_MESSAGE,
    EP_GET_CONFIG,
    EP_GET_UPLOAD_URL,
    LONG_POLL_TIMEOUT,
    API_TIMEOUT,
    QR_TIMEOUT,
    # 加解密
    CRYPTO_AVAILABLE,
    # 辅助函数
    _generate_qr_image,
    _guess_chat_type,
    _extract_text,
)

__all__ = [
    "BlorikoWechatConnector",
    "WechatMessageSender",
    "qr_login_step",
    "load_config",
    "clear_config",
    "load_sync_buf",
    "save_sync_buf",
    "ILINK_BASE_URL",
    "ILINK_APP_ID",
    "CHANNEL_VERSION",
    "ILINK_APP_CLIENT_VERSION",
    "EP_GET_BOT_QR",
    "EP_GET_QR_STATUS",
    "EP_GET_UPDATES",
    "EP_SEND_MESSAGE",
    "EP_GET_CONFIG",
    "EP_GET_UPLOAD_URL",
    "LONG_POLL_TIMEOUT",
    "API_TIMEOUT",
    "QR_TIMEOUT",
    "CRYPTO_AVAILABLE",
]
