#!/usr/bin/env python3
"""
此脚本用于以管理员权限设置 Bloret Launcher 的开机自启任务
"""
import os, sys, ctypes, json, logging
from modules.systems import setup_startup_with_self_starting

def show_help():
    """显示使用帮助信息"""
    print("""
用法: setup_startup.py [参数]

参数说明:
  --set-self-start    根据配置设置开机自启
  --self-starting     表示这是开机自启启动的程序
  --help              显示此帮助信息
    """)

def main():
    # 配置日志记录
    logging.basicConfig(
        filename='setup_startup.log',
        level=logging.INFO,  # 提高日志级别，记录更多信息
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 显示帮助信息
        if "--help" in sys.argv:
            show_help()
            return True
            
        # 解析命令行参数
        if "--set-self-start" in sys.argv:
            # 从配置文件读取设置
            config_path = 'config.json'
            if not os.path.exists(config_path):
                print("Error: config.json not found")
                logging.error("配置文件 config.json 未找到")
                return False
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 设置开机自启
            result = setup_startup_with_self_starting(config.get('self-starting', True))
            if result:
                print("Startup task set successfully")
                logging.info("开机自启任务设置成功")
                return True
            else:
                print("Failed to set startup task")
                logging.error("开机自启任务设置失败")
                return False
        elif "--self-starting" in sys.argv:
            # 如果是开机自启模式，直接启动主程序
            main_script = os.path.join(os.path.dirname(sys.argv[0]), "Bloret-Launcher.py")
            if os.path.exists(main_script):
                print("Starting application in self-starting mode")
                logging.info("正在以开机自启模式启动程序")
                ctypes.windll.shell32.ShellExecuteW(
                    None, "open", sys.executable, f'"{main_script}" --self-starting', None, 1)
                return True
            else:
                print("Error: Main script not found")
                logging.error("主程序脚本未找到")
                return False
        else:
            # 如果没有指定参数，则启动主程序
            print("No parameters specified, setting up self-start by default")
            logging.info("未指定参数，将以默认方式设置开机自启")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}" --set-self-start', None, 1)
            return False
            
    except Exception as e:
        logging.exception(f"设置开机自启时发生异常: {e}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    main()