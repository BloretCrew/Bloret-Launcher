import threading

import modules.globals as BLglobals
from modules.log import log

_IP_JSON_URL = "https://raw.gitcode.com/Bloret/Bloret-Launcher/raw/Windows/IP.json"
_refresh_lock = threading.Lock()
_refresh_started = False


def refresh_server_ip(timeout=5):
    """Fetch server IP from remote IP.json and update BLglobals.server_ip.

    Safe to call repeatedly; failures leave the existing default IP in place.
    """
    try:
        import requests

        log("正在获取服务器 IP...")
        res = requests.get(_IP_JSON_URL, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            if "PCFS" in data:
                new_ip = data["PCFS"]
                BLglobals.server_ip = f"http://{new_ip}"
                log(f"已更新服务器 IP: {BLglobals.server_ip}")
                return True
            log("IP.json 中未找到 PCFS 字段")
        else:
            log(f"获取服务器 IP 失败，状态码: {res.status_code}")
    except Exception as e:
        log(f"获取服务器 IP 时发生异常: {e}")
    return False


def refresh_server_ip_async():
    """Start a one-shot background refresh of server IP (idempotent per process)."""
    global _refresh_started
    with _refresh_lock:
        if _refresh_started:
            return
        _refresh_started = True

    def _worker():
        try:
            refresh_server_ip()
        except Exception as e:
            log(f"后台刷新服务器 IP 失败: {e}")

    threading.Thread(target=_worker, daemon=True, name="RefreshServerIP").start()


# Import no longer blocks on network; callers should use refresh_server_ip_async()
# after UI is ready (or refresh_server_ip() for synchronous needs).
