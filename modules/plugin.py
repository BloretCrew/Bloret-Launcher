from modules.compat_widgets import MessageBox, Dialog
from modules.log import log
import os
import json
import requests
import zipfile
import shutil
import tempfile
import threading
import urllib.parse
import re
from pathlib import Path
from PySide6.QtWidgets import QApplication
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from modules.customize import CustomizeAppAdd
import modules.globals as BLglobals
import modules.config as cfg

MANIFEST_NAMES = ("plugin.json", "cwplugin.json")


def _safe_plugin_id(raw: str, fallback: str = "plugin") -> str:
    value = (raw or "").strip() or fallback
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return value or fallback


def _read_manifest_file(plugin_dir: str) -> dict:
    for name in MANIFEST_NAMES:
        path = os.path.join(plugin_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except Exception as error:
            log(f"[Plugin] 读取清单失败 {path}: {error}")
    return {}


def _resolve_project_root(extracted_dir: str) -> str:
    """支持 ZIP 根直接是插件，或仅有一层包装目录。"""
    if _read_manifest_file(extracted_dir):
        return extracted_dir
    try:
        children = [
            os.path.join(extracted_dir, entry)
            for entry in os.listdir(extracted_dir)
            if os.path.isdir(os.path.join(extracted_dir, entry)) and not entry.startswith(".")
        ]
    except Exception:
        children = []
    if len(children) == 1 and _read_manifest_file(children[0]):
        return children[0]
    raise ValueError("插件包中未找到 plugin.json / cwplugin.json")


def _safe_extract_zip(archive_path: str, destination: str) -> None:
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as bundle:
        for member in bundle.infolist():
            target = (root / member.filename).resolve()
            try:
                target.relative_to(root)
            except ValueError as error:
                raise ValueError(f"不安全的压缩包成员: {member.filename}") from error
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def _maybe_register_legacy_process(plugin_dir: str, plugin_name: str) -> None:
    plugin_exe_path = os.path.join(plugin_dir, "main.exe")
    if not os.path.exists(plugin_exe_path):
        log(f"[Plugin] 未找到兼容进程入口 main.exe: {plugin_exe_path}")
        return
    log(f"[Plugin] 找到插件主程序: {plugin_exe_path}")
    try:
        result = CustomizeAppAdd(plugin_exe_path, plugin_name)
        if result:
            log(f"[Plugin] 已将主程序加入自定义程序列表: {plugin_exe_path}")
        else:
            log(f"[Plugin] 未能将主程序加入自定义程序列表: {plugin_exe_path}")
    except Exception as error:
        log(f"[Plugin] 调用 CustomizeAppAdd 失败: {error}")


def install_plugin_from_path(source_path, plugin_name=None, force=True):
    """
    从本地目录或 ZIP 安装插件。
    目录名优先使用 plugin.json 的 id；返回 (ok, plugin_id_or_error)。
    """
    source = os.path.abspath(os.path.expanduser(str(source_path or "")))
    if not source:
        return False, "未指定插件路径"
    log(f"[Plugin] install_plugin_from_path source={source} force={force}")
    temp_root = None
    try:
        if os.path.isdir(source):
            project = _resolve_project_root(source)
        elif os.path.isfile(source) and zipfile.is_zipfile(source):
            temp_root = tempfile.mkdtemp(prefix="bloret-plugin-")
            extract_dir = os.path.join(temp_root, "archive")
            os.makedirs(extract_dir, exist_ok=True)
            log(f"[Plugin] 解压插件包到临时目录: {extract_dir}")
            _safe_extract_zip(source, extract_dir)
            project = _resolve_project_root(extract_dir)
        else:
            return False, "插件源必须是目录或 .zip 文件"

        manifest = _read_manifest_file(project)
        if not manifest:
            return False, "插件包缺少 plugin.json / cwplugin.json"

        plugin_id = _safe_plugin_id(
            str(manifest.get("id") or plugin_name or os.path.basename(project.rstrip(os.sep))),
            fallback=str(plugin_name or os.path.basename(project.rstrip(os.sep)) or "plugin"),
        )
        display_name = str(manifest.get("name") or plugin_id)
        plugin_root = get_plugin_root()
        os.makedirs(plugin_root, exist_ok=True)
        target_dir = os.path.join(plugin_root, plugin_id)
        staging_dir = os.path.join(plugin_root, f".{plugin_id}.installing")

        if os.path.exists(target_dir) and not force:
            return False, f"插件已安装: {plugin_id}"

        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        shutil.copytree(project, staging_dir)
        log(f"[Plugin] 暂存完成: {staging_dir}")

        if os.path.exists(target_dir):
            backup_root = os.path.join(plugin_root, ".backups")
            os.makedirs(backup_root, exist_ok=True)
            backup_dir = os.path.join(backup_root, f"{plugin_id}-{int(time.time())}")
            log(f"[Plugin] 备份旧版本到 {backup_dir}")
            shutil.move(target_dir, backup_dir)

        os.replace(staging_dir, target_dir)
        _maybe_register_legacy_process(target_dir, display_name)
        log(f"[Plugin] 插件安装成功 id={plugin_id} path={target_dir}")

        try:
            from modules.plugin_host import get_plugin_host

            get_plugin_host().notify_installed(plugin_id)
            log(f"[Plugin] 已通知 PluginHost 加载: {plugin_id}")
        except Exception as host_err:
            log(f"[Plugin] 通知 PluginHost 失败（可忽略）: {host_err}")
        return True, plugin_id
    except Exception as error:
        log(f"[Plugin] install_plugin_from_path 失败: {error}")
        return False, str(error)
    finally:
        if temp_root and os.path.isdir(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)


def install_plugin_from_zip(zip_url, plugin_name=None, expected_sha256=None):
    '''
    直接从 ZIP 文件 URL 安装插件。
    参数:
        zip_url: ZIP 文件的下载 URL
        plugin_name: 可选回退名称；实际目录优先使用清单 id
        expected_sha256: 可选，下载后校验
    返回:
        bool（兼容旧调用）或在内部使用 install_plugin_from_zip_ex 获取详情
    '''
    ok, _detail = install_plugin_from_zip_ex(
        zip_url, plugin_name=plugin_name, expected_sha256=expected_sha256
    )
    return bool(ok)


def install_plugin_from_zip_ex(zip_url, plugin_name=None, expected_sha256=None):
    """从 URL 下载 ZIP 并安装；返回 (ok, plugin_id_or_error)。"""
    try:
        from modules.plugin_install_request import verify_sha256, validate_download_url

        log(f"[Plugin] 正在从 ZIP URL 安装插件: {zip_url}")
        ok_url, url_err = validate_download_url(str(zip_url or ""), allow_file=False)
        if not ok_url:
            log(f"[Plugin] download URL 校验失败: {url_err}")
            return False, url_err

        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.get(zip_url, timeout=120, stream=True)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_zip.write(chunk)
            temp_zip_path = temp_zip.name

        try:
            if expected_sha256:
                ok_hash, hash_err = verify_sha256(temp_zip_path, expected_sha256)
                if not ok_hash:
                    log(f"[Plugin] ZIP sha256 校验失败: {hash_err}")
                    return False, hash_err
            ok, detail = install_plugin_from_path(
                temp_zip_path, plugin_name=plugin_name, force=True
            )
            if not ok:
                log(f"[Plugin] ZIP URL 安装失败: {detail}")
            return ok, detail
        finally:
            try:
                os.unlink(temp_zip_path)
            except OSError:
                pass
    except Exception as e:
        log(f"从ZIP文件安装插件时发生错误: {str(e)}")
        return False, str(e)


def install_from_request(req) -> tuple:
    """根据 PluginInstallRequest 执行下载/安装（调用前应已用户确认）。

    返回 (ok, plugin_id_or_error)。
    """
    from modules.plugin_install_request import (
        PluginInstallRequest,
        validate_download_url,
        verify_sha256,
    )

    if not isinstance(req, PluginInstallRequest):
        return False, "无效的安装请求"

    download = (req.download or "").strip()
    log(
        f"[PluginStore] install_from_request token={req.token[:8]}… "
        f"source={req.source} host={req.download_host()} sha256={'yes' if req.sha256 else 'no'}"
    )

    ok_url, url_err = validate_download_url(download, allow_file=bool(req.allow_file))
    if not ok_url:
        return False, url_err

    # file:// 本地路径
    if download.lower().startswith("file:"):
        parsed = urllib.parse.urlparse(download)
        path = urllib.parse.unquote(parsed.path or "")
        if os.name == "nt" and path.startswith("/") and len(path) >= 3 and path[2] == ":":
            path = path[1:]
        if req.sha256:
            ok_hash, hash_err = verify_sha256(path, req.sha256)
            if not ok_hash:
                return False, hash_err
        return install_plugin_from_path(
            path, plugin_name=req.name or req.id or None, force=True
        )

    return install_plugin_from_zip_ex(
        download,
        plugin_name=req.name or req.id or None,
        expected_sha256=req.sha256 or None,
    )


def addPlugin(list_url, plugin_name):
    '''
    添加插件到 Bloret Launcher
    参数:
        list_url: 包含插件信息的列表或字典或URL字符串
        window: 父窗口，用于显示对话框
    '''
    try:
        # 1. list_url 是一个 url，获取 JSON 数据，存入变量 plugin
        
        if not list_url:
            log("无效的URL")
            return False
            
        log(f"正在从以下位置获取插件信息: {list_url}")
        
        # 检查是否是直接的ZIP文件URL（通过文件扩展名判断）
        if list_url.endswith('.zip'):
            # 直接处理ZIP文件下载
            return install_plugin_from_zip(list_url, plugin_name)
        
        # 创建一个带有重试策略的会话
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 尝试请求，处理SSL错误
        try:
            response = session.get(list_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.SSLError as ssl_error:
            log(f"SSL错误: {str(ssl_error)}")
            # 尝试禁用SSL验证再次请求（仅作为备选方案）
            try:
                response = session.get(list_url, verify=False, timeout=30)
                response.raise_for_status()
                log("警告: SSL验证已禁用，仅作为备选方案")
            except Exception as fallback_error:
                raise Exception(f"SSL连接失败，备选方案也失败: {str(fallback_error)}")
        except Exception as e:
            raise Exception(f"网络请求失败: {str(e)}")
        
        # 检查响应内容是否为空
        if not response.text or not response.text.strip():
            raise Exception("服务器返回空响应")
            
        # 检查响应内容是否为JSON格式
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            # 如果不是JSON类型，记录响应内容的前200个字符用于调试
            preview_content = response.text[:200] if response.text else "空响应"
            raise Exception(f"服务器返回非JSON内容 (Content-Type: {content_type}): {preview_content}")
        
        try:
            plugin = response.json()
        except json.JSONDecodeError as json_error:
            # 如果JSON解析失败，记录响应内容用于调试
            preview_content = response.text[:200] if response.text else "空响应"
            raise Exception(f"JSON解析失败: {str(json_error)}. 响应内容预览: {preview_content}")
            
        # 验证插件数据格式
        log(f"获取到的数据：{plugin}")
        if not isinstance(plugin, dict) or 'name' not in plugin or 'download' not in plugin:
            log("插件数据格式不正确")
            return False

        # 2. 通过网页界面询问用户是否安装插件，而不是使用桌面对话框
        # 构造插件确认页面的URL
        plugin_data = {
            'name': plugin['name'],
            'download': plugin['download'],
            'master': plugin.get('master', 'Unknown'),
            'version': plugin.get('version', 'Unknown')
        }
        
        # 将插件数据编码为URL参数
        plugin_params = urllib.parse.urlencode(plugin_data)
        confirmation_url = f"http://localhost:25252/plugin/confirm?{plugin_params}"
        
        log(f"请在浏览器中打开以下链接确认插件安装: {confirmation_url}")
        # 这里应该触发浏览器打开confirmation_url页面
        # 在实际应用中，可能需要调用系统默认浏览器打开这个链接

        # 3. 用户确认后，下载和解压缩过程放到新线程中进行
        def install_plugin_task():
            try:
                log(f"开始安装插件: {plugin['name']}")

                download_url = plugin['download']
                log(f"[Plugin] 正在下载插件: {plugin['name']} 从 {download_url}")
                ok = install_plugin_from_zip(download_url, plugin.get('name') or plugin_name)
                if not ok:
                    raise Exception(f"安装插件失败: {plugin['name']}")
                log(f"[Plugin] 插件安装成功: {plugin['name']}")

            except Exception as e:
                log(f"安装插件失败: {plugin['name']}, 错误: {str(e)}")
                # 可以在这里添加错误处理，比如显示错误消息

        # 启动新线程执行安装任务
        install_thread = threading.Thread(target=install_plugin_task)
        install_thread.daemon = True
        install_thread.start()

        return True

    except Exception as e:
        log(f"添加插件时发生错误: {str(e)}")
        return False


def get_plugin_root():
    return os.path.join(BLglobals.datapath, 'Plugin')


def _load_manifest(plugin_dir):
    return _read_manifest_file(plugin_dir)


def _find_icon_path(plugin_dir, manifest):
    icon_candidates = []
    icon_value = manifest.get('icon') if isinstance(manifest, dict) else None
    if icon_value:
        icon_candidates.append(os.path.join(plugin_dir, icon_value))

    icon_candidates.extend([
        os.path.join(plugin_dir, "icon.png"),
        os.path.join(plugin_dir, "icon.jpg"),
        os.path.join(plugin_dir, "icon.jpeg"),
        os.path.join(plugin_dir, "icon.ico"),
        os.path.join(plugin_dir, "logo.png"),
    ])

    for candidate in icon_candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return ""


def _find_entry_path(plugin_dir, manifest):
    entry_value = manifest.get('entry') if isinstance(manifest, dict) else None
    if entry_value:
        entry_path = os.path.join(plugin_dir, entry_value)
        if os.path.exists(entry_path):
            return entry_path

    fallback_entries = [
        os.path.join(plugin_dir, "main.exe"),
        os.path.join(plugin_dir, "main.py"),
        os.path.join(plugin_dir, "main.qml"),
    ]
    for candidate in fallback_entries:
        if os.path.exists(candidate):
            return candidate

    return ""


def list_installed_plugins():
    """列出已安装插件；优先使用 PluginHost 运行时信息。"""
    try:
        from modules.plugin_host import get_plugin_host
        host = get_plugin_host()
        runtime = host.list_plugins_info()
        if runtime:
            return runtime
    except Exception as e:
        log(f"[Plugin] PluginHost 列表不可用，回退目录扫描: {e}")

    plugin_root = get_plugin_root()
    if not os.path.exists(plugin_root):
        return []

    plugins = []
    try:
        for entry in sorted(os.listdir(plugin_root)):
            plugin_dir = os.path.join(plugin_root, entry)
            if not os.path.isdir(plugin_dir):
                continue

            manifest = _load_manifest(plugin_dir)
            plugin_id = manifest.get('id') if isinstance(manifest, dict) else None
            plugin_name = manifest.get('name') if isinstance(manifest, dict) else None

            info = {
                "id": plugin_id or entry,
                "name": plugin_name or entry,
                "version": manifest.get('version', '') if isinstance(manifest, dict) else "",
                "author": manifest.get('author', '') if isinstance(manifest, dict) else "",
                "description": manifest.get('description', '') if isinstance(manifest, dict) else "",
                "url": manifest.get('url', '') if isinstance(manifest, dict) else "",
                "folderName": entry,
                "path": plugin_dir,
                "iconPath": _find_icon_path(plugin_dir, manifest),
                "entryPath": _find_entry_path(plugin_dir, manifest),
                "enabled": True,
                "active": False,
            }
            plugins.append(info)
    except Exception as e:
        log(f"扫描插件目录失败: {str(e)}")
        return []

    return plugins


def _is_path_under(child_path, root_path):
    try:
        child = os.path.abspath(child_path)
        root = os.path.abspath(root_path)
        return os.path.commonpath([child, root]) == root
    except Exception:
        return False


def uninstall_plugin(plugin_name):
    plugin_root = get_plugin_root()
    if not os.path.exists(plugin_root):
        return False, "插件目录不存在"

    target_dir = None
    target_info = None
    for plugin in list_installed_plugins():
        if plugin_name in (plugin.get("folderName"), plugin.get("id"), plugin.get("name")):
            target_dir = plugin.get("path")
            target_info = plugin
            break

    if not target_dir or not os.path.exists(target_dir):
        return False, "未找到指定插件"

    if not _is_path_under(target_dir, plugin_root):
        return False, "插件路径无效"

    removed_customize = 0
    try:
        config_data = cfg.read()
        customize = config_data.get("Customize", [])
        if isinstance(customize, list):
            new_customize = []
            for item in customize:
                item_path = item.get("path", "") if isinstance(item, dict) else ""
                if item_path and _is_path_under(item_path, target_dir):
                    removed_customize += 1
                    continue
                new_customize.append(item)

            config_data["Customize"] = new_customize
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"更新自定义程序配置失败: {str(e)}")

    try:
        shutil.rmtree(target_dir)
    except Exception as e:
        log(f"删除插件目录失败: {str(e)}")
        return False, f"删除插件目录失败: {str(e)}"

    plugin_display = target_info.get("name") if target_info else os.path.basename(target_dir)
    try:
        from modules.plugin_host import get_plugin_host
        from modules.plugin_host import state as plugin_state
        pid = (target_info or {}).get("id") or plugin_name
        get_plugin_host().notify_uninstalled(pid)
        plugin_state.remove_plugin_state(pid)
    except Exception as e:
        log(f"[Plugin] 卸载后通知 PluginHost 失败: {e}")
    return True, f"已卸载插件 {plugin_display}，移除 {removed_customize} 个启动项"