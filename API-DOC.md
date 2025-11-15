# Bloriko AI 接口文档

## 接口概述

新的 AI 接口提供了基于 OAuth 认证的 AI 对话服务，支持工具调用和异步处理模式。

## 基础信息

- **Base URL**: `http://localhost:20000`
- **认证方式**: OAuth 2.0 应用认证 + 用户 Token
- **内容类型**: `application/json`

## 接口列表

### 1. AI 对话接口

**POST** `/api/ai`

发起 AI 对话请求。

#### 请求参数

```json
{
    "pause": true,              // 可选，当 AI 使用工具时是否立即返回，默认 false
    "model": "Bloriko",         // 必填，使用的模型名称
    "OauthApp": {               // 必填，OAuth 应用信息
        "app_id": "BloretLauncher",
        "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
    },
    "user": {                   // 必填，用户信息
        "name": "Detritalw",
        "token": "63d06c701a29e9ba2d5e1e0b687c7fcb"
    },
    "context": [                // 必填，对话上下文
        {
            "role": "user",
            "content": "你好"
        },
        {
            "role": "assistant", 
            "content": "你好！有什么我可以帮助你的吗？"
        },
        {
            "role": "user",
            "content": "黑曜石是什么"
        }
    ]
}
```

#### 响应参数

**成功响应（未使用工具）**:
```json
{
    "status": true,
    "pause": false,
    "content": "黑曜石是..."
}
```

**成功响应（使用工具且 pause=true）**:
```json
{
    "status": true,
    "pause": true,
    "connectionId": "conn_1234567890_abc123",
    "content": "稍等，我帮你查查...",
    "message": "AI正在使用工具，请使用连接ID继续获取结果"
}
```

**成功响应（使用工具且 pause=false）**:
```json
{
    "status": true,
    "pause": false,
    "content": "根据查询结果，黑曜石是...",
    "toolUsed": true
}
```

**错误响应**:
```json
{
    "status": false,
    "error": "错误描述"
}
```

### 2. 继续获取结果接口

**POST** `/api/ai/continue`

当 AI 对话接口返回 `pause=true` 时，使用此接口继续获取最终结果。

#### 请求参数

```json
{
    "connectionId": "conn_1234567890_abc123"
}
```

#### 响应参数

**成功响应**:
```json
{
    "status": true,
    "content": "根据查询结果，最终答案是..."
}
```

**处理中响应**:
```json
{
    "status": true,
    "message": "AI正在处理中，请稍后重试"
}
```

**错误响应**:
```json
{
    "status": false,
    "error": "连接ID不存在或已过期"
}
```

## 模型配置

当前支持的模型及其配置：

### Bloriko 模型
- **描述**: 百络谷小画家络可，专门用于Minecraft相关对话
- **工具支持**: Minecraft Wiki 查询
- **语言**: 简体中文

### translate 模型
- **描述**: 翻译模型，将任意语言翻译为英文
- **工具支持**: 无

## 工具使用

### Minecraft Wiki 查询工具

当 AI 检测到需要使用 Minecraft Wiki 时，会自动触发工具调用。

**使用示例**:
用户: "橡木原木是哪个版本加入的？"
AI: "稍等，我帮你查查... ${wiki}(橡木原木)${/wiki}"

工具会自动查询 Minecraft Wiki 并提取相关内容。

## 认证流程

1. **获取 OAuth 应用信息**
   - 从 `data/oauthapp.json` 获取应用配置
   - 需要 `app_id` 和 `app_secret`

2. **获取用户 Token**
   - 从 `data/user.json` 获取用户的 `apptoken`
   - Token 对应特定应用的授权

3. **验证权限**
   - 系统会验证应用是否存在且密钥正确
   - 验证用户是否存在且 Token 有效

## 错误码说明

| HTTP状态码 | 含义 |
|------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 403 | 认证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### Node.js 示例

```javascript
const axios = require('axios');

async function chatWithAI() {
    try {
        const response = await axios.post('http://localhost:20000/api/ai', {
            pause: false,
            model: 'Bloriko',
            OauthApp: {
                app_id: 'BloretLauncher',
                app_secret: 's4d56f4a68sd46g54asd46f54a5dsf654asdf546'
            },
            user: {
                name: 'Detritalw',
                token: '63d06c701a29e9ba2d5e1e0b687c7fcb'
            },
            context: [
                {
                    role: 'user',
                    content: '你好'
                }
            ]
        });
        
        console.log('AI回复:', response.data.content);
    } catch (error) {
        console.error('请求失败:', error.response.data);
    }
}
```

### cURL 示例

```bash
curl -X POST http://localhost:20000/api/ai \
  -H "Content-Type: application/json" \
  -d '{
    "pause": false,
    "model": "Bloriko",
    "OauthApp": {
      "app_id": "BloretLauncher",
      "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
    },
    "user": {
      "name": "Detritalw",
      "token": "63d06c701a29e9ba2d5e1e0b687c7fcb"
    },
    "context": [
      {
        "role": "user",
        "content": "你好"
      }
    ]
  }'
```

## 注意事项

1. **连接ID有效期**: 5分钟，过期后无法继续获取结果
2. **工具调用限制**: 目前仅支持 Minecraft Wiki 查询
3. **频率限制**: 建议适当控制请求频率，避免触发 API 限制
4. **错误处理**: 建议实现重试机制和错误降级处理

## 更新日志

### v1.0.0 (2025-01-09)
- ✨ 新增 AI 对话接口
- ✨ 新增 OAuth 认证机制
- ✨ 新增工具调用功能
- ✨ 新增异步处理模式