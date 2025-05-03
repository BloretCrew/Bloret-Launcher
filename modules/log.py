import os,logging,shutil
from datetime import datetime
from qfluentwidgets import InfoBar, InfoBarPosition

# 创建日志文件夹
log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
# 设置日志配置
log_filename = os.path.join(log_folder, f'Bloret_Launcher_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
if not os.path.exists(log_filename):
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write('')  # 创建空日志文件
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def log(message, level=logging.INFO):
    '''
    发送日志消息，输出到控制台并记录到日志文件。
    ***
    ###### Bloret Launcher 所有
    '''
    print(message)
    logging.log(level, message)
    logging.getLogger().handlers[0].flush()  # 强制刷新日志

def clear_log_files(self, log_clear_button):
    ''' 
    # 清空日志文件
    删除 `{%appdata%}/Bloret-Launcher/log` 文件夹下的所有文件。

    ***

    输入 :

        - [x] self
        - [x] log_clear_button
    ***
    输出 : 无
    
    ***
    ###### Bloret Launcher 所有
    '''
    log_folder = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'log')
    file_num = len(os.listdir(log_folder))-1  # 减去一个正在使用的文件
    if os.path.exists(log_folder) and os.path.isdir(log_folder):
        for filename in os.listdir(log_folder):
            file_path = os.path.join(log_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                # InfoBar.success(
                #     title='🗑️ 清理成功',
                #     content=f"已清理 {file_path}",
                #     isClosable=True,
                #     position=InfoBarPosition.TOP,
                #     duration=5000,
                #     parent=self
                # )
            except Exception as e:
                log(f"Failed to delete {file_path}. Reason: {e}", logging.ERROR)
    InfoBar.success(
        title='🗑️ 清理成功',
        content=f"已清理 {file_num} 个文件",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )
    self.update_log_clear_button_text(log_clear_button)
    
    
log("LOG.PY 的导入已完成。© Bloret Launcher")