"""
Linux 输入法（fcitx5 / ibus）兼容层。

必须在 import PySide6 或创建 QApplication 之前调用 setup_linux_input_method()。

问题背景
--------
1. pip / venv 安装的 PySide6 会自带私有 Qt6，其中不包含
   libfcitx5platforminputcontextplugin.so。系统 fcitx5-qt 插件链接的是系统 Qt6，
   与 pip 私有 Qt ABI 不兼容，表现为无法切换中/英、无法输入中文。
   系统包 python-pyside6 使用系统 Qt6，与 fcitx5-qt 一致，可正常工作。

2. 在 Wayland 会话下，部分 Qt 应用走 wayland 平台插件时，fcitx5 切换快捷键
   与候选窗不可靠。历史修复：在有 XWayland（DISPLAY 可用）时强制 QT_QPA_PLATFORM=xcb。

3. 部分环境把 QT_IM_MODULE 设成 "fcitx5"，旧插件只认 "fcitx"；
   新 fcitx5-qt 虽同时注册两者，仍统一归一为 "fcitx" 以最大兼容。

本模块会：
1. 检测输入法守护进程并配置 QT_IM_MODULE / XMODIFIERS / GTK_IM_MODULE 等
2. Wayland 会话下优先切到 xcb（可用 BLORET_ALLOW_WAYLAND=1 取消）
3. 若检测到 pip 风格 PySide6，优先改用系统 python-pyside6
4. 输出诊断日志
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


def _normalize_im_module(name: str) -> str:
    """归一化输入法模块名。fcitx5 的 Qt 插件主键仍是 fcitx。"""
    n = (name or "").strip().lower()
    if n in ("fcitx5", "fcitx"):
        return "fcitx"
    if n in ("ibus", "ibus-x11"):
        return "ibus"
    return (name or "").strip()


def _detect_im_module() -> str:
    """
    选择合适的 QT_IM_MODULE 值。

    fcitx5 的 Qt 插件注册的 key 主要是 "fcitx"（也兼容 fcitx5）。
    """
    current = _normalize_im_module(os.environ.get("QT_IM_MODULE", ""))
    # 已显式指定有效模块时尊重用户设置（但 fcitx5 已归一）
    if current and current.lower() not in ("xim", "none", "compose", "qtvirtualkeyboard"):
        # 若用户写了奇怪值但 fcitx 在跑，仍优先 fcitx
        if current not in ("fcitx", "ibus"):
            pass
        else:
            return current

    xmodifiers = (os.environ.get("XMODIFIERS") or "").lower()
    gtk_im = _normalize_im_module(os.environ.get("GTK_IM_MODULE", "")).lower()

    if (
        _process_running("fcitx5")
        or _process_running("fcitx")
        or "fcitx" in xmodifiers
        or "fcitx" in gtk_im
        or current == "fcitx"
    ):
        return "fcitx"

    if (
        _process_running("ibus-daemon")
        or "ibus" in xmodifiers
        or "ibus" in gtk_im
        or current == "ibus"
    ):
        return "ibus"

    # 默认偏向 fcitx：国内桌面更常见；无效时 Qt 会回退到 compose
    return current or "fcitx"


def _is_wayland_session() -> bool:
    session = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    if session == "wayland":
        return True
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    platform = (os.environ.get("QT_QPA_PLATFORM") or "").lower()
    return platform.startswith("wayland")


def _prefer_xcb_for_im() -> None:
    """
    Wayland 会话下强制 Qt 走 XCB（XWayland），改善 fcitx 切换与候选窗。

    取消方式：
      export BLORET_ALLOW_WAYLAND=1
    或显式设置非 wayland 的 QT_QPA_PLATFORM（如 already xcb）。
    """
    allow = (os.environ.get("BLORET_ALLOW_WAYLAND") or "").strip().lower()
    if allow in ("1", "true", "yes", "on"):
        _log("BLORET_ALLOW_WAYLAND 已启用，不强制 xcb")
        return

    current = (os.environ.get("QT_QPA_PLATFORM") or "").strip()
    current_l = current.lower()

    # 用户已明确指定非 wayland 平台时不改
    if current_l and not current_l.startswith("wayland"):
        _log(f"保留用户 QT_QPA_PLATFORM={current!r}")
        return

    if not _is_wayland_session() and not current_l.startswith("wayland"):
        return

    # 无 X11 DISPLAY 时强切 xcb 会直接起不来
    if not os.environ.get("DISPLAY"):
        _log(
            "检测到 Wayland 会话但无 DISPLAY（可能没有 XWayland），"
            "无法强制 xcb；中文输入法切换可能仍有问题"
        )
        return

    os.environ["QT_QPA_PLATFORM"] = "xcb"
    _log(
        f"Wayland 会话下设置 QT_QPA_PLATFORM=xcb（原值={current!r}），"
        f"以修复 fcitx 中文输入法切换；取消请设 BLORET_ALLOW_WAYLAND=1"
    )


def _configure_im_env() -> None:
    """配置输入法相关环境变量（创建 QApplication 前生效）。"""
    im = _detect_im_module()
    prev_qt = os.environ.get("QT_IM_MODULE")
    prev_xmod = os.environ.get("XMODIFIERS")

    # 主动写入（不用 setdefault）：纠正错误的 fcitx5/ibus 混用配置
    os.environ["QT_IM_MODULE"] = im

    if im == "fcitx":
        os.environ["XMODIFIERS"] = "@im=fcitx"
        os.environ["GTK_IM_MODULE"] = "fcitx"
        os.environ["SDL_IM_MODULE"] = "fcitx"
        # GLFW / LWJGL（Minecraft）只认 ibus 模块名；fcitx5 提供 ibus 前端协议
        os.environ["GLFW_IM_MODULE"] = "ibus"
    elif im == "ibus":
        os.environ["XMODIFIERS"] = "@im=ibus"
        os.environ["GTK_IM_MODULE"] = "ibus"
        os.environ["SDL_IM_MODULE"] = "ibus"
        os.environ["GLFW_IM_MODULE"] = "ibus"

    _prefer_xcb_for_im()

    _log(
        f"输入法环境: QT_IM_MODULE={im}"
        f" (原值={prev_qt!r})"
        f", XMODIFIERS={os.environ.get('XMODIFIERS')!r} (原值={prev_xmod!r})"
        f", GTK_IM_MODULE={os.environ.get('GTK_IM_MODULE')!r}"
        f", SDL_IM_MODULE={os.environ.get('SDL_IM_MODULE')!r}"
        f", GLFW_IM_MODULE={os.environ.get('GLFW_IM_MODULE')!r}"
        f", QT_QPA_PLATFORM={os.environ.get('QT_QPA_PLATFORM')!r}"
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
    # 已 import 过则无法换实现，只能告警
    if "PySide6" in sys.modules:
        mod = sys.modules["PySide6"]
        _log(
            f"警告: PySide6 已在输入法初始化前被导入: {getattr(mod, '__file__', '?')}。"
            f" 若为 pip 私有 Qt，中文输入法可能仍无法切换。"
        )

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
        f"ibus 进程={'是' if _process_running('ibus-daemon') else '否'}, "
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

    im = _normalize_im_module(out.get("QT_IM_MODULE") or _detect_im_module()) or "fcitx"
    out["QT_IM_MODULE"] = im
    if im == "fcitx":
        out["XMODIFIERS"] = "@im=fcitx"
        out["GTK_IM_MODULE"] = "fcitx"
        out["SDL_IM_MODULE"] = "fcitx"
        out["GLFW_IM_MODULE"] = "ibus"
    elif im == "ibus":
        out["XMODIFIERS"] = "@im=ibus"
        out["GTK_IM_MODULE"] = "ibus"
        out["SDL_IM_MODULE"] = "ibus"
        out["GLFW_IM_MODULE"] = "ibus"
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
        from PySide6.QtGui import QGuiApplication

        app = QApplication.instance()
        if app is None:
            _log("QApplication 尚未创建，跳过运行时诊断")
            return

        plugins = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        im_dir = Path(plugins) / "platforminputcontexts"
        plugins_list = sorted(p.name for p in im_dir.iterdir()) if im_dir.is_dir() else []
        platform = app.platformName()
        _log(f"Qt 平台: {platform}")
        _log(f"Qt 插件目录: {plugins}")
        _log(f"platforminputcontexts: {plugins_list}")
        has_fcitx = any("fcitx" in n for n in plugins_list)
        qt_im = os.environ.get("QT_IM_MODULE")
        if not has_fcitx and qt_im in ("fcitx", "fcitx5"):
            _log(
                "警告: QT_IM_MODULE=fcitx 但当前 Qt 插件目录无 fcitx 插件，"
                "输入法切换可能失败。请使用系统 python-pyside6 并安装 fcitx5-qt。"
            )
        else:
            _log(f"fcitx 插件可见: {has_fcitx}")

        if platform == "wayland" and qt_im in ("fcitx", "fcitx5"):
            _log(
                "提示: 当前仍运行在 wayland 平台上；若无法切换中文输入法，"
                "请确认未设置 BLORET_ALLOW_WAYLAND=1，并存在 XWayland（DISPLAY）。"
            )

        try:
            im = QGuiApplication.inputMethod()
            if im is not None:
                _log(f"QInputMethod locale={im.locale().name()}, visible={im.isVisible()}")
        except Exception as e:
            _log(f"读取 QInputMethod 失败: {e}")

        # 打印实际加载的 PySide6 路径
        try:
            import PySide6

            _log(f"已加载 PySide6: {getattr(PySide6, '__file__', '?')}")
        except Exception:
            pass
    except Exception as e:
        _log(f"运行时诊断失败: {e}")


def diagnose_im() -> str:
    """返回可读的输入法诊断文本（调试/设置页可用）。"""
    lines = [
        f"platform={sys.platform}",
        f"QT_IM_MODULE={os.environ.get('QT_IM_MODULE')!r}",
        f"XMODIFIERS={os.environ.get('XMODIFIERS')!r}",
        f"GTK_IM_MODULE={os.environ.get('GTK_IM_MODULE')!r}",
        f"GLFW_IM_MODULE={os.environ.get('GLFW_IM_MODULE')!r}",
        f"QT_QPA_PLATFORM={os.environ.get('QT_QPA_PLATFORM')!r}",
        f"XDG_SESSION_TYPE={os.environ.get('XDG_SESSION_TYPE')!r}",
        f"WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY')!r}",
        f"DISPLAY={os.environ.get('DISPLAY')!r}",
        f"fcitx5_running={_process_running('fcitx5')}",
        f"ibus_running={_process_running('ibus-daemon')}",
    ]
    plugin = Path(
        "/usr/lib/qt6/plugins/platforminputcontexts/libfcitx5platforminputcontextplugin.so"
    )
    lines.append(f"system_fcitx_plugin={plugin.exists()} ({plugin})")
    try:
        import PySide6

        lines.append(f"PySide6={getattr(PySide6, '__file__', '?')}")
    except Exception as e:
        lines.append(f"PySide6=import_error:{e}")
    return "\n".join(lines)
