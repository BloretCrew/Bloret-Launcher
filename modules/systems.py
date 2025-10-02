from modules.win11toast import toast
import ctypes.wintypes,ctypes,logging,os,subprocess
from win32com.client import Dispatch

from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText
import sys

def get_system_theme_color():
    """获取系统主题颜色"""
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
        test_file = os.path.join(os.getcwd(), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(i18nText("当前目录具有写入权限"))
        return True
    except PermissionError:
        print(i18nText("当前目录没有写入权限"))
        return False

def restart():
    log(i18nText('重启程序'))
    os.execl(sys.executable, sys.executable, *sys.argv)

base_directory = os.path.dirname(os.path.abspath(__file__))

def add_to_startup(file_path=f'{base_directory}/Bloret-Launcher.exe', icon_path=''):  # 注册到开机启动
    if os.name != 'nt':
        return
    if file_path == "":
        file_path = os.path.realpath(__file__)
    else:
        file_path = os.path.abspath(file_path)  # 将相对路径转换为绝对路径

    if icon_path == "":
        icon_path = file_path  # 如果未指定图标路径，则使用程序路径
    else:
        icon_path = os.path.abspath(icon_path)  # 将相对路径转换为绝对路径

    # 获取启动文件夹路径
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    # 快捷方式文件名（使用文件名或自定义名称）
    name = os.path.splitext(os.path.basename(file_path))[0]  # 使用文件名作为快捷方式名称
    shortcut_path = os.path.join(startup_folder, f'{name}.lnk')

    # 创建快捷方式
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = file_path
    shortcut.Arguments = "--self-starting"  # 添加自启动参数
    shortcut.WorkingDirectory = os.path.dirname(file_path)
    shortcut.IconLocation = icon_path  # 设置图标路径
    shortcut.save()


def remove_from_startup(file_path=f'{base_directory}/Time-Machine.exe'):
    log(i18nText('取消注册开机启动'))
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    if file_path == "":
        file_path = os.path.realpath(__file__)
    else:
        file_path = os.path.abspath(file_path)  # 将相对路径转换为绝对路径
    name = os.path.splitext(os.path.basename(file_path))[0]  # 使用文件名作为快捷方式名称
    shortcut_path = os.path.join(startup_folder, f'{name}.lnk')
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)


def setup_startup_with_self_starting(value=True):
    if value:
        add_to_startup()
    else:
        remove_from_startup()
    log(f"设置开机自启 {'启用' if value else '禁用'}")

