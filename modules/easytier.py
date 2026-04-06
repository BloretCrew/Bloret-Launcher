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
        # 检查文件是否存在
        if not os.path.exists(cli_path):
            log(f"❌ easytier-cli 不存在: {cli_path}", logging.ERROR)
            return None

        # 执行命令
        log(f"执行命令: {[cli_path, 'node', 'info']}", logging.DEBUG)
        result = subprocess.run(
            [cli_path, "node", "info"],
            capture_output=True,
            text=True,
            encoding='gbk',  # Windows 中文系统使用 GBK 编码
            timeout=5  # 添加超时设置
        )
        output = result.stdout
        log(f"命令输出: {output}", logging.DEBUG)
        
        # 如果有错误输出，也记录下来
        if result.stderr:
            log(f"easytier-cli 错误输出: {result.stderr}", logging.WARNING)

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
        
        # 如果输出为空或没有 Virtual IP 行
        if not output.strip():
            log("easytier-cli 输出为空", logging.WARNING)
        else:
            log(f"完整输出:\n{output}", logging.DEBUG)
            
        return None

    except subprocess.TimeoutExpired:
        log("❌ easytier-cli 执行超时", logging.ERROR)
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

def _run_easytier_core(name, key, use_public_server=True, is_host=True, peer_ip=None):
    global easytier_core_process
    easytier_core_path = os.path.join(os.getcwd(), "easytier", "easytier-core.exe")

    # 检查文件是否存在
    if not os.path.exists(easytier_core_path):
        log(f"❌ Easytier core 不存在: {easytier_core_path}", logging.ERROR)
        return False

    # 如果密码为空，使用默认值
    if not key or key.strip() == "":
        key = "NoPassWord"  # 使用与 frp 相同的默认密码
        log("密码为空，使用默认值: NoPassWord", logging.WARNING)

    # 构建 easytier-core 的参数（不使用 -d，避免 daemon 模式）
    args = [
        "--network-name", name,
        "--network-secret", key,
    ]
    
    # 如果启用公共服务器，添加多个备用服务器地址
    if use_public_server:
        # 添加多个公共服务器，增加连接成功率
        public_servers = [
            "tcp://public.easytier.top:11010",
            "tcp://public1.easytier.top:11010",
            "tcp://public2.easytier.top:11010",
        ]
        for server in public_servers:
            args.extend(["-p", server])
        log(f"使用公共服务器模式: {', '.join(public_servers)}", logging.INFO)
    elif not is_host and peer_ip:
        # 加入者模式：添加房主为对等节点
        peer_url = f"tcp://{peer_ip}:11010"
        args.extend(["-p", peer_url])
        log(f"使用加入者模式，连接到房主节点: {peer_url}", logging.INFO)
    else:
        # 房主模式：不添加任何公共服务器，仅监听本地端口
        log("使用房主模式（不添加公共服务器）", logging.INFO)
        log("提示: 启动后需要将你的 IP 告诉加入者，让他们添加你为对等节点", logging.INFO)

    log(f"Easytier core 路径: {easytier_core_path}", logging.DEBUG)
    log(f"Easytier core 参数: {args}", logging.DEBUG)

    # 直接使用 Popen 启动进程，不使用 PowerShell 和 RunAs
    try:
        easytier_core_process = subprocess.Popen(
            [easytier_core_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(os.getcwd(), "easytier"),
            creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏窗口
        )
        log(f"✅ Easytier core server started. PID: {easytier_core_process.pid}")
        return True
    except Exception as e:
        log(f"❌ 启动 Easytier core 失败: {e}", logging.ERROR)
        return False

def StartEasytierServer(name, key, use_public_server=False, is_host=True, peer_ip=None):
    """
    启动 Easytier 服务器
    
    参数:
        name: 网络名称（房主的用户名或加入者的目标用户名）
        key: 网络密钥
        use_public_server: 是否使用公共服务器（默认 False）。如果为 True，则尝试连接多个公共服务器
        is_host: 是否为房主模式（默认 True）。False 为加入者模式
        peer_ip: 加入者模式下，房主的局域网 IP 地址（可选）
    """
    if is_host:
        mode = "房主模式"
        log(f"开始启动 Easytier 服务器 ({mode})，网络名称: {name}", logging.INFO)
    else:
        mode = "加入者模式"
        log(f"开始加入 Easytier 网络 ({mode})，目标用户: {name}，房主 IP: {peer_ip}", logging.INFO)

    # 启动 Easytier core 服务器线程
    server_thread = threading.Thread(target=_run_easytier_core, args=(name, key, use_public_server, is_host, peer_ip))
    server_thread.daemon = True  # 设置为守护线程，主程序退出时自动终止
    server_thread.start()

    # 等待一段时间，让 Easytier core 有时间启动
    log("等待 Easytier core 启动...", logging.INFO)
    time.sleep(3)  # 只需要等待进程启动

    # 检查 easytier-core 进程是否正在运行
    log("检查 easytier-core 进程是否存在...", logging.INFO)
    core_running = False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq easytier-core.exe"],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if "easytier-core.exe" in result.stdout:
            core_running = True
            log("✅ easytier-core 进程正在运行", logging.INFO)
        else:
            log("⚠️ easytier-core 进程未找到", logging.WARNING)
    except Exception as e:
        log(f"检查进程时出错: {e}", logging.WARNING)

    if not core_running:
        error_msg = i18nText("启动失败: Easytier Core 未能成功启动，请检查是否授予管理员权限或安全软件是否阻止。")
        log(f"❌ {error_msg}", logging.ERROR)
        return error_msg

    # 获取虚拟 IP（只尝试 3 次，快速失败）
    log("尝试获取虚拟 IP...", logging.INFO)
    virtual_ip = None
    retry_count = 0
    max_retries = 3
    retry_delay = 2

    while retry_count < max_retries and not virtual_ip:
        if retry_count > 0:
            log(f"重试获取虚拟 IP (第 {retry_count + 1} 次尝试)...", logging.INFO)
            time.sleep(retry_delay)

        virtual_ip = get_easytier_virtual_ip(cli_path="easytier\\easytier-cli.exe")
        retry_count += 1

    if virtual_ip:
        log(f"✅ 成功获取虚拟 IP: {virtual_ip}", logging.INFO)
        return virtual_ip
    else:
        # 没有获取到虚拟 IP
        if is_host:
            # 房主模式
            log("⚠️ 房主模式已启动，但未获取到虚拟 IP（这是正常的，等待加入者连接后会自动分配）", logging.WARNING)
            log("请按以下步骤操作:", logging.INFO)
            log("1. 运行 ipconfig 查看你的局域网 IP", logging.INFO)
            log("2. 将你的局域网 IP 告诉加入者", logging.INFO)
            log("3. 等待加入者连接后，虚拟 IP 将自动分配", logging.INFO)
            log("4. 运行 easytier-cli node info 查看虚拟 IP", logging.INFO)
            return i18nText("~房主模式已启动，请将你的局域网 IP 告诉加入者")
        else:
            # 加入者模式
            log("⚠️ 加入者模式已启动，但未获取到虚拟 IP", logging.WARNING)
            log("可能原因:", logging.INFO)
            log("1. 房主尚未启动或房主的 IP 不正确", logging.INFO)
            log("2. 防火墙阻止了连接", logging.INFO)
            log("3. 网络不稳定，请稍后重试", logging.INFO)
            return i18nText("~已尝试连接房主网络，请确认房主已启动 Easytier 并提供了正确的 IP")

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