"""
测试 Easytier 公共服务器连接
"""
import subprocess
import sys

def test_server(server_url):
    """测试单个服务器连接"""
    print(f"\n测试服务器: {server_url}")
    try:
        # 尝试解析域名
        result = subprocess.run(
            ["nslookup", server_url.split("://")[1].split(":")[0]],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )
        
        if "找不到" in result.stdout or "Non-existent" in result.stdout:
            print(f"  ❌ DNS 解析失败")
            return False
        
        print(f"  ✅ DNS 解析成功")
        
        # 尝试 ping
        result = subprocess.run(
            ["ping", "-n", "2", "-w", "1000", server_url.split("://")[1].split(":")[0]],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )
        
        if "TTL" in result.stdout:
            print(f"  ✅ 可以 ping 通")
            return True
        else:
            print(f"  ⚠️  无法 ping 通（可能被防火墙阻止）")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ 测试超时")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Easytier 公共服务器连接测试")
    print("="*60)
    
    servers = [
        "tcp://public.easytier.cn:11010",
        "tcp://public.easytier.top:11010",
        "tcp://public1.easytier.top:11010",
        "tcp://public2.easytier.top:11010",
    ]
    
    results = {}
    for server in servers:
        results[server] = test_server(server)
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for server, success in results.items():
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"{status} - {server}")
    
    # 统计可用服务器数量
    available = sum(1 for v in results.values() if v)
    print(f"\n可用服务器数量: {available}/{len(results)}")
    
    if available == 0:
        print("\n⚠️  警告: 所有公共服务器都不可达")
        print("\n建议:")
        print("1. 检查你的网络连接")
        print("2. 检查防火墙设置")
        print("3. 使用本地直连模式（同一局域网）")
        print("4. 搭建自己的 Easytier 服务器")
    else:
        print(f"\n✅ 找到 {available} 个可用服务器")
