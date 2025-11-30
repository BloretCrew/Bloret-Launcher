import os, shutil
import modules.globals as BLglobals
from modules.log import log

# config_path = %appdata%/Bloret-Launcher/config.json
config_path = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'config.json')

#先检查是否存在
if not os.path.exists(config_path):
    log(f"配置文件未找到: {config_path}")
    # 复制 config.json 到 %appdata%/Bloret-Launcher/config.json
    shutil.copyfile("config.json", config_path)
    log(f"配置文件已复制到: {config_path}")
BLglobals.config_path = config_path
log("配置文件路径: " + config_path)