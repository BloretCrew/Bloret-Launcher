# Nuitka 打包错误诊断与修复

## 问题描述
**错误日志**：
```
Error loading QML file: C:\Users\0570\AppData\Local\Temp\onefile_8868_922944_FRrhetA8He4\qml\main.qml
```

## 根本原因分析

### 1. 路径处理不完整
**文件**: `RinUI/core/config.py`

问题：`resource_path()` 函数只处理了 PyInstaller 的情况，未处理 Nuitka：
```python
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):  # ✅ PyInstaller 支持
        return Path(sys._MEIPASS) / relative_path
    # ❌ 缺少 Nuitka 支持
    return Path(relative_path).resolve()
```

当 Nuitka 以 `--onefile` 模式打包时，会设置 `sys.__nuitka_binary_dir` 属性，但代码未识别这个属性，导致路径解析错误。

### 2. 路径检查逻辑混乱
**文件**: `RinUI/core/launcher.py`

问题：`load()` 方法的逻辑有矛盾：
```python
if self.qml_path.exists():          # 检查 QML 文件
    self.engine.addImportPath(RINUI_PATH)
else:
    msg = f"Cannot find RinUI module: {RINUI_PATH}"  # 错误！
    raise FileNotFoundError(msg)    # 错误消息不匹配
```

应该分别检查 RINUI_PATH 和 QML 文件的存在性。

## 已应用的修复

### 修复 1：添加 Nuitka 路径支持
```python
def resource_path(relative_path):
    """兼容 PyInstaller 打包、Nuitka 打包和开发环境的路径"""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller onefile mode
        return Path(sys._MEIPASS) / relative_path
    elif hasattr(sys, "__nuitka_binary_dir"):
        # Nuitka compiled mode
        return Path(sys.__nuitka_binary_dir) / relative_path
    return Path(relative_path).resolve()
```

### 修复 2：修正路径检查逻辑
```python
def load(self, qml_path: Union[str, Path] = None) -> None:
    # ... 初始化代码 ...
    
    # 检查 RinUI 模块路径是否存在
    if not RINUI_PATH.exists():
        msg = f"Cannot find RinUI module: {RINUI_PATH}"
        raise FileNotFoundError(msg)
    
    self.engine.addImportPath(RINUI_PATH)
    
    # 检查 QML 文件是否存在
    if not self.qml_path.exists():
        msg = f"Cannot find QML file: {self.qml_path}"
        raise FileNotFoundError(msg)
    
    # ... 加载和初始化 ...
```

## 相关的 Nuitka 打包命令

从 `.github/workflows/Nuitka-Build.yml` 的 Windows 部分：
```powershell
python -m nuitka --standalone --onefile \
  --include-data-dir=qml=qml \
  --include-data-dir=RinUI=RinUI \
  --include-data-dir=icon=icon \
  --include-data-dir=lang=lang \
  --include-data-dir=modules=modules \
  ...
```

这些包含数据目录的命令应该确保资源被正确打包。

## 调试建议

如果问题继续出现，请检查：

1. **验证 Nuitka 版本**：
   ```bash
   python -m pip list | grep nuitka
   ```

2. **添加调试输出**（临时）：
   ```python
   # 在 Bloret-Launcher.py 中
   print(f"SCRIPT_DIR: {SCRIPT_DIR}")
   print(f"sys.__nuitka_binary_dir: {getattr(sys, '__nuitka_binary_dir', 'NOT SET')}")
   print(f"QML path: {SCRIPT_DIR / 'qml' / 'main.qml'}")
   print(f"QML exists: {(SCRIPT_DIR / 'qml' / 'main.qml').exists()}")
   ```

3. **检查打包输出**：
   确认 `dist/Bloret-Launcher.exe` 创建后，在 temp 目录中检查是否包含 `qml/` 目录。

4. **Nuitka 特定选项**：
   如果问题仍然存在，可考虑添加：
   ```bash
   --follow-imports  # 跟踪所有导入
   --no-prefer-source-code  # 使用编译后的 .pyc
   ```

## 下一步

1. **重新打包**：使用修复后的代码重新运行 Nuitka 打包
2. **测试**：运行生成的 `Bloret-Launcher.exe`
3. **验证**：确保 QML UI 正常加载和显示

---

修复时间：2026-06-08
修改文件：
- `RinUI/core/config.py`
- `RinUI/core/launcher.py`
