"""
络可 Agent Qt 后端

支持：
- OpenCode Zen（内置，免费，无需密钥）
- Bloret PassPort（内置，从 config.json 读取凭据）
- 从 models.dev 动态添加供应商（用户输入密钥）
- 权限系统（写入操作确认）
- AskUserQuestion（AI 主动提问）
- 会话持久化
- 记忆系统（MEMORY.md / USER.md）
- 情感系统
- 多平台连接器（微信、Telegram、QQ、Discord 等）
"""

import json
import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication

from .agent_loop import BlorikoAgentLoop, run_agent_async, AGENT_ROLES
from .memory import MemoryStore
from .background_review import spawn_background_review_thread

# 多平台连接器框架
from .connectors import CONNECTOR_REGISTRY, get_all_connectors_info_json, BaseConnector

# 微信连接器（保持向后兼容的直接导入）
from .wechat_connector import (
    BlorikoWechatConnector,
    qr_login_step,
    load_config,
    clear_config,
    ILINK_BASE_URL,
    EP_GET_BOT_QR,
    ILINK_APP_ID,
    ILINK_APP_CLIENT_VERSION,
)

log = logging.getLogger(__name__)


def _send_os_notification(title: str, body: str):
    """发送操作系统级通知（仅在窗口未聚焦时）"""
    try:
        app = QGuiApplication.instance()
        if app and app.activeWindow() is not None:
            return
    except Exception:
        pass

    from modules.notification import send_notification
    send_notification(title, body, category="bloriko")


# 工具名称 → 中文描述映射
_TOOL_CN = {
    "read_file": "读取文件",
    "write_file": "写入文件",
    "edit_file": "编辑文件",
    "list_files": "列出文件",
    "search_text": "搜索文本",
    "get_directory_tree": "查看目录树",
    "ask_user": "向用户提问",
    "execute_command": "执行命令",
    "execute_command_background": "后台执行命令",
    "spawn_agent": "启动子 Agent",
    "memory": "管理记忆",
    "set_emotion": "更新情感",
}


def _summarize_agent_result(text: str, tool_calls: list) -> str:
    parts = []
    if tool_calls:
        names = [tc.get("name", "") for tc in tool_calls]
        unique = []
        seen = set()
        for n in names:
            if n and n not in seen:
                seen.add(n)
                unique.append(_TOOL_CN.get(n, n))
        if unique:
            parts.append("使用了 " + "、".join(unique))
    if text:
        snippet = text.strip().split("\n")[0][:80]
        if snippet:
            parts.append(snippet)
    return "；".join(parts) if parts else "已完成对话"


# 持久化路径
try:
    from modules.globals import datapath as _datapath
except ImportError:
    _datapath = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Bloret-Launcher')

_PROVIDERS_FILE = os.path.join(_datapath, 'ai_providers.json')
_MODELS_DEV_API = "https://models.dev/api.json"

# 内置供应商：默认 Bloret PassPort；OpenCode Zen 为免费备用
BUILTIN_PROVIDERS = {
    "bloret_passport": {
        "id": "bloret_passport",
        "name": "Bloret PassPort",
        "api": "https://passport.bloret.net/v1/chat/completions",
        "needs_auth": True,
        "builtin": True,
        "models": [
            {"id": "default", "name": "Claude Fable 5", "tool_call": True},
        ],
    },
    "opencode_zen": {
        "id": "opencode_zen",
        "name": "OpenCode Zen",
        "api": "https://opencode.ai/zen/v1/chat/completions",
        "needs_auth": False,
        "builtin": True,
        "models": [
            {"id": "deepseek-v4-flash-free", "name": "DeepSeek V4 Flash (Free)", "tool_call": True},
            {"id": "mimo-v2.5-free", "name": "Mimo V2.5 (Free)", "tool_call": True},
            {"id": "qwen3.6-plus-free", "name": "Qwen 3.6 Plus (Free)", "tool_call": True},
            {"id": "minimax-m2.5-free", "name": "MiniMax M2.5 (Free)", "tool_call": True},
            {"id": "nemotron-3-super-free", "name": "Nemotron 3 Super (Free)", "tool_call": True},
        ],
    },
}

# 情感状态 → 中文显示映射
EMOTION_DISPLAY = {
    "neutral": "平静",
    "happy": "开心",
    "shy": "害羞",
    "angry": "生气",
    "sad": "难过",
    "excited": "兴奋",
    "curious": "好奇",
}


def _build_bloret_passport_auth() -> str:
    """构建 Bloret PassPort 认证头。

    认证优先级（见 docs/BloretPassPort-AIAPI.md）：
    1. 优先：已登录用户的 OAuth 三段式 Key（Bearer {AppID};{AppSecret};{UserToken}）
    2. 回退：自注册专用 AI API Key（sk- 前缀，存于 Bloret_PassPort_AI_API_Key）
    返回空字符串表示无法认证（未登录且无专用Key）。
    """
    try:
        import modules.globals as BLglobals
        config_data = {}

        # 直接读取 config.json 避免循环导入
        if hasattr(BLglobals, 'config_path') and os.path.exists(BLglobals.config_path):
            with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

        # 优先：已登录用户使用 OAuth 三段式 Key（文档方式二）
        if config_data.get('Bloret_PassPort_Login'):
            user_token = config_data.get('Bloret_PassPort_PassWord', '')
            if user_token:
                masked = user_token[:8] + "..." + user_token[-4:]
                auth = f"Bearer BloretLauncher;s4d56f4a68sd46g54asd46f54a5dsf654asdf546;{user_token}"
                # 完整脱敏打印 Auth 头，方便核对三段式格式是否正确
                head = auth[:40]
                tail = auth[-12:]
                log.info(f"[BloretPassPort] 构建认证头: 长度={len(auth)}, 格式=Bearer{{AppID}};{{AppSecret}};{{UserToken}}")
                log.info(f"[BloretPassPort] AppID=BloretLauncher, AppSecret=s4d56f4a...546, UserToken={masked}")
                log.info(f"[BloretPassPort] 完整Auth头(脱敏): {head}...{tail}")
                return auth

        # 回退：自注册专用 AI API Key（文档方式一，sk- 前缀）
        api_key = config_data.get('Bloret_PassPort_AI_API_Key', '')
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            log.info(f"[BloretPassPort] 使用专用 AI API Key 认证: {masked}")
            return f"Bearer {api_key}"

        log.warning("[BloretPassPort] 未登录且未配置 AI API Key，无法认证")
        return ""
    except Exception as e:
        log.error(f"构建 Bloret PassPort 认证头失败: {e}")
        return ""


def _load_custom_providers() -> dict:
    try:
        if os.path.exists(_PROVIDERS_FILE):
            with open(_PROVIDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"加载自定义供应商失败: {e}")
    return {}


def _save_custom_providers(providers: dict):
    try:
        os.makedirs(os.path.dirname(_PROVIDERS_FILE), exist_ok=True)
        with open(_PROVIDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(providers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"保存自定义供应商失败: {e}")


def _load_global_ai_settings_static():
    """从 config.json 读取全局 AI 供应商和模型设置（模块级，供非 Backend 调用）。"""
    try:
        import modules.config as cfg
        config_data = cfg.read()
        provider = config_data.get("ai_provider", "bloret_passport")
        model = config_data.get("ai_model", "default")
        return provider, model
    except Exception as e:
        log.warning(f"[AI] 读取全局 AI 设置失败: {e}")
        return "bloret_passport", "default"


def resolve_global_ai_config() -> dict:
    """解析当前全局 AI 供应商配置，供 Agent 与一次性 Chat Completions 共用。

    Returns:
        dict: {
            "provider_key": str,
            "model": str,
            "api_url": str,
            "auth_header": str,      # 可为空（免密钥供应商）
            "provider_name": str,
            "error": str | None,     # 无法使用时的人类可读原因
        }
    """
    provider_key, model = _load_global_ai_settings_static()
    custom_providers = _load_custom_providers()
    provider = BUILTIN_PROVIDERS.get(provider_key) or custom_providers.get(provider_key)

    if not provider:
        log.error(f"[AI] 未找到供应商: {provider_key}")
        return {
            "provider_key": provider_key,
            "model": model or "",
            "api_url": "",
            "auth_header": "",
            "provider_name": provider_key,
            "error": f"未找到 AI 供应商: {provider_key}，请在设置中重新选择",
        }

    provider_name = provider.get("name", provider_key)
    api_url = provider.get("api", "")
    models = provider.get("models", []) or []

    # 模型为空或不在列表时回退到供应商第一个模型
    if not model:
        model = models[0].get("id", "") if models else ""
    elif models and not any(m.get("id") == model for m in models):
        fallback = models[0].get("id", model)
        log.warning(f"[AI] 模型 '{model}' 不在供应商 {provider_key} 列表中，回退为 '{fallback}'")
        model = fallback

    if not api_url or not model:
        log.error(f"[AI] 供应商配置不完整: provider={provider_key}, api_url='{api_url}', model='{model}'")
        return {
            "provider_key": provider_key,
            "model": model or "",
            "api_url": api_url or "",
            "auth_header": "",
            "provider_name": provider_name,
            "error": "供应商配置不完整，请在设置中检查 AI 供应商与模型",
        }

    auth_header = ""
    if provider.get("needs_auth", False):
        api_key = provider.get("api_key", "")
        if api_key:
            auth_header = f"Bearer {api_key}"
        elif provider_key == "bloret_passport":
            auth_header = _build_bloret_passport_auth()
            if not auth_header:
                log.error("[AI] Bloret PassPort 认证信息未配置：未找到 API Key 且用户未登录")
                return {
                    "provider_key": provider_key,
                    "model": model,
                    "api_url": api_url,
                    "auth_header": "",
                    "provider_name": provider_name,
                    "error": "请先登录 Bloret PassPort，或在 PassPort /ai 页面创建 API Key 并配置",
                }
        else:
            log.error(f"[AI] 供应商 {provider_name} 需要 API 密钥但未配置")
            return {
                "provider_key": provider_key,
                "model": model,
                "api_url": api_url,
                "auth_header": "",
                "provider_name": provider_name,
                "error": f"供应商 {provider_name} 需要 API 密钥，请在设置中配置",
            }
    else:
        log.info(f"[AI] 供应商 {provider_name} 无需认证")

    log.info(
        f"[AI] 全局配置就绪: provider={provider_key} ({provider_name}), "
        f"model={model}, api={api_url}, auth={'yes' if auth_header else 'no'}"
    )
    return {
        "provider_key": provider_key,
        "model": model,
        "api_url": api_url,
        "auth_header": auth_header,
        "provider_name": provider_name,
        "error": None,
    }


def _fetch_providers_from_models_dev() -> list:
    try:
        resp = requests.get(_MODELS_DEV_API, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        providers = []
        for pid, pdata in data.items():
            name = pdata.get("name", pid)
            api = pdata.get("api", "")
            doc = pdata.get("doc", "")
            models_raw = pdata.get("models", {})

            models = []
            for mid, mdata in models_raw.items():
                if mdata.get("tool_call", False):
                    models.append({
                        "id": mdata.get("id", mid),
                        "name": mdata.get("name", mid),
                        "tool_call": True,
                    })

            if models:
                providers.append({
                    "id": pid,
                    "name": name,
                    "api": api,
                    "doc": doc,
                    "model_count": len(models),
                    "models": models,
                })

        providers.sort(key=lambda p: p["name"].lower())
        return providers
    except Exception as e:
        log.error(f"从 models.dev 获取供应商失败: {e}")
        return []


class BlorikoBackend(QObject):
    """络可 Agent 的 Qt 后端"""

    # ========== 信号 ==========
    textUpdated = Signal(str)
    toolCallStarted = Signal(str, str)
    toolCallFinished = Signal(str, str, str)
    errorOccurred = Signal(str)
    busyChanged = Signal()
    messageAdded = Signal(str, str, str)
    providersChanged = Signal()

    # 权限系统信号
    permissionRequested = Signal(str, str, str, str)

    # AskUser 信号
    questionAsked = Signal(str, str, str)

    # 会话管理信号
    sessionLoaded = Signal()

    # 标题信号
    titleChanged = Signal(str)

    # 状态消息信号
    statusMessage = Signal(str)

    # 角色信号
    roleChanged = Signal()

    # 情感信号
    emotionChanged = Signal(str)

    # ========== 连接器信号（通用） ==========
    connectorStatusChanged = Signal(str, str)       # platform_id, status
    connectorMessageReceived = Signal(str, str, str) # platform_id, sender_id, text
    connectorError = Signal(str, str)                # platform_id, error

    # ========== 微信连接器信号（保持向后兼容） ==========
    wechatStatusChanged = Signal(str)       # connected / disconnected / connecting / error
    wechatQRProgress = Signal(str, str)     # status, progress_text  (QR 登录进度)
    wechatQRUrlChanged = Signal(str)        # 二维码图片 URL
    wechatMessageReceived = Signal(str, str)  # sender_id, text (微信消息到达通知 UI)
    wechatError = Signal(str)               # 错误消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._busy = False
        self._history = []
        self._current_text = ""
        self._current_tool_calls = []
        self._had_error = False

        # 从全局 config.json 读取供应商和模型设置
        self._current_provider, self._current_model = self._load_global_ai_settings()
        log.info(f"[Bloriko] 全局 AI 设置: provider={self._current_provider}, model={self._current_model}")

        # 工作目录
        self._working_dir = os.path.join(_datapath, 'bloriko-agent', 'workspace')
        os.makedirs(self._working_dir, exist_ok=True)

        # 记忆系统
        self._memory_dir = Path(_datapath) / 'bloriko-agent' / 'memory'
        self._memory_store = MemoryStore(self._memory_dir)
        self._memory_store.load_on_init()

        # 加载自定义供应商
        self._custom_providers = _load_custom_providers()

        # 权限系统
        self._permission_event = None
        self._permission_result = False

        # AskUser
        self._question_event = None
        self._question_answer = ""

        # Agent 角色
        self._agent_role = "auto"

        # 对话标题
        self._title = ""

        # 情感状态
        self._current_emotion = "neutral"

        # ========== 多平台连接器 ==========
        self._connectors: dict[str, BaseConnector] = {}
        self._connectors_lock = threading.Lock()
        self._pending_reply: Optional[dict] = None  # {"platform": str, "chat_id": str}

        # 微信连接器（保持向后兼容的快捷引用）
        self._wechat_connector: Optional[BlorikoWechatConnector] = None
        self._wechat_connector_lock = threading.Lock()
        self._pending_wechat_reply: Optional[str] = None  # 待回复的微信 chat_id

        # 自动启动所有已配置的连接器
        self._auto_start_connectors()

    # ========== 全局设置 ==========

    @staticmethod
    def _load_global_ai_settings():
        """从 config.json 读取全局 AI 供应商和模型设置"""
        return _load_global_ai_settings_static()

    def _sync_global_settings(self):
        """同步全局 AI 设置（每次交互时检查）"""
        provider, model = self._load_global_ai_settings()
        if provider != self._current_provider or model != self._current_model:
            self._current_provider = provider
            self._current_model = model
            log.info(f"[Bloriko] 同步全局 AI 设置: provider={provider}, model={model}")

    # ========== 属性 ==========

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=roleChanged)
    def agentRole(self):
        return self._agent_role

    @Property(str, notify=titleChanged)
    def title(self):
        return self._title

    @Property(str, notify=emotionChanged)
    def emotion(self):
        return self._current_emotion

    # ========== 权限系统 ==========

    @Slot()
    def approvePermission(self):
        if self._permission_event:
            self._permission_result = True
            self._permission_event.set()

    @Slot()
    def denyPermission(self):
        if self._permission_event:
            self._permission_result = False
            self._permission_event.set()

    def _on_permission_request(self, tool_name: str, description: str) -> bool:
        reasoning = self._current_text if self._current_text else ""
        log.info(f"[Bloriko] 权限请求: {tool_name}, reasoning='{reasoning[:50]}...'")

        tool_cn = _TOOL_CN.get(tool_name, tool_name)
        _send_os_notification("络可需要授权", f"请求{tool_cn}: {description or tool_cn}")

        self.permissionRequested.emit(tool_name, "", description, reasoning)

        self._permission_event = threading.Event()
        self._permission_result = False

        if self._permission_event.wait(timeout=120):
            return self._permission_result
        else:
            log.warning("权限请求超时，默认拒绝")
            return False

    # ========== AskUser ==========

    @Slot(str)
    def answerQuestion(self, answer):
        if self._question_event:
            self._question_answer = answer
            self._question_event.set()

    def _on_ask_user(self, question: str, question_type: str = "text", options: list = None) -> str:
        if options is None:
            options = []
        log.info(f"[Bloriko] 向用户提问: type={question_type}, question='{question[:50]}'")
        options_json = json.dumps(options, ensure_ascii=False)
        self.questionAsked.emit(question, question_type, options_json)

        self._question_event = threading.Event()
        self._question_answer = ""

        if self._question_event.wait(timeout=120):
            log.info(f"[Bloriko] 用户回答: '{self._question_answer}'")
            return self._question_answer
        else:
            log.warning("[Bloriko] 用户回答超时")
            return "用户未回答"

    # ========== 情感系统 ==========

    def _on_emotion_change(self, emotion: str):
        """情感变化回调（在 Agent 工作线程中调用）"""
        if emotion in EMOTION_DISPLAY and emotion != self._current_emotion:
            self._current_emotion = emotion
            log.info(f"[Bloriko] 情感变化: {emotion} ({EMOTION_DISPLAY[emotion]})")
            self.emotionChanged.emit(emotion)

    @Slot(result=str)
    def getEmotionDisplay(self):
        """获取当前情感状态的中文显示"""
        return EMOTION_DISPLAY.get(self._current_emotion, "平静")

    # ========== 角色管理 ==========

    @Slot(str)
    def setAgentRole(self, role):
        if role in AGENT_ROLES:
            if self._agent_role != role:
                self._agent_role = role
                self.roleChanged.emit()
                log.info(f"Agent 角色切换为: {role}")

    @Slot(result=str)
    def getAgentRoles(self):
        roles = []
        for key, config in AGENT_ROLES.items():
            roles.append({"key": key, "name": config["description"]})
        return json.dumps(roles, ensure_ascii=False)

    # ========== 供应商管理 ==========

    @Slot(result=str)
    def getProviders(self):
        self._custom_providers = _load_custom_providers()
        result = []
        for key, info in BUILTIN_PROVIDERS.items():
            if info.get("needs_auth"):
                has_key = bool(_build_bloret_passport_auth()) if key == "bloret_passport" else True
            else:
                has_key = True
            result.append({
                "key": key,
                "name": info["name"],
                "builtin": True,
                "has_key": has_key,
                "model_count": len(info.get("models", [])),
            })
        for key, info in self._custom_providers.items():
            result.append({
                "key": key,
                "name": info.get("name", key),
                "builtin": False,
                "has_key": bool(info.get("api_key")),
                "model_count": len(info.get("models", [])),
            })
        return json.dumps(result, ensure_ascii=False)

    @Slot(result=str)
    def getModels(self):
        # 每次获取模型时同步全局设置
        self._sync_global_settings()
        return self._getModelsByKey(self._current_provider)

    @Slot(str, result=str)
    def getModelsFor(self, provider_key):
        return self._getModelsByKey(provider_key)

    def _getModelsByKey(self, key):
        if key in BUILTIN_PROVIDERS:
            models = BUILTIN_PROVIDERS[key].get("models", [])
        elif key in self._custom_providers:
            models = self._custom_providers[key].get("models", [])
        else:
            models = []
        return json.dumps(models, ensure_ascii=False)

    @Slot(str)
    def setProvider(self, provider_key):
        self._current_provider = provider_key
        models_json = self._getModelsByKey(provider_key)
        try:
            models = json.loads(models_json)
            if models:
                self._current_model = models[0]["id"]
        except Exception:
            pass
        log.info(f"供应商切换为: {provider_key}, 模型: {self._current_model}")

    @Slot(str)
    def setModel(self, model_id):
        self._current_model = model_id
        log.info(f"模型切换为: {model_id}")

    @Slot(result=str)
    def getCurrentProvider(self):
        return self._current_provider

    @Slot(result=str)
    def getCurrentModel(self):
        return self._current_model

    def _get_current_api_config(self):
        """获取当前供应商的 API URL 和认证头"""
        provider = BUILTIN_PROVIDERS.get(self._current_provider) or self._custom_providers.get(self._current_provider)
        if not provider:
            return "", ""
        api_url = provider.get("api", "")
        auth_header = ""
        if provider.get("needs_auth", False):
            api_key = provider.get("api_key", "")
            if api_key:
                auth_header = f"Bearer {api_key}"
            elif self._current_provider == "bloret_passport":
                auth_header = _build_bloret_passport_auth()
        return api_url, auth_header

    # ========== 对话 ==========

    @Slot(str)
    def sendMessage(self, text):
        log.info(f"[Bloriko] sendMessage 调用, busy={self._busy}")
        if self._busy:
            log.warning("[Bloriko] sendMessage 被拒绝: 正忙")
            return

        # 获取 API 配置
        provider = BUILTIN_PROVIDERS.get(self._current_provider) or self._custom_providers.get(self._current_provider)
        if not provider:
            log.error(f"[Bloriko] 未找到供应商: {self._current_provider}")
            self.errorOccurred.emit("未选择供应商")
            return

        api_url = provider.get("api", "")
        model = self._current_model or (provider.get("models", [{}])[0].get("id", "") if provider.get("models") else "")

        if not api_url or not model:
            log.error(f"[Bloriko] 供应商配置不完整: api_url='{api_url}', model='{model}'")
            self.errorOccurred.emit("供应商配置不完整")
            return

        # 认证
        auth_header = ""
        if provider.get("needs_auth", False):
            api_key = provider.get("api_key", "")
            if not api_key:
                # 内置 Bloret PassPort：从 config.json 自动构建 OAuth 三段式 Token
                if self._current_provider == "bloret_passport":
                    auth_header = _build_bloret_passport_auth()
                    if not auth_header:
                        log.error("[Bloriko] Bloret PassPort 认证信息未配置：未找到 API Key 且用户未登录")
                        self.errorOccurred.emit("请先在 Bloret PassPort 的 /ai 页面创建 API Key，并在设置中配置；或确认已登录 Bloret PassPort")
                        return
                    log.info("[Bloriko] 使用 Bloret PassPort 认证")
                else:
                    self.errorOccurred.emit(f"供应商 {provider.get('name', '')} 需要 API 密钥")
                    return
            else:
                auth_header = f"Bearer {api_key}"
        else:
            log.info("[Bloriko] 无需认证（内置供应商）")

        # 第一条消息时自动生成对话标题
        if not self._title and len(self._history) == 0:
            log.info("[Bloriko] 首条消息，后台生成对话标题...")

            def _gen_title():
                try:
                    from .agent_loop import generate_title
                    title = generate_title(api_url, auth_header, text, model)
                    self._title = title
                    self.titleChanged.emit(title)
                except Exception as e:
                    log.warning(f"[Bloriko] 标题生成失败: {e}")
                    self._title = text[:15]
                    self.titleChanged.emit(self._title)

            threading.Thread(target=_gen_title, daemon=True).start()

        log.info(f"[Bloriko] 启动 Agent, 消息: '{text[:50]}...'")
        self._history.append({"role": "user", "content": text})
        self._current_text = ""
        self._current_tool_calls = []
        self._had_error = False
        self._busy = True
        self.busyChanged.emit()

        self._agent = run_agent_async(
            working_dir=self._working_dir,
            api_url=api_url,
            auth_header=auth_header,
            user_message=text,
            history=self._history[:-1],
            on_text_chunk=self._on_text_chunk,
            on_tool_call_start=self._on_tool_call_start,
            on_tool_call_end=self._on_tool_call_end,
            on_error=self._on_error,
            on_done=self._on_done,
            on_permission_request=self._on_permission_request,
            on_ask_user=self._on_ask_user,
            on_emotion_change=self._on_emotion_change,
            model=model,
            role=self._agent_role,
            memory_store=self._memory_store,
        )
        log.info("[Bloriko] Agent 线程已启动")

    @Slot()
    def cancelAgent(self):
        if self._agent:
            self._agent.cancel()
        if self._permission_event:
            self._permission_result = False
            self._permission_event.set()
        if self._question_event:
            self._question_answer = "操作已取消"
            self._question_event.set()

    @Slot()
    def clearHistory(self):
        self._history.clear()
        self._current_text = ""
        self._current_tool_calls = []
        self._title = ""
        self.titleChanged.emit(self._title)

    @Slot(result=int)
    def getHistoryLength(self):
        return len(self._history)

    # ========== 会话持久化 ==========

    def _get_session_dir(self) -> str:
        session_dir = os.path.join(_datapath, 'bloriko-agent', 'sessions')
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    @Slot()
    def saveSession(self):
        self._save_session()

    def _save_session(self):
        session_dir = self._get_session_dir()
        if not session_dir or not self._history:
            return

        try:
            timestamp = int(time.time())
            session_data = {
                "timestamp": timestamp,
                "title": self._title,
                "provider": self._current_provider,
                "model": self._current_model,
                "role": self._agent_role,
                "emotion": self._current_emotion,
                "history": self._history,
            }

            filename = f"history_{timestamp}.json"
            filepath = os.path.join(session_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            latest_path = os.path.join(session_dir, "latest.json")
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            log.info(f"[Bloriko] 会话已保存: {filepath}")

            self._cleanup_old_sessions(session_dir)
        except Exception as e:
            log.error(f"[Bloriko] 保存会话失败: {e}")

    def _cleanup_old_sessions(self, session_dir: str, keep: int = 10):
        try:
            files = [f for f in os.listdir(session_dir) if f.startswith("history_") and f.endswith(".json")]
            files.sort(reverse=True)
            for old_file in files[keep:]:
                os.remove(os.path.join(session_dir, old_file))
        except Exception as e:
            log.warning(f"[Bloriko] 清理旧会话失败: {e}")

    @Slot(result=str)
    def getSessionList(self):
        session_dir = self._get_session_dir()
        try:
            files = [f for f in os.listdir(session_dir) if f.startswith("history_") and f.endswith(".json")]
            files.sort(reverse=True)

            sessions = []
            for filename in files[:10]:
                filepath = os.path.join(session_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append({
                        "filename": filename,
                        "timestamp": data.get("timestamp", 0),
                        "title": data.get("title", ""),
                        "message_count": len(data.get("history", [])),
                        "model": data.get("model", ""),
                    })
                except Exception:
                    continue

            return json.dumps(sessions, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bloriko] 获取会话列表失败: {e}")
            return "[]"

    @Slot(str, result=bool)
    def loadSession(self, filename):
        session_dir = self._get_session_dir()
        filepath = os.path.join(session_dir, filename)
        if not os.path.exists(filepath):
            self.errorOccurred.emit(f"会话文件不存在: {filename}")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            previous_role = self._agent_role
            self._history = data.get("history", [])
            self._current_provider = data.get("provider", self._current_provider)
            loaded_model = data.get("model", self._current_model)
            available = [m["id"] for m in json.loads(self._getModelsByKey(self._current_provider))]
            if available and loaded_model not in available:
                log.info(f"[Bloriko] 会话模型 {loaded_model} 不在当前供应商中，回退到 {available[0]}")
                self._current_model = available[0]
            else:
                self._current_model = loaded_model
            loaded_role = data.get("role", self._agent_role)
            self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
            self._title = data.get("title", "")
            self._current_emotion = data.get("emotion", "neutral")
            if self._agent_role != previous_role:
                self.roleChanged.emit()
            self.titleChanged.emit(self._title)
            self.emotionChanged.emit(self._current_emotion)

            self.sessionLoaded.emit()
            log.info(f"[Bloriko] 已加载会话: {filename} ({len(self._history)} 条消息), 模型={self._current_model}")
            return True
        except Exception as e:
            self.errorOccurred.emit(f"加载会话失败: {str(e)}")
            return False

    @Slot()
    def loadLatestSession(self):
        session_dir = self._get_session_dir()
        latest_path = os.path.join(session_dir, "latest.json")
        if os.path.exists(latest_path):
            try:
                with open(latest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                previous_role = self._agent_role
                self._history = data.get("history", [])
                self._current_provider = data.get("provider", self._current_provider)
                loaded_model = data.get("model", self._current_model)
                # 校验模型是否属于当前供应商，不属于则回退到第一个可用模型
                available = [m["id"] for m in json.loads(self._getModelsByKey(self._current_provider))]
                if available and loaded_model not in available:
                    log.info(f"[Bloriko] 会话模型 {loaded_model} 不在当前供应商中，回退到 {available[0]}")
                    self._current_model = available[0]
                else:
                    self._current_model = loaded_model
                loaded_role = data.get("role", self._agent_role)
                self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
                self._title = data.get("title", "")
                self._current_emotion = data.get("emotion", "neutral")
                if self._agent_role != previous_role:
                    self.roleChanged.emit()
                self.titleChanged.emit(self._title)
                self.emotionChanged.emit(self._current_emotion)
                self.sessionLoaded.emit()
                log.info(f"[Bloriko] 已加载最近会话 ({len(self._history)} 条消息), 模型={self._current_model}")
            except Exception as e:
                log.warning(f"[Bloriko] 加载最近会话失败: {e}")

    @Slot(result=str)
    def getHistoryMessages(self):
        messages = []
        for msg in self._history:
            role = msg.get("role", "")
            if role == "user":
                messages.append({
                    "role": "user",
                    "content": msg.get("content", ""),
                    "toolName": "", "toolArgs": "", "toolResult": "",
                })
            elif role == "assistant":
                messages.append({
                    "role": "assistant",
                    "content": msg.get("content", ""),
                    "toolName": "", "toolArgs": "", "toolResult": "",
                })
            elif role == "tool_call":
                messages.append({
                    "role": "tool_call",
                    "content": "",
                    "toolName": msg.get("toolName", ""),
                    "toolArgs": msg.get("toolArgs", ""),
                    "toolResult": msg.get("toolResult", ""),
                })
        return json.dumps(messages, ensure_ascii=False)

    # ========== 记忆查看 ==========

    @Slot(result=str)
    def getMemoryContent(self):
        """获取 MEMORY.md 的当前内容（用于 UI 显示）"""
        return self._memory_store.get_all_entries("memory")

    @Slot(result=str)
    def getUserContent(self):
        """获取 USER.md 的当前内容（用于 UI 显示）"""
        return self._memory_store.get_all_entries("user")

    # ========== 全局设置同步 ==========

    @Slot(str, str)
    def onGlobalAIProviderChanged(self, provider_key, model_id):
        """响应全局 AI 供应商/模型变化（由 Backend.globalAIProviderChanged 信号触发）"""
        if self._current_provider != provider_key or self._current_model != model_id:
            self._current_provider = provider_key
            self._current_model = model_id
            self.providersChanged.emit()
            log.info(f"[Bloriko] 全局 AI 设置已更新: provider={provider_key}, model={model_id}")

    # ========== 内部回调 ==========

    def _on_text_chunk(self, text: str):
        self._current_text = text
        self.textUpdated.emit(text)

    def _on_tool_call_start(self, tool_name: str, args_json: str):
        log.info(f"[Bloriko] 工具调用开始: {tool_name}")
        self.toolCallStarted.emit(tool_name, args_json)

    def _on_tool_call_end(self, tool_name: str, args_json: str, result: str):
        log.info(f"[Bloriko] 工具调用完成: {tool_name}, 结果长度={len(result)}")
        self._current_tool_calls.append({
            "name": tool_name,
            "arguments": args_json,
            "result": result,
        })
        self.toolCallFinished.emit(tool_name, args_json, result)

    def _on_error(self, error: str):
        log.error(f"[Bloriko] 错误: {error}")
        self._had_error = True
        body = error
        if self._current_tool_calls:
            last = self._current_tool_calls[-1]
            tool_cn = _TOOL_CN.get(last.get("name", ""), last.get("name", ""))
            body = f"在{tool_cn}时出错: {error}"
        _send_os_notification("络可出错", body)
        self.errorOccurred.emit(error)

    def _on_done(self):
        log.info(f"[Bloriko] 完成回调触发, 文本长度={len(self._current_text)}, 工具调用数={len(self._current_tool_calls)}")
        if not self._had_error:
            _send_os_notification("络可完成了", _summarize_agent_result(self._current_text, self._current_tool_calls))
        if self._current_text:
            self._history.append({"role": "assistant", "content": self._current_text})
            for tc in self._current_tool_calls:
                self._history.append({
                    "role": "tool_call",
                    "toolName": tc["name"],
                    "toolArgs": tc["arguments"],
                    "toolResult": tc["result"],
                })
            self.messageAdded.emit("assistant", self._current_text, json.dumps(self._current_tool_calls, ensure_ascii=False))
        self._busy = False
        self.busyChanged.emit()
        self._agent = None
        log.info("[Bloriko] 保存会话...")
        self._save_session()

        # 后台记忆审查
        if self._history and not self._had_error:
            api_url, auth_header = self._get_current_api_config()
            if api_url:
                spawn_background_review_thread(
                    api_url=api_url,
                    auth_header=auth_header,
                    model=self._current_model,
                    memory_store=self._memory_store,
                    messages_snapshot=list(self._history),
                )

        log.info("[Bloriko] 全部完成")

        # 如果消息来自某个连接器，自动回复
        if self._pending_reply and self._current_text and not self._had_error:
            p = self._pending_reply
            self._pending_reply = None
            connector = self._connectors.get(p["platform"])
            if connector and connector.is_connected:
                log.info("[Connector] 回复消息到 %s chat_id=%s (长度=%d)",
                         p["platform"], p["chat_id"][:8], len(self._current_text))
                sent = connector.send_message_chunks(p["chat_id"], self._current_text)
                if sent > 0:
                    log.info("[Connector] 成功发送 %d 条消息", sent)
            else:
                log.warning("[Connector] %s 连接器未就绪，无法回复", p["platform"])

        # 向后兼容：微信专用回复路径
        if self._pending_wechat_reply and self._current_text and not self._had_error:
            chat_id = self._pending_wechat_reply
            self._pending_wechat_reply = None
            self._send_wechat_reply(chat_id, self._current_text)

    # ========== 多平台连接器管理 ==========

    def _auto_start_connectors(self):
        """启动时自动启动所有已配置的连接器"""
        for platform_id, connector_cls in CONNECTOR_REGISTRY.items():
            try:
                connector = connector_cls(
                    on_message=lambda cid, sid, text, pid=platform_id: self._on_connector_message(pid, cid, sid, text),
                    on_status_change=lambda status, pid=platform_id: self._on_connector_status_change(pid, status),
                    on_error=lambda error, pid=platform_id: self._on_connector_error(pid, error),
                )
                if connector.is_configured():
                    with self._connectors_lock:
                        self._connectors[platform_id] = connector
                    log.info("[Connector] 自动启动 %s 连接器...", connector.display_name)
                    connector.start()
                else:
                    # 即使未配置也注册到字典中（但不启动）
                    with self._connectors_lock:
                        self._connectors[platform_id] = connector
                    log.debug("[Connector] %s 未配置，跳过自动启动", connector.display_name)
            except Exception as e:
                log.error("[Connector] 初始化 %s 连接器失败: %s", platform_id, e)

    def _get_connector(self, platform_id: str) -> Optional[BaseConnector]:
        with self._connectors_lock:
            return self._connectors.get(platform_id)

    def _on_connector_message(self, platform_id: str, chat_id: str, sender_id: str, text: str) -> None:
        """统一连接器消息回调（在各连接器的轮询线程中调用）"""
        log.info("[Connector] 收到 %s 消息 from=%s text='%s'", platform_id, sender_id[:8], text[:50])

        # 通知 UI
        self.connectorMessageReceived.emit(platform_id, sender_id, text)

        # 向后兼容：微信专用信号
        if platform_id == "wechat":
            self.wechatMessageReceived.emit(sender_id, text)

        # 送入 Agent 处理
        self._pending_reply = {"platform": platform_id, "chat_id": chat_id}
        # 向后兼容
        if platform_id == "wechat":
            self._pending_wechat_reply = chat_id

        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self,
            "sendMessageFromConnector",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text),
        )

    @Slot(str)
    def sendMessageFromConnector(self, text: str):
        """从连接器收到的消息，调用 Agent 处理（必须在主线程调用）"""
        self.sendMessage(text)

    def _on_connector_status_change(self, platform_id: str, status: str) -> None:
        """统一连接器状态变化回调"""
        log.info("[Connector] %s 状态变化: %s", platform_id, status)
        self.connectorStatusChanged.emit(platform_id, status)

        # 向后兼容：微信专用信号
        if platform_id == "wechat":
            self.wechatStatusChanged.emit(status)

    def _on_connector_error(self, platform_id: str, error: str) -> None:
        """统一连接器错误回调"""
        log.error("[Connector] %s 错误: %s", platform_id, error)
        self.connectorError.emit(platform_id, error)

        # 向后兼容：微信专用信号
        if platform_id == "wechat":
            self.wechatError.emit(error)

    # ── 通用连接器槽函数 ──

    @Slot(result=str)
    def getAvailableConnectors(self) -> str:
        """获取所有注册连接器的静态信息（JSON 数组）"""
        return get_all_connectors_info_json()

    @Slot(str, result=str)
    def getConnectorStatus(self, platform_id: str) -> str:
        """获取指定连接器的状态"""
        connector = self._get_connector(platform_id)
        if not connector:
            return "disconnected"
        return connector.status

    @Slot(str, result=bool)
    def isConnectorConfigured(self, platform_id: str) -> bool:
        """检查指定连接器是否已配置"""
        connector = self._get_connector(platform_id)
        if not connector:
            return False
        return connector.is_configured()

    @Slot(str)
    def startConnector(self, platform_id: str) -> None:
        """启动指定连接器"""
        connector = self._get_connector(platform_id)
        if connector:
            if connector.start():
                log.info("[Connector] %s 启动成功", platform_id)
            else:
                log.warning("[Connector] %s 启动失败", platform_id)
        else:
            log.warning("[Connector] 未找到连接器: %s", platform_id)

    @Slot(str)
    def stopConnector(self, platform_id: str) -> None:
        """停止指定连接器"""
        connector = self._get_connector(platform_id)
        if connector:
            connector.stop()

    @Slot(str, result=str)
    def getConnectorAccountInfo(self, platform_id: str) -> str:
        """获取指定连接器的账号信息（JSON）"""
        connector = self._get_connector(platform_id)
        if connector:
            info = connector.get_account_info()
            return json.dumps(info, ensure_ascii=False)
        return "{}"

    @Slot(str, str)
    def configureConnectorToken(self, platform_id: str, config_json: str) -> None:
        """配置指定连接器的 Token（JSON 格式的配置）"""
        connector = self._get_connector(platform_id)
        if not connector:
            log.warning("[Connector] 未找到连接器: %s", platform_id)
            return

        try:
            config = json.loads(config_json)
            if connector.save_token_config(config):
                log.info("[Connector] %s 配置已保存", platform_id)
                connector.reload_config()
                connector.start()
            else:
                log.warning("[Connector] %s 配置保存失败", platform_id)
        except json.JSONDecodeError:
            log.error("[Connector] 配置 JSON 解析失败: %s", config_json)

    @Slot(str)
    def clearConnectorConfig(self, platform_id: str) -> None:
        """清除指定连接器的配置并断开"""
        connector = self._get_connector(platform_id)
        if connector:
            connector.clear_config()
        self.connectorStatusChanged.emit(platform_id, "disconnected")
        # 向后兼容
        if platform_id == "wechat":
            self.wechatStatusChanged.emit("disconnected")

    @Slot(str)
    def startConnectorQRLogin(self, platform_id: str) -> None:
        """启动指定连接器的 QR 登录（目前仅微信支持）"""
        if platform_id != "wechat":
            log.warning("[Connector] %s 不支持 QR 登录", platform_id)
            return
        self.startWechatQRLogin()

    @Slot(str)
    def reconnectConnector(self, platform_id: str) -> None:
        """重新连接指定连接器"""
        self.stopConnector(platform_id)
        self.startConnector(platform_id)

    # ========== 微信连接器（保持向后兼容） ==========

    def _create_wechat_connector(self) -> BlorikoWechatConnector:
        """创建微信连接器实例（线程安全）"""
        with self._wechat_connector_lock:
            if self._wechat_connector is None:
                self._wechat_connector = BlorikoWechatConnector(
                    on_message=self._on_wechat_message,
                    on_status_change=self._on_wechat_status_change,
                    on_error=self._on_wechat_error,
                )
                # 也注册到通用连接器字典
                with self._connectors_lock:
                    self._connectors["wechat"] = self._wechat_connector
            return self._wechat_connector

    def _get_wechat_connector(self) -> Optional[BlorikoWechatConnector]:
        with self._wechat_connector_lock:
            return self._wechat_connector

    def _on_wechat_message(self, chat_id: str, sender_id: str, text: str) -> None:
        """微信消息到达回调（在轮询线程中调用）"""
        log.info("[WeChat] 收到消息 from=%s text='%s'", sender_id[:8], text[:50])

        # 通知 UI
        self.wechatMessageReceived.emit(sender_id, text)

        # 送入 Agent 处理
        self._pending_wechat_reply = chat_id
        # 使用 QMetaObject.invokeMethod 确保在主线程调用 sendMessage
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG

        QMetaObject.invokeMethod(
            self,
            "sendMessageFromWechat",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text),
        )

    @Slot(str)
    def sendMessageFromWechat(self, text: str):
        """从微信收到的消息，调用 Agent 处理（必须在主线程调用）"""
        self.sendMessage(text)

    def _on_wechat_status_change(self, status: str) -> None:
        """微信连接状态变化回调"""
        log.info("[WeChat] 状态变化: %s", status)
        self.wechatStatusChanged.emit(status)

    def _on_wechat_error(self, error: str) -> None:
        """微信错误回调"""
        log.error("[WeChat] 错误: %s", error)
        self.wechatError.emit(error)

    def _send_wechat_reply(self, chat_id: str, text: str) -> None:
        """发送 Agent 回复到微信（在 _on_done 中调用）"""
        connector = self._get_wechat_connector()
        if not connector or not connector.is_connected:
            log.warning("[WeChat] 连接器未就绪，无法回复")
            return

        log.info("[WeChat] 回复消息到 chat_id=%s (长度=%d)", chat_id[:8], len(text))

        # 先发文字，再发媒体（如果有）
        sent = connector.send_message_chunks(chat_id, text)
        if sent > 0:
            log.info("[WeChat] 成功发送 %d 条消息", sent)
        else:
            log.warning("[WeChat] 消息发送失败")

    # ── Qt 槽函数 ──

    @Slot(result=str)
    def getWechatStatus(self) -> str:
        """获取微信连接状态"""
        connector = self._get_wechat_connector()
        if not connector:
            return BlorikoWechatConnector.STATUS_DISCONNECTED
        return connector.status

    @Slot(result=bool)
    def isWechatConfigured(self) -> bool:
        """检查是否已配置微信凭据"""
        return bool(load_config() is not None)

    @Slot()
    def startWechatConnector(self):
        """启动微信连接器"""
        connector = self._create_wechat_connector()
        if connector.start():
            log.info("[WeChat] 连接器启动成功")
        else:
            log.warning("[WeChat] 连接器启动失败")

    @Slot()
    def stopWechatConnector(self):
        """停止微信连接器"""
        connector = self._get_wechat_connector()
        if connector:
            connector.stop()

    @Slot(result=str)
    def getWechatAccountInfo(self) -> str:
        """获取微信账号信息（JSON）"""
        connector = self._get_wechat_connector()
        if connector:
            info = connector.get_account_info()
        else:
            saved = load_config()
            if saved:
                info = {
                    "account_id": saved.get("account_id", ""),
                    "user_id": saved.get("user_id", ""),
                    "base_url": saved.get("base_url", ""),
                    "connected": False,
                }
            else:
                info = {"account_id": "", "user_id": "", "base_url": "", "connected": False}
        return json.dumps(info, ensure_ascii=False)

    @Slot()
    def clearWechatConfig(self):
        """清除微信配置并断开"""
        connector = self._get_wechat_connector()
        if connector:
            connector.clear_config()
        else:
            clear_config()
        self.wechatStatusChanged.emit(BlorikoWechatConnector.STATUS_DISCONNECTED)

    @Slot()
    def startWechatQRLogin(self):
        """在后台线程中启动微信 QR 登录流程"""
        connector = self._create_wechat_connector()

        def _qr_login_thread():
            """QR 登录线程"""
            try:
                self.wechatQRProgress.emit("connecting", "正在获取二维码...")

                # QR URL 回调 → 发射信号给 UI
                def on_qr_url(url: str):
                    self.wechatQRUrlChanged.emit(url)

                # 状态更新回调 → 发射信号给 UI
                def on_status_update(status: str, progress: str):
                    self.wechatQRProgress.emit(status, progress)

                # 执行 QR 登录（内部完成获取二维码 + 轮询 + 保存凭据）
                result = qr_login_step(
                    timeout_seconds=480,
                    on_qr_url=on_qr_url,
                    on_status_update=on_status_update,
                )

                if result and result.get("status") == "confirmed":
                    # 登录成功后重新加载凭据再启动连接器
                    connector.reload_config()
                    self._on_wechat_status_change(BlorikoWechatConnector.STATUS_CONNECTING)
                    connector.start()
                else:
                    self._on_wechat_status_change(BlorikoWechatConnector.STATUS_DISCONNECTED)

            except Exception as e:
                log.error("QR 登录异常: %s", e)
                self.wechatQRProgress.emit("error", f"登录异常: {e}")
                self._on_wechat_status_change(BlorikoWechatConnector.STATUS_DISCONNECTED)

        thread = threading.Thread(target=_qr_login_thread, daemon=True, name="wechat-qr-login")
        thread.start()

    @Slot()
    def reconnectWechat(self):
        """重新连接微信"""
        self.stopWechatConnector()
        self.startWechatConnector()
