# Minecraft Token 刷新接口文档

## 接口概述

该接口用于刷新已登录用户的 Minecraft Access Token。当用户的 Token 过期（例如长时间未游玩导致凭证失效）时，调用此接口可自动使用后台存储的 `refresh_token` 向微软申请新的凭证，并更新服务器端的会话数据。

**接口地址**: `/api/login/Minecraft/Refresh`
**请求方式**: `POST`
**认证方式**: Cookie (需要包含有效的 `username` Cookie)

## 请求参数

无请求体参数。接口通过请求头中的 Cookie 识别用户身份。

**Headers**:
- `Cookie`: `username=your_username; ...`

## 响应格式

### 成功响应 (200 OK)

```json
{
    "success": true,
    "message": "Token 刷新成功",
    "access_token": "eyJhbGciOiJSUzI1NiIsIng1dCI6Im..." // 新的 Minecraft Access Token
}
```

### 失败响应

**1. 未登录或会话过期 (401 Unauthorized)**
```json
{
    "success": false,
    "message": "登录已过期"
}
```

**2. 未绑定 Minecraft 账号 (404 Not Found)**
```json
{
    "success": false,
    "message": "未绑定 Minecraft 账号"
}
```

**3. 凭证失效 (400 Bad Request)**
*通常发生在 refresh_token 也过期或被撤销的情况下，此时用户必须重新走完整的登录流程。*
```json
{
    "success": false,
    "message": "凭证已失效，请重新登录"
}
```

**4. 服务器内部错误 (500 Internal Server Error)**
*可能是网络连接微软服务器失败，或代理配置错误。*
```json
{
    "success": false,
    "message": "刷新失败，请重新登录",
    "error": "Request failed with status code 404"
}
```

## 使用场景

建议在前端应用或启动器中实现以下逻辑：

1.  发起 Minecraft 相关的 API 请求。
2.  如果 API 返回 `401 Unauthorized` 或提示 Token 无效。
3.  自动调用 `/api/login/Minecraft/Refresh` 接口。
4.  如果刷新成功，使用新的 `access_token` 重试之前的请求。
5.  如果刷新失败，提示用户重新进行微软登录。

## 注意事项

- **代理支持**: 该接口会遵循 `config.json` 中的 `proxy` 配置。如果开启了代理，刷新请求将通过代理发送。
- **频率限制**: 虽然接口内部实现了重试机制，但建议不要高频调用，以免触发微软的限流策略。
