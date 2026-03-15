import requests
import json
import threading
import time
import modules.globals as BLglobals
import modules.config as cfg
from modules.log import log


def _get_base_url():
    return BLglobals.bbbs_server_ip


def _get_session_cookie():
    """从 config.json 读取 bbbs_session，返回 cookies dict"""
    config_data = cfg.read()
    session = config_data.get('bbbs_session', '')
    if session:
        return {'session': session}
    return {}


# ==================== Space Management ====================

def fetch_space_list():
    """GET /api/live/list - 获取所有 Live 空间列表"""
    url = f"{_get_base_url()}/api/live/list"
    cookies = _get_session_cookie()
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
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
    try:
        response = requests.get(url, cookies=cookies, timeout=10)
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
    try:
        response = requests.post(url, json={"password": password}, cookies=cookies, timeout=10)
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
    try:
        response = requests.post(url, json=signal_data, cookies=cookies, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[Live] 发送信号失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log(f"[Live] 发送信号网络错误: {e}")
        return None


def create_space(name):
    """POST /api/live/create - 创建新 Live 空间"""
    url = f"{_get_base_url()}/api/live/create"
    cookies = _get_session_cookie()
    try:
        response = requests.post(url, json={"name": name}, cookies=cookies, timeout=10)
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

                    reconnect_delay = 1
                    event_type = None
                    data_lines = []

                    for line in resp.iter_lines(decode_unicode=True):
                        if not self._running:
                            break

                        if line is None:
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
                                except json.JSONDecodeError:
                                    log(f"[Live SSE] JSON 解析失败: {data_str[:100]}")
                                event_type = None
                                data_lines = []
                        elif line.startswith("event: "):
                            event_type = line[7:]
                        elif line.startswith("data: "):
                            data_lines.append(line[6:])
                        elif line.startswith("data:"):
                            data_lines.append(line[5:])

            except requests.exceptions.RequestException as e:
                if self._running:
                    log(f"[Live SSE] 连接断开: {e}，{reconnect_delay}秒后重连...")
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 30)
            except Exception as e:
                if self._running:
                    log(f"[Live SSE] 未知错误: {e}")
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
