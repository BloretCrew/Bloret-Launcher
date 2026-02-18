import sys
import logging,requests,os,subprocess,json
if sys.platform == "win32":
    from win32com.client import Dispatch
else:
    Dispatch = None
from qfluentwidgets import MessageBox
from modules.win11toast import update_progress
from modules.i18n import i18nText
import threading
from PyQt5.QtCore import QObject, pyqtSignal
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
import modules.globals as BLglobals

def IsNeedUpdate(NowVersion, LatestVersion):
    """
    比较两个版本号字符串，判断是否需要更新
    支持格式如: "1.2.3", "8.1-b1", "2.0-alpha", 等
    
    Args:
        NowVersion (str): 当前版本号
        LatestVersion (str): 最新版本号
    
    Returns:
        bool: 如果需要更新返回True，否则返回False
    """
    
    def parse_version(version_str):
        # 分离主版本号和预发布版本信息
        parts = version_str.split('-')
        main_version = parts[0]
        prerelease = parts[1] if len(parts) > 1 else ''
        
        # 解析主版本号
        main_parts = [int(x) for x in main_version.split('.') if x.isdigit()]
        return main_parts, prerelease
    
    now_main, now_prerelease = parse_version(NowVersion)
    latest_main, latest_prerelease = parse_version(LatestVersion)
    
    # 获取主版本号的最大长度
    max_length = max(len(now_main), len(latest_main))
    
    # 补齐主版本号
    now_main.extend([0] * (max_length - len(now_main)))
    latest_main.extend([0] * (max_length - len(latest_main)))
    
    # 比较主版本号
    for now, latest in zip(now_main, latest_main):
        if now < latest:
            return True
        elif now > latest:
            return False
    
    # 主版本号相同，比较预发布版本
    # 如果当前没有预发布版本，说明是正式版，不需要更新
    if not now_prerelease and latest_prerelease:
        return True
    # 如果当前是预发布版，最新是正式版，需要更新
    elif now_prerelease and not latest_prerelease:
        return True
    # 如果两者都有预发布版本或者都没有预发布版本
    elif now_prerelease and latest_prerelease:
        # 简单比较字符串（实际项目中可能需要更复杂的逻辑）
        return now_prerelease < latest_prerelease
    else:
        # 都是正式版且主版本号相同，不需要更新
        return False

def handle_first_run(self):
    def _inner(self):
        if self.config.get('first-run', True):
            parent_dir = os.path.dirname(os.getcwd())
            updating_folder = os.path.join(parent_dir, "updating")
            updata_ps1_file = os.path.join(parent_dir, "updata.ps1")
            if os.path.exists(updating_folder):
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"Remove-Item -Path '{updating_folder}' -Recurse -Force"], check=True)
                log(f"删除文件夹: {updating_folder}")
            if os.path.exists(updata_ps1_file):
                os.remove(updata_ps1_file)
                log(f"删除文件: {updata_ps1_file}")
    def create_shortcut(self):
        if sys.platform != "win32":
            log("非 Windows 平台暂不支持创建桌面快捷方式")
            return
        
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        shortcut_path = os.path.join(desktop, 'Bloret Launcher.lnk')
        target = os.path.join(os.getcwd(), 'Bloret-Launcher.exe')
        icon = os.path.join(os.getcwd(), 'bloret.ico')
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = icon
        shortcut.save()
    t = threading.Thread(target=_inner, args=(self,), daemon=True)
    t.start()

def get_latest_version():
    # 初始化变量
    BL_update_text = ""
    BL_latest_ver = "0.0"
    
    try:
        response = requests.get(f"{BLglobals.server_ip}:3001/api/info")
        if response.status_code == 200:
            latest_release = response.json()
            BL_update_text = latest_release.get("newVersionDescription", "")
            BL_latest_ver = latest_release.get("latestVersion", "0.0")

            # 获取每日提示并存储在全局变量里
            tips = latest_release.get("BLTips", [])
            if tips:
                BLglobals.BLtips = tips
            log(f"获取到的每日提示: {BLglobals.BLtips}")

            # 获取 Activity 活动信息并存储在全局变量里
            activity = latest_release.get("activity", {})
            if activity:
                BLglobals.BL_Activity = activity
            log(f"获取到的活动信息: {BLglobals.BL_Activity}")

            return BL_latest_ver, BL_update_text
        else:
            log(f"无法获取最新版本信息，状态码: {response.status_code}", logging.ERROR)
            return BL_latest_ver, BL_update_text
    except requests.RequestException as e:
        log(f"查询最新版本时发生错误: {e}", logging.ERROR)
        return BL_latest_ver, BL_update_text

class UpdateSignal(QObject):
    show_update = pyqtSignal(object, str, str, str)

def check_for_updates(self):
    if not hasattr(self, 'update_signal'):
        self.update_signal = UpdateSignal()
        self.update_signal.show_update.connect(show_update_message)

    def _inner():
        if not self.config.get('localmod', False):
            try:
                BL_latest_ver, BL_update_text = get_latest_version()
                log(f"最新正式版: {BL_latest_ver}")
                current_ver = self.config.get('ver', '0.0')  # 从config.json读取当前版本
                log(f"当前版本: {current_ver}")
                # 使用 IsNeedUpdate 函数比较版本
                if BL_latest_ver is not None and BL_latest_ver != "":
                    need_update = IsNeedUpdate(current_ver, BL_latest_ver)
                    log(f"是否需要更新: {need_update}")
                    if need_update:
                        log(f"当前版本不是最新版，请更新到 {BL_latest_ver} 版本", logging.WARNING)
                        # 使用信号确保在主线程中创建和显示 MessageBox
                        self.update_signal.show_update.emit(self, current_ver, BL_latest_ver, BL_update_text)
                    else:
                        log("当前版本是最新的")
            except Exception as e:
                handle_exception(type(e), e, e.__traceback__)
                log(f"检查更新时发生错误: {e}", logging.ERROR)
                log(i18nText("无法连接到 Bloret Launcher Server"), logging.ERROR)
                update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': i18nText('无法连接到服务器 ❌')})
        else:
            log(i18nText("本地模式已启用，检查更新 的过程已跳过。"))
    
    t = threading.Thread(target=_inner, daemon=True)
    t.start()

def show_update_message(parent, current_ver, latest_ver, update_text):
    """在主线程中显示更新消息框"""
    try:
        log("准备显示更新消息框")
        w = MessageBox(
            title=i18nText("当前版本不是最新版"),
            content=f'Bloret Launcher 貌似有个新新新版本\n你似乎正在运行 Bloret Launcher {current_ver}，但事实上，Bloret Launcher {latest_ver} 来啦！按下按钮自动更新。\n这个更新... {update_text}',
            parent=parent
        )
        from modules.update import update_to_latest_version
        w.yesButton.clicked.connect(lambda: update_to_latest_version(parent))
        w.show()
        log("更新消息框已显示")
    except Exception as e:
        handle_exception(type(e), e, e.__traceback__)
        log(f"显示更新消息时发生错误: {e}", logging.ERROR)

