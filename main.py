import sys
import logging
import os
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel, QFileDialog, QCheckBox, QMessageBox
from qfluentwidgets import NavigationInterface, NavigationItemPosition, TeachingTip, InfoBarIcon, TeachingTipTailPosition, ComboBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QDesktopServices, QCursor, QColor, QPalette, QMovie
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, QUrl, QSettings, QThread, pyqtSignal
import requests
import base64
import json
import configparser
import subprocess
import sip
import zipfile

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

class RunScriptThread(QThread):
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        script_path = "run.ps1"
        try:
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], check=True)
            self.finished.emit()
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(str(e.stderr))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #
        self.check_for_updates()

        self.setWindowTitle("Bloret 启动器 (Preview)")  # 设置软件标题
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

        # 显示窗口
        self.show()

    def check_for_updates(self):
        self.BL_latest_ver = self.get_latest_version()
        logging.info(f"最新正式版: {self.BL_latest_ver}")
        BL_ver = 1.0
        if BL_ver < float(self.BL_latest_ver):
            logging.warning(f"当前版本不是最新版，请更新到 {self.BL_latest_ver} 版本")
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('版本更新提示')
            msg_box.setText(f'当前版本不是最新版，请更新到 {self.BL_latest_ver} 版本')
            msg_box.setWindowIcon(QIcon("icons/bloret.png"))  # 设置弹窗图标
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_box.button(QMessageBox.Ok).setText('立即更新')
            msg_box.button(QMessageBox.Cancel).setText('暂时不了')
            if msg_box.exec() == QMessageBox.Ok:
                self.update_to_latest_version()

    def update_to_latest_version(self):
        url = f"http://localhost:100/zipdownload/{self.BL_latest_ver}.zip"
        #url = f"http://123.129.241.101:30399/zipdownload/{self.BL_latest_ver}.zip"
        save_path = os.path.join(os.getcwd(), f"{self.BL_latest_ver}.zip")
        updating_folder = os.path.join(os.path.dirname(os.getcwd()), "updating")

        if not os.path.exists(updating_folder):
            os.makedirs(updating_folder)

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logging.info(f"版本 {self.BL_latest_ver} 下载成功，保存路径: {save_path}")

            # 将下载的文件移动到 updating 文件夹
            new_save_path = os.path.join(updating_folder, f"{self.BL_latest_ver}.zip")
            os.rename(save_path, new_save_path)

            # 解压缩文件到 updating 文件夹
            with zipfile.ZipFile(new_save_path, 'r') as zip_ref:
                zip_ref.extractall(updating_folder)
            logging.info(f"版本 {self.BL_latest_ver} 解压缩成功，路径: {updating_folder}")

            # 删除压缩包
            os.remove(new_save_path)
            logging.info(f"删除压缩包: {new_save_path}")

            # 移动 .minecraft 文件夹到 updating 文件夹
            minecraft_folder = os.path.join(os.getcwd(), ".minecraft")
            if os.path.exists(minecraft_folder):
                new_minecraft_folder = os.path.join(updating_folder, ".minecraft")
                os.rename(minecraft_folder, new_minecraft_folder)
                logging.info(f"移动 .minecraft 文件夹到: {new_minecraft_folder}")

            # 创建 updata.ps1 文件
            current_folder_name = os.path.basename(os.getcwd())
            bat_file_path = os.path.join(os.path.dirname(os.getcwd()), "updata.ps1")
            with open(bat_file_path, 'w') as bat_file:
                bat_file.write(f'taskkill /im Bloret-Launcher.exe /f\n')
                bat_file.write(f'Remove-Item -Path ".\{current_folder_name}" -Recurse -Force\n')
                bat_file.write(r'Rename-Item -Path ".\\updating" -NewName "Bloret-Launcher"' + '\n')
                bat_file.write(r'.\\Bloret-Launcher\\Bloret-Launcher.exe' + '\n')
            logging.info(f"创建 updata.ps1 文件: {bat_file_path}")

            # 运行 updata.ps1 文件
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", bat_file_path], check=True)
            logging.info(f"运行 updata.ps1 文件: {bat_file_path}")

            QMessageBox.information(self, "下载完成", f"版本 {self.BL_latest_ver} 下载并解压缩成功")
        except requests.RequestException as e:
            logging.error(f"下载版本 {self.BL_latest_ver} 失败: {e}")
            QMessageBox.critical(self, "下载失败", f"下载版本 {self.BL_latest_ver} 失败: {e}")
        except zipfile.BadZipFile as e:
            logging.error(f"解压缩版本 {self.BL_latest_ver} 失败: {e}")
            QMessageBox.critical(self, "解压缩失败", f"解压缩版本 {self.BL_latest_ver} 失败: {e}")
        except OSError as e:
            logging.error(f"文件操作失败: {e}")
            QMessageBox.critical(self, "文件操作失败", f"文件操作失败: {e}")
        except subprocess.CalledProcessError as e:
            logging.error(f"运行 updata.ps1 文件失败: {e}")
            QMessageBox.critical(self, "更新失败", f"运行 updata.ps1 文件失败: {e}")

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

    def setup_passport_ui(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "player_name")
        player_name_set_button = widget.findChild(QPushButton, "player_name_set")
        if player_name_edit and player_name_set_button:
            player_name_set_button.clicked.connect(lambda: self.on_player_name_set_clicked(widget))

            # 读取 cmcl.json 中的 playerName 并设置到输入框中
            try:
                with open('cmcl.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                player_name = data['accounts'][0].get('playerName', '')
                player_name_edit.setText(player_name)
                logging.info(f"读取到的 playerName: {player_name}")
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                logging.error(f"读取 cmcl.json 失败: {e}")
                player_name_edit.setText('')  # 如果读取失败，清空输入框

    
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

    def on_player_name_set_clicked(self, widget):
        player_name_edit = widget.findChild(QLineEdit, "player_name")
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
        elif ui_path == "ui/passport.ui":
            self.setup_passport_ui(widget)

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
            set_list = [line.strip() for line in result.stdout.splitlines()[1:]]  # 去除每行末尾的空格
            logging.info(f"cmcl -l 输出: {set_list}")
        except subprocess.CalledProcessError as e:
            logging.error(f"执行 cmcl -l 失败: {e}")
            set_list = []
        
        run_choose = widget.findChild(ComboBox, "run_choose")
        if run_choose:
            run_choose.addItems(set_list)

        # 添加 run 按钮的点击事件
        run_button = widget.findChild(QPushButton, "run")  # 修改为 "run"
        if run_button:
            run_button.clicked.connect(lambda: self.run_cmcl(run_choose.currentText()))

    def run_cmcl(self, version):
        # 显示“正在启动”气泡消息
        logging.info(f"正在启动 {version}")
        run_button = self.sender()  # 获取按钮对象
        teaching_tip = TeachingTip.create(
            target=run_button,  # 修改为按钮对象
            icon=InfoBarIcon.SUCCESS,
            title=f'正在启动 {version}',
            content="请稍等",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=0,  # 设置为0表示不自动关闭
            parent=self
        )
        teaching_tip.move(run_button.mapToGlobal(run_button.rect().topLeft()))
        
        logging.info(f"运行 cmcl version {version} --export-script-ps=run.ps1")
        try:
            result = subprocess.run(["cmcl", "version", version, "--export-script-ps=run.ps1"], capture_output=True, text=True, check=True)
            logging.info(f"cmcl version {version} --export-script-ps=run.ps1 运行成功: {result.stdout}")
            
            # 替换 run.ps1 文件中的 "CMCL 2.2.2" 为 "Bloret Launcher"
            script_path = "run.ps1"
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as file:
                    script_content = file.read()
                
                script_content = script_content.replace('CMCL 2.2.2', 'Bloret Launcher')
                
                with open(script_path, 'w', encoding='utf-8') as file:
                    file.write(script_content)
                
                logging.info(f"成功替换 {script_path} 中的 'CMCL 2.2.2' 为 'Bloret Launcher'")
            
            # 运行 run.ps1 脚本
            logging.info(f"运行 {script_path}")
            self.run_script_thread = RunScriptThread()
            self.run_script_thread.teaching_tip = teaching_tip  # 将 TeachingTip 对象保存为线程的属性
            self.run_script_thread.finished.connect(lambda: self.on_run_script_finished(teaching_tip, run_button))
            self.run_script_thread.error_occurred.connect(lambda error: self.on_run_script_error(error, teaching_tip, run_button))
            self.run_script_thread.start()
            
        except subprocess.CalledProcessError as e:
            logging.error(f"cmcl version {version} --export-script-ps=run.ps1 运行失败: {e.stderr}")
            if teaching_tip:
                teaching_tip.close()  # 关闭气泡消息
            TeachingTip.create(
                target=self.sender(),
                icon=InfoBarIcon.ERROR,
                title='提示',
                content=f"cmcl version {version} --export-script-ps=run.ps1 运行失败: {e.stderr}",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000,
                parent=self
            )


    def on_run_script_finished(self, teaching_tip, run_button):
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()  # 关闭气泡消息
        TeachingTip.create(
            target=run_button,
            icon=InfoBarIcon.SUCCESS,
            title='{version} 启动成功',
            content="请等待 Minecraft 界面出现\n注意左下角是 Bloret Launcher 哦",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=5000,
            parent=self
        )

    def on_run_script_error(self, error, teaching_tip, run_button):
        if teaching_tip and not sip.isdeleted(teaching_tip):
            teaching_tip.close()
        TeachingTip.create(
            target=run_button,
            icon=InfoBarIcon.ERROR,
            title='提示',
            content=f"run.ps1 运行失败: {error}",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=2000,
            parent=self
        )
        logging.error(f"run.ps1 运行失败: {error}")

    def setup_download_load_ui(self, widget):
        # 设置下载加载界面的UI元素
        pass

    def setup_download_ui(self, widget):
        # 设置下载界面的UI元素
        pass

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
        logging.info(f"UUID {self.player_uuid} 已复制到剪贴板")

    def download_skin(self, widget):
        if self.player_skin:
            skin_url = self.player_skin
            skin_data = requests.get(skin_url).content
            with open("player_skin.png", "wb") as file:
                file.write(skin_data)
            logging.info(f"皮肤已下载到 player_skin.png")

    def download_cape(self, widget):
        if self.player_cape:
            cape_url = self.player_cape
            cape_data = requests.get(cape_url).content
            with open("player_cape.png", "wb") as file:
                file.write(cape_data)
            logging.info(f"披风已下载到 player_cape.png")

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
                logging.info(f"查询玩家名称 {player_name} 的UUID: {self.player_uuid}")
            else:
                uuid_result_label.setText("查询失败")
                logging.error(f"查询玩家名称 {player_name} 的UUID失败")

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
                        logging.info(f"查询玩家UUID {player_uuid} 的皮肤: {self.player_skin}")
                        logging.info(f"查询玩家UUID {player_uuid} 的披风: {self.player_cape}")
                        break
            else:
                skin_result_label.setText("查询失败")
                cape_result_label.setText("查询失败")
                logging.error(f"查询玩家UUID {player_uuid} 的皮肤和披风失败")

    def setup_settings_ui(self, widget):
        # 设置设置界面的UI元素
        pass

    def get_latest_version(self):
        try:
            response = requests.get("https://api.github.com/repos/BloretCrew/Bloret-Launcher/releases/latest")
            if response.status_code == 200:
                latest_release = response.json()
                return latest_release.get("tag_name", "未知版本")
            else:
                logging.error("查询最新版本失败")
                return "未知版本"
        except requests.RequestException as e:
            logging.error(f"查询最新版本时发生错误: {e}")
            return "未知版本"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
