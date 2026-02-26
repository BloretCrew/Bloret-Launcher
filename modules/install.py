# Removed qfluentwidgets imports for PySide6 compatibility
import logging, os, json, platform, requests, shutil, concurrent.futures, threading, time, sys
try:
    import send2trash
except ImportError:
    send2trash = None
from pathlib import Path
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

thread_local_data = threading.local()

_current_download_state = {
    'downloader': None,
    'is_paused': False,
    'backend': None,
    'cancelled': False
}

def get_session():
    """获取线程本地的 requests.Session 对象，实现连接复用"""
    if not hasattr(thread_local_data, "session"):
        thread_local_data.session = requests.Session()
    return thread_local_data.session

def toggle_current_download_pause():
    global _current_download_state
    downloader = _current_download_state.get('downloader')
    backend = _current_download_state.get('backend')
    if downloader:
        if _current_download_state['is_paused']:
            downloader.resume()
            _current_download_state['is_paused'] = False
        else:
            downloader.pause()
            _current_download_state['is_paused'] = True
        if backend:
            backend.setDownloadPaused(_current_download_state['is_paused'])

def cancel_current_download():
    global _current_download_state
    _current_download_state['cancelled'] = True
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
            script_dir = Path(__file__).parent.parent.absolute()
            ui_file_path = os.path.join(script_dir, ui_file_path)
        
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

def dl_source_launcher_or_meta_get(original_url):
    """
    根据PCL启动器的DlSourceLauncherOrMetaGet方法实现
    返回下载URL的镜像源列表
    """
    if not original_url:
        raise Exception("无对应的 json 下载地址")
    
    # 官方源
    official_urls = [original_url]
    
    # 镜像源
    mirror_urls = [original_url
        .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://launcher.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://launchermeta.mojang.com", "https://bmclapi2.bangbang93.com")
    ]
    
    # 根据是否优先使用官方源决定URL顺序
    # 这里我们默认使用镜像源优先，与PCL的逻辑保持一致
    return mirror_urls + official_urls

def dl_source_library_get(original_url):
    """
    根据PCL启动器的DlSourceLibraryGet方法实现
    返回库文件URL的镜像源列表
    """
    candidate_urls = []
    
    # 镜像源
    mirror_urls = []
    if "libraries.minecraft.net" in original_url:
        mirror_urls.append(original_url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/"))
        mirror_urls.append(original_url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/libraries/"))
    elif "maven.fabricmc.net" in original_url:
        mirror_urls.append(original_url.replace("https://maven.fabricmc.net/", "https://bmclapi2.bangbang93.com/maven/"))
    
    # 添加 BMCLAPI 镜像源
    mirror_urls.append(original_url
        .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven")
        .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"))
    mirror_urls.append(original_url
        .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
        .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries"))

    # 优先添加镜像源
    candidate_urls.extend(mirror_urls)
    # 最后添加官方源
    candidate_urls.append(original_url)
    
    return candidate_urls

def dl_source_assets_get(original_url):
    """
    根据PCL启动器的DlSourceAssetsGet方法实现
    返回资源文件URL的镜像源列表
    """
    original_url = original_url.replace("http://resources.download.minecraft.net", "https://resources.download.minecraft.net")
    
    # 官方源
    official_urls = [original_url]
    
    # 镜像源
    mirror_urls = [original_url
        .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/assets")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/assets")
        .replace("https://resources.download.minecraft.net", "https://bmclapi2.bangbang93.com/assets")
    ]
    
    # 根据是否优先使用官方源决定URL顺序
    # 这里我们默认使用镜像源优先，与PCL的逻辑保持一致
    return mirror_urls + official_urls

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

class LibraryDownloader:
    def __init__(self, missing_libraries, max_workers=64):
        self.missing_libraries = missing_libraries
        self.max_workers = max_workers
        self.completed_count = 0
        self.total_count = len(missing_libraries)
        self._active_downloads = 0
        self._active_downloads_lock = threading.Lock()
        self.lock = threading.Lock()
        self.completed_event = threading.Event()
        self._paused = False
        self._pause_cond = threading.Condition(self.lock)

    @property
    def is_paused(self):
        with self.lock:
            return self._paused

    def pause(self):
        with self.lock:
            self._paused = True
            log("下载已暂停")

    def resume(self):
        with self.lock:
            self._paused = False
            self._pause_cond.notify_all()
            log("下载已恢复")
        
    def download_single_library(self, lib_item, download_dialog=None):
        with self.lock:
            while self._paused:
                self._pause_cond.wait()
        lib, lib_path = lib_item

        # 如果文件已存在且大小匹配，则跳过下载
        if os.path.exists(lib_path):
            expected_size = lib.get("downloads", {}).get("artifact", {}).get("size")
            if expected_size is not None:
                actual_size = os.path.getsize(lib_path)
                if actual_size == expected_size:
                    log(f"库文件已存在且大小匹配，跳过下载: {lib_path}")
                    # 增加完成计数
                    with self.lock:
                        self.completed_count += 1
                    # 减少活动下载计数
                    with self._active_downloads_lock:
                        self._active_downloads -= 1
                    return True # 成功跳过
                else:
                    log(f"库文件已存在但大小不匹配，重新下载: {lib_path} (预期: {expected_size}, 实际: {actual_size})")
            else:
                log(f"库文件已存在，但未提供预期大小，跳过下载: {lib_path}")
                # 增加完成计数
                with self.lock:
                    self.completed_count += 1
                # 减少活动下载计数
                with self._active_downloads_lock:
                    self._active_downloads -= 1
                return True # 成功跳过

        # 增加活动下载计数
        with self._active_downloads_lock:
            self._active_downloads += 1
            if download_dialog:
                try:
                    thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                    if thread_label:
                        QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                           str(self._active_downloads))
                except Exception as e:
                    log(f"更新libraries_file_working_Thread时出错: {e}")

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(lib_path), exist_ok=True)
            
            # 下载库文件
            if "downloads" in lib and "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                original_url = artifact["url"]
                
                candidate_urls = dl_source_library_get(original_url)

                downloaded = False
                for url_to_try in candidate_urls:
                    for attempt in range(3): # 尝试3次
                        try:
                            log(f"正在下载库文件 (尝试 {attempt + 1}/3): {url_to_try} -> {lib_path}")
                            # 使用 session 复用连接
                            session = get_session()
                            response = session.get(url_to_try, proxies=None, timeout=30)
                            if response.status_code == 200:
                                with open(lib_path, 'wb') as f:
                                    f.write(response.content)
                                log(f"成功下载库文件: {lib_path}")
                                downloaded = True
                                break # 成功下载，跳出重试循环
                            else:
                                log(f"下载失败 (HTTP {response.status_code}) (尝试 {attempt + 1}/3): {url_to_try}", logging.WARNING)
                        except requests.exceptions.SSLError as e:
                            log(f"SSL错误 (尝试 {attempt + 1}/3) {url_to_try}: {str(e)}", logging.WARNING)
                            # 尝试使用HTTP协议
                            try:
                                http_url = url_to_try.replace("https://", "http://")
                                log(f"尝试使用HTTP协议: {http_url}")
                                session = get_session()
                                response = session.get(http_url, proxies=None, timeout=30)
                                if response.status_code == 200:
                                    with open(lib_path, 'wb') as f:
                                        f.write(response.content)
                                    log(f"成功下载库文件 (HTTP): {lib_path}")
                                    downloaded = True
                                    break # 成功下载，跳出重试循环
                                else:
                                    log(f"HTTP下载失败 (HTTP {response.status_code}) (尝试 {attempt + 1}/3): {http_url}", logging.WARNING)
                            except requests.exceptions.RequestException as e2:
                                log(f"HTTP协议也失败 (尝试 {attempt + 1}/3) {http_url}: {str(e2)}", logging.WARNING)
                        except requests.exceptions.RequestException as e:
                            log(f"下载异常 (尝试 {attempt + 1}/3) {url_to_try}: {str(e)}", logging.WARNING)
                        except Exception as e:
                            log(f"未知下载错误 (尝试 {attempt + 1}/3) {url_to_try}: {str(e)}", logging.WARNING)
                        time.sleep(1) # 等待1秒后重试
                    if downloaded: # 如果已下载，跳出URL循环
                        break
                
                if not downloaded:
                    log(f"所有镜像源和重试都下载失败: {lib_path}", logging.ERROR)
                    return False
            elif "name" in lib:
                # 处理 Maven 风格的库名称
                parts = lib["name"].split(":")
                if len(parts) >= 3:
                    group_id, artifact_id, version = parts[0:3]
                    
                    original_url = f"https://maven.fabricmc.net/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar" # Fabric Maven
                    candidate_urls = dl_source_library_get(original_url)

                    downloaded = False
                    for url_to_try in candidate_urls:
                        for attempt in range(3): # 尝试3次
                            try:
                                log(f"正在下载库文件 (尝试 {attempt + 1}/3): {url_to_try} -> {lib_path}")
                                # 使用 session 复用连接
                                session = get_session()
                                response = session.get(url_to_try, proxies=None, timeout=30)
                                if response.status_code == 200:
                                    with open(lib_path, 'wb') as f:
                                        f.write(response.content)
                                    log(f"成功下载库文件: {lib_path}")
                                    downloaded = True
                                    break # 成功下载，跳出重试循环
                                else:
                                    log(f"下载失败 (HTTP {response.status_code}) (尝试 {attempt + 1}/3): {url_to_try}", logging.WARNING)
                            except requests.exceptions.RequestException as e:
                                log(f"下载异常 (尝试 {attempt + 1}/3) {url_to_try}: {str(e)}", logging.WARNING)
                            except Exception as e:
                                log(f"未知下载错误 (尝试 {attempt + 1}/3) {url_to_try}: {str(e)}", logging.WARNING)
                            time.sleep(1) # 等待1秒后重试
                        if downloaded: # 如果已下载，跳出URL循环
                            break
                    
                    if not downloaded:
                        log(f"所有镜像源和重试都下载失败: {lib_path}", logging.ERROR)
                        return False
            
            # 更新完成计数
            with self.lock:
                self.completed_count += 1
                if download_dialog:
                    try:
                        lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                        if lib_progress_bar:
                            progress_value = int((self.completed_count / self.total_count) * 100)
                            QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                                   progress_value)
                    except Exception as e:
                        log(f"更新libraries_progress时出错: {e}")
            return True # 成功下载
        except Exception as e:
            log(f"下载库文件失败 {lib_path}: {str(e)}", logging.WARNING)
            # 更新完成计数（即使失败也计数）
            with self.lock:
                self.completed_count += 1
        finally:
            # 减少活动下载计数
            with self._active_downloads_lock:
                self._active_downloads -= 1
                if download_dialog:
                    try:
                        thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                        if thread_label:
                            QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                               Q_ARG(str, str(self._active_downloads)))
                    except Exception as e:
                        log(f"更新libraries_file_working_Thread时出错: {e}")
    
    def download_libraries(self, download_dialog=None):
        if download_dialog:
            try:
                lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                if lib_progress_bar:
                    QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                           Q_ARG(int, 0))
                if thread_label:
                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                           Q_ARG(str, "0"))
            except Exception as e:
                log(f"初始化libraries_progress或libraries_file_working_Thread时出错: {e}")
        
        log(f"使用 {self.max_workers} 个线程下载库文件")
        
        # 使用线程池并发下载
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="LibraryDownloader") as executor:
            futures = [executor.submit(self.download_single_library, lib_item, download_dialog) for lib_item in self.missing_libraries]
            # 等待所有下载完成
            concurrent.futures.wait(futures)
        
        all_downloads_successful = True
        for future in futures:
            if not future.result():
                all_downloads_successful = False
                break

        if not all_downloads_successful:
            log("Fabric Loader 库文件下载失败", logging.ERROR)

        # 显示完成通知
        if download_dialog:
            try:
                lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                if lib_progress_bar:
                    QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                           Q_ARG(int, 100))
                if thread_label:
                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                           Q_ARG(str, "0"))
            except Exception as e:
                log(f"更新libraries_progress或libraries_file_working_Thread时出错: {e}")
        
        # 设置完成事件
        self.completed_event.set()

    def download_file(self, url, file_path):
        """
        下载单个文件的辅助函数
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            log(f"正在下载文件: {url} -> {file_path}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                log(f"成功下载文件: {file_path}")
                return True
            else:
                log(f"下载文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                return False
        except Exception as e:
            log(f"下载文件失败 {url}: {str(e)}", logging.ERROR)
            return False

# 添加全局的download_file函数，供Fabric Loader安装使用
def download_file(url, file_path):
    """
    全局下载单个文件的辅助函数，供Fabric Loader安装使用
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        log(f"正在下载文件: {url} -> {file_path}")
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            log(f"成功下载文件: {file_path}")
            return True
        else:
            log(f"下载文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
            return False
    except Exception as e:
        log(f"下载文件失败 {url}: {str(e)}", logging.ERROR)
        return False

def InstallMinecraftVersion(version, minecraft_dir=None, download_dialog=None, Fabric_Loader=False, VersionName=None, backend=None):
    global _current_download_state
    
    _current_download_state = {
        'downloader': None,
        'is_paused': False,
        'backend': backend,
        'cancelled': False
    }
    
    if VersionName is None:
        VersionName = version
        
    thread = Thread(target=_install_minecraft_version_threaded, args=(version, minecraft_dir, Fabric_Loader, VersionName, backend))
    thread.start()

def _install_minecraft_version_threaded(version, minecraft_dir=None, Fabric_Loader=False, VersionName=None, backend=None):
    global _current_download_state
    
    def update_progress_ui(progress, status, speed="", downloaded="", total=""):
        if backend:
            backend.updateDownloadProgress(progress, status, speed, downloaded, total)
    
    def close_dialog_ui():
        if backend:
            backend.closeDownloadDialog()
    
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
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
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
            
        # 如果未提供VersionName，则使用version作为默认值
        if VersionName is None:
            VersionName = version

        version_dir = os.path.join(minecraft_dir, "versions", VersionName)
        log(f"开始安装 Minecraft 版本: {version}，版本目录名称: {VersionName}，安装目录: {version_dir}")

        # 确保目录存在
        os.makedirs(minecraft_dir, exist_ok=True)
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)

        # 1. 获取版本清单，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.1, 
            'valueStringOverride': '10%',
            'status': i18nText('正在获取版本清单...')
        })

        # 创建 LibraryDownloader 实例
        # 假设 missing_libraries 在后续步骤中获取
        # 这里先创建一个空的，后续再更新


        
        # 定义版本清单URL列表，使用PCL风格的镜像源处理
        manifest_urls = dl_source_launcher_or_meta_get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
        
        manifest_data = None
        for url in manifest_urls:
            try:
                log(f"正在获取版本清单: {url}")
                response = requests.get(url, proxies=None, timeout=30)
                if response.status_code == 200:
                    manifest_data = response.json()
                    break
                else:
                    log(f"获取版本清单失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议
                try:
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    response = requests.get(http_url, proxies=None, timeout=30)
                    if response.status_code == 200:
                        manifest_data = response.json()
                        break
                except requests.exceptions.ConnectionError as e2:
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        if not manifest_data:
            log("所有版本清单URL都获取失败", logging.ERROR)
            return False

        # 2. 在清单中查找指定版本
        update_progress({
            'value': 0.2, 
            'valueStringOverride': '20%',
            'status': i18nText('正在查找指定版本...')
        })
        version_info = None
        for ver in manifest_data.get("versions", []):
            if ver.get("id") == version:
                version_info = ver
                break

        if not version_info:
            log(f"未找到版本 {version}", logging.ERROR)
            return False

        log(f"找到版本信息: {version_info}")

        # 3. 获取版本详细信息URL并使用PCL风格的镜像源处理
        update_progress({
            'value': 0.3, 
            'valueStringOverride': '30%',
            'status': i18nText('正在获取版本详细信息...')
        })
        original_url = version_info.get("url")
        
        # 使用PCL风格的镜像源处理
        version_info_urls = dl_source_launcher_or_meta_get(original_url)

        log(f"正在获取版本详细信息: {version_info_urls}")
        version_data = None
        
        for url in version_info_urls:
            try:
                log(f"正在获取版本详细信息: {url}")
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    version_data = response.json()
                    break
                else:
                    log(f"获取版本详细信息失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议
                try:
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    response = requests.get(http_url, timeout=30)
                    if response.status_code == 200:
                        version_data = response.json()
                        break
                except requests.exceptions.ConnectionError as e2:
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        if not version_data:
            log("所有版本详细信息URL都获取失败", logging.ERROR)
            return False

        # 5. 确保版本目录存在
        update_progress({
            'value': 0.4, 
            'valueStringOverride': '40%',
            'status': i18nText('正在确保版本目录存在...')
        })
        os.makedirs(version_dir, exist_ok=True)

        # 保存版本JSON文件
        version_json_path = os.path.join(version_dir, f"{VersionName}.json")  # JSON文件名也使用VersionName
        with open(version_json_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=4)

        log(f"已保存版本JSON文件: {version_json_path}")

        # 设置 First_Step_CheckBox 为 true
        if download_dialog:
                    try:
                        # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                        checkbox = download_dialog.findChild(QCheckBox, "First_Step_CheckBox")
                        if checkbox:
                            QMetaObject.invokeMethod(checkbox, "setChecked", Qt.QueuedConnection, True)
                    except Exception as e:
                        log(f"设置First_Step_CheckBox时出错: {e}")

        # 下载客户端JAR文件，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.5, 
            'valueStringOverride': '50%',
            'status': i18nText('正在下载客户端JAR文件...')
        })
        if "downloads" in version_data and "client" in version_data["downloads"]:
            client_info = version_data["downloads"]["client"]
            client_url = client_info["url"]
            
            # 使用PCL风格的镜像源处理
            client_urls = dl_source_launcher_or_meta_get(client_url)

            client_jar_path = os.path.join(version_dir, f"{VersionName}.jar")  # 使用VersionName作为JAR文件名
            log(f"正在下载客户端JAR文件: {client_urls}")

            download_success = False
            for url in client_urls:
                try:
                    log(f"正在下载客户端JAR文件: {url}")
                    # 使用Session来更好地管理连接
                    with requests.Session() as session:
                        response = session.get(url, stream=True, timeout=30)
                        if response.status_code == 200:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            
                            with open(client_jar_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        
                                        # 更新客户端JAR进度条（每5%更新一次）
                                        if download_dialog and total_size > 0:
                                            try:
                                                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                if progress_bar:
                                                    progress_value = int((downloaded_size / total_size) * 100)
                                                    # 只更新到5%的倍数，避免频繁更新
                                                    if progress_value % 5 == 0 or progress_value == 100:
                                                        QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection, progress_value)
                                            except Exception as e:
                                                log(f"更新client_jar_progress时出错: {e}")
                            
                            log(f"已下载客户端JAR文件: {client_jar_path}")
                            download_success = True
                            break
                        else:
                            log(f"下载客户端JAR文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            # 如果是403错误，尝试使用原始URL
                            if response.status_code == 403:
                                original_url = client_info["url"]
                                log(f"尝试使用原始URL: {original_url}")
                                with requests.Session() as session:
                                    response = session.get(original_url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        total_size = int(response.headers.get('content-length', 0))
                                        downloaded_size = 0
                                        
                                        with open(client_jar_path, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                                    downloaded_size += len(chunk)
                                                    
                                                    # 更新客户端JAR进度条（每5%更新一次）
                                                    if download_dialog and total_size > 0:
                                                        try:
                                                            # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                            progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                            if progress_bar:
                                                                progress_value = int((downloaded_size / total_size) * 100)
                                                                # 只更新到5%的倍数，避免频繁更新
                                                                if progress_value % 5 == 0 or progress_value == 100:
                                                                    QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection, progress_value)
                                                        except Exception as e:
                                                            log(f"更新client_jar_progress时出错: {e}")
                                        
                                        log(f"已下载客户端JAR文件: {client_jar_path}")
                                        download_success = True
                                        break
                except requests.exceptions.ConnectionError as e:
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议
                    try:
                        http_url = url.replace("https://", "http://")
                        log(f"尝试使用HTTP协议: {http_url}")
                        with requests.Session() as session:
                            response = session.get(http_url, stream=True, timeout=30)
                            if response.status_code == 200:
                                total_size = int(response.headers.get('content-length', 0))
                                downloaded_size = 0
                                
                                with open(client_jar_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded_size += len(chunk)
                                            
                                            # 更新客户端JAR进度条（每5%更新一次）
                                            if download_dialog and total_size > 0:
                                                try:
                                                    progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                    if progress_bar:
                                                        progress_value = int((downloaded_size / total_size) * 100)
                                                        # 只更新到5%的倍数，避免频繁更新
                                                        if progress_value % 5 == 0 or progress_value == 100:
                                                            safe_ui_update(progress_bar, "setValue", progress_value, "progress_bar")
                                                except Exception as e:
                                                    log(f"更新client_jar_progress时出错: {e}")
                                
                                log(f"已下载客户端JAR文件: {client_jar_path}")
                                download_success = True
                                break
                    except requests.exceptions.ConnectionError as e2:
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            if not download_success:
                log("所有客户端JAR文件URL都下载失败", logging.ERROR)
                return False
        else:
            log(i18nText("版本信息中未找到客户端下载链接"), logging.ERROR)
            return False

        # 加载 config.json 文件
        config = cfg.read()
        # 创建 LibraryDownloader 实例
        max_thread_value = config.get("MaxThread", 64)
        # 处理主版本库文件
        processed_libraries = []
        if "libraries" in version_data:
            for lib in version_data["libraries"]:
                if "name" in lib:
                    parts = lib['name'].split(":")
                    if len(parts) == 3:
                        group = parts[0].replace(".", "/")
                        artifact = parts[1]
                        version_lib = parts[2]
                        lib_filename = f"{artifact}-{version_lib}.jar"
                        lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                        processed_libraries.append((lib, lib_path))
                    else:
                        log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                else:
                    log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

        if download_dialog is not None and processed_libraries:
            download_dialog.downloader = LibraryDownloader(processed_libraries, max_workers=max_thread_value)

        # 创建natives目录
        natives_dir = os.path.join(version_dir, f"{VersionName}-natives")  # 使用VersionName作为natives目录名
        os.makedirs(natives_dir, exist_ok=True)

        # 下载库文件，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.6, 
            'valueStringOverride': '60%',
            'status': i18nText('正在下载库文件...')
        })
        libraries_dir = os.path.join(minecraft_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        if download_dialog is not None and download_dialog.downloader is not None:
            download_dialog.downloader.download_libraries(download_dialog)
        
        # 下载资源索引，使用PCL风格的镜像源处理
        if "assetIndex" in version_data:
            asset_index = version_data["assetIndex"]
            asset_index_url = asset_index["url"]
            
            # 使用PCL风格的镜像源处理
            asset_index_urls = dl_source_launcher_or_meta_get(asset_index_url)
            
            assets_dir = os.path.join(minecraft_dir, "assets")
            indexes_dir = os.path.join(assets_dir, "indexes")
            objects_dir = os.path.join(assets_dir, "objects")
            
            os.makedirs(indexes_dir, exist_ok=True)
            os.makedirs(objects_dir, exist_ok=True)
            
            asset_index_id = asset_index["id"]
            asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")
            
            update_progress({'status': i18nText("正在下载资源索引...")})
            log(f"正在下载资源索引: {asset_index_urls}")
            
            download_success = False
            for url in asset_index_urls:
                try:
                    log(f"正在下载资源索引: {url}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        with open(asset_index_path, 'wb') as f:
                            f.write(response.content)
                        log(f"已下载资源索引: {asset_index_path}")
                        download_success = True
                        break
                    else:
                        log(f"下载资源索引失败: {url}, HTTP {response.status_code}", logging.WARNING)
                except requests.exceptions.ConnectionError as e:
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议
                    try:
                        http_url = url.replace("https://", "http://")
                        log(f"尝试使用HTTP协议: {http_url}")
                        response = requests.get(http_url, timeout=30)
                        if response.status_code == 200:
                            with open(asset_index_path, 'wb') as f:
                                f.write(response.content)
                            log(f"已下载资源索引: {asset_index_path}")
                            download_success = True
                            break
                    except requests.exceptions.ConnectionError as e2:
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            if not download_success:
                log("所有资源索引URL都下载失败", logging.ERROR)
                return False
                
            # 读取资源索引并下载资源文件
            with open(asset_index_path, 'r', encoding='utf-8') as f:
                asset_index_data = json.load(f)
            
            if "objects" in asset_index_data:
                assets_count = len(asset_index_data['objects'])
                update_progress({'status': f"开始下载资源文件，共 {assets_count} 个..."})
                log(f"开始下载资源文件，共 {assets_count} 个")
                
                # 使用线程池进行多线程下载
                
                # 设置最大线程数，根据系统资源限制调整默认值
                try:
                    with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    max_workers = config_data.get("MaxThread", 64)
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    handle_exception(exc_type, exc_value, exc_traceback)
                    max_workers = 64  # 读取失败时使用默认值64
                log(f"使用 {max_workers} 个线程下载资源文件")
                
                # 确保线程池创建时的线程安全
                if not threading.current_thread() is threading.main_thread():
                    log("警告：资源文件下载不在主线程中运行，可能导致Qt线程问题", logging.WARNING)
                
                # 用于跟踪活动下载线程数的变量
                active_downloads = 0
                active_downloads_lock = threading.Lock()
                
                # 创建线程安全的UI更新函数
                def update_thread_count():
                    """安全地更新线程数显示"""
                    if download_dialog:
                        try:
                            thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                            if thread_label:
                                safe_ui_update(thread_label, "setText", active_downloads, "label")
                        except Exception as e:
                            log(f"更新Resources_file_working_Thread时出错: {e}")
                
                # 创建多线程下载资源文件
                def download_asset(asset_name, asset_info):
                    # 增加活动下载计数
                    nonlocal active_downloads
                    with active_downloads_lock:
                        active_downloads += 1
                        update_thread_count()  # 更新线程数显示
                    
                    try:
                        hash_value = asset_info["hash"]
                        hash_prefix = hash_value[:2]
                        object_path = os.path.join(objects_dir, hash_prefix, hash_value)
                        
                        # 如果文件已存在且大小正确，则跳过
                        if os.path.exists(object_path) and os.path.getsize(object_path) == asset_info["size"]:
                            return True
                        
                        # 创建目录
                        os.makedirs(os.path.dirname(object_path), exist_ok=True)
                        
                        # 构建URL，使用PCL风格的镜像源处理
                        asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{hash_value}"
                        asset_urls = dl_source_assets_get(asset_url)
                        
                        # 下载文件
                        download_success = False
                        for url in asset_urls:
                            try:
                                log(f"正在下载资源文件: {url}")
                                # 使用 get_session() 复用线程内的连接，显著提升大量小文件下载速度
                                session = get_session()
                                response = session.get(url, stream=True, timeout=30)
                                if response.status_code == 200:
                                    with open(object_path, 'wb') as f:
                                        # 使用固定大小的块进行流式写入，避免内存占用过高
                                        for chunk in response.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                    download_success = True
                                    break
                                else:
                                    log(f"下载资源文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            except requests.exceptions.SSLError as e:
                                log(f"SSL连接错误: {url}, {e}", logging.WARNING)
                                # 尝试使用HTTP协议
                                try:
                                    http_url = url.replace("https://", "http://")
                                    log(f"尝试使用HTTP协议: {http_url}")
                                    session = get_session()
                                    response = session.get(http_url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        with open(object_path, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                        download_success = True
                                        break
                                except requests.exceptions.RequestException as e2:
                                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                            except requests.exceptions.ConnectionError as e:
                                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                                # 尝试使用HTTP协议
                                try:
                                    http_url = url.replace("https://", "http://")
                                    log(f"尝试使用HTTP协议: {http_url}")
                                    session = get_session()
                                    response = session.get(http_url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        with open(object_path, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                        download_success = True
                                        break
                                except requests.exceptions.RequestException as e2:
                                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                            except requests.exceptions.RequestException as e:
                                log(f"下载资源文件时发生网络请求错误: {asset_name}, {url}, {e}", logging.WARNING)
                        
                        if not download_success:
                            log(f"所有资源文件URL都下载失败: {asset_name}", logging.WARNING)
                            return False
                        
                        return True
                    except Exception:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        handle_exception(exc_type, exc_value, exc_traceback)
                        return False
                    finally:
                        # 减少活动下载计数
                        with active_downloads_lock:
                            active_downloads -= 1
                            update_thread_count()  # 更新线程数显示
                
                # 初始化UI进度条为0%
                if download_dialog:
                    try:
                        
                        resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                        if resources_progress_bar:
                            QMetaObject.invokeMethod(resources_progress_bar, "setValue", Qt.QueuedConnection, 0)
                            log(f"初始化资源文件进度条为0%")
                    except Exception as e:
                        log(f"初始化资源文件进度时出错: {e}")
                
                # 创建线程池，确保线程安全
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AssetsDownloader") as executor:
                    # 提交所有下载任务
                    future_to_asset = {executor.submit(download_asset, asset_name, asset_info): asset_name 
                                      for asset_name, asset_info in asset_index_data["objects"].items()}
                    
                    # 处理完成的任务
                    success_count = 0
                    failed_count = 0
                    completed_count = 0
                    for future in concurrent.futures.as_completed(future_to_asset):
                        asset_name = future_to_asset[future]
                        try:
                            success = future.result()
                            if success:
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            log(f"处理资源文件时发生错误: {asset_name}, {str(e)}", logging.WARNING)
                            failed_count += 1
                        finally:
                            completed_count += 1
                        
                        # 更新资源文件下载进度条和线程数显示
                        if download_dialog:
                            try:
                                # 每10%更新一次UI，避免频繁更新
                                current_progress = int((completed_count / assets_count) * 100)
                                last_progress = int(((completed_count - 1) / assets_count) * 100) if completed_count > 0 else 0
                                
                                # 当进度达到10%的倍数时更新UI，只更新进度条，不发送通知
                                if current_progress // 10 > last_progress // 10 or completed_count == assets_count:
                                    # 更新进度条
                                    resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                                    if resources_progress_bar:
                                        safe_ui_update(resources_progress_bar, "setValue", current_progress, "progress_bar")
                                        log(f"资源文件下载进度: {current_progress}% ({completed_count}/{assets_count})")
                                
                                # 更新活动线程数显示
                                update_thread_count()
                            except Exception as e:
                                log(f"更新资源文件进度时出错: {e}")
                    
                    # 等待所有任务完成
                    try:
                        concurrent.futures.wait(future_to_asset, timeout=60)
                    except Exception as e:
                        log(f"等待资源文件下载完成时出错: {e}")
                
                # 下载完成，更新UI进度条为100%
                if download_dialog:
                    try:
                        
                        resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                        if resources_progress_bar:
                            safe_ui_update(resources_progress_bar, "setValue", 100, "progress_bar")
                            log(f"资源文件下载完成，设置进度条为100%")
                    except Exception as e:
                        log(f"完成资源文件进度时出错: {e}")
                
                # 更新通知为完成状态
                # update_progress({
                #     'value': 1, 
                #     'valueStringOverride': f'{assets_count}/{assets_count} 个',
                #     'status': i18nText('资源文件下载完成!')
                # })
                
                # 输出下载结果
                log(f"资源文件下载完成: 成功 {success_count} 个, 失败 {failed_count} 个")
                
                # 如果有失败的资源文件，记录警告
                if failed_count > 0:
                    log(f"有 {failed_count} 个资源文件下载失败，但不影响游戏运行", logging.WARNING)
        
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
                        fabric_response = requests.get(url, timeout=30)
                        if fabric_response.status_code == 200:
                            fabric_versions = fabric_response.json()
                            break
                        else:
                            log(f"获取Fabric Loader版本列表失败: {url}, HTTP {fabric_response.status_code}", logging.WARNING)
                    except requests.exceptions.SSLError as e:
                        log(f"SSL错误: {url}, {e}", logging.WARNING)
                        # 尝试使用HTTP协议
                        try:
                            http_url = url.replace("https://", "http://")
                            log(f"尝试使用HTTP协议: {http_url}")
                            fabric_json_response = requests.get(http_url, timeout=30)
                            if fabric_json_response.status_code == 200:
                                fabric_json_data = fabric_json_response.json()
                                break
                            else:
                                log(f"HTTP获取Fabric安装JSON失败: {http_url}, HTTP {fabric_json_response.status_code}", logging.WARNING)
                        except requests.exceptions.RequestException as e2:
                            log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                    except requests.exceptions.SSLError as e:
                        log(f"SSL错误: {url}, {e}", logging.WARNING)
                        # 尝试使用HTTP协议
                        try:
                            http_url = url.replace("https://", "http://")
                            log(f"尝试使用HTTP协议: {http_url}")
                            fabric_json_response = requests.get(http_url, timeout=30)
                            if fabric_json_response.status_code == 200:
                                fabric_json_data = fabric_json_response.json()
                                break
                            else:
                                log(f"HTTP获取Fabric安装JSON失败: {http_url}, HTTP {fabric_json_response.status_code}", logging.WARNING)
                        except requests.exceptions.RequestException as e2:
                            log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                    except requests.exceptions.RequestException as e:
                        log(f"请求错误: {url}, {e}", logging.WARNING)
                
                if not fabric_versions:
                    log(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本，但将继续安装流程", logging.WARNING)
                    # 不中断安装流程，继续执行，使用默认版本信息
                    # 创建一个基本的fabric版本结构，确保后续代码可以执行
                    fabric_versions = [{
                        "loader": {
                            "version": "0.15.0"  # 使用默认版本
                        }
                    }]
                
                # 获取最新版本
                latest_fabric = fabric_versions[0]
                loader_version = latest_fabric["loader"]["version"]
                
                log(f"找到最新的 Fabric Loader 版本: {loader_version}")
                
                # 使用PCL风格的版本命名格式，基于VersionName生成Fabric版本ID
                fabric_version_id = f"{VersionName}-Fabric {loader_version}"
                fabric_version_dir = os.path.join(versions_dir, fabric_version_id)
                os.makedirs(fabric_version_dir, exist_ok=True)
                
                # 获取Fabric安装JSON，使用PCL风格的镜像源处理
                fabric_json_urls = dl_source_launcher_or_meta_get(f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader_version}/profile/json")
                log(f"正在获取Fabric安装JSON: {fabric_json_urls}")

                fabric_json_data = None
                for url in fabric_json_urls:
                    try:
                        fabric_json_response = requests.get(url, timeout=30)
                        if fabric_json_response.status_code == 200:
                            fabric_json_data = fabric_json_response.json()
                            break
                        else:
                            log(f"获取Fabric安装JSON失败: {url}, HTTP {fabric_json_response.status_code}", logging.WARNING)
                    except requests.exceptions.RequestException as e:
                        log(f"请求错误: {url}, {e}", logging.WARNING)
                
                if not fabric_json_data:
                    log("所有Fabric安装JSON URL都获取失败，但将继续安装流程", logging.WARNING)
                    # 不中断安装流程，继续执行，Fabric版本可能无法正常运行但不影响Minecraft安装
                    # 创建一个基本的fabric_json_data结构，确保后续代码可以执行
                    fabric_json_data = {
                        "id": fabric_version_id,
                        "libraries": [],
                        "mainClass": "net.fabricmc.loader.launch.knot.KnotClient",
                        "type": "release"
                    }

                # 修改Fabric版本JSON文件，使用PCL风格的结构
                fabric_json_data["id"] = fabric_version_id
                
                # 如果Fabric JSON不包含downloads字段，需要添加原始版本的资源信息
                if "downloads" not in fabric_json_data:
                    log("Fabric JSON不包含downloads字段，添加原始版本的资源信息")
                    # 从原始版本JSON中获取资源信息
                    original_version_json_path = os.path.join(version_dir, f"{version}.json")
                    if os.path.exists(original_version_json_path):
                        with open(original_version_json_path, 'r', encoding='utf-8') as f:
                            original_version_data = json.load(f)
                        
                        # 添加原始版本的资源信息
                        if "assetIndex" in original_version_data:
                            fabric_json_data["assetIndex"] = original_version_data["assetIndex"]
                        if "assets" in original_version_data:
                            fabric_json_data["assets"] = original_version_data["assets"]
                        if "complianceLevel" in original_version_data:
                            fabric_json_data["complianceLevel"] = original_version_data["complianceLevel"]
                        if "javaVersion" in original_version_data:
                            fabric_json_data["javaVersion"] = original_version_data["javaVersion"]
                        if "logging" in original_version_data:
                            fabric_json_data["logging"] = original_version_data["logging"]
                        if "minimumLauncherVersion" in original_version_data:
                            fabric_json_data["minimumLauncherVersion"] = original_version_data["minimumLauncherVersion"]
                        if "releaseTime" in original_version_data:
                            fabric_json_data["releaseTime"] = original_version_data["releaseTime"]
                        if "time" in original_version_data:
                            fabric_json_data["time"] = original_version_data["time"]
                        if "type" in original_version_data:
                            fabric_json_data["type"] = original_version_data["type"]
                        
                        # 添加原始版本的库文件（除了Fabric相关的库）
                        original_libraries = original_version_data.get("libraries", [])
                        fabric_libraries = fabric_json_data.get("libraries", [])
                        
                        # 合并库文件，避免重复
                        existing_lib_names = {lib.get("name", "") for lib in fabric_libraries}
                        for lib in original_libraries:
                            if lib.get("name", "") not in existing_lib_names:
                                fabric_libraries.append(lib)
                        
                        fabric_json_data["libraries"] = fabric_libraries
                        log(f"已添加原始版本的资源信息到Fabric版本")
                    else:
                        log(f"原始版本JSON文件不存在: {original_version_json_path}", logging.WARNING)
                
                # PCL的Fabric版本不使用inheritsFrom，而是直接包含所有库
                if "inheritsFrom" in fabric_json_data:
                    del fabric_json_data["inheritsFrom"]
                if "jar" in fabric_json_data:
                    del fabric_json_data["jar"]

                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json_data, f, ensure_ascii=False, indent=4)
                log(f"已保存Fabric安装JSON: {fabric_json_path}")

                # 处理Fabric版本的客户端JAR文件
                client_jar_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.jar")
                
                if "downloads" in fabric_json_data and "client" in fabric_json_data["downloads"]:
                    # 如果Fabric JSON包含客户端下载信息，直接下载
                    client_info = fabric_json_data["downloads"]["client"]
                    client_url = client_info["url"]
                    
                    # 使用PCL风格的镜像源处理
                    client_urls = dl_source_launcher_or_meta_get(client_url)

                    log(f"正在下载Fabric客户端JAR文件: {client_urls}")

                    download_success = False
                    for url in client_urls:
                        try:
                            log(f"正在下载Fabric客户端JAR文件: {url}")
                            # 使用Session来更好地管理连接
                            with requests.Session() as session:
                                response = session.get(url, stream=True, timeout=30)
                                if response.status_code == 200:
                                    total_size = int(response.headers.get('content-length', 0))
                                    downloaded_size = 0
                                    
                                    with open(client_jar_path, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                                downloaded_size += len(chunk)
                                    
                                    log(f"已下载Fabric客户端JAR文件: {client_jar_path}")
                                    download_success = True
                                    break
                                else:
                                    log(f"下载Fabric客户端JAR文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                        except requests.exceptions.SSLError as e:
                            log(f"SSL错误: {url}, {e}", logging.WARNING)
                            # 尝试使用HTTP协议
                            try:
                                http_url = url.replace("https://", "http://")
                                log(f"尝试使用HTTP协议: {http_url}")
                                response = session.get(http_url, stream=True, timeout=30)
                                if response.status_code == 200:
                                    total_size = int(response.headers.get('content-length', 0))
                                    downloaded_size = 0
                                    
                                    with open(client_jar_path, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                                downloaded_size += len(chunk)
                                    
                                    log(f"已下载Fabric客户端JAR文件 (HTTP): {client_jar_path}")
                                    download_success = True
                                    break
                                else:
                                    log(f"HTTP下载Fabric客户端JAR文件失败: {http_url}, HTTP {response.status_code}", logging.WARNING)
                            except requests.exceptions.RequestException as e2:
                                log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                        except requests.exceptions.RequestException as e:
                            log(f"请求错误: {url}, {e}", logging.WARNING)
                    
                    if not download_success:
                        log("所有Fabric客户端JAR文件URL都下载失败，但将继续安装流程", logging.WARNING)
                        # 不中断安装流程，继续执行，Fabric版本可能无法正常运行但不影响Minecraft安装
                else:
                    # 如果Fabric JSON不包含客户端下载信息，从原始版本复制客户端JAR
                    log("Fabric版本信息中未找到客户端下载链接，尝试从原始版本复制客户端JAR")
                    
                    # 检查原始版本的客户端JAR是否存在
                    original_client_jar_path = os.path.join(version_dir, f"{version}.jar")
                    if os.path.exists(original_client_jar_path):
                        # 复制原始版本的客户端JAR到Fabric版本目录
                        shutil.copy2(original_client_jar_path, client_jar_path)
                        log(f"已从原始版本复制客户端JAR: {original_client_jar_path} -> {client_jar_path}")
                    else:
                        log(f"原始版本的客户端JAR不存在: {original_client_jar_path}，但将继续安装流程", logging.WARNING)
                        # 不中断安装流程，继续执行，Fabric版本可能无法正常运行但不影响Minecraft安装

                # 下载Fabric Loader所需的库文件
                update_progress({
                    'status': f'正在下载 Fabric Loader 库文件...',
                    'value': 0.92,
                    'valueStringOverride': '92%'
                })
                log(f"开始下载 Fabric Loader 库文件...")

                fabric_libraries = fabric_json_data.get("libraries", [])
                
                processed_fabric_libraries = []
                for lib in fabric_libraries:
                    if "name" in lib:
                        parts = lib['name'].split(":")
                        if len(parts) == 3:
                            group = parts[0].replace(".", "/")
                            artifact = parts[1]
                            version_lib = parts[2]
                            lib_filename = f"{artifact}-{version_lib}.jar"
                            lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                            processed_fabric_libraries.append((lib, lib_path))
                        else:
                            log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                    else:
                        log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

                if processed_fabric_libraries:
                    library_downloader = LibraryDownloader(
                        processed_fabric_libraries,
                        max_workers=max_thread_value
                    )
                    if not library_downloader.download_libraries(download_dialog=download_dialog):
                        log("Fabric Loader 库文件下载失败，但将继续安装流程", logging.WARNING)
                        # 不中断安装流程，继续执行
                    else:
                        log("Fabric Loader 库文件下载完成")
                else:
                    log("未找到 Fabric Loader 库文件", logging.WARNING)

                # 创建Fabric版本的mods目录（PCL风格：在版本目录下）
                fabric_mods_dir = os.path.join(fabric_version_dir, "mods")
                os.makedirs(fabric_mods_dir, exist_ok=True)
                
                # 下载Fabric API（可选）
                update_progress({
                    'status': f'正在下载 Fabric API...',
                    'value': 0.95,
                    'valueStringOverride': '95%'
                })
                
                try:
                    # 获取Fabric API版本列表
                    fabric_api_urls = dl_source_launcher_or_meta_get(f"https://meta.fabricmc.net/v2/versions/fabric-api/{version}")
                    fabric_api_data = None
                    for url in fabric_api_urls:
                        try:
                            fabric_api_response = requests.get(url, timeout=30)
                            if fabric_api_response.status_code == 200:
                                fabric_api_data = fabric_api_response.json()
                                break
                        except requests.exceptions.RequestException as e:
                            log(f"获取Fabric API版本列表失败: {url}, {e}", logging.WARNING)
                    
                    if fabric_api_data and len(fabric_api_data) > 0:
                        # 获取最新版本的Fabric API
                        latest_fabric_api = fabric_api_data[0]
                        fabric_api_version = latest_fabric_api["version"]
                        fabric_api_filename = f"fabric-api-{fabric_api_version}.jar"
                        fabric_api_path = os.path.join(fabric_mods_dir, fabric_api_filename)
                        
                        # 下载Fabric API
                        fabric_api_download_urls = dl_source_launcher_or_meta_get(f"https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/{fabric_api_version}/fabric-api-{fabric_api_version}.jar")
                        
                        download_success = False
                        for url in fabric_api_download_urls:
                            try:
                                log(f"正在下载 Fabric API: {url}")
                                response = requests.get(url, timeout=30)
                                if response.status_code == 200:
                                    with open(fabric_api_path, 'wb') as f:
                                        f.write(response.content)
                                    log(f"已下载 Fabric API: {fabric_api_path}")
                                    download_success = True
                                    break
                                else:
                                    log(f"下载Fabric API失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            except requests.exceptions.RequestException as e:
                                log(f"下载Fabric API失败: {url}, {e}", logging.WARNING)
                        
                        if not download_success:
                            log("Fabric API 下载失败，但不影响 Fabric Loader 安装", logging.WARNING)
                    else:
                        log("未找到适用于此版本的 Fabric API", logging.WARNING)
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
                    program_dir = os.path.dirname(os.path.dirname(__file__))  # 获取程序根目录
                    servers_dat_source = os.path.join(program_dir, "servers.dat")  # 程序目录下的 servers.dat 文件
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
                log(f"安装 Fabric Loader 失败: {e}，但将继续完成 Minecraft 安装流程", logging.WARNING)
                # 即使Fabric安装失败，原版Minecraft仍然安装成功，继续完成整个安装流程
                update_progress({
                    'status': f'Minecraft 版本 {version} 安装完成，但 Fabric Loader 安装失败!',
                    'value': 1.0
                })
                # 不返回False，继续执行后续代码，确保Minecraft版本安装成功
        
        log(f"Minecraft 版本 {version} 安装完成")
        update_progress({
            'status': f'Minecraft 版本 {version} 安装完成!',
            'value': 1.0
        })
        
        # 更新 .BL.json 文件，记录已安装的版本
        try:
            # 获取程序运行目录
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # 原版图标路径
            vanilla_icon_path = os.path.join(current_dir, "ui", "icon", "Grass_Block.png")
            # Fabric 图标路径
            fabric_icon_path = os.path.join(current_dir, "ui", "icon", "fabric.png")
            
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
            else:
                update_bl_json(minecraft_dir, version, False, vanilla_icon_path)
        except Exception as e:
            log(f"更新 .BL.json 文件时出错: {e}，但安装流程继续", logging.WARNING)
        
        # 复制 servers.dat 文件到安装目录
        try:
            # 检查是否存在 servers.dat 文件（程序目录下）
            program_dir = os.path.dirname(os.path.dirname(__file__))  # 获取程序根目录
            servers_dat_source = os.path.join(program_dir, "servers.dat")  # 程序目录下的 servers.dat 文件
            if os.path.exists(servers_dat_source):
                # 确定目标版本目录
                if fabric_version_id_final:
                    target_version_dir = os.path.join(minecraft_dir, "versions", fabric_version_id_final)
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
        
        return True
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"安装 Minecraft 版本 {version} 时发生错误: {str(e)}", logging.ERROR)
        return False
    finally:
        close_dialog_ui()