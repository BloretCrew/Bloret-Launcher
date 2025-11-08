import sys
import ctypes
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt5.QtGui import QGuiApplication, QScreen, QPixmap, QPainter, QColor, QCursor
from PyQt5 import uic
import win32gui
import win32con
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
        
        # 初始化透明度属性
        self._opacity = 0.0
        self.setWindowOpacity(self._opacity)
        
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
        self.current_hover_rect = None  # 当前悬停窗口的矩形
        
        # 设置鼠标光标为十字形
        self.setCursor(QCursor(Qt.CrossCursor))
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 保存当前窗口大小（防止UI设置改变窗口大小）
        current_size = self.size()
        
        # 创建UI界面 - 直接加载UI文件
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'ScreenCut.ui')
        if os.path.exists(ui_file_path):
            uic.loadUi(ui_file_path, self)
            print(f"成功加载UI文件: {ui_file_path}")
        else:
            print(f"UI文件不存在: {ui_file_path}，使用默认界面")
        
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
                self.CardWidget.adjustSize()
                
                # 获取调整后的大小
                widget_width = self.CardWidget.width()
                widget_height = self.CardWidget.height()
                
                # 计算居中位置（屏幕顶部中央）
                x = screen_geometry.x() + (screen_geometry.width() - widget_width) // 2
                y = screen_geometry.y() + 50
                
                # 移动并确保可见
                self.CardWidget.move(x, y)
                self.CardWidget.raise_()
                self.CardWidget.show()
                print(f"提示信息已显示在位置: ({x}, {y})")
        else:
            # fallback 方案
            self.CardWidget.move(100, 50)
            self.CardWidget.raise_()
            self.CardWidget.show()
    
    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.is_selecting = True
        # 确保窗口在最前端
        self.raise_()
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    def fade_in(self):
        """淡入动画"""
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(300)  # 300ms 淡入
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.start()
    
    def fade_out(self):
        """淡出动画"""
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(200)  # 200ms 淡出
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InQuad)
        self.fade_animation.finished.connect(self.finish_close)
        self.fade_animation.start()
    
    def finish_close(self):
        """完成淡出后关闭窗口"""
        super().close()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
        else:
            # 非选择状态下，检测当前鼠标位置的窗口
            self.update_hover_window(event.pos())
            self.update()
    
    def update_hover_window(self, pos):
        """更新悬停窗口的矩形"""
        # 将相对坐标转换为全局坐标
        global_point = self.mapToGlobal(pos)
        
        # 检查鼠标位置是否变化很大，只有变化较大时才重新检测
        if hasattr(self, 'last_hover_pos') and (abs(global_point.x() - self.last_hover_pos.x()) < 20 and 
                                               abs(global_point.y() - self.last_hover_pos.y()) < 20):
            return  # 鼠标移动距离很小，不需要重新检测
        
        self.last_hover_pos = global_point
        
        # 获取当前屏幕信息
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # 使用更聪明的方法：获取当前窗口句柄，然后排除它
        self_hwnd = None
        try:
            self_hwnd = int(self.winId())
        except:
            pass
        
        # 使用更精确的方法获取窗口层次结构
        hwnd = None
        
        # 方法1: 先尝试获取顶层窗口
        hwnd = win32gui.WindowFromPoint((global_point.x(), global_point.y()))
        
        # 方法2: 如果获取到的是截图窗口或桌面，使用更精确的检测
        if hwnd == self_hwnd or hwnd == win32gui.GetDesktopWindow():
            # 尝试使用 WindowFromPoint 结合 WS_EX_TRANSPARENT 属性
            # 或者使用 EnumWindows 找到合适的窗口
            
            # 获取所有顶层窗口
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    rect = win32gui.GetWindowRect(hwnd)
                    # 检查点是否在窗口内
                    if (rect[0] <= global_point.x() <= rect[2] and 
                        rect[1] <= global_point.y() <= rect[3] and
                        hwnd != self_hwnd and
                        hwnd != win32gui.GetDesktopWindow()):
                        # 检查窗口大小是否合理
                        if (rect[2] - rect[0] < screen_geometry.width() - 100 and
                            rect[3] - rect[1] < screen_geometry.height() - 100):
                            windows.append((hwnd, rect))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # 选择最上层的合适窗口（通常是最后一个）
            if windows:
                hwnd, rect = windows[-1]  # 取最上层的窗口
            else:
                hwnd = None
        
        if hwnd and hwnd != self_hwnd and hwnd != win32gui.GetDesktopWindow():
            try:
                # 获取窗口矩形（屏幕坐标）
                rect = win32gui.GetWindowRect(hwnd)
                
                # 只在窗口变化时打印一次
                window_title = win32gui.GetWindowText(hwnd)
                print(f"检测到新窗口: {window_title} {rect}")
                
                # 更新提示信息的标题为当前窗口标题
                if hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                    self.ScreenCut_Title.setText(f"当前窗口：{window_title}")
                
                # 检查窗口是否有效（不是整个屏幕）
                if rect[2] - rect[0] >= screen_geometry.width() - 1 and rect[3] - rect[1] >= screen_geometry.height() - 1:
                    self.current_hover_rect = None
                    return
                
                # 检查窗口是否可见且有实际内容
                if not win32gui.IsWindowVisible(hwnd):
                    self.current_hover_rect = None
                    return
                
                # 检查是否是同一个窗口（避免重复绘制）
                if hasattr(self, 'last_hover_hwnd') and self.last_hover_hwnd == hwnd:
                    return  # 同一个窗口，不需要更新
                
                self.last_hover_hwnd = hwnd
                
                # 获取窗口客户区矩形（更准确的实际内容区域）
                try:
                    # 尝试获取客户区矩形
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_top_left = win32gui.ClientToScreen(hwnd, (0, 0))
                    
                    # 计算边框大小
                    border_left = client_top_left[0] - rect[0]
                    border_top = client_top_left[1] - rect[1]
                    border_right = rect[2] - (client_top_left[0] + client_rect[2])
                    border_bottom = rect[3] - (client_top_left[1] + client_rect[3])
                    
                    print(f"  窗口边框: 左={border_left}, 上={border_top}, 右={border_right}, 下={border_bottom}")
                    
                    # 使用客户区矩形作为实际绘制区域
                    draw_rect = (client_top_left[0], client_top_left[1], 
                               client_top_left[0] + client_rect[2], client_top_left[1] + client_rect[3])
                except:
                    # 如果无法获取客户区，使用原始窗口矩形
                    draw_rect = rect
                
                # 转换为相对于截图窗口的坐标
                top_left = self.mapFromGlobal(QPoint(draw_rect[0], draw_rect[1]))
                bottom_right = self.mapFromGlobal(QPoint(draw_rect[2], draw_rect[3]))
                
                # 创建相对于截图窗口的矩形
                self.current_hover_rect = QRect(top_left, bottom_right)
                
            except Exception as e:
                print(f"  错误: {e}")
                self.current_hover_rect = None
                self.last_hover_hwnd = None
        else:
            print(f"  未找到有效窗口句柄: hwnd={hwnd}, self_hwnd={self_hwnd}")
            self.current_hover_rect = None
            self.last_hover_hwnd = None
            
            # 当没有检测到窗口时，显示默认提示信息
            if hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                self.ScreenCut_Title.setText("移动鼠标选择窗口，或拖拽框选区域")
    
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
        
        # 完成截图后启动淡出动画
        self.fade_out()
    
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
            
            # 绘制悬停窗口的矩形框
            if self.current_hover_rect and not self.current_hover_rect.isEmpty():
                # 绘制悬停窗口的高亮边框
                painter.setPen(Qt.blue)  # 使用蓝色边框
                painter.drawRect(self.current_hover_rect)
                
                # 绘制半透明的填充
                hover_color = QColor(100, 100, 255, 30)  # 半透明的蓝色
                painter.fillRect(self.current_hover_rect, hover_color)
    
    def capture_window_at_point(self, point):
        """根据点击位置获取窗口并截图"""
        # 隐藏整个截图工具窗口
        self.hide()
        QApplication.processEvents()  # 确保窗口完全隐藏
        
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
        
        # 截图完成后直接关闭窗口（不再显示）
        # 注意：由于我们要关闭窗口，不需要重新显示
    
    def capture_region(self, rect):
        """截取指定区域"""
        # 隐藏整个截图工具窗口
        self.hide()
        QApplication.processEvents()  # 确保窗口完全隐藏
        
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
            
            # 添加提示信息
            print(f"区域截图已复制到剪贴板")
        
        # 截图完成后直接关闭窗口（不再显示）
        # 注意：由于我们要关闭窗口，不需要重新显示


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
    
    # 启动淡入动画
    capture_widget.fade_in()
    
    # 返回widget实例以便外部控制
    return capture_widget