import os,logging
from datetime import datetime

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
    print(message)
    logging.log(level, message)
    logging.getLogger().handlers[0].flush()  # 强制刷新日志
    
log("LOG.PY WAS WELL DONE.")