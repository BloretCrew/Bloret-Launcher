import os, shutil
import json
import sys
import modules.globals as BLglobals
from modules.log import log

# 辅助函数：获取源配置文件的路径（兼容 PyInstaller 打包环境）
def get_source_config_path():
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, 'config.json')
    else:
        # 开发环境当前目录
        return os.path.abspath("config.json")

# 获取默认配置文件的真实路径
source_config_path = get_source_config_path()

# config_path = %appdata%/Bloret-Launcher/config.json
config_path = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'config.json')

#先检查目标配置文件是否存在
log(f"正在检查配置文件路径: {config_path}")
log(f"源配置文件路径: {source_config_path}")
log(f"默认配置文件是否存在: {os.path.exists(source_config_path)}")

if not os.path.exists(config_path):
    log(f"目标配置文件未找到: {config_path}")
    
    # 确保目标目录存在
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        log(f"配置目录不存在，正在创建: {config_dir}")
        os.makedirs(config_dir, exist_ok=True)
        log(f"配置目录已创建: {config_dir}")
    
    # 检查源文件是否存在
    if os.path.exists(source_config_path):
        try:
            # 复制 config.json 到 %appdata%/Bloret-Launcher/config.json
            shutil.copyfile(source_config_path, config_path)
            log(f"配置文件已成功复制到: {config_path}")
        except Exception as e:
            log(f"复制配置文件时出错: {str(e)}")
    else:
        log(f"错误：默认配置文件 config.json 在源路径中不存在")
else:
    log(f"目标配置文件已存在: {config_path}")

BLglobals.config_path = config_path
log("配置文件路径: " + config_path)

# 检查一下配置文件中的 ver 字段是否与当前版本匹配
try:
    log(f"正在读取配置文件: {BLglobals.config_path}")
    with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    log(f"成功读取配置文件，正在检查版本字段...")
    
    # 检查默认配置文件是否存在
    if os.path.exists(source_config_path):
        with open(source_config_path, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
            
        current_ver = config.get('ver')
        default_ver = default_config.get('ver')
        
        log(f"当前配置文件版本: {current_ver}")
        log(f"默认配置文件版本: {default_ver}")
        
        if current_ver != default_ver:
            log(f"配置文件版本不匹配（当前: {current_ver}, 目标: {default_ver}），正在执行增量更新...")
            # 备份
            shutil.copyfile(BLglobals.config_path, config_path + ".back")
            
            # 增量合并：以旧配置(config)为主，补全缺少的默认项(default_config)
            updated_config = default_config.copy()
            updated_config.update(config) # config 的内容会覆盖 default_config 的同名内容
            updated_config['ver'] = default_ver
            
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f, ensure_ascii=False, indent=4)
            log(f"配置文件版本已从 {current_ver} 安全升级到 {default_ver}")
        else:
            log("配置文件版本匹配，无需更新")
    else:
        log("警告：默认配置文件 config.json 不存在，无法进行版本检查")
        
except FileNotFoundError:
    log(f"错误：配置文件 {BLglobals.config_path} 不存在")
except json.JSONDecodeError as e:
    log(f"错误：配置文件格式不正确: {str(e)}")
    # 如果配置文件损坏，尝试用默认配置替换
    if os.path.exists(source_config_path):
        log("尝试用默认配置文件替换损坏的配置文件...")
        shutil.copyfile(source_config_path, config_path)
        log("配置文件已替换")
except Exception as e:
    log(f"读取配置文件时发生未知错误: {str(e)}")


def read():
    with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
try:
    log(f"正在读取最终配置文件: {BLglobals.config_path}")
    config_data = read()
    log(f"成功读取配置文件内容: {config_data}")
    
    BLglobals.minecraft_dir = config_data.get('minecraft_dir', '')
    log(f"Minecraft目录已设置为: '{BLglobals.minecraft_dir}'")
    
    # 检查minecraft目录是否存在
    if BLglobals.minecraft_dir:
        if os.path.exists(BLglobals.minecraft_dir):
            log(f"Minecraft目录存在: {BLglobals.minecraft_dir}")
        else:
            log(f"警告：Minecraft目录不存在: {BLglobals.minecraft_dir}")
    else:
        log("警告：Minecraft目录未设置（为空字符串）")
        
except Exception as e:
    log(f"读取配置文件失败: {str(e)}")
    BLglobals.minecraft_dir = ''
    log("Minecraft目录已设置为空字符串作为默认值")