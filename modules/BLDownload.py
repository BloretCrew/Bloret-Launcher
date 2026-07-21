"""
Legacy zip-pack Minecraft download path (Bloret-Launcher-Old).

Current QML UI uses modules.install.InstallMinecraftVersion instead.
Kept only for backward compatibility with the Old entrypoint.
"""

from PySide6.QtWidgets import QDialog, QApplication, QProgressBar, QMessageBox
from PySide6.QtCore import QThread, Signal as pyqtSignal, QTimer
from modules.win11toast import notify, update_progress
from modules.notification import send_notification
import logging
import os
import stat
import time
import threading
import requests
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.safe import handle_exception
from modules.log import log
from modules.i18n import i18nText
from modules.paths import app_path
import modules.globals as BLglobals

_DOWNLOAD_TIMEOUT = (10, 60)


def _safe_destination(root, member_name):
    """Return a member destination only when it stays below root."""
    if not member_name or os.path.isabs(member_name):
        raise ValueError(f"压缩包包含非法绝对路径: {member_name!r}")
    normalized = member_name.replace("\\", "/")
    if normalized.startswith("/") or normalized.split("/", 1)[0].endswith(":"):
        raise ValueError(f"压缩包包含非法路径: {member_name!r}")
    root_real = os.path.realpath(root)
    destination = os.path.realpath(os.path.join(root_real, normalized))
    if os.path.commonpath((root_real, destination)) != root_real:
        raise ValueError(f"压缩包路径越界: {member_name!r}")
    return destination


def _safe_extract_zip(archive_path, target_dir):
    """Extract ZIP entries after rejecting traversal and link entries."""
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            _safe_destination(target_dir, info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"ZIP 包含不允许的符号链接: {info.filename}")
        for info in archive.infolist():
            destination = _safe_destination(target_dir, info.filename)
            if info.is_dir():
                os.makedirs(destination, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with archive.open(info, "r") as source, open(destination, "wb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)


def _download_atomic(url, file_path, progress_callback):
    """Download to .part, close the response, then atomically publish it."""
    if not url.lower().startswith("https://"):
        raise ValueError(f"拒绝非 HTTPS 下载地址: {url}")
    part_path = file_path + ".part"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with requests.get(url, stream=True, timeout=_DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            if total_size <= 0:
                log(f"文件 {os.path.basename(file_path)} 未返回 content-length，下载进度将显示已下载大小", logging.WARNING)
            with open(part_path, "wb") as output:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    output.write(chunk)
                    downloaded_size += len(chunk)
                    progress_callback(downloaded_size, total_size)
                output.flush()
                os.fsync(output.fileno())
            if total_size > 0 and downloaded_size != total_size:
                raise IOError(f"下载大小不匹配: 预期 {total_size}，实际 {downloaded_size}")
        os.replace(part_path, file_path)
        log(f"文件已原子写入: {file_path}")
    except Exception:
        try:
            if os.path.exists(part_path):
                os.remove(part_path)
                log(f"已清理未完成下载: {part_path}")
        except OSError as cleanup_error:
            log(f"清理未完成下载失败 {part_path}: {cleanup_error}", logging.WARNING)
        raise


def BL_download(self, version, LM_download_way_choose, LM_Download_Way_minecraft, LM_Download_Way_version, parent):
    def _emit_progress(progress_signal, progress_key, downloaded_size, total_size, message_prefix="下载进度"):
        if total_size > 0:
            progress = int(downloaded_size / total_size * 100)
            progress_signal.emit(progress_key, progress, f"{message_prefix}: {progress}%")
            update_progress({"value": progress / 100, "valueStringOverride": f"{progress}%"})
        else:
            progress_signal.emit(progress_key, 0, f"{message_prefix}: 已下载 {downloaded_size // 1024} KB")

    class BLDownloadDialog(QDialog):
        def __init__(self, selected_version, parent=None):
            super().__init__(parent)
            self.version = selected_version
            self.setWindowTitle("Bloret Launcher")
            keys = ("version", "libraries", "objects1", "objects2", "objects3", "objects4", "indexes")
            if os.path.exists(app_path(".minecraft")):
                keys = ("version",)
                log(i18nText(".minecraft 文件夹已存在"))
            else:
                log(i18nText(".minecraft 文件夹不存在"))
            self.progress_bars = {key: self.findChild(QProgressBar, key) for key in keys}
            self.threads = []

        def update_progress(self, key, value, message):
            if self.progress_bars.get(key):
                self.progress_bars[key].setValue(value)
            QApplication.processEvents()

        def closeEvent(self, event):
            for active_thread in self.threads:
                if active_thread.isRunning():
                    active_thread.requestInterruption()
                    active_thread.quit()
                    active_thread.wait()
            event.accept()

    class VersionDownloadThread(QThread):
        progress_signal = pyqtSignal(str, int, str)
        error_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, selected_version, minecraft_dir):
            super().__init__()
            self.version = selected_version
            BLglobals.minecraft_dir = minecraft_dir
            self.base_url = LM_Download_Way_minecraft.get(LM_download_way_choose)
            log(f"下载链接:{self.base_url}")

        def run(self):
            try:
                minecraft_dir = BLglobals.minecraft_dir
                log(f"开始下载版本 {self.version}，目标目录: {minecraft_dir}")
                if not os.path.exists(minecraft_dir):
                    log(i18nText(".minecraft 文件夹不存在，开始下载 Minecraft 核心"))
                    if not self.BL_download_minecraft():
                        raise RuntimeError(i18nText("下载 Minecraft 核心失败，请检查日志。"))
                else:
                    log(i18nText(".minecraft 文件夹已存在"))

                version_dir = os.path.join(minecraft_dir, "versions", self.version)
                os.makedirs(version_dir, exist_ok=True)
                file_name = f"{self.version}.zip"
                file_path = os.path.join(version_dir, file_name)
                notify(progress={
                    "title": f"下载版本 {self.version}", "status": i18nText("正在下载... ↓"),
                    "value": "0", "valueStringOverride": "0%", "icon": app_path("bloret.ico")
                })
                base_url = LM_Download_Way_version.get(LM_download_way_choose)
                if not base_url:
                    raise ValueError("未配置版本下载地址")
                url = base_url + file_name
                log(f"下载链接:{url}")
                _download_atomic(
                    url, file_path,
                    lambda downloaded, total: _emit_progress(self.progress_signal, "version", downloaded, total),
                )
                log(f"文件 {file_name} 下载完成，开始安全解压缩")
                _safe_extract_zip(file_path, version_dir)
                os.remove(file_path)
                log(f"文件 {file_name} 解压完成并已删除安装包")
                self.finished_signal.emit()
                update_progress({"status": i18nText("下载完成！✅"), "value": 100, "valueStringOverride": "100%"})
            except Exception as error:
                handle_exception(error)
                log(f"下载版本 {self.version} 时发生错误: {error}", logging.ERROR)
                self.error_signal.emit(str(error))

        def ensure_minecraft_dir(self):
            os.makedirs(BLglobals.minecraft_dir, exist_ok=True)
            log(f"Minecraft 文件夹已就绪: {BLglobals.minecraft_dir}")

        def BL_download_minecraft(self):
            self.ensure_minecraft_dir()
            assets_dir = os.path.join(BLglobals.minecraft_dir, "assets")
            files_to_download = [
                ("indexes.zip", os.path.join(assets_dir, "indexes"), "indexes"),
                ("libraries.zip", os.path.join(BLglobals.minecraft_dir, "libraries"), "libraries"),
                ("objects-01.zip", os.path.join(assets_dir, "objects"), "objects1"),
                ("objects-02.zip", os.path.join(assets_dir, "objects"), "objects2"),
                ("objects-03.zip", os.path.join(assets_dir, "objects"), "objects3"),
                ("objects-04.zip", os.path.join(assets_dir, "objects"), "objects4"),
            ]
            for _, target_dir, _ in files_to_download:
                os.makedirs(target_dir, exist_ok=True)
            base_url = LM_Download_Way_minecraft.get(LM_download_way_choose)
            if not base_url:
                log("未配置 Minecraft 核心下载地址", logging.ERROR)
                return False
            log_lock = threading.Lock()

            def download_file(file_name, target_dir, progress_key):
                url = base_url + file_name
                file_path = os.path.join(target_dir, file_name)
                for attempt in range(1, 6):
                    try:
                        with log_lock:
                            log(f"下载链接:{url}，尝试 {attempt}/5")
                        _download_atomic(
                            url, file_path,
                            lambda downloaded, total: _emit_progress(self.progress_signal, progress_key, downloaded, total),
                        )
                        return file_path
                    except Exception as error:
                        handle_exception(error)
                        log(f"下载 {file_name} 失败 (尝试 {attempt}/5): {error}", logging.ERROR)
                        if attempt < 5:
                            time.sleep(3)
                raise RuntimeError(f"下载 {file_name} 失败，已达到最大重试次数")

            failures = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_names = {
                    executor.submit(download_file, file_name, target_dir, progress_key): file_name
                    for file_name, target_dir, progress_key in files_to_download
                }
                for future in as_completed(future_names):
                    try:
                        future.result()
                    except Exception as error:
                        failures.append((future_names[future], error))
                        log(f"并发下载任务失败 {future_names[future]}: {error}", logging.ERROR)
            if failures:
                log("至少一个核心下载任务失败，取消全部解压流程", logging.ERROR)
                return False

            expected_paths = [os.path.join(target_dir, file_name) for file_name, target_dir, _ in files_to_download]
            if any(not os.path.isfile(path) or os.path.exists(path + ".part") for path in expected_paths):
                log("下载结果存在缺失文件或 .part 文件，取消解压", logging.ERROR)
                return False
            try:
                for (file_name, target_dir, _), file_path in zip(files_to_download, expected_paths):
                    _safe_extract_zip(file_path, target_dir)
                    log(f"文件 {file_name} 安全解压完成")
                for file_path in expected_paths:
                    os.remove(file_path)
                    log(f"删除文件: {file_path}")
            except Exception as error:
                handle_exception(error)
                log(f"解压文件失败: {error}", logging.ERROR)
                return False
            log(i18nText("所有文件下载和解压完成"))
            return True

    download_dialog = BLDownloadDialog(version, parent)
    minecraft_dir = app_path(".minecraft")
    log(f"BL_download 创建下载线程，Minecraft 目录: {minecraft_dir}")
    thread = VersionDownloadThread(version, minecraft_dir)
    thread.finished.connect(lambda t=thread: self.threads.remove(t) if t in self.threads else None)
    self.threads.append(thread)
    download_dialog.threads.append(thread)
    thread.progress_signal.connect(download_dialog.update_progress)

    def download_failed(error):
        log(f"下载失败: {error}", logging.ERROR)
        QMessageBox.critical(download_dialog, i18nText("下载失败"), f"下载过程中发生错误: {error}")
        send_notification(i18nText("下载失败"), f"版本 {version} 下载出错: {error}", category="download")
        QTimer.singleShot(0, download_dialog.reject)

    def download_finished():
        log(f"下载完成: 版本 {version}")
        send_notification(i18nText("下载完成"), f"版本 {version} 已成功下载", category="download")
        QTimer.singleShot(0, download_dialog.accept)
        log(i18nText("下载完成处理结束"))

    thread.error_signal.connect(download_failed)
    thread.finished_signal.connect(download_finished)
    thread.start()
    download_dialog.exec()
    return 0
