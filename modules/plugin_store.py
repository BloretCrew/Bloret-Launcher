"""Remote plugin store client used by the native QML store page."""

from __future__ import annotations

import json
import re
import threading
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PySide6.QtCore import QObject, Signal, Slot

import modules.config as cfg
from modules.log import log
from modules.plugin_install_request import validate_download_url

# The repository documents the listing shape but does not publish a working
# production listing endpoint; keep the client disabled until one is configured.
DEFAULT_STORE_API = ""
_DEFAULT_TIMEOUT = (8, 20)
_VERSION_PART = re.compile(r"\d+")


def _version_key(value: Any) -> tuple:
    """Return a forgiving comparable key for semver-like launcher versions."""
    text = str(value or "0").strip().lower().lstrip("v")
    parts = []
    for piece in re.split(r"[.+_-]", text):
        match = _VERSION_PART.search(piece)
        parts.append(int(match.group()) if match else -1)
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def _as_list(payload: Any) -> List[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise ValueError("商店响应必须是 JSON 数组或对象")
    for key in ("plugins", "items", "results"):
        if isinstance(payload.get(key), list):
            return [item for item in payload[key] if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return _as_list(data)
    if isinstance(payload.get("plugin"), dict):
        return [payload["plugin"]]
    # A single plugin detail object is also accepted.
    if payload.get("id") or payload.get("download"):
        return [payload]
    raise ValueError("商店响应中未找到插件列表")


def normalize_listing(item: dict, api_base: str = "") -> dict:
    """Normalize one store item without trusting it as executable content."""
    plugin_id = str(item.get("id") or "").strip()
    if not plugin_id or not re.fullmatch(r"[a-zA-Z0-9._-]{1,128}", plugin_id):
        raise ValueError("插件条目缺少合法 id")
    download = str(item.get("download") or item.get("download_url") or "").strip()
    if not download:
        raise ValueError(f"插件 {plugin_id} 缺少 download")
    ok, error = validate_download_url(download, allow_file=False)
    if not ok:
        raise ValueError(f"插件 {plugin_id} 下载地址无效: {error}")
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = [x.strip() for x in re.split(r"[,;]", tags) if x.strip()]
    permissions = item.get("permissions") or []
    if isinstance(permissions, str):
        permissions = [x.strip() for x in re.split(r"[,;\s]+", permissions) if x.strip()]
    icon = str(item.get("icon") or "").strip()
    if icon and not urlparse(icon).scheme:
        icon = urljoin(api_base.rstrip("/") + "/", icon.lstrip("/"))
    return {
        "id": plugin_id,
        "name": str(item.get("name") or plugin_id),
        "version": str(item.get("version") or ""),
        "author": str(item.get("author") or ""),
        "description": str(item.get("description") or ""),
        "icon": icon,
        "homepage": str(item.get("homepage") or ""),
        "download": download,
        "sha256": str(item.get("sha256") or "").strip(),
        "size": item.get("size") or 0,
        "permissions": permissions,
        "min_launcher": str(item.get("min_launcher") or ""),
        "tags": tags,
        "updated_at": str(item.get("updated_at") or item.get("updatedAt") or ""),
    }


def merge_install_state(items: List[dict], installed: List[dict]) -> List[dict]:
    by_id = {str(x.get("id")): x for x in installed if isinstance(x, dict)}
    result = []
    for item in items:
        row = dict(item)
        local = by_id.get(row["id"])
        row["installed"] = bool(local)
        row["installed_version"] = str(local.get("version") or "") if local else ""
        row["update_available"] = bool(
            local and row.get("version") and _version_key(row["version"]) > _version_key(local.get("version"))
        )
        result.append(row)
    return result


class PluginStore(QObject):
    """Asynchronous store client; installation remains delegated to PluginHost."""

    pluginsChanged = Signal(str)
    loadingChanged = Signal(bool)
    errorChanged = Signal(str)

    def __init__(self, plugin_host=None, parent=None):
        super().__init__(parent)
        self._plugin_host = plugin_host
        self._items: List[dict] = []
        self._lock = threading.RLock()
        self._generation = 0
        self._loading = False

    def _api_base(self) -> str:
        data = cfg.read() or {}
        value = str(data.get("plugin_store_api") or DEFAULT_STORE_API).strip().rstrip("/")
        if not value:
            return ""
        if not value.startswith("https://"):
            return ""
        return value

    def _installed(self) -> list:
        try:
            return self._plugin_host.list_plugins_info() if self._plugin_host else []
        except Exception as error:
            log(f"[PluginStore] 获取已安装插件失败: {error}")
            return []

    @Slot(result=str)
    def getApiBase(self) -> str:
        return self._api_base()

    @Slot(result=str)
    def getPluginsJson(self) -> str:
        with self._lock:
            return json.dumps(self._items, ensure_ascii=False)

    @Slot(result=bool)
    def isLoading(self) -> bool:
        return self._loading

    @Slot()
    def refresh(self) -> None:
        with self._lock:
            self._generation += 1
            generation = self._generation
            if self._loading:
                return
            self._loading = True
        self.loadingChanged.emit(True)

        def worker() -> None:
            try:
                api_base = self._api_base()
                if not api_base:
                    self.errorChanged.emit("未配置插件商店列表接口，请在设置中填写 HTTPS 地址")
                    return
                session = requests.Session()
                retry = Retry(total=2, backoff_factor=0.4, status_forcelist=[429, 500, 502, 503, 504])
                adapter = HTTPAdapter(max_retries=retry)
                session.mount("https://", adapter)
                response = session.get(api_base, timeout=_DEFAULT_TIMEOUT, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
                parsed = [normalize_listing(item, api_base) for item in _as_list(payload)]
                merged = merge_install_state(parsed, self._installed())
                with self._lock:
                    if generation == self._generation:
                        self._items = merged
                self.pluginsChanged.emit(json.dumps(merged, ensure_ascii=False))
                self.errorChanged.emit("")
            except Exception as error:
                log(f"[PluginStore] 刷新失败: {error}")
                self.errorChanged.emit(str(error))
            finally:
                with self._lock:
                    self._loading = False
                self.loadingChanged.emit(False)

        threading.Thread(target=worker, name="plugin-store-refresh", daemon=True).start()

    @Slot(str, result=str)
    def proposeInstall(self, plugin_json: str) -> str:
        if not self._plugin_host:
            return json.dumps({"ok": False, "error": "PluginHost 不可用"}, ensure_ascii=False)
        try:
            item = json.loads(plugin_json or "{}")
            if not isinstance(item, dict):
                raise ValueError("插件信息必须是对象")
            return self._plugin_host.proposeInstall(json.dumps(item, ensure_ascii=False))
        except Exception as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @Slot()
    def clearCache(self) -> None:
        with self._lock:
            self._items = []
        self.pluginsChanged.emit("[]")

    def refresh_install_state(self) -> None:
        with self._lock:
            current = list(self._items)
        merged = merge_install_state(current, self._installed())
        with self._lock:
            self._items = merged
        self.pluginsChanged.emit(json.dumps(merged, ensure_ascii=False))
