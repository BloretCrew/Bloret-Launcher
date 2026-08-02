"""插件权限枚举与校验。"""

from __future__ import annotations

from typing import Iterable, List, Set

# 所有已定义权限（spec 2.0.0）
ALL_PERMISSIONS: Set[str] = {
    # UI（safe 为主）
    "ui.nav",
    "ui.theme",
    "ui.settings",
    "ui.toolbar",
    "ui.home",
    "ui.tools",
    "ui.cores",
    "ui.mods",
    "ui.download",
    "ui.live",
    "ui.passport",
    "ui.bbbs",
    "ui.stats",
    "ui.info",
    "ui.bloriko",
    "ui.rpe",
    "ui.multiplayer",
    "ui.tray",
    "ui.hotkey",
    # 启动 / 下载
    "launch.hooks",
    "launch.control",
    "launch.items",
    "download.hooks",
    "download.control",
    "download.source",
    # 内容
    "versions.read",
    "versions.write",
    "mods.read",
    "mods.write",
    "mods.source",
    "content.read",
    "content.write",
    # 账户 / Live
    "accounts.read",
    "accounts.write",
    "live.control",
    # Agent / 通知
    "agent.bloriko",
    "agent.blrpe",
    "agent.provider",
    "notify.send",
    "notify.channel",
    # 系统
    "config.read",
    "config.write",
    "fs.datapath",
    "net.http",
    "process.exec",
    "web.routes",
    "java.manage",
    "protocol.handle",
    "stats.read",
}

# 安装时默认授予的低风险权限（仍会在 UI 中展示）
DEFAULT_SAFE_PERMISSIONS: Set[str] = {
    "ui.nav",
    "ui.theme",
    "ui.settings",
    "ui.toolbar",
    "ui.home",
    "ui.tools",
    "ui.cores",
    "ui.mods",
    "ui.download",
    "ui.live",
    "ui.passport",
    "ui.bbbs",
    "ui.stats",
    "ui.info",
    "ui.bloriko",
    "ui.rpe",
    "ui.multiplayer",
    "config.read",
    "versions.read",
    "mods.read",
    "content.read",
    "accounts.read",
    "stats.read",
    "notify.send",
}

# 高风险权限（需要用户明确授权）
HIGH_RISK_PERMISSIONS: Set[str] = {
    "ui.tray",
    "ui.hotkey",
    "launch.hooks",
    "launch.control",
    "launch.items",
    "download.hooks",
    "download.control",
    "download.source",
    "versions.write",
    "mods.write",
    "mods.source",
    "content.write",
    "accounts.write",
    "live.control",
    "agent.bloriko",
    "agent.blrpe",
    "agent.provider",
    "notify.channel",
    "config.write",
    "fs.datapath",
    "net.http",
    "process.exec",
    "web.routes",
    "java.manage",
    "protocol.handle",
}

# 权限元数据：label 为 i18n 源文案（中文 key，与 lang/*.json texts 对齐）
PERMISSION_META = {
    "ui.nav": {"label": "添加导航页", "risk": "safe"},
    "ui.theme": {"label": "修改主题", "risk": "safe"},
    "ui.settings": {"label": "添加设置项", "risk": "safe"},
    "ui.toolbar": {"label": "扩展 Minecraft 小工具栏", "risk": "safe"},
    "ui.home": {"label": "扩展主页卡片", "risk": "safe"},
    "ui.tools": {"label": "扩展小工具页卡片", "risk": "safe"},
    "ui.cores": {"label": "扩展核心管理面板", "risk": "safe"},
    "ui.mods": {"label": "扩展 Mods 页面板", "risk": "safe"},
    "ui.download": {"label": "扩展下载页面板", "risk": "safe"},
    "ui.live": {"label": "扩展 Live 面板", "risk": "safe"},
    "ui.passport": {"label": "扩展 PassPort 页面板", "risk": "safe"},
    "ui.bbbs": {"label": "扩展 BBBS 页面板", "risk": "safe"},
    "ui.stats": {"label": "扩展统计页面板", "risk": "safe"},
    "ui.info": {"label": "扩展信息页面板", "risk": "safe"},
    "ui.bloriko": {"label": "扩展络可页面板", "risk": "safe"},
    "ui.rpe": {"label": "扩展资源包编辑器面板", "risk": "safe"},
    "ui.multiplayer": {"label": "扩展联机页面板", "risk": "safe"},
    "ui.tray": {"label": "扩展系统托盘菜单", "risk": "high"},
    "ui.hotkey": {"label": "注册全局热键", "risk": "high"},
    "launch.hooks": {"label": "拦截/修改游戏启动", "risk": "high"},
    "launch.control": {"label": "控制游戏启动与进程", "risk": "high"},
    "launch.items": {"label": "注册自定义启动项", "risk": "high"},
    "download.hooks": {"label": "拦截下载/安装流程", "risk": "high"},
    "download.control": {"label": "控制下载任务", "risk": "high"},
    "download.source": {"label": "注册自定义下载源", "risk": "high"},
    "versions.read": {"label": "读取版本列表", "risk": "safe"},
    "versions.write": {"label": "修改或删除版本", "risk": "high"},
    "mods.read": {"label": "读取 Mods 列表", "risk": "safe"},
    "mods.write": {"label": "安装/启用/删除 Mods", "risk": "high"},
    "mods.source": {"label": "注册 Mods 内容源", "risk": "high"},
    "content.read": {"label": "读取资源包/服务器等", "risk": "safe"},
    "content.write": {"label": "修改资源包/服务器等", "risk": "high"},
    "accounts.read": {"label": "读取账户摘要", "risk": "safe"},
    "accounts.write": {"label": "切换或管理账户", "risk": "high"},
    "live.control": {"label": "控制 Live / EasyTier", "risk": "high"},
    "agent.bloriko": {"label": "扩展络可 Agent", "risk": "high"},
    "agent.blrpe": {"label": "扩展 Blora Agent", "risk": "high"},
    "agent.provider": {"label": "注册自定义 AI 供应商", "risk": "high"},
    "notify.send": {"label": "发送系统通知", "risk": "safe"},
    "notify.channel": {"label": "注册通知渠道", "risk": "high"},
    "config.read": {"label": "读取启动器配置", "risk": "safe"},
    "config.write": {"label": "写入启动器配置", "risk": "high"},
    "fs.datapath": {"label": "访问数据目录文件", "risk": "high"},
    "net.http": {"label": "发起网络请求", "risk": "high"},
    "process.exec": {"label": "执行外部进程", "risk": "high"},
    "web.routes": {"label": "注册本地 Web 路由", "risk": "high"},
    "java.manage": {"label": "管理 Java 运行时", "risk": "high"},
    "protocol.handle": {"label": "处理自定义协议链接", "risk": "high"},
    "stats.read": {"label": "读取游玩统计", "risk": "safe"},
}

# 兼容旧代码：权限 id -> 中文标签（未翻译）
PERMISSION_LABELS = {k: v["label"] for k, v in PERMISSION_META.items()}


def permission_risk(perm_id: str) -> str:
    meta = PERMISSION_META.get(perm_id)
    if meta:
        return meta.get("risk") or "safe"
    if perm_id in HIGH_RISK_PERMISSIONS:
        return "high"
    if perm_id in DEFAULT_SAFE_PERMISSIONS:
        return "safe"
    # 未知权限按高风险展示，提醒用户注意
    return "high"


def permission_label_key(perm_id: str) -> str:
    """返回 i18n 键（中文源文案）；未知权限回退为 id 本身。"""
    meta = PERMISSION_META.get(perm_id)
    if meta:
        return meta["label"]
    return str(perm_id or "")


def permission_label(perm_id: str) -> str:
    """当前语言下的权限显示名。"""
    key = permission_label_key(perm_id)
    if not key:
        return ""
    try:
        from modules.i18n import i18nText

        return i18nText(key)
    except Exception:
        return key


def permission_detail(perm_id: str) -> dict:
    """供 QML 胶囊使用：{id, label, risk, label_key}。"""
    pid = str(perm_id or "").strip()
    return {
        "id": pid,
        "label": permission_label(pid) if pid else "",
        "label_key": permission_label_key(pid),
        "risk": permission_risk(pid) if pid else "safe",
    }


def permission_details(perms: Iterable[str]) -> List[dict]:
    """批量解析权限展示信息（去重保序）。"""
    seen = set()
    out: List[dict] = []
    for p in normalize_permissions(list(perms or [])):
        if p in seen:
            continue
        seen.add(p)
        out.append(permission_detail(p))
    return out


def normalize_permissions(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    result = []
    for item in raw:
        if not isinstance(item, str):
            continue
        p = item.strip()
        if p and p not in result:
            result.append(p)
    return result


def unknown_permissions(perms: Iterable[str]) -> List[str]:
    return [p for p in perms if p not in ALL_PERMISSIONS]


def has_permission(granted: Iterable[str], required: str) -> bool:
    granted_set = set(granted or [])
    if required in granted_set:
        return True
    # 通配：ui.* / launch.* 等
    if not required:
        return False
    prefix = required.split(".")[0] + ".*"
    return prefix in granted_set


def auto_grant_for_manifest(requested: Iterable[str], auto_high_risk: bool = True) -> List[str]:
    """
    首次安装时的授权策略。
    auto_high_risk=True：按 manifest 请求全部授权（用户可在 UI 中改；便于开发体验）。
    """
    requested_list = normalize_permissions(requested)
    if auto_high_risk:
        return list(requested_list)
    granted = []
    for p in requested_list:
        if p in DEFAULT_SAFE_PERMISSIONS or p not in HIGH_RISK_PERMISSIONS:
            granted.append(p)
    return granted
