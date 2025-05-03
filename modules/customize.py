from qfluentwidgets import InfoBar, InfoBarPosition
import os,subprocess
from modules.log import log

def CustomizeRun(self,version):
    ''' 
    # Bloret Launcher 自定义启动
    启动版本 version  
    version 版本必须包含在 config 配置文件 中的 Customize 列表内。

    
    ***
    ###### Bloret Launcher 所有
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
                    title='❌ 启动失败',
                    content=f"路径 {program_path} 不存在或无效",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return
    InfoBar.error(
        title='❌ 启动失败',
        content=f"未找到与 {version} 匹配的自定义程序",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )

log("CUSTOMIZE.PY 的导入已完成。© Bloret Launcher")