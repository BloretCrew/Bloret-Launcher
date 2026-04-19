# BBBS Live 服务端 — EasyTier 联机功能对接文档

> 给服务端开发者：本文档描述启动器侧已实现的所有 EasyTier API 调用和服务端需要新增的内容。
> 参考实现见 `temp/BBBS/server.js`（Node.js / Express）。

---

## 一、概述

EasyTier 是启动器内置的虚拟局域网工具。用户在 Live 空间内可以一键联机 Minecraft，无需手动配置网络参数。

**流程简述：**

```
房主点击"开始网络" → 服务端生成网络名/密钥 → 启动器本地启动 EasyTier
房主在游戏内"对局域网开放" → 启动器自动抓端口 → 上报虚拟IP:端口到服务端
成员进入同一 Live → 看到"连接房主网络" → 一键连接 → 启动器注入 SOCKS5 代理启动游戏
```

---

## 二、数据模型变更

在每个 Live 空间（内存中的 liveSpaces 对象）上新增 `easytier` 字段：

```js
easytier: {
    enabled: false,          // boolean  是否已开启
    hostUsername: "",         // string   房主用户名
    networkName: "",          // string   固定格式 "BLEASYTIER<用户名>"
    networkSecret: "",        // string   随机密钥，crypto.randomBytes(16).hex()
    hostVirtualIp: "",        // string   房主的 EasyTier 虚拟 IP（如 "10.144.144.1"）
    gamePort: null,           // number   Minecraft 局域网端口（房主在游戏内开放后上报）
    status: "",               // string   "starting" | "ready" | ""
    startedAt: null,          // number   开启时间戳 (Date.now())
}
```

空间未开启 EasyTier 时，该字段为空对象 `{}`。

---

## 三、新增 API 端点

### 3.1 房主开启 EasyTier

```
POST /api/live/easytier/start/:spaceId
```

**权限：** 仅房主（space.owner）可调用。

**逻辑：**

1. 校验调用者是房主
2. 如已开启，直接返回现有状态（`created: false`）
3. 如未开启，生成 `networkName = "BLEASYTIER" + username`，生成随机 `networkSecret`
4. 写入 `space.easytier`
5. 通过 SSE 广播 `easytier-state` 事件（见第五节）
6. 返回结果

**响应：**

```json
{
    "success": true,
    "created": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6...",
        "hostVirtualIp": "",
        "gamePort": null,
        "status": "starting",
        "startedAt": 1745000000000
    }
}
```

### 3.2 房主关闭 EasyTier

```
POST /api/live/easytier/stop/:spaceId
```

**权限：** 仅房主。

**逻辑：**

1. 校验调用者是房主
2. 清空 `space.easytier = {}`
3. SSE 广播 `easytier-state`（payload 为空对象）

**响应：**

```json
{
    "success": true,
    "easytier": {}
}
```

### 3.3 房主上报虚拟 IP 和端口

```
POST /api/live/easytier/publish/:spaceId
```

**权限：** 仅房主。

**请求体：**

```json
{
    "hostVirtualIp": "10.144.144.1",
    "gamePort": 49152
}
```

**逻辑：**

1. 校验调用者是房主
2. 校验 EasyTier 已开启（`enabled === true`）
3. 更新 `space.easytier.hostVirtualIp` 和 `space.easytier.gamePort`
4. 设置 `status = "ready"`
5. SSE 广播 `easytier-state`

**响应：**

```json
{
    "success": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6...",
        "hostVirtualIp": "10.144.144.1",
        "gamePort": 49152,
        "status": "ready",
        "startedAt": 1745000000000
    }
}
```

**注意：** 房主的启动器会以约 1 秒间隔轮询此接口（仅当 IP 和端口发生变化时才发请求）。当房主在游戏内"对局域网开放"后，启动器自动捕获端口并上报。

### 3.4 查询 EasyTier 状态

```
GET /api/live/easytier/info/:spaceId
```

**权限：** 已加入该空间的用户。

**响应：**

```json
{
    "success": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6...",
        "hostVirtualIp": "10.144.144.1",
        "gamePort": 49152,
        "status": "ready",
        "startedAt": 1745000000000
    }
}
```

未开启时返回 `"easytier": {}`。

---

## 四、启动器侧已实现的 API 调用（供参考）

以下是 `modules/bbbs_live.py` 中已有的函数，服务端需确保这些端点可用：

| 函数名 | 方法 | 路径 | 说明 |
|--------|------|------|------|
| `start_space_easytier` | POST | `/api/live/easytier/start/{spaceId}` | body 为 `{}` |
| `stop_space_easytier` | POST | `/api/live/easytier/stop/{spaceId}` | body 为 `{}` |
| `publish_space_easytier_endpoint` | POST | `/api/live/easytier/publish/{spaceId}` | body 见 3.3 |
| `get_space_easytier_info` | GET | `/api/live/easytier/info/{spaceId}` | — |

---

## 五、SSE 广播

当 EasyTier 状态发生变化时（开启、关闭、上报），服务端需向该空间所有 SSE 客户端广播：

```
event: easytier-state
data: {"enabled":true,"hostUsername":"Alice","networkName":"BLEASYTIERAlice",...}
```

启动器在 `_handle_live_event` 中监听 `event: easytier-state`，收到后更新 UI。

---

## 六、房主离开时的清理

当房主断开 SSE 连接（关闭启动器、离开空间等）：

1. 检查 `space.easytier.enabled`
2. 如为 `true`，清空 `space.easytier = {}`
3. 向该空间剩余成员广播 `easytier-state`（空对象）

这确保房主异常退出时，成员端能看到"房主已关闭网络"。

---

## 七、init 事件需要包含 easytier 字段

现有的 SSE init 事件（用户加入空间时发送）需要扩展：

```json
{
    "type": "init",
    "users": [...],
    "chatHistory": [...],
    "easytier": { ... },
    "isOwner": true
}
```

- `easytier`：当前空间的 EasyTier 状态（空对象或完整状态）
- `isOwner`：布尔值，`space.owner === 当前用户`，启动器用此判断显示房主/成员 UI

---

## 八、注意事项

1. **网络名固定为 `BLEASYTIER<用户名>`**，同一用户同一时间只允许一个 Live 开启 EasyTier
2. **密钥由服务端生成**，启动器不传密钥，避免篡改
3. **不落库**，EasyTier 状态仅存内存，随空间生命周期存在
4. **SSE broadcast 范围**：仅限同一 spaceId 的连接，不跨空间
5. **publish 接口会被轮询调用**，但仅在值变化时实际写入，服务端可做幂等处理
