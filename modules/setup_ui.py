from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLineEdit, QLabel, QListWidget
from qfluentwidgets import SpinBox, ComboBox, SwitchButton, LineEdit, ListWidget, InfoBarPosition, InfoBar
from PyQt5 import uic
from PyQt5.QtGui import QDesktopServices, QPixmap, QIcon
from PyQt5.QtCore import QUrl, Qt
import requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log, importlog, clear_log_files
from modules.Bloret_PassPort import Bloret_PassPort_Account_login,Bloret_PassPort_Account_logout
from modules.links import open_github_bloret_Launcher,open_qq_link,open_BLC_qq_link,open_BBBS_link,open_bloret_web,open_github_bloret,copy_skin_to_clipboard,copy_cape_to_clipboard,copy_uuid_to_clipboard,copy_name_to_clipboard
from modules.querys import query_player_uuid,query_player_skin,query_player_name
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

def setup_home_ui(self, widget):
    '''
    设定 Bloret Launcher 主页 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    if self.config.get('localmod', False):
        InfoBar.warning(
            title='⚠️ 本地模式已开启',
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
    Bloret_PassPort_Name = widget.findChild(QLabel, "Bloret_PassPort_Name")
    if Bloret_PassPort_Name:
        Bloret_PassPort_Name.setText(f"{self.config.get('Bloret_PassPort_UserName', '未登录')}")
    Minecraft_account = widget.findChild(QLabel, "Minecraft_account")
    if Minecraft_account:
        if self.config.get('home_show_login_mod', False):
            if self.login_mod == "请在下方登录":
                Minecraft_account.setText("无档案(请到通行证页面登录)")
            else:
                Minecraft_account.setText(f"[{self.login_mod}] {self.player_name}")
        else:
            Minecraft_account.setText(f"{self.player_name}")

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

def setup_download_ui(self, widget, LM_Download_Way_list,ver_id_bloret):
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
    notification_switch = widget.findChild(SwitchButton, "Notification")
    if notification_switch:
        notification_switch.setChecked(True)  # 将Notification开关设置成开

    fabric_ver = ["不安装"]
    if not self.config.get('localmod', False):
        response = requests.get("https://bmclapi2.bangbang93.com/fabric-meta/v2/versions/loader")
        if response.status_code == 200:
            data = response.json()
            for item in data:
                fabric_ver.append(item["version"])
    else:
        log("本地模式已启用，获取 Minecraft 版本 的过程已跳过。")

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
        if not self.config.get('localmod', False):
            minecraft_choose.addItems(ver_id_bloret)
        else:
            minecraft_choose.addItems(["本地模式已启用，无法下载版本"])
        vername_edit = widget.findChild(LineEdit, "vername_edit")
        if vername_edit and ver_id_bloret:
            vername_edit.setText(ver_id_bloret[0])

    Customize_choose = widget.findChild(QPushButton, "Customize_choose")
    if Customize_choose:
        Customize_choose.clicked.connect(lambda: self.on_customize_choose_clicked(widget))

    Customize_add = widget.findChild(QPushButton, "Customize_add")
    if Customize_add:
        Customize_add.clicked.connect(lambda: self.on_customize_add_clicked(widget))

def setup_tools_ui(self, widget):
    '''
    设定 Bloret Launcher 小工具界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    name2uuid_button = widget.findChild(QPushButton, "name2uuid_player_Button")
    if name2uuid_button:
        name2uuid_button.clicked.connect(lambda: query_player_uuid(widget))
    search_name_button = widget.findChild(QPushButton, "search_name_button")
    if search_name_button:
        search_name_button.clicked.connect(lambda: query_player_name(widget))
    skin_search_button = widget.findChild(QPushButton, "skin_search_button")
    if skin_search_button:
        skin_search_button.clicked.connect(lambda: query_player_skin(widget))
    name_copy_button = widget.findChild(QPushButton, "search_name_copy")
    if name_copy_button:
        name_copy_button.clicked.connect(lambda: copy_name_to_clipboard(widget))
    uuid_copy_button = widget.findChild(QPushButton, "pushButton_5")
    if uuid_copy_button:
        uuid_copy_button.clicked.connect(lambda: copy_uuid_to_clipboard(widget))
    skin_copy_button = widget.findChild(QPushButton, "search_skin_copy")
    if skin_copy_button:
        skin_copy_button.clicked.connect(lambda: copy_skin_to_clipboard(widget))
    cape_copy_button = widget.findChild(QPushButton, "search_cape_copy")
    if cape_copy_button:
        cape_copy_button.clicked.connect(lambda: copy_cape_to_clipboard(widget))

def setup_passport_ui(self, widget, server_ip):
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
    # if player_name_edit:
    #     player_name_edit.setText(self.player_name if self.cmcl_data else '')
    # else:
    #     log("未找到player_name输入框", logging.ERROR)

    if player_name_edit and player_name_set_button:
        player_name_set_button.clicked.connect(lambda: self.on_player_name_set_clicked(widget))
        log("已连接 player_name_set_button 点击事件")

    if self.cmcl_data:
        log("成功读取 cmcl.json 数据")
        
        if login_way_combo:
            login_way_choose.clear()
            login_way_choose.addItems(["离线登录", "微软登录"])
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
        log("读取 cmcl.json 失败")
    
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
        Bloret_PassPort_logout.clicked.connect(lambda: Bloret_PassPort_Account_logout(widget))
    if Bloret_PassPort_login:
        Bloret_PassPort_login.clicked.connect(lambda: Bloret_PassPort_Account_login(self,widget))
    if Bloret_PassPort_view_BBBS:
        Bloret_PassPort_view_BBBS.clicked.connect(lambda: open_BBBS_link(server_ip))

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
        light_dark_choose.addItems(["跟随系统", "深色模式", "浅色模式"])
        light_dark_choose.currentTextChanged.connect(self.on_light_dark_changed)

    size_choose = widget.findChild(SpinBox, "Size_Choose")
    if size_choose:
        size_choose.setValue(self.config.get("size", 100))
        size_choose.valueChanged.connect(lambda value: (
            self.config.update(size=value),
            open('self.config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
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

def setup_version_ui(self, widget, minecraft_list, customize_list):
    '''
    设定 Bloret Launcher 版本管理界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # rgb(248, 76, 82)
    versions = widget.findChild(ListWidget, "versions")
    if versions:
        versions.clear()
        versions.addItems(minecraft_list)
        versions.setSelectRightClickedRow(True)
    Version_Change_Name_Button = widget.findChild(QPushButton, "Version_Change_Name_Button")
    version_delete_button = widget.findChild(QPushButton, "version_delete_button")
    Version_Open_File_Button = widget.findChild(QPushButton, "Version_Open_File_Button")
    if Version_Change_Name_Button:
        Version_Change_Name_Button.clicked.connect(lambda: self.Change_minecraft_version_name(minecraft_list[versions.currentRow()],versions))
    if version_delete_button:
        version_delete_button.clicked.connect(lambda: self.delete_minecraft_version(minecraft_list[versions.currentRow()],versions))
    if Version_Open_File_Button:
        '''
        # 🚧TODO🚧
        '''
        Version_Open_File_Button.clicked.connect(lambda: self.delete_minecraft_version(minecraft_list[versions.currentRow()],versions))

    Customizes = widget.findChild(ListWidget, "Customizes")
    if Customizes:
        Customizes.clear()
        Customizes.addItems(customize_list)
    Customizes_Change_Name_button = widget.findChild(QPushButton, "Customizes_Change_Name_button")
    Customizes_delete_button = widget.findChild(QPushButton, "Customizes_delete_button")
    if Customizes_Change_Name_button:
        Customizes_Change_Name_button.clicked.connect(lambda:self.Change_Customize_name(customize_list[Customizes.currentRow()],Customizes))
    if Customizes_delete_button:
        Customizes_delete_button.clicked.connect(lambda:self.delete_Customize(customize_list[Customizes.currentRow()],Customizes))


importlog("SETUP_UI.PY")