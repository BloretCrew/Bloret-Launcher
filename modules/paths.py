"""
paths.py
## Bloret Launcher 路径解析模块

### 模块功能：
 - [x] 提供统一的「应用资源根目录」解析，兼容开发环境、PyInstaller、Nuitka（standalone/onefile）。
 - [x] 避免各模块各自用 os.getcwd() / os.path.dirname(__file__) 定位打包资源，
       这些方式在 Nuitka onefile 下会指向错误目录。

### 关键事实（打包运行时）：
 - `sys.frozen` 不会被 Nuitka 设置（只有 PyInstaller 设置）。
 - `sys._MEIPASS` 仅 PyInstaller **onefile** 设置；**onedir** 无此属性，资源在 exe 同目录。
 - `sys.__nuitka_binary_dir` 由 Nuitka 设置：onefile 为临时解压目录，standalone 为 `.dist` 目录。
 - `os.getcwd()` 是启动目录（用户双击 exe 的位置），不一定是资源目录。
 - 被导入模块的 `__file__` 在打包后不可靠，不能用于定位打包数据。

因此定位打包资源时统一使用 `get_app_dir()`，不要依赖 `__file__` 或 `os.getcwd()`。


***
###### Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.
"""

import os
import sys
from pathlib import Path

_app_dir = None


def get_app_dir() -> Path:
    """
    返回应用打包资源的根目录（即 qml/、RinUI/、icon/、lang/、modules/、easytier/ 等
    数据目录所在的目录）。兼容开发环境、PyInstaller、Nuitka。

    返回值会被缓存，后续调用直接复用。

    :return: Path 对象，指向资源根目录
    """
    global _app_dir
    if _app_dir is not None:
        return _app_dir

    # Nuitka（standalone 目录 / onefile 临时目录）
    # sys.__nuitka_binary_dir 指向数据文件所在目录
    nuitka_binary_dir = getattr(sys, "__nuitka_binary_dir", None)
    if nuitka_binary_dir:
        _app_dir = Path(nuitka_binary_dir)
        return _app_dir

    # PyInstaller onefile：临时解压目录
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        _app_dir = Path(meipass)
        return _app_dir

    # PyInstaller onedir / 其它 frozen：资源与可执行文件同目录
    if getattr(sys, "frozen", False):
        _app_dir = Path(sys.argv[0]).resolve().parent
        return _app_dir

    # 开发环境：从本文件 (modules/paths.py) 向上一级到项目根目录
    _app_dir = Path(__file__).resolve().parent.parent
    return _app_dir


def app_path(*parts) -> str:
    """
    在应用资源根目录下拼接相对路径，返回字符串。
    例：app_path("lang", "zh-cn.json") -> "<app_dir>/lang/zh-cn.json"

    :param parts: 相对路径片段
    :return: 绝对路径字符串
    """
    return str(get_app_dir().joinpath(*parts))


def app_path_obj(*parts) -> Path:
    """与 app_path 相同，但返回 Path 对象。"""
    return get_app_dir().joinpath(*parts)


def resource_exists(*parts) -> bool:
    """检查应用资源根目录下某个相对路径是否存在。"""
    return app_path_obj(*parts).exists()
