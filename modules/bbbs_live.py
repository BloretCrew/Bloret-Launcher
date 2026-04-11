import requests
import json
import threading
import time
import modules.globals as BLglobals
import modules.config as cfg
from modules.log import log


def _get_base_url():
    return BLglobals.server_ip + ':21111'


def _log_request(method, url, cookies, body=None):
    """调试用：打印请求完整信息"""
    log(f"[Live DEBUG] ===== 请求 =====")
    log(f"[Live DEBUG] {method} {url}")
    log(f"[Live DEBUG] Cookies: {json.dumps(cookies, ensure_ascii=False)}")
    if body is not None:
        log(f"[Live DEBUG] Body: {json.dumps(body, ensure_ascii=False)}")


def _log_response(response):
    """调试用：打印响应完整信息"""
    log(f"[Live DEBUG] ===== 响应 =====")
    log(f"[Live DEBUG] Status: {response.status_code}")
    log(f"[Live DEBUG] Headers: {dict(response.headers)}")
    try:
        log(f"[Live DEBUG] Body: {response.text[:500]}")
    except Exception:
        pass


def _get_session_cookie():
    """从 config.json 读取 bbbs_session 和 bbbs_session_sig，返回 cookies dict"""
    config_data = cfg.read()
    cookies = {}
    session = config_data.get('bbbs_session', '')
    if session:
        cookies['session'] = session
    session_sig = config_data.get('bbbs_session_sig', '')
    if session_sig:
        cookies['session.sig'] = session_sig
    return cookies


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
            return response.json()
        else:
            log(f"[Live] 获取空间列表失败，状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        log(f"[Live] 获取空间列表网络错误: {e}")
        return []


def check_access(space_id):
    """GET /api/live/check-access/:spaceId - 检查是否需要密码"""
    url = f"{_get_base_url()}/api/live/check-access/{space_id}"
    cookies = _get_session_cookie()
    _log_request("GET", url, cookies)
    try:
        response = requests.get(url, cookies=cookies, timeout=10)
        _log_response(response)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        log(f"[Live] 检查访问权限网络错误: {e}")
        return None


def verify_password(space_id, password):
    """POST /api/live/verify-password/:spaceId - 验证空间密码"""
    url = f"{_get_base_url()}/api/live/verify-password/{space_id}"
    cookies = _get_session_cookie()
    _log_request("POST", url, cookies, {"password": password})
    try:
        response = requests.post(url, json={"password": password}, cookies=cookies, timeout=10)
        _log_response(response)
        if response.status_code == 200:
            return response.json()
        return {"success": False}
    except requests.exceptions.RequestException as e:
        log(f"[Live] 验证密码网络错误: {e}")
        return {"success": False}


def send_signal(space_id, signal_data):
    """POST /api/live/signal/:spaceId - 发送信号（聊天、WebRTC 等）"""
    url = f"{_get_base_url()}/api/live/signal/{space_id}"
    cookies = _get_session_cookie()
    _log_request("POST", url, cookies, signal_data)
    try:
        # 确保 Content-Type 为 application/json
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=signal_data, cookies=cookies, headers=headers, timeout=10)
        _log_response(response)
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                log(f"[Live] 响应解析失败,但状态码为 200")
                return {"success": True}
        else:
            # 尝试解析错误响应
            error_detail = response.text[:200]
            log(f"[Live] 发送信号失败，状态码: {response.status_code}, 详情: {error_detail}")
            return None
    except requests.exceptions.RequestException as e:
        log(f"[Live] 发送信号网络错误: {e}")
        return None


def create_space(name):
    """POST /api/live/create - 创建新 Live 空间"""
    url = f"{_get_base_url()}/api/live/create"
    cookies = _get_session_cookie()
    _log_request("POST", url, cookies, {"name": name})
    try:
        response = requests.post(url, json={"name": name}, cookies=cookies, timeout=10)
        _log_response(response)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[Live] 创建空间失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log(f"[Live] 创建空间网络错误: {e}")
        return None


# ==================== SSE Client ====================

class LiveSSEClient:
    """SSE 长连接客户端，接收 Live 空间实时事件"""

    def __init__(self, space_id, on_event_callback):
        self._space_id = space_id
        self._callback = on_event_callback
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        url = f"{_get_base_url()}/api/live/events/{self._space_id}"
        cookies = _get_session_cookie()
        reconnect_delay = 1

        while self._running:
            try:
                with requests.get(url, stream=True, cookies=cookies, timeout=(10, None)) as resp:
                    if resp.status_code != 200:
                        log(f"[Live SSE] 连接失败，状态码: {resp.status_code}")
                        self._callback({"type": "error", "message": f"SSE 连接失败: {resp.status_code}"})
                        break

                    # 确保使用 UTF-8 编码
                    resp.encoding = 'utf-8'
                    resp.raw.read = lambda amt: resp.raw.read(amt, decode_content=True)
                    reconnect_delay = 1
                    event_type = None
                    data_lines = []

                    # 手动读取并解码 UTF-8
                    buffer = ""
                    while self._running:
                        try:
                            # 读取原始字节并解码为 UTF-8
                            chunk = resp.raw.read(4096, decode_content=True)
                            if not chunk:
                                break
                            
                            # 尝试 UTF-8 解码
                            if isinstance(chunk, bytes):
                                text = chunk.decode('utf-8', errors='replace')
                            else:
                                text = chunk
                            
                            buffer += text
                            
                            # 按行处理
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                
                                if not line:
                                    continue
                                
                                if line == "":
                                    # 空行表示事件结束
                                    if data_lines:
                                        data_str = "\n".join(data_lines)
                                        try:
                                            payload = json.loads(data_str)
                                            if event_type:
                                                payload["type"] = event_type
                                            self._callback(payload)
                                        except json.JSONDecodeError as e:
                                            log(f"[Live SSE] JSON 解析失败: {data_str[:100]}, 错误: {e}")
                                        event_type = None
                                        data_lines = []
                                elif line.startswith("event: "):
                                    event_type = line[7:].strip()
                                elif line.startswith("data: "):
                                    data_lines.append(line[6:])
                                elif line.startswith("data:"):
                                    data_lines.append(line[5:])
                        except UnicodeDecodeError as e:
                            log(f"[Live SSE] UTF-8 解码错误: {e}")
                            buffer = ""
                        except Exception as e:
                            if self._running:
                                log(f"[Live SSE] 读取数据错误: {e}")
                            break

            except requests.exceptions.RequestException as e:
                if self._running:
                    log(f"[Live SSE] 连接断开: {e}，{reconnect_delay}秒后重连...")
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 30)
            except Exception as e:
                if self._running:
                    log(f"[Live SSE] 未知错误: {e}")
                    import traceback
                    log(f"[Live SSE] 错误详情: {traceback.format_exc()}")
                    self._callback({"type": "error", "message": str(e)})
                    break


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
