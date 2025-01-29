import sys
import logging
import os
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel, QFileDialog, QCheckBox
from qfluentwidgets import NavigationInterface, NavigationItemPosition, TeachingTip, InfoBarIcon, TeachingTipTailPosition, ComboBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QDesktopServices, QCursor, QColor, QPalette, QMovie
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, QUrl, QSettings, QThread, pyqtSignal
import requests
import base64
import json
import configparser
import subprocess

# 全局变量
ver_id_main = []
ver_id = [] 
ver_url = {}

# 创建日志文件夹
if not os.path.exists('log'):
    os.makedirs('log')

# 设置日志配置
log_filename = os.path.join('log', f'log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class DownloadWorker(QThread):
    finished = pyqtSignal()

    def run(self):
        # 模拟数据处理
        import time
        time.sleep(5)  # 模拟数据处理耗时
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bloret 启动器 (beta)")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icons/bloret.png"))  # 设置软件图标

        self.player_uuid = ""  
        self.player_skin = ""  
        self.player_cape = ""  
        self.player_name = ""  

        # 读取设置
        self.settings = QSettings("Bloret", "Launcher")
        self.apply_theme()

        # 创建侧边栏
        self.navigation_interface = NavigationInterface(self)
        self.navigation_interface.addItem(
            routeKey="home",
            icon=QIcon("icons/bloret.png"),  
            text="主页",
            onClick=self.on_home_clicked,
            position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey="download",
            icon=QIcon("icons/download.png"),  
            text="下载",
            onClick=self.on_download_clicked,
            position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey="tools",
            icon=QIcon("icons/tools.png"),  
            text="工具",
            onClick=self.on_tools_clicked,
            position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey="passport",
            icon=QIcon("icons/passport.png"),  
            text="通行证",
            onClick=self.on_passport_clicked,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey="settings",
            icon=QIcon("icons/settings.png"),  
            text="设置",
            onClick=self.on_settings_clicked,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey="info",
            icon=QIcon("icons/info.png"),  
            text="关于",
            onClick=self.on_info_clicked,
            position=NavigationItemPosition.BOTTOM
        )

        # 创建按钮
        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.on_button_clicked)

        # 主布局
        self.main_layout = QHBoxLayout()  # 使用QHBoxLayout使侧边栏在左侧，内容在右侧
        self.main_layout.addWidget(self.navigation_interface)

        self.content_layout = QVBoxLayout()
        self.content_layout.addWidget(self.button)

        self.main_layout.addLayout(self.content_layout)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.animation_duration = 300  # 动画持续时间（毫秒）

        # 创建侧边栏动画
        self.sidebar_animation = QPropertyAnimation(self.navigation_interface, b"geometry")
        self.sidebar_animation.setDuration(self.animation_duration)
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # 创建内容淡入动画
        self.fade_in_animation = QPropertyAnimation(self.container, b"windowOpacity")
        self.fade_in_animation.setDuration(self.animation_duration)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # 默认加载主页
        self.load_ui("ui/home.ui", animate=False)

    def toggle_show_all_versions(self, state):
        widget = self.findChild(QWidget, "downloadWidget")  # 假设你的下载界面的QWidget对象名称为downloadWidget
        if widget:
            minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
            show_all_versions = widget.findChild(QCheckBox, "show_all_versions")
            if minecraft_choose and show_all_versions:
                self.update_minecraft_versions(widget, show_all=state)

    def open_github_bloret(self):
        QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew"))
        logging.info("打开Bloret Github 组织页面")

    def copy_skin_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_skin)
        logging.info(f"皮肤URL {self.player_skin} 已复制到剪贴板")

    def copy_cape_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_cape)
        logging.info(f"披风URL {self.player_cape} 已复制到剪贴板")

    def open_skin_url(self, widget):
        QDesktopServices.openUrl(QUrl(self.player_skin))
        logging.info(f"打开皮肤URL: {self.player_skin}")

    def open_cape_url(self, widget):
        QDesktopServices.openUrl(QUrl(self.player_cape))
        logging.info(f"打开披风URL: {self.player_cape}")

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
                logging.info(f"查询UUID {player_uuid} 的名称: {self.player_name}")
            else:
                name_result_label.setText("查询失败")
                logging.error(f"查询UUID {player_uuid} 的名称失败")

    def copy_name_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_name)
        logging.info(f"名称 {self.player_name} 已复制到剪贴板")

    def open_github_bloret_Launcher(self):
        QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew/Bloret-Launcher"))
        logging.info("打开该项目的Github页面")

    def open_qq_link(self):
        QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/iGw0GwUCiI"))
        logging.info("打开Bloret QQ 群页面")

    def animate_sidebar(self):
        start_geometry = self.navigation_interface.geometry()
        end_geometry = QRect(start_geometry.x(), start_geometry.y(), start_geometry.width(), start_geometry.height())
        self.sidebar_animation.setStartValue(start_geometry)
        self.sidebar_animation.setEndValue(end_geometry)
        self.sidebar_animation.start()

    def animate_fade_in(self):
        self.fade_in_animation.start()

    def apply_theme(self):
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            self.setStyleSheet("QWidget { background-color: #2e2e2e; color: #ffffff; }")
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#2e2e2e"))
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.AlternateBase, QColor("#2e2e2e"))
            palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#ffffff"))
            palette.setColor(QPalette.Button, QColor("#2e2e2e"))
            palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.Link, QColor("#2a82da"))
            palette.setColor(QPalette.Highlight, QColor("#2a82da"))
            palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.setPalette(palette)
        else:
            self.setStyleSheet("")
            self.setPalette(self.style().standardPalette())

    
    # -----------------------------------------------------------
    # 以下内容是对于UI文件中各个元素的设定
    # -----------------------------------------------------------
    def on_home_clicked(self):
        logging.info("主页 被点击")
        self.load_ui("ui/home.ui")

    def on_download_clicked(self):
        logging.info("下载 被点击")
        self.load_ui("ui/download_load.ui", animate=False)
        self.download_worker = DownloadWorker()
        self.download_worker.finished.connect(self.load_download_ui)
        self.download_worker.start()

    def load_download_ui(self):
        self.load_ui("ui/download.ui", animate=False)
        self.setup_download_ui(self.content_layout.itemAt(0).widget())

    def on_passport_clicked(self):
        logging.info("通行证 被点击")
        self.load_ui("ui/passport.ui")

    def on_settings_clicked(self):
        logging.info("设置 被点击")
        self.load_ui("ui/settings.ui")

    def on_info_clicked(self):
        logging.info("关于 被点击")
        self.load_ui("ui/info.ui")

    def on_tools_clicked(self):
        logging.info("工具 被点击")
        self.load_ui("ui/tools.ui")

    def on_button_clicked(self):
        logging.info("按钮 被点击")

    def on_player_name_set_clicked(self):
        player_name_edit = self.findChild(QLineEdit, "lineEdit")
        player_name = player_name_edit.text()
        
        if not player_name:
            TeachingTip.create(
                target=self.sender(),
                icon=InfoBarIcon.ERROR,
                title='提示',
                content="请填写值后设定",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        elif any('\u4e00' <= char <= '\u9fff' for char in player_name):
            TeachingTip.create(
                target=self.sender(),
                icon=InfoBarIcon.ERROR,
                title='提示',
                content="名称不能包含中文",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        else:
            with open('cmcl.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['accounts'][0]['playerName'] = player_name
            with open('cmcl.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        # -----------------------------------------------------------
        # 以上内容是对于UI文件中各个元素的设定，
        # -----------------------------------------------------------
        # 下面是对于UI文件的加载和设置的方法
        # -----------------------------------------------------------
    def load_ui(self, ui_path, animate=True):
        widget = uic.loadUi(ui_path)
        # 清除之前的内容
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)
        self.content_layout.addWidget(widget)

        if ui_path == "ui/home.ui":
            self.setup_home_ui(widget)
        elif ui_path == "ui/info.ui":
            self.setup_info_ui(widget)
        elif ui_path == "ui/tools.ui":
            self.setup_tools_ui(widget)
        elif ui_path == "ui/download.ui":
            self.setup_download_ui(widget)
        elif ui_path == "ui/settings.ui":
            self.setup_settings_ui(widget)
        elif ui_path == "ui/download_load.ui":
            self.setup_download_load_ui(widget)

        if animate:
            self.animate_sidebar()
            self.animate_fade_in()

    def setup_home_ui(self, widget):
        github_org_button = widget.findChild(QPushButton, "pushButton_2")
        if github_org_button:
            github_org_button.clicked.connect(self.open_github_bloret)
        github_project_button = widget.findChild(QPushButton, "pushButton")
        if github_project_button:
            github_project_button.clicked.connect(self.open_github_bloret_Launcher)

        # 获取 set_list
        try:
            result = subprocess.run(["cmcl", "-l"], capture_output=True, text=True, check=True)
            set_list = result.stdout.splitlines()[1:]  # 从第二行开始读取
            logging.info(f"cmcl -l 输出: {set_list}")
        except subprocess.CalledProcessError as e:
            logging.error(f"执行 cmcl -l 失败: {e}")
            set_list = []

        run_choose = widget.findChild(ComboBox, "run_choose")
        if run_choose:
            run_choose.addItems(set_list)

        # 添加 run 按钮的点击事件
        run_button = widget.findChild(QPushButton, "run_button")  # 假设 run 按钮的对象名称为 run_button
        if run_button:
            run_button.clicked.connect(lambda: self.run_cmcl(run_choose.currentText()))

    def run_cmcl(self, version):
        # 显示“正在启动”气泡消息
        logging.info(f"正在启动 {version}")
        teaching_tip = TeachingTip.create(
            target=self.sender(),
            icon=InfoBarIcon.SUCCESS,  # 使用可用的图标常量
            title=f'正在启动 {version}',
            content="请稍等",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=0,  # 设置为0表示不自动关闭
            parent=self
        )
        teaching_tip.move(self.sender().mapToGlobal(self.sender().rect().topLeft()))

        logging.info(f"运行 cmcl {version}")
        try:
            result = subprocess.run(["cmcl", version], capture_output=True, text=True, check=True)
            logging.info(f"cmcl {version} 运行成功: {result.stdout}")
            teaching_tip.close()  # 关闭气泡消息
            TeachingTip.create(
                target=self.sender(),
                icon=InfoBarIcon.SUCCESS,
                title='提示',
                content=f"cmcl {version} 运行成功",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"cmcl {version} 运行失败: {e.stderr}")
            teaching_tip.close()  # 关闭气泡消息
            TeachingTip.create(
                target=self.sender(),
                icon=InfoBarIcon.ERROR,
                title='提示',
                content=f"cmcl {version} 运行失败: {e.stderr}",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            )

    def setup_info_ui(self, widget):
        github_org_button = widget.findChild(QPushButton, "pushButton_2")
        if github_org_button:
            github_org_button.clicked.connect(self.open_github_bloret)
        github_project_button = widget.findChild(QPushButton, "button_github")
        if github_project_button:
            github_project_button.clicked.connect(self.open_github_bloret_Launcher)
        qq_button = widget.findChild(QPushButton, "pushButton")  # 确保按钮名称正确
        if qq_button:
            qq_button.clicked.connect(self.open_qq_link)

    def setup_tools_ui(self, widget):
        query_button = widget.findChild(QPushButton, "name2uuid_player_Button")
        if query_button:
            query_button.clicked.connect(lambda: self.query_player_uuid(widget))
        copy_button = widget.findChild(QPushButton, "pushButton_5")
        if copy_button:
            copy_button.clicked.connect(lambda: self.copy_to_clipboard(widget))
        skin_search_button = widget.findChild(QPushButton, "skin_search_button")
        if skin_search_button:
            skin_search_button.clicked.connect(lambda: self.query_player_skin(widget))
        skin_copy_button = widget.findChild(QPushButton, "search_skin_copy")
        if skin_copy_button:
            skin_copy_button.clicked.connect(lambda: self.copy_skin_to_clipboard(widget))
        skin_down_button = widget.findChild(QPushButton, "search_skin_down")
        if skin_down_button:
            skin_down_button.clicked.connect(lambda: self.open_skin_url(widget))
        cape_copy_button = widget.findChild(QPushButton, "search_cape_copy")
        if cape_copy_button:
            cape_copy_button.clicked.connect(lambda: self.copy_cape_to_clipboard(widget))
        cape_down_button = widget.findChild(QPushButton, "search_cape_down")
        if cape_down_button:
            cape_down_button.clicked.connect(lambda: self.open_cape_url(widget))
        name_search_button = widget.findChild(QPushButton, "search_name_button")
        if name_search_button:
            name_search_button.clicked.connect(lambda: self.query_player_name(widget))
        name_copy_button = widget.findChild(QPushButton, "search_name_copy")
        if name_copy_button:
            name_copy_button.clicked.connect(lambda: self.copy_name_to_clipboard(widget))

    def setup_download_ui(self, widget):
        minecraft_part_edit = widget.findChild(QLineEdit, "minecraft_part")
        minecraft_part_choose_button = widget.findChild(QPushButton, "minecraft_part_choose")
        minecraft_part_set_button = widget.findChild(QPushButton, "minecraft_part_set")
        download_way_choose = widget.findChild(ComboBox, "download_way_choose")
        download_way_F5_button = widget.findChild(QPushButton, "download_way_F5")
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        show_all_versions = widget.findChild(QCheckBox, "show_all_minecraft")
        download_button = widget.findChild(QPushButton, "download")  # 使用正确的 objectName

        if minecraft_part_edit:
            config = configparser.ConfigParser()
            config.read('config.ini')
            if 'DEFAULT' in config and 'minecraft-part' in config['DEFAULT']:
                minecraft_part_edit.setText(config['DEFAULT']['minecraft-part'])
            else:
                minecraft_part_edit.setText(os.path.join(os.getcwd(), ".minecraft"))

        if minecraft_part_choose_button:
            minecraft_part_choose_button.clicked.connect(lambda: self.choose_minecraft_part(widget))

        if minecraft_part_set_button:
            minecraft_part_set_button.clicked.connect(lambda: self.set_minecraft_part(widget))

        if download_way_choose:
            download_way_choose.clear()
            download_way_choose.addItems(["BMCLAPI"])
            download_way_choose.currentIndexChanged.connect(lambda index: print(download_way_choose.currentText()))

        if download_way_F5_button:
            download_way_F5_button.clicked.connect(lambda: self.update_minecraft_versions(widget))

        if minecraft_choose:
            self.update_minecraft_versions(widget)  # 调用更新版本列表的方法

        if show_all_versions:
            show_all_versions.stateChanged.connect(lambda state: self.update_minecraft_versions(widget, show_all=state))

        if download_button:
            def on_download_clicked():
                self.start_download(widget)
            download_button.clicked.connect(on_download_clicked)

        # 设置和启动 GIF 动画
        loading_label = widget.findChild(QLabel, "label_2")
        if loading_label:
            self.setup_loading_gif(loading_label)


    def setup_settings_ui(self, widget):
        light_dark_choose = widget.findChild(ComboBox, "light_dark_choose")
        if light_dark_choose:
            light_dark_choose.addItems(["跟随系统", "浅色", "深色"])
            light_dark_choose.currentIndexChanged.connect(self.change_theme)

    def setup_loading_gif(self, label):
        movie = QMovie("ui/icon/loading2.gif")
        label.setMovie(movie)
        movie.start()

    def setup_download_load_ui(self, widget):
        # 设置和启动 GIF 动画
        loading_label = widget.findChild(QLabel, "loading_label")  # 假设 QLabel 的对象名称为 loading_label
        if loading_label:
            self.setup_loading_gif(loading_label)

    def change_theme(self, index):
        theme = self.sender().itemText(index)
        if theme == "深色":
            self.settings.setValue("theme", "dark")
        elif theme == "浅色":
            self.settings.setValue("theme", "light")
        else:
            self.settings.setValue("theme", "system")
        self.apply_theme()

    def choose_minecraft_part(self, widget):
        minecraft_part_edit = widget.findChild(QLineEdit, "minecraft_part")
        minecraft_part_choose_button = widget.findChild(QPushButton, "minecraft_part_choose")
        if minecraft_part_edit and minecraft_part_choose_button:
            folder_path = QFileDialog.getExistingDirectory(self, "选择 .minecraft 文件夹", os.getcwd())
            if folder_path:
                minecraft_part_edit.setText(folder_path)
                config = configparser.ConfigParser()
                config.read('config.ini')
                if 'DEFAULT' not in config:
                    config['DEFAULT'] = {}
                config['DEFAULT']['minecraft-part'] = folder_path
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                logging.info(f"选择的 .minecraft 文件夹路径: {folder_path}")
                self.showTeachingTip(minecraft_part_choose_button, folder_path)

    def set_minecraft_part(self, widget):
        minecraft_part_edit = widget.findChild(QLineEdit, "minecraft_part")
        minecraft_part_set_button = widget.findChild(QPushButton, "minecraft_part_set")
        if minecraft_part_edit and minecraft_part_set_button:
            folder_path = minecraft_part_edit.text()
            config = configparser.ConfigParser()
            config.read('config.ini')
            if 'DEFAULT' not in config:
                config['DEFAULT'] = {}
            config['DEFAULT']['minecraft-part'] = folder_path
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            logging.info(f"设置的 .minecraft 文件夹路径: {folder_path}")
            self.showTeachingTip(minecraft_part_set_button, folder_path)

    def showTeachingTip(self, target_widget, folder_path):
        TeachingTip.create(
            target=target_widget,
            icon=InfoBarIcon.SUCCESS,
            title='提示',
            content=f"已存储 Minecraft 核心文件夹位置为\n{folder_path}",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=2000,
            parent=self
        ).move(target_widget.mapToGlobal(target_widget.rect().topLeft()))

    def update_minecraft_versions(self, widget, show_all=False):
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
        if minecraft_choose:
            try:
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                if response.status_code == 200:
                    version_data = response.json()
                    latest_release = version_data["latest"]["release"]
                    latest_snapshot = version_data["latest"]["snapshot"]
                    versions = version_data["versions"]

                    for version in versions:
                        ver_id.append(version["id"])  # 直接将版本ID添加到列表中
                        ver_url[version["id"]] = version["url"]  # 使用版本ID作为键

                        if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                            ver_id_main.append(version["id"])

                    minecraft_choose.clear()
                    if show_all:
                        minecraft_choose.addItems(ver_id)
                    else:
                        minecraft_choose.addItems(ver_id_main)

                    logging.info(f"最新发布版本: {latest_release}")
                    logging.info(f"最新快照版本: {latest_snapshot}")
                    logging.info("Minecraft 版本列表已更新")
                else:
                    logging.error("无法获取 Minecraft 版本列表")
            except requests.exceptions.SSLError as e:
                logging.error(f"SSL 错误: {e}")
                TeachingTip.create(
                    target=minecraft_choose,
                    icon=InfoBarIcon.ERROR,  # 使用错误图标
                    title='提示',
                    content="无法连接到服务器，请检查网络连接或稍后再试。",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                )


    class DownloadThread(QThread):
        finished = pyqtSignal()
        error_occurred = pyqtSignal(str)  # 添加错误信号

        def __init__(self, version):
            super().__init__()
            self.version = version

        def run(self):
            try:
                result = subprocess.run(["cmcl", "install", self.version], capture_output=True, text=True, check=True)
                self.finished.emit()
            except subprocess.CalledProcessError as e:
                if "该名称已存在，请更换一个名称。" in e.stderr:
                    self.error_occurred.emit("你已下载过该版本。")
                else:
                    self.error_occurred.emit("下载失败，原因：未知错误。")

        def on_download_error(self, error_message, widget):
            download_button = widget.findChild(QPushButton, "download")
            if download_button:
                TeachingTip.create(
                    target=download_button,
                    icon=InfoBarIcon.ERROR,  # 使用错误图标
                    title='提示',
                    content=f"下载失败，原因：{error_message}",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                )


    def on_download_finished(self, version):
        logging.info(f'"{version}" 下载完成')

    def start_download(self, widget):
        minecraft_part_edit = widget.findChild(QLineEdit, "minecraft_part")
        download_way_choose = widget.findChild(ComboBox, "download_way_choose")
        minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")

        if minecraft_part_edit and download_way_choose and minecraft_choose:
            minecraft_part = minecraft_part_edit.text()
            ver = download_way_choose.currentText()
            version = minecraft_choose.currentText()

            download_button = widget.findChild(QPushButton, "download")

            # 创建versions文件夹
            versions_folder = os.path.join(minecraft_part, "versions")
            if not os.path.exists(versions_folder):
                os.makedirs(versions_folder)

            # 创建版本文件夹
            download_part = os.path.join(versions_folder, version)
            if os.path.exists(download_part):
                TeachingTip.create(
                    target=download_button,
                    icon=InfoBarIcon.ERROR,
                    title='你已下载过该版本',
                    content="百洛谷启动器暂不支持同版本多次下载\n如您需要重新下载，请手动删除该版本文件夹",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                )
                return
            else:
                os.makedirs(download_part)

                # 显示“已经开始下载”气泡消息
                teaching_tip = TeachingTip.create(
                    target=download_button,
                    icon=InfoBarIcon.SUCCESS,  # 使用可用的图标常量
                    title='已经开始下载',
                    content="由于雷达太厉害，关闭百洛谷启动器后还能继续下载✔\n请勿关闭计算机。",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                )
                teaching_tip.move(download_button.mapToGlobal(download_button.rect().topLeft()))

                logging.info(f"下载路径: {download_part}")

                # 获取版本信息
                res_url = ver_url[version]
                response = requests.get(res_url)
                if response.status_code == 200:
                    version_data = response.json()
                    client_url = version_data["downloads"]["client"]["url"]
                    client_filename = os.path.join(download_part, f"{version}.jar")

                    # 使用 cmcl 下载
                    self.download_thread = MainWindow.DownloadThread(version)
                    self.download_thread.finished.connect(lambda: self.on_download_finished(version))
                    self.download_thread.error_occurred.connect(lambda error_message: self.on_download_error(error_message, widget, teaching_tip))
                    self.download_thread.start()

                    # 执行 cmcl -l 命令并将读取的内容存储在列表 set_list 中
                    result = subprocess.run(["cmcl", "-l"], capture_output=True, text=True, check=True)
                    set_list = result.stdout.splitlines()[1:]  # 从第二行开始读取
                    logging.info(f"cmcl -l 输出: {set_list}")

def on_download_error(self, error_message, widget, teaching_tip):
    download_button = widget.findChild(QPushButton, "download")
    if download_button:
        teaching_tip.close()  # 关闭“已经开始下载”的气泡消息
        TeachingTip.create(
            target=download_button,
            icon=InfoBarIcon.ERROR,  # 使用错误图标
            title='提示',
            content=f"下载失败，原因：{error_message}",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=2000,
            parent=self
        )

    def query_player_uuid(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "name2uuid_player_uuid")
        result_label = widget.findChild(QLabel, "label_2")
        if player_name_edit and result_label:
            result_label.setText("查询中，请稍等...")
            player_name = player_name_edit.text()
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player_name}")
            if response.status_code == 200:
                player_data = response.json()
                self.player_uuid = player_data.get("id", "未找到UUID")
                self.player_name = player_name  # Store player name for later use
                result_label.setText(self.player_uuid)
                logging.info(f"查询玩家 {player_name} 的UUID: {self.player_uuid}")
            else:
                result_label.setText("查询失败")
                logging.error(f"查询玩家 {player_name} 的UUID失败")

    def copy_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_uuid)
        logging.info(f"UUID {self.player_uuid} 已复制到剪贴板")
        self.show_copy_success(widget, "pushButton_5")

    def copy_skin_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_skin)
        logging.info(f"皮肤URL {self.player_skin} 已复制到剪贴板")
        self.show_copy_success(widget, "search_skin_copy")

    def copy_cape_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_cape)
        logging.info(f"披风URL {self.player_cape} 已复制到剪贴板")
        self.show_copy_success(widget, "search_cape_copy")

    def copy_name_to_clipboard(self, widget):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.player_name)
        logging.info(f"名称 {self.player_name} 已复制到剪贴板")
        self.show_copy_success(widget, "search_name_copy")

    def show_copy_success(self, widget, button_name):
        button = widget.findChild(QPushButton, button_name)
        if button:
            TeachingTip.create(
                target=button,
                icon=InfoBarIcon.SUCCESS,
                title='提示',
                content="已复制到剪贴板",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            ).move(button.mapToGlobal(button.rect().topLeft()))

    def query_player_skin(self, widget):
        player_uuid_edit = widget.findChild(QLineEdit, "skin_uuid")
        skin_result_label = widget.findChild(QLabel, "search_skin")
        cape_result_label = widget.findChild(QLabel, "search_cape")
        if player_uuid_edit and skin_result_label and cape_result_label:
            skin_result_label.setText("查询中，请稍等...")
            cape_result_label.setText("查询中，请稍等...")
            player_uuid = player_uuid_edit.text()
            response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_uuid}")
            if response.status_code == 200:
                player_data = response.json()
                properties = player_data.get("properties", [])
                if properties:
                    value = properties[0].get("value", "")
                    decoded_data = base64.b64decode(value).decode('utf-8')
                    textures = json.loads(decoded_data).get("textures", {})
                    self.player_skin = textures.get("SKIN", {}).get("url", "未找到皮肤URL")
                    self.player_cape = textures.get("CAPE", {}).get("url", "未找到披风URL")
                    skin_result_label.setText(self.player_skin[:20] + "..." if len(self.player_skin) > 20 else self.player_skin)
                    cape_result_label.setText(self.player_cape[:20] + "..." if len(self.player_cape) > 20 else self.player_cape)
                    logging.info(f"皮肤URL: {self.player_skin}")
                    logging.info(f"披风URL: {self.player_cape}")
                else:
                    skin_result_label.setText("未找到皮肤信息")
                    cape_result_label.setText("未找到披风信息")
                    logging.error("未找到皮肤和披风信息")
            else:
                skin_result_label.setText("查询失败")
                cape_result_label.setText("查询失败")
                logging.error(f"查询玩家 {player_uuid} 的皮肤和披风信息失败")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())