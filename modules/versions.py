'''
Versions.py
## Bloret Launcher 版本操作模块

### 模块功能：
 - [x] 删除 Minecraft 版本
 - [x] 修改 Minecraft 版本名称
 - [x] 删除自定义选项
 - [x] 修改自定义选项名称

***
###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
'''
from qfluentwidgets import InfoBar, InfoBarPosition, ComboBox
import logging, os, json, send2trash, platform, requests, shutil, concurrent.futures, threading
import sip # type: ignore
from pathlib import Path
from modules.win11toast import notify, update_progress
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
from modules.safe import handle_exception
import sys
from modules.customize import find_Customize

# 初始化全局变量
set_list = []
minecraft_list = []

def open_minecraft_version_folder(self,version,MINECRAFT_DIR):
    '''

    打开指定的 Minecraft 版本文件夹
     version 要删除的版本名称
     versions 版本 ComboBox 控件
     MINECRAFT_DIR Minecraft 安装目录

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在打开 Minecraft 版本文件夹：{version}")
    
    # 构建版本文件夹路径
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    
    try:
        # 检查版本文件夹是否存在
        if os.path.exists(version_path) and os.path.isdir(version_path):
            # 使用默认文件管理器打开文件夹
            os.startfile(version_path)
            log(f"成功打开版本文件夹：{version_path}")
        else:
            log(f"版本文件夹不存在：{version_path}", logging.ERROR)
            InfoBar.warning(
                title='⚠️ 提示',
                content=f"版本 {version} 的文件夹不存在",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"打开版本文件夹时发生错误: {e}", logging.ERROR)
        InfoBar.error(
            title='❌ 错误',
            content=f"打开版本 {version} 文件夹时发生错误: {str(e)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def delete_minecraft_version(self,version,label,card,MINECRAFT_DIR,homeInterface):
    '''

    删除指定的 Minecraft 版本文件夹
     version 要删除的版本名称
     label 版本控件
     MINECRAFT_DIR Minecraft 安装目录

    ### 删除 `.minecraft/version/{version}` 文件夹
     并移到回收站

    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在删除 Minecraft 版本：{version}")
    
    # 构建版本文件夹路径
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    
    try:
        # 检查版本文件夹是否存在
        if os.path.exists(version_path) and os.path.isdir(version_path):
            # 删除版本文件夹
            send2trash.send2trash(version_path)
            log(f"成功删除版本文件夹：{version_path}")
            
            # 更新全局列表
            global set_list, minecraft_list
            if version in set_list:
                set_list.remove(version)
            if version in minecraft_list:
                minecraft_list.remove(version)
            
            log(f"正在更新 UI 中的版本名称：del {label.text()}")
            # 从父布局中移除 label 控件并删除
            parent_layout = label.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(label)
            label.deleteLater()
            log(f"正在更新 UI 中的版本卡片：del {card}")
            # 从父布局中移除 card 控件并删除
            parent_layout = card.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(card)
            card.deleteLater()
            
            InfoBar.success(
                title=f'✅ 版本 {version} 已成功删除',
                content="如需找回，可前往系统回收站找回。",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            log(f"版本文件夹不存在：{version_path}", logging.ERROR)
            InfoBar.warning(
                title='⚠️ 提示',
                content=f"版本 {version} 的文件夹不存在",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"删除版本时发生错误: {e}", logging.ERROR)
        InfoBar.error(
            title='❌ 错误',
            content=f"删除版本 {version} 时发生错误: {str(e)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def Change_minecraft_version_name(self,version,label,MINECRAFT_DIR,homeInterface):
    '''
    ### 将 `.minecraft/version` 文件夹下 `{version}` 文件夹名称换成想要的文件名称并重读刷新。
     version 要修改的版本名称
     label 版本控件
     MINECRAFT_DIR Minecraft 安装目录

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在修改 Minecraft 版本名称：{version}")
    # 获取新的版本名称
    dialog = self.MessageBox("请输入新的名称", f"（当前名称：{version}）", self)
    if not dialog.exec():
        return  # 用户取消操作

    new_name = dialog.name_edit.text().strip()
    if not new_name:
        InfoBar.warning(
            title='⚠️ 提示',
            content="新名称不能为空",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    if version == new_name:
        InfoBar.info(
            title='ℹ️ 提示',
            content="新名称与原名称相同，无需更改",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    # 构建路径
    old_path = os.path.join(MINECRAFT_DIR, "versions", version)
    new_path = os.path.join(MINECRAFT_DIR, "versions", new_name)

    # 检查目标是否存在
    if os.path.exists(new_path):
        InfoBar.error(
            title='❌ 错误',
            content=f"目标名称 {new_name} 已存在，请选择其他名称。",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        return

    # 更新全局列表
    global set_list, minecraft_list

    if version in set_list:
        set_list[set_list.index(version)] = new_name
    if version in minecraft_list:
        minecraft_list[minecraft_list.index(version)] = new_name

    try:
        # 重命名文件夹
        os.rename(old_path, new_path)
        log(f"成功将版本文件夹从 {old_path} 重命名为 {new_path}")

        log(f"正在更新 UI 中的版本名称：{label.text()} -> {new_name}")
        # 修改 label 的 StrongBodyLabel 的文字为 new_name
        label.setText(new_name)
        
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"重命名版本时发生错误: {e}", logging.ERROR)
        InfoBar.error(
            title='❌ 错误',
            content=f"重命名版本 {version} 时发生错误: {str(e)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def delete_Customize(self,version,label,card,customize_list,homeInterface):
    '''
    ### 删除自定义选项
    将 配置文件中 `{version}` 对应的项目删除。
     version 要删除的自定义选项名称
     customize_list 自定义选项列表
    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在删除自定义选项：{version}")
    try:
        isOK,item=find_Customize(self,version)
        if isOK:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            if item in config_data["Customize"]:
                config_data["Customize"].remove(item)
            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
            self.config = config_data
            InfoBar.success(
                title='✅ 成功',
                content=f"{version} 已成功删除",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            customize_list.remove(version)

            log(f"正在更新 UI 中的版本名称：del {label.text()}")
            # 从父布局中移除 label 控件并删除
            parent_layout = label.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(label)
            label.deleteLater()

            log(f"正在更新 UI 中的版本卡片：del {card}")
            # 从父布局中移除 card 控件并删除
            parent_layout = card.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(card)
            card.deleteLater()

            self.run_cmcl_list(True)
        else:
            InfoBar.error(
                title='❌ 删除失败',
                content=f"未找到与 {version} 匹配的自定义程序",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        InfoBar.error(
            title='❌ 错误',
            content=f"保存到 config.json 时发生错误: {e}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
def Change_Customize_name(self,version,label,homeInterface):
    '''
    ### 将配置文件中 `{version}` 项目换成想要的名称并刷新重读。

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    log(f"正在修改自定义选项名称：{version}")
    isOK,item=find_Customize(self,version)
    if isOK:
        with open('config.json', 'r', encoding='utf-8') as file:
            config_data = json.load(file)

        if "Customize" not in config_data:
            config_data["Customize"] = []
        dialog = self.MessageBox("请输入新的名称", f"（当前名称：{version}）", self)
        if not dialog.exec():
            return  # 用户取消操作
        new_name = dialog.name_edit.text().strip()
        if not new_name or new_name.strip() == "":
            InfoBar.warning(
                title='⚠️ 提示',
                content="新名称不能为空",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        if version == new_name:
            InfoBar.info(
                title='ℹ️ 提示',
                content="新名称与原名称相同，无需更改",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        isOK, item = find_Customize(self, version)
        if isOK:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            if "Customize" not in config_data:
                config_data["Customize"] = []
            # 更新或添加自定义项
            is_found = False
            for i, custom_item in enumerate(config_data["Customize"]):
                if custom_item["showname"] == version:
                    custom_item["showname"] = new_name
                    is_found = True
                    break
            if not is_found:
                handle_exception(ValueError("尝试修改的项目不存在于自定义列表中"))
                InfoBar.error(
                    title='❌ 错误',
                    content=f"尝试修改的项目 {item} 不存在于自定义列表中",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return
            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
            self.config = config_data
            InfoBar.success(
                title=f'✅ 成功',
                content=f"版本名称已从 {version} 更改为 {new_name}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        log(f"正在更新 UI 中的版本名称：{label.text()} -> {new_name}")
        # 修改 label 的 StrongBodyLabel 的文字为 new_name
        label.setText(new_name)
        run_choose = homeInterface.findChild(ComboBox, "run_choose")
        run_choose.clear()
        run_choose.addItems(self.run_cmcl_list(True))
    else:
        InfoBar.error(
            title='❌ 修改失败',
            content=f"未找到与 {version} 匹配的自定义程序",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

def Get_Run_Script(version):
    """
    根据 cmcl.json 的内容生成启动 .minecraft 文件夹中指定版本的命令
    支持 Fabric 加载器启动
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        version (str): 要启动的 Minecraft 版本号
        
    Returns:
        str: 启动命令（批处理格式）
    """
    
    # 检查 cmcl.json 文件是否存在
    if not os.path.exists('cmcl.json'):
        raise FileNotFoundError("cmcl.json 文件不存在")
    
    # 读取 cmcl.json 配置
    with open('cmcl.json', 'r', encoding='utf-8') as f:
        cmcl_data = json.load(f)
    
    # 获取 Minecraft 目录
    minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
    versions_dir = os.path.join(minecraft_dir, "versions", version)
    
    # 检查版本目录是否存在
    if not os.path.exists(versions_dir):
        raise FileNotFoundError(f"版本 {version} 不存在于 {versions_dir}")
    
    # 获取版本 JSON 文件路径
    version_json_path = os.path.join(versions_dir, f"{version}.json")
    if not os.path.exists(version_json_path):
        raise FileNotFoundError(f"版本配置文件 {version_json_path} 不存在")
    
    # 读取版本配置
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_data = json.load(f)
    
    # 获取客户端 JAR 文件路径
    client_jar_path = os.path.join(versions_dir, f"{version}.jar")
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
        "-Dfile.encoding=COMPAT",
        "-Dstderr.encoding=UTF-8", 
        "-Dstdout.encoding=UTF-8",
        "-XX:+UseG1GC",
        "-XX:-UseAdaptiveSizePolicy",
        "-XX:-OmitStackTraceInFastThrow",
        "-Djdk.lang.Process.allowAmbiguousCommands=true",
        "-Dfml.ignoreInvalidMinecraftCertificates=True",
        "-Dfml.ignorePatchDiscrepancies=True",
        "-Dlog4j2.formatMsgNoLookups=true",
        "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"
    ]
    
    # 添加 Native 库路径参数
    natives_path = os.path.join(versions_dir, f"{version}-natives")
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
                        group_id, artifact_id, version = parts[0:3]
                        relative_path = os.path.join(
                            group_id.replace(".", "/"),
                            artifact_id,
                            version,
                            f"{artifact_id}-{version}.jar"
                        )
                        lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
                
                if lib_path and os.path.exists(lib_path):
                    if "org.ow2.asm" not in lib.get("name", "").lower():
                        classpath.append(lib_path)
    
    # 检查是否为 Fabric 版本
    is_fabric = "fabric" in version.lower() or any("fabric" in lib.get("name", "").lower() for lib in version_data.get("libraries", []))

    if is_fabric:
        log(f"检测到 Fabric 版本: {version}")
    else:
        log(f"检测到原版: {version}")
    
    # 添加内存参数
    launch_args.extend([
        "-Xmn844m",
        "-Xmx5632m"
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
        fabric_version_dir = os.path.join(versions_dir, version)
        if os.path.exists(fabric_version_dir):
            for file in os.listdir(fabric_version_dir):
                if file.endswith('.jar') and 'fabric' in file.lower():
                    jar_path = os.path.join(fabric_version_dir, file)
                    fabric_libs.append(jar_path)
        
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
                    group_id, artifact_id, version = parts[0:3]
                    relative_path = os.path.join(
                        group_id.replace(".", "/"),
                        artifact_id,
                        version,
                        f"{artifact_id}-{version}.jar"
                    )
                    lib_path = os.path.join(minecraft_dir, "libraries", relative_path)
            
            if lib_path and os.path.exists(lib_path):
                # 处理ASM库
                if "org.ow2.asm" in lib_name:
                    # 从库名中提取版本号和模块名
                    parts = lib_name.split(":")
                    if len(parts) >= 3:
                        asm_module = parts[1]  # 例如 "asm", "asm-commons" 等
                        version = parts[2]  # 版本号
                        
                        # 如果这是一个更高版本，或者这个模块还没有被记录
                        if asm_module not in asm_libs or version > asm_libs[asm_module]["version"]:
                            asm_libs[asm_module] = {"version": version, "path": lib_path}
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
        
        # 1. 添加 ASM 库（按特定顺序）
        asm_modules_order = ["asm", "asm-commons", "asm-tree", "asm-analysis", "asm-util"]
        for module in asm_modules_order:
            if module in asm_libs:
                final_classpath.append(asm_libs[module]["path"])
                log(f"添加ASM库 {module} 版本 {asm_libs[module]['version']}")
        
        # 2. 添加 Fabric 核心库
        final_classpath.extend(fabric_libs)
        
        # 3. 添加其他所有库
        final_classpath.extend(classpath)
        
        # 更新类路径
        classpath = final_classpath
    
    # 添加客户端 JAR 到 classpath
    classpath.append(client_jar_path)
    
    # 添加类路径参数
    launch_args.append("-cp")
    launch_args.append('"' + ";".join(classpath) + '"')  # Windows 使用分号分隔
    
    # 添加主类和参数
    if is_fabric:
        # Fabric 使用 KnotClient 主类而不是 -jar 参数
        launch_args.append("net.fabricmc.loader.impl.launch.knot.KnotClient")
    else:
        # 原始 Minecraft 启动方式
        launch_args.append("-jar")
        launch_args.append(f'"{os.path.join(os.getcwd(), "JavaWrapper.jar")}"')
        launch_args.append("net.minecraft.client.main.Main")
    
    # 添加游戏参数
    game_dir = os.path.join(minecraft_dir, "versions", version)
    assets_dir = os.path.join(minecraft_dir, "assets")
    
    # 获取资产索引
    asset_index = version_data.get("assetIndex", {}).get("id", version)
    
    # 设置 versionType
    version_type = "Bloret-Launcher"
    
    # 检查账户信息相关字段
    missing_fields = []
    if not account_info:
        missing_fields.append("账户信息")
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
        "--version", version,
        "--gameDir", f'"{game_dir}"',
        "--assetsDir", f'"{assets_dir}"',
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
    bat_command = " ".join(launch_args)
    
    log(f"生成的启动命令: {bat_command}")
    return bat_command

def InstallMinecraftVersion(version, minecraft_dir=None, download_dialog=None):
    # 如果没有提供下载对话框，则创建并显示一个新的
    if download_dialog is None:
        try:
            from PyQt5.QtWidgets import QDialog
            from PyQt5 import uic
            import json
            
            download_dialog = QDialog()
            uic.loadUi("ui/MCVer_downloading.ui", download_dialog)
            download_dialog.setWindowTitle(f"正在下载 Minecraft {version}")
            
            # 设置MaxThread的值
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                max_thread_value = config.get("MaxThread", 2000)
                if hasattr(download_dialog, 'MaxThread'):
                    download_dialog.MaxThread.setText(str(max_thread_value))
            except Exception as e:
                log(f"设置MaxThread值时出错: {e}")
                
            download_dialog.show()
        except Exception as e:
            log(f"创建下载对话框时出错: {e}")
            download_dialog = None
    
    from threading import Thread
    thread = Thread(target=_install_minecraft_version_threaded, args=(version, minecraft_dir, download_dialog))
    thread.start()

def _install_minecraft_version_threaded(version, minecraft_dir=None, download_dialog=None):
    '''
    下载并安装指定版本的Minecraft
    
    Args:
        version (str): 要安装的Minecraft版本，例如 "1.21.8"
        minecraft_dir (str, optional): Minecraft安装目录。如果未提供，默认为 %appdata%/Bloret-Launcher/.minecraft
    
    Returns:
        bool: 安装成功返回True，失败返回False
    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    try:
        # 创建Windows 11通知
        notify(progress={
            'title': 'Minecraft版本安装',
            'status': '正在准备安装...',
            'value': '0',
            'valueStringOverride': '0%'
        })

        # 0. 如果minecraft_dir未提供，设置默认值
        if minecraft_dir is None:
            appdata = os.environ.get('APPDATA', '')
            minecraft_dir = os.path.join(appdata, 'Bloret-Launcher', '.minecraft')

        log(f"开始安装Minecraft版本: {version}，安装目录: {minecraft_dir}")

        # 确保目录存在
        os.makedirs(minecraft_dir, exist_ok=True)
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)

        # 1. 获取版本清单
        update_progress({
            'value': 0.1, 
            'valueStringOverride': '10%',
            'status': '正在获取版本清单...'
        })
        manifest_url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
        log(f"正在获取版本清单: {manifest_url}")

        response = requests.get(manifest_url, proxies=None)
        if response.status_code != 200:
            log(f"获取版本清单失败: HTTP {response.status_code}", logging.ERROR)
            return False

        manifest_data = response.json()

        # 2. 在清单中查找指定版本
        update_progress({
            'value': 0.2, 
            'valueStringOverride': '20%',
            'status': '正在查找指定版本...'
        })
        version_info = None
        for ver in manifest_data.get("versions", []):
            if ver.get("id") == version:
                version_info = ver
                break

        if not version_info:
            log(f"未找到版本 {version}", logging.ERROR)
            return False

        log(f"找到版本信息: {version_info}")

        # 3. 获取版本详细信息URL并替换域名
        update_progress({
            'value': 0.3, 
            'valueStringOverride': '30%',
            'status': '正在获取版本详细信息...'
        })
        original_url = version_info.get("url")
        version_info_url = original_url.replace("https://piston-meta.mojang.com/", "https://bmclapi2.bangbang93.com/")

        log(f"正在获取版本详细信息: {version_info_url}")

        # 4. 获取版本详细信息
        response = requests.get(version_info_url)
        if response.status_code != 200:
            log(f"获取版本详细信息失败: HTTP {response.status_code}", logging.ERROR)
            return False

        version_data = response.json()

        # 5. 创建版本目录
        update_progress({
            'value': 0.4, 
            'valueStringOverride': '40%',
            'status': '正在创建版本目录...'
        })
        version_dir = os.path.join(versions_dir, version)
        os.makedirs(version_dir, exist_ok=True)

        # 保存版本JSON文件
        version_json_path = os.path.join(version_dir, f"{version}.json")
        with open(version_json_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=4)

        log(f"已保存版本JSON文件: {version_json_path}")

        # 设置 First_Step_CheckBox 为 true
        if download_dialog:
            try:
                from PyQt5.QtWidgets import QCheckBox
                checkbox = download_dialog.findChild(QCheckBox, "First_Step_CheckBox")
                if checkbox:
                    checkbox.setChecked(True)
            except Exception as e:
                log(f"设置First_Step_CheckBox时出错: {e}")

        # 下载客户端JAR文件
        update_progress({
            'value': 0.5, 
            'valueStringOverride': '50%',
            'status': '正在下载客户端JAR文件...'
        })
        if "downloads" in version_data and "client" in version_data["downloads"]:
            client_info = version_data["downloads"]["client"]
            client_url = client_info["url"]
            client_url = client_url.replace("https://piston-data.mojang.com/", "https://bmclapi2.bangbang93.com/")

            client_jar_path = os.path.join(version_dir, f"{version}.jar")
            log(f"正在下载客户端JAR文件: {client_url}")

            response = requests.get(client_url, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(client_jar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 更新客户端JAR进度条
                            if download_dialog and total_size > 0:
                                try:
                                    from PyQt5.QtWidgets import QProgressBar
                                    progress_bar = download_dialog.findChild(QProgressBar, "client_jar_progress")
                                    if progress_bar:
                                        progress_value = int((downloaded_size / total_size) * 100)
                                        progress_bar.setValue(progress_value)
                                except Exception as e:
                                    log(f"更新client_jar_progress时出错: {e}")
                
                log(f"已下载客户端JAR文件: {client_jar_path}")
            else:
                log(f"下载客户端JAR文件失败: HTTP {response.status_code}", logging.ERROR)
                return False
        else:
            log("版本信息中未找到客户端下载链接", logging.ERROR)
            return False

        # 创建natives目录
        natives_dir = os.path.join(version_dir, f"{version}-natives")
        os.makedirs(natives_dir, exist_ok=True)

        # 下载库文件
        update_progress({
            'value': 0.6, 
            'valueStringOverride': '60%',
            'status': '正在下载库文件...'
        })
        libraries_dir = os.path.join(minecraft_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        if "libraries" in version_data:
            log(f"开始下载库文件，共 {len(version_data['libraries'])} 个")

            # 用于跟踪活动下载线程数的变量
            active_downloads = 0
            active_downloads_lock = threading.Lock()

            def _download_single_library(lib):
                nonlocal active_downloads
                # 增加活动下载计数
                with active_downloads_lock:
                    active_downloads += 1
                    # 更新活动线程数显示
                    if download_dialog:
                        try:
                            from PyQt5.QtWidgets import QLabel
                            thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                            if thread_label:
                                thread_label.setText(str(active_downloads))
                        except Exception as e:
                            log(f"更新libraries_file_working_Thread时出错: {e}")

                try:
                    # 检查库是否适用于当前系统
                    should_download = True
                    if "rules" in lib:
                        should_download = False
                        for rule in lib["rules"]:
                            if rule.get("action") == "allow":
                                os_rule = rule.get("os", {})
                                if not os_rule or (os_rule.get("name", "").lower() == platform.system().lower() or
                                                  (os_rule.get("name") == "windows" and platform.system() == "Windows") or
                                                  (os_rule.get("name") == "osx" and platform.system() == "Darwin") or
                                                  (os_rule.get("name") == "linux" and platform.system() == "Linux")):
                                    should_download = True
                                    break

                    if should_download and "downloads" in lib:
                        # 下载artifact
                        if "artifact" in lib["downloads"]:
                            artifact = lib["downloads"]["artifact"]
                            artifact_path = os.path.join(libraries_dir, artifact["path"])
                            artifact_dir = os.path.dirname(artifact_path)
                            os.makedirs(artifact_dir, exist_ok=True)

                            artifact_url = artifact["url"]
                            artifact_url = artifact_url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/")

                            if not os.path.exists(artifact_path):
                                log(f"正在下载库文件: {artifact_url} -> {artifact_path}")
                                for attempt in range(10): # 重试10次
                                    try:
                                        response = requests.get(artifact_url, proxies=None)
                                        if response.status_code == 200:
                                            with open(artifact_path, 'wb') as f:
                                                f.write(response.content)
                                            break # 成功则跳出循环
                                        else:
                                            log(f"下载库文件失败: {artifact_path}, HTTP {response.status_code}", logging.WARNING)
                                    except requests.exceptions.RequestException as e:
                                        log(f"下载库文件时发生网络请求错误，正在重试 (第 {attempt + 1} 次): {artifact_path}, 错误: {e}, url: {artifact_url}", logging.WARNING)
                                        time.sleep(0.1) # 等待0.1秒后重试
                                    except Exception:
                                        exc_type, exc_value, exc_traceback = sys.exc_info()
                                        handle_exception(exc_type, exc_value, exc_traceback)
                                        break # 其他错误则不重试，直接跳出

                        # 下载natives
                        if "classifiers" in lib["downloads"]:
                            classifiers = lib["downloads"]["classifiers"]
                            native_key = None

                            if platform.system() == "Windows" and "natives-windows" in classifiers:
                                native_key = "natives-windows"
                            elif platform.system() == "Darwin" and "natives-macos" in classifiers:
                                native_key = "natives-macos"
                            elif platform.system() == "Linux" and "natives-linux" in classifiers:
                                native_key = "natives-linux"

                            if native_key and native_key in classifiers:
                                native = classifiers[native_key]
                                native_path = os.path.join(libraries_dir, lib["downloads"]["artifact"]["path"].replace(".jar", f"-{native_key}.jar"))
                                native_dir = os.path.dirname(native_path)
                                os.makedirs(native_dir, exist_ok=True)

                                native_url = native["url"]
                                native_url = native_url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/")

                                if not os.path.exists(native_path):
                                    log(f"正在下载native库文件: {native_path}")
                                for attempt in range(3): # 重试3次
                                    try:
                                        response = requests.get(native_url, proxies=None)
                                        if response.status_code == 200:
                                            with open(native_path, 'wb') as f:
                                                f.write(response.content)
                                            break # 成功则跳出循环
                                        else:
                                            log(f"下载native库文件失败: {native_path}, HTTP {response.status_code}", logging.WARNING)
                                    except requests.exceptions.RequestException as e:
                                        log(f"下载native库文件时发生网络请求错误，正在重试 (第 {attempt + 1} 次): {native_path}, 错误: {e}", logging.WARNING)
                                        time.sleep(1) # 等待1秒后重试
                                    except Exception:
                                        exc_type, exc_value, exc_traceback = sys.exc_info()
                                        handle_exception(exc_type, exc_value, exc_traceback)
                                        break # 其他错误则不重试，直接跳出
                finally:
                    # 减少活动下载计数
                    with active_downloads_lock:
                        active_downloads -= 1
                        # 更新活动线程数显示
                        if download_dialog:
                            try:
                                from PyQt5.QtWidgets import QLabel
                                thread_label = download_dialog.findChild(QLabel, "libraries_file_working_Thread")
                                if thread_label:
                                    thread_label.setText(str(active_downloads))
                            except Exception as e:
                                log(f"更新libraries_file_working_Thread时出错: {e}")

            # 从 config.json 读取 MaxThread
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                max_workers = config_data.get("MaxThread", 2000) # 默认值 2000
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                handle_exception(exc_type, exc_value, exc_traceback)
                max_workers = 2000 # 读取失败时使用默认值

            log(f"使用 {max_workers} 个线程下载库文件")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_download_single_library, lib) for lib in version_data["libraries"]]
                total_libs = len(futures)
                
                # 更新库文件进度条
                if download_dialog:
                    try:
                        from PyQt5.QtWidgets import QProgressBar
                        lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                        if lib_progress_bar:
                            lib_progress_bar.setValue(0)
                    except Exception as e:
                        log(f"初始化libraries_progress时出错: {e}")
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result() # 获取结果以捕获异常
                    except Exception:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        handle_exception(exc_type, exc_value, exc_traceback)
                    finally:
                        completed += 1
                        # 更新库文件进度条
                        if download_dialog:
                            try:
                                from PyQt5.QtWidgets import QProgressBar
                                lib_progress_bar = download_dialog.findChild(QProgressBar, "libraries_progress")
                                if lib_progress_bar:
                                    progress_value = int((completed / total_libs) * 100)
                                    lib_progress_bar.setValue(progress_value)
                            except Exception as e:
                                log(f"更新libraries_progress时出错: {e}")
        
        # 下载资源索引
        if "assetIndex" in version_data:
            asset_index = version_data["assetIndex"]
            asset_index_url = asset_index["url"]
            asset_index_url = asset_index_url.replace("https://piston-meta.mojang.com/", "https://bmclapi2.bangbang93.com/")
            
            assets_dir = os.path.join(minecraft_dir, "assets")
            indexes_dir = os.path.join(assets_dir, "indexes")
            objects_dir = os.path.join(assets_dir, "objects")
            
            os.makedirs(indexes_dir, exist_ok=True)
            os.makedirs(objects_dir, exist_ok=True)
            
            asset_index_id = asset_index["id"]
            asset_index_path = os.path.join(indexes_dir, f"{asset_index_id}.json")
            
            update_progress("正在下载资源索引...")
            log(f"正在下载资源索引: {asset_index_url}")
            response = requests.get(asset_index_url)
            if response.status_code == 200:
                with open(asset_index_path, 'wb') as f:
                    f.write(response.content)
                log(f"已下载资源索引: {asset_index_path}")
                
                # 读取资源索引并下载资源文件
                with open(asset_index_path, 'r', encoding='utf-8') as f:
                    asset_index_data = json.load(f)
                
                if "objects" in asset_index_data:
                    assets_count = len(asset_index_data['objects'])
                    update_progress(f"开始下载资源文件，共 {assets_count} 个...")
                    log(f"开始下载资源文件，共 {assets_count} 个")
                    
                    # 创建多线程下载资源文件
                    def download_asset(asset_name, asset_info):
                        try:
                            hash_value = asset_info["hash"]
                            hash_prefix = hash_value[:2]
                            object_path = os.path.join(objects_dir, hash_prefix, hash_value)
                            
                            # 如果文件已存在且大小正确，则跳过
                            if os.path.exists(object_path) and os.path.getsize(object_path) == asset_info["size"]:
                                return True
                            
                            # 创建目录
                            os.makedirs(os.path.dirname(object_path), exist_ok=True)
                            
                            # 构建URL
                            asset_url = f"https://bmclapi2.bangbang93.com/assets/{hash_prefix}/{hash_value}"
                            
                            # 下载文件
                            response = requests.get(asset_url, stream=True)
                            if response.status_code == 200:
                                with open(object_path, 'wb') as f:
                                    shutil.copyfileobj(response.raw, f)
                                return True
                            else:
                                log(f"下载资源文件失败: {asset_name}, HTTP {response.status_code}", logging.WARNING)
                                return False
                        except Exception:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            handle_exception(exc_type, exc_value, exc_traceback)
                            return False
                    
                    # 使用线程池进行多线程下载
                    from concurrent.futures import ThreadPoolExecutor
                    
                    # 设置最大线程数
                    max_workers = min(32, os.cpu_count() * 4)
                    log(f"使用 {max_workers} 个线程下载资源文件")
                    
                    # 创建Windows 11通知
                    notify(progress={
                        'title': 'Minecraft资源下载',
                        'status': '正在下载资源文件...',
                        'value': '0',
                        'valueStringOverride': f'0/{assets_count} 个'
                    })
                    
                    # 创建线程池
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # 提交所有下载任务
                        future_to_asset = {executor.submit(download_asset, asset_name, asset_info): asset_name 
                                          for asset_name, asset_info in asset_index_data["objects"].items()}
                        
                        # 处理完成的任务
                        success_count = 0
                        failed_count = 0
                        completed_count = 0
                        for future in concurrent.futures.as_completed(future_to_asset):
                            asset_name = future_to_asset[future]
                            try:
                                success = future.result()
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                            except Exception as e:
                                log(f"处理资源文件时发生错误: {asset_name}, {str(e)}", logging.WARNING)
                                failed_count += 1
                            finally:
                                completed_count += 1
                            update_progress(f"正在下载资源文件...", value=completed_count, valueStringOverride=f'{completed_count}/{assets_count} 个')
                            # 每下载10个文件或达到总数的5%时更新一次通知，避免频繁更新
                            if completed_count % 10 == 0 or completed_count % int(assets_count * 0.05) == 0 or completed_count == assets_count:
                                update_progress({
                                    'value': completed_count/assets_count, 
                                    'valueStringOverride': f'{completed_count}/{assets_count} 个',
                                    'status': f'正在下载资源文件... ({int(completed_count/assets_count*100)}%)'
                                })
                    
                    # 更新通知为完成状态
                    update_progress({
                        'value': 1, 
                        'valueStringOverride': f'{assets_count}/{assets_count} 个',
                        'status': '资源文件下载完成!'
                    })
                    
                    # 输出下载结果
                    log(f"资源文件下载完成: 成功 {success_count} 个, 失败 {failed_count} 个")
                    
                    # 如果有失败的资源文件，记录警告
                    if failed_count > 0:
                        log(f"有 {failed_count} 个资源文件下载失败，但不影响游戏运行", logging.WARNING)
            else:
                log(f"下载资源索引失败: HTTP {response.status_code}", logging.WARNING)
        
        log(f"Minecraft版本 {version} 安装完成")
        update_progress({
            'status': f'Minecraft版本 {version} 安装完成!',
            'value': 100
        })
        return True
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"安装Minecraft版本 {version} 时发生错误: {str(e)}", logging.ERROR)
        return False
    finally:
        # 关闭下载对话框
        if download_dialog:
            try:
                download_dialog.close()
            except Exception as e:
                log(f"关闭下载对话框时出错: {e}")
