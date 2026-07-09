"""
资源包 AI Agent Qt 后端

支持：
- OpenCode Zen（内置，免费，无需密钥）
- Bloret PassPort（内置，从 config.json 读取凭据）
- 从 models.dev 动态添加供应商（用户输入密钥）
- 权限系统（写入操作确认）
- AskUserQuestion（AI 主动提问）
- 会话持久化
- 多 Agent 角色
"""

import json
import os
import time
import logging
import threading
import requests
from modules.i18n import i18nText
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication

from .agent_loop import AgentLoop, run_agent_async, AGENT_ROLES

log = logging.getLogger(__name__)


def _send_os_notification(title: str, body: str):
    """发送操作系统级通知（仅在窗口未聚焦时）"""
    try:
        app = QGuiApplication.instance()
        if app and app.activeWindow() is not None:
            return  # 窗口已聚焦，InfoBar 已足够
    except Exception:
        pass

    from modules.notification import send_notification
    send_notification(title, body, category="copilot")


# 工具名称 → 中文描述映射
_TOOL_CN = {
    "read_file": "读取文件",
    "write_file": "写入文件",
    "edit_file": "编辑文件",
    "list_files": "列出文件",
    "search_text": "搜索文本",
    "get_pack_info": "获取资源包信息",
    "analyze_pack": "分析资源包",
    "read_language": "读取语言文件",
    "edit_language": "编辑语言文件",
    "validate_json": "验证 JSON",
    "get_file_tree": "获取文件树",
    "ask_user": "向用户提问",
    "execute_command": "执行命令",
    "execute_command_background": "后台执行命令",
    "spawn_agent": "启动子 Agent",
    "get_mc_reference": "查询 MC 参考",
    "validate_mcmeta_advanced": "验证 pack.mcmeta",
    "create_resource_template": "创建资源模板",
}


def _summarize_agent_result(text: str, tool_calls: list) -> str:
    """生成 Agent 完成后的摘要"""
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

    return "；".join(parts) if parts else i18nText("已完成对话")


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
    """从磁盘加载用户自定义供应商"""
    try:
        if os.path.exists(_PROVIDERS_FILE):
            with open(_PROVIDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"加载自定义供应商失败: {e}")
    return {}


def _save_custom_providers(providers: dict):
    """保存用户自定义供应商到磁盘"""
    try:
        os.makedirs(os.path.dirname(_PROVIDERS_FILE), exist_ok=True)
        with open(_PROVIDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(providers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"保存自定义供应商失败: {e}")


def _fetch_providers_from_models_dev() -> list:
    """从 models.dev 获取供应商列表（仅返回支持 tool_call 的）"""
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

            # 只保留支持 tool_call 的模型
            models = []
            for mid, mdata in models_raw.items():
                if mdata.get("tool_call", False):
                    models.append({
                        "id": mdata.get("id", mid),
                        "name": mdata.get("name", mid),
                        "tool_call": True,
                    })

            if models:  # 只添加有可用模型的供应商
                providers.append({
                    "id": pid,
                    "name": name,
                    "api": api,
                    "doc": doc,
                    "model_count": len(models),
                    "models": models,
                })

        # 按名称排序
        providers.sort(key=lambda p: p["name"].lower())
        return providers
    except Exception as e:
        log.error(f"从 models.dev 获取供应商失败: {e}")
        return []


class AgentBackend(QObject):
    """AI Agent 的 Qt 后端"""

    # ========== 信号 ==========
    textUpdated = Signal(str)
    toolCallStarted = Signal(str, str)
    toolCallFinished = Signal(str, str, str)
    errorOccurred = Signal(str)
    busyChanged = Signal()
    messageAdded = Signal(str, str, str)
    providersChanged = Signal()  # 供应商列表变化

    # 权限系统信号
    permissionRequested = Signal(str, str, str, str)  # (tool_name, args_json, description, reasoning)

    # AskUser 信号
    questionAsked = Signal(str, str, str)  # (question, question_type, options_json)

    # 会话管理信号
    sessionLoaded = Signal()

    # 标题信号
    titleChanged = Signal(str)

    # 状态消息信号
    statusMessage = Signal(str)

    # 角色信号
    roleChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._busy = False
        self._pack_path = ""
        self._history = []
        self._current_text = ""
        self._current_tool_calls = []
        self._had_error = False
        # 从全局 config.json 读取供应商和模型设置
        self._current_provider, self._current_model = self._load_global_ai_settings()

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

        # RPE 编辑器后端引用（用于 git 操作）
        self._rpe_backend = None

    # ========== 全局设置 ==========

    @staticmethod
    def _load_global_ai_settings():
        """从 config.json 读取全局 AI 供应商和模型设置"""
        try:
            import modules.config as cfg
            config_data = cfg.read()
            provider = config_data.get("ai_provider", "bloret_passport")
            model = config_data.get("ai_model", "default")
            return provider, model
        except Exception as e:
            log.warning(f"[Agent] 读取全局 AI 设置失败: {e}")
            return "bloret_passport", "default"

    def _sync_global_settings(self):
        """同步全局 AI 设置（每次交互时检查）"""
        provider, model = self._load_global_ai_settings()
        if provider != self._current_provider or model != self._current_model:
            self._current_provider = provider
            self._current_model = model
            log.info(f"[Agent] 同步全局 AI 设置: provider={provider}, model={model}")

    @Slot(str, str)
    def onGlobalAIProviderChanged(self, provider_key, model_id):
        """响应全局 AI 供应商/模型变化"""
        if self._current_provider != provider_key or self._current_model != model_id:
            self._current_provider = provider_key
            self._current_model = model_id
            self.providersChanged.emit()
            log.info(f"[Agent] 全局 AI 设置已更新: provider={provider_key}, model={model_id}")

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

    # ========== 权限系统 ==========

    @Slot()
    def approvePermission(self):
        """批准当前权限请求"""
        if self._permission_event:
            self._permission_result = True
            self._permission_event.set()

    @Slot()
    def denyPermission(self):
        """拒绝当前权限请求"""
        if self._permission_event:
            self._permission_result = False
            self._permission_event.set()

    def _on_permission_request(self, tool_name: str, description: str) -> bool:
        """权限请求回调（在 Agent 工作线程中调用）"""
        reasoning = self._current_text if self._current_text else ""
        log.info(f"[Agent] 权限请求: {tool_name}, reasoning='{reasoning[:50]}...'")

        # 发送系统通知
        tool_cn = _TOOL_CN.get(tool_name, tool_name)
        _send_os_notification("Copilot 需要授权", f"请求{tool_cn}: {description or tool_cn}")

        # 发送信号到 QML
        self.permissionRequested.emit(tool_name, "", description, reasoning)

        # 等待用户响应
        self._permission_event = threading.Event()
        self._permission_result = False

        # 等待最多 120 秒
        if self._permission_event.wait(timeout=120):
            return self._permission_result
        else:
            log.warning("权限请求超时，默认拒绝")
            return False

    # ========== AskUser ==========

    @Slot(str)
    def answerQuestion(self, answer):
        """回答 AI 的提问"""
        if self._question_event:
            self._question_answer = answer
            self._question_event.set()

    def _on_ask_user(self, question: str, question_type: str = "text", options: list = None) -> str:
        """AskUser 回调（在 Agent 工作线程中调用）"""
        if options is None:
            options = []
        log.info(f"[Agent] 向用户提问: type={question_type}, question='{question[:50]}', options={options}")
        # 发送信号到 QML（用 JSON 字符串传递 options，避免列表转换问题）
        options_json = json.dumps(options, ensure_ascii=False)
        self.questionAsked.emit(question, question_type, options_json)

        # 等待用户回答
        self._question_event = threading.Event()
        self._question_answer = ""

        # 等待最多 120 秒
        if self._question_event.wait(timeout=120):
            log.info(f"[Agent] 用户回答: '{self._question_answer}'")
            return self._question_answer
        else:
            log.warning("[Agent] 用户回答超时")
            return i18nText("用户未回答")
    # ========== 角色管理 ==========

    @Slot(str)
    def setAgentRole(self, role):
        """设置 Agent 角色"""
        if role in AGENT_ROLES:
            if self._agent_role != role:
                self._agent_role = role
                self.roleChanged.emit()
                log.info(f"Agent 角色切换为: {role}")

    @Slot(result=str)
    def getAgentRoles(self):
        """获取可用角色列表"""
        roles = []
        for key, config in AGENT_ROLES.items():
            roles.append({"key": key, "name": config["description"]})
        return json.dumps(roles, ensure_ascii=False)

    # ========== 供应商管理 ==========

    @Slot(result=str)
    def getProviders(self):
        """获取所有供应商列表（内置 + 自定义）"""
        result = []
        # 内置
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
        # 自定义
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
        """获取当前供应商的模型列表"""
        return self._getModelsByKey(self._current_provider)

    @Slot(str, result=str)
    def getModelsFor(self, provider_key):
        """获取指定供应商的模型列表"""
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
        """切换当前供应商"""
        self._current_provider = provider_key
        # 自动选第一个模型
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
        """设置当前模型"""
        self._current_model = model_id
        log.info(f"模型切换为: {model_id}")

    @Slot(str, result=str)
    def getCurrentProvider(self):
        """获取当前供应商 key"""
        return self._current_provider

    @Slot(str, result=str)
    def getCurrentModel(self):
        """获取当前模型 id"""
        return self._current_model

    # ========== models.dev ==========

    @Slot(result=str)
    def fetchModelsDev(self):
        """从 models.dev 获取可用供应商列表"""
        providers = _fetch_providers_from_models_dev()
        return json.dumps(providers, ensure_ascii=False)

    @Slot(str, str, str, result=bool)
    def addProvider(self, provider_id, api_key, display_name=""):
        """添加自定义供应商

        Args:
            provider_id: models.dev 中的供应商 ID
            api_key: 用户输入的 API 密钥
            display_name: 自定义显示名称（可选）
        """
        # 从 models.dev 获取供应商信息
        try:
            resp = requests.get(_MODELS_DEV_API, timeout=15)
            resp.raise_for_status()
            all_providers = resp.json()
        except Exception as e:
            self.errorOccurred.emit(i18nText("获取供应商信息失败: {v0}").replace("{v0}", str(e)))
            return False

        pdata = all_providers.get(provider_id)
        if not pdata:
            self.errorOccurred.emit(i18nText("未找到供应商: {v0}").replace("{v0}", str(provider_id)))
            return False

        api_base = pdata.get("api", "")
        models_raw = pdata.get("models", {})

        # 构建 chat completions URL
        api_url = api_base
        if api_url and not api_url.endswith("/"):
            api_url += "/"
        if "chat/completions" not in api_url:
            api_url += "chat/completions"

        # 只保留支持 tool_call 的模型
        models = []
        for mid, mdata in models_raw.items():
            if mdata.get("tool_call", False):
                models.append({
                    "id": mdata.get("id", mid),
                    "name": mdata.get("name", mid),
                    "tool_call": True,
                })

        if not models:
            self.errorOccurred.emit(
                i18nText("供应商 {v0} 没有支持工具调用的模型").replace(
                    "{v0}", str(pdata.get("name", provider_id))
                )
            )
            return False

        # 保存
        provider_key = provider_id
        self._custom_providers[provider_key] = {
            "id": provider_id,
            "name": display_name or pdata.get("name", provider_id),
            "api": api_url,
            "api_key": api_key,
            "needs_auth": True,
            "builtin": False,
            "models": models,
        }
        _save_custom_providers(self._custom_providers)
        self.providersChanged.emit()
        log.info(f"已添加供应商: {provider_key} ({len(models)} 个模型)")
        return True

    @Slot(str, result=bool)
    def removeProvider(self, provider_key):
        """删除自定义供应商"""
        if provider_key in BUILTIN_PROVIDERS:
            self.errorOccurred.emit(i18nText("不能删除内置供应商"))
            return False
        if provider_key in self._custom_providers:
            del self._custom_providers[provider_key]
            _save_custom_providers(self._custom_providers)
            self.providersChanged.emit()
            return True
        return False

    # ========== 对话 ==========

    @Slot(str)
    def setPackPath(self, path):
        self._pack_path = path

    @Slot('QVariant')
    def setRPEditor(self, rpe):
        """接收编辑器后端引用（用于 git 自动提交）"""
        self._rpe_backend = rpe

    # ========== 项目配置 (.BLRPE/config.json) ==========

    def _get_project_config_path(self) -> str:
        """获取项目配置文件路径"""
        if not self._pack_path:
            return ""
        return os.path.join(self._pack_path, ".BLRPE", "config.json")

    @Slot(str, str, result=str)
    def getProjectSetting(self, key, default=""):
        """读取项目设置"""
        path = self._get_project_config_path()
        if not path or not os.path.exists(path):
            return str(default)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            return str(cfg.get(key, default))
        except Exception:
            return str(default)

    @Slot(str, str)
    def setProjectSetting(self, key, value):
        """写入项目设置"""
        path = self._get_project_config_path()
        if not path:
            return
        try:
            cfg = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            cfg[key] = value
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning(f"保存项目设置失败: {e}")

    @Slot(str)
    def sendMessage(self, text):
        log.info(f"[Agent] sendMessage 调用, busy={self._busy}, pack_path='{self._pack_path}', history_len={len(self._history)}")
        print(f"[Agent DEBUG] sendMessage 调用, busy={self._busy}, pack_path='{self._pack_path}', history_len={len(self._history)}")
        if self._busy:
            log.warning("[Agent] sendMessage 被拒绝: 正忙")
            print("[Agent DEBUG] sendMessage 被拒绝: 正忙")
            return
        if not self._pack_path:
            log.error("[Agent] sendMessage 被拒绝: 未设置资源包路径")
            self.errorOccurred.emit(i18nText("请先打开一个资源包"))
            return

        # 获取 API 配置
        provider = BUILTIN_PROVIDERS.get(self._current_provider) or self._custom_providers.get(self._current_provider)
        if not provider:
            log.error(f"[Agent] 未找到供应商: {self._current_provider}")
            self.errorOccurred.emit(i18nText("未选择供应商"))
            return

        api_url = provider.get("api", "")
        model = self._current_model or (provider.get("models", [{}])[0].get("id", "") if provider.get("models") else "")

        log.info(f"[Agent] 供应商={provider.get('name', '?')}, api_url='{api_url}', model='{model}'")

        if not api_url or not model:
            log.error(f"[Agent] 供应商配置不完整: api_url='{api_url}', model='{model}'")
            self.errorOccurred.emit(i18nText("供应商配置不完整"))
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
                        log.error("[Agent] Bloret PassPort API Key 未配置")
                        self.errorOccurred.emit(i18nText("请先在 Bloret PassPort 的 /ai 页面创建 API Key，并在设置中配置"))
                        return
                    log.info("[Agent] 使用 Bloret PassPort API Key 认证")
                else:
                    log.error(f"[Agent] 供应商 {provider.get('name', '')} 需要 API 密钥但未提供")
                    self.errorOccurred.emit(
                        i18nText("供应商 {v0} 需要 API 密钥").replace(
                            "{v0}", str(provider.get("name", ""))
                        )
                    )
                    return
            else:
                auth_header = f"Bearer {api_key}"
                log.info("[Agent] 使用 API 密钥认证")
        else:
            log.info("[Agent] 无需认证（内置供应商）")

        # 第一条消息时自动生成对话标题（后台线程，不阻塞主线程）
        if not self._title and len(self._history) == 0:
            log.info("[Agent] 首条消息，后台生成对话标题...")

            def _gen_title():
                try:
                    from .agent_loop import generate_title
                    title = generate_title(api_url, auth_header, text, model)
                    self._title = title
                    log.info(f"[Agent] 对话标题生成成功: '{title}'")
                    self.titleChanged.emit(title)
                except Exception as e:
                    log.warning(f"[Agent] 标题生成失败: {e}，使用截断消息作为标题")
                    self._title = text[:15]
                    self.titleChanged.emit(self._title)

            threading.Thread(target=_gen_title, daemon=True).start()

        log.info(f"[Agent] 启动 Agent, 消息: '{text[:50]}...'") if len(text) > 50 else log.info(f"[Agent] 启动 Agent, 消息: '{text}'")
        self._history.append({"role": "user", "content": text})
        # 注意：不在这里 emit messageAdded，因为 QML sendBtn 已经 append 了用户消息
        self._current_text = ""
        self._current_tool_calls = []
        self._had_error = False
        self._busy = True
        self.busyChanged.emit()

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
            on_permission_request=self._on_permission_request,
            on_ask_user=self._on_ask_user,
            model=model,
            role=self._agent_role,
        )
        log.info("[Agent] Agent 线程已启动")

    @Slot()
    def cancelAgent(self):
        if self._agent:
            self._agent.cancel()
        # 同时解除可能阻塞的权限/提问等待
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
        """获取会话保存目录"""
        if not self._pack_path:
            return ""
        session_dir = os.path.join(self._pack_path, ".bloriko_agent")
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    @Slot()
    def saveSession(self):
        """手动保存当前会话"""
        self._save_session()

    def _save_session(self):
        """保存当前会话到文件"""
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
                "history": self._history,
            }

            # 保存带时间戳的文件
            filename = f"history_{timestamp}.json"
            filepath = os.path.join(session_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 同时保存/覆盖 latest.json
            latest_path = os.path.join(session_dir, "latest.json")
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            log.info(f"会话已保存: {filepath}")

            # 清理旧会话（保留最近 10 个）
            self._cleanup_old_sessions(session_dir)
        except Exception as e:
            log.error(f"保存会话失败: {e}")

    def _cleanup_old_sessions(self, session_dir: str, keep: int = 10):
        """清理旧的会话文件"""
        try:
            files = [f for f in os.listdir(session_dir) if f.startswith("history_") and f.endswith(".json")]
            files.sort(reverse=True)
            for old_file in files[keep:]:
                os.remove(os.path.join(session_dir, old_file))
        except Exception as e:
            log.warning(f"清理旧会话失败: {e}")

    @Slot(result=str)
    def getSessionList(self):
        """获取可用会话列表"""
        session_dir = self._get_session_dir()
        if not session_dir:
            return "[]"

        try:
            files = [f for f in os.listdir(session_dir) if f.startswith("history_") and f.endswith(".json")]
            files.sort(reverse=True)

            sessions = []
            for filename in files[:10]:  # 最多返回 10 个
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
            log.error(f"获取会话列表失败: {e}")
            return "[]"

    @Slot(str, result=bool)
    def loadSession(self, filename):
        """加载指定的会话"""
        session_dir = self._get_session_dir()
        if not session_dir:
            return False

        filepath = os.path.join(session_dir, filename)
        if not os.path.exists(filepath):
            self.errorOccurred.emit(i18nText("会话文件不存在: {v0}").replace("{v0}", str(filename)))
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            previous_role = self._agent_role
            self._history = data.get("history", [])
            self._current_provider = data.get("provider", self._current_provider)
            loaded_model = data.get("model", self._current_model)
            # 校验模型是否属于当前供应商，不属于则回退到第一个可用模型
            available = [m["id"] for m in json.loads(self._getModelsByKey(self._current_provider))]
            if available and loaded_model not in available:
                log.info(f"[Agent] 会话模型 {loaded_model} 不在当前供应商中，回退到 {available[0]}")
                self._current_model = available[0]
            else:
                self._current_model = loaded_model
            loaded_role = data.get("role", self._agent_role)
            self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
            self._title = data.get("title", "")
            if self._agent_role != previous_role:
                self.roleChanged.emit()
            self.titleChanged.emit(self._title)

            self.sessionLoaded.emit()
            log.info(f"已加载会话: {filename} ({len(self._history)} 条消息), 模型={self._current_model}")
            return True
        except Exception as e:
            self.errorOccurred.emit(i18nText("加载会话失败: {v0}").replace("{v0}", str(e)))
            return False

    @Slot()
    def loadLatestSession(self):
        """加载最近的会话"""
        session_dir = self._get_session_dir()
        if not session_dir:
            return

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
                    log.info(f"[Agent] 会话模型 {loaded_model} 不在当前供应商中，回退到 {available[0]}")
                    self._current_model = available[0]
                else:
                    self._current_model = loaded_model
                loaded_role = data.get("role", self._agent_role)
                self._agent_role = loaded_role if loaded_role in AGENT_ROLES else next(iter(AGENT_ROLES), self._agent_role)
                self._title = data.get("title", "")
                if self._agent_role != previous_role:
                    self.roleChanged.emit()
                self.titleChanged.emit(self._title)
                self.sessionLoaded.emit()
                log.info(f"已加载最近会话 ({len(self._history)} 条消息), 模型={self._current_model}")
            except Exception as e:
                log.warning(f"加载最近会话失败: {e}")

    @Slot(result=str)
    def getHistoryMessages(self):
        """获取历史消息列表（用于 QML 重建消息模型）"""
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

    # ========== 内部回调 ==========

    def _on_text_chunk(self, text: str):
        self._current_text = text
        log.debug(f"[Agent] 文本更新: {len(text)} 字符")
        self.textUpdated.emit(text)

    def _on_tool_call_start(self, tool_name: str, args_json: str):
        log.info(f"[Agent] 工具调用开始: {tool_name}")
        self.toolCallStarted.emit(tool_name, args_json)

    def _on_tool_call_end(self, tool_name: str, args_json: str, result: str):
        log.info(f"[Agent] 工具调用完成: {tool_name}, 结果长度={len(result)}")
        self._current_tool_calls.append({
            "name": tool_name,
            "arguments": args_json,
            "result": result,
        })
        self.toolCallFinished.emit(tool_name, args_json, result)

    def _on_error(self, error: str):
        log.error(f"[Agent] 错误: {error}")
        self._had_error = True
        print(f"[Agent DEBUG] 错误: {error}")
        body = error
        if self._current_tool_calls:
            last = self._current_tool_calls[-1]
            tool_cn = _TOOL_CN.get(last.get("name", ""), last.get("name", ""))
            body = f"在{tool_cn}时出错: {error}"
        _send_os_notification("Copilot 出错", body)
        self.errorOccurred.emit(error)

    # ========== 自动提交 ==========

    def _get_git(self):
        """获取 git handler"""
        if self._rpe_backend and hasattr(self._rpe_backend, '_git'):
            return self._rpe_backend._git
        return None

    def _auto_commit(self):
        """Agent 完成后自动提交变更"""
        git = self._get_git()
        if not git:
            return
        try:
            status = git.get_status()
            if not status:
                return  # 无变更

            changed_files = list(status.keys())
            commit_msg = self._generate_commit_message(changed_files, status)

            git.stage_all()
            git.commit(commit_msg)
            self.statusMessage.emit(f"已自动提交: {commit_msg}")
            log.info(f"自动提交完成: {commit_msg}")
        except Exception as e:
            log.warning(f"自动提交失败: {e}")

    def _generate_commit_message(self, files: list, status: dict) -> str:
        """使用 LLM 生成 commit message"""
        provider = BUILTIN_PROVIDERS.get(self._current_provider) or self._custom_providers.get(self._current_provider)
        if not provider:
            return i18nText("更新 {v0} 个文件").replace("{v0}", str(len(files)))
        api_url = provider.get("api", "")
        model = self._current_model
        auth_header = ""
        if provider.get("needs_auth", False):
            api_key = provider.get("api_key", "")
            if api_key:
                auth_header = f"Bearer {api_key}"
            elif self._current_provider == "bloret_passport":
                auth_header = _build_bloret_passport_auth()

        status_str = ", ".join(f"{f}({status[f]})" for f in files[:20])
        prompt = f"根据以下文件变更生成一句简洁的中文 git commit message（不超过50字）：\n{status_str}"

        try:
            from .agent_loop import generate_title
            return generate_title(api_url, auth_header, prompt, model)
        except Exception:
            return i18nText("更新 {v0} 个文件").replace("{v0}", str(len(files)))
    @Slot(str, result=str)
    def generateCommitMessage(self, filesJson: str) -> str:
        """供 QML 调用的公开接口：根据文件列表生成提交信息"""
        try:
            files = json.loads(filesJson) if filesJson else []
        except Exception:
            files = []
        status = {}
        for f in files:
            if isinstance(f, dict):
                status[f.get("path", "")] = f.get("status", "M")
            elif isinstance(f, str):
                status[f] = "M"
        return self._generate_commit_message(list(status.keys()), status)

    def _on_done(self):
        log.info(f"[Agent] 完成回调触发, 文本长度={len(self._current_text)}, 工具调用数={len(self._current_tool_calls)}")
        print(f"[Agent DEBUG] 完成回调触发, 文本长度={len(self._current_text)}, 工具调用数={len(self._current_tool_calls)}")
        if not self._had_error:
            _send_os_notification("Copilot 完成", _summarize_agent_result(self._current_text, self._current_tool_calls))
        if self._current_text:
            self._history.append({"role": "assistant", "content": self._current_text})
            # 保存工具调用到历史记录
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
        # 自动保存会话
        log.info("[Agent] 保存会话...")
        self._save_session()
        # 自动提交变更
        log.info("[Agent] 检查是否需要自动提交...")
        self._auto_commit()
        log.info("[Agent] 全部完成")
