# Bloret PassPort AI API

本文档说明 Bloret PassPort 的 AI API 代理。上游固定为单一模型，客户端传入的 `model` 字段会被服务端覆盖。

## 兼容范围

已实现：

- `POST /v1/chat/completions`
- `GET /v1/models`
- `GET /v1/billing`
- `POST /v1/keys` — 创建 API Key
- `GET /v1/keys` — 列出 API Key
- `DELETE /v1/keys/:id` — 删除 API Key

请求体使用 OpenAI Chat Completions 格式。非流式响应透传上游响应，流式响应使用 SSE（`text/event-stream`），结束帧为 `data: [DONE]`。

未实现：

- `/v1/responses`
- embeddings、images、audio、files、batches 等其它端点

## 认证

支持两种 Bearer Token 格式：

### 方式一：自注册 API Key（推荐）

在 `/ai` 页面创建 API Key，格式为 `sk-` 前缀的随机字符串。

```http
Authorization: Bearer sk-your-api-key
```

### 方式二：OAuth 应用三段式 Key

兼容旧的 OAuth 集成方式，格式为：

```http
Authorization: Bearer {AppID};{AppSecret};{UserToken}
```

## 请求限额

每位用户每天最多 200 次请求（可通过 `config.json` 的 `ai.dailyRequestLimit` 调整）。超限返回 `429 Too Many Requests`：

```json
{
  "error": {
    "message": "Daily request limit reached (200/day)",
    "type": "rate_limit"
  }
}
```

限额在每日 0 点（服务器本地时间）重置。

## Chat Completions

### 非流式请求

```bash
curl https://passport.bloret.net/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      { "role": "user", "content": "Hello" }
    ]
  }'
```

客户端传入的 `model` 字段会被忽略，服务端统一使用上游固定模型。响应为上游 OpenAI 兼容格式：

```json
{
  "id": "chatcmpl_xxx",
  "object": "chat.completion",
  "created": 1720000000,
  "model": "claude-fable-5",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "Hello!" },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 3,
    "total_tokens": 11
  }
}
```

调试计费：添加 `?include_billing=true` 或请求头 `x-include-billing: true`，响应额外包含：

```json
{
  "billing": {
    "cost": 0.001,
    "balance": 9.999
  }
}
```

### 流式请求

```bash
curl -N https://passport.bloret.net/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "stream": true,
    "messages": [
      { "role": "user", "content": "Write one short sentence." }
    ]
  }'
```

服务端会自动注入 `stream_options.include_usage` 以在最终 chunk 中获取 usage 用于计费。

## API Key 管理

以下接口使用 Cookie 认证（需要已登录）。

### 创建 API Key

```bash
curl -X POST https://passport.bloret.net/v1/keys \
  -H "Content-Type: application/json" \
  -b "username=alice" \
  -d '{"name": "我的测试 Key"}'
```

响应：

```json
{
  "success": true,
  "key": {
    "id": 1,
    "api_key": "sk-a1b2c3d4e5f6...",
    "name": "我的测试 Key",
    "created_at": "2026-07-07T00:00:00.000Z"
  }
}
```

> **注意：** 完整 Key 仅在创建时返回一次，请立即复制保存。

### 列出 API Key

```bash
curl https://passport.bloret.net/v1/keys -b "username=alice"
```

响应中 Key 做掩码处理：

```json
{
  "success": true,
  "keys": [
    {
      "id": 1,
      "name": "我的测试 Key",
      "key_preview": "sk-a1b2c3...e5f6",
      "created_at": "2026-07-07T00:00:00.000Z"
    }
  ]
}
```

### 删除 API Key

```bash
curl -X DELETE https://passport.bloret.net/v1/keys/1 -b "username=alice"
```

```json
{ "success": true }
```

## Models

```bash
curl https://passport.bloret.net/v1/models \
  -H "Authorization: Bearer sk-your-api-key"
```

返回上游固定模型信息。添加 `include_billing=true` 可在响应中看到 `bound_to_app` 字段（OAuth 方式下）。

## Billing

查询余额和用量：

```bash
curl "https://passport.bloret.net/v1/billing?page=1&pageSize=20" \
  -H "Authorization: Bearer sk-your-api-key"
```

响应：

```json
{
  "balance": 10,
  "total_used": 0.25,
  "request_count": 12,
  "usage": {
    "records": [
      {
        "id": 1,
        "username": "alice",
        "model_id": "default",
        "provider_id": "upstream",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "cost": "0.000225",
        "billing_mode": "token",
        "ip_address": "127.0.0.1",
        "created_at": "2026-07-07T00:00:00.000Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `page` | `1` | 页码 |
| `pageSize` | `20` | 每页条数，最大 `100` |

## OpenAI SDK 示例

JavaScript：

```js
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://passport.bloret.net/v1",
  apiKey: "sk-your-api-key"
});

const completion = await client.chat.completions.create({
  messages: [{ role: "user", content: "Hello" }]
});

console.log(completion.choices[0].message.content);
```

Python：

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://passport.bloret.net/v1",
    api_key="sk-your-api-key",
)

completion = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
)

print(completion.choices[0].message.content)
```

## 错误响应

统一格式：

```json
{
  "error": {
    "message": "错误说明",
    "type": "错误类型"
  }
}
```

| HTTP 状态码 | `type` | 说明 |
| --- | --- | --- |
| `401` | `auth_error` | 缺少 API Key、格式错误、Key 无效或 UserToken 无效 |
| `402` | `insufficient_balance` | AI 余额不足 |
| `429` | `rate_limit` | 超出每日请求限额 |
| `500` | `server_error` | 服务端内部错误 |
| `502` | `upstream_error` | 无法连接上游，或上游流式响应异常 |
| `504` | `timeout_error` | 上游请求超时 |

## 计费行为

- 非流式：上游响应包含 `usage` 时按 token 扣费，否则不扣费。
- 流式：服务端请求上游在最终 chunk 返回 usage，收到后扣费。上游不返回 usage 则不扣费。
- `pricing.mode = "token"`：按输入/输出 token 分别计费（`inputPer1k` / `outputPer1k`）。
- `pricing.mode = "request"`：每次请求固定费用。

## 配置

`config.json` 中的 AI 配置：

```json
{
  "ai": {
    "provider": {
      "baseUrl": "https://router.bloret.net",
      "apiKey": "sk-..."
    },
    "upstreamModel": "claude-fable-5",
    "pricing": {
      "inputPer1k": 1,
      "outputPer1k": 1,
      "mode": "request"
    },
    "dailyRequestLimit": 200
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `provider.baseUrl` | 上游 API 基础地址（不含 `/v1/chat/completions`） |
| `provider.apiKey` | 上游 API Key |
| `upstreamModel` | 上游固定模型名，所有请求统一转发到此模型 |
| `pricing.mode` | `token` 或 `request` |
| `pricing.inputPer1k` | token 模式下每 1000 输入 token 费用 |
| `pricing.outputPer1k` | token 模式下每 1000 输出 token 费用 |
| `pricing.pricePerRequest` | request 模式下每次请求费用 |
| `dailyRequestLimit` | 每位用户每天最大请求数，默认 200 |

## 管理说明

管理员需要完成：

1. 在 `config.json` 中配置 `ai.provider`、`ai.upstreamModel` 和 `ai.pricing`。
2. 确保数据库表 `ai_balances`、`ai_usage_records`、`ai_api_keys` 已创建（服务启动时自动创建）。
3. 为用户设置 AI 余额（管理后台 `/ai` 页面）。

用户在 `/ai` 页面可以：
- 查看余额、今日请求用量
- 创建和管理 API Key
- 查看最近用量记录
