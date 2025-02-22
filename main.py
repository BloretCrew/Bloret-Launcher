from PyQt5 import uic
from loguru import logger
from datetime import datetime
from .ClassWidgets.base import PluginBase, SettingsBase, PluginConfig  # 导入CW的基类

from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from qfluentwidgets import ImageLabel, LineEdit
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

        # 按钮
        self.openButton = self.findChild(QPushButton, 'open')
        self.openButton.clicked.connect(self.run_batch_file_in_thread)  # 修改连接到新的槽函数

    def run_batch_file_in_thread(self):
        thread = threading.Thread(target=self.run_batch_file)  # 创建新线程
        thread.start()  # 启动线程

    def run_batch_file(self):
        try:
            subprocess.run(os.path.join(self.PATH, 'run.bat'), check=True)
        except Exception as e:
            logger.error(f"Failed to run run.bat: {e}")
