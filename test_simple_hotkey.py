import ctypes
import time
import threading

def test_hotkey():
    """简单的热键测试"""
    print("开始简单热键测试...")
    
    # 定义常量
    WM_HOTKEY = 0x0312
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    
    # 注册热键 Alt+F1
    hotkey_id = 1
    result = ctypes.windll.user32.RegisterHotKey(None, hotkey_id, MOD_ALT, 0x70)  # F1 = 0x70
    
    if result:
        print(f"热键注册成功: Alt+F1 (ID: {hotkey_id})")
    else:
        error = ctypes.windll.kernel32.GetLastError()
        print(f"热键注册失败，错误码: {error}")
        return
    
    # 消息循环
    msg = ctypes.wintypes.MSG()
    print("等待热键触发 (10秒)...")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        # 使用PeekMessageW非阻塞检查
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0x0001):  # PM_REMOVE
            print(f"收到消息: {msg.message} (wParam: {msg.wParam})")
            if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                print("✓ 热键 Alt+F1 被触发！")
                break
        time.sleep(0.01)
    
    # 注销热键
    ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
    print("热键已注销")

if __name__ == "__main__":
    test_hotkey()