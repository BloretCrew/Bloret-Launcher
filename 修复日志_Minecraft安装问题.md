# Minecraft 安装问题修复日志

## 问题描述
在将程序从 `qfluentwidgets` 转换为 `RinUI` 时，Minecraft 安装过程出现问题：
```
2026-02-26 18:02:10,073 [INFO] [install.py:496 - InstallMinecraftVersion()] Warning: uic.loadUi called but not available. UI may not display.
```

## 根本原因
旧代码中使用了 `PyQt5` 的 `uic.loadUi()` 方法来加载 UI 文件，而 PySide6 没有直接的 `uic` 模块。迁移时添加了警告日志并直接返回，导致**整个安装流程被中断**。

## 修复方案

### 1. **modules/install.py** 修改
#### a) 新增导入
```python
from PySide6.QtUiTools import QUiLoader
```

#### b) 新增 `load_ui_file()` 函数
这个函数使用 PySide6 的 `QUiLoader` 来加载 UI 文件：
- 支持相对路径和绝对路径
- 文件不存在时返回 `None` 并记录警告
- 加载失败时捕获异常并记录错误

#### c) 修复 `InstallMinecraftVersion()` 函数
**原始代码（有问题）：**
```python
if download_dialog is None:
    try:
        download_dialog = QDialog()
        # uic.loadUi is not available in PySide6. Returning early as a safeguard.
        log("Warning: uic.loadUi called but not available. UI may not display.")
        return  # ❌ 这里直接返回，导致流程中断
```

**修复后的代码：**
```python
if download_dialog is None:
    try:
        # 尝试使用 QUiLoader 加载 UI 文件
        download_dialog = load_ui_file("ui/MCVer_downloading.ui")
        
        # 如果 UI 加载失败，创建一个简单的对话框作为备选方案
        if download_dialog is None:
            log("UI 文件加载失败，使用基础对话框代替", logging.WARNING)
            download_dialog = QDialog()
            download_dialog.setMinimumWidth(700)
            download_dialog.setMinimumHeight(400)
        
        # ... 继续设置对话框 ...
```

**关键改进：**
- ✅ 使用 `QUiLoader` 被加载 UI 文件
- ✅ 如果 UI 加载失败，不会中断（创建基础对话框）
- ✅ 继续执行安装流程（不再有 `return` 语句）

### 2. **modules/versions.py** 修改
#### a) 新增导入
```python
from PySide6.QtWidgets import QDialog  # 新增
from PySide6.QtUiTools import QUiLoader  # 新增
```

#### b) 新增 `load_ui_file()` 函数
与 `install.py` 中的实现相同

#### c) 修复 `InstallMinecraftVersion()` 函数
应用与 `install.py` 相同的修复逻辑

## 修改的文件列表
1. `modules/install.py`
   - 添加 `QUiLoader` 导入
   - 添加 `load_ui_file()` 函数
   - 修复 `InstallMinecraftVersion()` 函数

2. `modules/versions.py`
   - 添加 `QDialog` 和 `QUiLoader` 导入
   - 添加 `load_ui_file()` 函数
   - 修复 `InstallMinecraftVersion()` 函数

## 验证方法
✅ 已通过 Python 语法检查：
```bash
python -m py_compile modules/install.py modules/versions.py
```

## 后续处理
- 如果 UI 文件加载仍有问题，可以考虑：
  1. 使用 QUiLoader 编译 UI 文件为 Python 代码（推荐）
  2. 手动使用 QML 或代码创建 UI
  3. 将 UI Designer 文件转换为 PySide6 兼容格式

## 相关文件
- 老版本参考：`temp/Bloret-Launcher-Windows/modules/install.py`
- UI 文件：`ui/MCVer_downloading.ui`
- RinUI 文档：`temp/RinUI-docs-main/`
