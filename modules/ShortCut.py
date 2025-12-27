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

# # 设置Windows DPI感知，确保正确获取屏幕尺寸
# try:
#     ctypes.windll.user32.SetProcessDPIAware()
# except:
#     pass


class ScreenCaptureWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口为全屏覆盖层 - 确保能接收鼠标事件
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 初始化透明度属性
        self._opacity = 0.0
        self.setWindowOpacity(self._opacity)
        
        # 获取屏幕缩放比例 (DPI Ratio)
        self.dpr = self.devicePixelRatioF()
        
        # 获取所有屏幕的组合几何区域
        screens = QGuiApplication.screens()
        if screens:
            total_geometry = QRect()
            for screen in screens:
                total_geometry = total_geometry.united(screen.geometry())
            self.setGeometry(total_geometry)
        else:
            self.setGeometry(0, 0, 1920, 1080)
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        # 设置变量
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.current_hover_rect = None
        self.last_hover_hwnd = None
        self.last_hover_pos = None
        
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)
        
        # UI 初始化
        current_size = self.size()
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'ScreenCut.ui')
        if os.path.exists(ui_file_path):
            uic.loadUi(ui_file_path, self)
        else:
            print(f"UI文件不存在: {ui_file_path}")
        self.resize(current_size)
        
        # 延时初始化提示框位置
        QTimer.singleShot(50, self._update_tip_geometry)

    def _update_tip_geometry(self):
        """强制更新提示框位置（居中显示在主屏顶部）"""
        if not hasattr(self, 'CardWidget'):
            return

        screens = QGuiApplication.screens()
        if screens:
            primary_screen = QGuiApplication.primaryScreen()
            if primary_screen:
                screen_geometry = primary_screen.geometry()
                
                self.CardWidget.adjustSize()
                widget_width = self.CardWidget.width()
                
                # 计算逻辑坐标
                target_global_x = screen_geometry.x() + (screen_geometry.width() - widget_width) // 2
                target_global_y = screen_geometry.y() + 50
                
                # 转换为局部坐标
                local_x = target_global_x - self.geometry().x()
                local_y = target_global_y - self.geometry().y()
                
                self.CardWidget.move(local_x, local_y)
                self.CardWidget.raise_()
                self.CardWidget.show()
        else:
            self.CardWidget.move(100, 50)
            self.CardWidget.show()

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.is_selecting = True
        self.raise_()
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    def fade_in(self):
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.start()
    
    def fade_out(self):
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InQuad)
        self.fade_animation.finished.connect(self.finish_close)
        self.fade_animation.start()
    
    def finish_close(self):
        super().close()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
        else:
            self.update_hover_window(event.pos())
            self.update()
    
    def update_hover_window(self, pos):
        """更新悬停窗口的矩形（修复DPI偏移问题）"""
        # 1. 将 Qt 逻辑坐标转换为全局逻辑坐标
        global_point_logical = self.mapToGlobal(pos)
        
        # 检查防抖
        if self.last_hover_pos and (abs(global_point_logical.x() - self.last_hover_pos.x()) < 10 and 
                                    abs(global_point_logical.y() - self.last_hover_pos.y()) < 10):
            return
        self.last_hover_pos = global_point_logical
        
        # 2. 将全局逻辑坐标转换为物理坐标 (传给 win32gui)
        # self.dpr 是 self.devicePixelRatioF()
        phy_x = int(global_point_logical.x() * self.dpr)
        phy_y = int(global_point_logical.y() * self.dpr)
        
        self_hwnd = int(self.winId()) if self.winId() else 0
        
        # 使用物理坐标查询窗口
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        
        # 排除自身和桌面
        if hwnd == self_hwnd or hwnd == win32gui.GetDesktopWindow():
            # 简单的向下查找逻辑 (EnumWindows 可能会比较慢，这里简化处理)
            hwnd = None 

        if hwnd and hwnd != self_hwnd:
            try:
                # 获取物理矩形
                rect = win32gui.GetWindowRect(hwnd) # Returns (left, top, right, bottom) in physical pixels
                
                # 更新文字并重新定位（解决位置重置问题）
                window_title = win32gui.GetWindowText(hwnd)
                if hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                    current_text = self.ScreenCut_Title.text()
                    new_text = f"当前窗口：{window_title}"
                    if current_text != new_text:
                        self.ScreenCut_Title.setText(new_text)
                        # 关键：文字改变后重新计算位置
                        self._update_tip_geometry()

                if not win32gui.IsWindowVisible(hwnd):
                    self.current_hover_rect = None
                    return

                if self.last_hover_hwnd == hwnd:
                    return
                self.last_hover_hwnd = hwnd
                
                # 3. 将物理矩形转换回逻辑矩形 (供 Qt 绘图)
                # ClientRect 处理
                try:
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_tl = win32gui.ClientToScreen(hwnd, (0, 0))
                    # 物理绘制区域
                    draw_rect_phy = (client_tl[0], client_tl[1], 
                                     client_tl[0] + client_rect[2], client_tl[1] + client_rect[3])
                except:
                    draw_rect_phy = rect

                # 物理转逻辑
                log_x = int(draw_rect_phy[0] / self.dpr)
                log_y = int(draw_rect_phy[1] / self.dpr)
                log_w = int((draw_rect_phy[2] - draw_rect_phy[0]) / self.dpr)
                log_h = int((draw_rect_phy[3] - draw_rect_phy[1]) / self.dpr)

                # 转换为相对于截图窗口的坐标
                top_left = self.mapFromGlobal(QPoint(log_x, log_y))
                self.current_hover_rect = QRect(top_left.x(), top_left.y(), log_w, log_h)
                
            except Exception as e:
                print(f"Window detect error: {e}")
                self.current_hover_rect = None
        else:
            self.current_hover_rect = None
            self.last_hover_hwnd = None
            if hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                if self.ScreenCut_Title.text() != "移动鼠标选择窗口，或拖拽框选区域":
                    self.ScreenCut_Title.setText("移动鼠标选择窗口，或拖拽框选区域")
                    self._update_tip_geometry()
    
    def mouseReleaseEvent(self, event):
        self.end_pos = event.pos()
        self.is_selecting = False
        
        if self.start_pos == self.end_pos:
            self.capture_window_at_point(event.pos())
        else:
            # 区域截图使用的是 Qt 逻辑坐标，无需转换
            rect = QRect(self.start_pos, self.end_pos).normalized()
            self.capture_region(rect)
        
        self.fade_out()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        if self.is_selecting and self.start_pos and self.end_pos:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
            selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.black)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(Qt.red)
            painter.drawRect(selection_rect)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
            if self.current_hover_rect and not self.current_hover_rect.isEmpty():
                painter.setPen(QColor(0, 120, 215))
                painter.setBrush(QColor(0, 120, 215, 50))
                painter.drawRect(self.current_hover_rect)
    
    def capture_window_at_point(self, point):
        """点击截图（修复DPI偏移）"""
        self.hide()
        QApplication.processEvents()
        
        # 逻辑转物理
        global_point = self.mapToGlobal(point)
        phy_x = int(global_point.x() * self.dpr)
        phy_y = int(global_point.y() * self.dpr)
        
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        
        if hwnd:
            try:
                rect = win32gui.GetWindowRect(hwnd) # 物理坐标
                # 物理转逻辑 (Qt grabWindow 需要逻辑坐标)
                x = int(rect[0] / self.dpr)
                y = int(rect[1] / self.dpr)
                w = int((rect[2] - rect[0]) / self.dpr)
                h = int((rect[3] - rect[1]) / self.dpr)
                
                screen = QGuiApplication.primaryScreen()
                if screen:
                    screenshot = screen.grabWindow(0, x, y, w, h)
                    QApplication.clipboard().setPixmap(screenshot)
                    print(f"截图已复制到剪贴板")
            except Exception as e:
                print(f"Error capturing window: {e}")
    
    def capture_region(self, rect):
        """区域截图"""
        self.hide()
        QApplication.processEvents()
        
        global_top_left = self.mapToGlobal(rect.topLeft())
        x, y, w, h = global_top_left.x(), global_top_left.y(), rect.width(), rect.height()

        screen = QGuiApplication.primaryScreen()
        if screen:
            screenshot = screen.grabWindow(0, x, y, w, h)
            QApplication.clipboard().setPixmap(screenshot)
            print(f"区域截图已复制到剪贴板")


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
    # 修改：仅调用 show()，不要调用 showFullScreen()，否则会重置大小为主屏幕大小
    capture_widget.show()
    # capture_widget.showFullScreen() # 已删除
    
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