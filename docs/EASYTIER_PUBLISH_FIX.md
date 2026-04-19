# EasyTier 发布端点修复文档

## 问题诊断

### 症状
1. 房主启动 EasyTier 后，虚拟 IP 被成功获取（例如 `192.168.3.168`）
2. 但服务器响应中 `hostVirtualIp` 为空字符串，`gamePort` 为 `null`
3. 日志中没有看到 `/api/live/easytier/publish` 请求
4. 客户端收到错误提示："房主已开启网络，但尚未在游戏中开放局域网"

### 根本原因

**发布循环（Publish Loop）的条件判断失败：**

```python
# 原始条件
if host_ip and game_port:
    # 发送 publish 请求
```

虽然虚拟 IP 被正确获取，但 **`game_port` 始终为 `None`**，导致：
- Publish 条件不满足
- 永远不会调用 `publish_space_easytier_endpoint()`
- 服务器端收不到房主的虚拟 IP 和游戏端口

### 游戏端口获取流程

Minecraft LAN 世界的端口需要通过监听游戏日志来获取：

```
Minecraft latest.log 中的日志行:
"[XX:XX:XX] [Server thread/INFO]: Local game hosted on port 25565"
                                                           ↓
LAN_PORT_PATTERNS 正则表达式匹配
                                                           ↓
set_live_game_port(25565) 被调用
                                                           ↓
_SESSION["game_port"] = 25565
                                                           ↓
Publish loop 检测到 game_port，发送 publish 请求
```

**问题：** `start_host_log_watch()` 函数从未被调用，所以日志监听从未启动！

## 修复方案

### 1. 添加自动日志监听启动函数

在 `modules/easytier.py` 中添加 `try_start_live_game_port_watch()` 函数：

```python
def try_start_live_game_port_watch():
    """尝试自动启动日志监听（仅在房主模式下）"""
    # 自动检测 Minecraft 目录
    # 扫描版本文件夹找到最新版本
    # 启动 start_host_log_watch(version, minecraft_dir)
```

### 2. 在房主启动时自动调用

在 `Bloret-Launcher.py` 的 `startLiveEasyTier()` 中：

```python
# 启动日志监听以捕获 Minecraft LAN 端口
if try_start_live_game_port_watch():
    log("已启动 Minecraft 日志监听，将自动捕获 LAN 端口")

self._start_live_easytier_publish_loop()
```

### 3. 添加手动设置端口的备选方案

添加 `setLiveGamePort()` Slot 用于手动设置：

```python
@Slot(int)
def setLiveGamePort(self, port):
    """手动设置游戏端口（自动检测失败时使用）"""
    set_live_game_port(port)
    self._emit_live_easytier_state()
```

### 4. 增强诊断日志

改进 `_start_live_easytier_publish_loop()` 的日志输出，便于诊断：

```
[EasyTier Publish Loop #1] space_id=abc123, mode=host, running=True
[EasyTier Publish] host_ip=192.168.3.168, game_port=None
[EasyTier Publish] 有虚拟 IP 但无游戏端口，等待 Minecraft LAN 世界启动
...
[EasyTier Publish] host_ip=192.168.3.168, game_port=25565
[EasyTier Publish] 上报端点: 192.168.3.168:25565
[EasyTier Publish] 上报成功
```

## 完整工作流程

```
1. 房主点击"开始网络"
   ↓
2. startLiveEasyTier()
   ├─ 调用 start_space_easytier() 获取网络凭证
   ├─ 调用 start_live_session() 启动本地 EasyTier 进程
   ├─ try_start_live_game_port_watch() ← [新增]
   │  └─ 启动 Minecraft 日志监听
   └─ _start_live_easytier_publish_loop()
      └─ 启动后台发布循环
   
3. 房主打开 Minecraft LAN 世界
   ↓
4. Minecraft 日志输出: "Local game hosted on port 25565"
   ↓
5. _watch_log_file() 检测到日志
   ├─ 正则表达式匹配
   ├─ 调用 set_live_game_port(25565)
   └─ _SESSION["game_port"] = 25565
   
6. Publish loop 检测到 game_port
   ↓
7. publish_space_easytier_endpoint(space_id, "192.168.3.168", 25565)
   ↓
8. 服务器返回成功响应，包含更新的 hostVirtualIp 和 gamePort
   ↓
9. 客户端可以连接了！
```

## 测试步骤

### 自动检测测试
1. 启动应用
2. 加入 Live 空间
3. 点击"开始网络"
4. 查看日志是否显示 `[Live Log Watch] 已启动日志监听`
5. 打开 Minecraft LAN 世界
6. 查看日志是否显示 `[EasyTier Publish] 上报端点: ...`

### 手动设置测试
如果自动检测失败，可以在控制台调用：
```python
backend.setLiveGamePort(25565)
```

## 调试技巧

### 查看完整的发布循环日志
搜索 `[EasyTier Publish]` 来追踪整个过程。

### 检查虚拟 IP 是否获取
查找 `虚拟 IP 获取成功` 或 `从日志提取虚拟 IP`

### 检查游戏端口是否检测
查找 `已捕获 Minecraft 局域网端口` 或 `set_live_game_port`

### 检查发布请求是否发送
查找 `[Live DEBUG]` 中的 `POST /api/live/easytier/publish` 请求

## 相关文件

- `Bloret-Launcher.py` - 主线程中的 `startLiveEasyTier()` 和 `setLiveGamePort()`
- `modules/easytier.py` - EasyTier 进程管理和日志监听
- `modules/bbbs_live.py` - 服务器 API 调用
- `qml/pages/Live.qml` - UI 显示

## 后续改进

1. **更智能的版本检测** - 根据启动历史或配置选择版本
2. **端口范围支持** - 支持自定义端口范围
3. **日志路径配置** - 允许用户指定 Minecraft 日志位置
4. **实时端口验证** - 定期验证端口是否仍然开放
