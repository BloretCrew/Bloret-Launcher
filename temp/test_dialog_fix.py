#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 测试VersionNameInputDialog修复 ===")

# 测试VersionNameInputDialog的get_minecraft_dir方法
print("\n1. 测试get_minecraft_dir方法:")
try:
    from modules.setup_ui import VersionNameInputDialog
    
    # 创建实例（不显示UI）
    dialog = VersionNameInputDialog("1.21.8", is_fabric=False)
    
    minecraft_dir = dialog.get_minecraft_dir()
    print(f"   get_minecraft_dir()返回: {repr(minecraft_dir)}")
    
    if minecraft_dir:
        print("   ✅ 成功获取minecraft_dir")
        
        # 测试版本文件夹检查
        print("\n2. 测试版本文件夹检查:")
        versions_path = os.path.join(minecraft_dir, "versions")
        version_path = os.path.join(versions_path, "1.21.8")
        
        print(f"   versions目录: {versions_path}")
        print(f"   versions目录存在: {os.path.exists(versions_path)}")
        print(f"   1.21.8版本目录: {version_path}")
        print(f"   1.21.8版本目录存在: {os.path.exists(version_path)}")
        
        # 测试version_folder_exists方法
        print("\n3. 测试version_folder_exists方法:")
        exists = dialog.version_folder_exists("1.21.8")
        print(f"   version_folder_exists('1.21.8')返回: {exists}")
        
        if exists:
            print("   ✅ 版本文件夹存在检查通过")
        else:
            print("   ❌ 版本文件夹存在检查失败")
            
    else:
        print("   ❌ minecraft_dir仍为空")
        
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")