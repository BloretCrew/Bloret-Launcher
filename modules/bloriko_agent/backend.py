"""
络可 Agent Qt 后端

支持：
- OpenCode Zen（内置，免费，无需密钥）
- 从 models.dev 动态添加供应商（用户输入密钥）
- 权限系统（写入操作确认）
- AskUserQuestion（AI 主动提问）
- 会话持久化
- 记忆系统（MEMORY.md / USER.md）
- 情感系统
"""

import json
import os
import time
import logging
import threading
import requests
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication

from .agent_loop import BlorikoAgentLoop, run_agent_async, AGENT_ROLES
from .memory import MemoryStore

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

# 内置供应商：OpenCode Zen（免费，无需密钥）
BUILTIN_PROVIDERS = {
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
    }
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._busy = False
        self._history = []
        self._current_text = ""
        self._current_tool_calls = []

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

    # ========== 全局设置 ==========

    @staticmethod
    def _load_global_ai_settings():
        """从 config.json 读取全局 AI 供应商和模型设置"""
        try:
            import modules.config as cfg
            config_data = cfg.read()
            provider = config_data.get("ai_provider", "opencode_zen")
            model = config_data.get("ai_model", "deepseek-v4-flash-free")
            return provider, model
        except Exception as e:
            log.warning(f"[Bloriko] 读取全局 AI 设置失败: {e}")
            return "opencode_zen", "deepseek-v4-flash-free"

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
        result = []
        for key, info in BUILTIN_PROVIDERS.items():
            result.append({
                "key": key,
                "name": info["name"],
                "builtin": True,
                "has_key": True,
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
                self.errorOccurred.emit(f"供应商 {provider.get('name', '')} 需要 API 密钥")
                return
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
            self._current_model = data.get("model", self._current_model)
            loaded_role = data.get("role", self._agent_role)
            self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
            self._title = data.get("title", "")
            self._current_emotion = data.get("emotion", "neutral")
            if self._agent_role != previous_role:
                self.roleChanged.emit()
            self.titleChanged.emit(self._title)
            self.emotionChanged.emit(self._current_emotion)

            self.sessionLoaded.emit()
            log.info(f"[Bloriko] 已加载会话: {filename} ({len(self._history)} 条消息)")
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
                self._current_model = data.get("model", self._current_model)
                loaded_role = data.get("role", self._agent_role)
                self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
                self._title = data.get("title", "")
                self._current_emotion = data.get("emotion", "neutral")
                if self._agent_role != previous_role:
                    self.roleChanged.emit()
                self.titleChanged.emit(self._title)
                self.emotionChanged.emit(self._current_emotion)
                self.sessionLoaded.emit()
                log.info(f"[Bloriko] 已加载最近会话 ({len(self._history)} 条消息)")
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
        body = error
        if self._current_tool_calls:
            last = self._current_tool_calls[-1]
            tool_cn = _TOOL_CN.get(last.get("name", ""), last.get("name", ""))
            body = f"在{tool_cn}时出错: {error}"
        _send_os_notification("络可出错", body)
        self.errorOccurred.emit(error)

    def _on_done(self):
        log.info(f"[Bloriko] 完成回调触发, 文本长度={len(self._current_text)}, 工具调用数={len(self._current_tool_calls)}")
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
        log.info("[Bloriko] 全部完成")
