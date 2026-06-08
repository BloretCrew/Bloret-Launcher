# 1. 标准库
import os
import re
import json
import shutil
import socket
import logging
import requests
import random
import sys

# 2. 第三方库 (PySide6)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QPushButton,
    QSizePolicy, QFileDialog, QFileIconProvider
)
from PySide6.QtGui import QDesktopServices, QPixmap, QColor, QIcon, QMovie
from PySide6.QtCore import QUrl, Qt, QSize, QTimer, QDateTime, QFileInfo, QThread, Signal as pyqtSignal
# from PySide6.QtUiTools import QUiLoader # Removed uic for PySide6 compatibility

# 3. 兼容控件 (替代 qfluentwidgets)
from modules.compat_widgets import (
    SpinBox, ComboBox, SwitchButton, LineEdit, InfoBarPosition, InfoBar,
    SubtitleLabel, CardWidget, StrongBodyLabel, BodyLabel, PushButton,
    SmoothScrollArea, RoundMenu, Action, FluentIcon, SearchLineEdit,
    CaptionLabel, ImageLabel, IndeterminateProgressBar, IconWidget,
    ToolButton, MessageBoxBase, MessageBox,
    TabBar, CheckBox, HyperlinkLabel
)

# 4. 自定义模块 (Bloret Launcher Modules)
import modules.globals as BLglobals
import modules.config as cfg
from modules.config import read
from modules.systems import setup_startup_with_self_starting
from modules.log import log, clear_log_files
from modules.Bloret_PassPort import (
    Bloret_PassPort_Account_logout,
    sync_bloret_passport_account_to_mc, savedata, readdata
)
from modules.links import (
    open_github_bloret_Launcher, open_qq_link, open_BLC_qq_link,
    open_BBBS_link, open_BBBS_Reg_link, open_github_bloret,
    copy_skin_to_clipboard, copy_cape_to_clipboard, copy_uuid_to_clipboard,
    copy_name_to_clipboard, Bloret_PassPort_Account_login,
    openLink
)
from modules.querys import query_player_uuid, query_player_skin, query_player_name
from modules.versions import (
    delete_Customize, Change_Customize_name, open_minecraft_version_folder,
    on_other_version_selected, open_core_management
)
from modules.install import InstallMinecraftVersion
from modules.modrinth import search_mods, Get_Mod_File_Download_Url, add_mrpack
from modules.win11toast import notify, update_progress
from modules.java import InstallJava, java_versions
from modules.i18n import i18nText
from modules.customize import CustomizeAdd, CustomizeRun
from modules.Bloriko import AskBlorikoAndSet, AskBloriko
from modules.chafuwang import getServerData
from modules.easytier import StartEasytierServer
from modules.ShortCut import ScreenShortCut


# 加载配置文件
def load_config():
    # 使用 BLglobals 中的全局路径，而不是硬编码
    try:
        with open(BLglobals.config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {BLglobals.config_path} 未找到。")
        return {}
    except json.JSONDecodeError:
        print(f"错误：配置文件 {BLglobals.config_path} 格式不正确。")
        return {}

config = load_config()


def resource_path(relative_path):
    """Resolve bundled resources in PyInstaller onefile builds."""
    base_path = getattr(sys, "_MEIPASS", os.getcwd())
    return os.path.join(base_path, relative_path)

def scan_java_paths():
    """扫描系统中的 Java 安装路径"""
    java_paths = []
    
    # 1. 检查 PATH 环境变量
    path_java = shutil.which("java")
    if path_java:
        java_paths.append(path_java)
        
    # 2. 常见安装目录
    common_roots = [
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Java"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Java"),
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Eclipse Adoptium"),
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Zulu"),
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "BellSoft"),
        os.path.join(os.path.expanduser("~"), ".jdks"),
        "/Library/Java/JavaVirtualMachines",  # macOS
        "/usr/lib/jvm",                       # Linux
        "/usr/java"                           # Linux alternative
    ]
    
    for root in common_roots:
        if os.path.exists(root):
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    # 简单优化：只查找 bin 目录下的 java.exe
                    if os.path.basename(dirpath) == 'bin' and "java.exe" in filenames:
                        full_path = os.path.join(dirpath, "java.exe")
                        if full_path not in java_paths:
                            java_paths.append(full_path)
            except Exception:
                pass
                
    return list(set(java_paths))

class DownloadDialog(MessageBoxBase):
    """ 自定义下载对话框 """

    def __init__(self, mod_title, slug, parent=None):
        super().__init__(parent)
        self.mod_title = mod_title
        self.slug = slug
        self.game_versions = []  # 存储模组支持的游戏版本
        self.version_mappings = {}  # 存储文件夹名到实际版本号的映射
        
        self.titleLabel = SubtitleLabel(mod_title)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        
        self.modNameLabel = StrongBodyLabel(f'选择安装 Mod 的版本')
        
        self.versionCombo = ComboBox()
        self.versionCombo.setPlaceholderText(i18nText('选择版本'))
        
        # 获取模组支持的游戏版本
        self.fetch_mod_versions()

        # 先获取 config.json 中 .minecraft 文件夹位置
        minecraft_dir = cfg.read()["minecraft_dir"]
        
        # 加载 .BL.json 文件来获取版本映射
        self.load_version_mappings(minecraft_dir)
        
        # 获取 .minecraft\versions 文件夹内的文件夹列表
        versions_path = os.path.join(minecraft_dir, "versions")
        if os.path.exists(versions_path):
            version_folders = [f for f in os.listdir(versions_path) 
                              if os.path.isdir(os.path.join(versions_path, f))]
            
            # 只添加启用了Fabric的版本
            fabric_versions = []
            for folder in version_folders:
                is_fabric = False
                if folder in self.version_mappings and self.version_mappings[folder].get("Fabric", False):
                    is_fabric = True
                if not is_fabric and "fabric" in folder.lower():
                    is_fabric = True
                if is_fabric:
                    fabric_versions.append(folder)
            
            self.versionCombo.addItems(fabric_versions)
        
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
        folder_name = self.versionCombo.currentText()
        actual_version = self.get_actual_version(folder_name) if folder_name else "未知版本"
        log(f"准备下载模组: {self.mod_title} (文件夹: {folder_name}, 版本: {actual_version})")
        log(f"模组链接: https://modrinth.com/mod/{self.slug}")
        # 打开模组页面
        QDesktopServices.openUrl(QUrl(f"https://modrinth.com/mod/{self.slug}"))
        self.accept()  # 关闭对话框
        
    def load_version_mappings(self, minecraft_dir):
        """加载 .BL.json 文件来获取版本映射"""
        bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
        try:
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    bl_data = json.load(f)
                    if "versions" in bl_data:
                        self.version_mappings = bl_data["versions"]
                        log(f"成功加载版本映射: {list(self.version_mappings.keys())}")
                    else:
                        log("警告: .BL.json 文件格式不正确，缺少 'versions' 字段")
            else:
                log("警告: 未找到 .BL.json 文件，将使用文件夹名作为版本号")
        except Exception as e:
            log(f"加载 .BL.json 文件时出错: {str(e)}")
    
    def get_actual_version(self, folder_name):
        """获取文件夹对应的实际版本号"""
        if folder_name in self.version_mappings:
            return self.version_mappings[folder_name].get("version", folder_name)
        return folder_name
    
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
        
        # 获取实际的版本号
        actual_version = self.get_actual_version(selected_version)
        log(f"检查版本兼容性: 文件夹名={selected_version}, 实际版本={actual_version}")
            
        # 检查实际版本是否在模组支持的版本列表中
        if actual_version in self.game_versions:
            self.warningLabel.hide()
            self.yesButton.show()  # 启用下载按钮
        else:
            self.warningLabel.setText(i18nText("警告：所选版本可能不兼容此模组"))
            self.warningLabel.show()
            self.yesButton.hide()  # 禁用下载按钮
            
    def download_mod(self):
        """下载选定的Mod文件"""
        folder_name = self.versionCombo.currentText()
        if not folder_name or folder_name == i18nText("未找到任何版本"):
            log(i18nText("未选择有效的版本"))
            return
        
        # 获取实际的版本号
        actual_version = self.get_actual_version(folder_name)
        log(f"开始下载模组: 文件夹名={folder_name}, 实际版本={actual_version}")
            
        # 获取Mod下载URL
        url = Get_Mod_File_Download_Url(self.slug, "fabric", actual_version)
        if not url:
            log(f"无法获取Mod {self.mod_title} 的下载URL")
            return
            
        # 使用配置中的minecraft目录创建目标路径
        minecraft_dir = cfg.read().get('minecraft_dir', os.path.join(BLglobals.datapath, '.minecraft'))
        mod_dir = os.path.join(minecraft_dir, "versions", folder_name, "mods")
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)
            
        # 获取文件名
        filename = url.split("/")[-1]
        file_path = os.path.join(mod_dir, filename)
        
        # 下载文件
        try:
            log(f"开始下载 {self.mod_title} (版本: {actual_version}) 到 {file_path}")
            log(f"Minecraft目录: {minecraft_dir}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            log(f"成功下载 {self.mod_title} (版本: {actual_version}) 到 {file_path}")
            InfoBar.success(
                title=i18nText('✅ 下载成功'),
                content=f"Mod {self.mod_title} 已成功下载到 {file_path}",
                parent=self.parent(),
                duration=5000
            )
            self.accept()  # 关闭对话框
        except Exception as e:
            log(f"下载Mod {self.mod_title} (版本: {actual_version}) 时出错: {str(e)}")
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
    # PySide6 Migration: uic.loadUi is not available. 
    # Skipping for now as we are migrating to QML or using manual layouts.
    # widget = uic.loadUi(ui_path)
    return
    '''

    if parent:
        # 强制使用布局管理（若原布局缺失）
        if not parent.layout():
            layout = QVBoxLayout(parent)  # 使用垂直布局
            layout.setContentsMargins(0,0,0,0)  # 移除默认边距
            layout.addWidget(widget)
        else:
            parent.layout().addWidget(widget)

def on_self_starting_changed(main_window, value):
    """
    当 SwitchButton 状态变化时，更新配置文件中的 self-starting 字段
    """
    log(f"开机自启设置为: {value}")
    
    # 1. 更新内存中的配置
    if hasattr(main_window, 'config'):
        main_window.config["self-starting"] = value
        
    # 2. 调用主窗口的保存方法（如果可用），否则执行安全保存
    if hasattr(main_window, 'save_config'):
        main_window.save_config()
    else:
        # 备用逻辑：直接写入文件（仅当无法访问 MainWindow 时）
        try:
            config = cfg.read()
            config["self-starting"] = value
            with open(BLglobals.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log(f"备用写入配置文件失败: {e}")

    # 3. 设置系统开机启动项
    setup_startup_with_self_starting(value)
    log(f"已更新开机自启设置: {value}")

class LaunchSelectorDialog(MessageBoxBase):
    """ 启动项选择窗口 """
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(i18nText("选择启动项目"), self)
        
        # 标题居中
        # self.titleLabel.setAlignment(Qt.AlignCenter)

        self.viewLayout.addWidget(self.titleLabel)
        
        self.tipLabel = CaptionLabel(i18nText("右键单击启动项可进行管理。"), self)
        # 设置指定的颜色: Light=[127,127,127,255], Dark=[185,185,185,255]
        self.tipLabel.setTextColor(QColor(127, 127, 127, 255), QColor(185, 185, 185, 255))

        # 提示信息居中
        # self.tipLabel.setAlignment(Qt.AlignCenter)
        
        self.viewLayout.addWidget(self.tipLabel)
        
        # 使用滚动区域容纳卡片列表
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setSpacing(10) # 卡片间距
        self.scrollLayout.setContentsMargins(5, 5, 15, 5) # 边距
        self.scrollLayout.setAlignment(Qt.AlignTop)
        
        self.scrollArea.setWidget(self.scrollContent)
        self.viewLayout.addWidget(self.scrollArea)
        
        # 隐藏确定按钮，因为点击选择按钮即选中
        self.yesButton.hide()
        self.cancelButton.setText(i18nText("取消"))
        
        self.widget.setMinimumWidth(450) # 稍微加宽一点以适应卡片布局
        self.widget.setMinimumHeight(500)

        # 填充列表
        self.populate_list(items)

    def populate_list(self, items=None):
        """ 填充或刷新列表 """
        # 清空现有列表
        while self.scrollLayout.count():
            item = self.scrollLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 如果没有传入 items，则重新获取
        self.items = items if items is not None else get_all_launch_items()
        self.selected_item = None
        
        for item in self.items:
            # 创建卡片
            card = CardWidget(self.scrollContent)
            card.setFixedHeight(60)
            
            cardLayout = QHBoxLayout(card)
            cardLayout.setContentsMargins(15, 10, 15, 10)
            cardLayout.setSpacing(15)
            
            # 图标
            iconLabel = QLabel(card)
            iconLabel.setFixedSize(32, 32)
            iconLabel.setScaledContents(True)
            if isinstance(item['icon'], QIcon):
                iconLabel.setPixmap(item['icon'].pixmap(32, 32))
            
            # 名称
            nameLabel = StrongBodyLabel(item['name'], card)
            
            # 选择按钮
            selectBtn = PushButton(i18nText("选择"), card)
            selectBtn.setFixedWidth(80)
            selectBtn.clicked.connect(lambda _, i=item: self.on_item_clicked(i))
            
            cardLayout.addWidget(iconLabel)
            cardLayout.addWidget(nameLabel)
            cardLayout.addStretch(1) # 弹簧，将按钮推到最右侧
            cardLayout.addWidget(selectBtn)

            # --- 右键菜单逻辑 ---
            card.setContextMenuPolicy(Qt.CustomContextMenu)
            
            # 使用默认参数捕获循环变量
            def on_context_menu(pos, i=item, c=card, l=nameLabel):
                self.show_context_menu(pos, i, c, l)
                
            card.customContextMenuRequested.connect(on_context_menu)
            # --------------------
            
            self.scrollLayout.addWidget(card)

    def on_item_clicked(self, item):
        """ 点击选择按钮触发 """
        self.selected_item = item
        self.accept() # 关闭并返回 True

    def refresh_list(self):
        """ 刷新列表显示 """
        # 延时一点以确保之前的操作（如删除动画或弹窗关闭）完成
        QTimer.singleShot(100, lambda: self.populate_list())

    def show_context_menu(self, pos, item, card, label):
        """ 显示右键菜单 """
        main_window = self.parent()
        if not main_window: return

        v_name = item['name']
        item_type = item.get('type')
        
        # 获取配置和目录
        config_data = cfg.read()
        minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
        home_interface = getattr(main_window, 'homeInterface', None)

        menu = RoundMenu(parent=card)
        
        # 启动
        menu.addAction(Action(FluentIcon.PLAY, i18nText('启动'), triggered=lambda: self.launch_and_close(v_name, item_type == 'custom')))

        if item_type == 'minecraft':
            # 核心管理
            def open_manage():
                open_core_management(main_window, v_name, minecraft_dir, home_interface)
                self.refresh_list()
            menu.addAction(Action(FluentIcon.SETTING, i18nText('核心管理'), triggered=lambda: QTimer.singleShot(100, open_manage)))

            # 打开文件位置
            menu.addAction(Action(FluentIcon.FOLDER, i18nText('打开文件位置'), triggered=lambda: open_minecraft_version_folder(main_window, v_name, minecraft_dir)))

        elif item_type == 'custom':
            # 更名
            def rename_custom():
                Change_Customize_name(main_window, v_name, label, home_interface)
                self.refresh_list()
            menu.addAction(Action(FluentIcon.EDIT, i18nText('更名'), triggered=rename_custom))
            
            # 删除
            def delete_custom():
                delete_Customize(main_window, v_name, label, card, BLglobals.customize_list, home_interface)
                self.refresh_list()
            menu.addAction(Action(FluentIcon.DELETE, i18nText('删除'), triggered=lambda: QTimer.singleShot(100, delete_custom)))

        global_pos = card.mapToGlobal(pos)
        menu.exec_(global_pos)

    def launch_and_close(self, name, is_custom=False):
        """ 启动并关闭选择器 """
        main_window = self.parent()
        
        # 保存选择 (同步更新内存和磁盘)
        if hasattr(main_window, 'config'):
            main_window.config["ChoosedRun"] = name
            if hasattr(main_window, 'save_config'):
                main_window.save_config()
            else:
                # 备用写入
                config = cfg.read()
                config["ChoosedRun"] = name
                with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            
        # 设置选中的项目以便调用者知道（虽然这里直接启动了）
        self.selected_item = next((i for i in self.items if i['name'] == name), None)
        
        # 启动
        if is_custom:
            CustomizeRun(main_window, name)
        else:
            main_window.run_cmcl(name, main_window.homeInterface)
            
        self.accept()

def get_all_launch_items():
    """ 获取所有启动项 (Minecraft + Customize) """
    items = []
    
    # --- 1. 获取 Minecraft 启动项 ---
    # 读取配置文件获取游戏目录
    config_data = cfg.read()
    minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
    versions_dir = os.path.join(minecraft_dir, "versions")
    bl_json_path = os.path.join(versions_dir, ".BL.json")
    
    versions_metadata = {}
    try:
        if os.path.exists(bl_json_path):
            with open(bl_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                versions_metadata = data.get("versions", {})
    except Exception as e:
        log(f"读取 .BL.json 失败: {e}", logging.WARNING)

    if os.path.exists(versions_dir):
        # 遍历 versions 文件夹，获取实际存在的版本文件夹
        # 这里虽然没有直接只读 .BL.json，但这更健壮，防止 .BL.json 有记录但文件夹不存在的情况
        # 同时也符合“从 .BL.json 中获取（图标也要展示）”的需求，因为元数据是从那来的
        for d in os.listdir(versions_dir):
            version_path = os.path.join(versions_dir, d)
            if os.path.isdir(version_path):
                # 默认图标
                icon = QIcon(resource_path("ui/icon/Grass_Block.png"))
                
                # 尝试从 .BL.json 获取元数据
                if d in versions_metadata:
                    meta = versions_metadata[d]
                    
                    # 获取图标路径
                    icon_path = meta.get("icon", "")
                    if icon_path and os.path.exists(icon_path):
                        icon = QIcon(icon_path)
                    # 如果是 Fabric 版本且没有自定义图标，使用 Fabric 图标
                    elif meta.get("Fabric", False):
                         icon = QIcon(resource_path("ui/icon/fabric.png"))
                
                items.append({
                    "name": d,
                    "type": "minecraft",
                    "icon": icon,
                    "path": d 
                })

    # --- 2. 获取自定义启动项 ---
    # 直接从 modules.config.read() 获取 Customize 列表
    if "Customize" in config_data and isinstance(config_data["Customize"], list):
        provider = QFileIconProvider()
        for custom_item in config_data["Customize"]:
            path = custom_item.get("path", "")
            name = custom_item.get("showname", "Unknown")
            
            # 获取程序文件图标
            icon = FluentIcon.APPLICATION.icon() # 默认图标
            if path and os.path.exists(path):
                file_info = QFileInfo(path)
                icon = provider.icon(file_info)
            
            items.append({
                "name": name,
                "type": "custom",
                "icon": icon,
                "path": path,
                "raw_data": custom_item
            })
            
    log(f"get_all_launch_items 返回 items: {items}")
    return items

def setup_home_ui(self, widget):
    '''
    设定 Bloret Launcher 主页 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
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
    BLtips = widget.findChild(CaptionLabel, "BLTips")
    if BLtips:
        log(f"BLTIPS:{BLglobals.BLtips}")
        if BLglobals.BLtips:
            BLtips.setText(random.choice(BLglobals.BLtips))
        else:
            BLtips.setText("欢迎使用 Bloret Launcher！")
    
    if BLglobals.BL_Activity.get("show", False):
        activity_icon = widget.findChild(StrongBodyLabel, "activity_icon")
        activity_title = widget.findChild(StrongBodyLabel, "activity_title")
        activity_description = widget.findChild(CaptionLabel, "activity_description")
        activity_time = widget.findChild(CaptionLabel, "activity_time")
        activity_to = widget.findChild(PushButton, "activity_to")
        if activity_icon:
            # --- 修复 1: 限制图标大小 ---
            # 设置固定大小(例如64x64)，防止大图撑坏布局
            activity_icon.setFixedSize(64, 64)
            # 开启内容缩放，让图片自动缩放以填满上述固定大小
            activity_icon.setScaledContents(True)

            icon_source = BLglobals.BL_Activity["icon"]
            
            # --- 修复 2: 加载网络图片 ---
            if icon_source.startswith("http"):
                try:
                    # 使用 requests 下载图片数据
                    response = requests.get(icon_source, timeout=3)
                    if response.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(response.content)
                        activity_icon.setPixmap(pixmap)
                    else:
                        log(f"活动图片下载失败，状态码: {response.status_code}")
                        # 下载失败时加载一个默认图标，防止留空
                        activity_icon.setPixmap(QPixmap(resource_path("ui/icon/Grass_Block.png")))
                except Exception as e:
                    log(f"加载网络活动图片出错: {str(e)}")
                    activity_icon.setPixmap(QPixmap(resource_path("ui/icon/Grass_Block.png")))
            else:
                # 本地文件直接加载
                activity_icon.setPixmap(QPixmap(icon_source))
        if activity_title:
            activity_title.setText(BLglobals.BL_Activity["title"])
        if activity_description:
            activity_description.setText(BLglobals.BL_Activity["description"])
        if activity_time:
            activity_time.setText(BLglobals.BL_Activity["time"])
        if activity_to:
            activity_to.setIcon(FluentIcon.LINK)
            activity_to.clicked.connect(lambda: openLink(BLglobals.BL_Activity["link"]))
            if BLglobals.BL_Activity["status"] == "before":
                activity_to.setEnabled(False)
                activity_to.setText("尚未开始")
            elif BLglobals.BL_Activity["status"] == "during":
                activity_to.setEnabled(True)
                activity_to.setText("前往")
            elif BLglobals.BL_Activity["status"] == "after":
                activity_to.setEnabled(False)
                activity_to.setText("已结束")
    else:
        activity_card = widget.findChild(CardWidget, "activity_card")
        if activity_card:
            activity_card.hide()
    
    # 1. 获取控件
    MinecraftVersionChoose = widget.findChild(QPushButton, "MinecraftVersionChoose")
    run_button = widget.findChild(QPushButton, "run")
    MinecraftVersionLabel = widget.findChild(StrongBodyLabel, "MinecraftVersionLabel")
    MinecraftVersionImageLabel = widget.findChild(BodyLabel, "MinecraftVersionImageLabel")
    
    # 2. 设置图标
    if MinecraftVersionChoose:
        MinecraftVersionChoose.setIcon(FluentIcon.MENU)
    if run_button:
        run_button.setIcon(FluentIcon.PLAY_SOLID)
        
    # 定义刷新显示函数
    def refresh_launch_display():
        """ 刷新当前选中的启动项显示 """
        # 优先使用内存中的配置，确保实时性
        choosed_run = self.config.get("ChoosedRun", "")
        items = get_all_launch_items()
        
        selected_item = None
        
        # 如果列表为空
        if not items:
            if MinecraftVersionLabel: MinecraftVersionLabel.setText(i18nText("无启动项"))
            if MinecraftVersionImageLabel: MinecraftVersionImageLabel.setPixmap(QPixmap())
            if run_button: 
                run_button.setEnabled(False)
                run_button.setText(i18nText("无项目"))
            return

        # 查找当前选中项
        for item in items:
            if item["name"] == choosed_run:
                selected_item = item
                break
        
        # 如果未选择或选择项不存在，默认选择第一个
        if not selected_item and items:
            selected_item = items[0]
            # 保存默认选择到内存并写入磁盘
            self.config["ChoosedRun"] = selected_item["name"]
            self.save_config()
        
        # 更新 UI
        if selected_item:
            if MinecraftVersionLabel: 
                MinecraftVersionLabel.setText(selected_item["name"])
            if MinecraftVersionImageLabel: 
                # 从 QIcon 提取 Pixmap
                pixmap = selected_item["icon"].pixmap(32, 32)
                MinecraftVersionImageLabel.setPixmap(pixmap)
                MinecraftVersionImageLabel.setScaledContents(True)
            if run_button:
                run_button.setEnabled(True)
                run_button.setText(i18nText("启动"))

    # 定义选择启动项函数
    def open_launch_selector():
        items = get_all_launch_items()
        if not items:
             InfoBar.warning(title=i18nText("提示"), content=i18nText("没有找到任何启动项，请先下载或添加。"), parent=self)
             return

        dialog = LaunchSelectorDialog(self, items)
        if dialog.exec():
            selected = dialog.selected_item
            if selected:
                # 保存选择到内存并写入磁盘
                self.config["ChoosedRun"] = selected["name"]
                self.save_config()
                
                # 刷新显示
                refresh_launch_display()

    # 定义启动函数
    def execute_launch():
        # 直接读取内存配置
        choosed_name = self.config.get("ChoosedRun", "")
        if not choosed_name:
            return
            
        items = get_all_launch_items()
        target_item = next((item for item in items if item["name"] == choosed_name), None)
        
        if target_item:
            if target_item["type"] == "minecraft":
                # Minecraft 启动
                self.run_cmcl(target_item["name"], widget)
            elif target_item["type"] == "custom":
                # 自定义启动
                # 注意：CustomizeRun 需要导入
                CustomizeRun(self, target_item["name"])
        else:
             InfoBar.error(title=i18nText("错误"), content=i18nText("选中的启动项已不存在"), parent=self)
             refresh_launch_display() # 重新刷新以修正状态

    # 连接信号
    if MinecraftVersionChoose:
        # 断开旧连接（如果存在）
        try: MinecraftVersionChoose.clicked.disconnect() 
        except: pass
        MinecraftVersionChoose.clicked.connect(open_launch_selector)
        
    if run_button:
        try: run_button.clicked.disconnect() 
        except: pass
        run_button.clicked.connect(execute_launch)

    # 初始化显示
    refresh_launch_display()
    
    # ----------------------------

    minecraft_tab = widget.findChild(TabBar, "MinecraftTab")
    if minecraft_tab:
        minecraft_tab.hide()
    
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
    BlorikoThinking = widget.findChild(IndeterminateProgressBar, "BlorikoThinking")
    Bloriko_DeepThink_CheckBox = widget.findChild(CheckBox, "Bloriko_DeepThink_CheckBox") # 获取 CheckBox

    if BlorikoThinking:
        BlorikoThinking.hide()
    else:
        log("未找到 BlorikoThinking 元素")

    if AskBloriko_Button:
        AskBloriko_Button.setIcon(FluentIcon.SEND)
        # 获取 CheckBox 状态并传入 AskBlorikoAndSet
        AskBloriko_Button.clicked.connect(lambda: AskBlorikoAndSet(
            self, 
            AskBloriko_Edit.text(), 
            AskBloriko_Answer, 
            BlorikoThinking, 
            widget, 
            deepthink=Bloriko_DeepThink_CheckBox.isChecked() if Bloriko_DeepThink_CheckBox else False
        ))
    else:
        log("未找到 AskBloriko_Button 元素")

    if not AskBloriko_Edit:
        log("未找到 AskBloriko_Edit 元素")

    if not AskBloriko_Answer:
        log("未找到 AskBloriko_Answer 元素")

    BloretServerIP = widget.findChild(QLabel, "BloretServerIP")
    BloretServerOnlineNumber = widget.findChild(QLabel, "BloretServerOnlineNumber")
    BloretServerText0 = widget.findChild(QLabel, "BloretServerText0")
    BloretServerText1 = widget.findChild(QLabel, "BloretServerText1")
    BloretServer_BestTime = widget.findChild(QLabel, "BloretServer_BestTime")
    if BloretServer_BestTime:
        BloretServer_BestTime.setWordWrap(True)

    def _stringify_server_value(value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (int, float, str)):
            return str(value)
        if isinstance(value, list):
            items = [str(item) for item in value if str(item).strip()]
            return "、".join(items)
        return json.dumps(value, ensure_ascii=False)

    def _collect_extra_lines(value, prefix=""):
        lines = []
        if isinstance(value, dict):
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                lines.extend(_collect_extra_lines(item, next_prefix))
            return lines
        if isinstance(value, list):
            if value and all(not isinstance(item, (dict, list)) for item in value):
                rendered = _stringify_server_value(value)
                if rendered:
                    lines.append(f"- **{prefix}**: {rendered}")
                return lines
            for index, item in enumerate(value):
                next_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
                lines.extend(_collect_extra_lines(item, next_prefix))
            return lines

        rendered = _stringify_server_value(value)
        if rendered:
            lines.append(f"- **{prefix}**: {rendered}")
        return lines

    # 修复：正确处理getServerData返回的线程对象
    def update_server_info(data):
        if BloretServerOnlineNumber and BloretServerText0 and BloretServerText1 and BloretServer_BestTime:
            # 检查是否有错误信息
            if "error" in data:
                log(f"服务器数据获取失败: {data.get('error')}")
                if BloretServerIP:
                    BloretServerIP.setText("N/A")
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
                server_ip = real_time_status.get('host', data.get('ip', data.get('host', 'bloret.net')))

                displayed_fields = {'BestTime'}
                displayed_realtime_fields = {'playersOnline', 'playersMax', 'motdClean', 'host'}
                extra_lines = []

                for key, value in data.items():
                    if key in displayed_fields or key == 'realTimeStatus':
                        continue
                    extra_lines.extend(_collect_extra_lines(value, key))

                if isinstance(real_time_status, dict):
                    for key, value in real_time_status.items():
                        if key in displayed_realtime_fields:
                            continue
                        extra_lines.extend(_collect_extra_lines(value, f"realTimeStatus.{key}"))

                log(f"从数据中提取: server_ip={server_ip}, players_online={players_online}, players_max={players_max}, motd_clean={motd_clean}, best_time={best_time}, extra_lines_count={len(extra_lines)}")

                # 检查QLabel对象是否存在
                if not BloretServerOnlineNumber:
                    log("BloretServerOnlineNumber QLabel not found.")
                if not BloretServerText0:
                    log("BloretServerText0 QLabel not found.")
                if not BloretServerText1:
                    log("BloretServerText1 QLabel not found.")
                if not BloretServer_BestTime:
                    log("BloretServer_BestTime QLabel not found.")

                if BloretServerIP:
                    BloretServerIP.setText(str(server_ip))

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

                detail_sections = []
                if str(best_time).strip():
                    detail_sections.append(str(best_time))
                if extra_lines:
                    detail_sections.append("**其余服务器数据**\n" + "\n".join(extra_lines))

                BloretServer_BestTime.setText("\n\n".join(detail_sections))
                log(f"UI已更新: BloretServerIP='{server_ip}', BloretServerOnlineNumber='{players_online} / {players_max}', extra_lines_count={len(extra_lines)}")
            except Exception as e:
                log(f"处理服务器数据时出错: {str(e)}")
                if BloretServerIP:
                    BloretServerIP.setText("N/A")
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
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    loading_label = widget.findChild(QLabel, "loading_label")
    if loading_label:
        self.setup_loading_gif(loading_label)

def setup_download_old_ui(self,widget,LM_Download_Way_list,ver_id_bloret,homeInterface):
    '''
    设定 Bloret Launcher 下载界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
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
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
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
        
    ScreenCutButton = widget.findChild(QPushButton, "ScreenCutButton")
    if ScreenCutButton:
        # 保持对截图窗口的引用，防止被垃圾回收
        self.screenshot_widget = None
        def start_screenshot():
            self.screenshot_widget = ScreenShortCut()
        ScreenCutButton.clicked.connect(start_screenshot)

class AvatarLoaderThread(QThread):
    avatar_loaded = pyqtSignal(str, bytes)

    def __init__(self, username):
        super().__init__()
        self.username = username

    def run(self):
        try:
            # log(f"后台线程开始加载头像: {self.username}")
            # 添加 User-Agent 以避免请求被拒绝
            headers = {"User-Agent": "BloretLauncher/1.0"}
            res = requests.get(f"https://visage.surgeplay.com/face/45/{self.username}", headers=headers, timeout=10)
            if res.status_code == 200:
                self.avatar_loaded.emit(self.username, res.content)
            else:
                log(f"头像加载失败 {self.username}: 状态码 {res.status_code}")
        except Exception as e:
            log(f"头像加载异常 {self.username}: {str(e)}")

def setup_passport_ui(self, widget, homeInterface):
    '''
    设定 Bloret Launcher 通行证界面 UI 布局和操作。
    适配 MinecraftAccounts (QWidget) 动态列表，支持局部刷新。
    '''
    
    # 1. 基础按钮功能绑定
    manage_web_btn = widget.findChild(QPushButton, "ManageMinecraftAccountOnBloretPassPortWebsite")
    if manage_web_btn:
        manage_web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://passport.bloret.net/minecraft")))

    sync_cloud_btn = widget.findChild(QPushButton, "go_Minecraft_Account_To_Bloret_PassPort_Cloud_from")
    if sync_cloud_btn:
        sync_cloud_btn.clicked.connect(lambda: sync_bloret_passport_account_to_mc(self))

    # Bloret PassPort 账户状态
    Bloret_PassPort_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
    if Bloret_PassPort_UserName:
        Bloret_PassPort_UserName.setText(self.config.get('Bloret_PassPort_UserName', i18nText('未登录')))

    Bloret_PassPort_login = widget.findChild(QPushButton, "Bloret_PassPort_login")
    if Bloret_PassPort_login:
        Bloret_PassPort_login.clicked.connect(lambda: Bloret_PassPort_Account_login())

    Bloret_PassPort_logout = widget.findChild(QPushButton, "Bloret_PassPort_logout")
    if Bloret_PassPort_logout:
        Bloret_PassPort_logout.clicked.connect(lambda: Bloret_PassPort_Account_logout(self, homeInterface))

    # --- 核心：Minecraft 账户列表管理 ---
    
    accounts_container = widget.findChild(QWidget, "MinecraftAccounts")
    if accounts_container and not accounts_container.layout():
        layout = QVBoxLayout(accounts_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

    def update_cards_visual():
        '''不重建 UI，仅更新卡片的高亮状态和按钮文字'''
        layout = accounts_container.layout()
        chosen_idx = self.config.get("MinecraftAccount", {}).get("chosen", 0)
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            card = item.widget()
            if not isinstance(card, CardWidget): continue
            
            # 获取卡片内的按钮
            btn = card.findChild(PushButton, "action_btn")
            if i == chosen_idx:
                card.setStyleSheet("CardWidget { border: 2px solid #0078d4; background-color: rgba(0, 120, 212, 0.05); }")
                btn.setText(i18nText("正在使用"))
                btn.setEnabled(False)
            else:
                card.setStyleSheet("")
                btn.setText(i18nText("使用此账户"))
                btn.setEnabled(True)

    def refresh_minecraft_accounts():
        '''物理重建账户列表（下载头像、创建卡片）'''
        # 1. 先从磁盘加载最新数据（防止 PassPort 云端同步后内存数据过时）
        self.load_config()
        
        layout = accounts_container.layout()
        # 清理旧卡片
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        mc_data = self.config.get("MinecraftAccount", {})
        accounts = mc_data.get("accounts", [])
        chosen_idx = mc_data.get("chosen", 0)

        if not accounts:
            layout.addWidget(BodyLabel(i18nText("暂无账户，请从云端同步")))
            return

        # 确保 MainWindow 实例有存储线程的列表
        if not hasattr(self, 'avatar_threads'):
            self.avatar_threads = []

        # 定义回调函数（避免在循环中重复定义）
        def on_avatar_loaded(u, data, lbl):
            log(f"头像加载成功: {u}")
            p = QPixmap()
            if p.loadFromData(data):
                lbl.setPixmap(p)

        def cleanup_thread(t):
            if t in self.avatar_threads:
                self.avatar_threads.remove(t)
            t.deleteLater()

        for i, acc in enumerate(accounts):
            username = acc.get("username", "Unknown")
            acc_type = acc.get("type", "Offline")
            uuid = acc.get("uuid", username)

            card = CardWidget(accounts_container)
            card.setFixedHeight(75)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            
            # 头像 (ImageLabel)
            avatar_label = ImageLabel(card)
            avatar_label.setFixedSize(45, 45)
            avatar_label.setBorderRadius(4, 4, 4, 4)
            avatar_label.setPixmap(QPixmap(resource_path("ui/icon/DefaultHead.png")))
            
            # 异步加载头像 (使用线程)
            thread = AvatarLoaderThread(username)
            thread.avatar_loaded.connect(lambda u, d, l=avatar_label: on_avatar_loaded(u, d, l))
            thread.finished.connect(lambda t=thread: cleanup_thread(t))
            self.avatar_threads.append(thread)
            thread.start()

            # 文本信息
            txt_lyt = QVBoxLayout()
            txt_lyt.setSpacing(2)
            name_lbl = StrongBodyLabel(username, card)
            type_lbl = CaptionLabel(i18nText("离线登录") if acc_type == "Offline" else i18nText("微软登录"), card)
            type_lbl.setTextColor(QColor(150, 150, 150), QColor(200, 200, 200))
            txt_lyt.addWidget(name_lbl)
            txt_lyt.addWidget(type_lbl)
            
            # 操作按钮 (设置 ObjectName 以便后期局部更新)
            btn = PushButton(card)
            btn.setObjectName("action_btn")
            btn.setFixedWidth(100)
            btn.clicked.connect(lambda checked, idx=i: switch_account(idx))

            card_layout.addWidget(avatar_label)
            card_layout.addLayout(txt_lyt)
            card_layout.addStretch(1)
            card_layout.addWidget(btn)
            
            layout.addWidget(card)
        
        update_cards_visual()

    def switch_account(index):
        '''切换逻辑：直接读写磁盘以避免 save_config 的回滚机制'''
        try:
            # 1. 读取磁盘上的最新配置
            with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                disk_config = json.load(f)
            
            mc_data = disk_config.get("MinecraftAccount", {})
            accounts = mc_data.get("accounts", [])
            
            if index >= len(accounts): 
                log(f"切换失败：索引 {index} 越界")
                return

            log(f"正在切换到账户索引: {index}")

            # 2. 修改磁盘配置并保存
            if "MinecraftAccount" in disk_config:
                disk_config["MinecraftAccount"]["chosen"] = index
                with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                    json.dump(disk_config, f, ensure_ascii=False, indent=4)
            
            # 3. 同步更新内存配置
            if "MinecraftAccount" in self.config:
                self.config["MinecraftAccount"]["chosen"] = index
                # 如果账户列表有变动，也同步一下（虽然此时只是切换索引）
                self.config["MinecraftAccount"]["accounts"] = accounts

            # 4. 更新主程序全局变量
            acc = accounts[index]
            self.player_name = acc.get("username", "")
            self.player_uuid = acc.get("uuid", "")
            acc_type = acc.get("type", "Offline")
            
            if acc_type == "Microsoft":
                self.login_mod = i18nText("微软登录")
            else:
                self.login_mod = i18nText("离线登录")
                
            log(f"账户已切换为: {self.player_name} ({self.login_mod})")

            # 5. 更新 UI 显示 (卡片状态)
            update_cards_visual()

            # 6. 刷新主页左上角的账户显示
            if homeInterface:
                Minecraft_account = homeInterface.findChild(QLabel, "Minecraft_account")
                if Minecraft_account:
                    if self.config.get('home_show_login_mod', False):
                        Minecraft_account.setText(f"[{self.login_mod}] {self.player_name}")
                    else:
                        Minecraft_account.setText(f"{self.player_name}")
                        
        except Exception as e:
            log(f"切换账户时发生错误: {str(e)}", logging.ERROR)

    # 绑定右上角刷新按钮
    refresh_btn = widget.findChild(QPushButton, "refreshMinecraftAccount")
    if refresh_btn:
        refresh_btn.clicked.connect(refresh_minecraft_accounts)

    # 初始加载
    refresh_minecraft_accounts()

def setup_settings_ui(self, widget):
    '''
    设定 Bloret Launcher 设置界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    minecraft_dir_link = widget.findChild(HyperlinkLabel, "minecraft_dir_link")
    if minecraft_dir_link:
        minecraft_dir_link.setText(BLglobals.minecraft_dir)
        minecraft_dir_link.setUrl(QUrl.fromLocalFile(BLglobals.minecraft_dir))

    log_clear_button = widget.findChild(QPushButton, "log_clear_button")
    if log_clear_button:
        log_clear_button.clicked.connect(lambda: clear_log_files(self,log_clear_button))
        self.update_log_clear_button_text(log_clear_button)

    log_dir_link = widget.findChild(HyperlinkLabel, "log_dir_link")
    if log_dir_link:
        log_dir_link.setText(os.path.join(BLglobals.datapath, "log"))
        log_dir_link.setUrl(QUrl.fromLocalFile(os.path.join(BLglobals.datapath, "log")))

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
                self.save_config() # 使用 MainWindow 提供的安全保存方法
                log(f"语言设置已更改为: {lang_code}")
            
            language_choose.currentTextChanged.connect(on_language_changed)
        except Exception as e:
            log(f"读取语言配置文件失败: {e}")
            # 出错时使用原有逻辑
            language_choose.addItems(["zh-cn", "en-GB"])
            language_choose.setCurrentText(self.config.get("language", "zh-cn"))
            language_choose.currentTextChanged.connect(lambda language: (
                self.config.update(language=language),
                open(BLglobals.config_path, 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4)),
                log(f"语言设置已更改为: {language}")
            ))

    # Java 选择配置
    Java_Choose = widget.findChild(ComboBox, "Java_Choose")
    if Java_Choose:
        try:
            Java_Choose.clear()
            
            # 定义常量字符串
            AUTO_TEXT = i18nText("自动 (使用系统环境变量)")
            BROWSE_TEXT = i18nText("浏览...")
            
            # 添加 "自动" 选项
            Java_Choose.addItem(AUTO_TEXT)
            
            # 扫描并添加 Java 路径
            scanned_java = scan_java_paths()
            for path in scanned_java:
                Java_Choose.addItem(path)
                
            # 添加 "浏览..." 选项
            Java_Choose.addItem(BROWSE_TEXT)
            
            # 设置当前选中项
            current_java = self.config.get("java_path", "Auto")
            
            if current_java == "Auto" or not current_java:
                Java_Choose.setCurrentIndex(0)
            else:
                # 检查是否存在于列表中
                index = Java_Choose.findText(current_java)
                if index != -1:
                    Java_Choose.setCurrentIndex(index)
                else:
                    # 如果不在列表中（可能是手动添加的），插入到自动选项之后
                    Java_Choose.insertItem(1, current_java)
                    Java_Choose.setCurrentText(current_java)
                    
            # 处理选择变化
            def on_java_changed(text):
                if text == AUTO_TEXT:
                    self.config["java_path"] = "Auto"
                    self.save_config()
                    log("Java 设置已更改为: 自动")
                elif text == BROWSE_TEXT:
                    file_path, _ = QFileDialog.getOpenFileName(
                        self, 
                        i18nText("选择 Java 可执行文件 (java.exe)"), 
                        "", 
                        "Java Executable (java.exe);;All Files (*.*)"
                    )
                    if file_path:
                        # 检查是否已存在，不存在则添加
                        if Java_Choose.findText(file_path) == -1:
                            Java_Choose.insertItem(1, file_path)
                        Java_Choose.setCurrentText(file_path)
                        self.config["java_path"] = file_path
                        self.save_config()
                        log(f"Java 设置已更改为: {file_path}")
                    else:
                        # 用户取消，恢复之前的选择
                        prev_java = self.config.get("java_path", "Auto")
                        if prev_java == "Auto":
                            Java_Choose.setCurrentIndex(0)
                        else:
                            Java_Choose.setCurrentText(prev_java)
                else:
                    self.config["java_path"] = text
                    self.save_config()
                    log(f"Java 设置已更改为: {text}")
                    
            Java_Choose.currentTextChanged.connect(on_java_changed)
        except Exception as e:
            log(f"设置 Java 选项失败: {e}", logging.ERROR)

    size_choose = widget.findChild(SpinBox, "Size_Choose")
    if size_choose:
        size_choose.setValue(self.config.get("size", 100))
        size_choose.valueChanged.connect(lambda value: (
            self.config.update(size=value),
            self.save_config()
        ))

    MaxThread_SpinBox = widget.findChild(SpinBox, "MaxThread_SpinBox")
    if MaxThread_SpinBox:
        MaxThread_SpinBox.setValue(self.config.get("MaxThread", 2000))
        MaxThread_SpinBox.valueChanged.connect(lambda value: (
            self.config.update(MaxThread=value),
            self.save_config()
        ))

    repeat_run_button = widget.findChild(SwitchButton, "repeat_run_button")
    if repeat_run_button:
        repeat_run_button.setChecked(self.config.get('repeat_run', False))
        repeat_run_button.checkedChanged.connect(lambda state: (
            self.config.update(repeat_run=state),
            self.save_config(),
            log(f"重复运行设置已更改为: {'启用' if state else '禁用'}")
        ))
    show_runtime_do_button = widget.findChild(SwitchButton, "show_runtime_do_button")
    if show_runtime_do_button:
        show_runtime_do_button.setChecked(self.config.get('show_runtime_do', False))
        show_runtime_do_button.checkedChanged.connect(lambda state: (
            self.config.update(show_runtime_do=state),
            self.save_config(),
            log(f"显示软件打开过程: {'启用' if state else '禁用'}")
        ))
    BL_version = widget.findChild(QLabel, "BL_version")
    if BL_version:
        BL_version.setText(f"{self.config.get('ver', '未知')}")
    
    localmod_button = widget.findChild(SwitchButton, "localmod_button")
    if localmod_button:
        localmod_button.setChecked(self.config.get('localmod', False))
        # 修复：统一使用 self.save_config()，禁止直接写文件
        localmod_button.checkedChanged.connect(lambda state: (
            self.config.update(localmod=state),
            self.save_config(),
            log(f"本地模式: {'启用' if state else '禁用'}")
        ))
        
    home_show_login_mod_button = widget.findChild(SwitchButton, "home_show_login_mod_button")
    if home_show_login_mod_button:
        home_show_login_mod_button.setChecked(self.config.get('home_show_login_mod', False))
        # 修复：统一使用 self.save_config()，禁止直接写文件
        home_show_login_mod_button.checkedChanged.connect(lambda state: (
            self.config.update(home_show_login_mod=state),
            self.save_config(),
            log(f"在首页上 显示 Minecraft 账户登录方式: {'启用' if state else '禁用'}")
        ))
    
    Self_starting = widget.findChild(SwitchButton, "Self_starting")
    if Self_starting:
        Self_starting.setChecked(self.config.get("self-starting", False))
        # 修复：传递 self (MainWindow实例) 给回调函数，以便更新内存中的 config
        Self_starting.checkedChanged.connect(lambda val: on_self_starting_changed(self, val))
    else:
        log(i18nText("未找到 Self_starting 控件"))

    mwtool_switch_open = widget.findChild(SwitchButton, "mwtool_switch_open")
    if mwtool_switch_open:
        mwtool_switch_open.setChecked(self.config.get('mwtool_switch_open', True))
        mwtool_switch_open.checkedChanged.connect(lambda state: (
            self.config.update(mwtool_switch_open=state),
            self.save_config(),
            log(f"Minecraft 浮动工具栏: {'启用' if state else '禁用'}")
        ))

def setup_multiplayer_ui(self, widget):
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
        start_online_client_btn.clicked.connect(lambda: start_online_client(self, widget))
        log(i18nText("已连接StartOnlineClient按钮"))
    else:
        log(i18nText("未找到StartOnlineClient按钮"))

    ClientOnlineClient = widget.findChild(QPushButton, "ClientOnlineClient")
    if ClientOnlineClient:
        ClientOnlineClient.clicked.connect(lambda: client_online_client(self, widget))
        log(i18nText("已连接ClientOnlineClient按钮"))
    else:
        log(i18nText("未找到ClientOnlineClient按钮"))


def start_online_client(parent, clientpage):
    """启动在线客户端服务"""

    def show_login_message():
        log("显示登录提示消息框", logging.INFO)
        w = MessageBox("登录才可使用联机功能", "Easytier 联机需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。", parent)
        if w.exec():
            parent.switchTo(parent.passportInterface)
            log("用户点击确认，切换到通行证界面", logging.INFO)

    if not config.get("Bloret_PassPort_Login", False):
        # 在主线程中显示消息框
        QTimer.singleShot(0, show_login_message)
        return

    # 创建端口输入对话框
    port_dialog = MessageBoxBase(parent)
    port_dialog.setWindowTitle(i18nText("开启联机服务"))
    
    port_label = BodyLabel(i18nText("请输入您的 Minecraft 端口"))
    port_input = LineEdit()
    port_input.setPlaceholderText(i18nText("默认端口: 25565"))
    port_input.setText("25565")  # 设置默认端口
    
    port_dialog.viewLayout.addWidget(port_label)
    port_dialog.viewLayout.addWidget(port_input)
    
    # 添加联机密钥输入框
    online_key_label = BodyLabel(i18nText("请输入联机密钥"))
    online_key_input = LineEdit()
    online_key_input.setPlaceholderText(i18nText("联机密钥"))
    online_key_input.setEchoMode(LineEdit.Password) # 设置为密码模式
    
    port_dialog.viewLayout.addWidget(online_key_label)
    port_dialog.viewLayout.addWidget(online_key_input)

    # 添加动图
    gif_label = QLabel()
    movie = QMovie(resource_path("ui/icon/OnlineClient.gif"))
    gif_label.setMovie(movie)
    movie.start()
    movie.setScaledSize(QSize(500, 280))  # 设置动图大小
    
    port_dialog.viewLayout.addWidget(gif_label)
    
    port_dialog.yesButton.setText(i18nText("确认"))
    port_dialog.cancelButton.setText(i18nText("取消"))
    
    def handle_port_confirm():
        port = port_input.text().strip()
        online_key = online_key_input.text().strip() # 获取联机密钥
        if not port.isdigit():
            InfoBar.error(
                title=i18nText('输入错误'),
                content=i18nText('请输入有效的端口号'),
                parent=parent
            )
            return False
        
        # 检查联机密钥是否为空
        if not online_key:
            online_key = "NoPassWord"
        
        # 调用OnlineClient函数
        try:
            # 将端口转换为整数再传递
            port_int = int(port)
            # 调用 StartEasytierServer 函数
            username = config.get("Bloret_PassPort_UserName", "")
            easytier_name = "BLClient"+username
            # 检查用户名是否为空
            if not easytier_name:
                InfoBar.error(
                    title=i18nText('启动失败'),
                    content=i18nText('无法获取用户名，请重新登录 Bloret PassPort'),
                    parent=parent
                )
                return False
                
            connection_address = StartEasytierServer(easytier_name, online_key)
            
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
            # 以下是联机信息示例：
            # 和我用 Bloret Launcher 联机！打开 Bloret Launcher 进入联机页面，选择“连接到对方的网络”，输入我的用户名 {username} 即可和我在 Minecraft 中一起游玩！如还未下载 Bloret Launcher ，请访问 https://launcher.bloret.net/

            # connection_info = "{\"ip\":\""+connection_address+"\",\"key\":\""+online_key+"\",\"port\":\""+port+"\",\"username\":\""+easytier_name+"\"}"
            # full_text = "和我用 Bloret Launcher 联机！打开 Bloret Launcher 并进入联机页面，即可和我在 Minecraft 中一起游玩！如还未下载 Bloret Launcher ，请访问 https://launcher.bloret.net/ . (%/BLClient%)"+connection_info+"(%/BLClient%) 复制该信息，输入 Bloret Launcher 联机页面的连接信息中即可加入联机。"

            # 此处发送必要信息到 Bloret PassPort 的 public 数据中，以便客户端读取
            ClinetPublic = readdata("Client", True)
            # 这里返回的数据是 str, 需要先转换为字典再处理
            ClinetPublic = json.loads(ClinetPublic)

            # 向 ClinetPublic 加入联机信息 username:{ip:connection_address, port:port, username:easytier_name}
            ClinetPublic[easytier_name] = {"ip":connection_address, "port":port, "username":easytier_name}
            
            # 重新转换为 str 再保存
            ClinetPublic = json.dumps(ClinetPublic)
            savedata("Client", ClinetPublic, True)

            full_text = f"和我用 Bloret Launcher 联机！打开 Bloret Launcher 进入联机页面，选择“连接到对方的网络”，输入我的用户名 {username} 即可和我在 Minecraft 中一起游玩！如还未下载 Bloret Launcher ，请访问 https://launcher.bloret.net/"
            show_connection_address_dialog(parent, full_text, connection_address + ':' + port, clientpage, True)
            return True
        except Exception as e:
            log(f"启动联机服务时出错: {str(e)}", logging.ERROR)
            InfoBar.error(
                title=i18nText('启动失败'),
                content=f'启动联机服务时出错: {str(e)}',
                parent=parent
            )
            return False
    
    def connect_handler():
        handle_port_confirm()
        
    port_dialog.yesButton.clicked.connect(connect_handler)
    port_dialog.exec_()

def client_online_client(parent, clientpage):
    """连接在线客户端服务（加入者模式）"""
    log("client_online_client: 开始执行客户端联机功能", logging.INFO)
    log(f"client_online_client: 传入参数 - parent: {parent}, clientpage: {clientpage}", logging.DEBUG)

    def show_login_message():
        log("client_online_client: 显示登录提示消息框", logging.INFO)
        w = MessageBox("登录才可使用联机功能", "Easytier 联机需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。", parent)
        if w.exec_():
            parent.switchTo(parent.passportInterface)
            log("client_online_client: 用户点击确认，切换到通行证界面", logging.INFO)

    # 检查登录状态
    login_status = config.get("Bloret_PassPort_Login", False)
    log(f"client_online_client: Bloret PassPort 登录状态: {login_status}", logging.INFO)

    if not login_status:
        log("client_online_client: 用户未登录，显示登录提示", logging.WARNING)
        # 在主线程中显示消息框
        QTimer.singleShot(0, show_login_message)
        return

    log("client_online_client: 用户已登录，继续执行联机流程", logging.INFO)

    # 创建连接信息输入对话框
    log("client_online_client: 创建连接信息输入对话框", logging.INFO)
    connect_dialog = MessageBoxBase(parent)
    connect_dialog.setWindowTitle(i18nText("连接到房主的网络"))

    name_label = BodyLabel(i18nText("请输入房主的 Bloret PassPort 用户名"))
    name_input = LineEdit()
    name_input.setPlaceholderText(i18nText('房主用户名'))

    # 密码输入框
    key_label = BodyLabel(i18nText("请输入房主的联机密钥"))
    key_input = LineEdit()
    key_input.setPlaceholderText(i18nText('房主密钥'))
    # 将密码输入框设置为密码模式
    key_input.setEchoMode(LineEdit.Password)

    # 房主 IP 输入框
    ip_label = BodyLabel(i18nText("请输入房主的局域网 IP 地址"))
    ip_input = LineEdit()
    ip_input.setPlaceholderText(i18nText('例如: 192.168.3.168'))
    
    # 获取本机 IP 作为提示
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_input.setPlaceholderText(i18nText(f'例如: {local_ip.rsplit(".", 1)[0]}.xxx'))
    except:
        pass

    connect_dialog.viewLayout.addWidget(name_label)
    connect_dialog.viewLayout.addWidget(name_input)
    connect_dialog.viewLayout.addWidget(key_label)
    connect_dialog.viewLayout.addWidget(key_input)
    connect_dialog.viewLayout.addWidget(ip_label)
    connect_dialog.viewLayout.addWidget(ip_input)

    connect_dialog.yesButton.setText(i18nText("确认"))
    connect_dialog.cancelButton.setText(i18nText("取消"))

    log("client_online_client: 对话框组件初始化完成", logging.DEBUG)

    def handle_connect_confirm():
        try:
            log("client_online_client: 用户点击确认连接按钮", logging.INFO)

            # 获取用户输入的用户名
            username = name_input.text().strip()
            log(f"client_online_client: 获取用户名输入: '{username}'", logging.DEBUG)

            if not username:
                log("client_online_client: 用户名为空，显示错误提示", logging.WARNING)
                InfoBar.error(
                    title=i18nText('输入错误'),
                    content=i18nText('请输入房主用户名'),
                    parent=parent
                )
                return

            # 获取用户输入的联机密钥
            key = key_input.text().strip()
            log(f"client_online_client: 获取联机密钥输入: {'*' * len(key) if key else '空'}", logging.DEBUG)

            # 检查联机密钥是否为空
            if not key:
                key = "NoPassWord"

            # 获取房主 IP
            peer_ip = ip_input.text().strip()
            log(f"client_online_client: 获取房主 IP: '{peer_ip}'", logging.DEBUG)

            if not peer_ip:
                log("client_online_client: 房主 IP 为空，显示错误提示", logging.WARNING)
                InfoBar.error(
                    title=i18nText('输入错误'),
                    content=i18nText('请输入房主的局域网 IP 地址'),
                    parent=parent
                )
                return

            log(f"client_online_client: 开始连接 - 房主用户名: {username}, 密钥长度: {len(key)}, 房主 IP: {peer_ip}", logging.INFO)

            # 调用 StartEasytierServer 函数连接到房主网络（加入者模式）
            connection_address = StartEasytierServer(username, key, is_host=False, peer_ip=peer_ip)
            log(f"client_online_client: StartEasytierServer 返回结果: {connection_address}", logging.DEBUG)

            # 检查是否返回了错误信息
            if isinstance(connection_address, str) and (connection_address.startswith(i18nText("权限错误：")) or connection_address.startswith(i18nText("安全软件阻止："))):
                log(f"client_online_client: 权限或安全软件错误: {connection_address}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('连接失败'),
                    content=connection_address,
                    parent=parent,
                    duration=10000
                )
                return
            elif isinstance(connection_address, str) and (connection_address.startswith(i18nText("启动失败:")) or connection_address == i18nText("网络请求失败") or connection_address == i18nText("配置文件不存在") or connection_address == i18nText("frpc程序不存在") or connection_address == i18nText("获取连接信息失败")):
                log(f"client_online_client: 连接失败: {connection_address}", logging.ERROR)
                InfoBar.error(
                    title=i18nText('连接失败'),
                    content=connection_address,
                    parent=parent
                )
                return
            elif isinstance(connection_address, str) and connection_address.startswith(i18nText("~")):
                # 连接尝试成功，但未获取到虚拟 IP
                log("client_online_client: 连接尝试成功，但未获取到虚拟 IP", logging.WARNING)
                msg = connection_address[1:]  # 移除 ~ 前缀
                InfoBar.warning(
                    title=i18nText('连接尝试'),
                    content=msg,
                    parent=parent,
                    duration=10000
                )
                return

            log("client_online_client: 连接成功，开始获取服务器信息", logging.INFO)
            
            # 获取虚拟 IP 成功后，从 PassPort 获取房主的服务器信息
            ClinetPublic = readdata("Client", True)
            ClinetPublic = json.loads(ClinetPublic)

            full_username = 'BLClient' + username
            if full_username not in ClinetPublic:
                log(f"client_online_client: 房主 {full_username} 不存在于公共数据中", logging.ERROR)
                InfoBar.error(
                    title=i18nText('连接失败'),
                    content=f'房主 {username} 未找到或不在线',
                    parent=parent
                )
                return

            # 获取房主的端口信息
            port = ClinetPublic[full_username]["port"]
            log(f"client_online_client: 房主服务器端口: {port}", logging.INFO)

            # 显示连接成功信息
            server_address = f"{connection_address}:{port}"
            show_connection_address_dialog(
                parent, 
                f"已成功连接到房主 {username} 的网络！\n\nMinecraft 服务器地址: {server_address}\n\n现在打开 Minecraft，添加服务器并连接。", 
                server_address, 
                clientpage, 
                False
            )
            
        except json.JSONDecodeError as e:
            log(f"client_online_client: JSON解析错误: {str(e)}", logging.ERROR)
            InfoBar.error(
                title=i18nText('解析失败'),
                content=f'连接信息解析错误: {str(e)}',
                parent=parent
            )
            return
        except KeyError as e:
            log(f"client_online_client: 数据字段缺失: {str(e)}", logging.ERROR)
            InfoBar.error(
                title=i18nText('数据错误'),
                content=f'服务器数据格式错误，缺少字段: {str(e)}',
                parent=parent
            )
            return
        except Exception as e:
            log(f"client_online_client: 连接过程发生未知错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            InfoBar.error(
                title=i18nText('连接失败'),
                content=f'连接联机服务时出错: {str(e)}',
                parent=parent
            )

    connect_dialog.yesButton.clicked.connect(handle_connect_confirm)
    log("client_online_client: 连接对话框事件绑定完成", logging.DEBUG)

    log("client_online_client: 显示连接对话框，等待用户输入", logging.INFO)
    connect_dialog.exec_()
    log("client_online_client: 连接对话框关闭", logging.INFO)

def show_connection_address_dialog(parent, text, ipandport, clientpage, isserver):
    """
    显示连接地址对话框
    联机信息：
    和我用 Bloret Launcher 联机！打开 Bloret Launcher 进入联机页面，选择“连接到对方的网络”，输入我的用户名 {username} 即可和我在 Minecraft 中一起游玩！如还未下载 Bloret Launcher ，请访问 https://launcher.bloret.net/
    """
    # 创建结果显示对话框
    result_dialog = MessageBoxBase(parent)
    result_dialog.setWindowTitle(i18nText("联机服务已启动"))
    
    address_label = StrongBodyLabel(text)
    address_label.setAlignment(Qt.AlignCenter if hasattr(Qt, 'AlignCenter') else Qt.AlignmentFlag.AlignCenter)
    address_label.setWordWrap(True)  # 启用自动换行
    address_label.setMaximumWidth(400)  # 设置最大宽度，确保文本不会过长

    if isserver:
        instruction_text = "按下确认键复制到剪贴板，然后发给好友，在 Minecraft 客户端中添加服务器并加入。"
    else:
        instruction_text = "按下确认键复制到剪贴板，然后在 Minecraft 客户端中添加服务器并加入。"
    
    instruction_label = CaptionLabel(i18nText(instruction_text))
    instruction_label.setAlignment(Qt.AlignCenter if hasattr(Qt, 'AlignCenter') else Qt.AlignmentFlag.AlignCenter)
    
    
    result_dialog.viewLayout.addWidget(address_label)
    result_dialog.viewLayout.addWidget(instruction_label)
    # result_dialog.viewLayout.addWidget(gif_label)
    
    result_dialog.yesButton.setText(i18nText("确认"))
    result_dialog.cancelButton.hide()  # 隐藏取消按钮
    
    def handle_result_confirm():
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
        InfoBar.success(
            title=i18nText('复制成功'),
            content=i18nText('联机地址已复制到剪贴板'),
            parent=parent
        )
        
        # 更新界面上的地址和时间显示
        # 获取界面上的时间和地址标签
        
        # 从parent中查找标签（联机界面）
        # online_client_time_label = parent.findChild(QLabel, "OnlineClient_ClientTime")
        # online_client_address_label = parent.findChild(QLabel, "OnlineClient_address")
        
        # 更新多人联机界面的状态显示
        # 查找并更新UI中的标签 (使用UI文件中实际的组件名称)
        client_status_label = clientpage.findChild(QLabel, "Client_Statue")  # "未连接" 标签
        client_status_desc_label = clientpage.findChild(QLabel, "Client_Statue_Show")  # "您尚未连接到 Easytier 网络" 标签
        client_link_tip_label = clientpage.findChild(QLabel, "Client_link_tip")    # "请打开 Minecraft，并像加入服务器一样加入 " 标签
        client_link_show_label = clientpage.findChild(QLabel, "Client_link_show")  # 地址显示标签
        
        log(f"查找界面组件:")
        log(f"  parent: {clientpage}")
        log(f"  client_status_label: {client_status_label}")
        log(f"  client_status_desc_label: {client_status_desc_label}")
        log(f"  client_link_tip_label: {client_link_tip_label}")
        log(f"  client_link_show_label: {client_link_show_label}")
        # log(f"  online_client_time_label: {online_client_time_label}")
        # log(f"  online_client_address_label: {online_client_address_label}")
        
        # 强制刷新界面
        if client_status_label:
            client_status_label.setText(i18nText("已连接"))
            client_status_label.repaint()  # 强制重绘
            log(f"已更新连接状态标签: {i18nText('已连接')}")
        else:
            log("未找到 Client_Statue 标签")
            
        if client_status_desc_label:
            client_status_desc_label.setText(i18nText("您已连接至 Easytier 网络"))
            client_status_desc_label.repaint()  # 强制重绘
            log(f"已更新连接状态描述标签: {i18nText('您已连接至 Easytier 网络')}")
        else:
            log("未找到 Client_Statue_Show 标签")
            
        if client_link_tip_label:
            if isserver:
                tip_text = "请告诉对方端口号、你的用户名和联机密钥，然后让对方打开 Bloret Launcher 连接"
            else:
                tip_text = "请打开 Minecraft，并像加入服务器一样加入 "
            client_link_tip_label.setText(i18nText(tip_text))
            client_link_tip_label.repaint()  # 强制重绘
            log(f"已更新连接提示标签: {i18nText(tip_text)}")
        else:
            log("未找到 Client_link_tip 标签")
            
        if client_link_show_label:
            client_link_show_label.setText(ipandport)
            client_link_show_label.repaint()  # 强制重绘
            log(f"已更新连接地址显示标签: {ipandport}")
        else:
            log("未找到 Client_link_show 标签")
        
        # if online_client_address_label:
        #     online_client_address_label.setText(connection_address)
        #     online_client_address_label.repaint()  # 强制重绘
        #     log(f"已更新连接地址标签: {connection_address}")
        # else:
        #     log(i18nText("未找到OnlineClient_address标签"))
        
        # # 启动计时器更新连接时长
        # if online_client_time_label:
            
        #     # 记录开始时间
        #     start_time = QDateTime.currentDateTime()
            
        #     # 创建定时器每秒更新时间显示
        #     timer = QTimer()
        #     timer.timeout.connect(lambda: update_connection_time(online_client_time_label, start_time))
        #     timer.start(1000)  # 每秒更新一次
            
        #     # 将定时器保存到parent对象中，以便后续可以停止它
        #     parent.online_client_timer = timer
        #     parent.online_client_start_time = start_time
            
        #     # 立即更新一次时间显示
        #     update_connection_time(online_client_time_label, start_time)
        #     log(i18nText("已启动连接时长计时器"))
        # else:
        #     log(i18nText("未找到OnlineClient_ClientTime标签"))
    
    result_dialog.yesButton.clicked.connect(handle_result_confirm)
    result_dialog.exec_()

def update_connection_time(time_label, start_time):
    """更新连接时长显示"""
    
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
    gif_label = QLabel()
    movie = QMovie(resource_path("ui/icon/OnlineClient.gif"))
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
        gif_label = QLabel()
        movie = QMovie(resource_path("ui/icon/OnlineClient.gif"))
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
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
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
        qq_icon.setPixmap(QPixmap(resource_path("ui/icon/qq.png")))
    BLC_QQ = widget.findChild(QPushButton, "BLC_QQ")
    if BLC_QQ:
        BLC_QQ.clicked.connect(open_BLC_qq_link)

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
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    # 获取配置文件中的Minecraft版本列表
    try:
        with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
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
        java_version_choose = widget.findChild(ComboBox, 'Java_version_choose')
        
        if java_version_choose and java_versions:
            # 直接使用Java版本号填充选择框
            java_version_items = []
            for version in java_versions.keys():
                java_version_items.append(version)
            
            if java_version_items:
                java_version_choose.addItems(java_version_items)

        # 设置Minecraft版本下载按钮点击事件
        minecraft_download_button = widget.findChild(QPushButton, 'Minecraft_version_Download')
        if minecraft_download_button:
            def on_minecraft_download_button_clicked():
                version = minecraft_version_choose.currentText()
                dialog = VersionNameInputDialog(version, False, self)
                if dialog.exec():
                    version_name = dialog.get_version_name()
                    InstallMinecraftVersion(version, VersionName=version_name, download_dialog=None, Fabric_Loader=False)
            
            minecraft_download_button.clicked.connect(on_minecraft_download_button_clicked)
            
        # 设置Fabric版本下载按钮点击事件
        fabric_download_button = widget.findChild(QPushButton, 'Fabric_version_Download')
        if fabric_download_button:
            def on_fabric_download_button_clicked():
                version = fabric_version_choose.currentText()
                dialog = VersionNameInputDialog(version, True, self)
                if dialog.exec():
                    version_name = dialog.get_version_name()
                    InstallMinecraftVersion(version, VersionName=version_name, download_dialog=None, Fabric_Loader=True)
            
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


class ShortCutSettingDialog(MessageBoxBase):
    """截图快捷键设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.capturing = False
        self.current_keys = set()
        self.new_shortcut_text = ""
        
        # 标题
        self.titleLabel = SubtitleLabel(i18nText('设置截图快捷键'))
        self.titleLabel.setAlignment(Qt.AlignCenter)
        
        # 当前快捷键显示
        self.currentLabel = StrongBodyLabel(i18nText('当前快捷键:'))
        self.currentShortcut = StrongBodyLabel("Ctrl+Alt+A")  # 默认值
        self.currentShortcut.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # 新快捷键显示
        self.newLabel = StrongBodyLabel(i18nText('新快捷键:'))
        self.newShortcutLabel = StrongBodyLabel(i18nText('点击"开始捕捉"后按下快捷键组合'))
        self.newShortcutLabel.setStyleSheet("color: #666666; font-style: italic;")
        
        # 按钮区域
        self.buttonLayout = QHBoxLayout()
        self.startCaptureButton = PushButton(i18nText('开始捕捉'))
        self.clearButton = PushButton(i18nText('清除'))
        self.buttonLayout.addWidget(self.startCaptureButton)
        self.buttonLayout.addWidget(self.clearButton)
        
        # 提示信息
        self.tipLabel = CaptionLabel(i18nText('提示: 点击"开始捕捉"按钮，然后按下您想要的快捷键组合'))
        self.tipLabel.setTextColor("#666666", QColor(102, 102, 102))
        
        # 状态提示
        self.statusLabel = CaptionLabel(i18nText('准备就绪'))
        self.statusLabel.setTextColor("#0078d4", QColor(0, 120, 212))
        
        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.currentLabel)
        self.viewLayout.addWidget(self.currentShortcut)
        self.viewLayout.addWidget(self.newLabel)
        self.viewLayout.addWidget(self.newShortcutLabel)
        self.viewLayout.addLayout(self.buttonLayout)
        self.viewLayout.addWidget(self.tipLabel)
        self.viewLayout.addWidget(self.statusLabel)
        
        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(400)
        
        # 加载当前配置
        self.load_current_shortcut()
        
        # 连接按钮信号
        self.startCaptureButton.clicked.connect(self.start_capture)
        self.clearButton.clicked.connect(self.clear_shortcut)
        
        # 安装事件过滤器来捕捉按键
        self.installEventFilter(self)

    def load_current_shortcut(self):
        """从配置文件加载当前快捷键"""
        try:
            config = cfg.read()
            shortcut = config.get("screen_cut_shortcut", "Ctrl+Alt+A")
            self.currentShortcut.setText(shortcut)
        except Exception as e:
            log(f"加载当前快捷键失败: {e}", logging.ERROR)
            self.currentShortcut.setText("Ctrl+Alt+A")

    def start_capture(self):
        """开始捕捉按键"""
        self.capturing = True
        self.current_keys = set()
        self.newShortcutLabel.setText(i18nText("请按下快捷键组合..."))
        self.statusLabel.setText(i18nText("正在捕捉..."))
        self.startCaptureButton.setEnabled(False)
        self.widget.setFocus() # 确保对话框获得焦点

    def clear_shortcut(self):
        """清除新设置的快捷键"""
        self.new_shortcut_text = ""
        self.newShortcutLabel.setText(i18nText('已清除，请重新捕捉'))
        self.statusLabel.setText(i18nText('准备就绪'))
        self.capturing = False
        self.startCaptureButton.setEnabled(True)

    def eventFilter(self, obj, event):
        """事件过滤器，用于捕捉键盘事件"""
        # 确保属性存在再访问，避免 AttributeError
        is_capturing = getattr(self, 'capturing', False)
        
        if is_capturing and event.type() == event.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            # 忽略单独的控制键按下
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return True
                
            key_text = ""
            parts = []
            
            if modifiers & Qt.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.AltModifier:
                parts.append("Alt")
            if modifiers & Qt.MetaModifier:
                parts.append("Meta")
                
            # 获取键名
            from PySide6.QtGui import QKeySequence
            key_name = QKeySequence(key).toString()
            if key_name:
                parts.append(key_name)
                
            if parts:
                self.new_shortcut_text = "+".join(parts)
                self.newShortcutLabel.setText(self.new_shortcut_text)
                self.statusLabel.setText(i18nText("捕捉完成"))
                self.capturing = False
                self.startCaptureButton.setEnabled(True)
                
            return True # 拦截事件
            
        return super().eventFilter(obj, event)

    def validate(self):
        """验证是否有效"""
        return bool(self.new_shortcut_text)

    def save_shortcut(self):
        """保存快捷键到配置文件"""
        try:
            if not self.new_shortcut_text:
                return False
                
            config = cfg.read()
            config["screen_cut_shortcut"] = self.new_shortcut_text
            
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            return True
        except Exception as e:
            log(f"保存快捷键失败: {e}", logging.ERROR)
            return False

    def get_new_shortcut(self):
        """获取新设置的快捷键"""
        return self.new_shortcut_text


class VersionNameInputDialog(MessageBoxBase):
    """版本名输入对话框"""
    
    def __init__(self, version, is_fabric=False, parent=None):
        super().__init__(parent)
        self.version = version
        self.is_fabric = is_fabric
        BLglobals.minecraft_dir = self.get_minecraft_dir()
        
        # 标题
        title_text = i18nText('安装 {} 版本 {}').format('Fabric' if is_fabric else 'Minecraft', version)
        self.titleLabel = SubtitleLabel(title_text)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        
        # 版本名输入区域
        self.versionNameLabel = StrongBodyLabel(i18nText('版本名:'))
        self.versionNameInput = LineEdit()
        self.versionNameInput.setText(version)  # 默认为版本号
        self.versionNameInput.setPlaceholderText(i18nText('输入版本名（默认为版本号）'))
        
        # 错误提示标签（红色）
        self.errorLabel = CaptionLabel('')
        self.errorLabel.setTextColor("#ff0000", QColor(255, 0, 0))
        self.errorLabel.hide()
        
        # 提示信息
        self.tipLabel = CaptionLabel(i18nText('版本名将用于创建版本文件夹'))
        self.tipLabel.setTextColor("#666666", QColor(102, 102, 102))
        
        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.versionNameLabel)
        self.viewLayout.addWidget(self.versionNameInput)
        self.viewLayout.addWidget(self.errorLabel)
        self.viewLayout.addWidget(self.tipLabel)
        
        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(400)
        
        # 连接输入变化事件
        self.versionNameInput.textChanged.connect(self.on_version_name_changed)

        # 将取消按钮设为 "取消安装"
        self.cancelButton.setText(i18nText('取消安装'))
        
        # 初始检查
        self.validate_version_name()
    
    def get_minecraft_dir(self):
        """获取Minecraft目录路径"""
        try:
            with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('minecraft_dir', '')
        except:
            return ''
    
    def is_valid_windows_filename(self, filename):
        """检查是否符合Windows文件夹命名规则"""
        log(f"开始检查Windows文件夹命名规则，文件名: '{filename}'")
        
        if not filename or filename.strip() == '':
            log("检查失败：文件名为空或仅包含空格")
            return False, i18nText('版本名不能为空')
        
        log(f"文件名长度: {len(filename)} 字符")
        
        # Windows保留字
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        upper_filename = filename.upper()
        log(f"转换为大写: '{upper_filename}'")
        
        if upper_filename in reserved_names:
            log(f"检查失败：文件名是Windows保留字: {upper_filename}")
            return False, i18nText('版本名不能为Windows保留字')
        
        log("保留字检查通过")
        
        # 检查非法字符
        invalid_chars = '<>:"/\\|?*'
        log(f"检查非法字符: {invalid_chars}")
        for char in invalid_chars:
            if char in filename:
                log(f"检查失败：发现非法字符 '{char}' 在文件名中")
                return False, i18nText('版本名包含非法字符: {}').format(char)
        
        log("非法字符检查通过")
        
        # 检查开头和结尾
        if filename.startswith(' ') or filename.endswith(' '):
            log("检查失败：文件名以空格开头或结尾")
            return False, i18nText('版本名不能以空格开头或结尾')
        
        log("开头结尾空格检查通过")
        
        if filename.endswith('.') or filename.endswith('..'):
            log(f"检查失败：文件名以点结尾: '{filename}'")
            return False, i18nText('版本名不能以点结尾')
        
        log("结尾点检查通过")
        log(f"所有Windows文件夹命名规则检查通过: '{filename}'")
        return True, ''
    
    def version_folder_exists(self, version_name):
        """检查版本文件夹是否已存在"""
        log(f"=== 开始检查版本文件夹是否存在 ===")
        log(f"输入的版本名: '{version_name}'")
        
        if not BLglobals.minecraft_dir:
            log(f"minecraft_dir 未设置，BLglobals.minecraft_dir: {BLglobals.minecraft_dir}")
            log("=== 检查结束：版本文件夹不存在 ===")
            return False
        
        log(f"minecraft_dir 已设置: {BLglobals.minecraft_dir}")
        
        versions_dir = os.path.join(BLglobals.minecraft_dir, 'versions')
        log(f"versions_dir 路径: {versions_dir}")
        
        # 检查 versions 目录是否存在
        if not os.path.exists(versions_dir):
            log(f"警告：versions 目录不存在: {versions_dir}")
            log("=== 检查结束：版本文件夹不存在 ===")
            return False
        
        version_dir = os.path.join(versions_dir, version_name)
        log(f"完整的版本文件夹路径: {version_dir}")
        
        # 检查具体版本文件夹是否存在
        exists = os.path.exists(version_dir)
        log(f"版本文件夹存在状态: {exists}")
        
        if exists:
            log(f"版本文件夹已存在: {version_dir}")
            # 检查是否为目录
            if os.path.isdir(version_dir):
                log(f"确认 {version_dir} 是一个目录")
            else:
                log(f"警告：{version_dir} 存在但不是目录")
        else:
            log(f"版本文件夹不存在: {version_dir}")
        
        log("=== 检查结束 ===")
        return exists
    
    def validate_version_name(self):
        """验证版本名"""
        log("=== 开始验证版本名 ===")
        version_name = self.versionNameInput.text().strip()
        log(f"输入的版本名（去除前后空格）: '{version_name}'")
        
        # 检查Windows文件夹命名规则
        log("开始检查Windows文件夹命名规则...")
        is_valid, error_msg = self.is_valid_windows_filename(version_name)
        if not is_valid:
            log(f"Windows文件夹命名规则检查失败: {error_msg}")
            self.show_error(error_msg)
            log("=== 验证结束：失败 ===")
            return False
        
        log("Windows文件夹命名规则检查通过")
        
        # 检查版本文件夹是否已存在
        log("开始检查版本文件夹是否已存在...")
        if self.version_folder_exists(version_name):
            log(f"版本文件夹已存在，显示警告信息")
            self.show_warning(i18nText('版本文件夹 {} 已存在，确定将修复已安装的版本。').format(version_name))
            log("=== 验证结束：通过（显示警告） ===")
            return True  # 允许继续，但显示警告
        
        log("版本文件夹不存在，可以继续创建")
        
        # 通过验证
        log("所有验证检查通过")
        self.hide_error()
        log("=== 验证结束：成功 ===")
        return True
    
    def show_error(self, message):
        """显示错误信息"""
        log(f"显示错误信息: {message}")
        self.errorLabel.setText(message)
        self.errorLabel.setTextColor("#ff0000", QColor(255, 0, 0))  # 红色
        self.errorLabel.show()
        self.yesButton.setEnabled(False)
        self.yesButton.setVisible(False)
        log("错误信息已显示，确认按钮已禁用")
    
    def show_warning(self, message):
        """显示警告信息"""
        log(f"显示警告信息: {message}")
        self.errorLabel.setText(message)
        self.errorLabel.setTextColor("#ff9800", QColor(255, 152, 0))  # 橙色
        self.errorLabel.show()
        self.yesButton.setEnabled(True)
        self.yesButton.setVisible(True)
        # 修改确认按钮文本为"修复已安装的版本"
        self.yesButton.setText(i18nText('修复已安装的版本'))
        log("警告信息已显示，确认按钮已启用并设置为'修复已安装的版本'")
    
    def hide_error(self):
        """隐藏错误信息"""
        log("隐藏错误信息")
        self.errorLabel.hide()
        self.yesButton.setEnabled(True)
        self.yesButton.setVisible(True)
        # 恢复确认按钮文本为"确定"
        self.yesButton.setText(i18nText('确定'))
        log("错误信息已隐藏，确认按钮已启用并恢复为'确定'")
    
    def on_version_name_changed(self, text):
        """版本名输入变化时的处理"""
        log(f"版本名输入发生变化，新文本: '{text}'")
        self.validate_version_name()
    
    def get_version_name(self):
        """获取用户输入的版本名"""
        return self.versionNameInput.text().strip()
    
    def validate(self):
        """重写验证方法，确保版本名有效"""
        return self.validate_version_name()


def setup_tools_ui(self, widget):
    """
    设定 Bloret Launcher 工具界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    """
    try:
        # 获取截图按钮
        ScreenCutButton = widget.findChild(QPushButton, "ScreenCutButton")
        if ScreenCutButton:
            # 保持对截图窗口的引用，防止被垃圾回收
            self.screenshot_widget = None
            def start_screenshot():
                self.screenshot_widget = ScreenShortCut()
            ScreenCutButton.clicked.connect(start_screenshot)
        
        # 获取快捷键设置按钮
        shortcut_set_button = widget.findChild(QPushButton, "ScreenCut_ShortCut_Set")
        if shortcut_set_button:
            shortcut_set_button.clicked.connect(lambda: show_shortcut_setting_dialog(self))
        
        # 获取当前快捷键显示标签
        shortcut_label = widget.findChild(StrongBodyLabel, "ScreenCut_ShortCut")
        if shortcut_label:
            # 加载并显示当前快捷键
            load_and_display_shortcut(shortcut_label)
        
        # 获取玩家UUID查询按钮
        name2uuid_button = widget.findChild(QPushButton, "name2uuid_player_Button")
        name2uuid_input = widget.findChild(LineEdit, "name2uuid_player_uuid")
        name2uuid_result = widget.findChild(StrongBodyLabel, "label_2")
        name2uuid_copy_button = widget.findChild(QPushButton, "pushButton_5")
        
        if name2uuid_button and name2uuid_input and name2uuid_result:
            name2uuid_button.clicked.connect(
                lambda: query_player_uuid(name2uuid_input.text(), name2uuid_result)
            )
        
        if name2uuid_copy_button and name2uuid_result:
            name2uuid_copy_button.clicked.connect(
                lambda: copy_uuid_to_clipboard(name2uuid_result.text())
            )
        
        # 获取玩家名字查询按钮
        search_name_button = widget.findChild(QPushButton, "search_name_button")
        search_name_input = widget.findChild(LineEdit, "search_name_type")
        search_name_result = widget.findChild(StrongBodyLabel, "search_name")
        search_name_copy_button = widget.findChild(QPushButton, "search_name_copy")
        
        if search_name_button and search_name_input and search_name_result:
            search_name_button.clicked.connect(
                lambda: query_player_name(search_name_input.text(), search_name_result)
            )
        
        if search_name_copy_button and search_name_result:
            search_name_copy_button.clicked.connect(
                lambda: copy_name_to_clipboard(search_name_result.text())
            )
        
        # 获取皮肤和披风查询按钮
        skin_search_button = widget.findChild(QPushButton, "skin_search_button")
        skin_uuid_input = widget.findChild(LineEdit, "skin_uuid")
        skin_result_label = widget.findChild(StrongBodyLabel, "search_skin")
        skin_copy_button = widget.findChild(QPushButton, "skin_copy")
        cape_copy_button = widget.findChild(QPushButton, "cape_copy")
        
        if skin_search_button and skin_uuid_input and skin_result_label:
            skin_search_button.clicked.connect(
                lambda: query_player_skin(skin_uuid_input.text(), skin_result_label, widget)
            )
        
        if skin_copy_button:
            skin_copy_button.clicked.connect(
                lambda: copy_skin_to_clipboard(skin_uuid_input.text())
            )
        
        if cape_copy_button:
            cape_copy_button.clicked.connect(
                lambda: copy_cape_to_clipboard(skin_uuid_input.text())
            )
        
    except Exception as e:
        log(f"设置工具UI时出错: {str(e)}", logging.ERROR)


def show_shortcut_setting_dialog(parent):
    """显示快捷键设置对话框"""
    dialog = ShortCutSettingDialog(parent)
    if dialog.exec():
        # 用户点击了确定按钮，保存快捷键
        if dialog.validate() and dialog.save_shortcut():
            # 更新界面上的快捷键显示
            main_window = parent.window() if hasattr(parent, 'window') else parent
            shortcut_label = main_window.findChild(StrongBodyLabel, "ScreenCut_ShortCut")
            if shortcut_label:
                load_and_display_shortcut(shortcut_label)
            
            # 更新全局快捷键
            try:
                old_shortcut = main_window.config.get('screen_cut_shortcut', '')
                new_shortcut = dialog.get_new_shortcut()
                
                # 调用主窗口的更新方法
                if hasattr(main_window, 'update_global_screenshot_hotkey'):
                    main_window.update_global_screenshot_hotkey(old_shortcut, new_shortcut)
                
            except Exception as e:
                log(f"更新全局快捷键失败: {e}", logging.WARNING)
            
            InfoBar.success(
                title=i18nText('✅ 设置成功'),
                content=i18nText('截图快捷键已更新'),
                parent=parent,
                duration=3000
            )
        else:
            InfoBar.error(
                title=i18nText('❌ 设置失败'),
                content=i18nText('保存快捷键时出错，请检查配置文件'),
                parent=parent,
                duration=3000
            )


def load_and_display_shortcut(label):
    """加载并显示当前快捷键"""
    try:
        config_path = "config.json"
        if os.path.exists(BLglobals.config_path):
            with open(BLglobals.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                shortcut = config.get("screen_cut_shortcut", "Ctrl+Alt+A")
                label.setText(shortcut)
    except Exception as e:
        log(f"加载快捷键显示失败: {e}")
        label.setText("Ctrl+Alt+A")  # 默认值

def setup_Mod_ui(self, widget):
    '''
    设定 Bloret Launcher 模组界面 UI 布局和操作。
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    # 绑定 OpenMod 按钮点击事件
    Open_Modrinth_Button = widget.findChild(QPushButton, "Open_Modrinth_Button")
    if Open_Modrinth_Button:
        Open_Modrinth_Button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://modrinth.com/mods")))
    else:
        log(i18nText("未找到 Open_Modrinth_Button 按钮"), logging.ERROR)

    Search = widget.findChild(SearchLineEdit, "Search")
    mod_list = widget.findChild(SmoothScrollArea, "mod_list")
    
    AskBloriko_Edit = widget.findChild(LineEdit, "AskBloriko_Edit")
    AskBloriko_Button = widget.findChild(QPushButton, "AskBloriko_Button")
    
    Bloriko_DeepThink_CheckBox = widget.findChild(CheckBox, "Bloriko_DeepThink_CheckBox") # 获取 CheckBox
    AskBloriko_Button.setIcon(FluentIcon.SEND)
    
    # 这一部分之前的代码可能连接了 AskBlorikoAndSet，现在我们要改用新的弹窗逻辑
    if AskBloriko_Button and AskBloriko_Edit:
        def show_bloriko_mod_dialog():
            question = AskBloriko_Edit.text()
            if not question.strip():
                InfoBar.warning(
                    title=i18nText('请输入需求'),
                    content=i18nText('请告诉 Bloriko 您想要什么样的 Mod'),
                    parent=self
                )
                return
                
            # 获取深度思考状态
            is_deepthink = Bloriko_DeepThink_CheckBox.isChecked() if Bloriko_DeepThink_CheckBox else False
            
            # 弹出自定义对话框，传入 deepthink 参数
            dialog = BlorikoModRecommendationDialog(self, question, deepthink=is_deepthink)
            dialog.exec_()

        # 断开旧的连接（如果有）并连接新函数
        try:
            AskBloriko_Button.clicked.disconnect()
        except:
            pass
        AskBloriko_Button.clicked.connect(show_bloriko_mod_dialog)

    if Search:
        # on_search_mod_clicked(mod_list)
        # 获取进度条控件实例
        loading_widget = widget.findChild(IndeterminateProgressBar, "loading")
        Search.searchSignal.connect(lambda: start_search_mod(self, mod_list, Search.text(), loading_widget))
    else:
        log(i18nText("未找到 Search 搜索框"), logging.ERROR)

class BlorikoAIModThread(QThread):
    """用于请求 Bloriko AI 的线程"""
    finished = pyqtSignal(bool, str, list)  # success, text_response, slug_list

    def __init__(self, question, version, config_data, deepthink=False):
        super().__init__()
        self.question = question
        self.version = version
        self.config_data = config_data
        self.deepthink = deepthink

    def run(self):
        
        # 构建 Prompt，强制 AI 返回 JSON 格式的 slug，并指定只推荐 Fabric 模组
        prompt = (
            f"User is playing Minecraft version {self.version} using the FABRIC loader. "
            f"User Request: {self.question}. "
            f"Please recommend some suitable Modrinth mods that are compatible with FABRIC. "
            f"Describe why you chose them briefly. "
            f"\n\nEXTREMELY IMPORTANT: At the very end of your response, you MUST provide a JSON block containing ONLY a list of the Modrinth slugs (project IDs) for these mods. "
            f"Format strictly like this:\n```json\n[\"slug-1\", \"slug-2\", \"slug-3\"]\n```"
        )
        
        try:
            # 调用 Bloriko.py 中的 AskBloriko
            # 注意：AskBloriko 需要 config 字典
            response_text = AskBloriko(prompt, self.config_data, deepthink=self.deepthink)
            
            # 解析 JSON
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response_text, re.DOTALL)
            slugs = []
            clean_text = response_text
            
            if json_match:
                json_str = json_match.group(1)
                try:
                    slugs = json.loads(json_str)
                    # 从展示文本中移除 JSON 块，让界面更干净
                    clean_text = response_text.replace(json_match.group(0), "").strip()
                except json.JSONDecodeError:
                    log("Bloriko AI 返回的 JSON 格式错误", logging.ERROR)
            
            self.finished.emit(True, clean_text, slugs)
            
        except Exception as e:
            log(f"Bloriko AI 请求失败: {e}", logging.ERROR)
            self.finished.emit(False, str(e), [])


class BlorikoModRecommendationDialog(MessageBoxBase):
    """ Bloriko Mod 推荐与安装对话框 """

    def __init__(self, parent_window, question, deepthink=False):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.question = question
        self.deepthink = deepthink # 存储 deepthink 状态
        self.slugs = [] # 存储 AI 推荐的 slug
        self.minecraft_dir = cfg.read().get('minecraft_dir', os.path.join(BLglobals.datapath, '.minecraft'))
        self.version_mappings = {} # 存储版本映射信息
        
        # --- UI 初始化 ---
        self.titleLabel = SubtitleLabel(i18nText('让 Bloriko 挑选 Mod'), self.widget)
        self.viewLayout.addWidget(self.titleLabel)

        # 1. 版本选择区域
        self.selectionWidget = QWidget()
        self.selectionLayout = QVBoxLayout(self.selectionWidget)
        self.selectionLayout.setContentsMargins(0, 0, 0, 0)
        
        self.verLabel = BodyLabel(i18nText("请选择您要安装 Mod 的游戏版本 (仅显示 Fabric)："))
        self.versionCombo = ComboBox()
        self.load_versions()
        
        self.selectionLayout.addWidget(self.verLabel)
        self.selectionLayout.addWidget(self.versionCombo)
        self.viewLayout.addWidget(self.selectionWidget)

        # 2. 加载区域
        self.loadingWidget = QWidget()
        self.loadingLayout = QVBoxLayout(self.loadingWidget)
        self.loadingBar = IndeterminateProgressBar()
        self.loadingLabel = CaptionLabel(i18nText("Bloriko 正在思考并搜索 Modrinth..."))
        self.loadingLabel.setAlignment(Qt.AlignCenter)
        self.loadingLayout.addWidget(self.loadingBar)
        self.loadingLayout.addWidget(self.loadingLabel)
        self.viewLayout.addWidget(self.loadingWidget)
        self.loadingWidget.hide()

        # 3. 结果区域 (整体滚动)
        self.resultScroll = SmoothScrollArea()
        self.resultScroll.setWidgetResizable(True)
        self.resultScroll.setStyleSheet("background-color: transparent; border: none;") 
        
        self.resultContentWidget = QWidget()
        self.resultLayout = QVBoxLayout(self.resultContentWidget)
        self.resultLayout.setContentsMargins(10, 0, 20, 0)
        
        self.aiResponseBrowser = BodyLabel()
        self.aiResponseBrowser.setWordWrap(True)
        self.aiResponseBrowser.setTextFormat(Qt.MarkdownText)
        self.aiResponseBrowser.setOpenExternalLinks(True)
        
        self.modListLabel = StrongBodyLabel(i18nText("推荐的 Mod (已自动勾选):"))
        self.modListContainer = QWidget()
        self.modListLayout = QVBoxLayout(self.modListContainer)
        self.modListLayout.setContentsMargins(0, 0, 0, 0)
        self.modListLayout.setSpacing(5)
        
        self.resultLayout.addWidget(self.aiResponseBrowser)
        self.resultLayout.addSpacing(10)
        self.resultLayout.addWidget(self.modListLabel)
        self.resultLayout.addWidget(self.modListContainer)
        self.resultLayout.addStretch(1)

        self.resultScroll.setWidget(self.resultContentWidget)
        self.viewLayout.addWidget(self.resultScroll)
        self.resultScroll.hide()

        # 设置按钮
        self.yesButton.setText(i18nText("开始询问"))
        self.cancelButton.setText(i18nText("取消"))
        
        self.yesButton.clicked.disconnect() 
        self.yesButton.clicked.connect(self.on_action_clicked)
        
        self.widget.setMinimumWidth(500)
        self.widget.setMinimumHeight(400) 
        self.current_state = "SELECT" # SELECT -> LOADING -> RESULT

    def load_versions(self):
        """加载已安装的版本，通过 .BL.json 筛选 Fabric 版本"""
        versions_path = os.path.join(self.minecraft_dir, "versions")
        bl_json_path = os.path.join(versions_path, ".BL.json")
        
        # 1. 尝试读取版本元数据
        try:
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    bl_data = json.load(f)
                    if "versions" in bl_data:
                        self.version_mappings = bl_data["versions"]
        except Exception as e:
            log(f"读取 .BL.json 失败: {str(e)}", logging.WARNING)

        fabric_versions = []
        if os.path.exists(versions_path):
            all_folders = [d for d in os.listdir(versions_path) if os.path.isdir(os.path.join(versions_path, d))]
            
            for folder in all_folders:
                is_fabric = False
                # 检查元数据
                if folder in self.version_mappings:
                    if self.version_mappings[folder].get("Fabric", False):
                        is_fabric = True
                # 后备检查：如果文件夹名包含 fabric（即使在 .BL.json 中存在记录也需要检查）
                if not is_fabric and "fabric" in folder.lower():
                    is_fabric = True
                
                if is_fabric:
                    fabric_versions.append(folder)
        
        if fabric_versions:
            self.versionCombo.addItems(fabric_versions)
            self.yesButton.setEnabled(True)
        else:
            self.versionCombo.addItem(i18nText("未找到 Fabric 版本"))
            self.versionCombo.setEnabled(False) # 禁用，防止误操作
            self.yesButton.setEnabled(False)

    def on_action_clicked(self):
        if self.current_state == "SELECT":
            self.start_ai_inquiry()
        elif self.current_state == "RESULT":
            self.install_selected_mods()

    def start_ai_inquiry(self):
        """开始请求 AI"""
        folder_name = self.versionCombo.currentText()
        if not folder_name or folder_name == i18nText("未找到 Fabric 版本"):
            InfoBar.error(title="错误", content="请先选择一个有效的 Fabric 游戏版本", parent=self.widget)
            return

        # 尝试获取真实的纯数字版本号传给 AI (例如 1.20.1 而不是 1.20.1-Fabric)
        actual_version = folder_name
        if folder_name in self.version_mappings:
            actual_version = self.version_mappings[folder_name].get("version", folder_name)

        # 切换 UI 到加载状态
        self.current_state = "LOADING"
        self.selectionWidget.hide()
        self.loadingWidget.show()
        self.resultScroll.hide() 
        self.yesButton.setEnabled(False)
        self.yesButton.setText(i18nText("正在思考..."))

        # 启动线程
        config = cfg.read()
        # 传入解析后的真实版本号
        self.thread = BlorikoAIModThread(self.question, actual_version, config, deepthink=self.deepthink)
        self.thread.finished.connect(self.on_ai_finished)
        self.thread.start()

    def on_ai_finished(self, success, response_text, slugs):
        self.loadingWidget.hide()
        
        if not success:
            self.selectionWidget.show()
            self.yesButton.setEnabled(True)
            self.yesButton.setText(i18nText("重试"))
            self.current_state = "SELECT"
            InfoBar.error(title="请求失败", content=response_text, parent=self.widget)
            return

        self.current_state = "RESULT"
        self.resultScroll.show()
        self.yesButton.setEnabled(True)
        self.yesButton.setText(i18nText("一键安装全部"))
        
        self.aiResponseBrowser.setText(response_text)
        self.slugs = slugs
        
        # 清空旧列表
        while self.modListLayout.count():
            item = self.modListLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not slugs:
            self.modListLayout.addWidget(BodyLabel(i18nText("未能识别出具体的 Mod，请参考上方文字手动搜索。")))
            self.yesButton.setEnabled(False)
        else:
            for slug in slugs:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                
                chk = CheckBox()
                chk.setChecked(True)
                chk.setText(slug) 
                chk.setProperty("slug", slug) 
                
                row_layout.addWidget(chk)
                self.modListLayout.addWidget(row)

    def install_selected_mods(self):
        """下载并安装选中的 Mod"""
        
        selected_slugs = []
        for i in range(self.modListLayout.count()):
            item = self.modListLayout.itemAt(i)
            if item and item.widget():
                chk = item.widget().findChild(CheckBox)
                if chk and chk.isChecked():
                    selected_slugs.append(chk.property("slug"))
        
        if not selected_slugs:
            InfoBar.warning(title="提示", content="未选择任何 Mod", parent=self.widget)
            return

        folder_name = self.versionCombo.currentText()
        
        actual_version = folder_name
        
        # 1. 优先尝试从 .BL.json 映射中获取 version 字段
        if folder_name in self.version_mappings:
            actual_version = self.version_mappings[folder_name].get("version", folder_name)
            log(f"BlorikoMod: 从 .BL.json 获取到真实版本号: {actual_version}")
        else:
            # 2. 如果映射失败 (例如文件夹存在但不在 JSON 中)，使用正则提取纯数字版本号
            # 匹配类似 1.21.8, 1.20.1 等开头的字符串
            match = re.match(r"^(\d+\.\d+(\.\d+)?)", folder_name)
            if match:
                extracted_ver = match.group(1)
                log(f"BlorikoMod: 映射查找失败，从 '{folder_name}' 提取版本号为 '{extracted_ver}'")
                actual_version = extracted_ver
            else:
                log(f"BlorikoMod: 警告 - 无法确定 '{folder_name}' 的真实版本号，将直接使用文件夹名", logging.WARNING)

        self.yesButton.setEnabled(False)
        self.yesButton.setText(i18nText("正在安装..."))
        
        self.download_thread = ModBatchDownloadThread(selected_slugs, folder_name, self.minecraft_dir, actual_version)
        
        self.download_thread.progress_signal.connect(self.update_download_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def update_download_progress(self, msg, is_error):
        """ 更新下载进度显示 """
        if is_error:
            log(msg, logging.ERROR)
        else:
            self.yesButton.setText(msg)

    def on_download_finished(self, success_count, fail_count):
        """ 下载完成后的处理 """
        self.accept() # 关闭弹窗
        title = i18nText('安装完成')
        content = i18nText(f"成功安装 {success_count} 个 Mod，失败 {fail_count} 个。")
        if fail_count > 0:
            InfoBar.warning(title=title, content=content, parent=self.parent_window, duration=5000)
        else:
            InfoBar.success(title=title, content=content, parent=self.parent_window, duration=5000)

class ModBatchDownloadThread(QThread):
    """ 批量下载 Mod 的线程 """
    progress_signal = pyqtSignal(str, bool) # message, is_error
    finished_signal = pyqtSignal(int, int) # success_count, fail_count

    def __init__(self, slugs, version_folder, minecraft_dir, game_version):
        super().__init__()
        self.slugs = slugs
        self.version_folder = version_folder
        self.minecraft_dir = minecraft_dir
        self.game_version = game_version # 存储真实的游戏版本号 (如 1.20.1)

    def run(self):
        success = 0
        fail = 0
        total = len(self.slugs)
        
        mod_dir = os.path.join(self.minecraft_dir, "versions", self.version_folder, "mods")
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)

        for i, slug in enumerate(self.slugs):
            self.progress_signal.emit(f"正在安装 ({i+1}/{total}): {slug}", False)
            
            try:
                # 明确指定 loader 为 fabric，并指定游戏版本
                url = Get_Mod_File_Download_Url(slug, loaders="fabric", game_versions=self.game_version) 
                
                # 如果指定版本没有找到，url 会是 None，这里不再尝试 Forge，因为不兼容
                if url:
                    filename = url.split("/")[-1]
                    file_path = os.path.join(mod_dir, filename)
                    
                    # 记录详细日志以便调试
                    log(f"开始下载 Mod: {slug} -> {file_path} (URL: {url})")

                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    success += 1
                else:
                    log(f"无法获取 Mod 下载链接: {slug} (Fabric, {self.game_version})", logging.ERROR)
                    fail += 1
            except Exception as e:
                log(f"下载 Mod 失败 {slug}: {e}", logging.ERROR)
                fail += 1
                
        self.finished_signal.emit(success, fail)
