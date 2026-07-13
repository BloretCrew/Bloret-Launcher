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

# 权限 -> 所需 contributes / hooks 映射提示
PERMISSION_LABELS = {
    "ui.nav": "添加导航页",
    "ui.theme": "修改主题",
    "ui.settings": "添加设置项",
    "ui.toolbar": "扩展 Minecraft 小工具栏",
    "ui.home": "扩展主页卡片",
    "ui.tools": "扩展小工具页卡片",
    "launch.hooks": "拦截/修改游戏启动",
    "download.hooks": "拦截下载/安装流程",
    "agent.bloriko": "扩展络可 Agent",
    "agent.blrpe": "扩展 BLRPE Copilot",
    "config.read": "读取启动器配置",
    "config.write": "写入启动器配置",
    "fs.datapath": "访问数据目录文件",
    "net.http": "发起网络请求",
    "process.exec": "执行外部进程",
    "web.routes": "注册本地 Web 路由",
}


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
