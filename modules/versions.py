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
from qfluentwidgets import InfoBar, InfoBarPosition, ComboBox, StrongBodyLabel, BodyLabel, SubtitleLabel, MessageBoxBase
import logging, os, json, send2trash, platform, requests, shutil, concurrent.futures, threading, time
import sip # type: ignore
from pathlib import Path
from modules.win11toast import notify, update_progress
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
from modules.safe import handle_exception
import sys
from modules.customize import find_Customize
from modules.i18n import i18nText


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
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
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
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            if item in config_data["Customize"]:
                config_data["Customize"].remove(item)
            with open('config.json', 'w', encoding='utf-8') as file:
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
        with open('config.json', 'r', encoding='utf-8') as file:
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
            with open('config.json', 'r', encoding='utf-8') as file:
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
            with open('config.json', 'w', encoding='utf-8') as file:
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

def Get_Run_Script(mc_version):
    """
    根据 cmcl.json 的内容生成启动 .minecraft 文件夹中指定版本的命令
    支持 Fabric 加载器启动
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        mc_version (str): 要启动的 Minecraft 版本号
        
    Returns:
        str: 启动命令（批处理格式）
    """
    
    # 检查 cmcl.json 文件是否存在
    if not os.path.exists('cmcl.json'):
        raise FileNotFoundError(i18nText("cmcl.json 文件不存在"))
    
    # 读取 cmcl.json 配置
    with open('cmcl.json', 'r', encoding='utf-8') as f:
        cmcl_data = json.load(f)
    
    # 获取 Minecraft 目录
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        minecraft_dir = config_data.get('minecraft_dir', '')
        if not minecraft_dir:
            # 如果配置中没有指定，则使用默认路径
            appdata = os.environ.get('APPDATA', '')
            minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')
    except Exception:
        # 如果读取配置文件失败，使用默认路径
        appdata = os.environ.get('APPDATA', '')
        minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')
    
    versions_dir = os.path.join(minecraft_dir, "versions", mc_version)
    
    # 检查版本目录是否存在
    if not os.path.exists(versions_dir):
        raise FileNotFoundError(f"版本 {mc_version} 不存在于 {versions_dir}")
    
    # 获取版本 JSON 文件路径
    version_json_path = os.path.join(versions_dir, f"{mc_version}.json")
    if not os.path.exists(version_json_path):
        raise FileNotFoundError(f"版本配置文件 {version_json_path} 不存在")
    
    # 读取版本配置
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_data = json.load(f)
    
    # 获取客户端 JAR 文件路径
    client_jar_path = os.path.join(versions_dir, f"{mc_version}.jar")
    if not os.path.exists(client_jar_path):
        raise FileNotFoundError(f"客户端 JAR 文件 {client_jar_path} 不存在")
    
    # 获取 Java 路径 (使用指定的 Zulu JDK 路径)
    java_path = r"java"
    
    # 获取账户信息
    account_info = None
    if cmcl_data.get("accounts"):
        # 查找选中的账户或使用第一个账户
        account_info = next((acc for acc in cmcl_data["accounts"] if acc.get("selected")), 
                           cmcl_data["accounts"][0])
    
    # 设置用户名
    username = "Bloret-Player"
    if account_info:
        username = account_info.get("playerName", "Bloret-Player")
    
    # 构建基本启动参数
    launch_args = [
        f'"{java_path}"',  # Java路径需要用引号包围
        "--enable-native-access=ALL-UNNAMED",  # 解决Java警告
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",  # 抑制弃用警告
        "--add-opens", "java.base/java.util=ALL-UNNAMED",  # 抑制弃用警告
        "--add-opens", "java.base/sun.nio.ch=ALL-UNNAMED",  # 抑制更多警告
        "--add-opens", "java.base/sun.misc=ALL-UNNAMED",   # 抑制sun.misc警告
        "--add-opens", "java.base/jdk.internal.misc=ALL-UNNAMED",  # 抑制jdk.internal.misc警告
        "--add-opens", "java.base/jdk.internal.ref=ALL-UNNAMED",   # 抑制jdk.internal.ref警告
        "--add-exports", "java.base/sun.nio.ch=ALL-UNNAMED",  # 导出sun.nio.ch包
        "--add-exports", "java.base/sun.misc=ALL-UNNAMED",   # 导出sun.misc包
        "--add-exports", "java.base/jdk.internal.misc=ALL-UNNAMED",  # 导出jdk.internal.misc包
        "--add-exports", "java.base/jdk.internal.ref=ALL-UNNAMED",   # 导出jdk.internal.ref包
        "-Dio.netty.tryReflectionSetAccessible=true",  # 解决Netty反射问题
        "-Dio.netty.native.skipTryReflectionSetAccessible=true",  # 跳过Netty反射检查
        "-Dsun.misc.unsafe.throwException=false",  # 禁用sun.misc.Unsafe异常
        "-Djdk.attach.allowAttachSelf=true",  # 允许自我附加
        "-Djdk.module.IllegalAccess.silent=true",  # 静默非法访问
        "-Dlog4j2.formatMsgNoLookups=true",
        "-Dfile.encoding=UTF-8",
        "-Dsun.jnu.encoding=UTF-8",
        "-Dstderr.encoding=UTF-8", 
        "-Dstdout.encoding=UTF-8",
        "-XX:+UseG1GC",
        "-XX:-UseAdaptiveSizePolicy",
        "-XX:-OmitStackTraceInFastThrow",
        "-Djdk.lang.Process.allowAmbiguousCommands=true",
        "-Dfml.ignoreInvalidMinecraftCertificates=True",
        "-Dfml.ignorePatchDiscrepancies=True",
        "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump",
        "-Dsun.misc.URLClassPath.disableJarChecking=true",  # 禁用JAR检查
        "-Djava.rmi.server.useCodebaseOnly=true",  # 仅使用代码库
        "-Dcom.sun.management.jmxremote.local.only=true",  # 仅限本地JMX远程
        "-Dcom.sun.management.jmxremote.authenticate=false",  # 禁用JMX身份验证
        "-Dcom.sun.management.jmxremote.ssl=false",  # 禁用JMX SSL
        "-XX:-OmitStackTraceInFastThrow",  # 不省略快速抛出的堆栈跟踪
        "-Djna.nosys=true",  # 禁用系统级JNA库
        "-Djnidispatch.preserve=true",  # 保留JNI分发
        "-Dorg.lwjgl.util.Debug=false",  # 禁用LWJGL调试
        "-Dorg.lwjgl.util.noload=true",  # 不加载LWJGL库
        "-Djava.awt.headless=false",  # 非headless模式
        "-Dsun.java2d.noddraw=true",  # 禁用DirectDraw
        "-Dsun.java2d.d3d=false",  # 禁用Direct3D
        "-Dsun.java2d.opengl=false",  # 禁用OpenGL
        "-Dsun.java2d.pmoffscreen=false",  # 禁用离屏渲染
        "-Dsun.java2d.accthreshold=0",  # 禁用硬件加速
        "-XX:ErrorFile=./hs_err_pid%p.log",  # 错误日志文件
        "-XX:+UnlockExperimentalVMOptions",  # 解锁实验性选项
        "-XX:+UseG1GC",  # 使用G1垃圾收集器
        "-XX:+UseCompressedOops",  # 使用压缩对象指针
        "-XX:+OptimizeStringConcat",  # 优化字符串连接
        "-XX:+UseStringDeduplication"  # 启用字符串去重
    ]
    
    # 添加 Native 库路径参数
    natives_path = os.path.join(versions_dir, f"{mc_version}-natives")
    launch_args.extend([
        f'-Djava.library.path="{natives_path}"',
        f'-Djna.tmpdir="{natives_path}"',
        f'-Dorg.lwjgl.system.SharedLibraryExtractPath="{natives_path}"',
        f'-Dio.netty.native.workdir="{natives_path}"'
    ])
    
    # 添加启动器标识参数
    launch_args.extend([
        "-Dminecraft.launcher.brand=Bloret-Launcher",
        "-Dminecraft.launcher.version=361"
    ])
    
    # 构建类路径 (classpath)
    classpath = []
    
    # 添加所有依赖库
    libraries_dir = os.path.join(minecraft_dir, "libraries")
    missing_libraries = []
    if "libraries" in version_data:
        for lib in version_data["libraries"]:
            # 检查库是否适用于当前系统
            should_include = True
            if "rules" in lib:
                should_include = False
                for rule in lib["rules"]:
                    if rule.get("action") == "allow":
                        os_rule = rule.get("os", {})
                        if not os_rule or (os_rule.get("name", "").lower() == platform.system().lower() or 
                                          (os_rule.get("name") == "windows" and platform.system() == "Windows") or
                                          (os_rule.get("name") == "osx" and platform.system() == "Darwin") or
                                          (os_rule.get("name") == "linux" and platform.system() == "Linux")):
                            should_include = True
                            break
            
            if should_include:
                lib_path = None
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    lib_path = os.path.join(minecraft_dir, "libraries", lib["downloads"]["artifact"]["path"])
                elif "name" in lib:
                    # 处理 Maven 风格的库名称
                    parts = lib["name"].split(":")
                    if len(parts) >= 3:
                        group_id, artifact_id, lib_version = parts[0:3]
                        relative_path = os.path.join(
                            group_id.replace(".", "/"),
                            artifact_id,
                            lib_version,
                            f"{artifact_id}-{lib_version}.jar"
                        )
                        lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
                
                if lib_path:
                    # 检查库文件是否存在
                    if os.path.exists(lib_path):
                        classpath.append(lib_path)
                    else:
                        # 记录缺失的库文件
                        missing_libraries.append((lib, lib_path))
    
    # 检查是否为 Fabric 版本
    is_fabric = "fabric" in mc_version.lower() or any("fabric" in lib.get("name", "").lower() for lib in version_data.get("libraries", []))

    if is_fabric:
        log(f"检测到 Fabric 版本: {mc_version}")
    else:
        log(f"检测到原版: {mc_version}")
    
    # 添加内存参数 (根据PCL中的默认设置)
    # PCL中默认分配内存为854x480，这里设置合理的内存参数
    launch_args.extend([
        "-Xmn192m",  # 年轻代内存
        "-Xmx4096m"  # 最大堆内存，设置为4GB
    ])
    
    # 添加自定义参数
    launch_args.append(f'-Doolloo.jlw.tmpdir="{os.path.join(os.getcwd(), "Bloret Launcher")}"')
    
    # 添加 Fabric 特定参数和处理
    if is_fabric:
        launch_args.append("-DFabricMcEmu=net.minecraft.client.main.Main")
        
        # 用于存储所有库
        fabric_libs = []
        # 跟踪已添加的ASM库
        asm_libs = {}
        
        # 添加 Fabric 版本文件夹中的所有 JAR 文件
        fabric_version_dir = os.path.join(versions_dir, mc_version)
        if os.path.exists(fabric_version_dir):
            for file in os.listdir(fabric_version_dir):
                if file.endswith('.jar') and 'fabric' in file.lower():
                    jar_path = os.path.join(fabric_version_dir, file)
                    fabric_libs.append(jar_path)
        
        # 添加 mods 目录中的所有 JAR 文件 (Fabric mods)
        mods_dir = os.path.join(minecraft_dir, "versions", mc_version, "mods")
        if os.path.exists(mods_dir):
            for file in os.listdir(mods_dir):
                if file.endswith('.jar'):
                    fabric_libs.append(os.path.join(mods_dir, file))
        
        # 首先添加 Fabric Loader 核心库和关键依赖
        fabric_loader_libs = [
            "net/fabricmc/fabric-loader",
            "net/fabricmc/sponge-mixin",
            "net/fabricmc/intermediary",
            "net/fabricmc/fabric-api",
            "net/fabricmc/fabric",
            "net/fabricmc/tiny-mappings-parser",
            "net/fabricmc/tiny-remapper",
            "net/fabricmc/access-widener"
        ]
        
        # 跟踪已添加的ASM库
        asm_libs = {}  # 使用字典跟踪每个ASM模块的最高版本
        
        for lib in version_data.get("libraries", []):
            lib_name = lib.get("name", "").lower()
            lib_path = None
            
            # 检查是否为 Fabric 相关库或关键依赖
            if "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = os.path.join(minecraft_dir, "libraries", lib["downloads"]["artifact"]["path"])
            elif "name" in lib:
                # 处理 Maven 风格的库名称
                parts = lib["name"].split(":")
                if len(parts) >= 3:
                    group_id, artifact_id, lib_version = parts[0:3]
                    relative_path = os.path.join(
                        group_id.replace(".", "/"),
                        artifact_id,
                        lib_version,
                        f"{artifact_id}-{lib_version}.jar"
                    )
                    lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
            
            if lib_path:
                # 检查库文件是否存在
                if not os.path.exists(lib_path):
                    # 记录缺失的库文件
                    missing_libraries.append((lib, lib_path))
                    continue
                    
                # 处理ASM库
                if "org.ow2.asm" in lib_name:
                    # 从库名中提取版本号和模块名
                    parts = lib_name.split(":")
                    if len(parts) >= 3:
                        asm_module = parts[1]  # 例如 "asm", "asm-commons" 等
                        lib_version = parts[2]  # 版本号
                        
                        # 如果这是一个更高版本，或者这个模块还没有被记录
                        if asm_module not in asm_libs or lib_version > asm_libs[asm_module]["version"]:
                            asm_libs[asm_module] = {"version": lib_version, "path": lib_path}
                            log(f"记录ASM库 {asm_module} 版本 {lib_version}")
                        else:
                            log(f"跳过较低版本的ASM库 {asm_module} 版本 {lib_version}，已有版本 {asm_libs[asm_module]['version']}")
                    continue  # 跳过当前的库添加，稍后会统一添加ASM库
                        
                # 添加Fabric核心库
                elif any(fabric_lib in lib_name for fabric_lib in fabric_loader_libs):
                    if "fabric-loader" in lib_name or "intermediary" in lib_name:
                        fabric_libs.insert(0, lib_path)  # 放在前面
                    else:
                        fabric_libs.append(lib_path)  # 其他的放在后面
                # 其他 Fabric 相关库
                elif "fabric" in lib_name or "mixin" in lib_name:
                    fabric_libs.append(lib_path)
            # 记录找到的库
            if lib_path and os.path.exists(lib_path):
                log(f"已添加库: {lib_path}")
        
        # 按照特定顺序构建最终的类路径
        final_classpath = []
        
        # 1. 添加 ASM 库（按特定顺序，只添加最高版本）
        asm_modules_order = ["asm", "asm-commons", "asm-tree", "asm-analysis", "asm-util"]
        for module in asm_modules_order:
            if module in asm_libs:
                final_classpath.append(asm_libs[module]["path"])
                log(f"添加ASM库 {module} 版本 {asm_libs[module]['version']}，路径: {asm_libs[module]['path']}")
        
        # 2. 添加 Fabric 核心库
        final_classpath.extend(fabric_libs)
        
        # 3. 添加其他所有库（排除已添加的ASM库）
        # 创建已添加ASM库路径的集合，用于过滤
        added_asm_paths = set()
        for module in asm_libs:
            added_asm_paths.add(asm_libs[module]["path"].lower())
        
        # 过滤掉已添加的ASM库
        filtered_classpath = []
        for lib_path in classpath:
            # 检查是否为ASM库
            if "org/ow2/asm" in lib_path.lower() or "/asm-" in lib_path.lower():
                if lib_path.lower() not in added_asm_paths:
                    log(f"跳过重复的ASM库: {lib_path}")
                    continue
            filtered_classpath.append(lib_path)
        
        final_classpath.extend(filtered_classpath)
        
        # 更新类路径
        classpath = final_classpath
    
    # 添加客户端 JAR 到 classpath
    classpath.append(client_jar_path)
    if not os.path.exists(client_jar_path): missing_libraries.append(({"name": f"{mc_version}.jar", "downloads": {"artifact": {"path": f"{mc_version}/{mc_version}.jar"}}}, client_jar_path))
    
    # 检查是否有缺失的库文件并尝试下载
    if missing_libraries:
        log(f"发现 {len(missing_libraries)} 个缺失的库文件，正在尝试下载...")
        
        # 从 config.json 读取 MaxThread
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            max_workers = config_data.get("MaxThread", 64)  # 默认值改为64，避免资源耗尽
        except Exception:
            max_workers = 64  # 读取失败时使用默认值
        
        # 创建下载器并启动下载线程
        downloader = LibraryDownloader(missing_libraries, max_workers)
        download_thread = threading.Thread(target=downloader.download_libraries)
        download_thread.daemon = True
        download_thread.start()
        
        # 等待下载完成
        downloader.completed_event.wait()
        
        # 重新检查库文件并添加到类路径中
        # 这一步确保即使之前缺失的库文件现在也已下载并添加到类路径中
        for lib, lib_path in missing_libraries:
            if os.path.exists(lib_path) and lib_path not in classpath:
                classpath.append(lib_path)
                log(f"添加之前缺失但现已下载的库: {lib_path}")
    
    # 添加类路径参数
    launch_args.extend(["-cp", '\"' + ";".join(classpath) + '\"'])  # Windows 使用分号分隔
    
    # Add Fabric Loader arguments to ensure mods are loaded
    launch_args.extend(["-Dfabric.addMods=" + mods_dir])
    
    # 添加主类和参数
    if is_fabric:
        # Fabric 使用 KnotClient 主类而不是 -jar 参数
        launch_args.append("net.fabricmc.loader.impl.launch.knot.KnotClient")
    else:
        # 原始 Minecraft 启动方式
        launch_args.append("-jar")
        java_wrapper_path = os.path.join(os.getcwd(), "JavaWrapper.jar")
        if not os.path.exists(java_wrapper_path):
            raise FileNotFoundError(f"JavaWrapper.jar 文件不存在: {java_wrapper_path}")
        launch_args.append(f'"{java_wrapper_path}"')
        launch_args.append("net.minecraft.client.main.Main")
    
    # 添加游戏参数
    # 对于Fabric版本，需要使用实际的游戏版本号而不是Fabric加载器版本号
    actual_game_version = mc_version
    game_dir_version = mc_version  # 用于构建game_dir的版本
    
    if is_fabric and "-fabric-" in mc_version.lower():
        # 对于Fabric版本，目录结构为 .minecraft/versions/实际版本-fabric-加载器版本/实际版本-fabric-加载器版本.json
        # 但游戏目录应该是 .minecraft/versions/实际版本-fabric-加载器版本/实际版本.json
        # 我们需要从版本名称中提取实际的游戏版本
        # 例如: 1.21.8-fabric-0.17.2 应该对应游戏版本 1.21.8
        actual_game_version = mc_version.split("-fabric-")[0]
        game_dir_version = mc_version  # game_dir仍然使用完整版本名作为目录名
    
    # 游戏目录应该是主 .minecraft 目录，而不是版本特定目录
    game_dir = minecraft_dir
    assets_dir = os.path.join(minecraft_dir, "assets")
    
    # 检查游戏目录和资产目录是否存在
    if not os.path.exists(game_dir):
        raise FileNotFoundError(f"游戏目录不存在: {game_dir}")
    
    if not os.path.exists(assets_dir):
        raise FileNotFoundError(f"资产目录不存在: {assets_dir}")
    
    # 获取资产索引
    asset_index = version_data.get("assetIndex", {}).get("id", mc_version)
    
    # 设置 versionType
    version_type = "Bloret Launcher"
    
    # 检查登录方式并设置相应参数
    login_method = account_info.get("loginMethod", 0) if account_info else 0
    
    # 在日志中以列表形式记录启动信息
    log("启动信息:")
    log(f"- Minecraft 版本: {mc_version}")  # 使用完整版本名而不是解析后的版本
    log(f"- 登录方式: {'离线登录' if login_method == 0 else '微软登录' if login_method == 2 else '未知'}")
    log(f"- 登录名称: {username}")
    if account_info:
        log(f"- UUID: {account_info.get('uuid', 'N/A')}")
        log(f"- AccessToken: {'******' if account_info.get('accessToken') else 'N/A'}")
    
    # 根据登录方式设置启动参数
    if login_method == 0:  # 离线登录
        launch_args.extend([
            "--username", username,
            "--version", mc_version,  # 使用完整版本名而不是解析后的版本
            "--gameDir", game_dir,  # 不要在路径外额外添加引号
            "--assetsDir", assets_dir,  # 不要在路径外额外添加引号
            "--assetIndex", str(asset_index),
            "--uuid", "00000000000000000000000000000000",
            "--accessToken", "00000000000000000000000000000000",
            "--userType", "legacy",
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    elif login_method == 2:  # 微软登录
        # 检查账户信息相关字段
        missing_fields = []
        if not account_info:
            missing_fields.append(i18nText("账户信息"))
        else:
            if not account_info.get("uuid"):
                missing_fields.append("UUID")
            if not account_info.get("accessToken"):
                missing_fields.append("AccessToken")
            # 你可以根据需要继续检查其他字段

        if missing_fields:
            raise ValueError(f"缺少必要的启动参数: {', '.join(missing_fields)}，请先登录或完善账户信息。")
            
        launch_args.extend([
            "--username", username,
            "--version", mc_version,  # 使用完整版本名而不是解析后的版本
            "--gameDir", game_dir,  # 不要在路径外额外添加引号
            "--assetsDir", assets_dir,  # 不要在路径外额外添加引号
            "--assetIndex", str(asset_index),
            "--uuid", account_info.get("uuid"),
            "--accessToken", account_info.get("accessToken"),
            "--clientId", account_info.get("clientId", ""),
            "--xuid", account_info.get("xuid", ""),
            "--userType", account_info.get("userType", "msa"),
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    
    # 构建命令
    # 不添加过滤器，避免被Minecraft误认为是游戏参数
    bat_command = " ".join(launch_args)
    
    # 修复f-string中不能包含反斜杠的问题
    chcp_command = "chcp 65001"
    cd_command = f'cd {os.path.join(minecraft_dir, "versions", game_dir_version)}'
    full_command = f"{chcp_command}\n{cd_command}\n{bat_command}"
    
    log(f"生成的启动命令: {bat_command}")
    log(f"最终生成的启动命令 (包含 chcp 65001 和 cd 文件夹): {full_command}")
    return full_command

def InstallMinecraftVersion(version, minecraft_dir=None, download_dialog=None, Fabric_Loader=False):
    # 如果没有提供下载对话框，则创建并显示一个新的
    if download_dialog is None:
        try:
            from PyQt5.QtWidgets import QDialog
            from PyQt5 import uic
            import json
            
            download_dialog = QDialog()
            uic.loadUi("ui/MCVer_downloading.ui", download_dialog)
            title_text = f"正在下载 Minecraft {version}"
            if Fabric_Loader:
                title_text += " 和 Fabric Loader"
            download_dialog.setWindowTitle(title_text)

            # 连接暂停按钮
            if hasattr(download_dialog, 'pause_button'):
                download_dialog.pause_button.clicked.connect(lambda: toggle_pause_download(download_dialog))

            # 设置MaxThread的值
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                max_thread_value = config.get("MaxThread", 2000)
                if hasattr(download_dialog, 'MaxThread') and hasattr(download_dialog, 'MaxThread_2'):
                    download_dialog.MaxThread.setText(str(max_thread_value))
                    download_dialog.MaxThread_2.setText(str(max_thread_value))
            except Exception as e:
                log(f"设置MaxThread值时出错: {e}")
                
            download_dialog.show()
        except Exception as e:
            log(f"创建下载对话框时出错: {e}")
            download_dialog = None
    
    from threading import Thread
    thread = Thread(target=_install_minecraft_version_threaded, args=(version, minecraft_dir, download_dialog, Fabric_Loader))
    thread.start()

def toggle_pause_download(download_dialog):
    if hasattr(download_dialog, 'downloader') and download_dialog.downloader is not None:
        downloader = download_dialog.downloader
        if downloader.is_paused:
            downloader.resume()
            download_dialog.pause_button.setText(i18nText("暂停"))
        else:
            downloader.pause()
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
        # 创建Windows 11通知
        notify(progress={
            'title': i18nText('Minecraft 版本安装'),
            'status': i18nText('正在准备安装...'),
            'value': '0',
            'valueStringOverride': '0%'
        })

        # 0. 如果minecraft_dir未提供，设置默认值
        if minecraft_dir is None:
            appdata = os.environ.get('APPDATA', '')
            minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')

        log(f"开始安装 Minecraft 版本: {version}，安装目录: {minecraft_dir}")

        # 确保目录存在
        os.makedirs(minecraft_dir, exist_ok=True)
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)

        # 1. 获取版本清单，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.1, 
            'valueStringOverride': '10%',
            'status': i18nText('正在获取版本清单...')
        })

        # 创建 LibraryDownloader 实例
        # 假设 missing_libraries 在后续步骤中获取
        # 这里先创建一个空的，后续再更新


        
        # 定义版本清单URL列表，使用PCL风格的镜像源处理
        manifest_urls = dl_source_launcher_or_meta_get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
        
        manifest_data = None
        for url in manifest_urls:
            try:
                log(f"正在获取版本清单: {url}")
                response = requests.get(url, proxies=None, timeout=30)
                if response.status_code == 200:
                    manifest_data = response.json()
                    break
                else:
                    log(f"获取版本清单失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议
                try:
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    response = requests.get(http_url, proxies=None, timeout=30)
                    if response.status_code == 200:
                        manifest_data = response.json()
                        break
                except requests.exceptions.ConnectionError as e2:
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        if not manifest_data:
            log("所有版本清单URL都获取失败", logging.ERROR)
            return False

        # 2. 在清单中查找指定版本
        update_progress({
            'value': 0.2, 
            'valueStringOverride': '20%',
            'status': i18nText('正在查找指定版本...')
        })
        version_info = None
        for ver in manifest_data.get("versions", []):
            if ver.get("id") == version:
                version_info = ver
                break

        if not version_info:
            log(f"未找到版本 {version}", logging.ERROR)
            return False

        log(f"找到版本信息: {version_info}")

        # 3. 获取版本详细信息URL并使用PCL风格的镜像源处理
        update_progress({
            'value': 0.3, 
            'valueStringOverride': '30%',
            'status': i18nText('正在获取版本详细信息...')
        })
        original_url = version_info.get("url")
        
        # 使用PCL风格的镜像源处理
        version_info_urls = dl_source_launcher_or_meta_get(original_url)

        log(f"正在获取版本详细信息: {version_info_urls}")
        version_data = None
        
        for url in version_info_urls:
            try:
                log(f"正在获取版本详细信息: {url}")
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    version_data = response.json()
                    break
                else:
                    log(f"获取版本详细信息失败: {url}, HTTP {response.status_code}", logging.WARNING)
            except requests.exceptions.ConnectionError as e:
                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                # 尝试使用HTTP协议
                try:
                    http_url = url.replace("https://", "http://")
                    log(f"尝试使用HTTP协议: {http_url}")
                    response = requests.get(http_url, timeout=30)
                    if response.status_code == 200:
                        version_data = response.json()
                        break
                except requests.exceptions.ConnectionError as e2:
                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
            except requests.exceptions.RequestException as e:
                log(f"请求错误: {url}, {e}", logging.WARNING)
        
        if not version_data:
            log("所有版本详细信息URL都获取失败", logging.ERROR)
            return False

        # 5. 创建版本目录
        update_progress({
            'value': 0.4, 
            'valueStringOverride': '40%',
            'status': i18nText('正在创建版本目录...')
        })
        version_dir = os.path.join(versions_dir, version)
        os.makedirs(version_dir, exist_ok=True)

        # 保存版本JSON文件
        version_json_path = os.path.join(version_dir, f"{version}.json")
        with open(version_json_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=4)

        log(f"已保存版本JSON文件: {version_json_path}")

        # 设置 First_Step_CheckBox 为 true
        if download_dialog:
            try:
                from PyQt5.QtWidgets import QCheckBox
                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                from PyQt5.QtCore import QMetaObject, Qt
                checkbox = download_dialog.findChild(QCheckBox, "First_Step_CheckBox")
                if checkbox:
                    QMetaObject.invokeMethod(checkbox, "setChecked", Qt.QueuedConnection, 
                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(bool, True))
            except Exception as e:
                log(f"设置First_Step_CheckBox时出错: {e}")

        # 下载客户端JAR文件，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.5, 
            'valueStringOverride': '50%',
            'status': i18nText('正在下载客户端JAR文件...')
        })
        if "downloads" in version_data and "client" in version_data["downloads"]:
            client_info = version_data["downloads"]["client"]
            client_url = client_info["url"]
            
            # 使用PCL风格的镜像源处理
            client_urls = dl_source_launcher_or_meta_get(client_url)

            client_jar_path = os.path.join(version_dir, f"{version}.jar")
            log(f"正在下载客户端JAR文件: {client_urls}")

            download_success = False
            for url in client_urls:
                try:
                    log(f"正在下载客户端JAR文件: {url}")
                    # 使用Session来更好地管理连接
                    with requests.Session() as session:
                        response = session.get(url, stream=True, timeout=30)
                        if response.status_code == 200:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            
                            with open(client_jar_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        
                                        # 更新客户端JAR进度条
                                        if download_dialog and total_size > 0:
                                            try:
                                                from PyQt5.QtWidgets import QProgressBar
                                                # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                from PyQt5.QtCore import QMetaObject, Qt
                                                progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                if progress_bar:
                                                    progress_value = int((downloaded_size / total_size) * 100)
                                                    QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                            except Exception as e:
                                                log(f"更新client_jar_progress时出错: {e}")
                            
                            log(f"已下载客户端JAR文件: {client_jar_path}")
                            download_success = True
                            break
                        else:
                            log(f"下载客户端JAR文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            # 如果是403错误，尝试使用原始URL
                            if response.status_code == 403:
                                original_url = client_info["url"]
                                log(f"尝试使用原始URL: {original_url}")
                                with requests.Session() as session:
                                    response = session.get(original_url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        total_size = int(response.headers.get('content-length', 0))
                                        downloaded_size = 0
                                        
                                        with open(client_jar_path, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                                    downloaded_size += len(chunk)
                                                    
                                                    # 更新客户端JAR进度条
                                                    if download_dialog and total_size > 0:
                                                        try:
                                                            from PyQt5.QtWidgets import QProgressBar
                                                            # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                            from PyQt5.QtCore import QMetaObject, Qt
                                                            progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                            if progress_bar:
                                                                progress_value = int((downloaded_size / total_size) * 100)
                                                                QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                                       __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                                        except Exception as e:
                                                            log(f"更新client_jar_progress时出错: {e}")
                                        
                                        log(f"已下载客户端JAR文件: {client_jar_path}")
                                        download_success = True
                                        break
                except requests.exceptions.ConnectionError as e:
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议
                    try:
                        http_url = url.replace("https://", "http://")
                        log(f"尝试使用HTTP协议: {http_url}")
                        with requests.Session() as session:
                            response = session.get(http_url, stream=True, timeout=30)
                            if response.status_code == 200:
                                total_size = int(response.headers.get('content-length', 0))
                                downloaded_size = 0
                                
                                with open(client_jar_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded_size += len(chunk)
                                            
                                            # 更新客户端JAR进度条
                                            if download_dialog and total_size > 0:
                                                try:
                                                    from PyQt5.QtWidgets import QProgressBar
                                                    # 使用QMetaObject.invokeMethod确保在主线程中执行UI更新
                                                    from PyQt5.QtCore import QMetaObject, Qt
                                                    progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                                    if progress_bar:
                                                        progress_value = int((downloaded_size / total_size) * 100)
                                                        QMetaObject.invokeMethod(progress_bar, "setValue", Qt.QueuedConnection,
                                                                               __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                                except Exception as e:
                                                    log(f"更新client_jar_progress时出错: {e}")
                                
                                log(f"已下载客户端JAR文件: {client_jar_path}")
                                download_success = True
                                break
                    except requests.exceptions.ConnectionError as e2:
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            if not download_success:
                log("所有客户端JAR文件URL都下载失败", logging.ERROR)
                return False
        else:
            log(i18nText("版本信息中未找到客户端下载链接"), logging.ERROR)
            return False

        # 加载 config.json 文件
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        # 创建 LibraryDownloader 实例
        max_thread_value = config.get("MaxThread", 2000)
        # 处理主版本库文件
        processed_libraries = []
        if "libraries" in version_data:
            for lib in version_data["libraries"]:
                if "name" in lib:
                    parts = lib["name"].split(":")
                    if len(parts) == 3:
                        group = parts[0].replace(".", "/")
                        artifact = parts[1]
                        version_lib = parts[2]
                        lib_filename = f"{artifact}-{version_lib}.jar"
                        lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                        processed_libraries.append((lib, lib_path))
                    else:
                        log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                else:
                    log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

        if download_dialog is not None and processed_libraries:
            download_dialog.downloader = LibraryDownloader(processed_libraries, max_workers=max_thread_value)

        # 创建natives目录
        natives_dir = os.path.join(version_dir, f"{version}-natives")
        os.makedirs(natives_dir, exist_ok=True)

        # 下载库文件，使用PCL风格的镜像源处理
        update_progress({
            'value': 0.6, 
            'valueStringOverride': '60%',
            'status': i18nText('正在下载库文件...')
        })
        libraries_dir = os.path.join(minecraft_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        if download_dialog is not None and download_dialog.downloader is not None:
            download_dialog.downloader.download_libraries(download_dialog)
        
        # 下载资源索引，使用PCL风格的镜像源处理
        if "assetIndex" in version_data:
            asset_index = version_data["assetIndex"]
            asset_index_url = asset_index["url"]
            
            # 使用PCL风格的镜像源处理
            asset_index_urls = dl_source_launcher_or_meta_get(asset_index_url)
            
            assets_dir = os.path.join(minecraft_dir, "assets")
            indexes_dir = os.path.join(assets_dir, "indexes")
            objects_dir = os.path.join(assets_dir, "objects")
            
            os.makedirs(indexes_dir, exist_ok=True)
            os.makedirs(objects_dir, exist_ok=True)
            
            asset_index_id = asset_index["id"]
            asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")
            
            update_progress({'status': i18nText("正在下载资源索引...")})
            log(f"正在下载资源索引: {asset_index_urls}")
            
            download_success = False
            for url in asset_index_urls:
                try:
                    log(f"正在下载资源索引: {url}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        with open(asset_index_path, 'wb') as f:
                            f.write(response.content)
                        log(f"已下载资源索引: {asset_index_path}")
                        download_success = True
                        break
                    else:
                        log(f"下载资源索引失败: {url}, HTTP {response.status_code}", logging.WARNING)
                except requests.exceptions.ConnectionError as e:
                    log(f"网络连接错误: {url}, {e}", logging.WARNING)
                    # 尝试使用HTTP协议
                    try:
                        http_url = url.replace("https://", "http://")
                        log(f"尝试使用HTTP协议: {http_url}")
                        response = requests.get(http_url, timeout=30)
                        if response.status_code == 200:
                            with open(asset_index_path, 'wb') as f:
                                f.write(response.content)
                            log(f"已下载资源索引: {asset_index_path}")
                            download_success = True
                            break
                    except requests.exceptions.ConnectionError as e2:
                        log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                except requests.exceptions.RequestException as e:
                    log(f"请求错误: {url}, {e}", logging.WARNING)
            
            if not download_success:
                log("所有资源索引URL都下载失败", logging.ERROR)
                return False
                
            # 读取资源索引并下载资源文件
            with open(asset_index_path, 'r', encoding='utf-8') as f:
                asset_index_data = json.load(f)
            
            if "objects" in asset_index_data:
                assets_count = len(asset_index_data['objects'])
                update_progress({'status': f"开始下载资源文件，共 {assets_count} 个..."})
                log(f"开始下载资源文件，共 {assets_count} 个")
                
                # 使用线程池进行多线程下载
                from concurrent.futures import ThreadPoolExecutor
                
                # 设置最大线程数，根据系统资源限制调整默认值
                try:
                    with open('config.json', 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    max_workers = config_data.get("MaxThread", 64)
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    handle_exception(exc_type, exc_value, exc_traceback)
                    max_workers = 64  # 读取失败时使用默认值64
                log(f"使用 {max_workers} 个线程下载资源文件")
                
                # 用于跟踪活动下载线程数的变量
                active_downloads = 0
                active_downloads_lock = threading.Lock()
                
                # 创建多线程下载资源文件
                def download_asset(asset_name, asset_info):
                    # 增加活动下载计数
                    nonlocal active_downloads
                    with active_downloads_lock:
                        active_downloads += 1
                        # 更新活动线程数显示
                        if download_dialog:
                            try:
                                from PyQt5.QtWidgets import QLabel
                                from PyQt5.QtCore import QMetaObject, Qt
                                thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                if thread_label:
                                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                            except Exception as e:
                                log(f"更新Resources_file_working_Thread时出错: {e}")
                    
                    try:
                        hash_value = asset_info["hash"]
                        hash_prefix = hash_value[:2]
                        object_path = os.path.join(objects_dir, hash_prefix, hash_value)
                        
                        # 如果文件已存在且大小正确，则跳过
                        if os.path.exists(object_path) and os.path.getsize(object_path) == asset_info["size"]:
                            return True
                        
                        # 创建目录
                        os.makedirs(os.path.dirname(object_path), exist_ok=True)
                        
                        # 构建URL，使用PCL风格的镜像源处理
                        asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{hash_value}"
                        asset_urls = dl_source_assets_get(asset_url)
                        
                        # 下载文件
                        download_success = False
                        for url in asset_urls:
                            try:
                                log(f"正在下载资源文件: {url}")
                                # 使用 requests.Session() 来更好地管理连接
                                with requests.Session() as session:
                                    response = session.get(url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        with open(object_path, 'wb') as f:
                                            # 使用固定大小的块进行流式写入，避免内存占用过高
                                            for chunk in response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                        download_success = True
                                        break
                                    else:
                                        log(f"下载资源文件失败: {url}, HTTP {response.status_code}", logging.WARNING)
                            except requests.exceptions.ConnectionError as e:
                                log(f"网络连接错误: {url}, {e}", logging.WARNING)
                                # 尝试使用HTTP协议
                                try:
                                    http_url = url.replace("https://", "http://")
                                    log(f"尝试使用HTTP协议: {http_url}")
                                    with requests.Session() as session:
                                        response = session.get(http_url, stream=True, timeout=30)
                                        if response.status_code == 200:
                                            with open(object_path, 'wb') as f:
                                                for chunk in response.iter_content(chunk_size=8192):
                                                    if chunk:
                                                        f.write(chunk)
                                            download_success = True
                                            break
                                except requests.exceptions.ConnectionError as e2:
                                    log(f"HTTP协议也失败: {http_url}, {e2}", logging.WARNING)
                            except requests.exceptions.RequestException as e:
                                log(f"下载资源文件时发生网络请求错误: {asset_name}, {url}, {e}", logging.WARNING)
                        
                        if not download_success:
                            log(f"所有资源文件URL都下载失败: {asset_name}", logging.WARNING)
                            return False
                        
                        return True
                    except Exception:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        handle_exception(exc_type, exc_value, exc_traceback)
                        return False
                    finally:
                        # 减少活动下载计数
                        with active_downloads_lock:
                            active_downloads -= 1
                            # 更新活动线程数显示
                            if download_dialog:
                                try:
                                    from PyQt5.QtWidgets import QLabel
                                    from PyQt5.QtCore import QMetaObject, Qt
                                    thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                    if thread_label:
                                        QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                                __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                                except Exception as e:
                                    log(f"更新Resources_file_working_Thread时出错: {e}")
                
                # 创建Windows 11通知
                notify(progress={
                    'title': i18nText('Minecraft 资源下载'),
                    'status': i18nText('正在下载资源文件...'),
                    'value': '0',
                    'valueStringOverride': f'0/{assets_count} 个'
                })
                
                # 创建线程池
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AssetsDownloader") as executor:
                    # 提交所有下载任务
                    future_to_asset = {executor.submit(download_asset, asset_name, asset_info): asset_name 
                                      for asset_name, asset_info in asset_index_data["objects"].items()}
                    
                    # 处理完成的任务
                    success_count = 0
                    failed_count = 0
                    completed_count = 0
                    for future in concurrent.futures.as_completed(future_to_asset):
                        asset_name = future_to_asset[future]
                        try:
                            success = future.result()
                            if success:
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            log(f"处理资源文件时发生错误: {asset_name}, {str(e)}", logging.WARNING)
                            failed_count += 1
                        finally:
                            completed_count += 1
                        
                        # 更新资源文件下载进度条和线程数显示
                        if download_dialog:
                            try:
                                from PyQt5.QtWidgets import QProgressBar, QLabel
                                from PyQt5.QtCore import QMetaObject, Qt
                                
                                # 更新进度条
                                resources_progress_bar = download_dialog.findChild(QProgressBar, "Resources_progress")
                                if resources_progress_bar:
                                    progress_value = int((completed_count / assets_count) * 100)
                                    QMetaObject.invokeMethod(resources_progress_bar, "setValue", Qt.QueuedConnection,
                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(int, progress_value))
                                
                                # 更新活动线程数显示
                                thread_label = download_dialog.findChild(QLabel, "Resources_file_working_Thread")
                                if thread_label:
                                    QMetaObject.invokeMethod(thread_label, "setText", Qt.QueuedConnection,
                                                           __import__('PyQt5.QtCore').QtCore.Q_ARG(str, str(active_downloads)))
                            except Exception as e:
                                log(f"更新资源文件进度时出错: {e}")
                                
                        # update_progress({'status': "正在下载资源文件...", 'value': completed_count, 'valueStringOverride': f'{completed_count}/{assets_count} 个'})
                        # 每下载10个文件或达到总数的5%时更新一次通知，避免频繁更新
                        if completed_count % 10 == 0 or completed_count % int(assets_count * 0.05) == 0 or completed_count == assets_count:
                            update_progress({
                                'value': completed_count/assets_count, 
                                'valueStringOverride': f'{completed_count}/{assets_count} ({int(completed_count/assets_count*100)}%)',
                                'status': f'正在下载资源文件...'
                            })
                    
                    # 等待所有任务完成
                    try:
                        concurrent.futures.wait(future_to_asset, timeout=60)
                    except Exception as e:
                        log(f"等待资源文件下载完成时出错: {e}")
                
                # 更新通知为完成状态
                update_progress({
                    'value': 1, 
                    'valueStringOverride': f'{assets_count}/{assets_count} 个',
                    'status': i18nText('资源文件下载完成!')
                })
                
                # 输出下载结果
                log(f"资源文件下载完成: 成功 {success_count} 个, 失败 {failed_count} 个")
                
                # 如果有失败的资源文件，记录警告
                if failed_count > 0:
                    log(f"有 {failed_count} 个资源文件下载失败，但不影响游戏运行", logging.WARNING)
        
        # 如果需要安装Fabric Loader
        if Fabric_Loader:
            log(f"开始安装 Fabric Loader 到 Minecraft {version}")
            update_progress({
                'status': f'正在安装 Fabric Loader...',
                'value': 0.9,
                'valueStringOverride': '90%'
            })
            
            # 获取最新的Fabric Loader版本
            try:
                # 获取Fabric Loader版本列表
                fabric_api_url = "https://meta.fabricmc.net/v2/versions/loader/" + version
                log(f"正在获取Fabric Loader版本列表: {fabric_api_url}")
                
                fabric_response = requests.get(fabric_api_url, timeout=30)
                if fabric_response.status_code != 200:
                    log(f"获取Fabric Loader版本列表失败: HTTP {fabric_response.status_code}", logging.ERROR)
                    raise Exception(f"获取Fabric Loader版本列表失败: HTTP {fabric_response.status_code}")
                
                fabric_versions = fabric_response.json()
                if not fabric_versions:
                    log(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本", logging.ERROR)
                    raise Exception(f"未找到适用于 Minecraft {version} 的 Fabric Loader 版本")
                
                # 获取最新版本
                latest_fabric = fabric_versions[0]
                loader_version = latest_fabric["loader"]["version"]
                
                log(f"找到最新的 Fabric Loader 版本: {loader_version}")
                
                # 构建Fabric版本的安装路径
                fabric_version_id = f"{version}-fabric-{loader_version}"
                fabric_version_dir = os.path.join(versions_dir, fabric_version_id)
                os.makedirs(fabric_version_dir, exist_ok=True)
                
                # 获取Fabric安装JSON
                fabric_json_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader_version}/profile/json"
                log(f"正在获取Fabric安装JSON: {fabric_json_url}")

                fabric_json_response = requests.get(fabric_json_url, timeout=30)
                if fabric_json_response.status_code != 200:
                    log(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}", logging.ERROR)
                    raise Exception(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}")

                fabric_json_data = fabric_json_response.json()
                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json_data, f, ensure_ascii=False, indent=4)
                log(f"已保存Fabric安装JSON: {fabric_json_path}")

                # 下载Fabric Loader所需的库文件
                update_progress({
                    'status': f'正在下载 Fabric Loader 库文件...',
                    'value': 0.92,
                    'valueStringOverride': '92%'
                })
                log(f"开始下载 Fabric Loader 库文件...")

                fabric_libraries = fabric_json_data.get("libraries", [])
                
                processed_fabric_libraries = []
                for lib in fabric_libraries:
                    if "name" in lib:
                        parts = lib["name"].split(":")
                        if len(parts) == 3:
                            group = parts[0].replace(".", "/")
                            artifact = parts[1]
                            version_lib = parts[2]
                            lib_filename = f"{artifact}-{version_lib}.jar"
                            lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                            processed_fabric_libraries.append((lib, lib_path))
                        else:
                            log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                    else:
                        log(f"库缺少 'name' 字段: {lib}", logging.WARNING)

                if processed_fabric_libraries:
                    library_downloader = LibraryDownloader(
                        processed_fabric_libraries,
                        max_workers=max_thread_value
                    )
                    if not library_downloader.download_libraries(download_dialog=download_dialog):
                        log("Fabric Loader 库文件下载失败", logging.ERROR)
                        raise Exception("Fabric Loader 库文件下载失败")
                    log("Fabric Loader 库文件下载完成")
                else:
                    log("未找到 Fabric Loader 库文件", logging.WARNING)

                # 修改版本隔离文件
                # 复制原始版本JSON文件
                original_version_json_path = os.path.join(version_dir, f"{version}.json")
                shutil.copy(original_version_json_path, fabric_version_dir)

                # 修改Fabric版本JSON文件
                fabric_json_data["id"] = fabric_version_id
                fabric_json_data["inheritsFrom"] = version
                fabric_json_data["jar"] = version

                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json_data, f, ensure_ascii=False, indent=4)
                log(f"已修改Fabric版本JSON文件: {fabric_json_path}")

                update_progress({
                    'status': f'Fabric Loader 安装完成!',
                    'value': 1,
                    'valueStringOverride': '100%'
                })
                log(f"Fabric Loader 安装完成到 {fabric_version_id}")
                
                fabric_json_response = requests.get(fabric_json_url, timeout=30)
                if fabric_json_response.status_code != 200:
                    log(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}", logging.ERROR)
                    raise Exception(f"获取Fabric安装JSON失败: HTTP {fabric_json_response.status_code}")
                
                fabric_json = fabric_json_response.json()
                
                # 保存Fabric版本JSON
                fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
                with open(fabric_json_path, 'w', encoding='utf-8') as f:
                    json.dump(fabric_json, f, ensure_ascii=False, indent=4)
                
                log(f"已保存Fabric版本JSON: {fabric_json_path}")
                
                # 下载Fabric所需的库文件
                update_progress({
                    'status': f'正在下载Fabric库文件...',
                    'value': 0.95,
                    'valueStringOverride': '95%'
                })
                
                # 获取Fabric所需的库文件列表
                libraries = fabric_json.get("libraries", [])
                log(f"Fabric需要下载 {len(libraries)} 个库文件")
                
                # 下载库文件
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    future_to_lib = {}
                    for lib in libraries:
                        if "downloads" in lib and "artifact" in lib["downloads"]:
                            artifact = lib["downloads"]["artifact"]
                            lib_path = os.path.join(minecraft_dir, "libraries", artifact["path"])
                            lib_url = artifact["url"]
                            
                            # 确保目录存在
                            os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                            
                            # 如果文件不存在或大小不匹配，则下载
                            if not os.path.exists(lib_path) or os.path.getsize(lib_path) != artifact.get("size", 0):
                                # 使用全局函数替换类方法调用
                                future_to_lib[executor.submit(download_file, lib_url, lib_path)] = lib_path
                    
                    # 等待所有库文件下载完成
                    for future in concurrent.futures.as_completed(future_to_lib):
                        lib_path = future_to_lib[future]
                        try:
                            future.result()
                            log(f"成功下载库文件: {lib_path}")
                        except Exception as e:
                            log(f"下载库文件失败: {lib_path}, {e}", logging.ERROR)
                
                log(f"Fabric Loader {loader_version} 安装完成")
                update_progress({
                    'status': f'Fabric Loader {loader_version} 安装完成!',
                    'value': 1.0,
                    'valueStringOverride': '100%'
                })
                
            except Exception as e:
                log(f"安装 Fabric Loader 失败: {e}", logging.ERROR)
                # 即使Fabric安装失败，原版Minecraft仍然安装成功
                update_progress({
                    'status': f'Minecraft 版本 {version} 安装完成，但 Fabric Loader 安装失败!',
                    'value': 1.0
                })
                return True
        
        log(f"Minecraft 版本 {version} 安装完成")
        update_progress({
            'status': f'Minecraft 版本 {version} 安装完成!',
            'value': 1.0
        })
        return True
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"安装 Minecraft 版本 {version} 时发生错误: {str(e)}", logging.ERROR)
        return False
    finally:
        # 关闭下载对话框
        if download_dialog:
            try:
                download_dialog.close()
            except Exception as e:
                log(f"关闭下载对话框时出错: {e}")

def update_version_combo_by_category(self, version_combo, category):
    """
    根据分类更新版本选择框的内容
    
    Args:
        version_combo: 版本选择框控件
        category: 分类名称
    """
    version_combo.clear()
    
    # 根据分类加载对应版本列表
    if category == i18nText("百络谷支持版本"):
        if hasattr(self, 'ver_id_bloret') and self.ver_id_bloret:
            version_combo.addItems(self.ver_id_bloret)
        else:
            version_combo.addItems(["1.21.7", "1.21.8"])
    elif category == i18nText("正式版本"):
        # 如果已经有缓存数据，直接使用
        if hasattr(self, 'ver_id_main') and self.ver_id_main:
            version_combo.addItems(self.ver_id_main)
        else:
            # 从网络获取版本列表
            try:
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                response.raise_for_status()
                version_data = response.json()
                versions = version_data["versions"]
                ver_id_main_temp = []
                for version in versions:
                    if version["type"] not in ["snapshot", "old_alpha", "old_beta"]:
                        ver_id_main_temp.append(version["id"])
                version_combo.addItems(ver_id_main_temp)
            except Exception as e:
                log(f"获取正式版本列表失败: {e}")
                version_combo.addItems(["1.21.8", "1.21.7"])
    elif category == i18nText("快照版本"):
        # 如果已经有缓存数据，直接使用
        if hasattr(self, 'ver_id_short') and self.ver_id_short:
            version_combo.addItems(self.ver_id_short)
        else:
            # 从网络获取版本列表
            try:
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                response.raise_for_status()
                version_data = response.json()
                versions = version_data["versions"]
                ver_id_short_temp = []
                for version in versions:
                    if version["type"] == "snapshot":
                        ver_id_short_temp.append(version["id"])
                version_combo.addItems(ver_id_short_temp)
            except Exception as e:
                log(f"获取快照版本列表失败: {e}")
                version_combo.addItems(["24w14a", "24w13a"])
    elif category == i18nText("远古版本"):
        # 如果已经有缓存数据，直接使用
        if hasattr(self, 'ver_id_long') and self.ver_id_long:
            version_combo.addItems(self.ver_id_long)
        else:
            # 从网络获取版本列表
            try:
                response = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
                response.raise_for_status()
                version_data = response.json()
                versions = version_data["versions"]
                ver_id_long_temp = []
                for version in versions:
                    if version["type"] in ["old_alpha", "old_beta"]:
                        ver_id_long_temp.append(version["id"])
                version_combo.addItems(ver_id_long_temp)
            except Exception as e:
                log(f"获取远古版本列表失败: {e}")
                version_combo.addItems(["b1.7.3", "b1.7.2"])


def on_other_version_selected(self, selected_text, combo_box):
    """
    当用户在版本选择框中选择"其他版本..."时触发
    
    Args:
        selected_text: 用户选择的文本
        combo_box: 触发事件的ComboBox控件
        version_type: 版本类型 ("Minecraft" 或 "Fabric")
    """
    log(f"[versions][on_other_version_selected] start with : {selected_text}, {combo_box.currentText()}")
    # 检查是否选择了"其他版本..."
    if selected_text == i18nText("其他版本..."):
        log("[versions][on_other_version_selected] 用户选择了其他版本...")
        # 创建自定义对话框
        dialog = MessageBoxBase(self)
        dialog.setWindowTitle(i18nText("其他版本..."))
        
        # 标题和副标题
        title_label = SubtitleLabel(i18nText("其他版本..."))
        subtitle_label = BodyLabel(i18nText("在这里可以选择下载 Minecraft 的其他版本。\n请注意，这些版本可能不受百络谷支持，可能无法正常进入 Bloret 服务器。\n部分比较老的或快照版本可能不受 Fabric Loader 支持。"))
        
        # 创建分类选择框
        category_label = StrongBodyLabel(i18nText("版本分类"))
        category_combo = ComboBox()
        category_combo.addItems([
            i18nText("百络谷支持版本"),
            i18nText("正式版本"), 
            i18nText("快照版本"),
            i18nText("远古版本")
        ])
        category_combo.setCurrentText(i18nText("百络谷支持版本"))
        
        # 创建版本选择框
        version_label = StrongBodyLabel(i18nText("具体版本"))
        version_combo = ComboBox()
        
        # 初始化版本选择框
        update_version_combo_by_category(self, version_combo, i18nText("百络谷支持版本"))
        
        # 当分类改变时更新版本选择框
        def on_category_changed(category):
            # 禁用两个选择框
            category_combo.setEnabled(False)
            version_combo.setEnabled(False)
            
            # 显示加载提示
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PyQt5.QtCore import Qt, QThread, pyqtSignal
            InfoBar.info(
                title=i18nText('正在加载'),
                content=i18nText(f'正在加载 {category} 版本列表'),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=dialog
            )
            
            # 在新线程中加载版本列表
            class LoadVersionThread(QThread):
                finished = pyqtSignal()
                
                def __init__(self, main_window, version_combo, category):
                    super().__init__()
                    self.main_window = main_window
                    self.version_combo = version_combo
                    self.category = category
                
                def run(self):
                    update_version_combo_by_category(self.main_window, self.version_combo, self.category)
                    self.finished.emit()
            
            # 创建并启动线程
            load_thread = LoadVersionThread(self, version_combo, category)
            
            # 线程完成后的处理
            def on_load_finished():
                # 重新启用两个选择框
                category_combo.setEnabled(True)
                version_combo.setEnabled(True)
                # 关闭线程
                load_thread.quit()
                load_thread.wait()
            
            load_thread.finished.connect(on_load_finished)
            load_thread.start()
        
        category_combo.currentTextChanged.connect(on_category_changed)
        
        # 添加控件到对话框布局
        dialog.viewLayout.addWidget(title_label)
        dialog.viewLayout.addWidget(subtitle_label)
        dialog.viewLayout.addWidget(category_label)
        dialog.viewLayout.addWidget(category_combo)
        dialog.viewLayout.addWidget(version_label)
        dialog.viewLayout.addWidget(version_combo)
        
        # 隐藏取消按钮
        # dialog.cancelButton.hide()
        
        # 处理确认按钮点击事件
        def handle_confirm():
            selected_version = version_combo.currentText()
            if selected_version:
                # 检查版本是否已存在于combo_box中
                existing_items = [combo_box.itemText(i) for i in range(combo_box.count())]
                # 移除"其他版本..."选项以避免重复
                if i18nText("其他版本...") in existing_items:
                    existing_items.remove(i18nText("其他版本..."))
                    
                # 如果版本不存在于现有列表中，则添加
                if selected_version not in existing_items:
                    # 在"其他版本..."之前插入新项目
                    combo_box.insertItem(combo_box.count() - 1, selected_version)
                combo_box.setCurrentText(selected_version)
            dialog.accept()
        
        dialog.yesButton.clicked.connect(handle_confirm)
        
        # 显示对话框
        dialog.exec_()
