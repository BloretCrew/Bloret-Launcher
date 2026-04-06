"""
测试 Easytier 网络连接和 DNS 解析
"""
import subprocess
import sys

def test_dns(domain):
    """测试 DNS 解析"""
    print(f"\n测试 DNS 解析: {domain}")
    try:
        result = subprocess.run(
            ["nslookup", domain],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if "找不到" in result.stdout or "Non-existent" in result.stdout:
            print(f"  ❌ 无法解析 {domain}")
            return False
        else:
            print(f"  ✅ 成功解析 {domain}")
            print(result.stdout[:200])
            return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_ping(domain):
    """测试网络连接"""
    print(f"\n测试网络连通性: {domain}")
    try:
        result = subprocess.run(
            ["ping", "-n", "2", domain],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if "TTL" in result.stdout:
            print(f"  ✅ 可以 ping 通 {domain}")
            return True
        else:
            print(f"  ❌ 无法 ping 通 {domain}")
            print(result.stdout[:200])
            return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def check_easytier_cli():
    """检查 easytier-cli 是否可以运行"""
    print(f"\n检查 easytier-cli...")
    try:
        result = subprocess.run(
            ["easytier\\easytier-cli.exe", "node", "info"],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )
        print(f"  标准输出:\n{result.stdout[:500]}")
        if result.stderr:
            print(f"  错误输出:\n{result.stderr[:500]}")
        return True
    except Exception as e:
        print(f"  ❌ 运行失败: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Easytier 网络诊断工具")
    print("="*60)
    
    # 测试不同的公共服务器地址
    domains = [
        "public.easytier.cn",
        "public.easytier.top",
        "8.8.8.8"
    ]
    
    dns_results = {}
    for domain in domains:
        dns_results[domain] = test_dns(domain)
    
    # 测试连通性
    print("\n" + "="*60)
    print("网络连通性测试")
    print("="*60)
    for domain in domains:
        if dns_results.get(domain):
            test_ping(domain)
    
    # 检查 easytier-cli
    print("\n" + "="*60)
    print("Easytier CLI 检查")
    print("="*60)
    check_easytier_cli()
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)
    print("\n建议:")
    print("1. 如果所有公共服务器都无法解析，考虑:")
    print("   - 检查 DNS 设置")
    print("   - 使用本地直连模式（不使用公共服务器）")
    print("   - 搭建自己的 Easytier 服务器")
    print("\n2. 本地直连模式:")
    print("   - 两台电脑直接通过 IP 连接")
    print("   - 不需要公共服务器")
    print("   - 适合同一局域网")
