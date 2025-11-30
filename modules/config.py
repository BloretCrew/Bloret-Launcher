import os, shutil
import json
import json
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

# 检查一下配置文件中的 ver 字段是否与当前版本匹配
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
    with open('config.json', 'r', encoding='utf-8') as f:
        default_config = json.load(f)
        if config.get('ver') != default_config.get('ver'):
            log(f"配置文件版本({config.get('ver')})与默认配置文件版本({default_config.get('ver')})不匹配")
            # 备份旧的配置文件为 config.back.json
            shutil.copyfile(config_path, config_path + ".back")
            log(f"旧的配置文件已备份为: {config_path + '.back'}")
            # 复制 config.json 到 %appdata%/Bloret-Launcher/config.json
            shutil.copyfile("config.json", config_path)
            log(f"配置文件已复制到: {config_path}")
            exit(1)

def read():
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)