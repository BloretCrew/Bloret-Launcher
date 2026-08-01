import hashlib
import json
import re
import shutil
import stat
import urllib.parse
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
import logging, os, subprocess, tempfile, requests, sys, zipfile
# 以下导入的部分是 Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.的模块，位于 modules 中
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText
import modules.globals as BLglobals
from modules.process_utils import hidden_process_kwargs
from modules.paths import app_path, get_app_dir


def _pick_download_url(res):
    """
    Choose a platform-appropriate download URL from API info payload.

    Supported shapes:
      downloads.stable = "https://..."
      downloads.stable = {"gitcode": "...", "github": "...", ...}
      downloads.stable = {"windows": "...", "linux": "...", "freebsd": "...", "macos": "..."}
      downloads.stable = {"windows": {"gitcode": "..."}, "freebsd": {"github": "..."}}
    """
    from modules.platform_compat import is_darwin, is_freebsd, is_linux, is_windows, update_artifact_kind

    downloads = res.get("downloads") or {}
    stable = downloads.get("stable")
    kind = update_artifact_kind()

    def _from_mapping(mapping):
        if not isinstance(mapping, dict):
            return None
        # Prefer platform keys
        platform_keys = []
        if is_windows():
            platform_keys = ["windows", "win", "win32"]
        elif is_freebsd():
            platform_keys = ["freebsd", "FreeBSD", "bsd"]
        elif is_darwin():
            platform_keys = ["macos", "darwin", "osx", "mac"]
        elif is_linux():
            platform_keys = ["linux"]
        for key in platform_keys:
            val = mapping.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, dict):
                for nested_key in ("github", "gitcode", "url", "direct"):
                    nested = val.get(nested_key)
                    if isinstance(nested, str) and nested.strip():
                        return nested.strip()
        # Legacy flat mirror keys (usually Windows installer)
        if is_windows():
            for nested_key in ("gitcode", "github", "url", "direct"):
                nested = mapping.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
        return None

    if isinstance(stable, str) and stable.strip():
        url = stable.strip()
        # Never feed a Windows installer URL to non-Windows hosts
        if not is_windows() and url.lower().endswith(".exe"):
            return None, kind
        return url, kind

    if isinstance(stable, dict):
        url = _from_mapping(stable)
        if url:
            if not is_windows() and url.lower().endswith(".exe"):
                return None, kind
            return url, kind

    return None, kind


def _find_url_metadata(payload, selected_url):
    """Return the closest metadata mapping and key that selected the exact URL."""
    if not isinstance(payload, dict):
        return None, None
    for key, value in payload.items():
        if isinstance(value, str) and value.strip() == selected_url:
            return payload, key
        if isinstance(value, dict):
            direct_url = value.get("url") or value.get("direct")
            if isinstance(direct_url, str) and direct_url.strip() == selected_url:
                return value, key
            found, selected_key = _find_url_metadata(value, selected_url)
            if found is not None:
                return found, selected_key
    return None, None


def _extract_bound_sha256(metadata, selected_key=None):
    """Read a hash explicitly attached to the selected URL or its mirror group."""
    if not isinstance(metadata, dict):
        return ""
    selected_value = metadata.get(selected_key) if selected_key else None
    if isinstance(selected_value, dict):
        digest = _extract_sha256(selected_value)
        if digest:
            return digest
    for field in ("sha256", "sha256sum", "hashes", "checksums"):
        value = metadata.get(field)
        if isinstance(value, dict) and selected_key:
            candidate = value.get(selected_key)
            if isinstance(candidate, dict):
                candidate = candidate.get("sha256")
            text = str(candidate or "").strip().lower()
            if text:
                if not _SHA256_RE.fullmatch(text):
                    raise ValueError("更新 SHA-256 元数据格式无效")
                return text
    return _extract_sha256(metadata)


def resolve_update_artifact(res):
    """Resolve an artifact and bind integrity metadata to its exact selected URL."""
    url, kind = _pick_download_url(res)
    if not url:
        return None
    parsed_path = urllib.parse.urlparse(url).path
    filename = os.path.basename(parsed_path) or f"Bloret-Launcher-Update-{res.get('latestVersion', 'latest')}"
    downloads = res.get("downloads") if isinstance(res, dict) else {}
    stable = downloads.get("stable") if isinstance(downloads, dict) else None
    metadata, selected_key = _find_url_metadata(stable, url)
    sha256 = _extract_bound_sha256(metadata, selected_key)
    if not sha256 and isinstance(stable, str) and stable.strip() == url:
        sha256 = _extract_sha256(downloads) or _extract_sha256(res)
    return {
        "url": url,
        "kind": kind,
        "filename": filename,
        "version": str(res.get("latestVersion", "latest")),
        "sha256": sha256,
    }


_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_MAX_ZIP_MEMBERS = 20000
_MAX_ZIP_FILE_SIZE = 1024 * 1024 * 1024
_MAX_ZIP_TOTAL_SIZE = 4 * 1024 * 1024 * 1024


def _extract_sha256(payload):
    """Read a compatible SHA-256 field from update metadata."""
    if not isinstance(payload, dict):
        return ""
    candidates = [
        payload.get("sha256"), payload.get("sha256sum"),
        (payload.get("hashes") or {}).get("sha256") if isinstance(payload.get("hashes"), dict) else None,
        (payload.get("checksums") or {}).get("sha256") if isinstance(payload.get("checksums"), dict) else None,
    ]
    for value in candidates:
        text = str(value or "").strip().lower()
        if text:
            if not _SHA256_RE.fullmatch(text):
                raise ValueError("更新 SHA-256 元数据格式无效")
            return text
    return ""


def verify_update_sha256(file_path, expected_sha256):
    if not expected_sha256:
        log("更新服务未提供 SHA-256；仅进行 HTTPS 传输校验", logging.WARNING)
        return True
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected_sha256.lower():
        raise ValueError(f"更新包 SHA-256 不匹配: expected={expected_sha256}, actual={actual}")
    return True


def safe_extract_update_zip(zip_path, destination):
    """Extract regular files/directories only, rejecting traversal and zip bombs."""
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    total_size = 0
    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.infolist()
        if len(members) > _MAX_ZIP_MEMBERS:
            raise ValueError("更新 ZIP 文件数量超过安全限制")
        for info in members:
            raw_name = info.filename
            if "\x00" in raw_name:
                raise ValueError("更新 ZIP 包含非法文件名")
            name = raw_name.replace("\\", "/")
            if name.startswith(("/", "//")) or re.match(r"^[A-Za-z]:", name):
                raise ValueError(f"更新 ZIP 包含绝对路径: {raw_name}")
            parts = [part for part in name.split("/") if part not in ("", ".")]
            if any(part == ".." for part in parts):
                raise ValueError(f"更新 ZIP 包含路径穿越: {raw_name}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError(f"更新 ZIP 包含不支持的文件类型: {raw_name}")
            if info.flag_bits & 0x1:
                raise ValueError("不支持加密更新 ZIP")
            if info.file_size > _MAX_ZIP_FILE_SIZE:
                raise ValueError(f"更新 ZIP 单文件过大: {raw_name}")
            total_size += info.file_size
            if total_size > _MAX_ZIP_TOTAL_SIZE:
                raise ValueError("更新 ZIP 解压总大小超过安全限制")
            target = (root.joinpath(*parts)).resolve()
            try:
                target.relative_to(root)
            except ValueError as error:
                raise ValueError(f"更新 ZIP 路径越界: {raw_name}") from error
            if info.is_dir() or raw_name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, open(target, "wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
    return root


def download_update_artifact(artifact, progress_callback=None):
    """Download to .part, verify SHA-256, then atomically publish in temp."""
    url = artifact["url"]
    if urllib.parse.urlparse(url).scheme.lower() != "https":
        raise ValueError("更新包仅允许 HTTPS 下载")
    temp_dir = tempfile.gettempdir()
    destination = os.path.join(temp_dir, artifact["filename"])
    part_path = destination + ".part"
    digest = hashlib.sha256()
    downloaded = 0
    try:
        with requests.get(url, stream=True, timeout=(10, 60)) as response:
            response.raise_for_status()
            if urllib.parse.urlparse(response.url).scheme.lower() != "https":
                raise ValueError("更新下载被重定向到非 HTTPS 地址")
            total = int(response.headers.get("content-length", 0) or 0)
            with open(part_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
                handle.flush()
                os.fsync(handle.fileno())
        expected = artifact.get("sha256") or ""
        if not expected:
            raise ValueError("更新服务未提供 SHA-256，已拒绝执行更新包")
        actual = digest.hexdigest()
        if actual != expected.lower():
            raise ValueError(f"更新包 SHA-256 不匹配: expected={expected}, actual={actual}")
        os.replace(part_path, destination)
        return destination
    except Exception:
        try:
            os.remove(part_path)
        except OSError:
            pass
        raise


def _apply_zip_update(zip_path):
    """Validate and stage a ZIP, journaling every mutation for rollback."""
    target = Path(get_app_dir()).resolve()
    staging = Path(tempfile.mkdtemp(prefix=".bloret-update-", dir=str(target.parent)))
    backup = Path(tempfile.mkdtemp(prefix=".bloret-backup-", dir=str(target.parent)))
    journal = []
    created_directories = []
    rollback_failed = False
    log(f"安全解压更新包到暂存目录: {staging}")
    try:
        safe_extract_update_zip(zip_path, staging)
        for source in sorted(staging.rglob("*"), key=lambda p: (p.is_file(), len(p.parts))):
            relative = source.relative_to(staging)
            destination = target / relative
            resolved_parent = destination.parent.resolve()
            try:
                resolved_parent.relative_to(target)
            except ValueError as error:
                raise ValueError(f"更新目标通过符号链接越界: {relative}") from error
            if source.is_dir():
                if not destination.exists():
                    destination.mkdir(parents=True, exist_ok=True)
                    created_directories.append(destination)
                continue
            missing_parents = []
            parent = destination.parent
            while parent != target and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            created_directories.extend(reversed(missing_parents))

            backup_path = backup / relative
            entry = {
                "destination": destination,
                "backup": backup_path,
                "backup_moved": False,
                "new_installed": False,
            }
            journal.append(entry)
            if destination.exists() or destination.is_symlink():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, backup_path)
                entry["backup_moved"] = True
            os.replace(source, destination)
            entry["new_installed"] = True
    except Exception:
        for entry in reversed(journal):
            destination = entry["destination"]
            backup_path = entry["backup"]
            try:
                if entry["new_installed"] and (destination.exists() or destination.is_symlink()):
                    destination.unlink()
                if entry["backup_moved"] and (backup_path.exists() or backup_path.is_symlink()):
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup_path, destination)
            except OSError as rollback_error:
                rollback_failed = True
                log(f"更新回滚失败: {destination}: {rollback_error}", logging.ERROR)
        for directory in sorted(set(created_directories), key=lambda p: len(p.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        if rollback_failed:
            log(f"更新备份已保留以便手动恢复: {backup}", logging.ERROR)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        if not rollback_failed:
            shutil.rmtree(backup, ignore_errors=True)
    return target


def _request_application_exit(owner, restart=False):
    """Route updater exits through launcher lifecycle hooks when available."""
    candidates = [owner, getattr(owner, "parent", None)]
    method_name = "restart_app" if restart else "quit_app"
    for candidate in candidates:
        method = getattr(candidate, method_name, None)
        if callable(method):
            method()
            return True
    from PySide6.QtWidgets import QApplication

    QApplication.quit()
    return False


def update_to_latest_version(self):
    try:
        # 导入win11toast模块，用于显示进度通知
        from modules.win11toast import notify, update_progress
        from modules.platform_compat import is_windows, update_artifact_kind

        kind = update_artifact_kind()

        # 初始化通知
        notify(progress={
            'title': '正在准备更新...',
            'status': '正在获取最新版本信息...',
            'value': '0',
            'valueStringOverride': '0%',
            'icon': app_path('bloret.ico')
        })

        # 1. 向API获取信息
        update_progress({
            'value': 10 / 100,
            'valueStringOverride': '10%',
            'status': '正在获取最新版本信息...'
        })
        
        # 记录请求URL
        log(f"请求URL: {BLglobals.server_ip}:3001/api/info")
        
        # 发送GET请求
        response = requests.get(f"{BLglobals.server_ip}:3001/api/info", timeout=5)
        response.raise_for_status()
        res = response.json()
        
        # 获取下载链接（按平台）及完整性信息
        artifact = resolve_update_artifact(res)
        download_url = artifact["url"] if artifact else None
        kind = artifact["kind"] if artifact else kind
        version = res.get("latestVersion", "latest")

        if not download_url:
            if kind == "freebsd_zip":
                message = (
                    "当前 FreeBSD 尚无服务端提供的自动更新包。"
                    "请从 GitHub Releases 下载 Bloret-Launcher-FreeBSD-amd64.zip，"
                    "或使用 git pull / 重新安装源码更新。"
                    "不会下载 Windows 安装程序。"
                )
            elif kind == "linux_zip":
                message = (
                    "未找到适用于 Linux 的更新包 URL。"
                    "请从 GitHub Releases 下载 Bloret-Launcher-Linux 产物，或使用系统包管理器更新。"
                )
            elif kind == "macos_zip":
                message = "未找到适用于 macOS 的更新包 URL。请从 GitHub Releases 手动下载。"
            else:
                message = "未找到适用于当前平台的更新下载地址。"
            log(message, logging.WARNING)
            if hasattr(self, 'parent') and self.parent:
                QMessageBox.information(self.parent, i18nText("更新"), message)
            else:
                QMessageBox.information(None, i18nText("更新"), message)
            return
        
        # 更新通知
        notify(progress={
            'title': f'正在更新 Bloret Launcher 至 {version}',
            'status': res.get("newVersionDescription", ""),
            'value': '0',
            'valueStringOverride': '0%',
            'icon': app_path('bloret.ico')
        })

        # 更新进度
        update_progress({
            'value': 20 / 100,
            'valueStringOverride': '20%',
            'status': '正在下载更新文件...'
        })
        
        # 2. 安全下载到 .part，校验后原子发布
        last_progress = 0
        def _download_progress(downloaded_size, total_size):
            nonlocal last_progress
            if total_size > 0:
                progress = 20 + (downloaded_size / total_size) * 60
                if progress - last_progress >= 5:
                    update_progress({
                        'value': progress / 100,
                        'valueStringOverride': f'{progress:.1f}%',
                        'status': f'正在下载更新文件... ({downloaded_size}/{total_size} bytes)'
                    })
                    last_progress = progress

        file_name = download_update_artifact(artifact, _download_progress)
        temp_dir = os.path.dirname(file_name)
        
        # 更新进度
        update_progress({
            'value': 80 / 100,
            'valueStringOverride': '80%',
            'status': '下载完成，准备安装...'
        })
        
        # 3. 安装并退出
        update_progress({
            'value': 90 / 100,
            'valueStringOverride': '90%',
            'status': '正在应用更新...'
        })

        if is_windows() and file_name.lower().endswith(".exe"):
            subprocess.Popen([file_name, "--quickstart"], **hidden_process_kwargs())
            _request_application_exit(self, restart=False)
            return

        if file_name.lower().endswith(".zip"):
            _apply_zip_update(file_name)
            _request_application_exit(self, restart=True)
            return

        # AppImage / other: leave for user to replace, open folder
        log(f"已下载更新文件: {file_name}（需手动替换当前安装）")
        try:
            from modules.platform_compat import open_path_command

            subprocess.Popen(open_path_command(temp_dir))
        except Exception:
            pass
        if hasattr(self, 'parent') and self.parent:
            QMessageBox.information(
                self.parent,
                i18nText("更新"),
                f"更新文件已下载到:\n{file_name}\n请手动替换当前安装后重启。",
            )
        _request_application_exit(self, restart=False)
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"更新失败: {str(e)}", logging.ERROR)
        # 如果有父窗口，显示错误消息框
        if hasattr(self, 'parent') and self.parent:
            QMessageBox.critical(self.parent, "更新失败", f"更新过程中发生错误:\n{str(e)}")
