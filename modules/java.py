import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import zipfile
from threading import Thread

import requests

from modules.win11toast import update_progress, notify
import modules.config as cfg
from modules.notification import send_notification as _send_notification
from modules.log import log
from modules.i18n import i18nText
import modules.globals as BLglobals
from modules.process_utils import hidden_process_kwargs

_DOWNLOAD_TIMEOUT = (10, 120)
_MSI_SUCCESS_CODES = {0, 1641, 3010}


def send_notification(title, body):
    _send_notification(title, body, category="install")


java_versions = {
    "25": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu25.30.17-ca-jdk25.0.1-win_x64.msi"}},
    "24": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu24.32.13-ca-jdk24.0.2-win_x64.msi"}},
    "21": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu21.44.17-ca-jdk21.0.8-win_x64.msi"}},
    "17": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu17.60.17-ca-jdk17.0.16-win_x64.msi"}},
    "11": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu11.82.19-ca-jdk11.0.28-win_x64.msi"}},
    "8": {"Windows": {"x64": "https://cdn.azul.com/zulu/bin/zulu8.88.0.19-ca-jdk8.0.462-win_x64.msi"}},
}


def _safe_destination(root, member_name):
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
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            _safe_destination(target_dir, info.filename)
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f"ZIP 包含不允许的符号链接: {info.filename}")
        for info in archive.infolist():
            destination = _safe_destination(target_dir, info.filename)
            if info.is_dir():
                os.makedirs(destination, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with archive.open(info, "r") as source, open(destination, "wb") as output:
                shutil.copyfileobj(source, output)


def _safe_extract_tar(archive_path, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    with tarfile.open(archive_path, "r:*") as archive:
        members = archive.getmembers()
        for member in members:
            _safe_destination(target_dir, member.name)
            if member.issym() or member.islnk():
                raise ValueError(f"TAR 包含不允许的符号/硬链接: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"TAR 包含不支持的特殊文件: {member.name}")
        for member in members:
            destination = _safe_destination(target_dir, member.name)
            if member.isdir():
                os.makedirs(destination, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"无法读取 TAR 成员: {member.name}")
            with source, open(destination, "wb") as output:
                shutil.copyfileobj(source, output)


def _download_atomic(url, destination, progress_callback):
    if not url.lower().startswith("https://"):
        raise ValueError(f"拒绝非 HTTPS 下载地址: {url}")
    part_path = destination + ".part"
    try:
        with requests.get(url, stream=True, timeout=_DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
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
        os.replace(part_path, destination)
        log(f"Java 安装包已原子写入: {destination}")
    except Exception:
        try:
            if os.path.exists(part_path):
                os.remove(part_path)
        except OSError as cleanup_error:
            log(f"清理未完成 Java 下载失败: {cleanup_error}")
        raise


def _is_windows_x64():
    machine = platform.machine().lower()
    return os.name == "nt" and machine in {"amd64", "x86_64"}


def _java_major_version(version_output):
    """Parse the Java major version from `java -version` output."""
    match = re.search(r'version\s+"([^"]+)"', version_output, re.IGNORECASE)
    if not match:
        match = re.search(r'openjdk\s+([0-9][^\s]*)', version_output, re.IGNORECASE)
    if not match:
        return None
    version_text = match.group(1)
    parts = version_text.split(".")
    try:
        return int(parts[1] if parts[0] == "1" and len(parts) > 1 else parts[0])
    except ValueError:
        return None


def _validate_java(java_path, expected_version):
    if not java_path or not os.path.isfile(java_path):
        return False
    try:
        result = subprocess.run(
            [java_path, "-version"], capture_output=True, text=True, timeout=15,
            **hidden_process_kwargs(),
        )
        version_output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        detected_version = _java_major_version(version_output)
        log(
            f"探测 Java: {java_path}，退出码: {result.returncode}，"
            f"探测主版本: {detected_version}，请求主版本: {expected_version}"
        )
        if version_output:
            log(f"Java 版本输出: {version_output}")
        if result.returncode != 0:
            return False
        if detected_version != int(expected_version):
            log(f"忽略版本不匹配的 Java: {java_path}")
            return False
        return True
    except Exception as error:
        log(f"探测 Java 失败 {java_path}: {error}")
        return False


def _find_installed_java(version_key):
    candidates = []
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidates.append(os.path.join(java_home, "bin", "java.exe"))
    path_java = shutil.which("java.exe") or shutil.which("java")
    if path_java:
        candidates.append(path_java)
    for env_name in ("ProgramFiles", "ProgramW6432"):
        root = os.environ.get(env_name)
        if not root:
            continue
        for vendor in ("Zulu", "Java"):
            vendor_root = os.path.join(root, vendor)
            if not os.path.isdir(vendor_root):
                continue
            try:
                for directory in os.listdir(vendor_root):
                    if version_key in directory.lower() or vendor == "Zulu":
                        candidates.append(os.path.join(vendor_root, directory, "bin", "java.exe"))
            except OSError as error:
                log(f"扫描 Java 目录失败 {vendor_root}: {error}")
    seen = set()
    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized in seen:
            continue
        seen.add(normalized)
        if _validate_java(candidate, version_key):
            return os.path.abspath(candidate)
    return ""


def _find_installed_java_with_retry(version_key, attempts=6, delay=3):
    """Give MSI registration/filesystem updates a short, bounded settling period."""
    for attempt in range(1, attempts + 1):
        java_path = _find_installed_java(version_key)
        if java_path:
            return java_path
        if attempt < attempts:
            log(f"第 {attempt}/{attempts} 次未探测到 Java {version_key}，{delay} 秒后重试")
            time.sleep(delay)
    return ""


def InstallJava(Java_Version):
    thread = Thread(target=_install_java_thread, args=(Java_Version,))
    thread.start()


def _install_java_thread(Java_Version):
    log(f"开始安装 Java {Java_Version}")
    if not _is_windows_x64():
        try:
            from modules.platform_compat import is_freebsd

            if is_freebsd():
                message = (
                    f"FreeBSD 不支持自动下载安装 Java。请使用系统包，例如："
                    f"pkg install openjdk{Java_Version} 或 openjdk17 / openjdk21。"
                )
            else:
                message = (
                    "Java 自动安装仅支持 Windows x64。"
                    "请在系统中安装匹配版本的 OpenJDK，并在设置中选择 java 可执行文件。"
                )
        except Exception:
            message = "Java 自动安装仅支持 Windows x64。"
        log(message)
        send_notification(i18nText("安装失败"), message)
        return

    temp_root = os.environ.get("TEMP") or os.environ.get("TMP") or tempfile.gettempdir()
    temp_dir = os.path.join(temp_root, "Bloret-Launcher")
    os.makedirs(temp_dir, exist_ok=True)
    log(f"Java 安装临时目录: {temp_dir}")
    download_path = ""
    install_succeeded = False

    try:
        with open(BLglobals.config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        version_key = str(Java_Version) if Java_Version is not None else ""
        version_data = java_versions.get(version_key)
        if not version_data:
            raise ValueError(f"未找到 Java {Java_Version} 的下载信息。")
        download_url = version_data.get("Windows", {}).get("x64")
        if not download_url or not download_url.lower().endswith(".msi"):
            raise ValueError(f"未找到 Java {Java_Version} 的 Windows x64 MSI 下载地址。")

        file_name = os.path.basename(download_url)
        download_path = os.path.join(temp_dir, file_name)
        notify(progress={
            "title": f"正在下载 Java {Java_Version}...", "status": i18nText("正在下载..."),
            "value": "0", "valueStringOverride": "0%",
        })
        log(f"开始通过 HTTPS 下载 Java: {download_url}")
        last_logged_percent = -5

        def report_progress(downloaded_size, total_size):
            nonlocal last_logged_percent
            if total_size <= 0:
                return
            progress = downloaded_size / total_size
            percent = int(progress * 100)
            update_progress({"value": progress, "valueStringOverride": f"{percent}%"})
            if percent >= last_logged_percent + 5:
                log(f"Java 下载进度: {percent}% ({downloaded_size}/{total_size})")
                last_logged_percent = percent

        _download_atomic(download_url, download_path, report_progress)
        update_progress({"value": 1, "valueStringOverride": "100%", "status": f"Java {Java_Version} 下载完成"})
        notify(progress={
            "title": f"正在安装 Java {Java_Version}...", "status": i18nText("正在安装..."),
            "value": "0", "valueStringOverride": "0%",
        })

        msi_log_path = os.path.join(temp_dir, f"java_install_{Java_Version}.log")
        command = [
            "msiexec.exe", "/i", download_path, "/quiet", "/norestart",
            "/L*v", msi_log_path,
        ]
        log(f"执行 MSI 安装: {' '.join(command)}")
        process = subprocess.run(
            command, capture_output=True, text=True, timeout=20 * 60,
            **hidden_process_kwargs(),
        )
        log(f"MSI 安装退出码: {process.returncode}，日志: {msi_log_path}")
        if process.stdout:
            log(f"MSI 标准输出: {process.stdout.strip()}")
        if process.stderr:
            log(f"MSI 标准错误: {process.stderr.strip()}")
        if process.returncode not in _MSI_SUCCESS_CODES:
            raise RuntimeError(f"MSI 安装失败，错误码: {process.returncode}")

        reboot_message = ""
        if process.returncode == 1641:
            reboot_message = "MSI 已启动系统重启；重启后安装才会完全生效。"
        elif process.returncode == 3010:
            reboot_message = "MSI 安装已完成，但需要重启系统后才会完全生效。"
        if reboot_message:
            log(f"Java {Java_Version}: {reboot_message}")
            update_progress({
                "value": 1, "valueStringOverride": i18nText("需要重启"),
                "status": f"Java {Java_Version} 需要重启系统",
            })

        java_path = _find_installed_java_with_retry(version_key)
        if not java_path:
            detail = "有限重试后仍未探测到版本匹配且可运行的 java.exe"
            if reboot_message:
                detail += f"；{reboot_message} 当前不能确认 Java 已完整可用"
            raise RuntimeError(f"MSI 返回成功代码 {process.returncode}，但{detail}")
        log(f"成功探测到版本匹配的 java.exe: {java_path}")
        config["java_path"] = java_path
        config["Java_Path"] = java_path
        cfg.write(config)
        log(f"已统一更新 java_path 与 Java_Path: {java_path}")
        install_succeeded = True
        if reboot_message:
            update_progress({
                "value": 1, "valueStringOverride": i18nText("需要重启"),
                "status": f"Java {Java_Version} 已验证，需要重启系统",
            })
            send_notification(
                i18nText("需要重启"),
                f"Java {Java_Version} 已安装并验证可用。{reboot_message}",
            )
        else:
            update_progress({
                "value": 1, "valueStringOverride": i18nText("安装完成"),
                "status": f"Java {Java_Version} 安装成功",
            })
            send_notification(i18nText("安装成功"), f"Java {Java_Version} 安装成功。")
    except requests.RequestException as error:
        log(f"下载 Java {Java_Version} 失败: {error}")
        send_notification(i18nText("下载失败"), f"下载 Java {Java_Version} 失败: {error}")
    except (json.JSONDecodeError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        log(f"Java {Java_Version} 安装失败: {error}")
        update_progress({
            "value": 1, "valueStringOverride": i18nText("安装失败"),
            "status": f"Java {Java_Version} 安装失败",
        })
        send_notification(i18nText("安装失败"), f"Java {Java_Version} 安装失败: {error}")
    except Exception as error:
        log(f"Java {Java_Version} 安装发生未知错误: {error}")
        send_notification(i18nText("错误"), f"Java {Java_Version} 安装失败: {error}")
    finally:
        if install_succeeded and download_path:
            try:
                os.remove(download_path)
                log(f"安装成功，已清理 Java 安装包: {download_path}")
            except OSError as error:
                log(f"无法清理 Java 安装包 {download_path}: {error}")
        elif download_path and os.path.exists(download_path):
            log(f"安装失败，保留安装包用于诊断: {download_path}")
