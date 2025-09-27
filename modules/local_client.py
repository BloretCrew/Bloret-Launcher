import requests
import toml
import subprocess
import os
from modules.log import log
import logging
from modules.i18n import i18nText

def OnlineClient(server_ip, port):
    """
    启动在线客户端服务
    
    Args:
        server_ip (str): 服务器IP地址
        port (int): 本地Minecraft服务器端口
        
    Returns:
        str: 连接地址
    """
    
    try:
        # 1. 请求 {server_ip}/api/minecraft-online-client?token=Bloret-PCFS-Token-Now-Rhedar-Detrital
        response = requests.get(f"{server_ip}api/minecraft-online-client?token=Bloret-PCFS-Token-Now-Rhedar-Detrital", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        remote_port = data.get('port')
        connection_address = "pcfs.eno.ink"
        
        if not remote_port or not connection_address:
            log(i18nText("获取远程端口或连接地址失败"), level=logging.ERROR)
            return i18nText("获取连接信息失败")
            
        log(f"获取到远程端口: {remote_port}")
        log(f"连接地址: {connection_address}:{remote_port}")
        
        # 2. 读取 frpc.toml 文件
        frpc_config_path = os.path.join(os.getcwd(), "frpc.toml")
        if not os.path.exists(frpc_config_path):
            log(i18nText("frpc.toml 文件不存在"), level=logging.ERROR)
            return i18nText("配置文件不存在")
            
        with open(frpc_config_path, 'r', encoding='utf-8') as f:
            frpc_config = toml.load(f)
        
        # 3. 编辑 frpc.toml 的 [proxies] 字段
        # 修改 name 为 str(port)
        frpc_config['proxies'][0]['name'] = str(port)
        # 修改 localPort 为输入函数的 port
        frpc_config['proxies'][0]['localPort'] = port
        # 修改 remotePort 为获取到的 port
        frpc_config['proxies'][0]['remotePort'] = remote_port
        
        # 4. 保存修改后的配置
        with open(frpc_config_path, 'w', encoding='utf-8') as f:
            toml.dump(frpc_config, f)
            
        log(f"已更新 frpc.toml 配置: name={port}, localPort={port}, remotePort={remote_port}")
        
        # 5. 运行 frpc -c frpc.toml
        frpc_path = os.path.join(os.getcwd(), "frpc.exe")
        if not os.path.exists(frpc_path):
            log(i18nText("frpc.exe 文件不存在"), level=logging.ERROR)
            return i18nText("frpc程序不存在")
            
        log(i18nText("正在启动 frpc 客户端..."))
        
        # 启动 frpc 进程
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.Popen(
            [frpc_path, "-c", "frpc.toml"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            creationflags=creation_flags  # 隐藏控制台窗口（仅Windows）
        )
        
        # 读取并记录输出
        try:
            stdout, stderr = process.communicate(timeout=5)
            if stdout:
                log(f"frpc stdout: {stdout}")
            if stderr:
                log(f"frpc stderr: {stderr}")
        except subprocess.TimeoutExpired:
            # 进程正常运行，超时是预期行为
            log(i18nText("frpc 客户端已在后台运行"))
            
        log(i18nText("在线客户端服务启动成功"))
        return f"{connection_address}:{remote_port}"
        
    except requests.RequestException as e:
        log(f"网络请求失败: {str(e)}", level=logging.ERROR)
        return i18nText("网络请求失败")
    except PermissionError as e:
        error_msg = i18nText("权限错误：系统安全软件（如Windows Defender）可能阻止了frpc.exe的执行。请将frpc.exe添加到杀毒软件的白名单或排除列表中。")
        log(f"{error_msg} 错误详情: {str(e)}", level=logging.ERROR)
        return error_msg
    except OSError as e:
        if e.winerror == 225:  # ERROR_ACCESS_DISABLED_BY_POLICY
            error_msg = i18nText("安全软件阻止：frpc.exe被安全软件识别为潜在威胁。请将该文件添加到杀毒软件的白名单或排除列表中。")
            log(f"{error_msg} 错误详情: {str(e)}", level=logging.ERROR)
            return error_msg
        else:
            log(f"操作系统错误: {str(e)}", level=logging.ERROR)
            return f"操作系统错误: {str(e)}"
    except Exception as e:
        log(f"启动在线客户端时出错: {str(e)}", level=logging.ERROR)
        return f"启动失败: {str(e)}"