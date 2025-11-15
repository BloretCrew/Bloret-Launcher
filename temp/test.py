from PyQt5.QtWidgets import QApplication
import sys
from modules.ShortCut import ScreenShortCut

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ScreenShortCut()
    sys.exit(app.exec_())