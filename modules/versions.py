'''
Versions.py
## Bloret Launcher 版本操作模块

### 模块功能：
 - [x] 删除 Minecraft 版本
 - [x] 修改 Minecraft 版本名称
 - [x] 删除自定义选项
 - [x] 修改自定义选项名称

***
###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
'''
import logging
import os
import sys
import json
import platform
import requests
import shutil
import subprocess
import concurrent.futures
import modules.globals as BLglobals
import threading
import time
import zipfile
import base64
import struct
import io
import gzip
import sys
from pathlib import Path

# 第三方库
# sip is not required for PySide6
try:
    import send2trash
except ImportError:
    send2trash = None
    print("[Warning] send2trash not found. Soft deletion to recycle bin will be unavailable.")
from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QUrl, QMetaObject
from PySide6.QtGui import QPixmap, QDesktopServices, QColor, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QFileDialog, QLabel,
    QSizePolicy, QGridLayout, QProgressBar, QCheckBox, QLineEdit, QPushButton, QDialog # 新增 QDialog
)
from PySide6.QtUiTools import QUiLoader
from modules.compat_widgets import (
    InfoBar, InfoBarPosition, ComboBox, StrongBodyLabel,
    BodyLabel, SubtitleLabel, MessageBoxBase, LineEdit,
    PushButton, SwitchButton, CaptionLabel, Pivot,
    SegmentedWidget, CardWidget, IconWidget, FluentIcon,
    PrimaryPushButton, ToolButton, ImageLabel
)

# 自定义模块
from modules.win11toast import notify, update_progress
from modules.safe import handle_exception
from modules.log import log
from modules.customize import find_Customize
from modules.i18n import i18nText
from modules.paths import app_path
import modules.globals as BLglobals
import modules.config as cfg

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
        # 如果是相对路径，需要转换为绝对路径
        if not os.path.isabs(ui_file_path):
            ui_file_path = app_path(ui_file_path)

        if not os.path.exists(ui_file_path):
            log(f"UI 文件不存在: {ui_file_path}", logging.WARNING)
            return None
        
        with open(ui_file_path, 'r', encoding='utf-8') as f:
            ui = loader.load(f, None)
        return ui
    except Exception as e:
        log(f"加载 UI 文件失败 {ui_file_path}: {e}", logging.ERROR)
        return None

def _gitcode_base_url(version=None):
    v = version or BLglobals.current_minecraft_version
    if not v:
        return None
    return f"https://raw.gitcode.com/Bloret/{v}/raw/main"

# Mirror helpers: single source of truth in modules.download
from modules.download.mirrors import (  # noqa: E402
    dl_source_launcher_or_meta_get,
    dl_source_library_get,
    dl_source_assets_get,
)

# 初始化全局变量
set_list = []
minecraft_list = []

def open_minecraft_version_folder(self,version,MINECRAFT_DIR):
    '''

    打开指定的 Minecraft 版本文件夹
     version 要删除的版本名称
     versions 版本 ComboBox 控件
     MINECRAFT_DIR Minecraft 安装目录

    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log(f"正在打开 Minecraft 版本文件夹：{version}")
    
    # 构建版本文件夹路径
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    
    try:
        # 检查版本文件夹是否存在
        if os.path.exists(version_path) and os.path.isdir(version_path):
            # 使用默认文件管理器打开文件夹
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(version_path)))
            log(f"成功打开版本文件夹：{version_path}")
        else:
            log(f"版本文件夹不存在：{version_path}", logging.ERROR)
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=f"版本 {version} 的文件夹不存在",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"打开版本文件夹时发生错误: {Exception}", logging.ERROR)
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"打开版本 {version} 文件夹时发生错误: {str(Exception)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def delete_minecraft_version(self,version,label,card,MINECRAFT_DIR,homeInterface):
    '''

    删除指定的 Minecraft 版本文件夹
     version 要删除的版本名称
     label 版本控件
     MINECRAFT_DIR Minecraft 安装目录

    ### 删除 `.minecraft/version/{version}` 文件夹
     并移到回收站

    
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log(f"正在删除 Minecraft 版本：{version}")
    
    # 构建版本文件夹路径
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    
    try:
        # 检查版本文件夹是否存在
        if os.path.exists(version_path) and os.path.isdir(version_path):
            # 删除版本文件夹
            if send2trash:
                send2trash.send2trash(version_path)
            else:
                import shutil
                if os.path.isdir(version_path):
                    shutil.rmtree(version_path)
                else:
                    os.remove(version_path)
            log(f"成功删除版本文件夹：{version_path}")
            
            # 更新全局列表
            global set_list, minecraft_list
            if version in set_list:
                set_list.remove(version)
            if version in minecraft_list:
                minecraft_list.remove(version)
            
            log(f"正在更新 UI 中的版本名称：del {label.text()}")
            # 从父布局中移除 label 控件并删除
            parent_layout = label.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(label)
            label.deleteLater()
            log(f"正在更新 UI 中的版本卡片：del {card}")
            # 从父布局中移除 card 控件并删除
            parent_layout = card.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(card)
            card.deleteLater()
            
            InfoBar.success(
                title=f'✅ 版本 {version} 已成功删除',
                content=i18nText("如需找回，可前往系统回收站找回。"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            log(f"版本文件夹不存在：{version_path}", logging.ERROR)
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=f"版本 {version} 的文件夹不存在",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"删除版本时发生错误: {Exception}", logging.ERROR)
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"删除版本 {version} 时发生错误: {str(Exception)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def Change_minecraft_version_name(self,version,label,MINECRAFT_DIR,homeInterface):
    '''
    ### 将 `.minecraft/version` 文件夹下 `{version}` 文件夹名称换成想要的文件名称并重读刷新。
     version 要修改的版本名称
     label 版本控件
     MINECRAFT_DIR Minecraft 安装目录

    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log(f"正在修改 Minecraft 版本名称：{version}")
    # 获取新的版本名称
    dialog = self.MessageBox(i18nText("请输入新的名称"), f"（当前名称：{version}）", self)
    if not dialog.exec():
        return  # 用户取消操作

    new_name = dialog.name_edit.text().strip()
    if not new_name:
        InfoBar.warning(
            title=i18nText('⚠️ 提示'),
            content=i18nText("新名称不能为空"),
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    if version == new_name:
        InfoBar.info(
            title=i18nText('ℹ️ 提示'),
            content=i18nText("新名称与原名称相同，无需更改"),
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    # 构建路径
    old_path = os.path.join(MINECRAFT_DIR, "versions", version)
    new_path = os.path.join(MINECRAFT_DIR, "versions", new_name)

    # 检查目标是否存在
    if os.path.exists(new_path):
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"目标名称 {new_name} 已存在，请选择其他名称。",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    # 更新全局列表
    global set_list, minecraft_list

    if version in set_list:
        set_list[set_list.index(version)] = new_name
    if version in minecraft_list:
        minecraft_list[minecraft_list.index(version)] = new_name

    try:
        # 重命名文件夹
        os.rename(old_path, new_path)
        log(f"成功将版本文件夹从 {old_path} 重命名为 {new_path}")

        log(f"正在更新 UI 中的版本名称：{label.text()} -> {new_name}")
        # 修改 label 的 StrongBodyLabel 的文字为 new_name
        label.setText(new_name)
        
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"重命名版本时发生错误: {Exception}", logging.ERROR)
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"重命名版本 {version} 时发生错误: {str(Exception)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def delete_Customize(self,version,label,card,customize_list,homeInterface):
    '''
    ### 删除自定义选项
    将 配置文件中 `{version}` 对应的项目删除。
     version 要删除的自定义选项名称
     customize_list 自定义选项列表
    
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log(f"正在删除自定义选项：{version}")
    try:
        isOK,item=find_Customize(self,version)
        if isOK:
            with open(BLglobals.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            if item in config_data["Customize"]:
                config_data["Customize"].remove(item)
            cfg.write(config_data)
            self.config = config_data
            InfoBar.success(
                title=i18nText('✅ 成功'),
                content=f"{version} 已成功删除",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            customize_list.remove(version)

            log(f"正在更新 UI 中的版本名称：del {label.text()}")
            # 从父布局中移除 label 控件并删除
            parent_layout = label.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(label)
            label.deleteLater()

            log(f"正在更新 UI 中的版本卡片：del {card}")
            # 从父布局中移除 card 控件并删除
            parent_layout = card.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(card)
            card.deleteLater()

            self.run_cmcl_list(True)
        else:
            InfoBar.error(
                title=i18nText('❌ 删除失败'),
                content=f"未找到与 {version} 匹配的自定义程序",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"保存到 config.json 时发生错误: {Exception}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def Change_Customize_name(self,version,label,homeInterface):
    '''
    ### 将配置文件中 `{version}` 项目换成想要的名称并刷新重读。

    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log(f"正在修改自定义选项名称：{version}")
    isOK,item=find_Customize(self,version)
    if isOK:
        with open(BLglobals.config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)

        if "Customize" not in config_data:
            config_data["Customize"] = []
        dialog = self.MessageBox(i18nText("请输入新的名称"), f"（当前名称：{version}）", self)
        if not dialog.exec():
            return  # 用户取消操作
        new_name = dialog.name_edit.text().strip()
        if not new_name or new_name.strip() == "":
            InfoBar.warning(
                title=i18nText('⚠️ 提示'),
                content=i18nText("新名称不能为空"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        if version == new_name:
            InfoBar.info(
                title=i18nText('ℹ️ 提示'),
                content=i18nText("新名称与原名称相同，无需更改"),
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        isOK, item = find_Customize(self, version)
        if isOK:
            with open(BLglobals.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            # 更新或添加自定义项
            is_found = False
            for i, custom_item in enumerate(config_data["Customize"]):
                if custom_item["showname"] == version:
                    custom_item["showname"] = new_name
                    is_found = True
                    break
            if not is_found:
                handle_exception(ValueError(i18nText("尝试修改的项目不存在于自定义列表中")))
                InfoBar.error(
                    title=i18nText('❌ 错误'),
                    content=f"尝试修改的项目 {item} 不存在于自定义列表中",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return
            cfg.write(config_data)
            self.config = config_data
            InfoBar.success(
                title=f'✅ 成功',
                content=f"版本名称已从 {version} 更改为 {new_name}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        log(f"正在更新 UI 中的版本名称：{label.text()} -> {new_name}")
        # 修改 label 的 StrongBodyLabel 的文字为 new_name
        label.setText(new_name)
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    else:
        InfoBar.error(
            title=i18nText('❌ 修改失败'),
            content=f"未找到与 {version} 匹配的自定义程序",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )


# ---------------------------------------------------------------------------
# Legacy install path removed. Prefer modules.install / modules.download.
# Thin re-exports keep accidental imports working.
# ---------------------------------------------------------------------------
from modules.install import (  # noqa: E402
    LibraryDownloader,
    InstallMinecraftVersion,
    download_file,
    secure_download,
)


def toggle_pause_download(download_dialog):
    """Deprecated Qt-dialog pause helper; route to install global pause when possible."""
    try:
        from modules.install import toggle_current_download_pause
        toggle_current_download_pause()
        return
    except Exception:
        pass
    if hasattr(download_dialog, "downloader") and download_dialog.downloader is not None:
        downloader = download_dialog.downloader
        if getattr(downloader, "is_paused", False):
            downloader.resume()
            if hasattr(download_dialog, "pause_button"):
                try:
                    download_dialog.pause_button.setText("暂停")
                except Exception:
                    pass
        else:
            downloader.pause()
            if hasattr(download_dialog, "pause_button"):
                try:
                    download_dialog.pause_button.setText("恢复下载")
                except Exception:
                    pass


def update_version_combo_by_category(self, version_combo, category):
    """
    根据分类更新版本选择框的内容
    
    Args:
        version_combo: 版本选择框控件
        category: 分类名称
    """
    # 清空版本选择框中的所有项目
    version_combo.clear()
    
    # 根据分类加载对应版本列表
    if category == i18nText("百络谷支持版本"):
        # 检查是否已经缓存了百络谷支持版本列表
        if hasattr(self, 'ver_id_bloret') and self.ver_id_bloret:
            # 使用缓存的版本列表填充选择框
            version_combo.addItems(self.ver_id_bloret)
        else:
            # 如果没有缓存，使用默认的测试版本
            version_combo.addItems(["1.21.7", "1.21.8"])
    elif category == i18nText("正式版本"):
        # 检查是否已经缓存了正式版本列表
        if hasattr(self, 'ver_id_main') and self.ver_id_main:
            # 使用缓存的版本列表填充选择框
            version_combo.addItems(self.ver_id_main)
        else:
            # 从网络获取版本列表
            try:
                # 发送HTTP GET请求获取Minecraft版本清单
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                # 检查HTTP响应是否成功（会抛出异常处理非2xx状态码）
                response.raise_for_status()
                # 解析JSON响应数据
                version_data = response.json()
                # 提取版本列表数据
                versions = version_data["versions"]
                # 创建临时列表存储正式版本ID
                ver_id_main_temp = []
                # 遍历所有版本
                for version in versions:
                    # 过滤掉快照版本和远古版本，只保留正式版本
                    if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                        # 将版本ID添加到列表
                        ver_id_main_temp.append(version["id"])
                # 将正式版本列表添加到选择框
                version_combo.addItems(ver_id_main_temp)
            except Exception as e:
                # 如果获取失败，记录ERROR级别日志并使用默认版本
                log(f"获取正式版本列表失败: {e}")
                # 添加默认的正式版本
                version_combo.addItems(["1.21.8", "1.21.7"])
    elif category == i18nText("快照版本"):
        # 检查是否已经缓存了快照版本列表
        if hasattr(self, 'ver_id_short') and self.ver_id_short:
            # 使用缓存的版本列表填充选择框
            version_combo.addItems(self.ver_id_short)
        else:
            # 从网络获取版本列表
            try:
                # 发送HTTP GET请求获取Minecraft版本清单
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                # 检查HTTP响应是否成功（会抛出异常处理非2xx状态码）
                response.raise_for_status()
                # 解析JSON响应数据
                version_data = response.json()
                # 提取版本列表数据
                versions = version_data["versions"]
                # 创建临时列表存储快照版本ID
                ver_id_short_temp = []
                # 遍历所有版本
                for version in versions:
                    # 只保留快照版本
                    if version["type"] == "snapshot":
                        # 将版本ID添加到列表
                        ver_id_short_temp.append(version["id"])
                # 将快照版本列表添加到选择框
                version_combo.addItems(ver_id_short_temp)
            except Exception as e:
                # 如果获取失败，记录ERROR级别日志并使用默认版本
                log(f"获取快照版本列表失败: {e}")
                # 添加默认的快照版本
                version_combo.addItems(["24w14a", "24w13a"])
    elif category == i18nText("远古版本"):
        # 检查是否已经缓存了远古版本列表
        if hasattr(self, 'ver_id_long') and self.ver_id_long:
            # 使用缓存的版本列表填充选择框
            version_combo.addItems(self.ver_id_long)
        else:
            # 从网络获取版本列表
            try:
                # 发送HTTP GET请求获取Minecraft版本清单
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                # 检查HTTP响应是否成功（会抛出异常处理非2xx状态码）
                response.raise_for_status()
                # 解析JSON响应数据
                version_data = response.json()
                # 提取版本列表数据
                versions = version_data["versions"]
                # 创建临时列表存储远古版本ID
                ver_id_long_temp = []
                # 遍历所有版本
                for version in versions:
                    # 只保留远古版本（alpha和beta版本）
                    if version["type"] in ["old_alpha", "old_beta"]:
                        # 将版本ID添加到列表
                        ver_id_long_temp.append(version["id"])
                # 将远古版本列表添加到选择框
                version_combo.addItems(ver_id_long_temp)
            except Exception as e:
                # 如果获取失败，记录ERROR级别日志并使用默认版本
                log(f"获取远古版本列表失败: {e}")
                # 添加默认的远古版本
                version_combo.addItems(["b1.7.3", "b1.7.2"])


def on_other_version_selected(self, selected_text, combo_box):
    """
    当用户在版本选择框中选择"其他版本..."时触发
    
    Args:
        selected_text: 用户选择的文本
        combo_box: 触发事件的ComboBox控件
        version_type: 版本类型 ("Minecraft" 或 "Fabric")
    """
    # 记录函数调用日志，包含选择的文本和当前选择框内容
    log(f"[versions][on_other_version_selected] start with : {selected_text}, {combo_box.currentText()}")
    # 检查是否选择了"其他版本..."
    if selected_text == i18nText("其他版本..."):
        # 记录用户选择其他版本的日志
        log("[versions][on_other_version_selected] 用户选择了其他版本...")
        # 创建自定义对话框
        dialog = MessageBoxBase(self)
        # 设置对话框窗口标题
        dialog.setWindowTitle(i18nText("其他版本..."))
        
        # 创建标题标签
        title_label = SubtitleLabel(i18nText("其他版本..."))
        # 创建副标题标签，显示版本选择提示信息
        subtitle_label = BodyLabel(i18nText("在这里可以选择下载 Minecraft 的其他版本。\n请注意，这些版本可能不受百络谷支持，可能无法正常进入 Bloret 服务器。\n部分比较老的或快照版本可能不受 Fabric Loader 支持。"))
        
        # 创建分类选择框标签
        category_label = StrongBodyLabel(i18nText("版本分类"))
        # 创建分类选择框
        category_combo = ComboBox()
        # 添加版本分类选项
        category_combo.addItems([
            i18nText("百络谷支持版本"),  # 百络谷支持的版本
            i18nText("正式版本"),     # 官方正式版本
            i18nText("快照版本"),     # 开发快照版本
            i18nText("远古版本")      # 早期alpha/beta版本
        ])
        # 设置默认选择为百络谷支持版本
        category_combo.setCurrentText(i18nText("百络谷支持版本"))
        
        # 创建版本选择框标签
        version_label = StrongBodyLabel(i18nText("具体版本"))
        # 创建版本选择框
        version_combo = ComboBox()
        
        # 初始化版本选择框，默认加载百络谷支持版本
        update_version_combo_by_category(self, version_combo, i18nText("百络谷支持版本"))
        
        # 定义分类改变时的处理函数
        def on_category_changed(category):
            # 禁用两个选择框，防止用户在加载过程中操作
            category_combo.setEnabled(False)
            version_combo.setEnabled(False)
            
            # 显示加载提示信息
            from modules.compat_widgets import InfoBar, InfoBarPosition
            from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal
            InfoBar.info(
                title=i18nText('正在加载'),  # 提示标题
                content=i18nText(f'正在加载 {category} 版本列表'),  # 提示内容
                orient=Qt.Horizontal,  # 水平布局
                isClosable=True,  # 可以关闭
                position=InfoBarPosition.TOP,  # 显示在顶部
                duration=2000,  # 显示2秒
                parent=dialog  # 父控件是对话框
            )
            
            # 定义加载版本列表的后台线程类
            class LoadVersionThread(QThread):
                # 定义完成信号
                finished = pyqtSignal()
                
                # 初始化线程，传入主窗口、版本选择框和分类
                def __init__(self, main_window, version_combo, category):
                    super().__init__()
                    self.main_window = main_window  # 主窗口引用
                    self.version_combo = version_combo  # 版本选择框
                    self.category = category  # 版本分类
                
                # 线程运行函数
                def run(self):
                    # 调用更新版本选择框函数加载对应分类的版本
                    update_version_combo_by_category(self.main_window, self.version_combo, self.category)
                    # 发送完成信号
                    self.finished.emit()
            
            # 创建并启动加载线程
            load_thread = LoadVersionThread(self, version_combo, category)
            
            # 定义线程完成后的处理函数
            def on_load_finished():
                # 重新启用两个选择框
                category_combo.setEnabled(True)
                version_combo.setEnabled(True)
                # 关闭线程
                load_thread.quit()
                load_thread.wait()
            
            # 连接线程完成信号到处理函数
            load_thread.finished.connect(on_load_finished)
            # 启动线程
            load_thread.start()
        
        # 连接分类选择框的改变信号到处理函数
        category_combo.currentTextChanged.connect(on_category_changed)
        
        # 添加控件到对话框布局
        dialog.viewLayout.addWidget(title_label)  # 添加标题标签
        dialog.viewLayout.addWidget(subtitle_label)  # 添加副标题标签
        dialog.viewLayout.addWidget(category_label)  # 添加分类标签
        dialog.viewLayout.addWidget(category_combo)  # 添加分类选择框
        dialog.viewLayout.addWidget(version_label)  # 添加版本标签
        dialog.viewLayout.addWidget(version_combo)  # 添加版本选择框
        
        # 隐藏取消按钮（注释掉了，实际显示取消按钮）
        # dialog.cancelButton.hide()
        
        # 定义确认按钮点击事件处理函数
        def handle_confirm():
            # 获取用户选择的版本
            selected_version = version_combo.currentText()
            # 检查是否选择了版本
            if selected_version:
                # 获取选择框中所有现有项目
                existing_items = [combo_box.itemText(i) for i in range(combo_box.count())]
                # 移除"其他版本..."选项以避免重复
                if i18nText("其他版本...") in existing_items:
                    existing_items.remove(i18nText("其他版本..."))
                    
                # 如果选择的版本不存在于现有列表中，则添加
                if selected_version not in existing_items:
                    # 在"其他版本..."之前插入新项目（count() - 1表示倒数第二个位置）
                    combo_box.insertItem(combo_box.count() - 1, selected_version)
                # 设置选择框当前选择为用户选择的版本
                combo_box.setCurrentText(selected_version)
            # 接受对话框（关闭对话框）
            dialog.accept()
        
        # 连接确认按钮的点击信号到处理函数
        dialog.yesButton.clicked.connect(handle_confirm)
        
        # 显示对话框（模态对话框，会阻塞直到用户操作）
        dialog.exec_()

class BaseInfoPage(QWidget):
    """ 基本信息页面 """
    def __init__(self, version_name, minecraft_dir, parent=None):
        super().__init__(parent)
        self.version_name = version_name
        self.minecraft_dir = minecraft_dir
        self.icon_path = "" # 存储当前图标路径

        self.vLayout = QVBoxLayout(self)
        self.vLayout.setSpacing(20)
        
        # 1. 核心名称
        self.name_layout = QVBoxLayout()
        self.name_layout.setSpacing(5)
        self.name_layout.addWidget(StrongBodyLabel(i18nText("核心名称 (文件夹名)"), self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(i18nText("修改此项将重命名版本文件夹"))
        self.name_layout.addWidget(self.name_edit)
        self.vLayout.addLayout(self.name_layout)

        # 2. 图标设置
        self.icon_group_layout = QVBoxLayout()
        self.icon_group_layout.setSpacing(10)
        self.icon_group_layout.addWidget(StrongBodyLabel(i18nText("图标"), self))
        
        self.icon_content_layout = QHBoxLayout()
        
        # 图标预览
        self.icon_preview = QLabel(self)
        self.icon_preview.setFixedSize(50, 50)
        self.icon_preview.setScaledContents(True)
        self.icon_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #e0e0e0;")
        
        # 选择按钮
        self.icon_btn_layout = QVBoxLayout()
        self.change_icon_btn = PushButton(i18nText("选择其他图标"), self)
        self.change_icon_btn.setIcon(FluentIcon.EDIT)
        self.change_icon_btn.clicked.connect(self.browse_icon)
        
        self.icon_path_label = CaptionLabel(i18nText("使用默认图标"), self)
        self.icon_path_label.setTextColor("#606060", "#a0a0a0")
        
        self.icon_btn_layout.addWidget(self.change_icon_btn)
        self.icon_btn_layout.addWidget(self.icon_path_label)
        self.icon_btn_layout.addStretch(1)

        self.icon_content_layout.addWidget(self.icon_preview)
        self.icon_content_layout.addLayout(self.icon_btn_layout)
        self.icon_content_layout.addStretch(1)
        
        self.icon_group_layout.addLayout(self.icon_content_layout)
        self.vLayout.addLayout(self.icon_group_layout)

        # 3. 快捷操作 (文件夹打开)
        self.folder_layout = QVBoxLayout()
        self.folder_layout.setSpacing(10)
        self.folder_layout.addWidget(StrongBodyLabel(i18nText("快速访问"), self))
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)

        # 定义快捷按钮生成函数
        def create_folder_btn(text, icon, sub_path):
            btn = PushButton(text, self)
            btn.setIcon(icon)
            btn.clicked.connect(lambda: self.open_folder(sub_path))
            return btn

        self.btn_version = create_folder_btn(i18nText("版本文件夹"), FluentIcon.FOLDER, "")
        self.btn_mods = create_folder_btn(i18nText("Mod 文件夹"), FluentIcon.ZIP_FOLDER, "mods")
        self.btn_resource = create_folder_btn(i18nText("资源包文件夹"), FluentIcon.ALBUM, "resourcepacks")
        self.btn_saves = create_folder_btn(i18nText("存档文件夹"), FluentIcon.SAVE, "saves")

        self.grid_layout.addWidget(self.btn_version, 0, 0)
        self.grid_layout.addWidget(self.btn_mods, 0, 1)
        self.grid_layout.addWidget(self.btn_resource, 1, 0)
        self.grid_layout.addWidget(self.btn_saves, 1, 1)

        self.folder_layout.addLayout(self.grid_layout)
        self.vLayout.addLayout(self.folder_layout)
        
        self.vLayout.addStretch(1)

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18nText("选择图标"), "", i18nText("图片文件 (*.png *.jpg *.ico);;所有文件 (*.*)")
        )
        if path:
            self.set_icon(path)

    def set_icon(self, path):
        """ 设置并显示图标 """
        self.icon_path = path
        if path and os.path.exists(path):
            self.icon_preview.setPixmap(QPixmap(path))
            self.icon_path_label.setText(os.path.basename(path))
        else:
            # 默认图标
            default_icon = "ui/icon/Grass_Block.png" 
            if os.path.exists(default_icon):
                self.icon_preview.setImage(default_icon)
            self.icon_path_label.setText(i18nText("默认图标"))

    def open_folder(self, sub_path):
        """ 打开指定子文件夹 """
        base_path = os.path.join(self.minecraft_dir, "versions", self.version_name)
        target_path = os.path.join(base_path, sub_path)
        
        if not os.path.exists(target_path):
            try:
                os.makedirs(target_path, exist_ok=True)
            except:
                InfoBar.warning(
                    title=i18nText('文件夹不存在'),
                    content=f"无法找到或创建文件夹: {target_path}",
                    parent=self.window()
                )
                return

        try:
            if sys.platform == 'win32':
                os.startfile(target_path)
            else:
                subprocess.Popen(['xdg-open', target_path])
        except Exception as e:
            InfoBar.error(
                title=i18nText('打开失败'),
                content=str(e),
                parent=self.window()
            )


class AdvancedPage(QWidget):
    """ 高级设置页面 """
    def __init__(self, delete_callback, parent=None):
        super().__init__(parent)
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setSpacing(20)

        # 1. 高级元数据
        self.meta_layout = QVBoxLayout()
        self.meta_layout.setSpacing(10)
        self.meta_layout.addWidget(StrongBodyLabel(i18nText("元数据设置"), self))
        
        # 真实版本号
        self.real_ver_edit = LineEdit(self)
        self.real_ver_edit.setPlaceholderText(i18nText("真实游戏版本 (例如: 1.21.8)"))
        self.meta_layout.addWidget(BodyLabel(i18nText("真实游戏版本"), self))
        self.meta_layout.addWidget(self.real_ver_edit)

        # Fabric 开关
        self.fabric_layout = QHBoxLayout()
        self.fabric_label = BodyLabel(i18nText("标记为 Fabric 版本"), self)
        self.fabric_switch = SwitchButton(self)
        self.fabric_switch.setOnText(i18nText("是"))
        self.fabric_switch.setOffText(i18nText("否"))
        
        self.fabric_layout.addWidget(self.fabric_label)
        self.fabric_layout.addWidget(self.fabric_switch)
        self.fabric_layout.addStretch(1)
        
        self.meta_layout.addLayout(self.fabric_layout)
        self.vLayout.addLayout(self.meta_layout)

        self.vLayout.addSpacing(20)
        
        # 2. 危险区域
        self.danger_layout = QVBoxLayout()
        self.danger_layout.setSpacing(10)
        self.danger_label = StrongBodyLabel(i18nText("危险区域"), self)
        self.danger_label.setTextColor("#cf1010", "#ff4d4f") # 红色文字
        self.danger_layout.addWidget(self.danger_label)

        self.delete_btn = PrimaryPushButton(i18nText("删除此核心"), self)
        self.delete_btn.setIcon(FluentIcon.DELETE)
        self.delete_btn.clicked.connect(delete_callback) 
        
        self.danger_layout.addWidget(self.delete_btn)
        self.vLayout.addLayout(self.danger_layout)
        
        self.vLayout.addStretch(1)
class ServerQueryThread(QThread):
    """ 用于查询服务器状态的后台线程 """
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, address):
        super().__init__()
        self.address = address

    def run(self):
        try:
            # 使用用户提供的 API
            url = f"https://api.mcsrvstat.us/3/{self.address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.finished.emit(data)
            else:
                self.error.emit(f"HTTP Error: {response.status_code}")
        except Exception as e:
            self.error.emit(str(e))


# --- NBT 解析工具类 (用于读取 servers.dat) ---
class SimpleNBT:
    TAG_END = 0
    TAG_BYTE = 1
    TAG_SHORT = 2
    TAG_INT = 3
    TAG_LONG = 4
    TAG_FLOAT = 5
    TAG_DOUBLE = 6
    TAG_BYTE_ARRAY = 7
    TAG_STRING = 8
    TAG_LIST = 9
    TAG_COMPOUND = 10
    TAG_INT_ARRAY = 11
    TAG_LONG_ARRAY = 12

    def __init__(self, data):
        self.stream = io.BytesIO(data)

    def read_tag(self, include_name=True):
        tag_type = self.read_byte()
        if tag_type == self.TAG_END:
            return None, None
        
        name = None
        if include_name:
            name = self.read_string()
        
        value = self.read_payload(tag_type)
        return name, value

    def read_payload(self, tag_type):
        if tag_type == self.TAG_BYTE:
            return self.read_byte()
        elif tag_type == self.TAG_SHORT:
            return self.read_short()
        elif tag_type == self.TAG_INT:
            return self.read_int()
        elif tag_type == self.TAG_LONG:
            return self.read_long()
        elif tag_type == self.TAG_FLOAT:
            return self.read_float()
        elif tag_type == self.TAG_DOUBLE:
            return self.read_double()
        elif tag_type == self.TAG_BYTE_ARRAY:
            length = self.read_int()
            return self.stream.read(length)
        elif tag_type == self.TAG_STRING:
            return self.read_string()
        elif tag_type == self.TAG_LIST:
            return self.read_list()
        elif tag_type == self.TAG_COMPOUND:
            return self.read_compound()
        elif tag_type == self.TAG_INT_ARRAY:
            length = self.read_int()
            return [self.read_int() for _ in range(length)]
        elif tag_type == self.TAG_LONG_ARRAY:
            length = self.read_int()
            return [self.read_long() for _ in range(length)]
        return None

    def read_byte(self):
        b = self.stream.read(1)
        if not b: return 0
        return struct.unpack('>b', b)[0]

    def read_short(self):
        return struct.unpack('>h', self.stream.read(2))[0]

    def read_int(self):
        return struct.unpack('>i', self.stream.read(4))[0]

    def read_long(self):
        return struct.unpack('>q', self.stream.read(8))[0]

    def read_float(self):
        return struct.unpack('>f', self.stream.read(4))[0]

    def read_double(self):
        return struct.unpack('>d', self.stream.read(8))[0]

    def read_string(self):
        length_bytes = self.stream.read(2)
        if len(length_bytes) < 2: return ""
        length = struct.unpack('>H', length_bytes)[0]
        return self.stream.read(length).decode('utf-8', errors='ignore')

    def read_list(self):
        tag_id = self.read_byte()
        length = self.read_int()
        res = []
        for _ in range(length):
            res.append(self.read_payload(tag_id))
        return res

    def read_compound(self):
        res = {}
        while True:
            tag_type = self.read_byte()
            if tag_type == self.TAG_END or tag_type == 0: # Handle potential EOF or End tag
                break
            name = self.read_string()
            value = self.read_payload(tag_type)
            res[name] = value
        return res

def parse_servers_dat(file_path):
    """ 解析 servers.dat 文件返回服务器列表 """
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # 检查是否为 GZIP 压缩 (标准 NBT 通常是 GZIP)
        if len(data) > 2 and data[:2] == b'\x1f\x8b':
            try:
                data = gzip.decompress(data)
            except:
                pass
                
        reader = SimpleNBT(data)
        # 根节点通常是一个 Compound Tag (name="")
        root_name, root_val = reader.read_tag()
        
        if isinstance(root_val, dict) and 'servers' in root_val:
            return root_val['servers']
        return []
    except Exception as e:
        log(f"解析 servers.dat 失败: {e}", logging.ERROR)
        return []

def save_servers_dat(file_path, servers_list):
    """ 将服务器列表保存为 servers.dat (NBT格式 + GZIP) """
    try:
        # 1. 构建 NBT 二进制数据
        bio = io.BytesIO()
        
        # 辅助写入函数
        def write_byte(v): bio.write(struct.pack('>b', v))
        def write_short(v): bio.write(struct.pack('>h', v))
        def write_string(s):
            encoded = s.encode('utf-8')
            write_short(len(encoded))
            bio.write(encoded)
            
        # 写入根 Compound Tag
        write_byte(10) # Tag_Compound
        write_string("") # Root name (empty)
        
        # 写入 servers 列表 Tag
        write_byte(9) # Tag_List
        write_string("servers")
        write_byte(10) # List payload type: Compound
        
        # 写入列表长度
        bio.write(struct.pack('>i', len(servers_list)))
        
        # 写入每个服务器 Compound
        for server in servers_list:
            # IP
            write_byte(8) # Tag_String
            write_string("ip")
            write_string(server.get("ip", ""))
            
            # Name
            write_byte(8) # Tag_String
            write_string("name")
            write_string(server.get("name", "Minecraft Server"))
            
            # Icon (如果有)
            if "icon" in server and server["icon"]:
                write_byte(8) # Tag_String
                write_string("icon")
                write_string(server["icon"])
            
            # acceptTextures (默认为 1/true 避免弹窗，或者不写)
            # write_byte(1) # Tag_Byte
            # write_string("acceptTextures")
            # write_byte(1)
            
            write_byte(0) # End of Server Compound
            
        write_byte(0) # End of Root Compound
        
        # 2. GZIP 压缩并写入文件
        raw_data = bio.getvalue()
        
        # 备份旧文件（如果存在）
        if os.path.exists(file_path):
            try:
                shutil.copy(file_path, file_path + ".bak")
            except:
                pass

        # 写入新文件
        with gzip.open(file_path, 'wb') as f:
            f.write(raw_data)
            
        log(f"成功保存 servers.dat 到 {file_path}")
        return True
        
    except Exception as e:
        handle_exception(e)
        log(f"保存 servers.dat 失败: {e}", logging.ERROR)
        return False

# --- 单个服务器列表项组件 ---
class ServerItemWidget(CardWidget):
    def __init__(self, name, ip, icon_data, parent=None):
        super().__init__(parent)
        self.ip = ip
        # 移除固定高度，允许内容撑开
        # self.setFixedHeight(80) 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16) # 稍微增加边距让布局更舒适
        layout.setSpacing(16)
        
        # 1. 图标
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(64, 64) # 稍微调大图标
        self.iconLabel.setScaledContents(True)
        
        # 默认图标
        self.default_pixmap = QPixmap(64, 64)
        self.default_pixmap.fill(QColor("#333333")) # 深灰色背景
        self.iconLabel.setPixmap(self.default_pixmap)
        
        # 处理初始 Base64 图标
        self.update_icon(icon_data)
        
        # 2. 文本信息
        textLayout = QVBoxLayout()
        textLayout.setSpacing(4)
        textLayout.setContentsMargins(0, 0, 0, 0)
        
        self.nameLabel = StrongBodyLabel(name, self)
        self.ipLabel = CaptionLabel(ip, self)
        self.ipLabel.setTextColor("#606060", "#a0a0a0") 
        
        self.statusLabel = BodyLabel(i18nText("正在获取状态..."), self)
        self.statusLabel.setTextColor("#0078D4", "#0078D4")
        self.statusLabel.setWordWrap(True) # 允许 MOTD 换行
        
        textLayout.addWidget(self.nameLabel)
        textLayout.addWidget(self.ipLabel)
        textLayout.addWidget(self.statusLabel)
        # textLayout.addStretch(1) # 移除 stretch，让内容决定高度
        
        # 3. 布局组装
        # 图标顶部对齐，防止文字过多时图标位置尴尬
        layout.addWidget(self.iconLabel, 0, Qt.AlignTop) 
        layout.addLayout(textLayout, 1) 
        
        # 移除原有的按钮区 layout.addLayout(btnLayout)

    def update_icon(self, icon_data):
        """ 解析 Base64 并更新图标 """
        if icon_data and isinstance(icon_data, str) and icon_data.startswith("data:image/png;base64,"):
            try:
                b64_data = icon_data.split(",")[1]
                img_data = base64.b64decode(b64_data)
                loaded_pixmap = QPixmap()
                if loaded_pixmap.loadFromData(img_data):
                    self.iconLabel.setPixmap(loaded_pixmap)
            except Exception as e:
                log(f"图标解析错误: {e}", logging.WARNING)

    def refresh_status(self):
        # 移除按钮禁用逻辑，只更新文本
        self.statusLabel.setText(i18nText("正在连接..."))
        self.statusLabel.setTextColor("#0078D4", "#0078D4")
        
        self.thread = ServerQueryThread(self.ip)
        self.thread.finished.connect(self.on_query_finished)
        self.thread.error.connect(self.on_query_error)
        self.thread.start()

    def on_query_finished(self, data):
        # 移除按钮启用逻辑
        online = data.get("online", False)
        
        # 尝试从 API 响应中更新图标
        api_icon = data.get("icon", None)
        if api_icon:
            self.update_icon(api_icon)
            
        if online:
            players = data.get("players", {})
            curr = players.get("online", 0)
            max_p = players.get("max", 0)
            
            # MOTD 处理：显示完整信息，不截断
            motd_raw = data.get("motd", {}).get("clean", [])
            # 将列表合并为多行字符串，且不进行长度截断
            motd_str = "\n".join(motd_raw).strip() if motd_raw else "Online"
            
            self.statusLabel.setText(f"🟢 {curr}/{max_p}\n{motd_str}")
            self.statusLabel.setTextColor("#107C10", "#107C10") # 绿色
        else:
            self.statusLabel.setText(i18nText("🔴 无法连接服务器"))
            self.statusLabel.setTextColor("#D13438", "#D13438") # 红色

    def on_query_error(self, err):
        # 移除按钮启用逻辑
        self.statusLabel.setText(i18nText("⚠️ 网络错误"))
        self.statusLabel.setTextColor("#D13438", "#D13438")



class AddServerDialog(MessageBoxBase):
    """ 添加服务器对话框 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(i18nText("添加服务器"), self)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 服务器名称
        self.nameLabel = BodyLabel(i18nText("服务器名称"), self)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText(i18nText("例如: Bloret Server"))
        self.nameEdit.setText("Minecraft Server")
        
        self.viewLayout.addWidget(self.nameLabel)
        self.viewLayout.addWidget(self.nameEdit)
        
        # 服务器地址
        self.ipLabel = BodyLabel(i18nText("服务器地址"), self)
        self.ipEdit = LineEdit(self)
        self.ipEdit.setPlaceholderText(i18nText("例如: mc.example.com"))
        self.ipEdit.setFocus()
        
        self.viewLayout.addWidget(self.ipLabel)
        self.viewLayout.addWidget(self.ipEdit)
        
        self.yesButton.setText(i18nText("添加"))
        self.cancelButton.setText(i18nText("取消"))
        
        # 简单的验证：禁止空IP
        self.ipEdit.textChanged.connect(self.validate)
        
        # 修改弹窗宽度
        self.widget.setMinimumWidth(500) # 加宽弹窗
        
        # 初始化验证
        self.validate()
        
        # 连接点击事件
        try:
            self.yesButton.clicked.disconnect()
        except:
            pass
        self.yesButton.clicked.connect(self.accept)
        
    def validate(self):
        self.yesButton.setDisabled(len(self.ipEdit.text().strip()) == 0)
        
    def get_data(self):
        return {
            "name": self.nameEdit.text().strip(),
            "ip": self.ipEdit.text().strip()
        }


class ServerPage(QWidget):
    """ 服务器管理页面 (读取/写入 servers.dat) """
    def __init__(self, version_name, minecraft_dir, home_interface, parent=None):
        super().__init__(parent)
        self.version_name = version_name
        self.minecraft_dir = minecraft_dir
        self.home_interface = home_interface
        
        # 确定 servers.dat 路径
        self.version_servers_dat = os.path.join(minecraft_dir, "versions", version_name, "servers.dat")
        self.root_servers_dat = os.path.join(minecraft_dir, "servers.dat")
        
        # 确定当前使用的路径
        self.target_dat_path = self.version_servers_dat

        self.current_servers = [] # 内存中缓存列表

        self.vLayout = QVBoxLayout(self)
        self.vLayout.setSpacing(10)
        
        # 1. 顶部工具栏
        self.headerLayout = QHBoxLayout()
        self.refreshBtn = ToolButton(FluentIcon.SYNC, self)
        self.refreshBtn.setToolTip(i18nText("重新读取列表"))
        self.refreshBtn.clicked.connect(self.load_servers)
        
        self.addBtn = PushButton(i18nText("添加服务器"), self)
        self.addBtn.setIcon(FluentIcon.ADD)
        self.addBtn.clicked.connect(self.add_server) # 连接添加函数
        
        self.headerLayout.addWidget(StrongBodyLabel(i18nText("服务器列表"), self))
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.refreshBtn)
        self.headerLayout.addWidget(self.addBtn)
        self.vLayout.addLayout(self.headerLayout)
        
        # 2. 列表滚动区
        from modules.compat_widgets import SmoothScrollArea
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 0, 10, 0)
        self.contentLayout.setSpacing(8)
        self.contentLayout.addStretch(1)
        
        self.scrollArea.setWidget(self.contentWidget)
        self.vLayout.addWidget(self.scrollArea)
        
        # 初始加载
        self.load_servers()

    def showEvent(self, event):
        """ 重写显示事件，当切换到此页面时自动刷新列表 """
        super().showEvent(event)
        # 每次进入页面都重新加载，确保数据是最新的
        self.load_servers()

    def load_servers(self):
        # 清空 UI
        while self.contentLayout.count() > 1:
            item = self.contentLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_servers = []
        
        # 优先读取版本目录，其次读取根目录
        read_path = ""
        if os.path.exists(self.version_servers_dat):
            read_path = self.version_servers_dat
        elif os.path.exists(self.root_servers_dat):
            read_path = self.root_servers_dat
            
        if read_path:
            self.current_servers = parse_servers_dat(read_path)
            
        log(f"加载服务器列表: {read_path}, 数量: {len(self.current_servers)}")
        
        if not self.current_servers:
            empty_lbl = BodyLabel(i18nText("暂无服务器"), self)
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.contentLayout.insertWidget(0, empty_lbl)
            return

        # 生成列表项
        for server in self.current_servers:
            name = server.get('name', 'Minecraft Server')
            ip = server.get('ip', '')
            icon = server.get('icon', None)
            
            item = ServerItemWidget(name, ip, icon, self)
            self.contentLayout.insertWidget(self.contentLayout.count() - 1, item)
            
            # --- 修改处：立即触发状态刷新 ---
            # 这里的 refresh_status 会启动异步线程，不会阻塞 UI
            item.refresh_status()

    def add_server(self):
        """ 弹出对话框添加服务器并保存 """
        w = AddServerDialog(self.window())
        if w.exec():
            data = w.get_data()
            new_server = {
                "name": data["name"],
                "ip": data["ip"],
                "icon": "" # 初始无图标，刷新后会自动获取但不保存回文件
            }
            
            # 添加到内存列表
            self.current_servers.append(new_server)
            
            # 确定保存路径 (默认保存到版本隔离目录)
            save_path = self.version_servers_dat
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            if save_servers_dat(save_path, self.current_servers):
                InfoBar.success(
                    title=i18nText("添加成功"),
                    content=i18nText(f"服务器 {data['name']} 已添加到列表"),
                    parent=self.window()
                )
                self.load_servers() # 刷新 UI (这也会自动触发新添加服务器的状态刷新)
            else:
                InfoBar.error(
                    title=i18nText("保存失败"),
                    content=i18nText("无法写入 servers.dat 文件"),
                    parent=self.window()
                )


class ModItemWidget(CardWidget):
    """ Mod 列表项组件 """
    def __init__(self, data, parent_page):
        super().__init__(parent_page)
        self.data = data
        self.parent_page = parent_page
        self.setFixedHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # 1. 图标
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(48, 48)
        self.iconLabel.setScaledContents(True)
        # 默认图标
        default_pix = FluentIcon.COMPLETED.icon().pixmap(48, 48)
        self.iconLabel.setPixmap(default_pix)
        
        if data.get("icon_data"):
            try:
                pix = QPixmap()
                pix.loadFromData(data["icon_data"])
                if not pix.isNull():
                    self.iconLabel.setPixmap(pix)
            except:
                pass
            
        # 2. 文本信息
        textLayout = QVBoxLayout()
        textLayout.setSpacing(2)
        
        topLine = QHBoxLayout()
        self.nameLabel = StrongBodyLabel(data["name"], self)
        self.verLabel = CaptionLabel(data["version"], self)
        self.verLabel.setTextColor("#606060", "#a0a0a0")
        
        topLine.addWidget(self.nameLabel)
        topLine.addWidget(self.verLabel)
        topLine.addStretch(1)
        
        self.descLabel = BodyLabel(data["description"], self)
        self.descLabel.setTextColor("#606060", "#a0a0a0")

        # 确保 Label 不会撑大水平布局
        self.descLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        # 文本截断
        font_metrics = self.descLabel.fontMetrics()
        elided_text = font_metrics.elidedText(data["description"], Qt.ElideRight, 400)
        self.descLabel.setText(elided_text)
        
        textLayout.addLayout(topLine)
        textLayout.addWidget(self.descLabel)
        
        # 3. 操作按钮
        self.switchBtn = SwitchButton(self)
        self.switchBtn.setOnText(i18nText("启用"))
        self.switchBtn.setOffText(i18nText("禁用"))
        self.switchBtn.setChecked(data["enabled"])
        self.switchBtn.checkedChanged.connect(self.on_toggle)
        
        self.delBtn = ToolButton(FluentIcon.DELETE, self)
        self.delBtn.setToolTip(i18nText("删除"))
        self.delBtn.clicked.connect(self.on_delete)
        
        layout.addWidget(self.iconLabel)
        layout.addLayout(textLayout, 1)
        layout.addWidget(self.switchBtn)
        layout.addWidget(self.delBtn)
        
    def on_toggle(self, checked):
        # 更新本地数据中的 path，防止连续操作出错
        new_path = self.parent_page.toggle_mod(self.data["path"], checked)
        if new_path:
            self.data["path"] = new_path
            self.data["enabled"] = checked
        else:
            # 如果操作失败，回滚开关状态
            self.switchBtn.blockSignals(True)
            self.switchBtn.setChecked(not checked)
            self.switchBtn.blockSignals(False)
        
    def on_delete(self):
        self.parent_page.delete_mod(self.data["path"])

class ModLoaderThread(QThread):
    """ Mod 异步加载线程 """
    item_loaded = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, mods_dir):
        super().__init__()
        self.mods_dir = mods_dir

    def run(self):
        if not os.path.exists(self.mods_dir):
            self.finished.emit()
            return

        files = os.listdir(self.mods_dir)
        for filename in files:
            file_path = os.path.join(self.mods_dir, filename)
            if os.path.isdir(file_path): continue
            
            is_disabled = filename.endswith('.disabled')
            
            # 简单扩展名检查
            if not (filename.endswith('.jar') or filename.endswith('.jar.disabled')):
                continue

            mod_data = {
                "name": filename, # 默认显示文件名
                "path": file_path,
                "filename": filename,
                "version": "",
                "description": i18nText("无描述"),
                "icon_data": None,
                "enabled": not is_disabled
            }

            # 尝试读取元数据 (主要针对 Fabric)
            try:
                if zipfile.is_zipfile(file_path):
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        # Fabric metadata
                        if 'fabric.mod.json' in zf.namelist():
                            with zf.open('fabric.mod.json') as f:
                                meta = json.load(f)
                                mod_data["name"] = meta.get("name", meta.get("id", filename))
                                mod_data["version"] = meta.get("version", "")
                                mod_data["description"] = meta.get("description", "")
                                
                                icon_path = meta.get("icon")
                                if icon_path and icon_path in zf.namelist():
                                    mod_data["icon_data"] = zf.read(icon_path)
                                # 部分 Mod 图标路径在 assets 下
                                elif f"assets/{meta.get('id')}/icon.png" in zf.namelist():
                                    mod_data["icon_data"] = zf.read(f"assets/{meta.get('id')}/icon.png")
                        
                        # Forge (mcmod.info - 旧版)
                        elif 'mcmod.info' in zf.namelist():
                            with zf.open('mcmod.info') as f:
                                try:
                                    meta_list = json.load(f)
                                    if meta_list and isinstance(meta_list, list):
                                        meta = meta_list[0]
                                        mod_data["name"] = meta.get("name", filename)
                                        mod_data["version"] = meta.get("version", "")
                                        mod_data["description"] = meta.get("description", "")
                                        # Forge 图标处理较复杂，通常是 logoFile
                                        logo = meta.get("logoFile")
                                        if logo and logo in zf.namelist():
                                            mod_data["icon_data"] = zf.read(logo)
                                except:
                                    pass
            except Exception as e:
                log(f"读取 Mod {filename} 失败: {e}", logging.WARNING)
            
            self.item_loaded.emit(mod_data)
        
        self.finished.emit()

class ModPage(QWidget):
    """ Mod 管理页面 """
    def __init__(self, version_name, minecraft_dir, parent=None):
        super().__init__(parent)
        self.version_name = version_name
        self.minecraft_dir = minecraft_dir
        # 假设启用版本隔离，Mods 位于 versions/{version}/mods
        self.mods_dir = os.path.join(minecraft_dir, "versions", version_name, "mods")
        
        self.vLayout = QVBoxLayout(self)
        
        # 顶部工具栏
        hLayout = QHBoxLayout()
        self.refreshBtn = ToolButton(FluentIcon.SYNC, self)
        self.refreshBtn.setToolTip(i18nText("刷新"))
        self.refreshBtn.clicked.connect(self.load_mods)
        
        self.openBtn = PushButton(i18nText("打开 Mods 文件夹"), self)
        self.openBtn.setIcon(FluentIcon.FOLDER)
        self.openBtn.clicked.connect(self.open_folder)
        
        hLayout.addWidget(StrongBodyLabel(i18nText("Mod 列表"), self))
        hLayout.addStretch(1)
        hLayout.addWidget(self.refreshBtn)
        hLayout.addWidget(self.openBtn)
        self.vLayout.addLayout(hLayout)
        
        # 列表区域
        from modules.compat_widgets import SmoothScrollArea
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # --- 修改点开始：禁用水平滚动条 ---
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # --- 修改点结束 ---
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setAlignment(Qt.AlignTop)
        self.contentLayout.setSpacing(8)
        # --- 修改点开始：调整边距，留出一点空间给垂直滚动条，避免挤压 ---
        self.contentLayout.setContentsMargins(0, 0, 4, 0) 
        # --- 修改点结束 ---
        
        self.scrollArea.setWidget(self.contentWidget)
        self.vLayout.addWidget(self.scrollArea)
        
        # 初始加载
        self.load_mods()

    def showEvent(self, event):
        super().showEvent(event)
        if self.contentLayout.count() == 0:
            self.load_mods()

    def open_folder(self):
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir, exist_ok=True)
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.mods_dir)))

    def load_mods(self):
        # 清空列表
        while self.contentLayout.count():
            item = self.contentLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir, exist_ok=True)
            
        self.loading_label = BodyLabel(i18nText("正在加载 Mods..."), self)
        self.contentLayout.addWidget(self.loading_label)
            
        self.thread = ModLoaderThread(self.mods_dir)
        self.thread.item_loaded.connect(self.add_item)
        self.thread.finished.connect(lambda: self.loading_label.deleteLater())
        self.thread.start()
        
    def add_item(self, data):
        item = ModItemWidget(data, self)
        # 插入到倒数第二的位置（如果有 loading label 的话），或者直接添加
        self.contentLayout.addWidget(item)
        
    def toggle_mod(self, path, enabled):
        """ 切换 Mod 启用状态 """
        try:
            if not os.path.exists(path):
                return None
                
            dirname, filename = os.path.split(path)
            
            if enabled:
                # 启用：去除 .disabled 后缀
                if filename.endswith('.disabled'):
                    new_filename = filename[:-9]
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
                    return new_path
            else:
                # 禁用：添加 .disabled 后缀
                if not filename.endswith('.disabled'):
                    new_filename = filename + '.disabled'
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
                    return new_path
            return path # 无需修改
        except Exception as e:
            InfoBar.error(title=i18nText("操作失败"), content=str(e), parent=self.window())
            return None
            
    def delete_mod(self, path):
        if os.path.exists(path):
            # 二次确认
            w = MessageBoxBase(self.window())
            w.viewLayout.addWidget(SubtitleLabel(i18nText("确认删除?")))
            w.viewLayout.addWidget(BodyLabel(os.path.basename(path)))
            w.yesButton.setText(i18nText("删除"))
            w.cancelButton.setText(i18nText("取消"))
            if w.exec():
                try:
                    if send2trash:
                        send2trash.send2trash(path)
                    else:
                        import shutil
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    InfoBar.success(title=i18nText("已删除"), content=os.path.basename(path), parent=self.window())
                    self.load_mods() # 刷新列表
                except Exception as e:
                    InfoBar.error(title=i18nText("删除失败"), content=str(e), parent=self.window())

# --- 资源包管理相关类 ---

class ResourcePackLoaderThread(QThread):
    """ 资源包异步加载线程 """
    item_loaded = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, packs_dir):
        super().__init__()
        self.packs_dir = packs_dir

    def run(self):
        if not os.path.exists(self.packs_dir):
            self.finished.emit()
            return

        for filename in os.listdir(self.packs_dir):
            file_path = os.path.join(self.packs_dir, filename)
            
            # 资源包可以是文件夹或 .zip
            if not (os.path.isdir(file_path) or filename.endswith('.zip')):
                continue

            pack_data = {
                "name": filename,
                "path": file_path,
                "description": i18nText("无描述"),
                "icon_data": None
            }

            try:
                # 如果是文件夹
                if os.path.isdir(file_path):
                    mcmeta_path = os.path.join(file_path, "pack.mcmeta")
                    icon_path = os.path.join(file_path, "pack.png")
                    
                    if os.path.exists(mcmeta_path):
                        with open(mcmeta_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                            pack_data["description"] = meta.get("pack", {}).get("description", "")
                    
                    if os.path.exists(icon_path):
                        with open(icon_path, 'rb') as f:
                            pack_data["icon_data"] = f.read()
                            
                # 如果是 Zip
                elif zipfile.is_zipfile(file_path):
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        if "pack.mcmeta" in zf.namelist():
                            with zf.open("pack.mcmeta") as f:
                                meta = json.load(f)
                                pack_data["description"] = meta.get("pack", {}).get("description", "")
                        
                        if "pack.png" in zf.namelist():
                            pack_data["icon_data"] = zf.read("pack.png")
            except Exception as e:
                log(f"读取资源包 {filename} 失败: {e}", logging.WARNING)

            self.item_loaded.emit(pack_data)
        
        self.finished.emit()

class ResourcePackItemWidget(CardWidget):
    """ 资源包列表项组件 (目前暂无启用禁用功能，仅管理文件) """
    def __init__(self, data, parent_page):
        super().__init__(parent_page)
        self.data = data
        self.parent_page = parent_page
        self.setFixedHeight(80)
        
        log(f"加载资源包项: {data}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(48, 48)
        self.iconLabel.setScaledContents(True)
        default_pix = FluentIcon.FOLDER.icon().pixmap(48, 48)
        self.iconLabel.setPixmap(default_pix)
        
        if data.get("icon_data"):
            try:
                pix = QPixmap()
                pix.loadFromData(data["icon_data"])
                if not pix.isNull():
                    self.iconLabel.setPixmap(pix)
            except:
                pass
            
        # Text
        textLayout = QVBoxLayout()
        textLayout.setSpacing(2)

        self.descLabel = BodyLabel(self)
        self.nameLabel = StrongBodyLabel(data["name"], self)
        # 如果description是字典，尝试获取特定语言的描述
        desc_data = data["description"]
        if isinstance(desc_data, dict):
            description_text = desc_data.get("translate", desc_data.get("en", str(desc_data)))
        else:
            # 如果它已经是字符串，则直接使用
            description_text = str(desc_data)

        self.descLabel.setText(description_text)
        self.descLabel.setTextColor("#606060", "#a0a0a0")

        # 确保 Label 不会撑大水平布局
        self.descLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        
        # 简单截断
        font_metrics = self.descLabel.fontMetrics()
        elided_text = font_metrics.elidedText(description_text, Qt.ElideRight, 400)
        self.descLabel.setText(elided_text)
        
        textLayout.addWidget(self.nameLabel)
        textLayout.addWidget(self.descLabel)
        
        # Controls
        self.delBtn = ToolButton(FluentIcon.DELETE, self)
        self.delBtn.setToolTip(i18nText("删除"))
        self.delBtn.clicked.connect(self.on_delete)
        
        layout.addWidget(self.iconLabel)
        layout.addLayout(textLayout, 1)
        layout.addWidget(self.delBtn)
        
    def on_delete(self):
        self.parent_page.delete_pack(self.data["path"])

class ResourcePackPage(QWidget):
    """ 资源包管理页面 """
    def __init__(self, version_name, minecraft_dir, parent=None):
        super().__init__(parent)
        self.version_name = version_name
        self.minecraft_dir = minecraft_dir
        self.packs_dir = os.path.join(minecraft_dir, "versions", version_name, "resourcepacks")
        
        self.vLayout = QVBoxLayout(self)
        
        # Header
        hLayout = QHBoxLayout()
        self.refreshBtn = ToolButton(FluentIcon.SYNC, self)
        self.refreshBtn.clicked.connect(self.load_packs)
        self.openBtn = PushButton(i18nText("打开资源包文件夹"), self)
        self.openBtn.setIcon(FluentIcon.FOLDER)
        self.openBtn.clicked.connect(self.open_folder)
        
        hLayout.addWidget(StrongBodyLabel(i18nText("资源包列表"), self))
        hLayout.addStretch(1)
        hLayout.addWidget(self.refreshBtn)
        hLayout.addWidget(self.openBtn)
        self.vLayout.addLayout(hLayout)
        
        # List
        from modules.compat_widgets import SmoothScrollArea
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # --- 修改点开始：禁用水平滚动条 ---
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # --- 修改点结束 ---
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setAlignment(Qt.AlignTop)
        self.contentLayout.setSpacing(8)
        # --- 修改点开始：调整边距 ---
        self.contentLayout.setContentsMargins(0, 0, 4, 0)
        # --- 修改点结束 ---
        
        self.scrollArea.setWidget(self.contentWidget)
        self.vLayout.addWidget(self.scrollArea)
        
        self.load_packs()

    def showEvent(self, event):
        super().showEvent(event)
        if self.contentLayout.count() == 0:
            self.load_packs()

    def open_folder(self):
        if not os.path.exists(self.packs_dir):
            os.makedirs(self.packs_dir, exist_ok=True)
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.packs_dir)))

    def load_packs(self):
        while self.contentLayout.count():
            item = self.contentLayout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not os.path.exists(self.packs_dir):
            os.makedirs(self.packs_dir, exist_ok=True)
            
        self.loading_label = BodyLabel(i18nText("正在加载资源包..."), self)
        self.contentLayout.addWidget(self.loading_label)
            
        self.thread = ResourcePackLoaderThread(self.packs_dir)
        self.thread.item_loaded.connect(self.add_item)
        self.thread.finished.connect(lambda: self.loading_label.deleteLater())
        self.thread.start()
        
    def add_item(self, data):
        item = ResourcePackItemWidget(data, self)
        self.contentLayout.addWidget(item)
        
    def delete_pack(self, path):
        if os.path.exists(path):
            w = MessageBoxBase(self.window())
            w.viewLayout.addWidget(SubtitleLabel(i18nText("确认删除?")))
            w.viewLayout.addWidget(BodyLabel(os.path.basename(path)))
            w.yesButton.setText(i18nText("删除"))
            w.cancelButton.setText(i18nText("取消"))
            if w.exec():
                try:
                    if send2trash:
                        send2trash.send2trash(path)
                    else:
                        import shutil
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    InfoBar.success(title=i18nText("已删除"), content=os.path.basename(path), parent=self.window())
                    self.load_packs()
                except Exception as e:
                    InfoBar.error(title=i18nText("删除失败"), content=str(e), parent=self.window())


class CoreManageDialog(MessageBoxBase):
    """ 核心管理对话框 (分页式) """
    def __init__(self, version_name, minecraft_dir, home_interface, parent=None):
        super().__init__(parent)
        self.version_name = version_name
        self.minecraft_dir = minecraft_dir
        self.home_interface = home_interface
        self.bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
        self.current_data = {}

        # 调整对话框大小
        self.widget.setMinimumWidth(650)
        self.widget.setMinimumHeight(550)

        # 1. 顶部标题
        self.titleLabel = SubtitleLabel(i18nText("核心管理") + f": {version_name}", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 2. Pivot 导航栏
        self.pivot = Pivot(self)
        self.pivot.addItem(routeKey="baseInfo", text=i18nText("基本信息"))
        self.pivot.addItem(routeKey="server", text=i18nText("服务器"))
        self.pivot.addItem(routeKey="resource", text=i18nText("资源包"))
        self.pivot.addItem(routeKey="mod", text=i18nText("Mod"))
        self.pivot.addItem(routeKey="advanced", text=i18nText("高级")) # 改为高级
        self.viewLayout.addWidget(self.pivot)

        # 3. StackedWidget 内容区
        self.stackedWidget = QStackedWidget(self)
        self.viewLayout.addWidget(self.stackedWidget)

        # 初始化各个页面
        # 传入 version_name 和 minecraft_dir 给 BaseInfoPage
        self.baseInfoPage = BaseInfoPage(self.version_name, self.minecraft_dir, self)
        self.serverPage = ServerPage(self.version_name, self.minecraft_dir, self.home_interface, self)
        self.resourcePage = ResourcePackPage(self.version_name, self.minecraft_dir, self)
        self.modPage = ModPage(self.version_name, self.minecraft_dir, self)
        # 使用 AdvancedPage 替换 ControlPage
        self.advancedPage = AdvancedPage(self.delete_core, self)

        self.stackedWidget.addWidget(self.baseInfoPage)
        self.stackedWidget.addWidget(self.serverPage)
        self.stackedWidget.addWidget(self.resourcePage)
        self.stackedWidget.addWidget(self.modPage)
        self.stackedWidget.addWidget(self.advancedPage)

        # 连接信号
        self.pivot.currentItemChanged.connect(lambda k: self.stackedWidget.setCurrentIndex(
            ["baseInfo", "server", "resource", "mod", "advanced"].index(k)
        ))

        # 加载数据
        self.load_data()

        # 调整底部按钮
        self.yesButton.setText(i18nText("保存修改"))
        self.cancelButton.setText(i18nText("关闭"))

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self.save_data)

    def load_data(self):
        """ 从 .BL.json 加载数据 """
        try:
            if os.path.exists(self.bl_json_path):
                with open(self.bl_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    versions_data = data.get("versions", {})
                    self.current_data = versions_data.get(self.version_name, {})
                    
                    # 填充 BaseInfoPage
                    self.baseInfoPage.name_edit.setText(self.version_name)
                    # 设置图标
                    icon_path = self.current_data.get("icon", "")
                    self.baseInfoPage.set_icon(icon_path)

                    # 填充 AdvancedPage
                    self.advancedPage.real_ver_edit.setText(self.current_data.get("version", self.version_name))
                    self.advancedPage.fabric_switch.setChecked(self.current_data.get("Fabric", False))
            else:
                 # 默认初始化
                self.baseInfoPage.name_edit.setText(self.version_name)
                self.baseInfoPage.set_icon("")
                self.advancedPage.real_ver_edit.setText(self.version_name)

        except Exception as e:
            log(f"加载核心信息失败: {e}", logging.ERROR)

    def delete_core(self):
        # 询问确认
        w = MessageBoxBase(self)
        w.viewLayout.addWidget(SubtitleLabel(i18nText("确认删除?")))
        w.viewLayout.addWidget(BodyLabel(i18nText("将删除此 Minecraft 版本。删除后可在系统回收站中找到。")))
        w.yesButton.setText(i18nText("删除"))
        w.cancelButton.setText(i18nText("取消"))
        
        if w.exec():
            version_path = os.path.join(self.minecraft_dir, "versions", self.version_name)
            try:
                if os.path.exists(version_path):
                    if send2trash:
                        send2trash.send2trash(version_path)
                    else:
                        import shutil
                        shutil.rmtree(version_path)
                    log(f"核心已删除: {version_path}")
                    try:
                        if os.path.exists(self.bl_json_path):
                            with open(self.bl_json_path, "r", encoding="utf-8") as f:
                                full_data = json.load(f)
                            
                            if "versions" in full_data and self.version_name in full_data["versions"]:
                                del full_data["versions"][self.version_name]
                                
                                with open(self.bl_json_path, "w", encoding="utf-8") as f:
                                    json.dump(full_data, f, ensure_ascii=False, indent=4)
                                log(f"已从 .BL.json 中移除核心信息: {self.version_name}")
                    except Exception as e_json:
                        log(f"更新 .BL.json 失败: {e_json}", logging.WARNING)

                    InfoBar.success(title=i18nText("删除成功"), content=i18nText("核心已移至回收站"), parent=self.parent())
                    self.reject() # 关闭当前管理窗口
            except Exception as e:
                InfoBar.error(title=i18nText("删除失败"), content=str(e), parent=self)

    def save_data(self):
        """ 保存数据 """
        # 获取 BaseInfoPage 的数据
        new_name = self.baseInfoPage.name_edit.text().strip()
        new_icon = self.baseInfoPage.icon_path # 获取图标路径
        
        # 获取 AdvancedPage 的数据
        new_real_ver = self.advancedPage.real_ver_edit.text().strip()
        is_fabric = self.advancedPage.fabric_switch.isChecked()
        
        if not new_name:
            InfoBar.error(title=i18nText("错误"), content=i18nText("核心名称不能为空"), parent=self.widget)
            return

        try:
            # 读取完整的 json
            full_data = {"versions": {}}
            if os.path.exists(self.bl_json_path):
                with open(self.bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)

            # 1. 处理文件夹重命名
            if new_name != self.version_name:
                old_path = os.path.join(self.minecraft_dir, "versions", self.version_name)
                new_path = os.path.join(self.minecraft_dir, "versions", new_name)
                
                if os.path.exists(new_path):
                    InfoBar.error(title=i18nText("错误"), content=i18nText("目标名称已存在"), parent=self.widget)
                    return
                
                try:
                    os.rename(old_path, new_path)
                    log(f"核心已重命名: {self.version_name} -> {new_name}")
                except Exception as e:
                    InfoBar.error(title=i18nText("重命名失败"), content=str(e), parent=self.widget)
                    return

                # 在 JSON 中移除旧键
                if self.version_name in full_data["versions"]:
                    del full_data["versions"][self.version_name]
            
            # 2. 更新 JSON 数据
            full_data["versions"][new_name] = {
                "Fabric": is_fabric,
                "version": new_real_ver,
                "setup_time": self.current_data.get("setup_time", int(time.time())),
                "icon": new_icon
            }

            # 写入文件
            with open(self.bl_json_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)

            InfoBar.success(
                title=i18nText("保存成功"),
                content=i18nText("核心信息已更新"),
                parent=self.parent() if self.parent() else self.widget
            )
            
            # 如果发生了重命名，更新全局列表
            if new_name != self.version_name:
                if hasattr(BLglobals, 'set_list') and self.version_name in BLglobals.set_list:
                    index = BLglobals.set_list.index(self.version_name)
                    BLglobals.set_list[index] = new_name
                if hasattr(BLglobals, 'minecraft_list') and self.version_name in BLglobals.minecraft_list:
                    index = BLglobals.minecraft_list.index(self.version_name)
                    BLglobals.minecraft_list[index] = new_name

            self.accept() # 关闭弹窗

        except Exception as e:
            handle_exception(e)
            InfoBar.error(title=i18nText("保存失败"), content=str(e), parent=self.widget)


def open_core_management(parent, version_name, MINECRAFT_DIR, home_interface):
    """ 打开核心管理对话框的入口函数 """
    dialog = CoreManageDialog(version_name, MINECRAFT_DIR, home_interface, parent=parent)
    if dialog.exec():
        return True # 返回 True 表示需要刷新列表
    return False # 返回 False (如取消或出错) 视情况刷新，但在 setup_ui 中我们做了全量刷新，所以影响不大


def show_core_manager_dialog(version_name, minecraft_dir):
    """从 QML 调用的核心管理对话框入口函数"""
    from PySide6.QtWidgets import QApplication
    
    parent_widget = QApplication.activeWindow()
    if parent_widget is None:
        parent_widget = QWidget()
        parent_widget.hide()
    
    dialog = CoreManageDialog(version_name, minecraft_dir, None, parent=parent_widget)
    result = dialog.exec()
    
    return result