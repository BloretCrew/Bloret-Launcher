import json
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


def _apply_zip_update(zip_path):
    """Extract zip over the application directory and restart."""
    target = str(get_app_dir())
    log(f"解压更新包到: {target}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target)
    # Prefer restart helper if available
    try:
        from modules.systems import restart

        restart()
    except Exception as e:
        log(f"restart() 失败，直接退出以便用户手动启动: {e}", logging.WARNING)
        sys.exit(0)


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
        
        # 获取下载链接（按平台）
        download_url, kind = _pick_download_url(res)
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
        
        # 2. 下载文件到临时目录
        temp_dir = tempfile.gettempdir()
        if is_windows() and download_url.lower().endswith(".exe"):
            file_name = os.path.join(temp_dir, f"Bloret-Launcher-Setup-{version}.exe")
        else:
            # zip / AppImage / other
            suffix = ".zip"
            lower = download_url.lower()
            for ext in (".zip", ".appimage", ".tar.gz", ".tgz", ".dmg"):
                if lower.endswith(ext):
                    suffix = ext
                    break
            file_name = os.path.join(temp_dir, f"Bloret-Launcher-Update-{version}{suffix}")
        
        # 下载文件并实时更新进度
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            last_progress = 0
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        # 计算进度 (20% - 80%之间)
                        progress = 20 + (downloaded_size / total_size) * 60
                        # 每5%更新一次进度，避免过于频繁的更新影响下载速度
                        if progress - last_progress >= 5:
                            update_progress({
                                'value': progress / 100,
                                'valueStringOverride': f'{progress:.1f}%',
                                'status': f'正在下载更新文件... ({downloaded_size}/{total_size} bytes)'
                            })
                            last_progress = progress
        
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
            sys.exit(0)

        if file_name.lower().endswith(".zip"):
            _apply_zip_update(file_name)
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
        sys.exit(0)
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"更新失败: {str(e)}", logging.ERROR)
        # 如果有父窗口，显示错误消息框
        if hasattr(self, 'parent') and self.parent:
            QMessageBox.critical(self.parent, "更新失败", f"更新过程中发生错误:\n{str(e)}")
