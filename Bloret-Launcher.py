# 1. 系统与内置库
import os
import sys
import re
import json
import time
import locale
import ctypes
import shutil
import logging
import traceback
import subprocess
from http import server

# 2. 第三方库
from PyQt5 import sip
import psutil
import requests
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QLabel, QFileDialog, 
    QMessageBox, QDialog, QSystemTrayIcon, QStackedWidget
)
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import (
    Qt, QTimer, QSize, QRect, QPropertyAnimation, QEasingCurve, 
    QSettings, QThread, pyqtSignal, QLocale
)
from qfluentwidgets import (
    MessageBox, SubtitleLabel, StrongBodyLabel, MessageBoxBase, 
    NavigationItemPosition, TeachingTip, InfoBarIcon, TeachingTipTailPosition, 
    ComboBox, InfoBar, InfoBarPosition, FluentWindow, SplashScreen, 
    Dialog, LineEdit, SystemTrayMenu, Action, setThemeColor, 
    FluentTranslator, FluentIcon, TabBar, TabCloseButtonDisplayMode
)

# 3. 自定义模块 (Bloret Launcher Modules)
import modules.globals as BLglobals
import modules.config as cfg
import modules.web
import modules.mwtool
from modules.config import read
from modules.safe import handle_exception
from modules.log import log
from modules.win11toast import toast, notify, update_progress
from modules.systems import (
    get_system_theme_color, is_dark_theme, check_write_permission, 
    restart, setup_startup_with_self_starting
)
from modules.setup_ui import (
    setup_home_ui, setup_download_old_ui, setup_tools_ui, setup_passport_ui, 
    setup_settings_ui, setup_info_ui, load_ui, setup_Mod_ui, setup_multiplayer_ui, setup_download_ui
)
from modules.customize import CustomizeRun
from modules.global_hotkey import init_global_hotkeys, get_signal_emitter
from modules.BLServer import (
    check_Light_Minecraft_Download_Way, handle_first_run, 
    check_Bloret_version, check_for_updates
)
from modules.links import open_BBBS_link
from modules.BLDownload import BL_download
from modules.launch import Get_Run_Script
from modules.i18n import i18n_widgets, i18nText
from modules.ShortCut import ScreenShortCut
from modules.install import InstallMinecraftVersion
from modules.VersionInfo import GetMinecraftList

config = read()

def update_download_way(data, data_list, version, minecraft):
    global LM_Download_Way, LM_Download_Way_list, LM_Download_Way_version, LM_Download_Way_minecraft
    LM_Download_Way = data
    LM_Download_Way_version = version
    LM_Download_Way_minecraft = minecraft


class SystemTrayIcon(QSystemTrayIcon):
    """ 
    系统托盘图标 
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if parent is None:
            print(i18nText("警告：SystemTrayIcon 的 parent 参数为 None"))
        self.setIcon(QIcon('bloret.ico'))  # 设置托盘图标
        self.parent = parent
        self.main_window = parent

        # 创建托盘菜单
        self.menu = SystemTrayMenu(parent=parent)

        # 添加二级菜单
        launch_menu = SystemTrayMenu(i18nText("🔼  启动版本"), self.menu)
        print("BLglobals.set_list:", BLglobals.set_list)

        for version in BLglobals.set_list:
            action = Action(
                version,
                triggered=lambda checked, version=version: self.main_window.run_cmcl(version)
            )
            launch_menu.addAction(action)

        self.menu.addMenu(launch_menu)

        self.menu.addActions([
            Action(i18nText('🔡  访问 BBS'), triggered=lambda: open_BBBS_link(BLglobals.server_ip)),
            Action(i18nText('🔄️  重启程序'), triggered=self.main_window.restart_app),
            Action(i18nText('✅  显示窗口'), triggered=self.main_window.show_main_window),
            Action(i18nText('❎  退出程序'), triggered=self.main_window.quit_app)
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
class RunScriptThread(QThread):
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    output_received = pyqtSignal(str)
    last_output_received = pyqtSignal(str)  # 新增信号
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.version = None
    
    def run(self):
        script_path = "run.bat"
        try:
            self.process = subprocess.Popen(
                [script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏控制台窗口
            )
            last_line = ""
            for line in iter(lambda: self.process.stdout.readline(), ''):  # 移除errors参数
                last_line = line.strip()
                self.output_received.emit(last_line)
            self.last_output_received.emit(last_line)
            self.process.stdout.close()
            self.process.wait()
            if self.process.returncode == 0:
                self.finished.emit()
            else:
                self.error_occurred.emit(self.process.stderr.read().strip())
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(str(e.stderr))
    
    def terminate_process(self):
        """终止Minecraft进程"""
        try:
            # 首先终止批处理脚本进程
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=3)  # 等待3秒
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait()
            
            # 查找包含版本信息的Java进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'java' in proc.info.get('name', '').lower():
                        # 检查命令行参数中是否包含版本信息
                        cmd_str = ' '.join(cmdline)
                        if self.version and self.version in cmd_str:
                            log(f"找到Minecraft进程 (PID: {proc.pid}, 版本: {self.version})")
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                proc.wait()
                            log(f"已终止Minecraft进程 (PID: {proc.pid})")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 如果没有找到特定版本的进程，尝试查找典型的Minecraft进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'java' in proc.info.get('name', '').lower():
                        cmd_str = ' '.join(cmdline)
                        # 检查是否包含Minecraft相关的类或参数
                        if any(keyword in cmd_str for keyword in ['net.minecraft', 'minecraft', '.jar', 'forge', 'fabric']):
                            log(f"找到可能的Minecraft进程 (PID: {proc.pid})")
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                proc.wait()
                            log(f"已终止可能的Minecraft进程 (PID: {proc.pid})")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            log(f"未找到正在运行的Minecraft进程 (版本: {self.version})")
            return True  # 即使没有找到进程，也算作成功
            
        except ImportError:
            log("警告: 未安装psutil库，无法精确查找Minecraft进程")
            return True
        except Exception as e:
            log(f"终止进程时出错: {e}")
            return False
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
            BLglobals.ver_id_main.clear()
            BLglobals.ver_id_short.clear()
            BLglobals.ver_id_long.clear()
            for version in versions:
                if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                    BLglobals.ver_id_main.append(version["id"])
                else:
                    if version["type"] == "snapshot":
                        BLglobals.ver_id_short.append(version["id"])
                    elif version["type"] in ["old_alpha", "old_beta"]:
                        BLglobals.ver_id_long.append(version["id"])
            if self.version_type == i18nText("百络谷支持版本"):
                # 直接使用固定的版本列表
                self.versions_loaded.emit(["1.21.7", "1.21.8"])
            elif self.version_type == i18nText("正式版本"):
                self.versions_loaded.emit(BLglobals.ver_id_main)
            elif self.version_type == i18nText("快照版本"):
                self.versions_loaded.emit(BLglobals.ver_id_short)
            elif self.version_type == i18nText("远古版本"):
                self.versions_loaded.emit(BLglobals.ver_id_long)
            else:
                self.error_occurred.emit(i18nText("未知的版本类型"))
        except requests.RequestException as e:
            self.error_occurred.emit(f"请求错误: {e}")
        except requests.exceptions.SSLError as e:
            self.error_occurred.emit(f"SSL 错误: {e}")
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 初始化配置文件
        with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 进程管理：版本 -> RunScriptThread 映射
        self.running_processes = {}
        self.minecraft_tab = None

        # 获取系统主题颜色
        theme_color = get_system_theme_color()
        log(f"系统主题颜色: {theme_color}")
        setThemeColor(theme_color)

        if(isdarktheme):
            from qfluentwidgets import setTheme, Theme
            setTheme(Theme.AUTO)
            
        self.setWindowTitle("Bloret Launcher")
        icon_path = os.path.join(os.getcwd(), 'bloret.ico')
        if os.path.exists(icon_path):
            log(f"图标路径存在: {icon_path}")
        else:
            log(f"图标路径不存在: {icon_path}", logging.ERROR)
        self.setWindowIcon(QIcon(icon_path))

        # 检测是否重复运行
        self.mutex = None
        if sys.platform == "win32":
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\BloretLauncherMutex")
            if self.mutex == 0:
                log(i18nText("创建互斥体失败"))
                sys.exit(1)
            error = ctypes.windll.kernel32.GetLastError()
            if error == 183:  # ERROR_ALREADY_EXISTS
                log(i18nText("检测到程序重复运行"))
                if not self.config.get('repeat_run', False):
                    log(i18nText("重复运行被禁用：检测到程序已运行，退出新实例"))
                    # 显示通知
                    notify(progress={
                        'title': i18nText('Bloret Launcher 已阻止了重复打开软件的操作'),
                        'body': i18nText('为了防止 Bloret Launcher 占满您的计算机，我们已阻止您重复打开 Bloret Launcher\n如需重复打开，请到设置中勾选允许重复运行。'),
                        'icon': os.path.join(os.getcwd(), 'bloret.ico')
                    })
                    w = Dialog(i18nText("Bloret Launcher 已阻止了重复打开软件的操作"), i18nText("为了防止 Bloret Launcher 占满您的计算机，我们已阻止您重复打开 Bloret Launcher\n如需重复打开，请到设置中勾选允许重复运行。"))
                    if w.exec():
                        print(i18nText('确认'))
                    ctypes.windll.kernel32.CloseHandle(self.mutex)
                    sys.exit(0)
                    
        check_for_updates(self,BLglobals.server_ip)

        if self.config.get('show_runtime_do', False):
            log(i18nText("显示软件打开过程已启用"))
            # 显示通知
            notify(progress={
                'title': i18nText('正在启动 Bloret Launcher'),
                'status': i18nText('正在做打开软件前的工作...'),
                'value': '0',
                'valueStringOverride': '0%',
                'icon': os.path.join(os.getcwd(), 'bloret.ico')
            })
        else:
            log(i18nText("显示软件打开过程已禁用"))

        # 检查是否需要设置开机自启
        setup_startup_with_self_starting(cfg.read().get("self-starting", False))

        # 检查并设置 minecraft_dir 配置
        if not self.config.get('minecraft_dir'):
            # 设置默认的 minecraft 目录为 %appdata%/Bloret-Launcher/.minecraft
            default_mc_dir = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', '.minecraft')
            self.config['minecraft_dir'] = default_mc_dir
            # 保存配置到文件
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            # 同时更新全局变量
            BLglobals.minecraft_dir = default_mc_dir
            log(f"已设置默认Minecraft目录: {default_mc_dir}")
        else:
            # 确保全局变量与配置文件同步
            BLglobals.minecraft_dir = self.config['minecraft_dir']

        # 设置全局编码
        codec = locale.getpreferredencoding()
        if sys.stdout:
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8')

        # # 为 Plugin.py 设置 Window 参数
        # setup_window(window)

        # 1. 创建启动页面
        update_progress({'value': 10 / 100, 'valueStringOverride': '1/10', 'status': i18nText('创建启动页面')})
        icon_path = os.path.join(os.getcwd(), 'bloret.ico')
        if os.path.exists(icon_path):
            log(f"图标路径存在: {icon_path}")
        else:
            log(f"图标路径不存在: {icon_path}", logging.ERROR)
        self.splashScreen = SplashScreen(QIcon(icon_path), self)
        log(i18nText("启动画面创建完成"))
        self.splashScreen.setIconSize(QSize(102, 102))
        self.splashScreen.setWindowTitle("Bloret Launcher")
        self.splashScreen.setWindowIcon(QIcon(icon_path))
        
        # 2. 在创建其他子页面前先显示主界面
        update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': i18nText('连接服务器')})
        self.splashScreen.show()
        log(i18nText("启动画面已显示"))

        if not isdarktheme:
            # 监听系统主题变化
            QApplication.instance().paletteChanged.connect(self.apply_theme)
        
        # 初始化 sidebar_animation
        update_progress({'value': 30 / 100, 'valueStringOverride': '3/10', 'status': i18nText('初始化侧边栏动画')})
        self.sidebar_animation = QPropertyAnimation(self.navigationInterface, b"geometry")
        self.sidebar_animation.setDuration(300)  # 设置动画持续时间
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 初始化 fade_in_animation
        update_progress({'value': 40 / 100, 'valueStringOverride': '4/10', 'status': i18nText('初始化淡入动画')})
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.loading_dialogs = []  # 初始化 loading_dialogs 属性
        self.threads = []  # 初始化 threads 属性
        handle_first_run(self,BLglobals.server_ip)
        ver_id_bloret = check_Bloret_version(self, BLglobals.server_ip, BLglobals.ver_id_bloret)
        

        # 初始化其他属性
        update_progress({'value': 60 / 100, 'valueStringOverride': '6/10', 'status': i18nText('初始化其他属性')})
        self.is_running = False

        # 从配置加载账户信息
        mc_acc_config = self.config.get("MinecraftAccount", {})
        accounts = mc_acc_config.get("accounts", [])
        chosen_idx = mc_acc_config.get("chosen", 0)

        self.player_name = ""
        self.player_uuid = ""
        self.login_mod = i18nText("请在下方登录")  # 默认值

        if accounts and 0 <= chosen_idx < len(accounts):
            acc = accounts[chosen_idx]
            self.player_name = acc.get("username", "")
            self.player_uuid = acc.get("uuid", "")
            acc_type = acc.get("type", "Offline")
            if acc_type == "Microsoft":
                self.login_mod = i18nText("微软登录")
            else:
                self.login_mod = i18nText("离线登录")

        self.player_skin = ""
        self.player_cape = ""
        self.Customize_icon = None
        self.settings = QSettings("Bloret", "Launcher")
        if not isdarktheme:
            self.apply_theme()
        self.cmcl_data = None
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

        # 初始化全局快捷键
        init_global_hotkeys()
        
        # 连接快捷键信号到主线程处理
        try:
            signal_emitter = get_signal_emitter()
            if signal_emitter:
                signal_emitter.shortcut_triggered.connect(self.handle_screenshot_shortcut)
                log("已连接截图快捷键信号到主线程处理")
            else:
                log("警告：无法获取快捷键信号发射器")
        except Exception as e:
            log(f"连接快捷键信号失败: {e}")

        # 处理首次运行
        update_progress({'value': 70 / 100, 'valueStringOverride': '7/10', 'status': i18nText('处理首次运行')})
        QTimer.singleShot(0, lambda: handle_first_run(self,BLglobals.server_ip))
        
        # 隐藏启动页面
        update_progress({'value': 80 / 100, 'valueStringOverride': '8/10', 'status': i18nText('隐藏启动页面')})
        QTimer.singleShot(3000, lambda: (log(i18nText("隐藏启动画面")), self.splashScreen.finish()))

        # 初始化需要 cmcl_data 的组件
        update_progress({'value': 90 / 100, 'valueStringOverride': '9/10', 'status': i18nText('初始化需要 cmcl_data 的组件')})
        self.initNavigation()

        # 显示窗口
        update_progress({'value': 100 / 100, 'valueStringOverride': '10/10', 'status': i18nText('显示窗口')})
        self.show()
        
    def handle_screenshot_shortcut(self):
        """处理截图快捷键，在主线程中执行截图功能"""
        try:
            log("收到截图快捷键信号，开始执行截图功能")
            widget = ScreenShortCut()
            log("截图功能已启动")
        except Exception as e:
            log(f"执行截图功能失败: {e}")
            traceback.print_exc()
        
        # 错误报告测试
        # try:
        #     raise Exception("test")
        # except Exception as e:
        #     handle_exception(e)

    def refresh_home_minecraft_account(self,player_name,widget):
        Minecraft_account = widget.findChild(QLabel, "Minecraft_account")
        # if Minecraft_account:
        log(f"设置主页玩家名称：{player_name}，Minecraft_account:{Minecraft_account}")
        Minecraft_account.setText(f"{player_name}")
        
    def initNavigation(self):
        self.homeInterface = QWidget()
        self.downloadInterface = QWidget()
        self.toolsInterface = QWidget()
        self.modInterface = QWidget()
        self.passportInterface = QWidget()
        self.settingsInterface = QWidget()
        self.infoInterface = QWidget()
        self.homeInterface.setObjectName("home")
        self.downloadInterface.setObjectName("download")
        self.toolsInterface.setObjectName("tools")
        self.modInterface.setObjectName("mod")
        self.passportInterface.setObjectName("passport")
        self.settingsInterface.setObjectName("settings")
        self.infoInterface.setObjectName("info")
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, i18nText("主页"), NavigationItemPosition.TOP)
        self.addSubInterface(self.downloadInterface, FluentIcon.DOWNLOAD, i18nText("下载"), NavigationItemPosition.TOP)
        self.addSubInterface(self.toolsInterface, FluentIcon.DEVELOPER_TOOLS, i18nText("工具"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.modInterface, FluentIcon.TRANSPARENT, "Mods", NavigationItemPosition.SCROLL)
        self.addSubInterface(self.passportInterface, FluentIcon.PEOPLE, i18nText("通行证"), NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, i18nText("设置"), NavigationItemPosition.BOTTOM)
        self.multiplayerInterface = QWidget()
        self.multiplayerInterface.setObjectName("multiplayer")
        self.addSubInterface(self.multiplayerInterface, FluentIcon.CONNECT, i18nText("联机"), NavigationItemPosition.SCROLL)
        self.addSubInterface(self.infoInterface, FluentIcon.INFO, i18nText("关于"), NavigationItemPosition.BOTTOM)
        load_ui("ui/home.ui", parent=self.homeInterface)
        load_ui("ui/client.ui", parent=self.multiplayerInterface)
        load_ui("ui/download.ui", parent=self.downloadInterface)
        load_ui("ui/tools.ui", parent=self.toolsInterface)
        load_ui("ui/mods.ui", parent=self.modInterface)
        load_ui("ui/passport.ui", parent=self.passportInterface)
        load_ui("ui/settings.ui", parent=self.settingsInterface)
        load_ui("ui/info.ui", parent=self.infoInterface)
        i18n_widgets(self)
        
        # 1. 先初始化主页，这里面会调用 run_cmcl_list 更新全局列表
        setup_home_ui(self,self.homeInterface)
        
        setup_download_ui(self,self.downloadInterface)
        setup_tools_ui(self,self.toolsInterface)
        setup_info_ui(self,self.infoInterface)
        setup_Mod_ui(self,self.modInterface)
        setup_multiplayer_ui(self,self.multiplayerInterface, BLglobals.server_ip)
        setup_passport_ui(self,self.passportInterface,BLglobals.server_ip,self.homeInterface)
        setup_settings_ui(self,self.settingsInterface)
        
        # 2. 此时 BLglobals 中的列表应该已经被 setup_home_ui -> run_cmcl_list 填充了
        # 如果不放心，可以再次手动获取一下，或者直接使用全局变量
        if not hasattr(BLglobals, 'minecraft_list'):
            # 如果全局变量未初始化，尝试手动运行一次列表刷新逻辑
            # 注意：这里我们不能直接调用 run_cmcl_list 因为它依赖 config
            # 但既然是 MainWindow 的方法，我们可以直接调
            self.run_cmcl_list(True)
            
        mc_list = getattr(BLglobals, 'minecraft_list', [])
        cust_list = getattr(BLglobals, 'customize_list', [])
        
        log(f"版本管理UI初始化列表: MC={mc_list}, Custom={cust_list}")

    def animate_sidebar(self):
        start_geometry = self.navigationInterface.geometry()
        end_geometry = QRect(start_geometry.x(), start_geometry.y(), start_geometry.width(), start_geometry.height())
        self.sidebar_animation.setStartValue(start_geometry)
        self.sidebar_animation.setEndValue(end_geometry)
        self.sidebar_animation.start()
    def initWindow(self):
        # self.resize(900, 700)
        self.setWindowIcon(QIcon("bloret.ico"))
        self.setWindowTitle("Bloret Launcher")
        self.scale_factor = self.config.get('size', 90) / 100.0
        # self.resize(int(800 * self.scale_factor), int(600 * self.scale_factor))
        # 优化窗口缩放逻辑（替换原有resize调用）
    def apply_scale(self):
        base_width, base_height = 800, 600  # 基准尺寸
        self.scale_factor = self.config.get('size', 90) / 100.0
        scaled_width = int(base_width * self.scale_factor)
        os.environ['QT_SCALE_FACTOR'] = str(self.scale_factor)
        scaled_height = int(base_height * self.scale_factor)

        self.resize(scaled_width, scaled_height)

        # 强制控件重新布局
        self.layout().activate()

        # 调用侧边栏缩放函数
        self.apply_sidebar_scaling()
    def apply_sidebar_scaling(self):
        base_sidebar_width = 300  # 设置一个基准宽度
        size = self.scale_factor   # 使用已有的 scale_factor 属性

        scaled_sidebar_width = int(base_sidebar_width * size)
        self.navigationInterface.setExpandWidth(scaled_sidebar_width)
        if hasattr(self.navigationInterface, 'setCollapseWidth'):
            self.navigationInterface.setCollapseWidth(int(scaled_sidebar_width * size))
        # 可选：设置最小展开宽度
        base_window_width = 900
        scaled_min_expand_width = int(base_window_width * size)
        self.resize(int(base_window_width * size), int(700 * size))  # 调整窗口大小
        self.navigationInterface.setMinimumExpandWidth(scaled_min_expand_width)
        # self.navigationInterface.expand(useAni=False)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        icon_size = int(64 * self.scale_factor)
        
        # 仅在存在 Customize_icon 时更新
        if hasattr(self, 'Customize_icon') and self.Customize_icon:
            self.Customize_icon.setPixmap(self.icon.pixmap(icon_size, icon_size))
    def on_home_clicked(self):
        log(i18nText("主页 被点击"))
        self.switchTo(self.homeInterface)
    def download_minecraft_version(self, version):
        """下载并安装Minecraft版本"""
        if not version:
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("请选择一个Minecraft版本"),
                parent=self,
                duration=3000
            )
            return
            
        log(f"开始下载Minecraft版本: {version}")
        
        # 使用InstallMinecraftVersion函数下载版本

        # 加载UI文件
        try:
            self.download_dialog = QDialog(self)
            uic.loadUi("ui/MCVer_downloading.ui", self.download_dialog)
            self.download_dialog.setWindowTitle(f"正在下载 Minecraft {version}")

            # 设置MaxThread的值
            with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            max_thread_value = config.get("MaxThread", 2000)
            self.download_dialog.MaxThread.setText(str(max_thread_value))

            self.download_dialog.show()
        except Exception as e:
            log(f"加载或显示下载弹窗时发生错误: {e}")
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=f"无法显示下载进度弹窗: {e}",
                parent=self,
                duration=5000
            )
            return

        # 创建线程下载版本
        class DownloadThread(QThread):
            download_finished = pyqtSignal(bool)

            def __init__(self, version, minecraft_dir, download_dialog):
                super().__init__()
                self.version = version
                BLglobals.minecraft_dir = minecraft_dir
                self.download_dialog = download_dialog

            def run(self):
                result = InstallMinecraftVersion(self.version, BLglobals.minecraft_dir, self.download_dialog)
                self.download_finished.emit(result)

        download_thread = DownloadThread(version, BLglobals.minecraft_dir, self.download_dialog)
        download_thread.download_finished.connect(lambda success: self.on_minecraft_download_finished(success, version, self.download_dialog))
        download_thread.start()
        BLglobals.threads.append(download_thread)  # 防止线程被垃圾回收
    
    def download_fabric_version(self, version):
        """下载并安装Fabric版本"""
        if not version:
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("请选择一个Fabric版本"),
                parent=self,
                duration=3000
            )
            return
            
        log(f"开始下载Fabric版本: {version}")
        
        # 创建进度提示
        teaching_tip = TeachingTip(
            title=f"正在下载 Fabric {version}",
            content=i18nText("下载过程可能需要几分钟，请耐心等待..."),
            parent=self,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=-1,  # 不自动关闭
            isClosable=False
        )
        teaching_tip.show()
        
        # TODO: 实现Fabric版本下载逻辑
        # 临时实现，仅显示提示
        InfoBar.warning(
            title=i18nText('⚠️ 功能开发中'),
            content=f"Fabric {version} 下载功能正在开发中",
            parent=self,
            duration=3000
        )
        teaching_tip.close()
    
    def download_java_version(self, version_text):
        """下载并安装Java版本"""
        if not version_text:
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("请选择一个Java版本"),
                parent=self,
                duration=3000
            )
            return
            
        # 从选择框文本中提取版本号
        match = re.search(r'Java (\d+)', version_text)
        if not match:
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("无法解析Java版本号"),
                parent=self,
                duration=3000
            )
            return
            
        version = match.group(1)
        log(f"开始下载Java版本: {version}")
        
        # 创建进度提示
        teaching_tip = TeachingTip(
            title=f"正在下载 Java {version}",
            content=i18nText("下载过程可能需要几分钟，请耐心等待..."),
            parent=self,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=-1,  # 不自动关闭
            isClosable=False
        )
        teaching_tip.show()
        
        # TODO: 实现Java版本下载逻辑
        # 临时实现，仅显示提示
        InfoBar.warning(
            title=i18nText('⚠️ 功能开发中'),
            content=f"Java {version} 下载功能正在开发中",
            parent=self,
            duration=3000
        )
        teaching_tip.close()
    
    def on_minecraft_download_finished(self, success, version, teaching_tip):
        """Minecraft下载完成回调"""
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
            
        if success:
            log(f"Minecraft版本 {version} 已成功下载")
            InfoBar.success(
                title=i18nText('✅ 下载成功'),
                content=f"Minecraft版本 {version} 已成功下载并安装",
                parent=self,
                duration=5000
            )
        else:
            log(f"Minecraft版本 {version} 下载失败")
            InfoBar.error(
                title=i18nText('❌ 下载失败'),
                content=f"Minecraft版本 {version} 下载失败，请查看日志了解详情",
                parent=self,
                duration=5000
            )
    
    def on_download_finished(self, teaching_tip, download_button):
        if hasattr(self, 'version'):
            log(f"版本 {self.version} 已成功下载")
        else:
            log(i18nText("下载完成，但版本信息缺失"))

        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        if download_button:
            InfoBar.success(
                title=i18nText('✅ 下载完成'),
                content=f"版本 {self.version if hasattr(self, 'version') else '未知'} 已成功下载\n前往主页就可以启动了！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        self.run_cmcl_list(True)
        # 拷贝 servers.dat 文件到 .minecraft 文件夹
        src_file = os.path.join(os.getcwd(), "servers.dat")
        dest_dir = os.path.join(os.getcwd(), ".minecraft")
        if os.path.exists(src_file):
            try:
                shutil.copy(src_file, dest_dir)
                log(f"成功拷贝 {src_file} 到 {dest_dir}")
            except Exception as e:
                handle_exception(e)
                log(f"拷贝 {src_file} 到 {dest_dir} 失败: {e}", logging.ERROR)
        self.is_running = False  # 重置标志变量
        # 发送系统通知
        QTimer.singleShot(0, lambda: self.send_system_notification(i18nText("下载完成"), f"版本 {self.version} 已成功下载"))
        # 检查 NoneType 错误
        if self.show_text is not None:
            self.show_text.setText(i18nText("下载完成"))
        else:
            log("show_text is None", logging.ERROR)
        self.run_cmcl_list(True)
    def run_cmcl_list(self,back_set_list):
        # 移除 minecraft_list, customize_list 的 global 声明，改用 BLglobals
        
        try:
            versions_path = os.path.join(self.config['minecraft_dir'], "versions")
            temp_list = []  # 使用临时变量
            
            if os.path.exists(versions_path) and os.path.isdir(versions_path):
                temp_list = [d for d in os.listdir(versions_path)
                            if os.path.isdir(os.path.join(versions_path, d))]
                
                if not temp_list:
                    # 注意：这里逻辑有点奇怪，如果为空返回提示文本，但这会污染列表类型
                    # 建议保持为空列表，在 UI 层处理提示
                    # 为了兼容现有逻辑，我们暂且保留，但要注意
                    # temp_list = []
                    # temp_list.append(i18nText("你还未安装任何版本哦，请前往下载页面安装"))
                    log(f"版本目录为空: {versions_path}")
                else:
                    log(f"成功读取版本列表: {temp_list}")
            else:
                # 同上
                # temp_list = []
                # temp_list.append(i18nText("你还未安装任何版本哦，请前往下载页面安装"))
                log(f"路径无效: {versions_path}")
                
            BLglobals.set_list = temp_list  # 最后统一赋值给全局变量

            # --- 修改：存入 BLglobals ---
            BLglobals.minecraft_list = temp_list 
            log(f"Minecraft 版本列表: {BLglobals.minecraft_list}")

            if "Customize" in self.config:
                BLglobals.customize_list = [item.get("showname") for item in self.config["Customize"]]
            else:
                BLglobals.customize_list = []
                
            log(f"Customize 列表中的 showname 值: {BLglobals.customize_list}")
            
            # 合并
            BLglobals.set_list = BLglobals.minecraft_list + BLglobals.customize_list
            log(f"合并后的版本列表: {BLglobals.set_list}")

            self.update_version_combobox()  # 新增UI更新方法
            if back_set_list:
                return BLglobals.set_list
            else:
                return BLglobals.customize_list
        except Exception as e:
            # handle_exception(e)
            log(f"读取版本列表失败: {e}", logging.ERROR)
            BLglobals.set_list = []
            # 异常情况下给默认空值
            BLglobals.minecraft_list = []
            BLglobals.customize_list = []
            # BLglobals.set_list.append(i18nText("你还未安装任何版本哦，请前往下载页面安装"))
   
    def run_cmcl(self, version, HomePage=None):
        log(f"minecraft_list:{GetMinecraftList()}")
        if version not in BLglobals.minecraft_list:
            CustomizeRun(self,version)
        else:
            # 检查 config.json 中是否有账户信息
            try:
                config_data = cfg.read()
                mc_account = config_data.get("MinecraftAccount", {})
                accounts = mc_account.get("accounts", [])
                
                # 如果 accounts 列表为空，提示用户登录
                if not accounts:
                    msg_box = MessageBox(
                        i18nText('您当前尚未登录'),
                        i18nText('Minecraft 还不知道您是谁，无法启动。请先登录，确认以转到通行证页面。'),
                        self
                    )
                    if msg_box.exec_():
                        # 切换到通行证页面
                        self.switchTo(self.passportInterface)
                    return
            except Exception as e:
                handle_exception(e)
                log(f"检查账户信息时出错: {e}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('❌ 错误'),
                    content=i18nText('检查账户信息时发生错误'),
                    parent=self,
                    duration=3000
                )
                return
            
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
            log(f"正在启动 {version}")
            
            # 在启动时添加TabBar标签
            if HomePage:
                try:
                    # 获取TabBar组件
                    minecraft_tab = HomePage.findChild(TabBar, "MinecraftTab")
                    if minecraft_tab and hasattr(minecraft_tab, 'addTab'):
                        try:
                            # 启用关闭按钮
                            minecraft_tab.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
                            minecraft_tab.show()
                            
                            # 添加标签
                            minecraft_tab.addTab(
                                routeKey=version,
                                text=version,
                                icon="ui/icon/Grass_Block.png",
                                onClick=lambda: log(f"点击了标签: {version}")
                            )
                            
                            # 连接关闭信号（如果尚未连接）
                            if not hasattr(self, '_tab_close_connected'):
                                minecraft_tab.tabCloseRequested.connect(self.on_tab_close_requested)
                                self._tab_close_connected = True
                                self.minecraft_tab = minecraft_tab

                            log(f"启动时已向 MinecraftTab 添加标签: {version}")
                        except Exception as e:
                            log(f"启动时添加标签到 MinecraftTab 失败: {e}")
                    else:
                        log(f"启动时未找到 MinecraftTab 组件或组件不支持 addTab 方法")
                except Exception as e:
                    log(f"启动时添加标签时出错: {e}")
            
            if os.path.exists("run.bat"):
                os.remove("run.bat")
            
            log(f"传递给 Get_Run_Script 的版本: {version}")
            
            try:
                # 获取启动脚本内容 (Get_Run_Script 内部会读取 config.json 获取账户信息)
                script_content = Get_Run_Script(version)
                with open("run.bat", "w", encoding="utf-8") as f:
                    f.write(script_content)
            except Exception as e:
                log(f"生成启动脚本失败: {e}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('❌ 启动错误'),
                    content=f"生成启动配置失败: {e}",
                    parent=self,
                    duration=5000
                )
                self.is_running = False
                return

            run_button = self.sender()  # 获取按钮对象（可能为 None）
            if run_button is not None:
                teaching_tip = TeachingTip.create(
                    target=run_button,
                    icon=InfoBarIcon.SUCCESS,
                    title=f'正在启动 {version}',
                    content=i18nText("请稍等"),
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=0,  # 设置为0表示不自动关闭
                    parent=self
                )
                if teaching_tip:
                    teaching_tip.move(run_button.mapToGlobal(run_button.rect().topLeft()))
            else:
                log(i18nText("托盘菜单启动，不显示 TeachingTip"))
                teaching_tip = None # 确保变量已定义

            # 线程
            self.run_script_thread = RunScriptThread()
            self.run_script_thread.version = version  # 设置版本信息
            self.run_script_thread.finished.connect(lambda: self.on_run_script_finished(None, run_button, version))
            self.run_script_thread.error_occurred.connect(lambda error: self.on_run_script_error(error, None, run_button))
            self.run_script_thread.start()
            self.threads.append(self.run_script_thread)
            
            # 跟踪运行中的进程
            self.running_processes[version] = self.run_script_thread
            
            # 启动 Minecraft 窗口监控 (使用 mwtool)
            if self.config.get('mwtool_switch_open', True):
                try:
                    log(f"启动工具栏监视器，目标版本: {version}")
                    modules.mwtool.start_monitoring(version)
                except Exception as e:
                    log(f"启动工具栏监视器失败: {e}", logging.ERROR)
            else:
                log("mwtool 窗口监视功能已禁用")

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
                unique_versions = list(dict.fromkeys(BLglobals.set_list))  # 保持顺序去重
                current_text = run_choose.currentText()  # 保留当前选中项
                
                run_choose.clear()
                run_choose.addItems(unique_versions)
                
                # 恢复选中项或默认选择
                if current_text in unique_versions:
                    run_choose.setCurrentText(current_text)
                elif unique_versions:
                    run_choose.setCurrentIndex(0)
    def closeEvent(self, event):
        """ 隐藏窗口而不是退出程序 """
        event.ignore()  # 忽略关闭事件
        self.hide()  # 隐藏窗口
    def on_download_clicked(self):
        log(i18nText("下载 被点击"))
        load_ui("ui/download.old.ui", animate=False)
        setup_download_old_ui(self,self.content_layout.itemAt(0).widget(),LM_Download_Way_list,BLglobals.ver_id_bloret,self.homeInterface)
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
    def on_customize_choose_clicked(self, widget):
        Customize_path = widget.findChild(LineEdit, "Customize_path")
        Customize_showname = widget.findChild(LineEdit, "Customize_showname")
        # Customize_icon = widget.findChild(QLabel, "Customize_icon")
        Customize_choose_path, _ = QFileDialog.getOpenFileName(self, i18nText("选择文件"), os.getcwd(), i18nText("所有文件 (*.*)"))
        if Customize_choose_path:
            Customize_path.setText(Customize_choose_path)
            Customize_showname.setText(os.path.splitext(os.path.basename(Customize_choose_path))[0])
            # icon = QIcon(Customize_choose_path)
            # if not icon.isNull():
            #     Customize_icon.setPixmap(icon.pixmap(64, 64))  # 设置图标大小为 64x64
            # else:
            #     Customize_icon.setText("无法加载图标")
            # self.showTeachingTip(Customize_showname, Customize_choose_path)
    def on_customize_add_clicked(self, widget, homeInterface):
        Customize_path = widget.findChild(LineEdit, "Customize_path")
        Customize_showname = widget.findChild(LineEdit, "Customize_showname")
        Customize_path_value = Customize_path.text()
        Customize_showname_value = Customize_showname.text()
        log(f"Customize Path: {Customize_path_value}, Customize Show Name: {Customize_showname_value}")
        if not Customize_path_value or not Customize_showname_value:
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=i18nText("路径或显示名称不能为空"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return

        if not os.path.exists(Customize_path_value):
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("指定的路径不存在，请重新选择"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return

        if not os.path.isfile(Customize_path_value):
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("指定的路径不是文件，请重新选择"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        # Save to config.json
        try:
            with open(BLglobals.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []

            config_data["Customize"].append({
                "showname": Customize_showname_value,
                "path": Customize_path_value
            })

            with open(BLglobals.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
            self.config = config_data  # 同步到 self.config
            InfoBar.success(
                title=i18nText('✅ 成功'),
                content=f"路径 {Customize_path_value} 和显示名称 {Customize_showname_value} 已成功保存",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            run_choose = homeInterface.findChild(ComboBox, "run_choose")
            run_choose.clear()
            run_choose.addItems(self.run_cmcl_list(True))
            
        except Exception as e:
            handle_exception(e)
            InfoBar.error(
                title=i18nText('❌ 错误'),
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
                title=i18nText('⏱️ 正在加载'),
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
            title=i18nText('错误'),
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
            log(f"目标小部件已被删除，无法显示 TeachingTip", logging.ERROR)
            return
        InfoBar.success(
            title=i18nText('✅ 提示'),
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
                    BLglobals.ver_id_main.clear()
                    BLglobals.ver_id_short.clear()
                    BLglobals.ver_id_long.clear()
                    for version in versions:
                        if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                            BLglobals.ver_id_main.append(version["id"])
                        else:
                            if version["type"] == "snapshot":
                                BLglobals.ver_id_short.append(version["id"])
                            elif version["type"] in ["old_alpha", "old_beta"]:
                                BLglobals.ver_id_long.append(version["id"])
            
                    # 更新UI中的minecraft_choose下拉框
                    minecraft_choose.clear()
                    if version_type == i18nText("百络谷支持版本"):
                        # 确保ver_id_bloret不为None且不为空
                        if BLglobals.ver_id_bloret is not None and len(BLglobals.ver_id_bloret) > 0:
                            minecraft_choose.addItems(BLglobals.ver_id_bloret)
                        else:
                            # 如果ver_id_bloret为空，则添加默认版本列表
                            minecraft_choose.addItems(["1.21.7", "1.21.8"])
                    elif version_type == i18nText("正式版本"):
                        minecraft_choose.addItems(BLglobals.ver_id_main)
                    elif version_type == i18nText("快照版本"):
                        minecraft_choose.addItems(BLglobals.ver_id_short)
                    elif version_type == i18nText("远古版本"):
                        minecraft_choose.addItems(BLglobals.ver_id_long)
                    else:
                        log(i18nText("未知的版本类型"), logging.ERROR)
            
                    log(f"最新发布版本: {latest_release}")
                    log(f"最新快照版本: {latest_snapshot}")
                    log(i18nText("Minecraft 版本列表已更新"))
                else:
                    log(i18nText("无法获取 Minecraft 版本列表"), logging.ERROR)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {e}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('提示'),
                    content=i18nText("无法连接到服务器，请检查网络连接或稍后再试。"),
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            except requests.exceptions.SSLError as e:
                log(f"SSL 错误: {e}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('提示'),
                    content=i18nText("无法连接到服务器，请检查网络连接或稍后再试。"),
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
                    title=i18nText("非法名称"),
                    content=i18nText("名称包含非法字符或中文，请遵循以下规则：\n1. 不能包含 \\ / : * ? \" < > |\n2. 不能包含中文\n3. 不能使用系统保留名称"),
                    parent=self
                )
                msg.exec()
                return
    
        if minecraft_choose and download_button and fabric_choose:
            cmcl_save_path = os.path.join(os.getcwd(), "cmcl_save.json")
            cmcl_path = os.path.join(os.getcwd(), "cmcl.exe")
    
            if not os.path.isfile(cmcl_path):
                log(f"文件 {cmcl_path} 不存在", logging.ERROR)
                QMessageBox.critical(self, i18nText("错误"), f"文件 {cmcl_path} 不存在")
                return
            
            choose_ver = minecraft_choose.currentText()
            self.version = choose_ver
            fabric_download = fabric_choose.currentText()
    
            InfoBar.success(
                title=i18nText('⬇️ 正在下载'),
                content=f"正在下载你所选的版本...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
            download_button.setText(i18nText("已经开始下载...下载状态将会显示在这里"))
    
            download_way_choose = widget.findChild(ComboBox, "download_way_choose")
            selected_way = download_way_choose.currentText()
    
            # 定义 teaching_tip 变量
            teaching_tip = None
    
            if selected_way == "Bloret Launcher":  # Bloret Launcher 方法
                log(f"LM_Download_Way_minecraft:{LM_Download_Way_minecraft}")
                LM_download_way_choose = widget.findChild(ComboBox, "LM_download_way_choose")
                BL_download(self, choose_ver, LM_download_way_choose.currentText(), LM_Download_Way_minecraft, LM_Download_Way_version, self)
                self.on_download_finished(teaching_tip, download_button)
            else:  # CMCL 方法
                if fabric_download != i18nText("不安装"):
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername} --fabric={fabric_download}"
                else:
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername}"
        
                log(f"下载命令: {command}")
        
                self.download_thread = self.DownloadThread(cmcl_path, command, log)
                self.threads.append(self.download_thread)
                self.download_thread.output_received.connect(self.log_output)
                self.download_thread.output_received.connect(lambda text: download_button.setText(text[:70] + '...' if len(text) > 70 else text))
                
                teaching_tip = InfoBar(
                    icon=InfoBarIcon.SUCCESS,
                    title=i18nText('✅ 正在下载'),
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
                log(f"正在下载版本 {self.version}")
                log(i18nText("执行命令: ") + f"{self.version}")
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
                    if i18nText("该名称已存在，请更换一个名称。") in line:
                        self.error_occurred.emit(i18nText("该版本已下载过。"))
                        process.terminate()
                        return
                    self.output_received.emit(line.strip())
                    log(line.strip())  # 将输出存入日志
                while process.poll() is None:
                    self.output_received.emit(i18nText("正在下载并安装"))
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
                    toast(title, message, duration="short", icon={'src': 'bloret.ico','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
            except Exception as e:
                handle_exception(e)
                log(f"发送系统通知失败: {e}", logging.ERROR)
    class MicrosoftLoginThread(QThread):
        finished = pyqtSignal(bool, str)
        
        def __init__(self):
            super().__init__()
            self.log_method = None
            
        def run(self):
            # 执行微软登录命令
            log(i18nText("正在执行微软登录命令：cmcl account --login=microsoft"))
            process = subprocess.Popen(["cmcl", "account", "--login=microsoft"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    encoding='utf-8')

            process.wait()
            
            if process.returncode == 0:
                self.finished.emit(True, i18nText("登录成功"))
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
                    self.finished.emit(True, i18nText("离线登录成功"))
                else:
                    error = process.stderr.read()
                    self.finished.emit(False, f"登录失败: {error}")
            except Exception as e:
                handle_exception(e)
                self.finished.emit(False, f"执行异常: {str(e)}")
    class MessageBox(MessageBoxBase):
        def __init__(self, title, content, parent=None):
            super().__init__(parent)
            self.name_edit = LineEdit()
            self.viewLayout.addWidget(SubtitleLabel(title))
            self.viewLayout.addWidget(StrongBodyLabel(content))
            self.viewLayout.addWidget(self.name_edit)
            self.widget.setMinimumWidth(300)
    class CustomMessageBox(MessageBoxBase):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.titleLabel = SubtitleLabel(i18nText('离线登录'))
            self.usernameLineEdit = LineEdit()

            self.usernameLineEdit.setPlaceholderText(i18nText('请输入玩家名称'))
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
        if login_way_choose.currentText() == i18nText("离线登录"):
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
                    handle_exception(e)
                    self.show_error(i18nText("文件操作失败"), f"无法覆盖cmcl.json: {str(e)}")
        elif login_way_choose.currentText() == i18nText("微软登录"):
            if not config.get('localmod', False):
                login_way_choose = widget.findChild(ComboBox, "login_way")
                if not login_way_choose or login_way_choose.currentText() != i18nText("微软登录"):
                    return

                # 覆盖cmcl.json
                try:
                    shutil.copyfile('cmcl.blank.json', 'cmcl.json')
                    log(i18nText("成功覆盖 cmcl.json 文件"))
                except Exception as e:
                    handle_exception(e)
                    self.show_error(i18nText("文件操作失败"), f"无法覆盖cmcl.json: {str(e)}")
                    return

                # 创建并启动登录线程
                self.microsoft_login_thread = self.MicrosoftLoginThread()
                self.microsoft_login_thread.log_method = log
                self.microsoft_login_thread.finished.connect(
                    lambda success, msg: self.on_login_finished(widget, success, msg)
                )
                
                # 显示加载提示
                self.login_tip = InfoBar(
                    icon=InfoBarIcon.WARNING,
                    title=i18nText('⏱️ 正在登录微软账户'),
                    content=i18nText('请按照浏览器中的提示完成登录...'),
                    isClosable=True,  # 允许用户手动关闭
                    position=InfoBarPosition.TOP,
                    duration=5000,  # 设置自动关闭时间
                    parent=self
                )
                self.login_tip.show()
                
                self.microsoft_login_thread.start()
            
            else:
                log(i18nText("本地模式已启用，无法使用微软登录。"))
                w = Dialog(i18nText("您已启用本地模式"), i18nText("Bloret Launcher 在本地模式下无法进行微软登录，\n因为该操作需要互联网\n如果需要登录，请到设置界面关闭本地模式。或使用离线登录。"))
                if w.exec():
                    print(i18nText('确认'))
                else:
                    print(i18nText('取消'))
    def on_login_finished(self, widget, success, message):
        # 添加有效性检查
        if hasattr(self, 'login_tip') and self.login_tip and not sip.isdeleted(self.login_tip):
            try:
                self.login_tip.close()
            except RuntimeError:
                pass  # 如果对象已被销毁则忽略异常
        
        # 处理结果
        if success:
            self.update_passport_ui(widget)
            InfoBar.success(
                title=i18nText('✅ 登录成功'),
                content=i18nText('登录成功'),
                parent=self
            )
        else:
            InfoBar.error(
                title=i18nText('❎ 登录失败'),
                content=message,
                parent=self
            )
    def update_passport_ui(self, widget):
        # 更新UI显示
        login_way_combo = widget.findChild(ComboBox, "player_login_way")
        name_combo = widget.findChild(ComboBox, "playername")
        
        if self.cmcl_data:
            # 更新登录方式
            login_method = self.login_mod
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
                toast(title, message, duration="short", icon={'src': 'bloret.ico','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
            elif sys.platform == "darwin":
                subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
            else:
                subprocess.run(["notify-send", title, message])
        except Exception as e:
            handle_exception(e)
            log(f"发送系统通知失败: {e}", logging.ERROR)
    def on_download_error(self, error_message, teaching_tip, download_button):
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        TeachingTip.create(
            target=download_button,
            icon=InfoBarIcon.ERROR,
            title=i18nText('❎ 提示'),
            content=f"下载失败，原因：{error_message}",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=5000,
            parent=self
        )
        self.is_running = False  # 重置标志变量

    def animate_sidebar(self):
        start_geometry = self.navigationInterface.geometry()
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


    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def save_config(self):
        """ 将当前内存中的配置保存到磁盘并刷新缓存 """
        try:
            if hasattr(self, 'config'):
                # 1. 防止覆盖：先从磁盘读取最新配置（获取 web.py 或其他模块写入的 Passport 信息）
                try:
                    if os.path.exists(BLglobals.config_path):
                        with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                            disk_config = json.load(f)
                        
                        # 定义需要从磁盘同步到内存的关键字段 (Passport 和 账户信息)
                        # 这些字段通常由 web.py 或 sync 模块在后台修改
                        sync_keys = [
                            'Bloret_PassPort_Login', 
                            'Bloret_PassPort_UserName', 
                            'Bloret_PassPort_PassWord',
                            'MinecraftAccount'
                        ]
                        
                        for key in sync_keys:
                            if key in disk_config:
                                self.config[key] = disk_config[key]
                                log(f"save_config: 已从磁盘同步最新字段 {key}")
                except Exception as e:
                    log(f"保存前同步磁盘配置失败: {e}", logging.ERROR)

                # 2. 保存合并后的配置
                with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                log("配置文件已成功保存到磁盘")
        except Exception as e:
            log(f"保存配置文件失败: {e}", logging.ERROR)

    def load_config(self):
        """ 从磁盘重新加载配置到内存（用于外部模块修改文件后的同步） """
        try:
            if os.path.exists(BLglobals.config_path):
                with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                log("配置已从磁盘重新加载")
        except Exception as e:
            log(f"加载配置文件失败: {e}", logging.ERROR)

    def quit_app(self):
        """ 安全退出程序 """
        self.save_config()
        if self.mutex:
            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None
        os._exit(0)

    def restart_app(self):
        """ 安全重启程序 """
        log(i18nText('正在准备重启程序...'))
        self.save_config()
        if self.mutex:
            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None
        
        # 判断是否为 PyInstaller 打包后的环境
        if getattr(sys, 'frozen', False):
            # 打包环境下，sys.executable 是 exe 路径，sys.argv[0] 也是 exe 路径
            # 我们只需要取 sys.executable 加上剩余的参数
            args = [sys.executable] + sys.argv[1:]
        else:
            # 脚本环境下，sys.executable 是 python.exe，sys.argv[0] 是脚本路径
            args = [sys.executable] + sys.argv

        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS, shell=False)
        os._exit(0)
        
    def on_player_name_set_clicked(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "player_name")
        player_name = player_name_edit.text()

        if not player_name:
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=i18nText("请填写值后设定"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        elif any('\u4e00' <= char <= '\u9fff' for char in player_name):
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=i18nText("名称不能包含中文"),
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

    def log_output(self, output):
        if output:
            log(output.strip())
    def on_tab_close_requested(self, index):
        """处理TabBar关闭按钮点击事件"""
        try:
            
            if self.minecraft_tab and isinstance(self.minecraft_tab, TabBar):
                # 获取要关闭的标签的版本信息
                tab_item = self.minecraft_tab.tabItem(index)
                if tab_item:
                    version = tab_item.routeKey()
                    
                    # 检查是否有对应的运行进程
                    if version in self.running_processes:
                        run_thread = self.running_processes[version]
                        
                        # 确认对话框
                        w = MessageBox(
                            i18nText('确认关闭'),
                            i18nText(f'确定要关闭 Minecraft {version} 吗？'),
                            self
                        )
                        
                        if w.exec():
                            # 用户确认关闭
                            log(f"用户请求关闭 Minecraft {version}")
                            
                            # 终止进程
                            if run_thread.terminate_process():
                                # 从跟踪列表中移除
                                del self.running_processes[version]
                                
                                # 移除标签
                                self.minecraft_tab.removeTab(index)
                                
                                InfoBar.success(
                                    title=i18nText('✅ 已关闭'),
                                    content=i18nText(f"Minecraft {version} 已关闭"),
                                    isClosable=True,
                                    position=InfoBarPosition.TOP,
                                    duration=3000,
                                    parent=self
                                )
                            else:
                                InfoBar.error(
                                    title=i18nText('❌ 关闭失败'),
                                    content=i18nText(f"无法终止 Minecraft {version} 进程"),
                                    isClosable=True,
                                    position=InfoBarPosition.TOP,
                                    duration=5000,
                                    parent=self
                                )
                    else:
                        # 没有对应的进程，直接移除标签
                        self.minecraft_tab.removeTab(index)
                        log(f"移除了未运行状态的标签: {version}")
                        
        except Exception as e:
            log(f"处理标签关闭请求时出错: {e}")
            InfoBar.error(
                title=i18nText('❌ 错误'),
                content=i18nText("关闭标签时发生错误"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def on_run_script_finished(self, teaching_tip, run_button, version=None):
        try:
            modules.mwtool.hide_minecraft_tool()
            modules.mwtool.stop_monitoring()
        except Exception as e:
            log(f"停止工具栏失败: {e}")

        if self.update_show_text_thread:
            self.update_show_text_thread.terminate()  # 停止更新线程
            self.update_show_text_thread.wait()  # 确保线程完全停止
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()  # 关闭气泡消息
        
        # 从运行进程列表中移除
        if version and version in self.running_processes:
            del self.running_processes[version]
        
        InfoBar.success(
            title=i18nText('⏹️ 游戏结束'),
            content=i18nText("Minecraft 已结束\n如果您认为是异常退出，请查看 log 文件夹中的最后一份日志文件\n并前往本项目的 Github 或 百络谷QQ群 询问"),
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.is_running = False  # 重置标志变量

        QApplication.processEvents()  # 处理所有挂起的事件
        time.sleep(1)  # 等待1秒确保所有事件处理完毕

    def on_run_script_error(self, error, teaching_tip, run_button):
        try:
            modules.mwtool.hide_minecraft_tool()
            modules.mwtool.stop_monitoring()
        except Exception:
            pass
        if self.update_show_text_thread:
            self.update_show_text_thread.terminate()  # 停止更新线程
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        InfoBar.error(
            title=i18nText('❌ 运行失败'),
            content=f"run.bat 运行失败: {error}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        log(f"run.bat 运行失败: {error}", logging.ERROR)
        self.is_running = False  # 重置标志变量

    def update_show_text(self, text):
        return

    def download_skin(self, widget):
        if self.player_skin:
            skin_url = self.player_skin
            skin_data = requests.get(skin_url).content
            with open("player_skin.png", "wb") as file:
                file.write(skin_data)
            log(f"皮肤已下载到 player_skin.png")
    def download_cape(self, widget):
        if self.player_cape:
            cape_url = self.player_cape
            cape_data = requests.get(cape_url).content
            with open("player_cape.png", "wb") as file:
                file.write(cape_data)
            log(f"披风已下载到 player_cape.png")
    def on_light_dark_changed(self, mode):
        if mode == i18nText("跟随系统"):
            self.apply_theme()
        elif mode == i18nText("深色模式"):
            self.apply_theme(QPalette(QColor("#2e2e2e")))
        elif mode == i18nText("浅色模式"):
            self.apply_theme(QPalette(QColor("#ffffff")))
    def update_log_clear_button_text(self, button):
        log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
        if os.path.exists(log_folder) and os.path.isdir(log_folder):
            log_files = os.listdir(log_folder)
            log_file_count = len(log_files)
            total_size = sum(os.path.getsize(os.path.join(log_folder, f)) for f in log_files)
            if log_file_count-1 <= 0:
                button.setText(i18nText("没有日志可以清空了"))
                button.setEnabled(False)
            else:
                button.setText(f"清空 {log_file_count-1} 个日志，总计 {total_size // 1024} KB")
        else:
            button.setText(i18nText("清空日志"))
# 初始化配置文件
with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 获取系统深浅色主题
isdarktheme = is_dark_theme()
log(f"当前主题:{isdarktheme}")

# 添加语言切换功能
# def switch_language(locale):
#     global translator
#     app.removeTranslator(translator)  # 移除当前翻译器
#     translator = FluentTranslator(locale)
#     app.installTranslator(translator)
#     window.retranslateUi()  # 重新翻译 UI

# 设置语言
# language = config.get('language', 'zh-cn')
# if language != 'zh-cn':
#     switch_language(QLocale(language))

if not config.get('localmod', False):
    check_Light_Minecraft_Download_Way(BLglobals.server_ip, update_download_way)
else:
    log(i18nText("本地模式已启用，获取 Light-Minecraft-Download-Way 的过程已跳过。"))

# 适配高DPI缩放
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)


# 创建 QApplication 实例
app = QApplication(["Bloret Launcher"])

# # 初始化 FluentTranslator
# translator = FluentTranslator()
# app.installTranslator(translator)

# 默认语言跟随系统语言
# current_locale = QLocale.system()

# # 添加语言切换功能
# def switch_language(locale):
#     global translator
#     app.removeTranslator(translator)  # 移除当前翻译器
#     translator = FluentTranslator(locale)
#     app.installTranslator(translator)
#     window.retranslateUi()  # 重新翻译 UI


# 检查写入权限
if not check_write_permission():
    w = Dialog(i18nText("Bloret Launcher 无法写入文件"), i18nText("Bloret Launcher 需要在安装文件夹写入文件，但是我们在多次尝试后仍无法正常写入文件\n这可能是由于安装文件夹是只读的。\n请考虑将百络谷启动器安装在非 Program Files , Program Files (x86) 等只读的文件夹\n由于没有写入权限，百络谷启动器将退出。"))
    if w.exec():
        print(i18nText('确认'))
    else:
        print(i18nText('取消'))
    sys.exit(0)

# 创建主窗口并显示
window = MainWindow()

# 如果启动参数包含 --self-starting，则不显示窗口
if '--self-starting' in sys.argv:
    window.hide()  # 直接隐藏主窗口
else:
    window.show()  # 否则正常显示主窗口

scale_factor = window.scale_factor
os.environ["QT_SCALE_FACTOR"] = str(scale_factor)

# 运行应用程序
sys.exit(app.exec())