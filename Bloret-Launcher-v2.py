import sys
import os
from pathlib import Path

# Add the local directory to handle imports like 'import RinUI' correctly
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from PySide6.QtCore import QLocale, Qt, QTranslator, QObject, Slot, Signal, Property
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

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
from modules.setup_ui import get_all_launch_items
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
        print("Requested open .minecraft directory")

    @Slot()
    def openLogDir(self):
        print("Requested open log directory")

    @Slot()
    def clearLogs(self):
        print("Requested clear logs")

    @Slot()
    def takeScreenCut(self):
        print("Requested take screen cut")

    @Slot()
    def setScreenCutShortcut(self):
        print("Requested set screen cut shortcut")

    @Slot(str, result=str)
    def queryUUID(self, name):
        print(f"Requested query UUID for name: {name}")
        return "1234abcd-mock-uuid"

    @Slot(str, result=str)
    def queryName(self, uuid):
        print(f"Requested query name for UUID: {uuid}")
        return "MockPlayerName"

    @Slot(str, result=str)
    def querySkin(self, uuid):
        print(f"Requested query skin for UUID: {uuid}")
        return "http://mock.skin.url/skin.png"

    @Slot(str, result=str)
    def queryCape(self, uuid):
        print(f"Requested query cape for UUID: {uuid}")
        return "http://mock.cape.url/cape.png"

    @Slot(str)
    def copyToClipboard(self, text):
        from PySide6.QtGui import QGuiApplication
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        print(f"Copied to clipboard: {text}")

    @Slot()
    def openModrinth(self):
        print("Requested open Modrinth")

    @Slot(str, bool)
    def askBlorikoForMods(self, query, deep_think):
        print(f"Bloriko Mod request: '{query}', deep think: {deep_think}")

    @Slot(str)
    def searchModrinth(self, query):
        print(f"Modrinth search request: '{query}'")

    @Slot(result=list)
    def getMockModList(self):
        return [
            {"name": "Sodium", "description": "Modern rendering engine", "id": "sodium-1"},
            {"name": "Iris", "description": "Shaders for Fabric", "id": "iris-2"},
            {"name": "Lithium", "description": "General-purpose optimization mod", "id": "lithium-3"}
        ]

    @Slot(str)
    def downloadMod(self, mod_id):
        print(f"Requested download mod: {mod_id}")

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
