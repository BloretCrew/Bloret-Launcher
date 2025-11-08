from PyQt5.QtWidgets import QApplication
import sys
import time
from modules.ShortCut import ScreenShortCut
from PyQt5.QtCore import QTimer

def test_screenshot():
    """测试截图功能"""
    print("启动截图测试...")
    
    app = QApplication(sys.argv)
    
    # 创建截图窗口
    screenshot_widget = ScreenShortCut()
    
    print("截图窗口已创建")
    print(f"窗口几何信息: {screenshot_widget.geometry()}")
    print(f"窗口标志: {screenshot_widget.windowFlags()}")
    
    # 10秒后自动关闭（用于测试）
    QTimer.singleShot(10000, lambda: app.quit())
    
    print("程序将在5秒后自动退出...")
    print("您可以在这5秒内测试截图功能：")
    print("- 点击窗口进行窗口截图")
    print("- 拖拽鼠标进行区域截图")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_screenshot()