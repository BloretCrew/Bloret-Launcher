import os,logging,shutil
from datetime import datetime
from modules.compat_widgets import InfoBar, InfoBarPosition
import logging,traceback,sys,webbrowser
from PySide6.QtWidgets import QApplication
# from PySide6.QtUiTools import QUiLoader # Removed uic for PySide6 compatibility
import modules.globals as BLglobals

copyright = "\n© 2026 Bloret Launcher All rights reserved. \n© 2026 Bloret All rights reserved."

# 创建日志文件夹
# 创建日志文件夹
log_folder = os.path.join(BLglobals.datapath, 'log')
try:
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
except Exception:
    pass # 忽略创建文件夹失败，可能没有权限

# 设置日志配置
log_filename = os.path.join(log_folder, f'Bloret_Launcher_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
try:
    if not os.path.exists(log_filename):
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write('')  # 创建空日志文件
except Exception:
    # 如果无法写入 APPDATA，尝试写入临时目录或当前目录
    log_filename = os.path.join(os.getcwd(), 'Bloret_Launcher.log')

# 配置根日志记录器
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 文件处理器
try:
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s'))
    logger.addHandler(file_handler)
except Exception:
    pass

# 控制台处理器 (仅当 sys.stdout 存在时)
if sys.stdout:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s'))
    logger.addHandler(console_handler)

def handle_exception(e):
    '''
    ## 显示错误跟踪窗口并报告异常
    专用于 log.py 模块的异常处理函数。其他文件中请使用 safe.py 的 handle_exception 函数。

    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    exc_type = type(e)
    exc_value = e
    exc_traceback = e.__traceback__
    log("未捕获的异常:", logging.CRITICAL)
    log("类型: {}".format(exc_type), logging.CRITICAL)
    log("信息: {}".format(exc_value), logging.CRITICAL)
    log("回溯: {}".format(traceback.format_tb(exc_traceback)), logging.CRITICAL)
    
    # loadUi is not directly available in PySide6
    # Skipping for now as we are migrating to QML
    # error_widget = loadUi("ui/ERROR.ui")
    return
    
    # 填写信息到输入框
    error_widget.type.setText(str(exc_type))
    error_widget.value.setText(str(exc_value))
    error_widget.traceback.setPlainText(''.join(traceback.format_tb(exc_traceback)))
    
    # 按钮功能实现
    def copy_to_clipboard():
        clipboard = QApplication.clipboard()
        clipboard.setText('Bloret Launcher 错误报告信息：\n - 类型：{}\n - 信息：{}\n - 回溯：{}'.format(exc_type, exc_value, ''.join(traceback.format_tb(exc_traceback))))
    
    def report_issue():
        webbrowser.open('https://github.com/BloretCrew/Bloret-Launcher/issues/new?template=BugReport.yml')
    
    def ignore_warning():
        error_widget.close()
    
    # 连接按钮点击事件
    error_widget.PushButton.clicked.connect(copy_to_clipboard)
    error_widget.PushButton_2.clicked.connect(report_issue)
    error_widget.PushButton_3.clicked.connect(ignore_warning)
    
    # 显示错误报告窗口
    error_widget.show()
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

# 缓存主要处理器的流对象以提升性能
_file_handler_stream = None

def _get_file_handler_stream():
    global _file_handler_stream
    if _file_handler_stream is not None:
        return _file_handler_stream
    
    # 尝试查找 FileHandler
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            if hasattr(h, 'stream') and h.stream:
                _file_handler_stream = h.stream
                return h.stream
    return None

import inspect

def log(message, level=logging.INFO):
    '''
    发送日志消息，输出到控制台并记录到日志文件。
    使用 stacklevel=2 来捕获调用者的位置信息。
    '''
    # 性能极致优化：针对极高频的游戏输出，直接写入流，跳过所有 logging 模块开销
    if message.startswith("[Game]") and level < logging.WARNING:
        stream = _get_file_handler_stream()
        if stream:
            try:
                # 手动格式化日志，格式需与 Formatter 保持一致：
                # %(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                level_name = logging.getLevelName(level)
                
                # 写入流 (不强制 flush)
                stream.write(f"{now_str} [{level_name}] [launch.py:0 - run()] {message}\n")
            except Exception:
                pass
        return

    # 正常日志：使用标准 logging 处理
    try:
        logger.log(level, message, stacklevel=2)
    except Exception:
        logger.log(level, message)

    # ERROR 及以上强制 flush，避免 Nuitka 无控制台打包在崩溃/退出前丢日志
    if level >= logging.ERROR:
        for h in logger.handlers:
            try:
                h.flush()
            except Exception:
                pass

def clear_log_files(self, log_clear_button):
    ''' 
    # 清空日志文件
    删除 `{%appdata%}/Bloret-Launcher/log` 文件夹下的所有文件。

    ***

    输入 :

        - [x] self
        - [x] log_clear_button
    ***
    输出 : 无
    
    ***
    ###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
    '''
    log_folder = os.path.join(BLglobals.datapath, 'log')
    file_num = len(os.listdir(log_folder))-1  # 减去一个正在使用的文件
    if os.path.exists(log_folder) and os.path.isdir(log_folder):
        for filename in os.listdir(log_folder):
            file_path = os.path.join(log_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                # InfoBar.success(
                #     title='🗑️ 清理成功',
                #     content=f"已清理 {file_path}",
                #     isClosable=True,
                #     position=InfoBarPosition.TOP,
                #     duration=5000,
                #     parent=self
                # )
            except Exception as e:
                log(f"Failed to delete {file_path}. Reason: {e}", logging.ERROR)
    InfoBar.success(
        title='🗑️ 清理成功',
        content=f"已清理 {file_num} 个文件",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )
    self.update_log_clear_button_text(log_clear_button)