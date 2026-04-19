# EasyTier 联机功能 — 完整实现指南

## 问题诊断

当前"开始网络"按钮无法正常工作的原因：**服务端（BBBS Live 后端）缺少 EasyTier 相关的 API 端点实现**。

启动器客户端已完整实现，但需要服务端配合。下面是完整的服务端实现要求。

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     启动器客户端 (Qt/QML)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Live.qml "开始网络"按钮                                        │
│       ↓                                                         │
│  Backend.startLiveEasyTier()                                   │
│       ↓                                                         │
├─────────────────────────────────────────────────────────────────┤
│            modules/bbbs_live.py (API 调用层)                   │
│                                                                 │
│  1. POST /api/live/easytier/start/{spaceId}                   │
│  2. POST /api/live/easytier/publish/{spaceId}  (轮询)          │
│  3. GET /api/live/easytier/info/{spaceId}                     │
│  4. SSE 监听 easytier-state 事件                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         BBBS Live 服务端（Node.js / Express / Go / Java）       │
│                       ⬅ 需要实现 ⬅                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
```

---

## 二、启动器期望的数据模型

### Live 空间对象扩展

每个 Live 空间对象需要新增 `easytier` 字段：

```javascript
{
    id: "space_123",
    name: "Alice的房间",
    owner: "Alice",
    users: [...],
    chatHistory: [...],
    
    // ⬇️ 新增以下字段
    easytier: {
        enabled: false,              // 是否已开启
        hostUsername: "Alice",        // 房主用户名
        networkName: "BLEASYTIERAlice",  // 网络名（固定格式）
        networkSecret: "a1b2c3...",  // 随机生成的密钥
        hostVirtualIp: "10.144.144.1",  // 房主虚拟 IP
        gamePort: 25565,             // Minecraft 局域网端口
        status: "ready",             // "starting" | "ready" | ""
        startedAt: 1745000000000     // 开启时间戳
    }
}
```

---

## 三、必需的 API 端点

### 3.1 开启 EasyTier 网络

**请求**
```http
POST /api/live/easytier/start/{spaceId}
Authorization: Bearer <token>
Content-Type: application/json

{}
```

**逻辑**
1. 校验用户是否是该空间的房主
2. 如已开启，返回现有状态（`created: false`）
3. 如未开启：
   - 生成 `networkName = "BLEASYTIER" + spaceOwnerUsername`
   - 生成随机 32 位十六进制 `networkSecret`
   - 初始化 `easytier` 字段
   - 设置 `status = "starting"`，`startedAt = Date.now()`
4. 通过 SSE 广播 `easytier-state` 事件给所有空间成员
5. 返回新生成的 `easytier` 对象

**响应（200 OK）**
```json
{
    "success": true,
    "created": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "hostVirtualIp": "",
        "gamePort": null,
        "status": "starting",
        "startedAt": 1745000000000
    }
}
```

**错误情况**
- 401 未授权
- 403 非房主
- 404 空间不存在
- 500 服务器错误

---

### 3.2 关闭 EasyTier 网络

**请求**
```http
POST /api/live/easytier/stop/{spaceId}
Authorization: Bearer <token>
Content-Type: application/json

{}
```

**逻辑**
1. 校验用户是否是房主
2. 清空该空间的 `easytier = {}`
3. SSE 广播 `easytier-state`（空对象）

**响应（200 OK）**
```json
{
    "success": true,
    "easytier": {}
}
```

---

### 3.3 发布虚拟 IP 和游戏端口

**请求**
```http
POST /api/live/easytier/publish/{spaceId}
Authorization: Bearer <token>
Content-Type: application/json

{
    "hostVirtualIp": "10.144.144.1",
    "gamePort": 25565
}
```

**频率**
- 启动器约每 1 秒调用一次（仅当 IP 或端口变化时发送）
- 这是**轮询**接口，可以幂等处理

**逻辑**
1. 校验用户是房主
2. 校验 `easytier.enabled === true`
3. 更新 `easytier.hostVirtualIp` 和 `easytier.gamePort`
4. 更新 `easytier.status = "ready"`
5. SSE 广播 `easytier-state`

**响应（200 OK）**
```json
{
    "success": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "hostVirtualIp": "10.144.144.1",
        "gamePort": 25565,
        "status": "ready",
        "startedAt": 1745000000000
    }
}
```

---

### 3.4 查询 EasyTier 状态

**请求**
```http
GET /api/live/easytier/info/{spaceId}
Authorization: Bearer <token>
```

**逻辑**
1. 校验用户已加入该空间
2. 返回该空间的 `easytier` 对象（未开启时为空对象）

**响应（200 OK）**
```json
{
    "success": true,
    "easytier": {
        "enabled": true,
        "hostUsername": "Alice",
        "networkName": "BLEASYTIERAlice",
        "networkSecret": "a1b2c3d4e5f6...",
        "hostVirtualIp": "10.144.144.1",
        "gamePort": 25565,
        "status": "ready",
        "startedAt": 1745000000000
    }
}
```

---

## 四、SSE (Server-Sent Events) 实现

### 4.1 广播事件格式

当 EasyTier 状态变化时，向该空间所有 SSE 连接广播：

```
event: easytier-state
data: {"enabled":true,"hostUsername":"Alice","networkName":"BLEASYTIERAlice","networkSecret":"...","hostVirtualIp":"10.144.144.1","gamePort":25565,"status":"ready","startedAt":1745000000000}
```

### 4.2 触发时机

以下情况需要广播：
- 房主调用 `/api/live/easytier/start/{spaceId}`
- 房主调用 `/api/live/easytier/stop/{spaceId}`
- 房主调用 `/api/live/easytier/publish/{spaceId}`（状态更新时）
- 房主断开 SSE 连接时，自动清空状态并广播空对象

### 4.3 启动器处理

启动器在 `Bloret-Launcher.py` 的 `_handle_live_event` 方法中监听此事件，收到后：
1. 更新 `_current_live_easytier_state`
2. 发出 `liveEasyTierStateChanged` 信号
3. UI 自动刷新（加载环消失，按钮状态更新等）

---

## 五、初始化事件扩展

用户首次加入空间时，SSE init 事件需要包含 `easytier` 和 `isOwner`：

```
event: init
data: {
  "type": "init",
  "users": [...],
  "chatHistory": [...],
  "easytier": {...},
  "isOwner": true
}
```

---

## 六、房主离开时的清理逻辑

### 连接关闭处理

当房主的 SSE 连接关闭（主动离开或意外断开）：

1. 检查该用户是否是某个空间的房主
2. 如是，检查 `space.easytier.enabled`
3. 如为 `true`，执行清理：
   - 清空 `space.easytier = {}`
   - SSE 广播 `easytier-state` 事件（空对象）
   - 日志记录房主异常退出事件

### 实现示例（伪代码）

```javascript
// 当 SSE 连接关闭时
connection.on('close', () => {
    const userId = connection.userId;
    
    // 查找该用户拥有的所有空间
    liveSpaces.forEach((space) => {
        if (space.owner === userId && space.easytier?.enabled) {
            // 清空 EasyTier 状态
            space.easytier = {};
            
            // 向该空间剩余成员广播
            broadcastToSpace(space.id, {
                event: 'easytier-state',
                data: {}
            });
            
            logger.info(`房主 ${userId} 离开，已清空空间 ${space.id} 的 EasyTier`);
        }
    });
});
```

---

## 七、错误处理

### 启动器会处理的错误响应

启动器会监听以下错误情况：

| 错误码 | 含义 | 启动器反应 |
|--------|------|----------|
| 401 | 未授权 | 重新登录 |
| 403 | 无权限 | 提示"仅房主可操作" |
| 404 | 空间/资源不存在 | 刷新空间列表 |
| 500 | 服务器错误 | 弹出错误提示 |
| 网络超时 | 连接失败 | 重试 3 次后提示离线 |

---

## 八、安全注意事项

1. **权限校验**
   - 开启/关闭：仅房主
   - 发布端口：仅房主
   - 查询状态：已加入空间的成员

2. **输入验证**
   - `hostVirtualIp`：应为有效的 IPv4 地址格式
   - `gamePort`：应为 1-65535 范围内的整数
   - 防止 TOCTOU（检查时间-使用时间）问题

3. **资源限制**
   - 每用户同一时间只允许一个 Live 开启 EasyTier
   - 防止密钥泄露

---

## 九、参考实现

### Node.js / Express 示例

```javascript
const express = require('express');
const router = express.Router();

// 中间件：验证用户和房主身份
const requireAuth = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ success: false, error: '未授权' });
    // 验证 token 并获取 userId
    req.userId = decodeToken(token);
    next();
};

const requireOwner = (req, res, next) => {
    const space = liveSpaces.get(req.params.spaceId);
    if (!space) return res.status(404).json({ success: false, error: '空间不存在' });
    if (space.owner !== req.userId) {
        return res.status(403).json({ success: false, error: '仅房主可操作' });
    }
    next();
};

// POST /api/live/easytier/start/:spaceId
router.post('/easytier/start/:spaceId', requireAuth, requireOwner, (req, res) => {
    const space = liveSpaces.get(req.params.spaceId);
    const created = !space.easytier?.enabled;
    
    if (created) {
        const crypto = require('crypto');
        space.easytier = {
            enabled: true,
            hostUsername: space.owner,
            networkName: `BLEASYTIER${space.owner}`,
            networkSecret: crypto.randomBytes(16).toString('hex'),
            hostVirtualIp: '',
            gamePort: null,
            status: 'starting',
            startedAt: Date.now()
        };
        
        // 广播事件
        broadcastToSpace(req.params.spaceId, {
            event: 'easytier-state',
            data: JSON.stringify(space.easytier)
        });
    }
    
    res.json({
        success: true,
        created,
        easytier: space.easytier
    });
});

// POST /api/live/easytier/publish/:spaceId
router.post('/easytier/publish/:spaceId', requireAuth, requireOwner, (req, res) => {
    const space = liveSpaces.get(req.params.spaceId);
    
    if (!space.easytier?.enabled) {
        return res.status(400).json({ success: false, error: 'EasyTier 未启用' });
    }
    
    const { hostVirtualIp, gamePort } = req.body;
    space.easytier.hostVirtualIp = hostVirtualIp;
    space.easytier.gamePort = gamePort;
    space.easytier.status = 'ready';
    
    // 广播事件
    broadcastToSpace(req.params.spaceId, {
        event: 'easytier-state',
        data: JSON.stringify(space.easytier)
    });
    
    res.json({ success: true, easytier: space.easytier });
});

// GET /api/live/easytier/info/:spaceId
router.get('/easytier/info/:spaceId', requireAuth, (req, res) => {
    const space = liveSpaces.get(req.params.spaceId);
    if (!space) return res.status(404).json({ success: false, error: '空间不存在' });
    
    // 验证用户在空间中
    if (!space.users.includes(req.userId)) {
        return res.status(403).json({ success: false, error: '未加入此空间' });
    }
    
    res.json({
        success: true,
        easytier: space.easytier || {}
    });
});

module.exports = router;
```

---

## 十、测试清单

### 功能测试

- [ ] 房主点击"开始网络"，成功调用 `/api/live/easytier/start`
- [ ] 服务端返回正确的 `networkName` 和 `networkSecret`
- [ ] 所有空间成员收到 SSE `easytier-state` 事件
- [ ] UI 加载环显示，按钮状态更新
- [ ] 房主发布虚拟 IP/端口，成员能查询到最新状态
- [ ] 房主点击"关闭网络"，成功调用 `/api/live/easytier/stop`
- [ ] 状态清空后，成员端显示"未启用"

### 错误处理测试

- [ ] 非房主尝试开启，返回 403 并提示
- [ ] 网络超时时，启动器正确重试和超时处理
- [ ] 房主异常退出，成员端自动清空状态

---

## 十一、问题排查

### 加载环一直在转，按钮无反应

**可能原因：**
1. 服务端 `/api/live/easytier/start` 返回失败
2. 网络请求超时
3. SSE 事件未被发送

**排查步骤：**
1. 打开启动器控制台，查看错误日志
2. 用浏览器开发者工具或 curl 测试 API
3. 检查服务端日志是否收到请求

**示例 curl 测试：**
```bash
curl -X POST http://localhost:8080/api/live/easytier/start/space_123 \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 按钮变灰，提示"房主已启动 EasyTier，正在等待游戏内开放局域网"

**正常状态**，这表示：
1. ✅ 服务端已返回成功
2. ✅ 本地 EasyTier 进程已启动
3. ⏳ 等待房主在游戏内点击"对局域网开放"

**后续流程：**
- 房主打开 Minecraft，创建世界后点击"对局域网开放"
- 启动器自动捕获端口号
- 启动器上报虚拟 IP:端口
- 按钮恢复可用，其他成员可以连接

---

## 十二、文档更新日期

- **创建日期**：2026-04-18
- **最后更新**：2026-04-18
- **版本**：1.0
