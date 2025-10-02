import os,logging,shutil
from datetime import datetime
from qfluentwidgets import InfoBar, InfoBarPosition
import logging,traceback,sys,webbrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.uic import loadUi

copyright = "\n© 2025 Bloret Launcher All rights reserved. \n© 2025 Bloret All rights reserved."

# 创建日志文件夹
log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
# 设置日志配置
log_filename = os.path.join(log_folder, f'Bloret_Launcher_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
if not os.path.exists(log_filename):
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write('')  # 创建空日志文件
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def handle_exception(e):
    '''
    ## 显示错误跟踪窗口并报告异常
    专用于 log.py 模块的异常处理函数。其他文件中请使用 safe.py 的 handle_exception 函数。

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    exc_type = type(e)
    exc_value = e
    exc_traceback = e.__traceback__
    log("未捕获的异常:", logging.CRITICAL)
    log("类型: {}".format(exc_type), logging.CRITICAL)
    log("信息: {}".format(exc_value), logging.CRITICAL)
    log("回溯: {}".format(traceback.format_tb(exc_traceback)), logging.CRITICAL)
    
    # 加载 ERROR.ui 文件
    error_widget = loadUi("ui/ERROR.ui")
    
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

def log(message, level=logging.INFO):
    '''
    发送日志消息，输出到控制台并记录到日志文件。
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    print(message)
    logging.log(level, message)
    logging.getLogger().handlers[0].flush()  # 强制刷新日志
    # if level == logging.ERROR:
    #     handle_exception(Exception(message))  # 如果是错误级别，调用异常处理函数

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
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
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
    
    
