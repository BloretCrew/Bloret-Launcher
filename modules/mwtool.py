import sys
import os
import time
import threading
import win32gui
import win32con
import win32api
import win32process
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QEventLoop
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon
from PyQt5.uic import loadUi
from qfluentwidgets import SimpleCardWidget, BodyLabel, StrongBodyLabel
import logging as log
from .log import log as app_log

# 确保日志输出立即刷新
class ImmediateFlushHandler(log.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if hasattr(self.stream, 'flush'):
            self.stream.flush()

# 配置日志处理器
for handler in log.root.handlers:
    if isinstance(handler, log.StreamHandler):
        handler.flush = lambda: sys.stderr.flush() if hasattr(sys.stderr, 'flush') else None


class MinecraftWindowWatcher(QThread):
    """监视线程：等待 Minecraft 窗口出现"""
    window_found = pyqtSignal(int, str)
    
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.is_running = True
    
    def run(self):
        log.info(f"开始寻找 Minecraft {self.version} 窗口...")
        # 最多寻找 300 秒 (5分钟)
        for _ in range(300):
            if not self.is_running:
                break
            
            # 使用加强版的查找逻辑
            hwnd = self._find_window()
            if hwnd:
                log.info(f"找到窗口句柄: {hwnd}")
                # 再次确认窗口有效性
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    time.sleep(1) # 等待窗口完全初始化
                    self.window_found.emit(hwnd, self.version)
                    return
            time.sleep(1)
            
    def _find_window(self):
        found_hwnd = []
        target_version = self.version

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # 排除启动器自己
                if "Bloret Launcher" in title:
                    return

                # 匹配逻辑：标题包含 "Minecraft" 且类名符合游戏特征
                # 1. 标题匹配
                if "Minecraft" in title or (target_version and target_version in title):
                    # 2. 类名匹配 (LWJGL, GLFW, SDL等是游戏常用窗口库)
                    if (class_name.startswith("LWJGL") or 
                        "GLFW" in class_name or 
                        "SunAwtFrame" in class_name or
                        "SDL_app" in class_name):
                        
                        found_hwnd.append(hwnd)
            except Exception:
                pass

        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass
            
        return found_hwnd[0] if found_hwnd else None

    def stop(self):
        self.is_running = False

# 全局监视器变量
_watcher_thread = None

def start_monitoring(version):
    """启动监视"""
    global _watcher_thread
    if _watcher_thread and _watcher_thread.isRunning():
        _watcher_thread.stop()
    
    _watcher_thread = MinecraftWindowWatcher(version)
    # 连接信号：找到窗口后直接调用创建工具栏函数
    _watcher_thread.window_found.connect(create_minecraft_tool)
    _watcher_thread.start()

def stop_monitoring():
    """停止监视"""
    global _watcher_thread
    if _watcher_thread:
        _watcher_thread.stop()

class MinecraftWindowToolManager(QObject):
    """Minecraft 窗口工具栏管理器 - 完全在主线程中运行"""
    
    tool_created = pyqtSignal(object)  # 工具栏创建信号
    tool_closed = pyqtSignal()  # 工具栏关闭信号
    create_request = pyqtSignal(int, str)  # 请求在主线程创建工具栏（发射者可在任意线程）
    
    def __init__(self):
        super().__init__()
        self.current_tool = None
        self.minecraft_hwnd = None
        self.version = None
        # 将创建请求连接到处理器，确保在 manager 所在线程处理（通常为主线程）
        self.create_request.connect(self._on_create_request)
        
    def show_tool(self, minecraft_hwnd, version):
        """显示工具栏"""
        log.debug(f"show_tool 被调用，句柄: {minecraft_hwnd}, 版本: {version}")
        sys.stderr.flush()
        
        # 确保 QApplication 存在
        app = QApplication.instance()
        log.debug(f"QApplication.instance(): {app}")
        sys.stderr.flush()
        if not app:
            log.debug("QApplication 不存在，创建新实例")
            app = QApplication(sys.argv)
            log.debug(f"新 QApplication 创建: {app}")
            sys.stderr.flush()
        
        # 如果当前已有工具栏实例，先关闭它
        if self.current_tool:
            log.debug("关闭现有工具栏")
            self.current_tool.close()
            self.current_tool = None
        
        # 检查是否在主线程中
        try:
            current_thread = QThread.currentThread()
            app_thread = app.thread()
            log.debug(f"当前线程: {current_thread}, QApplication 线程: {app_thread}")
            sys.stderr.flush()
            
            if app_thread == current_thread:
                log.debug("在主线程中，直接创建工具栏")
                sys.stderr.flush()
                return self._create_tool_impl(minecraft_hwnd, version)
            else:
                # 在非主线程中，请求 manager 在主线程创建工具栏，并同步等待结果（超时 5 秒）
                log.debug("在非主线程中，通过 create_request 请求主线程创建工具栏并等待结果")
                sys.stderr.flush()

                done = threading.Event()
                result = {'tool': None}

                def _on_created(tool):
                    try:
                        log.debug(f"wait on_created 回调得到 tool: {tool}")
                        result['tool'] = tool
                        done.set()
                    except Exception as _e:
                        log.error(f"on_created 回调出错: {_e}")

                try:
                    self.tool_created.connect(_on_created)
                except Exception as e:
                    log.error(f"连接临时回调失败: {e}")

                # 发送创建请求（由 manager 在主线程处理）
                try:
                    self.create_request.emit(minecraft_hwnd, version)
                    log.info("create_request 信号已发出")
                except Exception as e:
                    log.error(f"发出 create_request 信号失败: {e}")

                # 等待结果（超时 5 秒）
                waited = done.wait(5)
                if not waited:
                    log.error("等待创建工具栏超时（5 秒）")
                else:
                    log.info("创建工具栏已完成，返回结果")

                try:
                    self.tool_created.disconnect(_on_created)
                except Exception:
                    pass

                return result['tool']
                
        except Exception as e:
            log.error(f"跨线程创建工具栏失败: {e}")
            import traceback
            traceback.print_exc()
            sys.stderr.flush()
            self.current_tool = None
            return None

    def _create_tool_impl_and_emit(self, minecraft_hwnd, version):
        """在主线程中调用的包装器：创建工具并通过 signal 发出"""
        log.debug(f"_create_tool_impl_and_emit 被调用，句柄: {minecraft_hwnd}, 版本: {version}")
        try:
            tool = self._create_tool_impl(minecraft_hwnd, version)
            log.debug(f"_create_tool_impl 返回: {tool}")
            self.tool_created.emit(tool)
            log.debug(f"发出 tool_created 信号")
        except Exception as e:
            log.error(f"_create_tool_impl_and_emit 出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.tool_created.emit(None)
            except Exception:
                pass

    def _on_create_request(self, hwnd, version):
        """槽：在 manager 所在线程（主线程）中创建工具栏并发出创建信号"""
        log.info(f"_on_create_request 在主线程执行，句柄: {hwnd}, 版本: {version}")
        try:
            try:
                app_log(f"_on_create_request 在主线程执行，句柄: {hwnd}, 版本: {version}")
            except Exception:
                pass
            tool = self._create_tool_impl(hwnd, version)
            self.tool_created.emit(tool)
            log.info(f"_on_create_request 完成，tool: {tool}")
            try:
                app_log(f"_on_create_request 完成，tool: {tool}")
            except Exception:
                pass
        except Exception as e:
            log.error(f"_on_create_request 出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.tool_created.emit(None)
            except Exception:
                pass

    def _create_tool_impl(self, minecraft_hwnd, version):
        """实际在主线程中创建工具的实现函数"""
        log.info(f"_create_tool_impl 开始，句柄: {minecraft_hwnd}, 版本: {version}")
        try:
            try:
                app_log(f"_create_tool_impl 开始，句柄: {minecraft_hwnd}, 版本: {version}")
            except Exception:
                pass
            log.debug("创建 MinecraftWindowTool 实例")
            self.current_tool = MinecraftWindowTool()
            log.debug(f"MinecraftWindowTool 实例已创建: {self.current_tool}")
            try:
                app_log(f"MinecraftWindowTool 实例已创建: {self.current_tool}")
            except Exception:
                pass
            
            log.debug(f"调用 setup_tool，句柄: {minecraft_hwnd}, 版本: {version}")
            self.current_tool.setup_tool(minecraft_hwnd, version)
            log.debug("setup_tool 完成")
            
            log.debug("调用 show()")
            self.current_tool.show()
            try:
                # 立即记录可见性和基本属性
                vis = self.current_tool.isVisible()
                winid = int(self.current_tool.winId()) if hasattr(self.current_tool, 'winId') else None
                wh = self.current_tool.windowHandle()
                geo = self.current_tool.geometry()
                log.info(f"show() 完成，isVisible: {vis}, winId: {winid}, windowHandle: {wh}, geometry: ({geo.x()},{geo.y()},{geo.width()}x{geo.height()})")
                sys.stderr.flush()
            except Exception as _e:
                log.debug(f"记录 show() 状态时出错: {_e}")
                sys.stderr.flush()

            # 安排稍后再次检查（在事件循环中）以捕获单次定时器或 ensure_visible 的效果
            try:
                tool_ref = self.current_tool
                def _post_show_check():
                    try:
                        vis2 = tool_ref.isVisible()
                        winid2 = int(tool_ref.winId()) if hasattr(tool_ref, 'winId') else None
                        wh2 = tool_ref.windowHandle()
                        geo2 = tool_ref.geometry()
                        timer_active = hasattr(tool_ref, 'update_timer') and tool_ref.update_timer is not None and tool_ref.update_timer.isActive()
                        log.info(f"post_show 检查: isVisible={vis2}, winId={winid2}, windowHandle={wh2}, geometry=({geo2.x()},{geo2.y()},{geo2.width()}x{geo2.height()}), update_timer_active={timer_active}")
                        sys.stderr.flush()
                    except Exception as _e:
                        log.error(f"post_show_check 出错: {_e}")
                QTimer.singleShot(150, _post_show_check)
            except Exception as _e:
                log.error(f"安排 post_show_check 出错: {_e}")

            log.debug(f"工具栏已创建并显示，句柄: {minecraft_hwnd}")
            return self.current_tool
        except Exception as e:
            log.error(f"创建工具栏失败: {e}")
            import traceback
            traceback.print_exc()
            self.current_tool = None
            return None
    
    def hide_tool(self):
        """隐藏工具栏"""
        if self.current_tool:
            try:
                self.current_tool.close()
                self.current_tool = None
                self.tool_closed.emit()
                log.info("Minecraft 工具栏已隐藏")
            except Exception as e:
                log.error(f"隐藏工具栏失败: {e}")
    
    def is_tool_visible(self):
        """检查工具栏是否可见"""
        return self.current_tool is not None and self.current_tool.isVisible()


class MinecraftWindowTool(QWidget):
    """Minecraft 窗口工具栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.minecraft_hwnd = None
        self.version = ""
        self.is_fullscreen = False
        self.update_timer = None
        
        # 设置窗口标志 - 修改部分：移除Qt.WindowTransparentForInput，添加Qt.WindowDoesNotAcceptFocus
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框窗口
            Qt.WindowStaysOnTopHint |  # 始终保持在最顶层
            Qt.Tool |  # 工具窗口
            Qt.WindowDoesNotAcceptFocus  # 不接受焦点，但允许交互
        )
        
        # 设置窗口属性
        self.setAttribute(Qt.WA_TranslucentBackground)  # 半透明背景
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示但不激活
        
        # 初始化UI
        self.init_ui()
        
        # 添加延迟创建定时器，确保窗口创建完成后再显示
        QTimer.singleShot(500, self.ensure_visible)

        # 连接快捷键信号到槽
        from modules.ShortCut import ScreenShortCut
        screen_cut_button = self.findChild(QPushButton, "ScreenCutButton")
        if screen_cut_button:
            screen_cut_button.clicked.connect(lambda: ScreenShortCut())

        
    def init_ui(self):
        """初始化UI"""
        # 创建水平布局
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # 创建图标标签
        self.icon_label = QLabel("🎮")
        self.icon_label.setStyleSheet("font-size: 20px;")

        # 创建标题标签
        self.title_label = QLabel("Bloret Launcher")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")

        # 创建版本标签（保存为实例变量，便于后续更新）
        self.version_label = QLabel(f"Minecraft {self.version}")
        self.version_label.setFont(QFont("Arial", 10))
        self.version_label.setStyleSheet("color: #cccccc;")
        
        # 添加到布局
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.resize(400, 40)
    
    def ensure_visible(self):
        """确保窗口可见"""
        try:
            log.debug(f"ensure_visible 被调用，isVisible: {self.isVisible()}")
            if not self.isVisible():
                log.debug("窗口不可见，尝试显示")
                self.show()
                log.debug("窗口已显示")
            
            # 如果没有有效的窗口句柄，使用默认位置
            if not self.minecraft_hwnd:
                log.debug("minecraft_hwnd 为 None，使用默认位置")
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                x = (screen_width - self.width()) // 2
                y = 50  # 距离顶部50像素
                self.move(x, y)
                log.debug(f"使用默认位置: ({x}, {y})")
            
            # 启动位置更新定时器
            log.debug("启动位置更新定时器")
            self.start_update_timer()
            
            # 确保工具栏在最上层
            self.raise_()
            log.debug("工具栏已提升到最上层")
        except Exception as e:
            log.error(f"确保窗口可见时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_tool(self, minecraft_hwnd, version):
        """设置工具栏参数"""
        self.minecraft_hwnd = minecraft_hwnd
        self.version = version
        # 更新版本标签（使用实例变量，避免 findChild 的歧义）
        try:
            if hasattr(self, 'version_label'):
                self.version_label.setText(f"Minecraft {self.version}")
        except Exception:
            pass

        log.debug(f"工具栏参数已设置，句柄: {minecraft_hwnd}, 版本: {version}")
    
    def start_update_timer(self):
        """启动位置更新定时器"""
        try:
            log.debug("start_update_timer 被调用")
            self.update_timer = QTimer(self)
            log.debug(f"QTimer 已创建: {self.update_timer}")
            self.update_timer.timeout.connect(self.update_position)
            log.debug("连接 timeout 信号到 update_position")
            self.update_timer.start(100)  # 每100毫秒更新一次位置
            log.debug("定时器已启动（100ms 间隔）")
        except Exception as e:
            log.error(f"启动定时器失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_position(self):
        """更新工具栏位置"""
        log.debug(f"update_position 被调用，窗口句柄: {self.minecraft_hwnd}")
        
        if not self.minecraft_hwnd:
            log.debug("Minecraft 窗口句柄为 None，使用默认位置")
            # 使用默认位置
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            x = (screen_width - self.width()) // 2
            y = 50  # 距离顶部50像素
            self.move(x, y)
            if not self.isVisible():
                self.show()
            return
            
        # 检查窗口句柄有效性（更宽容的检查）
        try:
            is_valid = win32gui.IsWindow(self.minecraft_hwnd)
            log.debug(f"窗口句柄有效性检查: {self.minecraft_hwnd} -> {is_valid}")
            
            if not is_valid:
                log.debug("Minecraft 窗口句柄无效，使用默认位置")
                # 使用默认位置
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                x = (screen_width - self.width()) // 2
                y = 50  # 距离顶部50像素
                self.move(x, y)
                if not self.isVisible():
                    self.show()
                return
        except Exception as e:
            log.warning(f"检查窗口句柄时出错: {e}，继续运行工具栏")
            return
        
        try:
            # 验证窗口句柄是否仍然有效（使用 try-except 包装）
            try:
                if not win32gui.IsWindowVisible(self.minecraft_hwnd):
                    log.debug("Minecraft 窗口不可见，隐藏工具栏")
                    self.hide()  # 隐藏而不是关闭，等待窗口重新显示
                    return
                    
                # 检查窗口是否最小化
                if win32gui.IsIconic(self.minecraft_hwnd):
                    log.debug("Minecraft 窗口已最小化，隐藏工具栏")
                    self.hide()
                    return
                else:
                    # 如果之前是最小化状态，现在恢复显示
                    if not self.isVisible():
                        self.show()
                    
                # 获取 Minecraft 窗口信息
                rect = win32gui.GetWindowRect(self.minecraft_hwnd)
                if not rect or len(rect) != 4:
                    log.debug("无法获取 Minecraft 窗口矩形，使用默认位置")
                    # 使用默认位置
                    self.show()
                    return
                    
                window_left, window_top, window_right, window_bottom = rect
                
                # 验证窗口尺寸是否合理（避免无效数据）
                if window_right <= window_left or window_bottom <= window_top:
                    log.debug("Minecraft 窗口尺寸无效，使用默认位置")
                    self.show()
                    return
                    
            except Exception as e:
                log.warning(f"获取窗口信息失败: {e}，使用默认位置")
                # 如果无法获取窗口信息，使用默认位置
                self.show()
                return
                
            window_left, window_top, window_right, window_bottom = rect
            
            # 获取窗口客户区信息（排除标题栏）
            client_rect = win32gui.GetClientRect(self.minecraft_hwnd)
            client_left, client_top, client_right, client_bottom = client_rect
            
            # 计算标题栏高度
            title_height = window_bottom - window_top - (client_bottom - client_top)
            
            # 获取屏幕尺寸
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            # 检查是否全屏
            window_width = window_right - window_left
            window_height = window_bottom - window_top
            
            # 判断是否全屏（窗口大小接近屏幕大小，且位置接近屏幕边缘）
            is_fullscreen = (
                window_width >= screen_width * 0.95 and
                window_height >= screen_height * 0.95 and
                window_left <= 10 and
                window_top <= 10
            )
            
            if is_fullscreen != self.is_fullscreen:
                self.is_fullscreen = is_fullscreen
                log.debug(f"Minecraft 窗口全屏状态改变: {'全屏' if is_fullscreen else '窗口模式'}")
            
            if self.is_fullscreen:
                # 全屏模式：显示在屏幕顶部中央
                tool_width = self.width()
                x = (screen_width - tool_width) // 2
                y = 10  # 距离屏幕顶部10像素
            else:
                # 窗口模式：显示在 Minecraft 窗口标题栏上方
                tool_width = self.width()
                tool_height = self.height()
                
                # 计算位置：在窗口标题栏上方，水平居中
                x = window_left + (window_width - tool_width) // 2
                y = window_top - tool_height - 5  # 在窗口上方5像素处
                
                # 确保不会超出屏幕边界
                if y < 0:
                    y = window_top + title_height + 5  # 如果上方空间不足，显示在标题栏下方
                
                if x < 0:
                    x = 10  # 确保左边不超出屏幕
                elif x + tool_width > screen_width:
                    x = screen_width - tool_width - 10  # 确保右边不超出屏幕
            
            # 移动窗口
            try:
                log.debug(f"正在移动工具栏到位置: ({x}, {y}), 尺寸: {self.width()}x{self.height()}")
                
                # 确保位置在屏幕范围内
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                
                if x < 0:
                    x = 10
                if y < 0:
                    y = 10
                if x + self.width() > screen_width:
                    x = screen_width - self.width() - 10
                if y + self.height() > screen_height:
                    y = screen_height - self.height() - 10
                    
                self.move(x, y)
                
                # 确保窗口在最顶层（仅在窗口可见时）
                if self.isVisible():
                    self.raise_()
                    # 注意：不要调用 activateWindow()，这可能导致焦点问题
                    
                log.debug(f"工具栏移动完成，新位置: {self.pos()}, 可见性: {self.isVisible()}")
                    
            except Exception as e:
                log.debug(f"移动窗口失败: {e}")
                # 如果移动失败，尝试重新显示窗口
                if not self.isVisible():
                    self.show()
            
        except Exception as e:
            log.error(f"更新工具栏位置失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        event.accept()


# 全局管理器实例（延迟创建，确保在 Qt 主线程中实例化）
tool_manager = None
_tool_manager_lock = threading.Lock()
_tool_manager_ready = threading.Event()

def _ensure_tool_manager():
    """确保 tool_manager 在 Qt 主线程中已创建。返回 True 表示准备就绪。"""
    global tool_manager
    app = QApplication.instance()
    if not app:
        log.debug("QApplication 不存在，创建新实例")
        app = QApplication(sys.argv)
    
    main_thread = app.thread()
    current_thread = QThread.currentThread()

    # 1. 如果当前已经在主线程，直接创建，不要使用 Timer 和 Wait (否则会死锁)
    if current_thread == main_thread:
        if not tool_manager:
            try:
                tool_manager = MinecraftWindowToolManager()
                log.info("已在主线程(直接)创建 tool_manager")
            except Exception as e:
                log.error(f"在主线程直接创建 tool_manager 失败: {e}")
                return False
        return True

    # 2. 如果在后台线程，检查是否已存在
    if tool_manager and tool_manager.thread() == main_thread:
        return True

    # 3. 如果在后台线程且不存在，调度到主线程创建并等待
    with _tool_manager_lock:
        if tool_manager and tool_manager.thread() == main_thread:
            return True

        _tool_manager_ready.clear()

        def _create_manager():
            global tool_manager
            try:
                tool_manager = MinecraftWindowToolManager()
                log.info("已在主线程(Timer)创建 tool_manager")
            except Exception as e:
                log.error(f"在主线程创建 tool_manager 失败: {e}")
            finally:
                # 无论成功失败，都解除等待
                try:
                    _tool_manager_ready.set()
                except Exception:
                    pass
        
        # 在主线程调度创建
        try:
            QTimer.singleShot(0, _create_manager)
        except Exception as e:
            log.error(f"调度创建 tool_manager 失败: {e}")
            return False

        # 等待创建完成（最长等待 5 秒）
        if not _tool_manager_ready.wait(5):
            log.error("等待 tool_manager 创建超时")
            return False

        return tool_manager is not None and tool_manager.thread() == main_thread

def create_minecraft_tool(minecraft_hwnd, version):
    """
    创建 Minecraft 窗口工具栏
    
    Args:
        minecraft_hwnd: Minecraft 窗口句柄
        version: Minecraft 版本号
    
    Returns:
        MinecraftWindowTool 实例
    """
    log.debug(f"create_minecraft_tool 被调用，句柄: {minecraft_hwnd}, 版本: {version}")
    try:
        app_log(f"create_minecraft_tool 被调用，句柄: {minecraft_hwnd}, 版本: {version}")
    except Exception:
        pass
    try:
        # 确保 QApplication 存在
        app = QApplication.instance()
        if not app:
            log.debug("QApplication 不存在，创建新实例")
            app = QApplication(sys.argv)
        else:
            log.debug("使用现有的 QApplication 实例")
        
        # 确保 manager 在主线程中存在，然后使用其显示工具栏
        log.info("确保 tool_manager 在主线程中准备就绪...")
        try:
            app_log("确保 tool_manager 在主线程中准备就绪...")
        except Exception:
            pass
        if not _ensure_tool_manager():
            log.error("无法确保 tool_manager 在主线程中准备就绪")
            try:
                app_log("无法确保 tool_manager 在主线程中准备就绪")
            except Exception:
                pass
            return None

        log.debug("调用 tool_manager.show_tool...")
        tool_manager.show_tool(minecraft_hwnd, version)

        result = tool_manager.current_tool
        log.debug(f"tool_manager.current_tool 返回: {result}")
        
        # 确保工具栏显示
        if result and not result.isVisible():
            result.show()
            log.debug("工具栏已显示")
        
        return result
        
    except Exception as e:
        log.error(f"创建 Minecraft 工具栏失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def hide_minecraft_tool():
    """隐藏 Minecraft 工具栏"""
    try:
        if tool_manager:
            tool_manager.hide_tool()
    except Exception as e:
        log.error(f"隐藏 Minecraft 工具栏失败: {e}")


def is_tool_visible():
    """检查工具栏是否可见"""
    if tool_manager:
        return tool_manager.is_tool_visible()
    return False



if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)
    
    # 模拟 Minecraft 窗口句柄（实际使用时应该是真实的句柄）
    test_hwnd = 12345
    test_version = "1.21.9"
    
    tool = create_minecraft_tool(test_hwnd, test_version)
    
    sys.exit(app.exec_())