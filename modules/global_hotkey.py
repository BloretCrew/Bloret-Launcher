import json
import threading
import os
import sys
import ctypes
import ctypes.wintypes
import modules.globals as BLglobals
from modules.config import read

# Windows API 常量
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_ALT = 0x0001
MOD_WIN = 0x0008

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 全局变量，用于保持对截图窗口的引用，防止被垃圾回收
_screenshot_widget_ref = None

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Qt相关导入 - 用于线程间通信
try:
    from PyQt5.QtCore import QObject, pyqtSignal, QTimer
    from PyQt5.QtWidgets import QApplication
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print("[Warning] PyQt5 not available for hotkey signal communication")

# 截图功能导入延迟到使用时
ScreenShortCut = None


def load_config():
    """从 config.json 加载配置，并将快捷键转为小写"""
    shortcut = read().get("screen_cut_shortcut")
    if not shortcut:
        print("警告: 配置文件中缺少 'screen_cut_shortcut' 字段，将使用默认快捷键 Ctrl+Alt+A")
        # 返回默认快捷键
        return "ctrl+alt+a"
    
    # 转为小写
    shortcut = str(shortcut).strip().lower()
    
    if not shortcut:
        print("警告: 'screen_cut_shortcut' 不能为空，将使用默认快捷键 Ctrl+Alt+A")
        # 返回默认快捷键
        return "ctrl+alt+a"
    
    print(f"已从配置文件加载截图快捷键: {shortcut}")
    return shortcut


def parse_shortcut(shortcut):
    """
    解析快捷键字符串，返回修饰键和虚拟键码
    """
    modifiers = 0
    vk = 0
    
    parts = shortcut.split('+')
    key = parts[-1]  # 最后一个是主键
    mods = parts[:-1]  # 前面的是修饰键
    
    # 解析修饰键
    for mod in mods:
        mod = mod.strip()
        if mod == 'ctrl' or mod == 'control':
            modifiers |= MOD_CONTROL
        elif mod == 'shift':
            modifiers |= MOD_SHIFT
        elif mod == 'alt':
            modifiers |= MOD_ALT
        elif mod == 'win' or mod == 'windows':
            modifiers |= MOD_WIN
    
    # 解析主键
    if len(key) == 1 and key.isalpha():
        # 字母键
        vk = ord(key.upper())
    elif key.isdigit() and len(key) == 1:
        # 数字键
        vk = ord(key)
    elif key.startswith('f') and key[1:].isdigit():
        # 功能键 F1-F12
        f_num = int(key[1:])
        if 1 <= f_num <= 12:
            vk = 0x6F + f_num  # F1=0x70, F2=0x71, ...
    elif key == 'a':
        vk = 0x41
    elif key == 'z':
        vk = 0x5A
    elif key == 'space':
        vk = 0x20
    elif key == 'enter':
        vk = 0x0D
    elif key == 'esc' or key == 'escape':
        vk = 0x1B
    elif key == 'tab':
        vk = 0x09
    elif key == 'backspace':
        vk = 0x08
    
    return modifiers, vk


def register_hotkey(hwnd, id, modifiers, vk):
    """注册全局热键"""
    return user32.RegisterHotKey(hwnd, id, modifiers, vk)


def unregister_hotkey(hwnd, id):
    """注销热键"""
    return user32.UnregisterHotKey(hwnd, id)


class HotkeySignalEmitter(QObject):
    """用于从子线程向主线程发送快捷键信号"""
    shortcut_triggered = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.main_thread_timer = None
        
    def emit_shortcut(self):
        """在子线程中调用，通过定时器在主线程中执行截图"""
        if QT_AVAILABLE and QApplication.instance():
            # 使用单次定时器确保在主线程中执行
            QTimer.singleShot(0, self._execute_screenshot)
        else:
            # 降级处理：直接执行（可能导致问题）
            self._execute_screenshot_directly()
    
    def _execute_screenshot(self):
        """在主线程中执行截图"""
        self._do_screenshot()
    
    def _execute_screenshot_directly(self):
        """直接执行截图（不推荐，可能导致问题）"""
        print("[Warning] 在非主线程中执行截图，可能导致界面无响应")
        self._do_screenshot()
    
    def _do_screenshot(self):
        """实际执行截图功能"""
        global ScreenShortCut, _screenshot_widget_ref
        
        # 延迟导入截图功能
        if ScreenShortCut is None:
            try:
                from modules.ShortCut import ScreenShortCut
            except Exception as e:
                print(f"[Error] 导入截图功能失败: {e}")
                return
        
        try:
            # 保持对截图窗口的引用，防止被垃圾回收
            widget = ScreenShortCut()
            # 将截图窗口引用存储在全局变量中，确保不会被垃圾回收
            _screenshot_widget_ref = widget
            print("[Hotkey] 截图功能已成功启动")
        except Exception as e:
            print(f"[Error] 执行截图功能时出错: {e}")
            import traceback
            traceback.print_exc()

# 创建全局信号发射器实例
_signal_emitter = None

def get_signal_emitter():
    """获取或创建信号发射器实例"""
    global _signal_emitter
    if _signal_emitter is None and QT_AVAILABLE:
        _signal_emitter = HotkeySignalEmitter()
    return _signal_emitter

def on_shortcut_pressed():
    """
    当快捷键被按下时的回调函数
    """
    print("[Hotkey] 截图快捷键被触发")
    
    # 尝试通过信号机制在主线程中执行
    emitter = get_signal_emitter()
    if emitter:
        emitter.emit_shortcut()
    else:
        # 降级处理：直接执行（可能导致问题）
        print("[Warning] 无法获取信号发射器，尝试直接执行截图")
        HotkeySignalEmitter()._execute_screenshot_directly()


def hotkey_listener_thread(shortcut_key):
    """
    在独立线程中运行 Windows 热键监听
    """
    print(f"[Hotkey] 全局快捷键已注册: {shortcut_key}")
    
    # 解析快捷键
    modifiers, vk = parse_shortcut(shortcut_key)
    hotkey_id = 1001  # 热键ID
    
    # 创建一个隐藏的窗口（用于接收消息）
    hwnd = user32.CreateWindowExW(
        0, "STATIC", "", 0, 0, 0, 0, 0,
        None, None, None, None
    )
    if not hwnd:
        print("❌ 创建隐藏窗口失败")
        return

    if not register_hotkey(hwnd, hotkey_id, modifiers, vk):
        print(f"❌ 热键 {shortcut_key} 注册失败")
        user32.DestroyWindow(hwnd)
        return

    print(f"✅ 全局热键已注册（ID={hotkey_id}）: {shortcut_key}")

    # 消息循环
    msg = ctypes.wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == hotkey_id:
                    on_shortcut_pressed()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception as e:
        print(f"[Error] 热键监听线程异常: {e}")
    finally:
        unregister_hotkey(hwnd, hotkey_id)
        user32.DestroyWindow(hwnd)
        print("\n✅ 热键已注销")


def init_global_hotkeys():
    try:
        # 1. 读取配置
        shortcut = load_config()
        
        # 2. 启动键盘监听线程
        listener_thread = threading.Thread(
            target=hotkey_listener_thread,
            args=(shortcut,),
            daemon=True  # 设为守护线程：主程序退出时自动结束
        )
        listener_thread.start()
        print(f"[Hotkey] 已启动键盘监听线程: {listener_thread.name}")

        print("✅ 截图服务已启动")
        
    except Exception as e:
        print(f"[Fatal] 启动失败: {e}")
        import traceback
        traceback.print_exc()