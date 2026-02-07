from qfluentwidgets import InfoBar, InfoBarPosition, ComboBox
import logging, os, json, send2trash, platform, requests, shutil, concurrent.futures, threading, time, psutil
import sip # type: ignore
from pathlib import Path
from modules.win11toast import notify, update_progress
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
from modules.safe import handle_exception
import sys
from modules.customize import find_Customize
from modules.i18n import i18nText
from modules.install import LibraryDownloader
import modules.globals as BLglobals
import modules.config as cfg # 确保导入了 config 模块

# Windows API 导入，用于获取窗口句柄
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import win32gui
    import win32con
    import win32process

def Get_Run_Script(mc_version):
    """
    根据 config.json 的内容生成启动 .minecraft 文件夹中指定版本的命令
    支持 Fabric 加载器启动
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        mc_version (str): 要启动的 Minecraft 版本号
        
    Returns:
        tuple: (launch_args, game_dir) 启动参数列表和工作目录
    """
    
    # 1. 读取配置文件 (替代原有的 cmcl.json 读取)
    try:
        config_data = cfg.read()
    except Exception as e:
        raise FileNotFoundError(f"读取配置文件失败: {e}")
    
    # 获取 Minecraft 目录
    minecraft_dir = config_data.get('minecraft_dir', '')
    if not minecraft_dir:
        # 如果配置中没有指定，则使用默认路径
        appdata = os.environ.get('APPDATA', '')
        minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')
    
    versions_dir = os.path.join(minecraft_dir, "versions", mc_version)
    
    # 检查版本目录是否存在
    if not os.path.exists(versions_dir):
        raise FileNotFoundError(f"版本 {mc_version} 不存在于 {versions_dir}")
    
    # 获取版本 JSON 文件路径
    version_json_path = os.path.join(versions_dir, f"{mc_version}.json")
    if not os.path.exists(version_json_path):
        raise FileNotFoundError(f"版本配置文件 {version_json_path} 不存在")
    
    # 读取版本配置
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_data = json.load(f)
    
    # 获取客户端 JAR 文件路径
    client_jar_path = os.path.join(versions_dir, f"{mc_version}.jar")
    if not os.path.exists(client_jar_path):
        raise FileNotFoundError(f"客户端 JAR 文件 {client_jar_path} 不存在")
    
    # 获取 Java 路径
    java_path = "java"  # 默认值
    
    # 1. 优先使用配置中指定的 Java 路径 (新增逻辑)
    config_java_path = config_data.get('java_path', '')
    if config_java_path and os.path.exists(config_java_path) and config_java_path != "Auto":
        java_path = config_java_path
    else:
        # 2. 检查系统PATH中是否存在java命令
        import shutil
        java_in_path = shutil.which("java")
        
        if java_in_path:
            java_path = java_in_path
        else:
            # 3. 如果系统PATH中没有java，尝试使用配置中的旧字段 java_dir (兼容旧配置)
            java_dir = config_data.get('java_dir', '') 
            
            if java_dir and os.path.exists(java_dir):
                java_exe_path = os.path.join(java_dir, "bin", "java.exe")
                if os.path.exists(java_exe_path):
                    java_path = java_exe_path
            else:
                # 4. 尝试默认的Java安装路径
                default_java_paths = [
                    r"C:\Program Files\Java\jdk-17\bin\java.exe",
                    r"C:\Program Files\Java\jdk-21\bin\java.exe",
                    r"C:\Program Files\Java\jdk-24\bin\java.exe",
                    r"C:\Program Files\Eclipse Adoptium\jdk-17-hotspot\bin\java.exe",
                    r"C:\Program Files\Eclipse Adoptium\jdk-21-hotspot\bin\java.exe",
                    r"C:\Program Files\Eclipse Adoptium\jdk-24-hotspot\bin\java.exe",
                    r"C:\Program Files\Zulu\zulu-24\bin\java.exe",
                    r"C:\Program Files\Zulu\zulu-17\bin\java.exe",
                    r"C:\Program Files\Zulu\zulu-21\bin\java.exe"
                ]
                
                for default_path in default_java_paths:
                    if os.path.exists(default_path):
                        java_path = default_path
                        break
    
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
            access_token = current_account.get("access_token", access_token)
            # config.json 中可能没有 client_id 和 xuid，根据需要添加或留空
            client_id = current_account.get("clientId", "") 
            xuid = current_account.get("xuid", "")
        else:
            login_method = 0
            user_type = "legacy"
            # 离线模式 AccessToken 通常为空或全0
            access_token = "00000000000000000000000000000000"

    # --- 结束账户信息处理 ---
    
    # 构建基本启动参数
    # 根据java_path是否为完整路径决定是否添加引号
    if java_path == "java":
        java_arg = java_path
    else:
        java_arg = f'"{java_path}"'
    
    launch_args = [
        java_arg,  # Java路径
        "--enable-native-access=ALL-UNNAMED",
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",
        "--add-opens", "java.base/java.util=ALL-UNNAMED",
        "--add-opens", "java.base/sun.nio.ch=ALL-UNNAMED",
        "--add-opens", "java.base/sun.misc=ALL-UNNAMED",
        "--add-opens", "java.base/jdk.internal.misc=ALL-UNNAMED",
        "--add-opens", "java.base/jdk.internal.ref=ALL-UNNAMED",
        "--add-exports", "java.base/sun.nio.ch=ALL-UNNAMED",
        "--add-exports", "java.base/sun.misc=ALL-UNNAMED",
        "--add-exports", "java.base/jdk.internal.misc=ALL-UNNAMED",
        "--add-exports", "java.base/jdk.internal.ref=ALL-UNNAMED",
        "-Dio.netty.tryReflectionSetAccessible=true",
        "-Dio.netty.native.skipTryReflectionSetAccessible=true",
        "-Dsun.misc.unsafe.throwException=false",
        "-Djdk.attach.allowAttachSelf=true",
        "-Djdk.module.IllegalAccess.silent=true",
        "-Dlog4j2.formatMsgNoLookups=true",
        "-Dfile.encoding=UTF-8",
        "-Dsun.jnu.encoding=UTF-8",
        "-Dstderr.encoding=UTF-8", 
        "-Dstdout.encoding=UTF-8",
        "-XX:+UseG1GC",
        "-XX:-UseAdaptiveSizePolicy",
        "-XX:-OmitStackTraceInFastThrow",
        "-Djdk.lang.Process.allowAmbiguousCommands=true",
        "-Dfml.ignoreInvalidMinecraftCertificates=True",
        "-Dfml.ignorePatchDiscrepancies=True",
        "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump",
        "-Dsun.misc.URLClassPath.disableJarChecking=true",
        "-Djava.rmi.server.useCodebaseOnly=true",
        "-Dcom.sun.management.jmxremote.local.only=true",
        "-Dcom.sun.management.jmxremote.authenticate=false",
        "-Dcom.sun.management.jmxremote.ssl=false",
        "-XX:-OmitStackTraceInFastThrow",
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
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+UseG1GC",
        "-XX:+UseCompressedOops",
        "-XX:+OptimizeStringConcat",
        "-XX:+UseStringDeduplication"
    ]
    
    # 添加 Native 库路径参数
    natives_path = os.path.join(versions_dir, f"{mc_version}-natives")
    launch_args.extend([
        f'-Djava.library.path="{natives_path}"',
        f'-Djna.tmpdir="{natives_path}"',
        f'-Dorg.lwjgl.system.SharedLibraryExtractPath="{natives_path}"',
        f'-Dio.netty.native.workdir="{natives_path}"'
    ])
    
    # 添加启动器标识参数
    launch_args.extend([
        "-Dminecraft.launcher.brand=Bloret-Launcher",
        "-Dminecraft.launcher.version=361"
    ])
    
    # 构建类路径 (classpath)
    classpath = []
    
    # 添加所有依赖库
    libraries_dir = os.path.join(minecraft_dir, "libraries")
    missing_libraries = []
    if "libraries" in version_data:
        for lib in version_data["libraries"]:
            # 检查库是否适用于当前系统
            should_include = True
            if "rules" in lib:
                should_include = False
                for rule in lib["rules"]:
                    if rule.get("action") == "allow":
                        os_rule = rule.get("os", {})
                        if not os_rule or (os_rule.get("name", "").lower() == platform.system().lower() or 
                                          (os_rule.get("name") == "windows" and platform.system() == "Windows") or
                                          (os_rule.get("name") == "osx" and platform.system() == "Darwin") or
                                          (os_rule.get("name") == "linux" and platform.system() == "Linux")):
                            should_include = True
                            break
            
            if should_include:
                lib_path = None
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    lib_path = os.path.join(minecraft_dir, "libraries", lib["downloads"]["artifact"]["path"])
                elif "name" in lib:
                    # 处理 Maven 风格的库名称
                    parts = lib["name"].split(":")
                    if len(parts) >= 3:
                        group_id, artifact_id, lib_version = parts[0:3]
                        relative_path = os.path.join(
                            group_id.replace(".", "/"),
                            artifact_id,
                            lib_version,
                            f"{artifact_id}-{lib_version}.jar"
                        )
                        lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
                
                if lib_path:
                    # 检查库文件是否存在
                    if os.path.exists(lib_path):
                        classpath.append(lib_path)
                    else:
                        # 记录缺失的库文件
                        missing_libraries.append((lib, lib_path))
    
    # 检查是否为 Fabric 版本
    is_fabric = "fabric" in mc_version.lower() or any("fabric" in lib.get("name", "").lower() for lib in version_data.get("libraries", []))

    if is_fabric:
        log(f"检测到 Fabric 版本: {mc_version}")
    else:
        log(f"检测到原版: {mc_version}")
    
    # 添加内存参数 (从配置读取，默认最小 512MB，最大 4096MB)
    java_min_memory = config_data.get('java_min_memory', 512)
    java_max_memory = config_data.get('java_max_memory', 4096)
    
    launch_args.extend([
        f"-Xms{java_min_memory}m",  # 初始堆内存
        f"-Xmx{java_max_memory}m"   # 最大堆内存
    ])
    
    # 添加自定义参数 - 设置JavaWrapper的临时目录为系统临时目录
    temp_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', os.getcwd())), 'Bloret-Launcher')
    launch_args.append(f'-Doolloo.jlw.tmpdir="{temp_dir}"')
    
    # 添加 Fabric 特定参数和处理
    if is_fabric:
        launch_args.append("-DFabricMcEmu=net.minecraft.client.main.Main")
        
        # 用于存储所有库
        fabric_libs = []
        # 跟踪已添加的ASM库
        asm_libs = {}
        
        # 添加 Fabric 版本文件夹中的所有 JAR 文件
        fabric_version_dir = os.path.join(versions_dir, mc_version)
        if os.path.exists(fabric_version_dir):
            for file in os.listdir(fabric_version_dir):
                if file.endswith('.jar') and 'fabric' in file.lower():
                    jar_path = os.path.join(fabric_version_dir, file)
                    fabric_libs.append(jar_path)
        
        # 添加 mods 目录中的所有 JAR 文件 (Fabric mods)
        mods_dir = os.path.join(minecraft_dir, "versions", mc_version, "mods")
        if os.path.exists(mods_dir):
            for file in os.listdir(mods_dir):
                if file.endswith('.jar'):
                    fabric_libs.append(os.path.join(mods_dir, file))
        
        # 首先添加 Fabric Loader 核心库和关键依赖
        fabric_loader_libs = [
            "net/fabricmc/fabric-loader",
            "net/fabricmc/sponge-mixin",
            "net/fabricmc/intermediary",
            "net/fabricmc/fabric-api",
            "net/fabricmc/fabric",
            "net/fabricmc/tiny-mappings-parser",
            "net/fabricmc/tiny-remapper",
            "net/fabricmc/access-widener"
        ]
        
        # 跟踪已添加的ASM库
        asm_libs = {}  # 使用字典跟踪每个ASM模块的最高版本
        
        for lib in version_data.get("libraries", []):
            lib_name = lib.get("name", "").lower()
            lib_path = None
            
            # 检查是否为 Fabric 相关库或关键依赖
            if "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = os.path.join(minecraft_dir, "libraries", lib["downloads"]["artifact"]["path"])
            elif "name" in lib:
                # 处理 Maven 风格的库名称
                parts = lib["name"].split(":")
                if len(parts) >= 3:
                    group_id, artifact_id, lib_version = parts[0:3]
                    relative_path = os.path.join(
                        group_id.replace(".", "/"),
                        artifact_id,
                        lib_version,
                        f"{artifact_id}-{lib_version}.jar"
                    )
                    lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
            
            if lib_path:
                # 检查库文件是否存在
                if not os.path.exists(lib_path):
                    # 记录缺失的库文件
                    missing_libraries.append((lib, lib_path))
                    continue
                    
                # 处理ASM库
                if "org.ow2.asm" in lib_name:
                    # 从库名中提取版本号和模块名
                    parts = lib_name.split(":")
                    if len(parts) >= 3:
                        asm_module = parts[1]  # 例如 "asm", "asm-commons" 等
                        lib_version = parts[2]  # 版本号
                        
                        # 如果这是一个更高版本，或者这个模块还没有被记录
                        if asm_module not in asm_libs or lib_version > asm_libs[asm_module]["version"]:
                            asm_libs[asm_module] = {"version": lib_version, "path": lib_path}
                            log(f"记录ASM库 {asm_module} 版本 {lib_version}")
                        else:
                            log(f"跳过较低版本的ASM库 {asm_module} 版本 {lib_version}，已有版本 {asm_libs[asm_module]['version']}")
                    continue  # 跳过当前的库添加，稍后会统一添加ASM库
                        
                # 添加Fabric核心库
                elif any(fabric_lib in lib_name for fabric_lib in fabric_loader_libs):
                    if "fabric-loader" in lib_name or "intermediary" in lib_name:
                        fabric_libs.insert(0, lib_path)  # 放在前面
                    else:
                        fabric_libs.append(lib_path)  # 其他的放在后面
                # 其他 Fabric 相关库
                elif "fabric" in lib_name or "mixin" in lib_name:
                    fabric_libs.append(lib_path)
            # 记录找到的库
            if lib_path and os.path.exists(lib_path):
                log(f"已添加库: {lib_path}")
        
        # 按照特定顺序构建最终的类路径
        final_classpath = []
        
        # 1. 添加 ASM 库（按特定顺序，只添加最高版本）
        asm_modules_order = ["asm", "asm-commons", "asm-tree", "asm-analysis", "asm-util"]
        for module in asm_modules_order:
            if module in asm_libs:
                final_classpath.append(asm_libs[module]["path"])
                log(f"添加ASM库 {module} 版本 {asm_libs[module]['version']}，路径: {asm_libs[module]['path']}")
        
        # 2. 添加 Fabric 核心库
        final_classpath.extend(fabric_libs)
        
        # 3. 添加其他所有库（排除已添加的ASM库）
        # 创建已添加ASM库路径的集合，用于过滤
        added_asm_paths = set()
        for module in asm_libs:
            added_asm_paths.add(asm_libs[module]["path"].lower())
        
        # 过滤掉已添加的ASM库
        filtered_classpath = []
        for lib_path in classpath:
            # 检查是否为ASM库
            if "org/ow2/asm" in lib_path.lower() or "/asm-" in lib_path.lower():
                if lib_path.lower() not in added_asm_paths:
                    log(f"跳过重复的ASM库: {lib_path}")
                    continue
            filtered_classpath.append(lib_path)
        
        final_classpath.extend(filtered_classpath)
        
        # 更新类路径
        classpath = final_classpath
    
    # 添加客户端 JAR 到 classpath
    classpath.append(client_jar_path)
    if not os.path.exists(client_jar_path): missing_libraries.append(({"name": f"{mc_version}.jar", "downloads": {"artifact": {"path": f"{mc_version}/{mc_version}.jar"}}}, client_jar_path))
    
    # 检查是否有缺失的库文件并尝试下载
    if missing_libraries:
        log(f"发现 {len(missing_libraries)} 个缺失的库文件，正在尝试下载...")
        
        # 从 config.json 读取 MaxThread
        max_workers = config_data.get("MaxThread", 64)
        
        # 创建下载器并启动下载线程
        downloader = LibraryDownloader(missing_libraries, max_workers)
        download_thread = threading.Thread(target=downloader.download_libraries)
        download_thread.daemon = True
        download_thread.start()
        
        # 等待下载完成
        downloader.completed_event.wait()
        
        # 重新检查库文件并添加到类路径中
        for lib, lib_path in missing_libraries:
            if os.path.exists(lib_path) and lib_path not in classpath:
                classpath.append(lib_path)
                log(f"添加之前缺失但现已下载的库: {lib_path}")
    
    # 添加自定义参数 - 设置JavaWrapper的临时目录为系统临时目录
    temp_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', os.getcwd())), 'Bloret-Launcher')
    launch_args.append(f'-Doolloo.jlw.tmpdir="{temp_dir}"')
    
    # 初始化mods_dir变量 - 使用版本目录下的mods文件夹
    mods_dir = os.path.join(versions_dir, "mods")
    
    # 确保mods目录存在
    if not os.path.exists(mods_dir):
        os.makedirs(mods_dir)
        log(f"创建mods目录: {mods_dir}")
    
    log("mods 目录: " + mods_dir)

    # 添加类路径参数
    launch_args.extend(["-cp", '\"' + ";".join(classpath) + '\"'])  # Windows 使用分号分隔
    
    # Add Fabric Loader arguments to ensure mods are loaded
    if is_fabric and os.path.exists(mods_dir):
        log(f"添加 Fabric mods 目录: {mods_dir}")
        launch_args.extend([f'-Dfabric.addMods="{mods_dir}"'])
    
    # 添加主类和参数
    if is_fabric:
        # Fabric 使用 KnotClient 主类而不是 -jar 参数
        launch_args.append("net.fabricmc.loader.impl.launch.knot.KnotClient")

    else:
        # 原始 Minecraft 启动方式
        launch_args.append("-jar")
        java_wrapper_path = os.path.join(os.getcwd(), "JavaWrapper.jar")
        if not os.path.exists(java_wrapper_path):
            raise FileNotFoundError(f"JavaWrapper.jar 文件不存在: {java_wrapper_path}")
        launch_args.append(f'"{java_wrapper_path}"')
        launch_args.append("net.minecraft.client.main.Main")
    
    # 游戏目录应该是主 .minecraft 目录，而不是版本特定目录
    # 修改：为了实现版本隔离，game_dir 应该指向 versions_dir
    game_dir = versions_dir
    log(f"启用了版本隔离，游戏目录: {game_dir}")

    assets_dir = os.path.join(minecraft_dir, "assets")
    
    if not os.path.exists(game_dir):
        raise FileNotFoundError(f"游戏目录不存在: {game_dir}")
    
    if not os.path.exists(assets_dir):
        raise FileNotFoundError(f"资产目录不存在: {assets_dir}")
    
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
    
    # 根据登录方式设置启动参数
    if login_method == 0:  # 离线登录
        launch_args.extend([
            "--username", username,
            "--version", mc_version,
            "--gameDir", game_dir,
            "--assetsDir", assets_dir,
            "--assetIndex", str(asset_index),
            "--uuid", user_uuid, # 使用配置中的UUID
            "--accessToken", "00000000000000000000000000000000",
            "--userType", "legacy",
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    elif login_method == 2:  # 微软登录
        # 检查账户信息相关字段
        missing_fields = []
        if not username:
            missing_fields.append("Username")
        if not user_uuid:
            missing_fields.append("UUID")
        if not access_token:
            missing_fields.append("AccessToken")

        if missing_fields:
            raise ValueError(f"缺少必要的启动参数: {', '.join(missing_fields)}，请先登录或完善账户信息。")
            
        launch_args.extend([
            "--username", username,
            "--version", mc_version,
            "--gameDir", game_dir,
            "--assetsDir", assets_dir,
            "--assetIndex", str(asset_index),
            "--uuid", user_uuid,
            "--accessToken", access_token,
            "--clientId", client_id,
            "--xuid", xuid,
            "--userType", user_type,
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    
    # 返回启动参数列表和游戏目录，而不是批处理脚本
    log(f"生成的启动参数: {launch_args}")
    return launch_args, game_dir

# Change timeout default to 300
def get_minecraft_window_handle(version=None, timeout=300):
    """
    获取 Minecraft 窗口句柄
    
    Args:
        version (str): Minecraft 版本号，用于识别特定版本的窗口
        timeout (int): 超时时间（秒）
    
    Returns:
        int: 窗口句柄，如果未找到则返回 None
    """
    if platform.system() != "Windows":
        log("获取窗口句柄功能仅支持 Windows 系统")
        return None
    
    try:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
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

def monitor_minecraft_window(version, check_interval=1, callback=None):
    """
    监控 Minecraft 窗口，当窗口出现时获取句柄并显示浮动工具栏
    
    Args:
        version (str): Minecraft 版本号
        check_interval (int): 检查间隔（秒）
        callback (callable): 找到窗口后的回调函数
    """
    def monitor_thread():
        log(f"开始监控 Minecraft {version} 窗口...")
        
        # 等待一段时间让 Minecraft 启动
        time.sleep(3)
        
        # 尝试获取窗口句柄，延长超时时间至300秒（5分钟）
        hwnd = get_minecraft_window_handle(version, timeout=300)
        
        if hwnd:
            log(f"✅ Minecraft {version} 窗口已找到！")
            if callback:
                try:
                    callback()
                except Exception as e:
                    log(f"执行回调失败: {e}", logging.ERROR)
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
            
            # 创建工具栏 - 使用修复后的模块确保线程安全
            try:
                from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication, QTimer
                from . import mwtool
                
                # 确保在主线程中创建QObject
                app = QCoreApplication.instance()
                if not app:
                    log("无法获取 QApplication 实例", logging.ERROR)
                    return
                
                log("正在创建工具栏...", logging.DEBUG)
                
                # 直接在监控线程中调用工具栏创建（mwtool 内部会处理跨线程调用）
                try:
                    tool = mwtool.create_minecraft_tool(hwnd, version)
                    if tool:
                        log(f"工具栏创建成功: {tool}", logging.DEBUG)
                    else:
                        log("工具栏创建返回 None", logging.ERROR)
                except Exception as e:
                    log(f"工具栏创建失败: {e}", logging.ERROR)
                    import traceback
                    traceback.print_exc()
                
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