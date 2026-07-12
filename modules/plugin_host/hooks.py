"""标准钩子名称常量与调用封装。"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from modules.log import log

# 生命周期
ON_ENABLE = "on_enable"
ON_DISABLE = "on_disable"
ON_LOAD = "on_load"
ON_UNLOAD = "on_unload"

# 应用
APP_READY = "app.ready"
APP_QUIT = "app.quit"

# 启动
LAUNCH_PRE = "launch.pre"
LAUNCH_JVM_ARGS = "launch.jvm_args"
LAUNCH_ENV = "launch.env"
LAUNCH_POST = "launch.post"
LAUNCH_EXIT = "launch.exit"

# 下载
DOWNLOAD_START = "download.start"
DOWNLOAD_PROGRESS = "download.progress"
DOWNLOAD_COMPLETE = "download.complete"
DOWNLOAD_ERROR = "download.error"
DOWNLOAD_POST = "download.post"

# 账户
ACCOUNT_LOGIN = "account.login"
ACCOUNT_LOGOUT = "account.logout"
PASSPORT_SYNC = "passport.sync"

# 主题 / UI
THEME_CHANGED = "theme.changed"
UI_PAGE_OPEN = "ui.page.open"

# Agent
AGENT_BLORIKO_MESSAGE = "agent.bloriko.message"
AGENT_BLRPE_MESSAGE = "agent.blrpe.message"

# 工具栏
TOOLBAR_ACTION = "toolbar.action"

# 配置
CONFIG_CHANGED = "config.changed"

# 权限要求（钩子名 -> 所需权限，None 表示不需要特殊权限）
HOOK_PERMISSIONS: Dict[str, Optional[str]] = {
    ON_ENABLE: None,
    ON_DISABLE: None,
    ON_LOAD: None,
    ON_UNLOAD: None,
    APP_READY: None,
    APP_QUIT: None,
    LAUNCH_PRE: "launch.hooks",
    LAUNCH_JVM_ARGS: "launch.hooks",
    LAUNCH_ENV: "launch.hooks",
    LAUNCH_POST: "launch.hooks",
    LAUNCH_EXIT: "launch.hooks",
    DOWNLOAD_START: "download.hooks",
    DOWNLOAD_PROGRESS: "download.hooks",
    DOWNLOAD_COMPLETE: "download.hooks",
    DOWNLOAD_ERROR: "download.hooks",
    DOWNLOAD_POST: "download.hooks",
    ACCOUNT_LOGIN: None,
    ACCOUNT_LOGOUT: None,
    PASSPORT_SYNC: None,
    THEME_CHANGED: "ui.theme",
    UI_PAGE_OPEN: None,
    AGENT_BLORIKO_MESSAGE: "agent.bloriko",
    AGENT_BLRPE_MESSAGE: "agent.blrpe",
    TOOLBAR_ACTION: "ui.toolbar",
    CONFIG_CHANGED: None,
}


def parse_hook_ref(ref: str) -> Optional[tuple]:
    """解析 'module:func' 或 'module.func' 形式的钩子引用。"""
    if not ref or not isinstance(ref, str):
        return None
    ref = ref.strip()
    if ":" in ref:
        mod, _, func = ref.partition(":")
        return mod.strip(), func.strip()
    if "." in ref:
        mod, _, func = ref.rpartition(".")
        return mod.strip(), func.strip()
    return None


def safe_call(fn: Callable, *args, plugin_id: str = "?", hook: str = "?", **kwargs) -> Any:
    """安全调用钩子，捕获异常并打日志。"""
    try:
        log(f"[PluginHost] 调用钩子 {hook} @ {plugin_id}")
        return fn(*args, **kwargs)
    except Exception as e:
        log(f"[PluginHost] 钩子 {hook} @ {plugin_id} 失败: {e}")
        return None
