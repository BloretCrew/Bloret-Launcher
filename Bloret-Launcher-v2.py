import sys
import os
from pathlib import Path

# Add the local directory to handle imports like 'import RinUI' correctly
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from PySide6.QtCore import QLocale, Qt, QTranslator, QObject, Slot, Signal, Property, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog

import RinUI
from RinUI import RinUIWindow

import random
import threading
import subprocess
import json
import modules.config as cfg
import modules.globals as BLglobals
from modules.launch import Get_Run_Script
from modules.chafuwang import getServerData
from modules.setup_ui import get_all_launch_items, scan_java_paths
from modules.i18n import i18nText
from modules.Bloriko import AskBloriko

class Backend(QObject):
    """
    Python Backend to interact with QML.
    Later, we will migrate all Bloret-Launcher.py logic here.
    """
    serverInfoChanged = Signal(dict)
    activityInfoChanged = Signal(dict)
    blorikoResponseReceived = Signal(str)
    queryResultReceived = Signal(dict)
    easytierStatusChanged = Signal(str, str) # title, description
    modrinthResultsReceived = Signal(list)

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
        items = get_all_launch_items()
        # QML friendly list
        qml_items = []
        for item in items:
            qml_items.append({
                "name": item["name"],
                "type": item["type"],
                "path": item["path"]
            })
        return qml_items

    @Slot(str, bool)
    def askBloriko(self, question, deep_think):
        print(f"Bloriko request: '{question}', deep think: {deep_think}")
        def run_ask():
            try:
                config_data = cfg.read()
                response = AskBloriko(question, config_data, deepthink=deep_think)
                self.blorikoResponseReceived.emit(response)
            except Exception as e:
                self.blorikoResponseReceived.emit(f"Error: {str(e)}")
        threading.Thread(target=run_ask, daemon=True).start()

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

    @Slot(result=str)
    def getBloretVersion(self):
        return "1.0.0 (Mock)"

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
        from modules.modrinth import Get_Mod_File_Download_Url
        print(f"Requested download mod: {mod_id}")
        # Note: This is a simplified version. Usually needs loader/version info.
        def run_download():
            try:
                url = Get_Mod_File_Download_Url(mod_id)
                if url:
                    print(f"Found download URL: {url}")
                    # Here we would normally download the file...
                    # For now just open it in browser or log it
                    QDesktopServices.openUrl(QUrl(url))
                else:
                    print(f"Could not find download URL for {mod_id}")
            except Exception as e:
                print(f"Error downloading mod: {e}")
        threading.Thread(target=run_download, daemon=True).start()

    @Slot(str, bool)
    def askBlorikoForMods(self, query, deep_think):
        from modules.Bloriko import AskBloriko
        print(f"Bloriko Mod request: '{query}', deep think: {deep_think}")
        def run_bloriko():
            try:
                # AskBloriko(self, text, callback, model="Bloriko-V1")
                # We need a callback that emits the signal
                def callback(response):
                    self.blorikoResponseReceived.emit(response)
                
                AskBloriko(None, query, callback) # Passing None as self since it might expect a widget
            except Exception as e:
                print(f"Error asking Bloriko: {e}")
                self.blorikoResponseReceived.emit(f"Error: {e}")
        threading.Thread(target=run_bloriko, daemon=True).start()

    @Slot(result=str)
    def getBloretPassPortUserName(self):
        return "未登录 (Mock)"

    @Slot()
    def loginBloretPassPort(self):
        print("Requested login to Bloret PassPort")

    @Slot()
    def logoutBloretPassPort(self):
        print("Requested logout from Bloret PassPort")

    @Slot()
    def refreshMinecraftAccounts(self):
        print("Requested refresh Minecraft accounts")

    @Slot(result=list)
    def getMinecraftAccounts(self):
        return [
            {"name": "Steve", "type": "离线账户", "id": "acc-1", "isDefault": True},
            {"name": "Notch", "type": "微软账户", "id": "acc-2", "isDefault": False}
        ]

    @Slot(str)
    def setDefaultMinecraftAccount(self, acc_id):
        print(f"Requested set default Minecraft account: {acc_id}")

    @Slot()
    def manageAccountOnWebsite(self):
        print("Requested manage account on website")

    @Slot()
    def syncAccountFromPassPort(self):
        print("Requested sync account from PassPort")

    @Slot(result=str)
    def getIpv6Address(self):
        return "------:------:------:------:------:------:------:------"

    @Slot(result=str)
    def checkIpv6Address(self):
        print("Requested check IPv6 address")
        return "2001:0db8:85a3:0000:0000:8a2e:0370:7334"

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

    @Slot()
    def startEasytierHost(self):
        print("Requested start Easytier host")

    @Slot()
    def startEasytierClient(self):
        print("Requested start Easytier client")

    @Slot(str)
    def openUrl(self, url):
        print(f"Requested to open URL: {url}")
        
    @Slot()
    def joinQQBloret(self):
        print("Requested join QQ Bloret group")

    @Slot()
    def joinQQCommunity(self):
        print("Requested join QQ Software Community group")

    @Slot()
    def openGithubOrg(self):
        print("Requested open Github Org")

    @Slot()
    def openGithubRepo(self):
        print("Requested open Github Repo")

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
    app = QApplication(sys.argv)
    
    launcher = LauncherV2()
    sys.exit(app.exec())
