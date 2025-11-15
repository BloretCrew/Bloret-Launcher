import subprocess
import re
import sys
import threading
import time
import os
from modules.i18n import i18nText
from modules.log import log
import logging

easytier_core_process = None

def get_easytier_virtual_ip(cli_path="easytier-cli.exe"):
    """
    调用 easytier-cli node info，解析并返回虚拟 IP（如 10.126.126.1）
    """
    try:
        # 执行命令
        log(f"执行命令: {[cli_path, 'node', 'info']}", logging.DEBUG)
        result = subprocess.run(
            [cli_path, "node", "info"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout
        log(f"命令输出: {output}", logging.DEBUG)

        # 在输出中查找包含 "Virtual IP" 的行
        for line in output.splitlines():
            if "Virtual IP" in line:
                # 示例行: | Virtual IP     | 10.126.126.1/24                        |
                parts = line.split('|')
                if len(parts) >= 3:
                    ip_with_mask = parts[2].strip()
                    log(f"Virtual IP 字段内容: '{ip_with_mask}'", logging.DEBUG)
                    # 如果字段为空，直接返回 None
                    if not ip_with_mask:
                        log("Virtual IP 字段为空", logging.WARNING)
                        return None
                    # 使用正则提取 IP（兼容 IPv4 和可能的 IPv6）
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ip_with_mask)
                    if match:
                        return match.group(1)
                    else:
                        log(f"在 Virtual IP 字段中未找到有效的 IPv4 地址: {ip_with_mask}", logging.WARNING)
        return None

    except subprocess.CalledProcessError as e:
        log(f"❌ 执行 easytier-cli 失败: {e.stderr}", logging.ERROR)
        return None
    except FileNotFoundError:
        log(f"❌ 未找到 easytier-cli: {cli_path}", logging.ERROR)
        return None
    except Exception as e:
        log(f"❌ 发生错误: {e}", logging.ERROR)
        return None

def _run_easytier_core(name, key):
    global easytier_core_process
    easytier_core_path = os.path.join(os.getcwd(), "easytier", "easytier-core.exe")
    
    # 构建 easytier-core 的参数
    args = [
        "-d",
        "--network-name", name,
        "--network-secret", key,
        "-p", "tcp://public.easytier.cn:11010"
    ]
    
    # 将参数转换为字符串，以便传递给 PowerShell
    arg_string = " ".join([f"'{arg}'" if " " in arg else arg for arg in args])
    
    log(f"Easytier core 路径: {easytier_core_path}", logging.DEBUG)
    log(f"Easytier core 参数: {args}", logging.DEBUG)

    # 构建 PowerShell 命令，使用 Start-Process -Verb RunAs 申请管理员权限
    command = [
        "powershell.exe",
        "-Command",
        f"Start-Process -FilePath '{easytier_core_path}' -ArgumentList \"{arg_string}\" -Verb RunAs -WindowStyle Hidden"
    ]
    
    log(f"执行 PowerShell 命令: {command}", logging.DEBUG)

    try:
        # 使用 subprocess.Popen 启动 PowerShell 命令，不阻塞主线程
        # shell=True 是为了让 PowerShell 命令能够正确解析
        easytier_core_process = subprocess.Popen(command, shell=True, cwd=os.path.join(os.getcwd(), "easytier"))
        log(f"✅ Easytier core server started with admin privileges request. PID: {easytier_core_process.pid}")
        return True
    except Exception as e:
        log(f"❌ 启动 Easytier core 失败: {e}", logging.ERROR)
        return False

def StartEasytierServer(name, key):
    """
    新建一个单独的线程进行，不要占用主线程。
    1. 先申请提权运行命令 .\easytier-core.exe -d --network-name {name} --network-secret {key} -p tcp://public.easytier.cn:11010
    2. 3s 后 再新建一个线程，运行 get_easytier_virtual_ip() ，将该函数返回的内容返回
    """
    log(f"开始启动 Easytier 服务器，网络名称: {name}", logging.INFO)
    
    # 启动 Easytier core 服务器线程
    server_thread = threading.Thread(target=_run_easytier_core, args=(name, key))
    server_thread.daemon = True  # 设置为守护线程，主程序退出时自动终止
    server_thread.start()

    # 等待一段时间，让 Easytier core 有时间启动并申请权限
    log("等待 Easytier core 启动...", logging.INFO)
    time.sleep(5) # 增加等待时间，确保权限弹窗有足够时间显示和处理

    # 检查 easytier-core 是否成功启动
    # 由于 Start-Process -Verb RunAs 是异步的，我们无法直接获取其返回值
    # 只能通过检查 easytier-cli 是否能获取到 IP 来判断是否成功

    # 获取虚拟 IP，添加重试机制
    log("尝试获取虚拟 IP...", logging.INFO)
    virtual_ip = None
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries and not virtual_ip:
        if retry_count > 0:
            log(f"重试获取虚拟 IP (第 {retry_count + 1} 次尝试)...", logging.INFO)
            time.sleep(2)  # 重试前等待
            
        virtual_ip = get_easytier_virtual_ip(cli_path="easytier\\easytier-cli.exe")
        retry_count += 1
    
    if virtual_ip:
        log(f"✅ 成功获取虚拟 IP: {virtual_ip}", logging.INFO)
        return virtual_ip
    else:
        # 如果没有获取到虚拟 IP，则认为启动失败
        error_msg = i18nText("启动失败: Easytier Core 未能成功启动或获取虚拟IP失败，请检查是否授予管理员权限或安全软件是否阻止。")
        log(f"❌ {error_msg}", logging.ERROR)
        # 添加额外的诊断信息
        log("诊断信息: 可能的原因包括:", logging.INFO)
        log("1. 管理员权限未正确授予", logging.INFO)
        log("2. 防火墙或安全软件阻止了连接", logging.INFO)
        log("3. Easytier 服务端口被占用", logging.INFO)
        log("4. 虚拟网络接口创建失败", logging.INFO)
        return error_msg

def StopEasytierServer():
    log("正在停止 Easytier 服务器...", logging.INFO)
    # 使用 taskkill 强制终止 easytier-core.exe 进程
    try:
        result = subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"], check=True, capture_output=True)
        log("✅ Easytier core process terminated using taskkill.", logging.INFO)
        log(f"taskkill 输出: {result.stdout.decode()}", logging.DEBUG)
    except subprocess.CalledProcessError as e:
        log(f"❌ 终止 Easytier core 进程失败: {e.stderr.decode()}", logging.ERROR)
    except FileNotFoundError:
        log("❌ taskkill 命令未找到，无法终止 Easytier core 进程。", logging.ERROR)
    except Exception as e:
        log(f"❌ 终止 Easytier core 进程时发生错误: {e}", logging.ERROR)