from modules.win11toast import toast
import ctypes.wintypes,ctypes,logging,os,subprocess

from modules.log import log, importlog
from modules.safe import handle_exception

def get_system_theme_color():
    """获取系统主题颜色"""
    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AccentColor"

        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print("无法打开注册表键")
            return "#0078D7"  # 默认蓝色

        # 读取键值
        value = ctypes.c_uint()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print("无法读取注册表键值")
            ctypes.windll.advapi32.RegCloseKey(hkey)
            return "#0078D7"  # 默认蓝色

        # 关闭注册表键
        ctypes.windll.advapi32.RegCloseKey(hkey)

        # 转换为 RGB 颜色代码
        accent_color = value.value
        red = (accent_color & 0xFF0000) >> 16
        green = (accent_color & 0x00FF00) >> 8
        blue = (accent_color & 0x0000FF)
        return f"#{red:02X}{green:02X}{blue:02X}"
    except Exception as e:
        handle_exception(e)
        print(f"获取系统主题颜色时发生错误: {e}")
        return "#0078D7"  # 默认蓝色

def is_dark_theme():
    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AppsUseLightTheme"
        
        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print("无法打开注册表键")
            return False
        
        # 读取键值
        value = ctypes.c_int()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print("无法读取注册表键值")
            ctypes.windll.advapi32.RegCloseKey(hkey)
            return False
        
        # 关闭注册表键
        ctypes.windll.advapi32.RegCloseKey(hkey)
        
        # 返回主题状态
        return value.value == 0  # 0 表示深色主题，1 表示浅色主题
    except Exception as e:
        handle_exception(e)
        print(f"检测主题时发生错误: {e}")
        return False

def send_system_notification(title, message):
    try:
        toast(title, message, duration="short", icon={'src': 'bloret.ico','placement': 'appLogoOverride'})  # 使用 win11toast 的 toast 方法
    except Exception as e:
        handle_exception(e)
        log(f"发送系统通知失败: {e}", logging.ERROR)
def check_write_permission():
    # 检查当前目录的写入权限
    try:
        test_file = os.path.join(os.getcwd(), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("当前目录具有写入权限")
        return True
    except PermissionError:
        print("当前目录没有写入权限")
        return False

def restart():
    log('重启程序')
    # if share.isAttached():
    #     share.detach()  # 释放共享内存
    # os.execl(sys.executable, sys.executable, *sys.argv)
    subprocess.Popen(["restart.cmd"])


importlog("SYSTEMS.PY")