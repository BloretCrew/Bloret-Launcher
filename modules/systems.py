from modules.win11toast import toast
import logging, os, subprocess, tempfile
import sys

if sys.platform == "win32":
    import ctypes.wintypes, ctypes
    from win32com.client import Dispatch

from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText

def get_system_theme_color():
    """获取系统主题颜色"""
    if sys.platform != "win32":
        return "#0078D7"  # 非 Windows 平台默认返回蓝色

    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AccentColor"

        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print(i18nText("无法打开注册表键"))
            return "#0078D7"  # 默认蓝色

        # 读取键值
        value = ctypes.c_uint()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print(i18nText("无法读取注册表键值"))
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
    if sys.platform != "win32":
        # Linux/macOS 暂时默认浅色或深色，后续可接入对应系统的检测
        return False

    try:
        # 定义注册表路径和键名
        reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
        reg_key = "AppsUseLightTheme"
        
        # 打开注册表键
        hkey = ctypes.wintypes.HKEY()
        if ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, reg_path, 0, 0x20019, ctypes.byref(hkey)) != 0:
            print(i18nText("无法打开注册表键"))
            return False
        
        # 读取键值
        value = ctypes.c_int()
        size = ctypes.c_uint(4)
        if ctypes.windll.advapi32.RegQueryValueExW(hkey, reg_key, 0, None, ctypes.byref(value), ctypes.byref(size)) != 0:
            print(i18nText("无法读取注册表键值"))
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
        test_file = os.path.join(tempfile.gettempdir(), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(i18nText("当前目录具有写入权限"))
        return True
    except (PermissionError, OSError):
        print(i18nText("当前目录没有写入权限"))
        return False

def restart():
    log(i18nText('重启程序'))
    
    if getattr(sys, 'frozen', False):
        args = [sys.executable] + sys.argv[1:]
    else:
        args = [sys.executable] + sys.argv
        
    if sys.platform == "win32":
        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS, shell=False)
    else:
        # Linux/macOS 使用 start_new_session, 相当于 DETACHED_PROCESS
        subprocess.Popen(args, start_new_session=True, shell=False)

    os._exit(0)

# base_directory = os.path.dirname(os.path.abspath(__file__)) # 不再需要，动态获取路径

def add_to_startup():
    """ 注册开机启动 (创建快捷方式到启动目录) """
    if sys.platform != "win32":
        log("非 Windows 平台暂不支持自动设置开机自启")
        return

    try:
        # 获取启动文件夹路径
        startup_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
        if not os.path.exists(startup_dir):
            os.makedirs(startup_dir)
        
        lnk_path = os.path.join(startup_dir, 'Bloret Launcher.lnk')
        
        # 获取当前运行的程序路径和目录
        if getattr(sys, 'frozen', False):
            # 打包后的 exe
            target_path = sys.executable
            working_dir = os.path.dirname(target_path)
            arguments = "--self-starting"
        else:
            # Python 脚本运行
            target_path = sys.executable  # python.exe
            script_path = os.path.abspath(sys.argv[0])
            working_dir = os.path.dirname(script_path)
            arguments = f'"{script_path}" --self-starting'

        icon_path = os.path.join(working_dir, 'bloret.ico')

        # 创建快捷方式
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(lnk_path)
        shortcut.TargetPath = target_path
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = working_dir
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        shortcut.WindowStyle = 1 
        shortcut.Save()
        
        log(f"已创建开机自启快捷方式: {lnk_path}")
    except Exception as e:
        handle_exception(e)
        log(f"注册开机启动失败: {e}", logging.ERROR)


def remove_from_startup():
    """ 取消注册开机启动 """
    if sys.platform != "win32":
        return

    try:
        startup_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
        lnk_path = os.path.join(startup_dir, 'Bloret Launcher.lnk')
        
        if os.path.exists(lnk_path):
            os.remove(lnk_path)
            log(f"已删除开机自启快捷方式: {lnk_path}")
        else:
            log("开机自启快捷方式不存在，无需删除")
    except Exception as e:
        handle_exception(e)
        log(f"取消注册开机启动失败: {e}", logging.ERROR)


def setup_startup_with_self_starting(value=True):
    if value:
        add_to_startup()
    else:
        remove_from_startup()


