from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, QPushButton, QWidget, QLineEdit, QLabel, QFileDialog, QMessageBox
from qfluentwidgets import MessageBox, SubtitleLabel, MessageBoxBase, NavigationItemPosition, TeachingTip, InfoBarIcon, TeachingTipTailPosition, ComboBox, InfoBar, InfoBarPosition, FluentWindow, SplashScreen, Dialog, LineEdit, SystemTrayMenu, Action, setThemeColor, FluentTranslator, FluentIcon
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, QSettings, QThread, pyqtSignal, Qt, QTimer, QSize, QLocale
from modules.win11toast import toast, notify, update_progress
import ctypes, re, locale, sys, logging, os, requests, json, subprocess, time, shutil, send2trash
import sip # type: ignore
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
from modules.systems import get_system_theme_color,is_dark_theme,check_write_permission,restart
from modules.setup_ui import setup_home_ui,setup_download_ui,setup_tools_ui,setup_passport_ui,setup_settings_ui,setup_info_ui,load_ui,setup_version_ui
from modules.customize import CustomizeRun,find_Customize
from modules.BLServer import check_Light_Minecraft_Download_Way,handle_first_run,check_Bloret_version,check_for_updates
from modules.links import open_BBBS_link
from modules.BLDownload import BL_download
# 全局变量
server_ip = "http://pcfs.top:2/" # Bloret Launcher Server 服务器地址 （尾部带斜杠）
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
icon = {'src': 'bloret.ico','placement': 'appLogoOverride'}
minecraft_list = []
tabbar = None
isdarktheme = False
LM_Download_Way = {}
LM_Download_Way_list = []
LM_Download_Way_version = {}
LM_Download_Way_minecraft = {}

class SystemTrayIcon(QSystemTrayIcon):
    """ 
    系统托盘图标 
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if parent is None:
            print("警告：SystemTrayIcon 的 parent 参数为 None")
        self.setIcon(QIcon('bloret.ico'))  # 设置托盘图标
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
            Action('🔡  访问 BBS', triggered=lambda: open_BBBS_link(server_ip)),
            Action('🔄️  重启程序', triggered=lambda: restart()),
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
                errors='replace',  # 此处统一处理解码错误
                creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏控制台窗口
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
        super().__init__()

        # 初始化配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

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
        if sys.platform == "win32":
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\BloretLauncherMutex")
            if mutex == 0:
                log("创建互斥体失败")
                sys.exit(1)
            error = ctypes.windll.kernel32.GetLastError()
            if error == 183:  # ERROR_ALREADY_EXISTS
                log("检测到程序重复运行")
                if not self.config.get('repeat_run', False):
                    log("重复运行被禁用：检测到程序已运行，退出新实例")
                    # 显示通知
                    notify(progress={
                        'title': f'Bloret Launcher 已阻止了重复打开软件的操作',
                        'body': '为了防止 Bloret Launcher 占满您的计算机，我们已阻止您重复打开 Bloret Launcher\n如需重复打开，请到设置中勾选允许重复运行。',
                        'icon': os.path.join(os.getcwd(), 'bloret.ico')
                    })
                    w = Dialog("Bloret Launcher 已阻止了重复打开软件的操作", "为了防止 Bloret Launcher 占满您的计算机，我们已阻止您重复打开 Bloret Launcher\n如需重复打开，请到设置中勾选允许重复运行。")
                    if w.exec():
                        print('确认')
                    ctypes.windll.kernel32.CloseHandle(mutex)
                    sys.exit(0)

        if self.config.get('show_runtime_do', False):
            log("显示软件打开过程已启用")
            # 显示通知
            notify(progress={
                'title': '正在启动 Bloret Launcher',
                'status': '正在做打开软件前的工作...',
                'value': '0',
                'valueStringOverride': '0%',
                'icon': os.path.join(os.getcwd(), 'bloret.ico')
            })
        else:
            log("显示软件打开过程已禁用")



        # 设置全局编码
        codec = locale.getpreferredencoding()
        if sys.stdout:
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8')

        # 1. 创建启动页面
        update_progress({'value': 10 / 100, 'valueStringOverride': '1/10', 'status': '创建启动页面'})
        icon_path = os.path.join(os.getcwd(), 'bloret.ico')
        if os.path.exists(icon_path):
            log(f"图标路径存在: {icon_path}")
        else:
            log(f"图标路径不存在: {icon_path}", logging.ERROR)
        self.splashScreen = SplashScreen(QIcon(icon_path), self)
        log("启动画面创建完成")
        self.splashScreen.setIconSize(QSize(102, 102))
        self.splashScreen.setWindowTitle("Bloret Launcher")
        self.splashScreen.setWindowIcon(QIcon(icon_path))
        
        # 2. 在创建其他子页面前先显示主界面
        update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': '连接服务器'})
        self.splashScreen.show()
        log("启动画面已显示")

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
        handle_first_run(self,server_ip)
        check_for_updates(self,server_ip)
        global ver_id_bloret
        ver_id_bloret = check_Bloret_version(self, server_ip, ver_id_bloret)
        

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
        QTimer.singleShot(0, lambda: handle_first_run(self,server_ip))
        
        # 隐藏启动页面
        update_progress({'value': 80 / 100, 'valueStringOverride': '8/10', 'status': '隐藏启动页面'})
        QTimer.singleShot(3000, lambda: (log("隐藏启动画面"), self.splashScreen.finish()))

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
    def load_cmcl_data(self):
        log(f"开始向 cmcl.json 读取数据")
        try:
            with open('cmcl.json', 'r', encoding='utf-8') as file:
                self.cmcl_data = json.load(file)
            
            # 添加对空accounts列表的检查
            if not self.cmcl_data.get('accounts'):
                self.player_name = "未登录"
                self.login_mod = "请在下方登录"
                log("cmcl.json 中的 accounts 列表为空")
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

            log(f"读取到的 playerName: {self.player_name}")
            log(f"读取到的 loginMethod: {self.login_mod}")
            return self.player_name
            # self.refresh_home_minecraft_account(self.player_name)
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            log(f"读取 cmcl.json 失败: {e}", logging.ERROR)
            self.cmcl_data = None
            # 设置默认值
            self.player_name = "未登录"
            self.login_mod = "请在下方登录"
        except Exception as e:
            handle_exception(e)
            log(f"其他错误: {e}", logging.ERROR)
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
        self.versionInterface = QWidget()
        self.homeInterface.setObjectName("home")
        self.downloadInterface.setObjectName("download")
        self.toolsInterface.setObjectName("tools")
        self.passportInterface.setObjectName("passport")
        self.settingsInterface.setObjectName("settings")
        self.infoInterface.setObjectName("info")
        self.versionInterface.setObjectName("version")
        self.addSubInterface(self.homeInterface, QIcon("bloret.ico"), "主页")
        self.addSubInterface(self.downloadInterface, FluentIcon.DOWNLOAD, "下载")
        self.addSubInterface(self.toolsInterface, FluentIcon.DEVELOPER_TOOLS, "工具")
        self.addSubInterface(self.passportInterface, FluentIcon.FINGERPRINT, "通行证", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.infoInterface, FluentIcon.INFO, "关于", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.versionInterface, FluentIcon.APPLICATION, "版本管理")
        load_ui("ui/home.ui", parent=self.homeInterface)
        load_ui("ui/download.ui", parent=self.downloadInterface)
        load_ui("ui/tools.ui", parent=self.toolsInterface)
        load_ui("ui/passport.ui", parent=self.passportInterface)
        load_ui("ui/settings.ui", parent=self.settingsInterface)
        load_ui("ui/info.ui", parent=self.infoInterface)
        load_ui("ui/version.ui", parent=self.versionInterface)
        setup_home_ui(self,self.homeInterface)
        setup_download_ui(self,self.downloadInterface,LM_Download_Way_list,ver_id_bloret)
        setup_tools_ui(self,self.toolsInterface)
        setup_passport_ui(self,self.passportInterface,server_ip)
        setup_settings_ui(self,self.settingsInterface)
        setup_version_ui(self,self.versionInterface,minecraft_list,customize_list)
        setup_info_ui(self,self.infoInterface)
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
        else:
            log("NavigationInterface does not support setCollapseWidth", logging.ERROR)
        if hasattr(self.navigationInterface, 'collapse'):
            self.navigationInterface.collapse(useAni=False)  # 默认收缩
        else:
            log("NavigationInterface does not support collapse", logging.ERROR)

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
        log("主页 被点击")
        self.switchTo(self.homeInterface)
    def on_download_finished(self, teaching_tip, download_button):
        if hasattr(self, 'version'):
            log(f"版本 {self.version} 已成功下载")
        else:
            log("下载完成，但版本信息缺失")

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
                log(f"成功拷贝 {src_file} 到 {dest_dir}")
            except Exception as e:
                handle_exception(e)
                log(f"拷贝 {src_file} 到 {dest_dir} 失败: {e}", logging.ERROR)
        self.is_running = False  # 重置标志变量
        # 发送系统通知
        QTimer.singleShot(0, lambda: self.send_system_notification("下载完成", f"版本 {self.version} 已成功下载"))
        # 检查 NoneType 错误
        if self.show_text is not None:
            self.show_text.setText("下载完成")
        else:
            log("show_text is None", logging.ERROR)
        self.run_cmcl_list()
    def run_cmcl_list(self):
        global set_list,minecraft_list,customize_list  # 添加全局声明
        try:
            versions_path = os.path.join(os.getcwd(), ".minecraft", "versions")
            temp_list = []  # 使用临时变量
            
            if os.path.exists(versions_path) and os.path.isdir(versions_path):
                temp_list = [d for d in os.listdir(versions_path)
                            if os.path.isdir(os.path.join(versions_path, d))]
                
                if not temp_list:
                    temp_list = ["你还未安装任何版本哦，请前往下载页面安装"]
                    log(f"版本目录为空: {versions_path}")
                else:
                    log(f"成功读取版本列表: {temp_list}")
            else:
                temp_list = ["无法获取版本列表，可能是你还未安装任何版本，请前往下载页面安装"]
                log(f"路径无效: {versions_path}", logging.ERROR)
                
            set_list = temp_list  # 最后统一赋值给全局变量

            minecraft_list = temp_list # 保留原 Minecraft 版本列表备用
            log(f"Minecraft 版本列表: {minecraft_list}")

            if "Customize" in self.config:
                customize_list = [item.get("showname") for item in self.config["Customize"]]
            log(f"Customize 列表中的 showname 值: {customize_list}")
            set_list = temp_list + customize_list  # 合并 customize_list 到 set_list

            log(f"合并后的版本列表: {set_list}")

            self.update_version_combobox()  # 新增UI更新方法
            
        except Exception as e:
            handle_exception(e)
            log(f"读取版本列表失败: {e}", logging.ERROR)
            set_list = ["无法获取版本列表，可能是你还未安装任何版本，请前往下载页面安装"]
    def run_cmcl(self, version):
        log(f"minecraft_list:{minecraft_list}")
        if version not in minecraft_list:
            CustomizeRun(self,version)
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
            log(f"正在启动 {version}")
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
                log("托盘菜单启动，不显示 TeachingTip")

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
    def closeEvent(self, event):
        """ 隐藏窗口而不是退出程序 """
        event.ignore()  # 忽略关闭事件
        self.hide()  # 隐藏窗口
    def on_download_clicked(self):
        log("下载 被点击")
        load_ui("ui/download.ui", animate=False)
        setup_download_ui(self,self.content_layout.itemAt(0).widget(),LM_Download_Way_list,ver_id_bloret)
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
        log(f"Customize Path: {Customize_path_value}, Customize Show Name: {Customize_showname_value}")
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
            handle_exception(e)
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
            log(f"目标小部件已被删除，无法显示 TeachingTip", logging.ERROR)
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
                        log("未知的版本类型", logging.ERROR)
                    log(f"最新发布版本: {latest_release}")
                    log(f"最新快照版本: {latest_snapshot}")
                    log("Minecraft 版本列表已更新")
                else:
                    log("无法获取 Minecraft 版本列表", logging.ERROR)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {e}", logging.ERROR)
                InfoBar.error(
                    title='提示',
                    content="无法连接到服务器，请检查网络连接或稍后再试。",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            except requests.exceptions.SSLError as e:
                log(f"SSL 错误: {e}", logging.ERROR)
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
                log(f"文件 {cmcl_path} 不存在", logging.ERROR)
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
                BL_download(self, choose_ver, LM_download_way_choose.currentText(), LM_Download_Way_minecraft, LM_Download_Way_version, self)
                self.on_download_finished(teaching_tip, download_button)
            else:  # CMCL 方法
                if fabric_download != "不安装":
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername} --fabric={fabric_download}"
                else:
                    command = f"\"{cmcl_path}\" install {choose_ver} -n {vername}"
        
                log(f"下载命令: {command}")
        
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
    def delete_minecraft_version(self,version,versions):
        '''
        # 🚧TODO🚧

        ***

        删除指定的 Minecraft 版本文件夹
        :param version: 要删除的版本名称
        :param versions: 版本 ComboBox 控件

        ### 删除 `.minecraft/version/{version}` 文件夹
        最好移到回收站

        
        ***
        ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
        '''
        log(f"正在删除 Minecraft 版本：{version}")
        
        # 构建版本文件夹路径
        version_path = os.path.join(MINECRAFT_DIR, "versions", version)
        
        try:
            # 检查版本文件夹是否存在
            if os.path.exists(version_path) and os.path.isdir(version_path):
                # 删除版本文件夹
                send2trash.send2trash(version_path)
                log(f"成功删除版本文件夹：{version_path}")
                
                # 更新全局列表
                global set_list, minecraft_list
                set_list.remove(version)
                minecraft_list.remove(version)
                
                # 更新 UI 中的下拉列表
                if versions and not sip.isdeleted(versions):
                    selected_items = versions.selectedItems()
                    if selected_items:
                        for item in selected_items:
                            versions.takeItem(versions.row(item))
                    
                    InfoBar.success(
                        title=f'✅ 版本 {version} 已成功删除',
                        content="如需找回，可前往系统回收站找回。",
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                else:
                    log("版本 ComboBox 不存在或已被删除")
            else:
                log(f"版本文件夹不存在：{version_path}", logging.ERROR)
                InfoBar.warning(
                    title='⚠️ 提示',
                    content=f"版本 {version} 的文件夹不存在",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                
        except Exception as e:
            handle_exception(e)
            log(f"删除版本时发生错误: {e}", logging.ERROR)
            InfoBar.error(
                title='❌ 错误',
                content=f"删除版本 {version} 时发生错误: {str(e)}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    def Change_minecraft_version_name(self,version,versions):
        '''
        # 🚧TODO🚧

        ***

        ### 将 `.minecraft/version` 文件夹下 `{version}` 文件夹名称换成想要的文件名称并重读刷新。

        
        ***
        ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
        '''
        log(f"正在修改 Minecraft 版本名称：{version}")
    def delete_Customize(self,version,Customizes):
        '''
        ### 删除自定义选项
        将 配置文件中 `{version}` 对应的项目删除。

        
        ***
        ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
        '''
        log(f"正在删除自定义选项：{version}")
        try:
            isOK,item=find_Customize(self,version)
            if isOK:
                with open('config.json', 'r', encoding='utf-8') as file:
                    config_data = json.load(file)

                if "Customize" not in config_data:
                    config_data["Customize"] = []
                config_data["Customize"].remove(item)
                with open('config.json', 'w', encoding='utf-8') as file:
                    json.dump(config_data, file, ensure_ascii=False, indent=4)
                self.config = config_data
                InfoBar.success(
                    title='✅ 成功',
                    content=f"{version} 已成功删除",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                customize_list.remove(version)
                Customizes.clear()
                Customizes.addItems(customize_list)
                self.run_cmcl_list()
            else:
                InfoBar.error(
                    title='❌ 删除失败',
                    content=f"未找到与 {version} 匹配的自定义程序",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            
        except Exception as e:
            handle_exception(e)
            InfoBar.error(
                title='❌ 错误',
                content=f"保存到 config.json 时发生错误: {e}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    def Change_Customize_name(self,version,Customizes):
        '''
        # 🚧TODO🚧

        ***

        ### 将配置文件中 `{version}` 项目换成想要的名称并刷新重读。

        
        ***
        ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
        '''
        log(f"正在修改自定义选项名称：{version}")
        isOK,item=find_Customize(self,version)
        if isOK:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            # config_data["Customize"].remove(item)
            # TODO : 替换掉 Customize 中的对应项
            
        else:
            InfoBar.error(
                title='❌ 修改失败',
                content=f"未找到与 {version} 匹配的自定义程序",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
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
                log("执行命令: " + f"{self.version}")
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
                    log(line.strip())  # 将输出存入日志
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
            log("正在执行微软登录命令：cmcl account --login=microsoft")
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
                handle_exception(e)
                self.finished.emit(False, f"执行异常: {str(e)}")
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
                    handle_exception(e)
                    self.show_error("文件操作失败", f"无法覆盖cmcl.json: {str(e)}")
        elif login_way_choose.currentText() == "微软登录":
            if not config.get('localmod', False):
                login_way_choose = widget.findChild(ComboBox, "login_way")
                if not login_way_choose or login_way_choose.currentText() != "微软登录":
                    return

                # 覆盖cmcl.json
                try:
                    shutil.copyfile('cmcl.blank.json', 'cmcl.json')
                    log("成功覆盖 cmcl.json 文件")
                except Exception as e:
                    handle_exception(e)
                    self.show_error("文件操作失败", f"无法覆盖cmcl.json: {str(e)}")
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
                    title='⏱️ 正在登录微软账户',
                    content='请按照浏览器中的提示完成登录...',
                    isClosable=True,  # 允许用户手动关闭
                    position=InfoBarPosition.TOP,
                    duration=5000,  # 设置自动关闭时间
                    parent=self
                )
                self.login_tip.show()
                
                self.microsoft_login_thread.start()
            
            else:
                log("本地模式已启用，无法使用微软登录。")
                w = Dialog("您已启用本地模式", "Bloret Launcher 在本地模式下无法进行微软登录，\n因为该操作需要互联网\n如果需要登录，请到设置界面关闭本地模式。或使用离线登录。")
                if w.exec():
                    print('确认')
                else:
                    print('取消')
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
            title='❎ 提示',
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

    def log_output(self, output):
        if output:
            log(output.strip())
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
        log(f"run.ps1 运行失败: {error}", logging.ERROR)
        self.is_running = False  # 重置标志变量
    def update_show_text(self, text):
        self.show_text.setText(text) 
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
        if mode == "跟随系统":
            self.apply_theme()
        elif mode == "深色模式":
            self.apply_theme(QPalette(QColor("#2e2e2e")))
        elif mode == "浅色模式":
            self.apply_theme(QPalette(QColor("#ffffff")))
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
# 初始化配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 获取系统深浅色主题
isdarktheme = is_dark_theme()
log(f"当前主题:{isdarktheme}")

if not config.get('localmod', False):
    LM_Download_Way,LM_Download_Way_list,LM_Download_Way_version,LM_Download_Way_minecraft=check_Light_Minecraft_Download_Way(server_ip)
else:
    log("本地模式已启用，获取 Light-Minecraft-Download-Way 的过程已跳过。")

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

scale_factor = window.scale_factor
os.environ["QT_SCALE_FACTOR"] = str(scale_factor)

# 运行应用程序
sys.exit(app.exec())