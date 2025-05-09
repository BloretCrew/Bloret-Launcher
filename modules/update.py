from PyQt5.QtWidgets import QMessageBox
import logging,os,subprocess
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块，位于 modules 中
from modules.log import log, importlog
from modules.safe import handle_exception

def update_to_latest_version(self):
    update_script_path = os.path.join(os.getcwd(), "update.ps1")
    try:
        with open(update_script_path, "w", encoding="utf-8") as update_script:
            update_script.write(
                "taskkill /im Bloret-Launcher.exe /f\n"
                "winget update Bloret.BloretLauncher\n"
            )# 通过 winget 更新
        log(f"创建更新脚本: {update_script_path}")
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", update_script_path], check=True)
    except Exception as e:
        handle_exception(e)
        log(f"创建或运行更新脚本失败: {e}", logging.ERROR)
        QMessageBox.critical(self, "更新失败", f"创建或运行更新脚本失败: {e}")


importlog("uUPDATE.PY")