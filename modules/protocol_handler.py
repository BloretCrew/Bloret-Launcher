"""bloret:// 自定义协议：注册、解析、单实例 IPC 转发。

网页商店按钮:
  window.location = 'bloret://plugin/install?download=...&name=...'

已运行实例通过本地 IPC（socket / 请求文件）接收 deep link。
"""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

from modules.log import log

PROTOCOL_SCHEME = "bloret"
IPC_PORT_ENV = "BLORET_IPC_PORT"
DEFAULT_IPC_PORT = 25253
IPC_HOST = "127.0.0.1"

# 回调：收到 deep link / 安装请求时
_on_deep_link: Optional[Callable[[str], None]] = None
_ipc_server_thread: Optional[threading.Thread] = None
_ipc_stop = threading.Event()


def extract_bloret_urls(argv: Optional[List[str]] = None) -> List[str]:
    """从命令行参数提取 bloret:// URL。"""
    args = list(argv if argv is not None else sys.argv[1:])
    found: List[str] = []
    for arg in args:
        if not arg:
            continue
        s = str(arg).strip().strip('"').strip("'")
        if s.lower().startswith("bloret:"):
            found.append(s)
    return found


def is_bloret_url(value: str) -> bool:
    return bool(value) and str(value).strip().lower().startswith("bloret:")


def ipc_port_file() -> str:
    return os.path.join(tempfile.gettempdir(), "bloret-launcher-ipc.port")


def deep_link_queue_file() -> str:
    return os.path.join(tempfile.gettempdir(), "bloret-launcher-deeplinks.jsonl")


def write_ipc_port(port: int) -> None:
    path = ipc_port_file()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(int(port)))
        log(f"[Protocol] IPC 端口已写入 {path}: {port}")
    except Exception as e:
        log(f"[Protocol] 写入 IPC 端口失败: {e}")


def read_ipc_port() -> Optional[int]:
    path = ipc_port_file()
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def enqueue_deep_link_file(url: str) -> bool:
    """首实例未就绪时的文件队列 fallback。"""
    path = deep_link_queue_file()
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"url": url, "ts": time.time()}, ensure_ascii=False) + "\n")
        log(f"[Protocol] deep link 已写入队列文件: {url[:80]}…")
        return True
    except Exception as e:
        log(f"[Protocol] 写入 deep link 队列失败: {e}")
        return False


def drain_deep_link_file() -> List[str]:
    path = deep_link_queue_file()
    if not os.path.isfile(path):
        return []
    urls: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    u = data.get("url") or ""
                    if u:
                        urls.append(u)
                except Exception:
                    if line.lower().startswith("bloret:"):
                        urls.append(line)
        os.remove(path)
        log(f"[Protocol] 从队列文件取出 {len(urls)} 条 deep link")
    except Exception as e:
        log(f"[Protocol] 读取 deep link 队列失败: {e}")
    return urls


def send_deep_link_to_running(url: str, timeout: float = 2.0) -> bool:
    """向已运行实例发送 deep link；成功返回 True。"""
    port = read_ipc_port()
    if not port:
        # 尝试默认端口
        port = DEFAULT_IPC_PORT
    payload = (json.dumps({"type": "deep_link", "url": url}, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    try:
        with socket.create_connection((IPC_HOST, int(port)), timeout=timeout) as sock:
            sock.sendall(payload)
            sock.settimeout(timeout)
            try:
                resp = sock.recv(256)
                if resp:
                    log(f"[Protocol] IPC 发送成功 port={port} resp={resp[:40]!r}")
                    return True
            except socket.timeout:
                # 无响应也认为已送达
                log(f"[Protocol] IPC 已发送（无响应）port={port}")
                return True
        return True
    except Exception as e:
        log(f"[Protocol] IPC 发送失败 port={port}: {e}")
        # fallback 文件队列
        return enqueue_deep_link_file(url)


def set_deep_link_handler(callback: Callable[[str], None]) -> None:
    global _on_deep_link
    _on_deep_link = callback
    log("[Protocol] deep link 处理器已注册")


def _dispatch_url(url: str) -> None:
    log(f"[Protocol] 分发 deep link: {url[:120]}…")
    # 插件 protocol 贡献：匹配 path 前缀后优先处理
    try:
        from modules.plugin_host.registry import get_registry
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = (parsed.path or "").lstrip("/")
        host = (parsed.netloc or "").strip()
        # bloret://plugin/install → netloc=plugin, path=install
        full_key = f"{host}/{path}".strip("/") if host else path
        for item in get_registry().get_protocols():
            prefix = str(item.get("path") or item.get("prefix") or "").lstrip("/")
            handler = item.get("handler")
            if not prefix or not callable(handler):
                continue
            if full_key == prefix or full_key.startswith(prefix.rstrip("/") + "/"):
                try:
                    handled = handler(url, parsed)
                    if handled is not False:
                        log(f"[Protocol] 由插件处理 prefix={prefix} @ {item.get('plugin_id')}")
                        return
                except Exception as pe:
                    log(f"[Protocol] 插件协议处理失败 {item.get('plugin_id')}: {pe}")
    except Exception as e:
        log(f"[Protocol] 插件协议分发跳过: {e}")

    cb = _on_deep_link
    if cb:
        try:
            cb(url)
        except Exception as e:
            log(f"[Protocol] deep link 回调失败: {e}")
    else:
        log("[Protocol] 无 deep link 回调，写入文件队列")
        enqueue_deep_link_file(url)


def start_ipc_server(preferred_port: int = DEFAULT_IPC_PORT) -> Optional[int]:
    """在后台启动本机 IPC 服务，返回实际端口。"""
    global _ipc_server_thread
    if _ipc_server_thread and _ipc_server_thread.is_alive():
        log("[Protocol] IPC 服务已在运行")
        return read_ipc_port()

    _ipc_stop.clear()
    bound_port: List[int] = []

    def _serve() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = preferred_port
        try:
            srv.bind((IPC_HOST, port))
        except OSError:
            try:
                srv.bind((IPC_HOST, 0))
                port = srv.getsockname()[1]
            except OSError as e:
                log(f"[Protocol] IPC bind 失败: {e}")
                return
        srv.listen(8)
        srv.settimeout(1.0)
        bound_port.append(port)
        write_ipc_port(port)
        log(f"[Protocol] IPC 服务监听 {IPC_HOST}:{port}")
        while not _ipc_stop.is_set():
            try:
                conn, _addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                conn.settimeout(2.0)
                data = b""
                while b"\n" not in data and len(data) < 65536:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                text = data.decode("utf-8", errors="replace").strip()
                if text:
                    try:
                        msg = json.loads(text.split("\n", 1)[0])
                    except Exception:
                        msg = {"type": "deep_link", "url": text}
                    url = ""
                    if isinstance(msg, dict):
                        if msg.get("type") in ("deep_link", "plugin_install", None):
                            url = msg.get("url") or msg.get("link") or ""
                        # 也支持直接投递 propose 字段
                        if not url and msg.get("download"):
                            from urllib.parse import urlencode

                            q = {k: v for k, v in msg.items() if k not in ("type",) and v}
                            url = f"bloret://plugin/install?{urlencode(q)}"
                    if url:
                        _dispatch_url(url)
                    conn.sendall(b'{"ok":true}\n')
            except Exception as e:
                log(f"[Protocol] IPC 连接处理失败: {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        try:
            srv.close()
        except Exception:
            pass
        log("[Protocol] IPC 服务已停止")

    _ipc_server_thread = threading.Thread(target=_serve, name="bloret-ipc", daemon=True)
    _ipc_server_thread.start()
    # 等待 bind
    for _ in range(20):
        if bound_port:
            return bound_port[0]
        time.sleep(0.05)
    return read_ipc_port()


def stop_ipc_server() -> None:
    _ipc_stop.set()
    try:
        path = ipc_port_file()
        if os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def register_protocol_windows(executable: Optional[str] = None) -> bool:
    """注册 HKCU bloret URL protocol（当前用户，无需管理员）。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        exe = executable or sys.executable
        # 打包后 sys.executable 即启动器；开发时用 python + 脚本
        if getattr(sys, "frozen", False) or exe.lower().endswith(".exe"):
            cmd = f'"{exe}" "%1"'
        else:
            script = os.path.abspath(sys.argv[0]) if sys.argv else ""
            cmd = f'"{exe}" "{script}" "%1"'

        key_path = r"Software\Classes\bloret"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:Bloret Launcher Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\shell\open\command") as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, cmd)
        log(f"[Protocol] Windows 已注册 bloret:// → {cmd}")
        return True
    except Exception as e:
        log(f"[Protocol] Windows 注册失败: {e}")
        return False


def register_protocol_linux(executable: Optional[str] = None) -> bool:
    """写入用户级 .desktop 并尝试 xdg-mime 注册。"""
    if sys.platform == "win32" or sys.platform == "darwin":
        return False
    try:
        exe = executable or sys.executable
        if getattr(sys, "frozen", False):
            exec_line = f'"{exe}" %u'
        else:
            script = os.path.abspath(sys.argv[0]) if sys.argv else ""
            exec_line = f'"{exe}" "{script}" %u'

        apps_dir = Path.home() / ".local" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        desktop_path = apps_dir / "bloret-launcher-protocol.desktop"
        content = "\n".join(
            [
                "[Desktop Entry]",
                "Name=Bloret Launcher",
                "Comment=Open bloret:// links",
                "Type=Application",
                f"Exec={exec_line}",
                "Terminal=false",
                "Categories=Game;",
                "MimeType=x-scheme-handler/bloret;",
                "NoDisplay=true",
                "",
            ]
        )
        desktop_path.write_text(content, encoding="utf-8")
        log(f"[Protocol] Linux desktop 已写入: {desktop_path}")
        try:
            import subprocess

            subprocess.run(
                ["xdg-mime", "default", desktop_path.name, "x-scheme-handler/bloret"],
                check=False,
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            log(f"[Protocol] xdg-mime 注册提示: {e}")
        return True
    except Exception as e:
        log(f"[Protocol] Linux 注册失败: {e}")
        return False


def ensure_protocol_registered() -> bool:
    """按平台注册 bloret://（幂等、失败不阻断启动）。"""
    try:
        if sys.platform == "win32":
            return register_protocol_windows()
        if sys.platform == "darwin":
            log("[Protocol] macOS 协议注册依赖 Info.plist，打包时配置")
            return False
        return register_protocol_linux()
    except Exception as e:
        log(f"[Protocol] ensure_protocol_registered: {e}")
        return False


def handle_second_instance_argv(argv: Optional[List[str]] = None) -> bool:
    """二次实例：转发 deep link 后应退出。返回 True 表示已处理 deep link。"""
    urls = extract_bloret_urls(argv)
    if not urls:
        return False
    ok_any = False
    for url in urls:
        log(f"[Protocol] 二次实例转发: {url[:100]}…")
        if send_deep_link_to_running(url):
            ok_any = True
    return ok_any
