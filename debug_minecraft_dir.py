#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to check minecraft_dir initialization
"""

import os
import sys

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 调试 minecraft_dir 初始化 ===")

# 测试导入和配置加载
print("\n1. 导入模块...")
try:
    import modules.globals as BLglobals
    print(f"   - globals模块导入成功")
    print(f"   - BLglobals.minecraft_dir 初始值: '{BLglobals.minecraft_dir}'")
    print(f"   - BLglobals.config_path 初始值: '{BLglobals.config_path}'")
except Exception as e:
    print(f"   - 导入globals模块失败: {e}")

print("\n2. 加载配置...")
try:
    import modules.config as cfg
    print(f"   - config模块导入成功")
    print(f"   - BLglobals.config_path 最终值: '{BLglobals.config_path}'")
    print(f"   - BLglobals.minecraft_dir 最终值: '{BLglobals.minecraft_dir}'")
    
    # 尝试读取配置
    config_data = cfg.read()
    print(f"   - 配置内容中的minecraft_dir: '{config_data.get('minecraft_dir', '未找到')}'")
    
except Exception as e:
    print(f"   - 配置加载失败: {e}")
    import traceback
    traceback.print_exc()

print("\n3. 检查路径...")
if BLglobals.minecraft_dir:
    versions_path = os.path.join(BLglobals.minecraft_dir, 'versions')
    print(f"   - versions路径: {versions_path}")
    print(f"   - versions路径存在: {os.path.exists(versions_path)}")
else:
    print("   - minecraft_dir为空，无法检查versions路径")

print("\n=== 调试完成 ===")