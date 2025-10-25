import json
from PyQt5.QtWidgets import QMessageBox
import logging,os,subprocess,tempfile,requests,sys
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块，位于 modules 中
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText

def update_to_latest_version(self):
    try:
        # 导入win11toast模块，用于显示进度通知
        from modules.win11toast import notify, update_progress
        
        # 初始化通知
        notify(progress={
            'title': '正在准备更新...',
            'status': '正在获取最新版本信息...',
            'value': '0',
            'valueStringOverride': '0%',
            'icon': os.path.join(os.getcwd(), 'bloret.ico')
        })
        
        # 1. 向API获取信息
        update_progress({
            'value': 10 / 100,
            'valueStringOverride': '10%',
            'status': '正在获取最新版本信息...'
        })
        
        response = requests.get("http://pcfs.eno.ink:2/api/BL/info")
        response.raise_for_status()
        res = response.json()
        
        # 获取下载链接
        download_url = res["Bloret-Launcher-DownLoad-Link"]["Bloret-Launcher-Setup"]["GitCode"]
        version = res["Bloret-Launcher-latest-version"]
        
        # 更新通知
        notify(progress={
            'title': f'正在更新 Bloret Launcher 至 {version}',
            'status': res["Bloret-Launcher-update-text"],
            'value': '0',
            'valueStringOverride': '0%',
            'icon': os.path.join(os.getcwd(), 'bloret.ico')
        })
        
        # 更新进度
        update_progress({
            'value': 20 / 100,
            'valueStringOverride': '20%',
            'status': '正在下载更新文件...'
        })
        
        # 2. 下载文件到临时目录
        temp_dir = tempfile.gettempdir()
        file_name = os.path.join(temp_dir, f"Bloret-Launcher-Setup-{version}.exe")
        
        # 下载文件并实时更新进度
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            last_progress = 0
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        # 计算进度 (20% - 80%之间)
                        progress = 20 + (downloaded_size / total_size) * 60
                        # 每5%更新一次进度，避免过于频繁的更新影响下载速度
                        if progress - last_progress >= 5:
                            update_progress({
                                'value': progress / 100,
                                'valueStringOverride': f'{progress:.1f}%',
                                'status': f'正在下载更新文件... ({downloaded_size}/{total_size} bytes)'
                            })
                            last_progress = progress
        
        # 更新进度
        update_progress({
            'value': 80 / 100,
            'valueStringOverride': '80%',
            'status': '下载完成，准备安装...'
        })
        
        # 3. 结束程序并运行安装程序
        update_progress({
            'value': 90 / 100,
            'valueStringOverride': '90%',
            'status': '正在启动安装程序...'
        })
        
        # 启动安装程序并退出当前程序
        subprocess.Popen([file_name, "/SILENT", "/NORESTART"])
        sys.exit(0)
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"更新失败: {str(e)}", logging.ERROR)
        # 如果有父窗口，显示错误消息框
        if hasattr(self, 'parent') and self.parent:
            QMessageBox.critical(self.parent, "更新失败", f"更新过程中发生错误:\n{str(e)}")