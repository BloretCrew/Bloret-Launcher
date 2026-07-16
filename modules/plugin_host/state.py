"""插件启用状态与权限持久化（config.json plugins 段）。"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import modules.config as cfg
import modules.globals as BLglobals
from modules.log import log

DEFAULT_PLUGINS_STATE = {
    "enabled": {},
    "permissions_granted": {},
    "data": {},
    "active_theme_plugin": "",
}


def _ensure_plugins_section(config: dict) -> dict:
    plugins = config.get("plugins")
    if not isinstance(plugins, dict):
        plugins = {}
    for key, default in DEFAULT_PLUGINS_STATE.items():
        if key not in plugins:
            plugins[key] = default.copy() if isinstance(default, dict) else default
    if not isinstance(plugins.get("enabled"), dict):
        plugins["enabled"] = {}
    if not isinstance(plugins.get("permissions_granted"), dict):
        plugins["permissions_granted"] = {}
    if not isinstance(plugins.get("data"), dict):
        plugins["data"] = {}
    config["plugins"] = plugins
    return plugins


def read_plugins_state() -> dict:
    try:
        config = cfg.read() or {}
        return dict(_ensure_plugins_section(config))
    except Exception as e:
        log(f"[PluginHost] 读取 plugins 状态失败: {e}")
        return dict(DEFAULT_PLUGINS_STATE)


def _write_config(config: dict, changed_keys: Optional[dict] = None) -> bool:
    """统一走 modules.config.write，确保 config.changed 钩子被派发。"""
    try:
        # plugins 段内部状态变更：若未指定 keys，用 plugins 摘要触发一次
        keys = changed_keys
        if keys is None and isinstance(config, dict) and "plugins" in config:
            keys = {"plugins": "<updated>"}
        ok = cfg.write(config, changed_keys=keys)
        if not ok:
            log("[PluginHost] 写入配置失败: config.write returned False")
        return bool(ok)
    except Exception as e:
        log(f"[PluginHost] 写入配置失败: {e}")
        return False


def update_plugins_state(mutator) -> dict:
    """mutator(plugins_dict) -> None，返回更新后的 plugins 段。"""
    config = cfg.read() or {}
    plugins = _ensure_plugins_section(config)
    mutator(plugins)
    config["plugins"] = plugins
    _write_config(config)
    return plugins


def is_enabled(plugin_id: str, default: bool = True) -> bool:
    state = read_plugins_state()
    enabled_map = state.get("enabled") or {}
    if plugin_id not in enabled_map:
        return default
    return bool(enabled_map.get(plugin_id))


def set_enabled(plugin_id: str, enabled: bool) -> None:
    def mut(plugins):
        plugins.setdefault("enabled", {})[plugin_id] = bool(enabled)
        log(f"[PluginHost] set_enabled {plugin_id}={enabled}")

    update_plugins_state(mut)


def get_granted_permissions(plugin_id: str) -> List[str]:
    state = read_plugins_state()
    granted = (state.get("permissions_granted") or {}).get(plugin_id)
    if isinstance(granted, list):
        return list(granted)
    return []


def set_granted_permissions(plugin_id: str, perms: List[str]) -> None:
    def mut(plugins):
        plugins.setdefault("permissions_granted", {})[plugin_id] = list(perms)
        log(f"[PluginHost] permissions_granted {plugin_id}={perms}")

    update_plugins_state(mut)


def ensure_permissions(plugin_id: str, requested: List[str], auto_grant: bool = True) -> List[str]:
    """若尚未授权，按策略写入授权并返回 granted。"""
    existing = get_granted_permissions(plugin_id)
    if existing:
        return existing
    from modules.plugin_host.permissions import auto_grant_for_manifest

    granted = auto_grant_for_manifest(requested, auto_high_risk=auto_grant)
    set_granted_permissions(plugin_id, granted)
    return granted


def get_plugin_data(plugin_id: str) -> dict:
    state = read_plugins_state()
    data = (state.get("data") or {}).get(plugin_id)
    return dict(data) if isinstance(data, dict) else {}


def set_plugin_data(plugin_id: str, data: dict) -> None:
    def mut(plugins):
        plugins.setdefault("data", {})[plugin_id] = data

    update_plugins_state(mut)


def update_plugin_data(plugin_id: str, key: str, value: Any) -> None:
    def mut(plugins):
        bucket = plugins.setdefault("data", {}).setdefault(plugin_id, {})
        if not isinstance(bucket, dict):
            bucket = {}
            plugins["data"][plugin_id] = bucket
        bucket[key] = value

    update_plugins_state(mut)


def get_active_theme_plugin() -> str:
    state = read_plugins_state()
    return str(state.get("active_theme_plugin") or "")


def set_active_theme_plugin(plugin_id: str) -> None:
    def mut(plugins):
        plugins["active_theme_plugin"] = plugin_id or ""
        log(f"[PluginHost] active_theme_plugin={plugin_id}")

    update_plugins_state(mut)


def remove_plugin_state(plugin_id: str) -> None:
    def mut(plugins):
        for key in ("enabled", "permissions_granted", "data"):
            section = plugins.get(key)
            if isinstance(section, dict) and plugin_id in section:
                del section[plugin_id]
        if plugins.get("active_theme_plugin") == plugin_id:
            plugins["active_theme_plugin"] = ""
        log(f"[PluginHost] 已清除插件状态: {plugin_id}")

    update_plugins_state(mut)
