# 0. 先获取 IP 地址
import modules.IP


import sys
import os
import faulthandler
from pathlib import Path

# Add the local directory to handle imports like 'import RinUI' correctly
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Create the QApplication early so it can be used in shims and module imports
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QSystemTrayIcon
from PySide6.QtCore import QLocale, Qt, QTranslator, QObject, Slot, Signal, Property, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QDesktopServices, QAction, QPixmap, QPainter, QCursor

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
app = QApplication(sys.argv)


def _enable_fault_logging():
    """记录 Python/原生崩溃堆栈，避免仅看到退出码。"""
    try:
        appdata = Path(os.getenv("APPDATA", str(SCRIPT_DIR)))
        log_dir = appdata / "Bloret-Launcher" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        fault_path = log_dir / "python-faulthandler.log"

        stream = open(fault_path, "a", encoding="utf-8")
        stream.write("\n===== Bloret Launcher fault handler enabled =====\n")
        faulthandler.enable(file=stream, all_threads=True)
        return stream
    except Exception as e:
        print(f"Failed to enable faulthandler logging: {e}")
        return None


_FAULT_LOG_STREAM = _enable_fault_logging()

# --- Finished Full PySide6 Migration ---
# All modules have been refactored to use PySide6 and RinUI directly.

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
from modules.plugin import list_installed_plugins, uninstall_plugin, get_plugin_root
import modules.web
import modules.links as links
import socket
import send2trash


def get_app_icon_path(for_tray=False):
    """根据平台返回应用图标路径：macOS 使用 Bloret-Fluent.png；程序坞/标题栏使用带留白版本，托盘保留原始图标。"""
    if sys.platform == "darwin":
        mac_icon = SCRIPT_DIR / "Bloret-Fluent.png"
        if mac_icon.exists():
            if for_tray:
                return mac_icon

            # macOS 程序坞视觉尺寸修正：生成带透明留白的图标，避免看起来比其他应用更大
            padded_icon = SCRIPT_DIR / "cache" / "Bloret-Fluent-dock.png"
            try:
                src = QPixmap(str(mac_icon))
                if not src.isNull():
                    side = max(src.width(), src.height())
                    canvas = QPixmap(side, side)
                    canvas.fill(Qt.GlobalColor.transparent)

                    target_side = int(side * 0.84)
                    scaled = src.scaled(
                        target_side,
                        target_side,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )

                    painter = QPainter(canvas)
                    x = (side - scaled.width()) // 2
                    y = (side - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()

                    padded_icon.parent.mkdir(parents=True, exist_ok=True)
                    if canvas.save(str(padded_icon), "PNG"):
                        return padded_icon
            except Exception as e:
                print(f"Failed to generate padded mac icon: {e}")

            return mac_icon

    default_icon = SCRIPT_DIR / "bloret.ico"
    if default_icon.exists():
        return default_icon

    # 兜底：如果默认图标不存在，macOS 再尝试 fluent 图标
    fallback_mac_icon = SCRIPT_DIR / "Bloret-Fluent.png"
    if fallback_mac_icon.exists():
        return fallback_mac_icon

    return None

class Backend(QObject):
    """
    Python Backend to interact with QML.
    Later, we will migrate all Bloret-Launcher.py logic here.
    """
    modrinthResultsReceived = Signal(list)
    minecraftAccountsChanged = Signal(list, arguments=['accounts'])
    logsCleared = Signal()
    easytierStatusChanged = Signal(str, str)
    serverInfoChanged = Signal(dict)
    queryResultReceived = Signal(dict)
    blorikoResponseReceived = Signal(str)
    syncStatusChanged = Signal(str)
    languageChanged = Signal()
    downloadDialogRequested = Signal(str)
    downloadProgressUpdated = Signal(float, str, str, str, str)
    downloadDialogClosed = Signal()
    downloadPaused = Signal(bool)
    coreManagerRequested = Signal(str, dict)
    activityInfoChanged = Signal(dict)
    launchDialogRequested = Signal(str)
    launchProgressUpdated = Signal(float, str, str)
    launchDialogClosed = Signal()

    def __init__(self):
        super().__init__()
        self._server_info = {}
        self._activity_info = BLglobals.BL_Activity
        self._last_core_manager_request_time = 0  # 防止重复请求
        self._is_launching = False
        self._launch_session_id = 0
        self._screenshot_widget = None

    def setBackendParent(self, parent):
        self.parent = parent

    @Slot(result=bool)
    def handleWindowCloseRequest(self):
        parent = getattr(self, "parent", None)
        if parent and hasattr(parent, "handle_close_request_from_qml"):
            try:
                return bool(parent.handle_close_request_from_qml())
            except Exception as e:
                print(f"handleWindowCloseRequest failed: {e}")
        return False

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

        if self._is_launching:
            print("Launch request ignored: another launch is already in progress")
            return

        self._is_launching = True
        self._launch_session_id += 1
        launch_session_id = self._launch_session_id
        self.launchDialogRequested.emit(f"正在启动 {version}")

        def is_current_session():
            return launch_session_id == self._launch_session_id

        def emit_progress(progress, status, detail=""):
            if not is_current_session():
                return
            self.launchProgressUpdated.emit(float(progress), status, detail)

        def finish_launch(close_dialog=False):
            if not is_current_session():
                return
            self._is_launching = False
            if close_dialog:
                self.launchDialogClosed.emit()

        def run_launch():
            try:
                from modules.Bloret_PassPort import refresh_minecraft_token, sync_bloret_passport_account_to_mc
                from modules.launch import monitor_minecraft_window

                emit_progress(5, f"正在准备启动环境: {version}", "")

                emit_progress(20, "正在向 Bloret PassPort 刷新令牌...", "")
                refresh_ok = refresh_minecraft_token()
                if refresh_ok:
                    emit_progress(35, "令牌刷新完成", "")
                else:
                    emit_progress(35, "令牌刷新未完成，继续使用现有状态", "")

                emit_progress(50, "正在重新获取 Minecraft 档案数据...", "")
                sync_ok = sync_bloret_passport_account_to_mc(parent_window=None)
                if sync_ok:
                    self.minecraftAccountsChanged.emit([])
                    emit_progress(65, "档案数据更新完成", "")
                else:
                    emit_progress(65, "档案同步失败，将使用本地缓存档案", "")

                emit_progress(80, "正在补全文件并解析启动参数...", "如有缺失文件会自动下载")
                launch_args, game_dir = Get_Run_Script(version)

                emit_progress(95, "正在执行启动命令...", "")
                print(f"Launching with args: {launch_args}")
                subprocess.Popen(launch_args, cwd=game_dir)

                emit_progress(97, "启动命令已执行，正在等待 Minecraft 窗口出现...", "")

                window_found_event = threading.Event()

                def on_window_found():
                    if window_found_event.is_set():
                        return
                    window_found_event.set()
                    emit_progress(100, "已检测到 Minecraft 窗口，启动完成", "")
                    finish_launch(close_dialog=True)

                monitor_minecraft_window(version, callback=on_window_found)

                def monitor_timeout_guard():
                    if window_found_event.wait(310):
                        return
                    emit_progress(100, "等待 Minecraft 窗口超时", "未检测到窗口，你可以继续后台等待或关闭此对话框后重试")
                    finish_launch(close_dialog=False)

                threading.Thread(target=monitor_timeout_guard, daemon=True).start()
            except Exception as e:
                print(f"Failed to launch: {e}")
                import traceback
                traceback.print_exc()
                emit_progress(100, f"启动失败: {e}", "")
                finish_launch(close_dialog=False)

        threading.Thread(target=run_launch, daemon=True).start()

    @Slot(result=dict)
    def getActivityInfo(self):
        return BLglobals.BL_Activity

    @Slot()
    def refreshActivityInfo(self):
        """从 API 刷新活动信息"""
        from modules.BLServer import get_latest_version
        def update_activity():
            try:
                _, _ = get_latest_version()
                # BL_Activity 已在 get_latest_version 中更新
                # 如果图标是远程 URL，则下载缓存到本地文件
                icon_url = BLglobals.BL_Activity.get("icon", "")
                if icon_url.startswith("http"):
                    try:
                        import requests, hashlib
                        from PySide6.QtCore import QUrl
                        resp = requests.get(icon_url, timeout=5)
                        if resp.status_code == 200:
                            # compute hash for filename
                            h = hashlib.md5(icon_url.encode('utf-8')).hexdigest()
                            cache_dir = os.path.join(SCRIPT_DIR, "cache")
                            os.makedirs(cache_dir, exist_ok=True)
                            local_path = os.path.join(cache_dir, f"activity_{h}.png")
                            with open(local_path, "wb") as imgf:
                                imgf.write(resp.content)
                            # convert to file URL for QML
                            url = QUrl.fromLocalFile(local_path).toString()
                            BLglobals.BL_Activity["icon"] = url
                            icon_path = url
                        else:
                            icon_path = icon_url
                    except Exception as e:
                        print(f"Failed to download activity icon: {e}")
                        icon_path = icon_url
                else:
                    # non-http value might be local path; convert to file URL too
                    from PySide6.QtCore import QUrl
                    if icon_url:
                        BLglobals.BL_Activity["icon"] = QUrl.fromLocalFile(icon_url).toString()
                        icon_path = QUrl.fromLocalFile(icon_url).toString()
                # else icon_path remains whatever returned
                self._activity_info = BLglobals.BL_Activity
                self.activityInfoChanged.emit(self._activity_info)
            except Exception as e:
                print(f"Error refreshing activity info: {e}")
        
        threading.Thread(target=update_activity, daemon=True).start()

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

    @Slot(str)
    def selectLaunchItem(self, name):
        try:
            config_data = cfg.read()
            config_data['ChoosedRun'] = name
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"Selected launch item: {name}")
        except Exception as e:
            print(f"Error selecting launch item: {e}")

    @Slot(str)
    def openVersionFolder(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_path = os.path.join(minecraft_dir, "versions", versionName)
            if os.path.exists(version_path):
                os.startfile(version_path)
            else:
                print(f"Version folder not found: {version_path}")
        except Exception as e:
            print(f"Error opening version folder: {e}")

    @Slot(str, str)
    def openSubFolder(self, versionName, subPath):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            base_path = os.path.join(minecraft_dir, "versions", versionName)
            target_path = os.path.join(base_path, subPath)
            
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)
            
            os.startfile(target_path)
        except Exception as e:
            print(f"Error opening sub folder: {e}")

    @Slot(str)
    def deleteCustomItem(self, name):
        try:
            if name in BLglobals.customize_list:
                BLglobals.customize_list.remove(name)
                config_data = cfg.read()
                config_data['customize_list'] = BLglobals.customize_list
                with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                print(f"Deleted custom item: {name}")
        except Exception as e:
            print(f"Error deleting custom item: {e}")

    @Slot(str, str)
    def renameCustomItem(self, oldName, newName):
        try:
            if oldName in BLglobals.customize_list:
                idx = BLglobals.customize_list.index(oldName)
                BLglobals.customize_list[idx] = newName
                config_data = cfg.read()
                config_data['customize_list'] = BLglobals.customize_list
                if config_data.get('ChoosedRun') == oldName:
                    config_data['ChoosedRun'] = newName
                with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                print(f"Renamed custom item: {oldName} -> {newName}")
        except Exception as e:
            print(f"Error renaming custom item: {e}")

    @Slot(str)
    def showCoreManager(self, versionName):
        try:
            import time
            current_time = time.time()
            # 防止在100ms内重复触发请求
            if current_time - self._last_core_manager_request_time < 0.1:
                return
            
            self._last_core_manager_request_time = current_time
            
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            core_data = {}
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
                    core_data = full_data.get("versions", {}).get(versionName, {})
            
            self.coreManagerRequested.emit(versionName, core_data)
        except Exception as e:
            print(f"Error showing core manager: {e}")

    @Slot(str, result="QVariant")
    def getCoreData(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
                    return full_data.get("versions", {}).get(versionName, {})
            return {}
        except Exception as e:
            print(f"Error getting core data: {e}")
            return {}

    @Slot(str, "QVariant")
    def saveCoreData(self, versionName, data):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            full_data = {"versions": {}}
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
            
            new_name = data.get("name", versionName)
            
            if new_name != versionName:
                old_path = os.path.join(minecraft_dir, "versions", versionName)
                new_path = os.path.join(minecraft_dir, "versions", new_name)
                if os.path.exists(new_path):
                    print("Target name already exists")
                    return
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                if versionName in full_data.get("versions", {}):
                    del full_data["versions"][versionName]
            
            full_data["versions"][new_name] = {
                "Fabric": data.get("Fabric", False),
                "version": data.get("version", new_name),
                "icon": data.get("icon", ""),
                "server": data.get("server", ""),
                "jvmArgs": data.get("jvmArgs", "")
            }
            
            with open(bl_json_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)
            
            print(f"Core data saved for: {new_name}")
        except Exception as e:
            print(f"Error saving core data: {e}")

    @Slot(str, result=str)
    def selectCoreIcon(self, versionName):
        try:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "选择图标",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                return file_path
            return ""
        except Exception as e:
            print(f"Error selecting icon: {e}")
            return ""

    @Slot(str, result=bool)
    def confirmDeleteCore(self, versionName):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除 Minecraft 版本 {versionName}。删除后可在系统回收站中找到。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                config_data = cfg.read()
                minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
                version_path = os.path.join(minecraft_dir, "versions", versionName)
                
                if os.path.exists(version_path):
                    if send2trash:
                        send2trash.send2trash(version_path)
                    else:
                        import shutil
                        shutil.rmtree(version_path)
                
                bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
                if os.path.exists(bl_json_path):
                    with open(bl_json_path, "r", encoding="utf-8") as f:
                        full_data = json.load(f)
                    if versionName in full_data.get("versions", {}):
                        del full_data["versions"][versionName]
                    with open(bl_json_path, "w", encoding="utf-8") as f:
                        json.dump(full_data, f, ensure_ascii=False, indent=4)
                
                print(f"Core deleted: {versionName}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting core: {e}")
            return False

    @Slot(str, result="QVariant")
    def getServers(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_servers_dat = os.path.join(minecraft_dir, "versions", versionName, "servers.dat")
            root_servers_dat = os.path.join(minecraft_dir, "servers.dat")
            
            read_path = ""
            if os.path.exists(version_servers_dat):
                read_path = version_servers_dat
            elif os.path.exists(root_servers_dat):
                read_path = root_servers_dat
            
            if read_path:
                return self._parse_servers_dat(read_path)
            return []
        except Exception as e:
            print(f"Error getting servers: {e}")
            return []

    def _parse_servers_dat(self, path):
        import struct
        import io
        servers = []
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            def read_string(stream):
                length = struct.unpack('>h', stream.read(2))[0]
                if length < 0:
                    return ""
                return stream.read(length).decode('utf-8')
            
            def read_tag(stream, has_name=True):
                tag_type = struct.unpack('>b', stream.read(1))[0]
                if tag_type == 0:
                    return None, None
                
                name = ""
                if has_name:
                    name = read_string(stream)
                
                if tag_type == 8:
                    return name, read_string(stream)
                elif tag_type == 9:
                    list_type = struct.unpack('>b', stream.read(1))[0]
                    list_len = struct.unpack('>i', stream.read(4))[0]
                    items = []
                    for _ in range(list_len):
                        _, val = read_tag(stream, False)
                        items.append(val)
                    return name, items
                elif tag_type == 10:
                    compound = {}
                    while True:
                        sub_name, sub_val = read_tag(stream)
                        if sub_name is None:
                            break
                        compound[sub_name] = sub_val
                    return name, compound
                return name, None
            
            stream = io.BytesIO(data)
            _, servers_data = read_tag(stream)
            
            if servers_data and 'servers' in servers_data:
                for server in servers_data['servers']:
                    icon_str = server.get('icon', '')
                    # ensure string is clean and properly prefixed for QML
                    if isinstance(icon_str, str):
                        icon_str = icon_str.strip()
                        if icon_str and not icon_str.startswith('data:'):
                            icon_str = 'data:image/png;base64,' + icon_str
                    else:
                        icon_str = ''

                    servers.append({
                        'name': server.get('name', 'Minecraft Server'),
                        'ip': server.get('ip', ''),
                        'icon': icon_str
                    })
        except Exception as e:
            print(f"Error parsing servers.dat: {e}")
        return servers

    @Slot(str, str, str)
    def addServer(self, versionName, name, ip):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_servers_dat = os.path.join(minecraft_dir, "versions", versionName, "servers.dat")
            
            os.makedirs(os.path.dirname(version_servers_dat), exist_ok=True)
            
            servers = self._parse_servers_dat(version_servers_dat) if os.path.exists(version_servers_dat) else []
            servers.append({'name': name, 'ip': ip, 'icon': ''})
            
            self._save_servers_dat(version_servers_dat, servers)
            print(f"Server added: {name}")
        except Exception as e:
            print(f"Error adding server: {e}")

    def _save_servers_dat(self, path, servers):
        import struct
        import io
        try:
            stream = io.BytesIO()
            
            def write_string(s):
                encoded = s.encode('utf-8')
                stream.write(struct.pack('>h', len(encoded)))
                stream.write(encoded)
            
            stream.write(struct.pack('>b', 10))
            write_string("")
            
            stream.write(struct.pack('>b', 9))
            write_string("servers")
            stream.write(struct.pack('>b', 10))
            stream.write(struct.pack('>i', len(servers)))
            
            for server in servers:
                stream.write(struct.pack('>b', 10))
                write_string("")
                
                stream.write(struct.pack('>b', 8))
                write_string("name")
                write_string(server.get('name', ''))
                
                stream.write(struct.pack('>b', 8))
                write_string("ip")
                write_string(server.get('ip', ''))
                
                if server.get('icon'):
                    stream.write(struct.pack('>b', 8))
                    write_string("icon")
                    write_string(server['icon'])
                
                stream.write(struct.pack('>b', 0))
            
            stream.write(struct.pack('>b', 0))
            
            with open(path, 'wb') as f:
                f.write(stream.getvalue())
            print(f"Saved {len(servers)} servers to {path}")
        except Exception as e:
            print(f"Error saving servers.dat: {e}")

    @Slot(str, result="QVariant")
    def getMods(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            mods_dir = os.path.join(minecraft_dir, "versions", versionName, "mods")
            
            if not os.path.exists(mods_dir):
                os.makedirs(mods_dir, exist_ok=True)
                return []
            
            mods = []
            import zipfile
            import base64
            for filename in os.listdir(mods_dir):
                file_path = os.path.join(mods_dir, filename)
                if os.path.isdir(file_path):
                    continue
                
                is_disabled = filename.endswith('.disabled')
                if not (filename.endswith('.jar') or filename.endswith('.jar.disabled')):
                    continue
                
                mod_data = {
                    "name": filename,
                    "path": file_path,
                    "filename": filename,
                    "version": "",
                    "description": "无描述",
                    "icon": "",
                    "enabled": not is_disabled
                }
                
                try:
                    if zipfile.is_zipfile(file_path):
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            if 'fabric.mod.json' in zf.namelist():
                                with zf.open('fabric.mod.json') as f:
                                    meta = json.load(f)
                                    mod_data["name"] = meta.get("name", meta.get("id", filename))
                                    mod_data["version"] = meta.get("version", "")
                                    mod_data["description"] = meta.get("description", "")[:100]
                                    
                                    icon_path = meta.get("icon")
                                    if icon_path and isinstance(icon_path, str) and icon_path in zf.namelist():
                                        icon_data = zf.read(icon_path)
                                        mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                                    elif f"assets/{meta.get('id')}/icon.png" in zf.namelist():
                                        icon_data = zf.read(f"assets/{meta.get('id')}/icon.png")
                                        mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                            elif 'mcmod.info' in zf.namelist():
                                with zf.open('mcmod.info') as f:
                                    meta_list = json.load(f)
                                    if meta_list and isinstance(meta_list, list):
                                        meta = meta_list[0]
                                        mod_data["name"] = meta.get("name", filename)
                                        mod_data["version"] = meta.get("version", "")
                                        mod_data["description"] = meta.get("description", "")[:100]
                                        
                                        logo = meta.get("logoFile")
                                        if logo and logo in zf.namelist():
                                            icon_data = zf.read(logo)
                                            mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                except Exception as e:
                    print(f"Error reading mod {filename}: {e}")
                
                mods.append(mod_data)
            
            return mods
        except Exception as e:
            print(f"Error getting mods: {e}")
            return []

    @Slot(str, bool)
    def toggleMod(self, path, enabled):
        try:
            if not os.path.exists(path):
                return
            
            dirname, filename = os.path.split(path)
            
            if enabled:
                if filename.endswith('.disabled'):
                    new_filename = filename[:-9]
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
            else:
                if not filename.endswith('.disabled'):
                    new_filename = filename + '.disabled'
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
        except Exception as e:
            print(f"Error toggling mod: {e}")

    @Slot(str, result=bool)
    def deleteMod(self, path):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除 Mod: {os.path.basename(path)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if send2trash:
                    send2trash.send2trash(path)
                else:
                    os.remove(path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting mod: {e}")
            return False

    @Slot(str, result="QVariant")
    def getResourcePacks(self, versionName):
        try:
            import base64
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            packs_dir = os.path.join(minecraft_dir, "versions", versionName, "resourcepacks")
            
            if not os.path.exists(packs_dir):
                os.makedirs(packs_dir, exist_ok=True)
                return []
            
            packs = []
            import zipfile
            for filename in os.listdir(packs_dir):
                file_path = os.path.join(packs_dir, filename)
                
                if not (os.path.isdir(file_path) or filename.endswith('.zip')):
                    continue
                
                pack_data = {
                    "name": filename,
                    "path": file_path,
                    "description": "无描述",
                    "icon": ""
                }
                
                try:
                    if os.path.isdir(file_path):
                        mcmeta_path = os.path.join(file_path, "pack.mcmeta")
                        icon_path = os.path.join(file_path, "pack.png")
                        
                        if os.path.exists(mcmeta_path):
                            with open(mcmeta_path, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                                desc = meta.get("pack", {}).get("description", "")
                                if isinstance(desc, dict):
                                    desc = desc.get("translate", str(desc))
                                pack_data["description"] = str(desc)[:100]
                        
                        if os.path.exists(icon_path):
                            # read bytes and convert to data URI
                            try:
                                with open(icon_path, 'rb') as imgf:
                                    b64 = base64.b64encode(imgf.read()).decode('utf-8')
                                    pack_data["icon"] = f"data:image/png;base64,{b64}"
                            except Exception as ee:
                                print(f"Error reading resource pack icon {icon_path}: {ee}")
                            
                    elif zipfile.is_zipfile(file_path):
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            if "pack.mcmeta" in zf.namelist():
                                with zf.open("pack.mcmeta") as f:
                                    meta = json.load(f)
                                    desc = meta.get("pack", {}).get("description", "")
                                    if isinstance(desc, dict):
                                        desc = desc.get("translate", str(desc))
                                    pack_data["description"] = str(desc)[:100]
                            if "pack.png" in zf.namelist():
                                try:
                                    icon_bytes = zf.read("pack.png")
                                    b64 = base64.b64encode(icon_bytes).decode('utf-8')
                                    pack_data["icon"] = f"data:image/png;base64,{b64}"
                                except Exception as ee:
                                    print(f"Error extracting pack.png from {filename}: {ee}")
                except Exception as e:
                    print(f"Error reading resource pack {filename}: {e}")
                
                packs.append(pack_data)
            
            return packs
        except Exception as e:
            print(f"Error getting resource packs: {e}")
            return []

    @Slot(str, result=bool)
    def deleteResourcePack(self, path):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除资源包: {os.path.basename(path)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if send2trash:
                    send2trash.send2trash(path)
                else:
                    import shutil
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting resource pack: {e}")
            return False

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

    # 版本缓存
    _versions_cache = {}
    
    @Slot(str, result=list)
    def getVersionsByCategory(self, category):
        """根据类别返回版本列表"""
        try:
            print(f"[DEBUG] Getting versions for category: {category}")
            
            if category == "百络谷支持版本":
                print(f"[DEBUG] Returning Bloret supported versions: {len(BLglobals.ver_id_bloret)} items")
                return BLglobals.ver_id_bloret
            
            # 检查是否已有一网打尽的标志，或者直接检查缓存
            if category in self._versions_cache:
                print(f"[DEBUG] Found cached versions for {category}: {len(self._versions_cache[category])} items")
                return self._versions_cache[category]
            
            # 如果之前已经获取过清单但这个分类不在缓存里（说明是无效分类或者新分类），直接返回空
            if getattr(self, '_manifest_fetched', False):
                 return []

            # 从BMCLAPI获取版本清单
            api_url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
            print(f"[DEBUG] Fetching version manifest from: {api_url}")
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                all_versions = data.get("versions", [])
                print(f"[DEBUG] Total versions fetched: {len(all_versions)}")
                
                # 一次性处理所有分类并缓存
                self._versions_cache["正式版本"] = [v["id"] for v in all_versions if v.get("type") == "release"]
                self._versions_cache["快照版本"] = [v["id"] for v in all_versions if v.get("type") == "snapshot"]
                # 把 old_alpha 和 old_beta 都归为远古版本
                self._versions_cache["远古版本"] = [v["id"] for v in all_versions if v.get("type") in ["old_alpha", "old_beta"]]
                
                self._manifest_fetched = True
                
                result = self._versions_cache.get(category, [])
                print(f"[DEBUG] Cached result for {category}: {len(result)} items")
                return result
            else:
                print(f"[ERROR] Failed to fetch versions: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"[ERROR] Exception getting versions by category {category}: {type(e).__name__}: {e}")
            return []

    # Removed incorrect getFabricVersions implementation here to use the correct one below

    @Slot(result=list)
    def getJavaDownloadVersions(self):
        from modules.java import java_versions
        return list(java_versions.keys())

    @Slot(str, str, result='QVariant')
    def validateVersionName(self, baseVersion, name):
        """Validate name for installation: returns dict with valid, error, exists"""
        result = {"valid": True, "error": "", "exists": False}
        try:
            # empty
            if not name or name.strip() == "":
                result["valid"] = False
                result["error"] = "版本名不能为空"
                return result
            # invalid characters
            invalid = r"[\\/:\*\?\"<>|]"
            import re
            if re.search(invalid, name):
                result["valid"] = False
                result["error"] = "版本名不能包含 \\ / : * ? \" < > | 等字符"
                return result
            # reserved names
            reserved = ['CON','PRN','AUX','NUL'] + [f'COM{i}' for i in range(1,10)] + [f'LPT{i}' for i in range(1,10)]
            if name.upper() in reserved:
                result["valid"] = False
                result["error"] = "版本名为 Windows 保留字"
                return result
            # existence
            items = self.getLaunchItems()
            for item in items:
                if item.get("name") == name:
                    result["exists"] = True
                    break
        except Exception as e:
            print(f"validation exception: {e}")
        return result

    @Slot(str, str)
    def downloadVanilla(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Vanilla: {version} as {versionName}")
        title = f"正在下载 Minecraft {version}"
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, VersionName=versionName, backend=self)

    @Slot(str, str)
    def downloadFabric(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Fabric: {version} as {versionName}")
        title = f"正在下载 Minecraft {version} 和 Fabric Loader"
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, Fabric_Loader=True, VersionName=versionName, backend=self)

    @Slot()
    def toggleDownloadPause(self):
        from modules.install import toggle_current_download_pause
        toggle_current_download_pause()

    @Slot()
    def cancelDownload(self):
        from modules.install import cancel_current_download
        cancel_current_download()

    def updateDownloadProgress(self, progress, status, speed, downloaded, total):
        self.downloadProgressUpdated.emit(progress, status, speed, downloaded, total)

    def closeDownloadDialog(self):
        self.downloadDialogClosed.emit()

    def setDownloadPaused(self, paused):
        self.downloadPaused.emit(paused)

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

    @Slot(result=bool)
    def getShowAccountOnHome(self):
        config_data = cfg.read()
        return config_data.get('show_account_on_home', True)

    @Slot(bool)
    def setShowAccountOnHome(self, show):
        config_data = cfg.read()
        config_data['show_account_on_home'] = show
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Show account on home updated to: {show}")

    @Slot(result=bool)
    def getMinimizeToTrayOnClose(self):
        config_data = cfg.read()
        return config_data.get('minimize_to_tray_on_close', True)

    @Slot(bool)
    def setMinimizeToTrayOnClose(self, enabled):
        config_data = cfg.read()
        config_data['minimize_to_tray_on_close'] = enabled
        with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Minimize to tray on close updated to: {enabled}")

    @Slot(result=bool)
    def isSystemTrayAvailable(self):
        try:
            return QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            return False

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
                            "icon_url": hit.get("icon_url", ""),
                            "author": hit.get("author", ""),
                            "downloads": hit.get("downloads", 0),
                            "follows": hit.get("follows", 0),
                            "categories": hit.get("display_categories", [])
                        })
                self.modrinthResultsReceived.emit(results)
            except Exception as e:
                print(f"Error searching Modrinth: {e}")
                self.modrinthResultsReceived.emit([])
        threading.Thread(target=run_search, daemon=True).start()

    @Slot(str, str)
    def downloadMod(self, mod_id, version_name):
        """
        下载并安装模组
        
        Args:
            mod_id (str): 模组 ID 或 slug
            version_name (str): 目标版本名称
        """
        from modules.modrinth import Get_Mod_File_Download_Url
        print(f"Requested download mod: {mod_id} to {version_name}")
        
        def run_download():
            try:
                config_data = cfg.read()
                mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
                
                # 获取游戏版本
                game_version = None
                bl_json_path = os.path.join(mc_dir, "versions", ".BL.json")
                if os.path.exists(bl_json_path):
                    with open(bl_json_path, "r", encoding="utf-8") as f:
                        bl_data = json.load(f)
                        if version_name in bl_data.get("versions", {}):
                            ver_info = bl_data["versions"][version_name]
                            game_version = ver_info.get("version")
                
                if not game_version:
                    # 简单的 fallback，假设版本名以版本号开头
                    import re
                    match = re.match(r"^(\d+\.\d+(\.\d+)?)", version_name)
                    if match:
                        game_version = match.group(1)
                
                print(f"Detected game version: {game_version}")

                # 首先尝试以 mod_id 作为 slug 获取下载 URL
                url = Get_Mod_File_Download_Url(mod_id, loaders=["fabric"], game_versions=[game_version] if game_version else None)
                if url:
                    print(f"Found download URL: {url}")
                    # 获取 Minecraft 目录
                    
                    mods_dir = os.path.join(mc_dir, "versions", version_name, "mods")
                    
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

    @Slot(result=str)
    def getBloretPassPortUserName(self):
        config_data = cfg.read()
        if config_data.get('Bloret_PassPort_Login'):
            return config_data.get('Bloret_PassPort_UserName', 'Unknown')
        return "未登录"

    @Slot(result=bool)
    def getBloretPassPortLoginStatus(self):
        config_data = cfg.read()
        return config_data.get('Bloret_PassPort_Login', False)

    @Slot(result=str)
    def getPassPortName(self):
        return self.getBloretPassPortUserName()

    @Slot(result=str)
    def getPassPortAvatar(self):
        print(f"\n[getPassPortAvatar] 方法被调用")
        config_data = cfg.read()
        
        is_logged_in = config_data.get('Bloret_PassPort_Login')
        print(f"  登录状态: {is_logged_in}")
        if not is_logged_in:
            print(f"  未登录，返回空字符串")
            return ""
        
        username = config_data.get('Bloret_PassPort_UserName', '')
        print(f"  用户名: {username}")
        if not username:
            print(f"  用户名为空，返回空字符串")
            return ""
        
        cache_dir = os.path.join(BLglobals.cache_path, 'avatars')
        print(f"  缓存目录: {cache_dir}")
        try:
            os.makedirs(cache_dir, exist_ok=True)
            print(f"  缓存目录已创建")
        except Exception as e:
            print(f"  创建缓存目录失败: {e}")
        
        cache_file = os.path.join(cache_dir, f"{username}_passport.png")
        print(f"  缓存文件路径: {cache_file}")
        
        # 从 config.json 读取头像 URL
        avatar_url = config_data.get('Bloret_PassPort_Avatar', '')
        print(f"  存储的头像 URL: {avatar_url if avatar_url else '(空)'}")
        
        # 如果有有效的头像 URL，尝试下载（即使缓存存在也重新下载）
        if avatar_url and (avatar_url.startswith('http://') or avatar_url.startswith('https://')):
            try:
                print(f"  开始从远程服务器下载头像...")
                print(f"  请求 URL: {avatar_url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                }
                response = requests.get(avatar_url, timeout=10, headers=headers)
                print(f"  HTTP 响应状态码: {response.status_code}")
                print(f"  Content-Type: {response.headers.get('Content-Type', '未知')}")
                print(f"  响应内容大小: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    # 验证是否真的是图片数据
                    if len(response.content) < 500:
                        print(f"  ⚠️ 警告：图片数据太小（{len(response.content)} bytes），可能不是有效的图片")
                        print(f"  响应内容预览: {response.content[:200]}")
                    else:
                        print(f"  ✅ 图片数据大小正常")
                    
                    # 保存到缓存
                    with open(cache_file, 'wb') as f:
                        f.write(response.content)
                    print(f"  头像已保存到缓存文件（{len(response.content)} bytes）")
                    
                    local_url = QUrl.fromLocalFile(cache_file).toString()
                    print(f"  返回本地文件 URL: {local_url}")
                    print(f"[getPassPortAvatar] 方法执行完成\n")
                    return local_url
                else:
                    print(f"  下载失败：HTTP {response.status_code}")
            except Exception as e:
                print(f"  下载头像异常: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果主头像 URL 不存在或下载失败，使用 Minecraft 皮肤 API 作为备用
        print(f"  尝试使用 Minecraft 皮肤 API 作为备用...")
        try:
            fallback_url = f"https://visage.surgeplay.com/face/128/{username}"
            print(f"  备用 URL: {fallback_url}")
            response = requests.get(fallback_url, timeout=10, headers={"User-Agent": "BloretLauncher/1.0"})
            print(f"  HTTP 响应状态码: {response.status_code}")
            print(f"  响应内容大小: {len(response.content)} bytes")
            
            if response.status_code == 200 and len(response.content) > 500:
                with open(cache_file, 'wb') as f:
                    f.write(response.content)
                print(f"  备用头像已保存到缓存文件")
                local_url = QUrl.fromLocalFile(cache_file).toString()
                print(f"  返回本地文件 URL: {local_url}")
                print(f"[getPassPortAvatar] 方法执行完成\n")
                return local_url
            else:
                print(f"  备用下载失败：HTTP {response.status_code} 或内容过小")
        except Exception as e:
            print(f"  备用下载异常: {type(e).__name__}: {e}")
        
        print(f"  所有方法都失败，返回空字符串")
        print(f"[getPassPortAvatar] 方法执行完成\n")
        return ""

    # Removed duplicate getPlayerName, getVanillaVersions, getFabricVersions, getJavaDownloadVersions, downloadJava
    # ensuring the correct implementations later in the file are used.
    pass

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

        def start_screenshot():
            try:
                self._screenshot_widget = ScreenShortCut()
                if self._screenshot_widget is not None:
                    self._screenshot_widget.destroyed.connect(lambda *args: setattr(self, '_screenshot_widget', None))
            except Exception as e:
                print(f"Failed to start screenshot: {e}")

        # 使用 QTimer.singleShot 在主线程中执行截图，避免线程问题
        QTimer.singleShot(0, start_screenshot)

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
        QDesktopServices.openUrl(QUrl(url))
        
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

    def _resolve_plugin_path(self, name):
        if not name:
            return ""
        for plugin in list_installed_plugins():
            if name in (plugin.get("folderName"), plugin.get("id"), plugin.get("name")):
                return plugin.get("path", "")
        return ""

    @Slot(result="QVariant")
    def getInstalledPlugins(self):
        plugins = list_installed_plugins()
        for plugin in plugins:
            icon_path = plugin.get("iconPath")
            if icon_path:
                plugin["icon"] = QUrl.fromLocalFile(icon_path).toString()
            else:
                plugin["icon"] = ""
        return plugins

    @Slot(result=str)
    def getPluginRoot(self):
        return get_plugin_root()

    @Slot()
    def openPluginRoot(self):
        plugin_root = get_plugin_root()
        if plugin_root:
            QDesktopServices.openUrl(QUrl.fromLocalFile(plugin_root))

    @Slot(str)
    def openPluginFolder(self, name):
        plugin_path = self._resolve_plugin_path(name)
        if plugin_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(plugin_path))

    @Slot(str, result="QVariant")
    def uninstallPlugin(self, name):
        ok, message = uninstall_plugin(name)
        return {"success": ok, "message": message}


class LauncherTrayIcon(QSystemTrayIcon):
    """RinUI 版系统托盘图标与菜单"""

    def __init__(self, main_window):
        app_instance = QApplication.instance()
        if app_instance is not None:
            super().__init__(app_instance)
        else:
            super().__init__()

        self.main_window = main_window
        self._is_refreshing_launch_menu = False
        self._trigger_reason = self._resolve_trigger_reason()
        self._context_reason = self._resolve_context_reason()

        icon_path = get_app_icon_path(for_tray=True)
        if icon_path:
            self.setIcon(QIcon(str(icon_path)))
        else:
            self.setIcon(main_window.windowIcon())

        self.setToolTip("Bloret Launcher")

        self.menu = QMenu()
        self.launch_menu = self.menu.addMenu(i18nText("🔼  启动版本"))
        self._refresh_launch_menu()

        self.menu.addSeparator()
        self.menu.addAction(i18nText('🔡  访问 BBS'), links.open_BBBS_link)
        self.menu.addAction(i18nText('🔡  访问 Bloret PassPort'), links.open_PassPort_link)
        self.menu.addAction(i18nText('🔡  访问 百络图床'), links.open_BIMG_WEB_link)

        self.menu.addSeparator()
        self.menu.addAction(i18nText('🔄️  重启程序'), self.main_window.restart_app)
        self.menu.addAction(i18nText('✅  显示窗口'), self.main_window.show_main_window)
        self.menu.addAction(i18nText('❎  退出程序'), self.main_window.quit_app)

        self.activated.connect(self._on_tray_activated)

    @staticmethod
    def _resolve_trigger_reason():
        """兼容不同 PySide 版本的枚举写法。"""
        reason_enum = getattr(QSystemTrayIcon, "ActivationReason", None)
        if reason_enum is not None and hasattr(reason_enum, "Trigger"):
            return reason_enum.Trigger
        return getattr(QSystemTrayIcon, "Trigger", None)

    @staticmethod
    def _resolve_context_reason():
        reason_enum = getattr(QSystemTrayIcon, "ActivationReason", None)
        if reason_enum is not None and hasattr(reason_enum, "Context"):
            return reason_enum.Context
        return getattr(QSystemTrayIcon, "Context", None)

    def _refresh_launch_menu(self):
        if self._is_refreshing_launch_menu:
            return

        self._is_refreshing_launch_menu = True
        self.launch_menu.clear()

        try:
            unique_versions = self._get_tray_launch_versions()
            if not unique_versions:
                empty_action = QAction(i18nText("暂无可启动版本"), self.launch_menu)
                empty_action.setEnabled(False)
                self.launch_menu.addAction(empty_action)
                return

            for version in unique_versions:
                action = QAction(version, self.launch_menu)
                action.triggered.connect(lambda checked=False, v=version: self.main_window.launch_version_from_tray(v))
                self.launch_menu.addAction(action)

        except Exception as e:
            print(f"Failed to refresh tray launch menu: {e}")
            error_action = QAction(i18nText("加载启动列表失败"), self.launch_menu)
            error_action.setEnabled(False)
            self.launch_menu.addAction(error_action)
        finally:
            self._is_refreshing_launch_menu = False

    @staticmethod
    def _get_tray_launch_versions():
        """仅收集托盘菜单需要的名称，避免右键时触发图标解析。"""
        version_names = []

        try:
            config_data = cfg.read()

            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            versions_dir = os.path.join(minecraft_dir, "versions")

            if os.path.isdir(versions_dir):
                for entry in os.listdir(versions_dir):
                    version_path = os.path.join(versions_dir, entry)
                    if os.path.isdir(version_path):
                        version_names.append(entry)

            customize_items = config_data.get("Customize", [])
            if isinstance(customize_items, list):
                for custom_item in customize_items:
                    if isinstance(custom_item, dict):
                        custom_name = str(custom_item.get("showname", "")).strip()
                        if custom_name:
                            version_names.append(custom_name)
        except Exception as e:
            print(f"Failed to collect tray launch versions: {e}")

        return list(dict.fromkeys(version_names))

    def _on_tray_activated(self, reason):
        try:
            is_trigger = self._reason_equals(reason, self._trigger_reason)
            if is_trigger:
                if self._is_window_hidden_or_minimized():
                    self.main_window.show_main_window()
                else:
                    root_window = getattr(self.main_window, "root_window", None)
                    if root_window is not None:
                        root_window.hide()
                    else:
                        self.main_window.hide()
                return

            is_context = self._reason_equals(reason, self._context_reason)
            if is_context:
                self._refresh_launch_menu()
                self.menu.popup(QCursor.pos())
        except Exception as e:
            print(f"Tray activation handler failed: {e}")

    def _is_window_hidden_or_minimized(self):
        """兼容 RinUI/QQuickWindow 的窗口状态判断，避免访问不存在的 QWidget API。"""
        root_window = getattr(self.main_window, "root_window", None)
        window_obj = root_window if root_window is not None else self.main_window

        is_visible = True
        try:
            if hasattr(window_obj, "isVisible"):
                is_visible = bool(window_obj.isVisible())
            elif hasattr(window_obj, "visible"):
                is_visible = bool(window_obj.visible)
        except Exception:
            is_visible = True

        is_minimized = False
        try:
            if hasattr(window_obj, "isMinimized"):
                is_minimized = bool(window_obj.isMinimized())
            elif hasattr(window_obj, "visibility"):
                visibility_value = window_obj.visibility()
                is_minimized = "Minimized" in str(visibility_value)
        except Exception:
            is_minimized = False

        return (not is_visible) or is_minimized

    @staticmethod
    def _reason_equals(reason, expected):
        if expected is None:
            return False

        if reason == expected:
            return True

        try:
            return int(reason) == int(expected)
        except Exception:
            return False

class LauncherV2(RinUIWindow):
    def __init__(self):
        super().__init__()
        self._force_quit = False
        self.tray_icon = None
        
        # Inject Backend to QML BEFORE loading
        self.backend = Backend()
        self.backend.setBackendParent(self)
        self.engine.rootContext().setContextProperty("Backend", self.backend)
        
        qml_file = SCRIPT_DIR / "qml" / "main.qml"
        self.load(str(qml_file))
        
        icon_path = get_app_icon_path()
        if icon_path:
            self.setIcon(str(icon_path))
        self.setProperty("title", "Bloret Launcher v2")

        self._init_system_tray()

    def _read_minimize_to_tray_on_close(self):
        minimize_to_tray = True
        try:
            if self.backend:
                minimize_to_tray = bool(self.backend.getMinimizeToTrayOnClose())
        except Exception:
            minimize_to_tray = True
        return minimize_to_tray

    def _can_hide_to_tray(self):
        return bool(self.tray_icon and self.tray_icon.isVisible())

    def _should_hide_to_tray_on_close(self):
        return self._read_minimize_to_tray_on_close() and self._can_hide_to_tray()

    def handle_close_request_from_qml(self):
        """由 QML onClosing 调用，返回 True 表示已拦截关闭并隐藏到托盘。"""
        if self._force_quit:
            return False

        if self._should_hide_to_tray_on_close():
            self.hide()
            return True

        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        return False

    @staticmethod
    def _reject_close_event(event):
        if event is None:
            return

        try:
            if hasattr(event, "setAccepted"):
                event.setAccepted(False)
                return
        except Exception:
            pass

        try:
            if hasattr(event, "ignore"):
                event.ignore()
                return
        except Exception:
            pass

        try:
            if hasattr(event, "accepted"):
                event.accepted = False
        except Exception:
            pass

    def _init_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this platform")
            return

        self.tray_icon = LauncherTrayIcon(self)
        self.tray_icon.show()

    def launch_version_from_tray(self, version):
        if version and self.backend:
            self.backend.launchGame(version)

    def show_main_window(self):
        root_window = getattr(self, "root_window", None)
        window_obj = root_window if root_window is not None else self

        try:
            if hasattr(window_obj, "show"):
                window_obj.show()
            else:
                self.show()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "showNormal"):
                window_obj.showNormal()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "raise_"):
                window_obj.raise_()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "requestActivate"):
                window_obj.requestActivate()
            elif hasattr(window_obj, "activateWindow"):
                window_obj.activateWindow()
        except Exception:
            pass

    def quit_app(self):
        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def restart_app(self):
        if getattr(sys, 'frozen', False):
            args = [sys.executable] + sys.argv[1:]
        else:
            args = [sys.executable] + sys.argv

        kwargs = {"shell": False}
        if sys.platform == 'win32':
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            kwargs["start_new_session"] = True

        subprocess.Popen(args, **kwargs)
        self.quit_app()

    def closeEvent(self, event):
        if self._force_quit:
            try:
                super().closeEvent(event)
            except Exception:
                event.accept()
            return

        if self._should_hide_to_tray_on_close():
            try:
                event.ignore()
            except Exception:
                self._reject_close_event(event)
            self.hide()
            return

        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        try:
            super().closeEvent(event)
        except Exception:
            event.accept()

if __name__ == "__main__":
    # app is already created at the top
    global_icon_path = get_app_icon_path()
    if global_icon_path:
        app.setWindowIcon(QIcon(str(global_icon_path)))
    launcher = LauncherV2()
    sys.exit(app.exec())
