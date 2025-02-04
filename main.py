from PyQt5 import uic
from loguru import logger
from datetime import datetime
from .ClassWidgets.base import PluginBase, SettingsBase, PluginConfig  # 导入CW的基类

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QFileDialog, QLineEdit
from qfluentwidgets import ImageLabel
import subprocess


# 设置页
class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        subprocess.Popen([f'{self.PATH}/Bloret-Launcher.exe'])
