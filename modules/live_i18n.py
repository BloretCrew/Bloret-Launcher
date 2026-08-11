"""Synchronize Launcher UI catalogs from tr.bloret.net public APIs.

The network is always optional: callers load AppData/bundled catalogs first,
then invoke :func:`refresh_language_async`. A failed request never removes or
replaces a previously valid local catalog.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote

import requests

import modules.globals as BLglobals


def log(message):
    """Log without making the network/cache module depend on PySide6."""
    try:
        from modules.log import log as app_log

        app_log(message)
    except Exception:
        print(message)

DEFAULT_BASE_URL = "https://tr.bloret.net"
ORG_SLUG = "bloret"
PROJECT_SLUG = "bloret-launcher"
FILE_ID = "cd3f495d-eb9e-466f-888e-93df7eeef861"
DEFAULT_MODE = "top_voted"
MAX_CATALOG_BYTES = 4 * 1024 * 1024

# Launcher language code -> Translation Collector target locale.
LOCALE_MAP = {
    "en-GB": "en",
    "gt-ZH": "gt",
    "ja-JP": "ja",
    "ru-RU": "ru",
    "zh-wy": "wy",
    "zh-TW": "zh-TW",
}
API_TO_LAUNCHER = {value: key for key, value in LOCALE_MAP.items()}
DISPLAY_NAMES = {
    "zh-cn": "简体中文",
    "en-GB": "English",
    "gt-ZH": "梗体中文",
    "ja-JP": "日本語",
    "ru-RU": "Русский",
    "zh-wy": "文言文",
    "zh-TW": "繁體中文",
}

_inflight_lock = threading.RLock()
_inflight_callbacks: dict[str, list[Callable[[dict], None]]] = {}


def user_lang_dir(data_path: Optional[str] = None) -> Path:
    """Return the cross-platform writable language cache directory."""
    root = data_path if data_path is not None else BLglobals.datapath
    return Path(root) / "lang"


def cached_language_path(language: str, data_path: Optional[str] = None) -> Path:
    language = normalize_language(language)
    return user_lang_dir(data_path) / f"{language}.json"


def manifest_cache_path(data_path: Optional[str] = None) -> Path:
    return user_lang_dir(data_path) / "_manifest.json"


def normalize_language(language: object) -> str:
    code = str(language or "").strip()
    if code == "zh-CN":
        code = "zh-cn"
    if code not in {"zh-cn", *LOCALE_MAP.keys()}:
        raise ValueError(f"unsupported language code: {code!r}")
    return code


def _settings() -> dict:
    defaults = {
        "enabled": True,
        "baseUrl": DEFAULT_BASE_URL,
        "mode": DEFAULT_MODE,
        "timeout": (5, 12),
    }
    try:
        from modules import config as cfg

        raw = cfg.read() or {}
        api = raw.get("translationApi")
        if not isinstance(api, dict):
            return defaults
        enabled = api.get("enabled", True) is not False
        base_url = str(api.get("baseUrl") or DEFAULT_BASE_URL).rstrip("/")
        mode = str(api.get("mode") or DEFAULT_MODE)
        if mode not in {"top_voted", "approved", "source", "empty"}:
            mode = DEFAULT_MODE
        connect_timeout = float(api.get("connectTimeout", 5))
        read_timeout = float(api.get("readTimeout", 12))
        return {
            "enabled": enabled,
            "baseUrl": base_url,
            "mode": mode,
            "timeout": (max(1.0, connect_timeout), max(1.0, read_timeout)),
        }
    except Exception as exc:
        log(f"[live-i18n] 读取配置失败，使用默认值: {exc}")
        return defaults


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "Bloret-Launcher/i18n (https://github.com/Bloret-Crew/Bloret-Launcher)",
        }
    )
    return session


def _proxies():
    try:
        return BLglobals.get_proxies()
    except Exception:
        return None


def manifest_url(base_url: str = DEFAULT_BASE_URL) -> str:
    return (
        f"{base_url.rstrip('/')}/api/v1/orgs/{quote(ORG_SLUG, safe='')}"
        f"/projects/{quote(PROJECT_SLUG, safe='')}/manifest"
    )


def translated_url(language: str, base_url: str = DEFAULT_BASE_URL, mode: str = DEFAULT_MODE) -> str:
    code = normalize_language(language)
    locale = LOCALE_MAP.get(code)
    if not locale:
        raise ValueError(f"source language has no translated endpoint: {code}")
    return (
        f"{base_url.rstrip('/')}/api/v1/orgs/{quote(ORG_SLUG, safe='')}"
        f"/projects/{quote(PROJECT_SLUG, safe='')}"
        f"/files/{quote(FILE_ID, safe='')}/translated"
        f"?locale={quote(locale, safe='')}&mode={quote(mode, safe='')}"
    )


def validate_manifest(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("lang"), dict):
        raise ValueError("manifest missing lang object")
    return data


def validate_catalog(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("texts"), dict):
        raise ValueError("language catalog missing texts object")
    texts = data["texts"]
    cleaned = {}
    for key, value in texts.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("language catalog texts must be string-to-string")
        cleaned[key] = value
    result = dict(data)
    result["texts"] = cleaned
    return result


def _response_json(response: requests.Response, *, kind: str) -> object:
    response.raise_for_status()
    body = response.content
    if len(body) > MAX_CATALOG_BYTES:
        raise ValueError(f"{kind} response too large: {len(body)} bytes")
    try:
        return json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {kind} JSON: {exc}") from exc


def atomic_write_json(path: Path, data: dict) -> bool:
    """Atomically publish JSON. Returns whether file content changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    try:
        if path.is_file() and path.read_bytes() == payload:
            return False
    except OSError:
        pass

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        return True
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def load_cached_manifest(data_path: Optional[str] = None) -> Optional[dict]:
    path = manifest_cache_path(data_path)
    try:
        return validate_manifest(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None


def available_languages(data_path: Optional[str] = None) -> list[dict]:
    """Map cached manifest locales to stable Launcher language codes."""
    manifest = load_cached_manifest(data_path)
    result = [{"code": "zh-cn", "name": DISPLAY_NAMES["zh-cn"]}]
    if not manifest:
        return result
    for api_locale, info in manifest["lang"].items():
        launcher_code = API_TO_LAUNCHER.get(api_locale)
        if not launcher_code:
            continue
        name = DISPLAY_NAMES.get(launcher_code)
        if not name and isinstance(info, dict):
            name = str(info.get("name") or launcher_code)
        result.append({"code": launcher_code, "name": name or launcher_code})
    return result


def sync_language(language: str, *, session: Optional[requests.Session] = None) -> dict:
    """Synchronously refresh manifest and one translated catalog.

    Intended for worker threads and tests. On any failure the old cache remains
    untouched. The returned dict is suitable for a Qt signal/callback.
    """
    try:
        code = normalize_language(language)
    except ValueError as exc:
        return {"ok": False, "updated": False, "language": str(language), "error": str(exc)}

    settings = _settings()
    if not settings["enabled"]:
        return {"ok": False, "updated": False, "language": code, "error": "disabled"}

    own_session = session is None
    client = session or _session()
    manifest_ok = False
    manifest_changed = False
    try:
        try:
            response = client.get(
                manifest_url(settings["baseUrl"]),
                timeout=settings["timeout"],
                proxies=_proxies(),
            )
            manifest = validate_manifest(_response_json(response, kind="manifest"))
            manifest_changed = atomic_write_json(manifest_cache_path(), manifest)
            manifest_ok = True
        except Exception as exc:
            # Stable locale/file mapping still permits translated fetch.
            log(f"[live-i18n] manifest 获取失败，继续尝试译文: {exc}")

        if code == "zh-cn":
            return {
                "ok": manifest_ok,
                "updated": manifest_changed,
                "language": code,
                "source": True,
                "error": "" if manifest_ok else "manifest unavailable",
            }

        response = client.get(
            translated_url(code, settings["baseUrl"], settings["mode"]),
            timeout=settings["timeout"],
            proxies=_proxies(),
        )
        catalog = validate_catalog(_response_json(response, kind="translated catalog"))
        changed = atomic_write_json(cached_language_path(code), catalog)
        filled = sum(bool(value.strip()) for value in catalog["texts"].values())
        log(
            f"[live-i18n] 同步完成 language={code} keys={len(catalog['texts'])} "
            f"non_empty={filled} changed={changed}"
        )
        return {
            "ok": True,
            "updated": changed,
            "language": code,
            "path": str(cached_language_path(code)),
            "error": "",
        }
    except Exception as exc:
        log(f"[live-i18n] 同步失败 language={code}: {exc}")
        return {"ok": False, "updated": False, "language": code, "error": str(exc)}
    finally:
        if own_session:
            client.close()


def refresh_language_async(language: str, callback: Optional[Callable[[dict], None]] = None) -> bool:
    """Refresh in a daemon thread, deduplicating concurrent requests per locale."""
    try:
        code = normalize_language(language)
    except ValueError as exc:
        if callback:
            callback({"ok": False, "updated": False, "language": str(language), "error": str(exc)})
        return False

    with _inflight_lock:
        if code in _inflight_callbacks:
            if callback:
                _inflight_callbacks[code].append(callback)
            return False
        _inflight_callbacks[code] = [callback] if callback else []

    def worker() -> None:
        result = sync_language(code)
        with _inflight_lock:
            callbacks = _inflight_callbacks.pop(code, [])
        for done in callbacks:
            try:
                done(result)
            except Exception as exc:
                log(f"[live-i18n] 完成回调失败 language={code}: {exc}")

    threading.Thread(
        target=worker,
        daemon=True,
        name=f"LiveI18n-{code}",
    ).start()
    return True
