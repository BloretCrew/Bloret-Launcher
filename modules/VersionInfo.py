import os
import json
import logging
import modules.globals as BLglobals
from modules.log import log

def GetMinecraftList():
    """
    读取 BLglobals.minecraft_dir/versions/.BL.json，
    提取 "versions" 对象下的所有键作为版本列表，
    更新 BLglobals.minecraft_list 并返回。
    """
    # 1. 检查 minecraft_dir 是否有效
    if not BLglobals.minecraft_dir:
        log("BLglobals.minecraft_dir 未设置，跳过读取 .BL.json", logging.WARNING)
        BLglobals.minecraft_list = []
        return []

    # 2. 拼接路径: .../.minecraft/versions/.BL.json
    target_path = os.path.join(BLglobals.minecraft_dir, "versions", ".BL.json")
    
    # log(f"尝试读取版本记录文件: {target_path}")

    # 3. 检查文件是否存在
    if not os.path.exists(target_path):
        log(f"版本记录文件不存在: {target_path}")
        BLglobals.minecraft_list = []
        return []

    try:
        # 4. 读取 JSON
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 5. 解析 versions 字段
        # 目标结构: { "versions": { "1.21.8": {...}, ... } }
        versions_data = data.get("versions", {})
        
        if isinstance(versions_data, dict):
            # 获取所有键并转为列表
            mc_list = list(versions_data.keys())
            
            # 更新全局变量
            BLglobals.minecraft_list = mc_list
            
            log(f"成功从 .BL.json 加载 {len(mc_list)} 个版本: {mc_list}")
            return mc_list
        else:
            log(f".BL.json 格式异常: 'versions' 字段不是字典", logging.ERROR)
            BLglobals.minecraft_list = []
            return []

    except json.JSONDecodeError as e:
        log(f"解析 .BL.json 失败 (JSON 损坏): {e}", logging.ERROR)
        BLglobals.minecraft_list = []
        return []
    except Exception as e:
        log(f"读取 .BL.json 时发生未知错误: {e}", logging.ERROR)
        BLglobals.minecraft_list = []
        return []