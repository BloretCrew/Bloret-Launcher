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
import logging, os, json, send2trash, platform
import sip # type: ignore
# 以下导入的部分是 Bloret Launcher 所有的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
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
            
    except Exception as e:
        handle_exception(e)
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
    except Exception as e:
        handle_exception(e)
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
    except Exception as e:
        handle_exception(e)
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
    except Exception as e:
        handle_exception(e)
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
    不使用 cmcl.exe，而是直接生成启动命令
    
    Args:
        version (str): 要启动的 Minecraft 版本号
        
    Returns:
        str: 启动命令（PowerShell格式）
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
    
    # 获取 Java 路径 (使用系统默认 Java)
    java_path = "java"
    if platform.system() == "Windows":
        java_path = "javaw"  # Windows 下使用 javaw 避免显示控制台
    
    # 获取账户信息
    account_info = None
    if cmcl_data.get("accounts"):
        # 查找选中的账户或使用第一个账户
        account_info = next((acc for acc in cmcl_data["accounts"] if acc.get("selected")), 
                           cmcl_data["accounts"][0])
    
    # 设置用户名
    username = "Player"
    if account_info:
        username = account_info.get("playerName", "Player")
    
    # 构建基本启动参数
    launch_args = [
        java_path,
        "-Dfile.encoding=COMPAT",
        "-Dstderr.encoding=UTF-8", 
        "-Dstdout.encoding=UTF-8",
        "-XX:+UseG1GC",
        "-XX:-UseAdaptiveSizePolicy",
        "-XX:-OmitStackTraceInFastThrow",
        "-Djdk.lang.Process.allowAmbiguousCommands=true",
        "-Dfml.ignoreInvalidMinecraftCertificates=True",
        "-Dfml.ignorePatchDiscrepancies=True",
        "-Dlog4j2.formatMsgNoLookups=true"
    ]
    
    # 添加操作系统特定的JVM参数
    if platform.system() == "Windows":
        launch_args.append("-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump")
    
    # 添加 Native 库路径参数
    natives_path = os.path.join(versions_dir, f"{version}-natives")
    launch_args.extend([
        f"-Djava.library.path={natives_path}",
        f"-Djna.tmpdir={natives_path}",
        f"-Dorg.lwjgl.system.SharedLibraryExtractPath={natives_path}",
        f"-Dio.netty.native.workdir={natives_path}"
    ])
    
    # 添加启动器标识参数
    launch_args.extend([
        "-Dminecraft.launcher.brand=Bloret Launcher",
        "-Dminecraft.launcher.version=361"
    ])
    
    # 构建类路径 (classpath)
    classpath = []
    
    # 添加所有依赖库
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
            
            if should_include and "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = os.path.join(minecraft_dir, "libraries", lib["downloads"]["artifact"]["path"])
                if os.path.exists(lib_path):
                    classpath.append(lib_path)
    
    # 添加客户端 JAR
    classpath.append(client_jar_path)
    
    # 添加类路径参数
    launch_args.append("-cp")
    launch_args.append(";".join(classpath))  # Windows 使用分号分隔
    
    # 添加内存参数
    launch_args.extend([
        "-Xmn721m",
        "-Xmx4812m"
    ])
    
    # 添加模块导出参数
    launch_args.append("--add-exports")
    launch_args.append("cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED")
    
    # 添加自定义参数
    launch_args.append(f"-Doolloo.jlw.tmpdir={os.path.join(os.getcwd(), 'PCL')}")
    
    # 添加主类 JAR
    launch_args.append("-jar")
    launch_args.append(os.path.join(os.getcwd(), "JavaWrapper.jar"))
    
    # 添加主类
    launch_args.append("net.minecraft.client.main.Main")
    
    # 添加游戏参数
    game_dir = os.path.join(minecraft_dir, "versions", version)
    assets_dir = os.path.join(minecraft_dir, "assets")
    
    launch_args.extend([
        "--username", username,
        "--version", version,
        "--gameDir", game_dir,
        "--assetsDir", assets_dir,
        "--assetIndex", str(version_data.get("assets", version)),
        "--uuid", account_info.get("uuid", "") if account_info else "00000000000000000000000000000000",
        "--accessToken", account_info.get("accessToken", "") if account_info else "00000000000000000000000000000000",
        "--clientId", "${clientid}",
        "--xuid", "${auth_xuid}",
        "--userType", "msa",
        "--versionType", "Bloret Launcher",
        "--width", "854",
        "--height", "480"
    ])
    
    # 构建 PowerShell 命令
    formatted_args = []
    for arg in launch_args:
        # 对于包含空格、特殊字符或路径的参数，用双引号包围
        if isinstance(arg, str):
            # Java路径不需要引号
            if arg == java_path:
                formatted_args.append(arg)
            # 包含空格的参数需要引号
            elif " " in arg and not (arg.startswith('"') and arg.endswith('"')):
                # 转义引号内的引号
                escaped_arg = arg.replace('"', '""') if '"' in arg else arg
                formatted_args.append(f'"{escaped_arg}"')
            # 路径参数需要引号
            elif (arg.endswith(".jar") or os.sep in arg) and "=" not in arg:
                if not (arg.startswith('"') and arg.endswith('"')):
                    formatted_args.append(f'"{arg}"')
                else:
                    formatted_args.append(arg)
            # JVM参数通常不需要额外引号
            elif arg.startswith("-D") or arg.startswith("-X") or "=" in arg:
                formatted_args.append(arg)
            # 其他参数保持原样
            else:
                formatted_args.append(arg)
        else:
            formatted_args.append(str(arg))
    
    ps_command = " ".join(formatted_args)
    
    log(f"生成的启动命令: {ps_command}")
    return ps_command
