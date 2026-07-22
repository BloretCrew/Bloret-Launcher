import sys
import os
import faulthandler
from pathlib import Path

# Add the local directory to handle imports like 'import RinUI' correctly
# Handle both normal Python execution and Nuitka/PyInstaller bundling
def _get_script_dir():
    """获取脚本/应用程序目录，兼容不同的打包方式。

    Nuitka onefile 关键事实：
    - Nuitka 不设置 sys.frozen（只有 PyInstaller 设置）。
    - Nuitka 设置 sys.__nuitka_binary_dir，指向临时解压目录（数据文件所在）。
    - 主脚本 __file__ 在 onefile 下解析到临时解压目录，可用但语义不如
      sys.__nuitka_binary_dir 明确。
    """
    # Nuitka 编译模式（standalone / onefile）
    nuitka_binary_dir = getattr(sys, "__nuitka_binary_dir", None)
    if nuitka_binary_dir:
        return Path(nuitka_binary_dir)

    # PyInstaller with --onefile
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)

    # PyInstaller 其它模式（frozen 但无 _MEIPASS）：用 exe 所在目录
    if getattr(sys, 'frozen', False):
        return Path(sys.argv[0]).resolve().parent

    # Normal Python or Nuitka development mode
    # Use __file__ for source code execution
    return Path(__file__).resolve().parent

SCRIPT_DIR = _get_script_dir()

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# RinUI 现已通过 git 子模块引入：子模块根目录为 RinUI/，其中包含
# RinUI/RinUI/ 为真正的 Python 包。将子模块根目录加入 sys.path，
# 使得 import RinUI 能正确解析到嵌套的包路径。
_RINUI_SUBMODULE = SCRIPT_DIR / "RinUI"
if _RINUI_SUBMODULE.exists() and str(_RINUI_SUBMODULE) not in sys.path:
    sys.path.insert(0, str(_RINUI_SUBMODULE))

# Linux 输入法：必须在 import PySide6 / 创建 QApplication 之前完成
# （且尽量早于其它本地模块，避免提前 import 到 pip 私有 Qt）
# - pip/venv 私有 Qt 与系统 fcitx5 插件不兼容
# - Wayland 下强制 xcb，修复无法切换中文输入法
if sys.platform.startswith("linux"):
    from modules.linux_im import setup_linux_input_method, log_runtime_im_status
    setup_linux_input_method()
else:
    log_runtime_im_status = None  # type: ignore

# 服务器 IP：仅 import 模块，网络刷新延后到 UI 就绪（见 refresh_server_ip_async）
import modules.IP  # noqa: E402

# Create the QApplication early so it can be used in shims and module imports
from PySide6.QtWidgets import QApplication, QFileDialog, QSystemTrayIcon
from PySide6.QtCore import QLocale, Qt, QTranslator, QObject, Slot, Signal, Property, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QDesktopServices, QPixmap, QPainter, QCursor

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

app = QApplication(sys.argv)

if log_runtime_im_status is not None:
    log_runtime_im_status()


def _enable_fault_logging():
    """记录 Python/原生崩溃堆栈，避免仅看到退出码。"""
    try:
        try:
            from modules.platform_compat import datapath_default

            base = Path(datapath_default())
        except Exception:
            if sys.platform == "win32":
                base = Path(os.getenv("APPDATA", str(SCRIPT_DIR))) / "Bloret-Launcher"
            elif sys.platform == "darwin":
                base = Path.home() / "Library" / "Application Support" / "Bloret-Launcher"
            else:
                xdg = os.environ.get("XDG_DATA_HOME", "").strip()
                base = (
                    Path(xdg) / "Bloret-Launcher"
                    if xdg
                    else Path.home() / ".local" / "share" / "Bloret-Launcher"
                )
        log_dir = base / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        fault_path = log_dir / "python-faulthandler.log"

        stream = open(fault_path, "a", encoding="utf-8")
        stream.write("\n===== Bloret Launcher fault handler enabled =====\n")
        faulthandler.enable(file=stream, all_threads=True)
        return stream
    except Exception as e:
        print(f"Failed to enable faulthandler logging: {e}")
        return None


_FAULT_LOG_STREAM = _enable_fault_logging()

# --- Finished Full PySide6 Migration ---
# All modules have been refactored to use PySide6 and RinUI directly.

import RinUI
from RinUI import RinUIWindow
from RinUI.core.config import RINUI_PATH

import random
import threading
import subprocess
import json
import requests
import modules.config as cfg
import modules.globals as BLglobals
from modules.launch import Get_Run_Script
from modules.chafuwang import getServerData
from modules.i18n import i18nText
from modules.Bloriko import AskBloriko
import modules.web  # 保持 import 即启动 0.0.0.0:25252（本轮不改 Web 行为）
import modules.links as links
import socket
import send2trash
from modules.compat_widgets import Action, RoundMenu
from modules.log import log
import time
import logging
from modules.process_utils import hidden_process_kwargs


def get_app_icon_path(for_tray=False):
    """根据平台返回应用图标路径：macOS 使用 Bloret-Fluent.png；程序坞/标题栏使用带留白版本，托盘保留原始图标。"""
    if sys.platform == "darwin":
        mac_icon = SCRIPT_DIR / "Bloret-Fluent.png"
        if mac_icon.exists():
            if for_tray:
                return mac_icon

            # macOS 程序坞视觉尺寸修正：生成带透明留白的图标，避免看起来比其他应用更大
            padded_icon = SCRIPT_DIR / "cache" / "Bloret-Fluent-dock.png"
            try:
                src = QPixmap(str(mac_icon))
                if not src.isNull():
                    side = max(src.width(), src.height())
                    canvas = QPixmap(side, side)
                    canvas.fill(Qt.GlobalColor.transparent)

                    target_side = int(side * 0.84)
                    scaled = src.scaled(
                        target_side,
                        target_side,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )

                    painter = QPainter(canvas)
                    x = (side - scaled.width()) // 2
                    y = (side - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()

                    padded_icon.parent.mkdir(parents=True, exist_ok=True)
                    if canvas.save(str(padded_icon), "PNG"):
                        return padded_icon
            except Exception as e:
                print(f"Failed to generate padded mac icon: {e}")

            return mac_icon

    default_icon = SCRIPT_DIR / "bloret.ico"
    if default_icon.exists():
        return default_icon

    # 兜底：如果默认图标不存在，macOS 再尝试 fluent 图标
    fallback_mac_icon = SCRIPT_DIR / "Bloret-Fluent.png"
    if fallback_mac_icon.exists():
        return fallback_mac_icon

    return None

class Backend(QObject):
    """
    Python Backend to interact with QML.
    Later, we will migrate all Bloret-Launcher.py logic here.
    """
    modrinthResultsReceived = Signal(list)
    minecraftAccountsChanged = Signal(list, arguments=['accounts'])
    logsCleared = Signal()
    easytierStatusChanged = Signal(str, str)
    serverInfoChanged = Signal(dict)
    queryResultReceived = Signal(dict)
    blorikoResponseReceived = Signal(str)
    blorikoModSuggestionReceived = Signal(str, list)  # clean_text, slug_list
    blorikoModSuggestionStatus = Signal(str)  # 思考/工具过程
    blorikoModSuggestionChunk = Signal(str)  # 流式正文（累积）
    blorikoModSuggestionFailed = Signal(str)
    syncStatusChanged = Signal(str)
    languageChanged = Signal()
    downloadDialogRequested = Signal(str)
    downloadProgressUpdated = Signal(float, str, str, str, str)
    downloadDialogClosed = Signal()
    downloadCompleted = Signal(str)  # message — 安装完成时通知 UI
    downloadPaused = Signal(bool)
    coreManagerRequested = Signal(str, dict)
    mrpackExportRequested = Signal(str)
    activityInfoChanged = Signal(dict)
    downloadNotify = Signal(str, str, bool)
    launchDialogRequested = Signal(str)
    launchProgressUpdated = Signal(float, str, str)
    launchDialogClosed = Signal()
    runningInstancesChanged = Signal(list)
    updateAvailable = Signal(str, str, str)    # current_ver, latest_ver, update_text
    updateProgressUpdated = Signal(float, str)  # progress (0-1), status_text
    updateFailed = Signal(str)                  # error_message

    # BBBS signals
    bbbsSummaryReceived = Signal(dict)
    bbbsLeaderboardReceived = Signal(list)
    bbbsAllPostsReceived = Signal(list)
    bbbsErrorOccurred = Signal(str)

    # Live signals
    liveSpaceListReceived = Signal(list)
    
    # Minecraft Chat signal
    minecraftChatMessage = Signal(str, str)  # timestamp, message
    liveJoinedSpace = Signal(dict)
    liveLeftSpace = Signal()
    liveUserEvent = Signal(dict)
    liveChatMessageReceived = Signal(dict)
    liveSignalReceived = Signal(dict)
    liveErrorOccurred = Signal(str)
    liveConnectionStateChanged = Signal(str)
    liveEasyTierStateChanged = Signal(dict)

    # OOBE signals
    javaEnvironmentChecked = Signal(bool, str)  # installed, java_path
    javaInstallationComplete = Signal(str)      # java_path

    # Minecraft crash analysis signal
    minecraftCrashDetected = Signal(str, str, str)  # title, message, stack_trace

    # Version list signals
    versionListReady = Signal(str, list)  # category, versions
    versionListLoadFailed = Signal(str)  # error message
    playTimeTick = Signal()  # emitted every second while game is running
    statisticsUpdated = Signal()  # emitted when play statistics are updated

    # Global AI settings signal
    globalAIProviderChanged = Signal(str, str)  # provider_key, model_id

    # Resource Pack Editor signal
    resourcePackEditorRequested = Signal()

    # Backdrop/acrylic effect signal
    backdropEffectChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._server_info = {}
        self._activity_info = BLglobals.BL_Activity
        self._last_core_manager_request_time = 0  # 防止重复请求
        self._is_launching = False
        self._launch_session_id = 0
        self._launch_state_lock = threading.RLock()
        self._launch_start_lock = threading.Lock()
        self._launch_cancellation_event = None
        self._current_launching_version = ""  # 当前正在启动的版本
        self._screenshot_widget = None
        # Play time tracking
        self._play_time_sessions = {}  # instance_id -> session dict
        self._play_time_timer = None
        self._detailed_sessions = {}  # instance_id -> detailed session dict
        self._focus_monitor_thread = None
        self._focus_monitor_running = False
        # Live state
        self._live_sse_client = None
        self._live_webrtc_manager = None
        self._current_live_space_id = None
        self._current_live_space = {}
        self._current_live_easytier_state = {}
        self._current_live_easytier_merged_state = {}
        self._current_live_connection_state = "disconnected"
        self._live_easytier_publish_thread = None
        self._live_easytier_publish_running = False
        self._live_space_list_cache = []
        self._versions_cache = {}
        self._manifest_fetched = False
        self._version_prefetch_running = False
        self._version_prefetch_lock = threading.Lock()

    # ========== 全局 AI 供应商/模型设置 ==========

    @Slot(result=str)
    def getGlobalAIProvider(self):
        """获取全局 AI 供应商"""
        config_data = cfg.read()
        return config_data.get("ai_provider", "bloret_passport")

    @Slot(str)
    def setGlobalAIProvider(self, provider_key):
        """设置全局 AI 供应商"""
        try:
            config_data = cfg.read()
            config_data["ai_provider"] = provider_key
            cfg.write(config_data)
            model = config_data.get("ai_model", "default")
            self.globalAIProviderChanged.emit(provider_key, model)
            print(f"[AI] 全局供应商已设置为: {provider_key}, 当前模型: {model}")
        except Exception as e:
            print(f"Error saving global AI provider: {e}")

    @Slot(result=str)
    def getGlobalAIModel(self):
        """获取全局 AI 模型"""
        config_data = cfg.read()
        return config_data.get("ai_model", "default")

    @Slot(str)
    def setGlobalAIModel(self, model_id):
        """设置全局 AI 模型"""
        try:
            config_data = cfg.read()
            config_data["ai_model"] = model_id
            cfg.write(config_data)
            provider = config_data.get("ai_provider", "bloret_passport")
            self.globalAIProviderChanged.emit(provider, model_id)
            print(f"[AI] 全局模型已设置为: {model_id}, 当前供应商: {provider}")
        except Exception as e:
            print(f"Error saving global AI model: {e}")

    def setBackendParent(self, parent):
        self.parent = parent
        # 后台预加载版本列表，避免阻塞 UI
        self._prefetch_version_list()

    def _prefetch_version_list(self, force=False):
        """在后台线程中预加载版本列表，并在失败时通知 QML 结束加载状态。"""
        with self._version_prefetch_lock:
            if self._version_prefetch_running:
                print("[VersionList] 版本清单请求已在进行中，忽略重复请求")
                return
            if self._manifest_fetched and not force:
                print("[VersionList] 使用已缓存的版本清单")
                for category, versions in self._versions_cache.items():
                    self.versionListReady.emit(category, versions)
                return
            self._version_prefetch_running = True

        def _fetch():
            sources = [
                "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json",
                "https://launchermeta.mojang.com/mc/game/version_manifest.json",
            ]
            last_error = ""
            try:
                for api_url in sources:
                    try:
                        print(f"[VersionList] 正在获取版本清单: {api_url}")
                        response = requests.get(api_url, timeout=(8, 20))
                        response.raise_for_status()
                        data = response.json()
                        all_versions = data.get("versions", [])
                        if not isinstance(all_versions, list) or not all_versions:
                            raise ValueError("版本清单为空或格式不正确")

                        new_cache = {
                            "正式版本": [v["id"] for v in all_versions if v.get("type") == "release" and v.get("id")],
                            "快照版本": [v["id"] for v in all_versions if v.get("type") == "snapshot" and v.get("id")],
                            "远古版本": [v["id"] for v in all_versions if v.get("type") in ["old_alpha", "old_beta"] and v.get("id")],
                        }
                        self._versions_cache = new_cache
                        self._manifest_fetched = True
                        for category, versions in new_cache.items():
                            self.versionListReady.emit(category, versions)
                        print(f"[VersionList] 版本清单加载完成: {', '.join(f'{k}({len(v)})' for k, v in new_cache.items())}")
                        return
                    except Exception as source_error:
                        last_error = f"{api_url}: {source_error}"
                        print(f"[VersionList] 获取版本清单失败，尝试下一个来源: {last_error}")

                error_message = f"无法加载 Minecraft 版本列表：{last_error or '所有下载源均不可用'}"
                print(f"[VersionList] {error_message}")
                self.versionListLoadFailed.emit(error_message)
            finally:
                with self._version_prefetch_lock:
                    self._version_prefetch_running = False

        threading.Thread(target=_fetch, daemon=True, name="VersionManifestPrefetch").start()

    @Slot(result=bool)
    def handleWindowCloseRequest(self):
        parent = getattr(self, "parent", None)
        if parent and hasattr(parent, "handle_close_request_from_qml"):
            try:
                return bool(parent.handle_close_request_from_qml())
            except Exception as e:
                print(f"handleWindowCloseRequest failed: {e}")
        return False

    @Slot(result=str)
    def helloFromPython(self):
        return "Hello from PySide6 Backend!"

    @Slot(result=bool)
    def openResourcePackEditor(self):
        try:
            self.resourcePackEditorRequested.emit()
            return True
        except Exception as e:
            print(f"Failed to open ResourcePack Editor: {e}")
            return False
        
    @Slot(result=str)
    def getTips(self):
        if hasattr(BLglobals, "BLtips") and BLglobals.BLtips:
            return random.choice(BLglobals.BLtips)
        return "欢迎使用 Bloret Launcher！"

    @Slot(result=str)
    def getPlayerName(self):
        try:
            config_data = cfg.read()
            mc_account_config = config_data.get("MinecraftAccount", {})
            accounts_list = mc_account_config.get("accounts", [])
            chosen_index = mc_account_config.get("chosen", 0)
            if accounts_list and 0 <= chosen_index < len(accounts_list):
                return accounts_list[chosen_index].get("username", "访客")
        except Exception as e:
            print(f"Error reading player name: {e}")
        return "访客"
        
    @Slot(str)
    def launchGame(self, version):
        print(f"Requested to launch game: {version}")

        if self._is_launching:
            print("Launch request ignored: another launch is already in progress")
            return

        # 读取配置文件中的SkipFileCompletion选项
        try:
            import modules.config as cfg
            config_data = cfg.read()
            skip_completion = config_data.get("SkipFileCompletion", False)
        except Exception as e:
            print(f"Error reading SkipFileCompletion config: {e}")
            skip_completion = False

        if skip_completion:
            print("SkipFileCompletion is enabled, launching with skip_completion=True")
            self.launchGameWithSkip(version, skip_completion=True)
        else:
            print("SkipFileCompletion is disabled, launching with normal completion")
            self.launchGameWithSkip(version, skip_completion=False)

    @Slot(str, bool)
    def launchGameWithSkip(self, version, skip_completion=False):
        print(f"Requested to launch game with skip_completion={skip_completion}: {version}")

        if self._is_launching:
            print("Launch request ignored: another launch is already in progress")
            return

        # 插件钩子：launch.pre 可取消启动（registry + bus 统一派发）
        try:
            from modules.plugin_host.registry import get_registry
            cancel_reason = get_registry().launch_pre_cancel(version, {"skip_completion": skip_completion})
            if cancel_reason:
                print(f"[PluginHost] 启动被插件取消: {cancel_reason}")
                try:
                    from modules.notification import send_notification
                    send_notification(i18nText("启动已取消"), cancel_reason, category="launch")
                except Exception:
                    pass
                return
        except Exception as e:
            print(f"[PluginHost] launch.pre 失败: {e}")

        with self._launch_state_lock:
            self._is_launching = True
            self._launch_session_id += 1
            self._current_launching_version = version
            launch_session_id = self._launch_session_id
            cancellation_event = threading.Event()
            self._launch_cancellation_event = cancellation_event
        self.launchDialogRequested.emit(i18nText("正在启动 {version}").replace("{version}", version))

        def is_current_session():
            with self._launch_state_lock:
                return (
                    launch_session_id == self._launch_session_id
                    and self._launch_cancellation_event is cancellation_event
                    and not cancellation_event.is_set()
                )

        def emit_progress(progress, status, detail=""):
            if not is_current_session():
                return
            self.launchProgressUpdated.emit(float(progress), status, detail)

        def finish_launch(close_dialog=False):
            if not is_current_session():
                print(f"[Launch] 忽略已失效启动会话的清理请求: session={launch_session_id}, version={version}")
                return
            with self._launch_state_lock:
                self._is_launching = False
                self._current_launching_version = ""
                if self._launch_cancellation_event is cancellation_event:
                    self._launch_cancellation_event = None
            print(f"[Launch] 启动任务已清理: session={launch_session_id}, version={version}, close_dialog={close_dialog}")
            if close_dialog:
                self.launchDialogClosed.emit()

        def abort_if_cancelled(stage):
            if is_current_session():
                return False
            print(f"[Launch] 启动会话已取消，停止后续流程: session={launch_session_id}, version={version}, stage={stage}")
            return True

        def run_launch():
            try:
                from modules.Bloret_PassPort import refresh_minecraft_token, sync_bloret_passport_account_to_mc
                from modules.launch import monitor_minecraft_window

                emit_progress(5, f"正在准备启动环境: {version}", "")

                # Passport：仅在已登录且当前账户为 Microsoft 时刷新/同步；离线或未登录直接跳过
                need_passport = False
                try:
                    _cfg = cfg.read()
                    passport_login = bool(_cfg.get("Bloret_PassPort_Login"))
                    mc_acc = _cfg.get("MinecraftAccount") or {}
                    accounts = mc_acc.get("accounts") or []
                    chosen = int(mc_acc.get("chosen", 0) or 0)
                    current_acc = accounts[chosen] if accounts and 0 <= chosen < len(accounts) else {}
                    acc_type = (current_acc.get("type") or "Offline") if isinstance(current_acc, dict) else "Offline"
                    need_passport = passport_login and str(acc_type) == "Microsoft"
                except Exception as _passport_check_err:
                    print(f"[Launch] Passport 预检失败，将尝试同步: {_passport_check_err}")
                    need_passport = True

                if need_passport:
                    emit_progress(20, "正在向 Bloret PassPort 刷新令牌...", "")
                    refresh_ok = refresh_minecraft_token()
                    if abort_if_cancelled("refresh_token"):
                        return
                    if refresh_ok:
                        emit_progress(35, "令牌刷新完成", "")
                    else:
                        emit_progress(35, "令牌刷新未完成，继续同步档案...", "")

                    emit_progress(50, "正在重新获取 Minecraft 档案数据...", "")
                    sync_ok = sync_bloret_passport_account_to_mc(parent_window=None)
                    if abort_if_cancelled("sync_profile"):
                        return
                    if sync_ok:
                        self.minecraftAccountsChanged.emit([])
                        emit_progress(65, "档案数据更新完成", "")
                    else:
                        emit_progress(65, "档案同步失败，将使用本地缓存档案", "")
                else:
                    emit_progress(65, "跳过在线账户同步（离线/未登录）", "")

                if skip_completion:
                    emit_progress(80, "跳过文件补全，直接解析启动参数...", "用户选择跳过文件补全")
                else:
                    emit_progress(80, "正在补全文件并解析启动参数...", "如有缺失文件会自动下载")
                launch_args, game_dir = Get_Run_Script(
                    version,
                    skip_completion=skip_completion,
                    cancellation_event=cancellation_event,
                )
                if abort_if_cancelled("resolve_launch_args"):
                    return

                emit_progress(95, "正在执行启动命令...", "")
                print(f"[Launch] 启动参数已生成，共 {len(launch_args)} 项（敏感值不输出）")

                # Linux：为 Minecraft/GLFW 继承并补齐输入法环境，保证游戏内可切换中文输入
                _launch_env = None
                if sys.platform.startswith("linux"):
                    try:
                        from modules.linux_im import ensure_game_im_env
                        _launch_env = ensure_game_im_env()
                        print(
                            f"[IM] 游戏进程输入法环境: "
                            f"QT_IM_MODULE={_launch_env.get('QT_IM_MODULE')}, "
                            f"GLFW_IM_MODULE={_launch_env.get('GLFW_IM_MODULE')}, "
                            f"XMODIFIERS={_launch_env.get('XMODIFIERS')}"
                        )
                    except Exception as _im_err:
                        print(f"[IM] 游戏输入法环境准备失败（继续启动）: {_im_err}")

                # 插件钩子：合并环境变量
                try:
                    from modules.plugin_host.registry import get_registry
                    base_env = dict(_launch_env) if _launch_env else dict(os.environ)
                    merged_env = get_registry().collect_env(version, base_env)
                    if merged_env and merged_env != base_env:
                        _launch_env = merged_env
                        print(f"[PluginHost] 已合并插件环境变量 keys={list(merged_env.keys())[:8]}...")
                except Exception as _env_err:
                    print(f"[PluginHost] launch.env 失败: {_env_err}")

                # 最终会话校验与 Popen 在同一把锁内串行化；取消操作也取得此锁，
                # 从而消除“检查通过后、Popen 前”被取消的竞态。
                with self._launch_start_lock:
                    if abort_if_cancelled("before_process_start"):
                        return
                    proc = subprocess.Popen(
                        launch_args, cwd=game_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding='utf-8',
                        errors='replace',
                        bufsize=1,
                        env=_launch_env,
                        **hidden_process_kwargs(),
                    )
                    print(f"[Launch] Popen 已完成: session={launch_session_id}, pid={proc.pid}")

                import uuid as _uuid
                instance_id = str(_uuid.uuid4())
                BLglobals.running_instances[instance_id] = {
                    "name": version, "type": "minecraft",
                    "pid": proc.pid, "suspended": False
                }
                try:
                    from modules.plugin_host.dispatch import invoke_hook
                    invoke_hook("launch.post", version, proc.pid)
                    print(f"[PluginHost] launch.post version={version} pid={proc.pid}")
                except Exception as _post_err:
                    print(f"[PluginHost] launch.post 失败: {_post_err}")
                # Start play time tracking
                from modules.play_time import start_session, start_detailed_session
                self._play_time_sessions[instance_id] = start_session(version)
                self._detailed_sessions[instance_id] = start_detailed_session(version)
                self._start_play_time_tick()
                self._start_focus_monitor()
                self._recordRecentRun(version, "minecraft")
                self.runningInstancesChanged.emit(self.getRunningInstances())

                emit_progress(97, "启动命令已执行，正在等待 Minecraft 窗口出现...", "")

                # 添加后台线程实时监控日志输出，解析聊天消息并打印到控制台
                def monitor_process_output(p, ver, evt):
                    try:
                        import re
                        # 匹配聊天消息的正则表达式
                        # 格式: [13:01:18] [Render thread/INFO]: [System] [CHAT] 霕 Detritalw: xx
                        # 注意中间有冒号分隔符
                        chat_pattern = r'\[([^\]]+)\]\s*\[[^\]]+\]:\s*(?:\[System\]\s*)?\[CHAT\]\s*(.*)'

                        for line in p.stdout:
                            if not line:
                                break

                            # 实时打印到控制台
                            print(line, end='', flush=True)

                            # 尝试匹配聊天消息
                            match = re.search(chat_pattern, line)
                            if match:
                                timestamp = match.group(1)
                                chat_message = match.group(2).strip()
                                if chat_message:
                                    # 清理乱码字符（替换无效字符）
                                    chat_message = chat_message.replace('\ufffd', '')
                                    # 发送聊天消息信号
                                    self.minecraftChatMessage.emit(timestamp, chat_message)
                                    print(f"[聊天] {timestamp} - {chat_message}")  # 调试输出

                                    # 当 Minecraft 窗口不在前台时发送 Windows 通知
                                    self._notify_if_not_foreground(timestamp, chat_message)

                        # 进程结束后检查
                        p.wait()
                        # End play time tracking
                        self._end_play_time_session(instance_id)
                        exited_before_window = not evt.is_set()
                        crashed = bool(p.returncode not in (0, None))
                        try:
                            from modules.plugin_host.dispatch import invoke_hook
                            invoke_hook(
                                "launch.exit",
                                ver,
                                p.pid,
                                p.returncode,
                                crashed,
                            )
                            print(
                                f"[PluginHost] launch.exit version={ver} pid={p.pid} "
                                f"code={p.returncode} crashed={crashed}"
                            )
                        except Exception as _exit_err:
                            print(f"[PluginHost] launch.exit 失败: {_exit_err}")
                        if exited_before_window:
                            evt.set()
                            emit_progress(
                                100,
                                i18nText("Minecraft 进程已退出"),
                                i18nText("游戏在窗口出现前退出，返回码: {code}").replace("{code}", str(p.returncode)),
                            )
                            finish_launch(close_dialog=False)
                            print(
                                f"[Launch] Minecraft 在窗口出现前退出，已立即结束等待: "
                                f"version={ver}, pid={p.pid}, returncode={p.returncode}"
                            )
                        if p.returncode != 0 and exited_before_window:
                            print(f"\n[错误] Minecraft {ver} 进程异常退出，返回码: {p.returncode}")
                            self.minecraftCrashDetected.emit(
                                i18nText("Minecraft {ver} 崩溃").replace("{ver}", ver),
                                i18nText("进程异常退出 (返回码: {code})\n请查看上面的日志输出").replace("{code}", str(p.returncode)),
                                i18nText("进程异常退出，返回码: {code}").replace("{code}", str(p.returncode)),
                            )
                            try:
                                from modules.notification import send_notification
                                send_notification(
                                    i18nText("Minecraft {ver} 崩溃").replace("{ver}", ver),
                                    i18nText("进程异常退出，返回码: {code}").replace("{code}", str(p.returncode)),
                                    category="launch_error",
                                )
                            except Exception:
                                pass
                    except Exception as e:
                        print(f"[错误] 监控进程输出时发生异常: {e}")

                window_found_event = threading.Event()
                threading.Thread(
                    target=monitor_process_output,
                    args=(proc, version, window_found_event),
                    daemon=True
                ).start()

                def on_window_found():
                    if window_found_event.is_set():
                        return
                    window_found_event.set()
                    emit_progress(100, i18nText("已检测到 Minecraft 窗口，启动完成"), "")
                    finish_launch(close_dialog=True)
                    try:
                        from modules.notification import send_notification
                        send_notification(
                            i18nText("Minecraft 已就绪"),
                            i18nText("Minecraft {version} 启动完成").replace("{version}", version),
                            category="launch_ready",
                        )
                    except Exception:
                        pass

                # 传入 proc.pid 以便监控进程退出并自动隐藏工具条
                monitor_minecraft_window(version, callback=on_window_found, mc_pid=proc.pid)

                def monitor_timeout_guard():
                    if window_found_event.wait(310):
                        return
                    emit_progress(
                        100,
                        i18nText("等待 Minecraft 窗口超时"),
                        i18nText("未检测到窗口，你可以继续后台等待或关闭此对话框后重试"),
                    )
                    finish_launch(close_dialog=False)
                    try:
                        from modules.notification import send_notification
                        send_notification(
                            i18nText("启动超时"),
                            i18nText("Minecraft {version} 窗口等待超时，请手动检查").replace("{version}", version),
                            category="launch_error",
                        )
                    except Exception:
                        pass

                threading.Thread(target=monitor_timeout_guard, daemon=True).start()
            except Exception as e:
                if cancellation_event.is_set() or not is_current_session():
                    print(f"[Launch] 已取消的启动会话结束: session={launch_session_id}, version={version}, reason={e}")
                    return
                print(f"Failed to launch: {e}")
                import traceback
                tb_str = traceback.format_exc()
                traceback.print_exc()
                emit_progress(100, i18nText("启动失败: {error}").replace("{error}", str(e)), "")
                finish_launch(close_dialog=False)
                self.minecraftCrashDetected.emit(
                    i18nText("启动失败"),
                    str(e),
                    tb_str
                )
                try:
                    from modules.notification import send_notification
                    send_notification(i18nText("启动失败"), str(e), category="launch_error")
                except Exception:
                    pass

        threading.Thread(target=run_launch, daemon=True).start()

    @Slot()
    def skipCurrentLaunchCompletion(self):
        """跳过当前启动的文件补全过程"""
        if not self._is_launching:
            print("No launch in progress to skip completion")
            return
        
        version = self._current_launching_version
        if not version:
            print("No version to skip completion for")
            return
        
        print(f"[Launch] 用户请求跳过文件补全: version={version}, session={self._launch_session_id}")
        # 真实取消旧会话及正在进行的 LibraryDownloader，然后启动跳过补全的新会话。
        with self._launch_start_lock:
            with self._launch_state_lock:
                if self._launch_cancellation_event is not None:
                    self._launch_cancellation_event.set()
                self._launch_session_id += 1
                self._is_launching = False
                self._current_launching_version = ""
                self._launch_cancellation_event = None
        self.launchDialogClosed.emit()
        self.launchGameWithSkip(version, skip_completion=True)

    @Slot()
    def cancelCurrentLaunch(self):
        """取消当前启动会话，并立即释放启动按钮状态。"""
        if not self._is_launching:
            print("[Launch] 忽略取消请求：当前没有启动任务")
            self._current_launching_version = ""
            self.launchDialogClosed.emit()
            return

        version = self._current_launching_version
        cancelled_session = self._launch_session_id
        # 与最终 Popen 使用同一把锁：若尚未启动则可靠阻止；若 Popen 正在执行则等待其完成。
        with self._launch_start_lock:
            with self._launch_state_lock:
                if self._launch_cancellation_event is not None:
                    self._launch_cancellation_event.set()
                self._launch_session_id += 1
                self._is_launching = False
                self._current_launching_version = ""
                self._launch_cancellation_event = None
        self.launchDialogClosed.emit()
        print(
            f"[Launch] 用户已取消启动任务: version={version}, "
            f"session={cancelled_session}, next_session={self._launch_session_id}"
        )

    # ========== 聊天记录持久化 ==========

    _chat_history_path = os.path.join(BLglobals.datapath, 'chat_history.json')

    def _readChatFile(self):
        """读取整个聊天历史文件"""
        try:
            if os.path.exists(self._chat_history_path):
                with open(self._chat_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取聊天历史失败: {e}")
        return {}

    def _writeChatFile(self, data):
        """写入整个聊天历史文件"""
        try:
            os.makedirs(os.path.dirname(self._chat_history_path), exist_ok=True)
            with open(self._chat_history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入聊天历史失败: {e}")

    @Slot(str, str)
    def saveChatHistory(self, version, messagesJson):
        """保存某个版本的聊天记录"""
        try:
            all_history = self._readChatFile()
            all_history[version] = json.loads(messagesJson)
            self._writeChatFile(all_history)
        except Exception as e:
            print(f"saveChatHistory 失败: {e}")

    @Slot(str, result=str)
    def loadChatHistory(self, version):
        """加载聊天记录，version 为 'all' 时返回全部，否则返回指定版本"""
        try:
            all_history = self._readChatFile()
            if version == "all":
                return json.dumps(all_history)
            return json.dumps(all_history.get(version, []))
        except Exception as e:
            print(f"loadChatHistory 失败: {e}")
            return "{}" if version == "all" else "[]"

    _recent_runs_path = os.path.join(BLglobals.datapath, 'recent_runs.json')

    def _notify_if_not_foreground(self, timestamp, message):
        """当 Minecraft 窗口不在前台时发送系统通知"""
        try:
            if self._is_minecraft_foreground():
                return

            from modules.notification import send_notification
            threading.Thread(
                target=lambda t, b: send_notification(t, b, category="chat_message"),
                args=('Minecraft 聊天消息', f'{timestamp} {message}'),
                daemon=True,
            ).start()
        except Exception:
            pass

    def _recordRecentRun(self, name, run_type):
        """记录最近运行的项目"""
        from datetime import datetime
        try:
            recent = []
            if os.path.exists(self._recent_runs_path):
                with open(self._recent_runs_path, 'r', encoding='utf-8') as f:
                    recent = json.load(f)
            # 移除同名旧记录
            recent = [r for r in recent if r.get("name") != name]
            # 插入到最前面
            recent.insert(0, {
                "name": name,
                "type": run_type,
                "lastRun": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            # 最多保留 20 条
            recent = recent[:20]
            os.makedirs(os.path.dirname(self._recent_runs_path), exist_ok=True)
            with open(self._recent_runs_path, 'w', encoding='utf-8') as f:
                json.dump(recent, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录最近运行失败: {e}")

    @Slot(result=list)
    def getRecentRuns(self):
        """获取最近运行的项目列表"""
        try:
            if os.path.exists(self._recent_runs_path):
                with open(self._recent_runs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取最近运行失败: {e}")
        return []

    # ========== 游戏时间 ==========

    def _start_play_time_tick(self):
        """Start a 1-second timer that emits playTimeTick"""
        from PySide6.QtCore import QTimer
        if self._play_time_timer is not None:
            return
        self._play_time_timer = QTimer()
        self._play_time_timer.timeout.connect(self.playTimeTick.emit)
        self._play_time_timer.start(1000)

    def _stop_play_time_tick(self):
        """Stop the tick timer when no sessions are active"""
        if self._play_time_timer and not self._play_time_sessions:
            self._play_time_timer.stop()
            self._play_time_timer = None

    def _end_play_time_session(self, instance_id):
        """End a play time session and accumulate to total"""
        session = self._play_time_sessions.pop(instance_id, None)
        if session:
            from modules.play_time import end_session
            end_session(session)
        detailed = self._detailed_sessions.pop(instance_id, None)
        if detailed:
            from modules.play_time import end_detailed_session
            end_detailed_session(detailed)
            self.statisticsUpdated.emit()
        if not self._play_time_sessions and not self._detailed_sessions:
            self._stop_focus_monitor()
        self._stop_play_time_tick()

    @Slot(result=dict)
    def getAllPlayTimes(self):
        from modules.play_time import get_all_play_times
        return get_all_play_times()

    @Slot(str, result=float)
    def getPlayTime(self, versionName):
        from modules.play_time import get_total_play_time
        return get_total_play_time(versionName)

    @Slot(str, result=str)
    def getPlayTimeFormatted(self, versionName):
        from modules.play_time import get_total_play_time, format_duration_long
        return format_duration_long(get_total_play_time(versionName))

    @Slot(result=str)
    def getSessionPlayTimeFormatted(self):
        """Get current session elapsed time for the first running instance"""
        import time
        from modules.play_time import format_duration_long
        if not self._play_time_sessions:
            return ""
        session = next(iter(self._play_time_sessions.values()), None)
        if session and session.get("start"):
            elapsed = time.time() - session["start"]
            return format_duration_long(elapsed)
        return ""

    # ========== Focus monitoring for foreground/background time ==========

    def _start_focus_monitor(self):
        if self._focus_monitor_running:
            return
        self._focus_monitor_running = True
        self._focus_monitor_thread = threading.Thread(target=self._focus_monitor_loop, daemon=True)
        self._focus_monitor_thread.start()

    def _stop_focus_monitor(self):
        self._focus_monitor_running = False

    def _focus_monitor_loop(self):
        import time
        while self._focus_monitor_running:
            try:
                is_fg = self._is_minecraft_foreground()
                for sid, session in list(self._detailed_sessions.items()):
                    from modules.play_time import update_session_focus
                    update_session_focus(session, is_fg)
            except Exception:
                pass
            time.sleep(2)

    @staticmethod
    def _is_minecraft_foreground():
        try:
            if sys.platform == 'win32':
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd:
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
                    buf = ctypes.create_unicode_buffer(length)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length)
                    title = buf.value.lower()
                    return 'minecraft' in title
            elif sys.platform == 'darwin':
                import subprocess
                result = subprocess.run(
                    ['osascript', '-e', 'tell application "System Events" to get name of first application process whose frontmost is true'],
                    capture_output=True, text=True, timeout=3
                )
                return 'minecraft' in result.stdout.lower()
            else:
                import subprocess
                # 尝试 xdotool (X11)
                try:
                    result = subprocess.run(
                        ['xdotool', 'getactivewindow', 'getwindowname'],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return 'minecraft' in result.stdout.lower()
                except FileNotFoundError:
                    pass
                # 回退: wmctrl 列出窗口，检查是否有可见的 Minecraft 窗口
                try:
                    result = subprocess.run(
                        ['wmctrl', '-l'],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0:
                        for line in result.stdout.strip().splitlines():
                            if 'minecraft' in line.lower():
                                return True
                except FileNotFoundError:
                    pass
                return False
        except Exception:
            pass
        return False

    # ========== Statistics Slots ==========

    @Slot(result=dict)
    def getPlayStatisticsOverview(self):
        from modules.play_time import get_overview_stats
        return get_overview_stats()

    @Slot(str, result=list)
    def getPlayStatisticsByDate(self, date):
        from modules.play_time import get_sessions
        result = get_sessions(date_filter=date, page=1, page_size=1000)
        return result.get("sessions", [])

    @Slot(str, result=list)
    def getPlayStatisticsByVersion(self, version):
        from modules.play_time import get_sessions
        result = get_sessions(version_filter=version, page=1, page_size=1000)
        return result.get("sessions", [])

    @Slot(str, str, int, int, result=dict)
    def getPlayStatisticsPaginated(self, dateFilter, versionFilter, page, pageSize):
        from modules.play_time import get_sessions
        return get_sessions(
            date_filter=dateFilter if dateFilter else None,
            version_filter=versionFilter if versionFilter else None,
            page=page,
            page_size=pageSize,
        )

    @Slot(str, str, result=list)
    def getPlayStatisticsDaily(self, dateFrom, dateTo):
        from modules.play_time import get_daily_stats
        return get_daily_stats(
            date_from=dateFrom if dateFrom else None,
            date_to=dateTo if dateTo else None,
        )

    @Slot(result=list)
    def getPlayStatisticsVersions(self):
        from modules.play_time import get_version_stats
        return get_version_stats()

    @Slot(result=list)
    def getPlayStatisticsDates(self):
        from modules.play_time import get_all_dates
        return get_all_dates()

    @Slot(result=list)
    def getPlayStatisticsAllVersions(self):
        from modules.play_time import get_all_versions
        return get_all_versions()

    @Slot(float, result=str)
    def formatPlayTime(self, seconds):
        from modules.play_time import format_duration_full
        return format_duration_full(seconds)

    @Slot(result=list)
    def getLaunchItemsSortedByPlayTime(self):
        """Get launch items sorted by total play time (descending)"""
        from modules.setup_ui import get_all_launch_items
        from modules.play_time import get_all_play_times, format_duration
        items = get_all_launch_items()
        times = get_all_play_times()
        qml_items = []
        for item in items:
            icon_path = "../../icon/Grass_Block.png"
            if item.get("type") == "custom":
                icon_path = "../../icon/exeapps.png"
            total = times.get(item["name"], 0)
            qml_items.append({
                "name": item["name"],
                "type": item["type"],
                "path": item["path"],
                "icon": icon_path,
                "playTime": total,
                "playTimeFormatted": format_duration(total),
            })
        qml_items.sort(key=lambda x: x.get("playTime", 0), reverse=True)
        return qml_items

    @Slot(result=list)
    def getRunningInstances(self):
        import psutil
        dead = [k for k, v in BLglobals.running_instances.items() if not psutil.pid_exists(v["pid"])]
        for k in dead:
            self._end_play_time_session(k)
            del BLglobals.running_instances[k]
        return [{"id": k, **v} for k, v in BLglobals.running_instances.items()]

    @Slot(str)
    def suspendInstance(self, instance_id):
        import psutil
        entry = BLglobals.running_instances.get(instance_id)
        if not entry or not psutil.pid_exists(entry["pid"]):
            return
        pid = entry["pid"]
        try:
            import platform as _platform
            if _platform.system() == "Windows":
                import ctypes
                handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
                if entry["suspended"]:
                    ctypes.windll.ntdll.NtResumeProcess(handle)
                else:
                    ctypes.windll.ntdll.NtSuspendProcess(handle)
                ctypes.windll.kernel32.CloseHandle(handle)
            else:
                import signal as _signal
                import os as _os
                _os.kill(pid, _signal.SIGCONT if entry["suspended"] else _signal.SIGSTOP)
            entry["suspended"] = not entry["suspended"]
            self.runningInstancesChanged.emit(self.getRunningInstances())
        except Exception as e:
            print(f"suspendInstance failed: {e}")

    @Slot(str)
    def terminateInstance(self, instance_id):
        import psutil
        entry = BLglobals.running_instances.pop(instance_id, None)
        self._end_play_time_session(instance_id)
        if entry and psutil.pid_exists(entry["pid"]):
            try:
                psutil.Process(entry["pid"]).kill()
            except Exception as e:
                print(f"terminateInstance failed: {e}")
        self.runningInstancesChanged.emit(self.getRunningInstances())

    @Slot(result=bool)
    def isMinecraftToolVisible(self):
        from modules import mwtool
        return mwtool.is_tool_visible()

    @Slot()
    def toggleMinecraftTool(self):
        from modules import mwtool
        if mwtool.is_tool_visible():
            mwtool.hide_minecraft_tool()

    @Slot(result=dict)
    def getActivityInfo(self):
        return BLglobals.BL_Activity

    @Slot()
    def refreshActivityInfo(self):
        """从 API 刷新活动信息"""
        from modules.BLServer import get_latest_version
        def update_activity():
            try:
                _, _ = get_latest_version()
                # BL_Activity 已在 get_latest_version 中更新
                # 如果图标是远程 URL，则下载缓存到本地文件
                icon_url = BLglobals.BL_Activity.get("icon", "")
                if icon_url.startswith("http"):
                    try:
                        import requests, hashlib
                        from PySide6.QtCore import QUrl
                        resp = requests.get(icon_url, timeout=5)
                        if resp.status_code == 200:
                            # compute hash for filename
                            h = hashlib.md5(icon_url.encode('utf-8')).hexdigest()
                            cache_dir = os.path.join(SCRIPT_DIR, "cache")
                            os.makedirs(cache_dir, exist_ok=True)
                            local_path = os.path.join(cache_dir, f"activity_{h}.png")
                            with open(local_path, "wb") as imgf:
                                imgf.write(resp.content)
                            # convert to file URL for QML
                            url = QUrl.fromLocalFile(local_path).toString()
                            BLglobals.BL_Activity["icon"] = url
                            icon_path = url
                        else:
                            icon_path = icon_url
                    except Exception as e:
                        print(f"Failed to download activity icon: {e}")
                        icon_path = icon_url
                else:
                    # non-http value might be local path; convert to file URL too
                    from PySide6.QtCore import QUrl
                    if icon_url:
                        BLglobals.BL_Activity["icon"] = QUrl.fromLocalFile(icon_url).toString()
                        icon_path = QUrl.fromLocalFile(icon_url).toString()
                # else icon_path remains whatever returned
                self._activity_info = BLglobals.BL_Activity
                self.activityInfoChanged.emit(self._activity_info)
            except Exception as e:
                print(f"Error refreshing activity info: {e}")
        
        threading.Thread(target=update_activity, daemon=True).start()

    @Slot()
    def refreshServerInfo(self):
        def update_callback(data):
            self._server_info = data
            self.serverInfoChanged.emit(data)
        getServerData("Bloret", callback=update_callback)

    @Slot(result=list)
    def getLaunchItems(self):
        from modules.setup_ui import get_all_launch_items
        items = get_all_launch_items()
        qml_items = []
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"getLaunchItems: Retrieved {len(items)} items from get_all_launch_items()")
        
        for item in items:
            # Extract icon path from item
            icon_path = "../../icon/Grass_Block.png"  # Default
            
            if item.get("type") == "minecraft":
                # For minecraft, check if we have metadata with custom icon
                # Default to Grass_Block for minecraft
                icon_path = "../../icon/Grass_Block.png"
                
            elif item.get("type") == "custom":
                # For custom apps, use a generic app icon
                icon_path = "../../icon/exeapps.png"
            
            qml_item = {
                "name": item["name"],
                "type": item["type"],
                "path": item["path"],
                "icon": icon_path
            }
            
            logger.debug(f"getLaunchItems: Added item {qml_item}")
            qml_items.append(qml_item)
        
        logger.debug(f"getLaunchItems: Returning {len(qml_items)} items to QML")
        return qml_items

    @Slot(str)
    def selectLaunchItem(self, name):
        try:
            config_data = cfg.read()
            config_data['ChoosedRun'] = name
            cfg.write(config_data)
            print(f"[Home] Selected launch item: {name}")
        except Exception as e:
            print(f"Error selecting launch item: {e}")

    @Slot(result=str)
    def getSelectedLaunchItem(self):
        """读取配置中保存的核心选择，若不存在则返回空字符串"""
        try:
            config_data = cfg.read()
            return config_data.get('ChoosedRun', '')
        except Exception as e:
            print(f"Error reading selected launch item: {e}")
            return ''

    @Slot(str)
    def openVersionFolder(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_path = os.path.join(minecraft_dir, "versions", versionName)
            if os.path.exists(version_path):
                if sys.platform == 'win32':
                    os.startfile(version_path)
                else:
                    subprocess.Popen(['xdg-open', version_path])
            else:
                print(f"Version folder not found: {version_path}")
        except Exception as e:
            print(f"Error opening version folder: {e}")

    @Slot(str, result='QVariantMap')
    def getMrpackInstanceInfo(self, versionName):
        """获取实例信息用于导出对话框"""
        try:
            from modules.mrpack_export import get_instance_info
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            instance_path = os.path.join(minecraft_dir, "versions", versionName)
            if not os.path.exists(instance_path):
                return {}
            info = get_instance_info(instance_path)
            return info if info else {}
        except Exception as e:
            print(f"获取实例信息失败：{e}")
            return {}

    @Slot(str, str, str, str, result=bool)
    def doExportMrpack(self, versionName, packName, packVersion, outputPath):
        """执行 Modrinth 整合包导出"""
        try:
            from modules.mrpack_export import export_to_mrpack
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            instance_path = os.path.join(minecraft_dir, "versions", versionName)
            if not outputPath.endswith('.mrpack'):
                outputPath += '.mrpack'
            summary = f"从 {versionName} 导出的整合包"
            return export_to_mrpack(instance_path, outputPath, packName, packVersion, summary)
        except Exception as e:
            print(f"导出整合包失败：{e}")
            import traceback
            traceback.print_exc()
            return False

    @Slot(str, str, str, result=str)
    def selectSaveFile(self, caption, defaultName, fileFilter):
        """显示保存文件对话框，返回选择的路径"""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(None, caption, defaultName, fileFilter)
        return path or ""

    @Slot(str, str)
    def openSubFolder(self, versionName, subPath):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            base_path = os.path.join(minecraft_dir, "versions", versionName)
            target_path = os.path.join(base_path, subPath)
            
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)

            if sys.platform == 'win32':
                os.startfile(target_path)
            else:
                subprocess.Popen(['xdg-open', target_path])
        except Exception as e:
            print(f"Error opening sub folder: {e}")

    @Slot(str)
    def deleteCustomItem(self, name):
        try:
            if name in BLglobals.customize_list:
                BLglobals.customize_list.remove(name)
                config_data = cfg.read()
                config_data['customize_list'] = BLglobals.customize_list
                cfg.write(config_data)
                print(f"Deleted custom item: {name}")
        except Exception as e:
            print(f"Error deleting custom item: {e}")

    @Slot(str, str)
    def renameCustomItem(self, oldName, newName):
        try:
            if oldName in BLglobals.customize_list:
                idx = BLglobals.customize_list.index(oldName)
                BLglobals.customize_list[idx] = newName
                config_data = cfg.read()
                config_data['customize_list'] = BLglobals.customize_list
                if config_data.get('ChoosedRun') == oldName:
                    config_data['ChoosedRun'] = newName
                cfg.write(config_data)
                print(f"Renamed custom item: {oldName} -> {newName}")
        except Exception as e:
            print(f"Error renaming custom item: {e}")

    @Slot(str)
    def showCoreManager(self, versionName):
        try:
            import time
            current_time = time.time()
            # 防止在100ms内重复触发请求
            if current_time - self._last_core_manager_request_time < 0.1:
                return
            
            self._last_core_manager_request_time = current_time
            
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            core_data = {}
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
                    core_data = full_data.get("versions", {}).get(versionName, {})
            
            self.coreManagerRequested.emit(versionName, core_data)
        except Exception as e:
            print(f"Error showing core manager: {e}")

    @Slot(str)
    def showMrpackExport(self, versionName):
        self.mrpackExportRequested.emit(versionName)

    @Slot(str, result="QVariant")
    def getCoreData(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
                    return full_data.get("versions", {}).get(versionName, {})
            return {}
        except Exception as e:
            print(f"Error getting core data: {e}")
            return {}

    @Slot(str, "QVariant")
    def saveCoreData(self, versionName, data):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
            
            full_data = {"versions": {}}
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
            
            new_name = data.get("name", versionName)
            
            if new_name != versionName:
                old_path = os.path.join(minecraft_dir, "versions", versionName)
                new_path = os.path.join(minecraft_dir, "versions", new_name)
                if os.path.exists(new_path):
                    print("Target name already exists")
                    return
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                if versionName in full_data.get("versions", {}):
                    del full_data["versions"][versionName]
            
            full_data["versions"][new_name] = {
                "Fabric": data.get("Fabric", False),
                "version": data.get("version", new_name),
                "icon": data.get("icon", ""),
                "server": data.get("server", ""),
                "jvmArgs": data.get("jvmArgs", "")
            }
            
            with open(bl_json_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)
            
            print(f"Core data saved for: {new_name}")
            try:
                from modules.plugin_host.hook_util import fire
                if new_name != versionName:
                    fire("version.renamed", {"old": versionName, "new": new_name})
                fire("core.data.changed", {"version": new_name, "keys": list((data or {}).keys()) if isinstance(data, dict) else []})
            except Exception as _pe:
                print(f"[PluginHost] core.data.changed 失败: {_pe}")
        except Exception as e:
            print(f"Error saving core data: {e}")

    @Slot(str, result=str)
    def selectCoreIcon(self, versionName):
        try:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "选择图标",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                return file_path
            return ""
        except Exception as e:
            print(f"Error selecting icon: {e}")
            return ""

    @Slot(str, result=bool)
    def confirmDeleteCore(self, versionName):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除 Minecraft 版本 {versionName}。删除后可在系统回收站中找到。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                config_data = cfg.read()
                minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
                version_path = os.path.join(minecraft_dir, "versions", versionName)
                
                if os.path.exists(version_path):
                    if send2trash:
                        send2trash.send2trash(version_path)
                    else:
                        import shutil
                        shutil.rmtree(version_path)
                
                bl_json_path = os.path.join(minecraft_dir, "versions", ".BL.json")
                if os.path.exists(bl_json_path):
                    with open(bl_json_path, "r", encoding="utf-8") as f:
                        full_data = json.load(f)
                    if versionName in full_data.get("versions", {}):
                        del full_data["versions"][versionName]
                    with open(bl_json_path, "w", encoding="utf-8") as f:
                        json.dump(full_data, f, ensure_ascii=False, indent=4)
                
                print(f"Core deleted: {versionName}")
                try:
                    from modules.plugin_host.hook_util import fire
                    fire("version.deleted", {"version": versionName})
                except Exception as _pe:
                    print(f"[PluginHost] version.deleted 失败: {_pe}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting core: {e}")
            return False

    @Slot(str, result="QVariant")
    def getServers(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_servers_dat = os.path.join(minecraft_dir, "versions", versionName, "servers.dat")
            root_servers_dat = os.path.join(minecraft_dir, "servers.dat")
            
            read_path = ""
            if os.path.exists(version_servers_dat):
                read_path = version_servers_dat
            elif os.path.exists(root_servers_dat):
                read_path = root_servers_dat
            
            if read_path:
                return self._parse_servers_dat(read_path)
            return []
        except Exception as e:
            print(f"Error getting servers: {e}")
            return []

    def _parse_servers_dat(self, path):
        import struct
        import io
        servers = []
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            def read_string(stream):
                length = struct.unpack('>h', stream.read(2))[0]
                if length < 0:
                    return ""
                return stream.read(length).decode('utf-8')
            
            def read_tag(stream, has_name=True):
                tag_type = struct.unpack('>b', stream.read(1))[0]
                if tag_type == 0:
                    return None, None
                
                name = ""
                if has_name:
                    name = read_string(stream)
                
                if tag_type == 8:
                    return name, read_string(stream)
                elif tag_type == 9:
                    list_type = struct.unpack('>b', stream.read(1))[0]
                    list_len = struct.unpack('>i', stream.read(4))[0]
                    items = []
                    for _ in range(list_len):
                        _, val = read_tag(stream, False)
                        items.append(val)
                    return name, items
                elif tag_type == 10:
                    compound = {}
                    while True:
                        sub_name, sub_val = read_tag(stream)
                        if sub_name is None:
                            break
                        compound[sub_name] = sub_val
                    return name, compound
                return name, None
            
            stream = io.BytesIO(data)
            _, servers_data = read_tag(stream)
            
            if servers_data and 'servers' in servers_data:
                for server in servers_data['servers']:
                    icon_str = server.get('icon', '')
                    # ensure string is clean and properly prefixed for QML
                    if isinstance(icon_str, str):
                        icon_str = icon_str.strip()
                        if icon_str and not icon_str.startswith('data:'):
                            icon_str = 'data:image/png;base64,' + icon_str
                    else:
                        icon_str = ''

                    servers.append({
                        'name': server.get('name', 'Minecraft Server'),
                        'ip': server.get('ip', ''),
                        'icon': icon_str
                    })
        except Exception as e:
            print(f"Error parsing servers.dat: {e}")
        return servers

    @Slot(str, str, str)
    def addServer(self, versionName, name, ip):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            version_servers_dat = os.path.join(minecraft_dir, "versions", versionName, "servers.dat")
            
            os.makedirs(os.path.dirname(version_servers_dat), exist_ok=True)
            
            servers = self._parse_servers_dat(version_servers_dat) if os.path.exists(version_servers_dat) else []
            servers.append({'name': name, 'ip': ip, 'icon': ''})
            
            self._save_servers_dat(version_servers_dat, servers)
            print(f"Server added: {name}")
            try:
                from modules.plugin_host.hook_util import fire
                fire("servers.changed", {"version": versionName, "action": "add", "name": name, "ip": ip})
            except Exception as _pe:
                print(f"[PluginHost] servers.changed 失败: {_pe}")
        except Exception as e:
            print(f"Error adding server: {e}")

    def _save_servers_dat(self, path, servers):
        import struct
        import io
        try:
            stream = io.BytesIO()
            
            def write_string(s):
                encoded = s.encode('utf-8')
                stream.write(struct.pack('>h', len(encoded)))
                stream.write(encoded)
            
            stream.write(struct.pack('>b', 10))
            write_string("")
            
            stream.write(struct.pack('>b', 9))
            write_string("servers")
            stream.write(struct.pack('>b', 10))
            stream.write(struct.pack('>i', len(servers)))
            
            for server in servers:
                stream.write(struct.pack('>b', 10))
                write_string("")
                
                stream.write(struct.pack('>b', 8))
                write_string("name")
                write_string(server.get('name', ''))
                
                stream.write(struct.pack('>b', 8))
                write_string("ip")
                write_string(server.get('ip', ''))
                
                if server.get('icon'):
                    stream.write(struct.pack('>b', 8))
                    write_string("icon")
                    write_string(server['icon'])
                
                stream.write(struct.pack('>b', 0))
            
            stream.write(struct.pack('>b', 0))
            
            with open(path, 'wb') as f:
                f.write(stream.getvalue())
            print(f"Saved {len(servers)} servers to {path}")
        except Exception as e:
            print(f"Error saving servers.dat: {e}")

    @Slot(str, result="QVariant")
    def getMods(self, versionName):
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            mods_dir = os.path.join(minecraft_dir, "versions", versionName, "mods")
            
            if not os.path.exists(mods_dir):
                os.makedirs(mods_dir, exist_ok=True)
                return []
            
            mods = []
            import zipfile
            import base64
            for filename in os.listdir(mods_dir):
                file_path = os.path.join(mods_dir, filename)
                if os.path.isdir(file_path):
                    continue
                
                is_disabled = filename.endswith('.disabled')
                if not (filename.endswith('.jar') or filename.endswith('.jar.disabled')):
                    continue
                
                mod_data = {
                    "name": filename,
                    "path": file_path,
                    "filename": filename,
                    "version": "",
                    "description": "无描述",
                    "icon": "",
                    "enabled": not is_disabled
                }
                
                try:
                    if zipfile.is_zipfile(file_path):
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            if 'fabric.mod.json' in zf.namelist():
                                with zf.open('fabric.mod.json') as f:
                                    meta = json.load(f)
                                    mod_data["name"] = meta.get("name", meta.get("id", filename))
                                    mod_data["version"] = meta.get("version", "")
                                    mod_data["description"] = meta.get("description", "")[:100]
                                    
                                    icon_path = meta.get("icon")
                                    if icon_path and isinstance(icon_path, str) and icon_path in zf.namelist():
                                        icon_data = zf.read(icon_path)
                                        mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                                    elif f"assets/{meta.get('id')}/icon.png" in zf.namelist():
                                        icon_data = zf.read(f"assets/{meta.get('id')}/icon.png")
                                        mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                            elif 'mcmod.info' in zf.namelist():
                                with zf.open('mcmod.info') as f:
                                    meta_list = json.load(f)
                                    if meta_list and isinstance(meta_list, list):
                                        meta = meta_list[0]
                                        mod_data["name"] = meta.get("name", filename)
                                        mod_data["version"] = meta.get("version", "")
                                        mod_data["description"] = meta.get("description", "")[:100]
                                        
                                        logo = meta.get("logoFile")
                                        if logo and logo in zf.namelist():
                                            icon_data = zf.read(logo)
                                            mod_data["icon"] = "data:image/png;base64," + base64.b64encode(icon_data).decode('utf-8')
                except Exception as e:
                    print(f"Error reading mod {filename}: {e}")
                
                mods.append(mod_data)
            
            return mods
        except Exception as e:
            print(f"Error getting mods: {e}")
            return []

    @Slot(str, bool)
    def toggleMod(self, path, enabled):
        try:
            if not os.path.exists(path):
                return
            try:
                from modules.plugin_host.hook_util import fire, any_cancel
                cancel = any_cancel(fire("mods.toggle", {"path": path, "enabled": bool(enabled)}))
                if cancel:
                    print(f"[PluginHost] mods.toggle cancelled: {cancel}")
                    return
            except Exception as _pe:
                print(f"[PluginHost] mods.toggle 失败: {_pe}")
            
            dirname, filename = os.path.split(path)
            
            if enabled:
                if filename.endswith('.disabled'):
                    new_filename = filename[:-9]
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
            else:
                if not filename.endswith('.disabled'):
                    new_filename = filename + '.disabled'
                    new_path = os.path.join(dirname, new_filename)
                    os.rename(path, new_path)
        except Exception as e:
            print(f"Error toggling mod: {e}")

    @Slot(str, result=bool)
    def deleteMod(self, path):
        try:
            try:
                from modules.plugin_host.hook_util import fire, any_cancel
                cancel = any_cancel(fire("mods.delete", {"path": path}))
                if cancel:
                    print(f"[PluginHost] mods.delete cancelled: {cancel}")
                    return False
            except Exception as _pe:
                print(f"[PluginHost] mods.delete 失败: {_pe}")
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除 Mod: {os.path.basename(path)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if send2trash:
                    send2trash.send2trash(path)
                else:
                    os.remove(path)
                try:
                    from modules.plugin_host.hook_util import fire
                    fire("mods.delete", {"path": path, "done": True})
                except Exception:
                    pass
                return True
            return False
        except Exception as e:
            print(f"Error deleting mod: {e}")
            return False

    @Slot(str, result="QVariant")
    def getResourcePacks(self, versionName):
        try:
            import base64
            config_data = cfg.read()
            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            packs_dir = os.path.join(minecraft_dir, "versions", versionName, "resourcepacks")
            
            if not os.path.exists(packs_dir):
                os.makedirs(packs_dir, exist_ok=True)
                return []
            
            packs = []
            import zipfile
            for filename in os.listdir(packs_dir):
                file_path = os.path.join(packs_dir, filename)
                
                if not (os.path.isdir(file_path) or filename.endswith('.zip')):
                    continue
                
                pack_data = {
                    "name": filename,
                    "path": file_path,
                    "description": "无描述",
                    "icon": ""
                }
                
                try:
                    if os.path.isdir(file_path):
                        mcmeta_path = os.path.join(file_path, "pack.mcmeta")
                        icon_path = os.path.join(file_path, "pack.png")
                        
                        if os.path.exists(mcmeta_path):
                            with open(mcmeta_path, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                                desc = meta.get("pack", {}).get("description", "")
                                if isinstance(desc, dict):
                                    desc = desc.get("translate", str(desc))
                                pack_data["description"] = str(desc)[:100]
                        
                        if os.path.exists(icon_path):
                            # read bytes and convert to data URI
                            try:
                                with open(icon_path, 'rb') as imgf:
                                    b64 = base64.b64encode(imgf.read()).decode('utf-8')
                                    pack_data["icon"] = f"data:image/png;base64,{b64}"
                            except Exception as ee:
                                print(f"Error reading resource pack icon {icon_path}: {ee}")
                            
                    elif zipfile.is_zipfile(file_path):
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            if "pack.mcmeta" in zf.namelist():
                                with zf.open("pack.mcmeta") as f:
                                    meta = json.load(f)
                                    desc = meta.get("pack", {}).get("description", "")
                                    if isinstance(desc, dict):
                                        desc = desc.get("translate", str(desc))
                                    pack_data["description"] = str(desc)[:100]
                            if "pack.png" in zf.namelist():
                                try:
                                    icon_bytes = zf.read("pack.png")
                                    b64 = base64.b64encode(icon_bytes).decode('utf-8')
                                    pack_data["icon"] = f"data:image/png;base64,{b64}"
                                except Exception as ee:
                                    print(f"Error extracting pack.png from {filename}: {ee}")
                except Exception as e:
                    print(f"Error reading resource pack {filename}: {e}")
                
                packs.append(pack_data)
            
            return packs
        except Exception as e:
            print(f"Error getting resource packs: {e}")
            return []

    @Slot(str, result=bool)
    def deleteResourcePack(self, path):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "确认删除",
                f"将删除资源包: {os.path.basename(path)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    from modules.plugin_host.hook_util import fire, any_cancel
                    cancel = any_cancel(fire("resourcepack.delete", {"path": path}))
                    if cancel:
                        print(f"[PluginHost] resourcepack.delete cancelled: {cancel}")
                        return False
                except Exception as _pe:
                    print(f"[PluginHost] resourcepack.delete 失败: {_pe}")
                if send2trash:
                    send2trash.send2trash(path)
                else:
                    import shutil
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting resource pack: {e}")
            return False

    @Slot(str, bool)
    def askBloriko(self, query, deep_think=False):
        """一次性 AI 问答（走全局 AI 供应商；deep_think 已废弃）。"""
        print(f"Bloriko request: '{query}', deep_think(ignored)={deep_think}")
        def run_ask():
            try:
                from modules.Bloriko import AskBloriko
                from modules.log import log as _log
                import logging as _logging
                _log(f"Backend.askBloriko 开始, query_len={len(query or '')}", _logging.INFO)
                response = AskBloriko(query, config=None, deepthink=False)
                self.blorikoResponseReceived.emit(response)
            except Exception as e:
                print(f"Error in askBloriko: {e}")
                self.blorikoResponseReceived.emit(i18nText("错误: {error}").replace("{error}", str(e)))
        threading.Thread(target=run_ask, daemon=True).start()

    @Slot(str, bool)
    def askBlorikoForMods(self, query, deep_think=False):
        print(f"Bloriko Mod suggestion request: '{query}'")
        suffix = " (请针对 Minecraft 模组给出建议)" if "模组" not in query and "mod" not in query.lower() else ""
        self.askBloriko(query + suffix, False)

    @Slot(str, str)
    def askBlorikoForModsWithVersion(self, query, version):
        """
        带 Minecraft 版本的模组推荐：
        Modrinth 工具搜索 + 流式正文 + 思考/工具过程展示。
        """
        print(f"Bloriko Mod suggestion request with version: '{query}' for MC {version}")
        from modules.log import log as _log
        import logging as _logging

        # 取消上一轮未完成的推荐
        prev = getattr(self, "_mod_suggest_agent", None)
        if prev is not None:
            try:
                prev.cancel()
                _log("[Backend] 已取消上一轮 Mod 推荐 Agent", _logging.INFO)
            except Exception as e:
                _log(f"[Backend] 取消上一轮 Agent 失败: {e}", _logging.WARNING)
            self._mod_suggest_agent = None

        self._mod_suggest_cancelled = False
        self._mod_suggest_generation = getattr(self, "_mod_suggest_generation", 0) + 1
        generation = self._mod_suggest_generation

        try:
            from modules.bloriko_mod_agent import run_mod_recommendation_agent

            # 尽量把文件夹名解析为纯 MC 版本（与旧逻辑一致）
            actual_version = version
            try:
                config_data = cfg.read()
                mc_dir = config_data.get("minecraft_dir", BLglobals.minecraft_dir)
                bl_json_path = os.path.join(mc_dir, "versions", ".BL.json")
                if os.path.exists(bl_json_path):
                    with open(bl_json_path, "r", encoding="utf-8") as f:
                        bl_data = json.load(f)
                    mappings = bl_data.get("versions", {})
                    if version in mappings:
                        actual_version = mappings[version].get("version", version) or version
            except Exception as e:
                _log(f"[Backend] 解析 Fabric 真实版本失败，使用原名: {e}", _logging.WARNING)

            _log(
                f"Backend.askBlorikoForModsWithVersion(agent): folder={version}, "
                f"mc={actual_version}, query_len={len(query or '')}, gen={generation}",
                _logging.INFO,
            )
            self.blorikoModSuggestionStatus.emit("络可正在连接 AI 并准备搜索 Modrinth…")

            def on_status(msg):
                if generation != getattr(self, "_mod_suggest_generation", 0):
                    return
                if getattr(self, "_mod_suggest_cancelled", False):
                    return
                self.blorikoModSuggestionStatus.emit(str(msg or ""))

            def on_chunk(text):
                if generation != getattr(self, "_mod_suggest_generation", 0):
                    return
                if getattr(self, "_mod_suggest_cancelled", False):
                    return
                self.blorikoModSuggestionChunk.emit(str(text or ""))

            def on_error(msg):
                if generation != getattr(self, "_mod_suggest_generation", 0):
                    return
                if getattr(self, "_mod_suggest_cancelled", False):
                    return
                self.blorikoModSuggestionFailed.emit(str(msg or ""))

            def on_done(clean_text, slugs):
                if generation != getattr(self, "_mod_suggest_generation", 0):
                    _log("[Backend] 忽略过期 Mod 推荐结果", _logging.INFO)
                    return
                if getattr(self, "_mod_suggest_cancelled", False):
                    _log("[Backend] 推荐已取消，不弹出结果", _logging.INFO)
                    self._mod_suggest_agent = None
                    return
                self._mod_suggest_agent = None
                _log(
                    f"Backend.askBlorikoForModsWithVersion 完成: slugs={len(slugs or [])}, "
                    f"text_len={len(clean_text or '')}",
                    _logging.INFO,
                )
                self.blorikoModSuggestionReceived.emit(clean_text or "", list(slugs or []))

            agent = run_mod_recommendation_agent(
                query,
                actual_version,
                on_text_chunk=on_chunk,
                on_status=on_status,
                on_error=on_error,
                on_done=on_done,
            )
            self._mod_suggest_agent = agent
        except Exception as e:
            print(f"Error in askBlorikoForModsWithVersion: {e}")
            _log(f"askBlorikoForModsWithVersion 启动失败: {e}", _logging.ERROR)
            self.blorikoModSuggestionFailed.emit(str(e))
            self.blorikoModSuggestionReceived.emit(
                i18nText("错误: {error}").replace("{error}", str(e)), []
            )

    @Slot()
    def cancelBlorikoModSuggestion(self):
        """取消进行中的络可 Mod 推荐。"""
        self._mod_suggest_cancelled = True
        self._mod_suggest_generation = getattr(self, "_mod_suggest_generation", 0) + 1
        agent = getattr(self, "_mod_suggest_agent", None)
        if agent is not None:
            try:
                agent.cancel()
                print("[Backend] cancelBlorikoModSuggestion: cancelled")
            except Exception as e:
                print(f"[Backend] cancelBlorikoModSuggestion failed: {e}")
            self._mod_suggest_agent = None
        self.blorikoModSuggestionStatus.emit("已取消")

    @Slot(result=list)
    def getVanillaVersions(self):
        try:
            config_data = cfg.read()
            return config_data.get('Minecraft_Versions', ["1.21.8", "1.21.7", "1.20.1"])
        except:
            return ["1.21.8", "1.21.7", "1.20.1"]

    # 版本缓存
    _versions_cache = {}
    
    @Slot(str, result=list)
    def getVersionsByCategory(self, category):
        """根据类别返回缓存版本列表；缓存未就绪时触发后台加载。"""
        if category == "百络谷支持版本":
            from modules.install import fetch_fastdownload_versions
            fastdownload = fetch_fastdownload_versions()
            return list(fastdownload.keys())
        versions = self._versions_cache.get(category, [])
        if not versions and not self._manifest_fetched:
            print(f"[VersionList] 类别 {category} 尚无缓存，触发后台加载")
            self._prefetch_version_list()
        return versions

    @Slot()
    def retryVersionListLoad(self):
        """供版本选择对话框在加载失败后主动重试。"""
        print("[VersionList] 用户请求重新加载版本清单")
        self._prefetch_version_list(force=True)

    # Removed incorrect getFabricVersions implementation here to use the correct one below

    @Slot(result=list)
    def getJavaDownloadVersions(self):
        from modules.java import java_versions
        return list(java_versions.keys())

    @Slot(str, str, result='QVariant')
    def validateVersionName(self, baseVersion, name):
        """Validate name for installation: returns dict with valid, error, exists"""
        result = {"valid": True, "error": "", "exists": False}
        try:
            # empty
            if not name or name.strip() == "":
                result["valid"] = False
                result["error"] = "版本名不能为空"
                return result
            # invalid characters
            invalid = r"[\\/:\*\?\"<>|]"
            import re
            if re.search(invalid, name):
                result["valid"] = False
                result["error"] = "版本名不能包含 \\ / : * ? \" < > | 等字符"
                return result
            # reserved names
            reserved = ['CON','PRN','AUX','NUL'] + [f'COM{i}' for i in range(1,10)] + [f'LPT{i}' for i in range(1,10)]
            if name.upper() in reserved:
                result["valid"] = False
                result["error"] = "版本名为 Windows 保留字"
                return result
            # existence
            items = self.getLaunchItems()
            for item in items:
                if item.get("name") == name:
                    result["exists"] = True
                    break
        except Exception as e:
            print(f"validation exception: {e}")
        return result

    @Slot(str, str)
    def downloadVanilla(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Vanilla: {version} as {versionName}")
        title = i18nText("正在下载 Minecraft {version}").replace("{version}", version)
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, VersionName=versionName, backend=self)

    @Slot(str, str)
    def downloadFabric(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Fabric: {version} as {versionName}")
        title = i18nText("正在下载 Minecraft {version} 和 Fabric Loader").replace("{version}", version)
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, Fabric_Loader=True, VersionName=versionName, backend=self)

    @Slot(str, str)
    def downloadForge(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download Forge: {version} as {versionName}")
        title = i18nText("正在下载 Minecraft {version} 和 Forge").replace("{version}", version)
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, VersionName=versionName, backend=self, Loader_Type="forge")

    @Slot(str, str)
    def downloadNeoForge(self, version, versionName):
        from modules.install import InstallMinecraftVersion
        print(f"Requested download NeoForge: {version} as {versionName}")
        title = i18nText("正在下载 Minecraft {version} 和 NeoForge").replace("{version}", version)
        self.downloadDialogRequested.emit(title)
        InstallMinecraftVersion(version, VersionName=versionName, backend=self, Loader_Type="neoforge")

    @Slot()
    def toggleDownloadPause(self):
        from modules.install import toggle_current_download_pause
        toggle_current_download_pause()

    @Slot()
    def cancelDownload(self):
        from modules.install import cancel_current_download
        cancel_current_download()

    def updateDownloadProgress(self, progress, status, speed, downloaded, total):
        self.downloadProgressUpdated.emit(progress, status, speed, downloaded, total)

    def closeDownloadDialog(self):
        self.downloadDialogClosed.emit()

    def notifyDownloadComplete(self, message="Minecraft 安装完成"):
        self.downloadCompleted.emit(message)
        try:
            if sys.platform == "win32":
                from modules.win11toast import notify
                notify(progress={
                    'title': 'Bloret Launcher',
                    'status': message,
                    'value': '100',
                    'valueStringOverride': '100%'
                })
            else:
                from modules.notification import send_notification
                send_notification("Bloret Launcher", message, category="download")
        except Exception as e:
            print(f"发送安装完成通知失败: {e}")

    def setDownloadPaused(self, paused):
        self.downloadPaused.emit(paused)

    @Slot(str)
    def downloadJava(self, version):
        from modules.java import InstallJava
        print(f"Requested download Java: {version}")
        InstallJava(version)

    @Slot()
    def addCustomApp(self):
        print("Requested add custom app")
        # 打开文件浏览对话框让用户选择 exe 或其他可执行文件
        file_path = QFileDialog.getOpenFileName(
            None,
            "选择应用程序文件",
            "",
            "所有文件 (*);;执行文件 (*.exe);;程序包 (*.zip);;整合包 (*.zip);;批处理脚本 (*.bat)"
        )[0]
        
        if not file_path:
            print("用户取消了文件选择")
            return
        
        # 提取文件名作为默认显示名称
        default_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 创建一个简单的输入对话框让用户确认/修改名称
        from PySide6.QtWidgets import QInputDialog
        display_name, ok = QInputDialog.getText(
            None,
            "输入显示名称",
            "请为此应用输入一个显示名称:",
            text=default_name
        )
        
        if not ok or not display_name:
            print("用户取消了名称输入")
            return
        
        # 保存到配置文件
        try:
            config_data = cfg.read()
            if "Customize" not in config_data:
                config_data["Customize"] = []
            
            # 检查是否已存在相同的项
            for item in config_data["Customize"]:
                if item.get("showname") == display_name:
                    print(f"自定义项 '{display_name}' 已存在")
                    return
            
            config_data["Customize"].append({
                "showname": display_name,
                "path": file_path
            })
            
            cfg.write(config_data)
            
            print(f"成功添加自定义项: {display_name} -> {file_path}")
            # 可以在这里发出信号或刷新 UI（如果需要）
        except Exception as e:
            print(f"添加自定义项失败: {e}")

    @Slot()
    def importMrpack(self):
        """导入 Modrinth .mrpack 整合包"""
        try:
            from modules.modrinth import add_mrpack
            print("Requested import Modrinth mrpack")
            add_mrpack(None)
        except Exception as e:
            print(f"导入 Modrinth 整合包失败: {e}")
            import traceback
            traceback.print_exc()

    @Slot(result=str)
    def getBloretVersion(self):
        """获取当前版本号 - 优先从用户配置获取，否则从源配置文件获取"""
        config_data = cfg.read()
        version = config_data.get("ver")
        if version:
            return str(version)
        
        # 配置文件不存在或没有版本号，从源配置文件获取
        source_config_path = cfg.source_config_path
        if os.path.exists(source_config_path):
            try:
                with open(source_config_path, 'r', encoding='utf-8') as f:
                    source_config = json.load(f)
                    return str(source_config.get("ver", ""))
            except Exception as e:
                print(f"Error reading source config for version: {e}")
        return ""

    @Slot(result=str)
    def getLanguageCode(self):
        config_data = cfg.read()
        lang_code = config_data.get("language") or config_data.get("Language") or "zh-cn"
        if not isinstance(lang_code, str):
            return "zh-cn"

        lang_code = lang_code.strip()
        return lang_code if lang_code else "zh-cn"

    @Slot(result=list)
    def getLanguages(self):
        """从 Default.json 加载语言列表"""
        try:
            default_lang_path = "lang/Default.json"
            if os.path.exists(default_lang_path):
                with open(default_lang_path, "r", encoding="utf-8") as f:
                    default_data = json.load(f)
                    result = []
                    # 从 Default.json 中提取语言列表
                    if "lang" in default_data:
                        for code, lang_info in default_data["lang"].items():
                            # 使用 Default.json 中定义的名称
                            name = lang_info.get("name", code)
                            # 确保文件存在
                            lang_file = f"lang/{lang_info.get('file', code + '.json')}"
                            if os.path.exists(lang_file):
                                result.append({"code": code, "name": name})
                            else:
                                # 如果文件不存在，跳过这个语言
                                print(f"Warning: Language file {lang_file} not found for code {code}")
                    if not result:
                        result = [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]
            else:
                # 如果 Default.json 不存在，回退到旧方法
                lang_dir = "lang"
                result = []
                # 语言代码到显示名称的映射（常用语言）
                lang_names = {
                    "zh-cn": "简体中文", "zh-TW": "繁體中文", "en-US": "English (US)",
                    "en-GB": "English (UK)", "ja-JP": "日本語", "ko-KR": "한국어",
                    "fr-FR": "Français", "de-DE": "Deutsch", "es-ES": "Español",
                    "ru-RU": "Русский", "pt-BR": "Português (Brasil)",
                    "it-IT": "Italiano", "nl-NL": "Nederlands", "pl-PL": "Polski",
                    "tr-TR": "Türkçe", "ar-SA": "العربية", "vi-VN": "Tiếng Việt",
                }
                if os.path.isdir(lang_dir):
                    for fn in sorted(os.listdir(lang_dir)):
                        if fn.endswith(".json") and fn != "Default.json":
                            code = fn[:-5]  # 去掉 .json
                            # 尝试从语言文件读取自描述名称
                            name = lang_names.get(code, code)
                            try:
                                with open(os.path.join(lang_dir, fn), "r", encoding="utf-8") as f:
                                    d = json.load(f)
                                    # 某些语言文件里有 _meta.name 字段
                                    if "_meta" in d and "name" in d["_meta"]:
                                        name = d["_meta"]["name"]
                            except Exception:
                                pass
                            result.append({"code": code, "name": name})
                if not result:
                    result = [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]
            return result
        except Exception as e:
            print(f"Error loading languages: {e}")
            return [{"code": "zh-cn", "name": "简体中文"}, {"code": "en-US", "name": "English"}]

    @Slot(str)
    def setLanguage(self, lang_code):
        try:
            if not isinstance(lang_code, str):
                lang_code = "" if lang_code is None else str(lang_code)

            lang_code = lang_code.strip()
            if not lang_code:
                print("Ignored empty language code")
                return

            config_data = cfg.read()
            config_data['language'] = lang_code
            # Drop legacy key to avoid ambiguity.
            config_data.pop('Language', None)
            cfg.write(config_data)
            
            from modules.i18n import reload_language
            reload_language(lang_code)
            print(f"Language set to: {lang_code}")
            self.languageChanged.emit()
        except Exception as e:
            print(f"Error setting language: {e}")

    @Slot(str, result=str)
    def tr(self, key):
        return i18nText(key)

    # ── Software Update ──────────────────────────────────────────

    def checkForUpdates(self):
        """Check for updates in a background thread; emit updateAvailable if newer version exists."""
        def _inner():
            try:
                config_data = cfg.read()
                if config_data.get('localmod', False):
                    print("Local mode enabled, skipping update check")
                    return

                from modules.BLServer import get_latest_version, IsNeedUpdate
                latest_ver, update_text = get_latest_version()
                
                # 优先从用户配置获取版本号，如果不存在则从源配置文件获取
                current_ver = config_data.get('ver')
                if not current_ver:
                    # 配置文件不存在或没有版本号，从源配置文件获取
                    source_config_path = cfg.source_config_path
                    if os.path.exists(source_config_path):
                        try:
                            with open(source_config_path, 'r', encoding='utf-8') as f:
                                source_config = json.load(f)
                                current_ver = source_config.get('ver', '0.0')
                                print(f"Version from source config: {current_ver}")
                        except Exception as e:
                            print(f"Error reading source config: {e}")
                            current_ver = '0.0'
                    else:
                        current_ver = '0.0'
                
                current_ver = str(current_ver)
                print(f"Update check: current={current_ver}, latest={latest_ver}")

                if latest_ver and IsNeedUpdate(current_ver, latest_ver):
                    print(f"Update available: {latest_ver}")
                    self.updateAvailable.emit(current_ver, latest_ver, update_text)
                    try:
                        from modules.notification import send_notification
                        send_notification(
                            i18nText("发现新版本"),
                            i18nText("Bloret Launcher {version} 已发布，点击查看详情").replace("{version}", str(latest_ver)),
                            category="update",
                        )
                    except Exception:
                        pass
                else:
                    print("Already up to date")
            except Exception as e:
                print(f"Update check failed: {e}")

        threading.Thread(target=_inner, daemon=True).start()

    @Slot()
    def startUpdate(self):
        """Download the latest installer and launch it."""
        def _inner():
            try:
                self.updateProgressUpdated.emit(0.05, i18nText("正在获取下载地址..."))

                response = requests.get(f"{BLglobals.server_ip}:3001/api/info", timeout=15)
                response.raise_for_status()
                res = response.json()

                download_url = res["downloads"]["stable"]["gitcode"]
                version = res["latestVersion"]

                self.updateProgressUpdated.emit(0.1, i18nText("正在下载更新文件..."))

                import tempfile
                temp_dir = tempfile.gettempdir()
                file_name = os.path.join(temp_dir, f"Bloret-Launcher-Setup-{version}.exe")

                with requests.get(download_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded_size = 0
                    last_progress = 0.1
                    with open(file_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = 0.1 + (downloaded_size / total_size) * 0.8
                                if progress - last_progress >= 0.03:
                                    status = f"{downloaded_size // 1024} KB / {total_size // 1024} KB"
                                    self.updateProgressUpdated.emit(progress, status)
                                    last_progress = progress

                self.updateProgressUpdated.emit(0.95, i18nText("正在启动安装程序..."))
                subprocess.Popen([file_name, "--quickstart"], **hidden_process_kwargs())
                sys.exit(0)

            except Exception as e:
                print(f"Update failed: {e}")
                self.updateFailed.emit(str(e))
                try:
                    from modules.notification import send_notification
                    send_notification(i18nText("更新失败"), str(e), category="update")
                except Exception:
                    pass

    @Slot()
    def openMinecraftDir(self):
        config_data = cfg.read()
        mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
        if mc_dir and os.path.exists(mc_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(mc_dir))
        else:
            print(f"Minecraft directory not found: {mc_dir}")

    @Slot()
    def openLogDir(self):
        log_dir = os.path.join(BLglobals.datapath, "log")
        if os.path.exists(log_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))

    @Slot()
    def clearLogs(self):
        print("Clearing logs...")
        log_dir = os.path.join(BLglobals.datapath, "log")
        if os.path.exists(log_dir):
            import shutil
            for filename in os.listdir(log_dir):
                file_path = os.path.join(log_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

    @Slot(result=str)
    def getMinecraftDir(self):
        config_data = cfg.read()
        return config_data.get('minecraft_dir', BLglobals.minecraft_dir)

    @Slot(result=str)
    def browseMinecraftDir(self):
        dir_path = QFileDialog.getExistingDirectory(None, "选择 Minecraft 目录", self.getMinecraftDir())
        if dir_path:
            self.setMinecraftDir(dir_path)
            return dir_path
        return ""

    @Slot(str)
    def setMinecraftDir(self, path):
        config_data = cfg.read()
        config_data['minecraft_dir'] = path
        cfg.write(config_data)
        BLglobals.minecraft_dir = path
        print(f"Minecraft directory updated to: {path}")

    @Slot(result=list)
    def getSystemJavas(self):
        from modules.java_runtime import probe_java, scan_java_runtimes, invalidate_java_runtime_cache
        invalidate_java_runtime_cache()
        runtimes = scan_java_runtimes(force_refresh=True)
        configured_path = self.getCurrentJavaPath()
        if configured_path and not any(item.get('path') == configured_path for item in runtimes):
            configured = probe_java(configured_path)
            if configured['valid']:
                runtimes.append(configured)
        log(f"[Settings] 返回 {len(runtimes)} 个 Java 扫描结果")
        return runtimes

    @Slot(result=str)
    def getJavaSelectionMode(self):
        config_data = cfg.read()
        mode = config_data.get('java_mode')
        if mode in ('auto', 'fixed'):
            return mode
        legacy_path = config_data.get('java_path', config_data.get('Java_Path', 'Auto'))
        return 'auto' if not legacy_path or legacy_path == 'Auto' else 'fixed'

    @Slot(result=str)
    def getCurrentJavaPath(self):
        config_data = cfg.read()
        path = config_data.get('java_fixed_path') or config_data.get('java_path', config_data.get('Java_Path', 'Auto'))
        return '' if path == 'Auto' else path

    @Slot(str, str, result=bool)
    def setJavaSelection(self, mode, path):
        from modules.java_runtime import probe_java, invalidate_java_runtime_cache
        if mode not in ('auto', 'fixed'):
            log(f"[Settings] 拒绝未知 Java 选择模式: {mode}", logging.WARNING)
            return False
        normalized_path = ''
        if mode == 'fixed':
            info = probe_java(path)
            if not info['valid']:
                log(f"[Settings] 拒绝无效固定 Java: {path}，原因={info['error']}", logging.WARNING)
                return False
            normalized_path = info['path']
        config_data = cfg.read()
        config_data['java_mode'] = mode
        config_data['java_fixed_path'] = normalized_path
        config_data['java_path'] = normalized_path if mode == 'fixed' else 'Auto'
        cfg.write(config_data)
        invalidate_java_runtime_cache()
        log(f"[Settings] Java 选择已更新：模式={mode}，路径={normalized_path or '自动'}")
        return True

    @Slot(str)
    def setCurrentJavaPath(self, path):
        self.setJavaSelection('auto' if path == 'Auto' else 'fixed', '' if path == 'Auto' else path)

    @Slot(result=str)
    def browseJavaExecutable(self):
        executable, _ = QFileDialog.getOpenFileName(
            None,
            i18nText("选择 Java 可执行文件"),
            "",
            "Java (java java.exe);;All Files (*)",
        )
        if not executable:
            return ""
        from modules.java_runtime import probe_java
        info = probe_java(executable)
        if not info['valid']:
            log(f"[Settings] 浏览选择的文件不是有效 Java: {executable}，原因={info['error']}", logging.WARNING)
            return ""
        log(f"[Settings] 浏览选择 Java {info['major']}：{info['path']}")
        return info['path']

    @Slot(result=str)
    def getThemeMode(self):
        config_data = cfg.read()
        return config_data.get('theme', 'Auto')

    @Slot(str)
    def setThemeMode(self, mode):
        config_data = cfg.read()
        config_data['theme'] = mode
        cfg.write(config_data, changed_keys={'theme': mode})
        print(f"Theme mode updated to: {mode}")

    @Slot(str)
    def setBackdropEffect(self, effect):
        """设置背景效果 (none/acrylic)"""
        config_data = cfg.read()
        config_data['backdrop_effect'] = effect
        cfg.write(config_data, changed_keys={'backdrop_effect': effect})
        # 通知 RinUI（Windows 处理原生效果，Linux 仅打印日志）
        parent = getattr(self, "parent", None)
        if parent and hasattr(parent, "theme_manager"):
            parent.theme_manager.apply_backdrop_effect(effect)
        # 发射信号让 QML 端更新 Utils.backdropEnabled
        self.backdropEffectChanged.emit(effect)
        print(f"Backdrop effect set to: {effect}")

    @Slot(result=str)
    def getBackdropEffect(self):
        config_data = cfg.read()
        return config_data.get('backdrop_effect', 'none')

    @Slot(result=str)
    def getDownloadSource(self):
        config_data = cfg.read()
        return config_data.get('download_source', 'gitcode')

    @Slot(str)
    def setDownloadSource(self, source):
        config_data = cfg.read()
        config_data['download_source'] = source
        cfg.write(config_data, changed_keys={'download_source': source})
        BLglobals.download_source = source
        print(f"Download source updated to: {source}")

    @Slot(result=int)
    def getMaxThread(self):
        """Max concurrent download workers (clamped 1–64, default 16)."""
        try:
            from modules.download import clamp_workers
            return int(clamp_workers(cfg.read().get("MaxThread", 16)))
        except Exception:
            try:
                n = int(cfg.read().get("MaxThread", 16) or 16)
            except (TypeError, ValueError):
                n = 16
            return max(1, min(n, 64))

    @Slot(int)
    def setMaxThread(self, value):
        try:
            from modules.download import clamp_workers
            n = int(clamp_workers(value))
        except Exception:
            try:
                n = max(1, min(int(value), 64))
            except (TypeError, ValueError):
                n = 16
        config_data = cfg.read()
        config_data["MaxThread"] = n
        cfg.write(config_data, changed_keys={"MaxThread": n})
        print(f"MaxThread updated to: {n}")

    @Slot(result=str)
    def getShowAccountOnHome(self):
        config_data = cfg.read()
        val = config_data.get('show_account_on_home', 'compact')
        # 向后兼容旧版布尔值
        if val is True:
            return 'full'
        if val is False:
            return 'hidden'
        if val not in ('compact', 'full', 'hidden'):
            return 'compact'
        return val

    @Slot(str)
    def setShowAccountOnHome(self, mode):
        config_data = cfg.read()
        config_data['show_account_on_home'] = mode
        cfg.write(config_data)
        print(f"Show account on home updated to: {mode}")

    @Slot(result=bool)
    def getMinimizeToTrayOnClose(self):
        config_data = cfg.read()
        return config_data.get('minimize_to_tray_on_close', True)

    @Slot(bool)
    def setMinimizeToTrayOnClose(self, enabled):
        config_data = cfg.read()
        config_data['minimize_to_tray_on_close'] = enabled
        cfg.write(config_data)
        print(f"Minimize to tray on close updated to: {enabled}")

    @Slot(result=bool)
    def getRepeatRun(self):
        config_data = cfg.read()
        return config_data.get('repeat_run', False)

    @Slot(bool)
    def setRepeatRun(self, enabled):
        config_data = cfg.read()
        config_data['repeat_run'] = enabled
        cfg.write(config_data)
        print(f"Repeat run updated to: {enabled}")

    # ========== 资源包编辑器全局设置 ==========

    @Slot(str, str, result=str)
    def getRpeSetting(self, key, default=""):
        """读取资源包编辑器全局设置"""
        config_data = cfg.read()
        return str(config_data.get("rpe", {}).get(key, default))

    @Slot(str, str)
    def setRpeSetting(self, key, value):
        """写入资源包编辑器全局设置"""
        config_data = cfg.read()
        if "rpe" not in config_data:
            config_data["rpe"] = {}
        config_data["rpe"][key] = value
        cfg.write(config_data)
        print(f"RPE setting {key} updated to: {value}")

    @Slot(str, result=bool)
    def getNotificationSetting(self, key):
        """读取通知偏好设置"""
        config_data = cfg.read()
        return config_data.get("notifications", {}).get(key, True)

    @Slot(str, bool)
    def setNotificationSetting(self, key, value):
        """写入通知偏好设置"""
        from modules.notification import invalidate_config_cache
        config_data = cfg.read()
        if "notifications" not in config_data:
            config_data["notifications"] = {}
        config_data["notifications"][key] = value
        cfg.write(config_data)
        invalidate_config_cache()
        print(f"Notification setting {key} updated to: {value}")

    @Slot(result=str)
    def getBarkUrl(self):
        """读取 Bark 推送 URL"""
        config_data = cfg.read()
        return config_data.get("notifications", {}).get("bark_url", "")

    @Slot(str)
    def setBarkUrl(self, url):
        """写入 Bark 推送 URL"""
        from modules.notification import invalidate_config_cache
        config_data = cfg.read()
        if "notifications" not in config_data:
            config_data["notifications"] = {}
        config_data["notifications"]["bark_url"] = url.strip()
        cfg.write(config_data)
        invalidate_config_cache()
        print(f"Bark URL updated to: {url.strip()}")

    @Slot(result=str)
    def testBark(self):
        """测试 Bark 推送"""
        from modules.notification import test_bark
        return test_bark()

    @Slot(result=bool)
    def getWebRemoterEnabled(self):
        config_data = cfg.read()
        return config_data.get('web_remoter_enabled', True)

    @Slot(bool)
    def setWebRemoterEnabled(self, enabled):
        config_data = cfg.read()
        config_data['web_remoter_enabled'] = enabled
        cfg.write(config_data)
        print(f"Web Remoter enabled updated to: {enabled}")

    @Slot(result=str)
    def getLocalIPAddress(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @Slot(result=str)
    def getWebRemoterQRCode(self):
        try:
            ip = self.getLocalIPAddress()
            url = f"http://{ip}:25252/"
            import subprocess
            result = subprocess.run(
                ["qrencode", "-t", "SVG", "-o", "-", "-s", "6", "-m", "1", url],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 and result.stdout:
                import base64
                return "data:image/svg+xml;base64," + base64.b64encode(result.stdout).decode()
        except Exception:
            pass
        try:
            import qrcode
            import io
            import base64
            ip = self.getLocalIPAddress()
            url = f"http://{ip}:25252/"
            qr = qrcode.QRCode(version=1, box_size=6, border=1)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        except Exception:
            return ""

    @Slot(result=bool)
    def isSystemTrayAvailable(self):
        try:
            return QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            return False

    @Slot(result=int)
    def getGamepadMoveSensitivity(self):
        try:
            config_data = cfg.read()
            return config_data.get('gamepad_move_sensitivity', 50)
        except Exception:
            return 50

    @Slot(int)
    def setGamepadMoveSensitivity(self, value):
        try:
            config_data = cfg.read()
            config_data['gamepad_move_sensitivity'] = max(10, min(100, value))
            cfg.write(config_data)
        except Exception as e:
            print(f"setGamepadMoveSensitivity failed: {e}")

    @Slot(result=int)
    def getGamepadViewSensitivity(self):
        try:
            config_data = cfg.read()
            return config_data.get('gamepad_view_sensitivity', 50)
        except Exception:
            return 50

    @Slot(int)
    def setGamepadViewSensitivity(self, value):
        try:
            config_data = cfg.read()
            config_data['gamepad_view_sensitivity'] = max(10, min(100, value))
            cfg.write(config_data)
        except Exception as e:
            print(f"setGamepadViewSensitivity failed: {e}")

    @Slot(result=str)
    def getGamepadButtonLayout(self):
        try:
            config_data = cfg.read()
            return config_data.get('gamepad_button_layout', 'default')
        except Exception:
            return 'default'

    @Slot(str)
    def setGamepadButtonLayout(self, layout):
        try:
            config_data = cfg.read()
            config_data['gamepad_button_layout'] = layout
            cfg.write(config_data)
        except Exception as e:
            print(f"setGamepadButtonLayout failed: {e}")

    @Slot(result=str)
    def getGamepadLayoutData(self):
        try:
            config_data = cfg.read()
            layout_data = config_data.get('gamepad_layout_data', '')
            if not layout_data:
                # 返回默认布局
                default_layout = [
                    {"key": "space", "label": "跳跃", "x": 0.5, "y": 0.3, "size": 1.0},
                    {"key": "shift", "label": "潜行", "x": 0.2, "y": 0.5, "size": 1.0},
                    {"key": "e", "label": "E", "x": 0.8, "y": 0.1, "size": 0.8},
                    {"key": "q", "label": "Q", "x": 0.2, "y": 0.1, "size": 0.8},
                    {"key": "f", "label": "F", "x": 0.7, "y": 0.5, "size": 0.8},
                    {"key": "t", "label": "T", "x": 0.9, "y": 0.3, "size": 0.8}
                ]
                return json.dumps(default_layout)
            return layout_data
        except Exception as e:
            print(f"getGamepadLayoutData failed: {e}")
            return "[]"

    @Slot(str)
    def setGamepadLayoutData(self, layoutData):
        try:
            config_data = cfg.read()
            config_data['gamepad_layout_data'] = layoutData
            config_data['gamepad_button_layout'] = 'custom'
            cfg.write(config_data)
        except Exception as e:
            print(f"setGamepadLayoutData failed: {e}")

    # ========== 网络代理 ==========

    @Slot(result=str)
    def getProxy(self):
        config_data = cfg.read()
        return config_data.get('proxy', '')

    @Slot(str)
    def setProxy(self, proxy_addr):
        config_data = cfg.read()
        config_data['proxy'] = proxy_addr
        cfg.write(config_data)
        BLglobals.proxy = proxy_addr
        print(f"Proxy updated to: {proxy_addr or '(none)'}")

    @Slot(str)
    def queryUUID(self, name):
        print(f"Requested query UUID for name: {name}")
        def run_query():
            try:
                response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}")
                if response.status_code == 200:
                    data = response.json()
                    self.queryResultReceived.emit({"type": "uuid", "result": data.get("id"), "success": True})
                else:
                    self.queryResultReceived.emit({"type": "uuid", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "uuid", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def queryName(self, uuid):
        print(f"Requested query name for UUID: {uuid}")
        def run_query():
            try:
                response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
                if response.status_code == 200:
                    data = response.json()
                    self.queryResultReceived.emit({"type": "name", "result": data.get("name"), "success": True})
                else:
                    self.queryResultReceived.emit({"type": "name", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "name", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def querySkin(self, uuid):
        print(f"Requested query skin for UUID: {uuid}")
        def run_query():
            try:
                import base64
                response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
                if response.status_code == 200:
                    player_data = response.json()
                    properties = player_data.get("properties", [])
                    for prop in properties:
                        if prop["name"] == "textures":
                            textures = json.loads(base64.b64decode(prop["value"]).decode("utf-8"))
                            skin = textures["textures"].get("SKIN", {}).get("url")
                            cape = textures["textures"].get("CAPE", {}).get("url")
                            self.queryResultReceived.emit({"type": "textures", "skin": skin, "cape": cape, "success": True})
                            return
                    self.queryResultReceived.emit({"type": "textures", "success": False})
                else:
                    self.queryResultReceived.emit({"type": "textures", "success": False})
            except Exception as e:
                self.queryResultReceived.emit({"type": "textures", "success": False, "error": str(e)})
        threading.Thread(target=run_query, daemon=True).start()

    @Slot(str)
    def copyToClipboard(self, text):
        from PySide6.QtGui import QGuiApplication
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        print(f"Copied to clipboard: {text}")

    @Slot()
    def startEasytierHost(self):
        from modules.easytier import StartEasytierServer
        print("Requested start Easytier host")
        # For simplicity, using hardcoded/config-based name and secret
        def run_et():
            self.easytierStatusChanged.emit(i18nText("正在启动"), i18nText("请稍候..."))
            res = StartEasytierServer("Bloret", "123456") # Example defaults
            if "." in res: # Looks like an IP
                self.easytierStatusChanged.emit(i18nText("已连接"), i18nText("您的虚拟 IP: {ip}").replace("{ip}", res))
            else:
                self.easytierStatusChanged.emit(i18nText("错误"), res)
        threading.Thread(target=run_et, daemon=True).start()

    @Slot()
    def startEasytierClient(self):
        # Same as host for now in the simple view
        self.startEasytierHost()

    @Slot(result=list)
    def getFabricVersions(self):
        """从 .BL.json 读取 Fabric 版本列表，后备检查文件夹名"""
        try:
            config_data = cfg.read()
            mc_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            bl_json_path = os.path.join(mc_dir, "versions", ".BL.json")
            
            version_mappings = {}
            if os.path.exists(bl_json_path):
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                version_mappings = data.get("versions", {})
            
            fabric_versions = []
            versions_path = os.path.join(mc_dir, "versions")
            if os.path.exists(versions_path):
                for d in os.listdir(versions_path):
                    if not os.path.isdir(os.path.join(versions_path, d)):
                        continue
                    is_fabric = False
                    if d in version_mappings:
                        if version_mappings[d].get("Fabric", False):
                            is_fabric = True
                    if not is_fabric and "fabric" in d.lower():
                        is_fabric = True
                    if is_fabric:
                        fabric_versions.append(d)
            
            return sorted(fabric_versions, reverse=True)
        except Exception as e:
            print(f"Error getting Fabric versions: {e}")
            return []

    @Slot(str, str)
    def searchModrinth(self, query, category=""):
        from modules.modrinth import search_mods
        print(f"Modrinth search request: '{query}', category: '{category}'")
        def run_search():
            try:
                facets = None
                if category == "mod":
                    facets = [["project_type:mod"], ["categories:fabric"]]
                elif category:
                    facets = [[f"project_type:{category}"]]
                data = search_mods(query, facets=facets)
                results = []
                if isinstance(data, dict) and "hits" in data:
                    for hit in data["hits"]:
                        results.append({
                            "name": hit.get("title", "Unknown"),
                            "description": hit.get("description", ""),
                            "id": hit.get("project_id"),
                            "slug": hit.get("slug"),
                            "icon_url": hit.get("icon_url", ""),
                            "author": hit.get("author", ""),
                            "downloads": hit.get("downloads", 0),
                            "follows": hit.get("follows", 0),
                            "categories": hit.get("display_categories", []),
                            "project_type": hit.get("project_type", "mod")
                        })
                self.modrinthResultsReceived.emit(results)
            except Exception as e:
                print(f"Error searching Modrinth: {e}")
                self.modrinthResultsReceived.emit([])
        threading.Thread(target=run_search, daemon=True).start()

    def _resolve_game_version_for_folder(self, version_name, mc_dir=None):
        """从版本文件夹名 / .BL.json 解析纯 MC 版本号。"""
        import re
        if mc_dir is None:
            config_data = cfg.read()
            mc_dir = config_data.get("minecraft_dir", BLglobals.minecraft_dir)
        game_version = None
        bl_json_path = os.path.join(mc_dir, "versions", ".BL.json")
        if os.path.exists(bl_json_path):
            try:
                with open(bl_json_path, "r", encoding="utf-8") as f:
                    bl_data = json.load(f)
                if version_name in bl_data.get("versions", {}):
                    game_version = bl_data["versions"][version_name].get("version")
            except Exception as e:
                print(f"[ModInstall] 读取 .BL.json 失败: {e}")
        if not game_version:
            match = re.match(r"^(\d+\.\d+(\.\d+)?)", version_name or "")
            if match:
                game_version = match.group(1)
        return game_version

    def _download_one_mod(self, mod_id, version_name, progress_cb=None):
        """
        同步下载单个模组到 versions/{version_name}/mods。

        progress_cb(frac 0-1, status_str) 可选。
        Returns:
            tuple: (ok: bool, message: str)
        """
        from modules.modrinth import Get_Mod_File_Download_Url
        from modules.log import log as _log
        import logging as _logging

        try:
            config_data = cfg.read()
            mc_dir = config_data.get("minecraft_dir", BLglobals.minecraft_dir)
            game_version = self._resolve_game_version_for_folder(version_name, mc_dir)
            _log(
                f"[ModInstall] 下载 {mod_id} -> {version_name} (mc={game_version})",
                _logging.INFO,
            )
            if progress_cb:
                progress_cb(0.05, f"解析下载地址: {mod_id}")

            url = Get_Mod_File_Download_Url(
                mod_id,
                loaders=["fabric"],
                game_versions=[game_version] if game_version else None,
            )
            if not url:
                url = Get_Mod_File_Download_Url(
                    mod_id,
                    loaders=None,
                    game_versions=[game_version] if game_version else None,
                )
            if not url:
                msg = f"未找到 {mod_id} 的下载链接"
                _log(f"[ModInstall] {msg}", _logging.WARNING)
                return False, msg

            filename = url.split("/")[-1].split("?")[0]
            if not filename or "." not in filename:
                filename = f"{mod_id}.jar"
            if filename.endswith(".mrpack"):
                return False, f"{mod_id}: 得到 mrpack 而非 jar，已跳过"

            mods_dir = os.path.join(mc_dir, "versions", version_name, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            file_path = os.path.join(mods_dir, filename)

            if progress_cb:
                progress_cb(0.1, f"下载中: {filename}")

            with requests.get(url, timeout=120, stream=True) as response:
                if response.status_code != 200:
                    msg = f"{mod_id}: HTTP {response.status_code}"
                    _log(f"[ModInstall] {msg}", _logging.ERROR)
                    return False, msg
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                chunk_size = 64 * 1024
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total > 0:
                            frac = 0.1 + 0.9 * min(1.0, downloaded / total)
                            mb_d = downloaded / (1024 * 1024)
                            mb_t = total / (1024 * 1024)
                            progress_cb(frac, f"下载中: {filename} ({mb_d:.1f}/{mb_t:.1f} MB)")
                        elif progress_cb and downloaded % (512 * 1024) < chunk_size:
                            progress_cb(0.5, f"下载中: {filename} ({downloaded // 1024} KB)")

            _log(f"[ModInstall] 成功: {file_path}", _logging.INFO)
            return True, f"{filename} -> {mods_dir}"
        except Exception as e:
            _log(f"[ModInstall] 异常 {mod_id}: {e}", _logging.ERROR)
            import traceback
            traceback.print_exc()
            return False, str(e)

    @Slot(str, str)
    def downloadMod(self, mod_id, version_name):
        """
        下载并安装模组（带全局 DownloadDialog 进度）。
        """
        print(f"Requested download mod: {mod_id} to {version_name}")

        if getattr(self, "_mod_install_busy", False):
            self.downloadNotify.emit(
                self.tr("请稍候"),
                self.tr("已有模组安装任务进行中"),
                False,
            )
            return

        def run_download():
            self._mod_install_busy = True
            try:
                title = f"{self.tr('正在下载模组')}: {mod_id}"
                self.downloadDialogRequested.emit(title)
                # DownloadDialog ProgressBar 为 0–100
                self.downloadProgressUpdated.emit(0.0, self.tr("准备下载..."), "", "", "")

                def progress_cb(frac, status):
                    pct = float(max(0.0, min(1.0, frac))) * 100.0
                    self.downloadProgressUpdated.emit(pct, status or "", "", "", "")

                ok, message = self._download_one_mod(mod_id, version_name, progress_cb=progress_cb)
                if ok:
                    self.downloadCompleted.emit(f"{self.tr('下载成功')}: {message}")
                    self.downloadNotify.emit(self.tr("下载成功"), message, True)
                    try:
                        from modules.notification import send_notification
                        send_notification(self.tr("下载成功"), message, category="download")
                    except Exception:
                        pass
                else:
                    self.downloadCompleted.emit(f"{self.tr('下载失败')}: {message}")
                    self.downloadNotify.emit(self.tr("下载失败"), message, False)
                    try:
                        from modules.notification import send_notification
                        send_notification(self.tr("下载失败"), message, category="download")
                    except Exception:
                        pass
            finally:
                self._mod_install_busy = False

        threading.Thread(target=run_download, daemon=True).start()

    @Slot("QVariantList", str)
    def installModsBatch(self, slugs, version_name):
        """
        顺序安装多个模组，使用全局 DownloadDialog 展示总进度。
        供络可「一键安装全部」使用。
        """
        print(f"installModsBatch: {len(slugs or [])} mods -> {version_name}")
        from modules.log import log as _log
        import logging as _logging

        if not version_name:
            self.downloadNotify.emit(
                self.tr("安装失败"),
                self.tr("未选择目标 Fabric 版本"),
                False,
            )
            return

        # 规范化 slug 列表（QML 可能传入 list 或 QVariantList）
        cleaned = []
        seen = set()
        raw = slugs
        try:
            raw = list(slugs) if slugs is not None else []
        except Exception:
            raw = []
        for s in raw:
            slug = str(s).strip() if s is not None else ""
            if not slug or slug in seen:
                continue
            seen.add(slug)
            cleaned.append(slug)

        if not cleaned:
            self.downloadNotify.emit(self.tr("安装失败"), self.tr("没有可安装的模组"), False)
            return

        if getattr(self, "_mod_install_busy", False):
            self.downloadNotify.emit(
                self.tr("请稍候"),
                self.tr("已有模组安装任务进行中"),
                False,
            )
            return

        def run_batch():
            self._mod_install_busy = True
            total = len(cleaned)
            ok_list = []
            fail_list = []
            try:
                title = self.tr("安装推荐 Mods") + f" ({total})"
                _log(f"[ModInstall] batch 开始: n={total}, version={version_name}", _logging.INFO)
                self.downloadDialogRequested.emit(title)
                self.downloadProgressUpdated.emit(
                    0.0,
                    self.tr("准备安装...") + f" 0/{total}",
                    "",
                    "",
                    "",
                )

                for i, slug in enumerate(cleaned):
                    # 总进度 0–100
                    base_pct = (i / total) * 100.0
                    span_pct = (1.0 / total) * 100.0
                    status_prefix = self.tr("正在安装") + f" {i + 1}/{total}: {slug}"
                    _log(f"[ModInstall] batch [{i+1}/{total}] {slug}", _logging.INFO)
                    self.downloadProgressUpdated.emit(base_pct, status_prefix, "", "", "")

                    def progress_cb(frac, status, _base=base_pct, _span=span_pct, _prefix=status_prefix):
                        overall = _base + _span * float(max(0.0, min(1.0, frac)))
                        self.downloadProgressUpdated.emit(
                            overall,
                            f"{_prefix} — {status}" if status else _prefix,
                            "",
                            "",
                            "",
                        )

                    ok, message = self._download_one_mod(
                        slug, version_name, progress_cb=progress_cb
                    )
                    if ok:
                        ok_list.append(slug)
                        _log(f"[ModInstall] batch OK {slug}: {message}", _logging.INFO)
                    else:
                        fail_list.append(f"{slug} ({message})")
                        _log(f"[ModInstall] batch FAIL {slug}: {message}", _logging.WARNING)

                summary_parts = [
                    self.tr("成功") + f" {len(ok_list)}/{total}",
                ]
                if fail_list:
                    summary_parts.append(
                        self.tr("失败") + ": " + ", ".join(fail_list[:5])
                        + ("…" if len(fail_list) > 5 else "")
                    )
                summary = "；".join(summary_parts)
                _log(f"[ModInstall] batch 结束: {summary}", _logging.INFO)
                self.downloadCompleted.emit(summary)
                self.downloadNotify.emit(
                    self.tr("模组安装完成") if not fail_list else self.tr("模组安装结束（有失败）"),
                    summary,
                    len(fail_list) == 0,
                )
                try:
                    from modules.notification import send_notification
                    send_notification(
                        self.tr("模组安装完成") if not fail_list else self.tr("模组安装结束（有失败）"),
                        summary,
                        category="download",
                    )
                except Exception:
                    pass
            except Exception as e:
                _log(f"[ModInstall] batch 异常: {e}", _logging.ERROR)
                import traceback
                traceback.print_exc()
                self.downloadCompleted.emit(self.tr("安装失败") + f": {e}")
                self.downloadNotify.emit(self.tr("安装失败"), str(e), False)
            finally:
                self._mod_install_busy = False

        threading.Thread(target=run_batch, daemon=True).start()

    @Slot(str, str, str)
    def downloadToFile(self, mod_id, game_version, target_folder):
        """下载模组/资源到指定文件夹"""
        from modules.modrinth import Get_Mod_File_Download_Url
        print(f"Download to file: {mod_id}, game_version: {game_version}, folder: {target_folder}")

        def run_download():
            try:
                url = Get_Mod_File_Download_Url(mod_id, loaders=None, game_versions=[game_version] if game_version else None)
                if url:
                    filename = url.split('/')[-1]
                    if not filename or '.' not in filename:
                        filename = f"{mod_id}.jar"
                    if filename.endswith(".mrpack"):
                        filename = filename.replace(".mrpack", ".zip")
                    os.makedirs(target_folder, exist_ok=True)
                    file_path = os.path.join(target_folder, filename)
                    print(f"Downloading to: {file_path}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Successfully downloaded to: {file_path}")
                        self.downloadNotify.emit(self.tr("下载成功"), f"{self.tr('已下载')} {filename} -> {target_folder}", True)
                        try:
                            from modules.notification import send_notification
                            send_notification(self.tr("下载成功"), f"{filename} -> {target_folder}", category="download")
                        except Exception:
                            pass
                    else:
                        print(f"Failed to download: HTTP {response.status_code}")
                        self.downloadNotify.emit(self.tr("下载失败"), f"HTTP {response.status_code}", False)
                        try:
                            from modules.notification import send_notification
                            send_notification(self.tr("下载失败"), f"HTTP {response.status_code}", category="download")
                        except Exception:
                            pass
                else:
                    print(f"Could not find download URL for {mod_id}")
                    self.downloadNotify.emit(self.tr("下载失败"), f"{self.tr('未找到')} {mod_id} {self.tr('的下载链接')}", False)
                    try:
                        from modules.notification import send_notification
                        send_notification(self.tr("下载失败"), f"{self.tr('未找到')} {mod_id} {self.tr('的下载链接')}", category="download")
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error downloading: {e}")
                self.downloadNotify.emit(self.tr("下载失败"), str(e), False)
                try:
                    from modules.notification import send_notification
                    send_notification(self.tr("下载失败"), str(e), category="download")
                except Exception:
                    pass

        threading.Thread(target=run_download, daemon=True).start()

    @Slot(result=str)
    def selectFolder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            None,
            self.tr("选择保存文件夹"),
            ""
        )
        return folder if folder else ""

    @Slot(result=str)
    def getBloretPassPortUserName(self):
        config_data = cfg.read()
        if config_data.get('Bloret_PassPort_Login'):
            return config_data.get('Bloret_PassPort_UserName', 'Unknown')
        return i18nText("未登录")

    @Slot(result=bool)
    def getBloretPassPortLoginStatus(self):
        config_data = cfg.read()
        return config_data.get('Bloret_PassPort_Login', False)

    @Slot(result=str)
    def getPassPortName(self):
        return self.getBloretPassPortUserName()

    @Slot(result=str)
    def getPassPortAvatar(self):
        """获取用户头像 - 优先使用 PassPort 头像，备用使用 Minecraft 账户头像"""
        print(f"\n[getPassPortAvatar] 方法被调用")
        config_data = cfg.read()
        
        is_logged_in = config_data.get('Bloret_PassPort_Login')
        print(f"  登录状态: {is_logged_in}")
        if not is_logged_in:
            print(f"  未登录，返回空字符串")
            return ""
        
        username = config_data.get('Bloret_PassPort_UserName', '')
        print(f"  PassPort 用户名: {username}")
        if not username:
            print(f"  用户名为空，返回空字符串")
            return ""
        
        cache_dir = os.path.join(BLglobals.cache_path, 'avatars')
        print(f"  缓存目录: {cache_dir}")
        try:
            os.makedirs(cache_dir, exist_ok=True)
            print(f"  缓存目录已创建")
        except Exception as e:
            print(f"  创建缓存目录失败: {e}")
        
        cache_file = os.path.join(cache_dir, f"{username}_passport.png")
        print(f"  缓存文件路径: {cache_file}")
        
        # 从 config.json 读取头像 URL
        avatar_url = config_data.get('Bloret_PassPort_Avatar', '')
        print(f"  存储的头像 URL: {avatar_url if avatar_url else '(空)'}")
        
        # 如果有有效的头像 URL，尝试下载
        if avatar_url and (avatar_url.startswith('http://') or avatar_url.startswith('https://')):
            try:
                print(f"  开始从 PassPort 头像 URL 下载...")
                print(f"  请求 URL: {avatar_url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                }
                response = requests.get(avatar_url, timeout=10, headers=headers)
                print(f"  HTTP 响应状态码: {response.status_code}")
                print(f"  响应内容大小: {len(response.content)} bytes")
                
                if response.status_code == 200 and len(response.content) > 500:
                    # 保存到缓存
                    with open(cache_file, 'wb') as f:
                        f.write(response.content)
                    print(f"  PassPort 头像已保存到缓存文件")
                    
                    local_url = QUrl.fromLocalFile(cache_file).toString()
                    print(f"  返回本地文件 URL: {local_url}")
                    print(f"[getPassPortAvatar] 方法执行完成\n")
                    return local_url
                else:
                    print(f"  下载失败：HTTP {response.status_code} 或内容过小")
            except Exception as e:
                print(f"  下载头像异常: {type(e).__name__}: {e}")
        
        # 如果 PassPort 头像不可用，尝试使用 Minecraft 账户的头像
        print(f"  PassPort 头像不可用，尝试使用 Minecraft 账户头像...")
        mc_account_config = config_data.get("MinecraftAccount", {})
        accounts_list = mc_account_config.get("accounts", [])
        chosen_index = mc_account_config.get("chosen", 0)
        
        if accounts_list and 0 <= chosen_index < len(accounts_list):
            chosen_account = accounts_list[chosen_index]
            mc_uuid = chosen_account.get("uuid", "")
            mc_username = chosen_account.get("username", "")
            print(f"  选中的 Minecraft 账户: {mc_username}, UUID: {mc_uuid}")
            
            # 优先使用 UUID 获取头像
            avatar_identifier = mc_uuid if mc_uuid else mc_username
            if avatar_identifier:
                try:
                    # 使用 minotar.net 获取头像（更稳定）
                    fallback_url = f"https://minotar.net/helm/{avatar_identifier}/64"
                    print(f"  Minecraft 头像 URL: {fallback_url}")
                    response = requests.get(fallback_url, timeout=10, headers={"User-Agent": "BloretLauncher/1.0"})
                    print(f"  HTTP 响应状态码: {response.status_code}")
                    print(f"  响应内容大小: {len(response.content)} bytes")
                    
                    if response.status_code == 200 and len(response.content) > 500:
                        with open(cache_file, 'wb') as f:
                            f.write(response.content)
                        print(f"  Minecraft 头像已保存到缓存文件")
                        local_url = QUrl.fromLocalFile(cache_file).toString()
                        print(f"  返回本地文件 URL: {local_url}")
                        print(f"[getPassPortAvatar] 方法执行完成\n")
                        return local_url
                    else:
                        print(f"  Minecraft 头像下载失败：HTTP {response.status_code} 或内容过小")
                except Exception as e:
                    print(f"  Minecraft 头像下载异常: {type(e).__name__}: {e}")
        
        print(f"  所有方法都失败，返回空字符串")
        print(f"[getPassPortAvatar] 方法执行完成\n")
        return ""

    # Removed duplicate getPlayerName, getVanillaVersions, getFabricVersions, getJavaDownloadVersions, downloadJava
    # ensuring the correct implementations later in the file are used.
    pass

    @Slot()
    def loginBloretPassPort(self):
        from modules.links import Bloret_PassPort_Account_login
        Bloret_PassPort_Account_login()

    @Slot()
    def logoutBloretPassPort(self):
        from modules.Bloret_PassPort import Bloret_PassPort_Account_logout
        # We need to pass the main window or a mock for homeInterface
        config_data = cfg.read()
        prev_user = config_data.get("Bloret_PassPort_UserName") or ""
        config_data['Bloret_PassPort_Login'] = False
        config_data['Bloret_PassPort_UserName'] = ""
        config_data['Bloret_PassPort_PassWord'] = ""
        cfg.write(config_data)
        print("Logged out from Bloret PassPort")
        try:
            from modules.plugin_host.dispatch import invoke_hook
            invoke_hook("account.logout", {"username": prev_user, "source": "passport"})
            print(f"[PluginHost] account.logout user={prev_user}")
        except Exception as e:
            print(f"[PluginHost] account.logout 失败: {e}")
        # 发出信号以刷新 UI（不传递参数，让 QML 主动查询）
        self.minecraftAccountsChanged.emit([])

    @Slot()
    def refreshMinecraftAccounts(self):
        # 发出信号以刷新 UI
        self.minecraftAccountsChanged.emit([])

    @Slot(result=list)
    def getMinecraftAccounts(self):
        config_data = cfg.read()
        mc_data = config_data.get("MinecraftAccount", {})
        accounts = mc_data.get("accounts", [])
        chosen_idx = mc_data.get("chosen", 0)
        
        result = []
        for i, acc in enumerate(accounts):
            uuid = acc.get("uuid", "")
            # Generate avatar URL if UUID is present
            # 使用 minotar.net 的 helmet/avatar 接口，如果没有 UUID 则使用默认头像
            if uuid:
                avatar_url = f"https://minotar.net/helm/{uuid}/64"
            else:
                # 对于离线账户，使用用户名生成头像
                username = acc.get("username", "")
                if username:
                    avatar_url = f"https://minotar.net/helm/{username}/64"
                else:
                    avatar_url = ""
            result.append({
                "index": i,
                "name": acc.get("username", "Unknown"),
                "type": acc.get("type", "Offline"),
                "uuid": uuid,
                "avatarUrl": avatar_url,
                "isDefault": (i == chosen_idx)
            })
        return result

    @Slot(int)
    def setDefaultMinecraftAccount(self, index):
        config_data = cfg.read()
        if "MinecraftAccount" not in config_data:
            config_data["MinecraftAccount"] = {}
        config_data["MinecraftAccount"]["chosen"] = index
        cfg.write(config_data)
        print(f"Set default Minecraft account to index: {index}")
        self.minecraftAccountsChanged.emit([])

    @Slot()
    def manageAccountOnWebsite(self):
        QDesktopServices.openUrl(QUrl("https://passport.bloret.net/minecraft"))

    @Slot()
    def syncAccountFromPassPort(self):
        from modules.Bloret_PassPort import sync_bloret_passport_account_to_mc
        print("Requested sync account from PassPort")
        def run_sync():
            try:
                success = sync_bloret_passport_account_to_mc(None)
                if success:
                    self.minecraftAccountsChanged.emit([])
                    self.syncStatusChanged.emit("success")
                else:
                    self.syncStatusChanged.emit("error: " + i18nText("同步失败，请检查是否已登录 Bloret PassPort"))
            except Exception as e:
                print(f"Error syncing accounts: {e}")
                self.syncStatusChanged.emit(f"error: {str(e)}")
        threading.Thread(target=run_sync, daemon=True).start()

    @Slot(result=str)
    def getIpv6Address(self):
        from modules.setup_ui import get_ipv6_address
        addr = get_ipv6_address()
        return addr if addr else i18nText("无法获取 IPv6 地址")

    @Slot(result=str)
    def checkIpv6Address(self):
        return self.getIpv6Address()

    @Slot()
    def takeScreenCut(self):
        """截图功能"""
        from modules.ShortCut import ScreenShortCut
        from PySide6.QtCore import QTimer
        print("Requested screenshot")

        def start_screenshot():
            try:
                self._screenshot_widget = ScreenShortCut()
                if self._screenshot_widget is not None:
                    self._screenshot_widget.destroyed.connect(lambda *args: setattr(self, '_screenshot_widget', None))
            except Exception as e:
                print(f"Failed to start screenshot: {e}")

        # 使用 QTimer.singleShot 在主线程中执行截图，避免线程问题
        QTimer.singleShot(0, start_screenshot)

    @Slot(str, str)
    def startEasytierWithConfig(self, port, password):
        from modules.easytier import StartEasytierServer
        print(f"Starting EasyTier for MC port {port} with password {password}")
        
        config_data = cfg.read()
        if not config_data.get("Bloret_PassPort_Login"):
            self.easytierStatusChanged.emit(i18nText("未登录"), i18nText("请先在通行证页面登录"))
            return

        username = config_data.get("Bloret_PassPort_UserName", "")
        easytier_name = "BLClient" + username
        
        def run_et():
            self.easytierStatusChanged.emit(i18nText("正在启动"), i18nText("请稍候..."))
            res = StartEasytierServer(easytier_name, password)
            if "." in res: # Success with IP (contains IP address)
                self.easytierStatusChanged.emit(
                    i18nText("已连接"),
                    i18nText("您的虚拟 IP: {ip}\n共享端口: {port}").replace("{ip}", res).replace("{port}", str(port)),
                )
            elif res.startswith("~"): # Success without IP (local direct mode)
                # 移除 ~ 前缀，显示友好提示
                msg = res[1:]  # 移除 ~ 前缀
                self.easytierStatusChanged.emit(i18nText("已启动"), msg)
            else: # Error
                self.easytierStatusChanged.emit(i18nText("错误"), res)
        threading.Thread(target=run_et, daemon=True).start()

    @Slot(str, str)
    def joinEasytierWithConfig(self, host_name, password):
        # In EasyTier, joining is basically starting a server with same name/secret
        # But for the UI we might want to distinguish.
        self.startEasytierWithConfig("25565", password) # Join often doesn't need port redirect for the joiner

    @Slot(result=str)
    def getEasytierStatusTitle(self):
        return "未连接"

    @Slot(result=str)
    def getEasytierStatusDesc(self):
        return "您尚未连接到 Easytier 网络"

    @Slot(result=str)
    def getEasytierLinkTip(self):
        return ""

    @Slot(result=str)
    def getEasytierLinkShow(self):
        return ""

    @Slot(str)
    def openUrl(self, url):
        print(f"Requested to open URL: {url}")
        QDesktopServices.openUrl(QUrl(url))
        
    @Slot()
    def joinQQBloret(self):
        from modules.links import open_qq_link
        open_qq_link()

    @Slot()
    def joinQQCommunity(self):
        from modules.links import open_BLC_qq_link
        open_BLC_qq_link()

    @Slot()
    def openGithubOrg(self):
        from modules.links import open_github_bloret
        open_github_bloret()

    @Slot()
    def openGithubRepo(self):
        from modules.links import open_github_bloret_Launcher
        open_github_bloret_Launcher()

    # ==================== BBBS ====================

    @Slot(result=bool)
    def isBBBSAuthenticated(self):
        config_data = cfg.read()
        return bool(config_data.get('bbbs_session', ''))

    @Slot()
    def fetchBBBSSummary(self):
        def run():
            from modules.bbbs import fetch_summary
            try:
                data = fetch_summary()
                if data is not None:
                    self.bbbsSummaryReceived.emit(data if isinstance(data, dict) else {"text": str(data)})
                else:
                    self.bbbsErrorOccurred.emit(i18nText("无法获取每日摘要"))
            except Exception as e:
                self.bbbsErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def fetchBBBSLeaderboard(self):
        def run():
            from modules.bbbs import fetch_leaderboard_posts
            try:
                data = fetch_leaderboard_posts()
                self.bbbsLeaderboardReceived.emit(data or [])
            except Exception as e:
                self.bbbsErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def fetchBBBSAllPosts(self):
        def run():
            from modules.bbbs import fetch_all_posts
            try:
                data = fetch_all_posts()
                self.bbbsAllPostsReceived.emit(data or [])
            except Exception as e:
                self.bbbsErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    # ==================== Live ====================

    def _normalize_live_users(self, users_payload):
        users = []
        if isinstance(users_payload, dict):
            for username, state in users_payload.items():
                users.append({
                    "username": username,
                    "state": state if isinstance(state, dict) else {}
                })
        elif isinstance(users_payload, list):
            for item in users_payload:
                if isinstance(item, dict):
                    username = item.get("username") or item.get("name") or item.get("from")
                    if username:
                        users.append({
                            "username": username,
                            "state": item.get("state", {}) if isinstance(item.get("state"), dict) else {}
                        })
        return users

    def _normalize_live_chat_history(self, chat_history):
        if not isinstance(chat_history, list):
            return []

        normalized = []
        for item in chat_history:
            if not isinstance(item, dict):
                continue
            normalized.append({
                "type": "chat",
                "from": item.get("from", ""),
                "payload": {
                    "msg": item.get("msg", ""),
                    "msgId": item.get("msgId"),
                    "recalled": item.get("recalled", False),
                    "time": item.get("time"),
                }
            })
        return normalized

    def _emit_live_easytier_state(self, remote_state=None):
        try:
            from modules.easytier import get_live_session_snapshot, update_live_target
        except Exception:
            get_live_session_snapshot = None
            update_live_target = None

        if remote_state is not None:
            self._current_live_easytier_state = remote_state or {}

        merged = dict(self._current_live_easytier_state or {})
        session = get_live_session_snapshot() if get_live_session_snapshot else {}
        same_space = bool(session) and session.get("space_id") == (self._current_live_space_id or "")

        if same_space and session.get("mode") == "client" and update_live_target and merged.get("hostVirtualIp"):
            update_live_target(merged.get("hostVirtualIp"), merged.get("gamePort"))
            session = get_live_session_snapshot() if get_live_session_snapshot else session

        # 确保所有必要的字段都存在且类型正确（防止 QML undefined 错误）
        merged["active"] = bool(merged.get("enabled", False))
        merged["ready"] = bool(merged.get("hostVirtualIp") and merged.get("gamePort"))
        merged["hostAddress"] = merged.get("hostAddress") or (
            f"{merged.get('hostVirtualIp')}:{merged.get('gamePort')}"
            if merged.get("hostVirtualIp") and merged.get("gamePort")
            else ""
        )
        merged["localRunning"] = bool(same_space and session.get("running", False))
        merged["localMode"] = session.get("mode", "") if same_space else ""
        merged["localVirtualIp"] = session.get("virtual_ip", "") if same_space else ""
        merged["localProxyPort"] = session.get("proxy_port") if same_space else None
        merged["localGamePort"] = session.get("game_port") if same_space else None
        merged["localTargetAddress"] = session.get("target_address", "") if same_space else ""
        merged["localIsHost"] = bool(merged.get("localRunning", False) and merged.get("localMode") == "host")
        merged["localIsClient"] = bool(merged.get("localRunning", False) and merged.get("localMode") == "client")
        merged["localError"] = session.get("error", "") if same_space else ""

        self._current_live_easytier_merged_state = merged
        self.liveEasyTierStateChanged.emit(merged)
        return merged

    def _stop_live_easytier_publish_loop(self):
        self._live_easytier_publish_running = False

    def _start_live_easytier_publish_loop(self):
        if self._live_easytier_publish_thread and self._live_easytier_publish_thread.is_alive():
            log("[EasyTier Publish] 旧发布线程仍在运行，等待其结束", logging.WARNING)
            self._stop_live_easytier_publish_loop()
            self._live_easytier_publish_thread.join(timeout=5)

        self._live_easytier_publish_running = True
        space_id = self._current_live_space_id

        def run():
            from modules.bbbs_live import publish_space_easytier_endpoint
            from modules.easytier import get_live_session_snapshot, refresh_live_virtual_ip

            last_published = None
            loop_count = 0
            while self._live_easytier_publish_running and self._current_live_space_id == space_id:
                try:
                    loop_count += 1
                    snapshot = get_live_session_snapshot()
                    
                    # 详细日志用于诊断
                    if loop_count <= 3 or loop_count % 10 == 0:
                        log(f"[EasyTier Publish Loop #{loop_count}] space_id={snapshot.get('space_id')}, mode={snapshot.get('mode')}, running={snapshot.get('running')}", logging.DEBUG)
                    
                    if snapshot.get("space_id") != space_id:
                        log(f"[EasyTier Publish] 空间 ID 不匹配，停止发布循环", logging.INFO)
                        break
                    if snapshot.get("mode") != "host":
                        log(f"[EasyTier Publish] 模式不是 host（当前={snapshot.get('mode')}），停止发布循环", logging.INFO)
                        break
                    if not snapshot.get("running"):
                        log(f"[EasyTier Publish] EasyTier 未运行，停止发布循环", logging.INFO)
                        break

                    if not snapshot.get("virtual_ip"):
                        if loop_count <= 1:
                            log(f"[EasyTier Publish] 虚拟 IP 为空，刷新中...", logging.DEBUG)
                        refresh_live_virtual_ip()
                        snapshot = get_live_session_snapshot()

                    self._emit_live_easytier_state()

                    host_ip = snapshot.get("virtual_ip") or ""
                    game_port = snapshot.get("game_port")
                    
                    # 详细诊断日志
                    if loop_count <= 3 or loop_count % 10 == 0:
                        log(f"[EasyTier Publish] host_ip={host_ip}, game_port={game_port}", logging.DEBUG)
                    
                    if host_ip and game_port:
                        publish_key = f"{host_ip}:{game_port}"
                        if publish_key != last_published:
                            log(f"[EasyTier Publish] 上报端点: {publish_key}", logging.INFO)
                            result = publish_space_easytier_endpoint(space_id, host_ip, game_port)
                            if result and result.get("success"):
                                last_published = publish_key
                                log(f"[EasyTier Publish] 上报成功", logging.INFO)
                                self._emit_live_easytier_state(result.get("easytier", {}))
                            else:
                                log(f"[EasyTier Publish] 上报失败: {result}", logging.WARNING)
                    elif host_ip and not game_port:
                        if loop_count <= 1:
                            log(f"[EasyTier Publish] 有虚拟 IP ({host_ip}) 但无游戏端口，等待 Minecraft LAN 世界启动", logging.DEBUG)
                    
                    time.sleep(1)
                except Exception as e:
                    log(f"Live EasyTier 房主状态上报失败: {e}", logging.WARNING)
                    import traceback
                    log(f"[EasyTier Publish] 错误堆栈:\n{traceback.format_exc()}", logging.DEBUG)
                    time.sleep(2)

            log(f"[EasyTier Publish] 发布循环已停止（运行了 {loop_count} 次迭代）", logging.INFO)
            self._live_easytier_publish_running = False

        self._live_easytier_publish_thread = threading.Thread(target=run, daemon=True)
        self._live_easytier_publish_thread.start()
        log(f"[EasyTier Publish] 发布循环已启动，空间 ID: {space_id}", logging.INFO)

    @Slot()
    def fetchLiveSpaceList(self):
        def run():
            from modules.bbbs_live import fetch_space_list
            try:
                data = fetch_space_list()
                self._live_space_list_cache = data or []
                self.liveSpaceListReceived.emit(data or [])
            except Exception as e:
                self.liveErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    @Slot(result=bool)
    def isInLiveSpace(self):
        return bool(self._current_live_space_id)

    @Slot(result=dict)
    def getCurrentLiveSpace(self):
        return dict(self._current_live_space or {})

    @Slot(result=dict)
    def getCurrentLiveEasyTierState(self):
        return dict(self._current_live_easytier_merged_state or {})

    @Slot(result=str)
    def getCurrentLiveConnectionState(self):
        return self._current_live_connection_state or "disconnected"

    @Slot(str, str)
    def joinLiveSpace(self, spaceId, password):
        def run():
            from modules.bbbs_live import check_access, verify_password, LiveSSEClient, get_space_easytier_info
            try:
                if self._current_live_space_id and self._current_live_space_id != spaceId:
                    self.leaveLiveSpace()

                access = check_access(spaceId)
                if access and access.get('needsPassword'):
                    if password:
                        result = verify_password(spaceId, password)
                        if not result or not result.get('success'):
                            self.liveErrorOccurred.emit(i18nText("密码验证失败"))
                            return
                    else:
                        self.liveErrorOccurred.emit(i18nText("需要密码才能加入"))
                        return

                self._current_live_space_id = spaceId
                self._current_live_space = {}
                self._current_live_easytier_state = {}
                self._live_sse_client = LiveSSEClient(spaceId, self._handle_live_event)
                self._live_sse_client.start()
                self._current_live_connection_state = "connecting"
                self.liveConnectionStateChanged.emit("connecting")
                try:
                    from modules.plugin_host.hook_util import fire
                    fire("live.join", {"space_id": spaceId})
                except Exception as _pe:
                    log(f"[PluginHost] live.join 失败: {_pe}", logging.WARNING)

                # 立即用已有的空间信息发射 joinedSpace 信号，不等待服务器 init 事件
                space_name = access.get('spaceName', '') if access else ''
                username = self.getBloretPassPortUserName()

                # 从缓存的空间列表判断 isOwner
                is_owner = False
                for sp in self._live_space_list_cache:
                    if sp.get("id") == spaceId and sp.get("owner") == username:
                        is_owner = True
                        break

                initial_space = {
                    "id": spaceId,
                    "name": space_name,
                    "users": [{"username": username}],
                    "spaceName": space_name,
                    "chatHistory": [],
                    "easytier": {},
                    "isOwner": is_owner,
                }
                self._current_live_space = initial_space
                self.liveJoinedSpace.emit(initial_space)
                self._emit_live_easytier_state({})
                self._current_live_connection_state = "connected"
                self.liveConnectionStateChanged.emit("connected")

                # 用户进入房间后立即检测是否已有进行中的 EasyTier 网络
                try:
                    easytier_result = get_space_easytier_info(spaceId)
                    if easytier_result and easytier_result.get("success"):
                        self._emit_live_easytier_state(easytier_result.get("easytier", {}))
                except Exception as e:
                    log(f"加入 Live 后检测 EasyTier 状态失败: {e}", logging.DEBUG)
            except Exception as e:
                self.liveErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def leaveLiveSpace(self):
        current_space_id = self._current_live_space_id
        if self._live_sse_client:
            self._live_sse_client.stop()
            self._live_sse_client = None
        if self._live_webrtc_manager:
            self._live_webrtc_manager.stop()
            self._live_webrtc_manager = None
        self._stop_live_easytier_publish_loop()
        try:
            from modules.easytier import stop_live_session
            stop_live_session(space_id=current_space_id)
        except Exception as e:
            log(f"离开 Live 时停止 EasyTier 失败: {e}", logging.WARNING)
        self._current_live_space_id = None
        self._current_live_space = {}
        self._current_live_easytier_state = {}
        self._current_live_connection_state = "disconnected"
        self.liveLeftSpace.emit()
        self.liveEasyTierStateChanged.emit({})
        self.liveConnectionStateChanged.emit("disconnected")
        try:
            from modules.plugin_host.hook_util import fire
            fire("live.leave", {"space_id": current_space_id or ""})
        except Exception as _pe:
            log(f"[PluginHost] live.leave 失败: {_pe}", logging.WARNING)

    @Slot(str)
    def sendLiveChatMessage(self, message):
        def run():
            from modules.bbbs_live import send_signal
            import time
            import uuid
            try:
                # 生成唯一消息ID
                username = self.getBloretPassPortUserName()
                msg_id = f"{username}_{int(time.time()*1000)}_{str(uuid.uuid4())[:8]}"
                payload = {
                    "msg": message,
                    "msgId": msg_id
                }
                result = send_signal(self._current_live_space_id, {
                    "type": "chat",
                    "payload": payload
                })
                if result is None:
                    self.liveErrorOccurred.emit(i18nText("发送消息失败，请检查网络连接或服务器状态"))
                else:
                    # 在本地显示自己发送的消息(服务器不会广播给自己)
                    chat_history = list(self._current_live_space.get("chatHistory") or [])
                    chat_history.append({
                        "type": "chat",
                        "from": username,
                        "payload": payload
                    })
                    self._current_live_space["chatHistory"] = chat_history
                    self.liveChatMessageReceived.emit({
                        "type": "chat",
                        "from": username,
                        "payload": payload
                    })
                    try:
                        from modules.plugin_host.hook_util import fire
                        fire(
                            "live.chat",
                            {
                                "space_id": self._current_live_space_id,
                                "from": username,
                                "msg_id": msg_id,
                                # 不向插件暴露完整聊天内容以外的敏感字段
                            },
                        )
                    except Exception:
                        pass
            except Exception as e:
                self.liveErrorOccurred.emit(i18nText("发送消息失败: {error}").replace("{error}", str(e)))
        threading.Thread(target=run, daemon=True).start()

    @Slot(str)
    def createLiveSpace(self, name):
        def run():
            from modules.bbbs_live import create_space
            try:
                result = create_space(name)
                if result and result.get('success'):
                    self.fetchLiveSpaceList()
                else:
                    self.liveErrorOccurred.emit(i18nText("创建空间失败"))
            except Exception as e:
                self.liveErrorOccurred.emit(str(e))
        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def startLiveEasyTier(self):
        def run():
            from modules.bbbs_live import start_space_easytier, stop_space_easytier
            from modules.easytier import start_live_session, try_start_live_game_port_watch

            if not self._current_live_space_id:
                self.liveErrorOccurred.emit(i18nText("请先加入 Live 空间"))
                return

            try:
                result = start_space_easytier(self._current_live_space_id)
                if not result or not result.get("success"):
                    self.liveErrorOccurred.emit((result or {}).get("error", i18nText("开启 EasyTier 失败")))
                    return

                easytier_info = result.get("easytier", {})
                local_result = start_live_session(
                    mode="host",
                    network_name=easytier_info.get("networkName", ""),
                    network_secret=easytier_info.get("networkSecret", ""),
                    space_id=self._current_live_space_id,
                    space_name=self._current_live_space.get("name", ""),
                    host_username=self.getBloretPassPortUserName(),
                )
                if not local_result.get("success"):
                    if result.get("created"):
                        stop_space_easytier(self._current_live_space_id)
                    self.liveErrorOccurred.emit(local_result.get("message", i18nText("本地 EasyTier 启动失败")))
                    return

                self._emit_live_easytier_state(easytier_info)

                # 立即刷新一次状态，确保 UI 能快速响应本地运行状态
                import time
                time.sleep(0.5)
                self._emit_live_easytier_state()

                # 启动日志监听以捕获 Minecraft LAN 端口
                if try_start_live_game_port_watch():
                    log("已启动 Minecraft 日志监听，将自动捕获 LAN 端口", logging.INFO)

                log(f"[EasyTier] 本地会话已启动，准备启动发布循环，space_id={self._current_live_space_id}", logging.INFO)
                self._start_live_easytier_publish_loop()
                try:
                    from modules.plugin_host.hook_util import fire
                    fire(
                        "live.easytier.start",
                        {
                            "space_id": self._current_live_space_id,
                            "mode": "host",
                        },
                    )
                    fire("easytier.session.changed", {"mode": "host", "active": True})
                except Exception as _pe:
                    log(f"[PluginHost] live.easytier.start 失败: {_pe}", logging.WARNING)
            except Exception as e:
                log(f"[EasyTier] startLiveEasyTier 异常: {e}", logging.ERROR)
                import traceback
                log(f"[EasyTier] 堆栈: {traceback.format_exc()}", logging.ERROR)
                self.liveErrorOccurred.emit(i18nText("开启 EasyTier 失败: {error}").replace("{error}", str(e)))

        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def connectLiveEasyTier(self):
        def run():
            from modules.bbbs_live import get_space_easytier_info
            from modules.easytier import start_live_session

            if not self._current_live_space_id:
                self.liveErrorOccurred.emit(i18nText("请先加入 Live 空间"))
                return

            try:
                result = get_space_easytier_info(self._current_live_space_id)
                if not result or not result.get("success"):
                    self.liveErrorOccurred.emit((result or {}).get("error", i18nText("获取 EasyTier 信息失败")))
                    return

                easytier_info = result.get("easytier", {})
                if not easytier_info.get("enabled"):
                    self.liveErrorOccurred.emit(i18nText("房主尚未开启 EasyTier 网络"))
                    return
                if not easytier_info.get("hostVirtualIp") or not easytier_info.get("gamePort"):
                    self.liveErrorOccurred.emit(i18nText("房主已开启网络，但尚未在游戏中开放局域网"))
                    return

                local_result = start_live_session(
                    mode="client",
                    network_name=easytier_info.get("networkName", ""),
                    network_secret=easytier_info.get("networkSecret", ""),
                    space_id=self._current_live_space_id,
                    space_name=self._current_live_space.get("name", ""),
                    host_username=easytier_info.get("hostUsername", ""),
                    target_host_virtual_ip=easytier_info.get("hostVirtualIp", ""),
                    target_game_port=easytier_info.get("gamePort"),
                )
                if not local_result.get("success"):
                    self.liveErrorOccurred.emit(local_result.get("message", i18nText("连接 EasyTier 失败")))
                    return

                self._emit_live_easytier_state(easytier_info)
                
                # 立即刷新一次状态，确保 UI 能快速响应本地运行状态
                import time
                time.sleep(0.5)
                self._emit_live_easytier_state()
                try:
                    from modules.plugin_host.hook_util import fire
                    fire(
                        "live.easytier.connected",
                        {
                            "space_id": self._current_live_space_id,
                            "mode": "client",
                        },
                    )
                    fire("easytier.session.changed", {"mode": "client", "active": True})
                except Exception as _pe:
                    log(f"[PluginHost] live.easytier.connected 失败: {_pe}", logging.WARNING)
            except Exception as e:
                self.liveErrorOccurred.emit(i18nText("连接 EasyTier 失败: {error}").replace("{error}", str(e)))

        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def disconnectLiveEasyTier(self):
        def run():
            try:
                if self._current_live_space.get("isOwner"):
                    from modules.bbbs_live import stop_space_easytier
                    result = stop_space_easytier(self._current_live_space_id)
                    if result and result.get("easytier") is not None:
                        self._current_live_easytier_state = result.get("easytier", {})

                from modules.easytier import stop_live_session
                stop_live_session(space_id=self._current_live_space_id)
                self._stop_live_easytier_publish_loop()
                self._emit_live_easytier_state(self._current_live_easytier_state)
                try:
                    from modules.plugin_host.hook_util import fire
                    fire("live.easytier.stop", {"space_id": self._current_live_space_id})
                    fire("easytier.session.changed", {"active": False})
                except Exception as _pe:
                    log(f"[PluginHost] live.easytier.stop 失败: {_pe}", logging.WARNING)
            except Exception as e:
                self.liveErrorOccurred.emit(i18nText("断开 EasyTier 失败: {error}").replace("{error}", str(e)))

        threading.Thread(target=run, daemon=True).start()

    @Slot()
    def refreshLiveEasyTierState(self):
        def run():
            from modules.bbbs_live import get_space_easytier_info
            try:
                if not self._current_live_space_id:
                    self.liveEasyTierStateChanged.emit({})
                    return
                result = get_space_easytier_info(self._current_live_space_id)
                if result and result.get("success"):
                    self._emit_live_easytier_state(result.get("easytier", {}))
            except Exception as e:
                log(f"刷新 Live EasyTier 状态失败: {e}", logging.WARNING)
        threading.Thread(target=run, daemon=True).start()

    @Slot(int)
    def setLiveGamePort(self, port):
        """手动设置 Minecraft LAN 世界的端口（自动检测失败时使用）"""
        def run():
            from modules.easytier import set_live_game_port, get_live_session_snapshot
            try:
                if port > 0 and port <= 65535:
                    set_live_game_port(port)
                    log(f"已手动设置游戏端口: {port}", logging.INFO)
                    self._emit_live_easytier_state()
                    # 立即发布到服务器，确保网页端同步
                    if self._current_live_space_id:
                        snapshot = get_live_session_snapshot()
                        host_ip = snapshot.get("virtual_ip", "")
                        if host_ip and port:
                            try:
                                from modules.bbbs_live import publish_space_easytier_endpoint
                                result = publish_space_easytier_endpoint(self._current_live_space_id, host_ip, port)
                                if result and result.get("success"):
                                    log(f"[EasyTier] 手动设置端口后发布成功: {host_ip}:{port}", logging.INFO)
                                    self._emit_live_easytier_state(result.get("easytier", {}))
                                else:
                                    log(f"[EasyTier] 手动设置端口后发布失败: {result}", logging.WARNING)
                            except Exception as e:
                                log(f"[EasyTier] 手动设置端口后发布异常: {e}", logging.WARNING)
                else:
                    self.liveErrorOccurred.emit(i18nText("无效的端口号: {port}").replace("{port}", str(port)))
            except Exception as e:
                self.liveErrorOccurred.emit(i18nText("设置端口失败: {error}").replace("{error}", str(e)))
        threading.Thread(target=run, daemon=True).start()

    @Slot(bool)
    def toggleLiveAudio(self, enabled):
        if self._live_webrtc_manager:
            self._live_webrtc_manager.toggle_audio(enabled)

    @Slot(bool)
    def toggleLiveVideo(self, enabled):
        if self._live_webrtc_manager:
            self._live_webrtc_manager.toggle_video(enabled)

    def _handle_live_event(self, event):
        """分发 SSE 事件到对应的 Signal"""
        event_type = event.get("type", "")
        if event_type == "init":
            normalized_event = dict(event)
            normalized_event["users"] = self._normalize_live_users(event.get("users"))
            normalized_event["chatHistory"] = self._normalize_live_chat_history(event.get("chatHistory"))
            # 确保 isOwner 有值：服务端不返回时从缓存列表推算
            if "isOwner" not in normalized_event:
                username = self.getBloretPassPortUserName()
                space_id = normalized_event.get("id", "")
                is_owner = any(
                    sp.get("id") == space_id and sp.get("owner") == username
                    for sp in self._live_space_list_cache
                )
                normalized_event["isOwner"] = is_owner
            self._current_live_space = normalized_event
            self.liveJoinedSpace.emit(normalized_event)

            # 部分服务端 init 事件不会携带 easytier（或返回空对象），
            # 这里避免用空对象覆盖 join 阶段已拉取到的 EasyTier 状态。
            init_easytier = event.get("easytier")
            if isinstance(init_easytier, dict) and init_easytier:
                self._emit_live_easytier_state(init_easytier)
            else:
                self._emit_live_easytier_state()
            self._current_live_connection_state = "connected"
            self.liveConnectionStateChanged.emit("connected")
        elif event_type in ("user-joined", "user-left"):
            normalized_event = dict(event)
            normalized_event["user"] = {
                "username": event.get("from", ""),
                "state": event.get("state", {}) if isinstance(event.get("state"), dict) else {}
            }
            users = self._normalize_live_users(self._current_live_space.get("users"))
            username = normalized_event["user"].get("username", "")
            if event_type == "user-joined" and username:
                next_users = [user for user in users if user.get("username") != username]
                next_users.append(normalized_event["user"])
                self._current_live_space["users"] = next_users
            elif event_type == "user-left" and username:
                self._current_live_space["users"] = [
                    user for user in users if user.get("username") != username
                ]
            self.liveUserEvent.emit(normalized_event)
        elif event_type == "chat":
            normalized_event = dict(event)
            if not isinstance(normalized_event.get("payload"), dict):
                normalized_event["payload"] = {"msg": normalized_event.get("payload", "")}
            chat_history = list(self._current_live_space.get("chatHistory") or [])
            chat_history.append(normalized_event)
            self._current_live_space["chatHistory"] = chat_history
            self.liveChatMessageReceived.emit(normalized_event)
        elif event_type == "easytier-state":
            remote_state = {k: v for k, v in event.items() if k != "type"}
            self._emit_live_easytier_state(remote_state)
        elif event_type in ("offer", "answer", "ice-candidate"):
            if self._live_webrtc_manager:
                self._live_webrtc_manager.handle_signaling(event)
            self.liveSignalReceived.emit(event)
        elif event_type == "error":
            self.liveErrorOccurred.emit(event.get("message", i18nText("未知错误")))

    # ========== OOBE 相关方法 ==========

    @Slot(result=bool)
    def isFirstRun(self):
        """检查是否是首次运行 - 通过检查配置文件中是否有必要配置项来判断"""
        try:
            config_data = cfg.read()
            # 如果没有设置 minecraft_dir 或者 Java_Path，则认为是首次运行
            minecraft_dir = config_data.get("minecraft_dir", "")
            java_path = config_data.get("Java_Path", "")
            return not minecraft_dir or not java_path
        except Exception:
            return True

    @Slot()
    def completeOOBE(self):
        """标记 OOBE 已完成 - 从源配置文件复制默认配置，但保留用户已保存的数据"""
        try:
            import shutil
            # 从 modules.config 获取源配置文件路径
            source_config = cfg.source_config_path if hasattr(cfg, 'source_config_path') else str(SCRIPT_DIR / 'config.json')
            target_config = BLglobals.config_path
            
            # 首先保存用户在 OOBE 中已经设置的数据
            existing_config = cfg.read()
            existing_mc_account = existing_config.get("MinecraftAccount", {})
            existing_java_path = existing_config.get("Java_Path", "")
            existing_minecraft_dir = existing_config.get("minecraft_dir", "")
            existing_language = existing_config.get("language", "zh-cn")
            existing_passport_login = existing_config.get("Bloret_PassPort_Login", False)
            existing_passport_username = existing_config.get("Bloret_PassPort_UserName", "")
            existing_passport_admin = existing_config.get("Bloret_PassPort_Admin", False)
            existing_passport_avatar = existing_config.get("Bloret_PassPort_Avatar", "")
            existing_passport_password = existing_config.get("Bloret_PassPort_PassWord", "")
            
            if os.path.exists(source_config):
                # 复制默认配置文件
                shutil.copyfile(source_config, target_config)
                print(f"OOBE completed: Default config copied to {target_config}")
                
                # 读取复制的默认配置
                config_data = cfg.read()
                
                # 恢复用户在 OOBE 中已保存的数据
                if existing_mc_account.get("accounts") or existing_mc_account.get("chosen", -1) >= 0:
                    config_data["MinecraftAccount"] = existing_mc_account
                    print(f"Preserved MinecraftAccount: {existing_mc_account}")
                
                if existing_java_path:
                    config_data["Java_Path"] = existing_java_path
                    print(f"Preserved Java_Path: {existing_java_path}")
                
                if existing_minecraft_dir:
                    config_data["minecraft_dir"] = existing_minecraft_dir
                    print(f"Preserved minecraft_dir: {existing_minecraft_dir}")
                
                if existing_language and existing_language != "zh-cn":
                    config_data["language"] = existing_language
                    print(f"Preserved language: {existing_language}")
                
                # 保留 Bloret PassPort 登录状态
                if existing_passport_login:
                    config_data["Bloret_PassPort_Login"] = existing_passport_login
                    config_data["Bloret_PassPort_UserName"] = existing_passport_username
                    config_data["Bloret_PassPort_Admin"] = existing_passport_admin
                    if existing_passport_avatar:
                        config_data["Bloret_PassPort_Avatar"] = existing_passport_avatar
                    if existing_passport_password:
                        config_data["Bloret_PassPort_PassWord"] = existing_passport_password
                    print(f"Preserved PassPort login: {existing_passport_username}")
                
                # 标记首次运行完成
                config_data["first-run"] = False
                
                with open(target_config, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                print("OOBE completed: User data preserved")
            else:
                # 如果没有源配置文件，创建一个基本的，并保留用户数据
                config_data = {
                    "minecraft-part": ".minecraft",
                    "first-run": False,
                    "ver": "25.0",
                    "minecraft_dir": existing_minecraft_dir,
                    "Java_Path": existing_java_path,
                    "language": existing_language,
                    "MinecraftAccount": existing_mc_account,
                    "Bloret_PassPort_Login": existing_passport_login,
                    "Bloret_PassPort_UserName": existing_passport_username,
                    "Bloret_PassPort_Admin": existing_passport_admin,
                    "Bloret_PassPort_Avatar": existing_passport_avatar,
                    "Bloret_PassPort_PassWord": existing_passport_password
                }
                with open(target_config, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                print("OOBE completed: Created config with user data")
        
            # OOBE 完成后检查并修复 .BL.json
            try:
                from modules.install import repair_bl_json
                final_config = cfg.read()
                final_mc_dir = final_config.get('minecraft_dir', '')
                if final_mc_dir:
                    repair_bl_json(final_mc_dir)
                    print("OOBE completed: .BL.json checked and repaired")
            except Exception as e:
                print(f"OOBE .BL.json 检查失败: {e}")

        except Exception as e:
            print(f"Error completing OOBE: {e}")

    @Slot(result=str)
    def getDefaultMinecraftDir(self):
        """获取默认的 Minecraft 目录路径"""
        # 默认目录为 %appdata%/Bloret-Launcher/.minecraft
        return os.path.join(BLglobals.datapath, ".minecraft")

    @Slot(result=str)
    def selectMinecraftDirectory(self):
        """让用户选择 Minecraft 目录"""
        from PySide6.QtWidgets import QFileDialog
        default_dir = os.path.join(BLglobals.datapath, ".minecraft")
        selected_dir = QFileDialog.getExistingDirectory(
            None,
            self.tr("选择 Minecraft 游戏文件夹"),
            default_dir
        )
        if selected_dir:
            # 保存到配置
            try:
                config_data = cfg.read()
                config_data["minecraft_dir"] = selected_dir
                cfg.write(config_data)
                print(f"Minecraft directory set to: {selected_dir}")
                return selected_dir
            except Exception as e:
                print(f"Error saving minecraft directory: {e}")
        return ""

    @Slot(str)
    def setMinecraftDirectory(self, minecraft_dir):
        """设置 Minecraft 目录"""
        try:
            config_data = cfg.read()
            config_data["minecraft_dir"] = minecraft_dir
            cfg.write(config_data)
            print(f"Minecraft directory set to: {minecraft_dir}")
        except Exception as e:
            print(f"Error setting minecraft directory: {e}")

    @Slot(result=str)
    def getAppDataPath(self):
        """获取 AppData 路径"""
        import os
        return os.environ.get('APPDATA', '')

    @Slot()
    def checkJavaEnvironment(self):
        """检查 Java 运行环境"""
        def check_java():
            try:
                import subprocess
                import shutil
                
                java_path = ""
                
                # 1. 首先尝试从配置获取 Java 路径
                config_data = cfg.read()
                config_java_path = config_data.get("Java_Path", "")
                
                if config_java_path and os.path.exists(config_java_path):
                    java_path = config_java_path
                
                # 2. 如果配置中没有或无效，尝试在系统 PATH 中查找
                if not java_path:
                    # Windows 上需要查找 java.exe
                    java_exe = shutil.which("java")
                    if java_exe:
                        java_path = java_exe
                
                # 3. 尝试常见的 Java 安装路径 (Windows)
                if not java_path:
                    common_paths = []
                    
                    # Program Files 下的 Java
                    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
                    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
                    
                    def find_java_in_dir(base_dir):
                        """递归查找目录下的 java.exe，只搜索 Java 相关文件夹"""
                        found = []
                        java_keywords = ("java", "jdk", "jre", "zulu", "adopt", "corretto", "microsoft", "openjdk", "temurin", "graalvm")
                        try:
                            for folder in os.listdir(base_dir):
                                folder_path = os.path.join(base_dir, folder)
                                if os.path.isdir(folder_path) and folder.lower().startswith(java_keywords):
                                    # 首先检查直接子目录下的 bin/java.exe
                                    potential_path = os.path.join(folder_path, "bin", "java.exe")
                                    if os.path.exists(potential_path):
                                        found.append(potential_path)
                                    # 如果没有找到，递归检查子目录（最多 2 层）
                                    else:
                                        try:
                                            for subfolder in os.listdir(folder_path):
                                                subfolder_path = os.path.join(folder_path, subfolder)
                                                if os.path.isdir(subfolder_path):
                                                    potential_path = os.path.join(subfolder_path, "bin", "java.exe")
                                                    if os.path.exists(potential_path):
                                                        found.append(potential_path)
                                        except Exception:
                                            pass
                        except Exception:
                            pass
                        return found
                    
                    for base in [program_files, program_files_x86]:
                        if os.path.exists(base):
                            common_paths.extend(find_java_in_dir(base))
                    
                    # 检查 JAVA_HOME 环境变量
                    java_home = os.environ.get("JAVA_HOME", "")
                    if java_home:
                        potential_path = os.path.join(java_home, "bin", "java.exe")
                        if os.path.exists(potential_path):
                            common_paths.insert(0, potential_path)
                    
                    # 测试每个可能的路径
                    for potential_path in common_paths:
                        try:
                            result = subprocess.run(
                                [potential_path, "-version"],
                                capture_output=True,
                                text=True,
                                timeout=10,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                            if result.returncode == 0:
                                java_path = potential_path
                                break
                        except Exception:
                            continue
                
                # 4. 验证找到的 Java 是否可用
                if java_path:
                    try:
                        result = subprocess.run(
                            [java_path, "-version"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        if result.returncode == 0:
                            # 保存到配置
                            config_data["Java_Path"] = java_path
                            cfg.write(config_data)
                            print(f"Java found: {java_path}")
                            self.javaEnvironmentChecked.emit(True, java_path)
                            return
                    except Exception as e:
                        print(f"Error validating Java: {e}")
                
                # 未找到有效的 Java
                print("Java not found")
                self.javaEnvironmentChecked.emit(False, "")
            except Exception as e:
                print(f"Error checking Java environment: {e}")
                self.javaEnvironmentChecked.emit(False, "")

        threading.Thread(target=check_java, daemon=True).start()

    @Slot(str)
    def installJava(self, version="21"):
        """安装指定版本的 Java"""
        def install_java():
            try:
                from modules.java import InstallJava
                
                # 我们使用 modules.java 中的安装逻辑，但需要监听安装完成状态
                # 这里简化处理，假设安装会在完成后通知
                InstallJava(version)
                
                # 等待一段时间后检查安装结果
                import time
                time.sleep(5)  # 给安装一些时间
                
                # 重新检查 Java 环境
                self.checkJavaEnvironment()
                
                # 发射安装完成信号
                config_data = cfg.read()
                java_path = config_data.get("Java_Path", "")
                if java_path:
                    self.javaInstallationComplete.emit(java_path)
                else:
                    self.javaInstallationComplete.emit("")
            except Exception as e:
                print(f"Error installing Java: {e}")
                self.javaInstallationComplete.emit("")

        threading.Thread(target=install_java, daemon=True).start()

    @Slot(result=bool)
    def getMinecraftAccountSynced(self):
        """检查 Minecraft 账户是否已同步"""
        try:
            config_data = cfg.read()
            mc_account_config = config_data.get("MinecraftAccount", {})
            accounts_list = mc_account_config.get("accounts", [])
            return len(accounts_list) > 0 and mc_account_config.get("chosen", -1) >= 0
        except Exception:
            return False

    @Slot()
    def syncMinecraftAccount(self):
        """同步 Minecraft 账户"""
        def sync_account():
            try:
                from modules.Bloret_PassPort import sync_bloret_passport_account_to_mc
                sync_bloret_passport_account_to_mc(parent_window=None)
                self.minecraftAccountsChanged.emit([])
            except Exception as e:
                print(f"Error syncing Minecraft account: {e}")

        threading.Thread(target=sync_account, daemon=True).start()

    @Slot(result=str)
    def getConfigLanguage(self):
        """获取当前配置的语言"""
        try:
            config_data = cfg.read()
            return config_data.get("language", "zh-cn")
        except Exception:
            return "zh-cn"

    @Slot(str)
    def setLanguage(self, language):
        """设置界面语言"""
        try:
            config_data = cfg.read()
            config_data["language"] = language
            cfg.write(config_data)
            
            # 重新加载语言数据
            from modules.i18n import reload_language
            reload_language(language)
            
            self.languageChanged.emit()
            print(f"Language set to: {language}")
        except Exception as e:
            print(f"Error setting language: {e}")

    @Slot()
    def restartApp(self):
        """重启程序（从设置页面调用）"""
        if hasattr(self, 'parent') and self.parent is not None:
            self.parent.restart_app()

    @Slot()
    def shutdownApp(self):
        """关闭/退出程序（从设置页面调用）"""
        if hasattr(self, 'parent') and self.parent is not None:
            self.parent.quit_app()


class LauncherTrayIcon(QSystemTrayIcon):
    """RinUI 版系统托盘图标与菜单"""

    def __init__(self, main_window):
        app_instance = QApplication.instance()
        if app_instance is not None:
            super().__init__(app_instance)
        else:
            super().__init__()

        self.main_window = main_window
        self._is_refreshing_launch_menu = False
        self._trigger_reason = self._resolve_trigger_reason()
        self._context_reason = self._resolve_context_reason()

        icon_path = get_app_icon_path(for_tray=True)
        if icon_path:
            self.setIcon(QIcon(str(icon_path)))
        else:
            self.setIcon(main_window.windowIcon())

        self.setToolTip("Bloret Launcher")

        self.menu = RoundMenu()
        self.launch_menu = RoundMenu(i18nText("🔼  启动版本"), self.menu)
        self.menu.addMenu(self.launch_menu)

        # 初始化时填充一次，确保菜单首次显示时有内容
        self._refresh_launch_menu()
        # 之后每次子菜单展开时刷新，保持版本列表最新
        self.launch_menu.aboutToShow.connect(self._refresh_launch_menu)

        self.menu.addSeparator()
        self.menu.addAction(Action(i18nText('🔡  访问 BBS'), self.menu, triggered=links.open_BBBS_link))
        self.menu.addAction(Action(i18nText('🔡  访问 Bloret PassPort'), self.menu, triggered=links.open_PassPort_link))
        self.menu.addAction(Action(i18nText('🔡  访问 百络图床'), self.menu, triggered=links.open_BIMG_WEB_link))

        self.menu.addSeparator()
        self.menu.addAction(Action(i18nText('🔄️  重启程序'), self.menu, triggered=self.main_window.restart_app))
        self.menu.addAction(Action(i18nText('✅  显示窗口'), self.menu, triggered=self.main_window.show_main_window))
        self.menu.addAction(Action(i18nText('❎  退出程序'), self.menu, triggered=self.main_window.quit_app))

        # 注册为系统托盘的上下文菜单（Linux 下必须，否则菜单内容为空）
        self.setContextMenu(self.menu)

        self.activated.connect(self._on_tray_activated)

    @staticmethod
    def _resolve_trigger_reason():
        """兼容不同 PySide 版本的枚举写法。"""
        reason_enum = getattr(QSystemTrayIcon, "ActivationReason", None)
        if reason_enum is not None and hasattr(reason_enum, "Trigger"):
            return reason_enum.Trigger
        return getattr(QSystemTrayIcon, "Trigger", None)

    @staticmethod
    def _resolve_context_reason():
        reason_enum = getattr(QSystemTrayIcon, "ActivationReason", None)
        if reason_enum is not None and hasattr(reason_enum, "Context"):
            return reason_enum.Context
        return getattr(QSystemTrayIcon, "Context", None)

    def _refresh_launch_menu(self):
        if self._is_refreshing_launch_menu:
            return

        self._is_refreshing_launch_menu = True
        self.launch_menu.clear()

        try:
            unique_versions = self._get_tray_launch_versions()
            if not unique_versions:
                empty_action = Action(i18nText("暂无可启动版本"), self.launch_menu)
                empty_action.setEnabled(False)
                self.launch_menu.addAction(empty_action)
                return

            for version in unique_versions:
                action = Action(
                    version,
                    self.launch_menu,
                    triggered=lambda checked=False, v=version: self.main_window.launch_version_from_tray(v),
                )
                self.launch_menu.addAction(action)

        except Exception as e:
            print(f"Failed to refresh tray launch menu: {e}")
            error_action = Action(i18nText("加载启动列表失败"), self.launch_menu)
            error_action.setEnabled(False)
            self.launch_menu.addAction(error_action)
        finally:
            self._is_refreshing_launch_menu = False

    @staticmethod
    def _get_tray_launch_versions():
        """仅收集托盘菜单需要的名称，避免右键时触发图标解析。"""
        version_names = []

        try:
            config_data = cfg.read()

            minecraft_dir = config_data.get('minecraft_dir', BLglobals.minecraft_dir)
            versions_dir = os.path.join(minecraft_dir, "versions")

            if os.path.isdir(versions_dir):
                for entry in os.listdir(versions_dir):
                    version_path = os.path.join(versions_dir, entry)
                    if os.path.isdir(version_path):
                        version_names.append(entry)

            customize_items = config_data.get("Customize", [])
            if isinstance(customize_items, list):
                for custom_item in customize_items:
                    if isinstance(custom_item, dict):
                        custom_name = str(custom_item.get("showname", "")).strip()
                        if custom_name:
                            version_names.append(custom_name)
        except Exception as e:
            print(f"Failed to collect tray launch versions: {e}")

        return list(dict.fromkeys(version_names))

    def _on_tray_activated(self, reason):
        try:
            is_trigger = self._reason_equals(reason, self._trigger_reason)
            if is_trigger:
                if self._is_window_hidden_or_minimized():
                    self.main_window.show_main_window()
                else:
                    root_window = getattr(self.main_window, "root_window", None)
                    if root_window is not None:
                        root_window.hide()
                    else:
                        self.main_window.hide()
                return

            is_context = self._reason_equals(reason, self._context_reason)
            if is_context:
                # 菜单已通过 setContextMenu(menu) 注册，由平台负责显示
                # 无需手动 popup（Linux 下 StatusNotifierItem 通过 DBus 获取菜单）
                return
        except Exception as e:
            print(f"Tray activation handler failed: {e}")

    def _is_window_hidden_or_minimized(self):
        """兼容 RinUI/QQuickWindow 的窗口状态判断，避免访问不存在的 QWidget API。"""
        root_window = getattr(self.main_window, "root_window", None)
        window_obj = root_window if root_window is not None else self.main_window

        is_visible = True
        try:
            if hasattr(window_obj, "isVisible"):
                is_visible = bool(window_obj.isVisible())
            elif hasattr(window_obj, "visible"):
                is_visible = bool(window_obj.visible)
        except Exception:
            is_visible = True

        is_minimized = False
        try:
            if hasattr(window_obj, "isMinimized"):
                is_minimized = bool(window_obj.isMinimized())
            elif hasattr(window_obj, "visibility"):
                visibility_value = window_obj.visibility()
                is_minimized = "Minimized" in str(visibility_value)
        except Exception:
            is_minimized = False

        return (not is_visible) or is_minimized

    @staticmethod
    def _reason_equals(reason, expected):
        if expected is None:
            return False

        if reason == expected:
            return True

        try:
            return int(reason) == int(expected)
        except Exception:
            return False

class LauncherV2(RinUIWindow):
    def __init__(self):
        super().__init__()
        self._force_quit = False
        self.tray_icon = None
        
        # Inject Backend to QML BEFORE loading
        self.backend = Backend()
        self.backend.setBackendParent(self)
        self.engine.rootContext().setContextProperty("Backend", self.backend)

        # Inject ResourcePackEditor Backend
        try:
            from modules.resourcepack_editor import ResourcePackEditorBackend
            self.rp_editor_backend = ResourcePackEditorBackend()
            self.engine.rootContext().setContextProperty("RPEditor", self.rp_editor_backend)
        except Exception as e:
            print(f"Failed to load ResourcePack Editor backend: {e}")

        # Inject AI Agent Backend
        try:
            from modules.resourcepack_editor.agent_backend import AgentBackend
            self.agent_backend = AgentBackend()
            self.engine.rootContext().setContextProperty("Agent", self.agent_backend)
            # 连接全局 AI 设置变化信号
            self.backend.globalAIProviderChanged.connect(self.agent_backend.onGlobalAIProviderChanged)
        except Exception as e:
            print(f"Failed to load AI Agent backend: {e}")

        # Inject Bloriko Agent Backend
        try:
            from modules.bloriko_agent import BlorikoBackend
            self.bloriko_backend = BlorikoBackend()
            self.engine.rootContext().setContextProperty("Bloriko", self.bloriko_backend)
            # 连接全局 AI 设置变化信号
            self.backend.globalAIProviderChanged.connect(self.bloriko_backend.onGlobalAIProviderChanged)
        except Exception as e:
            import traceback
            traceback.print_exc()

        # Inject Plugin Host
        try:
            from modules.plugin_host import bootstrap_plugins, get_plugin_host
            self.plugin_host = bootstrap_plugins()
            self.engine.rootContext().setContextProperty("PluginHost", self.plugin_host)
            print(f"[PluginHost] 已注入 QML，插件数={len(self.plugin_host.list_plugins_info())}")
        except Exception as e:
            import traceback
            print(f"[PluginHost] 初始化失败: {e}")
            traceback.print_exc()
            try:
                from modules.plugin_host import get_plugin_host
                self.plugin_host = get_plugin_host()
                self.engine.rootContext().setContextProperty("PluginHost", self.plugin_host)
            except Exception:
                self.engine.rootContext().setContextProperty("PluginHost", None)

        # 协议 / 商店 deep link：IPC 服务 + 冷启动 argv
        try:
            from modules.protocol_handler import (
                start_ipc_server,
                set_deep_link_handler,
                extract_bloret_urls,
                ensure_protocol_registered,
            )

            def _on_deep_link(url: str) -> None:
                print(f"[Protocol] 收到 deep link: {str(url)[:160]}")
                host = getattr(self, "plugin_host", None)
                if host is not None and hasattr(host, "handleDeepLink"):
                    try:
                        # 尽量在主线程处理，避免与 QML 竞态
                        from PySide6.QtCore import QMetaObject, Qt, Q_ARG

                        QMetaObject.invokeMethod(
                            host,
                            "handleDeepLink",
                            Qt.QueuedConnection,
                            Q_ARG(str, str(url)),
                        )
                    except Exception as inv_e:
                        print(f"[Protocol] invoke handleDeepLink 失败，直接调用: {inv_e}")
                        host.handleDeepLink(str(url))
                try:
                    self.show_main_window()
                except Exception:
                    pass

            set_deep_link_handler(_on_deep_link)
            start_ipc_server()
            # 幂等注册 bloret://（失败不阻断）
            ensure_protocol_registered()
            for _url in extract_bloret_urls():
                print(f"[Protocol] 冷启动 argv deep link: {_url[:120]}")
                if self.plugin_host is not None:
                    self.plugin_host.handleDeepLink(_url)
        except Exception as e:
            print(f"[Protocol] 初始化失败: {e}")
        
        # 启动时后台检查并修复 .BL.json（不阻塞首帧）
        def _repair_bl_json_bg():
            try:
                from modules.install import repair_bl_json
                config_data = cfg.read()
                mc_dir = config_data.get('minecraft_dir', '')
                if mc_dir:
                    repair_bl_json(mc_dir)
            except Exception as e:
                print(f"启动时 .BL.json 检查失败: {e}")

        threading.Thread(target=_repair_bl_json_bg, daemon=True, name="RepairBLJson").start()
        
        qml_file = SCRIPT_DIR / "qml" / "main.qml"
        
        # 调试信息（默认安静；BLORET_DEBUG=1 时详细输出）
        _debug_boot = os.environ.get("BLORET_DEBUG", "").strip() in ("1", "true", "TRUE", "yes")
        if _debug_boot:
            print(f"[DEBUG] SCRIPT_DIR: {SCRIPT_DIR}")
            print(f"[DEBUG] QML file path: {qml_file}")
            print(f"[DEBUG] QML file exists: {qml_file.exists()}")
            print(f"[DEBUG] sys.frozen: {getattr(sys, 'frozen', False)}")
            print(f"[DEBUG] sys.__nuitka_binary_dir: {getattr(sys, '__nuitka_binary_dir', 'NOT SET')}")
            print(f"[DEBUG] RINUI_PATH: {RINUI_PATH}")
            print(f"[DEBUG] RINUI_PATH exists: {RINUI_PATH.exists()}")
            qml_dir = SCRIPT_DIR / "qml"
            if qml_dir.exists():
                print(f"[DEBUG] QML directory contents: {list(qml_dir.iterdir())}")
            else:
                print(f"[DEBUG] QML directory not found at {qml_dir}")
        elif not qml_file.exists():
            print(f"[Boot] QML file missing: {qml_file}")
        
        self.load(str(qml_file))
        
        icon_path = get_app_icon_path()
        if icon_path:
            self.setIcon(str(icon_path))
        self.setProperty("title", "Bloret Launcher")

        self._init_system_tray()

        # UI 就绪后：异步刷新服务器 IP + 检查更新
        try:
            modules.IP.refresh_server_ip_async()
        except Exception as e:
            print(f"[Boot] 后台刷新服务器 IP 失败: {e}")
        self.backend.checkForUpdates()

    def _read_minimize_to_tray_on_close(self):
        minimize_to_tray = True
        try:
            if self.backend:
                minimize_to_tray = bool(self.backend.getMinimizeToTrayOnClose())
        except Exception:
            minimize_to_tray = True
        return minimize_to_tray

    def _can_hide_to_tray(self):
        return bool(self.tray_icon and self.tray_icon.isVisible())

    def _should_hide_to_tray_on_close(self):
        return self._read_minimize_to_tray_on_close() and self._can_hide_to_tray()

    def handle_close_request_from_qml(self):
        """由 QML onClosing 调用，返回 True 表示已拦截关闭并隐藏到托盘。"""
        if self._force_quit:
            return False

        if self._should_hide_to_tray_on_close():
            self.hide()
            return True

        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        return False

    @staticmethod
    def _reject_close_event(event):
        if event is None:
            return

        try:
            if hasattr(event, "setAccepted"):
                event.setAccepted(False)
                return
        except Exception:
            pass

        try:
            if hasattr(event, "ignore"):
                event.ignore()
                return
        except Exception:
            pass

        try:
            if hasattr(event, "accepted"):
                event.accepted = False
        except Exception:
            pass

    def _init_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this platform")
            return

        self.tray_icon = LauncherTrayIcon(self)
        self.tray_icon.show()

    def launch_version_from_tray(self, version):
        if version and self.backend:
            self.backend.launchGame(version)

    def show_main_window(self):
        root_window = getattr(self, "root_window", None)
        window_obj = root_window if root_window is not None else self

        try:
            if hasattr(window_obj, "show"):
                window_obj.show()
            else:
                self.show()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "showNormal"):
                window_obj.showNormal()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "raise_"):
                window_obj.raise_()
        except Exception:
            pass

        try:
            if hasattr(window_obj, "requestActivate"):
                window_obj.requestActivate()
            elif hasattr(window_obj, "activateWindow"):
                window_obj.activateWindow()
        except Exception:
            pass

    def quit_app(self):
        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        try:
            host = getattr(self, "plugin_host", None)
            if host is not None and hasattr(host, "shutdown"):
                print("[PluginHost] quit_app -> shutdown")
                host.shutdown()
        except Exception as e:
            print(f"[PluginHost] quit_app shutdown 失败: {e}")
        QApplication.quit()

    def restart_app(self):
        """关闭并重新启动。

        必须先释放单实例锁，再拉起新进程，并尽快退出当前进程。
        否则新实例会在旧实例尚未退出时撞上「不允许重复启动」检测。
        """
        # 重启标记：新实例若仍短暂检测到旧锁，会等待而不是直接拦截
        restart_flag = "--from-restart"

        if getattr(sys, "frozen", False):
            raw_args = list(sys.argv[1:])
        else:
            raw_args = list(sys.argv)

        # 去掉可能残留的重启标记，避免叠加
        filtered = [a for a in raw_args if a != restart_flag]
        args = [sys.executable] + filtered + [restart_flag]

        # 尽量优雅清理插件宿主
        try:
            host = getattr(self, "plugin_host", None)
            if host is not None and hasattr(host, "shutdown"):
                host.shutdown()
        except Exception as e:
            print(f"[Restart] plugin_host.shutdown 失败: {e}")

        if self.tray_icon:
            try:
                self.tray_icon.hide()
            except Exception:
                pass

        # 关键：先释放单实例互斥/文件锁，再启动新进程
        try:
            release_single_instance_lock()
        except Exception as e:
            print(f"[Restart] 释放单实例锁失败: {e}")

        kwargs = {"shell": False}
        if sys.platform == "win32":
            kwargs = hidden_process_kwargs(
                **kwargs,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
        else:
            kwargs["start_new_session"] = True

        try:
            subprocess.Popen(args, **kwargs)
        except Exception as e:
            print(f"[Restart] 启动新进程失败: {e}")
            # 启动失败时仍退出当前实例，避免卡在半重启状态
            os._exit(1)

        # 立即硬退出：QApplication.quit() 是异步的，窗口/事件循环收尾期间
        # 新实例仍可能看到旧进程存活，从而被防重复启动拦截
        os._exit(0)

    def closeEvent(self, event):
        if self._force_quit:
            try:
                super().closeEvent(event)
            except Exception:
                event.accept()
            return

        if self._should_hide_to_tray_on_close():
            try:
                event.ignore()
            except Exception:
                self._reject_close_event(event)
            self.hide()
            return

        self._force_quit = True
        if self.tray_icon:
            self.tray_icon.hide()
        try:
            host = getattr(self, "plugin_host", None)
            if host is not None and hasattr(host, "shutdown"):
                print("[PluginHost] closeEvent -> shutdown")
                host.shutdown()
        except Exception as e:
            print(f"[PluginHost] closeEvent shutdown 失败: {e}")
        try:
            super().closeEvent(event)
        except Exception:
            event.accept()

# --- 单实例锁：供启动检测与「重启」时主动释放 ---
RESTART_ARGV_FLAG = "--from-restart"
_single_instance_mutex = None  # Windows HANDLE
_single_instance_lock_file = None  # Linux/macOS 锁文件对象
_SINGLE_INSTANCE_MUTEX_NAME = "Global\\BloretLauncherMutex"


def release_single_instance_lock():
    """释放本进程持有的单实例互斥/文件锁，便于重启后的新实例立刻启动。"""
    global _single_instance_mutex, _single_instance_lock_file

    if sys.platform == "win32":
        if _single_instance_mutex:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(_single_instance_mutex)
            except Exception as e:
                print(f"[SingleInstance] CloseHandle 失败: {e}")
            _single_instance_mutex = None
        return

    if _single_instance_lock_file is not None:
        try:
            import fcntl
            try:
                fcntl.lockf(_single_instance_lock_file, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                _single_instance_lock_file.close()
            except Exception:
                pass
        except Exception as e:
            print(f"[SingleInstance] 解锁失败: {e}")
        _single_instance_lock_file = None


def _acquire_single_instance_lock():
    """尝试获取单实例锁。返回 (already_running: bool)。"""
    global _single_instance_mutex, _single_instance_lock_file

    if sys.platform == "win32":
        import ctypes
        # 先丢掉旧句柄，避免重试时泄漏
        if _single_instance_mutex:
            try:
                ctypes.windll.kernel32.CloseHandle(_single_instance_mutex)
            except Exception:
                pass
            _single_instance_mutex = None

        handle = ctypes.windll.kernel32.CreateMutexW(
            None, False, _SINGLE_INSTANCE_MUTEX_NAME
        )
        # ERROR_ALREADY_EXISTS = 183
        already = bool(handle) and ctypes.windll.kernel32.GetLastError() == 183
        _single_instance_mutex = handle
        return already

    import fcntl
    import tempfile

    if _single_instance_lock_file is None:
        lock_path = os.path.join(tempfile.gettempdir(), "bloret.lock")
        _single_instance_lock_file = open(lock_path, "w")
    try:
        fcntl.lockf(_single_instance_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except OSError:
        return True


def _wait_for_single_instance_after_restart(timeout_s: float = 30.0) -> bool:
    """重启场景下轮询获取单实例锁，直到成功或超时。成功返回 True。"""
    import time

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        already = _acquire_single_instance_lock()
        if not already:
            print("[SingleInstance] 重启等待：已取得单实例锁")
            return True
        # Windows 下若仍拿到「已存在」的句柄，先关掉再等，避免占着引用
        if sys.platform == "win32" and _single_instance_mutex:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(_single_instance_mutex)
            except Exception:
                pass
            globals()["_single_instance_mutex"] = None
        time.sleep(0.15)
    print(f"[SingleInstance] 重启等待超时（{timeout_s}s），仍检测到其它实例")
    return False


if __name__ == "__main__":
    # app is already created at the top
    global_icon_path = get_app_icon_path()
    if global_icon_path:
        app.setWindowIcon(QIcon(str(global_icon_path)))

    # 是否由「重启」拉起：若短暂撞上旧实例锁，应等待而不是弹「请勿重复打开」
    _from_restart = RESTART_ARGV_FLAG in sys.argv
    if _from_restart:
        sys.argv = [a for a in sys.argv if a != RESTART_ARGV_FLAG]
        print("[SingleInstance] 检测到 --from-restart，将在锁冲突时等待旧实例退出")

    # --- Single-instance mutex ---
    _already_running = _acquire_single_instance_lock()

    if _already_running and _from_restart:
        _already_running = not _wait_for_single_instance_after_restart(30.0)

    if _already_running:
        # 优先转发 bloret:// deep link 给首实例，再退出（商店一键安装）
        try:
            from modules.protocol_handler import handle_second_instance_argv, extract_bloret_urls

            urls = extract_bloret_urls()
            if urls:
                print(f"[Protocol] 二次实例检测到 deep link x{len(urls)}，转发后退出")
                handle_second_instance_argv()
                sys.exit(0)
        except Exception as e:
            print(f"[Protocol] 二次实例转发失败: {e}")

        config_data = cfg.read()
        if not config_data.get('repeat_run', False):
            from PySide6.QtWidgets import QMessageBox
            box = QMessageBox()
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle(i18nText("Bloret Launcher 已在运行"))
            box.setText(i18nText(
                "Bloret Launcher 已经在运行中。\n请勿重复打开。"
            ))
            box.setStandardButtons(QMessageBox.Ok)
            box.open()  # non-modal
            box.finished.connect(lambda _: sys.exit(0))
            sys.exit(app.exec())

    launcher = LauncherV2()
    sys.exit(app.exec())
