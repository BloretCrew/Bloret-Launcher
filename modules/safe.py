import threading,logging,traceback,sys
from qfluentwidgets import Dialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from modules.log import log, importlog
def handle_exception(exc_type, exc_value, exc_traceback):
    log("未捕获的异常:", logging.CRITICAL)
    log("类型: {}".format(exc_type), logging.CRITICAL)
    log("信息: {}".format(exc_value), logging.CRITICAL)
    log("回溯: {}".format(traceback.format_tb(exc_traceback)), logging.CRITICAL)
    w = Dialog("Bloret Launcher 发生了一些小问题...", "类型: {}\n信息: {}\n回溯: {}\n如果您认为这是 Bloret Launcher 的问题，请提交此问题。\n按下确认按钮将以上信息复制到剪贴板".format(exc_type, exc_value, traceback.format_tb(exc_traceback)))
    w.setWindowIcon(QIcon('bloret.ico'))
    w.setWindowTitle("Bloret Launcher")
    if w.exec():
        print('复制到剪贴板')
        clipboard = QApplication.clipboard()
        clipboard.setText("类型: {}\n信息: {}\n回溯: {}".format(exc_type, exc_value, ''.join(traceback.format_tb(exc_traceback))))
    else:
        print('取消')
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    # uic.loadUi("ui/ERROR.ui")

sys.excepthook = handle_exception

log_lock = threading.Lock()

def log_thread_safe(message, level=logging.INFO):
    with log_lock:
        log(message, level)

importlog("SAFE.PY")