from qfluentwidgets import InfoBar, InfoBarPosition
import os,subprocess,json,sys,logging
from modules.log import log
from modules.i18n import i18nText
from modules.safe import handle_exception

def CustomizeRun(self,version):
    ''' 
    # Bloret Launcher 自定义启动
    启动版本 version  
    version 版本必须包含在 config 配置文件 中的 Customize 列表内。

    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    # 查找 config.json 中 Customize 的 showname 是否匹配 version
    for item in self.config.get("Customize", []):
        if item.get("showname") == version:
            program_path = item.get("path")
            if program_path and os.path.exists(program_path):
                InfoBar.success(
                    title=f'🔄️ 正在启动 {version}',
                    content=f"...",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                subprocess.Popen(program_path, shell=True)
                return
            else:
                InfoBar.error(
                    title=i18nText('❌ 启动失败'),
                    content=f"路径 {program_path} 不存在或无效",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return
    InfoBar.error(
        title=i18nText('❌ 启动失败'),
        content=f"未找到与 {version} 匹配的自定义程序",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )
def find_Customize(self,version):
    '''
    ## 查找 config.json 中 Customize 的 showname 是否匹配 version

    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    with open('config.json', 'r', encoding='utf-8') as file:
        config_data = json.load(file)
    if "Customize" not in config_data:
        config_data["Customize"] = []
    for item in self.config.get("Customize", []):
        if item.get("showname") == version:
            program_path = item.get("path")
            if program_path and os.path.exists(program_path):
                log(f"找到：{item}")
                return True,item
            else:
                log(f"找到：{item}，但路径 {program_path} 不存在或无效")
                return False,item
    log(f"无法找到：{version}")
    return False,version


def CustomizeAdd(self):
    '''
    ### 添加自定义程序
    弹出文件选择框，选择文件后将文件信息存入config中的Customize列表
    1. 文件名称(不带后缀名) -> showname
    2. 文件路径 -> path
    
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    try:
        from PyQt5.QtWidgets import QFileDialog
        
        # 弹出文件选择框选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            i18nText("选择自定义程序文件"),
            "",
            i18nText("可执行文件 (*.exe);;所有文件 (*)")
        )
        
        # 如果用户取消选择或未选择文件
        if not file_path:
            return
            
        # 获取不带后缀的文件名
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 读取现有配置
        try:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)
        except FileNotFoundError:
            config_data = {}
            
        # 确保Customize字段存在
        if "Customize" not in config_data:
            config_data["Customize"] = []
            
        # 检查是否已存在相同的路径
        for item in config_data["Customize"]:
            if item.get("path") == file_path:
                InfoBar.warning(
                    title=i18nText('⚠️ 提示'),
                    content=f"文件 {file_name} 已存在于自定义程序列表中",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return
                
        # 添加新的自定义项
        new_custom = {
            "showname": file_name,
            "path": file_path
        }
        
        config_data["Customize"].append(new_custom)
        
        # 保存到配置文件
        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(config_data, file, ensure_ascii=False, indent=4)
            
        # 更新当前配置
        self.config = config_data
        
        # 显示成功信息
        InfoBar.success(
            title=i18nText('✅ 成功'),
            content=f"已成功添加自定义程序: {file_name}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        
        log(f"成功添加自定义程序: {file_name} ({file_path})")
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        InfoBar.error(
            title=i18nText('❌ 错误'),
            content=f"添加自定义程序时发生错误: {str(e)}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        log(f"添加自定义程序时发生错误: {str(e)}", logging.ERROR)

def CustomizeAppAdd(file_path, file_name):
    '''
    ### 添加自定义程序（通过指定路径）
    与CustomizeAdd功能一致，但不弹出文件选择框和InfoBar
    直接将指定路径的文件信息存入config中的Customize列表
    1. 文件名称(不带后缀名) -> showname
    2. 文件路径 -> path
    
    参数:
        file_path (str): 要添加的自定义程序的完整文件路径
        
    返回:
        bool: 添加成功返回True，失败或已存在返回False
        
    异常处理:
        任何异常都会被捕获并记录到日志中，不会导致程序崩溃
        
    ***
    ###### Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.
    '''
    try:
        log(f"开始添加自定义程序: {file_path}， {file_name}")
        
        # 检查文件路径是否为空
        if not file_path:
            log("文件路径为空，无法添加自定义程序")
            return False
            
        # 获取不带后缀的文件名
        # file_name = os.path.splitext(os.path.basename(file_path))[0]
        # log(f"提取文件名: {file_name}")
        
        # 读取现有配置
        log("正在读取现有配置文件 config.json")
        try:
            with open('config.json', 'r', encoding='utf-8') as file:
                config_data = json.load(file)
            log("成功读取配置文件")
        except FileNotFoundError:
            config_data = {}
            log("配置文件不存在，将创建新的配置")
        except json.JSONDecodeError as e:
            log(f"配置文件格式错误: {e}", logging.ERROR)
            return False
            
        # 确保Customize字段存在
        if "Customize" not in config_data:
            config_data["Customize"] = []
            log("初始化 Customize 字段")
        else:
            log(f"当前已有 {len(config_data['Customize'])} 个自定义程序")
            
        # 检查是否已存在相同的路径
        log("检查是否已存在相同的程序路径")
        for item in config_data["Customize"]:
            if item.get("path") == file_path:
                log(f"文件 {file_name} 已存在于自定义程序列表中，路径: {file_path}")
                return False
                
        # 添加新的自定义项
        new_custom = {
            "showname": file_name,           # 显示名称为不带后缀的文件名
            "path": file_path                # 完整的文件路径
        }
        
        config_data["Customize"].append(new_custom)
        log(f"已将新程序添加到内存中的配置列表，当前共有 {len(config_data['Customize'])} 个程序")
        
        # 保存到配置文件
        log("正在将配置保存到 config.json")
        try:
            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=4)
            log("配置文件保存成功")
        except Exception as e:
            log(f"保存配置文件时发生错误: {e}", logging.ERROR)
            return False
            
        # # 更新当前配置
        # self.config = config_data
        
        log(f"成功添加自定义程序: {file_name} ({file_path})")
        return True
        
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handle_exception(exc_type, exc_value, exc_traceback)
        log(f"添加自定义程序时发生错误: {str(e)}", logging.ERROR)
        return False
