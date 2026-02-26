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
from PySide6.QtWidgets import QApplication
# from PySide6.QtUiTools import QUiLoader # Removed uic/loadUi for PySide6 compatibility
from PySide6.QtCore import QThread, QObject, Signal as pyqtSignal
from modules.log import log
from modules.i18n import i18nText

def _show_error_ui(exc_type, exc_value, exc_traceback):
    """
    实际显示错误UI的函数，必须在主线程中运行
    """
    app = QApplication.instance()
    if not app:
        return

    try:
        # loadUi is not directly available in PySide6 without extra setup
        # Skipping for now as we are migrating to QML
        # error_widget = loadUi("ui/ERROR.ui")
        error_widget = None
        if not error_widget: return
        
        # 填写信息到输入框
        error_widget.type.setText(str(exc_type))
        error_widget.value.setText(str(exc_value))
        error_widget.traceback.setPlainText(''.join(traceback.format_tb(exc_traceback)))
        
        # 按钮功能实现
        def copy_to_clipboard():
            clipboard = app.clipboard()
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
        # 进入事件循环以保持窗口显示（如果这是启动时的致命错误且主循环未运行）
        if not QApplication.instance().activeWindow() and not QThread.currentThread().loopLevel():
             pass
             
    except Exception as e:
        print(f"CRITICAL: Failed to show ERROR UI: {e}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

class ErrorSignaler(QObject):
    show_error = pyqtSignal(object, object, object)

# 全局信号对象，将在模块导入时（主线程）创建
_signaler = ErrorSignaler()
_signaler.show_error.connect(_show_error_ui)

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
    
    # 检查是否有 QApplication 实例
    app = QApplication.instance()
    if not app:
        try:
            app = QApplication(sys.argv)
        except Exception:
            print("CRITICAL: PySide6 QApplication initialization failed during exception handling.")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

    # 检查当前线程是否为主线程
    if QThread.currentThread() != app.thread():
        # 如果在后台线程，使用信号发射到主线程执行
        _signaler.show_error.emit(exc_type, exc_value, exc_traceback)
    else:
        # 如果在主线程，直接执行
        _show_error_ui(exc_type, exc_value, exc_traceback)
        
        if not QApplication.instance().activeWindow():
             pass
    
    # 调用默认 hook
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

log_lock = threading.Lock()

def log_thread_safe(message, level=logging.INFO):
    with log_lock:
        log(message, level)
