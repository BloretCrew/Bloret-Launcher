"""插件商店安装请求：解析、校验与待确认队列。

商店 / 协议 / 本机 HTTP 共用此模型。确认前不得写入 Plugin 目录。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from modules.log import log

# 官方 / 默认可信下载主机（可被 config 扩展）
DEFAULT_TRUSTED_HOSTS: Tuple[str, ...] = (
    "github.com",
    "www.github.com",
    "raw.githubusercontent.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "cdn.jsdelivr.net",
    "gitee.com",
    "www.gitee.com",
    "gitlab.com",
    "www.gitlab.com",
    "bloret.com",
    "www.bloret.com",
    "store.bloret.com",
    "api.bloret.com",
)

_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_ID_RE = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


@dataclass
class PluginInstallRequest:
    """一次待用户确认的安装请求。"""

    token: str
    download: str
    id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""
    description: str = ""
    sha256: str = ""
    source: str = "store"  # store | web | file | protocol | localhost
    permissions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending | installing | done | failed | cancelled
    error: str = ""
    plugin_id: str = ""
    allow_file: bool = False  # 仅启动器内本地路径

    def display_name(self) -> str:
        return self.name or self.id or "Unknown Plugin"

    def download_host(self) -> str:
        try:
            return (urlparse(self.download).hostname or "") or ""
        except Exception:
            return ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["download_host"] = self.download_host()
        data["display_name"] = self.display_name()
        # 权限国际化详情，供确认框胶囊展示
        try:
            from modules.plugin_host.permissions import permission_details

            data["permission_details"] = permission_details(self.permissions or [])
        except Exception:
            data["permission_details"] = [
                {"id": p, "label": p, "risk": "high"} for p in (self.permissions or [])
            ]
        # 不向 QML 暴露内部 allow_file 细节以外的敏感字段
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def _normalize_source(raw: str) -> str:
    value = (raw or "store").strip().lower()
    if value in ("store", "web", "file", "protocol", "localhost", "in-app", "debug"):
        return value
    return "store"


def get_trusted_hosts() -> List[str]:
    """默认白名单 + config.plugin_store_trusted_hosts。"""
    hosts = list(DEFAULT_TRUSTED_HOSTS)
    try:
        import modules.config as cfg

        data = cfg.read() or {}
        extra = data.get("plugin_store_trusted_hosts") or data.get("plugin_trusted_hosts") or []
        if isinstance(extra, str):
            extra = [h.strip() for h in extra.split(",") if h.strip()]
        if isinstance(extra, list):
            for h in extra:
                h = str(h or "").strip().lower()
                if h and h not in hosts:
                    hosts.append(h)
        # 空列表表示不限制主机（仍强制 https）
        if data.get("plugin_store_allow_any_https") is True:
            return []
    except Exception as e:
        log(f"[PluginStore] 读取信任主机配置失败: {e}")
    return hosts


def validate_download_url(
    download: str,
    *,
    allow_file: bool = False,
    trusted_hosts: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """校验下载地址：https 必选；可选主机白名单；file 仅启动器内。"""
    url = (download or "").strip()
    if not url:
        return False, "缺少 download 参数"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"无效的 download URL: {e}"

    scheme = (parsed.scheme or "").lower()
    if scheme == "file":
        if not allow_file:
            return False, "file:// 仅允许启动器内安装入口"
        path = urllib.parse.unquote(parsed.path or "")
        if os.name == "nt" and path.startswith("/") and len(path) >= 3 and path[2] == ":":
            path = path[1:]
        if not path or not os.path.exists(path):
            return False, f"本地文件不存在: {path}"
        return True, ""

    if scheme != "https":
        return False, f"download 仅允许 https://（当前: {scheme or '无协议'}）"

    host = (parsed.hostname or "").lower()
    if not host:
        return False, "download URL 缺少主机名"

    # trusted_hosts 为 None 时读配置；空列表表示允许任意 https
    if trusted_hosts is None:
        trusted_hosts = get_trusted_hosts()
    if trusted_hosts:
        allowed = False
        for t in trusted_hosts:
            t = (t or "").lower().lstrip(".")
            if not t:
                continue
            if host == t or host.endswith("." + t):
                allowed = True
                break
        if not allowed:
            return False, f"下载主机不在信任列表: {host}"

    return True, ""


def parse_install_params(params: Dict[str, Any], *, allow_file: bool = False) -> Tuple[Optional[PluginInstallRequest], str]:
    """从字典解析安装请求（query / JSON body / QML）。"""
    if not isinstance(params, dict):
        return None, "参数必须是对象"

    def _get(*keys: str, default: str = "") -> str:
        for k in keys:
            if k in params and params[k] is not None:
                v = params[k]
                if isinstance(v, list):
                    v = v[0] if v else default
                return str(v).strip()
        return default

    download = _get("download", "url", "zip")
    ok, err = validate_download_url(download, allow_file=allow_file)
    if not ok:
        return None, err

    plugin_id = _get("id", "plugin_id", "pluginId")
    if plugin_id and not _ID_RE.match(plugin_id):
        return None, f"无效的插件 id: {plugin_id}"

    sha256 = _get("sha256", "hash", "checksum")
    if sha256 and not _SHA256_RE.match(sha256):
        return None, "sha256 必须是 64 位十六进制"

    name = _get("name", "title")
    version = _get("version", "ver")
    author = _get("author", "master")
    description = _get("description", "desc", "summary")
    source = _normalize_source(_get("source", default="store"))

    # 权限：JSON 数组字符串，或逗号分隔，或 list
    perms_raw = params.get("permissions")
    if perms_raw is None:
        perms_raw = params.get("permission") or params.get("perms") or []
    if isinstance(perms_raw, list) and len(perms_raw) == 1 and isinstance(perms_raw[0], str):
        # parse_qs 风格
        perms_raw = perms_raw[0]
    permissions: List[str] = []
    if isinstance(perms_raw, list):
        permissions = [str(x).strip() for x in perms_raw if str(x).strip()]
    elif isinstance(perms_raw, str) and perms_raw.strip():
        text = perms_raw.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                permissions = [str(x).strip() for x in parsed if str(x).strip()]
            elif isinstance(parsed, str):
                permissions = [parsed.strip()] if parsed.strip() else []
        except Exception:
            permissions = [p.strip() for p in re.split(r"[,;\s]+", text) if p.strip()]

    token = secrets.token_urlsafe(16)
    req = PluginInstallRequest(
        token=token,
        download=download,
        id=plugin_id,
        name=name,
        version=version,
        author=author,
        description=description,
        sha256=sha256.lower() if sha256 else "",
        source=source,
        permissions=permissions,
        allow_file=allow_file,
    )
    log(
        f"[PluginStore] 解析安装请求 token={token[:8]}… "
        f"id={plugin_id or '-'} name={name or '-'} host={req.download_host()} source={source}"
    )
    return req, ""


def parse_query_string(query: str, *, allow_file: bool = False) -> Tuple[Optional[PluginInstallRequest], str]:
    """从 URL query 解析。"""
    try:
        qs = urllib.parse.parse_qs(query or "", keep_blank_values=False)
        flat = {k: (v[0] if isinstance(v, list) and v else v) for k, v in qs.items()}
        return parse_install_params(flat, allow_file=allow_file)
    except Exception as e:
        return None, f"解析 query 失败: {e}"


def parse_bloret_url(url: str) -> Tuple[Optional[PluginInstallRequest], str]:
    """解析 bloret://plugin/install?... 或 bloret://install-plugin?..."""
    raw = (url or "").strip()
    if not raw:
        return None, "空协议 URL"
    try:
        # 某些系统会把 bloret:// 变成 bloret:/
        if raw.lower().startswith("bloret:"):
            # 规范化
            rest = raw[len("bloret:") :]
            while rest.startswith("/"):
                rest = rest[1:]
            # rest like plugin/install?... or install-plugin?...
            if "?" in rest:
                path_part, query = rest.split("?", 1)
            else:
                path_part, query = rest, ""
            path_part = path_part.strip("/").lower()
            if path_part in (
                "plugin/install",
                "install-plugin",
                "plugin/install/",
                "install",
            ) or path_part.startswith("plugin/install"):
                req, err = parse_query_string(query, allow_file=False)
                if req:
                    req.source = req.source if req.source != "store" else "protocol"
                    log(f"[Protocol] 解析 bloret URL path={path_part} token={req.token[:8]}…")
                return req, err
            return None, f"不支持的 bloret 路径: {path_part}"
        return None, "不是 bloret:// URL"
    except Exception as e:
        log(f"[Protocol] 解析失败: {e}")
        return None, str(e)


def file_sha256(path: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: str, expected: str) -> Tuple[bool, str]:
    expected = (expected or "").strip().lower()
    if not expected:
        return True, ""
    if not _SHA256_RE.match(expected):
        return False, "期望的 sha256 格式无效"
    try:
        actual = file_sha256(path)
    except Exception as e:
        return False, f"计算 sha256 失败: {e}"
    if actual.lower() != expected:
        log(f"[PluginStore] sha256 不匹配 expected={expected} actual={actual}")
        return False, f"sha256 校验失败（期望 {expected[:12]}… 实际 {actual[:12]}…）"
    log(f"[PluginStore] sha256 校验通过 {actual[:16]}…")
    return True, ""


class InstallRequestQueue:
    """进程内待确认安装请求队列（线程安全）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: Dict[str, PluginInstallRequest] = {}
        self._order: List[str] = []

    def put(self, req: PluginInstallRequest) -> PluginInstallRequest:
        with self._lock:
            self._items[req.token] = req
            if req.token not in self._order:
                self._order.append(req.token)
            log(f"[PluginStore] 入队 token={req.token[:8]}… pending={len(self._order)}")
            return req

    def get(self, token: str) -> Optional[PluginInstallRequest]:
        with self._lock:
            return self._items.get(token)

    def pop_next_pending(self) -> Optional[PluginInstallRequest]:
        with self._lock:
            for token in list(self._order):
                req = self._items.get(token)
                if req and req.status == "pending":
                    return req
            return None

    def list_pending(self) -> List[PluginInstallRequest]:
        with self._lock:
            return [
                self._items[t]
                for t in self._order
                if t in self._items and self._items[t].status == "pending"
            ]

    def update(self, token: str, **kwargs: Any) -> Optional[PluginInstallRequest]:
        with self._lock:
            req = self._items.get(token)
            if not req:
                return None
            for k, v in kwargs.items():
                if hasattr(req, k):
                    setattr(req, k, v)
            return req

    def remove(self, token: str) -> None:
        with self._lock:
            self._items.pop(token, None)
            if token in self._order:
                self._order.remove(token)


# 全局队列
_queue = InstallRequestQueue()


def get_install_queue() -> InstallRequestQueue:
    return _queue
