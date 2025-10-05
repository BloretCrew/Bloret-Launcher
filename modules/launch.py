from qfluentwidgets import InfoBar, InfoBarPosition, ComboBox
import logging, os, json, send2trash, platform, requests, shutil, concurrent.futures, threading, time
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

def Get_Run_Script(mc_version):
    """
    根据 cmcl.json 的内容生成启动 .minecraft 文件夹中指定版本的命令
    支持 Fabric 加载器启动
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        mc_version (str): 要启动的 Minecraft 版本号
        
    Returns:
        str: 启动命令（批处理格式）
    """
    
    # 检查 cmcl.json 文件是否存在
    if not os.path.exists('cmcl.json'):
        raise FileNotFoundError(i18nText("cmcl.json 文件不存在"))
    
    # 读取 cmcl.json 配置
    with open('cmcl.json', 'r', encoding='utf-8') as f:
        cmcl_data = json.load(f)
    
    # 获取 Minecraft 目录
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        minecraft_dir = config_data.get('minecraft_dir', '')
        if not minecraft_dir:
            # 如果配置中没有指定，则使用默认路径
            appdata = os.environ.get('APPDATA', '')
            minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')
    except Exception:
        # 如果读取配置文件失败，使用默认路径
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
    
    # 获取 Java 路径 (使用指定的 Zulu JDK 路径)
    java_path = r"java"
    
    # 获取账户信息
    account_info = None
    if cmcl_data.get("accounts"):
        # 查找选中的账户或使用第一个账户
        account_info = next((acc for acc in cmcl_data["accounts"] if acc.get("selected")), 
                           cmcl_data["accounts"][0])
    
    # 设置用户名
    username = "Bloret-Player"
    if account_info:
        username = account_info.get("playerName", "Bloret-Player")
    
    # 构建基本启动参数
    launch_args = [
        f'"{java_path}"',  # Java路径需要用引号包围
        "--enable-native-access=ALL-UNNAMED",  # 解决Java警告
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",  # 抑制弃用警告
        "--add-opens", "java.base/java.util=ALL-UNNAMED",  # 抑制弃用警告
        "--add-opens", "java.base/sun.nio.ch=ALL-UNNAMED",  # 抑制更多警告
        "--add-opens", "java.base/sun.misc=ALL-UNNAMED",   # 抑制sun.misc警告
        "--add-opens", "java.base/jdk.internal.misc=ALL-UNNAMED",  # 抑制jdk.internal.misc警告
        "--add-opens", "java.base/jdk.internal.ref=ALL-UNNAMED",   # 抑制jdk.internal.ref警告
        "--add-exports", "java.base/sun.nio.ch=ALL-UNNAMED",  # 导出sun.nio.ch包
        "--add-exports", "java.base/sun.misc=ALL-UNNAMED",   # 导出sun.misc包
        "--add-exports", "java.base/jdk.internal.misc=ALL-UNNAMED",  # 导出jdk.internal.misc包
        "--add-exports", "java.base/jdk.internal.ref=ALL-UNNAMED",   # 导出jdk.internal.ref包
        "-Dio.netty.tryReflectionSetAccessible=true",  # 解决Netty反射问题
        "-Dio.netty.native.skipTryReflectionSetAccessible=true",  # 跳过Netty反射检查
        "-Dsun.misc.unsafe.throwException=false",  # 禁用sun.misc.Unsafe异常
        "-Djdk.attach.allowAttachSelf=true",  # 允许自我附加
        "-Djdk.module.IllegalAccess.silent=true",  # 静默非法访问
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
        "-Dsun.misc.URLClassPath.disableJarChecking=true",  # 禁用JAR检查
        "-Djava.rmi.server.useCodebaseOnly=true",  # 仅使用代码库
        "-Dcom.sun.management.jmxremote.local.only=true",  # 仅限本地JMX远程
        "-Dcom.sun.management.jmxremote.authenticate=false",  # 禁用JMX身份验证
        "-Dcom.sun.management.jmxremote.ssl=false",  # 禁用JMX SSL
        "-XX:-OmitStackTraceInFastThrow",  # 不省略快速抛出的堆栈跟踪
        "-Djna.nosys=true",  # 禁用系统级JNA库
        "-Djnidispatch.preserve=true",  # 保留JNI分发
        "-Dorg.lwjgl.util.Debug=false",  # 禁用LWJGL调试
        "-Dorg.lwjgl.util.noload=true",  # 不加载LWJGL库
        "-Djava.awt.headless=false",  # 非headless模式
        "-Dsun.java2d.noddraw=true",  # 禁用DirectDraw
        "-Dsun.java2d.d3d=false",  # 禁用Direct3D
        "-Dsun.java2d.opengl=false",  # 禁用OpenGL
        "-Dsun.java2d.pmoffscreen=false",  # 禁用离屏渲染
        "-Dsun.java2d.accthreshold=0",  # 禁用硬件加速
        "-XX:ErrorFile=./hs_err_pid%p.log",  # 错误日志文件
        "-XX:+UnlockExperimentalVMOptions",  # 解锁实验性选项
        "-XX:+UseG1GC",  # 使用G1垃圾收集器
        "-XX:+UseCompressedOops",  # 使用压缩对象指针
        "-XX:+OptimizeStringConcat",  # 优化字符串连接
        "-XX:+UseStringDeduplication"  # 启用字符串去重
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
    final_classpath = []
    
    # 添加所有依赖库
    libraries_dir = os.path.join(minecraft_dir, "libraries")
    optifine_libs = []
    missing_libraries = []  # 用于记录缺失的库文件
    if "libraries" in version_data:
        for lib in version_data["libraries"]:
            # 检查库的规则
            if "rules" in lib:
                allow_lib = False
                for rule in lib['rules']:
                    # 检查规则是否允许该库
                    if "action" in rule and rule["action"] == "allow":
                        # 检查操作系统规则
                        if "os" in rule:
                            os_rule = rule["os"]
                            if "name" in os_rule:
                                # 检查操作系统名称
                                os_name = os.name  # 获取当前操作系统名称
                                if os_rule["name"] == "windows" and os_name != "nt":
                                    continue
                                elif os_rule["name"] == "osx" and os_name != "posix":
                                    continue
                                elif os_rule["name"] == "linux" and os_name != "posix":
                                    continue
                        allow_lib = True
                if not allow_lib:
                    continue
            
            # 检查库是否需要下载
            if "downloads" in lib and "artifact" in lib['downloads']:
                lib_path = os.path.join(minecraft_dir, "libraries", lib['downloads']['artifact']["path"])
            else:
                # 从库名称构建路径
                parts = lib['name'].split(":")
                if len(parts) == 3:
                    group = parts[0].replace(".", "/")
                    artifact = parts[1]
                    version_lib = parts[2]
                    lib_filename = f"{artifact}-{version_lib}.jar"
                    lib_path = os.path.join(minecraft_dir, "libraries", group, artifact, version_lib, lib_filename)
                else:
                    log(f"无法解析库名称: {lib['name']}", logging.WARNING)
                    continue
            
            # 添加库到类路径
            final_classpath.append(lib_path)
            
            # 处理特殊库（如OptiFine）
            if "name" in lib and "optifine" in lib['name'].lower():
                optifine_libs.append(lib_path)
    
    # 检查是否为 Fabric 版本
    is_fabric = "fabric" in mc_version.lower() or any("fabric" in lib.get("name", "").lower() for lib in version_data.get("libraries", []))

    if is_fabric:
        log(f"检测到 Fabric 版本: {mc_version}")
    else:
        log(f"检测到原版: {mc_version}")
    
    # 添加内存参数 (根据PCL中的默认设置)
    # PCL中默认分配内存为854x480，这里设置合理的内存参数
    launch_args.extend([
        "-Xmn192m",  # 年轻代内存
        "-Xmx4096m"  # 最大堆内存，设置为4GB
    ])
    
    # 添加自定义参数
    launch_args.append(f'-Doolloo.jlw.tmpdir="{os.path.join(os.getcwd(), "Bloret Launcher")}"')
    
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
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            max_workers = config_data.get("MaxThread", 64)  # 默认值改为64，避免资源耗尽
        except Exception:
            max_workers = 64  # 读取失败时使用默认值
        
        # 创建下载器并启动下载线程
        downloader = LibraryDownloader(missing_libraries, max_workers)
        download_thread = threading.Thread(target=downloader.download_libraries)
        download_thread.daemon = True
        download_thread.start()
        
        # 等待下载完成
        downloader.completed_event.wait()
        
        # 重新检查库文件并添加到类路径中
        # 这一步确保即使之前缺失的库文件现在也已下载并添加到类路径中
        for lib, lib_path in missing_libraries:
            if os.path.exists(lib_path) and lib_path not in classpath:
                classpath.append(lib_path)
                log(f"添加之前缺失但现已下载的库: {lib_path}")
    
    # 添加类路径参数
    launch_args.extend(["-cp", '\"' + ";".join(classpath) + '\"'])  # Windows 使用分号分隔
    
    # Add Fabric Loader arguments to ensure mods are loaded
    launch_args.extend(["-Dfabric.addMods=" + mods_dir])
    
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
    
    # 添加游戏参数
    # 对于Fabric版本，需要使用实际的游戏版本号而不是Fabric加载器版本号
    actual_game_version = mc_version
    game_dir_version = mc_version  # 用于构建game_dir的版本
    
    if is_fabric and "-fabric-" in mc_version.lower():
        # 对于Fabric版本，目录结构为 .minecraft/versions/实际版本-fabric-加载器版本/实际版本-fabric-加载器版本.json
        # 但游戏目录应该是 .minecraft/versions/实际版本-fabric-加载器版本/实际版本.json
        # 我们需要从版本名称中提取实际的游戏版本
        # 例如: 1.21.8-fabric-0.17.2 应该对应游戏版本 1.21.8
        actual_game_version = mc_version.split("-fabric-")[0]
        game_dir_version = mc_version  # game_dir仍然使用完整版本名作为目录名
    
    # 游戏目录应该是主 .minecraft 目录，而不是版本特定目录
    game_dir = minecraft_dir
    assets_dir = os.path.join(minecraft_dir, "assets")
    
    # 检查游戏目录和资产目录是否存在
    if not os.path.exists(game_dir):
        raise FileNotFoundError(f"游戏目录不存在: {game_dir}")
    
    if not os.path.exists(assets_dir):
        raise FileNotFoundError(f"资产目录不存在: {assets_dir}")
    
    # 获取资产索引
    asset_index = version_data.get("assetIndex", {}).get("id", mc_version)
    
    # 设置 versionType
    version_type = "Bloret Launcher"
    
    # 检查登录方式并设置相应参数
    login_method = account_info.get("loginMethod", 0) if account_info else 0
    
    # 在日志中以列表形式记录启动信息
    log("启动信息:")
    log(f"- Minecraft 版本: {mc_version}")  # 使用完整版本名而不是解析后的版本
    log(f"- 登录方式: {'离线登录' if login_method == 0 else '微软登录' if login_method == 2 else '未知'}")
    log(f"- 登录名称: {username}")
    if account_info:
        log(f"- UUID: {account_info.get('uuid', 'N/A')}")
        log(f"- AccessToken: {'******' if account_info.get('accessToken') else 'N/A'}")
    
    # 根据登录方式设置启动参数
    if login_method == 0:  # 离线登录
        launch_args.extend([
            "--username", username,
            "--version", mc_version,  # 使用完整版本名而不是解析后的版本
            "--gameDir", game_dir,  # 不要在路径外额外添加引号
            "--assetsDir", assets_dir,  # 不要在路径外额外添加引号
            "--assetIndex", str(asset_index),
            "--uuid", "00000000000000000000000000000000",
            "--accessToken", "00000000000000000000000000000000",
            "--userType", "legacy",
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    elif login_method == 2:  # 微软登录
        # 检查账户信息相关字段
        missing_fields = []
        if not account_info:
            missing_fields.append(i18nText("账户信息"))
        else:
            if not account_info.get("uuid"):
                missing_fields.append("UUID")
            if not account_info.get("accessToken"):
                missing_fields.append("AccessToken")
            # 你可以根据需要继续检查其他字段

        if missing_fields:
            raise ValueError(f"缺少必要的启动参数: {', '.join(missing_fields)}，请先登录或完善账户信息。")
            
        launch_args.extend([
            "--username", username,
            "--version", mc_version,  # 使用完整版本名而不是解析后的版本
            "--gameDir", game_dir,  # 不要在路径外额外添加引号
            "--assetsDir", assets_dir,  # 不要在路径外额外添加引号
            "--assetIndex", str(asset_index),
            "--uuid", account_info.get("uuid"),
            "--accessToken", account_info.get("accessToken"),
            "--clientId", account_info.get("clientId", ""),
            "--xuid", account_info.get("xuid", ""),
            "--userType", account_info.get("userType", "msa"),
            "--versionType", version_type,
            "--width", "854",
            "--height", "480"
        ])
    
    # 构建命令
    # 不添加过滤器，避免被Minecraft误认为是游戏参数
    bat_command = " ".join(launch_args)
    
    log(f"生成的启动命令: {bat_command}")
    log(f"最终生成的启动命令 (包含 chcp 65001 和 cd 文件夹): {"chcp 65001\n" + f'cd {os.path.join(minecraft_dir, "versions", game_dir_version)}\n' + bat_command}")
    return "chcp 65001\n" + f'cd {os.path.join(minecraft_dir, "versions", game_dir_version)}\n' + bat_command
