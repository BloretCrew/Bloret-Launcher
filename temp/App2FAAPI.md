**Bloret PassPort 移动端 App 开发文档**。

这份文档详细说明了 App 端如何对接“一键验证”功能。由于目前的后端实现采用的是 **轮询 (Polling)** 机制（而非 WebSocket 或 FCM 推送），App 端需要定期向服务器查询是否有待处理的请求。

---

# Bloret PassPort - 移动端 2FA 验证接口文档

## 1. 流程概述

1.  **网页端**：用户在网页输入密码后，选择“使用手机 App 验证”。
2.  **服务端**：生成一个验证请求，状态为 `pending`。
3.  **App 端**：
    *   App 在后台或前台定期轮询（或用户手动刷新）接口。
    *   发现 `pending` 状态的请求。
    *   弹出提示框显示请求详情（IP、设备、时间）。
    *   用户点击“允许”或“拒绝”。
    *   App 调用接口将结果提交给服务端。
4.  **网页端**：轮询检测到状态变为 `approved`，自动跳转进入系统。

## 2. 前置条件

App 在调用以下接口前，必须满足：
1.  **用户已在 App 登录**：App 本地持有用户的 `username`。
2.  **App 已注册**：App 拥有合法的 `app_id`（例如：`BloretApp`，需在 `oauthapp.json` 中存在）。
3.  **持有 App Token**：App 本地持有该用户针对此 App 的专用 Token（对应后端 `user.apptoken[app_id]` 的值）。

---

## 3. API 接口说明

### 3.1 获取待处理的验证请求

App 需要定期调用此接口来检查是否有网页端发起的登录请求。建议轮询间隔：**5 - 10 秒**，或者在 App 首页提供下拉刷新功能。

- **URL**: `https://passport.bloret.net/api/2fa/app/pending`
- **Method**: `GET`
- **Content-Type**: `application/json`

#### 请求参数 (Query Parameters)

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `username` | String | 是 | 当前登录的用户名 |
| `app_id` | String | 是 | App 的应用 ID (如 `BloretApp`) |
| `token` | String | 是 | 用户的 App Token |

#### 请求示例
```http
GET /api/2fa/app/pending?username=Detritalw&app_id=BloretApp&token=87335c1df1398ac91cc779bae687f63c HTTP/1.1
Host: passport.bloret.net
```

#### 响应示例 (有待处理请求)
```json
{
  "success": true,
  "requests": [
    {
      "requestId": "a1b2c3d4e5f6...",
      "timestamp": 1709888888888,
      "ip": "192.168.1.10",
      "device": "Mozilla/5.0 (Windows NT 10.0...)",
      "location": "网页端登录"
    }
  ]
}
```

#### 响应示例 (无请求)
```json
{
  "success": true,
  "requests": []
}
```

---

### 3.2 批准/拒绝登录请求

当用户在 App 界面上点击“允许”或“拒绝”时调用此接口。

- **URL**: `https://passport.bloret.net/api/2fa/app/approve`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### 请求体 (JSON Body)

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `username` | String | 是 | 当前登录的用户名 |
| `app_id` | String | 是 | App 的应用 ID |
| `token` | String | 是 | 用户的 App Token |
| `requestId` | String | 是 | 从 3.1 接口获取到的 `requestId` |
| `action` | String | 是 | 操作类型：`approve` (允许) 或 `reject` (拒绝) |

#### 请求示例 (允许登录)
```json
{
  "username": "Detritalw",
  "app_id": "BloretApp",
  "token": "87335c1df1398ac91cc779bae687f63c",
  "requestId": "a1b2c3d4e5f6...",
  "action": "approve"
}
```

#### 响应示例
```json
{
  "success": true
}
```

---

## 4. App 端开发逻辑建议 (伪代码)

以下逻辑适用于 Flutter, React Native, Swift 或 Kotlin 开发。

### 步骤 1: 轮询服务 (Polling Service)

在 App 启动后或进入前台时，启动一个定时器。

```javascript
// 全局变量，防止重复处理同一个请求
let processedRequestIds = new Set();

function startPolling() {
    setInterval(async () => {
        try {
            // 1. 获取本地存储的用户信息
            const { username, appId, token } = await getUserCredentials();
            if (!username || !token) return;

            // 2. 发起请求
            const response = await fetch(`https://passport.bloret.net/api/2fa/app/pending?username=${username}&app_id=${appId}&token=${token}`);
            const data = await response.json();

            // 3. 处理响应
            if (data.success && data.requests.length > 0) {
                // 取出最新的一个请求
                const request = data.requests[0];
                
                // 如果这个 ID 还没处理过，弹窗提示
                if (!processedRequestIds.has(request.requestId)) {
                    showAuthDialog(request);
                }
            }
        } catch (error) {
            console.error("Polling error", error);
        }
    }, 5000); // 建议每 5 秒轮询一次
}
```

### 步骤 2: 弹窗 UI 逻辑

当获取到请求时，展示一个模态对话框 (Modal/Alert)。

**UI 展示内容建议：**
*   **标题**：尝试登录
*   **内容**：
    *   您的账号正在尝试登录网页端。
    *   **时间**：`Format(request.timestamp)`
    *   **IP地址**：`request.ip`
    *   **设备信息**：`request.device` (可以简单解析一下显示为 Chrome/Windows 等)
*   **按钮**：[拒绝] [允许登录]

### 3. 处理用户点击

```javascript
async function handleUserAction(requestId, action) {
    // action = 'approve' 或 'reject'
    
    // 1. 记录已处理，避免下次轮询再次弹出
    processedRequestIds.add(requestId);
    
    // 2. 关闭弹窗
    closeDialog();

    // 3. 发送请求给服务器
    try {
        const { username, appId, token } = await getUserCredentials();
        
        const response = await fetch('https://passport.bloret.net/api/2fa/app/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                app_id: appId,
                token,
                requestId,
                action
            })
        });

        const result = await response.json();
        
        if (result.success) {
            showToast(action === 'approve' ? "已确认登录" : "已拒绝登录");
        } else {
            showToast("操作失败: " + result.error);
        }
    } catch (e) {
        showToast("网络错误");
    }
}
```

## 5. 注意事项

1.  **安全性**：请确保 App 本地的 `token` 存储在安全区域（如 iOS Keychain 或 Android Keystore）。
2.  **用户体验**：
    *   不要在用户未登录 App 时轮询。
    *   如果 App 进入后台，建议降低轮询频率或停止轮询（依赖用户打开 App 刷新），或者在将来接入推送服务。
3.  **时间差**：请求在服务器端默认 **2分钟** 后过期。App 端如果获取到请求但用户迟迟不操作，服务器端可能会先过期，此时提交 `approve` 会返回 404 错误，App 需处理这种情况。