try:
    from modules.compat_widgets import InfoBar, InfoBarPosition, ComboBox
except ImportError:
    InfoBar = None
    InfoBarPosition = None
    ComboBox = None
import logging, os, json, platform, requests, shutil, concurrent.futures, threading, time, psutil, subprocess, re, shlex
try:
    import send2trash
except ImportError:
    send2trash = None
# sip is not required for PySide6
from pathlib import Path
from modules.win11toast import notify, update_progress
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
import sys
from modules.customize import find_Customize
from modules.i18n import i18nText
from modules.install import (
    load_merged_version_json,
    ensure_runtime_files,
    _library_download_items,
    _version_sort_key,
)
import modules.globals as BLglobals
import modules.config as cfg # 确保导入了 config 模块
from modules.java_runtime import select_java_runtime

# Windows API 导入，用于获取窗口句柄
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    try:
        import win32gui # type: ignore
        import win32con # type: ignore
        import win32process # type: ignore
    except ImportError:
        pass
    try:
        # Import on module load (main Qt thread in normal app startup) so mwtool's
        # global QObject instances keep correct thread affinity.
        from modules import mwtool  # type: ignore
    except Exception as e:
        mwtool = None
        log(f"加载 mwtool 失败，将跳过 Minecraft 工具栏: {e}", logging.WARNING)
else:
    mwtool = None


def _mojang_os_context():
    from modules.platform_compat import mojang_arch, mojang_os_name

    return mojang_os_name(), mojang_arch()


def _prepare_system_lwjgl_natives(natives_path):
    """
    FreeBSD: copy/link system games/lwjgl3 .so files into the version natives dir.
    Raises FileNotFoundError with install hints when ports LWJGL is missing.
    """
    from modules.platform_compat import (
        probe_system_lwjgl,
        system_lwjgl_lib_dir,
        uses_system_lwjgl,
    )

    if not uses_system_lwjgl():
        return
    ok, message = probe_system_lwjgl()
    if not ok:
        log(message, logging.ERROR)
        raise FileNotFoundError(message)
    lib_dir = system_lwjgl_lib_dir()
    os.makedirs(natives_path, exist_ok=True)
    copied = 0
    for so_path in sorted(lib_dir.glob("*.so")):
        dest = os.path.join(natives_path, so_path.name)
        try:
            if os.path.lexists(dest):
                try:
                    os.remove(dest)
                except OSError:
                    pass
            try:
                os.symlink(str(so_path), dest)
            except OSError:
                shutil.copy2(str(so_path), dest)
            copied += 1
        except OSError as exc:
            log(f"复制系统 LWJGL native 失败 {so_path} -> {dest}: {exc}", logging.WARNING)
    if copied == 0:
        raise FileNotFoundError(
            f"系统 LWJGL 目录中无可复制的 .so: {lib_dir}。请安装: pkg install lwjgl3"
        )
    log(f"FreeBSD: 已注入系统 LWJGL natives ({copied} 个) -> {natives_path}")


def _rewrite_classpath_with_system_lwjgl(classpath):
    """
    FreeBSD: replace org.lwjgl jars on the classpath with ports jars when present.
    Mojang-bundled LWJGL jars may not match FreeBSD natives; prefer system jars.
    """
    from modules.platform_compat import system_lwjgl_jar_dir, uses_system_lwjgl

    if not uses_system_lwjgl():
        return classpath
    jar_dir = system_lwjgl_jar_dir()
    if not jar_dir.is_dir():
        return classpath

    # Map basename stem (without -sources / -natives-*) -> preferred jar path
    system_jars = {}
    for jar in jar_dir.glob("*.jar"):
        name = jar.name
        if name.endswith("-sources.jar") or "-natives-" in name:
            continue
        # e.g. lwjgl.jar, lwjgl-opengl.jar
        stem = name[:-4] if name.endswith(".jar") else name
        system_jars[stem.lower()] = str(jar)

    if not system_jars:
        return classpath

    rewritten = []
    replaced = 0
    for path in classpath:
        base = os.path.basename(path).lower()
        # Detect Mojang LWJGL artifact paths: .../lwjgl-3.3.x.jar or lwjgl-opengl-3.3.x.jar
        if "lwjgl" not in base:
            rewritten.append(path)
            continue
        # Strip version suffix: lwjgl-3.3.1.jar -> lwjgl ; lwjgl-opengl-3.3.1.jar -> lwjgl-opengl
        stem = base[:-4] if base.endswith(".jar") else base
        # Remove trailing -N.N.N or -N.N.N-beta...
        stem_no_ver = re.sub(r"-\d+(?:\.\d+)*(?:[-.].*)?$", "", stem)
        if stem_no_ver.startswith("lwjgl") and stem_no_ver in system_jars:
            new_path = system_jars[stem_no_ver]
            if os.path.abspath(new_path) != os.path.abspath(path):
                log(
                    f"FreeBSD: classpath 使用系统 LWJGL jar: {os.path.basename(path)} -> {new_path}",
                    logging.INFO,
                )
                replaced += 1
            rewritten.append(new_path)
        else:
            rewritten.append(path)
    if replaced:
        log(f"FreeBSD: 已替换 {replaced} 个 LWJGL classpath 条目为系统 jar")
    else:
        log("FreeBSD: 未匹配到可替换的 LWJGL jar（仍使用 Mojang 下载的 jar）", logging.WARNING)
    return rewritten


def _mojang_rule_matches(rule, features=None):
    """判断单条 Mojang rule 的条件是否匹配当前运行环境。"""
    os_rule = rule.get("os") or {}
    current_os, current_arch = _mojang_os_context()
    if os_rule.get("name") and os_rule["name"] != current_os:
        return False
    if os_rule.get("arch") and os_rule["arch"] != current_arch:
        return False
    if os_rule.get("version"):
        try:
            if not re.search(os_rule["version"], platform.version()):
                return False
        except re.error as e:
            log(f"忽略无效 Mojang OS version 规则 {os_rule['version']!r}: {e}", logging.WARNING)
            return False

    actual_features = features or {}
    for name, required in (rule.get("features") or {}).items():
        if bool(actual_features.get(name, False)) != bool(required):
            return False
    return True


def _mojang_rules_allow(rules, features=None):
    """按 Mojang 顺序规则求值；无 rules 时允许，有 rules 时默认拒绝，最后匹配项生效。"""
    if not rules:
        return True
    allowed = False
    for rule in rules:
        if _mojang_rule_matches(rule, features):
            allowed = rule.get("action") == "allow"
    return allowed


def _process_tree_pids(root_pid):
    if not root_pid:
        return None
    try:
        root = psutil.Process(root_pid)
        return {root.pid, *(child.pid for child in root.children(recursive=True))}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return set()


def _split_legacy_arguments(command_line):
    """按目标平台命令行规则解析旧 minecraftArguments。"""
    if os.name != "nt":
        return shlex.split(command_line, posix=True)
    try:
        shell32 = ctypes.windll.shell32
        shell32.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
        argc = ctypes.c_int()
        argv = shell32.CommandLineToArgvW(command_line, ctypes.byref(argc))
        if not argv:
            raise ctypes.WinError()
        try:
            return [argv[index] for index in range(argc.value)]
        finally:
            ctypes.windll.kernel32.LocalFree(argv)
    except Exception as e:
        log(f"CommandLineToArgvW 解析旧参数失败，回退 shlex: {e}", logging.WARNING)
        return [
            value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value
            for value in shlex.split(command_line, posix=False)
        ]


def Get_Run_Script(mc_version, skip_completion=False, cancellation_event=None):
    """
    根据 config.json 的内容生成启动 .minecraft 文件夹中指定版本的命令
    支持 Fabric 加载器启动
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        mc_version (str): 要启动的 Minecraft 版本号
        skip_completion (bool): 是否跳过文件补全，直接启动
        cancellation_event (threading.Event): 启动会话取消信号
        
    Returns:
        tuple: (launch_args, game_dir) 启动参数列表和工作目录
    """
    
    def raise_if_cancelled(stage):
        if cancellation_event is not None and cancellation_event.is_set():
            raise RuntimeError(f"启动会话已取消（{stage}）")

    raise_if_cancelled("读取配置前")

    # 1. 读取配置文件 (替代原有的 cmcl.json 读取)
    try:
        config_data = cfg.read()
    except Exception as e:
        raise FileNotFoundError(f"读取配置文件失败: {e}")
    
    # 获取 Minecraft 目录
    minecraft_dir = config_data.get('minecraft_dir', '')
    if not minecraft_dir:
        # 如果配置中没有指定，则使用默认路径
        minecraft_dir = os.path.join(BLglobals.datapath, '.minecraft')
    
    versions_dir = os.path.join(minecraft_dir, "versions", mc_version)
    
    # 检查版本目录是否存在
    if not os.path.exists(versions_dir):
        raise FileNotFoundError(f"版本 {mc_version} 不存在于 {versions_dir}")
    
    # 读取并合并 inheritsFrom 父版本 JSON
    version_data = load_merged_version_json(minecraft_dir, mc_version)
    raise_if_cancelled("版本 JSON 解析后")

    client_jar_path = os.path.join(versions_dir, f"{mc_version}.jar")
    natives_path = os.path.join(versions_dir, f"{mc_version}-natives")
    mods_dir = os.path.join(versions_dir, "mods")
    os.makedirs(natives_path, exist_ok=True)

    # 先选 Java（有缓存），避免无运行时仍下载补全
    java_requirement = version_data.get("javaVersion") or {}
    required_java_major = java_requirement.get("majorVersion")
    java_component = java_requirement.get("component", "")
    log(
        f"Minecraft {mc_version} Java 要求：component={java_component or '未声明'}，"
        f"major={required_java_major or '未声明'}"
    )
    legacy_java_dir = config_data.get("java_dir", "")
    extra_java_roots = [os.path.join(BLglobals.datapath, "runtime")]
    if legacy_java_dir:
        extra_java_roots.append(legacy_java_dir)
    java_info = select_java_runtime(config_data, required_java_major, extra_roots=extra_java_roots)
    java_path = java_info["path"]
    java_version = java_info["major"]
    log(f"Minecraft {mc_version} 最终 Java：{java_path}（Java {java_version}）")
    raise_if_cancelled("Java 选择后")

    # 运行时文件补全（库 / native / client / 轻量 assets）
    def _completion_progress(stage, current, total, message):
        log(f"[补全:{stage}] {message} ({current}/{total})", logging.DEBUG)

    ensure_runtime_files(
        minecraft_dir,
        version_data,
        mc_version,
        natives_dir=natives_path,
        cancellation_event=cancellation_event,
        progress_cb=_completion_progress,
        check_assets=True,
        check_client=True,
        skip_completion=skip_completion,
    )
    raise_if_cancelled("运行时文件补全后")

    # FreeBSD: inject system LWJGL natives (ports games/lwjgl3) after Mojang libs
    try:
        _prepare_system_lwjgl_natives(natives_path)
    except FileNotFoundError:
        raise
    except Exception as e:
        log(f"准备系统 LWJGL natives 失败: {e}", logging.ERROR)
        raise

    if not os.path.exists(client_jar_path):
        raise FileNotFoundError(f"客户端 JAR 文件 {client_jar_path} 不存在")
    
    # --- 账户信息处理 (从 config.json 读取) ---
    mc_account_config = config_data.get("MinecraftAccount", {})
    accounts_list = mc_account_config.get("accounts", [])
    chosen_index = mc_account_config.get("chosen", 0)

    # 默认值
    username = "Bloret-Player"
    user_uuid = "00000000-0000-0000-0000-000000000000"
    access_token = "00000000000000000000000000000000"
    user_type = "legacy"
    login_method = 0 # 0: Offline, 2: Microsoft
    client_id = "" # 微软登录通常不需要在启动参数显式传递client_id，除非特定需求
    xuid = ""

    current_account = {}

    if accounts_list and 0 <= chosen_index < len(accounts_list):
        current_account = accounts_list[chosen_index]
        username = current_account.get("username", username)
        user_uuid = current_account.get("uuid", user_uuid)
        
        # 判断账户类型
        acc_type_str = current_account.get("type", "Offline")
        if acc_type_str == "Microsoft":
            login_method = 2
            user_type = "msa"
            access_token = current_account.get("access_token", "")
            client_id = current_account.get("clientId", "")
            xuid = current_account.get("xuid", "")
            missing_fields = [
                field for field, value in (
                    ("Username", username), ("UUID", user_uuid), ("AccessToken", access_token)
                ) if not isinstance(value, str) or not value.strip()
            ]
            if missing_fields:
                raise ValueError(
                    f"Microsoft 在线账户缺少必要字段: {', '.join(missing_fields)}，请重新登录后再启动。"
                )
            log(f"Microsoft 在线账户验证通过: username={username}, uuid={user_uuid}")
        else:
            login_method = 0
            user_type = "legacy"
            # 离线模式 AccessToken 通常为空或全0
            access_token = "00000000000000000000000000000000"

    # --- 结束账户信息处理 ---
    
    # 构建基本启动参数
    # 使用 subprocess.Popen 时，如果 shell=False (推荐)，不需要手动为路径添加引号。
    # subprocess 会自动处理包含空格的路径。
    java_arg = java_path
    
    launch_args = [java_arg]
    
    # macOS 特有修复：GLFW 必须在第一个线程启动
    if platform.system() == "Darwin":
        launch_args.append("-XstartOnFirstThread")
        log("检测到 macOS，已添加 -XstartOnFirstThread 参数")

    # 启动器 JVM 参数按 Java 版本选择。模块系统参数不能传给 Java 8。
    launcher_jvm_args = [
        "-Dio.netty.tryReflectionSetAccessible=true",
        "-Dio.netty.native.skipTryReflectionSetAccessible=true",
        "-Dlog4j2.formatMsgNoLookups=true",
        "-Dfile.encoding=UTF-8",
        "-Dsun.jnu.encoding=UTF-8",
        "-XX:-OmitStackTraceInFastThrow",
        "-Dfml.ignoreInvalidMinecraftCertificates=True",
        "-Dfml.ignorePatchDiscrepancies=True",
        "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump",
        "-Djava.rmi.server.useCodebaseOnly=true",
        "-Djna.nosys=true",
        "-Djnidispatch.preserve=true",
        "-Dorg.lwjgl.util.Debug=false",
        "-Dorg.lwjgl.util.noload=true",
        "-Djava.awt.headless=false",
        "-Dsun.java2d.noddraw=true",
        "-Dsun.java2d.d3d=false",
        "-Dsun.java2d.opengl=false",
        "-Dsun.java2d.pmoffscreen=false",
        "-Dsun.java2d.accthreshold=0",
        "-XX:ErrorFile=./hs_err_pid%p.log",
    ]
    if java_version >= 9:
        launcher_jvm_args.extend([
            "--add-modules=jdk.unsupported",
            "--add-opens=java.base/java.lang=ALL-UNNAMED",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
            "--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED",
            "--add-opens=java.base/jdk.internal.ref=ALL-UNNAMED",
            "--add-opens=java.base/jdk.internal.loader=ALL-UNNAMED",
            "--add-opens=java.base/java.net=ALL-UNNAMED",
            "--add-opens=java.base/java.security=ALL-UNNAMED",
            "--add-exports=java.base/sun.nio.ch=ALL-UNNAMED",
            "--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED",
            "--add-exports=java.base/jdk.internal.ref=ALL-UNNAMED",
            "-Djdk.attach.allowAttachSelf=true",
            "-Djdk.module.IllegalAccess.silent=true",
        ])
    if java_version >= 17:
        launcher_jvm_args.append("--enable-native-access=ALL-UNNAMED")
    log(f"已选择适用于 Java {java_version} 的启动器 JVM 参数: {len(launcher_jvm_args)} 项")
    
    # 添加 Native 库路径参数（natives_path 已在补全阶段确定）
    launch_args.extend([
        f'-Djava.library.path={natives_path}',
        f'-Djna.tmpdir={natives_path}',
        f'-Dorg.lwjgl.system.SharedLibraryExtractPath={natives_path}',
        f'-Dio.netty.native.workdir={natives_path}'
    ])
    
    # 添加启动器标识参数
    launch_args.extend([
        "-Dminecraft.launcher.brand=Bloret-Launcher",
        "-Dminecraft.launcher.version=361"
    ])

    try:
        from modules.easytier import prepare_launch_context
        easytier_context = prepare_launch_context(mc_version, minecraft_dir)
        extra_jvm_args = easytier_context.get("jvm_args", [])
        if extra_jvm_args:
            launch_args.extend(extra_jvm_args)
            log(f"已注入 EasyTier JVM 参数: {extra_jvm_args}")
        if easytier_context.get("target_address"):
            log(f"Live EasyTier 目标地址: {easytier_context['target_address']}")
    except Exception as e:
        log(f"准备 EasyTier 启动上下文失败: {e}", logging.WARNING)

    # 插件钩子：追加 JVM 参数
    try:
        from modules.plugin_host.registry import get_registry
        plugin_jvm = get_registry().collect_jvm_args(mc_version, list(launch_args))
        if plugin_jvm:
            launch_args.extend(plugin_jvm)
            log(f"[PluginHost] 已注入插件 JVM 参数: {plugin_jvm}")
    except Exception as e:
        log(f"[PluginHost] 收集插件 JVM 参数失败: {e}", logging.WARNING)
    
    # 构建类路径：仅 rules 允许的 artifact jars（不含 mods；Fabric mods 由 Loader 加载）
    libraries_dir = os.path.join(minecraft_dir, "libraries")
    classpath = []
    asm_libs = {}  # module -> {"version": str, "path": str, "sort": key}

    for item in _library_download_items(version_data.get("libraries") or [], minecraft_dir):
        lib, lib_path, artifact, is_native = item
        if is_native:
            continue  # natives 已解压到 natives_path，不进 classpath
        if not lib_path or not os.path.exists(lib_path):
            log(f"classpath 跳过缺失库: {lib.get('name', lib_path)}", logging.WARNING)
            continue
        lib_name = lib.get("name", "")
        name_lower = lib_name.lower()
        if name_lower.startswith("org.ow2.asm:"):
            parts = lib_name.split(":")
            if len(parts) >= 3:
                asm_module = parts[1]
                lib_ver = parts[2]
                sort_key = _version_sort_key(lib_ver)
                prev = asm_libs.get(asm_module)
                if prev is None or sort_key > prev["sort"]:
                    asm_libs[asm_module] = {"version": lib_ver, "path": lib_path, "sort": sort_key}
            continue
        classpath.append(lib_path)

    # ASM 按固定模块顺序、仅最高版本
    asm_modules_order = ["asm", "asm-commons", "asm-tree", "asm-analysis", "asm-util"]
    ordered_asm = []
    for module in asm_modules_order:
        if module in asm_libs:
            ordered_asm.append(asm_libs[module]["path"])
            log(f"ASM {module}@{asm_libs[module]['version']}", logging.DEBUG)
    # 其它 ASM 模块（若有）
    for module, info in asm_libs.items():
        if module not in asm_modules_order:
            ordered_asm.append(info["path"])

    # 去重 classpath（保留顺序）
    seen_cp = set()
    deduped_cp = []
    for path in ordered_asm + classpath:
        key = os.path.normcase(os.path.abspath(path))
        if key in seen_cp:
            continue
        seen_cp.add(key)
        deduped_cp.append(path)
    classpath = deduped_cp
    classpath = _rewrite_classpath_with_system_lwjgl(classpath)

    library_names = [lib.get("name", "").lower() for lib in version_data.get("libraries", [])]
    is_fabric = (
        "fabric" in mc_version.lower()
        or "quilt" in mc_version.lower()
        or any("fabric" in name or "quilt" in name for name in library_names)
    )
    is_quilt = "quilt" in mc_version.lower() or any("quilt" in name for name in library_names)
    is_forge_like = (
        "forge" in mc_version.lower()
        or any("minecraftforge" in name or "neoforged" in name for name in library_names)
        or "net.minecraftforge" in version_data.get("mainClass", "")
        or "cpw.mods" in version_data.get("mainClass", "")
    )

    if is_quilt:
        log(f"检测到 Quilt 版本: {mc_version}")
    elif is_fabric:
        log(f"检测到 Fabric 版本: {mc_version}")
    elif is_forge_like:
        log(f"检测到 Forge/NeoForge 版本: {mc_version}")
    else:
        log(f"检测到原版: {mc_version}")
    
    # 实例级 overrides（内存 / 额外 JVM / 自定义 Java）
    try:
        from modules.services.instance_settings import resolve_launch_overrides
        _inst_over = resolve_launch_overrides(mc_version, config_data, minecraft_dir)
    except Exception as _ov_err:
        log(f"读取实例设置失败，使用全局配置: {_ov_err}", logging.WARNING)
        _inst_over = {
            "java_min_memory": config_data.get("java_min_memory", 512),
            "java_max_memory": config_data.get("java_max_memory", 4096),
            "extra_jvm_args": [],
            "env_vars": {},
            "hooks": {},
            "quick_play": {},
            "custom_game_args": "",
            "java_path": "",
        }

    # 若实例指定了 java_path 且存在，覆盖前面选中的 Java
    override_java = str(_inst_over.get("java_path") or "").strip()
    if override_java and os.path.isfile(override_java):
        java_path = override_java
        java_arg = java_path
        log(f"使用实例指定 Java: {java_path}")

    java_min_memory = _inst_over.get("java_min_memory", config_data.get("java_min_memory", 512))
    java_max_memory = _inst_over.get("java_max_memory", config_data.get("java_max_memory", 4096))
    
    launch_args.extend([
        f"-Xms{java_min_memory}m",
        f"-Xmx{java_max_memory}m"
    ])
    for extra in _inst_over.get("extra_jvm_args") or []:
        if extra and extra not in launch_args:
            launch_args.append(str(extra))
    
    if is_fabric:
        launch_args.append("-DFabricMcEmu=net.minecraft.client.main.Main")
    
    # 客户端 JAR 置于 classpath 最前
    classpath.insert(0, client_jar_path)
    log(f"classpath 条目数: {len(classpath)}")

    # Java 临时目录
    if sys.platform == "darwin":
        temp_dir = os.path.expanduser("~/Library/Caches/Bloret-Launcher-Temp")
    else:
        base_temp = os.environ.get('TEMP') or os.environ.get('TMP') or os.path.join(BLglobals.datapath, "temp")
        temp_dir = os.path.join(base_temp, 'Bloret-Launcher-Temp')
        
    if not os.path.exists(temp_dir):
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception:
            pass
    
    launch_args.append(f'-Doolloo.jlw.tmpdir={temp_dir}')
    launch_args.append(f'-Djava.io.tmpdir={temp_dir}')
    
    # 正确路径：versions/{version}/mods（无双重版本名）
    os.makedirs(mods_dir, exist_ok=True)
    log("mods 目录: " + mods_dir)

    # 处理 JavaWrapper.jar 路径
    # 注意：JavaWrapper 是一个第三方进程管理工具，但它早已停止维护
    # 它在 Java 17+（包括 Java 25）上会导致严重的 NullPointerException 崩溃
    # 因此，我们现在默认直接禁用它，改用原生直接启动方式
    use_wrapper = False  # 强制禁用

    # JSON arguments.jvm 是版本声明的权威 JVM 模板；启动器固定参数只作为附加兼容参数保留。
    jvm_variables = {
        "natives_directory": natives_path,
        "launcher_name": "Bloret-Launcher",
        "launcher_version": "361",
        "classpath": os.pathsep.join(classpath),
        "classpath_separator": os.pathsep,
        "library_directory": libraries_dir,
    }

    def replace_variables(value, variables):
        if not isinstance(value, str):
            return value
        for key, replacement in variables.items():
            value = value.replace("${" + key + "}", str(replacement))
        return value

    # 版本 JSON JVM 模板优先，随后追加启动器兼容参数，并在最终阶段去重。
    pending_launcher_jvm_args = launch_args[1:] + launcher_jvm_args
    launch_args = [java_arg]

    json_jvm_arguments = version_data.get("arguments", {}).get("jvm")
    if isinstance(json_jvm_arguments, list):
        added_jvm_count = 0
        for entry in json_jvm_arguments:
            if isinstance(entry, str):
                launch_args.append(replace_variables(entry, jvm_variables))
                added_jvm_count += 1
            elif isinstance(entry, dict) and _mojang_rules_allow(entry.get("rules")):
                values = entry.get("value", [])
                if isinstance(values, str):
                    values = [values]
                for value in values:
                    if isinstance(value, str):
                        launch_args.append(replace_variables(value, jvm_variables))
                        added_jvm_count += 1
        log(f"已按 Mojang rules 应用版本 JSON JVM 参数: {added_jvm_count} 项")
    else:
        launch_args.extend(["-cp", os.pathsep.join(classpath)])
        log("版本 JSON 未提供 arguments.jvm，已使用兼容类路径参数", logging.WARNING)

    pending_launcher_jvm_args.extend([
        f'-Doolloo.jlw.tmpdir={temp_dir}',
        f'-Djava.io.tmpdir={temp_dir}',
    ])
    if is_fabric and os.path.exists(mods_dir):
        log(f"添加 Fabric/Quilt mods 目录: {mods_dir}")
        pending_launcher_jvm_args.append(f'-Dfabric.addMods={mods_dir}')
        if is_quilt:
            pending_launcher_jvm_args.append(f'-Dloader.addMods={mods_dir}')

    seen_jvm_args = set(launch_args[1:])
    for arg in pending_launcher_jvm_args:
        if arg not in seen_jvm_args:
            launch_args.append(arg)
            seen_jvm_args.add(arg)
    log(f"JVM 参数合并去重完成: {len(launch_args) - 1} 项")

    main_class = version_data.get("mainClass")
    if not main_class:
        main_class = "net.minecraft.client.main.Main"
        log("版本 JSON 缺少 mainClass，回退到原版主类", logging.WARNING)
    launch_args.append(main_class)
    log(f"使用版本 JSON 主类: {main_class}")
    
    # 游戏目录应该是主 .minecraft 目录，而不是版本特定目录
    # 修改：为了实现版本隔离，game_dir 应该指向 versions_dir
    game_dir = versions_dir
    log(f"启用了版本隔离，游戏目录: {game_dir}")

    assets_dir = os.path.join(minecraft_dir, "assets")
    
    if not os.path.exists(game_dir):
        raise FileNotFoundError(f"游戏目录不存在: {game_dir}")
    
    os.makedirs(assets_dir, exist_ok=True)
    
    # 获取资产索引
    asset_index = version_data.get("assetIndex", {}).get("id", mc_version)
    
    # 设置 versionType
    version_type = "Bloret-Launcher"
    
    # 在日志中以列表形式记录启动信息
    log("启动信息:")
    log(f"- Minecraft 版本: {mc_version}")
    log(f"- 登录方式: {'离线登录' if login_method == 0 else '微软登录' if login_method == 2 else '未知'}")
    log(f"- 登录名称: {username}")
    log(f"- UUID: {user_uuid}")
    log(f"- AccessToken: {'******' if access_token else 'N/A'}")
    game_variables = {
        "auth_player_name": username,
        "version_name": mc_version,
        "game_directory": game_dir,
        "assets_root": assets_dir,
        "assets_index_name": str(asset_index),
        "auth_uuid": user_uuid,
        "auth_access_token": access_token if login_method == 2 else "00000000000000000000000000000000",
        "user_type": user_type if login_method == 2 else "legacy",
        "version_type": version_type,
        "clientid": client_id,
        "auth_xuid": xuid,
    }

    def replace_game_variables(value):
        return replace_variables(value, game_variables)

    game_arguments = version_data.get("arguments", {}).get("game")
    appended_count = 0
    if isinstance(game_arguments, list):
        for entry in game_arguments:
            if isinstance(entry, str):
                launch_args.append(replace_game_variables(entry))
                appended_count += 1
            elif isinstance(entry, dict) and _mojang_rules_allow(entry.get("rules")):
                values = entry.get("value", [])
                if isinstance(values, str):
                    values = [values]
                for value in values:
                    if isinstance(value, str):
                        launch_args.append(replace_game_variables(value))
                        appended_count += 1
        log(f"已按 Mojang rules 应用版本 JSON 游戏参数: {appended_count} 项")
    else:
        minecraft_arguments = version_data.get("minecraftArguments")
        if minecraft_arguments:
            expanded = replace_game_variables(minecraft_arguments)
            parsed_legacy_args = _split_legacy_arguments(expanded)
            launch_args.extend(parsed_legacy_args)
            log(f"已使用 shlex 可靠解析旧版 minecraftArguments: {len(parsed_legacy_args)} 项")
        else:
            # 极旧或不完整 JSON 的最后兼容路径。
            launch_args.extend([
                "--username", username, "--version", mc_version,
                "--gameDir", game_dir, "--assetsDir", assets_dir,
                "--assetIndex", str(asset_index), "--uuid", user_uuid,
                "--accessToken", game_variables["auth_access_token"],
                "--userType", game_variables["user_type"],
                "--versionType", version_type, "--width", "854", "--height", "480"
            ])
            log("版本 JSON 未提供游戏参数模板，已使用兼容参数", logging.WARNING)

    # clientId/xuid 只在模板实际引用且账户有值时才补充，避免发送空参数或重复参数。
    template_text = json.dumps(game_arguments if isinstance(game_arguments, list) else version_data.get("minecraftArguments", ""))
    existing_flags = set(launch_args)
    if login_method == 2 and "${clientid}" in template_text and client_id and "--clientId" not in existing_flags:
        launch_args.extend(["--clientId", client_id])
    if login_method == 2 and "${auth_xuid}" in template_text and xuid and "--xuid" not in existing_flags:
        launch_args.extend(["--xuid", xuid])

    # Quick Play + 自定义游戏参数
    try:
        from modules.services.worlds_service import quick_play_game_args
        qp_args = quick_play_game_args(_inst_over.get("quick_play") or {})
        if qp_args:
            launch_args.extend(qp_args)
            log(f"已注入 Quick Play 参数: {qp_args}")
        custom_game = str(_inst_over.get("custom_game_args") or "").strip()
        if custom_game:
            import shlex as _shlex
            try:
                extra_g = _shlex.split(custom_game, posix=(os.name != "nt"))
            except ValueError:
                extra_g = custom_game.split()
            launch_args.extend(extra_g)
    except Exception as _qp_err:
        log(f"Quick Play 参数注入失败: {_qp_err}", logging.WARNING)

    # 用户 wrapper hook
    hooks = _inst_over.get("hooks") or {}
    wrapper = str(hooks.get("wrapper") or "").strip()
    if wrapper:
        try:
            from modules.services.runtime_extras import wrap_launch_args
            launch_args = wrap_launch_args(
                wrapper,
                launch_args,
                {
                    "INST_NAME": mc_version,
                    "INST_ID": mc_version,
                    "INST_DIR": versions_dir,
                    "INST_MC_DIR": versions_dir,
                    "INST_JAVA": java_path,
                },
            )
            log(f"已应用 wrapper hook")
        except Exception as _wh:
            log(f"wrapper hook 失败: {_wh}", logging.WARNING)

    # pre-launch hook（失败则中止启动）
    pre = str(hooks.get("pre_launch") or "").strip()
    if pre:
        try:
            from modules.services.runtime_extras import run_pre_launch_hook
            pre_res = run_pre_launch_hook(
                pre,
                instance_name=mc_version,
                instance_dir=versions_dir,
                java_path=java_path,
                cwd=versions_dir,
            )
            if not pre_res.ok:
                raise RuntimeError(pre_res.error or "pre-launch hook failed")
            log("pre-launch hook 完成")
        except Exception as _ph:
            log(f"pre-launch hook 失败: {_ph}", logging.ERROR)
            raise

    # 把 hooks / env 挂到返回值之外：调用方可通过全局读取
    try:
        import modules.globals as _g
        _g._pending_launch_hooks = {
            "post_exit": str(hooks.get("post_exit") or ""),
            "instance_name": mc_version,
            "instance_dir": versions_dir,
            "java_path": java_path,
            "env_vars": dict(_inst_over.get("env_vars") or {}),
        }
    except Exception:
        pass

    # 返回启动参数列表和游戏目录；日志必须脱敏。
    sensitive_values = {value for value in (access_token, client_id, xuid) if value}
    safe_args = ["******" if arg in sensitive_values else arg for arg in launch_args]
    log(f"生成的启动参数（敏感字段已脱敏）: {safe_args}")
    return launch_args, game_dir

# Change timeout default to 300
def get_minecraft_window_handle(version=None, timeout=300, mc_pid=None):
    """
    获取 Minecraft 窗口句柄（Windows）或 进程PID（macOS/Linux）
    
    Args:
        version (str): Minecraft 版本号，用于识别特定版本的窗口
        timeout (int): 超时时间（秒）
        mc_pid (int): 启动得到的根进程 PID；提供后仅匹配该进程树
    
    Returns:
        int: 窗口句柄或PID，如果未找到则返回 None
    """
    if platform.system() != "Windows":
        # 非 Windows 系统下通过进程监控实现
        log(f"在 {platform.system()} 上尝试通过进程寻找 Minecraft...")
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                allowed_pids = _process_tree_pids(mc_pid)
                if mc_pid and not allowed_pids:
                    log(f"Minecraft 根进程 {mc_pid} 已退出，停止等待进程窗口")
                    return None
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if allowed_pids is not None and proc.pid not in allowed_pids:
                        continue
                    try:
                        cmdline_list = proc.info.get('cmdline', [])
                        if not cmdline_list: continue
                        cmdline = ' '.join(cmdline_list)
                        if 'java' in proc.info.get('name', '').lower() or 'java' in cmdline.lower():
                            # 检查是否包含 Minecraft 关键特征
                            if any(keyword in cmdline.lower() for keyword in ['net.minecraft', 'minecraft', '.jar']):
                                if not version or version in cmdline:
                                    log(f"找到 Minecraft 进程: PID={proc.pid}")
                                    return proc.pid
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(1)
        except Exception as e:
            log(f"查找进程失败: {e}")
        return None
    
    try:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            allowed_pids = _process_tree_pids(mc_pid)
            if mc_pid and not allowed_pids:
                log(f"Minecraft 根进程 {mc_pid} 已退出，停止等待窗口")
                return None

            # 枚举所有窗口
            def enum_windows_callback(hwnd, windows_list):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    try:
                        window_text = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        
                        # 检查是否为 Minecraft 窗口
                        # Minecraft 窗口通常包含 "Minecraft" 或 "Minecraft*" 标题
                        # 并且类名通常是 "LWJGL" 或包含 "GLFW" 的类名
                        if ("Minecraft" in window_text or 
                            (version and version in window_text)):
                            
                            # 进一步验证窗口类名
                            if (class_name.startswith("LWJGL") or 
                                "GLFW" in class_name or
                                "SunAwtFrame" in class_name or
                                "SDL_app" in class_name):
                                
                                # 获取进程ID
                                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                                if allowed_pids is not None and pid not in allowed_pids:
                                    return True

                                # 检查进程命令行是否包含 Minecraft 相关参数
                                try:
                                    process = psutil.Process(pid)
                                    cmdline = ' '.join(process.cmdline())
                                    
                                    # 检查是否包含 Minecraft 相关关键词
                                    minecraft_keywords = [
                                        'net.minecraft',
                                        'minecraft',
                                        '.jar',
                                        'forge',
                                        'fabric',
                                        version if version else ''
                                    ]
                                    
                                    if any(keyword in cmdline.lower() for keyword in minecraft_keywords if keyword):
                                        windows_list.append({
                                            'hwnd': hwnd,
                                            'title': window_text,
                                            'class': class_name,
                                            'pid': pid,
                                            'cmdline': cmdline
                                        })
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    # 如果无法获取进程信息，但窗口标题和类名匹配，也认为是 Minecraft 窗口
                                    windows_list.append({
                                        'hwnd': hwnd,
                                        'title': window_text,
                                        'class': class_name,
                                        'pid': pid,
                                        'cmdline': 'unknown'
                                    })
                    except Exception as e:
                        log(f"枚举窗口时出错: {e}")
                return True
            
            minecraft_windows = []
            win32gui.EnumWindows(enum_windows_callback, minecraft_windows)
            
            if minecraft_windows:
                # 找到最可能的 Minecraft 窗口
                # 优先选择标题中包含版本号的窗口
                best_match = None
                for window in minecraft_windows:
                    if version and version in window['title']:
                        best_match = window
                        break
                
                if not best_match:
                    best_match = minecraft_windows[0]  # 选择第一个匹配的窗口
                
                hwnd = best_match['hwnd']
                log(f"找到 Minecraft 窗口: 句柄={hwnd}, 标题='{best_match['title']}', "
                    f"类名='{best_match['class']}', PID={best_match['pid']}")
                
                return hwnd
            
            # 等待一段时间后重试
            time.sleep(0.5)
        
        log(f"在 {timeout} 秒内未找到 Minecraft 窗口")
        return None
        
    except ImportError as e:
        log(f"缺少必要的库: {e}")
        log("请安装 pywin32 和 psutil: pip install pywin32 psutil")
        return None
    except Exception as e:
        log(f"获取 Minecraft 窗口句柄时出错: {e}")
        return None

def monitor_minecraft_window(version, check_interval=1, callback=None, mc_pid=None):
    """
    监控 Minecraft 窗口，当窗口出现时获取句柄并显示浮动工具栏

    Args:
        version (str): Minecraft 版本号
        check_interval (int): 检查间隔（秒）
        callback (callable): 找到窗口后的回调函数
        mc_pid (int): Minecraft 进程 ID（可选），用于监控进程退出并自动隐藏工具条
    """
    def monitor_thread():
        log(f"开始监控 Minecraft {version} 窗口... (进程 ID: {mc_pid})")
        
        # 等待一段时间让 Minecraft 启动
        time.sleep(3)
        
        # 仅在传入的 Minecraft 根进程及其子进程树内查找窗口。
        hwnd = get_minecraft_window_handle(version, timeout=300, mc_pid=mc_pid)
        
        if hwnd:
            log(f"✅ Minecraft {version} 已找到！")
            if callback:
                try:
                    callback()
                except Exception as e:
                    log(f"执行回调失败: {e}", logging.ERROR)
            
            if platform.system() == "Windows":
                log(f"🎯 窗口句柄: {hwnd}")
                log(f"🔍 窗口句柄(十六进制): 0x{hwnd:08X}")
                
                # 获取窗口信息
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    log(f"📋 窗口标题: {window_text}")
                    log(f"🏷️ 窗口类名: {class_name}")
                    log(f"🔢 进程ID: {pid}")
                    
                    # 尝试获取进程信息
                    try:
                        import psutil
                        process = psutil.Process(pid)
                        log(f"⚙️ 进程名称: {process.name()}")
                        log(f"📁 进程路径: {process.exe()}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
                except Exception as e:
                    log(f"获取窗口详细信息时出错: {e}")
            else:
                log(f"🎯 进程 PID: {hwnd}")
            
            # 创建工具栏 - 仅在 Windows 上支持 mwtool 的窗口吸附
            if platform.system() != "Windows":
                log("非 Windows 系统暂不支持浮动工具栏功能")
                return hwnd

            try:
                if not cfg.read().get("mwtool_switch_open", True):
                    log("已关闭 Minecraft 小工具栏，跳过创建")
                    return hwnd
            except Exception as e:
                log(f"读取 mwtool_switch_open 失败，继续按默认开启处理: {e}", logging.WARNING)

            # 创建工具栏 - 使用修复后的模块确保线程安全
            try:
                if mwtool is None:
                    log("mwtool 未就绪，跳过 Minecraft 浮动工具栏创建", logging.WARNING)
                    return

                log("正在创建工具栏...", logging.DEBUG)

                # 直接在监控线程中调用工具栏创建（mwtool 内部会处理跨线程调用）
                try:
                    tool = mwtool.create_minecraft_tool(hwnd, version)
                    if tool:
                        log(f"工具栏创建成功: {tool}", logging.DEBUG)
                    else:
                        log("工具栏创建已异步派发", logging.DEBUG)
                except Exception as e:
                    log(f"工具栏创建失败: {e}", logging.ERROR)
                    import traceback
                    traceback.print_exc()

                # 启动进程退出监控，当 Minecraft 退出时自动隐藏工具条
                if mc_pid:
                    try:
                        mwtool.start_monitoring(version, mc_pid=mc_pid)
                        log(f"✅ 已启动进程退出监控 (PID: {mc_pid})，Minecraft 退出时工具条将自动隐藏")
                    except Exception as e:
                        log(f"启动进程退出监控失败: {e}", logging.WARNING)

                log(f"✅ Minecraft 浮动工具栏创建完成，版本: {version}")
            except Exception as e:
                log(f"创建 Minecraft 浮动工具栏失败: {e}")
            
            # 返回窗口句柄给调用者
            return hwnd
        else:
            log(f"❌ 未找到 Minecraft {version} 窗口")
            return None
    
    # 启动监控线程
    thread = threading.Thread(target=monitor_thread, daemon=True)
    thread.start()
    return thread
