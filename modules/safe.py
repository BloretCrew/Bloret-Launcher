'''
Safe.py
## Bloret Launcher 错误处理模块

### 模块功能：
 - [x] 捕获未捕获的异常，并显示错误跟踪窗口。
 - [x] 显示错误跟踪窗口，并允许用户复制错误信息到剪贴板，并提交问题。
 - [x] 允许用户忽略警告。


***
###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
'''

import threading,logging,traceback,sys,webbrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.uic import loadUi
from modules.log import log
from modules.i18n import i18nText

def handle_exception(exc_type, exc_value, exc_traceback):
    '''
    ## 显示错误跟踪窗口并报告异常

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 参数已由系统异常钩子直接提供
    log(i18nText("未捕获的异常:"), logging.CRITICAL)
    log(i18nText("类型: {}").format(exc_type), logging.CRITICAL)
    log(i18nText("信息: {}").format(exc_value), logging.CRITICAL)
    log(i18nText("回溯: {}").format(traceback.format_tb(exc_traceback)), logging.CRITICAL)
    
    # 加载 ERROR.ui 文件
    error_widget = loadUi("ui/ERROR.ui")
    
    # 填写信息到输入框
    error_widget.type.setText(str(exc_type))
    error_widget.value.setText(str(exc_value))
    error_widget.traceback.setPlainText(''.join(traceback.format_tb(exc_traceback)))
    
    # 按钮功能实现
    def copy_to_clipboard():
        clipboard = QApplication.clipboard()
        clipboard.setText(i18nText('Bloret Launcher 错误报告信息：\n - 类型：{}\n - 信息：{}\n - 回溯：{}').format(exc_type, exc_value, ''.join(traceback.format_tb(exc_traceback))))
    
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
    
    # w = Dialog("Bloret Launcher 发生了一些小问题...", "类型: {}\n信息: {}\n回溯: {}\n如果您认为这是 Bloret Launcher 的问题，请提交此问题。\n按下确认按钮将以上信息复制到剪贴板".format(exc_type, exc_value, traceback.format_tb(exc_traceback)))
    # w.setWindowIcon(QIcon('bloret.ico'))
    # w.setWindowTitle("Bloret Launcher")
    # if w.exec():
    #     print('复制到剪贴板')
    #     clipboard = QApplication.clipboard()
    #     clipboard.setText("类型: {}\n信息: {}\n回溯: {}".format(exc_type, exc_value, ''.join(traceback.format_tb(exc_traceback))))
    # else:
    #     print('取消')
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    # uic.loadUi("ui/ERROR.ui")

sys.excepthook = handle_exception

log_lock = threading.Lock()

def log_thread_safe(message, level=logging.INFO):
    with log_lock:
        log(message, level)

