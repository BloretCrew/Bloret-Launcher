# Bloret PassPort AI API

本文档说明 Bloret PassPort 的 OpenAI 兼容 AI API。当前实现面向 Chat Completions，支持非流式和流式传输。

## 兼容范围

已实现：

- `POST /v1/chat/completions`
- `GET /v1/models`
- `GET /v1/billing`

兼容目标：

- 请求体使用 OpenAI Chat Completions 格式。
- 非流式响应默认透传上游 OpenAI 兼容响应。
- 流式响应使用 Server-Sent Events，`Content-Type: text/event-stream`。
- 流式结束帧为 `data: [DONE]`。

未实现：

- `/v1/responses`
- embeddings、images、audio、files、batches 等其它 OpenAI API 端点
- OpenAI organization/project 级鉴权头

## 准备工作

使用 AI API 前需要满足以下条件：

1. 用户已拥有 AI 余额。
2. 已创建 OAuth 应用。
3. OAuth 应用已绑定 AI 模型。
4. 用户已为该 OAuth 应用生成 UserToken。

API Key 由三段拼接：

```text
{AppID};{AppSecret};{UserToken}
```

调用时放在标准 Bearer 头中：

```http
Authorization: Bearer {AppID};{AppSecret};{UserToken}
```

服务端会按 OAuth 应用绑定的模型调用上游模型。客户端请求体中的 `model` 字段会被服务端覆盖，因此可以传任意占位值，也可以不依赖它做路由。

## 配置模型

AI 网关读取 `config.json` 中的 `ai.providers` 和 `ai.models`。

示例：

```json
{
  "ai": {
    "providers": [
      {
        "id": "default",
        "name": "Default Provider",
        "baseUrl": "https://api.openai.com",
        "apiKey": "sk-...",
        "enabled": true
      }
    ],
    "models": [
      {
        "id": "gpt-4o",
        "name": "gpt-4o",
        "upstreamModel": "gpt-4o",
        "provider": "default",
        "enabled": true,
        "pricing": {
          "mode": "token",
          "inputPer1k": 0.0025,
          "outputPer1k": 0.01
        }
      }
    ]
  }
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `providers[].id` | 上游供应商 ID，供模型配置引用 |
| `providers[].baseUrl` | 上游 OpenAI 兼容 API 基础地址，不要包含 `/v1/chat/completions` |
| `providers[].apiKey` | 上游供应商 API Key |
| `models[].id` | 本地模型 ID，可用于 OAuth 应用绑定 |
| `models[].name` | 对外展示的模型名；未配置 `upstreamModel` 时也作为上游模型名 |
| `models[].upstreamModel` | 可选，上游真实模型名 |
| `models[].provider` | 对应 `providers[].id` |
| `models[].pricing.mode` | `token` 或 `request` |
| `models[].pricing.inputPer1k` | token 计费模式下，每 1000 输入 token 费用 |
| `models[].pricing.outputPer1k` | token 计费模式下，每 1000 输出 token 费用 |
| `models[].pricing.pricePerRequest` | request 计费模式下，每次请求费用 |

## Chat Completions

### 非流式请求

```bash
curl https://passport.bloret.net/v1/chat/completions \
  -H "Authorization: Bearer {AppID};{AppSecret};{UserToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ignored-by-passport",
    "messages": [
      { "role": "user", "content": "Hello" }
    ]
  }'
```

成功响应为上游 OpenAI 兼容响应，例如：

```json
{
  "id": "chatcmpl_xxx",
  "object": "chat.completion",
  "created": 1720000000,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello!"
      },
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

默认不会向响应中添加非 OpenAI 字段。若需要调试计费结果，可以加查询参数或请求头：

```bash
curl "https://passport.bloret.net/v1/chat/completions?include_billing=true" \
  -H "Authorization: Bearer {AppID};{AppSecret};{UserToken}" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

或者：

```http
x-include-billing: true
```

启用后，非流式响应会额外包含：

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
  -H "Authorization: Bearer {AppID};{AppSecret};{UserToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ignored-by-passport",
    "stream": true,
    "messages": [
      { "role": "user", "content": "Write one short sentence." }
    ]
  }'
```

响应格式为 SSE：

```text
data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: [DONE]
```

服务端会在流式请求中自动注入：

```json
{
  "stream_options": {
    "include_usage": true
  }
}
```

这样可以在最终 chunk 中拿到 `usage` 并记录扣费。客户端通常可以忽略包含 `usage` 的最终 chunk，直到收到 `data: [DONE]`。

## OpenAI SDK 示例

JavaScript：

```js
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://passport.bloret.net/v1",
  apiKey: "{AppID};{AppSecret};{UserToken}"
});

const completion = await client.chat.completions.create({
  model: "ignored-by-passport",
  messages: [{ role: "user", content: "Hello" }]
});

console.log(completion.choices[0].message.content);
```

JavaScript 流式：

```js
const stream = await client.chat.completions.create({
  model: "ignored-by-passport",
  stream: true,
  messages: [{ role: "user", content: "Say hi." }]
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

Python：

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://passport.bloret.net/v1",
    api_key="{AppID};{AppSecret};{UserToken}",
)

completion = client.chat.completions.create(
    model="ignored-by-passport",
    messages=[{"role": "user", "content": "Hello"}],
)

print(completion.choices[0].message.content)
```

## Models

```bash
curl https://passport.bloret.net/v1/models \
  -H "Authorization: Bearer {AppID};{AppSecret};{UserToken}"
```

响应：

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1720000000,
      "owned_by": "bloret-passport"
    }
  ]
}
```

该接口只返回当前 OAuth 应用绑定的模型。

若需要调试绑定关系，可以加 `include_billing=true` 或 `x-include-billing: true`，响应中的 model 对象会额外包含 `bound_to_app`。

## Billing

查询余额和用量：

```bash
curl "https://passport.bloret.net/v1/billing?page=1&pageSize=20" \
  -H "Authorization: Bearer {AppID};{AppSecret};{UserToken}"
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
        "model_id": "gpt-4o",
        "provider_id": "default",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "cost": "0.000225",
        "billing_mode": "token",
        "ip_address": "127.0.0.1",
        "created_at": "2026-07-06T00:00:00.000Z"
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

## 错误响应

错误响应统一为：

```json
{
  "error": {
    "message": "错误说明",
    "type": "错误类型"
  }
}
```

常见错误：

| HTTP 状态码 | `type` | 说明 |
| --- | --- | --- |
| `401` | `auth_error` | 缺少 API Key、格式错误、AppSecret 错误或 UserToken 无效 |
| `402` | `insufficient_balance` | AI 余额不足 |
| `400` | `config_error` | OAuth 应用未绑定模型，或绑定模型不存在/已禁用 |
| `500` | `server_error` | Provider 配置缺失或服务端内部错误 |
| `502` | `upstream_error` | 无法连接上游，或上游流式响应异常 |
| `504` | `timeout_error` | 上游请求超时 |

上游 OpenAI 兼容服务返回的错误会尽量原样透传。

## 计费行为

非流式请求：

- 若上游响应包含 `usage`，服务端按 `prompt_tokens` 和 `completion_tokens` 扣费。
- 若上游不返回 `usage`，不会扣 token 费用。

流式请求：

- 服务端会请求上游在最终 chunk 返回 usage。
- 收到 usage 后记录用量并扣费。
- 如果上游不支持 `stream_options.include_usage` 或没有返回 usage，流式请求不会按 token 扣费。

扣费模式：

- `pricing.mode = "token"`：按输入/输出 token 分别计费。
- `pricing.mode = "request"`：每次有 usage 记录时按请求计费。

## 管理说明

管理员需要完成：

1. 在 `config.json` 中配置 AI provider 和 model。
2. 初始化数据库，确保存在 `ai_balances`、`ai_usage_records` 表，以及 `oauth_apps.bound_model` 字段。
3. 为用户设置 AI 余额。
4. 为 OAuth 应用绑定模型。

用户在 `/ai` 页面可以查看余额、可用 API Key 组成方式和最近用量。

