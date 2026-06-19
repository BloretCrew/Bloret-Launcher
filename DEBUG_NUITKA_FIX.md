# Nuitka 打包错误诊断与修复

## 问题描述
**错误日志**：
```
RuntimeError: Error loading QML file: C:\Users\...\Temp\onefile_xxx\qml\main.qml
```

## 根本原因分析

### 核心 Bug：`resource_path()` 被传入绝对路径
**文件**: `RinUI/core/config.py`

`resource_path()` 设计用于**相对路径**，但 `RINUI_PATH` 计算时传入了绝对路径：
```python
rinui_core_path = Path(__file__).resolve().parent  # 绝对路径！
RINUI_PATH = resource_path(rinui_core_path.parent.parent)  # 传入绝对路径
```

Python 的 `Path(base) / absolute_path` 会**忽略 base**，直接返回 absolute_path。
在 Nuitka 编译模式下，`resource_path()` 内部的 `Path(sys.__nuitka_binary_dir) / absolute_path`
不会拼接 `sys.__nuitka_binary_dir`，而是直接返回编译时的源码路径（CI runner 的路径），
该路径在用户机器上不存在。

### 次要问题：QML 引擎错误被静默吞掉
**文件**: `RinUI/core/launcher.py`

`engine.load()` 的异常被捕获并 print，但 QML 引擎的内部警告/错误通过 Qt 消息系统
输出，不会变成 Python 异常。当 `rootObjects()` 为空时，无法知道具体失败原因。

## 已应用的修复（2026-06-19）

### 修复 1：新增 `_get_data_root()` 函数
```python
def _get_data_root():
    """获取数据文件根目录，兼容 PyInstaller、Nuitka 和开发环境"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    if hasattr(sys, "__nuitka_binary_dir"):
        return Path(sys.__nuitka_binary_dir)
    return rinui_core_path.parent.parent

RINUI_PATH = _get_data_root()
```

### 修复 2：添加 QML 引擎错误捕获
```python
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

_qml_messages = []

def _qml_message_handler(msg_type, context, message):
    if msg_type in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        _qml_messages.append(f"[QML {type_name}] {message}")
```

在 `load()` 中安装消息处理器，加载后输出收集到的 QML 消息。

### 修复 3：增强错误诊断信息
```python
if not self.engine.rootObjects():
    diag = f"Error loading QML file: {self.qml_path}"
    diag += f"\n  RINUI_PATH: {RINUI_PATH} (exists: {RINUI_PATH.exists()})"
    diag += f"\n  QML file exists: {self.qml_path.exists()}"
    if _qml_messages:
        diag += "\n  QML engine errors:\n    " + "\n    ".join(_qml_messages)
    raise RuntimeError(diag)
```

### 修复 4：修复 `modules/setup_ui.py` 的 `resource_path()`
添加了 `sys.__nuitka_binary_dir` 支持。

## 调试输出
`Bloret-Launcher.py` 现在会输出以下调试信息：
```
[DEBUG] SCRIPT_DIR: <temp_extraction_dir>
[DEBUG] sys.__nuitka_binary_dir: <temp_extraction_dir>
[DEBUG] RINUI_PATH: <temp_extraction_dir>
[DEBUG] RINUI_PATH exists: True
```

## 修改文件清单
- `RinUI/core/config.py` — 新增 `_get_data_root()`，修复 `RINUI_PATH`
- `RinUI/core/launcher.py` — QML 消息捕获 + 增强错误诊断
- `Bloret-Launcher.py` — 增强调试输出
- `modules/setup_ui.py` — `resource_path()` 添加 Nuitka 支持

---
修复时间：2026-06-19
