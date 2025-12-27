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
        # 设置窗口为全屏覆盖层
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 初始化透明度
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
        
        # 状态变量
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.current_hover_rect = None
        self.last_hover_hwnd = None
        self.last_hover_pos = None
        
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)
        
        # UI 加载
        current_size = self.size()
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'ScreenCut.ui')
        if os.path.exists(ui_file_path):
            uic.loadUi(ui_file_path, self)
            
            # --- 关键修复：彻底从布局管理器中剥离 CardWidget ---
            # 仅仅调用 removeWidget 可能不够（如果控件在嵌套布局中）。
            # 通过重设 Parent，可以确保它彻底脱离原有的布局约束。
            if hasattr(self, 'CardWidget'):
                self.CardWidget.setParent(None)  # 1. 移除父对象（自动脱离布局）
                self.CardWidget.setParent(self)  # 2. 重新挂载为本窗口子对象
                self.CardWidget.show()           # 3. 重新显示（setParent(None)会隐藏控件）
            # --------------------------------------------
            
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
                
                # 计算主屏顶部的逻辑坐标
                target_global_x = screen_geometry.x() + (screen_geometry.width() - widget_width) // 2
                target_global_y = screen_geometry.y() + 50
                
                # 使用 mapFromGlobal 确保坐标在多屏/高DPI下正确转换
                local_pos = self.mapFromGlobal(QPoint(target_global_x, target_global_y))
                
                self.CardWidget.move(local_pos)
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
            self.update() # 触发重绘
        else:
            self.update_hover_window(event.pos())
            self.update() # 触发重绘
    
    def update_hover_window(self, pos):
        """检测鼠标下的窗口（包含DPI修正和穿透检测）"""
        # 1. Qt逻辑坐标 转 物理坐标
        global_point_logical = self.mapToGlobal(pos)
        
        # 简单的防抖动
        if self.last_hover_pos and (abs(global_point_logical.x() - self.last_hover_pos.x()) < 5 and 
                                    abs(global_point_logical.y() - self.last_hover_pos.y()) < 5):
            return
        self.last_hover_pos = global_point_logical
        
        phy_x = int(global_point_logical.x() * self.dpr)
        phy_y = int(global_point_logical.y() * self.dpr)
        
        self_hwnd = int(self.winId()) if self.winId() else 0
        
        # 2. 获取鼠标下的窗口句柄
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        
        # 3. 如果检测到的是截图层自己，则通过遍历寻找下层窗口
        if hwnd == self_hwnd or hwnd == win32gui.GetDesktopWindow():
            hwnd = None
            def enum_cb(wnd, result_list):
                # 过滤掉自己、不可见窗口
                if wnd != self_hwnd and win32gui.IsWindowVisible(wnd):
                    try:
                        rect = win32gui.GetWindowRect(wnd)
                        # 检查点是否在窗口内
                        if rect[0] <= phy_x < rect[2] and rect[1] <= phy_y < rect[3]:
                            # 过滤掉尺寸异常小的窗口
                            if rect[2] - rect[0] > 10 and rect[3] - rect[1] > 10:
                                result_list.append(wnd)
                    except:
                        pass
                return True
            
            found_windows = []
            win32gui.EnumWindows(enum_cb, found_windows)
            
            # EnumWindows 通常按 Z-order 顺序返回，取第一个即为最上层窗口
            for w in found_windows:
                if w != win32gui.GetDesktopWindow():
                    hwnd = w
                    break

        # 4. 如果找到了有效的窗口
        if hwnd and hwnd != self_hwnd:
            try:
                # 获取物理矩形
                rect = win32gui.GetWindowRect(hwnd)
                
                # 更新提示文字
                window_title = win32gui.GetWindowText(hwnd)
                if hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                    new_text = f"当前窗口：{window_title}" if window_title else "当前窗口"
                    # 当文字改变时，调用 _update_tip_geometry
                    if self.ScreenCut_Title.text() != new_text:
                        self.ScreenCut_Title.setText(new_text)
                        self._update_tip_geometry() 
                
                if self.last_hover_hwnd == hwnd:
                    return
                self.last_hover_hwnd = hwnd

                # 5. 计算绘制区域（物理 -> 逻辑）
                # 尝试获取客户区以去除阴影干扰，如果失败则用窗口矩形
                try:
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_tl = win32gui.ClientToScreen(hwnd, (0, 0))
                    draw_rect_phy = (client_tl[0], client_tl[1], 
                                     client_tl[0] + client_rect[2], client_tl[1] + client_rect[3])
                except:
                    draw_rect_phy = rect

                # 物理坐标除以 DPR 得到逻辑坐标
                log_x = int(draw_rect_phy[0] / self.dpr)
                log_y = int(draw_rect_phy[1] / self.dpr)
                log_w = int((draw_rect_phy[2] - draw_rect_phy[0]) / self.dpr)
                log_h = int((draw_rect_phy[3] - draw_rect_phy[1]) / self.dpr)

                # 转换为相对于截图窗口的局部坐标
                top_left = self.mapFromGlobal(QPoint(log_x, log_y))
                self.current_hover_rect = QRect(top_left.x(), top_left.y(), log_w, log_h)
                
            except Exception as e:
                # print(f"Window detect error: {e}")
                self.current_hover_rect = None
        else:
            self.current_hover_rect = None
            self.last_hover_hwnd = None
            # 恢复默认提示
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
            rect = QRect(self.start_pos, self.end_pos).normalized()
            self.capture_region(rect)
        
        self.fade_out()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景遮罩
        if self.is_selecting and self.start_pos and self.end_pos:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
            selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.black)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(Qt.red)
            painter.drawRect(selection_rect)
        else:
            # 默认背景色
            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
            # 绘制窗口识别框
            if self.current_hover_rect and not self.current_hover_rect.isEmpty():
                painter.setPen(QColor(0, 120, 215)) # 蓝色边框
                painter.setBrush(QColor(0, 120, 215, 50)) # 蓝色半透明填充
                painter.drawRect(self.current_hover_rect)
    
    def capture_window_at_point(self, point):
        """点击截图"""
        self.hide()
        QApplication.processEvents()
        
        global_point = self.mapToGlobal(point)
        phy_x = int(global_point.x() * self.dpr)
        phy_y = int(global_point.y() * self.dpr)
        
        # 使用穿透逻辑获取真实窗口
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        self_hwnd = int(self.winId()) if self.winId() else 0
        
        # 再次确认不是点到了自己
        if hwnd == self_hwnd or hwnd == win32gui.GetDesktopWindow():
            def enum_cb_capture(wnd, result_list):
                if wnd != self_hwnd and win32gui.IsWindowVisible(wnd):
                    try:
                        rect = win32gui.GetWindowRect(wnd)
                        if rect[0] <= phy_x < rect[2] and rect[1] <= phy_y < rect[3]:
                            result_list.append(wnd)
                    except: pass
                return True
            found = []
            win32gui.EnumWindows(enum_cb_capture, found)
            if found:
                hwnd = found[0]

        if hwnd:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                # 物理 -> 逻辑
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