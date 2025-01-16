import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from qfluentwidgets import NavigationInterface, NavigationItemPosition
import datetime
from PyQt5 import uic
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bloret 启动器 (beta)")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icons/bloret.png"))  # 设置软件图标

        # 创建侧边栏
        self.navigation_interface = NavigationInterface(self)
        self.navigation_interface.addItem(
            routeKey="home",
            icon="icons/bloret.png",
            text="主页",
            onClick=self.on_home_clicked,
            position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey="download",
            icon="icons/download.png",
            text="下载",
            onClick=self.on_download_clicked,
            position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey="passport",
            icon="icons/passport.png",
            text="通行证",
            onClick=self.on_passport_clicked,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey="settings",
            icon="icons/settings.png",
            text="设置",
            onClick=self.on_settings_clicked,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey="info",
            icon="icons/info.png",
            text="关于",
            onClick=self.on_info_clicked,
            position=NavigationItemPosition.BOTTOM
        )

        # 创建按钮
        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.on_button_clicked)

        # 主布局
        self.main_layout = QHBoxLayout()  # 使用QHBoxLayout使侧边栏在左侧，内容在右侧
        self.main_layout.addWidget(self.navigation_interface)

        self.content_layout = QVBoxLayout()
        self.content_layout.addWidget(self.button)
        self.main_layout.addLayout(self.content_layout)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        # 默认加载主页
        self.load_ui("ui/home.ui")

    def on_home_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 主页 被点击")
        self.load_ui("ui/home.ui")

    def on_download_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 下载 被点击")
        self.load_ui("ui/download.ui")

    def on_passport_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 通行证 被点击")
        self.load_ui("ui/passport.ui")

    def on_settings_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 设置 被点击")
        self.load_ui("ui/settings.ui")

    def on_info_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 关于 被点击")
        self.load_ui("ui/info.ui")

    def load_ui(self, ui_path):
        widget = uic.loadUi(ui_path)
        # 清除之前的内容
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)
        self.content_layout.addWidget(widget)

    def on_button_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 按钮 被点击")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
