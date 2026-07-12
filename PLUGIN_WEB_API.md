# Bloret Launcher Plugin Web API

本文件描述 Bloret Launcher 的插件 Web API 规范与可用接口。该 API 运行在本地 Web 服务器上，适合插件或外部工具通过 HTTP 调用启动器能力。

## 1. 基础规则

- **全部使用 GET**。
- **所有插件 API 都必须携带 `oauth` 参数**，否则会返回 400/401。
- 可选参数：`redirect=<url>`，用于操作成功后跳转到指定页面。
- API 默认监听：`http://localhost:25252`。

> 注意：`oauth` 包含应用的 `name` 与 `secret`，会被转发到 Bloret PassPort 的 OAuth 应用校验接口进行验证。

## 2. OAuth 参数规范

### 2.1 推荐格式（JSON）

将 `oauth` 编码为 JSON 字符串并进行 URL 编码：

```
GET /api/v1/ping?oauth=%7B%22name%22%3A%22APP_NAME%22%2C%22secret%22%3A%22APP_SECRET%22%7D
```

等价于（未编码的示例）：

```
/oauth?oauth={"name":"APP_NAME","secret":"APP_SECRET"}
```

### 2.2 兼容格式

以下格式也会被识别：

- `oauth=APP_NAME:APP_SECRET`
- `oauth=APP_NAME,APP_SECRET`
- `oauth.name=APP_NAME&oauth.secret=APP_SECRET`
- `oauth_name=APP_NAME&oauth_secret=APP_SECRET`

### 2.3 OAuth 校验流程

服务端会调用 PassPort 校验接口：

```
GET https://passport.bloret.net/app/oauthapp/validate?appname=APP_NAME&appsecret=APP_SECRET
```

校验失败将返回 401 JSON，校验成功才能继续后续处理。

## 3. 返回格式与跳转

### 3.1 JSON 响应

成功：

```json
{
  "status": "success",
  "message": "...",
  "data": { ... }
}
```

错误：

```json
{
  "status": "error",
  "message": "错误原因"
}
```

### 3.2 redirect 行为

当请求包含 `redirect=<url>` 时，成功场景会返回 302 跳转，并在目标 URL 上附加：

```
status=success
```

部分接口（插件安装）在失败时会使用：

```
status=error
```

## 4. API 列表（/api/v1）

> 以下接口均为 GET，并 **必须携带 oauth**。

### 4.1 健康检查

- **路径**: `/api/v1/ping`
- **参数**: 无
- **返回**: `pong` + `timestamp`

示例：

```
GET http://localhost:25252/api/v1/ping?oauth=...
```

### 4.2 系统信息

- **路径**: `/api/v1/system/info`
- **参数**: 无
- **返回**: 平台、Python 版本、数据路径、缓存路径、配置路径、Minecraft 目录

### 4.3 启动项列表

- **路径**: `/api/v1/launch/items`
- **参数**: 无
- **返回**: `get_all_launch_items()` 列表

### 4.4 启动游戏

- **路径**: `/api/v1/launch/start`
- **参数**:
  - `version` (必填) 目标版本名称
- **返回**: 启动进程 PID

### 4.5 PassPort 登录状态

- **路径**: `/api/v1/passport/status`
- **参数**: 无
- **返回**: `logined`、`username`、`avatar`

### 4.6 同步 PassPort 账户

- **路径**: `/api/v1/passport/sync-accounts`
- **参数**: 无
- **返回**: 同步结果

### 4.7 启动前账户准备

- **路径**: `/api/v1/passport/prepare-launch-account`
- **参数**: 无
- **返回**: 启动前账户准备结果

### 4.8 Minecraft 账户信息

- **路径**: `/api/v1/minecraft/accounts`
- **参数**: 无
- **返回**: `MinecraftAccount` 配置对象

### 4.9 读取配置

- **路径**: `/api/v1/config/get`
- **参数**:
  - `key` (可选) 若指定则只返回该键值

### 4.10 写入配置

- **路径**: `/api/v1/config/set`
- **参数**:
  - `key` (必填)
  - `value` (必填)
- **说明**: `value` 会尝试 JSON 解析，失败则按字符串保存。

### 4.11 活动信息

- **路径**: `/api/v1/activity/get`
- **参数**: 无
- **返回**: `BL_Activity` 数据

### 4.12 刷新活动信息

- **路径**: `/api/v1/activity/refresh`
- **参数**: 无
- **返回**: 刷新后的 `BL_Activity`

### 4.13 插件安装（JSON 版）

- **路径**: `/api/v1/plugin/install`
- **参数**:
  - `download` (必填) 插件下载 URL（zip 或插件描述 JSON）
  - `name` (可选) 插件名称
- **返回**: 任务提交结果

### 4.14 插件列表

- **路径**: `/api/v1/plugin/list`
- **参数**: 无
- **返回**: 已安装插件列表（包含 name/id/version/author/description/url/path 等）

### 4.15 插件卸载

- **路径**: `/api/v1/plugin/uninstall`
- **参数**:
  - `name` (必填) 插件名称或目录名
- **返回**: 卸载结果

### 4.16 插件启用

- **路径**: `/api/v1/plugin/enable`
- **参数**:
  - `name` (必填) 插件 id / 名称 / 目录名
- **返回**: 启用结果

### 4.17 插件禁用

- **路径**: `/api/v1/plugin/disable`
- **参数**:
  - `name` (必填) 插件 id / 名称 / 目录名
- **返回**: 禁用结果

### 4.18 插件详情

- **路径**: `/api/v1/plugin/info`
- **参数**:
  - `name` (可选) 指定插件；省略则返回全部
- **返回**: 插件运行时信息（enabled/active/permissions 等）

### 4.19 帮助

- **路径**: `/api/v1/help`
- **参数**: 无
- **返回**: 规则与路径清单

> 进程内插件宿主（PluginHost）开发文档见 `docs/PLUGIN_DEVELOPER.md`。

## 5. 插件交互式页面接口（/plugin）

> 这些接口会返回 HTML 页面或执行跳转，适合在浏览器中打开。

### 5.1 一体化插件入口

- **路径**: `/plugin/add`
- **参数**:
  - `oauth` (必填)
  - `action` (可选) `confirm` / `install`，默认 `confirm`
  - `list` (可选) 插件信息 JSON 的 URL
  - `download` (可选) 插件下载 URL
  - `name` / `master` / `version` (可选)
  - `redirect` (可选)

**推荐用法**:

```
GET http://localhost:25252/plugin/add?action=confirm&list=PLUGIN_JSON_URL&oauth=...
```

### 5.2 仅确认页（旧版）

- **路径**: `/plugin/confirm`
- **参数**: `oauth` + `name` + `download` + `master` + `version` + `redirect`(可选)

### 5.3 仅安装（旧版）

- **路径**: `/plugin/install`
- **参数**: `oauth` + `download` + `name`(可选) + `redirect`(可选)

## 6. 示例

### 6.1 启动游戏

```
GET http://localhost:25252/api/v1/launch/start?version=1.20.4&oauth={"name":"Demo","secret":"xxxx"}
```

### 6.2 写入配置（布尔）

```
GET http://localhost:25252/api/v1/config/set?key=show_account_on_home&value=true&oauth=...
```

### 6.3 插件确认页

```
GET http://localhost:25252/plugin/add?action=confirm&list=https://example.com/plugin.json&oauth=...
```

## 7. 错误码与常见问题

- **400**: 缺少必填参数（如 `oauth`、`version` 等）
- **401**: OAuth 校验失败（应用不存在或密钥不正确）
- **404**: 未知 API 路径
- **500**: 服务内部异常

> 安全提示：由于 OAuth 密钥通过 URL 传递，建议仅在本机或可信网络中使用，并避免将完整 URL 记录在公开日志中。
