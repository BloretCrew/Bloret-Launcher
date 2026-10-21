import requests
import json
import threading
import logging
import modules.globals as BLglobals


def log(message, level=None):
    try:
        from modules.log import log as app_log
        return app_log(message, level) if level is not None else app_log(message)
    except ImportError:
        logging.getLogger(__name__).log(level or logging.INFO, message)


def _read_config():
    try:
        import modules.config as cfg
        return cfg.read()
    except ImportError:
        return {}


def _get_base_url():
    return BLglobals.server_ip + ':21111'


_LOG_BODY_LIMIT = 500
_SENSITIVE_COOKIE_NAMES = {"session", "session.sig"}
_MAX_CHAT_MESSAGE_LENGTH = 2000


def _redact_cookies(cookies):
    return {
        key: "<redacted>" if key.lower() in _SENSITIVE_COOKIE_NAMES else value
        for key, value in (cookies or {}).items()
    }


def _log_request(method, url, cookies, body=None):
    """记录请求诊断信息，同时隐藏认证 cookie。"""
    log("[Live DEBUG] ===== 请求 =====")
    log(f"[Live DEBUG] {method} {url}")
    log(f"[Live DEBUG] Cookies: {json.dumps(_redact_cookies(cookies), ensure_ascii=False)}")
    if body is not None:
        try:
            body_text = json.dumps(body, ensure_ascii=False)
        except (TypeError, ValueError):
            body_text = repr(body)
        log(f"[Live DEBUG] Body: {body_text[:_LOG_BODY_LIMIT]}")


def _redact_response_headers(headers):
    redacted = {}
    for key, value in dict(headers or {}).items():
        if key.lower() in {"set-cookie", "cookie", "authorization"}:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def _log_response(response):
    """记录有界的响应诊断信息。"""
    log("[Live DEBUG] ===== 响应 =====")
    log(f"[Live DEBUG] Status: {response.status_code}")
    log(f"[Live DEBUG] Headers: {_redact_response_headers(response.headers)}")
    try:
        log(f"[Live DEBUG] Body: {response.text[:_LOG_BODY_LIMIT]}")
    except Exception:
        pass


def _parse_json_response(response, default=None, expected_types=(dict, list)):
    try:
        payload = response.json()
    except (ValueError, TypeError) as e:
        log(f"[Live] 响应 JSON 解析失败: {e}", logging.WARNING)
        return default
    if not isinstance(payload, expected_types):
        log(f"[Live] 响应数据类型异常: {type(payload).__name__}", logging.WARNING)
        return default
    return payload


def validate_chat_message(space_id, message, max_length=_MAX_CHAT_MESSAGE_LENGTH):
    if not space_id:
        return False, "请先加入 Live 空间", ""
    if not isinstance(message, str) or not message.strip():
        return False, "消息不能为空", ""
    normalized = message.strip()
    if len(normalized) > max_length:
        return False, f"消息不能超过 {max_length} 个字符", ""
    return True, "", normalized


def _request_json(method, path, timeout=10, body=None):
    url = f"{_get_base_url()}{path}"
    cookies = _get_session_cookie()
    _log_request(method, url, cookies, body)
    try:
        headers = {"Content-Type": "application/json"} if body is not None else {}
        if method.upper() not in {"GET", "HEAD", "OPTIONS"}:
            headers.update(_csrf_headers())
        response = requests.request(
            method,
            url,
            json=body,
            cookies=cookies,
            headers=headers,
            timeout=timeout,
        )
        _log_response(response)
        payload = _parse_json_response(response)
        if response.ok:
            return payload
        log(f"[Live] 请求失败: {method} {path} -> {response.status_code}", logging.WARNING)
        if isinstance(payload, dict):
            return payload
        return {"success": False, "error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        log(f"[Live] 请求网络错误: {method} {path} -> {e}")
        return None


def _get_session_cookie():
    """从 config.json 读取 BBBS 会话和 CSRF cookies"""
    config_data = _read_config()
    cookies = {}
    session = config_data.get('bbbs_session', '')
    if session:
        cookies['session'] = session
    session_sig = config_data.get('bbbs_session_sig', '')
    if session_sig:
        cookies['session.sig'] = session_sig
    csrf_token = str(config_data.get('bbbs_csrf_token') or '').strip()
    if csrf_token:
        cookies['csrf-token'] = csrf_token
    return cookies


def _csrf_headers():
    token = str(_read_config().get('bbbs_csrf_token') or '').strip()
    if not token:
        return {}
    return {'x-csrf-token': token, 'Origin': _get_base_url()}


# ==================== Space Management ====================

def fetch_space_list():
    """GET /api/live/list - 获取所有 Live 空间列表"""
    url = f"{_get_base_url()}/api/live/list"
    cookies = _get_session_cookie()
    _log_request("GET", url, cookies)
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        _log_response(response)
        if response.status_code == 200:
            return _parse_json_response(response, default=[], expected_types=(list,))
        log(f"[Live] 获取空间列表失败，状态码: {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        log(f"[Live] 获取空间列表网络错误: {e}")
        return []


def check_access(space_id):
    """GET /api/live/check-access/:spaceId - 检查是否需要密码"""
    return _request_json("GET", f"/api/live/check-access/{space_id}")


def verify_password(space_id, password):
    """POST /api/live/verify-password/:spaceId - 验证空间密码"""
    return _request_json("POST", f"/api/live/verify-password/{space_id}", body={"password": password}) or {"success": False}


def send_signal(space_id, signal_data):
    """POST /api/live/signal/:spaceId - 发送信号（聊天、WebRTC 等）"""
    url = f"{_get_base_url()}/api/live/signal/{space_id}"
    cookies = _get_session_cookie()
    _log_request("POST", url, cookies, signal_data)
    try:
        # 确保 Content-Type 为 application/json，并携带 CSRF 令牌
        headers = {"Content-Type": "application/json"}
        headers.update(_csrf_headers())
        response = requests.post(url, json=signal_data, cookies=cookies, headers=headers, timeout=10)
        _log_response(response)
        if response.status_code == 200:
            payload = _parse_json_response(response, default=None, expected_types=(dict,))
            if payload is None:
                log("[Live] 发送信号响应无效")
            return payload
        error_detail = response.text[:200]
        log(f"[Live] 发送信号失败，状态码: {response.status_code}, 详情: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        log(f"[Live] 发送信号网络错误: {e}")
        return None


def create_space(name):
    """POST /api/live/create - 创建新 Live 空间"""
    return _request_json("POST", "/api/live/create", body={"name": name})


def start_space_easytier(space_id):
    """POST /api/live/easytier/start/:spaceId - 由房主开启当前 Live 的 EasyTier 网络"""
    return _request_json("POST", f"/api/live/easytier/start/{space_id}", body={})


def stop_space_easytier(space_id):
    """POST /api/live/easytier/stop/:spaceId - 停止当前 Live 的 EasyTier 网络"""
    return _request_json("POST", f"/api/live/easytier/stop/{space_id}", body={})


def publish_space_easytier_endpoint(space_id, host_virtual_ip, game_port):
    """POST /api/live/easytier/publish/:spaceId - 上报房主虚拟 IP 和局域网端口"""
    return _request_json(
        "POST",
        f"/api/live/easytier/publish/{space_id}",
        body={
            "hostVirtualIp": host_virtual_ip,
            "gamePort": int(game_port),
        },
    )


def get_space_easytier_info(space_id):
    """GET /api/live/easytier/info/:spaceId - 获取当前 Live 的 EasyTier 连接信息"""
    return _request_json("GET", f"/api/live/easytier/info/{space_id}")


# ==================== SSE Client ====================

class LiveSSEClient:
    """SSE 长连接客户端，接收 Live 空间实时事件。"""

    def __init__(self, space_id, on_event_callback):
        self._space_id = space_id
        self._callback = on_event_callback
        self._stop_event = threading.Event()
        self._thread = None
        self._response = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                daemon=True,
                name=f"LiveSSE-{self._space_id}",
            )
            self._thread.start()

    def stop(self, timeout=2.0):
        self._stop_event.set()
        with self._lock:
            response = self._response
            thread = self._thread
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        if thread and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        return not thread or not thread.is_alive()

    def _emit_event(self, event_type, data_lines):
        if not data_lines or self._stop_event.is_set():
            return
        data_str = "\n".join(data_lines)
        try:
            payload = json.loads(data_str)
        except (ValueError, TypeError) as e:
            log(f"[Live SSE] JSON 解析失败: {data_str[:100]}, 错误: {e}")
            return
        if not isinstance(payload, dict):
            log(f"[Live SSE] 忽略非对象事件: {type(payload).__name__}")
            return
        if event_type:
            payload["type"] = event_type
        if not self._stop_event.is_set():
            self._callback(payload)

    def _consume_response(self, response):
        event_type = None
        data_lines = []
        for raw_line in response.iter_lines(decode_unicode=True):
            if self._stop_event.is_set():
                break
            if isinstance(raw_line, bytes):
                line = raw_line.decode("utf-8", errors="replace")
            else:
                line = raw_line or ""
            line = line.rstrip("\r")
            if line == "":
                self._emit_event(event_type, data_lines)
                event_type = None
                data_lines = []
                continue
            if line.startswith(":"):
                continue
            field, separator, value = line.partition(":")
            if not separator:
                continue
            if value.startswith(" "):
                value = value[1:]
            if field == "event":
                event_type = value
            elif field == "data":
                data_lines.append(value)
        self._emit_event(event_type, data_lines)

    def _wait_to_reconnect(self, delay):
        return self._stop_event.wait(delay)

    def _run(self):
        url = f"{_get_base_url()}/api/live/events/{self._space_id}"
        reconnect_delay = 1
        while not self._stop_event.is_set():
            try:
                log(f"[Live SSE] 正在连接 SSE: {url}")
                response = requests.get(
                    url,
                    stream=True,
                    cookies=_get_session_cookie(),
                    timeout=(10, 30),
                )
                with self._lock:
                    self._response = response
                try:
                    log(
                        f"[Live SSE] 连接响应状态码: {response.status_code}, "
                        f"Headers Content-Type: {response.headers.get('Content-Type', 'N/A')}"
                    )
                    if response.status_code != 200:
                        log(f"[Live SSE] 连接失败，状态码: {response.status_code}")
                        if not self._stop_event.is_set():
                            self._callback({"type": "error", "message": f"SSE 连接失败: {response.status_code}"})
                        if self._wait_to_reconnect(reconnect_delay):
                            break
                        reconnect_delay = min(reconnect_delay * 2, 30)
                        continue
                    response.encoding = "utf-8"
                    reconnect_delay = 1
                    self._consume_response(response)
                finally:
                    try:
                        response.close()
                    finally:
                        with self._lock:
                            if self._response is response:
                                self._response = None
                if not self._stop_event.is_set() and self._wait_to_reconnect(reconnect_delay):
                    break
            except requests.exceptions.RequestException as e:
                if self._stop_event.is_set():
                    break
                log(f"[Live SSE] 连接断开: {e}，{reconnect_delay}秒后重连...")
                if self._wait_to_reconnect(reconnect_delay):
                    break
                reconnect_delay = min(reconnect_delay * 2, 30)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log(f"[Live SSE] 未知错误: {e}")
                self._callback({"type": "error", "message": str(e)})
                if self._wait_to_reconnect(reconnect_delay):
                    break
                reconnect_delay = min(reconnect_delay * 2, 30)
        with self._lock:
            self._response = None


# ==================== WebRTC Manager ====================

class LiveWebRTCManager:
    """WebRTC 管理器，处理音视频连接"""

    def __init__(self, space_id, send_signal_func):
        self._space_id = space_id
        self._send_signal = send_signal_func
        self._loop = None
        self._thread = None
        self._peers = {}
        self._audio_enabled = False
        self._video_enabled = False
        self._rtc_available = False

        try:
            import aiortc
            self._rtc_available = True
        except ImportError:
            log("[Live WebRTC] aiortc 未安装，WebRTC 功能不可用")

    def start(self):
        if not self._rtc_available:
            return
        import asyncio
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        import asyncio
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop:
            import asyncio
            for pc in list(self._peers.values()):
                asyncio.run_coroutine_threadsafe(pc.close(), self._loop)
            self._peers.clear()
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._running = False

    def handle_signaling(self, event):
        """处理 WebRTC 信令事件"""
        if not self._rtc_available or not self._loop:
            return
        import asyncio
        asyncio.run_coroutine_threadsafe(self._process_signaling(event), self._loop)

    async def _process_signaling(self, event):
        from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

        event_type = event.get("type", "")
        user_id = event.get("from", event.get("user", ""))

        if event_type == "offer":
            pc = RTCPeerConnection()
            self._peers[user_id] = pc

            @pc.on("track")
            def on_track(track):
                log(f"[Live WebRTC] 收到 track: {track.kind} from {user_id}")

            @pc.on("icecandidate")
            def on_icecandidate(candidate):
                if candidate:
                    self._send_signal(self._space_id, {
                        "target": user_id,
                        "type": "ice-candidate",
                        "payload": {
                            "candidate": candidate.candidate,
                            "sdpMid": candidate.sdpMid,
                            "sdpMLineIndex": candidate.sdpMLineIndex,
                        }
                    })

            sdp = event.get("payload", {}).get("sdp", "")
            await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            self._send_signal(self._space_id, {
                "target": user_id,
                "type": "answer",
                "payload": {"sdp": pc.localDescription.sdp}
            })

        elif event_type == "answer":
            pc = self._peers.get(user_id)
            if pc:
                sdp = event.get("payload", {}).get("sdp", "")
                await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="answer"))

        elif event_type == "ice-candidate":
            pc = self._peers.get(user_id)
            if pc:
                payload = event.get("payload", {})
                candidate = RTCIceCandidate(
                    sdpMid=payload.get("sdpMid", ""),
                    sdpMLineIndex=payload.get("sdpMLineIndex", 0),
                    candidate=payload.get("candidate", ""),
                )
                await pc.addIceCandidate(candidate)

    async def _create_offer(self, user_id):
        """创建 WebRTC Offer 并发送"""
        if not self._rtc_available:
            return
        from aiortc import RTCPeerConnection

        pc = RTCPeerConnection()
        self._peers[user_id] = pc

        @pc.on("icecandidate")
        def on_icecandidate(candidate):
            if candidate:
                self._send_signal(self._space_id, {
                    "target": user_id,
                    "type": "ice-candidate",
                    "payload": {
                        "candidate": candidate.candidate,
                        "sdpMid": candidate.sdpMid,
                        "sdpMLineIndex": candidate.sdpMLineIndex,
                    }
                })

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        self._send_signal(self._space_id, {
            "target": user_id,
            "type": "offer",
            "payload": {"sdp": pc.localDescription.sdp}
        })

    def toggle_audio(self, enabled):
        self._audio_enabled = enabled
        log(f"[Live WebRTC] 音频: {'启用' if enabled else '禁用'}")

    def toggle_video(self, enabled):
        self._video_enabled = enabled
        log(f"[Live WebRTC] 视频: {'启用' if enabled else '禁用'}")
