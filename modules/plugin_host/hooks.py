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
LAUNCH_ARGS = "launch.args"
LAUNCH_CLASSPATH = "launch.classpath"
LAUNCH_SCRIPT = "launch.script"
LAUNCH_POST = "launch.post"
LAUNCH_EXIT = "launch.exit"
LAUNCH_WINDOW = "launch.window"

# 下载 / 安装
DOWNLOAD_START = "download.start"
DOWNLOAD_PROGRESS = "download.progress"
DOWNLOAD_COMPLETE = "download.complete"
DOWNLOAD_ERROR = "download.error"
DOWNLOAD_POST = "download.post"
DOWNLOAD_RESOLVE_URL = "download.resolve_url"
INSTALL_PRE = "install.pre"
INSTALL_POST = "install.post"
JAVA_INSTALL_PRE = "java.install.pre"
JAVA_INSTALL_POST = "java.install.post"
MRPACK_IMPORT_PRE = "mrpack.import.pre"
MRPACK_IMPORT_POST = "mrpack.import.post"
MRPACK_EXPORT_PRE = "mrpack.export.pre"
MRPACK_EXPORT_POST = "mrpack.export.post"

# 版本 / 内容
VERSION_CREATED = "version.created"
VERSION_DELETED = "version.deleted"
VERSION_RENAMED = "version.renamed"
VERSION_ICON_CHANGED = "version.icon_changed"
CORE_DATA_CHANGED = "core.data.changed"
MODS_LIST = "mods.list"
MODS_TOGGLE = "mods.toggle"
MODS_DELETE = "mods.delete"
MODS_INSTALL_PRE = "mods.install.pre"
MODS_INSTALL_POST = "mods.install.post"
RESOURCEPACK_LIST = "resourcepack.list"
RESOURCEPACK_DELETE = "resourcepack.delete"
RESOURCEPACK_INSTALL = "resourcepack.install"
SERVERS_CHANGED = "servers.changed"

# 账户
ACCOUNT_LOGIN = "account.login"
ACCOUNT_LOGOUT = "account.logout"
ACCOUNT_CHOSEN = "account.chosen"
PASSPORT_SYNC = "passport.sync"
MC_TOKEN_REFRESH = "mc_token.refresh"

# Live / EasyTier
LIVE_JOIN = "live.join"
LIVE_LEAVE = "live.leave"
LIVE_CHAT = "live.chat"
LIVE_EASYTIER_START = "live.easytier.start"
LIVE_EASYTIER_STOP = "live.easytier.stop"
LIVE_EASYTIER_CONNECTED = "live.easytier.connected"
EASYTIER_SESSION_CHANGED = "easytier.session.changed"

# 主题 / UI
THEME_CHANGED = "theme.changed"
UI_PAGE_OPEN = "ui.page.open"

# Agent
AGENT_BLORIKO_MESSAGE = "agent.bloriko.message"
AGENT_BLRPE_MESSAGE = "agent.blrpe.message"

# 工具栏 / 通知 / 配置
TOOLBAR_ACTION = "toolbar.action"
NOTIFY_SEND = "notify.send"
CONFIG_CHANGED = "config.changed"
UPDATE_CHECK = "update.check"
UPDATE_AVAILABLE = "update.available"
PLAYTIME_SESSION_START = "playtime.session.start"
PLAYTIME_SESSION_END = "playtime.session.end"

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
    LAUNCH_ARGS: "launch.hooks",
    LAUNCH_CLASSPATH: "launch.hooks",
    LAUNCH_SCRIPT: "launch.hooks",
    LAUNCH_POST: "launch.hooks",
    LAUNCH_EXIT: "launch.hooks",
    LAUNCH_WINDOW: "launch.hooks",
    DOWNLOAD_START: "download.hooks",
    DOWNLOAD_PROGRESS: "download.hooks",
    DOWNLOAD_COMPLETE: "download.hooks",
    DOWNLOAD_ERROR: "download.hooks",
    DOWNLOAD_POST: "download.hooks",
    DOWNLOAD_RESOLVE_URL: "download.hooks",
    INSTALL_PRE: "download.hooks",
    INSTALL_POST: "download.hooks",
    JAVA_INSTALL_PRE: "java.manage",
    JAVA_INSTALL_POST: "java.manage",
    MRPACK_IMPORT_PRE: "content.write",
    MRPACK_IMPORT_POST: "content.write",
    MRPACK_EXPORT_PRE: "content.read",
    MRPACK_EXPORT_POST: "content.read",
    VERSION_CREATED: "versions.write",
    VERSION_DELETED: "versions.write",
    VERSION_RENAMED: "versions.write",
    VERSION_ICON_CHANGED: "versions.write",
    CORE_DATA_CHANGED: "versions.write",
    MODS_LIST: "mods.read",
    MODS_TOGGLE: "mods.write",
    MODS_DELETE: "mods.write",
    MODS_INSTALL_PRE: "mods.write",
    MODS_INSTALL_POST: "mods.write",
    RESOURCEPACK_LIST: "content.read",
    RESOURCEPACK_DELETE: "content.write",
    RESOURCEPACK_INSTALL: "content.write",
    SERVERS_CHANGED: "content.write",
    ACCOUNT_LOGIN: None,
    ACCOUNT_LOGOUT: None,
    ACCOUNT_CHOSEN: None,
    PASSPORT_SYNC: None,
    MC_TOKEN_REFRESH: None,
    LIVE_JOIN: "live.control",
    LIVE_LEAVE: "live.control",
    LIVE_CHAT: "live.control",
    LIVE_EASYTIER_START: "live.control",
    LIVE_EASYTIER_STOP: "live.control",
    LIVE_EASYTIER_CONNECTED: "live.control",
    EASYTIER_SESSION_CHANGED: "live.control",
    THEME_CHANGED: "ui.theme",
    UI_PAGE_OPEN: None,
    AGENT_BLORIKO_MESSAGE: "agent.bloriko",
    AGENT_BLRPE_MESSAGE: "agent.blrpe",
    TOOLBAR_ACTION: "ui.toolbar",
    NOTIFY_SEND: "notify.send",
    CONFIG_CHANGED: None,
    UPDATE_CHECK: None,
    UPDATE_AVAILABLE: None,
    PLAYTIME_SESSION_START: "stats.read",
    PLAYTIME_SESSION_END: "stats.read",
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
