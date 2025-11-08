import sys
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QGuiApplication, QScreen, QPixmap, QPainter, QColor, QCursor
import win32gui
import win32con
from ui.ScreenCut import Ui_Form
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import CardWidget, BodyLabel, StrongBodyLabel, CaptionLabel

# 设置Windows DPI感知，确保正确获取屏幕尺寸
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass


class ScreenCaptureWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口为全屏覆盖层 - 确保能接收鼠标事件
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 获取所有屏幕的组合几何区域
        screens = QGuiApplication.screens()
        if screens:
            # 计算所有屏幕的组合区域
            total_geometry = QRect()
            for screen in screens:
                total_geometry = total_geometry.united(screen.geometry())
                print(f"屏幕 {screen.name()}: {screen.geometry()}")
            
            # 设置窗口覆盖所有屏幕
            self.setGeometry(total_geometry)
            print(f"窗口已设置为多屏幕模式，大小: {self.geometry()}")
        else:
            # fallback 方案
            print("未找到屏幕，使用默认尺寸")
            self.setGeometry(0, 0, 1920, 1080)
            print(f"窗口已设置为默认尺寸: {self.geometry()}")
        
        # 确保窗口状态正确
        self.setWindowState(Qt.WindowFullScreen)
        self.showFullScreen()
        
        # 确保窗口在最前面
        self.raise_()
        self.activateWindow()
        
        # 设置变量
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        
        # 设置鼠标光标为十字形
        self.setCursor(QCursor(Qt.CrossCursor))
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 保存当前窗口大小（防止UI设置改变窗口大小）
        current_size = self.size()
        
        # 创建UI界面
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # 恢复窗口大小
        self.resize(current_size)
        
        # 设置提示界面位置在屏幕中央顶部
        screens = QGuiApplication.screens()
        if screens:
            # 使用主屏幕的几何信息
            primary_screen = QGuiApplication.primaryScreen()
            if primary_screen:
                screen_geometry = primary_screen.geometry()
                # 确保UI组件大小正确
                self.ui.CardWidget.adjustSize()
                
                # 获取调整后的大小
                widget_width = self.ui.CardWidget.width()
                widget_height = self.ui.CardWidget.height()
                
                # 计算居中位置（屏幕顶部中央）
                x = screen_geometry.x() + (screen_geometry.width() - widget_width) // 2
                y = screen_geometry.y() + 50
                
                # 移动并确保可见
                self.ui.CardWidget.move(x, y)
                self.ui.CardWidget.raise_()
                self.ui.CardWidget.show()
                print(f"提示信息已显示在位置: ({x}, {y})")
        else:
            # fallback 方案
            self.ui.CardWidget.move(100, 50)
            self.ui.CardWidget.raise_()
            self.ui.CardWidget.show()
    
    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.is_selecting = True
        # 确保窗口在最前端
        self.raise_()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        self.end_pos = event.pos()
        self.is_selecting = False
        
        if self.start_pos == self.end_pos:
            # 点击截图模式
            self.capture_window_at_point(event.pos())
        else:
            # 区域截图模式
            rect = QRect(self.start_pos, self.end_pos).normalized()
            self.capture_region(rect)
        
        # 完成截图后关闭窗口
        self.close()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明遮罩
        if self.is_selecting and self.start_pos and self.end_pos:
            # 正在选择区域时，绘制较暗的背景
            overlay_color = QColor(0, 0, 0, 120)
            painter.fillRect(self.rect(), overlay_color)
            
            # 绘制选择区域
            selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.black)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # 绘制边框
            painter.setPen(Qt.red)
            painter.drawRect(selection_rect)
        else:
            # 初始状态，绘制半透明遮罩
            overlay_color = QColor(0, 0, 0, 80)
            painter.fillRect(self.rect(), overlay_color)
    
    def capture_window_at_point(self, point):
        """根据点击位置获取窗口并截图"""
        # 将相对坐标转换为全局坐标
        global_point = self.mapToGlobal(point)
        
        # 获取该点的窗口句柄
        hwnd = win32gui.WindowFromPoint((global_point.x(), global_point.y()))
        
        # 如果找到了窗口
        if hwnd:
            # 获取窗口位置和大小
            try:
                rect = win32gui.GetWindowRect(hwnd)
                x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
                
                # 截取窗口区域
                screen = QGuiApplication.primaryScreen()
                if screen:
                    screenshot = screen.grabWindow(0, x, y, w, h)
                    
                    # 复制到剪贴板
                    clipboard = QApplication.clipboard()
                    clipboard.setPixmap(screenshot)
                    
                    # 添加提示信息
                    print(f"截图已复制到剪贴板")
            except Exception as e:
                print(f"Error capturing window: {e}")
    
    def capture_region(self, rect):
        """截取指定区域"""
        # 转换为全局坐标
        global_top_left = self.mapToGlobal(rect.topLeft())
        
        # 截取指定区域
        screen = QGuiApplication.primaryScreen()
        if screen:
            screenshot = screen.grabWindow(
                0, 
                global_top_left.x(), 
                global_top_left.y(), 
                rect.width(), 
                rect.height()
            )
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(screenshot)


def ScreenShortCut():
    """
    运行后激活截图功能：
    选择界面：
    当鼠标放到一个窗口上时，单击则将该窗口的截图复制到剪贴板。
    如果鼠标按住拖动，则将鼠标最终框选的矩形区域截图复制到剪贴板
    """
    # 创建并显示截图工具
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        print("创建新的QApplication实例")
    
    # 确保应用程序可以显示全屏窗口
    app.setQuitOnLastWindowClosed(True)
    
    capture_widget = ScreenCaptureWidget()
    print(f"创建ScreenCaptureWidget实例，窗口标志: {capture_widget.windowFlags()}")
    
    # 显示窗口并确保正确显示
    capture_widget.show()
    capture_widget.showFullScreen()
    print(f"窗口已显示，位置: {capture_widget.geometry()}")
    
    # 强制窗口到最前面
    capture_widget.raise_()
    capture_widget.activateWindow()
    print("调用raise_()和activateWindow()确保窗口在最前面")
    
    # 处理所有待处理的事件
    for _ in range(5):  # 多次处理事件确保窗口正确显示
        QApplication.processEvents()
    print("多次调用processEvents()确保事件循环处理完成")
    
    # 返回widget实例以便外部控制
    return capture_widget