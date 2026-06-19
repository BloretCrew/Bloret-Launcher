import copy
import gzip
import io
import logging
import os
import platform
import re
import shutil
import socket
import struct
import subprocess
import threading
import time

from modules.i18n import i18nText
from modules.log import log
from modules.paths import get_app_dir


PUBLIC_PEERS = [
    "tcp://et1.fuis.top:11010",
]

VIRTUAL_IP_PATTERN = re.compile(r"tcp://(\d+\.\d+\.\d+\.\d+):")

LAN_PORT_PATTERNS = [
    re.compile(r"Local game hosted on port (\d+)"),
    re.compile(r"Started serving on (\d+)"),
    re.compile(r"本地游戏已在端口[\[\s]*(\d+)[\]\s]*上开启"),  # 支持 [port] 或 port 格式
    re.compile(r"本地游戏已在端口 (\d+)"),
]

_SESSION_LOCK = threading.RLock()
_LOG_READER_THREADS = []
_LOG_WATCH_THREAD = None
_LOG_WATCH_STOP = None

_SESSION = {
    "space_id": "",
    "space_name": "",
    "mode": "",
    "network_name": "",
    "network_secret": "",
    "host_username": "",
    "proxy_port": None,
    "virtual_ip": "",
    "target_host_virtual_ip": "",
    "target_game_port": None,
    "game_port": None,
    "target_address": "",
    "running": False,
    "status": "idle",
    "error": "",
    "watching_version": "",
    "log_path": "",
    "started_at": None,
}

_PROCESS_STATE = {
    "process": None,
    "binary_dir": "",
}


def _get_creationflags():
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _ensure_executable(path):
    if path and os.name != "nt" and os.path.exists(path):
        try:
            current_mode = os.stat(path).st_mode
            os.chmod(path, current_mode | 0o111)
        except OSError as exc:
            log(f"EasyTier chmod 失败: {exc}", logging.WARNING)


def _candidate_binary_dirs():
    # 打包后 easytier/ 位于资源根目录（Nuitka onefile 下为临时解压目录），
    # 不能用 os.getcwd()（那是启动目录，不是解压目录）。
    app_dir = str(get_app_dir())
    return [
        os.path.join(app_dir, "EasyTier"),
        os.path.join(app_dir, "easytier"),
        os.path.join(app_dir, "BL4CW2", "net.bloret.launcher", "launcher", "easytier"),
    ]


def _resolve_binary(binary_name):
    for base_dir in _candidate_binary_dirs():
        candidate = os.path.join(base_dir, binary_name)
        if os.path.exists(candidate):
            _ensure_executable(candidate)
            return candidate
    return ""


def _binary_paths():
    core_name = "easytier-core.exe" if os.name == "nt" else "easytier-core"
    cli_name = "easytier-cli.exe" if os.name == "nt" else "easytier-cli"
    core_path = _resolve_binary(core_name)
    cli_path = _resolve_binary(cli_name)
    binary_dir = os.path.dirname(core_path) if core_path else ""
    
    if not cli_path:
        log(f"警告：未找到 {cli_name}，虚拟 IP 查询将失败", logging.WARNING)
    
    return core_path, cli_path, binary_dir


def _decode_output(data):
    if isinstance(data, str):
        return data
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(encoding)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def _reader_thread(stream, label):
    try:
        while True:
            chunk = stream.readline()
            if not chunk:
                break
            text = _decode_output(chunk).strip()
            if text:
                log(f"[EasyTier/{label}] {text}")
                
                # 从日志中提取虚拟 IP（格式：tcp://198.18.0.1:xxxxx）
                if label == "stdout" and "local_addr" in text:
                    match = VIRTUAL_IP_PATTERN.search(text)
                    if match:
                        virtual_ip = match.group(1)
                        with _SESSION_LOCK:
                            if not _SESSION.get("virtual_ip"):
                                _SESSION["virtual_ip"] = virtual_ip
                                log(f"从 EasyTier 日志提取虚拟 IP: {virtual_ip}", logging.INFO)
    except Exception as exc:
        log(f"读取 EasyTier {label} 日志失败: {exc}", logging.WARNING)


def _allocate_proxy_port(preferred=1080):
    candidates = [preferred] + list(range(1081, 1096))
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_process(args, binary_dir):
    process = subprocess.Popen(
        args,
        cwd=binary_dir or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=_get_creationflags(),
    )

    for label, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        thread = threading.Thread(target=_reader_thread, args=(stream, label), daemon=True)
        thread.start()
        _LOG_READER_THREADS.append(thread)

    return process


def _try_get_virtual_ip(cli_path):
    if not cli_path or not os.path.exists(cli_path):
        log(f"EasyTier CLI 路径不存在: {cli_path}", logging.DEBUG)
        return ""

    try:
        result = subprocess.run(
            [cli_path, "node", "info"],
            capture_output=True,
            timeout=10,  # 增加到 10 秒
            cwd=os.path.dirname(cli_path) or None,
            creationflags=_get_creationflags(),
        )
    except subprocess.TimeoutExpired:
        log("EasyTier CLI 查询虚拟 IP 超时（可能进程还在初始化）", logging.DEBUG)
        return ""
    except Exception as exc:
        log(f"EasyTier CLI 查询失败: {exc}", logging.WARNING)
        return ""

    output = _decode_output(result.stdout or b"")
    if result.stderr:
        stderr_text = _decode_output(result.stderr)
        if stderr_text.strip():
            log(f"[EasyTier/cli] {stderr_text.strip()}", logging.DEBUG)

    for line in output.splitlines():
        if "Virtual IP" not in line:
            continue
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        if match:
            ip = match.group(1)
            log(f"成功获取 EasyTier 虚拟 IP: {ip}", logging.DEBUG)
            return ip
    
    log(f"未在 CLI 输出中找到虚拟 IP，输出: {output[:200]}", logging.DEBUG)
    return ""


def get_easytier_virtual_ip(cli_path=None):
    if not cli_path:
        _, cli_path, _ = _binary_paths()
    ip = _try_get_virtual_ip(cli_path)
    if ip:
        with _SESSION_LOCK:
            _SESSION["virtual_ip"] = ip
    return ip or None


def _update_target_address_locked():
    host_ip = _SESSION.get("target_host_virtual_ip") or ""
    game_port = _SESSION.get("target_game_port")
    if host_ip and game_port:
        _SESSION["target_address"] = f"{host_ip}:{game_port}"
    else:
        _SESSION["target_address"] = ""


def _build_command(mode, network_name, network_secret, proxy_port, use_public_servers):
    core_path, _, binary_dir = _binary_paths()
    if not core_path:
        raise FileNotFoundError("未找到 EasyTier 核心程序")

    args = [
        core_path,
        "--network-name", network_name,
        "--network-secret", network_secret,
        "--no-tun",
    ]

    if mode == "client" and proxy_port:
        args.extend(["--proxy-port", str(proxy_port)])

    if use_public_servers:
        for peer in PUBLIC_PEERS:
            args.extend(["-p", peer])

    return args, binary_dir


def _wait_for_virtual_ip(cli_path, timeout_seconds=12):
    deadline = time.time() + timeout_seconds
    retry_count = 0
    
    while time.time() < deadline:
        ip = _try_get_virtual_ip(cli_path)
        if ip:
            log(f"虚拟 IP 获取成功（CLI 第 {retry_count+1} 次尝试）", logging.INFO)
            return ip
        
        # 检查日志中是否已提取到虚拟 IP
        with _SESSION_LOCK:
            if _SESSION.get("virtual_ip"):
                log(f"虚拟 IP 已从日志中提取: {_SESSION['virtual_ip']}", logging.INFO)
                return _SESSION["virtual_ip"]
        
        retry_count += 1
        time.sleep(1)
    
    # 超时后返回日志中提取的 IP（如果有）
    with _SESSION_LOCK:
        ip = _SESSION.get("virtual_ip", "")
    
    if ip:
        log(f"虚拟 IP 最终获取成功（从日志）: {ip}", logging.INFO)
        return ip
    
    log(f"虚拟 IP 获取超时（{retry_count} 次重试），进程继续运行", logging.WARNING)
    return ""


def _set_session_base(mode, space_id, space_name, network_name, network_secret, host_username, proxy_port):
    with _SESSION_LOCK:
        _SESSION.update({
            "space_id": space_id or "",
            "space_name": space_name or "",
            "mode": mode or "",
            "network_name": network_name or "",
            "network_secret": network_secret or "",
            "host_username": host_username or "",
            "proxy_port": proxy_port,
            "virtual_ip": "",
            "game_port": None,
            "target_host_virtual_ip": "",
            "target_game_port": None,
            "target_address": "",
            "running": False,
            "status": "starting",
            "error": "",
            "watching_version": "",
            "log_path": "",
            "started_at": int(time.time()),
        })


def start_live_session(
    mode,
    network_name,
    network_secret,
    space_id="",
    space_name="",
    host_username="",
    target_host_virtual_ip="",
    target_game_port=None,
    use_public_servers=True,
):
    if mode not in ("host", "client"):
        return {"success": False, "message": "未知的 EasyTier 模式", "snapshot": get_live_session_snapshot()}

    stop_live_session()

    proxy_port = _allocate_proxy_port() if mode == "client" else None
    _set_session_base(mode, space_id, space_name, network_name, network_secret, host_username, proxy_port)

    try:
        command, binary_dir = _build_command(mode, network_name, network_secret, proxy_port, use_public_servers)
        process = _start_process(command, binary_dir)
    except Exception as exc:
        with _SESSION_LOCK:
            _SESSION["status"] = "error"
            _SESSION["error"] = str(exc)
        log(f"启动 EasyTier 失败: {exc}", logging.ERROR)
        return {"success": False, "message": str(exc), "snapshot": get_live_session_snapshot()}

    with _SESSION_LOCK:
        _PROCESS_STATE["process"] = process
        _PROCESS_STATE["binary_dir"] = binary_dir

    time.sleep(1.5)
    if process.poll() is not None:
        stderr_text = ""
        try:
            stderr_text = _decode_output(process.stderr.read() or b"").strip()
        except Exception:
            pass
        message = stderr_text or "EasyTier 进程已提前退出"
        with _SESSION_LOCK:
            _SESSION["status"] = "error"
            _SESSION["error"] = message
        log(f"EasyTier 进程提前退出: {message}", logging.ERROR)
        return {"success": False, "message": message, "snapshot": get_live_session_snapshot()}

    _, cli_path, _ = _binary_paths()
    virtual_ip = _wait_for_virtual_ip(cli_path)

    with _SESSION_LOCK:
        _SESSION["running"] = True
        _SESSION["status"] = "running"
        _SESSION["virtual_ip"] = virtual_ip or _SESSION.get("virtual_ip") or ""
        if target_host_virtual_ip:
            _SESSION["target_host_virtual_ip"] = target_host_virtual_ip
        if target_game_port:
            _SESSION["target_game_port"] = int(target_game_port)
        _update_target_address_locked()

    snapshot = get_live_session_snapshot()
    return {"success": True, "message": "EasyTier 已启动", "snapshot": snapshot}


def stop_live_session(space_id=None):
    global _LOG_WATCH_THREAD, _LOG_WATCH_STOP

    with _SESSION_LOCK:
        if space_id and _SESSION.get("space_id") and _SESSION.get("space_id") != space_id:
            return False

        process = _PROCESS_STATE.get("process")
        _PROCESS_STATE["process"] = None
        _PROCESS_STATE["binary_dir"] = ""

        if _LOG_WATCH_STOP:
            _LOG_WATCH_STOP.set()

    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as exc:
            log(f"停止 EasyTier 失败: {exc}", logging.WARNING)

    if _LOG_WATCH_THREAD and _LOG_WATCH_THREAD.is_alive():
        _LOG_WATCH_THREAD.join(timeout=1)
    _LOG_WATCH_THREAD = None
    _LOG_WATCH_STOP = None

    with _SESSION_LOCK:
        _SESSION.update({
            "space_id": "",
            "space_name": "",
            "mode": "",
            "network_name": "",
            "network_secret": "",
            "host_username": "",
            "proxy_port": None,
            "virtual_ip": "",
            "target_host_virtual_ip": "",
            "target_game_port": None,
            "game_port": None,
            "target_address": "",
            "running": False,
            "status": "idle",
            "error": "",
            "watching_version": "",
            "log_path": "",
            "started_at": None,
        })
    return True


def get_live_session_snapshot():
    with _SESSION_LOCK:
        snapshot = copy.deepcopy(_SESSION)
        snapshot["local_running"] = snapshot.get("running", False)
        snapshot["host_address"] = snapshot.get("target_address", "")
    return snapshot


def refresh_live_virtual_ip():
    ip = get_easytier_virtual_ip()
    return ip or ""


def update_live_target(host_virtual_ip="", game_port=None):
    with _SESSION_LOCK:
        if host_virtual_ip is not None:
            _SESSION["target_host_virtual_ip"] = host_virtual_ip or ""
        if game_port is not None:
            _SESSION["target_game_port"] = int(game_port) if game_port else None
        _update_target_address_locked()
        return copy.deepcopy(_SESSION)


def set_live_game_port(game_port):
    if not game_port:
        return
    with _SESSION_LOCK:
        if _SESSION.get("game_port") == int(game_port):
            return
        _SESSION["game_port"] = int(game_port)
        log(f"已捕获 Minecraft 局域网端口: {game_port}")


def _watch_log_file(log_path, stop_event):
    last_offset = 0
    while not stop_event.is_set():
        try:
            if not os.path.exists(log_path):
                time.sleep(1)
                continue

            current_size = os.path.getsize(log_path)
            if current_size < last_offset:
                last_offset = 0

            with open(log_path, "r", encoding="utf-8", errors="ignore") as handle:
                handle.seek(last_offset)
                chunk = handle.read()
                last_offset = handle.tell()

            if chunk:
                for line in chunk.splitlines():
                    for pattern in LAN_PORT_PATTERNS:
                        match = pattern.search(line)
                        if match:
                            set_live_game_port(match.group(1))
                            break
            time.sleep(1)
        except Exception as exc:
            log(f"监听 Minecraft latest.log 失败: {exc}", logging.WARNING)
            time.sleep(2)


def start_host_log_watch(mc_version, minecraft_dir):
    global _LOG_WATCH_THREAD, _LOG_WATCH_STOP

    with _SESSION_LOCK:
        if _SESSION.get("mode") != "host" or not _SESSION.get("running"):
            return ""

    log_path = os.path.join(minecraft_dir, "versions", mc_version, "logs", "latest.log")

    with _SESSION_LOCK:
        if _SESSION.get("log_path") == log_path and _LOG_WATCH_THREAD and _LOG_WATCH_THREAD.is_alive():
            return log_path

        if _LOG_WATCH_STOP:
            _LOG_WATCH_STOP.set()

        _LOG_WATCH_STOP = threading.Event()
        _SESSION["watching_version"] = mc_version
        _SESSION["log_path"] = log_path

    _LOG_WATCH_THREAD = threading.Thread(
        target=_watch_log_file,
        args=(log_path, _LOG_WATCH_STOP),
        daemon=True,
    )
    _LOG_WATCH_THREAD.start()
    log(f"开始监听 Live 房主日志: {log_path}")
    return log_path


def try_start_live_game_port_watch():
    """尝试自动启动日志监听（仅在房主模式下）。
    返回是否成功启动了监听。
    """
    with _SESSION_LOCK:
        if _SESSION.get("mode") != "host" or not _SESSION.get("running"):
            return False
    
    # 获取 Minecraft 目录和当前版本
    from modules import globals as BLglobals
    from modules.launch import Get_Run_Script
    
    minecraft_dir = BLglobals.minecraft_dir
    if not minecraft_dir or not os.path.exists(minecraft_dir):
        log(f"[Live Log Watch] Minecraft 目录不存在: {minecraft_dir}", logging.WARNING)
        return False
    
    # 尝试获取最后运行的版本
    # 这是一个简化版本 - 实际上可能需要从配置读取
    try:
        versions_dir = os.path.join(minecraft_dir, "versions")
        if os.path.exists(versions_dir):
            versions = [d for d in os.listdir(versions_dir) 
                       if os.path.isdir(os.path.join(versions_dir, d))]
            if versions:
                # 选择最新修改的版本（作为可能的最后运行版本）
                latest_version = max(versions, 
                                    key=lambda v: os.path.getmtime(os.path.join(versions_dir, v)))
                started_log_watch = start_host_log_watch(latest_version, minecraft_dir)
                if started_log_watch:
                    log(f"[Live Log Watch] 已启动日志监听，版本: {latest_version}", logging.INFO)
                    return True
    except Exception as e:
        log(f"[Live Log Watch] 启动日志监听失败: {e}", logging.DEBUG)
        return False
    
    return False


def _read_nbt_string(stream):
    length_bytes = stream.read(2)
    if len(length_bytes) < 2:
        return ""
    length = struct.unpack(">H", length_bytes)[0]
    return stream.read(length).decode("utf-8", errors="ignore")


def _read_nbt_payload(stream, tag_type):
    if tag_type == 8:
        return _read_nbt_string(stream)
    if tag_type == 9:
        list_tag = struct.unpack(">b", stream.read(1))[0]
        list_length = struct.unpack(">i", stream.read(4))[0]
        return [_read_nbt_payload(stream, list_tag) for _ in range(list_length)]
    if tag_type == 10:
        compound = {}
        while True:
            nested_tag_bytes = stream.read(1)
            if not nested_tag_bytes:
                break
            nested_tag = struct.unpack(">b", nested_tag_bytes)[0]
            if nested_tag == 0:
                break
            nested_name = _read_nbt_string(stream)
            compound[nested_name] = _read_nbt_payload(stream, nested_tag)
        return compound
    if tag_type == 1:
        return struct.unpack(">b", stream.read(1))[0]
    if tag_type == 2:
        return struct.unpack(">h", stream.read(2))[0]
    if tag_type == 3:
        return struct.unpack(">i", stream.read(4))[0]
    if tag_type == 7:
        length = struct.unpack(">i", stream.read(4))[0]
        return stream.read(length)
    if tag_type == 11:
        length = struct.unpack(">i", stream.read(4))[0]
        return [struct.unpack(">i", stream.read(4))[0] for _ in range(length)]
    if tag_type == 12:
        length = struct.unpack(">i", stream.read(4))[0]
        return [struct.unpack(">q", stream.read(8))[0] for _ in range(length)]
    raise ValueError(f"暂不支持的 NBT 标签类型: {tag_type}")


def _parse_servers_dat(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "rb") as handle:
            data = handle.read()
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        stream = io.BytesIO(data)
        root_tag = struct.unpack(">b", stream.read(1))[0]
        if root_tag != 10:
            return []
        _read_nbt_string(stream)
        root_payload = _read_nbt_payload(stream, 10)
        servers = root_payload.get("servers", [])
        return servers if isinstance(servers, list) else []
    except Exception as exc:
        log(f"读取 servers.dat 失败: {exc}", logging.WARNING)
        return []


def _write_nbt_string(stream, value):
    encoded = value.encode("utf-8")
    stream.write(struct.pack(">H", len(encoded)))
    stream.write(encoded)


def _save_servers_dat(file_path, servers):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.exists(file_path):
            try:
                shutil.copy(file_path, file_path + ".bak")
            except Exception:
                pass

        stream = io.BytesIO()
        stream.write(struct.pack(">b", 10))
        _write_nbt_string(stream, "")

        stream.write(struct.pack(">b", 9))
        _write_nbt_string(stream, "servers")
        stream.write(struct.pack(">b", 10))
        stream.write(struct.pack(">i", len(servers)))

        for server in servers:
            stream.write(struct.pack(">b", 8))
            _write_nbt_string(stream, "name")
            _write_nbt_string(stream, server.get("name", "Minecraft Server"))

            stream.write(struct.pack(">b", 8))
            _write_nbt_string(stream, "ip")
            _write_nbt_string(stream, server.get("ip", ""))

            icon_value = server.get("icon", "")
            if icon_value:
                stream.write(struct.pack(">b", 8))
                _write_nbt_string(stream, "icon")
                _write_nbt_string(stream, icon_value)

            stream.write(struct.pack(">b", 0))

        stream.write(struct.pack(">b", 0))

        with gzip.open(file_path, "wb") as handle:
            handle.write(stream.getvalue())
        return True
    except Exception as exc:
        log(f"保存 servers.dat 失败: {exc}", logging.ERROR)
        return False


def ensure_live_server_entry(mc_version, minecraft_dir):
    snapshot = get_live_session_snapshot()
    if snapshot.get("mode") != "client":
        return False

    target_address = snapshot.get("target_address")
    if not target_address:
        return False

    file_path = os.path.join(minecraft_dir, "versions", mc_version, "servers.dat")
    servers = _parse_servers_dat(file_path)

    display_name = f"Live | {snapshot.get('host_username') or 'EasyTier'}"
    updated = False
    for server in servers:
        if server.get("name") == display_name or server.get("ip") == target_address:
            server["name"] = display_name
            server["ip"] = target_address
            updated = True
            break

    if not updated:
        servers.append({
            "name": display_name,
            "ip": target_address,
        })

    return _save_servers_dat(file_path, servers)


def prepare_launch_context(mc_version, minecraft_dir):
    snapshot = get_live_session_snapshot()
    context = {
        "jvm_args": [],
        "target_address": snapshot.get("target_address", ""),
        "proxy_port": snapshot.get("proxy_port"),
        "mode": snapshot.get("mode", ""),
    }

    if not snapshot.get("running"):
        return context

    if snapshot.get("mode") == "host":
        start_host_log_watch(mc_version, minecraft_dir)
        return context

    if snapshot.get("mode") == "client" and snapshot.get("proxy_port"):
        ensure_live_server_entry(mc_version, minecraft_dir)
        proxy_port = int(snapshot["proxy_port"])
        context["jvm_args"] = [
            "-DsocksProxyHost=127.0.0.1",
            f"-DsocksProxyPort={proxy_port}",
            "-DsocksNonProxyHosts=localhost|127.0.0.1",
            "-Djava.net.preferIPv4Stack=true",
        ]
        return context

    return context


def StartEasytierServer(name, key, use_public_server=False, is_host=True, peer_ip=None):
    network_secret = key.strip() if key and key.strip() else "NoPassWord"
    mode = "host" if is_host else "client"

    result = start_live_session(
        mode=mode,
        network_name=name,
        network_secret=network_secret,
        host_username=name if is_host else "",
        use_public_servers=use_public_server or True,
    )

    if not result.get("success"):
        return i18nText(f"启动失败: {result.get('message', '未知错误')}")

    snapshot = result.get("snapshot") or {}
    if not is_host and peer_ip:
        log(f"兼容模式下忽略旧的 peer_ip 参数: {peer_ip}", logging.INFO)

    virtual_ip = snapshot.get("virtual_ip") or ""
    if virtual_ip:
        return virtual_ip

    if is_host:
        return i18nText("~房主模式已启动，等待虚拟 IP 分配")
    return i18nText("~已尝试连接房主网络，请稍候")


def StopEasytierServer():
    stop_live_session()

