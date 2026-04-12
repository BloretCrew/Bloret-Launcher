# Minecraft 跨平台启动器 EasyTier 联机集成文档 (免提权方案)

## 1. 架构概述

本方案采用 **“免提权 (No-Root/No-Admin) + 应用层代理”** 的架构。与传统的“虚拟网卡 (TUN)”模式相比，本方案在跨平台（Windows, macOS, Linux）环境下无需向用户申请管理员权限（无 UAC 弹窗 / 密码弹窗），可实现真正的“无感一键联机”。

### 1.1 核心原理
1. **网络层**：调用 EasyTier 的 `--no-tun` 模式，在不修改系统路由表、不创建虚拟网卡的前提下，让节点加入 P2P 虚拟网络。
2. **房主端**：游戏在本地随机端口（如 `55667`）开放局域网，EasyTier 将该服务暴露在虚拟网络中。
3. **玩家端**：EasyTier 在玩家本地开启 SOCKS5 代理服务（如 `1080` 端口）。启动器通过注入 JVM 参数，强制玩家的 Minecraft 网络流量走本地代理，从而打通连接。

---

## 2. 联机工作流设计

### 2.1 房主（建房）流程
1. 用户在启动器点击【创建房间】。
2. 启动器生成随机 `Network Name`、`Secret` 和唯一的 `虚拟 IP`（或由中心服务器分配）。
3. 启动器在后台免提权运行 `easytier-core`。
4. 用户启动游戏，并在游戏内点击“对局域网开放”。
5. 启动器监控 `latest.log`，捕获开放的端口号。
6. 启动器将组合信息 `[虚拟IP:端口]` 绑定至房间信息中。

### 2.2 玩家（加入）流程
1. 用户输入“房间码”或在联机大厅点击【加入房间】。
2. 启动器解析房间信息，获取 `Network Name`、`Secret` 和房主服务地址 `[虚拟IP:端口]`。
3. 启动器在后台免提权运行 `easytier-core`，并开启 SOCKS5 代理。
4. 启动器静默修改玩家 `.minecraft` 目录下的 `servers.dat`，将房主地址写入服务器列表。
5. 启动器携带 SOCKS5 代理参数 (`-DsocksProxyHost` 等) 启动游戏。
6. 玩家进入“多人游戏”，直接双击服务器进入。

---

## 3. 技术实现步骤

### 3.1 环境与核心程序准备
启动器需要根据用户的操作系统动态下载并配置 EasyTier 二进制文件。

*   **路径隔离**：建议将文件保存在启动器的数据目录下（如 `~/.launcher/easytier/`）。
*   **权限赋予（仅 Mac/Linux）**：下载完成后，必须赋予执行权限，否则无法启动。
    ```javascript
    // Node.js (Electron/Tauri) 示例
    const fs = require('fs');
    if (process.platform !== 'win32') {
        fs.chmodSync('/path/to/easytier-core', 0o755);
    }
    ```

### 3.2 启动进程与参数配置
**统一启动命令：**
无论在哪个平台，直接以普通进程身份拉起 `easytier-core`（无需 `sudo` 或 `runas`）。

```bash
easytier-core -n "ROOM_NAME" -s "ROOM_SECRET" --no-tun --proxy-port 1080 --ipv4 <分配的虚拟IP>
```
*参数说明：*
*   `--no-tun`：**核心参数**，关闭虚拟网卡，实现免提权。
*   `--proxy-port 1080`：在本地 `1080` 端口启动代理服务。
*   `--ipv4`：指定节点在当前 P2P 网络中的唯一标识 IP。

### 3.3 房主端：自动捕获游戏端口
为避免用户手动查看端口的麻烦，启动器需实现日志轮询。
1. 监听文件：`.minecraft/logs/latest.log`
2. 正则匹配规则：
   ```regex
   /Local game hosted on port (\d+)/
   ```
3. 捕获到端口后，停止轮询，并通过 WebSocket 或 API 将端口上报给启动器联机大厅。

### 3.4 玩家端：JVM 参数注入
在玩家启动游戏时，必须在游戏的启动参数中附加 SOCKS5 代理配置。

**必需加入的 JVM 参数：**
```text
-DsocksProxyHost=127.0.0.1
-DsocksProxyPort=1080
-DsocksNonProxyHosts=localhost|127.0.0.1  # 极其重要：防止游戏内置的本地皮肤验证/资源下载也走代理导致失败
-Djava.net.preferIPv4Stack=true           # 强制使用 IPv4，防止跨平台网络栈冲突
```

### 3.5 玩家体验极致优化：自动写 Server (可选但强烈推荐)
利用 NBT 解析库（如 Node.js 的 `prismarine-nbt` 或 C# 的 `fNbt`），在启动游戏前修改 `.minecraft/servers.dat` 文件。

```json
// servers.dat NBT 结构示例
{
  "servers": [
    {
      "name": "🚀 好友的联机房间",
      "ip": "房主虚拟IP:动态端口",
      "icon": "..." // 可选，填入 Base64 图片
    }
  ]
}
```
*效果：玩家打开游戏进入多人模式时，无需手动“添加服务器”，直接就能看到好友的房间。*

---

## 4. 进程与生命周期管理（重要）

跨平台开发中最容易出现“僵尸进程”，必须严格管理 `easytier-core` 的生命周期。

### 4.1 进程拉起与引用保存
```javascript
// Node.js 示例
const { spawn } = require('child_process');

let easytierProcess = spawn('/path/to/easytier-core', ['-n', 'ROOM123', '--no-tun', '--proxy-port', '1080'], {
    detached: false, // 绑定到父进程
    stdio: ['ignore', 'pipe', 'pipe']
});

// 监听状态
easytierProcess.stdout.on('data', (data) => {
    // 可解析 data 判断 P2P 连接状态
});
```

### 4.2 优雅退出机制
当用户**退出联机房间**或**关闭启动器**时，必须确保进程被杀死：
```javascript
function stopEasyTier() {
    if (easytierProcess) {
        easytierProcess.kill('SIGINT'); // 发送中断信号，让其安全退出
        easytierProcess = null;
    }
}

// 绑定系统退出事件
process.on('exit', stopEasyTier);
process.on('SIGINT', stopEasyTier); // Ctrl+C
process.on('SIGTERM', stopEasyTier); 
```

---

## 5. 避坑指南与常见问题 (FAQ)

### 1. 为什么加入房间后，进不去游戏，显示 "Connection Refused"？
*   **排查 1**：检查房主的 Windows/Mac 防火墙。房主在第一次开启游戏时，系统会弹出防火墙提示，**必须允许 Java (javaw.exe) 访问网络**，否则即使 P2P 打通，游戏也拒绝外部连接。
*   **排查 2**：检查玩家端的启动器是否正确注入了 SOCKS5 JVM 参数。

### 2. 为什么部分用户连接极度卡顿或延迟很高？
EasyTier 默认使用公共节点打洞。如果双方处于严格的 NAT 环境，可能会走公共节点中转。
*   **解决方案**：作为启动器开发者，建议在您的服务器上部署一个独立的 **EasyTier 公共节点 (Relay Server)**，并在启动命令中添加参数 `--peers tcp://您的服务器IP:11010`，以提供稳定、低延迟的官方中转。

### 3. Mac / Linux 下启动提示 `Permission denied`？
请回头检查 **3.1 节**，务必在下载文件后使用系统 API 或 `chmod` 命令为二进制文件附加可执行权限（`+x`）。

### 4. JVM 代理参数会不会影响用户玩其他服务器？
不会。因为我们在参数中加了 `-DsocksNonProxyHosts=localhost|127.0.0.1`。同时，游戏内连接非局域网（公网）服务器时，TCP 流量会通过代理发往目标，只要本地代理保持畅通，常规游戏不会受限；退出联机模式后，重启游戏（不带代理参数）即可恢复正常。