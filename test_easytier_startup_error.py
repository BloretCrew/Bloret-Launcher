"""
详细检查 easytier-core 的启动错误
"""
import subprocess
import os

print("="*60)
print("详细检查 easytier-core 的启动错误")
print("="*60)

# 先查看 easytier-core 的帮助信息
print("\n获取 easytier-core 帮助信息...")
try:
    result = subprocess.run(
        ["easytier\\easytier-core.exe", "--help"],
        capture_output=True,
        text=True,
        encoding='gbk',
        timeout=5
    )
    
    print("标准输出:")
    print(result.stdout[:1000])
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr[:500])
except Exception as e:
    print(f"获取帮助失败: {e}")

# 测试不同的参数组合
print("\n" + "="*60)
print("测试不同的启动参数")
print("="*60)

test_cases = [
    ["easytier\\easytier-core.exe", "-d", "--network-name", "Test", "--network-secret", "123"],
    ["easytier\\easytier-core.exe", "--network-name", "Test", "--network-secret", "123"],  # 不带 -d
]

for i, args in enumerate(test_cases, 1):
    print(f"\n测试 {i}: {args}")
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=3
        )
        
        print(f"  退出码: {result.returncode}")
        if result.stdout.strip():
            print(f"  输出: {result.stdout[:200]}")
        if result.stderr.strip():
            print(f"  错误: {result.stderr[:200]}")
            
        # 检查是否仍在运行
        if result.returncode == 0 and not result.stdout and not result.stderr:
            print(f"  ✅ 可能成功启动（无输出）")
    except subprocess.TimeoutExpired:
        print(f"  ✅ 进程正在运行（3秒超时）")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
