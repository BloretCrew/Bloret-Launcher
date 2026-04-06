"""
测试空密码时 easytier-core 的启动行为
"""
import subprocess
import time
import os

print("="*60)
print("测试空密码时 easytier-core 的启动行为")
print("="*60)

# 终止所有现有进程
print("\n终止所有现有的 easytier-core 进程...")
subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"], 
               capture_output=True)
time.sleep(1)

# 测试 1: 空密码
print("\n" + "="*60)
print("测试 1: 使用空密码启动")
print("="*60)

args_empty = [
    "easytier\\easytier-core.exe",
    "-d",
    "--network-name", "TestNetwork",
    "--network-secret", "",  # 空密码
]

print(f"参数: {args_empty}")

try:
    # 直接运行，捕获输出
    result = subprocess.run(
        args_empty,
        capture_output=True,
        text=True,
        encoding='gbk',
        timeout=2
    )
    
    print(f"退出码: {result.returncode}")
    print(f"标准输出:\n{result.stdout[:500]}")
    if result.stderr:
        print(f"\n错误输出:\n{result.stderr[:500]}")
except subprocess.TimeoutExpired:
    print("✅ 进程成功启动（2秒后仍在运行）")
except Exception as e:
    print(f"❌ 启动失败: {e}")

time.sleep(2)

# 检查进程
result = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq easytier-core.exe"],
    capture_output=True,
    text=True,
    encoding='gbk'
)

if "easytier-core.exe" in result.stdout:
    print("✅ 空密码: 进程正在运行")
else:
    print("❌ 空密码: 进程未找到")

# 终止所有进程
subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"], 
               capture_output=True)
time.sleep(1)

# 测试 2: 使用默认密码
print("\n" + "="*60)
print("测试 2: 使用默认密码 'NoPassWord' 启动")
print("="*60)

args_default = [
    "easytier\\easytier-core.exe",
    "-d",
    "--network-name", "TestNetwork",
    "--network-secret", "NoPassWord",
]

print(f"参数: {args_default}")

try:
    result = subprocess.run(
        args_default,
        capture_output=True,
        text=True,
        encoding='gbk',
        timeout=2
    )
    
    print(f"退出码: {result.returncode}")
    print(f"标准输出:\n{result.stdout[:500]}")
    if result.stderr:
        print(f"\n错误输出:\n{result.stderr[:500]}")
except subprocess.TimeoutExpired:
    print("✅ 进程成功启动（2秒后仍在运行）")
except Exception as e:
    print(f"❌ 启动失败: {e}")

time.sleep(2)

# 检查进程
result = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq easytier-core.exe"],
    capture_output=True,
    text=True,
    encoding='gbk'
)

if "easytier-core.exe" in result.stdout:
    print("✅ 默认密码: 进程正在运行")
else:
    print("❌ 默认密码: 进程未找到")

# 终止所有进程
print("\n清理进程...")
subprocess.run(["taskkill", "/F", "/IM", "easytier-core.exe"], 
               capture_output=True)

print("\n" + "="*60)
print("测试完成")
print("="*60)
