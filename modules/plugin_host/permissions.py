"""插件权限枚举与校验。"""

from __future__ import annotations

from typing import Iterable, List, Set

# 所有已定义权限
ALL_PERMISSIONS: Set[str] = {
    "ui.nav",
    "ui.theme",
    "ui.settings",
    "ui.toolbar",
    "ui.home",
    "ui.tools",
    "launch.hooks",
    "download.hooks",
    "agent.bloriko",
    "agent.blrpe",
    "config.read",
    "config.write",
    "fs.datapath",
    "net.http",
    "process.exec",
    "web.routes",
}

# 安装时默认授予的低风险权限（仍会在 UI 中展示）
DEFAULT_SAFE_PERMISSIONS: Set[str] = {
    "ui.nav",
    "ui.theme",
    "ui.settings",
    "ui.toolbar",
    "ui.home",
    "ui.tools",
    "config.read",
}

# 高风险权限（需要用户明确授权）
HIGH_RISK_PERMISSIONS: Set[str] = {
    "launch.hooks",
    "download.hooks",
    "agent.bloriko",
    "agent.blrpe",
    "config.write",
    "fs.datapath",
    "net.http",
    "process.exec",
    "web.routes",
}

# 权限元数据：label 为 i18n 源文案（中文 key，与 lang/*.json texts 对齐）
PERMISSION_META = {
    "ui.nav": {"label": "添加导航页", "risk": "safe"},
    "ui.theme": {"label": "修改主题", "risk": "safe"},
    "ui.settings": {"label": "添加设置项", "risk": "safe"},
    "ui.toolbar": {"label": "扩展 Minecraft 小工具栏", "risk": "safe"},
    "ui.home": {"label": "扩展主页卡片", "risk": "safe"},
    "ui.tools": {"label": "扩展小工具页卡片", "risk": "safe"},
    "launch.hooks": {"label": "拦截/修改游戏启动", "risk": "high"},
    "download.hooks": {"label": "拦截下载/安装流程", "risk": "high"},
    "agent.bloriko": {"label": "扩展络可 Agent", "risk": "high"},
    "agent.blrpe": {"label": "扩展 BLRPE Copilot", "risk": "high"},
    "config.read": {"label": "读取启动器配置", "risk": "safe"},
    "config.write": {"label": "写入启动器配置", "risk": "high"},
    "fs.datapath": {"label": "访问数据目录文件", "risk": "high"},
    "net.http": {"label": "发起网络请求", "risk": "high"},
    "process.exec": {"label": "执行外部进程", "risk": "high"},
    "web.routes": {"label": "注册本地 Web 路由", "risk": "high"},
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
    # 通配：未来可扩展 "ui.*"
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
