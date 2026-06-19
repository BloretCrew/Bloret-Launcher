import sys
import ctypes
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve, QTimer, Property as pyqtProperty, QUrl
from PySide6.QtGui import QGuiApplication, QScreen, QPixmap, QPainter, QColor, QCursor, QFont
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtUiTools import QUiLoader
if sys.platform == "win32":
    import win32gui
    import win32con
    import win32api
else:
    win32gui = None
    win32con = None
    win32api = None
from PySide6.QtWidgets import QLabel, QPushButton as StandardPushButton
from modules.paths import app_path, get_app_dir

# 尝试导入兼容控件（替代 QFluentWidgets）
try:
    from modules.compat_widgets import CardWidget, BodyLabel, StrongBodyLabel, CaptionLabel
    QFLUENTWIDGETS_AVAILABLE = True
except ImportError:
    QFLUENTWIDGETS_AVAILABLE = False


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
        
        title = QLabel("检测到多个显示器，请选择要截图的屏幕：", self)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        layout.addSpacing(10)

        for i, screen in enumerate(screens):
            geo = screen.geometry()
            # 获取缩放比例
            dpr = screen.devicePixelRatio()
            info_text = f"屏幕 {i + 1}: {geo.width()}x{geo.height()} (缩放: {int(dpr*100)}%)"
            
            # 使用普通按钮
            btn = StandardPushButton(info_text, self)
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
        if sys.platform == "win32":
            self.default_tip_text = "移动鼠标选择窗口，或拖拽框选区域"
        else:
            self.default_tip_text = "拖拽框选区域，单击可截取当前屏幕"

        self.tipQuickWidget = None
        self.CardWidget = None
        self.ScreenCut_Title = None
        
        # 设置窗口为全屏覆盖层
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # 初始化透明度
        self._opacity = 0.0
        self.setWindowOpacity(self._opacity)
        
        # 获取目标屏幕的 DPI
        self.dpr = self.target_screen.devicePixelRatio()
        
        # 只设置 geometry 为选定的屏幕
        screen_geo = self.target_screen.geometry()
        self.setGeometry(screen_geo)
        
        self.show()
        self.raise_()  # 置顶
        # 不调用 activateWindow()，因为 WindowDoesNotAcceptFocus 被移除了
        
        # 状态变量
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.current_hover_rect = None
        self.last_hover_hwnd = None
        self.last_hover_pos = None
        
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)
        
        # 使用代码直接构建 UI，避免 QFormBuilder 问题
        self._build_ui()
    
    def _build_ui(self):
        """直接用代码构建截图提示 UI"""
        if self._build_rinui_tip_widget():
            QTimer.singleShot(0, self._update_tip_geometry)
            return

        try:
            if QFLUENTWIDGETS_AVAILABLE:
                # 创建 CardWidget 容器
                self.CardWidget = CardWidget(self)
                
                # 创建图标标签
                icon_label = BodyLabel(self.CardWidget)
                icon_label.setMaximumSize(25, 25)
                try:
                    icon_pixmap = QPixmap(app_path("icon", "home.png"))
                    if not icon_pixmap.isNull():
                        icon_label.setPixmap(icon_pixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except:
                    pass
                
                # 创建标题标签
                title_label = StrongBodyLabel(self.CardWidget)
                title_label.setText("Bloret Launcher Screen Cut")
                
                # 创建提示标签
                self.ScreenCut_Title = CaptionLabel(self.CardWidget)
                self.ScreenCut_Title.setText(self.default_tip_text)
                self.ScreenCut_Title.setWordWrap(True)
                
                # 构建布局
                text_layout = QVBoxLayout()
                text_layout.addWidget(title_label)
                text_layout.addWidget(self.ScreenCut_Title)
                text_layout.setContentsMargins(0, 0, 0, 0)
                
                main_layout = QHBoxLayout(self.CardWidget)
                main_layout.addWidget(icon_label)
                main_layout.addLayout(text_layout)
                main_layout.setContentsMargins(10, 5, 10, 5)
                
                # 设置 CardWidget 的大小和位置
                self.CardWidget.setMinimumSize(400, 60)
                self.CardWidget.adjustSize()
                
            else:
                # 降级方案：使用标准 QLabel
                self.ScreenCut_Title = QLabel(self)
                self.ScreenCut_Title.setText(self.default_tip_text)
                self.ScreenCut_Title.setWordWrap(True)
                self.ScreenCut_Title.setStyleSheet("background-color: rgba(0,0,0,180); color: white; padding: 10px; border-radius: 5px;")
                
        except Exception as e:
            print(f"UI build error: {e}")
            import traceback
            traceback.print_exc()
            # 创建最小化的 ScreenCut_Title 作为后备
            self.ScreenCut_Title = QLabel(self)
            self.ScreenCut_Title.setText("截图")
            self.ScreenCut_Title.setStyleSheet("background-color: rgba(0,0,0,180); color: white;")
        
        # 初始化位置
        QTimer.singleShot(0, self._update_tip_geometry)

    def _build_rinui_tip_widget(self):
        """优先使用 RinUI QML 组件构建截图提示卡片（效果参考 CW2 Widget）"""
        try:
            project_root = get_app_dir()
            qml_file = project_root / "qml" / "components" / "ScreenCutTipWidget.qml"
            if not qml_file.exists():
                return False

            tip_widget = QQuickWidget(self)
            tip_widget.setResizeMode(QQuickWidget.ResizeMode.SizeViewToRootObject)
            tip_widget.setClearColor(Qt.GlobalColor.transparent)
            tip_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            tip_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)

            engine = tip_widget.engine()
            engine.addImportPath(str(project_root))
            engine.addImportPath(str(project_root / "RinUI"))

            tip_widget.setSource(QUrl.fromLocalFile(str(qml_file)))
            if tip_widget.status() == QQuickWidget.Status.Error:
                error_text = "; ".join(e.toString() for e in tip_widget.errors())
                print(f"Failed to load RinUI screenshot tip widget: {error_text}")
                tip_widget.deleteLater()
                return False

            root_obj = tip_widget.rootObject()
            if root_obj is None:
                tip_widget.deleteLater()
                return False

            root_obj.setProperty("tipText", self.default_tip_text)
            self.tipQuickWidget = tip_widget
            return True
        except Exception as e:
            print(f"Failed to build RinUI screenshot tip widget: {e}")
            return False

    def _set_tip_text(self, text):
        text = text or ""

        if self.tipQuickWidget:
            root_obj = self.tipQuickWidget.rootObject()
            if root_obj and root_obj.property("tipText") != text:
                root_obj.setProperty("tipText", text)
                self._update_tip_geometry()
            return

        if self.ScreenCut_Title and self.ScreenCut_Title.text() != text:
            self.ScreenCut_Title.setText(text)
            self._update_tip_geometry()

    def _update_tip_geometry(self):
        """强制更新提示框位置（居中显示在当前屏幕顶部）"""
        try:
            # 获取自身 geometry (即当前屏幕 geometry)
            widget_rect = self.rect()

            if self.tipQuickWidget:
                size_hint = self.tipQuickWidget.sizeHint()
                hint_width = size_hint.width() if size_hint.width() > 0 else 420
                hint_height = size_hint.height() if size_hint.height() > 0 else 66

                self.tipQuickWidget.resize(max(420, hint_width), max(60, hint_height))
                widget_width = self.tipQuickWidget.width()

                target_local_x = (widget_rect.width() - widget_width) // 2
                target_local_y = 25

                self.tipQuickWidget.move(target_local_x, target_local_y)
                self.tipQuickWidget.raise_()
                self.tipQuickWidget.show()
                return
            
            # 优先使用 CardWidget，如果不存在则使用 ScreenCut_Title
            if hasattr(self, 'CardWidget') and self.CardWidget:
                self.CardWidget.setMinimumSize(400, 60)
                self.CardWidget.adjustSize()
                widget_width = self.CardWidget.width()
                
                # 计算在当前窗口内的水平居中位置
                target_local_x = (widget_rect.width() - widget_width) // 2
                target_local_y = 25
                
                self.CardWidget.move(target_local_x, target_local_y)
                self.CardWidget.raise_()
                self.CardWidget.show()
            elif hasattr(self, 'ScreenCut_Title') and self.ScreenCut_Title:
                self.ScreenCut_Title.adjustSize()
                widget_width = self.ScreenCut_Title.width()
                
                # 计算在当前窗口内的水平居中位置
                target_local_x = (widget_rect.width() - widget_width) // 2
                target_local_y = 25
                
                self.ScreenCut_Title.move(target_local_x, target_local_y)
                self.ScreenCut_Title.raise_()
                self.ScreenCut_Title.show()
        except Exception as e:
            print(f"Error updating tip geometry: {e}")

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
                new_text = f"当前窗口：{window_title}" if window_title else "当前窗口"
                self._set_tip_text(new_text)
                
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
            self._set_tip_text(self.default_tip_text)
    
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
            self.hide()
            QApplication.processEvents()
            if self.target_screen:
                screenshot = self.target_screen.grabWindow(0)
                if screenshot and not screenshot.isNull():
                    QApplication.clipboard().setPixmap(screenshot)
                    print("截图已复制到剪贴板 (Screen)")
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
    
    # 不设置 QuitOnLastWindowClosed，以避免截图窗口关闭时关闭整个应用
    app.setQuitOnLastWindowClosed(False)
    
    screens = QGuiApplication.screens()
    target_screen = screens[0]
    
    # 逻辑修改：多屏检测
    if len(screens) > 1:
        # 弹出选择对话框
        dialog = MonitorSelectionDialog(screens)
        if dialog.exec() == QDialog.Accepted and dialog.selected_screen:
            target_screen = dialog.selected_screen
        else:
            print("用户取消了屏幕选择")
            return None

    print(f"将在屏幕 {target_screen.name()} 上启动截图")
    
    capture_widget = ScreenCaptureWidget(target_screen=target_screen)
    capture_widget.show()
    
    capture_widget.raise_()
    # 不直接调用 activateWindow()，以避免焦点问题
    
    for _ in range(5):
        QApplication.processEvents()
    
    capture_widget.fade_in()
    
    return capture_widget