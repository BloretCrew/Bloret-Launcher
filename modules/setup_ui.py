from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QWidget, QSizePolicy, QApplication
from qfluentwidgets import SpinBox, ComboBox, SwitchButton, LineEdit, InfoBarPosition, InfoBar, SubtitleLabel, CardWidget, StrongBodyLabel, BodyLabel, PushButton, SmoothScrollArea, RoundMenu, Action, FluentIcon, SearchLineEdit, CaptionLabel, ImageLabel, IndeterminateProgressBar, IconWidget, ToolButton, MessageBoxBase, NavigationItemPosition
from PyQt5 import uic
from PyQt5.QtGui import QDesktopServices, QPixmap, QColor
from PyQt5.QtCore import QUrl, Qt, QSize, QTimer, QDateTime
import requests, json, logging, os, socket
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.systems import setup_startup_with_self_starting
from modules.log import log, clear_log_files
from modules.Bloret_PassPort import Bloret_PassPort_Account_logout, sync_mc_account_to_bloret_passport, sync_bloret_passport_account_to_mc
from modules.links import open_github_bloret_Launcher,open_qq_link,open_BLC_qq_link,open_BBBS_link,open_BBBS_Reg_link,open_github_bloret,copy_skin_to_clipboard,copy_cape_to_clipboard,copy_uuid_to_clipboard,copy_name_to_clipboard, Bloret_PassPort_Account_login
from modules.querys import query_player_uuid,query_player_skin,query_player_name
from modules.versions import delete_minecraft_version,Change_minecraft_version_name,delete_Customize,Change_Customize_name,open_minecraft_version_folder, on_other_version_selected
from modules.install import InstallMinecraftVersion
from modules.modrinth import search_mods, Get_Mod_File_Download_Url, add_mrpack
from PyQt5.QtCore import QThread, pyqtSignal
from modules.win11toast import notify, update_progress
from modules.local_client import OnlineClient
from modules.java import InstallJava
from modules.i18n import i18nText
from modules.customize import CustomizeAdd
from modules.Bloriko import AskBlorikoAndSet
from modules.chafuwang import getServerData

class DownloadDialog(MessageBoxBase):
    """ 自定义下载对话框 """

    def __init__(self, mod_title, slug, parent=None):
        super().__init__(parent)
        self.mod_title = mod_title
        self.slug = slug
        self.game_versions = []  # 存储模组支持的游戏版本
        
        self.titleLabel = SubtitleLabel(mod_title)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        
        self.modNameLabel = StrongBodyLabel(f'选择安装 Mod 的版本')
        
        self.versionCombo = ComboBox()
        self.versionCombo.setPlaceholderText(i18nText('选择版本'))
        
        # 获取模组支持的游戏版本
        self.fetch_mod_versions()
        
        # 获取 .minecraft\versions 文件夹内的文件夹列表
        versions_path = os.path.join(os.getcwd(), ".minecraft", "versions")
        if os.path.exists(versions_path):
            version_folders = [f for f in os.listdir(versions_path) 
                              if os.path.isdir(os.path.join(versions_path, f))]
            self.versionCombo.addItems(version_folders)
        
        if self.versionCombo.count() > 0:
            self.versionCombo.setCurrentIndex(0)
        else:
            self.versionCombo.addItem(i18nText("未找到任何版本"))
            
        # 连接版本选择变化信号
        self.versionCombo.currentTextChanged.connect(self.check_version_compatibility)
        
        # 创建提示标签（默认隐藏）
        self.warningLabel = CaptionLabel("")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabel.hide()
        self.downloadButton = PushButton(i18nText('打开 Modrinth 详情页面'))
        self.downloadButton.clicked.connect(self.open_modrinth_page)
        
        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.modNameLabel)
        self.viewLayout.addWidget(self.versionCombo)
        self.viewLayout.addWidget(self.warningLabel)
        self.viewLayout.addWidget(self.downloadButton)
        
        # 修改按钮
        self.yesButton.setText(i18nText('下载 Mod'))
        self.yesButton.clicked.connect(self.download_mod)
        self.cancelButton.setText(i18nText('取消'))
        
        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(350)
        
        # 检查初始版本兼容性
        self.check_version_compatibility(self.versionCombo.currentText())
    
    def open_modrinth_page(self):
        # 这里可以添加实际的下载逻辑
        log(f"准备下载模组: {self.mod_title} (版本: {self.versionCombo.currentText()})")
        log(f"模组链接: https://modrinth.com/mod/{self.slug}")
        # 打开模组页面
        QDesktopServices.openUrl(QUrl(f"https://modrinth.com/mod/{self.slug}"))
        self.accept()  # 关闭对话框
        
    def fetch_mod_versions(self):
        """获取模组支持的游戏版本"""
        try:
            url = f"https://api.modrinth.com/v2/project/{self.slug}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self.game_versions = data.get("game_versions", [])
                log(f"模组 {self.mod_title} 支持的游戏版本: {self.game_versions}")
            else:
                log(f"获取模组信息失败，状态码: {response.status_code}")
        except Exception as e:
            log(f"获取模组信息时出错: {str(e)}")
            
    def check_version_compatibility(self, selected_version):
        """检查所选版本是否与模组兼容"""
        if not selected_version or selected_version == i18nText("未找到任何版本"):
            self.warningLabel.hide()
            self.yesButton.show()  # 重新启用下载按钮
            return
            
        # 检查所选版本是否在模组支持的版本列表中
        if selected_version in self.game_versions:
            self.warningLabel.hide()
            self.yesButton.show()  # 启用下载按钮
        else:
            self.warningLabel.setText(i18nText("警告：所选版本可能不兼容此模组"))
            self.warningLabel.show()
            self.yesButton.hide()  # 禁用下载按钮
            
    def download_mod(self):
        """下载选定的Mod文件"""
        version = self.versionCombo.currentText()
        if not version or version == i18nText("未找到任何版本"):
            log(i18nText("未选择有效的版本"))
            return
            
        # 获取Mod下载URL
        url = Get_Mod_File_Download_Url(self.slug, "fabric", version)
        if not url:
            log(f"无法获取Mod {self.mod_title} 的下载URL")
            return
            
        # 创建目标目录
        mod_dir = os.path.join(os.getcwd(), ".minecraft", "versions", version, "mods")
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)
            
        # 获取文件名
        filename = url.split("/")[-1]
        file_path = os.path.join(mod_dir, filename)
        
        # 下载文件
        try:
            log(f"开始下载 {self.mod_title} 到 {file_path}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            log(f"成功下载 {self.mod_title} 到 {file_path}")
            InfoBar.success(
                title=i18nText('✅ 下载成功'),
                content=f"Mod {self.mod_title} 已成功下载到 {file_path}",
                parent=self.parent(),
                duration=5000
            )
            self.accept()  # 关闭对话框
        except Exception as e:
            log(f"下载Mod时出错: {str(e)}")
            InfoBar.error(
                title=i18nText('❌ 下载失败'),
                content=f"下载Mod {self.mod_title} 时出错: {str(e)}",
                parent=self.parent(),
                duration=5000
            )

class ModSearchThread(QThread):
    results_ready = pyqtSignal(object)
    ui_elements_ready = pyqtSignal(list)  # 新增信号传递预处理数据

    def __init__(self, mod_list, search_term):
        super().__init__()
        self.mod_list = mod_list
        self.search_term = search_term

    def run(self):
        results = search_mods(self.search_term)
        log(f"2搜索结果: {results}")
        self.results_ready.emit(results)
        if results and isinstance(results, dict) and 'hits' in results and isinstance(results['hits'], list):
            # 在子线程预处理数据（不创建控件）
            processed = []
            for mod in results['hits']:
                # 只处理字典类型的mod
                if isinstance(mod, dict):
                    processed.append({
                        "title": mod.get("title", ""),
                        "description": mod.get("description", ""),
                        "icon_url": mod.get("icon_url", ""),
                        "downloads": mod.get("downloads", 0),
                        "follows": mod.get("follows", 0),
                        "categories": mod.get("categories", []),
                        "slug": mod.get("slug", "")
                    })
            self.ui_elements_ready.emit(processed)  # 发送预处理数据


def show_download_dialog(mod_title, slug, parent):
    """显示下载对话框"""
    dialog = DownloadDialog(mod_title, slug, parent)
    dialog.exec_()


def load_ui(ui_path, parent=None, animate=True):
    '''
    ### 加载 UI 布局
    通过 .ui 文件
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    widget = uic.loadUi(ui_path)

    if parent:
        # 强制使用布局管理（若原布局缺失）
        if not parent.layout():
            layout = QVBoxLayout(parent)  # 使用垂直布局
            layout.setContentsMargins(0,0,0,0)  # 移除默认边距
            layout.addWidget(widget)
        else:
            parent.layout().addWidget(widget)

def on_self_starting_changed(value):
    """
    当 SwitchButton 状态变化时，更新配置文件中的 self-starting 字段
    """
    log(f"开机自启设置为: {value}")
    config_path = os.path.join("config.json")
    try:
        # 读取现有配置
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}
    config["self-starting"] = value
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        log(f"已更新配置: self-starting={value}")
        setup_startup_with_self_starting(value) # 更新开机自启设置
        log(f"已更新开机自启设置: {value}")
    except Exception as e:
        log(f"写入配置文件失败: {e}")

def setup_home_ui(self, widget):
    '''
    设定 Bloret Launcher 主页 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    if self.config.get('localmod', False):
        InfoBar.warning(
            title=i18nText('⚠️ 本地模式已开启'),
            content=f"您已启用本地模式\n本地模式下 Bloret Launcher 不会访问一部分的网络，包括 Bloret Launcher Server 服务。\n\n这意味着什么？\n您将无法获取到 Bloret Launcher 的最新版本\n您将无法下载除 Bloret 支持版本外的版本\n您将无法使用微软登录和百络谷通行证登录等\n\n如果需要以上服务，请到设置界面关闭本地模式。",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=10000,
            parent=self
        )
    github_org_button = widget.findChild(QPushButton, "pushButton_2")
    if github_org_button:
        github_org_button.clicked.connect(open_github_bloret)
    github_project_button = widget.findChild(QPushButton, "pushButton")
    if github_project_button:
        github_project_button.clicked.connect(open_github_bloret_Launcher)

    openblweb_button = widget.findChild(QPushButton, "openblweb")
    if openblweb_button:
        openblweb_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://launcher.bloret.net")))
    self.run_cmcl_list(True)
    run_choose = widget.findChild(ComboBox, "run_choose")
    run_button = widget.findChild(QPushButton, "run")
    if run_button:
        run_button.clicked.connect(lambda: self.run_cmcl(run_choose.currentText()))
    self.show_text = widget.findChild(QLabel, "show")
    Bloret_PassPort_Name = widget.findChild(QLabel, "Bloret_PassPort_Name")
    if Bloret_PassPort_Name:
        Bloret_PassPort_Name.setText(f"{self.config.get('Bloret_PassPort_UserName', '未登录')}")
    Minecraft_account = widget.findChild(QLabel, "Minecraft_account")
    if Minecraft_account:
        if self.config.get('home_show_login_mod', False):
            if self.login_mod == i18nText("请在下方登录"):
                Minecraft_account.setText(i18nText("无档案(请到通行证页面登录)"))
            else:
                Minecraft_account.setText(f"[{self.login_mod}] {self.player_name}")
        else:
            Minecraft_account.setText(f"{self.player_name}")
            
    AskBloriko_Edit = widget.findChild(LineEdit, "AskBloriko_Edit")
    AskBloriko_Button = widget.findChild(PushButton, "AskBloriko_Button")
    AskBloriko_Answer = widget.findChild(StrongBodyLabel, "AskBloriko_Answer")
    if AskBloriko_Button:
        AskBloriko_Button.setIcon(FluentIcon.SEND)
        AskBloriko_Button.clicked.connect(lambda: AskBlorikoAndSet(self, widget, AskBloriko_Edit.text(), AskBloriko_Answer))
    else:
        log("未找到 AskBloriko_Button 元素")

    if not AskBloriko_Edit:
        log("未找到 AskBloriko_Edit 元素")

    if not AskBloriko_Answer:
        log("未找到 AskBloriko_Answer 元素")

    BloretServerOnlineNumber = widget.findChild(QLabel, "BloretServerOnlineNumber")
    BloretServerText0 = widget.findChild(QLabel, "BloretServerText0")
    BloretServerText1 = widget.findChild(QLabel, "BloretServerText1")
    BloretServer_BestTime = widget.findChild(QLabel, "BloretServer_BestTime")
    if BloretServer_BestTime:
        BloretServer_BestTime.setWordWrap(True)
    
    # 修复：正确处理getServerData返回的线程对象
    def update_server_info(data):
        if BloretServerOnlineNumber and BloretServerText0 and BloretServerText1 and BloretServer_BestTime:
            # 检查是否有错误信息
            if "error" in data:
                log(f"服务器数据获取失败: {data.get('error')}")
                BloretServerOnlineNumber.setText("N/A")
                BloretServerText0.setText("服务器数据获取失败")
                BloretServerText1.setText("")
                BloretServer_BestTime.setText("")
                return
            
            try:
                # 安全地处理数据，确保数字类型正确转换为字符串
                real_time_status = data.get('realTimeStatus', {})
                players_online = real_time_status.get('playersOnline', 'N/A')
                players_max = real_time_status.get('playersMax', 'N/A')
                motd_clean = real_time_status.get('motdClean', ['', ''])
                best_time = data.get('BestTime', '')

                log(f"从数据中提取: players_online={players_online}, players_max={players_max}, motd_clean={motd_clean}, best_time={best_time}")
                
                # 检查QLabel对象是否存在
                if not BloretServerOnlineNumber:
                    log("BloretServerOnlineNumber QLabel not found.")
                if not BloretServerText0:
                    log("BloretServerText0 QLabel not found.")
                if not BloretServerText1:
                    log("BloretServerText1 QLabel not found.")
                if not BloretServer_BestTime:
                    log("BloretServer_BestTime QLabel not found.")

                # 正确地将数字转换为字符串进行显示
                BloretServerOnlineNumber.setText(f"{players_online} / {players_max}")
                
                if motd_clean and len(motd_clean) > 0:
                    BloretServerText0.setText(str(motd_clean[0]))
                else:
                    BloretServerText0.setText("暂无公告")

                if motd_clean and len(motd_clean) > 1:
                    BloretServerText1.setText(str(motd_clean[1]))
                else:
                    BloretServerText1.setText("")

                BloretServer_BestTime.setText(str(best_time))
                log(f"UI已更新: BloretServerOnlineNumber='{players_online} / {players_max}', BloretServerText0='{motd_clean[0] if motd_clean and len(motd_clean) > 0 else '暂无公告'}', BloretServerText1='{motd_clean[1] if motd_clean and len(motd_clean) > 1 else ''}'")
            except Exception as e:
                log(f"处理服务器数据时出错: {str(e)}")
                BloretServerOnlineNumber.setText("N/A")
                BloretServerText0.setText("数据处理错误")
                BloretServerText1.setText("")
                BloretServer_BestTime.setText("")
    
    # 调用getServerData并传入回调函数
    getServerData("Bloret", callback=update_server_info)

def setup_download_load_ui(self, widget):
    '''
    ### 设定 Bloret Launcher 下载界面加载时 UI 布局和操作。
    # ⚠️ 已弃用
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    loading_label = widget.findChild(QLabel, "loading_label")
    if loading_label:
        self.setup_loading_gif(loading_label)

def setup_download_old_ui(self,widget,LM_Download_Way_list,ver_id_bloret,homeInterface):
    '''
    设定 Bloret Launcher 下载界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    download_way_choose = widget.findChild(ComboBox, "download_way_choose")  # 获取 download_way_choose 元素
    LM_download_way_choose = widget.findChild(ComboBox, "LM_download_way_choose")
    download_way_F5_button = widget.findChild(QPushButton, "download_way_F5")
    minecraft_choose = widget.findChild(ComboBox, "minecraft_choose")
    show_way = widget.findChild(ComboBox, "show_way")
    download_button = widget.findChild(QPushButton, "download")
    if show_way:
        show_way.clear()
        show_way.addItems([i18nText("百络谷支持版本"), i18nText("正式版本"), i18nText("快照版本"), i18nText("远古版本")])
        show_way.setCurrentText(i18nText("百络谷支持版本"))
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
    notification_switch = widget.findChild(SwitchButton, "Notification")
    if notification_switch:
        notification_switch.setChecked(True)  # 将Notification开关设置成开

    fabric_ver = [i18nText("不安装")]
    if not self.config.get('localmod', False):
        response = requests.get("https://bmclapi2.bangbang93.com/fabric-meta/v2/versions/loader")
        if response.status_code == 200:
            data = response.json()
            for item in data:
                fabric_ver.append(item["version"])
    else:
        log(i18nText("本地模式已启用，获取 Minecraft 版本 的过程已跳过。"))

    fabric_choose = widget.findChild(ComboBox, "Fabric_choose")
    if fabric_choose:
        fabric_choose.clear()
        fabric_choose.addItems(fabric_ver)
        fabric_choose.setCurrentText(i18nText("不安装"))

    # 设置minecraft_choose下拉框
    if minecraft_choose:
        # 清空并添加版本列表
        minecraft_choose.clear()
        # 确保ver_id_bloret不为None且不为空
        if ver_id_bloret is not None and len(ver_id_bloret) > 0:
            minecraft_choose.addItems(ver_id_bloret)
        else:
            # 如果ver_id_bloret为空，则添加默认版本列表
            minecraft_choose.addItems(["1.21.7", "1.21.8"])
            
    vername_edit = widget.findChild(LineEdit, "vername_edit")
    if minecraft_choose and vername_edit:
        minecraft_choose.currentTextChanged.connect(vername_edit.setText)

    # 默认填入百络谷支持版本的第一项
    if minecraft_choose:
        vername_edit = widget.findChild(LineEdit, "vername_edit")
        # 只有当ver_id_bloret有效且有内容时才设置第一个版本为默认值
        if vername_edit and ver_id_bloret is not None and len(ver_id_bloret) > 0:
            vername_edit.setText(ver_id_bloret[0])
        # 如果ver_id_bloret为空，则设置默认值为"1.21.7"
        elif vername_edit:
            vername_edit.setText("1.21.7")

    Customize_choose = widget.findChild(QPushButton, "Customize_choose")
    if Customize_choose:
        Customize_choose.clicked.connect(lambda: self.on_customize_choose_clicked(widget))

    Customize_add = widget.findChild(QPushButton, "Customize_add")
    if Customize_add:
        Customize_add.clicked.connect(lambda: self.on_customize_add_clicked(widget,homeInterface))

    add_mrpack_button = widget.findChild(QPushButton, "add_mrpack_button")
    if add_mrpack_button:
        add_mrpack_button.clicked.connect(lambda: add_mrpack(widget))

def setup_tools_ui(self, widget):
    '''
    设定 Bloret Launcher 小工具界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    name2uuid_button = widget.findChild(QPushButton, "name2uuid_player_Button")
    if name2uuid_button:
        name2uuid_button.clicked.connect(lambda: query_player_uuid(self,widget))
    search_name_button = widget.findChild(QPushButton, "search_name_button")
    if search_name_button:
        search_name_button.clicked.connect(lambda: query_player_name(self,widget))
    skin_search_button = widget.findChild(QPushButton, "skin_search_button")
    if skin_search_button:
        skin_search_button.clicked.connect(lambda: query_player_skin(self,widget))
    name_copy_button = widget.findChild(QPushButton, "search_name_copy")
    if name_copy_button:
        name_copy_button.clicked.connect(lambda: copy_name_to_clipboard(self))
    uuid_copy_button = widget.findChild(QPushButton, "pushButton_5")
    if uuid_copy_button:
        uuid_copy_button.clicked.connect(lambda: copy_uuid_to_clipboard(self))
    skin_copy_button = widget.findChild(QPushButton, "search_skin_copy")
    if skin_copy_button:
        skin_copy_button.clicked.connect(lambda: copy_skin_to_clipboard(self))
    cape_copy_button = widget.findChild(QPushButton, "search_cape_copy")
    if cape_copy_button:
        cape_copy_button.clicked.connect(lambda: copy_cape_to_clipboard(self))

def setup_passport_ui(self, widget, server_ip, homeInterface):
    '''
    # 设定 Bloret Launcher 通行证界面 UI 布局和操作。
    包括：
     - [x] 微软登录与离线登录
     - [x] 百络谷通行证登录
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    player_name_edit = widget.findChild(QLineEdit, "player_name")
    player_name_set_button = widget.findChild(QPushButton, "player_name_set")
    login_way_combo = widget.findChild(ComboBox, "player_login_way")
    login_way_choose = widget.findChild(ComboBox, "login_way")
    name_combo = widget.findChild(ComboBox, "playername")
    Bloret_PassPort_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
    Bloret_PassPort_logout = widget.findChild(QPushButton, "Bloret_PassPort_logout")
    Bloret_PassPort_login = widget.findChild(QPushButton, "Bloret_PassPort_login")
    go_Minecraft_Account_To_Bloret_PassPort_Cloud_to = widget.findChild(QPushButton, "go_Minecraft_Account_To_Bloret_PassPort_Cloud_to")
    go_Minecraft_Account_To_Bloret_PassPort_Cloud_from = widget.findChild(QPushButton, "go_Minecraft_Account_To_Bloret_PassPort_Cloud_from")

    if player_name_edit and player_name_set_button:
        player_name_set_button.clicked.connect(lambda: self.on_player_name_set_clicked(widget))
        log(i18nText("已连接 player_name_set_button 点击事件"))

    if self.cmcl_data:
        log(i18nText("成功读取 cmcl.json 数据"))
        
        if login_way_combo:
            login_way_choose.clear()
            login_way_choose.addItems([i18nText("离线登录"), i18nText("微软登录")])
            login_way_choose.setCurrentText(self.login_mod)
            login_way_choose.setCurrentIndex(0)

        if login_way_combo:
            login_way_combo.clear()
            login_way_combo.addItem(str(self.login_mod))
            login_way_combo.setCurrentIndex(0)
            log(f"设置 login_way_combo 当前索引为: {self.login_mod}")

        if name_combo:
            name_combo.clear()
            name_combo.addItem(self.player_name)
            name_combo.setCurrentIndex(0)
            log(f"设置 name_combo 当前索引为: {self.player_name}")
    else:
        log(i18nText("读取 cmcl.json 失败"))
    
    login_button = widget.findChild(QPushButton, "login")
    if login_button:
        login_button.clicked.connect(lambda: self.handle_login(widget))
    Bloret_PassPort_view_BBBS = widget.findChild(QPushButton, "Bloret_PassPort_view_BBBS")
    reg_Bloret_PassPort = widget.findChild(QPushButton, "reg_Bloret_PassPort")
    if Bloret_PassPort_UserName:
        Bloret_PassPort_UserName.setText(self.config.get('Bloret_PassPort_UserName', i18nText('未登录')))
    if Bloret_PassPort_logout:
        Bloret_PassPort_logout.clicked.connect(lambda: Bloret_PassPort_Account_logout(self,homeInterface))
    if Bloret_PassPort_login:
        Bloret_PassPort_login.clicked.connect(lambda: Bloret_PassPort_Account_login())
    if Bloret_PassPort_view_BBBS:
        Bloret_PassPort_view_BBBS.clicked.connect(lambda: open_BBBS_link(server_ip))
    if reg_Bloret_PassPort:
        reg_Bloret_PassPort.clicked.connect(lambda: open_BBBS_Reg_link())
    if go_Minecraft_Account_To_Bloret_PassPort_Cloud_to:
        go_Minecraft_Account_To_Bloret_PassPort_Cloud_to.clicked.connect(lambda: sync_mc_account_to_bloret_passport(self))

    if go_Minecraft_Account_To_Bloret_PassPort_Cloud_from:
        go_Minecraft_Account_To_Bloret_PassPort_Cloud_from.clicked.connect(lambda: sync_bloret_passport_account_to_mc(self))

def setup_settings_ui(self, widget):
    '''
    设定 Bloret Launcher 设置界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 设置设置界面的UI元素
    log_clear_button = widget.findChild(QPushButton, "log_clear_button")
    if log_clear_button:
        log_clear_button.clicked.connect(lambda: clear_log_files(self,log_clear_button))
        self.update_log_clear_button_text(log_clear_button)

    # 添加深浅色模式选择框
    light_dark_choose = widget.findChild(ComboBox, "light_dark_choose")
    if light_dark_choose:
        light_dark_choose.clear()
        light_dark_choose.addItems([i18nText("跟随系统"), i18nText("深色模式"), i18nText("浅色模式")])
        light_dark_choose.currentTextChanged.connect(self.on_light_dark_changed)

    # 添加语言选择框
    language_choose = widget.findChild(ComboBox, "language_Choose")
    if language_choose:
        language_choose.clear()
        # 从Default.json文件中读取语言列表
        try:
            with open(os.path.join('lang', 'Default.json'), 'r', encoding='utf-8') as f:
                default_lang_data = json.load(f)
            # 提取语言项并显示name值
            language_items = []
            language_map = {}  # 用于存储显示名称到语言代码的映射
            for lang_code, lang_info in default_lang_data.get('lang', {}).items():
                display_name = lang_info.get('name', lang_code)
                language_items.append(display_name)
                language_map[display_name] = lang_code
            
            language_choose.addItems(language_items)
            
            # 设置当前选中项
            current_lang_code = self.config.get("language", "zh-cn")
            current_lang_name = default_lang_data.get('lang', {}).get(current_lang_code, {}).get('name', current_lang_code)
            language_choose.setCurrentText(current_lang_name)
            
            # 连接更改事件
            def on_language_changed(display_name):
                # 获取语言代码
                lang_code = language_map.get(display_name, display_name)
                self.config.update(language=lang_code)
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                log(f"语言设置已更改为: {lang_code}")
            
            language_choose.currentTextChanged.connect(on_language_changed)
        except Exception as e:
            log(f"读取语言配置文件失败: {e}")
            # 出错时使用原有逻辑
            language_choose.addItems(["zh-cn", "en-GB"])
            language_choose.setCurrentText(self.config.get("language", "zh-cn"))
            language_choose.currentTextChanged.connect(lambda language: (
                self.config.update(language=language),
                open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
                log(f"语言设置已更改为: {language}")
            ))

    size_choose = widget.findChild(SpinBox, "Size_Choose")
    if size_choose:
        size_choose.setValue(self.config.get("size", 100))
        size_choose.valueChanged.connect(lambda value: (
            self.config.update(size=value),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
        ))

    MaxThread_SpinBox = widget.findChild(SpinBox, "MaxThread_SpinBox")
    if MaxThread_SpinBox:
        MaxThread_SpinBox.setValue(self.config.get("MaxThread", 2000))
        MaxThread_SpinBox.valueChanged.connect(lambda value: (
            self.config.update(MaxThread=value),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
        ))

    repeat_run_button = widget.findChild(SwitchButton, "repeat_run_button")
    if repeat_run_button:
        repeat_run_button.setChecked(self.config.get('repeat_run', False))
        repeat_run_button.checkedChanged.connect(lambda state: (
            self.config.update(repeat_run=state),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
            log(f"重复运行设置已更改为: {'启用' if state else '禁用'}")
        ))
    show_runtime_do_button = widget.findChild(SwitchButton, "show_runtime_do_button")
    if show_runtime_do_button:
        show_runtime_do_button.setChecked(self.config.get('show_runtime_do', False))
        show_runtime_do_button.checkedChanged.connect(lambda state: (
            self.config.update(show_runtime_do=state),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
            log(f"显示软件打开过程: {'启用' if state else '禁用'}")
        ))
    BL_version = widget.findChild(QLabel, "BL_version")
    if BL_version:
        BL_version.setText(f"{self.config.get('ver', '未知')}")
    localmod_button = widget.findChild(SwitchButton, "localmod_button")
    if localmod_button:
        localmod_button.setChecked(self.config.get('localmod', False))
        localmod_button.checkedChanged.connect(lambda state: (
            self.config.update(localmod=state),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
            log(f"本地模式: {'启用' if state else '禁用'}")
        ))
    home_show_login_mod_button = widget.findChild(SwitchButton, "home_show_login_mod_button")
    if home_show_login_mod_button:
        home_show_login_mod_button.setChecked(self.config.get('home_show_login_mod', False))
        home_show_login_mod_button.checkedChanged.connect(lambda state: (
            self.config.update(home_show_login_mod=state),
            open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
            log(f"在首页上 显示 Minecraft 账户登录方式: {'启用' if state else '禁用'}")
        ))
    
    Self_starting = widget.findChild(SwitchButton, "Self_starting")
    if Self_starting:
        Self_starting.setChecked(self.config.get("self-starting", False))
        Self_starting.checkedChanged.connect(lambda val: on_self_starting_changed(val))
    else:
        log(i18nText("未找到 Self_starting 控件"))

def setup_multiplayer_ui(self, widget, server_ip):
    """设定 Bloret Launcher 多人联机界面 UI 布局和操作"""
    # 获取IPv6地址
    ipv6_address_str = get_ipv6_address()
    log(f"检测到的IPv6地址: {ipv6_address_str if ipv6_address_str else '未找到可用IPv6地址'}")
    
    ipv6_address_label = widget.findChild(QLabel, "ipv6_address")
    if ipv6_address_label:
        if ipv6_address_str:
            # 显示缩短的IPv6地址（只显示前8个字符）
            ipv6_display = f"{ipv6_address_str[:8]}..." if len(ipv6_address_str) > 8 else ipv6_address_str
            ipv6_address_label.setText(ipv6_display)
        else:
            ipv6_address_label.setText(i18nText("无法获取IPv6地址"))
            log(i18nText("未找到可用的IPv6地址，IPv6功能将被禁用"))

    get_ipv6_btn = widget.findChild(QPushButton, "GetIPV6AddressButton")
    if get_ipv6_btn:
        # 根据是否有IPv6地址设置按钮状态
        if ipv6_address_str:
            get_ipv6_btn.setEnabled(True)
            get_ipv6_btn.setToolTip(i18nText("点击显示IPv6联机对话框"))
        else:
            get_ipv6_btn.setEnabled(False)
            get_ipv6_btn.setToolTip(i18nText("未检测到IPv6地址，请确保您的网络支持IPv6"))
        
        # 断开可能存在的重复连接
        try:
            get_ipv6_btn.clicked.disconnect()
        except:
            pass
            
        # 连接按钮点击事件
        get_ipv6_btn.clicked.connect(lambda: show_ipv6_dialog(self, ipv6_address_str))
    
    # 设置初始状态
    online_client_time_label = widget.findChild(QLabel, "OnlineClient_ClientTime")
    online_client_address_label = widget.findChild(QLabel, "OnlineClient_address")
    
    if online_client_time_label:
        online_client_time_label.setText("--:--")
        log(i18nText("初始化OnlineClient_ClientTime标签"))
    else:
        log(i18nText("未找到OnlineClient_ClientTime标签"))
    
    if online_client_address_label:
        online_client_address_label.setText(i18nText("未连接"))
        log(i18nText("初始化OnlineClient_address标签"))
    else:
        log(i18nText("未找到OnlineClient_address标签"))
    
    # 连接StartOnlineClient按钮
    start_online_client_btn = widget.findChild(QPushButton, "StartOnlineClient")
    if start_online_client_btn:
        # 断开可能存在的重复连接
        try:
            start_online_client_btn.clicked.disconnect()
        except:
            pass
        start_online_client_btn.clicked.connect(lambda: start_online_client(self, server_ip))
        log(i18nText("已连接StartOnlineClient按钮"))
    else:
        log(i18nText("未找到StartOnlineClient按钮"))


def start_online_client(parent, server_ip):
    """启动在线客户端服务"""
    # 创建端口输入对话框
    port_dialog = MessageBoxBase(parent)
    port_dialog.setWindowTitle(i18nText("开启联机服务"))
    
    port_label = BodyLabel(i18nText("请输入您的 Minecraft 端口"))
    port_input = LineEdit()
    port_input.setPlaceholderText(i18nText("默认端口: 25565"))
    port_input.setText("25565")  # 设置默认端口
    
    port_dialog.viewLayout.addWidget(port_label)
    port_dialog.viewLayout.addWidget(port_input)
    
    # 添加动图
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtGui import QMovie
    gif_label = QLabel()
    movie = QMovie("ui/icon/OnlineClient.gif")
    gif_label.setMovie(movie)
    movie.start()
    
    port_dialog.viewLayout.addWidget(gif_label)
    
    port_dialog.yesButton.setText(i18nText("确认"))
    port_dialog.cancelButton.setText(i18nText("取消"))
    
    def handle_port_confirm():
        port = port_input.text().strip()
        if not port.isdigit():
            InfoBar.error(
                title=i18nText('输入错误'),
                content=i18nText('请输入有效的端口号'),
                parent=parent
            )
            return False
        
        # 调用OnlineClient函数
        try:
            # 将端口转换为整数再传递
            port_int = int(port)
            connection_address = OnlineClient(server_ip, port_int)
            
            # 检查是否返回了错误信息
            if connection_address.startswith(i18nText("权限错误：")) or connection_address.startswith(i18nText("安全软件阻止：")):
                InfoBar.error(
                    title=i18nText('启动失败'),
                    content=connection_address,
                    parent=parent,
                    duration=10000  # 显示更长时间以便用户阅读
                )
                return False
            elif connection_address.startswith(i18nText("启动失败:")) or connection_address == i18nText("网络请求失败") or connection_address == i18nText("配置文件不存在") or connection_address == i18nText("frpc程序不存在") or connection_address == i18nText("获取连接信息失败"):
                InfoBar.error(
                    title=i18nText('启动失败'),
                    content=connection_address,
                    parent=parent
                )
                return False
            
            # 显示连接地址对话框
            show_connection_address_dialog(parent, connection_address, port)
            return True
        except Exception as e:
            InfoBar.error(
                title=i18nText('启动失败'),
                content=f'启动联机服务时出错: {str(e)}',
                parent=parent
            )
            return False
    
    port_dialog.yesButton.clicked.connect(handle_port_confirm)
    port_dialog.exec_()


def show_connection_address_dialog(parent, connection_address, port):
    """显示连接地址对话框"""
    # 创建结果显示对话框
    result_dialog = MessageBoxBase(parent)
    result_dialog.setWindowTitle(i18nText("联机服务已启动"))
    
    address_label = StrongBodyLabel(connection_address)
    address_label.setAlignment(Qt.AlignCenter)
    
    instruction_label = CaptionLabel(i18nText("按下确认键复制到剪贴板，然后发给好友，在 Minecraft 客户端中添加服务器并加入。"))
    instruction_label.setAlignment(Qt.AlignCenter)
    
    # 添加动图
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtGui import QMovie
    gif_label = QLabel()
    movie = QMovie("ui/icon/OnlineClient.gif")
    gif_label.setMovie(movie)
    movie.start()
    
    result_dialog.viewLayout.addWidget(address_label)
    result_dialog.viewLayout.addWidget(instruction_label)
    result_dialog.viewLayout.addWidget(gif_label)
    
    result_dialog.yesButton.setText(i18nText("确认"))
    result_dialog.cancelButton.hide()  # 隐藏取消按钮
    
    def handle_result_confirm():
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(connection_address)
        InfoBar.success(
            title=i18nText('复制成功'),
            content=i18nText('联机地址已复制到剪贴板'),
            parent=parent
        )
        
        # 更新界面上的地址和时间显示
        # 获取界面上的时间和地址标签
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import QTimer, QDateTime
        
        # 通过parent.window()获取主窗口，再查找标签
        # 这样可以确保在正确的窗口中查找组件
        main_window = parent.window()
        online_client_time_label = main_window.findChild(QLabel, "OnlineClient_ClientTime")
        online_client_address_label = main_window.findChild(QLabel, "OnlineClient_address")
        
        if online_client_address_label:
            online_client_address_label.setText(connection_address)
            log(f"已更新连接地址标签: {connection_address}")
        else:
            # 如果通过window()找不到，尝试直接在parent中查找
            online_client_address_label = parent.findChild(QLabel, "OnlineClient_address")
            if online_client_address_label:
                online_client_address_label.setText(connection_address)
                log(f"已更新连接地址标签: {connection_address}")
            else:
                log(i18nText("未找到OnlineClient_address标签"))
        
        # 启动计时器更新连接时长
        if online_client_time_label:
            
            # 记录开始时间
            start_time = QDateTime.currentDateTime()
            
            # 创建定时器每秒更新时间显示
            timer = QTimer()
            timer.timeout.connect(lambda: update_connection_time(online_client_time_label, start_time))
            timer.start(1000)  # 每秒更新一次
            
            # 将定时器保存到main_window对象中，以便后续可以停止它
            main_window.online_client_timer = timer
            main_window.online_client_start_time = start_time
            
            # 立即更新一次时间显示
            update_connection_time(online_client_time_label, start_time)
            log(i18nText("已启动连接时长计时器"))
        else:
            # 如果通过window()找不到，尝试直接在parent中查找
            online_client_time_label = parent.findChild(QLabel, "OnlineClient_ClientTime")
            if online_client_time_label:
                # 记录开始时间
                start_time = QDateTime.currentDateTime()
                
                # 创建定时器每秒更新时间显示
                timer = QTimer()
                timer.timeout.connect(lambda: update_connection_time(online_client_time_label, start_time))
                timer.start(1000)  # 每秒更新一次
                
                # 将定时器保存到parent对象中，以便后续可以停止它
                parent.online_client_timer = timer
                parent.online_client_start_time = start_time
                
                # 立即更新一次时间显示
                update_connection_time(online_client_time_label, start_time)
                log(i18nText("已启动连接时长计时器"))
            else:
                log(i18nText("未找到OnlineClient_ClientTime标签"))
    
    result_dialog.yesButton.clicked.connect(handle_result_confirm)
    result_dialog.exec_()


def update_connection_time(time_label, start_time):
    """更新连接时长显示"""
    from PyQt5.QtCore import QDateTime
    
    # 计算已连接的时间
    current_time = QDateTime.currentDateTime()
    elapsed = start_time.secsTo(current_time)
    
    # 转换为小时、分钟和秒
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    
    # 格式化时间显示
    time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if time_label:
        # 确保标签存在后再更新
        time_label.setText(time_text)
        log(f"更新连接时长显示: {time_text}")
    else:
        log(i18nText("未找到OnlineClient_ClientTime标签，无法更新连接时长显示"))


def get_ipv6_address():
    """获取本机可用的IPv6地址"""
    try:
        # 获取所有网络接口的地址信息
        for addrinfo in socket.getaddrinfo(socket.gethostname(), None):
            ip_address = addrinfo[4][0]
            # 检查是否为IPv6地址且不是本地回环地址或链路本地地址
            if ':' in ip_address and not ip_address.startswith('::1') and \
               not ip_address.startswith('fe80::') and \
               not ip_address.startswith('ff00::'):
                # 尝试连接互联网以确认地址是否可达
                s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                s.settimeout(1)
                # 使用 Google 的公共 DNS 服务器进行连接测试
                s.connect(('2001:4860:4860::8888', 80))
                s.close()
                return ip_address
        return None
    except Exception as e:
        log(f"获取IPv6地址失败: {str(e)}")
        return None


def show_ipv6_dialog(parent, ipv6_address):
    """显示IPv6联机对话框"""
    # 创建端口输入对话框
    port_dialog = MessageBoxBase(parent)
    port_dialog.setWindowTitle(i18nText("IPV6 联机"))
    
    port_label = BodyLabel(i18nText("请输入您的 Minecraft 端口"))
    port_input = LineEdit()
    port_input.setPlaceholderText(i18nText("默认端口: 25565"))
    port_input.setText("25565")  # 设置默认端口
    
    port_dialog.viewLayout.addWidget(port_label)
    port_dialog.viewLayout.addWidget(port_input)
    
    # 添加动图
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtGui import QMovie
    gif_label = QLabel()
    movie = QMovie("ui/icon/OnlineClient.gif")
    gif_label.setMovie(movie)
    movie.start()
    
    port_dialog.viewLayout.addWidget(gif_label)
    
    port_dialog.yesButton.setText(i18nText("确认"))
    port_dialog.cancelButton.setText(i18nText("取消"))
    
    def handle_port_confirm():
        port = port_input.text().strip()
        if not port.isdigit():
            InfoBar.error(
                title=i18nText('输入错误'),
                content=i18nText('请输入有效的端口号'),
                parent=parent
            )
            return
        
        # 创建结果显示对话框
        result_dialog = MessageBoxBase(parent)
        result_dialog.setWindowTitle(i18nText("IPV6 联机"))
        
        address_label = StrongBodyLabel(f"[{ipv6_address}]:{port}")
        address_label.setAlignment(Qt.AlignCenter)
        
        instruction_label = CaptionLabel(i18nText("按下确认键复制到剪贴板，然后发给好友，在 Minecraft 客户端中添加服务器并加入。"))
        instruction_label.setAlignment(Qt.AlignCenter)
        
        # 添加动图
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtGui import QMovie
        gif_label = QLabel()
        movie = QMovie("ui/icon/OnlineClient.gif")
        gif_label.setMovie(movie)
        movie.start()
        
        result_dialog.viewLayout.addWidget(address_label)
        result_dialog.viewLayout.addWidget(instruction_label)
        result_dialog.viewLayout.addWidget(gif_label)
        
        result_dialog.yesButton.setText(i18nText("确认"))
        result_dialog.cancelButton.hide()  # 隐藏取消按钮
        
        def handle_result_confirm():
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(f"[{ipv6_address}]:{port}")
            InfoBar.success(
                title=i18nText('复制成功'),
                content=i18nText('IPV6地址和端口已复制到剪贴板'),
                parent=parent
            )
        
        result_dialog.yesButton.clicked.connect(handle_result_confirm)
        result_dialog.exec_()
    
    port_dialog.yesButton.clicked.connect(handle_port_confirm)
    
    port_dialog.exec_()

def setup_info_ui(self, widget):
    '''
    设定 Bloret Launcher 关于界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    github_org_button = widget.findChild(QPushButton, "pushButton_2")
    if github_org_button:
        github_org_button.clicked.connect(open_github_bloret)
    github_project_button = widget.findChild(QPushButton, "button_github")
    if github_project_button:
        github_project_button.clicked.connect(open_github_bloret_Launcher)
    qq_group_button = widget.findChild(QPushButton, "pushButton")
    if qq_group_button:
        qq_group_button.clicked.connect(open_qq_link)
    qq_icon = widget.findChild(QLabel, "QQ_icon")
    if qq_icon:
        qq_icon.setPixmap(QPixmap("ui/icon/qq.png"))
    BLC_QQ = widget.findChild(QPushButton, "BLC_QQ")
    if BLC_QQ:
        BLC_QQ.clicked.connect(open_BLC_qq_link)

def setup_version_ui(self, widget, minecraft_list, customize_list, MINECRAFT_DIR, homeInterface):
    '''
    设定 Bloret Launcher 版本管理界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    minecraft_list_NUM = len(minecraft_list)
    customize_list_NUM = len(customize_list)
    Minecraft_list = widget.findChild(SmoothScrollArea, "Minecraft_list")
    if Minecraft_list:
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        if minecraft_list_NUM != 0 or customize_list_NUM != 0:
            if minecraft_list_NUM != 0:
                title_label = SubtitleLabel(i18nText("Minecraft 核心"), parent=scroll_widget)
                scroll_layout.addWidget(title_label)

                for i in range(minecraft_list_NUM):
                    card = CardWidget(scroll_widget)
                    card.setMaximumWidth(659)  # 设置最大宽度
                    label = StrongBodyLabel(minecraft_list[i], card)
                    layout = QVBoxLayout(card)
                    layout.addWidget(label)

                    def create_minecraft_context_menu(pos, label_now, card_now, version_name=minecraft_list[i]):
                        menu = RoundMenu()
                        info_action = Action(FluentIcon.INFO, version_name, triggered=lambda: self.run_cmcl(version_name))
                        launch_action = Action(FluentIcon.PLAY, i18nText('启动'), triggered=lambda: self.run_cmcl(version_name))
                        rename_action = Action(FluentIcon.EDIT, i18nText('更名'), triggered=lambda: Change_minecraft_version_name(self,version_name,label_now, MINECRAFT_DIR,homeInterface))
                        delete_action = Action(FluentIcon.DELETE, i18nText('删除'), triggered=lambda: delete_minecraft_version(self,version_name,label_now, card_now, MINECRAFT_DIR, homeInterface))
                        folder_action = Action(FluentIcon.FOLDER, i18nText('打开文件位置'), triggered=lambda: open_minecraft_version_folder(self,version_name,MINECRAFT_DIR))

                        menu.addActions([
                            info_action,
                            launch_action,
                            rename_action,
                            delete_action,
                            folder_action
                        ])

                        global_pos = card_now.mapToGlobal(pos)
                        menu.exec_(global_pos)

                    card.setContextMenuPolicy(Qt.CustomContextMenu)
                    card.customContextMenuRequested.connect(lambda pos, v=minecraft_list[i], label_now=label, card_now=card: create_minecraft_context_menu(pos, label_now, card_now, v))
                    scroll_layout.addWidget(card)

            if customize_list_NUM != 0:
                title_label_custom = SubtitleLabel(i18nText("自定义启动"), parent=scroll_widget)
                scroll_layout.addWidget(title_label_custom)

                for i in range(customize_list_NUM):
                    card = CardWidget(scroll_widget)
                    card.setMaximumWidth(659)  # 设置最大宽度
                    label = StrongBodyLabel(f"{customize_list[i]}", card)
                    layout = QVBoxLayout(card)
                    layout.addWidget(label)

                    def create_customize_context_menu(pos, label_now, card_now, version_name=customize_list[i]):
                        menu = RoundMenu()
                        info_action = Action(FluentIcon.INFO, version_name, triggered=lambda: self.run_cmcl(version_name))
                        launch_action = Action(FluentIcon.PLAY, i18nText('启动'), triggered=lambda: self.run_cmcl(version_name))
                        rename_action = Action(FluentIcon.EDIT, i18nText('更名'), triggered=lambda: Change_Customize_name(self,version_name, label_now, homeInterface))
                        delete_action = Action(FluentIcon.DELETE, i18nText('删除'), triggered=lambda: delete_Customize(self,version_name, label_now, card_now,customize_list,homeInterface))

                        menu.addActions([
                            info_action,
                            launch_action,
                            rename_action,
                            delete_action
                        ])

                        global_pos = card_now.mapToGlobal(pos)
                        menu.exec_(global_pos)

                    card.setContextMenuPolicy(Qt.CustomContextMenu)
                    card.customContextMenuRequested.connect(lambda pos, v=customize_list[i], label_now=label, card_now=card: create_customize_context_menu(pos, label_now, card_now, v))
                    scroll_layout.addWidget(card)

        scroll_layout.addStretch(1)

        Minecraft_list.setWidget(scroll_widget)
        Minecraft_list.setWidgetResizable(True)

def setup_BBS_ui(self, widget, server_ip):
    '''
    设定 Bloret Launcher 社区界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 绑定 OpenBBS 按钮点击事件
    open_bbs_button = widget.findChild(QPushButton, "OpenBBS")
    if open_bbs_button:
        open_bbs_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"{server_ip}bbs")))

    # 从服务器获取 BBS 数据
    try:
        response = requests.get(f"{server_ip}api/part")
        response.raise_for_status()  # 检查请求是否成功
        bbs_part = response.json()  # 存储数据到 bbs_part 变量
    except requests.RequestException as e:
        log(f"无法获取 BBS 数据: {e}", logging.ERROR)
        bbs_part = {}  # 请求失败时初始化为空字典

    # 找到名为 BBS_list 的 SmoothScrollArea
    BBS_list = widget.findChild(SmoothScrollArea, "BBS_list")
    if not BBS_list:
        log(i18nText("未找到 BBS_list SmoothScrollArea"), logging.ERROR)
        return

    # 清空 BBS_list 现有内容
    if BBS_list.widget():
        BBS_list.widget().deleteLater()

    # 创建新的内容容器和布局
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)

    # 遍历 bbs_part 的每个键作为板块标题
    for part_title, posts in bbs_part.items():
        # 创建 SubtitleLabel 并设置文本
        subtitle_label = SubtitleLabel(part_title, parent=scroll_widget)
        scroll_layout.addWidget(subtitle_label)

        # 根据帖子数量创建对应的 CardWidget
        for post in posts:
            card_widget = CardWidget(parent=scroll_widget)
            card_layout = QVBoxLayout(card_widget)

            # 创建 StrongBodyLabel 并设置帖子标题
            title_label = StrongBodyLabel(post['title'], parent=card_widget)
            card_layout.addWidget(title_label)

            # 创建 BodyLabel 并设置帖子文本为 Markdown 形式显示
            text_label = BodyLabel(post.get('text', ''), parent=card_widget)
            text_label.setTextFormat(Qt.MarkdownText)
            text_label.setOpenExternalLinks(True)  # 允许打开外部链接
            if len(text_label.text()) > 30:
                text_label.setText(text_label.text()[:50] + '...')
            card_layout.addWidget(text_label)

            # 创建 PushButton 在浏览器中打开帖子
            open_button = PushButton(i18nText('在浏览器中打开'), parent=card_widget)
            open_button.clicked.connect(lambda _, pt=part_title, t=post['title']: QDesktopServices.openUrl(QUrl(f"{server_ip}bbs/{pt}/{t}")))
            card_layout.addWidget(open_button)

            scroll_layout.addWidget(card_widget)

    # 设置 scroll_widget 为 BBS_list 的内容
    BBS_list.setWidget(scroll_widget)
    BBS_list.setWidgetResizable(True)
    
def on_search_mod_clicked(self, mod_list, search_term=''):
    # 显示进度条
    if mod_list:
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        loading = IndeterminateProgressBar(start=True)
        scroll_layout.addWidget(loading, alignment=Qt.AlignCenter)
        mod_list.setWidget(scroll_widget)
        mod_list.setWidgetResizable(True)
    # 执行搜索
    results = search_mods(search_term)
    log(f"1搜索结果: {results}")
    on_search_mod_finish(self, results, mod_list, loading)

def on_search_mod_finish(self, results, mod_list, loading):
    """处理模组搜索结果并更新UI
    
    Args:
        results: 从Modrinth API获取的模组搜索结果
        mod_list: SmoothScrollArea控件，用于显示模组列表
        loading: 加载进度条控件
    """
    if results:
        if mod_list:
            # 显示加载进度通知
            notify(progress={
                'title': i18nText('正在加载 Mod 数据...'),
                'status': i18nText('正在加载 Mod 数据...'),
                'value': '0',
                'valueStringOverride': '0/' + str(len(results)),
                'icon': os.path.join(os.getcwd(), 'bloret.ico')
            })
            
            # 创建滚动区域和布局
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            i = 0
            for mod in results:
                # 更新加载进度
                update_progress({'value': i / len(results), 'valueStringOverride': f'{i + 1}/{len(results)}', 'status': f"正在加载 Mod 数据... {i + 1}/{len(results)}"})
                i = i + 1
                
                # 创建模组卡片
                card = CardWidget()
                card.setMaximumWidth(659)
                # 设置模组标题和描述
                # 创建模组标题标签（使用StrongBodyLabel样式，字体加粗）
                title_label = StrongBodyLabel(mod["title"], card)
                # 创建模组描述标签（使用BodyLabel样式，普通字体）
                body_label = BodyLabel(mod["description"], card)
                # 卡片宽度锁定 550
                body_label.setMinimumWidth(550)
                body_label.setMaximumWidth(550)
                # 设置尺寸策略：水平方向可扩展，垂直方向保持首选大小
                body_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                # 设置文本格式为Markdown，支持Markdown语法渲染
                body_label.setTextFormat(Qt.MarkdownText)  # 支持Markdown格式
                # 允许点击描述中的链接打开外部浏览器
                body_label.setOpenExternalLinks(True)  # 允许打开外部链接
                # 启用自动换行功能，使长文本能自动换行显示
                body_label.setWordWrap(True)  # 自动换行

                # 加载模组图标
                icon_label = ImageLabel()
                icon_label.setBorderRadius(8, 8, 8, 8)
                icon_url = mod.get('icon_url')
                pixmap = QPixmap()
                icon_loaded = mod.get('icon_data') is not None
                
                if not icon_loaded:
                    log(f"未能加载图标: {mod.get('title', '未知mod')}，URL: {mod.get('icon_url', '未提供')}")
                
                # 尝试从URL下载图标
                if icon_url:
                    try:
                        response = requests.get(icon_url, timeout=5)
                        if response.status_code == 200:
                            icon_loaded = pixmap.loadFromData(response.content)
                        else:
                            log(f"⚠️ 图片下载失败: HTTP {response.status_code}, URL: {icon_url}")
                    except Exception as e:
                        log(f"⚠️ 图片下载异常: {str(e)}, URL: {icon_url}")
                else:
                    log(f"⚠️ 图片URL不存在")
                
                # 如果图标加载失败，使用默认图标
                if not icon_loaded:
                    default_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default_icon.png')
                    if os.path.exists(default_icon_path):
                        pixmap.load(default_icon_path)
                        icon_loaded = True
                    else:
                        log(f"⚠️ 默认图片不存在: {default_icon_path}")

                
                
                # 创建下载量和关注数显示
                download_icon = IconWidget(FluentIcon.DOWNLOAD, card)
                download_icon.setFixedSize(16, 16)
                download_label = CaptionLabel(f"{mod['downloads']}", card)
                follower_icon = IconWidget(FluentIcon.HEART, card)
                follower_icon.setFixedSize(16, 16)
                follower_label = CaptionLabel(f"{mod['follows']}", card)

                # 创建卡片主布局
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(12, 12, 12, 12)
                card_layout.setSpacing(8)

                # 创建顶部布局（图标+标题）
                top_layout = QHBoxLayout()
                top_layout.setSpacing(12)
                
                # 添加图标
                if icon_loaded:
                    icon_label.setPixmap(pixmap)
                    icon_label.setFixedSize(64, 64)
                    icon_label.setScaledContents(True)
                    top_layout.addWidget(icon_label)
                
                # 添加标题区域
                title_layout = QVBoxLayout()
                title_layout.setSpacing(4)
                title_layout.addWidget(title_label)
                title_layout.addWidget(body_label)
                
                # 创建统计信息布局
                stats_layout = QHBoxLayout()
                stats_layout.setSpacing(16)
                stats_layout.addWidget(download_icon)
                stats_layout.addWidget(download_label)
                stats_layout.addWidget(follower_icon)
                stats_layout.addWidget(follower_label)
                stats_layout.addStretch(1)
                
                # 将统计信息添加到标题布局
                title_layout.addLayout(stats_layout)
                title_layout.addStretch(1)
                top_layout.addLayout(title_layout)
                top_layout.addStretch(1)
                
                # 将顶部布局添加到主布局
                card_layout.addLayout(top_layout)

                # 创建标签布局（模组分类）
                tags_layout = QHBoxLayout()
                tags_layout.setSpacing(8)
                for types in mod["categories"]:
                    type_label = CaptionLabel(types, card)
                    tags_layout.addWidget(type_label)
                # 添加 Modrinth 链接按钮
                modrinth_button = ToolButton(parent=card)
                modrinth_button.setIcon(FluentIcon.LINK.icon())
                modrinth_button.setFixedSize(24, 24)
                modrinth_button.setIconSize(QSize(16, 16))
                # modrinth_button.setStyleSheet("QPushButton { qproperty-iconAlignment: AlignCenter; }")
                modrinth_button.setToolTip(i18nText("打开 Modrinth 模组详情页面"))
                modrinth_button.clicked.connect(lambda _, slug=mod.get('slug'): QDesktopServices.openUrl(QUrl(f"https://modrinth.com/mod/{slug}")) if slug else None)
                log(f"设定Modrinth链接按钮: https://modrinth.com/mod/{mod.get('slug')}")

                # 添加 Download Mod 按钮
                download_button = ToolButton(parent=card)
                download_button.setIcon(FluentIcon.DOWNLOAD.icon())
                download_button.setFixedSize(24, 24)
                download_button.setIconSize(QSize(16, 16))
                # modrinth_button.setStyleSheet("QPushButton { qproperty-iconAlignment: AlignCenter; }")
                download_button.setToolTip(i18nText("下载 Mod"))
                # 修改点击事件处理函数
                download_button.clicked.connect(lambda _, mod_title=mod.get('title', i18nText('未知模组')), slug=mod.get('slug'): show_download_dialog(mod_title, slug, self))
                log(f"设定Download Mod按钮: https://modrinth.com/mod/{mod.get('slug')}")

                # 创建包含两个按钮的布局并靠右对齐
                buttons_layout = QHBoxLayout()
                buttons_layout.addStretch(1)  # 添加弹性空间将按钮推到右侧
                buttons_layout.addWidget(modrinth_button)
                buttons_layout.addWidget(download_button)

                tags_layout.addLayout(buttons_layout)
                card_layout.addLayout(tags_layout)

                # 将卡片添加到滚动布局
                scroll_layout.addWidget(card)
                log(f"正在更新 UI 中的版本卡片：add {mod['title']}")

            # 完成布局设置
            scroll_layout.addStretch(1)
            mod_list.setWidget(scroll_widget)
            mod_list.setWidgetResizable(True)
            
            # 更新完成通知
            update_progress({'value': 1, 'valueStringOverride': '✅', 'status': f"搜索完成 ✅"})

        else:
            log(i18nText("未找到 mod_list SmoothScrollArea"), logging.ERROR)
            return
    else:
        log(i18nText("未找到相关模组"), logging.WARNING)

def setup_download_ui(self, widget):
    '''
    设定 Bloret Launcher 下载 UI 布局和操作。
    根据 ui/download.ui 文件设置界面元素和事件处理。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 获取配置文件中的Minecraft版本列表
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 1. 填充Minecraft版本选择框和Fabric版本选择框
        minecraft_versions = config.get('Minecraft_Versions', [])
        minecraft_version_choose = widget.findChild(ComboBox, 'Minecraft_version_choose')
        fabric_version_choose = widget.findChild(ComboBox, 'Fabric_version_choose')
        
        if minecraft_version_choose and minecraft_versions:
            minecraft_version_choose.addItems(minecraft_versions)
            # 添加"其他版本..."选项
            minecraft_version_choose.addItem(i18nText("其他版本..."))
            # 连接选择变化事件
            minecraft_version_choose.currentTextChanged.connect(
                lambda text: on_other_version_selected(self, minecraft_version_choose.currentText(), minecraft_version_choose)
            )
            
        if fabric_version_choose and minecraft_versions:
            fabric_version_choose.addItems(minecraft_versions)
            # 添加"其他版本..."选项
            fabric_version_choose.addItem(i18nText("其他版本..."))
            # 连接选择变化事件
            fabric_version_choose.currentTextChanged.connect(
                lambda text: on_other_version_selected(self, fabric_version_choose.currentText(), fabric_version_choose)
            )
            
        # 2. 填充Java版本选择框
        java_versions = config.get('Java_Versions', {})
        java_version_choose = widget.findChild(ComboBox, 'Java_version_choose')
        
        if java_version_choose and java_versions:
            # 直接使用Java版本号填充选择框
            java_version_items = []
            for version in java_versions.keys():
                java_version_items.append(version)
            
            if java_version_items:
                java_version_choose.addItems(java_version_items)
        
        # 3. 设置旧版下载页面按钮点击事件
        old_download_page_button = widget.findChild(QPushButton, 'Old_download_Page')
        if old_download_page_button:
            # 使用MessageBoxBase创建对话框
            def show_old_download_dialog():
                # 创建一个对话框
                dialog = MessageBoxBase(self)
                dialog.setWindowTitle(i18nText("旧版下载"))
                
                # 创建内容界面
                content_widget = QWidget()
                content_widget.setObjectName("download_old")
                load_ui("ui/download.old.ui", parent=content_widget)
                
                # 设置对话框内容
                dialog.viewLayout.addWidget(content_widget)
                
                # 设置对话框大小
                dialog.resize(800, 600)
                
                # 隐藏默认按钮
                # dialog.yesButton.hide()
                dialog.cancelButton.hide()
                
                # 设置UI
                setup_download_old_ui(self, content_widget, 
                                     self.LM_Download_Way_list if hasattr(self, 'LM_Download_Way_list') else ["1.21.8", "1.21.7"], 
                                     self.ver_id_bloret if hasattr(self, 'ver_id_bloret') else ["1.21.8", "1.21.7"], 
                                     self.homeInterface)
                
                # 显示对话框
                dialog.exec_()
            
            # 连接按钮点击事件
            old_download_page_button.clicked.connect(show_old_download_dialog)
            
        # 设置Minecraft版本下载按钮点击事件
        minecraft_download_button = widget.findChild(QPushButton, 'Minecraft_version_Download')
        if minecraft_download_button:
            minecraft_download_button.clicked.connect(lambda: InstallMinecraftVersion(minecraft_version_choose.currentText(),None,None,False))
            
        # 设置Fabric版本下载按钮点击事件
        fabric_download_button = widget.findChild(QPushButton, 'Fabric_version_Download')
        if fabric_download_button:
            def on_fabric_download_button_clicked():
                from qfluentwidgets import MessageBox
                version = fabric_version_choose.currentText()
                box = MessageBox(i18nText('您确定要安装 Fabric 版本 {} 吗？').format(version), i18nText('Fabric 版本安装目前尚在 Beta 阶段（实验性功能），安装完成后可能不能正常启动，但 Bloret Launcher 目前已可正常启动其他 Minecraft 启动器安装的 Fabric 版本 Minecraft。\n（人话：目前 Fabric 安装安装出来的可能不够标准，但是 Bloret Launcher 可以启动标准 Fabric 版本）\n如果您有能力，欢迎到 Github 来帮忙改进 Bloret Launcher'), widget)
                if box.exec():
                    InstallMinecraftVersion(version, None, None, True)
            
            fabric_download_button.clicked.connect(on_fabric_download_button_clicked)
            
        # 设置Java版本下载按钮点击事件
        java_download_button = widget.findChild(QPushButton, 'Java_version_Download')
        if java_download_button:
            java_download_button.clicked.connect(lambda: InstallJava(java_version_choose.currentText()))

        # 设置自定义项目按钮点击事件
        Customize_add = widget.findChild(QPushButton, 'Customize_add')
        if Customize_add:
            Customize_add.clicked.connect(lambda: CustomizeAdd(self))
            
    except Exception as e:
        log(f"设置下载UI时出错: {str(e)}", logging.ERROR)

def setup_multiplayer_ui(self, widget, server_ip):
    """设定 Bloret Launcher 多人联机界面 UI 布局和操作"""
    # 获取IPv6地址
    ipv6_address_str = get_ipv6_address()
    log(f"检测到的IPv6地址: {ipv6_address_str if ipv6_address_str else '未找到可用IPv6地址'}")
    
    ipv6_address_label = widget.findChild(QLabel, "ipv6_address")
    if ipv6_address_label:
        if ipv6_address_str:
            # 显示缩短的IPv6地址（只显示前8个字符）
            ipv6_display = f"{ipv6_address_str[:8]}..." if len(ipv6_address_str) > 8 else ipv6_address_str
            ipv6_address_label.setText(ipv6_display)
        else:
            ipv6_address_label.setText(i18nText("无法获取IPv6地址"))
            log(i18nText("未找到可用的IPv6地址，IPv6功能将被禁用"))

    get_ipv6_btn = widget.findChild(QPushButton, "GetIPV6AddressButton")
    if get_ipv6_btn:
        # 根据是否有IPv6地址设置按钮状态
        if ipv6_address_str:
            get_ipv6_btn.setEnabled(True)
            get_ipv6_btn.setToolTip(i18nText("点击显示IPv6联机对话框"))
        else:
            get_ipv6_btn.setEnabled(False)
            get_ipv6_btn.setToolTip(i18nText("未检测到IPv6地址，请确保您的网络支持IPv6"))
        
        # 断开可能存在的重复连接
        try:
            get_ipv6_btn.clicked.disconnect()
        except:
            pass
            
        # 连接按钮点击事件
        get_ipv6_btn.clicked.connect(lambda: show_ipv6_dialog(self, ipv6_address_str))
    
    # 设置初始状态
    online_client_time_label = widget.findChild(QLabel, "OnlineClient_ClientTime")
    online_client_address_label = widget.findChild(QLabel, "OnlineClient_address")
    
    if online_client_time_label:
        online_client_time_label.setText("--:--")
        log(i18nText("初始化OnlineClient_ClientTime标签"))
    else:
        log(i18nText("未找到OnlineClient_ClientTime标签"))
    
    if online_client_address_label:
        online_client_address_label.setText(i18nText("未连接"))
        log(i18nText("初始化OnlineClient_address标签"))
    else:
        log(i18nText("未找到OnlineClient_address标签"))
    
    # 连接StartOnlineClient按钮
    start_online_client_btn = widget.findChild(QPushButton, "StartOnlineClient")
    if start_online_client_btn:
        # 断开可能存在的重复连接
        try:
            start_online_client_btn.clicked.disconnect()
        except:
            pass
        start_online_client_btn.clicked.connect(lambda: start_online_client(self, server_ip))
        log(i18nText("已连接StartOnlineClient按钮"))
    else:
        log(i18nText("未找到StartOnlineClient按钮"))


def start_search_mod(self, mod_list, search_term, loading):
    """
    启动模组搜索功能，在单独的线程中执行搜索以避免阻塞UI
    
    Args:
        mod_list: 模组列表对象，用于显示搜索结果
        search_term: 搜索关键词
        loading: 加载状态指示器
    """
    # 确保旧线程结束，避免线程冲突
    if hasattr(mod_list, '_ui_thread') and mod_list._ui_thread.isRunning():
        mod_list._ui_thread.quit()
        mod_list._ui_thread.wait()
    
    # 创建新的模组搜索线程实例
    mod_list._ui_thread = ModSearchThread(mod_list, search_term)
    
    # 连接搜索结果信号到处理函数
    def handle_results(results):
        """
        处理搜索结果的通用逻辑
        
        Args:
            results: 搜索返回的结果数据
        """
        # 这里可以处理搜索结果的通用逻辑
        pass
    mod_list._ui_thread.results_ready.connect(handle_results)
    
    # 连接UI元素就绪信号到结果处理函数
    # 当搜索完成且UI元素准备就绪时，调用on_search_mod_finish进行后续处理
    mod_list._ui_thread.ui_elements_ready.connect(lambda data: on_search_mod_finish(self, data, mod_list, loading))
    
    # 启动搜索线程
    mod_list._ui_thread.start()

def setup_Mod_ui(self, widget, server_ip):
    '''
    设定 Bloret Launcher 模组界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 绑定 OpenMod 按钮点击事件
    Open_Modrinth_Button = widget.findChild(QPushButton, "Open_Modrinth_Button")
    if Open_Modrinth_Button:
        Open_Modrinth_Button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://modrinth.com/mods")))
    else:
        log(i18nText("未找到 Open_Modrinth_Button 按钮"), logging.ERROR)

    Search = widget.findChild(SearchLineEdit, "Search")
    mod_list = widget.findChild(SmoothScrollArea, "mod_list")
    if Search:
        # on_search_mod_clicked(mod_list)
        # 获取进度条控件实例
        loading_widget = widget.findChild(IndeterminateProgressBar, "loading")
        Search.searchSignal.connect(lambda: start_search_mod(self, mod_list, Search.text(), loading_widget))
    else:
        log(i18nText("未找到 Search 搜索框"), logging.ERROR)