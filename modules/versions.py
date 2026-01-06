'''
Versions.py
## Bloret Launcher 版本操作模块

### 模块功能：
 - [x] 删除 Minecraft 版本
 - [x] 修改 Minecraft 版本名称
 - [x] 删除自定义选项
 - [x] 修改自定义选项名称

***
###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
'''
import logging
import os
import json
import platform
import requests
import shutil
import concurrent.futures
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
import sip  # type: ignore
import send2trash
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QDesktopServices, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QListWidget, QListWidgetItem, QFileDialog, QLabel, 
    QSizePolicy
)
from qfluentwidgets import (
    InfoBar, InfoBarPosition, ComboBox, StrongBodyLabel, 
    BodyLabel, SubtitleLabel, MessageBoxBase, LineEdit, 
    PushButton, SwitchButton, CaptionLabel, Pivot, 
    SegmentedWidget, CardWidget, IconWidget, FluentIcon,
    IndeterminateProgressBar, ToolButton
)

# 自定义模块
from modules.win11toast import notify, update_progress
from modules.safe import handle_exception
from modules.log import log
from modules.customize import find_Customize
from modules.i18n import i18nText
import modules.globals as BLglobals
import modules.config as cfg

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
    # 检查是否包含Forge/Fabric等特定库
    special_libs = ["minecraftforge", "fabricmc", "neoforged"]
    use_official_only = any(lib in original_url for lib in special_libs)
    
    if use_official_only:
        # 不添加原版源
        return [
            original_url
                .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven")
                .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven")
                .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"),
            original_url
                .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
                .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
                .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries")
        ]
    else:
        # 官方源
        official_urls = [original_url]
        
        # 镜像源
        mirror_urls = [
            original_url
                .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven")
                .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven")
                .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"),
            original_url
                .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
                .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/libraries")
                .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries")
        ]
        
        # 根据是否优先使用官方源决定URL顺序
        # 这里我们默认使用镜像源优先，与PCL的逻辑保持一致
        return mirror_urls + official_urls

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

def open_minecraft_version_folder(self,version,MINECRAFT_DIR):
    '''

    打开指定的 Minecraft 版本文件夹
     version 要删除的版本名称
     versions 版本 ComboBox 控件
     MINECRAFT_DIR Minecraft 安装目录

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在打开 Minecraft 版本文件夹：{version}")
    
    # 构建版本文件夹路径
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    
    try:
        # 检查版本文件夹是否存在
        if os.path.exists(version_path) and os.path.isdir(version_path):
            # 使用默认文件管理器打开文件夹
            os.startfile(version_path)
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
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
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
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
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
            with open(BLglobals.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
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
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
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
            with open(BLglobals.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
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
                    from PyQt5.QtWidgets import QLabel
                    from PyQt5.QtCore import QMetaObject, Qt
                    thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                    if thread_label:
                        QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                               __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(self._active_downloads)))
                except Exception as e:
                    log(f"更新libraries_file_working_Thread时出错: {e}")

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(lib_path), exist_ok=True)
            
            # 下载库文件
            if "downloads" in lib and "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                original_url = artifact["url"]
                
                candidate_urls = []
                # 优先添加原始 URL
                candidate_urls.append(original_url)
                
                # 如果原始 URL 是 Minecraft 官方库，添加 BMCLAPI 镜像
                if "libraries.minecraft.net" in original_url:
                    candidate_urls.append(original_url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/"))
                # 如果原始 URL 是 Fabric Maven 库，添加 BMCLAPI 镜像
                elif "maven.fabricmc.net" in original_url:
                    candidate_urls.append(original_url.replace("https://maven.fabricmc.net/", "https://bmclapi2.bangbang93.com/maven/"))

                downloaded = False
                for url_to_try in candidate_urls:
                    for attempt in range(3): # 尝试3次
                        try:
                            log(f"正在下载库文件 (尝试 {attempt + 1}/3): {url_to_try} -> {lib_path}")
                            response = requests.get(url_to_try, proxies=None, timeout=30)
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
            elif "name" in lib:
                # 处理 Maven 风格的库名称
                parts = lib["name"].split(":")
                if len(parts) >= 3:
                    group_id, artifact_id, version = parts[0:3]
                    
                    candidate_urls = [
                        f"https://maven.fabricmc.net/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar", # Fabric Maven
                        f"https://bmclapi2.bangbang93.com/maven/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar",  # BMCLAPI镜像
                        f"https://libraries.minecraft.net/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar",  # 官方源
                    ]

                    downloaded = False
                    for url_to_try in candidate_urls:
                        for attempt in range(3): # 尝试3次
                            try:
                                log(f"正在下载库文件 (尝试 {attempt + 1}/3): {url_to_try} -> {lib_path}")
                                response = requests.get(url_to_try, proxies=None, timeout=30)
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
                        from PyQt5.QtWidgets import QProgressBar, QLabel
                        from PyQt5.QtCore import QMetaObject, Qt
                        lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                        if lib_progress_bar:
                            progress_value = int((self.completed_count / self.total_count) * 100)
                            QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                                   __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
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
                        from PyQt5.QtWidgets import QLabel
                        from PyQt5.QtCore import QMetaObject, Qt
                        thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                        if thread_label:
                            QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                   __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(self._active_downloads)))
                    except Exception as e:
                        log(f"更新libraries_file_working_Thread时出错: {e}")
    
    def download_libraries(self, download_dialog=None):
        if download_dialog:
            try:
                from PyQt5.QtWidgets import QProgressBar, QLabel
                from PyQt5.QtCore import QMetaObject, Qt
                lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                if lib_progress_bar:
                    QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(int, 0))
                if thread_label:
                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(str, "0"))
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
            # 这里可以添加更多的错误处理逻辑，例如抛出异常或返回错误状态
            return False

        # 显示完成通知
        if download_dialog:
            try:
                from PyQt5.QtWidgets import QProgressBar, QLabel
                from PyQt5.QtCore import QMetaObject, Qt
                lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                if lib_progress_bar:
                    QMetaObject.invokeMethod(lib_progress_bar, "setValue", Qt.QueuedConnection,
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(int, 100))
                if thread_label:
                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(str, "0"))
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

def InstallMinecraftVersion(version, minecraft_dir=None, download_dialog=None, Fabric_Loader=False):
    """
    安装 Minecraft 版本的主函数，负责创建下载对话框并启动后台安装线程
    
    Args:
        version: 要安装的 Minecraft 版本号，例如 "1.21.8"
        minecraft_dir: Minecraft 安装目录，如果为None则使用默认路径
        download_dialog: 下载对话框实例，如果为None则创建新的对话框
        Fabric_Loader: 是否同时安装 Fabric Loader，默认为 False
    
    Returns:
        None: 此函数立即返回，实际安装工作在后台线程中进行
    """
    # 检查是否需要创建新的下载对话框
    # 如果没有提供下载对话框实例，则创建一个新的对话框
    if download_dialog is None:
        try:
            # 导入PyQt5相关模块用于创建GUI对话框
            from PyQt5.QtWidgets import QDialog
            from PyQt5 import uic
            import json
            
            # 创建新的对话框实例
            download_dialog = QDialog()
            # 从UI文件加载对话框布局
            uic.loadUi("ui/MCVer_downloading.ui", download_dialog)
            
            # 设置对话框标题，包含版本信息和Fabric Loader状态
            title_text = f"正在下载 Minecraft {version}"
            if Fabric_Loader:
                title_text += " 和 Fabric Loader"
            download_dialog.setWindowTitle(title_text)

            # 连接暂停/恢复按钮的点击事件到toggle_pause_download函数
            if hasattr(download_dialog, 'pause_button'):
                download_dialog.pause_button.clicked.connect(lambda: toggle_pause_download(download_dialog))

            # 从配置文件读取并设置最大线程数值
            try:
                # 打开配置文件
                config = cfg.read()
                # 获取最大线程数配置，默认2000
                max_thread_value = config.get("MaxThread", 2000)
                # 如果对话框中有MaxThread相关控件，则设置其值
                if hasattr(download_dialog, 'MaxThread') and hasattr(download_dialog, 'MaxThread_2'):
                    download_dialog.MaxThread.setText(str(max_thread_value))
                    download_dialog.MaxThread_2.setText(str(max_thread_value))
            except Exception as e:
                # 如果读取配置文件失败，记录错误日志但不中断程序
                log(f"设置MaxThread值时出错: {e}")
            
            # 显示下载对话框
            download_dialog.show()
        except Exception as e:
            # 如果创建对话框失败，记录错误日志并将download_dialog设为None
            log(f"创建下载对话框时出错: {e}")
            download_dialog = None
    
    # 创建并启动后台安装线程
    # 使用Thread而不是threading.Thread，因为已经从threading导入了Thread
    from threading import Thread
    # 创建新线程，目标函数为_install_minecraft_version_threaded，传递所有参数
    thread = Thread(target=_install_minecraft_version_threaded, args=(version, minecraft_dir, download_dialog, Fabric_Loader))
    # 启动线程，开始后台安装过程
    thread.start()

def toggle_pause_download(download_dialog):
    """
    切换下载暂停/恢复状态的函数
    
    Args:
        download_dialog: 下载对话框实例，必须包含downloader属性和pause_button控件
    
    Returns:
        None: 此函数直接修改下载器状态和按钮文本，无返回值
    
    功能说明:
        - 检查下载器当前状态
        - 如果已暂停则恢复下载，更新按钮文本为"暂停"
        - 如果正在下载则暂停下载，更新按钮文本为"恢复下载"
    """
    # 检查下载对话框是否存在downloader属性且不为None
    if hasattr(download_dialog, 'downloader') and download_dialog.downloader is not None:
        # 获取下载器实例
        downloader = download_dialog.downloader
        # 检查下载器当前是否处于暂停状态
        if downloader.is_paused:
            # 如果已暂停，则恢复下载
            downloader.resume()
            # 更新暂停按钮文本为"暂停"（表示当前可以暂停）
            download_dialog.pause_button.setText(i18nText("暂停"))
        else:
            # 如果正在下载，则暂停下载
            downloader.pause()
            # 更新暂停按钮文本为"恢复下载"（表示当前可以恢复）
            download_dialog.pause_button.setText(i18nText("恢复下载"))

def _install_minecraft_version_threaded(version, minecraft_dir=None, download_dialog=None, Fabric_Loader=False):
    '''
    下载并安装指定版本的 Minecraft，可选安装 Fabric Loader
    
    Args:
        version (str): 要安装的 Minecraft 版本，例如 "1.21.8"
        minecraft_dir (str, optional): Minecraft 安装目录。如果未提供，默认为 %appdata%/Bloret-Launcher/.minecraft
        download_dialog (QDialog, optional): 下载进度对话框
        Fabric_Loader (bool, optional): 是否安装 Fabric Loader，默认为 False
    
    Returns:
        bool: 安装成功返回True，失败返回False
    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    try:
        # 创建Windows 11通知，通知用户开始安装Minecraft版本
        notify(progress={
            'title': i18nText('Minecraft 版本安装'),  # 通知标题：Minecraft版本安装
            'status': i18nText('正在准备安装...'),   # 通知内容：正在准备安装...
            'value': '0',                             # 进度值：0%
            'valueStringOverride': '0%'              # 进度文本覆盖：0%
        })

        # 0. 如果minecraft_dir未提供，设置默认值
        if minecraft_dir is None:
            # 从环境变量获取APPDATA路径（Windows系统）
            appdata = os.environ.get('APPDATA', '')
            # 构建默认的Minecraft安装目录路径：%appdata%/Bloret-Launcher/.minecraft
            minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')

        # 记录开始安装的日志信息
        log(f"开始安装 Minecraft 版本: {version}，安装目录: {minecraft_dir}")

        # 确保Minecraft安装目录存在，如果不存在则创建
        os.makedirs(minecraft_dir, exist_ok=True)
        # 构建versions目录路径并确保其存在
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)

        # 1. 获取版本清单，使用PCL风格的镜像源处理
        # 更新进度条显示，当前进度10%
        update_progress({
            'value': 0.1,                             # 进度值：10%
            'valueStringOverride': '10%',             # 进度文本：10%
            'status': i18nText('正在获取版本清单...')  # 状态文本：正在获取版本清单...
        })

        # 创建 LibraryDownloader 实例
        # 注意：这里先创建一个空的实例占位，后续步骤中会获取实际的缺失库列表并更新
        # 假设 missing_libraries 在后续步骤中获取
        # 这里先创建一个空的，后续再更新


        
        # 定义版本清单URL列表，使用PCL风格的镜像源处理
        # dl_source_launcher_or_meta_get函数会返回多个镜像源URL，提高下载成功率
        manifest_urls = dl_source_launcher_or_meta_get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
        
        # 初始化版本清单数据变量
        manifest_data = None
        # 遍历所有可用的镜像源URL，尝试获取版本清单
        for url in manifest_urls:
            try:
                # 记录当前尝试的URL日志
                log(f"正在获取版本清单: {url}")
                # 发送HTTP GET请求获取版本清单，不使用代理，超时时间30秒
                response = requests.get(url, proxies=None, timeout=30)
                # 检查HTTP响应状态码
                if response.status_code == 200:
                    # 状态码200表示成功，解析JSON数据
                    manifest_data = response.json()
                    # 成功获取数据后跳出循环
                    break
                else:
                    # 状态码非200，记录警告日志
                    log(f"获取版本清单失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                # 捕获连接错误异常
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议作为备选方案（有些网络环境HTTPS可能被限制）
                try:
                    # 将HTTPS协议替换为HTTP协议
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    # 重新发送HTTP GET请求
                    response = requests.get(http_url, proxies=None, timeout=30)
                    if response.status_code == 200:
                        # HTTP请求成功，解析JSON数据
                        manifest_data = response.json()
                        # 成功获取数据后跳出循环
                        break
                except requests.exceptions.ConnectionError as e2:
                    # HTTP协议也失败，记录警告日志
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                # 捕获其他类型的请求异常
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        # 检查是否成功获取到版本清单数据
        if not manifest_data:
            # 所有URL都获取失败，记录错误日志并返回False
            log("所有版本清单URL都获取失败", logging.ERROR)
            return False

        # 2. 在清单中查找指定版本
        # 更新进度条显示，当前进度20%
        update_progress({
            'value': 0.2,                             # 进度值：20%
            'valueStringOverride': '20%',             # 进度文本：20%
            'status': i18nText('正在查找指定版本...')  # 状态文本：正在查找指定版本...
        })
        
        # 初始化版本信息变量
        version_info = None
        # 遍历版本清单中的所有版本
        for ver in manifest_data.get("versions", []):
            # 检查当前版本的ID是否匹配目标版本
            if ver.get("id") == version:
                # 找到匹配的版本，保存版本信息并跳出循环
                version_info = ver
                break

        # 检查是否找到指定版本
        if not version_info:
            # 未找到指定版本，记录错误日志并返回False
            log(f"未找到版本 {version}", logging.ERROR)
            return False

        # 记录找到的版本信息日志
        log(f"找到版本信息: {version_info}")

        # 3. 获取版本详细信息URL并使用PCL风格的镜像源处理
        # 更新进度条显示，当前进度30%
        update_progress({
            'value': 0.3,                             # 进度值：30%
            'valueStringOverride': '30%',             # 进度文本：30%
            'status': i18nText('正在获取版本详细信息...')  # 状态文本：正在获取版本详细信息...
        })
        
        # 从版本信息中获取原始版本详细信息URL
        original_url = version_info.get("url")
        
        # 使用PCL风格的镜像源处理，获取多个可用的镜像URL
        # dl_source_launcher_or_meta_get函数会将官方URL转换为多个镜像源URL
        version_info_urls = dl_source_launcher_or_meta_get(original_url)

        # 记录正在获取版本详细信息的日志
        log(f"正在获取版本详细信息: {version_info_urls}")
        
        # 初始化版本详细数据变量
        version_data = None
        
        # 遍历所有可用的镜像源URL，尝试获取版本详细信息
        for url in version_info_urls:
            try:
                # 记录当前尝试的URL日志
                log(f"正在获取版本详细信息: {url}")
                # 发送HTTP GET请求获取版本详细信息，超时时间30秒
                response = requests.get(url, timeout=30)
                # 检查HTTP响应状态码
                if response.status_code == 200:
                    # 状态码200表示成功，解析JSON数据
                    version_data = response.json()
                    # 成功获取数据后跳出循环
                    break
                else:
                    # 状态码非200，记录警告日志
                    log(f"获取版本详细信息失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                # 捕获连接错误异常
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议作为备选方案（有些网络环境HTTPS可能被限制）
                try:
                    # 将HTTPS协议替换为HTTP协议
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    # 重新发送HTTP GET请求
                    response = requests.get(http_url, timeout=30)
                    if response.status_code == 200:
                        # HTTP请求成功，解析JSON数据
                        version_data = response.json()
                        # 成功获取数据后跳出循环
                        break
                except requests.exceptions.ConnectionError as e2:
                    # HTTP协议也失败，记录警告日志
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                # 捕获其他类型的请求异常
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        if not version_data:
            log("所有版本详细信息URL都获取失败", logging.ERROR)
            return False

        # 5. 创建版本目录
        # 更新进度条显示，当前进度40%
        update_progress({
            'value': 0.4,                             # 进度值：40%
            'valueStringOverride': '40%',             # 进度文本：40%
            'status': i18nText('正在创建版本目录...')  # 状态文本：正在创建版本目录...
        })
        # 构建当前版本的目录路径：versions/{version}
        version_dir = os.path.join(versions_dir, version)
        # 确保版本目录存在，如果不存在则创建
        os.makedirs(version_dir, exist_ok=True)

        # 保存版本JSON文件到本地，用于后续启动游戏时使用
        version_json_path = os.path.join(version_dir, f"{version}.json")
        # 以UTF-8编码写入JSON文件，禁用ASCII编码确保中文字符正确处理，使用4空格缩进格式化
        with open(version_json_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=4)

        # 记录成功保存版本JSON文件的日志
        log(f"已保存版本JSON文件: {version_json_path}")

        # 设置 First_Step_CheckBox 为 true，表示第一步（版本信息获取）已完成
        if download_dialog:
            try:
                # 导入PyQt5相关模块用于UI更新
                from PyQt5.QtWidgets import QCheckBox
                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                from PyQt5.QtCore import QMetaObject, Qt
                # 查找对话框中的First_Step_CheckBox控件
                checkbox = download_dialog.findChild(QCheckBox, "First_Step_CheckBox")
                if checkbox:
                    # 使用invokeMethod在Qt主线程中设置复选框为选中状态
                    QMetaObject.invokeMethod(checkbox, "setChecked", Qt.QueuedConnection, 
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(bool, True))
            except Exception as e:
                # 如果设置复选框失败，记录错误日志但不中断程序
                log(f"设置First_Step_CheckBox时出错: {e}")

        # 下载客户端JAR文件，使用PCL风格的镜像源处理
        # 更新进度条显示，当前进度50%
        update_progress({
            'value': 0.5,                             # 进度值：50%
            'valueStringOverride': '50%',             # 进度文本：50%
            'status': i18nText('正在下载客户端JAR文件...')  # 状态文本：正在下载客户端JAR文件...
        })
        # 检查版本数据中是否包含客户端下载信息
        if "downloads" in version_data and "client" in version_data["downloads"]:
            # 获取客户端JAR文件的下载信息
            client_info = version_data["downloads"]["client"]
            # 获取客户端JAR文件的下载URL
            client_url = client_info["url"]
            
            # 使用PCL风格的镜像源处理，获取多个可用的镜像URL
            client_urls = dl_source_launcher_or_meta_get(client_url)

            # 构建客户端JAR文件的本地保存路径
            client_jar_path = os.path.join(version_dir, f"{version}.jar")
            # 记录开始下载客户端JAR文件的日志
            log(f"正在下载客户端JAR文件: {client_urls}")

            # 初始化下载成功标志为False
            download_success = False
            # 遍历所有可用的镜像源URL，尝试下载客户端JAR文件
            for url in client_urls:
                try:
                    # 记录当前尝试下载的URL日志
                    log(f"正在下载客户端JAR文件: {url}")
                    # 使用Session来更好地管理连接，提高下载稳定性和性能
                    with requests.Session() as session:
                        # 发送HTTP GET请求，启用流式下载以处理大文件
                        response = session.get(url, stream=True, timeout=30)
                        # 检查HTTP响应状态码
                        if response.status_code == 200:
                            # 获取文件总大小，用于进度计算
                            total_size = int(response.headers.get('content-length', 0))
                            # 初始化已下载大小计数器
                            downloaded_size = 0
                            
                            # 以二进制写入模式打开本地文件
                            with open(client_jar_path, 'wb') as f:
                                # 以8KB为单位分块读取和写入，避免内存占用过大
                                for chunk in response.iter_content(chunk_size=8192):
                                    # 检查是否有数据块
                                    if chunk:
                                        # 将数据块写入本地文件
                                        f.write(chunk)
                                        # 累加已下载大小
                                        downloaded_size += len(chunk)
                                        
                                        # 更新客户端JAR进度条显示
                                        if download_dialog and total_size > 0:
                                            try:
                                                # 导入PyQt5进度条控件
                                                from PyQt5.QtWidgets import QProgressBar
                                                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                from PyQt5.QtCore import QMetaObject, Qt
                                                # 查找对话框中的客户端JAR进度条控件
                                                progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                if progress_bar:
                                                    # 计算进度百分比
                                                    progress_value = int((downloaded_size / total_size) * 100)
                                                    # 使用invokeMethod在Qt主线程中更新进度条
                                                    QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                            except Exception as e:
                                                # 如果更新进度条失败，记录错误日志但不中断下载
                                                log(f"更新client_jar_progress时出错: {e}")
                            
                            # 记录客户端JAR文件下载成功的日志
                            log(f"已下载客户端JAR文件: {client_jar_path}")
                            # 设置下载成功标志为True
                            download_success = True
                            # 成功下载后跳出循环，不再尝试其他镜像源
                            break
                        else:
                            # 记录下载失败的状态码和URL，使用WARNING级别日志
                            log(f"下载客户端JAR文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            # 特殊处理403错误（访问被拒绝）
                            if response.status_code == 403:
                                # 尝试使用原始URL（可能是官方源）绕过403限制
                                original_url = client_info["url"]
                                log(f"尝试使用原始URL: {original_url}")
                                # 使用原始URL重新尝试下载
                                with requests.Session() as session:
                                    # 发送HTTP GET请求到原始URL
                                    response = session.get(original_url, stream=True, timeout=30)
                                    # 检查HTTP响应状态码
                                    if response.status_code == 200:
                                        # 获取文件总大小，用于进度计算
                                        total_size = int(response.headers.get('content-length', 0))
                                        # 初始化已下载大小计数器
                                        downloaded_size = 0
                                        
                                        # 以二进制写入模式打开本地文件
                                        with open(client_jar_path, 'wb') as f:
                                            # 以8KB为单位分块读取和写入，避免内存占用过大
                                            for chunk in response.iter_content(chunk_size=8192):
                                                # 检查是否有数据块
                                                if chunk:
                                                    # 将数据块写入本地文件
                                                    f.write(chunk)
                                                    # 累加已下载大小
                                                    downloaded_size += len(chunk)
                                                    
                                                    # 更新客户端JAR进度条显示
                                                    if download_dialog and total_size > 0:
                                                        try:
                                                            # 导入PyQt5进度条控件
                                                            from PyQt5.QtWidgets import QProgressBar
                                                            # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                            from PyQt5.QtCore import QMetaObject, Qt
                                                            # 查找对话框中的客户端JAR进度条控件
                                                            progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                            if progress_bar:
                                                                # 计算进度百分比
                                                                progress_value = int((downloaded_size / total_size) * 100)
                                                                # 使用invokeMethod在Qt主线程中更新进度条
                                                                QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                                       __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                                        except Exception as e:
                                                            # 如果更新进度条失败，记录错误日志但不中断下载
                                                            log(f"更新client_jar_progress时出错: {e}")
                                        
                                        # 记录使用原始URL成功下载的日志
                                        log(f"已下载客户端JAR文件: {client_jar_path}")
                                        # 设置下载成功标志为True
                                        download_success = True
                                        # 成功下载后跳出循环
                                        break
                except requests.exceptions.ConnectionError as e:
                    # 捕获网络连接错误异常，使用WARNING级别记录日志
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议降级，绕过可能的HTTPS证书或网络问题
                    try:
                        # 将HTTPS URL替换为HTTP URL
                        http_url = url.replace("https://", "http://")
                        # 记录尝试HTTP协议的日志
                        log(f"尝试使用HTTP协议: {http_url}")
                        # 使用HTTP URL重新尝试下载
                        with requests.Session() as session:
                            # 发送HTTP GET请求到HTTP版本的URL
                            response = session.get(http_url, stream=True, timeout=30)
                            # 检查HTTP响应状态码
                            if response.status_code == 200:
                                # 获取文件总大小，用于进度计算
                                total_size = int(response.headers.get('content-length', 0))
                                # 初始化已下载大小计数器
                                downloaded_size = 0
                                
                                # 以二进制写入模式打开本地文件
                                with open(client_jar_path, 'wb') as f:
                                    # 以8KB为单位分块读取和写入，避免内存占用过大
                                    for chunk in response.iter_content(chunk_size=8192):
                                        # 检查是否有数据块
                                        if chunk:
                                            # 将数据块写入本地文件
                                            f.write(chunk)
                                            # 累加已下载大小
                                            downloaded_size += len(chunk)
                                            
                                            # 更新客户端JAR进度条显示
                                            if download_dialog and total_size > 0:
                                                try:
                                                    # 导入PyQt5进度条控件
                                                    from PyQt5.QtWidgets import QProgressBar
                                                    # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                    from PyQt5.QtCore import QMetaObject, Qt
                                                    # 查找对话框中的客户端JAR进度条控件
                                                    progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                    if progress_bar:
                                                        # 计算进度百分比
                                                        progress_value = int((downloaded_size / total_size) * 100)
                                                        # 使用invokeMethod在Qt主线程中更新进度条
                                                        QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                               __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                                except Exception as e:
                                                    # 如果更新进度条失败，记录错误日志但不中断下载
                                                    log(f"更新client_jar_progress时出错: {e}")
                                
                                # 记录使用HTTP协议成功下载的日志
                                log(f"已下载客户端JAR文件: {client_jar_path}")
                                # 设置下载成功标志为True
                                download_success = True
                                # 成功下载后跳出循环
                                break
                    except requests.exceptions.ConnectionError as e2:
                        # HTTP协议也失败，记录错误日志并继续尝试其他镜像源
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    # 捕获其他类型的requests异常，使用WARNING级别记录日志
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            # 检查客户端JAR文件是否下载成功
            if not download_success:
                # 所有镜像源都下载失败，记录ERROR级别日志
                log("所有客户端JAR文件URL都下载失败", logging.ERROR)
                # 返回False表示安装失败
                return False
        else:
            # 版本信息中未找到客户端下载链接，使用i18n本地化文本记录ERROR级别日志
            log(i18nText("版本信息中未找到客户端下载链接"), logging.ERROR)
            # 返回False表示安装失败
            return False

        # 加载配置文件config.json，获取下载线程数等配置
        config = cfg.read()
        # 从配置中获取最大线程数，默认值为2000
        max_thread_value = config.get("MaxThread", 2000)
        # 处理主版本库文件，准备下载Minecraft依赖的库文件
        processed_libraries = []
        # 检查版本数据中是否包含库文件列表
        if "libraries" in version_data:
            # 遍历所有库文件定义
            for lib in version_data["libraries"]:
                # 检查库文件定义中是否包含名称字段
                if "name" in lib:
                    # 解析库文件名称格式（group:artifact:version）
                    parts = lib["name"].split(":")
                    # 检查名称格式是否正确（应该包含3个部分）
                    if len(parts) == 3:
                        # 提取组织ID，将点号替换为斜杠（Maven目录结构）
                        group = parts[0].replace(".", "/")
                        # 提取构件ID
                        artifact = parts[1]
                        # 提取版本号
                        version_lib = parts[2]
                        # 构建库文件名称（artifact-version.jar）
                        lib_filename = f"{artifact}-{version_lib}.jar"
                        # 构建完整的库文件路径（按照Maven目录结构）
                        lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                        # 将库文件定义和路径添加到处理列表中
                        processed_libraries.append((lib, lib_path))
                    else:
                        # 库文件名称格式不正确，记录WARNING级别日志
                        log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                else:
                    # 库文件定义缺少名称字段，记录WARNING级别日志
                    log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

        # 如果存在处理后的库文件列表且下载对话框已创建，则创建LibraryDownloader实例
        if download_dialog is not None and processed_libraries:
            # 创建LibraryDownloader实例，用于多线程下载库文件
            # max_workers参数控制最大并发下载线程数
            download_dialog.downloader = LibraryDownloader(processed_libraries, max_workers=max_thread_value)

        # 创建natives目录，用于存放本地库文件（平台相关的动态链接库）
        natives_dir = os.path.join(version_dir, f"{version}-natives")
        # 使用exist_ok=True参数，如果目录已存在则不会抛出异常
        os.makedirs(natives_dir, exist_ok=True)

        # 更新进度条状态，开始下载库文件阶段
        update_progress({
            'value': 0.6,  # 设置进度值为60%
            'valueStringOverride': '60%',  # 覆盖进度条文本显示
            'status': i18nText('正在下载库文件...')  # 设置状态文本，使用i18n本地化
        })
        # 构建库文件根目录路径
        libraries_dir = os.path.join(minecraft_dir, "libraries")
        # 确保库文件目录存在，如果不存在则创建
        os.makedirs(libraries_dir, exist_ok=True)

        # 如果下载对话框和下载器实例都存在，则开始下载库文件
        if download_dialog is not None and download_dialog.downloader is not None:
            # 调用LibraryDownloader的download_libraries方法开始多线程下载
            download_dialog.downloader.download_libraries(download_dialog)
        
        # 检查版本数据中是否包含资源索引信息
        if "assetIndex" in version_data:
            # 提取资源索引数据
            asset_index = version_data["assetIndex"]
            # 获取资源索引的下载URL
            asset_index_url = asset_index["url"]
            
            # 使用PCL风格的镜像源处理，获取多个镜像源URL列表
            asset_index_urls = dl_source_launcher_or_meta_get(asset_index_url)
            
            # 构建资源文件相关目录路径
            assets_dir = os.path.join(minecraft_dir, "assets")  # 资源根目录
            indexes_dir = os.path.join(assets_dir, "indexes")    # 索引文件目录
            objects_dir = os.path.join(assets_dir, "objects")  # 资源对象目录
            
            # 确保索引目录和对象目录存在
            os.makedirs(indexes_dir, exist_ok=True)
            os.makedirs(objects_dir, exist_ok=True)
            
            # 提取资源索引ID，用于构建本地文件路径
            asset_index_id = asset_index["id"]
            # 构建资源索引文件的完整路径
            asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")
            
            # 更新进度条状态，开始下载资源索引
            update_progress({'status': i18nText("正在下载资源索引...")})
            # 记录资源索引下载日志，包含所有镜像源URL
            log(f"正在下载资源索引: {asset_index_urls}")
            
            # 初始化下载成功标志为False
            download_success = False
            # 遍历所有镜像源URL，尝试下载资源索引
            for url in asset_index_urls:
                try:
                    # 记录当前尝试下载的URL日志
                    log(f"正在下载资源索引: {url}")
                    # 发送HTTP GET请求下载资源索引
                    response = requests.get(url, timeout=30)
                    # 检查HTTP响应状态码
                    if response.status_code == 200:
                        # 以二进制写入模式打开本地文件
                        with open(asset_index_path, 'wb') as f:
                            # 将下载的内容写入本地文件
                            f.write(response.content)
                        # 记录资源索引下载成功的日志
                        log(f"已下载资源索引: {asset_index_path}")
                        # 设置下载成功标志为True
                        download_success = True
                        # 成功下载后跳出循环
                        break
                    else:
                        # 下载失败，记录WARNING级别日志
                        log(f"下载资源索引失败: {url}, HTTP {response.status_code}", logging.WARNING)
                except requests.exceptions.ConnectionError as e:
                    # 捕获网络连接错误异常，使用WARNING级别记录日志
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议降级，绕过可能的HTTPS证书或网络问题
                    try:
                        # 将HTTPS URL替换为HTTP URL
                        http_url = url.replace("https://", "http://")
                        # 记录尝试HTTP协议的日志
                        log(f"尝试使用HTTP协议: {http_url}")
                        # 发送HTTP GET请求到HTTP版本的URL
                        response = requests.get(http_url, timeout=30)
                        # 检查HTTP响应状态码
                        if response.status_code == 200:
                            # 以二进制写入模式打开本地文件
                            with open(asset_index_path, 'wb') as f:
                                # 将下载的内容写入本地文件
                                f.write(response.content)
                            # 记录使用HTTP协议成功下载的日志
                            log(f"已下载资源索引: {asset_index_path}")
                            # 设置下载成功标志为True
                            download_success = True
                            # 成功下载后跳出循环
                            break
                    except requests.exceptions.ConnectionError as e2:
                        # HTTP协议也失败，记录错误日志并继续尝试其他镜像源
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    # 捕获其他类型的requests异常，使用WARNING级别记录日志
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            # 检查资源索引是否下载成功
            if not download_success:
                # 所有镜像源都下载失败，记录ERROR级别日志
                log("所有资源索引URL都下载失败", logging.ERROR)
                # 返回False表示安装失败
                return False
                
            # 读取资源索引文件，获取资源文件列表和哈希信息
            with open(asset_index_path, 'r', encoding='utf-8') as f:
                # 使用UTF-8编码读取JSON格式的资源索引文件
                asset_index_data = json.load(f)
            
            # 检查资源索引数据中是否包含资源对象信息
            if "objects" in asset_index_data:
                # 统计资源文件总数
                assets_count = len(asset_index_data['objects'])
                # 更新进度条状态，显示资源文件总数
                update_progress({'status': f"开始下载资源文件，共 {assets_count} 个..."})
                # 记录资源文件下载开始的日志
                log(f"开始下载资源文件，共 {assets_count} 个")
                
                # 使用线程池进行多线程下载，提高下载效率
                from concurrent.futures import ThreadPoolExecutor
                
                # 设置最大线程数，根据系统资源限制调整默认值
                try:
                    # 尝试读取配置文件获取最大线程数设置
                    with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                        # 使用UTF-8编码读取JSON配置文件
                        config_data = json.load(f)
                    # 从配置中获取MaxThread值，默认使用64个线程
                    max_workers = config_data.get("MaxThread", 64)
                except Exception:
                    # 如果读取配置文件失败，捕获异常信息
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    # 调用异常处理函数记录错误信息
                    handle_exception(exc_type, exc_value, exc_traceback)
                    # 读取失败时使用默认值64个线程
                    max_workers = 64
                # 记录使用的线程数日志
                log(f"使用 {max_workers} 个线程下载资源文件")
                
                # 用于跟踪活动下载线程数的变量
                active_downloads = 0
                # 创建线程锁，确保线程安全地更新活动下载计数
                active_downloads_lock = threading.Lock()
                
                # 创建多线程下载资源文件函数
                def download_asset(asset_name, asset_info):
                    # 增加活动下载计数，使用nonlocal访问外部变量
                    nonlocal active_downloads
                    # 使用线程锁确保线程安全
                    with active_downloads_lock:
                        # 增加活动下载计数
                        active_downloads += 1
                        # 更新活动线程数显示（在UI中显示当前活动线程数）
                        if download_dialog:
                            try:
                                # 导入PyQt5标签控件
                                from PyQt5.QtWidgets import QLabel
                                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                from PyQt5.QtCore import QMetaObject, Qt
                                # 查找对话框中的活动线程数标签控件
                                thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                if thread_label:
                                    # 使用invokeMethod在Qt主线程中更新标签文本
                                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                            except Exception as e:
                                # 如果更新UI失败，记录错误日志但不中断下载
                                log(f"更新Resources_file_working_Thread时出错: {e}")
                    
                    try:
                        # 提取资源文件的哈希值，用于验证文件完整性
                        hash_value = asset_info["hash"]
                        # 提取哈希值的前两个字符，用于构建目录结构（Minecraft资源文件按哈希前缀分目录存储）
                        hash_prefix = hash_value[:2]
                        # 构建资源文件的完整路径（objects/hash_prefix/hash_value）
                        object_path = os.path.join(objects_dir, hash_prefix, hash_value)
                        
                        # 检查文件是否已存在且大小正确，避免重复下载
                        if os.path.exists(object_path) and os.path.getsize(object_path) == asset_info["size"]:
                            # 文件已存在且大小正确，直接返回成功
                            return True
                        
                        # 创建目录结构（如果不存在则创建）
                        os.makedirs(os.path.dirname(object_path), exist_ok=True)
                        
                        # 构建资源文件URL，使用官方URL格式
                        asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{hash_value}"
                        # 使用PCL风格的镜像源处理，获取多个镜像源URL列表
                        asset_urls = dl_source_assets_get(asset_url)
                        
                        # 初始化下载成功标志为False
                        download_success = False
                        # 遍历所有镜像源URL，尝试下载资源文件
                        for url in asset_urls:
                            try:
                                # 记录当前尝试下载的URL日志
                                log(f"正在下载资源文件: {url}")
                                # 使用requests.Session()来更好地管理连接，提高下载稳定性
                                with requests.Session() as session:
                                    # 发送HTTP GET请求，启用流式下载以处理大文件
                                    response = session.get(url, stream=True, timeout=30)
                                    # 检查HTTP响应状态码
                                    if response.status_code == 200:
                                        # 以二进制写入模式打开本地文件
                                        with open(object_path, 'wb') as f:
                                            # 使用固定大小的块（8KB）进行流式写入，避免内存占用过高
                                            for chunk in response.iter_content(chunk_size=8192):
                                                # 检查是否有数据块
                                                if chunk:
                                                    # 将数据块写入本地文件
                                                    f.write(chunk)
                                        # 设置下载成功标志为True
                                        download_success = True
                                        # 成功下载后跳出循环
                                        break
                                    else:
                                        # 下载失败，记录WARNING级别日志
                                        log(f"下载资源文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            except requests.exceptions.ConnectionError as e:
                                # 捕获网络连接错误异常，使用WARNING级别记录日志
                                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                                # 尝试使用HTTP协议降级，绕过可能的HTTPS证书或网络问题
                                try:
                                    # 将HTTPS URL替换为HTTP URL
                                    http_url = url.replace("https://", "http://")
                                    # 记录尝试HTTP协议的日志
                                    log(f"尝试使用HTTP协议: {http_url}")
                                    # 使用HTTP URL重新尝试下载
                                    with requests.Session() as session:
                                        # 发送HTTP GET请求到HTTP版本的URL
                                        response = session.get(http_url, stream=True, timeout=30)
                                        # 检查HTTP响应状态码
                                        if response.status_code == 200:
                                            # 以二进制写入模式打开本地文件
                                            with open(object_path, 'wb') as f:
                                                # 以8KB为单位分块读取和写入，避免内存占用过大
                                                for chunk in response.iter_content(chunk_size=8192):
                                                    # 检查是否有数据块
                                                    if chunk:
                                                        # 将数据块写入本地文件
                                                        f.write(chunk)
                                            # 设置下载成功标志为True
                                            download_success = True
                                            # 成功下载后跳出循环
                                            break
                                except requests.exceptions.ConnectionError as e2:
                                    # HTTP协议也失败，记录错误日志并继续尝试其他镜像源
                                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                            except requests.exceptions.RequestException as e:
                                # 捕获其他类型的requests异常，使用WARNING级别记录日志
                                log(f"下载资源文件时发生网络请求错误: {asset_name}, {url}, {e}", logging.WARNING)
                        
                        # 检查资源文件是否下载成功
                        if not download_success:
                            # 所有镜像源都下载失败，记录WARNING级别日志
                            log(f"所有资源文件URL都下载失败: {asset_name}", logging.WARNING)
                            # 返回False表示下载失败
                            return False
                        
                        # 资源文件下载成功，返回True
                        return True
                    except Exception:
                        # 捕获所有其他异常，使用异常处理函数记录错误信息
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        # 调用异常处理函数记录详细的异常信息
                        handle_exception(exc_type, exc_value, exc_traceback)
                        # 返回False表示下载失败
                        return False
                    finally:
                        # 减少活动下载计数（无论成功还是失败都要执行）
                        with active_downloads_lock:
                            # 减少活动下载计数
                            active_downloads -= 1
                            # 更新活动线程数显示（在UI中显示当前活动线程数）
                            if download_dialog:
                                try:
                                    # 导入PyQt5标签控件
                                    from PyQt5.QtWidgets import QLabel
                                    # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                    from PyQt5.QtCore import QMetaObject, Qt
                                    # 查找对话框中的活动线程数标签控件
                                    thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                    if thread_label:
                                        # 使用invokeMethod在Qt主线程中更新标签文本
                                        QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                                __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                                except Exception as e:
                                    # 如果更新UI失败，记录错误日志但不中断下载
                                    log(f"更新Resources_file_working_Thread时出错: {e}")
                
                # 创建Windows 11通知
                # 使用notify函数创建系统通知，显示下载开始信息
                notify(progress={
                    'title': i18nText('Minecraft 资源下载'),  # 使用国际化文本作为标题
                    'status': i18nText('正在下载资源文件...'),  # 使用国际化文本作为状态描述
                    'value': '0',  # 初始进度值为0
                    'valueStringOverride': f'0/{assets_count} 个'  # 自定义进度文本显示
                })
                
                # 创建线程池
                # 使用ThreadPoolExecutor创建线程池，设置最大线程数和线程名称前缀
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AssetsDownloader") as executor:
                    # 提交所有下载任务到线程池
                    # 使用字典推导式创建future到资源名称的映射，便于后续结果处理
                    future_to_asset = {executor.submit(download_asset, asset_name, asset_info): asset_name 
                                      for asset_name, asset_info in asset_index_data["objects"].items()}
                    
                    # 处理完成的任务（按完成顺序处理）
                    success_count = 0  # 初始化成功下载计数器
                    failed_count = 0   # 初始化失败下载计数器
                    completed_count = 0  # 初始化完成计数器（无论成功失败）
                    
                    # 使用concurrent.futures.as_completed按任务完成顺序处理结果
                    for future in concurrent.futures.as_completed(future_to_asset):
                        # 获取当前future对应的资源名称
                        asset_name = future_to_asset[future]
                        try:
                            # 获取任务执行结果（True表示下载成功，False表示失败）
                            success = future.result()
                            if success:
                                # 下载成功，增加成功计数器
                                success_count += 1
                            else:
                                # 下载失败，增加失败计数器
                                failed_count += 1
                        except Exception as e:
                            # 捕获future.result()的异常，增加失败计数器
                            failed_count += 1
                            # 记录处理资源文件时的错误日志，使用WARNING级别
                            log(f"处理资源文件时发生错误: {asset_name}, {str(e)}", logging.WARNING)
                        finally:
                            # 无论成功失败，都增加完成计数器
                            completed_count += 1
                        
                        # 每10%更新一次UI，避免频繁更新
                        current_progress = int((completed_count / assets_count) * 100)
                        last_progress = int(((completed_count - 1) / assets_count) * 100) if completed_count > 0 else 0
                        
                        # 当进度达到10%的倍数时更新UI，只更新进度条，不发送通知
                        if current_progress // 10 > last_progress // 10 or completed_count == assets_count:
                            # 更新资源文件下载进度条和线程数显示（在UI中安全更新）
                            if download_dialog:
                                try:
                                    # 导入PyQt5控件
                                    from PyQt5.QtWidgets import QProgressBar, QLabel
                                    # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                    from PyQt5.QtCore import QMetaObject, Qt
                                    
                                    # 更新进度条显示
                                    resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                                    if resources_progress_bar:
                                        # 使用invokeMethod在Qt主线程中更新进度条值
                                        QMetaObject.invokeMethod(resources_progress_bar, "setValue", Qt.QueuedConnection,
                                                               __import__('PyQt5.QtCore').QtCore.Q_ARG(int, current_progress))
                                        log(f"资源文件下载进度: {current_progress}% ({completed_count}/{assets_count})")
                                    
                                    # 更新活动线程数显示
                                    thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                    if thread_label:
                                        # 使用invokeMethod在Qt主线程中更新活动线程数文本
                                        QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                               __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                                except Exception as e:
                                    # 如果更新UI失败，记录错误日志但不中断下载
                                    log(f"更新资源文件进度时出错: {e}")
                    
                    # 等待所有任务完成（设置60秒超时）
                    try:
                        # 使用concurrent.futures.wait等待所有future完成
                        concurrent.futures.wait(future_to_asset, timeout=60)
                    except Exception as e:
                        # 如果等待超时或出错，记录错误日志
                        log(f"等待资源文件下载完成时出错: {e}")
                
                # 下载完成时更新UI到100%
                if download_dialog:
                    try:
                        from PyQt5.QtWidgets import QProgressBar
                        from PyQt5.QtCore import QMetaObject, Qt
                        
                        resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                        if resources_progress_bar:
                            QMetaObject.invokeMethod(resources_progress_bar, "setValue", Qt.QueuedConnection,
                                                   __import__('PyQt5.QtCore').QtCore.Q_ARG(int, 100))
                            log(f"资源文件下载完成，设置进度条为100%")
                    except Exception as e:
                        log(f"更新资源文件完成进度时出错: {e}")
                
                # 输出下载结果日志
                log(f"资源文件下载完成: 成功 {success_count} 个, 失败 {failed_count} 个")
                
                # 如果有失败的资源文件，记录警告日志
                if failed_count > 0:
                    # 记录WARNING级别日志，说明失败数量但不影响游戏运行
                    log(f"有 {failed_count} 个资源文件下载失败，但不影响游戏运行", logging.WARNING)
        
        # 如果需要安装Fabric Loader
        if Fabric_Loader:
            # 记录开始安装Fabric Loader的日志
            log(f"开始安装 Fabric Loader 到 Minecraft {version}")
            # 更新进度条显示，显示正在安装Fabric Loader
            update_progress({
                'status': f'正在安装 Fabric Loader...',  # 状态描述
                'value': 0.9,  # 进度值设置为90%
                'valueStringOverride': '90%'  # 自定义进度文本显示
            })
            
            # 获取最新的Fabric Loader版本
            try:
                # 构建Fabric Loader版本列表API URL
                fabric_api_url = "https://meta.fabricmc.net/v2/versions/loader/" + version
                # 记录正在获取版本列表的日志
                log(f"正在获取Fabric Loader版本列表: {fabric_api_url}")
                
                # 发送HTTP GET请求获取版本列表，设置30秒超时
                fabric_response = requests.get(fabric_api_url, timeout=30)
                # 检查HTTP响应状态码
                if fabric_response.status_code != 200:
                    # 如果状态码不是200，记录ERROR级别日志并抛出异常
                    log(f"获取Fabric Loader版本列表失败: HTTP {fabric_response.status_code}", logging.ERROR)
                    # 抛出异常，中断安装流程
                    raise Exception(f"获取Fabric Loader版本列表失败: HTTP {fabric_response.status_code}")
                
                # 解析JSON响应数据
                fabric_versions = fabric_response.json()
                # 检查是否获取到版本数据
                if not fabric_versions:
                    # 如果没有找到版本，记录ERROR级别日志并抛出异常
                    log(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本", logging.ERROR)
                    # 抛出异常，中断安装流程
                    raise Exception(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本")
                
                # 获取最新版本（数组第一个元素通常是最新的）
                latest_fabric = fabric_versions[0]
                # 提取loader版本号
                loader_version = latest_fabric["loader"]["version"]
                # 记录找到的版本信息
                log(f"找到最新的 Fabric Loader 版本: {loader_version}")
                
                # 使用PCL风格的版本命名格式（空格分隔）
                fabric_version_id = f"{version}-Fabric {loader_version}"
                # 构建Fabric版本目录路径
                fabric_version_dir = os.path.join(versions_dir, fabric_version_id)
                # 创建版本目录（如果不存在则创建）
                os.makedirs(fabric_version_dir, exist_ok=True)
                
                # 获取Fabric安装JSON文件
                fabric_json_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader_version}/profile/json"
                # 记录正在获取安装JSON的日志
                log(f"正在获取Fabric安装JSON: {fabric_json_url}")

                # 发送HTTP GET请求获取安装JSON，设置30秒超时
                fabric_json_response = requests.get(fabric_json_url, timeout=30)
                # 检查HTTP响应状态码
                if fabric_json_response.status_code != 200:
                    # 如果状态码不是200，记录ERROR级别日志并抛出异常
                    log(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}", logging.ERROR)
                    # 抛出异常，中断安装流程
                    raise Exception(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}")

                # 解析JSON响应数据
                fabric_json_data = fabric_json_response.json()
                
                # 获取原版版本JSON以合并库文件和资源信息
                original_version_json_path = os.path.join(version_dir, f"{version}.json")
                if os.path.exists(original_version_json_path):
                    with open(original_version_json_path, 'r', encoding='utf-8') as f:
                        original_json = json.load(f)
                    
                    # 合并原版库文件到Fabric JSON
                    original_libraries = original_json.get("libraries", [])
                    fabric_libraries = fabric_json_data.get("libraries", [])
                    
                    # 合并库文件并去重（基于name字段）
                    merged_libraries = fabric_libraries.copy()
                    existing_names = {lib.get("name") for lib in fabric_libraries if "name" in lib}
                    
                    for lib in original_libraries:
                        lib_name = lib.get("name")
                        if lib_name and lib_name not in existing_names:
                            merged_libraries.append(lib)
                    
                    # 更新合并后的库文件列表
                    fabric_json_data["libraries"] = merged_libraries
                    
                    # 合并资源文件信息
                    if "assetIndex" in original_json:
                        fabric_json_data["assetIndex"] = original_json["assetIndex"]
                    if "assets" in original_json:
                        fabric_json_data["assets"] = original_json["assets"]
                    if "downloads" in original_json and "client" in original_json["downloads"]:
                        fabric_json_data["downloads"] = {"client": original_json["downloads"]["client"]}
                
                # 删除inheritsFrom和jar字段，使用直接包含的方式
                fabric_json_data.pop("inheritsFrom", None)
                fabric_json_data.pop("jar", None)
                
                # 设置版本ID
                fabric_json_data["id"] = fabric_version_id
                
                # 构建Fabric版本JSON文件路径
                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                # 以UTF-8编码写入JSON文件，使用ensure_ascii=False保持Unicode字符，indent=4格式化输出
                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json_data, f, ensure_ascii=False, indent=4)
                # 记录保存JSON文件成功的日志
                log(f"已保存Fabric安装JSON: {fabric_json_path}")

                # 下载Fabric Loader所需的库文件
                update_progress({
                    'status': f'正在下载 Fabric Loader 库文件...',  # 状态描述
                    'value': 0.92,  # 进度值设置为92%
                    'valueStringOverride': '92%'  # 自定义进度文本显示
                })
                # 记录开始下载库文件的日志
                log(f"开始下载 Fabric Loader 库文件...")

                # 从安装JSON中提取库文件列表
                fabric_libraries = fabric_json_data.get("libraries", [])
                
                # 处理库文件列表，提取库文件信息并构建下载路径
                processed_fabric_libraries = []
                # 遍历所有库文件
                for lib in fabric_libraries:
                    # 检查库文件是否有name字段
                    if "name" in lib:
                        # 按冒号分割库文件名称（格式：group:artifact:version）
                        parts = lib["name"].split(":")
                        # 检查格式是否正确（应该有3个部分）
                        if len(parts) == 3:
                            # 提取group部分，将点号替换为斜杠（Maven目录结构）
                            group = parts[0].replace(".", "/")
                            # 提取artifact部分
                            artifact = parts[1]
                            # 提取版本号部分
                            version_lib = parts[2]
                            # 构建JAR文件名
                            lib_filename = f"{artifact}-{version_lib}.jar"
                            # 构建完整的库文件路径（遵循Maven目录结构）
                            lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                            # 将库文件信息和路径添加到处理列表
                            processed_fabric_libraries.append((lib, lib_path))
                        else:
                            # 如果格式不正确，记录WARNING级别日志
                            log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                    else:
                        # 如果缺少name字段，记录WARNING级别日志
                        log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

                # 检查是否有需要下载的库文件
                if processed_fabric_libraries:
                    # 创建LibraryDownloader实例，传入库文件列表和最大线程数
                    library_downloader = LibraryDownloader(
                        processed_fabric_libraries,  # 库文件列表
                        max_workers=max_thread_value  # 使用配置的最大线程数
                    )
                    # 调用download_libraries方法下载库文件
                    if not library_downloader.download_libraries(download_dialog=download_dialog):
                        # 如果下载失败，记录ERROR级别日志并抛出异常
                        log("Fabric Loader 库文件下载失败", logging.ERROR)
                        # 抛出异常，中断安装流程
                        raise Exception("Fabric Loader 库文件下载失败")
                    # 记录库文件下载完成的日志
                    log("Fabric Loader 库文件下载完成")
                else:
                    # 如果没有找到库文件，记录WARNING级别日志
                    log("未找到 Fabric Loader 库文件", logging.WARNING)

                # 下载客户端JAR文件
                update_progress({
                    'status': f'正在下载 Fabric 客户端 JAR...',  # 状态描述
                    'value': 0.92,  # 进度值设置为92%
                    'valueStringOverride': '92%'  # 自定义进度文本显示
                })
                
                # 处理客户端JAR文件
                client_jar_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.jar")
                
                # 优先尝试下载原版客户端JAR
                if "downloads" in fabric_json_data and "client" in fabric_json_data["downloads"]:
                    client_download_info = fabric_json_data["downloads"]["client"]
                    client_url = client_download_info.get("url")
                    client_size = client_download_info.get("size", 0)
                    client_sha1 = client_download_info.get("sha1", "")
                    
                    if client_url:
                        log(f"正在下载客户端JAR: {client_url}")
                        try:
                            # 使用镜像源下载客户端JAR
                            mirror_urls = dl_source_launcher_or_meta_get(client_url)
                            for url in mirror_urls:
                                try:
                                    download_file(url, client_jar_path)
                                    # 验证文件大小
                                    if os.path.exists(client_jar_path) and os.path.getsize(client_jar_path) == client_size:
                                        log(f"客户端JAR下载成功: {client_jar_path}")
                                        break
                                except Exception as e:
                                    log(f"从 {url} 下载客户端JAR失败: {e}", logging.WARNING)
                                    continue
                            else:
                                # 如果所有镜像源都失败，尝试从原版复制
                                original_jar_path = os.path.join(version_dir, f"{version}.jar")
                                if os.path.exists(original_jar_path):
                                    shutil.copy(original_jar_path, client_jar_path)
                                    log(f"从原版复制客户端JAR: {original_jar_path} -> {client_jar_path}")
                                else:
                                    log(f"无法获取客户端JAR文件", logging.ERROR)
                        except Exception as e:
                            log(f"下载客户端JAR失败: {e}", logging.ERROR)
                else:
                    # 如果没有下载信息，尝试从原版复制
                    original_jar_path = os.path.join(version_dir, f"{version}.jar")
                    if os.path.exists(original_jar_path):
                        shutil.copy(original_jar_path, client_jar_path)
                        log(f"从原版复制客户端JAR: {original_jar_path} -> {client_jar_path}")
                    else:
                        log(f"无法获取客户端JAR文件", logging.ERROR)

                # 更新进度条显示Fabric Loader安装完成
                update_progress({
                    'status': f'Fabric Loader 安装完成!',  # 状态描述
                    'value': 1,  # 进度值设置为100%
                    'valueStringOverride': '100%'  # 自定义进度文本显示
                })
                # 记录Fabric Loader安装完成的日志
                log(f"Fabric Loader 安装完成到 {fabric_version_id}")
                
                # 重新获取Fabric安装JSON（这里可能是重复代码，但为了保持原有逻辑不变）
                fabric_json_response = requests.get(fabric_json_url, timeout=30)
                # 检查HTTP响应状态码
                if fabric_json_response.status_code != 200:
                    # 如果状态码不是200，记录ERROR级别日志并抛出异常
                    log(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}", logging.ERROR)
                    # 抛出异常，中断安装流程
                    raise Exception(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}")
                
                # 解析JSON响应数据
                fabric_json = fabric_json_response.json()
                
                # 保存Fabric版本JSON文件
                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                # 以UTF-8编码写入JSON文件，使用ensure_ascii=False保持Unicode字符，indent=4格式化输出
                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json, f, ensure_ascii=False, indent=4)
                
                # 记录保存JSON文件成功的日志
                log(f"已保存Fabric版本JSON: {fabric_json_path}")
                
                # 下载Fabric所需的库文件
                update_progress({
                    'status': f'正在下载Fabric库文件...',  # 状态描述
                    'value': 0.95,  # 进度值设置为95%
                    'valueStringOverride': '95%'  # 自定义进度文本显示
                })
                
                # 从安装JSON中提取库文件列表
                libraries = fabric_json.get("libraries", [])
                # 记录需要下载的库文件数量
                log(f"Fabric需要下载 {len(libraries)} 个库文件")
                
                # 使用镜像源下载库文件
                processed_libraries = []
                for lib in libraries:
                    if "downloads" in lib and "artifact" in lib["downloads"]:
                        artifact = lib["downloads"]["artifact"]
                        lib_path = os.path.join(minecraft_dir, "libraries", artifact["path"])
                        lib_url = artifact["url"]
                        lib_size = artifact.get("size", 0)
                        
                        # 检查文件是否需要下载
                        if not os.path.exists(lib_path) or os.path.getsize(lib_path) != lib_size:
                            processed_libraries.append((lib, lib_path, lib_url))
                
                # 使用多线程下载库文件
                if processed_libraries:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                        future_to_lib = {}
                        for lib, lib_path, lib_url in processed_libraries:
                            # 确保目录存在
                            os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                            
                            # 使用镜像源下载库文件
                            mirror_urls = dl_source_library_get(lib_url)
                            for url in mirror_urls:
                                try:
                                    future = executor.submit(download_file, url, lib_path)
                                    future_to_lib[future] = (lib_path, url)
                                    break
                                except Exception as e:
                                    log(f"从 {url} 下载库文件失败: {e}", logging.WARNING)
                                    continue
                        
                        # 等待所有下载任务完成
                        for future in concurrent.futures.as_completed(future_to_lib):
                            lib_path, url = future_to_lib[future]
                            try:
                                future.result()
                                log(f"成功下载库文件: {lib_path}")
                            except Exception as e:
                                log(f"下载库文件失败: {lib_path}, {e}", logging.ERROR)
                
                # 创建mods目录
                mods_dir = os.path.join(fabric_version_dir, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                log(f"已创建mods目录: {mods_dir}")
                
                # 创建资源包目录
                resourcepacks_dir = os.path.join(fabric_version_dir, "resourcepacks")
                os.makedirs(resourcepacks_dir, exist_ok=True)
                log(f"已创建资源包目录: {resourcepacks_dir}")
                
                # 记录Fabric Loader安装完成的日志
                log(f"Fabric {loader_version} 安装完成")
                # 更新进度条显示安装完成
                update_progress({
                    'status': f'Fabric {loader_version} 安装完成!',  # 状态描述
                    'value': 1.0,  # 进度值设置为100%
                    'valueStringOverride': '100%'  # 自定义进度文本显示
                })
                
            except Exception as e:
                # 捕获Fabric Loader安装过程中的任何异常
                log(f"安装 Fabric Loader 失败: {e}", logging.ERROR)
                # 即使Fabric安装失败，原版Minecraft仍然安装成功
                update_progress({
                    'status': f'Minecraft 版本 {version} 安装完成，但 Fabric Loader 安装失败!',  # 状态描述显示部分成功
                    'value': 1.0  # 进度值设置为100%
                })
                # 返回True表示原版Minecraft安装成功
                return True
        
        # 记录Minecraft版本安装完成的日志
        log(f"Minecraft 版本 {version} 安装完成")
        # 更新进度条显示安装完成
        update_progress({
            'status': f'Minecraft 版本 {version} 安装完成!',  # 状态描述
            'value': 1.0  # 进度值设置为100%
        })
        # 返回True表示安装成功
        return True
        
    except Exception as e:
        # 捕获整个安装过程中的任何异常
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # 调用异常处理函数记录详细的异常信息
        handle_exception(exc_type, exc_value, exc_traceback)
        # 记录安装失败的ERROR级别日志
        log(f"安装 Minecraft 版本 {version} 时发生错误: {str(e)}", logging.ERROR)
        # 返回False表示安装失败
        return False
    finally:
        # 关闭下载对话框（无论成功还是失败都会执行）
        if download_dialog:
            try:
                # 尝试关闭下载对话框
                download_dialog.close()
            except Exception as e:
                # 如果关闭对话框出错，记录WARNING级别日志
                log(f"关闭下载对话框时出错: {e}")

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
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vLayout = QVBoxLayout(self)
        
        # 1. 核心名称
        self.vLayout.addWidget(StrongBodyLabel(i18nText("核心名称 (文件夹名)"), self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(i18nText("修改此项将重命名版本文件夹"))
        self.vLayout.addWidget(self.name_edit)

        # 2. 真实版本号
        self.vLayout.addWidget(StrongBodyLabel(i18nText("真实游戏版本"), self))
        self.real_ver_edit = LineEdit(self)
        self.real_ver_edit.setPlaceholderText(i18nText("例如: 1.21.8"))
        self.vLayout.addWidget(self.real_ver_edit)

        # 3. Fabric 状态
        self.fabric_layout = QHBoxLayout()
        self.fabric_label = BodyLabel(i18nText("是否为 Fabric 版本"), self)
        self.fabric_switch = SwitchButton(self)
        self.fabric_switch.setOnText(i18nText("是"))
        self.fabric_switch.setOffText(i18nText("否"))
        self.fabric_layout.addWidget(self.fabric_label)
        self.fabric_layout.addWidget(self.fabric_switch)
        self.fabric_layout.addStretch(1)
        self.vLayout.addLayout(self.fabric_layout)

        # 4. 图标路径
        self.vLayout.addWidget(StrongBodyLabel(i18nText("自定义图标路径"), self))
        self.icon_layout = QHBoxLayout()
        self.icon_edit = LineEdit(self)
        self.icon_edit.setPlaceholderText(i18nText("图标文件的绝对路径"))
        self.browse_btn = PushButton(i18nText("浏览"), self)
        self.browse_btn.clicked.connect(self.browse_icon)
        self.icon_layout.addWidget(self.icon_edit)
        self.icon_layout.addWidget(self.browse_btn)
        self.vLayout.addLayout(self.icon_layout)
        
        self.vLayout.addStretch(1)

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18nText("选择图标"), "", i18nText("图片文件 (*.png *.jpg *.ico);;所有文件 (*.*)")
        )
        if path:
            self.icon_edit.setText(path)

class ControlPage(QWidget):
    """ 核心控制页面 """
    def __init__(self, open_folder_callback, delete_callback, parent=None):
        super().__init__(parent)
        self.vLayout = QVBoxLayout(self)
        
        self.open_folder_btn = PushButton(i18nText("打开版本文件夹"), self)
        self.open_folder_btn.setIcon(FluentIcon.FOLDER)
        self.open_folder_btn.clicked.connect(open_folder_callback)
        self.vLayout.addWidget(self.open_folder_btn)
        
        self.delete_btn = PushButton(i18nText("删除此核心"), self)
        self.delete_btn.setIcon(FluentIcon.DELETE)
        # 注意：删除操作可能需要关闭对话框，这里只是回调
        self.delete_btn.clicked.connect(delete_callback) 
        self.vLayout.addWidget(self.delete_btn)
        
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
        from qfluentwidgets import SmoothScrollArea
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
        from qfluentwidgets import SmoothScrollArea
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
        os.startfile(self.mods_dir)

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
                    send2trash.send2trash(path)
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
        from qfluentwidgets import SmoothScrollArea
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
        os.startfile(self.packs_dir)

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
                    send2trash.send2trash(path)
                    InfoBar.success(title=i18nText("已删除"), content=os.path.basename(path), parent=self.window())
                    self.load_packs()
                except Exception as e:
                    InfoBar.error(title=i18nText("删除失败"), content=str(e), parent=self.window())

# --- CoreManageDialog (更新引用) ---

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
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)

        # 1. 顶部标题
        self.titleLabel = SubtitleLabel(i18nText("核心管理") + f": {version_name}", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 2. Pivot 导航栏
        self.pivot = Pivot(self)
        self.pivot.addItem(routeKey="baseInfo", text=i18nText("基本信息"))
        self.pivot.addItem(routeKey="control", text=i18nText("核心控制"))
        self.pivot.addItem(routeKey="server", text=i18nText("服务器"))
        self.pivot.addItem(routeKey="resource", text=i18nText("资源包"))
        self.pivot.addItem(routeKey="mod", text=i18nText("Mod"))
        self.viewLayout.addWidget(self.pivot)

        # 3. StackedWidget 内容区
        self.stackedWidget = QStackedWidget(self)
        self.viewLayout.addWidget(self.stackedWidget)

        # 初始化各个页面
        self.baseInfoPage = BaseInfoPage(self)
        self.controlPage = ControlPage(self.open_version_folder, self.delete_core, self)
        self.serverPage = ServerPage(self.version_name, self.minecraft_dir, self.home_interface, self)
        # --- 更新：使用新实现的页面 ---
        self.resourcePage = ResourcePackPage(self.version_name, self.minecraft_dir, self)
        self.modPage = ModPage(self.version_name, self.minecraft_dir, self)

        self.stackedWidget.addWidget(self.baseInfoPage)
        self.stackedWidget.addWidget(self.controlPage)
        self.stackedWidget.addWidget(self.serverPage)
        self.stackedWidget.addWidget(self.resourcePage)
        self.stackedWidget.addWidget(self.modPage)

        # 连接信号
        self.pivot.currentItemChanged.connect(lambda k: self.stackedWidget.setCurrentIndex(
            ["baseInfo", "control", "server", "resource", "mod"].index(k)
        ))

        # 加载数据
        self.load_data()

        # 调整底部按钮
        self.yesButton.setText(i18nText("保存修改"))
        self.cancelButton.setText(i18nText("关闭"))

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self.save_data)

    def load_data(self):
        """ 从 .BL.json 加载数据到 BaseInfoPage """
        try:
            if os.path.exists(self.bl_json_path):
                with open(self.bl_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    versions_data = data.get("versions", {})
                    self.current_data = versions_data.get(self.version_name, {})
                    
                    # 填充 BaseInfoPage
                    self.baseInfoPage.name_edit.setText(self.version_name)
                    self.baseInfoPage.real_ver_edit.setText(self.current_data.get("version", self.version_name))
                    self.baseInfoPage.fabric_switch.setChecked(self.current_data.get("Fabric", False))
                    self.baseInfoPage.icon_edit.setText(self.current_data.get("icon", ""))
        except Exception as e:
            log(f"加载核心信息失败: {e}", logging.ERROR)

    def open_version_folder(self):
        open_minecraft_version_folder(self, self.version_name, self.minecraft_dir)

    def delete_core(self):
        # 这里的删除逻辑比较复杂，因为在对话框内部删除自己引用的对象
        # 简单处理：关闭对话框，并返回一个信号让外部处理删除
        # 或者直接在这里调用 delete_minecraft_version 但需要传入 label/card 等 UI 对象，这里没有
        # 所以这里只做逻辑删除（文件删除），UI 刷新交给外部
        
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
                    send2trash.send2trash(version_path)
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
                    # 注意：这里需要在关闭后通知主界面刷新列表，
                    # open_core_management 的返回值逻辑需要处理这种情况
            except Exception as e:
                InfoBar.error(title=i18nText("删除失败"), content=str(e), parent=self)

    def save_data(self):
        """ 保存 BaseInfoPage 的数据 """
        # 获取 BaseInfoPage 的数据
        new_name = self.baseInfoPage.name_edit.text().strip()
        new_real_ver = self.baseInfoPage.real_ver_edit.text().strip()
        is_fabric = self.baseInfoPage.fabric_switch.isChecked()
        new_icon = self.baseInfoPage.icon_edit.text().strip()
        
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

def open_core_management(self, version_name, MINECRAFT_DIR, home_interface):
    """ 打开核心管理对话框的入口函数 """
    dialog = CoreManageDialog(version_name, MINECRAFT_DIR, home_interface, parent=self)
    if dialog.exec():
        return True # 返回 True 表示需要刷新列表
    return False # 返回 False (如取消或出错) 视情况刷新，但在 setup_ui 中我们做了全量刷新，所以影响不大