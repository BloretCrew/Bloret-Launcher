"""
Modrinth Modpack Export Module
用于将 Minecraft 实例导出为 .mrpack 格式
"""

import zipfile
import json
import hashlib
import os
import logging
from pathlib import Path
from modules.log import log
from modules.i18n import i18nText


def calculate_hash(file_path, algorithm='sha512'):
    """计算文件的哈希值"""
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        log(f"计算文件哈希失败 {file_path}: {str(e)}", logging.ERROR)
        return None


def detect_game_version(instance_path):
    """检测游戏版本"""
    try:
        # 尝试从 version.json 读取
        version_file = Path(instance_path) / "version.json"
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('id', '1.20.1')
        
        # 尝试从实例名称解析
        instance_name = Path(instance_path).name
        # 简单的版本提取逻辑
        import re
        match = re.search(r'(\d+\.\d+(\.\d+)?)', instance_name)
        if match:
            return match.group(1)
            
    except Exception as e:
        log(f"检测游戏版本失败：{str(e)}", logging.WARNING)
    
    return "1.20.1"


def detect_loader(instance_path):
    """检测加载器类型和版本"""
    try:
        mods_dir = Path(instance_path) / "mods"
        if not mods_dir.exists():
            return None
        
        # 检测 Fabric
        fabric_loader_jars = list(mods_dir.glob("fabric-loader-*.jar"))
        if fabric_loader_jars:
            # 从文件名提取版本
            name = fabric_loader_jars[0].name
            import re
            match = re.search(r'fabric-loader-(\d+\.\d+\.\d+)', name)
            if match:
                return {"name": "fabric-loader", "version": match.group(1)}
            return {"name": "fabric-loader", "version": "*"}
        
        # 检测 Forge
        forge_jars = list(mods_dir.glob("forge-*.jar")) + list(mods_dir.glob("*forge-*.jar"))
        if forge_jars:
            name = forge_jars[0].name
            import re
            match = re.search(r'forge[-_](\d+\.\d+\.\d+)', name, re.IGNORECASE)
            if match:
                return {"name": "forge", "version": match.group(1)}
            return {"name": "forge", "version": "*"}
        
        # 检测 NeoForge
        neoforge_jars = list(mods_dir.glob("neoforge-*.jar"))
        if neoforge_jars:
            name = neoforge_jars[0].name
            import re
            match = re.search(r'neoforge[-_](\d+\.\d+\.\d+)', name, re.IGNORECASE)
            if match:
                return {"name": "neoforge", "version": match.group(1)}
            return {"name": "neoforge", "version": "*"}
            
    except Exception as e:
        log(f"检测加载器失败：{str(e)}", logging.WARNING)
    
    return None


def collect_files(instance_path):
    """收集实例中的文件"""
    files_list = []
    instance = Path(instance_path)
    
    # 收集 mods 目录
    mods_dir = instance / "mods"
    if mods_dir.exists():
        for mod_file in mods_dir.glob("*.jar"):
            rel_path = f"mods/{mod_file.name}"
            files_list.append({
                "path": rel_path,
                "source": str(mod_file),
                "env": {"client": "required", "server": "required"}
            })
    
    # 收集 config 目录
    config_dir = instance / "config"
    if config_dir.exists():
        for config_file in config_dir.rglob("*"):
            if config_file.is_file():
                rel_path = f"config/{config_file.relative_to(config_dir)}"
                # 使用正斜杠
                rel_path = rel_path.replace(os.sep, '/')
                files_list.append({
                    "path": rel_path,
                    "source": str(config_file)
                })
    
    # 收集 resourcepacks 目录
    rp_dir = instance / "resourcepacks"
    if rp_dir.exists():
        for rp_file in rp_dir.rglob("*"):
            if rp_file.is_file():
                rel_path = f"resourcepacks/{rp_file.relative_to(rp_dir)}"
                rel_path = rel_path.replace(os.sep, '/')
                files_list.append({
                    "path": rel_path,
                    "source": str(rp_file)
                })
    
    # 收集 shaderpacks 目录
    shader_dir = instance / "shaderpacks"
    if shader_dir.exists():
        for shader_file in shader_dir.rglob("*"):
            if shader_file.is_file():
                rel_path = f"shaderpacks/{shader_file.relative_to(shader_dir)}"
                rel_path = rel_path.replace(os.sep, '/')
                files_list.append({
                    "path": rel_path,
                    "source": str(shader_file)
                })
    
    return files_list


def export_to_mrpack(instance_path, output_path, name, version, summary=""):
    """
    导出 Minecraft 实例为 .mrpack 文件
    
    Args:
        instance_path: 实例目录路径
        output_path: 输出的 .mrpack 文件路径
        name: 整合包名称
        version: 整合包版本号
        summary: 整合包简介
    
    Returns:
        bool: 是否成功
    """
    try:
        log(i18nText("开始导出 Modrinth 整合包"), logging.INFO)
        
        instance = Path(instance_path)
        if not instance.exists():
            log(f"实例路径不存在：{instance_path}", logging.ERROR)
            return False
        
        # 检测游戏版本和加载器
        game_version = detect_game_version(instance_path)
        loader = detect_loader(instance_path)
        
        log(f"检测到游戏版本：{game_version}", logging.INFO)
        if loader:
            log(f"检测到加载器：{loader['name']} {loader['version']}", logging.INFO)
        
        # 构建依赖项
        dependencies = {"minecraft": game_version}
        if loader:
            dependencies[loader['name']] = loader['version']
        
        # 收集文件
        files_list = collect_files(instance_path)
        log(f"收集到 {len(files_list)} 个文件", logging.INFO)
        
        if not files_list:
            log("没有找到可导出的文件", logging.WARNING)
        
        # 构建 index 文件
        index = {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": version,
            "name": name,
            "summary": summary,
            "files": [],
            "dependencies": dependencies
        }
        
        # 创建 ZIP 文件
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 处理每个文件
            for file_info in files_list:
                source_path = Path(file_info['source'])
                target_path = file_info['path']
                
                if not source_path.exists():
                    log(f"文件不存在，跳过：{source_path}", logging.WARNING)
                    continue
                
                # 计算哈希
                sha512_hash = calculate_hash(source_path, 'sha512')
                sha1_hash = calculate_hash(source_path, 'sha1')
                
                if not sha512_hash or not sha1_hash:
                    log(f"计算哈希失败，跳过：{source_path}", logging.WARNING)
                    continue
                
                # 构建文件条目
                file_entry = {
                    "path": target_path,
                    "hashes": {
                        "sha512": sha512_hash,
                        "sha1": sha1_hash
                    },
                    "fileSize": source_path.stat().st_size
                }
                
                # 添加环境要求
                if 'env' in file_info:
                    file_entry['env'] = file_info['env']
                
                index['files'].append(file_entry)
                
                # 将文件添加到 ZIP 的 files/ 目录下
                arcname = f"files/{target_path}"
                zipf.write(source_path, arcname)
                log(f"添加文件到整合包：{target_path}", logging.DEBUG)
            
            # 写入 index 文件
            zipf.writestr('modrinth.index.json', json.dumps(index, indent=2))
        
        log(f"整合包导出成功：{output_path}", logging.INFO)
        log(f"  - 名称：{name}", logging.INFO)
        log(f"  - 版本：{version}", logging.INFO)
        log(f"  - 游戏版本：{game_version}", logging.INFO)
        log(f"  - 文件数量：{len(index['files'])}", logging.INFO)
        
        return True
        
    except Exception as e:
        log(f"导出整合包失败：{str(e)}", logging.ERROR)
        import traceback
        log(traceback.format_exc(), logging.ERROR)
        return False


def get_instance_info(instance_path):
    """获取实例信息用于导出对话框"""
    try:
        info = {
            "name": Path(instance_path).name,
            "game_version": detect_game_version(instance_path),
            "loader": detect_loader(instance_path),
            "file_count": len(collect_files(instance_path))
        }
        return info
    except Exception as e:
        log(f"获取实例信息失败：{str(e)}", logging.ERROR)
        return None
