"""
Easytier 本地直连辅助工具
用于在本地直连模式下添加对等节点
"""
import subprocess
import sys

def get_local_ip():
    """获取本机局域网 IP"""
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        
        # 查找 IPv4 地址
        for line in result.stdout.split('\n'):
            if 'IPv4' in line and '192.168' in line:
                # 提取 IP 地址
                parts = line.split(':')
                if len(parts) >= 2:
                    ip = parts[1].strip()
                    return ip
        
        return "未知"
    except Exception as e:
        print(f"获取 IP 地址失败: {e}")
        return "未知"

def add_peer(peer_ip):
    """添加对等节点"""
    peer_url = f"tcp://{peer_ip}:11010"
    print(f"\n正在添加对等节点: {peer_url}")
    
    try:
        result = subprocess.run(
            ["easytier\\easytier-cli.exe", "add-peer", peer_url],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )
        
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        print(f"添加对等节点失败: {e}")
        return False

def show_status():
    """显示当前状态"""
    print("\n" + "="*60)
    print("Easytier 状态")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["easytier\\easytier-cli.exe", "node", "info"],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )
        
        print(result.stdout)
    except Exception as e:
        print(f"获取状态失败: {e}")

if __name__ == "__main__":
    print("="*60)
    print("Easytier 本地直连辅助工具")
    print("="*60)
    
    # 获取本机 IP
    local_ip = get_local_ip()
    print(f"\n你的局域网 IP: {local_ip}")
    print("\n使用说明:")
    print(f"1. 将你的 IP ({local_ip}) 告诉对方")
    print("2. 让对方运行: easytier-cli add-peer tcp://你的IP:11010")
    print("3. 让对方将他们的 IP 告诉你")
    print("4. 运行下面的命令添加对方节点")
    
    print("\n" + "="*60)
    print("请选择操作:")
    print("1. 添加对等节点")
    print("2. 查看当前状态")
    print("3. 退出")
    print("="*60)
    
    choice = input("\n请输入选项 (1-3): ").strip()
    
    if choice == "1":
        peer_ip = input("请输入对方的 IP 地址: ").strip()
        if add_peer(peer_ip):
            print("\n✅ 成功添加对等节点")
        else:
            print("\n❌ 添加对等节点失败")
    elif choice == "2":
        show_status()
    elif choice == "3":
        print("退出")
        sys.exit(0)
    else:
        print("无效的选项")
