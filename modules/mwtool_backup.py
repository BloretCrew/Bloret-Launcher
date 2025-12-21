import sys
import os
import time
import threading
import win32gui
import win32con
import win32api
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon
from PyQt5.uic import loadUi
from qfluentwidgets import SimpleCardWidget, BodyLabel, StrongBodyLabel
import logging as log

class MinecraftWindowTool(QWidget):
    """Minecraft 窗口浮动工具栏"""
    
    def __init__(self, minecraft_hwnd, version):
        super().__init__()
        self.minecraft_hwnd = minecraft_hwnd
        self.version = version
        self.is_fullscreen = False
        
        log.debug(f"MinecraftWindowTool 构造函数被调用，句柄: {minecraft_hwnd}, 版本: {version}")
        
        # 窗口标志设置
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput  # 透明输入，不拦截鼠标事件
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活窗口
        
        log.debug(f"窗口标志设置完成: {self.windowFlags()}")
        
        self.init_ui()
        
        # 延迟创建定时器，确保在主线程中
        # 使用单次定时器来延迟启动位置更新定时器
        QTimer.singleShot(100, self.start_update_timer)
        
        # 如果窗口句柄无效，使用默认位置（屏幕中央）
        if not self.minecraft_hwnd:
            log.warning("没有有效的 Minecraft 窗口句柄，使用默认位置")
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            x = (screen_width - self.width()) // 2
            y = 50  # 屏幕顶部附近
            self.move(x, y)
        else:
            self.update_position()
            
        log.debug("正在显示工具栏...")
        self.show()
        log.debug(f"工具栏显示状态: {self.isVisible()}, 几何信息: {self.geometry()}")
        log.debug(f"工具栏屏幕位置: {self.pos()}, 屏幕数量: {len(QApplication.screens())}")
        
        # 确保工具栏在最上层
        self.raise_()
        log.debug("工具栏已提升到最上层")
        
    def init_ui(self):
        """初始化UI界面"""
        try:
            # 加载 UI 文件
            ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'mwtool.ui')
            if os.path.exists(ui_file_path):
                # 使用 loadUi 加载 UI 文件
                loadUi(ui_file_path, self)
                
                # 设置版本信息
                version_label = self.findChild(QLabel, 'MinecraftVersion')
                if version_label:
                    version_label.setText(f"Minecraft {self.version}")
                
                # 设置窗口大小
                self.resize(697, 61)
                
            else:
                log.error(f"UI 文件不存在: {ui_file_path}")
                # 如果 UI 文件不存在，创建简单的界面作为备选
                self.create_simple_ui()
                
        except Exception as e:
            log.error(f"加载 UI 文件失败: {e}")
            # 如果加载失败，创建简单的界面作为备选
            self.create_simple_ui()
    
    def create_simple_ui(self):
        """创建简单的UI界面"""
        # 创建主布局
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建图标标签
        icon_label = QLabel("🎮")
        icon_label.setStyleSheet("font-size: 20px;")
        
        # 创建标题标签
        title_label = QLabel("Bloret Launcher")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        
        # 创建版本标签
        version_label = QLabel(f"Minecraft {self.version}")
        version_label.setFont(QFont("Arial", 10))
        version_label.setStyleSheet("color: #cccccc;")
        
        # 添加到布局
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.resize(400, 40)
    
    def update_position(self):
        """更新工具栏位置"""
        log.debug(f"update_position 被调用，窗口句柄: {self.minecraft_hwnd}")
        
        if not self.minecraft_hwnd:
            log.warning("Minecraft 窗口句柄为 None，关闭工具栏")
            self.close()
            return
            
        # 检查窗口句柄有效性（更宽容的检查）
        try:
            is_valid = win32gui.IsWindow(self.minecraft_hwnd)
            log.debug(f"窗口句柄有效性检查: {self.minecraft_hwnd} -> {is_valid}")
            
            if not is_valid:
                log.warning("Minecraft 窗口句柄无效，但继续运行工具栏（用于测试）")
                # 不关闭工具栏，而是使用默认位置
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
    
    def start_update_timer(self):
        """启动位置更新定时器"""
        try:
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.update_position)
            self.update_timer.start(100)  # 每100毫秒更新一次位置
            log.debug("工具栏位置更新定时器已启动")
        except Exception as e:
            log.error(f"启动定时器失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        event.accept()


class MinecraftWindowToolManager(QObject):
    """Minecraft 窗口工具栏管理器"""
    
    tool_created = pyqtSignal(object)  # 工具栏创建信号
    tool_closed = pyqtSignal()  # 工具栏关闭信号
    
    def __init__(self):
        super().__init__()
        self.current_tool = None
        self.minecraft_hwnd = None
        self.version = None
        
    def show_tool(self, minecraft_hwnd, version):
        """显示工具栏"""
        try:
            log.info(f"开始创建 Minecraft 工具栏，版本: {version}, 句柄: {minecraft_hwnd}")
            
            # 如果已有工具栏，先关闭
            self.hide_tool()
            
            self.minecraft_hwnd = minecraft_hwnd
            self.version = version
            
            # 创建新的工具栏
            log.debug(f"正在创建 MinecraftWindowTool 实例，传入句柄: {minecraft_hwnd}...")
            self.current_tool = MinecraftWindowTool(minecraft_hwnd, version)
            log.debug(f"工具栏实例创建成功: {self.current_tool}")
            log.debug(f"工具栏可见性: {self.current_tool.isVisible()}")
            log.debug(f"工具栏几何信息: {self.current_tool.geometry()}")
            
            self.tool_created.emit(self.current_tool)
            
            log.info(f"Minecraft 工具栏已显示，版本: {version}, 句柄: {minecraft_hwnd}")
            
        except Exception as e:
            log.error(f"显示工具栏失败: {e}")
            import traceback
            traceback.print_exc()
    
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


# 全局管理器实例
tool_manager = MinecraftWindowToolManager()


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
        # 确保 QApplication 存在
        app = QApplication.instance()
        if not app:
            log.debug("QApplication 不存在，创建新实例")
            app = QApplication(sys.argv)
        else:
            log.debug("使用现有的 QApplication 实例")
        
        # 使用管理器显示工具栏（确保在主线程中调用）
        log.debug("调用 tool_manager.show_tool...")
        tool_manager.show_tool(minecraft_hwnd, version)
        
        result = tool_manager.current_tool
        log.debug(f"tool_manager.current_tool 返回: {result}")
        return result
        
    except Exception as e:
        log.error(f"创建 Minecraft 工具栏失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def hide_minecraft_tool():
    """隐藏 Minecraft 工具栏"""
    try:
        tool_manager.hide_tool()
    except Exception as e:
        log.error(f"隐藏 Minecraft 工具栏失败: {e}")


def is_tool_visible():
    """检查工具栏是否可见"""
    return tool_manager.is_tool_visible()


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)
    
    # 模拟 Minecraft 窗口句柄（实际使用时应该是真实的句柄）
    test_hwnd = 12345
    test_version = "1.21.9"
    
    tool = create_minecraft_tool(test_hwnd, test_version)
    
    sys.exit(app.exec_())