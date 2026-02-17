import requests
import modules.globals as BLglobals
from modules.log import log

# Fetch server IP from gitcode
try:
    log("正在获取服务器 IP...")
    res = requests.get("https://raw.gitcode.com/Bloret/Bloret-Launcher/raw/Windows/IP.json", timeout=5)
    if res.status_code == 200:
        data = res.json()
        if "PCFS" in data:
            new_ip = data["PCFS"]
            # Construct the full URL with port 2 as per original config
            BLglobals.server_ip = f"http://{new_ip}"
            log(f"已更新服务器 IP: {BLglobals.server_ip}")
        else:
            log("IP.json 中未找到 PCFS 字段")
    else:
        log(f"获取服务器 IP 失败，状态码: {res.status_code}")
except Exception as e:
    log(f"获取服务器 IP 时发生异常: {e}")
