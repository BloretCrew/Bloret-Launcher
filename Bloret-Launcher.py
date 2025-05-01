from datetime import datetime
from PyQt5.QtWidgets import QSystemTrayIcon, QDialog, QApplication, QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, QFileDialog, QCheckBox, QMessageBox, QProgressBar, QCheckBox
from qfluentwidgets import SpinBox, MessageBox, SubtitleLabel, MessageBoxBase, NavigationItemPosition, TeachingTip, InfoBarIcon, TeachingTipTailPosition, ComboBox, SwitchButton, InfoBar, InfoBarPosition, FluentWindow, SplashScreen, Dialog, LineEdit,  SystemTrayMenu, Action, setThemeColor, FluentTranslator
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QDesktopServices, QColor, QPalette, QPixmap
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, QUrl, QSettings, QThread, pyqtSignal, Qt, QTimer, QSize, QLocale
from modules.win11toast import toast, notify, update_progress
import ctypes.wintypes,ctypes,socket,re,locale,sys,logging,os,requests,base64,json,subprocess,zipfile,time,shutil,traceback
import sip # type: ignore
from win32com.client import Dispatch
import threading
from concurrent.futures import ThreadPoolExecutor

# 全局变量
server_ip = "http://pcfs.top:2/"
ver_id_bloret = ['1.21.4', '1.21.3', '1.21.2', '1.21.1', '1.21']
ver_id_main = []
ver_id_short = []
ver_id = [] 
ver_url = {}
ver_id_long = []
set_list = ["你还未安装任何版本哦，请前往下载页面安装"]
BL_update_text = ""
BL_latest_ver = 0
threads = []
MINECRAFT_DIR = os.path.join(os.getcwd(), ".minecraft")
icon = {'src': 'icons/bloret.png','placement': 'appLogoOverride'}
minecraft_list = []
tabbar = None
isdarktheme = False
LM_Download_Way = {}
LM_Download_Way_list = []
LM_Download_Way_version = {}
LM_Download_Way_minecraft = {}
def handle_exception(exc_type, exc_value, exc_traceback):
    log("未捕获的异常:", logging.CRITICAL)
    log("类型: {}".format(exc_type), logging.CRITICAL)
    log("信息: {}".format(exc_value), logging.CRITICAL)
    log("回溯: {}".format(traceback.format_tb(exc_traceback)), logging.CRITICAL)
    w = Dialog("Bloret Launcher 发生了一些小问题...", "类型: {}\n信息: {}\n回溯: {}\n如果您认为这是 Bloret Launcher 的问题，请提交此问题。\n按下确认按钮将以上信息复制到剪贴板".format(exc_type, exc_value, traceback.format_tb(exc_traceback)))
    w.setWindowIcon(QIcon('icons/bloret.png'))
    w.setWindowTitle("Bloret Launcher")
    if w.exec():
        print('复制到剪贴板')
        clipboard = QApplication.clipboard()
        clipboard.setText("类型: {}\n信息: {}\n回溯: {}".format(exc_type, exc_value, ''.join(traceback.format_tb(exc_traceback))))
    else:
        print('取消')
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

log_lock = threading.Lock()

def log_thread_safe(message, level=logging.INFO):
    with log_lock:
        log(message, level)

def get_system_theme_color():
    """获取系统主题颜色"""
    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AccentColor"

        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print("无法打开注册表键")
            return "#0078D7"  # 默认蓝色

        # 读取键值
        value = ctypes.c_uint()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print("无法读取注册表键值")
            ctypes.windll.advapi32.RegCloseKey(hkey)
            return "#0078D7"  # 默认蓝色

        # 关闭注册表键
        ctypes.windll.advapi32.RegCloseKey(hkey)

        # 转换为 RGB 颜色代码
        accent_color = value.value
        red = (accent_color & 0xFF0000) >> 16
        green = (accent_color & 0x00FF00) >> 8
        blue = (accent_color & 0x0000FF)
        return f"#{red:02X}{green:02X}{blue:02X}"
    except Exception as e:
        print(f"获取系统主题颜色时发生错误: {e}")
        return "#0078D7"  # 默认蓝色

def is_dark_theme():
    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AppsUseLightTheme"
        
        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print("无法打开注册表键")
            return False
        
        # 读取键值
        value = ctypes.c_int()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print("无法读取注册表键值")
            ctypes.windll.advapi32.RegCloseKey(hkey)
            return False
        
        # 关闭注册表键
        ctypes.windll.advapi32.RegCloseKey(hkey)
        
        # 返回主题状态
        return value.value == 0  # 0 表示深色主题，1 表示浅色主题
    except Exception as e:
        print(f"检测主题时发生错误: {e}")
        return False
# 创建日志文件夹
log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# 设置日志配置
log_filename = os.path.join(log_folder, f'Bloret_Launcher_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
if not os.path.exists(log_filename):
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write('')  # 创建空日志文件
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def log(message, level=logging.INFO):
    print(message)
    logging.log(level, message)
    logging.getLogger().handlers[0].flush()  # 强制刷新日志
def send_system_notification(title, message):
    try:
        toast(title, message, duration="short", icon={'src': 'icons/bloret.png','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
    except Exception as e:
        log(f"发送系统通知失败: {e}", logging.ERROR)
def closeEvent(event):
    for thread in threads:
        if thread.isRunning():
            thread.quit()  # 请求线程退出
            thread.wait()  # 等待线程完全退出
    event.accept()
def check_write_permission():
    # 检查当前目录的写入权限
    try:
        test_file = os.path.join(os.getcwd(), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("当前目录具有写入权限")
        return True
    except PermissionError:
        print("当前目录没有写入权限")
        return False
def check_Light_Minecraft_Download_Way():
    try:
        response = requests.get(server_ip + "api/Light-Minecraft-Download-Way")
        if response.status_code == 200:
            data = response.json()
            LM_Download_Way = data.get("Light-Minecraft-Download-Way", {})  # 确保是字典

            LM_Download_Way_list.extend(LM_Download_Way.get("download-way", []))
            LM_Download_Way_version = LM_Download_Way.get("version", {})
            LM_Download_Way_minecraft = LM_Download_Way.get("minecraft", {})
            return LM_Download_Way, LM_Download_Way_list, LM_Download_Way_version, LM_Download_Way_minecraft
            # log(f"成功获取 Light-Minecraft-Download-Way: {LM_Download_Way}，LM_Download_Way_list:{LM_Download_Way_list}，LM_Download_Way_version:{LM_Download_Way_version}，LM_Download_Way_minecraft:{LM_Download_Way_minecraft}")
        else:
            log("无法获取 Light-Minecraft-Download-Way", logging.ERROR)
    except requests.RequestException as e:
        log(f"获取 Light-Minecraft-Download-Way时发生错误: {e}", logging.ERROR)

def BL_download(version, LM_download_way_choose, parent):
    class BLDownloadDialog(QDialog):
        def __init__(self, version, parent=None):
            super().__init__(parent)
            self.version = version
            self.setWindowTitle("Bloret Launcher")

            # 检查 .minecraft 文件夹是否存在
            minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
            if not os.path.exists(minecraft_dir):
                log(".minecraft 文件夹不存在")
                uic.loadUi("ui/BL_download.ui", self)
                # 初始化进度条控件
                self.progress_bars = {
                    "version": self.findChild(QProgressBar, "version"),
                    "libraries": self.findChild(QProgressBar, "libraries"),
                    "objects1": self.findChild(QProgressBar, "objects1"),
                    "objects2": self.findChild(QProgressBar, "objects2"),
                    "objects3": self.findChild(QProgressBar, "objects3"),
                    "objects4": self.findChild(QProgressBar, "objects4"),
                    "indexes": self.findChild(QProgressBar, "indexes")
                }
            else:
                parent.log(".minecraft 文件夹已存在")
                uic.loadUi("ui/BL_download_version.ui", self)
                self.progress_bars = {
                    "version": self.findChild(QProgressBar, "version")
                }

            

            # 初始化 threads 属性
            self.threads = []

        def update_progress(self, key, value, message):
            if key in self.progress_bars and self.progress_bars[key]:
                self.progress_bars[key].setValue(value)
            QApplication.processEvents()

        def closeEvent(self, event):
            for thread in self.threads:
                if thread.isRunning():
                    thread.quit()  # 请求线程退出
                    thread.wait()  # 等待线程完全退出
            event.accept()

    class VersionDownloadThread(QThread):
        progress_signal = pyqtSignal(str, int, str)
        error_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, version, minecraft_dir):
            super().__init__()
            self.version = version
            self.minecraft_dir = minecraft_dir
            # self.base_url = f"https://gitee.com/detrital/minecraft/releases/download/minecraft/"
            self.base_url = LM_Download_Way_minecraft.get(LM_download_way_choose)
            log(f"下载链接:{self.base_url}")

        def run(self):
            try:
                parent.log(f"开始下载版本 {self.version}，目标目录: {self.minecraft_dir}")

                # 检查 .minecraft 文件夹是否存在
                minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
                if not os.path.exists(minecraft_dir):
                    parent.log(".minecraft 文件夹不存在，开始下载 Minecraft 核心")
                    success = self.BL_download_minecraft()
                    if not success:
                        self.error_signal.emit("下载 Minecraft 核心失败，请检查日志。")
                        return
                else:
                    parent.log(".minecraft 文件夹已存在")

                # 确保 .minecraft/versions 文件夹存在
                versions_dir = os.path.join(minecraft_dir, "versions")
                if not os.path.exists(versions_dir):
                    os.makedirs(versions_dir)
                    parent.log(f"创建 .minecraft/versions 文件夹: {versions_dir}")
                else:
                    parent.log(".minecraft/versions 文件夹已存在")

                # 确保 .minecraft/versions/{version} 文件夹存在
                version_dir = os.path.join(versions_dir, self.version)
                if not os.path.exists(version_dir):
                    os.makedirs(version_dir)
                    parent.log(f"创建 .minecraft/versions/{self.version} 文件夹: {version_dir}")
                else:
                    parent.log(f".minecraft/versions/{self.version} 文件夹已存在")

                file_name = f"{self.version}.zip"
                file_path = os.path.join(version_dir, file_name)
                parent.log(f"准备下载文件: {file_name} 到路径: {file_path}")

                # 显示通知
                notify(progress={
                    'title': f'下载版本 {self.version}',
                    'status': '正在下载... ↓',
                    'value': '0',
                    'valueStringOverride': '0%',
                    'icon': os.path.join(os.getcwd(), 'icons', 'bloret.png')
                })
                
                log(f"LM_download_way_choose:{LM_download_way_choose}")
                version_download_url = LM_Download_Way_version.get(LM_download_way_choose)
                log(f"下载链接:{version_download_url}")

                response = requests.get(version_download_url + file_name, stream=True, timeout=10)
                response.raise_for_status()
                parent.log(f"成功获取文件: {file_name}，开始下载")

                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size / total_size * 100)
                        self.progress_signal.emit("version", progress, f"下载进度: {progress}%")
                        update_progress({'value': progress / 100, 'valueStringOverride': f'{progress}%'})

                parent.log(f"文件 {file_name} 下载完成，开始解压缩")

                # 解压缩文件
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(version_dir)
                parent.log(f"文件 {file_name} 解压缩完成")

                # 删除 .zip 文件
                os.remove(file_path)
                parent.log(f"删除文件: {file_path}")

                self.finished_signal.emit()
                parent.log(f"版本 {self.version} 下载和解压缩完成")

                # 更新通知状态
                update_progress({
                    'status': '下载完成！✅',
                    'value': 100,
                    'valueStringOverride': f'100%'
                })
            except Exception as e:
                parent.log(f"下载版本 {self.version} 时发生错误: {str(e)}", logging.ERROR)
                self.error_signal.emit(str(e))
            finally:
                # 确保资源释放
                if hasattr(self, "response"):
                    self.response.close()
                self.quit()


        def ensure_minecraft_dir(self):
            """确保 .minecraft 文件夹存在"""
            if not os.path.exists(MINECRAFT_DIR):
                os.makedirs(MINECRAFT_DIR)
                log(f"创建 .minecraft 文件夹: {MINECRAFT_DIR}")
            else:
                log(".minecraft 文件夹已存在")

        def BL_download_minecraft(self):
            """下载 Minecraft 资源文件"""
        
            # 确保 .minecraft 文件夹存在
            self.ensure_minecraft_dir()
        
            # 创建必要的子文件夹
            assets_dir = os.path.join(MINECRAFT_DIR, "assets")  # 定义 assets 文件夹路径
            objects_dir = os.path.join(assets_dir, "objects")  # 定义 objects 文件夹路径
            indexes_dir = os.path.join(assets_dir, "indexes")  # 定义 indexes 文件夹路径
            libraries_dir = os.path.join(MINECRAFT_DIR, "libraries")  # 定义 libraries 文件夹路径
        
            # 确保上述文件夹存在，如果不存在则创建
            os.makedirs(objects_dir, exist_ok=True)  # 创建 objects 文件夹
            os.makedirs(indexes_dir, exist_ok=True)  # 创建 indexes 文件夹
            os.makedirs(libraries_dir, exist_ok=True)  # 创建 libraries 文件夹
        
            # 定义需要下载的文件及其目标路径
            files_to_download = [
                ("indexes.zip", indexes_dir, "indexes"),  # indexes.zip 文件下载到 indexes 文件夹
                ("libraries.zip", libraries_dir, "libraries"),  # libraries.zip 文件下载到 libraries 文件夹
                ("objects-01.zip", objects_dir, "objects1"),  # objects-01.zip 文件下载到 objects 文件夹
                ("objects-02.zip", objects_dir, "objects2"),  # objects-02.zip 文件下载到 objects 文件夹
                ("objects-03.zip", objects_dir, "objects3"),  # objects-03.zip 文件下载到 objects 文件夹
                ("objects-04.zip", objects_dir, "objects4")  # objects-04.zip 文件下载到 objects 文件夹
            ]
        
            # 使用线程锁保护日志输出，避免多线程日志混乱
            log_lock = threading.Lock()
        
            def download_file(file_name, target_dir, progress_key):
                """下载文件并支持重试"""
                url = f"{LM_Download_Way_minecraft.get(LM_download_way_choose)}{file_name}"
                log(f"下载链接:{url}")
                file_path = os.path.join(target_dir, file_name)
                max_retries = 5
                retry_delay = 3
            
                log(f"开始处理文件: {file_name}, 目标路径: {file_path}")
            
                for attempt in range(max_retries):
                    try:
                        log(f"准备下载 {file_name} 到 {file_path} (尝试 {attempt + 1}/{max_retries})")
                        response = requests.get(url, stream=True, timeout=10)
                        response.raise_for_status()
            
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        log(f"下载链接:{url}")
            
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    progress = int(downloaded_size / total_size * 100)
                                    self.progress_signal.emit(progress_key, progress, f"下载进度: {progress}%")
                                    # log(f"文件{file_name},下载进度: {progress}%")
            
                        log(f"文件 {file_name} 下载完成")
                        return True
                    except requests.RequestException as e:
                        log(f"下载 {file_name} 失败 (尝试 {attempt + 1}/{max_retries}): {e}", logging.ERROR)
                        time.sleep(retry_delay)
                    except Exception as e:
                        log(f"下载 {file_name} 时发生未知错误: {e}", logging.ERROR)
                        time.sleep(retry_delay)
                    finally:
                        if 'response' in locals():
                            response.close()
            
                log(f"下载 {file_name} 失败，已达到最大重试次数", logging.ERROR)
                return False
            # 使用线程池并发下载文件
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 提交下载任务到线程池
                futures = [executor.submit(download_file, file_name, target_dir, progress_key) for file_name, target_dir, progress_key in files_to_download]
                for future in futures:
                    try:
                        future.result()  # 等待任务完成
                    except Exception as e:
                        log(f"下载文件时发生错误: {e}", logging.ERROR)  # 记录任务执行错误日志
        
            # 解压下载的文件
            try:
                for file_name, target_dir, _ in files_to_download:
                    file_path = os.path.join(target_dir, file_name)  # 获取文件路径
                    if os.path.exists(file_path):  # 检查文件是否存在
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:  # 打开 ZIP 文件
                            zip_ref.extractall(target_dir)  # 解压文件到目标目录
                        log(f"文件 {file_name} 解压缩完成")  # 记录解压完成日志
                        os.remove(file_path)  # 删除 ZIP 文件
                        log(f"删除文件: {file_path}")  # 记录删除文件日志
                    else:
                        log(f"文件 {file_name} 不存在，无法解压缩", logging.ERROR)  # 记录文件不存在日志
            except Exception as e:  # 捕获解压异常
                log(f"解压文件失败: {e}", logging.ERROR)  # 记录解压失败日志
                return False  # 返回 False 表示解压失败
        
            log("所有文件下载和解压完成")  # 记录所有文件下载和解压完成日志
            return True  # 返回 True 表示成功
        def download_file_with_retry(self, file_name, target_dir, progress_key):
            """下载文件并支持重试"""
            # 构造下载 URL
            url = f"{LM_Download_Way_version.get(LM_download_way_choose)}{file_name}"
            log(f"下载链接:{url}")
            # 构造文件保存路径
            file_path = os.path.join(target_dir, file_name)
            # 设置最大重试次数
            max_retries = 5
            # 设置每次重试之间的延迟时间（秒）
            retry_delay = 3
        
            # 循环尝试下载文件，最多重试 max_retries 次
            for attempt in range(max_retries):
                try:
                    # 记录日志，显示当前尝试次数
                    parent.log(f"开始下载 {file_name} (尝试 {attempt + 1}/{max_retries})")
                    # 发起 HTTP GET 请求，启用流式下载，设置超时时间为 10 秒
                    response = requests.get(url, stream=True, timeout=10)
                    # 检查 HTTP 响应状态码，如果不是 200 则抛出异常
                    response.raise_for_status()
        
                    # 获取文件总大小（字节）
                    total_size = int(response.headers.get('content-length', 0))
                    # 初始化已下载大小为 0
                    downloaded_size = 0
        
                    # 显示通知，初始化进度条
                    notify(progress={
                        'title': f'下载资源文件 {file_name}',
                        'status': '正在下载... ↓',
                        'value': '0',
                        'valueStringOverride': '0%',
                        'icon': os.path.join(os.getcwd(), 'icons', 'bloret.png')  # 确保路径有效
                    })
        
                    # 打开文件并写入下载内容
                    with open(file_path, 'wb') as f:
                        # 分块下载文件，每次读取 8192 字节
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # 确保 chunk 不为空
                                f.write(chunk)  # 写入文件
                                downloaded_size += len(chunk)  # 更新已下载大小
                                # 计算下载进度百分比
                                progress = int(downloaded_size / total_size * 100)
                                # 发送进度信号，更新 UI
                                self.progress_signal.emit(progress_key, progress, f"下载进度: {progress}%")
                                # 更新通知的进度条
                                update_progress({'value': progress / 100, 'valueStringOverride': f'{progress}%'})
        
                    # 记录日志，显示文件下载完成
                    parent.log(f"文件 {file_name} 下载完成")
        
                    # 更新通知状态为下载完成
                    update_progress({
                        'status': '下载完成！✅',
                        'value': 100,
                        'valueStringOverride': f'100%'
                    })
        
                    # 每个文件下载完成后间隔 3 秒
                    time.sleep(3)
                    return True  # 下载成功，返回 True
                except requests.RequestException as e:
                    # 捕获请求异常，记录日志并等待一段时间后重试
                    parent.log(f"下载 {file_name} 失败 (尝试 {attempt + 1}/{max_retries}): {e}", logging.ERROR)
                    time.sleep(retry_delay)
                except Exception as e:
                    # 捕获其他异常，记录日志并等待一段时间后重试
                    parent.log(f"下载 {file_name} 时发生未知错误: {e}", logging.ERROR)
                    time.sleep(retry_delay)
                finally:
                    # 确保 response 被正确关闭
                    if 'response' in locals():
                        response.close()
        
            # 如果达到最大重试次数仍未成功，记录日志并返回 False
            parent.log(f"下载 {file_name} 失败，已达到最大重试次数", logging.ERROR)
            return False
    
    # 创建对话框
    download_dialog = BLDownloadDialog(version, parent)

    # 创建下载线程
    minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
    thread = VersionDownloadThread(version, minecraft_dir)
    thread.finished.connect(lambda t=thread: threads.remove(t) if t in threads else None)
    threads.append(thread)

    # 连接信号与槽
    thread.progress_signal.connect(
        lambda key, value, message: download_dialog.update_progress(key, value, message)
    )
    thread.error_signal.connect(
        lambda e: (
            parent.log(f"下载失败: {e}", logging.ERROR),
            Dialog("下载失败", f"下载过程中发生错误: {e}").exec()
        )
    )

    def download_finished():
        parent.log(f"下载完成: 版本 {version}")
        # QTimer.singleShot(0, lambda: send_system_notification("下载完成", f"版本 {version} 已成功下载"))

        # 断开信号
        thread.progress_signal.disconnect()
        thread.error_signal.disconnect()
        thread.finished_signal.disconnect()

        # 确保线程退出
        if thread.isRunning():
            thread.quit()
            thread.wait(2000)  # 等待线程完全退出

        # 关闭对话框
        QTimer.singleShot(0, download_dialog.close)
        QTimer.singleShot(0, download_dialog.deleteLater)
        QTimer.singleShot(0, thread.deleteLater)

        # 清理线程列表
        if thread in threads:
            threads.remove(thread)

        parent.log("下载完成处理结束")

    thread.finished_signal.connect(download_finished)

    # 启动线程
    thread.start()

    # 显示对话框
    download_dialog.exec()

    return 0
class SystemTrayIcon(QSystemTrayIcon):
    """ 系统托盘图标 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if parent is None:
            print("警告：SystemTrayIcon 的 parent 参数为 None")
        self.setIcon(QIcon('icons/bloret.ico'))  # 设置托盘图标
        self.parent = parent
        self.main_window = parent

        # 创建托盘菜单
        self.menu = SystemTrayMenu(parent=parent)

        # 添加二级菜单
        launch_menu = SystemTrayMenu("🔼  启动版本", self.menu)
        print("set_list:", set_list)  # 打印 set_list 的内容以调试

        for version in set_list:
            action = Action(
                version,
                triggered=lambda checked, version=version: self.main_window.run_cmcl(version)
            )
            launch_menu.addAction(action)

        self.menu.addMenu(launch_menu)

        self.menu.addActions([
            # Action('🔄️  重启程序', triggered=os.execl(sys.executable, sys.executable, *sys.argv)),
            Action('✅  显示窗口', triggered=self.main_window.show_main_window),
            Action('❎  退出程序', triggered=QApplication.quit)
        ])
        self.setContextMenu(self.menu)

        # 连接托盘图标激活事件
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """ 托盘图标激活事件 """
        if reason == QSystemTrayIcon.Trigger:  # 单击托盘图标
            if self.parent.isMinimized() or not self.parent.isVisible():
                self.parent.showNormal()
                self.parent.activateWindow()
            else:
                self.parent.hide()
class DownloadWorker(QThread):
    finished = pyqtSignal()
    def run(self):
        # 模拟数据处理
        time.sleep(5)  # 模拟数据处理耗时
        self.finished.emit()
class RunScriptThread(QThread):
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    output_received = pyqtSignal(str)
    last_output_received = pyqtSignal(str)  # 新增信号
    
    def run(self):
        script_path = "run.ps1"
        try:
            process = subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'  # 此处统一处理解码错误
            )
            last_line = ""
            for line in iter(lambda: process.stdout.readline(), ''):  # 移除errors参数
                last_line = line.strip()
                self.output_received.emit(last_line)
            self.last_output_received.emit(last_line)
            process.stdout.close()
            process.wait()
            if process.returncode == 0:
                self.finished.emit()
            else:
                self.error_occurred.emit(process.stderr.read().strip())
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(str(e.stderr))
class UpdateShowTextThread(QThread):
    update_text = pyqtSignal(str)
    def __init__(self, run_script_thread):
        super().__init__()
        self.run_script_thread = run_script_thread
        self.last_output = ""
    def run(self):
        while self.run_script_thread.isRunning():
            time.sleep(1)  # 每秒更新一次
            self.update_text.emit(self.last_output)
    def update_last_output(self, text):
        self.last_output = text
class LoadMinecraftVersionsThread(QThread):
    versions_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    def __init__(self, version_type):
        super().__init__()
        self.version_type = version_type
    def run(self):
        try:
            response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
            response.raise_for_status()
            version_data = response.json()
            versions = version_data["versions"]
            ver_id_main.clear()
            ver_id_short.clear()
            ver_id_long.clear()
            for version in versions:
                if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                    ver_id_main.append(version["id"])
                else:
                    if version["type"] == "snapshot":
                        ver_id_short.append(version["id"])
                    elif version["type"] in ["old_alpha", "old_beta"]:
                        ver_id_long.append(version["id"])
            if self.version_type == "百络谷支持版本":
                self.versions_loaded.emit(ver_id_bloret)
            elif self.version_type == "正式版本":
                self.versions_loaded.emit(ver_id_main)
            elif self.version_type == "快照版本":
                self.versions_loaded.emit(ver_id_short)
            elif self.version_type == "远古版本":
                self.versions_loaded.emit(ver_id_long)
            else:
                self.error_occurred.emit("未知的版本类型")
        except requests.RequestException as e:
            self.error_occurred.emit(f"请求错误: {e}")
        except requests.exceptions.SSLError as e:
            self.error_occurred.emit(f"SSL 错误: {e}")
class MainWindow(FluentWindow):
    def __init__(self):
        # 初始化配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        Bloret_PassPort_User_UserName = self.config.get('Bloret_PassPort_UserName', '未登录')

        # 获取系统主题颜色
        theme_color = get_system_theme_color()
        log(f"系统主题颜色: {theme_color}")
        setThemeColor(theme_color)

        if(isdarktheme):
            from qfluentwidgets import setTheme, Theme
            setTheme(Theme.AUTO)

        if self.config.get('show_runtime_do', False):
            log("显示软件打开过程已启用")
            # 显示通知
            notify(progress={
                'title': '正在启动 Bloret Launcher',
                'status': '正在做打开软件前的工作...',
                'value': '0',
                'valueStringOverride': '0%',
                'icon': os.path.join(os.getcwd(), 'icons', 'bloret.png')
            })
        else:
            log("显示软件打开过程已禁用")


        super().__init__()

        # 设置全局编码
        codec = locale.getpreferredencoding()
        if sys.stdout:
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8')

        # 1. 创建启动页面
        update_progress({'value': 10 / 100, 'valueStringOverride': '1/10', 'status': '创建启动页面'})
        icon_path = os.path.join(os.getcwd(), 'icons', 'bloret.png')
        if os.path.exists(icon_path):
            self.log(f"图标路径存在: {icon_path}")
        else:
            self.log(f"图标路径不存在: {icon_path}", logging.ERROR)
        self.splashScreen = SplashScreen(QIcon(icon_path), self)
        self.log("启动画面创建完成")
        self.splashScreen.setIconSize(QSize(102, 102))
        self.splashScreen.setWindowTitle("Bloret Launcher")
        self.splashScreen.setWindowIcon(QIcon(icon_path))
        
        # 2. 在创建其他子页面前先显示主界面
        update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': '连接服务器'})
        self.splashScreen.show()
        self.log("启动画面已显示")

        if not isdarktheme:
            # 监听系统主题变化
            QApplication.instance().paletteChanged.connect(self.apply_theme)
        
        # 初始化 sidebar_animation
        update_progress({'value': 30 / 100, 'valueStringOverride': '3/10', 'status': '初始化侧边栏动画'})
        self.sidebar_animation = QPropertyAnimation(self.navigationInterface, b"geometry")
        self.sidebar_animation.setDuration(300)  # 设置动画持续时间
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 初始化 fade_in_animation
        update_progress({'value': 40 / 100, 'valueStringOverride': '4/10', 'status': '初始化淡入动画'})
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.loading_dialogs = []  # 初始化 loading_dialogs 属性
        self.threads = []  # 初始化 threads 属性
        self.handle_first_run()
        self.check_for_updates()
        self.check_Bloret_version()
        
        # 设置窗口标题和图标
        update_progress({'value': 50 / 100, 'valueStringOverride': '5/10', 'status': '设置窗口标题和图标'})
        self.setWindowTitle("Bloret Launcher")
        icon_path = os.path.join(os.getcwd(), 'icons', 'bloret.png')
        if os.path.exists(icon_path):
            self.log(f"图标路径存在: {icon_path}")
        else:
            self.log(f"图标路径不存在: {icon_path}", logging.ERROR)
        self.setWindowIcon(QIcon(icon_path))

        # 初始化其他属性
        update_progress({'value': 60 / 100, 'valueStringOverride': '6/10', 'status': '初始化其他属性'})
        self.is_running = False
        self.player_uuid = ""
        self.player_skin = ""
        self.player_cape = ""
        self.player_name = ""
        self.Customize_icon = None
        self.settings = QSettings("Bloret", "Launcher")
        if not isdarktheme:
            self.apply_theme()
        self.cmcl_data = None
        self.load_cmcl_data()
        self.initNavigation()
        self.initWindow()
        self.apply_scale()
        self.setAttribute(Qt.WA_QuitOnClose, True)  # 确保窗口关闭时程序退出
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)  # 确保窗口显示在最前面
        self.raise_()
        self.activateWindow()

        # 初始化托盘图标
        self.tray_icon = SystemTrayIcon(parent=self)
        self.tray_icon.show()

        # 处理首次运行
        update_progress({'value': 70 / 100, 'valueStringOverride': '7/10', 'status': '处理首次运行'})
        QTimer.singleShot(0, lambda: self.handle_first_run())
        
        # 隐藏启动页面
        update_progress({'value': 80 / 100, 'valueStringOverride': '8/10', 'status': '隐藏启动页面'})
        QTimer.singleShot(3000, lambda: (self.log("隐藏启动画面"), self.splashScreen.finish()))

        # 初始化需要 cmcl_data 的组件
        update_progress({'value': 90 / 100, 'valueStringOverride': '9/10', 'status': '初始化需要 cmcl_data 的组件'})
        self.initNavigation()

        # 显示窗口
        update_progress({'value': 100 / 100, 'valueStringOverride': '10/10', 'status': '显示窗口'})
        self.show()

        self.destroyed.connect(lambda: (
            json.dump(self.config, open('config.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
            if hasattr(self, 'config') else None
        ))

    def load_cmcl_data(self):
        self.log(f"开始向 cmcl.json 读取数据")
        try:
            with open('cmcl.json', 'r', encoding='utf-8') as file:
                self.cmcl_data = json.load(file)
            
            # 添加对空accounts列表的检查
            if not self.cmcl_data.get('accounts'):
                self.player_name = "未登录"
                self.login_mod = "请在下方登录"
                self.log("cmcl.json 中的 accounts 列表为空")
                return
                
            # 添加索引越界保护
            account = self.cmcl_data['accounts'][0] if self.cmcl_data['accounts'] else {}
            
            self.player_name = account.get('playerName', '未登录')
            self.login_mod_num = account.get('loginMethod', -1)  # 默认-1表示未知
            
            # 更新登录方式描述
            self.login_mod = {
                0: "离线登录",
                2: "微软登录"
            }.get(self.login_mod_num, "未知登录方式")

            self.log(f"读取到的 playerName: {self.player_name}")
            self.log(f"读取到的 loginMethod: {self.login_mod}")
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.log(f"读取 cmcl.json 失败: {e}", logging.ERROR)
            self.cmcl_data = None
            # 设置默认值
            self.player_name = "未登录"
            self.login_mod = "请在下方登录"
        except Exception as e:
            self.log(f"其他错误: {e}", logging.ERROR)
            self.cmcl_data = None
            self.player_name = "未登录"
            self.login_mod = "请在下方登录"

    def initNavigation(self):
        self.homeInterface = QWidget()
        self.downloadInterface = QWidget()
        self.toolsInterface = QWidget()
        self.passportInterface = QWidget()
        self.settingsInterface = QWidget()
        self.infoInterface = QWidget()
        self.homeInterface.setObjectName("home")
        self.downloadInterface.setObjectName("download")
        self.toolsInterface.setObjectName("tools")
        self.passportInterface.setObjectName("passport")
        self.settingsInterface.setObjectName("settings")
        self.infoInterface.setObjectName("info")
        if isdarktheme:
            self.addSubInterface(self.homeInterface, QIcon("icons/dark/bloret.png"), "主页")
            self.addSubInterface(self.downloadInterface, QIcon("icons/dark/download.png"), "下载")
            self.addSubInterface(self.toolsInterface, QIcon("icons/dark/tools.png"), "工具")
            self.addSubInterface(self.passportInterface, QIcon("icons/dark/passport.png"), "通行证", NavigationItemPosition.BOTTOM)
            self.addSubInterface(self.settingsInterface, QIcon("icons/dark/settings.png"), "设置", NavigationItemPosition.BOTTOM)
            self.addSubInterface(self.infoInterface, QIcon("icons/dark/info.png"), "关于", NavigationItemPosition.BOTTOM)
        else:  
            self.addSubInterface(self.homeInterface, QIcon("icons/bloret.png"), "主页")
            self.addSubInterface(self.downloadInterface, QIcon("icons/download.png"), "下载")
            self.addSubInterface(self.toolsInterface, QIcon("icons/tools.png"), "工具")
            self.addSubInterface(self.passportInterface, QIcon("icons/passport.png"), "通行证", NavigationItemPosition.BOTTOM)
            self.addSubInterface(self.settingsInterface, QIcon("icons/settings.png"), "设置", NavigationItemPosition.BOTTOM)
            self.addSubInterface(self.infoInterface, QIcon("icons/info.png"), "关于", NavigationItemPosition.BOTTOM)
        self.load_ui("ui/home.ui", parent=self.homeInterface)
        self.load_ui("ui/download.ui", parent=self.downloadInterface)
        self.load_ui("ui/tools.ui", parent=self.toolsInterface)
        self.load_ui("ui/passport.ui", parent=self.passportInterface)
        self.load_ui("ui/settings.ui", parent=self.settingsInterface)
        self.load_ui("ui/info.ui", parent=self.infoInterface)
        self.setup_home_ui(self.homeInterface)
        self.setup_download_ui(self.downloadInterface)
        self.setup_tools_ui(self.toolsInterface)
        self.setup_passport_ui(self.passportInterface)
        self.setup_settings_ui(self.settingsInterface)
        self.setup_info_ui(self.infoInterface)
    def animate_sidebar(self):
        start_geometry = self.navigationInterface.geometry()
        end_geometry = QRect(start_geometry.x(), start_geometry.y(), start_geometry.width(), start_geometry.height())
        self.sidebar_animation.setStartValue(start_geometry)
        self.sidebar_animation.setEndValue(end_geometry)
        self.sidebar_animation.start()
    def initWindow(self):
        # self.resize(900, 700)
        self.setWindowIcon(QIcon("icons/bloret.png"))
        self.setWindowTitle("Bloret Launcher")
        self.scale_factor = self.config.get('size', 90) / 100.0
        # self.resize(int(800 * self.scale_factor), int(600 * self.scale_factor))
        # 优化窗口缩放逻辑（替换原有resize调用）
    def apply_scale(self):
        base_width, base_height = 800, 600  # 基准尺寸
        self.scale_factor = self.config.get('size', 90) / 100.0
        scaled_width = int(base_width * self.scale_factor)
        scaled_height = int(base_height * self.scale_factor)

        self.resize(scaled_width, scaled_height)

        # 强制控件重新布局
        self.layout().activate()

        # 调用侧边栏缩放函数
        # self.apply_sidebar_scaling()

    def apply_sidebar_scaling(self):
        base_sidebar_width = 300  # 设置一个基准宽度
        size = self.scale_factor   # 使用已有的 scale_factor 属性

        scaled_sidebar_width = int(base_sidebar_width * size)
        self.navigationInterface.setExpandWidth(scaled_sidebar_width)
        if hasattr(self.navigationInterface, 'setCollapseWidth'):
            self.navigationInterface.setCollapseWidth(int(scaled_sidebar_width * size))
        else:
            self.log("NavigationInterface does not support setCollapseWidth", logging.ERROR)
        if hasattr(self.navigationInterface, 'collapse'):
            self.navigationInterface.collapse(useAni=False)  # 默认收缩
        else:
            self.log("NavigationInterface does not support collapse", logging.ERROR)

        # 可选：设置最小展开宽度并强制展开
        base_window_width = 900
        scaled_min_expand_width = int(base_window_width * size)
        self.resize(int(base_window_width * size), int(700 * size))  # 调整窗口大小
        self.navigationInterface.setMinimumExpandWidth(scaled_min_expand_width)
        self.navigationInterface.expand(useAni=False)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        icon_size = int(64 * self.scale_factor)
        
        # 仅在存在 Customize_icon 时更新
        if hasattr(self, 'Customize_icon') and self.Customize_icon:
            self.Customize_icon.setPixmap(self.icon.pixmap(icon_size, icon_size))
    def load_ui(self, ui_path, parent=None, animate=True):
        widget = uic.loadUi(ui_path)
    
        if parent:
            # 强制使用布局管理（若原布局缺失）
            if not parent.layout():
                layout = QVBoxLayout(parent)  # 使用垂直布局
                layout.setContentsMargins(0,0,0,0)  # 移除默认边距
                layout.addWidget(widget)
            else:
                parent.layout().addWidget(widget)
    def on_home_clicked(self):
        self.log("主页 被点击")
        self.switchTo(self.homeInterface)
    def on_download_finished(self, teaching_tip, download_button):
        if hasattr(self, 'version'):
            self.log(f"版本 {self.version} 已成功下载")
        else:
            self.log("下载完成，但版本信息缺失")

        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        if download_button:
            InfoBar.success(
                title='✅ 下载完成',
                content=f"版本 {self.version if hasattr(self, 'version') else '未知'} 已成功下载\n前往主页就可以启动了！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        self.run_cmcl_list()
        # 拷贝 servers.dat 文件到 .minecraft 文件夹
        src_file = os.path.join(os.getcwd(), "servers.dat")
        dest_dir = os.path.join(os.getcwd(), ".minecraft")
        if os.path.exists(src_file):
            try:
                shutil.copy(src_file, dest_dir)
                self.log(f"成功拷贝 {src_file} 到 {dest_dir}")
            except Exception as e:
                self.log(f"拷贝 {src_file} 到 {dest_dir} 失败: {e}", logging.ERROR)
        self.is_running = False  # 重置标志变量
        # 发送系统通知
        QTimer.singleShot(0, lambda: self.send_system_notification("下载完成", f"版本 {self.version} 已成功下载"))
        # 检查 NoneType 错误
        if self.show_text is not None:
            self.show_text.setText("下载完成")
        else:
            self.log("show_text is None", logging.ERROR)
        self.run_cmcl_list()
    def on_download_clicked(self):
        self.log("下载 被点击")
        self.switchTo(self.downloadInterface)
    def on_tools_clicked(self):
        self.log("工具 被点击")
        self.switchTo(self.toolsInterface)
    def on_passport_clicked(self):
        self.log("通行证 被点击")
        self.switchTo(self.passportInterface)  # 切换到通行证页面
        self.setup_passport_ui(self.passportInterface)  # 调用 setup_passport_ui 方法
        self.log("通行证页面UI加载完成")
    def on_settings_clicked(self):
        self.log("设置 被点击")
        self.switchTo(self.settingsInterface)
    def on_info_clicked(self):
        self.log("关于 被点击")
        self.switchTo(self.infoInterface)
    def run_cmcl_list(self):
        global set_list,minecraft_list  # 添加全局声明
        try:
            versions_path = os.path.join(os.getcwd(), ".minecraft", "versions")
            temp_list = []  # 使用临时变量
            
            if os.path.exists(versions_path) and os.path.isdir(versions_path):
                temp_list = [d for d in os.listdir(versions_path)
                            if os.path.isdir(os.path.join(versions_path, d))]
                
                if not temp_list:
                    temp_list = ["你还未安装任何版本哦，请前往下载页面安装"]
                    self.log(f"版本目录为空: {versions_path}")
                else:
                    self.log(f"成功读取版本列表: {temp_list}")
            else:
                temp_list = ["无法获取版本列表，可能是你还未安装任何版本，请前往下载页面安装"]
                self.log(f"路径无效: {versions_path}", logging.ERROR)
                
            set_list = temp_list  # 最后统一赋值给全局变量

            minecraft_list = temp_list # 保留原 Minecraft 版本列表备用
            self.log(f"Minecraft 版本列表: {minecraft_list}")

            customize_list = []
            if "Customize" in self.config:
                customize_list = [item.get("showname") for item in self.config["Customize"]]
            self.log(f"Customize 列表中的 showname 值: {customize_list}")
            set_list = temp_list + customize_list  # 合并 customize_list 到 set_list

            self.log(f"合并后的版本列表: {set_list}")

            self.update_version_combobox()  # 新增UI更新方法
            
        except Exception as e:
            self.log(f"读取版本列表失败: {e}", logging.ERROR)
            set_list = ["无法获取版本列表，可能是你还未安装任何版本，请前往下载页面安装"]
    def run_cmcl(self, version):
        # self.tabBar.addTab(
        #     routeKey={version},
        #     text={version},
        #     onClick=lambda: print("Click")
        # )
        
        log(f"minecraft_list:{minecraft_list}")
        if version not in minecraft_list:
            # 自定义启动
            # InfoBar.success(
            #     title='🔄️ 正在启动 {version}',
            #     content=f"...",
            #     isClosable=True,
            #     position=InfoBarPosition.TOP,
            #     duration=5000,
            #     parent=self
            # )
            # 查找 config.json 中 Customize 的 showname 是否匹配 version
            for item in self.config.get("Customize", []):
                if item.get("showname") == version:
                    program_path = item.get("path")
                    if program_path and os.path.exists(program_path):
                        InfoBar.success(
                            title=f'🔄️ 正在启动 {version}',
                            content=f"...",
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=5000,
                            parent=self
                        )
                        subprocess.Popen(program_path, shell=True)
                        return
                    else:
                        InfoBar.error(
                            title='❌ 启动失败',
                            content=f"路径 {program_path} 不存在或无效",
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=5000,
                            parent=self
                        )
                        return
            InfoBar.error(
                title='❌ 启动失败',
                content=f"未找到与 {version} 匹配的自定义程序",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            InfoBar.success(
                title=f'🔄️ 正在启动 {version}',
                content=f"正在处理 Minecraft 文件和启动...\n您马上就能见到 Minecraft 窗口出现了！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

            if self.is_running:
                return
            self.is_running = True
            self.log(f"正在启动 {version}")
            if os.path.exists("run.ps1"):
                os.remove("run.ps1")
            subprocess.run(["cmcl", "version", version, "--export-script-ps=run.ps1"])

            # 替换 CMCL 2.2.2 → Bloret Launcher
            with open("run.ps1", "r+", encoding='utf-8') as f:
                content = f.read().replace('CMCL 2.2.2', 'Bloret Launcher')
                f.seek(0)
                f.write(content)
                f.truncate()

            # 替换 CMCL → Bloret-Launcher
            with open("run.ps1", "r+", encoding='utf-8') as f:
                content = f.read().replace('CMCL', 'Bloret-Launcher')
                f.seek(0)
                f.write(content)
                f.truncate()

            run_button = self.sender()  # 获取按钮对象（可能为 None）
            if run_button is not None:
                teaching_tip = TeachingTip.create(
                    target=run_button,
                    icon=InfoBarIcon.SUCCESS,
                    title=f'正在启动 {version}',
                    content="请稍等",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=0,  # 设置为0表示不自动关闭
                    parent=self
                )
                if teaching_tip:
                    teaching_tip.move(run_button.mapToGlobal(run_button.rect().topLeft()))
            else:
                self.log("托盘菜单启动，不显示 TeachingTip")

            # 线程
            self.run_script_thread = RunScriptThread()
            self.run_script_thread.finished.connect(lambda: self.on_run_script_finished(None, run_button))
            self.run_script_thread.error_occurred.connect(lambda error: self.on_run_script_error(error, None, run_button))
            self.run_script_thread.start()
            self.threads.append(self.run_script_thread)

            self.update_show_text_thread = UpdateShowTextThread(self.run_script_thread)
            self.update_show_text_thread.update_text.connect(self.update_show_text)
            self.run_script_thread.last_output_received.connect(self.update_show_text_thread.update_last_output)
            self.update_show_text_thread.start()
            self.threads.append(self.update_show_text_thread)

    def update_version_combobox(self):
        home_interface = self.homeInterface
        if home_interface:
            run_choose = home_interface.findChild(ComboBox, "run_choose")
            if run_choose:
                # 添加版本去重逻辑
                unique_versions = list(dict.fromkeys(set_list))  # 保持顺序去重
                current_text = run_choose.currentText()  # 保留当前选中项
                
                run_choose.clear()
                run_choose.addItems(unique_versions)
                
                # 恢复选中项或默认选择
                if current_text in unique_versions:
                    run_choose.setCurrentText(current_text)
                elif unique_versions:
                    run_choose.setCurrentIndex(0)
    def log(self, message, level=logging.INFO):
        print(message)
        logging.log(level, message)
    def closeEvent(self, event):
        """ 重写关闭事件，隐藏窗口而不是退出程序 """
        event.ignore()  # 忽略关闭事件
        self.hide()  # 隐藏窗口
        # self.tray_icon.showMessage(
        #     "Bloret Launcher",
        #     "程序已最小化到系统托盘",
        #     QSystemTrayIcon.Information,
        #     2000  # 提示持续时间（毫秒）
        # )
    def on_download_clicked(self):
        self.log("下载 被点击")
        self.load_ui("ui/download.ui", animate=False)
        self.setup_download_ui(self.content_layout.itemAt(0).widget())
    def on_download_way_changed(self, widget, selected_way):
        show_way = widget.findChild(ComboBox, "show_way")
        fabric_choose = widget.findChild(ComboBox, "Fabric_choose")
        LM_download_way_choose = widget.findChild(ComboBox, "LM_download_way_choose")
        if selected_way == "Bloret Launcher":
            if show_way:
                show_way.setEnabled(False)
            if fabric_choose:
                fabric_choose.setEnabled(False)
            if LM_download_way_choose:
                LM_download_way_choose.setEnabled(True)
        else:
            if show_way:
                show_way.setEnabled(True)
            if fabric_choose:
                fabric_choose.setEnabled(True)
            if LM_download_way_choose:
                LM_download_way_choose.setEnabled(False)
    def setup_download_ui(self, widget):
        download_way_choose = widget.findChild(ComboBox, "download_way_choose")  # 获取 download_way_choose 元素
        LM_download_way_choose = widget.findChild(ComboBox, "LM_download_way_choose")
        download_way_F5_button = widget.findChild(QPushButton, "download_way_F5")
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        show_way = widget.findChild(ComboBox, "show_way")
        download_button = widget.findChild(QPushButton, "download")
        if show_way:
            show_way.clear()
            show_way.addItems(["百络谷支持版本", "正式版本", "快照版本", "远古版本"])
            show_way.setCurrentText("百络谷支持版本")
            show_way.currentTextChanged.connect(lambda: self.on_show_way_changed(widget, show_way.currentText()))
        if download_way_choose:
            download_way_choose.clear()  # 清空下拉框
            download_way_choose.addItem("Bloret Launcher")
            download_way_choose.addItem("CMCL")
            download_way_choose.currentTextChanged.connect(lambda text: self.on_download_way_changed(widget, text))
        if LM_download_way_choose:
            LM_download_way_choose.clear()  # 清空下拉框
            for item in LM_Download_Way_list:
                LM_download_way_choose.addItem(item)
        if download_way_F5_button:
            download_way_F5_button.clicked.connect(lambda: self.update_minecraft_versions(widget, show_way.currentText()))
        if download_button:
            # log(f"成功获取 Light-Minecraft-Download-Way: {LM_Download_Way}，LM_Download_Way_list:{LM_Download_Way_list}，LM_Download_Way_version:{LM_Download_Way_version}，LM_Download_Way_minecraft:{LM_Download_Way_minecraft}")
            download_button.clicked.connect(lambda: self.start_download(widget))
        loading_label = widget.findChild(QLabel, "label_2")
        if loading_label:
            self.setup_loading_gif(loading_label)
        # 默认填入百络谷支持版本
        if minecraft_choose:
            minecraft_choose.clear()
            minecraft_choose.addItems(ver_id_bloret)
        notification_switch = widget.findChild(SwitchButton, "Notification")
        if notification_switch:
            notification_switch.setChecked(True)  # 将Notification开关设置成开

        fabric_ver = ["不安装"]
        response = requests.get("https://bmclapi2.bangbang93.com/fabric-meta/v2/versions/loader")
        if response.status_code == 200:
            data = response.json()
            for item in data:
                fabric_ver.append(item["version"])

        fabric_choose = widget.findChild(ComboBox, "Fabric_choose")
        if fabric_choose:
            fabric_choose.clear()
            fabric_choose.addItems(fabric_ver)
            fabric_choose.setCurrentText("不安装")

        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        vername_edit = widget.findChild(LineEdit, "vername_edit")
        if minecraft_choose and vername_edit:
            minecraft_choose.currentTextChanged.connect(vername_edit.setText)

        # 默认填入百络谷支持版本的第一项
        if minecraft_choose:
            minecraft_choose.clear()
            minecraft_choose.addItems(ver_id_bloret)
            vername_edit = widget.findChild(LineEdit, "vername_edit")
            if vername_edit and ver_id_bloret:
                vername_edit.setText(ver_id_bloret[0])

        Customize_choose = widget.findChild(QPushButton, "Customize_choose")
        if Customize_choose:
            Customize_choose.clicked.connect(lambda: self.on_customize_choose_clicked(widget))

        Customize_add = widget.findChild(QPushButton, "Customize_add")
        if Customize_add:
            Customize_add.clicked.connect(lambda: self.on_customize_add_clicked(widget))

    def on_customize_choose_clicked(self, widget):
        Customize_path = widget.findChild(LineEdit, "Customize_path")
        Customize_showname = widget.findChild(LineEdit, "Customize_showname")
        # Customize_icon = widget.findChild(QLabel, "Customize_icon")
        Customize_choose_path, _ = QFileDialog.getOpenFileName(self, "选择文件", os.getcwd(), "所有文件 (*.*)")
        if Customize_choose_path:
            Customize_path.setText(Customize_choose_path)
            Customize_showname.setText(os.path.splitext(os.path.basename(Customize_choose_path))[0])
            # icon = QIcon(Customize_choose_path)
            # if not icon.isNull():
            #     Customize_icon.setPixmap(icon.pixmap(64, 64))  # 设置图标大小为 64x64
            # else:
            #     Customize_icon.setText("无法加载图标")
            # self.showTeachingTip(Customize_showname, Customize_choose_path)
    def on_customize_add_clicked(self, widget):
        Customize_path = widget.findChild(LineEdit, "Customize_path")
        Customize_showname = widget.findChild(LineEdit, "Customize_showname")
        Customize_path_value = Customize_path.text()
        Customize_showname_value = Customize_showname.text()
        self.log(f"Customize Path: {Customize_path_value}, Customize Show Name: {Customize_showname_value}")
        if not Customize_path_value or not Customize_showname_value:
            InfoBar.warning(
                title='⚠️ 提示',
                content="路径或显示名称不能为空",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return

        if not os.path.exists(Customize_path_value):
            InfoBar.error(
                title='❌ 错误',
                content="指定的路径不存在，请重新选择",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return

        if not os.path.isfile(Customize_path_value):
            InfoBar.error(
                title='❌ 错误',
                content="指定的路径不是文件，请重新选择",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return

        # InfoBar.success(
        #     title='✅ 成功',
        #     content=f"路径 {Customize_path_value} 和显示名称 {Customize_showname_value} 已成功校验",
        #     isClosable=True,
        #     position=InfoBarPosition.TOP,
        #     duration=5000,
        #     parent=self
        # )

        # Save to config.json
        try:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []

            config_data["Customize"].append({
                "showname": Customize_showname_value,
                "path": Customize_path_value
            })

            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
            self.config = config_data  # 同步到 self.config
            InfoBar.success(
                title='✅ 成功',
                content=f"路径 {Customize_path_value} 和显示名称 {Customize_showname_value} 已成功保存",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            self.run_cmcl_list()
            
        except Exception as e:
            InfoBar.error(
                title='❌ 错误',
                content=f"保存到 config.json 时发生错误: {e}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        
    def on_show_way_changed(self, widget, version_type):
        show_way = widget.findChild(ComboBox, "show_way")
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")

        if show_way and minecraft_choose:
            show_way.setEnabled(False)
            minecraft_choose.setEnabled(False)
            InfoBar.success(
                title='⏱️ 正在加载',
                content=f"正在加载 {version_type} 的列表",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        def fetch_versions():
            self.load_versions_thread = LoadMinecraftVersionsThread(version_type)
            self.threads.append(self.load_versions_thread)  # 将线程添加到列表中
            self.load_versions_thread.versions_loaded.connect(lambda versions: self.update_minecraft_choose(widget, versions))
            self.load_versions_thread.error_occurred.connect(lambda error: self.show_error_tip(widget, error))
            self.load_versions_thread.start()
        QTimer.singleShot(5000, fetch_versions)
    def update_minecraft_choose(self, widget, versions):
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        show_way = widget.findChild(ComboBox, "show_way")
        if minecraft_choose:
            minecraft_choose.clear()
            minecraft_choose.addItems(versions)
            minecraft_choose.setEnabled(True)
        if show_way:
            show_way.setEnabled(True)
        for dialog in self.loading_dialogs:
            dialog.close()
        self.loading_dialogs.clear()
    def show_error_tip(self, widget, error):
        show_way = widget.findChild(ComboBox, "show_way")
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        if show_way:
            show_way.setEnabled(True)
        if minecraft_choose:
            minecraft_choose.setEnabled(True)
        InfoBar.error(
            title='错误',
            content=f"加载列表时出错: {error}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        for dialog in self.loading_dialogs:
            dialog.close()
        self.loading_dialogs.clear()
    def showTeachingTip(self, target_widget, folder_path):
        if sip.isdeleted(target_widget):
            self.log(f"目标小部件已被删除，无法显示 TeachingTip", logging.ERROR)
            return
        InfoBar.success(
            title='✅ 提示',
            content=f"已存储 Minecraft 核心文件夹位置为\n{folder_path}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    def update_minecraft_versions(self, widget, version_type):
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        if minecraft_choose:
            try:
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                if response.status_code == 200:
                    version_data = response.json()
                    latest_release = version_data["latest"]["release"]
                    latest_snapshot = version_data["latest"]["snapshot"]
                    versions = version_data["versions"]
                    ver_id_main.clear()
                    ver_id_short.clear()
                    ver_id_long.clear()
                    for version in versions:
                        if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                            ver_id_main.append(version["id"])
                        else:
                            if version["type"] == "snapshot":
                                ver_id_short.append(version["id"])
                            elif version["type"] in ["old_alpha", "old_beta"]:
                                ver_id_long.append(version["id"])
                    minecraft_choose.clear()
                    if version_type == "百络谷支持版本":
                        minecraft_choose.addItems(ver_id_bloret)
                    elif version_type == "正式版本":
                        minecraft_choose.addItems(ver_id_main)
                    elif version_type == "快照版本":
                        minecraft_choose.addItems(ver_id_short)
                    elif version_type == "远古版本":
                        minecraft_choose.addItems(ver_id_long)
                    else:
                        self.log("未知的版本类型", logging.ERROR)
                    self.log(f"最新发布版本: {latest_release}")
                    self.log(f"最新快照版本: {latest_snapshot}")
                    self.log("Minecraft 版本列表已更新")
                else:
                    self.log("无法获取 Minecraft 版本列表", logging.ERROR)
            except requests.exceptions.RequestException as e:
                self.log(f"请求错误: {e}", logging.ERROR)
                InfoBar.error(
                    title='提示',
                    content="无法连接到服务器，请检查网络连接或稍后再试。",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            except requests.exceptions.SSLError as e:
                self.log(f"SSL 错误: {e}", logging.ERROR)
                InfoBar.error(
                    title='提示',
                    content="无法连接到服务器，请检查网络连接或稍后再试。",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            finally:
                for dialog in self.loading_dialogs:  # 关闭所有 loading_dialog
                    dialog.close()
                self.loading_dialogs.clear()  # 清空列表
    def start_download(self, widget):
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        download_button = widget.findChild(QPushButton, "download")
        fabric_choose = widget.findChild(ComboBox, "Fabric_choose")
        
        vername_edit = widget.findChild(LineEdit, "vername_edit")
        if vername_edit:
            vername = vername_edit.text().strip()
            pattern = r'^(?!^(PRN|AUX|NUL|CON|COM[1-9]|LPT[1-9])$)[^\\/:*?"<>|\x00-\x1F\u4e00-\u9fff]+$'
            if not re.match(pattern, vername):
                msg = MessageBox(
                    title="非法名称",
                    content="名称包含非法字符或中文，请遵循以下规则：\n1. 不能包含 \\ / : * ? \" < > |\n2. 不能包含中文\n3. 不能使用系统保留名称",
                    parent=self
                )
                msg.exec()
                return
    
        if minecraft_choose and download_button and fabric_choose:
            cmcl_save_path = os.path.join(os.getcwd(), "cmcl_save.json")
            cmcl_path = os.path.join(os.getcwd(), "cmcl.exe")
    
            if not os.path.isfile(cmcl_path):
                self.log(f"文件 {cmcl_path} 不存在", logging.ERROR)
                QMessageBox.critical(self, "错误", f"文件 {cmcl_path} 不存在")
                return
            
            choose_ver = minecraft_choose.currentText()
            self.version = choose_ver
            fabric_download = fabric_choose.currentText()
    
            InfoBar.success(
                title='⬇️ 正在下载',
                content=f"正在下载你所选的版本...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
            download_button.setText("已经开始下载...下载状态将会显示在这里")
    
            download_way_choose = widget.findChild(ComboBox, "download_way_choose")
            selected_way = download_way_choose.currentText()
    
            # 定义 teaching_tip 变量
            teaching_tip = None
    
            if selected_way == "Bloret Launcher":  # Bloret Launcher 方法
                log(f"LM_Download_Way_minecraft:{LM_Download_Way_minecraft}")
                LM_download_way_choose = widget.findChild(ComboBox, "LM_download_way_choose")
                BL_download(choose_ver, LM_download_way_choose.currentText(), self)
                self.on_download_finished(teaching_tip, download_button)
            else:  # CMCL 方法
                if fabric_download != "不安装":
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername} --fabric={fabric_download}"
                else:
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername}"
        
                self.log(f"下载命令: {command}")
        
                self.download_thread = self.DownloadThread(cmcl_path, command, self.log)
                self.threads.append(self.download_thread)
                self.download_thread.output_received.connect(self.log_output)
                self.download_thread.output_received.connect(lambda text: download_button.setText(text[:70] + '...' if len(text) > 70 else text))
                
                teaching_tip = InfoBar(
                    icon=InfoBarIcon.SUCCESS,
                    title='✅ 正在下载',
                    content=f"正在下载你所选的版本...",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                teaching_tip.show()
        
                self.download_thread.finished.connect(
                    lambda: self.on_download_finished(teaching_tip, download_button)
                )
                
                self.download_thread.error_occurred.connect(
                    lambda error: self.on_download_error(error, teaching_tip, download_button)
                )
                self.download_thread.start()
                self.threads.append(self.download_thread)  # 将线程添加到列表中

    class DownloadThread(QThread):
        finished = pyqtSignal()
        error_occurred = pyqtSignal(str)
        output_received = pyqtSignal(str)

        def __init__(self, cmcl_path, version, log_method):
            self.log = log_method
            super().__init__()
            self.cmcl_path = cmcl_path
            self.version = version

        def run(self):
            try:
                self.log(f"正在下载版本 {self.version}")
                self.log("执行命令: " + f"{self.version}")
                process = subprocess.Popen(
                    self.version,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                last_line = ""
                for line in iter(process.stdout.readline, ''):
                    last_line = line.strip()
                    self.output_received.emit(last_line)
                    if "该名称已存在，请更换一个名称。" in line:
                        self.error_occurred.emit("该版本已下载过。")
                        process.terminate()
                        return
                    self.output_received.emit(line.strip())
                    self.log(line.strip())  # 将输出存入日志
                while process.poll() is None:
                    self.output_received.emit("正在下载并安装")
                    time.sleep(1)
                process.stdout.close()
                process.wait()
                if process.returncode == 0:
                    self.finished.emit()
                else:
                    error = process.stderr.read().strip() or "Unknown error"
                    self.error_occurred.emit(error)
            except subprocess.CalledProcessError as e:
                self.error_occurred.emit(str(e.stderr))

        def send_system_notification(self, title, message):
            try:
                if sys.platform == "win32":
                    toast(title, message, duration="short", icon={'src': 'icons/bloret.png','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
            except Exception as e:
                self.log(f"发送系统通知失败: {e}", logging.ERROR)

    class MicrosoftLoginThread(QThread):
        finished = pyqtSignal(bool, str)
        
        def __init__(self):
            super().__init__()
            self.log_method = None
            
        def run(self):
            # 执行微软登录命令
            process = subprocess.Popen(["cmcl", "account", "--login=microsoft"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    encoding='utf-8')

            process.wait()
            
            if process.returncode == 0:
                self.finished.emit(True, "登录成功")
            else:
                error = process.stderr.read()
                self.finished.emit(False, f"登录失败: {error}")

    class OfflineLoginThread(QThread):
        finished = pyqtSignal(bool, str)
        
        def __init__(self, username):
            super().__init__()
            self.username = username
            
        def run(self):
            try:
                process = subprocess.Popen(["cmcl", "account", "--login=offline", "-n", self.username,"-s"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                process.wait()
                if process.returncode == 0:
                    self.finished.emit(True, "离线登录成功")
                else:
                    error = process.stderr.read()
                    self.finished.emit(False, f"登录失败: {error}")
            except Exception as e:
                self.finished.emit(False, f"执行异常: {str(e)}")

    # 添加 MessageBox 类
    class MessageBox(MessageBoxBase):
        def __init__(self, title, content, parent=None):
            super().__init__(parent)
            self.name_edit = LineEdit()
            self.viewLayout.addWidget(SubtitleLabel(content))
            self.viewLayout.addWidget(self.name_edit)
            self.widget.setMinimumWidth(300)

    class CustomMessageBox(MessageBoxBase):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.titleLabel = SubtitleLabel('离线登录')
            self.usernameLineEdit = LineEdit()

            self.usernameLineEdit.setPlaceholderText('请输入玩家名称')
            self.usernameLineEdit.setClearButtonEnabled(True)

            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.usernameLineEdit)

            self.widget.setMinimumWidth(300)

        def validate(self):
            """ 重写验证表单数据的方法 """
            isValid = len(self.usernameLineEdit.text()) > 0
            return isValid
    def handle_login(self, widget):
        login_way_choose = widget.findChild(ComboBox, "login_way")
        # 添加离线登录处理
        if login_way_choose.currentText() == "离线登录":
                try:
                    shutil.copyfile('cmcl.blank.json', 'cmcl.json')
                    dialog = self.CustomMessageBox(self)
                    if dialog.exec():
                        username = dialog.usernameLineEdit.text()
                        self.offline_thread = self.OfflineLoginThread(username)
                        self.offline_thread.finished.connect(
                            lambda success, msg: self.on_login_finished(widget, success, msg))
                        self.offline_thread.start()
                except Exception as e:
                    self.show_error("文件操作失败", f"无法覆盖cmcl.json: {str(e)}")
        elif login_way_choose.currentText() == "微软登录":
            login_way_choose = widget.findChild(ComboBox, "login_way")
            if not login_way_choose or login_way_choose.currentText() != "微软登录":
                return

            # 覆盖cmcl.json
            try:
                shutil.copyfile('cmcl.blank.json', 'cmcl.json')
                self.log("成功覆盖cmcl.json文件")
            except Exception as e:
                self.show_error("文件操作失败", f"无法覆盖cmcl.json: {str(e)}")
                return

            # 创建并启动登录线程
            self.microsoft_login_thread = self.MicrosoftLoginThread()
            self.microsoft_login_thread.log_method = self.log
            self.microsoft_login_thread.finished.connect(
                lambda success, msg: self.on_login_finished(widget, success, msg)
            )
            
            # 显示加载提示
            self.login_tip = InfoBar(
                icon=InfoBarIcon.WARNING,
                title='⏱️ 正在登录微软账户',
                content='请按照浏览器中的提示完成登录...',
                isClosable=True,  # 允许用户手动关闭
                position=InfoBarPosition.TOP,
                duration=5000,  # 设置自动关闭时间
                parent=self
            )
            self.login_tip.show()
            
            self.microsoft_login_thread.start()

    def on_login_finished(self, widget, success, message):
        # 添加有效性检查
        if hasattr(self, 'login_tip') and self.login_tip and not sip.isdeleted(self.login_tip):
            try:
                self.login_tip.close()
            except RuntimeError:
                pass  # 如果对象已被销毁则忽略异常
        
        # 处理结果
        if success:
            self.load_cmcl_data()
            self.update_passport_ui(widget)
            InfoBar.success(
                title='✅ 登录成功',
                content='登录成功',
                parent=self
            )
        else:
            InfoBar.error(
                title='❎ 登录失败',
                content=message,
                parent=self
            )

    def update_passport_ui(self, widget):
        # 更新UI显示
        login_way_combo = widget.findChild(ComboBox, "player_login_way")
        name_combo = widget.findChild(ComboBox, "playername")
        
        if self.cmcl_data:
            # 更新登录方式
            login_method = "微软登录" if self.login_mod_num == 2 else "离线登录"
            if login_way_combo:
                login_way_combo.clear()
                login_way_combo.addItem(login_method)
            
            # 更新玩家名称
            if name_combo:
                name_combo.clear()
                name_combo.addItem(self.player_name)
                
    def show_error(self, title, content):
        InfoBar.error(
            title=title,
            content=content,
            parent=self
        )
    def send_system_notification(self, title, message):
        try:
            if sys.platform == "win32":
                toast(title, message, duration="short", icon={'src': 'icons/bloret.png','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
            elif sys.platform == "darwin":
                subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
            else:
                subprocess.run(["notify-send", title, message])
        except Exception as e:
            self.log(f"发送系统通知失败: {e}", logging.ERROR)
    def on_download_error(self, error_message, teaching_tip, download_button):
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        TeachingTip.create(
            target=download_button,
            icon=InfoBarIcon.ERROR,
            title='❎ 提示',
            content=f"下载失败，原因：{error_message}",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=5000,
            parent=self
        )
        self.is_running = False  # 重置标志变量
    def handle_first_run(self):
        if self.config.get('first-run', True):
            parent_dir = os.path.dirname(os.getcwd())
            updating_folder = os.path.join(parent_dir, "updating")
            updata_ps1_file = os.path.join(parent_dir, "updata.ps1")
            if os.path.exists(updating_folder):
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"Remove-Item -Path '{updating_folder}' -Recurse -Force"], check=True)
                self.log(f"删除文件夹: {updating_folder}")
            if os.path.exists(updata_ps1_file):
                os.remove(updata_ps1_file)
                self.log(f"删除文件: {updata_ps1_file}")
                def create_shortcut(self):
                    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
                    shortcut_path = os.path.join(desktop, 'Bloret Launcher.lnk')
                    target = os.path.join(os.getcwd(), 'Bloret-Launcher.exe')
                    icon = os.path.join(os.getcwd(), 'icons', 'bloret.ico')
                    shell = Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(shortcut_path)
                    shortcut.TargetPath = target
                    shortcut.WorkingDirectory = os.getcwd()
                    shortcut.IconLocation = icon
                    shortcut.save()
                self.create_shortcut()
            #首次启动向 http://pcfs.top:2/api/blnum 发送请求，服务器计数器+1
            #具体可见项目 https://github.com/BloretCrew/Bloret-Launcher-Server
            response = requests.get(server_ip + "api/blnum")
            if response.status_code == 200:
                data = response.json()
                self.bl_users = data.get("user", "未知用户")
                self.log(f"获取到的用户数: {self.bl_users}")
            else:
                self.bl_users = "未知用户"
                self.log("无法获取用户数", logging.ERROR)

            #首次启动显示弹窗提醒
            # msg_box = QMessageBox(self)
            # msg_box.setIcon(QMessageBox.Information)
            # msg_box.setWindowTitle('欢迎')
            # msg_box.setText("欢迎使用百络谷启动器 (＾ｰ^)ノ\n您是百络谷启动器的第 %s 位用户" % self.bl_users)
            # msg_box.setWindowIcon(QIcon("icons/bloret.png"))  # 设置弹窗图标
            # msg_box.setStandardButtons(QMessageBox.Ok)
            # msg_box.exec()

            # 使用非模态对话框
            w = MessageBox(
                title="欢迎使用百络谷启动器 (＾ｰ^)ノ",
                content=f'您是百络谷启动器的第 {self.bl_users} 位用户',
                parent=self
            )
            w.show()


            # QMessageBox.information(self, "欢迎", "欢迎使用百络谷启动器 (＾ｰ^)ノ\n您是百络谷启动器的第 %s 位用户" % self.bl_users)
            # 更新配置文件中的 first-run 值
            self.config['first-run'] = False
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)

    def check_Bloret_version(self):
        try:
            response = requests.get(server_ip + "api/bloret-version")
            if response.status_code == 200:
                data = response.json()
                ver_id_bloret.clear()
                ver_id_bloret.extend(data.get("Bloret-versions", []))
                self.log(f"成功获取 Bloret 版本列表: {ver_id_bloret}")
            else:
                self.log("无法获取 Bloret 版本列表", logging.ERROR)
        except requests.RequestException as e:
            self.log(f"获取 Bloret 版本列表时发生错误: {e}", logging.ERROR)
    def check_for_updates(self):
        try:
            # 插入 socket 检查
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('pcfs.top', 2))
            BL_latest_ver, BL_update_text = self.get_latest_version()
            self.log(f"最新正式版: {BL_latest_ver}")
            BL_ver = float(self.config.get('ver', '0.0'))  # 从config.json读取当前版本
            if BL_ver < float(BL_latest_ver):
                self.log(f"当前版本不是最新版，请更新到 {BL_latest_ver} 版本", logging.WARNING)

                # 使用非模态对话框
                w = MessageBox(
                    title="当前版本不是最新版",
                    content=f'Bloret Launcher 貌似有个新新新版本\n你似乎正在运行 {BL_ver}，但事实上，百络谷启动器 {BL_latest_ver} 来啦！按下按钮自动更新。\n这个更新... {BL_update_text}',
                    parent=self
                )
                w.show()

                # 连接按钮点击事件以触发更新
                w.yesButton.clicked.connect(self.update_to_latest_version)
        except Exception as e:
            self.log(f"检查更新时发生错误: {e}", logging.ERROR)
            
            self.log("无法连接到 pcfs.top", logging.ERROR)
            w = MessageBox(
                title="无法连接到 pcfs.top",
                content=f'您无法连接到 PCFS 服务器来检查版本更新\n这可能是由于您的网络不佳？或是 PCFS 服务出现故障？\n请检查您的网络连接，或者稍后再试。\n我们等待了 3 秒，但它只显示：{e}',
                parent=self
            )
            update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': '无法连接到服务器 ❌'})
            w.show()
    def update_to_latest_version(self):
        update_script_path = os.path.join(os.getcwd(), "update.ps1")
        try:
            with open(update_script_path, "w", encoding="utf-8") as update_script:
                update_script.write(
                    "taskkill /im Bloret-Launcher.exe /f\n"
                    "winget update Bloret.BloretLauncher\n"
                )# 通过 winget 更新
            self.log(f"创建更新脚本: {update_script_path}")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", update_script_path], check=True)
        except Exception as e:
            self.log(f"创建或运行更新脚本失败: {e}", logging.ERROR)
            QMessageBox.critical(self, "更新失败", f"创建或运行更新脚本失败: {e}")
    #     #url = f"http://localhost:100/zipdownload/{self.BL_latest_ver}.zip"
    #     url = f"http://pcfs.top:2/zipdownload/latest.zip"
    #     save_path = os.path.join(os.getcwd(), f"{self.BL_latest_ver}.zip")
    #     updating_folder = os.path.join(os.path.dirname(os.getcwd()), "updating")
    #     if not os.path.exists(updating_folder):
    #         os.makedirs(updating_folder)
    #     try:
    #         response = requests.get(url, stream=True)
    #         response.raise_for_status()
    #         with open(save_path, 'wb') as file:
    #             for chunk in response.iter_content(chunk_size=8192):
    #                 file.write(chunk)
    #         self.log(f"版本 {self.BL_latest_ver} 下载成功，保存路径: {save_path}")
    #         # 将下载的文件移动到 updating 文件夹
    #         new_save_path = os.path.join(updating_folder, f"{self.BL_latest_ver}.zip")
    #         os.rename(save_path, new_save_path)
    #         # 解压缩文件到 updating 文件夹
    #         with zipfile.ZipFile(new_save_path, 'r') as zip_ref:
    #             zip_ref.extractall(updating_folder)
    #         self.log(f"版本 {self.BL_latest_ver} 解压缩成功，路径: {updating_folder}")
    #         # 删除压缩包
    #         os.remove(new_save_path)
    #         self.log(f"删除压缩包: {new_save_path}")
    #         # 移动 .minecraft 文件夹到 updating 文件夹
    #         minecraft_folder = os.path.join(os.getcwd(), ".minecraft")
    #         if os.path.exists(minecraft_folder):
    #             new_minecraft_folder = os.path.join(updating_folder, ".minecraft")
    #             os.rename(minecraft_folder, new_minecraft_folder)
    #             self.log(f"移动 .minecraft 文件夹到: {new_minecraft_folder}")
    #         # 创建 updata.ps1 文件
    #         current_folder_name = os.path.basename(os.getcwd())
    #         bat_file_path = os.path.join(os.path.dirname(os.getcwd()), "updata.ps1")
    #         with open(bat_file_path, 'w', encoding='utf-8') as bat_file:
    #             bat_file.write(f'cd "{os.path.dirname(os.getcwd())}"\n')
    #             bat_file.write(f'taskkill /im Bloret-Launcher.exe /f\n')
    #             bat_file.write(f'Start-Sleep -Seconds 2\n')
    #             bat_file.write(f'Remove-Item -Path ".\\{current_folder_name}" -Recurse -Force\n')
    #             bat_file.write(f'Move-Item -Path ".\\updating\\*" -Destination ".\\{current_folder_name}"\n')
    #             bat_file.write(f'cd "{os.path.join(os.path.dirname(os.getcwd()), "Bloret-Launcher")}"\n')
    #             bat_file.write(f'Start-Process -FilePath "Bloret-Launcher.exe"\n')
    #         self.log(f"创建 updata.ps1 文件: {bat_file_path}")
    #         QMessageBox.information(self, "即将安装", f"版本 {self.BL_latest_ver} 即将开始安装")

    #         # 运行 updata.ps1 文件
    #         subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", bat_file_path], check=True)
    #         self.log(f"运行 updata.ps1 文件: {bat_file_path}")
    #     except requests.RequestException as e:
    #         self.log(f"下载版本 {self.BL_latest_ver} 失败: {e}", logging.ERROR)
    #         QMessageBox.critical(self, "下载失败", f"下载版本 {self.BL_latest_ver} 失败: {e}")
    #     except zipfile.BadZipFile as e:
    #         self.log(f"解压缩版本 {self.BL最新版本} 失败: {e}", logging.ERROR)
    #         QMessageBox.critical(self, "解压缩失败", f"解压缩版本 {self.BL最新版本} 失败: {e}")
    #     except OSError as e:
    #         self.log(f"文件操作失败: {e}", logging.ERROR)
    #         QMessageBox.critical(self, "文件操作失败", f"文件操作失败: {e}")
    #     except subprocess.CalledProcessError as e:
    #         self.log(f"运行 updata.ps1 文件失败: {e}", logging.ERROR)
    #         QMessageBox.critical(self, "更新失败", f"运行 updata.ps1 文件失败: {e}")
    def toggle_show_all_versions(self, state):
        widget = self.findChild(QWidget, "downloadWidget")  # 假设你的下载界面的QWidget对象名称为downloadWidget
        if widget:
            minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
            show_all_versions = widget.findChild(QCheckBox, "show_all_versions")
            if minecraft_choose and show_all_versions:
                self.update_minecraft_versions(widget, show_all=state)

    def open_bloret_web(self):
        QDesktopServices.openUrl(QUrl("http://pcfs.top:2"))
        self.log("打开 Bloret Launcher 网页")
    def open_github_bloret(self):
        QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew"))
        self.log("打开Bloret Github 组织页面")
    def copy_skin_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_skin)
        self.log(f"皮肤URL {self.player_skin} 已复制到剪贴板")
    def copy_cape_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_cape)
        self.log(f"披风URL {self.player_cape} 已复制到剪贴板")
    def open_skin_url(self, widget):
        QDesktopServices.openUrl(QUrl(self.player_skin))
        self.log(f"打开皮肤URL: {self.player_skin}")
    def open_cape_url(self, widget):
        QDesktopServices.openUrl(QUrl(self.player_cape))
        self.log(f"打开披风URL: {self.player_cape}")
    def query_player_name(self, widget):
        player_uuid_edit = widget.findChild(QLineEdit, "search_name_type")
        name_result_label = widget.findChild(QLabel, "search_name")
        if player_uuid_edit and name_result_label:
            name_result_label.setText("查询中，请稍等...")
            player_uuid = player_uuid_edit.text()
            response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_uuid}")
            if response.status_code == 200:
                player_data = response.json()
                self.player_name = player_data.get("name", "未找到名称")
                name_result_label.setText(self.player_name)
                self.log(f"查询UUID {player_uuid} 的名称: {self.player_name}")
            else:
                name_result_label.setText("查询失败")
                self.log(f"查询UUID {player_uuid} 的名称失败", logging.ERROR)
    def copy_name_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_name)
        self.log(f"名称 {self.player_name} 已复制到剪贴板")
    def open_github_bloret_Launcher(self):
        QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew/Bloret-Launcher"))
        self.log("打开该项目的 Github 页面")
    def open_qq_link(self):
        QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/iGw0GwUCiI"))
        self.log("打开 Bloret QQ 群页面")
    def open_BLC_qq_link(self):
        QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/kEt8fb41wc"))
        self.log("打开 BLC QQ 群页面")
    def open_BBBS_link(self):
        QDesktopServices.openUrl(QUrl(server_ip+"bbs/"))
        self.log("打开 BBBS 页面")
    def animate_sidebar(self):
        start_geometry = self.navigationInterface.geometry()  # 修正拼写错误
        end_geometry = QRect(start_geometry.x(), start_geometry.y(), start_geometry.width(), start_geometry.height())
        self.sidebar_animation.setStartValue(start_geometry)
        self.sidebar_animation.setEndValue(end_geometry)
        self.sidebar_animation.start()
    def animate_fade_in(self):
        self.fade_in_animation.start()
    def apply_theme(self, palette=None):
        if palette is None:
            palette = QApplication.palette()
        
        # 检测系统主题
        if palette.color(QPalette.Window).lightness() < 128:
            theme = "dark"
        else:
            theme = "light"
        
        if theme == "dark":
            self.setStyleSheet("""
                QWidget { background-color: #2e2e2e; color: #ffffff; }
                QPushButton { background-color: #3a3a3a; border: 1px solid #444444; color: #ffffff; }
                QPushButton:hover { background-color: #4a4a4a; color: #ffffff; }
                QPushButton:pressed { background-color: #5a5a5a; color: #ffffff; }
                QComboBox { background-color: #3a3a3a; border: 1px solid #444444; color: #ffffff; }
                QComboBox:hover { background-color: #4a4a4a; color: #ffffff; }
                QComboBox:pressed { background-color: #5a5a5a; color: #ffffff; }
                QComboBox QAbstractItemView { background-color: #2e2e2e; selection-background-color: #4a4a4a; color: #ffffff; }
                QLineEdit { background-color: #3a3a3a; border: 1px solid #444444; color: #ffffff; }
                QLabel { color: #ffffff; }
                QCheckBox { color: #ffffff; }
                QCheckBox::indicator { width: 20px; height: 20px; }
                QCheckBox::indicator:checked { image: url(ui/icon/checked.png); }
                QCheckBox::indicator:unchecked { image: url(ui/icon/unchecked.png); }
            """)
            palette.setColor(QPalette.Window, QColor("#2e2e2e"))
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.AlternateBase, QColor("#2e2e2e"))
            palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#ffffff"))
            palette.setColor(QPalette.Button, QColor("#3a3a3a"))
            palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.Link, QColor("#2a82da"))
            palette.setColor(QPalette.Highlight, QColor("#2a82da"))
            palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.setPalette(palette)
        else:
            self.setStyleSheet("")
            self.setPalette(self.style().standardPalette())
    def setup_passport_ui(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "player_name")
        player_name_set_button = widget.findChild(QPushButton, "player_name_set")
        login_way_combo = widget.findChild(ComboBox, "player_login_way")
        login_way_choose = widget.findChild(ComboBox, "login_way")
        name_combo = widget.findChild(ComboBox, "playername")
        # if player_name_edit:
        #     player_name_edit.setText(self.player_name if self.cmcl_data else '')
        # else:
        #     self.log("未找到player_name输入框", logging.ERROR)
    
        if player_name_edit and player_name_set_button:
            player_name_set_button.clicked.connect(lambda: self.on_player_name_set_clicked(widget))
            self.log("已连接 player_name_set_button 点击事件")
    
        if self.cmcl_data:
            self.log("成功读取 cmcl.json 数据")
            
            if login_way_combo:
                login_way_choose.clear()
                login_way_choose.addItems(["离线登录", "微软登录"])
                login_way_choose.setCurrentText(self.login_mod)
                login_way_choose.setCurrentIndex(0)
    
            if login_way_combo:
                login_way_combo.clear()
                login_way_combo.addItem(str(self.login_mod))
                login_way_combo.setCurrentIndex(0)
                self.log(f"设置 login_way_combo 当前索引为: {self.login_mod}")
    
            if name_combo:
                name_combo.clear()
                name_combo.addItem(self.player_name)
                name_combo.setCurrentIndex(0)
                self.log(f"设置 name_combo 当前索引为: {self.player_name}")
        else:
            self.log("读取 cmcl.json 失败")
        
        # 添加登录按钮点击事件
        login_button = widget.findChild(QPushButton, "login")
        if login_button:
            login_button.clicked.connect(lambda: self.handle_login(widget))
        Bloret_PassPort_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
        Bloret_PassPort_logout = widget.findChild(QPushButton, "Bloret_PassPort_logout")
        Bloret_PassPort_login = widget.findChild(QPushButton, "Bloret_PassPort_login")
        Bloret_PassPort_view_BBBS = widget.findChild(QPushButton, "Bloret_PassPort_view_BBBS")
        if Bloret_PassPort_UserName:
            Bloret_PassPort_UserName.setText(self.config.get('Bloret_PassPort_UserName', '未登录'))
        if Bloret_PassPort_logout:
            Bloret_PassPort_logout.clicked.connect(lambda: self.Bloret_PassPort_Account_logout(widget))
        if Bloret_PassPort_login:
            Bloret_PassPort_login.clicked.connect(lambda: self.Bloret_PassPort_Account_login(widget))
        if Bloret_PassPort_view_BBBS:
            Bloret_PassPort_view_BBBS.clicked.connect(lambda: self.open_BBBS_link())
    def Bloret_PassPort_Account_logout(self, widget):
        self.config.update(Bloret_PassPort_UserName='未登录')
        self.config.update(Bloret_PassPort_PassWord='')
        self.config.update(Bloret_PassPort_Admin=False)
        
        open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
        # 更新界面显示
        Bloret_PassPort_User_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
        Bloret_PassPort_User_UserName.setText("未登录")
        InfoBar.success(
            title='⏫ 已退出登录',
            content="",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.log("已退出登录")
    def Bloret_PassPort_Account_login(self, widget):
        class CustomLoginDialog(MessageBoxBase):
            """ 自定义登录对话框 """
            def __init__(self, parent=None):
                super().__init__(parent)
                
                # 用户名组件
                self.usernameLabel = SubtitleLabel('用户名', self)
                self.usernameLineEdit = LineEdit(self)
                self.usernameLineEdit.setPlaceholderText('请输入用户名')
                
                # 密码组件
                self.passwordLabel = SubtitleLabel('密码', self)
                self.passwordLineEdit = LineEdit(self)
                self.passwordLineEdit.setPlaceholderText('请输入密码')
                self.passwordLineEdit.setEchoMode(LineEdit.Password)
                
                # 添加到布局
                self.viewLayout.addWidget(self.usernameLabel)
                self.viewLayout.addWidget(self.usernameLineEdit)
                self.viewLayout.addWidget(self.passwordLabel)
                self.viewLayout.addWidget(self.passwordLineEdit)
                
                self.widget.setMinimumWidth(350)

            def validate(self):
                """ 验证输入不能为空 """
                username = self.usernameLineEdit.text().strip()
                password = self.passwordLineEdit.text().strip()
                return bool(username and password)
        """ 登录账户方法 """
        # 创建并显示自定义对话框
        dialog = CustomLoginDialog(self)
        if dialog.exec():  # 用户点击确认
            username = dialog.usernameLineEdit.text().strip()
            password = dialog.passwordLineEdit.text().strip()

            try:
                response = requests.get(
                    f"{server_ip}api/login",
                    params={"name": username, "password": password}
                )
                response_data = response.json()
                if response_data.get("status") is False:
                    error_message = response_data.get('message', '未知错误')
                    log(f"登录失败:{error_message}", logging.ERROR)
                    InfoBar.error(
                        title='❌ 登录失败',
                        content=response_data.get("message", "未知错误"),
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                    return
                elif response_data.get("status") is True:
                    # 更新配置并记录日志
                    self.config['Bloret_PassPort_UserName'] = username
                    self.config['Bloret_PassPort_PassWord'] = password
                    self.config['Bloret_PassPort_Admin'] = response_data.get("admin", False)
                    self.log(f"登录成功: 用户名={username}", logging.INFO)
                    
                    # 更新界面显示
                    Bloret_PassPort_User_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
                    Bloret_PassPort_User_UserName.setText(username)

                    open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
                    InfoBar.success(
                        title='✅ 登录成功',
                        content="",
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                log("请求失败: %s" % str(e), logging.ERROR)
                InfoBar.error(
                    title='❌ 登录失败',
                    content=f"请求失败: {str(e)}",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
        else:
            self.log("登录对话框被取消", logging.INFO)
    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        

    # -----------------------------------------------------------
    # 以下内容是对于UI文件中各个元素的设定
    # -----------------------------------------------------------

    def on_home_clicked(self):
        self.log("主页 被点击")
        self.load_ui("ui/home.ui")
    def on_passport_clicked(self):
        self.log("通行证 被点击")
        self.load_ui("ui/passport.ui", parent=self.passportInterface)
        self.setup_passport_ui(self.passportInterface)
        self.log("通行证页面UI加载完成")
    def on_settings_clicked(self):
        self.log("设置 被点击")
        self.load_ui("ui/settings.ui")
    def on_info_clicked(self):
        self.log("关于 被点击")
        self.load_ui("ui/info.ui")
    def on_tools_clicked(self):
        self.log("工具 被点击")
        self.load_ui("ui/tools.ui")
    def on_button_clicked(self):
        self.log("按钮 被点击")
    def on_player_name_set_clicked(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "player_name")
        player_name = player_name_edit.text()

        if not player_name:
            InfoBar.warning(
                title='⚠️ 提示',
                content="请填写值后设定",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        elif any('\u4e00' <= char <= '\u9fff' for char in player_name):
            InfoBar.warning(
                title='⚠️ 提示',
                content="名称不能包含中文",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            with open('cmcl.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['accounts'][0]['playerName'] = player_name
            with open('cmcl.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

    def setup_home_ui(self, widget):
        github_org_button = widget.findChild(QPushButton, "pushButton_2")
        if github_org_button:
            github_org_button.clicked.connect(self.open_github_bloret)
        github_project_button = widget.findChild(QPushButton, "pushButton")
        if github_project_button:
            github_project_button.clicked.connect(self.open_github_bloret_Launcher)

        openblweb_button = widget.findChild(QPushButton, "openblweb")
        if openblweb_button:
            openblweb_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("http://pcfs.top:2")))

        self.run_cmcl_list()
        run_choose = widget.findChild(ComboBox, "run_choose")
        # if run_choose:
        #     run_choose.addItems(set_list)
        run_button = widget.findChild(QPushButton, "run")
        if run_button:
            run_button.clicked.connect(lambda: self.run_cmcl(run_choose.currentText()))
        self.show_text = widget.findChild(QLabel, "show")

        # self.run_cmcl_list()  # 初始化时加载版本列表
        # run_choose = widget.findChild(ComboBox, "run_choose")
        # if run_choose:
        #     run_choose.addItems(set_list)

        # tabBar = widget.findChild(TabBar, "runs")

    def log_output(self, output):
        if output:
            self.log(output.strip())
    def on_run_script_finished(self, teaching_tip, run_button):
        if self.update_show_text_thread:
            self.update_show_text_thread.terminate()  # 停止更新线程
            self.update_show_text_thread.wait()  # 确保线程完全停止
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()  # 关闭气泡消息
        InfoBar.success(
            title='⏹️ 游戏结束',
            content="Minecraft 已结束\n如果您认为是异常退出，请查看 log 文件夹中的最后一份日志文件\n并前往本项目的 Github 或 百络谷QQ群 询问",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.is_running = False  # 重置标志变量

        QApplication.processEvents()  # 处理所有挂起的事件
        time.sleep(1)  # 等待1秒确保所有事件处理完毕

    def on_run_script_error(self, error, teaching_tip, run_button):
        if self.update_show_text_thread:
            self.update_show_text_thread.terminate()  # 停止更新线程
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        InfoBar.error(
            title='❌ 运行失败',
            content=f"run.ps1 运行失败: {error}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.log(f"run.ps1 运行失败: {error}", logging.ERROR)
        self.is_running = False  # 重置标志变量
    def update_show_text(self, text):
        self.show_text.setText(text)  # 更新show文字框的内容
    def setup_download_load_ui(self, widget):
        loading_label = widget.findChild(QLabel, "loading_label")
        if loading_label:
            self.setup_loading_gif(loading_label)
    # def se tup_download_ui(self, widget):
    #     # 设置下载界面的UI元素
    #     minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
    #     show_all_versions = widget.findChild(QCheckBox, "show_all_versions")
    #     if minecraft_choose and show_all_versions:
    #         show_all_versions.stateChanged.connect(lambda state: self.update_minecraft_versions(minecraft_choose, state == Qt.Checked))
    #         self.update_minecraft_versions(minecraft_choose, show_all_versions.isChecked())
    def get_minecraft_versions(self, show_all):
        # 模拟获取 Minecraft 版本列表
        if show_all:
            return ["1.18.1", "1.18", "1.17.1", "1.17", "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16"]
        else:
            return ["1.18.1", "1.17.1", "1.16.5"]
    def setup_tools_ui(self, widget):
        name2uuid_button = widget.findChild(QPushButton, "name2uuid_player_Button")
        if name2uuid_button:
            name2uuid_button.clicked.connect(lambda: self.query_player_uuid(widget))
        search_name_button = widget.findChild(QPushButton, "search_name_button")
        if search_name_button:
            search_name_button.clicked.connect(lambda: self.query_player_name(widget))
        skin_search_button = widget.findChild(QPushButton, "skin_search_button")
        if skin_search_button:
            skin_search_button.clicked.connect(lambda: self.query_player_skin(widget))
        name_copy_button = widget.findChild(QPushButton, "search_name_copy")
        if name_copy_button:
            name_copy_button.clicked.connect(lambda: self.copy_name_to_clipboard(widget))
        uuid_copy_button = widget.findChild(QPushButton, "pushButton_5")
        if uuid_copy_button:
            uuid_copy_button.clicked.connect(lambda: self.copy_uuid_to_clipboard(widget))
        skin_copy_button = widget.findChild(QPushButton, "search_skin_copy")
        if skin_copy_button:
            skin_copy_button.clicked.connect(lambda: self.copy_skin_to_clipboard(widget))
        cape_copy_button = widget.findChild(QPushButton, "search_cape_copy")
        if cape_copy_button:
            cape_copy_button.clicked.connect(lambda: self.copy_cape_to_clipboard(widget))
    def copy_uuid_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_uuid)
        self.log(f"UUID {self.player_uuid} 已复制到剪贴板")
    def download_skin(self, widget):
        if self.player_skin:
            skin_url = self.player_skin
            skin_data = requests.get(skin_url).content
            with open("player_skin.png", "wb") as file:
                file.write(skin_data)
            self.log(f"皮肤已下载到 player_skin.png")
    def download_cape(self, widget):
        if self.player_cape:
            cape_url = self.player_cape
            cape_data = requests.get(cape_url).content
            with open("player_cape.png", "wb") as file:
                file.write(cape_data)
            self.log(f"披风已下载到 player_cape.png")
    def query_player_uuid(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "name2uuid_player_uuid")
        uuid_result_label = widget.findChild(QLabel, "label_2")
        if player_name_edit and uuid_result_label:
            uuid_result_label.setText("查询中，请稍等...")
            player_name = player_name_edit.text()
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player_name}")
            if response.status_code == 200:
                player_data = response.json()
                self.player_uuid = player_data.get("id", "未找到UUID")
                uuid_result_label.setText(self.player_uuid)
                self.log(f"查询玩家名称 {player_name} 的UUID: {self.player_uuid}")
            else:
                uuid_result_label.setText("查询失败")
                self.log(f"查询玩家名称 {player_name} 的UUID失败", logging.ERROR)
    def query_player_skin(self, widget):
        skin_uuid_edit = widget.findChild(QLineEdit, "skin_uuid")
        skin_result_label = widget.findChild(QLabel, "search_skin")
        cape_result_label = widget.findChild(QLabel, "search_cape")
        if skin_uuid_edit and skin_result_label and cape_result_label:
            skin_result_label.setText("查询中，请稍等...")
            cape_result_label.setText("查询中，请稍等...")
            player_uuid = skin_uuid_edit.text()
            response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_uuid}")
            if response.status_code == 200:
                player_data = response.json()
                properties = player_data.get("properties", [])
                for prop in properties:
                    if prop["name"] == "textures":
                        textures = json.loads(base64.b64decode(prop["value"]).decode("utf-8"))
                        self.player_skin = textures["textures"].get("SKIN", {}).get("url", "未找到皮肤")
                        self.player_cape = textures["textures"].get("CAPE", {}).get("url", "未找到披风")
                        skin_result_label.setText(self.player_skin[:12] + "..." if len(self.player_skin) > 12 else self.player_skin)
                        cape_result_label.setText(self.player_cape[:12] + "..." if len(self.player_cape) > 12 else self.player_cape)
                        self.log(f"查询玩家UUID {player_uuid} 的皮肤: {self.player_skin}")
                        self.log(f"查询玩家UUID {player_uuid} 的披风: {self.player_cape}")
                        break
            else:
                skin_result_label.setText("查询失败")
                cape_result_label.setText("查询失败")
                self.log(f"查询玩家UUID {player_uuid} 的皮肤和披风失败", logging.ERROR)
    def setup_settings_ui(self, widget):
        # 设置设置界面的UI元素
        log_clear_button = widget.findChild(QPushButton, "log_clear_button")
        if log_clear_button:
            log_clear_button.clicked.connect(lambda: self.clear_log_files(log_clear_button))
            self.update_log_clear_button_text(log_clear_button)  # 更新按钮文本

        # 添加深浅色模式选择框
        light_dark_choose = widget.findChild(ComboBox, "light_dark_choose")
        if light_dark_choose:
            light_dark_choose.clear()
            light_dark_choose.addItems(["跟随系统", "深色模式", "浅色模式"])
            light_dark_choose.currentTextChanged.connect(self.on_light_dark_changed)

        size_choose = widget.findChild(SpinBox, "Size_Choose")
        if size_choose:
            size_choose.setValue(self.config.get("size", 100))
            size_choose.valueChanged.connect(lambda value: (
                self.config.update(size=value),
                open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
            ))
        repeat_run_button = widget.findChild(SwitchButton, "repeat_run_button")
        if repeat_run_button:
            repeat_run_button.setChecked(self.config.get('repeat_run', False))
            repeat_run_button.checkedChanged.connect(lambda state: (
                self.config.update(repeat_run=state),
                open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
                self.log(f"显示软件打开过程: {'启用' if state else '禁用'}")
            ))
        show_runtime_do_button = widget.findChild(SwitchButton, "show_runtime_do_button")
        if show_runtime_do_button:
            show_runtime_do_button.setChecked(self.config.get('show_runtime_do', False))
            show_runtime_do_button.checkedChanged.connect(lambda state: (
                self.config.update(show_runtime_do=state),
                open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
                self.log(f"重复运行设置已更改为: {'启用' if state else '禁用'}")
            ))
        BL_version = widget.findChild(QLabel, "BL_version")
        if BL_version:
            BL_version.setText(f"{self.config.get('ver', '未知')}")
    def on_light_dark_changed(self, mode):
        if mode == "跟随系统":
            self.apply_theme()
        elif mode == "深色模式":
            self.apply_theme(QPalette(QColor("#2e2e2e")))
        elif mode == "浅色模式":
            self.apply_theme(QPalette(QColor("#ffffff")))

    def clear_log_files(self, log_clear_button):
        log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
        file_num = len(os.listdir(log_folder))-1  # 减去一个正在使用的文件
        if os.path.exists(log_folder) and os.path.isdir(log_folder):
            for filename in os.listdir(log_folder):
                file_path = os.path.join(log_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    # InfoBar.success(
                    #     title='🗑️ 清理成功',
                    #     content=f"已清理 {file_path}",
                    #     isClosable=True,
                    #     position=InfoBarPosition.TOP,
                    #     duration=5000,
                    #     parent=self
                    # )
                except Exception as e:
                    self.log(f"Failed to delete {file_path}. Reason: {e}", logging.ERROR)
        InfoBar.success(
            title='🗑️ 清理成功',
            content=f"已清理 {file_num} 个文件",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.update_log_clear_button_text(log_clear_button)
    def get_latest_version(self):

        try:
            response = requests.get(server_ip + "api/BLlatest")
            if response.status_code == 200:
                latest_release = response.json()
                BL_update_text = latest_release.get("text")
                BL_latest_ver = latest_release.get("Bloret-Launcher-latest")
                return BL_latest_ver, BL_update_text
            else:
                self.log("查询最新版本失败", logging.ERROR)
                return BL_latest_ver, BL_update_text
        except requests.RequestException as e:
            self.log(f"查询最新版本时发生错误: {e}", logging.ERROR)
            return BL_latest_ver, BL_update_text
    def setup_info_ui(self, widget):
        github_org_button = widget.findChild(QPushButton, "pushButton_2")
        if github_org_button:
            github_org_button.clicked.connect(self.open_github_bloret)
        github_project_button = widget.findChild(QPushButton, "button_github")
        if github_project_button:
            github_project_button.clicked.connect(self.open_github_bloret_Launcher)
        qq_group_button = widget.findChild(QPushButton, "pushButton")
        if qq_group_button:
            qq_group_button.clicked.connect(self.open_qq_link)
        qq_icon = widget.findChild(QLabel, "QQ_icon")
        if qq_icon:
            qq_icon.setPixmap(QPixmap("ui/icon/qq.png"))
        BLC_QQ = widget.findChild(QPushButton, "BLC_QQ")
        if BLC_QQ:
            BLC_QQ.clicked.connect(self.open_BLC_qq_link)

    def update_log_clear_button_text(self, button):
        log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
        if os.path.exists(log_folder) and os.path.isdir(log_folder):
            log_files = os.listdir(log_folder)
            log_file_count = len(log_files)
            total_size = sum(os.path.getsize(os.path.join(log_folder, f)) for f in log_files)
            if log_file_count-1 <= 0:
                button.setText("没有日志可以清空了")
                button.setEnabled(False)
            else:
                button.setText(f"清空 {log_file_count-1} 个日志，总计 {total_size // 1024} KB")
        else:
            button.setText("清空日志")
 
# 获取系统深浅色主题
isdarktheme = is_dark_theme()
log(f"当前主题:{isdarktheme}")
LM_Download_Way,LM_Download_Way_list,LM_Download_Way_version,LM_Download_Way_minecraft=check_Light_Minecraft_Download_Way()

# 适配高DPI缩放
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)


# 创建 QApplication 实例
app = QApplication(["Bloret Launcher"])

# 初始化 FluentTranslator
translator = FluentTranslator()
app.installTranslator(translator)

# 默认语言跟随系统语言
current_locale = QLocale.system()

# 添加语言切换功能
def switch_language(locale):
    global translator
    app.removeTranslator(translator)  # 移除当前翻译器
    translator = FluentTranslator(locale)
    app.installTranslator(translator)
    window.retranslateUi()  # 重新翻译 UI


# 检查写入权限
if not check_write_permission():
    w = Dialog("Bloret Launcher 无法写入文件", "...")
    if w.exec():
        print('确认')
    else:
        print('取消')
    sys.exit(0)

# 创建主窗口并显示
window = MainWindow()
window.show()

# 检测是否重复运行
if sys.platform == "win32":
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\BloretLauncherMutex")
    if mutex == 0:
        log("创建互斥体失败")
        sys.exit(1)
    error = ctypes.windll.kernel32.GetLastError()
    if error == 183:  # ERROR_ALREADY_EXISTS
        log("检测到程序重复运行")
        if not window.config.get('repeat_run', False):
            log("重复运行被禁用：检测到程序已运行，退出新实例")
            w = Dialog("Bloret Launcher 已阻止了重复打开软件的操作", "为了防止 Bloret Launcher 占满您的计算机，我们已阻止您重复打开 Bloret Launcher\n如需重复打开，请到设置中设置允许重复运行。")
            if w.exec():
                print('确认')
            ctypes.windll.kernel32.CloseHandle(mutex)
            sys.exit(0)


scale_factor = window.scale_factor
os.environ["QT_SCALE_FACTOR"] = str(scale_factor)

# 运行应用程序
sys.exit(app.exec())