from PyQt5 import uic
from loguru import logger
from .ClassWidgets.base import SettingsBase, PluginConfig  # 导入CW的基类

from PyQt5.QtWidgets import QPushButton
from qfluentwidgets import SwitchButton
import subprocess, os
import threading  # 添加导入threading模块

# 设置页
class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(f'{self.PATH}/settings.ui', self)  # 加载设置界面

        default_config = {
            "name": "打开记事本",
            "action": "notepad"
        }

        self.cfg = PluginConfig(self.PATH, 'config.json')  # 实例化配置类
        self.cfg.load_config(default_config)  # 加载配置

        if self.cfg.config.get('whenCWopen_BLopen', False):
            self.run_batch_file_in_thread() # 打开 Class-Widgets 时就打开 Bloret-Launcher

        # 按钮
        self.openButton = self.findChild(QPushButton, 'open')
        self.openButton.clicked.connect(self.run_batch_file_in_thread)  # 修改连接到新的槽函数
        # 开关控件
        self.whenCWopen_BLopen = self.findChild(SwitchButton, 'whenCWopen_BLopen')
        self.whenCWopen_BLopen.setChecked(self.cfg.config.get('whenCWopen_BLopen', False))  # 根据配置文件设置开关状态
        self.whenCWopen_BLopen.checkedChanged.connect(self.update_whenCWopen_BLopen)  # 连接到槽函数

    def update_whenCWopen_BLopen(self, state):
        self.cfg.config['whenCWopen_BLopen'] = state  # 直接更新配置字典
        self.cfg.save_config()  # 保存配置
        print(f"whenCWopen_BLopen 开关状态已更新为: {state}")  # 添加日志记录

    def run_batch_file_in_thread(self):
        thread = threading.Thread(target=self.run_batch_file)  # 创建新线程
        thread.start()  # 启动线程

    def run_batch_file(self):
        try:
            exe_path = os.path.join(self.PATH, 'Bloret-Launcher', 'Bloret-Launcher.exe')
            subprocess.run(exe_path, check=True, cwd=os.path.join(self.PATH, 'Bloret-Launcher'), creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            logger.error(f"Failed to run Bloret-Launcher\Bloret-Launcher.exe: {e}")
