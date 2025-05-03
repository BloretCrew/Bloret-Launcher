import logging,requests,os,subprocess,json,socket
from win32com.client import Dispatch
from qfluentwidgets import MessageBox
from modules.win11toast import update_progress
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log, importlog
from modules.safe import handle_exception
def check_Light_Minecraft_Download_Way(server_ip): 
    ''' 
    # 获取 Light Minecraft 下载方式
    向 `Bloret Launcher Server` /api/Light-Minecraft-Download-Way 获取

    ***

    输入 : server_ip

    输出 :

        - [x] LM_Download_Way
        - [x] LM_Download_Way_list
        - [x] LM_Download_Way_version
        - [x] LM_Download_Way_minecraft
    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    try:
        response = requests.get(server_ip + "api/Light-Minecraft-Download-Way")
        if response.status_code == 200:
            data = response.json()
            LM_Download_Way = data.get("Light-Minecraft-Download-Way", {})  # 确保是字典
            LM_Download_Way_list = []
            LM_Download_Way_list.extend(LM_Download_Way.get("download-way", []))
            LM_Download_Way_version = LM_Download_Way.get("version", {})
            LM_Download_Way_minecraft = LM_Download_Way.get("minecraft", {})
            return LM_Download_Way, LM_Download_Way_list, LM_Download_Way_version, LM_Download_Way_minecraft
            # log(f"成功获取 Light-Minecraft-Download-Way: {LM_Download_Way}，LM_Download_Way_list:{LM_Download_Way_list}，LM_Download_Way_version:{LM_Download_Way_version}，LM_Download_Way_minecraft:{LM_Download_Way_minecraft}")
        else:
            log("无法获取 Light-Minecraft-Download-Way", logging.ERROR)
    except requests.RequestException as e:
        # handle_exception(e,e,e)
        log(f"获取 Light-Minecraft-Download-Way 时发生错误: {e}", logging.ERROR)

def handle_first_run(self,server_ip):
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
                icon = os.path.join(os.getcwd(), 'icons', 'bloret.ico')
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.TargetPath = target
                shortcut.WorkingDirectory = os.getcwd()
                shortcut.IconLocation = icon
                shortcut.save()
            self.create_shortcut()
        #首次启动向 http://pcfs.top:2/api/blnum 发送请求，服务器计数器+1
        #具体可见项目 https://github.com/BloretCrew/Bloret-Launcher-Server
        response = requests.get(server_ip + "api/blnum")
        if response.status_code == 200:
            data = response.json()
            self.bl_users = data.get("user", "未知用户")
            log(f"获取到的用户数: {self.bl_users}")
        else:
            self.bl_users = "未知用户"
            log("无法获取用户数", logging.ERROR)

        #首次启动显示弹窗提醒
        # msg_box = QMessageBox(self)
        # msg_box.setIcon(QMessageBox.Information)
        # msg_box.setWindowTitle('欢迎')
        # msg_box.setText("欢迎使用百络谷启动器 (＾ｰ^)ノ\n您是百络谷启动器的第 %s 位用户" % self.bl_users)
        # msg_box.setWindowIcon(QIcon("bloret.ico"))  # 设置弹窗图标
        # msg_box.setStandardButtons(QMessageBox.Ok)
        # msg_box.exec()

        # 使用非模态对话框
        w = MessageBox(
            title="欢迎使用百络谷启动器 (＾ｰ^)ノ",
            content=f'您是百络谷启动器的第 {self.bl_users} 位用户',
            parent=self
        )
        w.show()


        # QMessageBox.information(self, "欢迎", "欢迎使用百络谷启动器 (＾ｰ^)ノ\n您是百络谷启动器的第 %s 位用户" % self.bl_users)
        # 更新配置文件中的 first-run 值
        self.config['first-run'] = False
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

def check_Bloret_version(self,server_ip,ver_id_bloret):
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
                log("无法获取 Bloret 版本列表", logging.ERROR)
        except requests.RequestException as e:
            log(f"获取 Bloret 版本列表时发生错误: {e}", logging.ERROR)
    else:
        log("本地模式已启用，获取 Bloret 版本列表 的过程已跳过。")

def get_latest_version(server_ip):
    try:
        response = requests.get(server_ip + "api/BLlatest")
        if response.status_code == 200:
            latest_release = response.json()
            BL_update_text = latest_release.get("text")
            BL_latest_ver = latest_release.get("Bloret-Launcher-latest")
            return BL_latest_ver, BL_update_text
        else:
            log("查询最新版本失败", logging.ERROR)
            return BL_latest_ver, BL_update_text
    except requests.RequestException as e:
        log(f"查询最新版本时发生错误: {e}", logging.ERROR)
        return BL_latest_ver, BL_update_text
def check_for_updates(self,server_ip):
    if not self.config.get('localmod', False):
        try:
            # 插入 socket 检查
            # socket.setdefaulttimeout(3)
            # socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('pcfs.top', 2))
            BL_latest_ver, BL_update_text = get_latest_version(server_ip)
            log(f"最新正式版: {BL_latest_ver}")
            BL_ver = float(self.config.get('ver', '0.0'))  # 从config.json读取当前版本
            if BL_ver < float(BL_latest_ver):
                log(f"当前版本不是最新版，请更新到 {BL_latest_ver} 版本", logging.WARNING)

                # 使用非模态对话框
                w = MessageBox(
                    title="当前版本不是最新版",
                    content=f'Bloret Launcher 貌似有个新新新版本\n你似乎正在运行 {BL_ver}，但事实上，百络谷启动器 {BL_latest_ver} 来啦！按下按钮自动更新。\n这个更新... {BL_update_text}',
                    parent=self
                )
                w.show()

                # 连接按钮点击事件以触发更新
                w.yesButton.clicked.connect(self.update_to_latest_version)
        except Exception as e:
            log(f"检查更新时发生错误: {e}", logging.ERROR)
            
            log("无法连接到 pcfs.top", logging.ERROR)
            w = MessageBox(
                title="无法连接到 pcfs.top",
                content=f'您无法连接到 PCFS 服务器来检查版本更新\n这可能是由于您的网络不佳？或是 PCFS 服务出现故障？\n请检查您的网络连接，或者稍后再试。\n我们等待了 3 秒，但它只显示：{e}',
                parent=self
            )
            update_progress({'value': 20 / 100, 'valueStringOverride': '2/10', 'status': '无法连接到服务器 ❌'})
            w.show()
    else:
        log("本地模式已启用，检查更新 的过程已跳过。")

importlog("BLSERVER.PY")