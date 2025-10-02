import logging,requests,os,subprocess,json
from win32com.client import Dispatch
from qfluentwidgets import MessageBox
from modules.win11toast import update_progress
from modules.i18n import i18nText
import threading
import sys
import traceback
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception

def check_Light_Minecraft_Download_Way(server_ip, callback=None):
    def _inner():
        try:
            response = requests.get(server_ip + "api/Light-Minecraft-Download-Way")
            if response.status_code == 200:
                data = response.json()
                LM_Download_Way = data.get("Light-Minecraft-Download-Way", {})
                LM_Download_Way_list = LM_Download_Way.get("download-way", [])
                LM_Download_Way_version = LM_Download_Way.get("version", {})
                LM_Download_Way_minecraft = LM_Download_Way.get("minecraft", {})
                if callback:
                    callback(LM_Download_Way, LM_Download_Way_list, LM_Download_Way_version, LM_Download_Way_minecraft)
        except Exception as e:
            handle_exception(type(e), e, e.__traceback__)
            pass
    threading.Thread(target=_inner, daemon=True).start()

def handle_first_run(self,server_ip):
    def _inner(self, server_ip):
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
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        shortcut_path = os.path.join(desktop, 'Bloret Launcher.lnk')
        target = os.path.join(os.getcwd(), 'Bloret-Launcher.exe')
        icon = os.path.join(os.getcwd(), 'bloret.ico')
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = icon
        shortcut.save()
    t = threading.Thread(target=_inner, args=(self, server_ip), daemon=True)
    t.start()

def check_Bloret_version(self,server_ip,ver_id_bloret):
    def _inner(self, server_ip, ver_id_bloret):
        if not self.config.get('localmod', False):
            try:
                response = requests.get(server_ip + "api/bloret-version")
                if response.status_code == 200:
                    data = response.json()
                    ver_id_bloret.clear()
                    ver_id_bloret.extend(data.get("Bloret-versions", []))
                    log(f"成功获取 Bloret 版本列表: {ver_id_bloret}")
                    return ver_id_bloret
                else:
                    log(i18nText("无法获取 Bloret 版本列表"), logging.ERROR)
            except requests.RequestException as e:
                log(f"获取 Bloret 版本列表时发生错误: {e}", logging.ERROR)
        else:
            log(i18nText("本地模式已启用，获取 Bloret 版本列表 的过程已跳过。"))
    t = threading.Thread(target=_inner, args=(self, server_ip, ver_id_bloret), daemon=True)
    t.start()

def get_latest_version(server_ip):
    # 初始化变量
    BL_update_text = ""
    BL_latest_ver = "0.0"
    
    try:
        response = requests.get(server_ip + "api/BLlatest")
        if response.status_code == 200:
            latest_release = response.json()
            BL_update_text = latest_release.get("text", "")
            BL_latest_ver = latest_release.get("Bloret-Launcher-latest", "0.0")
            return BL_latest_ver, BL_update_text
        else:
            log(i18nText("查询最新版本失败"), logging.ERROR)
            return BL_latest_ver, BL_update_text
    except requests.RequestException as e:
        log(f"查询最新版本时发生错误: {e}", logging.ERROR)
        return BL_latest_ver, BL_update_text

def check_for_updates(self,server_ip):
    def _inner(self, server_ip):
        if not self.config.get('localmod', False):
            try:
                BL_latest_ver, BL_update_text = get_latest_version(server_ip)
                log(f"最新正式版: {BL_latest_ver}")
                BL_ver = float(self.config.get('ver', '0.0'))  # 从config.json读取当前版本
                # 确保BL_latest_ver是一个有效的数字字符串
                if BL_latest_ver is not None and BL_latest_ver != "":
                    if BL_ver < float(BL_latest_ver):
                        log(f"当前版本不是最新版，请更新到 {BL_latest_ver} 版本", logging.WARNING)
                        w = MessageBox(
                            title=i18nText("当前版本不是最新版"),
                            content=f'Bloret Launcher 貌似有个新新新版本\n你似乎正在运行 {BL_ver}，但事实上，百络谷启动器 {BL_latest_ver} 来啦！按下按钮自动更新。\n这个更新... {BL_update_text}',
                            parent=self
                        )
                        w.show()
                        w.yesButton.clicked.connect(self.update_to_latest_version)
            except Exception as e:
                handle_exception(type(e), e, e.__traceback__)
                log(f"检查更新时发生错误: {e}", logging.ERROR)
                log(i18nText("无法连接到 pcfs.eno.ink"), logging.ERROR)
                update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': i18nText('无法连接到服务器 ❌')})
        else:
            log(i18nText("本地模式已启用，检查更新 的过程已跳过。"))
    t = threading.Thread(target=_inner, args=(self, server_ip), daemon=True)
    t.start()

