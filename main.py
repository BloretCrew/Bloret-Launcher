import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from qfluentwidgets import NavigationInterface, NavigationItemPosition
import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bloret 启动器")
        self.setGeometry(100, 100, 800, 600)

        # 创建侧边栏
        self.navigation_interface = NavigationInterface(self)
        self.navigation_interface.addItem(
            routeKey="home",
            icon="icons/home.png",
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
            icon="icons/passport.svg",
            text="通行证",
            onClick=self.on_passport_clicked,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey="settings",
            icon="icons/settings.svg",
            text="设置",
            onClick=self.on_settings_clicked,
            position=NavigationItemPosition.BOTTOM
        )

        # 创建按钮
        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.on_button_clicked)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.navigation_interface)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_home_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 主页 clicked")

    def on_download_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 下载 clicked")

    def on_passport_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 通行证 clicked")

    def on_settings_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] 设置 clicked")

    def on_button_clicked(self):
        print(f"{datetime.datetime.now()} [INFO] Button clicked")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
