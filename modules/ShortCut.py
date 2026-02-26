import sys
import ctypes
import os
from PySide6.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve, QTimer, Property as pyqtProperty
from PySide6.QtGui import QGuiApplication, QScreen, QPixmap, QPainter, QColor, QCursor
# removed uic import for PySide6 compatibility
if sys.platform == "win32":
    import win32gui
    import win32con
    import win32api
else:
    win32gui = None
    win32con = None
    win32api = None
from qfluentwidgets import CardWidget, BodyLabel, StrongBodyLabel, CaptionLabel, SubtitleLabel, PushButton

class MonitorSelectionDialog(QDialog):
    """
    多显示器选择对话框
    """
    def __init__(self, screens, parent=None):
        super().__init__(parent)
        # --- 修改：设置窗口置顶标志 ---
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # ---------------------------
        
        self.setWindowTitle("选择截图屏幕")
        self.resize(400, 300)
        self.selected_screen = None
        
        # 简单的样式设置，适配暗色主题
        self.setStyleSheet("""
            QDialog { background-color: #2e2e2e; color: white; }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout(self)
        
        title = SubtitleLabel("检测到多个显示器，请选择要截图的屏幕：", self)
        layout.addWidget(title)
        layout.addSpacing(10)

        for i, screen in enumerate(screens):
            geo = screen.geometry()
            # 获取缩放比例
            dpr = screen.devicePixelRatio()
            info_text = f"屏幕 {i + 1}: {geo.width()}x{geo.height()} (缩放: {int(dpr*100)}%)"
            
            # 使用 Fluent 风格的按钮（如果可用），否则回退到普通按钮
            btn = PushButton(info_text, self)
            btn.setMinimumHeight(40)
            # 使用闭包绑定当前屏幕
            btn.clicked.connect(lambda checked, s=screen: self.on_screen_selected(s))
            layout.addWidget(btn)

        layout.addStretch()
        
        cancel_btn = QPushButton("取消", self)
        cancel_btn.setStyleSheet("background-color: #444; color: white; border: none; padding: 8px;")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def on_screen_selected(self, screen):
        self.selected_screen = screen
        self.accept()


class ScreenCaptureWidget(QWidget):
    def __init__(self, target_screen=None):
        super().__init__()
        
        # 如果没有指定屏幕，默认主屏
        if target_screen is None:
            target_screen = QGuiApplication.primaryScreen()
        
        self.target_screen = target_screen
        
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
        
        # 获取目标屏幕的 DPI
        self.dpr = self.target_screen.devicePixelRatio()
        
        # 只设置 geometry 为选定的屏幕
        screen_geo = self.target_screen.geometry()
        self.setGeometry(screen_geo)
        
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
            if hasattr(self, 'CardWidget'):
                self.CardWidget.setParent(None)  # 1. 移除父对象（自动脱离布局）
                self.CardWidget.setParent(self)  # 2. 重新挂载为本窗口子对象
                self.CardWidget.show()           # 3. 重新显示
            # --------------------------------------------
            
        else:
            print(f"UI文件不存在: {ui_file_path}")
        # 恢复大小（防止loadUi重置大小）
        self.resize(current_size)
        
        # 延时初始化提示框位置
        QTimer.singleShot(50, self._update_tip_geometry)

    def _update_tip_geometry(self):
        """强制更新提示框位置（居中显示在当前屏幕顶部）"""
        if not hasattr(self, 'CardWidget'):
            return

        # 获取自身 geometry (即当前屏幕 geometry)
        widget_rect = self.rect() # 这是一个局部坐标 (0, 0, w, h)
        
        self.CardWidget.setMinimumSize(400, 60)
        self.CardWidget.adjustSize()
        widget_width = self.CardWidget.width()
        
        # 计算在当前窗口内的水平居中位置
        target_local_x = (widget_rect.width() - widget_width) // 2
        target_local_y = 25
        
        self.CardWidget.move(target_local_x, target_local_y)
        self.CardWidget.raise_()
        self.CardWidget.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.is_selecting = True
            self.raise_()
        elif event.button() == Qt.RightButton:
            # 右键退出
            self.fade_out()
    
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
        """检测鼠标下的窗口"""
        if sys.platform != "win32":
            return
        
        # 1. 直接使用 Win32 API 获取物理坐标 (绝对准确)
        phy_x, phy_y = win32api.GetCursorPos()
        
        # 2. 获取鼠标下的窗口句柄
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        
        self_hwnd = int(self.winId()) if self.winId() else 0
        
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
                    except Exception:
                        pass
                return True
            
            found_windows = []
            win32gui.EnumWindows(enum_cb, found_windows)
            
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
                    if self.ScreenCut_Title.text() != new_text:
                        self.ScreenCut_Title.setText(new_text)
                        self._update_tip_geometry() 
                
                if self.last_hover_hwnd == hwnd:
                    return
                self.last_hover_hwnd = hwnd

                # 5. 计算绘制区域
                try:
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_tl = win32gui.ClientToScreen(hwnd, (0, 0))
                    draw_rect_phy = (client_tl[0], client_tl[1], 
                                     client_tl[0] + client_rect[2], client_tl[1] + client_rect[3])
                except Exception:
                    draw_rect_phy = rect

                # 核心逻辑：物理坐标 -> 截图窗口局部坐标
                # 将物理矩形转换为 Qt 逻辑矩形
                log_left = int(draw_rect_phy[0] / self.dpr)
                log_top = int(draw_rect_phy[1] / self.dpr)
                log_width = int((draw_rect_phy[2] - draw_rect_phy[0]) / self.dpr)
                log_height = int((draw_rect_phy[3] - draw_rect_phy[1]) / self.dpr)
                
                # 转换为相对于截图窗口的局部坐标
                # mapFromGlobal 需要全局逻辑坐标
                top_left = self.mapFromGlobal(QPoint(log_left, log_top))
                
                self.current_hover_rect = QRect(top_left.x(), top_left.y(), log_width, log_height)
                
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
        if event.button() != Qt.LeftButton:
            return

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
        if sys.platform != "win32":
            return
        self.hide()
        QApplication.processEvents()
        
        # 使用 Win32 API 再次确认目标
        phy_x, phy_y = win32api.GetCursorPos()
        
        # 查找窗口... (逻辑同 update_hover_window)
        hwnd = win32gui.WindowFromPoint((phy_x, phy_y))
        self_hwnd = int(self.winId()) if self.winId() else 0
        
        if hwnd == self_hwnd or hwnd == win32gui.GetDesktopWindow():
            def enum_cb_capture(wnd, result_list):
                if wnd != self_hwnd and win32gui.IsWindowVisible(wnd):
                    try:
                        rect = win32gui.GetWindowRect(wnd)
                        if rect[0] <= phy_x < rect[2] and rect[1] <= phy_y < rect[3]:
                            result_list.append(wnd)
                    except Exception:
                        pass
                return True
            found = []
            win32gui.EnumWindows(enum_cb_capture, found)
            if found:
                hwnd = found[0]

        if hwnd:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                # 物理坐标 -> 相对屏幕的逻辑坐标
                
                x = int(rect[0] / self.dpr)
                y = int(rect[1] / self.dpr)
                w = int((rect[2] - rect[0]) / self.dpr)
                h = int((rect[3] - rect[1]) / self.dpr)
                
                # grabWindow 的坐标是相对于 Virtual Desktop 的（如果是window=0）
                # 所以直接传全局逻辑坐标即可
                screenshot = self.target_screen.grabWindow(0, x, y, w, h)
                
                QApplication.clipboard().setPixmap(screenshot)
                print(f"截图已复制到剪贴板 (Window)")
            except Exception as e:
                print(f"Error capturing window: {e}")
    
    def capture_region(self, rect):
        """区域截图"""
        self.hide()
        QApplication.processEvents()
        
        # rect 是相对于 Widget 的局部坐标
        # 转换为全局逻辑坐标
        global_top_left = self.mapToGlobal(rect.topLeft())
        x, y, w, h = global_top_left.x(), global_top_left.y(), rect.width(), rect.height()

        if self.target_screen:
            # grabWindow(0) 表示截取根窗口，坐标为全局坐标
            screenshot = self.target_screen.grabWindow(0, x, y, w, h)
            QApplication.clipboard().setPixmap(screenshot)
            print(f"区域截图已复制到剪贴板 (Region)")


def ScreenShortCut():
    """
    运行后激活截图功能：
    1. 检测屏幕数量
    2. 如果 > 1，弹出对话框选择屏幕
    3. 在指定屏幕打开截图层
    """
    # 创建并显示截图工具
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    app.setQuitOnLastWindowClosed(True)
    
    screens = QGuiApplication.screens()
    target_screen = screens[0]
    
    # 逻辑修改：多屏检测
    if len(screens) > 1:
        # 弹出选择对话框
        dialog = MonitorSelectionDialog(screens)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_screen:
            target_screen = dialog.selected_screen
        else:
            print("用户取消了屏幕选择")
            return None

    print(f"将在屏幕 {target_screen.name()} 上启动截图")
    
    capture_widget = ScreenCaptureWidget(target_screen=target_screen)
    capture_widget.show()
    
    capture_widget.raise_()
    capture_widget.activateWindow()
    
    for _ in range(5):
        QApplication.processEvents()
    
    capture_widget.fade_in()
    
    return capture_widget