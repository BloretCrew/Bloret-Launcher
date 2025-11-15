# Bloret Launcher Website API 文档

## 概述
本文档描述了 Bloret Launcher 网站的 API 接口，用于管理版本发布和配置更新。

## 基础信息
- **Base URL**: `http://pcfs.eno.ink:3001`
- **Content-Type**: `application/json`
- **认证方式**: API Key 验证

## API 端点

### 发布新版本

**POST** `/api/newversion/github`

发布新的测试版或正式版，并更新配置文件。

#### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| key | string | ✅ | API 密钥，从 config.json 中获取 |
| beta | boolean | ✅ | 是否为测试版 (`true` 为测试版，`false` 为正式版) |
| version | string | ✅ | 版本号 (tag)，如 `"8.2b3"` |
| versionName | string | ✅ | 版本名称，如 `"8.2 Beta 3"` |
| description | string | ✅ | 版本描述，如 `"欢迎体验 Bloret Launcher 8.2 测试版！"` |

#### 请求示例

**测试版发布：**
```json
{
  "key": "github_key",
  "beta": true,
  "version": "8.2b3",
  "versionName": "8.2 Beta 3",
  "description": "欢迎体验 Bloret Launcher 8.2 测试版！"
}
```

**正式版发布：**
```json
{
  "key": "github_key",
  "beta": false,
  "version": "8.2",
  "versionName": "8.2 正式版",
  "description": "Bloret Launcher 8.2 正式版发布了！"
}
```

#### 响应参数

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "Beta version updated successfully",
  "data": {
    "beta": true,
    "version": "8.2b3",
    "versionName": "8.2 Beta 3",
    "description": "欢迎体验 Bloret Launcher 8.2 测试版！"
  }
}
```

**错误响应：**

**401 Unauthorized - 密钥错误：**
```json
{
  "success": false,
  "error": "Invalid key"
}
```

**400 Bad Request - 缺少必填字段：**
```json
{
  "success": false,
  "error": "Missing required fields: version, versionName, description"
}
```

**500 Internal Server Error - 服务器错误：**
```json
{
  "success": false,
  "error": "Internal server error"
}
```

#### 功能说明

1. **测试版发布** (`beta: true`)
   - 更新 `Beta` 配置对象
   - 设置 `Beta.enabled = true`
   - 更新版本号、版本名称和描述
   - 网站将显示测试版下载选项

2. **正式版发布** (`beta: false`)
   - 更新 `BLLatest` 版本号
   - 更新 `BLNewVersionDescription` 描述
   - 网站主版本信息将更新

#### 配置文件更新

API 调用成功后，将自动更新 `config.json` 文件：

**测试版更新示例：**
```json
{
  "Beta": {
    "enabled": true,
    "version": "8.2b3",
    "versionName": "8.2 Beta 3",
    "description": "欢迎体验 Bloret Launcher 8.2 测试版！"
  }
}
```

**正式版更新示例：**
```json
{
  "BLLatest": "8.2",
  "BLNewVersionDescription": "Bloret Launcher 8.2 正式版发布了！"
}
```

## 使用示例

### cURL 示例
```bash
# 发布测试版
curl -X POST http://localhost:3001/api/newversion/github \
  -H "Content-Type: application/json" \
  -d '{
    "key": "github_key",
    "beta": true,
    "version": "8.2b3",
    "versionName": "8.2 Beta 3",
    "description": "欢迎体验 Bloret Launcher 8.2 测试版！"
  }'

# 发布正式版
curl -X POST http://localhost:3001/api/newversion/github \
  -H "Content-Type: application/json" \
  -d '{
    "key": "github_key",
    "beta": false,
    "version": "8.2",
    "versionName": "8.2 正式版",
    "description": "Bloret Launcher 8.2 正式版发布了！"
  }'
```

### JavaScript (fetch) 示例
```javascript
// 发布测试版
fetch('http://localhost:3001/api/newversion/github', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    key: 'github_key',
    beta: true,
    version: '8.2b3',
    versionName: '8.2 Beta 3',
    description: '欢迎体验 Bloret Launcher 8.2 测试版！'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 安全说明

1. **API 密钥管理**
   - 密钥存储在 `config.json` 文件的 `github_key` 字段中
   - 建议在生产环境中使用更复杂的密钥
   - 定期更换密钥以确保安全

2. **请求验证**
   - 所有请求必须包含正确的 API 密钥
   - 请求体会进行完整的字段验证
   - 错误请求会返回相应的 HTTP 状态码

## 注意事项

1. 配置文件 (`config.json`) 会在每次成功请求后自动更新
2. 测试版发布不会影响正式版配置
3. 正式版发布可以选择是否禁用测试版（当前实现中注释了相关代码）
4. API 会实时生效，网站会立即显示更新后的版本信息

## 更新日志

- **2024年**: 初始版本，支持测试版和正式版发布