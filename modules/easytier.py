import subprocess
import re
import sys
import threading
import time
import os
from modules.i18n import i18nText

easytier_core_process = None

def get_easytier_virtual_ip(cli_path="easytier-cli.exe"):
    """
    调用 easytier-cli node info，解析并返回虚拟 IP（如 10.126.126.1）
    """
    try:
        # 执行命令
        result = subprocess.run(
            [cli_path, "node", "info"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout

        # 在输出中查找包含 "Virtual IP" 的行
        for line in output.splitlines():
            if "Virtual IP" in line:
                # 示例行: | Virtual IP     | 10.126.126.1/24                        |
                parts = line.split('|')
                if len(parts) >= 3:
                    ip_with_mask = parts[2].strip()
                    # 使用正则提取 IP（兼容 IPv4 和可能的 IPv6）
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ip_with_mask)
                    if match:
                        return match.group(1)
        return None

    except subprocess.CalledProcessError as e:
        print(f"❌ 执行 easytier-cli 失败: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"❌ 未找到 easytier-cli: {cli_path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 发生错误: {e}", file=sys.stderr)
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

    # 构建 PowerShell 命令，使用 Start-Process -Verb RunAs 申请管理员权限
    command = [
        "powershell.exe",
        "-Command",
        f"Start-Process -FilePath '{easytier_core_path}' -ArgumentList \"{arg_string}\" -Verb RunAs -WindowStyle Hidden"
    ]

    try:
        # 使用 subprocess.Popen 启动 PowerShell 命令，不阻塞主线程
        # shell=True 是为了让 PowerShell 命令能够正确解析
        easytier_core_process = subprocess.Popen(command, shell=True, cwd=os.path.join(os.getcwd(), "easytier"))
        print(f"✅ Easytier core server started with admin privileges request.")
        return True
    except Exception as e:
        print(f"❌ 启动 Easytier core 失败: {e}", file=sys.stderr)
        return False

def StartEasytierServer(name, key):
    """
    新建一个单独的线程进行，不要占用主线程。
    1. 先申请提权运行命令 .\easytier-core.exe -d --network-name {name} --network-secret {key} -p tcp://public.easytier.cn:11010
    2. 3s 后 再新建一个线程，运行 get_easytier_virtual_ip() ，将该函数返回的内容返回
    """
    # 启动 Easytier core 服务器线程
    server_thread = threading.Thread(target=_run_easytier_core, args=(name, key))
    server_thread.daemon = True  # 设置为守护线程，主程序退出时自动终止
    server_thread.start()

    # 等待一段时间，让 Easytier core 有时间启动并申请权限
    time.sleep(5) # 增加等待时间，确保权限弹窗有足够时间显示和处理

    # 检查 easytier-core 是否成功启动
    # 由于 Start-Process -Verb RunAs 是异步的，我们无法直接获取其返回值
    # 只能通过检查 easytier-cli 是否能获取到 IP 来判断是否成功

    # 获取虚拟 IP
    virtual_ip = get_easytier_virtual_ip(cli_path="easytier\\easytier-cli.exe")
    
    if virtual_ip:
        return virtual_ip
    else:
        # 如果没有获取到虚拟 IP，则认为启动失败
        return i18nText("启动失败: Easytier Core 未能成功启动或获取虚拟IP失败，请检查是否授予管理员权限或安全软件是否阻止。")

def StopEasytierServer():
    # 使用 taskkill 强制终止 easytier-core.exe 进程
    try:
        subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"], check=True, capture_output=True)
        print("✅ Easytier core process terminated using taskkill.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 终止 Easytier core 进程失败: {e.stderr.decode()}", file=sys.stderr)
    except FileNotFoundError:
        print("❌ taskkill 命令未找到，无法终止 Easytier core 进程。", file=sys.stderr)
    except Exception as e:
        print(f"❌ 终止 Easytier core 进程时发生错误: {e}", file=sys.stderr)
