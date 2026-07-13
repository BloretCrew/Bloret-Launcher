"""PluginHost：扫描、启用、禁用、卸载与 QObject 桥。"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal, Slot

import modules.globals as BLglobals
from modules.log import log
from modules.plugin_host import state as plugin_state
from modules.plugin_host.api import PluginAPI
from modules.plugin_host.event_bus import get_event_bus
from modules.plugin_host.loader_declarative import apply_declarative
from modules.plugin_host.loader_process import activate_process_plugin
from modules.plugin_host.loader_python import activate_python_plugin, deactivate_python_plugin
from modules.plugin_host.manifest import load_raw_manifest, normalize_manifest
from modules.plugin_host.registry import get_registry


def get_plugin_root() -> str:
    root = os.path.join(getattr(BLglobals, "datapath", "") or "", "Plugin")
    os.makedirs(root, exist_ok=True)
    return root


class PluginHost(QObject):
    """暴露给 QML 的插件宿主。"""

    pluginsChanged = Signal()
    themeOverrideChanged = Signal(str)  # plugin_id or empty
    navContributionsChanged = Signal()
    settingsContributionsChanged = Signal()
    homeContributionsChanged = Signal()
    toolsContributionsChanged = Signal()
    logMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugins: Dict[str, dict] = {}  # id -> runtime info
        self._bootstrapped = False
        self._bus = get_event_bus()
        self._registry = get_registry()
        log("[PluginHost] 实例已创建")

    # ── 生命周期 ──────────────────────────────────────────

    def bootstrap(self) -> None:
        if self._bootstrapped:
            log("[PluginHost] bootstrap 跳过（已完成）")
            return
        log("[PluginHost] bootstrap 开始")
        self.scan_and_load()
        self._bootstrapped = True
        try:
            from modules.plugin_host.dispatch import invoke_hook

            invoke_hook("app.ready")
        except Exception as e:
            log(f"[PluginHost] app.ready 派发失败: {e}")
            self._bus.emit("app.ready")
        # 语言包可能在 bootstrap 后才进入 registry，重新合并
        try:
            from modules.i18n import merge_plugin_i18n

            merge_plugin_i18n()
        except Exception as e:
            log(f"[PluginHost] merge_plugin_i18n 失败: {e}")
        log(f"[PluginHost] bootstrap 完成，已加载 {len(self._plugins)} 个插件")

    def shutdown(self) -> None:
        if getattr(self, "_shutdown_done", False):
            log("[PluginHost] shutdown 跳过（已完成）")
            return
        self._shutdown_done = True
        log("[PluginHost] shutdown")
        try:
            from modules.plugin_host.dispatch import invoke_hook

            invoke_hook("app.quit")
        except Exception as e:
            log(f"[PluginHost] app.quit 派发失败: {e}")
            self._bus.emit("app.quit")
        for plugin_id in list(self._plugins.keys()):
            try:
                self._deactivate(plugin_id, persist=False)
            except Exception as e:
                log(f"[PluginHost] shutdown 停用 {plugin_id} 失败: {e}")

    def scan_and_load(self) -> None:
        """重新扫描 Plugin 目录并加载插件。

        可重复调用：会先安全停用已激活实例，再按磁盘目录重建，
        这样「刷新」能发现手动复制/删除/更新的插件。
        """
        root = get_plugin_root()
        log(f"[PluginHost] 扫描插件目录: {root}")
        if not os.path.isdir(root):
            # 目录不存在时清空运行时缓存
            for plugin_id in list(self._plugins.keys()):
                try:
                    if self._plugins[plugin_id].get("active"):
                        self._deactivate(plugin_id, persist=False)
                except Exception as e:
                    log(f"[PluginHost] 清空插件 {plugin_id} 失败: {e}")
                self._plugins.pop(plugin_id, None)
            self._emit_ui_signals()
            self.pluginsChanged.emit()
            return

        # 先停用全部已激活插件，避免二次扫描重复注册钩子/贡献
        for plugin_id in list(self._plugins.keys()):
            info = self._plugins.get(plugin_id) or {}
            if info.get("active"):
                try:
                    self._deactivate(plugin_id, persist=False)
                except Exception as e:
                    log(f"[PluginHost] 扫描前停用 {plugin_id} 失败: {e}")

        found_ids = set()
        for entry in sorted(os.listdir(root)):
            # 跳过备份/暂存目录与隐藏项，避免 .backups 被当成插件
            if entry.startswith(".") or entry in (".backups", "__pycache__"):
                continue
            plugin_dir = os.path.join(root, entry)
            if not os.path.isdir(plugin_dir):
                continue
            try:
                manifest = normalize_manifest(plugin_dir, entry)
                plugin_id = manifest["id"]
                found_ids.add(plugin_id)
                enabled = plugin_state.is_enabled(plugin_id, default=True)
                perms = plugin_state.ensure_permissions(plugin_id, manifest.get("permissions") or [])
                info = {
                    "manifest": manifest,
                    "enabled": enabled,
                    "permissions": perms,
                    "module": None,
                    "api": None,
                    "active": False,
                    "error": "",
                }
                self._plugins[plugin_id] = info
                if enabled:
                    self._activate(plugin_id)
                else:
                    log(f"[PluginHost] 插件已禁用，跳过激活: {plugin_id}")
            except Exception as e:
                log(f"[PluginHost] 扫描插件 {entry} 失败: {e}")

        # 清理目录中已不存在的插件运行时状态
        for pid in list(self._plugins.keys()):
            if pid not in found_ids:
                log(f"[PluginHost] 插件目录已移除，清理运行时: {pid}")
                try:
                    if self._plugins[pid].get("active"):
                        self._deactivate(pid, persist=False)
                except Exception as e:
                    log(f"[PluginHost] 清理已删除插件 {pid} 失败: {e}")
                del self._plugins[pid]

        log(f"[PluginHost] 扫描完成 count={len(self._plugins)} ids={sorted(self._plugins.keys())}")
        self._emit_ui_signals()
        self.pluginsChanged.emit()

    @Slot(result=str)
    def rescanPlugins(self) -> str:
        """供 QML「刷新」调用：重新扫描磁盘插件目录并返回摘要 JSON。"""
        log("[PluginHost] rescanPlugins 开始")
        try:
            self.scan_and_load()
            items = self.list_plugins_info()
            payload = {
                "ok": True,
                "count": len(items),
                "plugins": [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "enabled": p.get("enabled"),
                        "active": p.get("active"),
                        "error": p.get("error") or "",
                    }
                    for p in items
                ],
                "message": f"已刷新，共 {len(items)} 个插件",
            }
            log(f"[PluginHost] rescanPlugins 完成 count={len(items)}")
            return json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            log(f"[PluginHost] rescanPlugins 失败: {e}")
            return json.dumps(
                {"ok": False, "count": 0, "plugins": [], "message": f"刷新失败: {e}", "error": str(e)},
                ensure_ascii=False,
            )

    def reload_plugin(self, plugin_id: str) -> bool:
        log(f"[PluginHost] reload {plugin_id}")
        info = self._plugins.get(plugin_id)
        if info and info.get("active"):
            self._deactivate(plugin_id, persist=False)
        # 重新读 manifest
        root = get_plugin_root()
        # 找目录
        path = None
        if info:
            path = info["manifest"]["path"]
        if not path or not os.path.isdir(path):
            for entry in os.listdir(root):
                p = os.path.join(root, entry)
                if not os.path.isdir(p):
                    continue
                m = normalize_manifest(p, entry)
                if m["id"] == plugin_id:
                    path = p
                    break
        if not path:
            return False
        manifest = normalize_manifest(path, os.path.basename(path))
        perms = plugin_state.ensure_permissions(plugin_id, manifest.get("permissions") or [])
        self._plugins[plugin_id] = {
            "manifest": manifest,
            "enabled": plugin_state.is_enabled(plugin_id, default=True),
            "permissions": perms,
            "module": None,
            "api": None,
            "active": False,
            "error": "",
        }
        if self._plugins[plugin_id]["enabled"]:
            self._activate(plugin_id)
        self._emit_ui_signals()
        self.pluginsChanged.emit()
        return True

    def notify_installed(self, folder_or_id: str) -> None:
        """安装完成后调用，扫描并启用。"""
        log(f"[PluginHost] notify_installed: {folder_or_id}")
        self.scan_and_load()
        # 尝试按 folder 找到 id 并确保 enabled
        for pid, info in self._plugins.items():
            m = info["manifest"]
            if folder_or_id in (pid, m.get("folderName"), m.get("name")):
                if not info.get("enabled"):
                    self.setPluginEnabled(pid, True)
                break

    def notify_uninstalled(self, plugin_id: str) -> None:
        log(f"[PluginHost] notify_uninstalled: {plugin_id}")
        if plugin_id in self._plugins:
            self._deactivate(plugin_id, persist=False)
            del self._plugins[plugin_id]
        plugin_state.remove_plugin_state(plugin_id)
        self._emit_ui_signals()
        self.pluginsChanged.emit()

    # ── 激活 / 停用 ───────────────────────────────────────

    def _activate(self, plugin_id: str) -> bool:
        info = self._plugins.get(plugin_id)
        if not info:
            return False
        if info.get("active"):
            return True
        manifest = info["manifest"]
        perms = info.get("permissions") or []
        api = PluginAPI(plugin_id, manifest["path"], perms)
        info["api"] = api
        info["error"] = ""
        log(f"[PluginHost] 激活插件 {plugin_id} perms={perms}")
        try:
            # 声明式先注册
            apply_declarative(manifest, api)
            # Python
            module = activate_python_plugin(manifest, api)
            info["module"] = module
            # 外部进程
            activate_process_plugin(manifest)
            info["active"] = True
            info["enabled"] = True
            log(f"[PluginHost] 插件已激活: {plugin_id}")
            return True
        except Exception as e:
            info["error"] = str(e)
            info["active"] = False
            log(f"[PluginHost] 激活失败 {plugin_id}: {e}")
            self._registry.clear_plugin(plugin_id)
            self._bus.off_plugin(plugin_id)
            return False

    def _deactivate(self, plugin_id: str, persist: bool = True) -> None:
        info = self._plugins.get(plugin_id)
        if not info:
            return
        log(f"[PluginHost] 停用插件 {plugin_id}")
        try:
            deactivate_python_plugin(plugin_id, info.get("module"), info.get("api"))
        except Exception as e:
            log(f"[PluginHost] deactivate python 失败: {e}")
        self._registry.clear_plugin(plugin_id)
        self._bus.off_plugin(plugin_id)
        info["active"] = False
        info["module"] = None
        info["api"] = None
        if persist:
            plugin_state.set_enabled(plugin_id, False)
            info["enabled"] = False

    # ── QML / Backend slots ───────────────────────────────

    @Slot(result=str)
    def getPluginsJson(self) -> str:
        return json.dumps(self.list_plugins_info(), ensure_ascii=False)

    def list_plugins_info(self) -> List[dict]:
        result = []
        for plugin_id, info in sorted(self._plugins.items(), key=lambda x: x[0]):
            m = info["manifest"]
            result.append(
                {
                    "id": plugin_id,
                    "name": m.get("name") or plugin_id,
                    "version": m.get("version") or "",
                    "author": m.get("author") or "",
                    "description": m.get("description") or "",
                    "url": m.get("url") or "",
                    "folderName": m.get("folderName") or "",
                    "path": m.get("path") or "",
                    "iconPath": m.get("iconPath") or "",
                    "enabled": bool(info.get("enabled")),
                    "active": bool(info.get("active")),
                    "error": info.get("error") or "",
                    "permissions": list(info.get("permissions") or []),
                    "requestedPermissions": list(m.get("permissions") or []),
                    "hasTheme": plugin_id in self._registry.get_themes(),
                    "entry": m.get("entry") or {},
                }
            )
        return result

    @Slot(str, bool, result=bool)
    def setPluginEnabled(self, plugin_id: str, enabled: bool) -> bool:
        log(f"[PluginHost] setPluginEnabled {plugin_id}={enabled}")
        if plugin_id not in self._plugins:
            # 尝试 rescan
            self.scan_and_load()
        if plugin_id not in self._plugins:
            log(f"[PluginHost] 未知插件: {plugin_id}")
            return False
        if enabled:
            plugin_state.set_enabled(plugin_id, True)
            self._plugins[plugin_id]["enabled"] = True
            self._plugins[plugin_id]["permissions"] = plugin_state.ensure_permissions(
                plugin_id, self._plugins[plugin_id]["manifest"].get("permissions") or []
            )
            ok = self._activate(plugin_id)
        else:
            self._deactivate(plugin_id, persist=True)
            ok = True
        self._emit_ui_signals()
        self.pluginsChanged.emit()
        return ok

    @Slot(str, result=str)
    def installFromPath(self, path: str) -> str:
        """从本地 ZIP 或插件目录安装，返回 JSON: {ok, plugin_id|error, message}。"""
        log(f"[PluginHost] installFromPath path={path}")
        try:
            from modules.plugin import install_plugin_from_path

            ok, detail = install_plugin_from_path(path, force=True)
            if ok:
                payload = {
                    "ok": True,
                    "plugin_id": detail,
                    "message": f"已安装插件 {detail}",
                }
            else:
                payload = {
                    "ok": False,
                    "error": detail,
                    "message": f"安装失败: {detail}",
                }
            log(f"[PluginHost] installFromPath result={payload}")
            self._emit_ui_signals()
            self.pluginsChanged.emit()
            return json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            log(f"[PluginHost] installFromPath 失败: {e}")
            return json.dumps(
                {"ok": False, "error": str(e), "message": f"安装失败: {e}"},
                ensure_ascii=False,
            )

    @Slot(str, result=bool)
    def uninstallPlugin(self, plugin_id: str) -> bool:
        log(f"[PluginHost] uninstallPlugin {plugin_id}")
        try:
            from modules.plugin import uninstall_plugin

            # 先停用
            if plugin_id in self._plugins:
                self._deactivate(plugin_id, persist=False)
            name = plugin_id
            if plugin_id in self._plugins:
                name = self._plugins[plugin_id]["manifest"].get("folderName") or plugin_id
            ok, msg = uninstall_plugin(name)
            log(f"[PluginHost] uninstall result: {ok} {msg}")
            if plugin_id in self._plugins:
                del self._plugins[plugin_id]
            plugin_state.remove_plugin_state(plugin_id)
            self._emit_ui_signals()
            self.pluginsChanged.emit()
            return bool(ok)
        except Exception as e:
            log(f"[PluginHost] uninstallPlugin 失败: {e}")
            return False

    @Slot(result=bool)
    def openPluginDir(self) -> bool:
        root = get_plugin_root()
        log(f"[PluginHost] openPluginDir {root}")
        try:
            import subprocess
            import sys

            if sys.platform == "win32":
                os.startfile(root)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", root])
            else:
                subprocess.Popen(["xdg-open", root])
            return True
        except Exception as e:
            log(f"[PluginHost] openPluginDir 失败: {e}")
            return False

    @Slot(str, result=bool)
    def openPluginFolder(self, plugin_id: str) -> bool:
        info = self._plugins.get(plugin_id)
        path = info["manifest"]["path"] if info else ""
        if not path or not os.path.isdir(path):
            return False
        try:
            import subprocess
            import sys

            if sys.platform == "win32":
                os.startfile(path)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return True
        except Exception as e:
            log(f"[PluginHost] openPluginFolder 失败: {e}")
            return False

    @staticmethod
    def _path_to_url(path: str) -> str:
        if not path or path.startswith("file:"):
            return path or ""
        if not os.path.isfile(path) and not os.path.isdir(path):
            return path
        try:
            from pathlib import Path
            return Path(path).resolve().as_uri()
        except Exception:
            normalized = path.replace("\\", "/")
            if normalized.startswith("/"):
                return "file://" + normalized
            return "file:///" + normalized

    @Slot(result=str)
    def getNavContributionsJson(self) -> str:
        items = []
        for nav in self._registry.get_nav():
            page = nav.get("page") or ""
            page_url = self._path_to_url(page)
            items.append(
                {
                    "id": nav.get("id"),
                    "plugin_id": nav.get("plugin_id"),
                    "title": nav.get("title"),
                    "page": page_url,
                    "icon": nav.get("icon") or "ic_fluent_puzzle_piece_20_regular",
                    "position": nav.get("position") or "top",
                    "source": nav.get("source") or "",
                }
            )
        return json.dumps(items, ensure_ascii=False)

    @Slot(result=str)
    def getSettingsContributionsJson(self) -> str:
        items = []
        for s in self._registry.get_settings():
            qml = self._path_to_url(s.get("qml") or "")
            items.append(
                {
                    "id": s.get("id"),
                    "plugin_id": s.get("plugin_id"),
                    "title": s.get("title"),
                    "qml": qml,
                    "icon": s.get("icon") or "ic_fluent_puzzle_piece_20_regular",
                }
            )
        return json.dumps(items, ensure_ascii=False)

    @Slot(result=str)
    def getHomeContributionsJson(self) -> str:
        items = []
        for h in self._registry.get_home():
            qml = self._path_to_url(h.get("qml") or "")
            items.append(
                {
                    "id": h.get("id"),
                    "plugin_id": h.get("plugin_id"),
                    "title": h.get("title") or "",
                    "qml": qml,
                    "icon": h.get("icon") or "ic_fluent_news_20_regular",
                    "order": h.get("order", 100),
                }
            )
        log(f"[PluginHost] getHomeContributionsJson count={len(items)}")
        return json.dumps(items, ensure_ascii=False)

    @Slot(result=str)
    def getToolsContributionsJson(self) -> str:
        items = []
        for t in self._registry.get_tools():
            qml = self._path_to_url(t.get("qml") or "")
            items.append(
                {
                    "id": t.get("id"),
                    "plugin_id": t.get("plugin_id"),
                    "title": t.get("title") or "",
                    "qml": qml,
                    "icon": t.get("icon") or "ic_fluent_wrench_20_regular",
                    "order": t.get("order", 100),
                }
            )
        log(f"[PluginHost] getToolsContributionsJson count={len(items)}")
        return json.dumps(items, ensure_ascii=False)

    @Slot(str, str, str)
    def notifyPageOpen(self, page_id: str, title: str = "", plugin_id: str = "") -> None:
        """QML 导航切换时调用，触发 ui.page.open。"""
        try:
            from modules.plugin_host.dispatch import invoke_hook

            ctx = {
                "page_id": page_id or "",
                "title": title or "",
                "plugin_id": plugin_id or "",
            }
            log(f"[PluginHost] ui.page.open {ctx}")
            invoke_hook("ui.page.open", ctx)
        except Exception as e:
            log(f"[PluginHost] notifyPageOpen 失败: {e}")

    @Slot(result=str)
    def getToolbarContributionsJson(self) -> str:
        items = []
        for t in self._registry.get_toolbar():
            items.append(
                {
                    "id": t.get("id"),
                    "plugin_id": t.get("plugin_id"),
                    "label": t.get("label"),
                    "icon": t.get("icon") or "",
                    "action": t.get("action") or "",
                }
            )
        return json.dumps(items, ensure_ascii=False)

    @Slot(result=str)
    def getThemesJson(self) -> str:
        themes = self._registry.get_themes()
        active = plugin_state.get_active_theme_plugin()
        out = []
        for pid, theme in themes.items():
            out.append(
                {
                    "plugin_id": pid,
                    "name": theme.get("name") or pid,
                    "accent": theme.get("accent") or (theme.get("colors") or {}).get("primaryColor", ""),
                    "mode": theme.get("mode") or "",
                    "active": pid == active,
                    "colors": theme.get("colors") or {},
                }
            )
        return json.dumps(out, ensure_ascii=False)

    @Slot(result=str)
    def getActiveThemeJson(self) -> str:
        active = plugin_state.get_active_theme_plugin()
        if not active:
            return "{}"
        theme = self._registry.get_theme(active)
        if not theme:
            return "{}"
        data = dict(theme)
        data["plugin_id"] = active
        return json.dumps(data, ensure_ascii=False)

    @Slot(str, result=bool)
    def setActiveThemePlugin(self, plugin_id: str) -> bool:
        log(f"[PluginHost] setActiveThemePlugin {plugin_id}")
        if plugin_id and plugin_id not in self._registry.get_themes():
            log(f"[PluginHost] 主题插件未注册: {plugin_id}")
            return False
        from modules.plugin_host.dispatch import invoke_hook

        plugin_state.set_active_theme_plugin(plugin_id or "")
        theme = self._registry.get_theme(plugin_id) if plugin_id else {}
        invoke_hook("theme.changed", plugin_id, theme or {})
        self.themeOverrideChanged.emit(plugin_id or "")
        return True

    @Slot(result=str)
    def getPluginRoot(self) -> str:
        return get_plugin_root()

    @Slot(result="QVariantList")
    def getPermissionLabels(self) -> list:
        from modules.plugin_host.permissions import PERMISSION_LABELS

        return [{"id": k, "label": v} for k, v in PERMISSION_LABELS.items()]

    def get_toolbar_callbacks(self) -> List[dict]:
        return self._registry.get_toolbar()

    def _emit_ui_signals(self) -> None:
        self.navContributionsChanged.emit()
        self.settingsContributionsChanged.emit()
        self.homeContributionsChanged.emit()
        self.toolsContributionsChanged.emit()
        active = plugin_state.get_active_theme_plugin()
        # 若 active 主题插件已不在 registry，清空
        if active and active not in self._registry.get_themes():
            # 尝试选第一个主题
            themes = self._registry.get_themes()
            if themes:
                first = next(iter(themes.keys()))
                plugin_state.set_active_theme_plugin(first)
                active = first
            else:
                plugin_state.set_active_theme_plugin("")
                active = ""
        self.themeOverrideChanged.emit(active or "")
        # 插件启用/禁用后刷新 i18n 合并
        try:
            from modules.i18n import merge_plugin_i18n

            merge_plugin_i18n()
        except Exception as e:
            log(f"[PluginHost] _emit_ui_signals merge_plugin_i18n: {e}")


# 单例
_host: Optional[PluginHost] = None


def get_plugin_host() -> PluginHost:
    global _host
    if _host is None:
        _host = PluginHost()
    return _host


def bootstrap_plugins() -> PluginHost:
    host = get_plugin_host()
    host.bootstrap()
    return host
