"""
资源包 AI Agent Qt 后端

将 AgentLoop 桥接到 QML，通过信号/槽实现跨线程通信。
支持多个 AI 提供商（Bloriko、OpenCode Zen 等）。
"""

import json
import logging
import requests
from PySide6.QtCore import QObject, Signal, Slot, Property

from .agent_loop import AgentLoop, run_agent_async

log = logging.getLogger(__name__)

# ========== AI 提供商配置 ==========

PROVIDERS = {
    "bloriko": {
        "name": "Bloriko",
        "api_url": "http://123.129.241.101:20000/v1/chat/completions",
        "model": "Bloriko",
        "needs_auth": True,
        "app_id": "BloretLauncher",
        "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546",
    },
    "opencode_zen": {
        "name": "OpenCode Zen",
        "api_url": "https://opencode.ai/zen/v1/chat/completions",
        "model": "",  # 由用户选择
        "needs_auth": False,
    },
}

# OpenCode Zen 免费模型列表
OPENCODE_ZEN_FREE_MODELS = [
    {"id": "deepseek-v4-flash-free", "name": "DeepSeek V4 Flash (Free)"},
    {"id": "mimo-v2.5-free", "name": "Mimo V2.5 (Free)"},
    {"id": "qwen3.6-plus-free", "name": "Qwen 3.6 Plus (Free)"},
    {"id": "minimax-m2.5-free", "name": "MiniMax M2.5 (Free)"},
    {"id": "nemotron-3-super-free", "name": "Nemotron 3 Super (Free)"},
]


def _build_auth_header(provider_key: str, user_token: str = "") -> str:
    """构建认证头"""
    provider = PROVIDERS.get(provider_key, {})
    if not provider.get("needs_auth", False):
        return ""
    app_id = provider.get("app_id", "")
    app_secret = provider.get("app_secret", "")
    return f"Bearer {app_id};{app_secret};{user_token}"


class AgentBackend(QObject):
    """AI Agent 的 Qt 后端，暴露给 QML"""

    # ========== 信号 ==========

    # 流式文本更新 (accumulated_text)
    textUpdated = Signal(str)

    # 工具调用开始 (tool_name, arguments_json)
    toolCallStarted = Signal(str, str)

    # 工具调用结束 (tool_name, arguments_json, result)
    toolCallFinished = Signal(str, str, str)

    # 错误消息
    errorOccurred = Signal(str)

    # Agent 忙碌状态变化
    busyChanged = Signal()

    # 一条完整消息 (role, content, tool_calls_json)
    messageAdded = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._busy = False
        self._pack_path = ""
        self._history = []
        self._current_text = ""
        self._current_tool_calls = []
        self._provider = "opencode_zen"  # 默认使用 OpenCode Zen
        self._model = "deepseek-v4-flash-free"  # 默认模型

    # ========== 属性 ==========

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=busyChanged)
    def currentProvider(self):
        return self._provider

    @Property(str, notify=busyChanged)
    def currentModel(self):
        return self._model

    # ========== 槽函数 ==========

    @Slot(str)
    def setPackPath(self, path):
        """设置当前资源包路径"""
        self._pack_path = path
        log.info(f"Agent pack path set to: {path}")

    @Slot(str)
    def setProvider(self, provider_key):
        """设置 AI 提供商"""
        if provider_key in PROVIDERS:
            self._provider = provider_key
            log.info(f"Agent provider set to: {provider_key}")

    @Slot(str)
    def setModel(self, model_id):
        """设置模型"""
        self._model = model_id
        log.info(f"Agent model set to: {model_id}")

    @Slot(result=str)
    def getProviders(self):
        """获取可用提供商列表"""
        result = []
        for key, info in PROVIDERS.items():
            result.append({"key": key, "name": info["name"]})
        return json.dumps(result, ensure_ascii=False)

    @Slot(result=str)
    def getModels(self):
        """获取当前提供商的可用模型列表"""
        if self._provider == "opencode_zen":
            return json.dumps(OPENCODE_ZEN_FREE_MODELS, ensure_ascii=False)
        # Bloriko 只有一个模型
        return json.dumps([{"id": "Bloriko", "name": "Bloriko"}], ensure_ascii=False)

    @Slot(str)
    def sendMessage(self, text):
        """发送用户消息并启动 Agent"""
        if self._busy:
            log.warning("Agent 正在运行中，忽略新消息")
            return

        if not self._pack_path:
            self.errorOccurred.emit("请先打开一个资源包")
            return

        # 获取 API 配置
        provider = PROVIDERS.get(self._provider, {})
        api_url = provider.get("api_url", "")
        model = self._model or provider.get("model", "")

        if not api_url:
            self.errorOccurred.emit("未配置 AI 提供商")
            return

        # 构建认证头
        auth_header = ""
        if provider.get("needs_auth", False):
            try:
                import modules.config as cfg
                config = cfg.read()
                if not config.get("Bloret_PassPort_Login", False):
                    self.errorOccurred.emit("请先登录 Bloret PassPort 以使用 Bloriko AI")
                    return
                user_token = config.get("Bloret_PassPort_PassWord", "")
                if not user_token:
                    self.errorOccurred.emit("用户 token 为空，请重新登录")
                    return
                auth_header = _build_auth_header(self._provider, user_token)
            except Exception as e:
                self.errorOccurred.emit(f"读取配置失败: {str(e)}")
                return

        # 将用户消息加入历史
        self._history.append({"role": "user", "content": text})
        self.messageAdded.emit("user", text, "[]")

        # 重置当前状态
        self._current_text = ""
        self._current_tool_calls = []

        # 设置忙碌状态
        self._busy = True
        self.busyChanged.emit()

        # 启动 Agent
        self._agent = run_agent_async(
            pack_path=self._pack_path,
            api_url=api_url,
            auth_header=auth_header,
            user_message=text,
            history=self._history[:-1],
            on_text_chunk=self._on_text_chunk,
            on_tool_call_start=self._on_tool_call_start,
            on_tool_call_end=self._on_tool_call_end,
            on_error=self._on_error,
            on_done=self._on_done,
            model=model,
        )

    @Slot()
    def cancelAgent(self):
        """取消正在运行的 Agent"""
        if self._agent:
            self._agent.cancel()
            log.info("Agent 取消请求已发送")

    @Slot()
    def clearHistory(self):
        """清除对话历史"""
        self._history.clear()
        self._current_text = ""
        self._current_tool_calls = []
        log.info("Agent 对话历史已清除")

    @Slot(result=int)
    def getHistoryLength(self):
        """获取历史消息数量"""
        return len(self._history)

    # ========== 内部回调 ==========

    def _on_text_chunk(self, text: str):
        self._current_text = text
        self.textUpdated.emit(text)

    def _on_tool_call_start(self, tool_name: str, args_json: str):
        self.toolCallStarted.emit(tool_name, args_json)

    def _on_tool_call_end(self, tool_name: str, args_json: str, result: str):
        self._current_tool_calls.append({
            "name": tool_name,
            "arguments": args_json,
            "result": result,
        })
        self.toolCallFinished.emit(tool_name, args_json, result)

    def _on_error(self, error: str):
        self.errorOccurred.emit(error)

    def _on_done(self):
        if self._current_text:
            assistant_msg = {"role": "assistant", "content": self._current_text}
            self._history.append(assistant_msg)
            self.messageAdded.emit("assistant", self._current_text, json.dumps(self._current_tool_calls, ensure_ascii=False))

        self._busy = False
        self.busyChanged.emit()
        self._agent = None
