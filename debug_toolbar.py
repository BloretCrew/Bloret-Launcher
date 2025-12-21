#!/usr/bin/env python3
"""
调试工具栏功能的脚本
"""
import sys
import time
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 测试工具栏创建
def test_toolbar_creation():
    print("🚀 开始调试工具栏功能...")
    
    # 确保QApplication存在
    app = QApplication.instance()
    if not app:
        print("📱 创建QApplication实例...")
        app = QApplication(sys.argv)
    else:
        print("📱 使用现有的QApplication实例")
    
    # 测试导入
    try:
        from modules.launch import monitor_minecraft_window, get_minecraft_window_handle
        from modules import mwtool
        print("✅ 成功导入工具栏模块")
    except Exception as e:
        print(f"❌ 导入模块失败: {e}")
        return
    
    # 测试版本
    test_version = "1.21.8"
    
    print(f"🔍 测试版本: {test_version}")
    
    # 测试获取窗口句柄
    print("🔍 正在查找Minecraft窗口...")
    hwnd = get_minecraft_window_handle(test_version, timeout=5)
    
    if hwnd:
        print(f"✅ 找到Minecraft窗口！句柄: {hwnd}")
        
        # 测试直接创建工具栏
        print("🛠️ 直接创建工具栏...")
        try:
            tool = mwtool.create_minecraft_tool(hwnd, test_version)
            if tool:
                print("✅ 工具栏创建成功！")
                print(f"   - 工具栏对象: {tool}")
                print(f"   - 可见性: {tool.isVisible()}")
                print(f"   - 几何信息: {tool.geometry()}")
                
                # 运行一段时间观察
                print("⏱️ 运行5秒观察工具栏行为...")
                start_time = time.time()
                while time.time() - start_time < 5:
                    app.processEvents()
                    time.sleep(0.1)
                    
                print("🧹 清理工具栏...")
                mwtool.hide_minecraft_tool()
                
            else:
                print("❌ 工具栏创建返回None")
        except Exception as e:
            print(f"❌ 工具栏创建失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ 未找到Minecraft窗口，使用模拟句柄测试...")
        # 使用模拟句柄测试
        try:
            tool = mwtool.create_minecraft_tool(12345, test_version)
            if tool:
                print("✅ 模拟工具栏创建成功！")
                print(f"   - 工具栏对象: {tool}")
                print(f"   - 可见性: {tool.isVisible()}")
                print(f"   - 几何信息: {tool.geometry()}")
                
                # 运行一段时间观察
                print("⏱️ 运行3秒观察工具栏行为...")
                start_time = time.time()
                while time.time() - start_time < 3:
                    app.processEvents()
                    time.sleep(0.1)
                    
                print("🧹 清理工具栏...")
                mwtool.hide_minecraft_tool()
            else:
                print("❌ 模拟工具栏创建返回None")
        except Exception as e:
            print(f"❌ 模拟工具栏创建失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("✅ 调试完成！")

if __name__ == "__main__":
    test_toolbar_creation()