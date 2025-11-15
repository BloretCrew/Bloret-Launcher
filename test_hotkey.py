import ctypes
import ctypes.wintypes
import sys
import threading
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 常量定义
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_ALT = 0x0001
MOD_WIN = 0x0008

def register_hotkey(hwnd, id, modifiers, vk):
    """注册全局热键"""
    return user32.RegisterHotKey(hwnd, id, modifiers, vk)

def unregister_hotkey(hwnd, id):
    """注销热键"""
    user32.UnregisterHotKey(hwnd, id)

def hotkey_listener(callback, modifiers, vk, hotkey_id=100):
    """
    启动一个窗口消息循环来监听热键
    """
    def _message_loop():
        # 创建一个隐藏的窗口（用于接收消息）
        hwnd = user32.CreateWindowExW(
            0, "STATIC", "", 0, 0, 0, 0, 0,
            None, None, None, None
        )
        if not hwnd:
            print("❌ 创建隐藏窗口失败")
            return

        if not register_hotkey(hwnd, hotkey_id, modifiers, vk):
            print("❌ 热键已被其他程序占用，注册失败")
            user32.DestroyWindow(hwnd)
            return

        print(f"✅ 全局热键已注册（ID={hotkey_id}），按 Ctrl+Shift+Z 触发（按 Ctrl+C 退出）")

        msg = ctypes.wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    if msg.wParam == hotkey_id:
                        callback()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except KeyboardInterrupt:
            pass
        finally:
            unregister_hotkey(hwnd, hotkey_id)
            user32.DestroyWindow(hwnd)
            print("\n✅ 热键已注销")

    # 在子线程中运行消息循环（避免阻塞主线程，但这里我们让它阻塞）
    thread = threading.Thread(target=_message_loop, daemon=True)
    thread.start()
    try:
        # 主线程等待（可用 keyboard.wait() 或简单 time.sleep）
        while thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n正在退出...")

# ====== 使用示例 ======
def on_ctrl_shift_z():
    print("🔥 检测到全局热键: Ctrl + Shift + Z（已被拦截！）")
    # 此处执行你的逻辑（例如：截图、启动程序等）

if __name__ == "__main__":
    # 注册 Ctrl + Shift + 'Z'（'Z' 的虚拟键码是 90）
    # 参考：https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    hotkey_listener(
        callback=on_ctrl_shift_z,
        modifiers=MOD_CONTROL | MOD_SHIFT,
        vk=0x5A  # 'Z' 的十六进制虚拟键码（十进制 90）
    )