# 0. 先获取 IP 地址
import modules.IP


import sys
import os
from pathlib import Path

# Add the local directory to handle imports like 'import RinUI' correctly
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Create the QApplication early so it can be used in shims and module imports
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtCore import QLocale, Qt, QTranslator, QObject, Slot, Signal, Property, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QDesktopServices

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
app = QApplication(sys.argv)

# --- Finished Full PySide6 Migration ---
# All modules have been refactored to use PySide6 and PySide6-Fluent-Widgets directly.

import RinUI
from RinUI import RinUIWindow

import random
import threading
import subprocess
import json
import requests
import modules.config as cfg
import modules.globals as BLglobals
from modules.launch import Get_Run_Script
from modules.chafuwang import getServerData
from modules.setup_ui import get_all_launch_items, scan_java_paths
from modules.i18n import i18nText
from modules.Bloriko import AskBloriko
import modules.web
import socket

class Backend(QObject):
    """
    Python Backend to interact with QML.
    Later, we will migrate all Bloret-Launcher.py logic here.
    """
    modrinthResultsReceived = Signal(list)
    minecraftAccountsChanged = Signal(list)
    logsCleared = Signal()
    easytierStatusChanged = Signal(str, str)
    serverInfoChanged = Signal(dict)
    queryResultReceived = Signal(dict)
    blorikoResponseReceived = Signal(str)
    syncStatusChanged = Signal(str)
    languageChanged = Signal()

    def __init__(self):
        super().__init__()
        self._server_info = {}
        self._activity_info = BLglobals.BL_Activity

    def setBackendParent(self, parent):
        self.parent = parent

    @Slot(result=str)
    def helloFromPython(self):
        return "Hello from PySide6 Backend!"
        
    @Slot(result=str)
    def getTips(self):
        if hasattr(BLglobals, "BLtips") and BLglobals.BLtips:
            return random.choice(BLglobals.BLtips)
        return "欢迎使用 Bloret Launcher！"

    @Slot(result=str)
    def getPlayerName(self):
        try:
            config_data = cfg.read()
            mc_account_config = config_data.get("MinecraftAccount", {})
            accounts_list = mc_account_config.get("accounts", [])
            chosen_index = mc_account_config.get("chosen", 0)
            if accounts_list and 0 <= chosen_index < len(accounts_list):
                return accounts_list[chosen_index].get("username", "访客")
        except Exception as e:
            print(f"Error reading player name: {e}")
        return "访客"
        
    @Slot(str)
    @Slot(str)
    def launchGame(self, version):
        print(f"Requested to launch game: {version}")
        def run_launch():
            try:
                launch_args, game_dir = Get_Run_Script(version)
                print(f"Launching with args: {launch_args}")
                subprocess.Popen(launch_args, cwd=game_dir)
            except Exception as e:
                print(f"Failed to launch: {e}")
                import traceback
                traceback.print_exc()
        threading.Thread(target=run_launch, daemon=True).start()

    @Slot(result=dict)
    def getActivityInfo(self):
        return BLglobals.BL_Activity

    @Slot()
    def refreshServerInfo(self):
        def update_callback(data):
            self._server_info = data
            self.serverInfoChanged.emit(data)
        getServerData("Bloret", callback=update_callback)

    @Slot(result=list)
    def getLaunchItems(self):
        from modules.setup_ui import get_all_launch_items
        items = get_all_launch_items()
        qml_items = []
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"getLaunchItems: Retrieved {len(items)} items from get_all_launch_items()")
        
        for item in items:
            # Extract icon path from item
            icon_path = "../../icon/Grass_Block.png"  # Default
            
            if item.get("type") == "minecraft":
                # For minecraft, check if we have metadata with custom icon
                # Default to Grass_Block for minecraft
                icon_path = "../../icon/Grass_Block.png"
                
            elif item.get("type") == "custom":
                # For custom apps, use a generic app icon
                icon_path = "../../icon/exeapps.png"
            
            qml_item = {
                "name": item["name"],
                "type": item["type"],
                "path": item["path"],
                "icon": icon_path
            }
            
            logger.debug(f"getLaunchItems: Added item {qml_item}")
            qml_items.append(qml_item)
        
        logger.debug(f"getLaunchItems: Returning {len(qml_items)} items to QML")
        return qml_items

    @Slot(str, bool)
    def askBloriko(self, query, deep_think):
        print(f"Bloriko request: '{query}', deep think: {deep_think}")
        def run_ask():
            try:
                config_data = cfg.read()
                if not config_data.get("Bloret_PassPort_Login", False):
                    self.blorikoResponseReceived.emit("未登录: 请先登录 Bloret PassPort 以使用 AI 功能。")
                    return
                
                from modules.Bloriko import AskBloriko
                response = AskBloriko(query, config_data, deepthink=deep_think)
                self.blorikoResponseReceived.emit(response)
            except Exception as e:
                print(f"Error in askBloriko: {e}")
                self.blorikoResponseReceived.emit(f"错误: {str(e)}")
        threading.Thread(target=run_ask, daemon=True).start()

    @Slot(str, bool)
    def askBlorikoForMods(self, query, deep_think):
        # We can reuse same signal or dedicated one, let's reuse
        print(f"Bloriko Mod suggestion request: '{query}'")
        self.askBloriko(query + ( " (请针对 Minecraft 模组给出建议)" if "模组" not in query and "mod" not in query.lower() else ""), deep_think)
    
    @Slot(str, str, bool)
    def askBlorikoForModsWithVersion(self, query, version, deep_think):
        """
        带 Minecraft 版本的模组推荐请求
        
        Args:
            query (str): 用户的需求描述
            version (str): Minecraft 版本号
            deep_think (bool): 是否启用深度思考
        """
        from modules.Bloriko import BuildModRecommendationQuestion
        print(f"Bloriko Mod suggestion request with version: '{query}' for MC {version}")
        recommendation_question = BuildModRecommendationQuestion(query, version)
        self.askBloriko(recommendation_question, deep_think)

    @Slot(result=list)
    def getVanillaVersions(self):
        try:
            config_data = cfg.read()
            return config_data.get('Minecraft_Versions', ["1.21.8", "1.21.7", "1.20.1"])
        except:
            return ["1.21.8", "1.21.7", "1.20.1"]

    @Slot(result=list)
    def getFabricVersions(self):
        # Using the same list for now as in setup_ui.py
        return self.getVanillaVersions()

    @Slot(result=list)
    def getJavaDownloadVersions(self):
        from modules.java import java_versions
        return list(java_versions.keys())

    @Slot(str)
    def downloadVanilla(self, version):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Vanilla: {version}")
        # Note: This will likely trigger a PyQt5 dialog if install.py isn't refactored
        InstallMinecraftVersion(version)

    @Slot(str)
    def downloadFabric(self, version):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Fabric: {version}")
        InstallMinecraftVersion(version, Fabric_Loader=True)

    @Slot(str)
    def downloadJava(self, version):
        from modules.java import InstallJava
        print(f"Requested download Java: {version}")
        InstallJava(version)

    @Slot()
    def addCustomApp(self):
        print("Requested add custom app")
        # 打开文件浏览对话框让用户选择 exe 或其他可执行文件
        file_path = QFileDialog.getOpenFileName(
            None,
            "选择应用程序文件",
            "",
            "所有文件 (*);;执行文件 (*.exe);;程序包 (*.zip);;整合包 (*.zip);;批处理脚本 (*.bat)"
        )[0]
        
        if not file_path:
            print("用户取消了文件选择")
            return
        
        # 提取文件名作为默认显示名称
        default_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 创建一个简单的输入对话框让用户确认/修改名称
        from PySide6.QtWidgets import QInputDialog
        display_name, ok = QInputDialog.getText(
            None,
            "输入显示名称",
            "请为此应用输入一个显示名称:",
            text=default_name
        )
        
        if not ok or not display_name:
            print("用户取消了名称输入")
            return
        
        # 保存到配置文件
        try:
            config_data = cfg.read()
            if "Customize" not in config_data:
                config_data["Customize"] = []
            
            # 检查是否已存在相同的项
            for item in config_data["Customize"]:
                if item.get("showname") == display_name:
                    print(f"自定义项 '{display_name}' 已存在")
                    return
            
            config_data["Customize"].append({
                "showname": display_name,
                "path": file_path
            })
            
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            print(f"成功添加自定义项: {display_name} -> {file_path}")
            # 可以在这里发出信号或刷新 UI（如果需要）
        except Exception as e:
            print(f"添加自定义项失败: {e}")

    @Slot(result=str)
    def getBloretVersion(self):
        return "2.0.0-RinUI (Beta)"

    @Slot(result=str)
    def getLanguageCode(self):
        config_data = cfg.read()
        # 旧版 config 用小写 'language' 键
        return config_data.get("language", config_data.get("Language", "zh-cn"))

    @Slot(result=list)
    def getLanguages(self):
        """从 Default.json 加载语言列表"""
        try:
            default_lang_path = "lang/Default.json"
            if os.path.exists(default_lang_path):
                with open(default_lang_path, "r", encoding="utf-8") as f:
                    default_data = json.load(f)
                    result = []
                    # 从 Default.json 中提取语言列表
                    if "lang" in default_data:
                        for code, lang_info in default_data["lang"].items():
                            # 使用 Default.json 中定义的名称
                            name = lang_info.get("name", code)
                            # 确保文件存在
                            lang_file = f"lang/{lang_info.get('file', code + '.json')}"
                            if os.path.exists(lang_file):
                                result.append({"code": code, "name": name})
                            else:
                                # 如果文件不存在，跳过这个语言
                                print(f"Warning: Language file {lang_file} not found for code {code}")
                    if not result:
                        result = [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]
            else:
                # 如果 Default.json 不存在，回退到旧方法
                lang_dir = "lang"
                result = []
                # 语言代码到显示名称的映射（常用语言）
                lang_names = {
                    "zh-cn": "简体中文", "zh-TW": "繁體中文", "en-US": "English (US)",
                    "en-GB": "English (UK)", "ja-JP": "日本語", "ko-KR": "한국어",
                    "fr-FR": "Français", "de-DE": "Deutsch", "es-ES": "Español",
                    "ru-RU": "Русский", "pt-BR": "Português (Brasil)",
                    "it-IT": "Italiano", "nl-NL": "Nederlands", "pl-PL": "Polski",
                    "tr-TR": "Türkçe", "ar-SA": "العربية", "vi-VN": "Tiếng Việt",
                }
                if os.path.isdir(lang_dir):
                    for fn in sorted(os.listdir(lang_dir)):
                        if fn.endswith(".json") and fn != "Default.json":
                            code = fn[:-5]  # 去掉 .json
                            # 尝试从语言文件读取自描述名称
                            name = lang_names.get(code, code)
                            try:
                                with open(os.path.join(lang_dir, fn), "r", encoding="utf-8") as f:
                                    d = json.load(f)
                                    # 某些语言文件里有 _meta.name 字段
                                    if "_meta" in d and "name" in d["_meta"]:
                                        name = d["_meta"]["name"]
                            except Exception:
                                pass
                            result.append({"code": code, "name": name})
                if not result:
                    result = [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]
            return result
        except Exception as e:
            print(f"Error loading languages: {e}")
            return [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]

    @Slot(str)
    def setLanguage(self, lang_code):
        try:
            config_data = cfg.read()
            config_data['language'] = lang_code
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            from modules.i18n import reload_language
            reload_language(lang_code)
            print(f"Language set to: {lang_code}")
            self.languageChanged.emit()
        except Exception as e:
            print(f"Error setting language: {e}")

    @Slot(str, result=str)
    def tr(self, key):
        return i18nText(key)

    @Slot(result=list)
    def getSystemJavas(self):
        return ["C:\\Program Files\\Java\\jre1.8.0_361\\bin\\java.exe", "E:\\Java\\jdk-17\\bin\\java.exe"]

    @Slot()
    def openMinecraftDir(self):
        config_data = cfg.read()
        mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
        if mc_dir and os.path.exists(mc_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(mc_dir))
        else:
            print(f"Minecraft directory not found: {mc_dir}")

    @Slot()
    def openLogDir(self):
        log_dir = os.path.join(BLglobals.datapath, "log")
        if os.path.exists(log_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))

    @Slot()
    def clearLogs(self):
        print("Clearing logs...")
        log_dir = os.path.join(BLglobals.datapath, "log")
        if os.path.exists(log_dir):
            import shutil
            for filename in os.listdir(log_dir):
                file_path = os.path.join(log_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

    @Slot(result=str)
    def getMinecraftDir(self):
        config_data = cfg.read()
        return config_data.get('minecraft_dir', BLglobals.minecraft_dir)

    @Slot(result=str)
    def browseMinecraftDir(self):
        dir_path = QFileDialog.getExistingDirectory(None, "选择 Minecraft 目录", self.getMinecraftDir())
        if dir_path:
            self.setMinecraftDir(dir_path)
            return dir_path
        return ""

    @Slot(str)
    def setMinecraftDir(self, path):
        config_data = cfg.read()
        config_data['minecraft_dir'] = path
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        BLglobals.minecraft_dir = path
        print(f"Minecraft directory updated to: {path}")

    @Slot(result=list)
    def getSystemJavas(self):
        return scan_java_paths()

    @Slot(result=str)
    def getCurrentJavaPath(self):
        config_data = cfg.read()
        return config_data.get('java_path', 'Auto')

    @Slot(str)
    def setCurrentJavaPath(self, path):
        config_data = cfg.read()
        config_data['java_path'] = path
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Java path updated to: {path}")

    @Slot(result=str)
    def getThemeMode(self):
        config_data = cfg.read()
        return config_data.get('theme', 'Auto')

    @Slot(str)
    def setThemeMode(self, mode):
        config_data = cfg.read()
        config_data['theme'] = mode
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Theme mode updated to: {mode}")

    @Slot(str)
    def queryUUID(self, name):
        print(f"Requested query UUID for name: {name}")
        def run_query():
            try:
                response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}")
                if response.status_code == 200:
                    data = response.json()
                    self.queryResultReceived.emit({"type": "uuid", "result": data.get("id"), "success": True})
                else:
                    self.queryResultReceived.emit({"type": "uuid", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "uuid", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def queryName(self, uuid):
        print(f"Requested query name for UUID: {uuid}")
        def run_query():
            try:
                response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
                if response.status_code == 200:
                    data = response.json()
                    self.queryResultReceived.emit({"type": "name", "result": data.get("name"), "success": True})
                else:
                    self.queryResultReceived.emit({"type": "name", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "name", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def querySkin(self, uuid):
        print(f"Requested query skin for UUID: {uuid}")
        def run_query():
            try:
                import base64
                response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
                if response.status_code == 200:
                    player_data = response.json()
                    properties = player_data.get("properties", [])
                    for prop in properties:
                        if prop["name"] == "textures":
                            textures = json.loads(base64.b64decode(prop["value"]).decode("utf-8"))
                            skin = textures["textures"].get("SKIN", {}).get("url")
                            cape = textures["textures"].get("CAPE", {}).get("url")
                            self.queryResultReceived.emit({"type": "textures", "skin": skin, "cape": cape, "success": True})
                            return
                    self.queryResultReceived.emit({"type": "textures", "success": False})
                else:
                    self.queryResultReceived.emit({"type": "textures", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "textures", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def copyToClipboard(self, text):
        from PySide6.QtGui import QGuiApplication
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        print(f"Copied to clipboard: {text}")

    @Slot()
    def startEasytierHost(self):
        from modules.easytier import StartEasytierServer
        print("Requested start Easytier host")
        # For simplicity, using hardcoded/config-based name and secret
        def run_et():
            self.easytierStatusChanged.emit("正在启动", "请稍候...")
            res = StartEasytierServer("Bloret", "123456") # Example defaults
            if "." in res: # Looks like an IP
                self.easytierStatusChanged.emit("已连接", f"您的虚拟 IP: {res}")
            else:
                self.easytierStatusChanged.emit("错误", res)
        threading.Thread(target=run_et, daemon=True).start()

    @Slot()
    def startEasytierClient(self):
        # Same as host for now in the simple view
        self.startEasytierHost()

    @Slot(result=list)
    def getFabricVersions(self):
        """从 .BL.json 读取 Fabric 版本列表（与旧版 setup_Mod_ui 一致）"""
        try:
            config_data = cfg.read()
            mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(mc_dir, "versions", ".BL.json")
            if not os.path.exists(bl_json_path):
                return []
            with open(bl_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            versions = data.get("versions", {})
            # 只返回 Fabric 版本
            fabric_versions = []
            for ver_name, ver_info in versions.items():
                if ver_info.get("Fabric", False):
                    fabric_versions.append(ver_name)
            return sorted(fabric_versions, reverse=True)
        except Exception as e:
            print(f"Error getting Fabric versions: {e}")
            return []

    @Slot(str)
    def searchModrinth(self, query):
        from modules.modrinth import search_mods
        print(f"Modrinth search request: '{query}'")
        def run_search():
            try:
                data = search_mods(query)
                results = []
                if isinstance(data, dict) and "hits" in data:
                    for hit in data["hits"]:
                        results.append({
                            "name": hit.get("title", "Unknown"),
                            "description": hit.get("description", ""),
                            "id": hit.get("project_id"),
                            "slug": hit.get("slug"),
                            "icon_url": hit.get("icon_url", "")
                        })
                self.modrinthResultsReceived.emit(results)
            except Exception as e:
                print(f"Error searching Modrinth: {e}")
                self.modrinthResultsReceived.emit([])
        threading.Thread(target=run_search, daemon=True).start()

    @Slot(str)
    def downloadMod(self, mod_id):
        """
        下载并安装模组
        
        Args:
            mod_id (str): 模组 ID 或 slug
        """
        from modules.modrinth import Get_Mod_File_Download_Url
        print(f"Requested download mod: {mod_id}")
        
        def run_download():
            try:
                # 首先尝试以 mod_id 作为 slug 获取下载 URL
                url = Get_Mod_File_Download_Url(mod_id)
                if url:
                    print(f"Found download URL: {url}")
                    # 获取 Minecraft 目录
                    config_data = cfg.read()
                    mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
                    mods_dir = os.path.join(mc_dir, "mods")
                    
                    # 确保 mods 目录存在
                    os.makedirs(mods_dir, exist_ok=True)
                    
                    # 从 URL 获取文件名
                    filename = url.split('/')[-1]
                    if not filename or '.' not in filename:
                        filename = f"{mod_id}.jar"
                    
                    file_path = os.path.join(mods_dir, filename)
                    
                    # 下载文件
                    print(f"Downloading mod to: {file_path}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Successfully downloaded mod to: {file_path}")
                    else:
                        print(f"Failed to download: HTTP {response.status_code}")
                else:
                    print(f"Could not find download URL for {mod_id}")
                    # 尝试打开 Modrinth 页面
                    QDesktopServices.openUrl(QUrl(f"https://modrinth.com/mod/{mod_id}"))
            except Exception as e:
                print(f"Error downloading mod: {e}")
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=run_download, daemon=True).start()

    @Slot(str)
    def getBloretPassPortUserName(self):
        config_data = cfg.read()
        if config_data.get('Bloret_PassPort_Login'):
            return config_data.get('Bloret_PassPort_UserName', 'Unknown')
        return "未登录"

    @Slot(result=str)
    def getPlayerName(self):
        config_data = cfg.read()
        mc_data = config_data.get("MinecraftAccount", {})
        accounts = mc_data.get("accounts", [])
        chosen_idx = mc_data.get("chosen", 0)
        if chosen_idx < len(accounts):
            return accounts[chosen_idx].get("username", "User")
        return "User"

    @Slot(result=list)
    def getVanillaVersions(self):
        # Placeholder for now, could be fetched from modules.versions or BMCLAPI
        return ["1.21.8", "1.21.4", "1.20.1", "1.12.2"]

    @Slot(result=list)
    def getFabricVersions(self):
        # Placeholder
        return ["0.18.1", "0.17.2", "0.16.0"]

    @Slot(result=list)
    def getJavaDownloadVersions(self):
        from modules.java import java_versions
        return list(java_versions.keys())

    @Slot(str)
    def downloadJava(self, version):
        from modules.java import InstallJava
        print(f"Requested download Java: {version}")
        InstallJava(version)

    @Slot()
    def loginBloretPassPort(self):
        from modules.links import Bloret_PassPort_Account_login
        Bloret_PassPort_Account_login()

    @Slot()
    def logoutBloretPassPort(self):
        from modules.Bloret_PassPort import Bloret_PassPort_Account_logout
        # We need to pass the main window or a mock for homeInterface
        config_data = cfg.read()
        config_data['Bloret_PassPort_Login'] = False
        config_data['Bloret_PassPort_UserName'] = ""
        config_data['Bloret_PassPort_PassWord'] = ""
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print("Logged out from Bloret PassPort")
        # 发出信号以刷新 UI（不传递参数，让 QML 主动查询）
        self.minecraftAccountsChanged.emit([])

    @Slot()
    def refreshMinecraftAccounts(self):
        # 发出信号以刷新 UI
        self.minecraftAccountsChanged.emit([])

    @Slot(result=list)
    def getMinecraftAccounts(self):
        config_data = cfg.read()
        mc_data = config_data.get("MinecraftAccount", {})
        accounts = mc_data.get("accounts", [])
        chosen_idx = mc_data.get("chosen", 0)
        
        result = []
        for i, acc in enumerate(accounts):
            uuid = acc.get("uuid", "")
            # Generate avatar URL if UUID is present
            avatar_url = f"https://minotar.net/avatar/{uuid}" if uuid else "../../icon/DefaultHead.png"
            result.append({
                "index": i,
                "name": acc.get("username", "Unknown"),
                "type": acc.get("type", "Offline"),
                "uuid": uuid,
                "avatarUrl": avatar_url,
                "isDefault": (i == chosen_idx)
            })
        return result

    @Slot(int)
    def setDefaultMinecraftAccount(self, index):
        config_data = cfg.read()
        if "MinecraftAccount" not in config_data:
            config_data["MinecraftAccount"] = {}
        config_data["MinecraftAccount"]["chosen"] = index
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Set default Minecraft account to index: {index}")
        self.minecraftAccountsChanged.emit([])

    @Slot()
    def manageAccountOnWebsite(self):
        QDesktopServices.openUrl(QUrl("https://passport.bloret.net/"))

    @Slot()
    def syncAccountFromPassPort(self):
        from modules.Bloret_PassPort import sync_bloret_passport_account_to_mc
        print("Requested sync account from PassPort")
        def run_sync():
            try:
                success = sync_bloret_passport_account_to_mc(None)
                if success:
                    self.minecraftAccountsChanged.emit([])
                    self.syncStatusChanged.emit("success")
                else:
                    self.syncStatusChanged.emit("error: 同步失败，请检查是否已登录 Bloret PassPort")
            except Exception as e:
                print(f"Error syncing accounts: {e}")
                self.syncStatusChanged.emit(f"error: {str(e)}")
        threading.Thread(target=run_sync, daemon=True).start()

    @Slot(result=str)
    def getIpv6Address(self):
        from modules.setup_ui import get_ipv6_address
        addr = get_ipv6_address()
        return addr if addr else "无法获取 IPv6 地址"

    @Slot(result=str)
    def checkIpv6Address(self):
        return self.getIpv6Address()

    @Slot()
    def takeScreenCut(self):
        """截图功能"""
        from modules.ShortCut import ScreenShortCut
        from PySide6.QtCore import QTimer
        print("Requested screenshot")
        # 使用 QTimer.singleShot 在主线程中执行截图，避免线程问题
        QTimer.singleShot(0, lambda: ScreenShortCut())

    @Slot(str, str)
    def startEasytierWithConfig(self, port, password):
        from modules.easytier import StartEasytierServer
        print(f"Starting EasyTier for MC port {port} with password {password}")
        
        config_data = cfg.read()
        if not config_data.get("Bloret_PassPort_Login"):
            self.easytierStatusChanged.emit("未登录", "请先在通行证页面登录")
            return

        username = config_data.get("Bloret_PassPort_UserName", "")
        easytier_name = "BLClient" + username
        
        def run_et():
            self.easytierStatusChanged.emit("正在启动", "请稍候...")
            res = StartEasytierServer(easytier_name, password)
            if "." in res: # Success
                self.easytierStatusChanged.emit("已连接", f"您的虚拟 IP: {res}\n共享端口: {port}")
            else:
                self.easytierStatusChanged.emit("错误", res)
        threading.Thread(target=run_et, daemon=True).start()

    @Slot(str, str)
    def joinEasytierWithConfig(self, host_name, password):
        # In EasyTier, joining is basically starting a server with same name/secret
        # But for the UI we might want to distinguish.
        self.startEasytierWithConfig("25565", password) # Join often doesn't need port redirect for the joiner

    @Slot(result=str)
    def getEasytierStatusTitle(self):
        return "未连接"

    @Slot(result=str)
    def getEasytierStatusDesc(self):
        return "您尚未连接到 Easytier 网络"

    @Slot(result=str)
    def getEasytierLinkTip(self):
        return ""

    @Slot(result=str)
    def getEasytierLinkShow(self):
        return ""

    @Slot(str)
    def openUrl(self, url):
        print(f"Requested to open URL: {url}")
        
    @Slot()
    def joinQQBloret(self):
        from modules.links import open_qq_link
        open_qq_link()

    @Slot()
    def joinQQCommunity(self):
        from modules.links import open_BLC_qq_link
        open_BLC_qq_link()

    @Slot()
    def openGithubOrg(self):
        from modules.links import open_github_bloret
        open_github_bloret()

    @Slot()
    def openGithubRepo(self):
        from modules.links import open_github_bloret_Launcher
        open_github_bloret_Launcher()

class LauncherV2(RinUIWindow):
    def __init__(self):
        super().__init__()
        
        # Inject Backend to QML BEFORE loading
        self.backend = Backend()
        self.backend.setBackendParent(self)
        self.engine.rootContext().setContextProperty("Backend", self.backend)
        
        qml_file = SCRIPT_DIR / "qml" / "main.qml"
        self.load(str(qml_file))
        
        icon_path = SCRIPT_DIR / "bloret.ico"
        if icon_path.exists():
            self.setIcon(str(icon_path))
        self.setProperty("title", "Bloret Launcher v2")

if __name__ == "__main__":
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # app is already created at the top
    launcher = LauncherV2()
    sys.exit(app.exec())
