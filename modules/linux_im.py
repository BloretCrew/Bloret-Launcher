"""
Linux 输入法（fcitx5 / ibus）兼容层。

必须在 import PySide6 或创建 QApplication 之前调用 setup_linux_input_method()。

问题背景
--------
pip / venv 安装的 PySide6 会自带一份私有 Qt6 库与插件目录，其中不包含
libfcitx5platforminputcontextplugin.so。系统 fcitx5-qt 插件链接的是系统 Qt6，
与 pip 私有 Qt 二进制不兼容：插件即使被链接过去也会立刻卸载，表现为：
  - 无法切换中/英输入法
  - 无法输入中文

系统包 python-pyside6 使用系统 Qt6，与 fcitx5-qt 一致，可正常工作。

本模块会：
1. 根据运行中的输入法守护进程配置 QT_IM_MODULE / XMODIFIERS 等环境变量
2. 若检测到 pip 风格的 PySide6，优先改用系统 python-pyside6
3. 输出详细诊断日志，便于排查
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _log(msg: str) -> None:
    """启动极早期日志：此时 modules.log 可能尚未就绪，统一走 stdout。"""
    print(f"[IM] {msg}", flush=True)


def _process_running(name: str) -> bool:
    """粗略检测某进程是否在运行（不依赖 psutil，避免启动期额外依赖）。"""
    try:
        proc = Path("/proc")
        if not proc.is_dir():
            return False
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmdline = (entry / "cmdline").read_bytes()
            except (OSError, PermissionError):
                continue
            # cmdline 以 \0 分隔
            text = cmdline.replace(b"\0", b" ").decode("utf-8", errors="ignore")
            if name in text:
                return True
    except Exception as e:
        _log(f"检测进程 {name} 失败: {e}")
    return False


def _detect_im_module() -> str:
    """
    选择合适的 QT_IM_MODULE 值。

    fcitx5 的 Qt 插件注册的 key 仍是 "fcitx"（不是 "fcitx5"）。
    """
    current = (os.environ.get("QT_IM_MODULE") or "").strip()
    # 已显式指定有效模块时尊重用户设置
    if current and current.lower() not in ("xim", "none", "compose", "qtvirtualkeyboard"):
        return current

    xmodifiers = (os.environ.get("XMODIFIERS") or "").lower()
    gtk_im = (os.environ.get("GTK_IM_MODULE") or "").lower()

    if (
        _process_running("fcitx5")
        or _process_running("fcitx")
        or "fcitx" in xmodifiers
        or "fcitx" in gtk_im
    ):
        return "fcitx"

    if (
        _process_running("ibus-daemon")
        or "ibus" in xmodifiers
        or "ibus" in gtk_im
    ):
        return "ibus"

    # 默认偏向 fcitx：国内桌面更常见；无效时 Qt 会回退到 compose
    return current or "fcitx"


def _configure_im_env() -> None:
    """配置输入法相关环境变量（创建 QApplication 前生效）。"""
    im = _detect_im_module()
    prev_qt = os.environ.get("QT_IM_MODULE")
    os.environ["QT_IM_MODULE"] = im

    # X11 / XWayland 传统协议
    if im == "fcitx":
        os.environ.setdefault("XMODIFIERS", "@im=fcitx")
        os.environ.setdefault("GTK_IM_MODULE", "fcitx")
        # GLFW / LWJGL（Minecraft）只认 ibus 模块名；fcitx5 提供 ibus 前端协议
        os.environ.setdefault("GLFW_IM_MODULE", "ibus")
    elif im == "ibus":
        os.environ.setdefault("XMODIFIERS", "@im=ibus")
        os.environ.setdefault("GTK_IM_MODULE", "ibus")
        os.environ.setdefault("GLFW_IM_MODULE", "ibus")

    _log(
        f"输入法环境: QT_IM_MODULE={im}"
        f" (原值={prev_qt!r})"
        f", XMODIFIERS={os.environ.get('XMODIFIERS')!r}"
        f", GLFW_IM_MODULE={os.environ.get('GLFW_IM_MODULE')!r}"
        f", session={os.environ.get('XDG_SESSION_TYPE')!r}"
        f", wayland={os.environ.get('WAYLAND_DISPLAY')!r}"
        f", display={os.environ.get('DISPLAY')!r}"
    )


def _is_pip_style_pyside6(site_packages: Path) -> bool:
    """
    pip 安装的 PySide6 在包内自带 Qt/plugins、Qt/lib；
    系统 python-pyside6 则依赖系统 /usr/lib/qt6。
    """
    pyside = site_packages / "PySide6"
    if not pyside.is_dir():
        return False
    bundled_plugins = pyside / "Qt" / "plugins"
    bundled_lib = pyside / "Qt" / "lib"
    return bundled_plugins.is_dir() or bundled_lib.is_dir()


def _has_fcitx_plugin_in_pyside(site_packages: Path) -> bool:
    plugin = (
        site_packages
        / "PySide6"
        / "Qt"
        / "plugins"
        / "platforminputcontexts"
        / "libfcitx5platforminputcontextplugin.so"
    )
    return plugin.exists()


def _system_site_packages() -> list[Path]:
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        Path(f"/usr/lib/python{ver}/site-packages"),
        Path(f"/usr/lib64/python{ver}/site-packages"),
        # Debian / Ubuntu 多版本布局
        Path(f"/usr/local/lib/python{ver}/dist-packages"),
        Path(f"/usr/lib/python3/dist-packages"),
    ]
    return [p for p in candidates if p.is_dir()]


def _prefer_system_pyside6_for_fcitx() -> None:
    """
    若当前会加载到「无 fcitx 插件的 pip PySide6」，优先把系统 site-packages
    插到 sys.path 前面，让 import PySide6 命中系统包。

    其它仅存在于 venv 的依赖仍可从后续 path 中解析。
    """
    system_sites = _system_site_packages()
    system_with_pyside = [s for s in system_sites if (s / "PySide6").is_dir()]

    # 当前 path 上即将命中的 PySide6 位置
    pip_sites: list[Path] = []
    for raw in sys.path:
        if not raw:
            continue
        try:
            site = Path(raw)
        except Exception:
            continue
        if _is_pip_style_pyside6(site) and not _has_fcitx_plugin_in_pyside(site):
            pip_sites.append(site)

    if not pip_sites:
        # 可能已经是系统包，或尚不存在 PySide6
        for s in system_with_pyside:
            _log(f"将使用 PySide6 候选路径: {s / 'PySide6'}")
            break
        else:
            # 检查 path 上是否有任意 PySide6
            for raw in sys.path:
                if raw and (Path(raw) / "PySide6").is_dir():
                    _log(f"检测到 PySide6: {Path(raw) / 'PySide6'}")
                    break
            else:
                _log("尚未在 sys.path 中发现 PySide6（将在 import 时解析）")
        return

    if not system_with_pyside:
        _log(
            "检测到 pip/venv PySide6（自带私有 Qt，无 fcitx5 插件），"
            "但系统未安装 python-pyside6。中文输入法可能无法切换。"
            "请安装: sudo pacman -S python-pyside6 fcitx5-qt  "
            "或: sudo apt install python3-pyside6.qtwidgets fcitx5-frontend-qt6"
        )
        _try_warn_plugin_mismatch(pip_sites[0])
        return

    # 将系统 site-packages 插到「第一个 pip PySide6 路径」之前，
    # 这样：项目目录 / SCRIPT_DIR 仍优先（本地 RinUI 等不被覆盖），
    # 同时 PySide6/shiboken6 会命中系统包而非 venv 私有 Qt。
    insert_at = None
    for idx, raw in enumerate(sys.path):
        try:
            if Path(raw) in pip_sites or any(Path(raw) == p for p in pip_sites):
                insert_at = idx
                break
        except Exception:
            continue
    if insert_at is None:
        insert_at = 0

    for site in reversed(system_with_pyside):
        site_str = str(site)
        while site_str in sys.path:
            # 若已在 path 中，先移除再按目标位置插入
            old_idx = sys.path.index(site_str)
            sys.path.remove(site_str)
            if old_idx < insert_at:
                insert_at -= 1
        sys.path.insert(insert_at, site_str)
        _log(
            f"优先使用系统 PySide6: {site / 'PySide6'} "
            f"（插入 sys.path[{insert_at}]，避免 pip 私有 Qt 与 fcitx5 冲突）"
        )

    for site in pip_sites:
        _log(f"已降级 pip/venv PySide6 路径: {site}")


def _try_warn_plugin_mismatch(pip_site: Path) -> None:
    """提示无法用简单 symlink 修复 ABI 不匹配。"""
    system_plugin = Path(
        "/usr/lib/qt6/plugins/platforminputcontexts/libfcitx5platforminputcontextplugin.so"
    )
    if system_plugin.exists():
        _log(
            f"系统存在 fcitx5 Qt6 插件: {system_plugin}，"
            f"但 pip PySide6 私有 Qt 与其 ABI 不兼容，链接无效。"
            f" pip site={pip_site}"
        )
    else:
        _log("系统未找到 fcitx5 Qt6 插件，请安装 fcitx5-qt / fcitx5-frontend-qt6")


def _log_im_diagnostics() -> None:
    """启动后可再调用；此处仅记录静态信息。"""
    fcitx_plugin = Path(
        "/usr/lib/qt6/plugins/platforminputcontexts/libfcitx5platforminputcontextplugin.so"
    )
    _log(
        f"fcitx5 进程={'是' if _process_running('fcitx5') else '否'}, "
        f"系统 fcitx5-qt 插件={'是' if fcitx_plugin.exists() else '否'} ({fcitx_plugin})"
    )
    which_fcitx = shutil.which("fcitx5") or shutil.which("fcitx")
    if which_fcitx:
        _log(f"fcitx 可执行文件: {which_fcitx}")


def ensure_game_im_env(env: dict | None = None) -> dict:
    """
    为 Minecraft / Java / GLFW 子进程补齐输入法环境。
    返回可直接传给 subprocess.Popen(env=...) 的字典。
    """
    out = dict(env) if env is not None else os.environ.copy()
    if not sys.platform.startswith("linux"):
        return out

    im = (out.get("QT_IM_MODULE") or _detect_im_module()).strip() or "fcitx"
    out["QT_IM_MODULE"] = im
    if im == "fcitx":
        out.setdefault("XMODIFIERS", "@im=fcitx")
        out.setdefault("GTK_IM_MODULE", "fcitx")
        out.setdefault("GLFW_IM_MODULE", "ibus")
    elif im == "ibus":
        out.setdefault("XMODIFIERS", "@im=ibus")
        out.setdefault("GTK_IM_MODULE", "ibus")
        out.setdefault("GLFW_IM_MODULE", "ibus")
    return out


def setup_linux_input_method() -> None:
    """
    Linux 输入法完整初始化入口。

    **必须**在 `import PySide6` 与 `QApplication(...)` 之前调用。
    """
    if not sys.platform.startswith("linux"):
        return
    try:
        _configure_im_env()
        _prefer_system_pyside6_for_fcitx()
        _log_im_diagnostics()
    except Exception as e:
        # 输入法初始化失败不应阻断启动
        _log(f"初始化失败（忽略，继续启动）: {e}")


def log_runtime_im_status() -> None:
    """
    在 QApplication 创建之后调用，记录实际加载的平台与输入法状态。
    """
    if not sys.platform.startswith("linux"):
        return
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QLibraryInfo

        app = QApplication.instance()
        if app is None:
            _log("QApplication 尚未创建，跳过运行时诊断")
            return

        plugins = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        im_dir = Path(plugins) / "platforminputcontexts"
        plugins_list = sorted(p.name for p in im_dir.iterdir()) if im_dir.is_dir() else []
        _log(f"Qt 平台: {app.platformName()}")
        _log(f"Qt 插件目录: {plugins}")
        _log(f"platforminputcontexts: {plugins_list}")
        has_fcitx = any("fcitx" in n for n in plugins_list)
        if not has_fcitx and os.environ.get("QT_IM_MODULE") == "fcitx":
            _log(
                "警告: QT_IM_MODULE=fcitx 但当前 Qt 插件目录无 fcitx 插件，"
                "输入法切换可能失败。请使用系统 python-pyside6 或安装 fcitx5-qt。"
            )
        else:
            _log(f"fcitx 插件可见: {has_fcitx}")
    except Exception as e:
        _log(f"运行时诊断失败: {e}")
