# Nuitka 打包错误诊断与修复

## 问题描述
**错误日志**：
```
RuntimeError: Error loading QML file: ...\onefile_xxx\qml\main.qml
  QML engine errors:
    module "QtQuick.Layouts" is not installed
    module "QtQuick.Controls" is not installed
```

## 根本原因

### 原因 1（已修复）：缺少 QML 插件打包
Nuitka 的 PySide6 插件只有在 `--include-qt-plugins` 含 `qml` 时才打包 Qt QML 模块。
**修复**：`.github/workflows/Nuitka-Build.yml` 三个平台均添加 `qml`。

### 原因 2（已修复）：`RINUI_PATH` 绝对路径拼接 Bug
`resource_path()` 被传入绝对路径，Python 的 `Path(base)/绝对路径` 会忽略 base。
**修复**：`RinUI/core/config.py` 新增 `_get_data_root()` 用 `sys.__nuitka_binary_dir`。

### 原因 3（已修复）：QML 引擎错误被静默吞掉
**修复**：`RinUI/core/launcher.py` 添加 `qInstallMessageHandler` 捕获 QML 警告/错误。

### 原因 4（已修复）：`os.getcwd()` / `__file__` 定位打包资源
Nuitka onefile 下 `os.getcwd()` 是启动目录（非解压目录），被导入模块的 `__file__`
解析不可靠。多个模块用这两种方式定位 lang/、icon/、easytier/、web/ 等资源，打包后失效。
**修复**：新增 `modules/paths.py` 统一路径解析（优先 `sys.__nuitka_binary_dir`），
替换各模块的 `os.getcwd()` / `os.path.dirname(__file__)` 资源定位。

### 原因 5（已修复）：`_get_script_dir()` 依赖 `sys.frozen`
Nuitka 不设置 `sys.frozen`（只有 PyInstaller 设置），原逻辑靠 `__file__` 兜底巧合工作。
**修复**：`Bloret-Launcher.py` 显式检测 `sys.__nuitka_binary_dir`。

## 新增文件
- `modules/paths.py` — 统一资源路径解析（`get_app_dir()` / `app_path()`）
  - Nuitka: `sys.__nuitka_binary_dir`
  - PyInstaller: `sys._MEIPASS`
  - 开发环境: `__file__` 向上一级

## 修改文件清单

### 路径解析修复（问题 2）
| 文件 | 修改 |
|------|------|
| `modules/paths.py` | **新增**：统一路径工具 |
| `modules/i18n.py` | `lang/*.json` 用 `app_path` |
| `modules/web.py` | CSS/HTML（9处）用 `app_path` |
| `modules/easytier.py` | easytier 二进制定位用 `get_app_dir`（修复联机功能） |
| `modules/ShortCut.py` | `icon/home.png`、QML 用 `app_path`/`get_app_dir` |
| `modules/install.py` | UI、servers.dat、图标用 `app_path` |
| `modules/versions.py` | UI 用 `app_path` |
| `modules/mwtool.py` | mwtool.ui、config.json、Bloret.png 用 `app_path` |
| `modules/local_client.py` | frpc 定位用 `app_path`，配置复制到可写目录 |
| `modules/BLServer.py` | 快捷方式用 exe 实际目录（`sys.argv[0]`） |
| `modules/update.py` | 通知图标用 `app_path` |
| `modules/setup_ui.py` | `resource_path` 委托 `app_path`；修复 `ui/icon/`→`icon/`（既有 bug） |
| `modules/BLDownload.py` | `.minecraft`、图标用 `app_path` |

### 主入口修复（问题 1）
| 文件 | 修改 |
|------|------|
| `Bloret-Launcher.py` | `_get_script_dir()` 显式检测 `sys.__nuitka_binary_dir` |

### QML 修复（已在前一轮完成）
| 文件 | 修改 |
|------|------|
| `.github/workflows/Nuitka-Build.yml` | `--include-qt-plugins` 加 `qml`（三平台） |
| `RinUI/RinUI/core/config.py` | `_get_data_root()` |
| `RinUI/RinUI/core/launcher.py` | QML 消息捕获 + 诊断信息 |

## 问题 3：frpc 自动下载（已检查）
- `modules/local_client.py` 只读取本地已有的 `frpc.toml`/`frpc.exe`，**无自动下载逻辑**。
- workflow 的 EasyTier 自动下载逻辑正常：资产命名匹配 v2.6.4，有 zip 验证 + gh/curl 回退。
- frpc 文件未打包且无下载代码 → 在线客户端功能在打包后仍会提示"frpc程序不存在"。
  这属于功能缺失（非 Nuitka 打包问题），已将路径改为 `app_path` 以便将来补充 frpc 后即可工作。

## 既有 bug（顺手修复）
- `modules/setup_ui.py` 引用 `ui/icon/*.png`，但图标实际在 `icon/`（无 `ui/icon` 目录），
  导致版本列表图标一直加载失败。已改为 `icon/`。
- `modules/install.py` 的 `vanilla_icon_path`/`fabric_icon_path` 同样引用 `ui/icon/`，已修复。

---
修复时间：2026-06-19
