"""
跨平台系统通知模块

支持：
- Windows: win11toast (WinRT Toast)
- macOS: osascript (NSUserNotification)
- Linux: notify-send (libnotify)
- Bark: iOS 推送通知服务 (HTTP API)

通知类别（category）:
- launch_ready: Minecraft 启动完成
- launch_error: 启动失败 / 崩溃 / 超时
- download: 版本 / Mod 下载完成及失败
- install: Minecraft / Java / 插件安装完成及失败
- update: 应用更新可用 / 失败
- chat_message: Minecraft 聊天消息
- copilot: Copilot Agent 完成 / 需授权 / 出错
- account: 登录 / 同步
"""

import sys
import json
import logging
import subprocess
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

_CONFIG_CACHE = None
_CONFIG_MTIME = 0


def _read_notifications_config() -> dict:
    """读取通知配置（带 mtime 缓存，避免每次通知都读磁盘）"""
    global _CONFIG_CACHE, _CONFIG_MTIME
    try:
        import modules.globals as BLglobals
        import os
        path = BLglobals.config_path
        mtime = os.path.getmtime(path)
        if _CONFIG_CACHE is not None and mtime == _CONFIG_MTIME:
            return _CONFIG_CACHE
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _CONFIG_CACHE = data.get("notifications", {})
        _CONFIG_MTIME = mtime
        return _CONFIG_CACHE
    except Exception:
        return {}


def is_notification_enabled(category: str) -> bool:
    """检查指定类别的系统通知是否启用"""
    cfg = _read_notifications_config()
    if not cfg.get("enabled", True):
        return False
    return cfg.get(category, True)


def is_bark_enabled(category: str) -> bool:
    """检查指定类别的 Bark 通知是否启用"""
    cfg = _read_notifications_config()
    if not cfg.get("enabled", True):
        return False
    bark_url = cfg.get("bark_url", "")
    if not bark_url:
        return False
    return cfg.get(f"bark_{category}", True)


def invalidate_config_cache():
    """配置写入后调用，使缓存失效"""
    global _CONFIG_CACHE, _CONFIG_MTIME
    _CONFIG_CACHE = None
    _CONFIG_MTIME = 0


BARK_ICON = "https://launcher.bloret.net/BL.png"


def _send_bark(title: str, body: str, bark_url: str = None):
    """发送 Bark 推送通知

    Args:
        title: 通知标题
        body: 通知内容
        bark_url: Bark 终结点 URL（由调用方传入，避免重复读配置）
    """
    if bark_url is None:
        cfg = _read_notifications_config()
        bark_url = cfg.get("bark_url", "")
    if not bark_url:
        return

    bark_url = bark_url.rstrip("/")
    params = urllib.parse.urlencode({"icon": BARK_ICON})
    url = f"{bark_url}/{urllib.parse.quote(title)}/{urllib.parse.quote(body)}?{params}"

    def _do_request():
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "Bloret-Launcher")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
            log.info(f"Bark 通知发送成功: {title}")
        except Exception as e:
            log.warning(f"Bark 通知发送失败: {e}")

    import threading
    threading.Thread(target=_do_request, daemon=True).start()


def test_bark() -> str:
    """测试 Bark 推送，返回结果消息"""
    cfg = _read_notifications_config()
    bark_url = cfg.get("bark_url", "")
    if not bark_url:
        return "未配置 Bark URL"

    bark_url = bark_url.rstrip("/")
    params = urllib.parse.urlencode({"icon": BARK_ICON})
    url = f"{bark_url}/{urllib.parse.quote('Bark 测试')}/{urllib.parse.quote('来自 Bloret Launcher 的测试推送') }?{params}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Bloret-Launcher")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        return "发送成功"
    except Exception as e:
        return f"发送失败: {e}"


def send_notification(title: str, body: str, *, category: str = None, app_id: str = "Bloret Launcher"):
    """发送操作系统级通知 + Bark 推送

    Args:
        title: 通知标题
        body: 通知内容
        category: 通知类别（用于读取用户偏好），为 None 则强制发送
        app_id: 应用标识（Linux notify-send 用）
    """
    cfg = _read_notifications_config()
    master_on = cfg.get("enabled", True)

    send_system = category is None or (master_on and cfg.get(category, True))
    bark_url = cfg.get("bark_url", "")
    send_bark = category is not None and master_on and bark_url and cfg.get(f"bark_{category}", True)

    if not send_system and not send_bark:
        return

    if send_system:
        try:
            if sys.platform == "win32":
                from modules.win11toast import notify
                notify(title=title, body=body)
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["osascript", "-e",
                     f'display notification "{body}" with title "{title}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["notify-send", "-a", app_id, title, body],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            log.debug(f"发送系统通知失败: {e}")

    if send_bark:
        _send_bark(title, body, bark_url=bark_url)
