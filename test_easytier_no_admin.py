"""
测试无管理员权限启动 Easytier
"""
import subprocess
import time
import os

print("测试无管理员权限启动 Easytier...")

# 构建参数
args = [
    "-d",
    "--network-name", "TestNetwork",
    "--network-secret", "123",
]

arg_string = " ".join(args)
easytier_core_path = os.path.join(os.getcwd(), "easytier", "easytier-core.exe")

print(f"路径: {easytier_core_path}")
print(f"参数: {args}")

# 不使用 RunAs，直接启动
command = [
    "powershell.exe",
    "-Command",
    f"Start-Process -FilePath '{easytier_core_path}' -ArgumentList \"{arg_string}\" -WindowStyle Hidden"
]

print(f"\n执行命令...")
try:
    process = subprocess.Popen(command, shell=True)
    print(f"✅ 启动成功，PID: {process.pid}")
except Exception as e:
    print(f"❌ 启动失败: {e}")
    exit(1)

# 等待进程启动
print("\n等待 3 秒...")
time.sleep(3)

# 检查进程
print("\n检查进程...")
result = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq easytier-core.exe"],
    capture_output=True,
    text=True,
    encoding='gbk'
)

if "easytier-core.exe" in result.stdout:
    print("✅ easytier-core 进程正在运行")
    print(result.stdout[:500])
else:
    print("❌ easytier-core 进程未找到")
    print(result.stdout)

# 尝试获取虚拟 IP
print("\n尝试获取虚拟 IP...")
try:
    result = subprocess.run(
        ["easytier\\easytier-cli.exe", "node", "info"],
        capture_output=True,
        text=True,
        encoding='gbk',
        timeout=5
    )
    
    print("命令输出:")
    print(result.stdout[:500])
    
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr[:500])
    
    # 查找 Virtual IP
    for line in result.stdout.split('\n'):
        if 'Virtual IP' in line:
            print(f"\n找到 Virtual IP 行: {line}")
            break
    else:
        print("\n未找到 Virtual IP 行")
        
except Exception as e:
    print(f"获取虚拟 IP 失败: {e}")

print("\n测试完成")
print("\n提示: 按任意键终止 easytier-core 进程...")
input()

# 终止进程
subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"])
print("已终止 easytier-core 进程")
