#!/usr/bin/env python3
"""
测试获取 Minecraft 窗口句柄的功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.launch import get_minecraft_window_handle, monitor_minecraft_window
from modules.log import log
import time

def test_window_monitor():
    """测试窗口监控功能"""
    print("🧪 测试 Minecraft 窗口监控功能")
    print("=" * 50)
    
    # 测试1: 直接获取窗口句柄
    print("\n📋 测试1: 直接获取 Minecraft 窗口句柄")
    print("请在10秒内启动 Minecraft...")
    
    hwnd = get_minecraft_window_handle(version="1.21.8", timeout=10)
    
    if hwnd:
        print(f"✅ 成功获取到 Minecraft 窗口句柄: {hwnd}")
        print(f"🔍 十六进制格式: 0x{hwnd:08X}")
    else:
        print("❌ 未找到 Minecraft 窗口")
    
    # 测试2: 使用监控线程
    print("\n📋 测试2: 使用监控线程")
    print("请在10秒内启动 Minecraft...")
    
    monitor_thread = monitor_minecraft_window("1.21.8")
    
    # 等待监控完成
    monitor_thread.join(timeout=35)  # 等待最多35秒（3秒初始延迟 + 30秒超时）
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_window_monitor()