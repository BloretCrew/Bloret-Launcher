# Removed qfluentwidgets imports for PySide6 compatibility
import logging, os, json, platform, requests, shutil, concurrent.futures, threading, time, sys, subprocess, zipfile, re
import xml.etree.ElementTree as ET
try:
    import send2trash
except ImportError:
    send2trash = None
from pathlib import Path
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from modules.download import (
    DEFAULT_MAX_THREAD as _DEFAULT_MAX_THREAD,
    MAX_THREAD_CAP as _MAX_THREAD_CAP,
    FASTDOWNLOAD_TTL_SEC as _FASTDOWNLOAD_TTL_SEC,
    clamp_workers as _clamp_workers,
    get_session,
    DownloadCancelled as _DownloadCancelled,
    verify_file as _verify_file,
    strict_hash_verify_enabled as _strict_hash_verify_enabled,
    secure_download,
    download_file,
    dl_source_launcher_or_meta_get,
    dl_source_library_get,
    dl_source_assets_get,
)

_current_download_state = {
    'task_id': None,
    'thread': None,
    'cancel_event': threading.Event(),
    'pause_event': threading.Event(),  # set = paused
    'downloader': None,
    'is_paused': False,
    'backend': None,
    'cancelled': False,
}


def toggle_current_download_pause():
    """Pause/resume current install: LibraryDownloader + secure_download pause_event."""
    global _current_download_state
    state = _current_download_state
    downloader = state.get('downloader')
    backend = state.get('backend')
    pause_event = state.get('pause_event')
    if pause_event is None:
        pause_event = threading.Event()
        state['pause_event'] = pause_event

    if state.get('is_paused'):
        if downloader and hasattr(downloader, 'resume'):
            downloader.resume()
        pause_event.clear()
        state['is_paused'] = False
        log("下载已恢复")
    else:
        if downloader and hasattr(downloader, 'pause'):
            downloader.pause()
        pause_event.set()
        state['is_paused'] = True
        log("下载已暂停")
    if backend:
        backend.setDownloadPaused(state['is_paused'])


def cancel_current_download():
    global _current_download_state
    _current_download_state['cancelled'] = True
    _current_download_state['cancel_event'].set()
    pause_event = _current_download_state.get('pause_event')
    if pause_event is not None:
        pause_event.clear()  # unblock waiters so cancel can proceed
    downloader = _current_download_state.get('downloader')
    if downloader:
        downloader.cancel()
    backend = _current_download_state.get('backend')
    if backend:
        backend.closeDownloadDialog()


# Bloret Launcher modules
from modules.win11toast import notify, update_progress
from modules.safe import handle_exception
from modules.log import log
from modules.customize import find_Customize
from modules.i18n import i18nText
from modules.paths import app_path
import modules.globals as BLglobals
import modules.config as cfg

# 线程安全的UI更新函数
def load_ui_file(ui_file_path):
    """
    使用 QUiLoader 加载 UI 文件，兼容 PySide6
    
    Args:
        ui_file_path (str): UI 文件的路径
    
    Returns:
        QWidget: 加载的 UI 对象，如果失败返回 None
    """
    try:
        loader = QUiLoader()
        if not os.path.isabs(ui_file_path):
            ui_file_path = app_path(ui_file_path)

        if not os.path.exists(ui_file_path):
            log(f"UI 文件不存在: {ui_file_path}", logging.WARNING)
            return None
        
        ui = loader.load(ui_file_path, None)
        return ui
    except Exception as e:
        log(f"加载 UI 文件失败 {ui_file_path}: {e}", logging.ERROR)
        return None

def safe_ui_update(widget, method, value, widget_type=None):
    """
    安全地更新UI组件，确保在主线程中执行
    """
    try:
        if widget and hasattr(widget, method):
            if widget_type == "progress_bar":
                QMetaObject.invokeMethod(widget, method, Qt.QueuedConnection, value)
            elif widget_type == "label":
                QMetaObject.invokeMethod(widget, method, Qt.QueuedConnection, str(value))
            else:
                QMetaObject.invokeMethod(widget, method, Qt.QueuedConnection)
            return True
    except Exception as e:
        log(f"UI更新失败: {e}")
    return False

# ── Bloret 快速下载源（Git Clone） ──

_FASTDOWNLOAD_API = "https://launcher.bloret.net/api/fastdownload"
_fastdownload_cache = None  # 缓存 API 返回结果
_fastdownload_cache_ts = 0.0


def fetch_fastdownload_versions(force_refresh=False):
    """
    从 fastdownload API 获取支持的版本列表。
    返回 {version: git_url} 字典，失败返回空字典。
    结果带 TTL 缓存，避免进程内永久过期。
    """
    global _fastdownload_cache, _fastdownload_cache_ts
    now = time.time()
    if (
        not force_refresh
        and _fastdownload_cache is not None
        and (now - _fastdownload_cache_ts) < _FASTDOWNLOAD_TTL_SEC
    ):
        return _fastdownload_cache

    try:
        resp = get_session().get(_FASTDOWNLOAD_API, timeout=10)
        if resp.status_code != 200:
            log(f"fastdownload API 请求失败: HTTP {resp.status_code}", logging.WARNING)
            # 短期缓存空结果，避免连打失败接口
            _fastdownload_cache = {}
            _fastdownload_cache_ts = now
            return {}
        data = resp.json()
        if not data.get("enabled", False):
            log("fastdownload API 返回 enabled=false", logging.INFO)
            _fastdownload_cache = {}
            _fastdownload_cache_ts = now
            return {}
        result = {}
        for entry in data.get("versions", []):
            v = entry.get("version", "")
            url = entry.get("url", "")
            if v and url:
                result[v] = url
        _fastdownload_cache = result
        _fastdownload_cache_ts = now
        log(f"fastdownload API 获取到 {len(result)} 个版本: {list(result.keys())}")
        return result
    except Exception as e:
        log(f"fastdownload API 请求异常: {e}", logging.WARNING)
        _fastdownload_cache = {}
        _fastdownload_cache_ts = now
        return {}


class _GitProgressStream:
    """捕获 dulwich 的进度输出并转发到 UI，支持取消。"""

    def __init__(self, backend=None, cancel_event=None):
        self._backend = backend
        self._cancel_event = cancel_event
        self._buf = b""

    def write(self, data):
        if self._cancel_event is not None and self._cancel_event.is_set():
            raise _DownloadCancelled("用户取消了下载")
        if isinstance(data, bytes):
            self._buf += data
        else:
            self._buf += data.encode("utf-8", errors="replace")
        # dulwich 输出格式如 "Receiving objects:  45% (100/222)\r"
        while b"\r" in self._buf:
            line, self._buf = self._buf.split(b"\r", 1)
            text = line.decode("utf-8", errors="replace").strip()
            if text and self._backend:
                self._backend.updateDownloadProgress(0.3, text, "", "", "")
                log(f"[git] {text}")

    def flush(self):
        pass

    def fileno(self):
        raise OSError("GitProgressStream has no fileno")


def bloret_git_clone_download(version, minecraft_dir, backend=None, cancel_event=None):
    """
    使用 dulwich clone 从 Bloret Git 仓库下载 Minecraft 版本文件（HTTPS only）。
    如果版本不在 fastdownload API 列表中，返回 False（回退正常下载）。
    成功返回 True。
    """
    from dulwich import porcelain
    import tempfile

    fastdownload = fetch_fastdownload_versions()
    if version not in fastdownload:
        log(f"版本 {version} 不在 fastdownload 列表中，回退正常下载")
        return False

    url = fastdownload[version]

    def update_progress(progress, status):
        if backend:
            backend.updateDownloadProgress(progress, status, "", "", "")

    parent = os.path.dirname(os.path.abspath(minecraft_dir)) or minecraft_dir
    os.makedirs(parent, exist_ok=True)

    tmp_dir = tempfile.mkdtemp(prefix="bloret_git_", dir=parent)
    try:
        update_progress(0.05, i18nText("正在从 Bloret 仓库克隆文件..."))
        log(f"开始 git clone (https) {url} -> {tmp_dir}")

        progress_stream = _GitProgressStream(backend, cancel_event=cancel_event)
        porcelain.clone(url, tmp_dir, depth=1, errstream=progress_stream, outstream=progress_stream)
        if cancel_event is not None and cancel_event.is_set():
            raise _DownloadCancelled("用户取消了下载")
        log(f"git clone 完成 (https): {tmp_dir}")

        # 克隆成功，复制文件到目标目录
        update_progress(0.6, i18nText("正在复制文件到 Minecraft 目录..."))
        os.makedirs(minecraft_dir, exist_ok=True)
        for item in os.listdir(tmp_dir):
            if item == ".git":
                continue
            if cancel_event is not None and cancel_event.is_set():
                raise _DownloadCancelled("用户取消了下载")
            src = os.path.join(tmp_dir, item)
            dst = os.path.join(minecraft_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        update_progress(0.85, i18nText("文件复制完成"))
        log(f"Bloret git clone 下载完成: {version}")
        return True
    except _DownloadCancelled:
        log("Bloret git clone 下载被用户取消")
        return False
    except Exception as e:
        log(f"https clone 失败: {e}", logging.ERROR)
        return False
    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _request_json_from_urls(urls, timeout=30):
    for url in urls:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            log(f"获取 JSON 失败: {url}, HTTP {response.status_code}", logging.WARNING)
        except requests.exceptions.RequestException as e:
            log(f"请求 JSON 失败: {url}, {e}", logging.WARNING)
    return None

def _request_text_from_urls(urls, timeout=30):
    for url in urls:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.text
            log(f"获取文本失败: {url}, HTTP {response.status_code}", logging.WARNING)
        except requests.exceptions.RequestException as e:
            log(f"请求文本失败: {url}, {e}", logging.WARNING)
    return None

def _get_java_path_for_installer():
    """Resolve a usable java executable for Forge/NeoForge installers."""
    config_data = cfg.read()
    candidates = []
    for key in ("java_path", "Java_Path"):
        java_path = config_data.get(key, "")
        if java_path and java_path != "Auto":
            candidates.append(java_path)
    which_java = shutil.which("java")
    if which_java:
        candidates.append(which_java)
    candidates.append("java")

    for java_path in candidates:
        if not java_path:
            continue
        # bare "java" may resolve via PATH even if not exists as file
        if java_path != "java" and not os.path.exists(java_path):
            continue
        try:
            proc = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=15,
                **(
                    {"creationflags": subprocess.CREATE_NO_WINDOW}
                    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
                    else {}
                ),
            )
            # java -version writes to stderr; success if process ran
            if proc.returncode == 0 or proc.stderr or proc.stdout:
                log(f"Forge installer 将使用 Java: {java_path}")
                return java_path
        except (OSError, subprocess.TimeoutExpired) as exc:
            log(f"检测 Java 失败 ({java_path}): {exc}", logging.WARNING)
            continue
    return None


def _cleanup_incomplete_version_dir(version_dir, reason=""):
    """Remove a half-installed version directory on hard failure (best-effort)."""
    if not version_dir or not os.path.isdir(version_dir):
        return
    marker = os.path.join(version_dir, ".bloret_installing")
    # Only remove dirs we marked as in-progress, or empty-ish new dirs
    try:
        if os.path.exists(marker) or not os.path.exists(
            os.path.join(version_dir, os.path.basename(version_dir) + ".json")
        ):
            log(f"清理未完成的版本目录: {version_dir} ({reason})", logging.WARNING)
            shutil.rmtree(version_dir, ignore_errors=True)
        else:
            # leave files but drop marker
            if os.path.exists(marker):
                try:
                    os.remove(marker)
                except OSError:
                    pass
    except Exception as exc:
        log(f"清理版本目录失败 {version_dir}: {exc}", logging.WARNING)


def _mark_installing(version_dir):
    try:
        os.makedirs(version_dir, exist_ok=True)
        with open(os.path.join(version_dir, ".bloret_installing"), "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except OSError as exc:
        log(f"写入安装标记失败: {exc}", logging.WARNING)


def _clear_installing_marker(version_dir):
    marker = os.path.join(version_dir, ".bloret_installing") if version_dir else ""
    if marker and os.path.exists(marker):
        try:
            os.remove(marker)
        except OSError:
            pass


def _dl_kwargs(task_state):
    """Common cancel/pause kwargs for secure_download during an install task."""
    if not task_state:
        return {}
    return {
        "cancel_event": task_state.get("cancel_event"),
        "pause_event": task_state.get("pause_event"),
    }

def _ensure_launcher_profile(minecraft_dir, minecraft_version):
    """Forge installer expects a launcher profile in the target .minecraft directory."""
    try:
        os.makedirs(minecraft_dir, exist_ok=True)
        profile_path = os.path.join(minecraft_dir, "launcher_profiles.json")
        default_profile = {
            "profiles": {
                "BloretLauncher": {
                    "name": "BloretLauncher",
                    "type": "custom",
                    "created": "1970-01-01T00:00:00.000Z",
                    "lastUsed": "1970-01-01T00:00:00.000Z",
                    "gameDir": minecraft_dir
                }
            },
            "selectedProfile": "BloretLauncher",
            "clientToken": "00000000000000000000000000000000"
        }

        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if not isinstance(existing, dict):
                    existing = {}
            except Exception:
                existing = {}
        else:
            existing = {}

        profiles = existing.get("profiles") if isinstance(existing.get("profiles"), dict) else {}
        if not profiles:
            existing["profiles"] = default_profile["profiles"]
        else:
            profiles.setdefault("BloretLauncher", default_profile["profiles"]["BloretLauncher"])
            existing["profiles"] = profiles

        if not existing.get("selectedProfile"):
            existing["selectedProfile"] = "BloretLauncher"
        if not existing.get("clientToken"):
            existing["clientToken"] = default_profile["clientToken"]

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
        log(f"已确保 launcher_profiles.json 存在: {profile_path}")
        return True
    except Exception as e:
        log(f"创建 launcher_profiles.json 失败: {e}", logging.WARNING)
        return False

def _maven_metadata_versions(metadata_url):
    # Forge / NeoForge 的版本元数据以官方 Maven 为准，避免镜像数据滞后导致误判
    metadata_text = _request_text_from_urls([metadata_url])
    if not metadata_text:
        return []
    try:
        root = ET.fromstring(metadata_text)
        return [node.text for node in root.findall("./versioning/versions/version") if node.text]
    except ET.ParseError as e:
        log(f"解析 Maven metadata 失败: {metadata_url}, {e}", logging.ERROR)
        return []

def _version_sort_key(value):
    parts = []
    for item in value.replace("-", ".").split("."):
        if item.isdigit():
            parts.append(int(item))
        else:
            parts.append(item)
    return parts

def _latest_forge_version(minecraft_version):
    metadata_url = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
    versions = [v for v in _maven_metadata_versions(metadata_url) if v.startswith(f"{minecraft_version}-")]
    if not versions:
        return None
    return sorted(versions, key=_version_sort_key)[-1]

def _latest_neoforge_version(minecraft_version):
    metadata_url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
    versions = _maven_metadata_versions(metadata_url)
    parts = minecraft_version.split(".")
    if len(parts) < 2 or parts[0] != "1":
        return None
    patch = parts[2] if len(parts) > 2 else "0"
    prefix = f"{parts[1]}.{patch}."
    matched = [v for v in versions if v.startswith(prefix)]
    if not matched:
        return None
    return sorted(matched, key=_version_sort_key)[-1]

def _merge_loader_json(base_data, loader_data, target_id):
    merged = dict(base_data)
    for key, value in loader_data.items():
        if key == "libraries":
            continue
        merged[key] = value
    base_libraries = base_data.get("libraries", [])
    loader_libraries = loader_data.get("libraries", [])
    seen = set()
    libraries = []
    for lib in loader_libraries + base_libraries:
        name = lib.get("name", "")
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        libraries.append(lib)
    merged["libraries"] = libraries
    merged["id"] = target_id
    merged.pop("inheritsFrom", None)
    return merged

def _install_forge_like_loader(loader_type, minecraft_version, minecraft_dir, versions_dir, vanilla_version_dir, version_data, version_name, max_thread_value, task_state):
    is_neoforge = loader_type == "neoforge"
    display_name = "NeoForge" if is_neoforge else "Forge"
    log(f"开始安装 {display_name} 到 Minecraft {minecraft_version}")

    loader_version = _latest_neoforge_version(minecraft_version) if is_neoforge else _latest_forge_version(minecraft_version)
    if not loader_version:
        raise RuntimeError(f"未找到适用于 Minecraft {minecraft_version} 的 {display_name} 版本")

    if is_neoforge:
        installer_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar"
        installer_filename = f"neoforge-{loader_version}-installer.jar"
        install_commands = [["--install-client", minecraft_dir], ["--installClient", minecraft_dir], ["--install-client"], ["--installClient"]]
        target_id = f"{version_name}-NeoForge {loader_version}"
    else:
        installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{loader_version}/forge-{loader_version}-installer.jar"
        installer_filename = f"forge-{loader_version}-installer.jar"
        install_commands = [["--installClient", minecraft_dir], ["--installClient"]]
        target_id = f"{version_name}-Forge {loader_version.split('-', 1)[1]}"

    temp_dir = os.path.join(BLglobals.datapath, "temp", "loaders")
    os.makedirs(temp_dir, exist_ok=True)
    installer_path = os.path.join(temp_dir, installer_filename)
    downloaded = False
    for url in dl_source_library_get(installer_url):
        if secure_download(
            url,
            installer_path,
            description=f"{display_name} installer",
            **_dl_kwargs(task_state),
        ):
            downloaded = True
            break
    if not downloaded:
        raise RuntimeError(
            f"{display_name} installer 下载失败。请检查网络或切换下载源后重试。"
        )

    _ensure_launcher_profile(minecraft_dir, minecraft_version)

    before_dirs = {
        d for d in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, d))
    }
    java_path = _get_java_path_for_installer()
    if not java_path:
        raise RuntimeError(
            f"未找到可用的 Java，无法安装 {display_name}。"
            "请在设置中配置 Java 路径，或先安装 JDK 17+。"
        )

    backend = task_state.get("backend") if task_state else None
    install_success = False
    last_error = ""
    for args in install_commands:
        if task_state and task_state.get("cancel_event") and task_state["cancel_event"].is_set():
            raise RuntimeError(f"{display_name} 安装已被用户取消")
        cmd = [java_path, "-jar", installer_path] + args
        log(f"执行 {display_name} installer: {' '.join(cmd)}")
        if backend:
            try:
                backend.updateDownloadProgress(
                    0.92, f"正在运行 {display_name} 安装程序...", "", "", ""
                )
            except Exception:
                pass
        process = subprocess.Popen(
            cmd,
            cwd=minecraft_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        captured_lines = []
        last_output_time = time.time()
        line_count = 0
        try:
            while True:
                if task_state and task_state.get("cancel_event") and task_state["cancel_event"].is_set():
                    process.kill()
                    raise RuntimeError(f"{display_name} 安装已被用户取消")
                line = process.stdout.readline() if process.stdout else ""
                if line:
                    stripped = line.rstrip()
                    captured_lines.append(stripped)
                    last_output_time = time.time()
                    line_count += 1
                    log(f"{display_name} installer: {stripped}")
                    if backend and line_count % 5 == 0:
                        try:
                            backend.updateDownloadProgress(
                                0.92,
                                f"{display_name}: {stripped[:80]}",
                                "",
                                "",
                                "",
                            )
                        except Exception:
                            pass
                    continue

                if process.poll() is not None:
                    break

                if time.time() - last_output_time > 15:
                    log(f"{display_name} installer 仍在运行，等待输出...", logging.INFO)
                    last_output_time = time.time()
                time.sleep(0.5)

            return_code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            return_code = process.wait()
            captured_lines.append("installer timeout")

        last_error = "\n".join(captured_lines[-20:]).strip()
        if return_code == 0:
            install_success = True
            break
        log(
            f"{display_name} installer 执行失败，返回码 {return_code}: {last_error}",
            logging.WARNING,
        )
    if not install_success:
        hint = ""
        low = (last_error or "").lower()
        if "unsupportedclassversion" in low or "class file version" in low:
            hint = "（Java 版本过旧，请安装并选择更高版本的 JDK）"
        elif "permission" in low or "access" in low:
            hint = "（权限不足，请检查 .minecraft 目录写权限）"
        raise RuntimeError(
            f"{display_name} installer 执行失败{hint}: {last_error or '无输出'}"
        )

    after_dirs = {d for d in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, d))}
    candidates = [d for d in after_dirs - before_dirs if display_name.lower() in d.lower() or "forge" in d.lower()]
    if not candidates:
        candidates = [d for d in after_dirs if loader_version.lower() in d.lower() or display_name.lower() in d.lower()]
    if not candidates:
        raise RuntimeError(f"{display_name} installer 未生成版本目录")
    generated_id = sorted(candidates, key=lambda d: os.path.getmtime(os.path.join(versions_dir, d)), reverse=True)[0]
    generated_dir = os.path.join(versions_dir, generated_id)
    generated_json_path = os.path.join(generated_dir, f"{generated_id}.json")
    if not os.path.exists(generated_json_path):
        json_files = [f for f in os.listdir(generated_dir) if f.endswith(".json")]
        if not json_files:
            raise RuntimeError(f"{display_name} 版本 JSON 不存在: {generated_dir}")
        generated_json_path = os.path.join(generated_dir, json_files[0])

    with open(generated_json_path, 'r', encoding='utf-8') as f:
        loader_data = json.load(f)

    target_dir = os.path.join(versions_dir, target_id)
    if generated_dir != target_dir:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.rename(generated_dir, target_dir)

    target_json_path = os.path.join(target_dir, f"{target_id}.json")
    merged_data = _merge_loader_json(version_data, loader_data, target_id)
    with open(target_json_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
    for file_name in os.listdir(target_dir):
        if file_name.endswith(".json") and file_name != f"{target_id}.json":
            try:
                os.remove(os.path.join(target_dir, file_name))
            except OSError:
                pass

    vanilla_jar = os.path.join(vanilla_version_dir, f"{version_name}.jar")
    if not os.path.exists(vanilla_jar):
        vanilla_jar = os.path.join(vanilla_version_dir, f"{minecraft_version}.jar")
    target_jar = os.path.join(target_dir, f"{target_id}.jar")
    if os.path.exists(vanilla_jar):
        shutil.copy2(vanilla_jar, target_jar)
    else:
        log(f"未找到原版客户端 JAR，{display_name} 启动可能失败: {vanilla_jar}", logging.WARNING)

    natives_dir = os.path.join(target_dir, f"{target_id}-natives")
    os.makedirs(natives_dir, exist_ok=True)
    processed_libraries = _library_download_items(merged_data.get("libraries", []), minecraft_dir)
    if processed_libraries:
        downloader = LibraryDownloader(processed_libraries, max_workers=max_thread_value, natives_dir=natives_dir, pause_event=task_state.get('pause_event') if task_state else None)
        task_state['downloader'] = downloader
        if task_state['cancel_event'].is_set():
            downloader.cancel()
        if task_state['cancel_event'].is_set() or not downloader.download_libraries():
            raise RuntimeError(f"{display_name} 关键库/native 下载失败")

    os.makedirs(os.path.join(target_dir, "mods"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "resourcepacks"), exist_ok=True)
    return target_id

# 初始化全局变量
set_list = []
minecraft_list = []

def update_bl_json(minecraft_dir, version_id, fabric_loader=False, icon_path=None):
    """
    更新或创建 .BL.json 文件，记录已安装的 Minecraft 版本信息
    
    Args:
        minecraft_dir: Minecraft 安装目录
        version_id: 版本标识符（如 "1.21.8" 或 "1.21.8-Fabric 0.18.1"）
        fabric_loader: 是否为 Fabric 版本
        icon_path: 图标路径（可选）
    """
    try:
        bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
        
        # 如果文件已存在，读取现有内容
        if os.path.exists(bl_json_path):
            try:
                with open(bl_json_path, 'r', encoding='utf-8') as f:
                    bl_data = json.load(f)
            except Exception as e:
                log(f"读取现有的 .BL.json 文件失败: {e}，将创建新文件")
                bl_data = {"versions": {}}
        else:
            bl_data = {"versions": {}}
        
        # 确保 bl_data 有 versions 键且是字典类型
        if "versions" not in bl_data or not isinstance(bl_data.get("versions"), dict):
            bl_data["versions"] = {}
        
        # 提取基础版本号（去除 Fabric 标识）
        base_version = version_id.split("-")[0] if "-" in version_id else version_id
        
        # 创建版本条目
        version_entry = {
            "Fabric": fabric_loader,
            "client": True,  # 假设都是客户端版本
            "version": base_version,
            "setup_time": int(time.time())  # 当前时间戳
        }
        
        # 如果有图标路径，添加到条目
        if icon_path:
            version_entry["icon"] = icon_path
        
        # 更新或添加版本信息
        try:
            bl_data["versions"][version_id] = version_entry
        except Exception as e:
            log(f"更新版本信息时出错，bl_data类型: {type(bl_data)}, versions键: {bl_data.get('versions', 'NOT_FOUND')}, 错误: {e}", logging.ERROR)
            raise
        
        # 确保目录存在
        os.makedirs(os.path.dirname(bl_json_path), exist_ok=True)
        
        # 写回文件
        with open(bl_json_path, 'w', encoding='utf-8') as f:
            json.dump(bl_data, f, indent=4, ensure_ascii=False)
        
        log(f"已更新 .BL.json 文件，添加了版本: {version_id}")

        
        return True
        
    except Exception as e:
        log(f"更新 .BL.json 文件失败: {e}，版本ID: {version_id}, Fabric: {fabric_loader}", logging.ERROR)
        return False

def repair_bl_json(minecraft_dir):
    """
    检查并修复 .BL.json 文件：如果缺失则生成，如果版本记录不全则补全。
    扫描 versions 目录下所有子文件夹，确保每个已安装版本在 .BL.json 中都有记录。
    
    Args:
        minecraft_dir: Minecraft 安装目录
    """
    try:
        versions_path = os.path.join(minecraft_dir, "versions")
        bl_json_path = os.path.join(versions_path, ".BL.json")
        
        # 如果 versions 目录不存在，无需修复
        if not os.path.isdir(versions_path):
            log("versions 目录不存在，跳过 .BL.json 修复", logging.INFO)
            return
        
        # 读取现有 .BL.json（或创建空结构）
        bl_data = {"versions": {}}
        if os.path.exists(bl_json_path):
            try:
                with open(bl_json_path, 'r', encoding='utf-8') as f:
                    bl_data = json.load(f)
                if "versions" not in bl_data or not isinstance(bl_data.get("versions"), dict):
                    bl_data["versions"] = {}
            except Exception as e:
                log(f"读取 .BL.json 失败: {e}，将重新创建", logging.WARNING)
                bl_data = {"versions": {}}
        
        existing_versions = set(bl_data["versions"].keys())
        
        # 扫描 versions 目录下所有子文件夹
        added = 0
        for entry in os.listdir(versions_path):
            entry_path = os.path.join(versions_path, entry)
            if not os.path.isdir(entry_path):
                continue
            
            # 跳过已有的记录
            if entry in existing_versions:
                continue
            
            # 检测是否为 Fabric 版本（通过文件夹名）
            is_fabric = "fabric" in entry.lower()
            
            # 提取基础版本号（去除 Fabric 标识）
            base_version = entry.split("-")[0] if "-" in entry else entry
            
            # 创建版本条目
            version_entry = {
                "Fabric": is_fabric,
                "client": True,
                "version": base_version,
                "setup_time": int(time.time())
            }
            
            bl_data["versions"][entry] = version_entry
            added += 1
            log(f".BL.json 补全: 添加版本 {entry} (Fabric: {is_fabric})")
        
        # 写回文件
        os.makedirs(versions_path, exist_ok=True)
        with open(bl_json_path, 'w', encoding='utf-8') as f:
            json.dump(bl_data, f, indent=4, ensure_ascii=False)
        
        if added > 0:
            log(f".BL.json 修复完成: 新增 {added} 个版本记录")
        else:
            log(".BL.json 检查完成: 所有版本记录完整")
            
    except Exception as e:
        log(f".BL.json 修复失败: {e}", logging.ERROR)

def _is_safe_version_name(value):
    """VersionName 必须是单个、安全的路径组件。"""
    if not isinstance(value, str) or not value or value in (".", ".."):
        return False
    if value != os.path.basename(value) or "/" in value or "\\" in value:
        return False
    if os.path.isabs(value) or re.search(r"[\x00-\x1f<>:\"|?*]", value):
        return False
    return True


def _resolve_version_file(version_dir, version_name, minecraft_version, extension):
    """按 VersionName 优先、原版 id 回退，解析 jar/json 路径。"""
    candidates = []
    if version_name:
        candidates.append(os.path.join(version_dir, f"{version_name}.{extension}"))
    if minecraft_version and minecraft_version != version_name:
        candidates.append(os.path.join(version_dir, f"{minecraft_version}.{extension}"))
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0] if candidates else os.path.join(version_dir, f"{version_name}.{extension}")


def _load_version_json(version_dir, version_name, minecraft_version):
    path = _resolve_version_file(version_dir, version_name, minecraft_version, "json")
    if not os.path.exists(path):
        return None, path
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), path
    except Exception as exc:
        log(f"读取版本 JSON 失败 {path}: {exc}", logging.WARNING)
        return None, path


def _rule_matches(rule):
    from modules.platform_compat import mojang_os_name, mojang_arch

    os_rule = rule.get("os") or {}
    current_name = mojang_os_name()
    if os_rule.get("name") and os_rule["name"] != current_name:
        return False
    if os_rule.get("arch"):
        arch = platform.machine().lower()
        normalized = (
            "x86"
            if arch in ("i386", "i686", "x86")
            else "x86_64"
            if arch in ("amd64", "x86_64")
            else arch
        )
        # Prefer shared helper when it matches Mojang's coarse arch tags
        if os_rule["arch"].lower() in ("x86", "x86_64"):
            normalized = mojang_arch() if arch in ("amd64", "x86_64", "x86", "i386", "i686") else normalized
        if os_rule["arch"].lower() != normalized:
            return False
    if os_rule.get("version"):
        try:
            if not re.search(os_rule["version"], platform.version()):
                return False
        except re.error:
            return False
    features = rule.get("features") or {}
    if features and any(bool(value) for value in features.values()):
        return False
    return True


def _library_allowed(lib):
    rules = lib.get("rules")
    if not rules:
        return True
    allowed = False
    for rule in rules:
        if _rule_matches(rule):
            allowed = rule.get("action", "disallow") == "allow"
    return allowed


def _maven_artifact_path(name, classifier=None, extension="jar"):
    parts = name.split(":")
    if len(parts) < 3:
        return None
    group, artifact, version = parts[:3]
    classifier = classifier or (parts[3] if len(parts) > 3 else None)
    filename = f"{artifact}-{version}{'-' + classifier if classifier else ''}.{extension}"
    return "/".join((group.replace(".", "/"), artifact, version, filename))


def _native_classifier(lib):
    """Return Mojang native classifier for this host, or None."""
    from modules.platform_compat import mojang_native_classifier

    return mojang_native_classifier(lib)



def _safe_library_destination(minecraft_dir, relative_path):
    root = os.path.realpath(os.path.join(minecraft_dir, "libraries"))
    normalized = str(relative_path).replace("\\", "/").lstrip("/")
    destination = os.path.realpath(os.path.join(root, *normalized.split("/")))
    if os.path.commonpath((root, destination)) != root:
        raise ValueError(f"非法 library artifact path: {relative_path}")
    return destination

def _library_download_items(libraries, minecraft_dir):
    items = []
    for lib in libraries or []:
        if not _library_allowed(lib):
            log(f"库规则不适用于当前平台，跳过: {lib.get('name', '<unknown>')}")
            continue
        downloads = lib.get("downloads") or {}
        artifact = downloads.get("artifact")
        if artifact:
            rel_path = artifact.get("path") or _maven_artifact_path(lib.get("name", ""))
            if rel_path:
                items.append((lib, _safe_library_destination(minecraft_dir, rel_path), artifact, False))
        elif lib.get("name"):
            rel_path = _maven_artifact_path(lib["name"])
            if rel_path:
                base = lib.get("url", "https://libraries.minecraft.net/").rstrip("/") + "/"
                items.append((lib, _safe_library_destination(minecraft_dir, rel_path), {"path": rel_path, "url": base + rel_path}, False))
        classifier = _native_classifier(lib)
        if classifier:
            native = (downloads.get("classifiers") or {}).get(classifier)
            if native:
                rel_path = native.get("path") or _maven_artifact_path(lib.get("name", ""), classifier)
                if rel_path:
                    items.append((lib, _safe_library_destination(minecraft_dir, rel_path), native, True))
            else:
                log(f"缺少当前平台 native classifier {classifier}: {lib.get('name')}", logging.ERROR)
                # 不加入空 path 项，避免必然失败的下载任务
        else:
            from modules.platform_compat import uses_system_lwjgl

            if uses_system_lwjgl() and (lib.get("natives") or downloads.get("classifiers")):
                log(
                    f"FreeBSD: 跳过 Mojang native classifier，将使用系统 LWJGL: {lib.get('name', '<unknown>')}",
                    logging.DEBUG,
                )
    return items


def _safe_extract_native(archive_path, natives_dir, excludes):
    """安全解压 native jar 到目标目录（路径校验，禁止符号链接/穿越）。直接写入目标，避免全量 copytree。"""
    import stat
    destination = os.path.realpath(natives_dir)
    os.makedirs(destination, exist_ok=True)
    exclude_prefixes = tuple(str(item).replace("\\", "/").lstrip("/") for item in excludes or [])
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                name = info.filename.replace("\\", "/").lstrip("/")
                if not name or any(name.startswith(prefix) for prefix in exclude_prefixes):
                    continue
                mode = (info.external_attr >> 16) & 0xFFFF
                is_dir = info.is_dir() or name.endswith("/")
                if stat.S_ISLNK(mode):
                    raise ValueError(f"native ZIP 包含符号链接: {info.filename}")
                if mode and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    raise ValueError(f"native ZIP 包含非普通条目: {info.filename}")
                target = os.path.realpath(os.path.join(destination, *name.split("/")))
                if os.path.commonpath((destination, target)) != destination:
                    raise ValueError(f"native ZIP 包含路径穿越条目: {info.filename}")
                if is_dir:
                    os.makedirs(target, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with archive.open(info) as source, open(target, "wb") as output:
                    shutil.copyfileobj(source, output)
        log(f"native 已安全解压: {archive_path} -> {natives_dir}")
        return True
    except Exception as exc:
        log(f"安全解压 native 失败 {archive_path}: {exc}", logging.ERROR)
        return False


class LibraryDownloader:
    def __init__(
        self,
        missing_libraries,
        max_workers=_DEFAULT_MAX_THREAD,
        natives_dir=None,
        pause_event=None,
        cancellation_event=None,
    ):
        self.missing_libraries = missing_libraries
        self.max_workers = _clamp_workers(max_workers)
        self.natives_dir = natives_dir
        self.completed_count = 0
        self.total_count = len(missing_libraries)
        self._active_downloads = 0
        self._active_downloads_lock = threading.Lock()
        self.lock = threading.Lock()
        self.completed_event = threading.Event()
        self.cancel_event = threading.Event()
        self.pause_event = pause_event  # shared with secure_download when set
        self.cancellation_event = cancellation_event
        self.result = None
        self._paused = False
        self._cancelled = False
        self._pause_cond = threading.Condition(self.lock)
        self._external_cancel_watcher = None
        if cancellation_event is not None:
            def _watch_external_cancel():
                try:
                    cancellation_event.wait()
                except Exception:
                    return
                if cancellation_event.is_set() and not self.completed_event.is_set():
                    self.cancel()

            self._external_cancel_watcher = threading.Thread(
                target=_watch_external_cancel, daemon=True, name="LibDlCancelWatch"
            )
            self._external_cancel_watcher.start()

    @property
    def is_paused(self):
        with self.lock: return self._paused

    def pause(self):
        with self.lock:
            self._paused = True
            log("下载已暂停")

    def resume(self):
        with self.lock:
            self._paused = False
            self._pause_cond.notify_all()
            log("下载已恢复")

    def cancel(self):
        with self.lock:
            self._cancelled = True
            self._paused = False
            self._pause_cond.notify_all()
        self.cancel_event.set()
        log("下载取消请求已发出，等待线程池完全结束")

    @property
    def is_cancelled(self):
        with self.lock: return self._cancelled

    def download_single_library(self, item):
        with self.lock:
            while self._paused and not self._cancelled:
                self._pause_cond.wait()
            if self._cancelled:
                return False
        with self._active_downloads_lock:
            self._active_downloads += 1
        try:
            if len(item) == 2:
                lib, path = item
                artifact = (lib.get("downloads") or {}).get("artifact") or {}
                is_native = False
            else:
                lib, path, artifact, is_native = item
            if not path or not artifact.get("url"):
                log(f"库下载元数据不完整: {lib.get('name')}", logging.ERROR)
                return False
            urls = dl_source_library_get(artifact["url"])
            if artifact["url"] not in urls:
                urls.append(artifact["url"])
            if not secure_download(
                urls,
                path,
                artifact,
                "native 库" if is_native else "库文件",
                cancel_event=self.cancel_event,
                pause_event=self.pause_event,
                quiet=True,
            ):
                return False
            if is_native:
                if not self.natives_dir:
                    log(f"native 库缺少解压目录: {path}", logging.ERROR)
                    return False
                excludes = (lib.get("extract") or {}).get("exclude", [])
                if not _safe_extract_native(path, self.natives_dir, excludes):
                    return False
            with self.lock:
                self.completed_count += 1
            return True
        except Exception as exc:
            log(f"下载库文件失败: {exc}", logging.ERROR)
            return False
        finally:
            with self._active_downloads_lock:
                self._active_downloads = max(0, self._active_downloads - 1)

    def download_libraries(self):
        log(f"使用 {self.max_workers} 个线程下载 {self.total_count} 个库/native 文件")
        success = False
        item_ok = {}
        try:
            if not self.missing_libraries:
                success = True
                self.result = True
                return True

            def _run_batch(items, prefix):
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=prefix) as executor:
                    future_map = {executor.submit(self.download_single_library, item): item for item in items}
                    for future in concurrent.futures.as_completed(future_map):
                        item = future_map[future]
                        try:
                            item_ok[id(item)] = bool(future.result())
                        except Exception as exc:
                            log(f"库下载任务异常: {exc}", logging.ERROR)
                            item_ok[id(item)] = False

            _run_batch(self.missing_libraries, "LibraryDownloader")
            failed_items = [item for item in self.missing_libraries if not item_ok.get(id(item))]
            if failed_items and not self.is_cancelled and not self.cancel_event.is_set():
                log(f"库文件首轮失败 {len(failed_items)} 个，开始第二轮重试", logging.WARNING)
                _run_batch(failed_items, "LibraryRetry")

            ok_count = sum(1 for item in self.missing_libraries if item_ok.get(id(item)))
            success = (
                not self.is_cancelled
                and not self.cancel_event.is_set()
                and ok_count == self.total_count
            )
            if not success:
                log(f"库文件下载失败: 成功 {ok_count}/{self.total_count}", logging.ERROR)
            self.result = success
            return success
        finally:
            if self.result is None:
                self.result = False
            self.completed_event.set()
            log(f"库下载任务结束: success={success}, completed={self.completed_count}/{self.total_count}, active={self._active_downloads}")


# ---------------------------------------------------------------------------
# Shared launch/install runtime file ensure (libraries, natives, client, assets)
# ---------------------------------------------------------------------------

def _version_json_path(minecraft_dir, version_id):
    return os.path.join(minecraft_dir, "versions", version_id, f"{version_id}.json")


def _read_version_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_merged_version_json(minecraft_dir, version_id, _visited=None):
    """
    Load version JSON and merge inheritsFrom parents (loader child over base).
    Raises FileNotFoundError if the leaf version JSON is missing.
    """
    if _visited is None:
        _visited = set()
    if version_id in _visited:
        raise RuntimeError(f"版本 inheritsFrom 形成环: {version_id}")
    _visited.add(version_id)

    path = _version_json_path(minecraft_dir, version_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"版本配置文件不存在: {path}")

    data = _read_version_json_file(path)
    parent_id = data.get("inheritsFrom")
    if not parent_id:
        return data

    parent_data = load_merged_version_json(minecraft_dir, parent_id, _visited)
    return _merge_loader_json(parent_data, data, version_id)


def _local_file_ok(path, metadata=None, *, is_native=False, natives_dir=None):
    """True if path exists and (when metadata present) size/sha1 pass light checks."""
    if not path or not os.path.exists(path):
        return False
    metadata = metadata or {}
    expected_size = metadata.get("size")
    expected_sha1 = metadata.get("sha1") or metadata.get("hash")
    if expected_size is not None or expected_sha1:
        strict = _strict_hash_verify_enabled()
        ok, _ = _verify_file(
            path,
            expected_size,
            expected_sha1,
            fast=not strict,
        )
        if not ok:
            return False
    if is_native and natives_dir:
        # After install, natives are extracted; presence of jar alone is enough for
        # re-extract decision — empty natives dir means we should re-download/extract.
        try:
            if not os.path.isdir(natives_dir) or not os.listdir(natives_dir):
                return False
        except OSError:
            return False
    return True


def collect_missing_runtime_files(
    minecraft_dir,
    version_data,
    version_id,
    *,
    natives_dir=None,
    check_assets=True,
    check_client=True,
):
    """
    Collect missing runtime artifacts for launch/install completion.

    Returns dict:
      libraries: list of (lib, path, artifact, is_native) for LibraryDownloader
      client: None or (path, client_info dict)
      assets: {
          index: None or (path, asset_index_meta),
          objects: list of (asset_name, asset_info, object_path),
          skipped: int,
          total: int,
      }
    """
    if natives_dir is None:
        version_dir = os.path.join(minecraft_dir, "versions", version_id)
        natives_dir = os.path.join(version_dir, f"{version_id}-natives")

    missing_libs = []
    for item in _library_download_items(version_data.get("libraries") or [], minecraft_dir):
        lib, path, artifact, is_native = item
        if not _local_file_ok(path, artifact, is_native=is_native, natives_dir=natives_dir if is_native else None):
            missing_libs.append(item)

    # Deduplicate by destination path (keep first)
    seen_paths = set()
    deduped = []
    for item in missing_libs:
        path = item[1]
        key = os.path.normcase(os.path.abspath(path)) if path else id(item)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        deduped.append(item)
    missing_libs = deduped

    client_missing = None
    if check_client:
        version_dir = os.path.join(minecraft_dir, "versions", version_id)
        client_path = os.path.join(version_dir, f"{version_id}.jar")
        client_info = (version_data.get("downloads") or {}).get("client") or {}
        if not _local_file_ok(client_path, client_info if client_info else None):
            if client_info.get("url"):
                client_missing = (client_path, client_info)
            elif not os.path.exists(client_path):
                client_missing = (client_path, client_info)

    assets_info = {"index": None, "objects": [], "skipped": 0, "total": 0}
    if check_assets and version_data.get("assetIndex"):
        asset_index = version_data["assetIndex"]
        assets_dir = os.path.join(minecraft_dir, "assets")
        indexes_dir = os.path.join(assets_dir, "indexes")
        objects_dir = os.path.join(assets_dir, "objects")
        asset_index_id = asset_index.get("id") or version_id
        asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")

        index_data = None
        if not _local_file_ok(asset_index_path, asset_index):
            assets_info["index"] = (asset_index_path, asset_index)
        elif os.path.exists(asset_index_path):
            try:
                with open(asset_index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception as exc:
                log(f"读取资源索引失败，将重新下载: {exc}", logging.WARNING)
                assets_info["index"] = (asset_index_path, asset_index)

        if index_data is None and assets_info["index"] is None and os.path.exists(asset_index_path):
            try:
                with open(asset_index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception:
                pass

        # Objects can only be enumerated when index is present; if index missing,
        # ensure_runtime_files downloads index first then re-scans.
        if index_data is not None:
            objects = index_data.get("objects") or {}
            assets_info["total"] = len(objects)
            strict = _strict_hash_verify_enabled()
            for asset_name, asset_meta in objects.items():
                hash_value = asset_meta.get("hash")
                if not hash_value:
                    continue
                object_path = os.path.join(objects_dir, hash_value[:2], hash_value)
                if os.path.exists(object_path):
                    ok, _ = _verify_file(
                        object_path,
                        asset_meta.get("size"),
                        hash_value,
                        fast=not strict,
                    )
                    if ok:
                        assets_info["skipped"] += 1
                        continue
                assets_info["objects"].append((asset_name, asset_meta, object_path))

    return {
        "libraries": missing_libs,
        "client": client_missing,
        "assets": assets_info,
        "natives_dir": natives_dir,
    }


def _raise_if_cancelled(cancellation_event, stage):
    if cancellation_event is not None and cancellation_event.is_set():
        raise RuntimeError(f"启动会话已取消（{stage}）")


def _download_missing_assets(pending_objects, max_workers, cancellation_event=None, progress_cb=None):
    """Download missing asset objects. Returns True on full success."""
    if not pending_objects:
        return True
    strict = _strict_hash_verify_enabled()
    max_workers = _clamp_workers(max_workers)
    total = len(pending_objects)
    item_ok = {}
    completed = 0
    lock = threading.Lock()

    def download_one(item):
        if cancellation_event is not None and cancellation_event.is_set():
            return False
        asset_name, asset_info, object_path = item
        hash_value = asset_info["hash"]
        asset_url = f"https://resources.download.minecraft.net/{hash_value[:2]}/{hash_value}"
        urls = dl_source_assets_get(asset_url)
        if asset_url not in urls:
            urls.append(asset_url)
        return secure_download(
            urls,
            object_path,
            asset_info,
            f"资源对象 {asset_name}",
            cancel_event=cancellation_event,
            quiet=True,
            fast_verify=not strict,
        )

    def run_batch(items, prefix):
        nonlocal completed
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=prefix) as executor:
            future_map = {executor.submit(download_one, item): item for item in items}
            for future in concurrent.futures.as_completed(future_map):
                item = future_map[future]
                try:
                    ok = bool(future.result())
                except Exception as exc:
                    log(f"资源下载异常: {exc}", logging.ERROR)
                    ok = False
                item_ok[id(item)] = ok
                with lock:
                    completed += 1
                    if progress_cb:
                        try:
                            progress_cb(
                                "assets",
                                completed,
                                total,
                                f"资源对象 {completed}/{total}",
                            )
                        except Exception:
                            pass

    run_batch(pending_objects, "LaunchAssets")
    failed = [item for item in pending_objects if not item_ok.get(id(item))]
    if failed and (cancellation_event is None or not cancellation_event.is_set()):
        log(f"启动资源补全首轮失败 {len(failed)} 个，重试", logging.WARNING)
        for item in failed:
            item_ok.pop(id(item), None)
        run_batch(failed, "LaunchAssetsRetry")
        failed = [item for item in pending_objects if not item_ok.get(id(item))]

    if cancellation_event is not None and cancellation_event.is_set():
        return False
    if failed:
        sample = ", ".join(name for name, _, _ in failed[:5])
        log(f"资源补全仍失败 {len(failed)} 个（例: {sample}）", logging.ERROR)
        return False
    return True


def ensure_runtime_files(
    minecraft_dir,
    version_data,
    version_id,
    *,
    max_workers=None,
    natives_dir=None,
    cancellation_event=None,
    progress_cb=None,
    check_assets=True,
    check_client=True,
    skip_completion=False,
):
    """
    Ensure libraries, natives, client jar, and (optionally) assets for a version.

    progress_cb(stage, current, total, message) optional.
    Returns True on success. Raises RuntimeError on hard failure / cancel.
    When skip_completion=True, only reports missing counts and returns True if
    critical client jar exists (or soft-warns).
    """
    if max_workers is None:
        try:
            max_workers = _clamp_workers(cfg.read().get("MaxThread", _DEFAULT_MAX_THREAD))
        except Exception:
            max_workers = _DEFAULT_MAX_THREAD
    else:
        max_workers = _clamp_workers(max_workers)

    if natives_dir is None:
        version_dir = os.path.join(minecraft_dir, "versions", version_id)
        natives_dir = os.path.join(version_dir, f"{version_id}-natives")
    os.makedirs(natives_dir, exist_ok=True)
    os.makedirs(os.path.join(minecraft_dir, "assets", "indexes"), exist_ok=True)
    os.makedirs(os.path.join(minecraft_dir, "assets", "objects"), exist_ok=True)

    def emit(stage, current, total, message):
        if progress_cb:
            try:
                progress_cb(stage, current, total, message)
            except Exception:
                pass

    _raise_if_cancelled(cancellation_event, "补全开始前")
    plan = collect_missing_runtime_files(
        minecraft_dir,
        version_data,
        version_id,
        natives_dir=natives_dir,
        check_assets=check_assets,
        check_client=check_client,
    )

    n_lib = len(plan["libraries"])
    n_obj = len(plan["assets"].get("objects") or [])
    has_index = plan["assets"].get("index") is not None
    has_client = plan["client"] is not None
    log(
        f"运行时补全计划: libs={n_lib}, client={'yes' if has_client else 'no'}, "
        f"asset_index={'yes' if has_index else 'no'}, asset_objects={n_obj}, "
        f"assets_skipped={plan['assets'].get('skipped', 0)}"
    )

    if skip_completion:
        if n_lib or has_client or has_index or n_obj:
            log(
                f"跳过文件补全：仍缺 libs={n_lib}, client={has_client}, "
                f"index={has_index}, objects={n_obj}",
                logging.WARNING,
            )
        version_dir = os.path.join(minecraft_dir, "versions", version_id)
        client_path = os.path.join(version_dir, f"{version_id}.jar")
        if not os.path.exists(client_path):
            raise FileNotFoundError(f"客户端 JAR 文件 {client_path} 不存在（已跳过补全）")
        return True

    # --- client jar ---
    if plan["client"]:
        _raise_if_cancelled(cancellation_event, "客户端 JAR 补全")
        client_path, client_info = plan["client"]
        if not client_info.get("url"):
            raise FileNotFoundError(f"客户端 JAR 缺失且无下载元数据: {client_path}")
        emit("client", 0, 1, "正在补全客户端 JAR...")
        client_url = client_info["url"]
        client_urls = dl_source_launcher_or_meta_get(client_url)
        if not secure_download(
            client_urls + [client_url],
            client_path,
            client_info,
            "客户端 JAR",
            cancel_event=cancellation_event,
        ):
            _raise_if_cancelled(cancellation_event, "客户端 JAR 补全失败")
            raise RuntimeError(f"客户端 JAR 补全失败: {client_path}")
        emit("client", 1, 1, "客户端 JAR 已就绪")

    # --- libraries + natives ---
    if plan["libraries"]:
        _raise_if_cancelled(cancellation_event, "库文件补全")
        emit("libraries", 0, len(plan["libraries"]), f"正在补全 {len(plan['libraries'])} 个库/native...")
        downloader = LibraryDownloader(
            plan["libraries"],
            max_workers,
            natives_dir=natives_dir,
            cancellation_event=cancellation_event,
        )
        ok = downloader.download_libraries()
        _raise_if_cancelled(cancellation_event, "库文件补全")
        if not ok:
            raise RuntimeError(
                f"库文件补全失败: completed={downloader.completed_count}/{downloader.total_count}"
            )
        # Re-extract natives if jar present but natives dir empty (download skipped as ok)
        for item in plan["libraries"]:
            if len(item) >= 4 and item[3]:
                lib, path, artifact, _ = item
                if os.path.exists(path) and natives_dir:
                    excludes = (lib.get("extract") or {}).get("exclude", [])
                    if not os.path.isdir(natives_dir) or not os.listdir(natives_dir):
                        _safe_extract_native(path, natives_dir, excludes)
        emit("libraries", len(plan["libraries"]), len(plan["libraries"]), "库/native 补全完成")

    # --- asset index ---
    if plan["assets"].get("index"):
        _raise_if_cancelled(cancellation_event, "资源索引补全")
        asset_index_path, asset_index = plan["assets"]["index"]
        emit("asset_index", 0, 1, "正在补全资源索引...")
        asset_index_url = asset_index.get("url")
        if not asset_index_url:
            raise RuntimeError("资源索引缺少 url，无法补全")
        asset_index_urls = dl_source_launcher_or_meta_get(asset_index_url)
        if not secure_download(
            asset_index_urls + [asset_index_url],
            asset_index_path,
            asset_index,
            "资源索引",
            cancel_event=cancellation_event,
        ):
            _raise_if_cancelled(cancellation_event, "资源索引补全失败")
            raise RuntimeError(f"资源索引补全失败: {asset_index_path}")
        emit("asset_index", 1, 1, "资源索引已就绪")
        # Re-collect objects after index download
        replan = collect_missing_runtime_files(
            minecraft_dir,
            version_data,
            version_id,
            natives_dir=natives_dir,
            check_assets=True,
            check_client=False,
        )
        plan["assets"] = replan["assets"]

    # --- asset objects (lightweight: only missing) ---
    pending_objects = plan["assets"].get("objects") or []
    if pending_objects:
        _raise_if_cancelled(cancellation_event, "资源对象补全")
        emit("assets", 0, len(pending_objects), f"正在补全 {len(pending_objects)} 个资源对象...")
        if not _download_missing_assets(
            pending_objects,
            max_workers,
            cancellation_event=cancellation_event,
            progress_cb=progress_cb,
        ):
            _raise_if_cancelled(cancellation_event, "资源对象补全失败")
            raise RuntimeError(f"资源对象补全失败: {len(pending_objects)} 个待下载项未全部成功")
        emit("assets", len(pending_objects), len(pending_objects), "资源对象补全完成")

    # Final client existence check
    version_dir = os.path.join(minecraft_dir, "versions", version_id)
    client_path = os.path.join(version_dir, f"{version_id}.jar")
    if not os.path.exists(client_path):
        raise FileNotFoundError(f"客户端 JAR 文件 {client_path} 不存在")

    emit("done", 1, 1, "运行时文件已就绪")
    return True


def InstallMinecraftVersion(version, minecraft_dir=None, download_dialog=None, Fabric_Loader=False, VersionName=None, backend=None, Loader_Type="vanilla"):
    global _current_download_state
    if VersionName is None:
        VersionName = version
    if not _is_safe_version_name(VersionName):
        log(f"拒绝不安全的 VersionName: {VersionName!r}", logging.ERROR)
        if backend:
            backend.updateDownloadProgress(0, i18nText("安装失败：版本名称不安全"), "", "", "")
            backend.closeDownloadDialog()
        return False
    if Fabric_Loader:
        Loader_Type = "fabric"
    task_id = object()
    state = {
        'task_id': task_id,
        'thread': None,
        'cancel_event': threading.Event(),
        'pause_event': threading.Event(),
        'downloader': None,
        'is_paused': False,
        'backend': backend,
        'cancelled': False,
        'completed_event': threading.Event(),
        'result': None,
        'version_dir': None,
        'cleanup_on_fail': True,
    }
    _current_download_state = state

    def run_install_task():
        try:
            state['result'] = bool(
                _install_minecraft_version_threaded(
                    version, minecraft_dir, Fabric_Loader, VersionName, backend, Loader_Type, state
                )
            )
        except Exception as exc:
            state['result'] = False
            log(f"安装任务包装器捕获异常: {exc}", logging.ERROR)
        finally:
            state['completed_event'].set()
            log(f"安装任务已完全结束: version={version}, result={state['result']}")

    thread = Thread(target=run_install_task, daemon=True)
    state['thread'] = thread
    thread.install_state = state
    try:
        thread.start()
        return thread
    except Exception:
        if _current_download_state.get('task_id') is task_id:
            _current_download_state = {
                'task_id': None,
                'thread': None,
                'cancel_event': threading.Event(),
                'pause_event': threading.Event(),
                'downloader': None,
                'is_paused': False,
                'backend': None,
                'cancelled': False,
                'completed_event': threading.Event(),
                'result': None,
            }
        _install_state_lock.release()
        raise

def _install_minecraft_version_threaded(version, minecraft_dir=None, Fabric_Loader=False, VersionName=None, backend=None, Loader_Type="vanilla", task_state=None):
    global _current_download_state
    
    _plugin_progress_last = {"pct": -1, "ts": 0.0}

    def update_progress_ui(progress, status, speed="", downloaded="", total=""):
        if backend:
            backend.updateDownloadProgress(progress, status, speed, downloaded, total)
        # 同步更新 DownloadManager（多任务支持）。必须使用明确 task_id，
        # 多个任务共享同一个 Backend，按 backend 查找会把进度串到首个任务。
        try:
            from modules.download_manager import DownloadManager
            task_id = task_state.get("task_id") if task_state else None
            if task_id:
                DownloadManager().update_progress(
                    task_id, progress, status, speed, downloaded, total
                )
        except Exception:
            pass
        # 插件 download.progress：每 5% 或 500ms 节流
        try:
            import time as _time
            pct = float(progress or 0)
            if pct <= 1.0:
                pct = pct * 100.0
            now = _time.monotonic()
            last = _plugin_progress_last
            if abs(pct - last["pct"]) >= 5.0 or (now - last["ts"]) >= 0.5:
                last["pct"] = pct
                last["ts"] = now
                from modules.plugin_host.dispatch import invoke_hook
                invoke_hook(
                    "download.progress",
                    {
                        "version": version,
                        "progress": pct,
                        "status": status,
                        "speed": speed,
                        "downloaded": downloaded,
                        "total": total,
                    },
                )
        except Exception:
            pass
    
    def close_dialog_ui():
        if backend:
            backend.closeDownloadDialog()

    def fail_install(message, cleanup=True):
        log(message, logging.ERROR)
        update_progress_ui(0, i18nText(f"安装失败：{message}"), "", "", "")
        try:
            update_progress({'status': i18nText(f"安装失败：{message}"), 'value': 0})
        except Exception as notify_error:
            log(f"更新安装失败通知时出错: {notify_error}", logging.WARNING)
        if cleanup and task_state and task_state.get("cleanup_on_fail"):
            _cleanup_incomplete_version_dir(task_state.get("version_dir"), reason=str(message)[:120])
        close_dialog_ui()
        try:
            from modules.notification import send_notification
            send_notification(i18nText("安装失败"), message, category="install")
        except Exception as notify_error:
            log(f"发送安装失败通知时出错: {notify_error}", logging.WARNING)
        try:
            from modules.plugin_host.dispatch import invoke_hook
            invoke_hook(
                "download.error",
                {
                    "version": version,
                    "message": str(message),
                    "loader": Loader_Type if "Loader_Type" in dir() else None,
                },
            )
            log(f"[PluginHost] download.error version={version}: {message}")
        except Exception as plugin_err:
            log(f"[PluginHost] download.error 失败: {plugin_err}", logging.WARNING)
        return False
    
    '''
    下载并安装指定版本的 Minecraft，可选安装 Fabric Loader
    
    Args:
        version (str): 要安装的 Minecraft 版本，例如 "1.21.8"
        minecraft_dir (str, optional): Minecraft 安装目录。如果未提供，默认为 %appdata%/Bloret-Launcher/.minecraft
        Fabric_Loader (bool, optional): 是否安装 Fabric Loader，默认为 False
        VersionName (str, optional): 版本目录名称，如果未提供，默认为 version 的值
        backend: Python Backend 对象，用于更新 QML UI
    
    Returns:
        bool: 安装成功返回True，失败返回False
    
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    try:
        # 创建Windows 11通知
        notify(progress={
            'title': i18nText('Minecraft 版本安装'),
            'status': i18nText('正在准备安装...'),
            'value': '0',
            'valueStringOverride': '0%'
        })

        # 0. 如果minecraft_dir未提供，设置默认值
        if minecraft_dir is None:
            minecraft_dir = os.path.join(BLglobals.datapath, '.minecraft')
            
        if Loader_Type is None:
            Loader_Type = "vanilla"
        Loader_Type = Loader_Type.lower()
        if Loader_Type == "fabric":
            Fabric_Loader = True

        # 如果未提供VersionName，则使用version作为默认值
        if VersionName is None:
            VersionName = version

        try:
            from modules.plugin_host.dispatch import invoke_hook
            invoke_hook(
                "download.start",
                {
                    "version": version,
                    "minecraft_dir": minecraft_dir,
                    "version_name": VersionName,
                    "loader_type": Loader_Type,
                    "fabric": bool(Fabric_Loader),
                },
            )
            log(f"[PluginHost] download.start version={version} loader={Loader_Type}")
        except Exception as plugin_err:
            log(f"[PluginHost] download.start 失败: {plugin_err}", logging.WARNING)

        if not _is_safe_version_name(VersionName):
            raise ValueError(f"VersionName 不是安全的单路径组件: {VersionName!r}")

        version_dir = os.path.join(minecraft_dir, "versions", VersionName)
        log(f"开始安装 Minecraft 版本: {version}，版本目录名称: {VersionName}，安装目录: {version_dir}")
        if task_state is not None:
            task_state["version_dir"] = version_dir

        # 确保目录存在
        os.makedirs(minecraft_dir, exist_ok=True)
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)
        _mark_installing(version_dir)

        # ── Bloret 快速下载源：Git Clone（成功后仍校验/补全缺失）──
        _bloret_git_done = False
        version_data = None
        config = cfg.read()
        # 使用 DownloadManager 分配的每任务线程数，否则退化为配置值
        max_thread_value = task_state.get("max_thread") if task_state else None
        if max_thread_value is None:
            max_thread_value = _clamp_workers(config.get("MaxThread", _DEFAULT_MAX_THREAD))

        if BLglobals.download_source == "gitcode":
            try:
                if bloret_git_clone_download(
                    version,
                    minecraft_dir,
                    backend,
                    cancel_event=task_state["cancel_event"] if task_state else None,
                ):
                    # git 仓库常以官方 version id 落盘；自定义 VersionName 时尝试两处
                    for candidate_dir in (
                        version_dir,
                        os.path.join(versions_dir, version),
                    ):
                        loaded, loaded_path = _load_version_json(candidate_dir, VersionName, version)
                        if loaded:
                            version_data = loaded
                            # 若落在官方 id 目录且用户指定了不同名称，复制到 VersionName 目录
                            if os.path.realpath(candidate_dir) != os.path.realpath(version_dir):
                                os.makedirs(version_dir, exist_ok=True)
                                for ext in ("json", "jar"):
                                    src = _resolve_version_file(candidate_dir, version, version, ext)
                                    if os.path.exists(src):
                                        dst = os.path.join(version_dir, f"{VersionName}.{ext}")
                                        if not os.path.exists(dst):
                                            shutil.copy2(src, dst)
                                # 以 VersionName 再写一份 JSON（id 字段保持原版）
                                with open(os.path.join(version_dir, f"{VersionName}.json"), "w", encoding="utf-8") as f:
                                    json.dump(version_data, f, ensure_ascii=False, indent=4)
                            log(f"从克隆文件加载 version_data: {loaded_path}")
                            _bloret_git_done = True
                            break
                    if not _bloret_git_done:
                        log("克隆完成但未找到 version JSON，将回退正常下载", logging.WARNING)
            except Exception as e:
                log(f"Bloret git clone 流程异常: {e}，回退正常下载", logging.WARNING)
                _bloret_git_done = False
                version_data = None

        if task_state['cancel_event'].is_set():
            return fail_install("安装已被用户取消")

        if _bloret_git_done:
            log("Bloret git clone 已完成，将校验并补全缺失的库/资源")
            update_progress({
                'value': 0.35,
                'valueStringOverride': '35%',
                'status': i18nText('快速下载完成，正在校验文件...')
            })

        # 常规路径：拉取 manifest + version JSON + client.jar
        if not version_data:
            update_progress({
                'value': 0.1,
                'valueStringOverride': '10%',
                'status': i18nText('正在获取版本清单...')
            })
            update_progress_ui(5, i18nText("正在获取版本清单..."), "", "", "")

            manifest_urls = dl_source_launcher_or_meta_get(
                "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            )
            manifest_data = None
            for url in manifest_urls:
                try:
                    log(f"正在获取版本清单: {url}")
                    response = get_session().get(url, proxies=BLglobals.get_proxies(), timeout=30)
                    if response.status_code == 200:
                        manifest_data = response.json()
                        break
                    log(f"获取版本清单失败: {url}, HTTP {response.status_code}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)

            if not manifest_data:
                return fail_install("所有版本清单 HTTPS URL 都获取失败")

            update_progress_ui(8, i18nText("正在查找指定版本..."), "", "", "")
            version_info = next(
                (ver for ver in manifest_data.get("versions", []) if ver.get("id") == version),
                None,
            )
            if not version_info:
                return fail_install(f"未找到 Minecraft 版本 {version}")
            log(f"找到版本信息: {version_info}")

            update_progress_ui(12, i18nText("正在获取版本详细信息..."), "", "", "")
            original_url = version_info.get("url")
            version_info_urls = dl_source_launcher_or_meta_get(original_url)
            version_data = None
            for url in version_info_urls:
                try:
                    log(f"正在获取版本详细信息: {url}")
                    response = get_session().get(url, timeout=30)
                    if response.status_code == 200:
                        version_data = response.json()
                        break
                    log(f"获取版本详细信息失败: {url}, HTTP {response.status_code}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)

            if not version_data:
                return fail_install("所有版本详细信息 HTTPS URL 都获取失败")

            os.makedirs(version_dir, exist_ok=True)
            version_json_path = os.path.join(version_dir, f"{VersionName}.json")
            with open(version_json_path, "w", encoding="utf-8") as f:
                json.dump(version_data, f, ensure_ascii=False, indent=4)
            log(f"已保存版本JSON文件: {version_json_path}")

        # 确保 version_dir 与 JSON 存在
        os.makedirs(version_dir, exist_ok=True)
        version_json_path = os.path.join(version_dir, f"{VersionName}.json")
        if not os.path.exists(version_json_path) and version_data:
            with open(version_json_path, "w", encoding="utf-8") as f:
                json.dump(version_data, f, ensure_ascii=False, indent=4)

        # 客户端 JAR（git 已提供则 secure_download 会跳过）
        update_progress_ui(15, i18nText("正在下载客户端JAR文件..."), "", "", "")
        if "downloads" not in version_data or "client" not in version_data["downloads"]:
            return fail_install(i18nText("版本信息中未找到客户端下载链接"))
        client_info = version_data["downloads"]["client"]
        client_url = client_info["url"]
        client_urls = dl_source_launcher_or_meta_get(client_url)
        client_jar_path = os.path.join(version_dir, f"{VersionName}.jar")
        # 兼容 git 克隆出的 {version}.jar
        alt_client = os.path.join(version_dir, f"{version}.jar")
        if not os.path.exists(client_jar_path) and os.path.exists(alt_client):
            shutil.copy2(alt_client, client_jar_path)

        def client_progress(downloaded_size, total_size):
            if total_size > 0:
                # client 阶段映射到全局 15%–30%
                frac = downloaded_size / total_size
                global_pct = 15 + int(frac * 15)
                if global_pct % 2 == 0 or frac >= 1.0:
                    update_progress_ui(
                        global_pct,
                        i18nText("正在下载客户端JAR文件..."),
                        "",
                        f"{downloaded_size // 1024 // 1024}MB",
                        f"{total_size // 1024 // 1024}MB",
                    )

        if not secure_download(
            client_urls + [client_url],
            client_jar_path,
            client_info,
            "客户端 JAR",
            progress_callback=client_progress,
            **_dl_kwargs(task_state),
        ):
            return fail_install("客户端 JAR 下载或校验失败")

        # 库文件 / natives
        natives_dir = os.path.join(version_dir, f"{VersionName}-natives")
        os.makedirs(natives_dir, exist_ok=True)
        processed_libraries = _library_download_items(version_data.get("libraries", []), minecraft_dir)
        update_progress_ui(32, i18nText("正在下载库文件..."), "", "", "")
        if processed_libraries:
            task_state['downloader'] = LibraryDownloader(
                processed_libraries,
                max_workers=max_thread_value,
                natives_dir=natives_dir,
                pause_event=task_state.get("pause_event") if task_state else None,
            )
            if task_state['cancel_event'].is_set():
                task_state['downloader'].cancel()
            if not task_state['downloader'].download_libraries():
                return fail_install("关键库/native 下载或解压失败")
        update_progress_ui(45, i18nText("库文件下载完成"), "", "", "")

        # 资源索引 + 对象
        if "assetIndex" in version_data:
            asset_index = version_data["assetIndex"]
            asset_index_url = asset_index["url"]
            asset_index_urls = dl_source_launcher_or_meta_get(asset_index_url)
            assets_dir = os.path.join(minecraft_dir, "assets")
            indexes_dir = os.path.join(assets_dir, "indexes")
            objects_dir = os.path.join(assets_dir, "objects")
            os.makedirs(indexes_dir, exist_ok=True)
            os.makedirs(objects_dir, exist_ok=True)
            asset_index_id = asset_index["id"]
            asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")

            update_progress_ui(48, i18nText("正在下载资源索引..."), "", "", "")
            log(f"正在下载资源索引: {asset_index_urls}")
            if not secure_download(
                asset_index_urls + [asset_index_url],
                asset_index_path,
                asset_index,
                "资源索引",
                **_dl_kwargs(task_state),
            ):
                return fail_install("资源索引下载或校验失败")

            with open(asset_index_path, "r", encoding="utf-8") as f:
                asset_index_data = json.load(f)

            objects = asset_index_data.get("objects") or {}
            assets_count = len(objects)
            if assets_count:
                # 预过滤：size 匹配的 hash 命名文件直接跳过，避免提交线程池与全量 SHA1
                strict = _strict_hash_verify_enabled()
                pending = []
                skipped = 0
                for asset_name, asset_info in objects.items():
                    hash_value = asset_info.get("hash")
                    if not hash_value:
                        continue
                    object_path = os.path.join(objects_dir, hash_value[:2], hash_value)
                    if os.path.exists(object_path):
                        ok, _ = _verify_file(
                            object_path,
                            asset_info.get("size"),
                            hash_value,
                            fast=not strict,
                        )
                        if ok:
                            skipped += 1
                            continue
                    pending.append((asset_name, asset_info, object_path))

                log(
                    f"资源文件: 总计 {assets_count}，已存在 {skipped}，待下载 {len(pending)}"
                )
                update_progress({
                    'status': f"资源: 跳过 {skipped}，下载 {len(pending)}...",
                    'value': 0.5,
                })

                if pending:
                    if task_state['cancel_event'].is_set():
                        return fail_install("安装已被用户取消")

                    max_workers = max_thread_value
                    log(f"使用 {max_workers} 个线程下载资源文件")
                    progress_lock = threading.Lock()
                    completed_count = 0
                    success_count = 0
                    failed_items = []
                    bytes_done = 0
                    t0 = time.monotonic()
                    total_pending = len(pending)

                    def download_asset(item):
                        asset_name, asset_info, object_path = item
                        hash_value = asset_info["hash"]
                        asset_url = f"https://resources.download.minecraft.net/{hash_value[:2]}/{hash_value}"
                        urls = dl_source_assets_get(asset_url)
                        if asset_url not in urls:
                            urls.append(asset_url)
                        ok = secure_download(
                            urls,
                            object_path,
                            asset_info,
                            f"资源对象 {asset_name}",
                            **_dl_kwargs(task_state),
                            quiet=True,
                            fast_verify=not strict,
                        )
                        return asset_name, asset_info, object_path, ok

                    def _run_asset_batch(items, label):
                        nonlocal completed_count, success_count, bytes_done
                        local_failed = []
                        with ThreadPoolExecutor(
                            max_workers=max_workers, thread_name_prefix=label
                        ) as executor:
                            future_map = {
                                executor.submit(download_asset, item): item for item in items
                            }
                            for future in concurrent.futures.as_completed(future_map):
                                if task_state['cancel_event'].is_set():
                                    break
                                try:
                                    asset_name, asset_info, object_path, ok = future.result()
                                except Exception as e:
                                    item = future_map[future]
                                    asset_name, asset_info, object_path = item
                                    log(f"处理资源文件时发生错误: {asset_name}, {e}", logging.WARNING)
                                    ok = False
                                with progress_lock:
                                    completed_count += 1
                                    if ok:
                                        success_count += 1
                                        bytes_done += int(asset_info.get("size") or 0)
                                    else:
                                        local_failed.append((asset_name, asset_info, object_path))
                                    # 资源阶段映射到全局 50%–88%
                                    frac = completed_count / max(total_pending, 1)
                                    global_pct = 50 + int(frac * 38)
                                    elapsed = max(time.monotonic() - t0, 0.001)
                                    speed = bytes_done / elapsed
                                    speed_str = (
                                        f"{speed / 1024 / 1024:.1f} MB/s"
                                        if speed > 1024 * 1024
                                        else f"{speed / 1024:.0f} KB/s"
                                    )
                                    # 粗略 ETA：按剩余文件比例
                                    remain = max(total_pending - completed_count, 0)
                                    if speed > 0 and completed_count > 0:
                                        avg_bytes = bytes_done / completed_count
                                        eta_sec = int((remain * avg_bytes) / speed) if avg_bytes > 0 else 0
                                        if eta_sec > 0:
                                            m, s = divmod(eta_sec, 60)
                                            h, m = divmod(m, 60)
                                            eta_txt = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                                            speed_str = f"{speed_str} · ETA {eta_txt}"
                                    if completed_count % max(1, total_pending // 20) == 0 or completed_count == total_pending or not ok:
                                        update_progress_ui(
                                            global_pct,
                                            i18nText("正在下载资源文件..."),
                                            speed_str,
                                            f"{completed_count}",
                                            f"{total_pending}",
                                        )
                        return local_failed

                    failed_items = _run_asset_batch(pending, "AssetsDownloader")
                    if task_state['cancel_event'].is_set():
                        return fail_install("安装已被用户取消")

                    if failed_items:
                        log(f"资源首轮失败 {len(failed_items)} 个，开始第二轮重试", logging.WARNING)
                        # 重置计数语义：第二轮只统计失败项
                        retry_total = len(failed_items)
                        completed_count = total_pending - retry_total
                        total_pending = total_pending  # 进度分母保持首轮规模
                        failed_items = _run_asset_batch(failed_items, "AssetsRetry")

                    log(
                        f"资源文件下载完成: 跳过 {skipped}, 成功 {success_count}, 失败 {len(failed_items)}"
                    )
                    if failed_items:
                        sample = ", ".join(name for name, _, _ in failed_items[:5])
                        return fail_install(
                            f"有 {len(failed_items)} 个关键资源对象下载失败（例: {sample}）"
                        )

                update_progress_ui(88, i18nText("资源文件下载完成!"), "", f"{assets_count}", f"{assets_count}")

        # 如果需要安装Fabric Loader
        if Fabric_Loader:
            log(f"开始安装 Fabric Loader 到 Minecraft {version}")
            update_progress({
                'status': f'正在安装 Fabric Loader...',
                'value': 0.9,
                'valueStringOverride': '90%'
            })
            
            try:
                # 使用PCL风格的镜像源处理获取Fabric Loader版本列表
                fabric_api_urls = dl_source_launcher_or_meta_get("https://meta.fabricmc.net/v2/versions/loader/" + version)
                log(f"正在获取Fabric Loader版本列表: {fabric_api_urls}")
                
                fabric_versions = None
                for url in fabric_api_urls:
                    try:
                        fabric_response = get_session().get(url, timeout=30)
                        if fabric_response.status_code == 200:
                            fabric_versions = fabric_response.json()
                            break
                        log(f"获取Fabric Loader版本列表失败: {url}, HTTP {fabric_response.status_code}", logging.WARNING)
                    except requests.exceptions.RequestException as e:
                        log(f"请求错误: {url}, {e}", logging.WARNING)

                if not fabric_versions:
                    raise RuntimeError(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本")

                latest_fabric = fabric_versions[0]
                loader_version = latest_fabric["loader"]["version"]
                log(f"找到最新的 Fabric Loader 版本: {loader_version}")

                fabric_version_id = f"{VersionName}-Fabric {loader_version}"
                fabric_version_dir = os.path.join(versions_dir, fabric_version_id)
                os.makedirs(fabric_version_dir, exist_ok=True)

                fabric_json_urls = dl_source_launcher_or_meta_get(
                    f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader_version}/profile/json"
                )
                log(f"正在获取Fabric安装JSON: {fabric_json_urls}")

                fabric_json_data = None
                for url in fabric_json_urls:
                    try:
                        fabric_json_response = get_session().get(url, timeout=30)
                        if fabric_json_response.status_code == 200:
                            fabric_json_data = fabric_json_response.json()
                            break
                        log(f"获取Fabric安装JSON失败: {url}, HTTP {fabric_json_response.status_code}", logging.WARNING)
                    except requests.exceptions.RequestException as e:
                        log(f"请求错误: {url}, {e}", logging.WARNING)

                if not fabric_json_data:
                    raise RuntimeError("所有 Fabric 安装 JSON URL 均获取失败")

                fabric_json_data["id"] = fabric_version_id

                # 合并原版元数据（VersionName 优先，version id 回退）
                original_version_data = version_data
                if original_version_data is None:
                    original_version_data, original_version_json_path = _load_version_json(
                        version_dir, VersionName, version
                    )
                    if original_version_data is None:
                        log(f"原始版本JSON不存在: {original_version_json_path}", logging.WARNING)

                if "downloads" not in fabric_json_data and original_version_data:
                    log("Fabric JSON不包含downloads字段，添加原始版本的资源信息")
                    for key in (
                        "assetIndex", "assets", "complianceLevel", "javaVersion",
                        "logging", "minimumLauncherVersion", "releaseTime", "time", "type",
                    ):
                        if key in original_version_data:
                            fabric_json_data[key] = original_version_data[key]

                    original_libraries = original_version_data.get("libraries", [])
                    fabric_libraries = fabric_json_data.get("libraries", [])
                    existing_lib_names = {lib.get("name", "") for lib in fabric_libraries}
                    for lib in original_libraries:
                        name = lib.get("name", "")
                        if name not in existing_lib_names:
                            fabric_libraries.append(lib)
                            existing_lib_names.add(name)
                    fabric_json_data["libraries"] = fabric_libraries
                    log("已添加原始版本的资源信息到Fabric版本")

                fabric_json_data.pop("inheritsFrom", None)
                fabric_json_data.pop("jar", None)

                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                with open(fabric_json_path, "w", encoding="utf-8") as f:
                    json.dump(fabric_json_data, f, ensure_ascii=False, indent=4)
                log(f"已保存Fabric安装JSON: {fabric_json_path}")

                fabric_client_jar_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.jar")

                if "downloads" in fabric_json_data and "client" in fabric_json_data["downloads"]:
                    client_info = fabric_json_data["downloads"]["client"]
                    client_url = client_info["url"]
                    client_urls = dl_source_launcher_or_meta_get(client_url)
                    log(f"正在下载Fabric客户端JAR文件: {client_urls}")
                    if not secure_download(
                        client_urls + [client_url],
                        fabric_client_jar_path,
                        client_info,
                        "Fabric 客户端 JAR",
                        **_dl_kwargs(task_state),
                    ):
                        raise RuntimeError("Fabric 客户端 JAR 下载或校验失败")
                else:
                    log("Fabric版本信息中未找到客户端下载链接，尝试从原始版本复制客户端JAR")
                    original_client_jar_path = _resolve_version_file(
                        version_dir, VersionName, version, "jar"
                    )
                    if os.path.exists(original_client_jar_path):
                        shutil.copy2(original_client_jar_path, fabric_client_jar_path)
                        log(f"已从原始版本复制客户端JAR: {original_client_jar_path} -> {fabric_client_jar_path}")
                    else:
                        raise RuntimeError(f"原始版本的客户端 JAR 不存在: {original_client_jar_path}")

                update_progress({
                    'status': f'正在下载 Fabric Loader 库文件...',
                    'value': 0.92,
                    'valueStringOverride': '92%'
                })
                log("开始下载 Fabric Loader 库文件...")

                fabric_libraries = fabric_json_data.get("libraries", [])
                fabric_natives_dir = os.path.join(fabric_version_dir, f"{fabric_version_id}-natives")
                os.makedirs(fabric_natives_dir, exist_ok=True)
                processed_fabric_libraries = _library_download_items(fabric_libraries, minecraft_dir)
                if processed_fabric_libraries:
                    library_downloader = LibraryDownloader(
                        processed_fabric_libraries,
                        max_workers=max_thread_value,
                        natives_dir=fabric_natives_dir,
                        pause_event=task_state.get("pause_event") if task_state else None,
                    )
                    task_state['downloader'] = library_downloader
                    if task_state['cancel_event'].is_set():
                        library_downloader.cancel()
                    if not library_downloader.download_libraries():
                        raise RuntimeError("Fabric Loader 关键库/native 下载失败")
                    log("Fabric Loader 库文件下载完成")
                else:
                    log("Fabric Loader 未声明额外库文件")

                fabric_mods_dir = os.path.join(fabric_version_dir, "mods")
                os.makedirs(fabric_mods_dir, exist_ok=True)

                # Fabric API：经 Modrinth（meta.fabricmc.net 无 fabric-api 端点）
                update_progress({
                    'status': f'正在下载 Fabric API...',
                    'value': 0.95,
                    'valueStringOverride': '95%'
                })
                try:
                    mr_url = (
                        "https://api.modrinth.com/v2/project/P7dR8mSH/version"
                        f"?game_versions={requests.utils.quote(json.dumps([version]))}"
                        f"&loaders={requests.utils.quote(json.dumps(['fabric']))}"
                    )
                    mr_resp = get_session().get(mr_url, timeout=30)
                    if mr_resp.status_code == 200:
                        versions_list = mr_resp.json() or []
                        if versions_list:
                            entry = versions_list[0]
                            files = entry.get("files") or []
                            primary = next((f for f in files if f.get("primary")), None) or (
                                files[0] if files else None
                            )
                            if primary and primary.get("url"):
                                fabric_api_path = os.path.join(
                                    fabric_mods_dir, primary.get("filename") or "fabric-api.jar"
                                )
                                api_metadata = {
                                    "size": primary.get("size"),
                                    "sha1": (primary.get("hashes") or {}).get("sha1"),
                                }
                                api_metadata = {k: v for k, v in api_metadata.items() if v is not None}
                                if not secure_download(
                                    [primary["url"]],
                                    fabric_api_path,
                                    api_metadata,
                                    "Fabric API",
                                    **_dl_kwargs(task_state),
                                ):
                                    log("Fabric API 下载失败，但不影响 Fabric Loader 安装", logging.WARNING)
                                else:
                                    log(f"Fabric API 已安装: {fabric_api_path}")
                            else:
                                log("Modrinth 返回的 Fabric API 无可用文件", logging.WARNING)
                        else:
                            log(f"Modrinth 未找到适用于 {version} 的 Fabric API", logging.WARNING)
                    else:
                        log(f"Modrinth Fabric API 查询失败: HTTP {mr_resp.status_code}", logging.WARNING)
                except Exception as e:
                    log(f"下载 Fabric API 时出错: {e}，但将继续安装流程", logging.WARNING)

                # 创建Fabric版本的resourcepacks目录
                fabric_resourcepacks_dir = os.path.join(fabric_version_dir, "resourcepacks")
                os.makedirs(fabric_resourcepacks_dir, exist_ok=True)

                update_progress({
                    'status': f'Fabric Loader 安装完成!',
                    'value': 1,
                    'valueStringOverride': '100%'
                })
                log(f"Fabric Loader 安装完成到 {fabric_version_id}")
                
                # 更新 .BL.json 文件，记录已安装的 Fabric 版本
                update_bl_json(minecraft_dir, fabric_version_id, True, None)
                
                # 同时记录原版版本到 .BL.json 文件
                update_bl_json(minecraft_dir, version, False, None)
                log(f"已将原版版本 {version} 和 Fabric 版本 {fabric_version_id} 记录到 .BL.json 文件")
                
                # 复制 servers.dat 文件到 Fabric 版本目录
                try:
                    # 检查是否存在 servers.dat 文件（程序目录下）
                    servers_dat_source = app_path("servers.dat")  # 程序目录下的 servers.dat 文件
                    if os.path.exists(servers_dat_source):
                        # Fabric版本目录
                        servers_dat_target = os.path.join(fabric_version_dir, "servers.dat")
                        shutil.copy2(servers_dat_source, servers_dat_target)
                        log(f"已复制 servers.dat 文件到 Fabric 版本: {servers_dat_target}")
                    else:
                        log(f"未找到 servers.dat 文件: {servers_dat_source}，跳过复制", logging.INFO)
                except Exception as e:
                    log(f"复制 servers.dat 文件到 Fabric 版本时出错: {e}，但安装流程继续", logging.WARNING)
                
            except Exception as e:
                log(f"安装 Fabric Loader 失败: {e}，停止安装且不登记成功", logging.ERROR)
                # 即使Fabric安装失败，原版Minecraft仍然安装成功，继续完成整个安装流程
                update_progress({
                    'status': f'Minecraft 版本 {version} 安装完成，但 Fabric Loader 安装失败!',
                    'value': 1.0
                })
                return fail_install(f"Fabric Loader 安装失败: {e}")

        forge_like_version_id_final = None
        if Loader_Type in ("forge", "neoforge"):
            display_name = "NeoForge" if Loader_Type == "neoforge" else "Forge"
            update_progress({
                'status': f'正在安装 {display_name}...',
                'value': 0.9,
                'valueStringOverride': '90%'
            })
            update_progress_ui(90, f"正在安装 {display_name}...", "", "", "")
            try:
                forge_like_version_id_final = _install_forge_like_loader(
                    Loader_Type,
                    version,
                    minecraft_dir,
                    versions_dir,
                    version_dir,
                    version_data,
                    VersionName,
                    max_thread_value,
                    task_state
                )
                update_progress({
                    'status': f'{display_name} 安装完成!',
                    'value': 1,
                    'valueStringOverride': '100%'
                })
                log(f"{display_name} 安装完成到 {forge_like_version_id_final}")
                update_bl_json(minecraft_dir, version, False, None)
            except Exception as e:
                log(f"安装 {display_name} 失败: {e}，停止安装且不登记成功", logging.ERROR)
                update_progress({
                    'status': f'Minecraft 版本 {version} 安装完成，但 {display_name} 安装失败!',
                    'value': 1.0
                })
                return fail_install(f"{display_name} 安装失败: {e}")
        
        log(f"Minecraft 版本 {version} 安装完成")
        update_progress({
            'status': f'Minecraft 版本 {version} 安装完成!',
            'value': 1.0
        })
        
        # 更新 .BL.json 文件，记录已安装的版本
        try:
            # 原版图标路径（图标位于资源根目录的 icon/ 下）
            vanilla_icon_path = app_path("icon", "Grass_Block.png")
            # Fabric 图标路径
            fabric_icon_path = app_path("icon", "fabric.png")

            # 确保路径存在，如果不存在则设为None
            if not os.path.exists(vanilla_icon_path):
                log(f"原版图标未找到: {vanilla_icon_path}", logging.WARNING)
                vanilla_icon_path = None
            if not os.path.exists(fabric_icon_path):
                log(f"Fabric图标未找到: {fabric_icon_path}", logging.WARNING)
                fabric_icon_path = None
            # 尝试获取fabric版本ID，如果fabric安装成功的话
            fabric_version_id_final = None
            if Fabric_Loader:
                try:
                    fabric_version_id_final = fabric_version_id
                except NameError:
                    # fabric_version_id未定义，说明fabric安装可能失败了
                    fabric_version_id_final = None
            
            if fabric_version_id_final:
                update_bl_json(minecraft_dir, fabric_version_id_final, True, fabric_icon_path)
                # 如果安装了Fabric版本，同时记录原版版本
                update_bl_json(minecraft_dir, version, False, vanilla_icon_path)
                log(f"已将 Fabric 版本 {fabric_version_id_final} 和原版版本 {version} 记录到 .BL.json 文件")
            elif forge_like_version_id_final:
                update_bl_json(minecraft_dir, forge_like_version_id_final, False, vanilla_icon_path)
                update_bl_json(minecraft_dir, version, False, vanilla_icon_path)
                log(f"已将 {forge_like_version_id_final} 和原版版本 {version} 记录到 .BL.json 文件")
            else:
                update_bl_json(minecraft_dir, version, False, vanilla_icon_path)
        except Exception as e:
            log(f"更新 .BL.json 文件时出错: {e}，但安装流程继续", logging.WARNING)
        
        # 复制 servers.dat 文件到安装目录
        try:
            # 检查是否存在 servers.dat 文件（程序目录下）
            servers_dat_source = app_path("servers.dat")  # 程序目录下的 servers.dat 文件
            if os.path.exists(servers_dat_source):
                # 确定目标版本目录
                if fabric_version_id_final:
                    target_version_dir = os.path.join(minecraft_dir, "versions", fabric_version_id_final)
                elif forge_like_version_id_final:
                    target_version_dir = os.path.join(minecraft_dir, "versions", forge_like_version_id_final)
                else:
                    target_version_dir = os.path.join(minecraft_dir, "versions", version)
                
                # 确保目标目录存在
                os.makedirs(target_version_dir, exist_ok=True)
                
                # 复制 servers.dat 文件
                servers_dat_target = os.path.join(target_version_dir, "servers.dat")
                shutil.copy2(servers_dat_source, servers_dat_target)
                log(f"已复制 servers.dat 文件到: {servers_dat_target}")
            else:
                log(f"未找到 servers.dat 文件: {servers_dat_source}，跳过复制", logging.INFO)
        except Exception as e:
            log(f"复制 servers.dat 文件时出错: {e}，但安装流程继续", logging.WARNING)

        _clear_installing_marker(version_dir)
        if task_state is not None:
            task_state["cleanup_on_fail"] = False

        # 通知 UI 安装完成（对话框不关闭，秒表暂停）
        if backend:
            backend.notifyDownloadComplete(i18nText(f"Minecraft {version} 安装完成！"))

        # 插件钩子：下载/安装完成
        try:
            from modules.plugin_host.dispatch import invoke_hook
            _fabric = locals().get("fabric_version_id_final")
            _forge = locals().get("forge_like_version_id_final")
            installed_name = _fabric or _forge or version
            installed_path = os.path.join(minecraft_dir, "versions", installed_name)
            ctx = {
                "version": version,
                "installed_name": installed_name,
                "path": installed_path,
                "loader": Loader_Type,
                "fabric": bool(_fabric),
            }
            invoke_hook("download.post", version, Loader_Type, installed_path)
            invoke_hook("download.complete", ctx)
            log(f"[PluginHost] download.post 已触发: {installed_name}")
        except Exception as plugin_err:
            log(f"[PluginHost] download.post 失败: {plugin_err}", logging.WARNING)
        return True

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        return fail_install(f"Minecraft {version}: {e}")
    finally:
        if task_state is not None and _current_download_state.get('task_id') is task_state.get('task_id'):
            _current_download_state = {'task_id': None, 'thread': None, 'cancel_event': threading.Event(), 'pause_event': threading.Event(), 'downloader': None, 'is_paused': False, 'backend': None, 'cancelled': False, 'completed_event': threading.Event(), 'result': None}
