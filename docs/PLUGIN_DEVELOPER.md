# Bloret Launcher 插件开发文档

规范版本：**1.1.0**（机器可读：`docs/plugin-spec.json`）

## 概述

Bloret Launcher 支持混合插件模型：

| 类型 | 说明 |
|------|------|
| **Python 扩展** | `main.py` 中 `register(api)`，可注册钩子、Agent 工具、工具栏等 |
| **声明式资源** | 仅 `plugin.json` + theme/qml/lang，不执行任意代码 |
| **外部进程** | `main.exe`，兼容旧插件，可走 Web API / `web.routes` |

插件安装目录：`{datapath}/Plugin/{folder}/`  
私有数据目录：`{datapath}/PluginData/{plugin_id}/`

## 三层扩展模型

1. **contributes**：UI / 资源注入（nav、home、tools、settings、theme…）
2. **hooks + 事件总线**：生命周期（`invoke_hook` 会同时通知 `register_hook` 与 `api.on`）
3. **PluginAPI**：受权限保护的能力调用（HTTP、FS、进程、通知…）

## 清单 `plugin.json`

兼容旧名 `cwplugin.json`。

```json
{
  "id": "com.example.demo",
  "name": "Demo",
  "version": "1.0.0",
  "author": "You",
  "description": "...",
  "entry": {
    "python": "main.py",
    "process": "main.exe",
    "qml_page": "ui/Page.qml"
  },
  "permissions": ["ui.nav", "ui.home", "launch.hooks", "agent.bloriko"],
  "contributes": {
    "nav": [{ "id": "demo", "title": "Demo", "page": "ui/Page.qml", "icon": "ic_fluent_puzzle_piece_20_regular" }],
    "home": [{ "id": "news", "title": "新闻", "qml": "ui/HomeCard.qml", "order": 50 }],
    "tools": [{ "id": "tool", "title": "工具", "qml": "ui/ToolCard.qml" }],
    "settings": [{ "id": "cfg", "title": "Demo 设置", "qml": "ui/Settings.qml" }],
    "theme": { "path": "theme/theme.json", "accent": "#ff8fab" },
    "toolbar": [{ "id": "btn", "label": "Demo", "action": "python:on_click" }],
    "i18n": [{ "locale": "zh-cn", "path": "lang/zh-cn.json" }],
    "prompts": { "bloriko_append": "prompts/extra.md", "blrpe_append": "prompts/rp.md" }
  },
  "hooks": {
    "on_enable": "main:on_enable",
    "launch.pre": "main:before_launch",
    "launch.jvm_args": "main:jvm_args",
    "launch.post": "main:after_launch",
    "launch.exit": "main:on_exit",
    "download.post": "main:after_download"
  }
}
```

## 权限

| 权限 | 风险 | 用途 |
|------|------|------|
| `ui.nav` | safe | 侧栏导航页 |
| `ui.theme` | safe | 主题包（accent + colors） |
| `ui.settings` | safe | 设置中心分类 + QML 页 |
| `ui.toolbar` | safe | Minecraft 小工具栏按钮 |
| `ui.home` | safe | 主页卡片 |
| `ui.tools` | safe | 小工具页卡片 |
| `launch.hooks` | high | 启动 pre/jvm/env/post/exit |
| `download.hooks` | high | 下载 start/progress/post/error |
| `agent.bloriko` | high | 络可工具与提示词 |
| `agent.blrpe` | high | BLRPE Copilot 工具与提示词 |
| `config.read` / `config.write` | safe/high | 读写启动器配置 |
| `fs.datapath` | high | 读写 datapath / PluginData 文件 |
| `net.http` | high | HTTP 请求 |
| `process.exec` | high | 执行外部进程（cwd 限 datapath/插件目录） |
| `web.routes` | high | 注册本地 Web 路由 |

## Python 插件

```python
def register(api):
    api.log("hello")
    api.register_hook("launch.jvm_args", lambda version, args: ["-Ddemo=1"])
    api.on("app.ready", lambda: api.log("ready via bus"))
    # 主页卡片也可运行时注册：
    # api.register_home_card("news", "新闻", "ui/HomeCard.qml", order=50)

def before_launch(api, version, context=None):
    # 取消启动：
    # return {"cancel": True, "reason": "原因"}
    return None

def jvm_args(api, version, base_args=None):
    return ["-Ddemo=1"]
```

### PluginAPI 常用方法

- `api.log(msg)`
- `api.notify(title, body)`
- `api.get_private_config()` / `set_private_config(dict)`
- `api.register_hook(name, fn)` — 与 `api.on` 均能收到 `invoke_hook` 标准事件
- `api.register_nav` / `register_settings` / `register_toolbar`
- `api.register_home_card` / `register_tools_card`（需 `ui.home` / `ui.tools`）
- `api.apply_theme_override(dict)`
- `api.register_agent_tool` / `append_system_prompt`
- `api.list_versions()` / `get_minecraft_dir()`
- `api.on` / `api.once`：订阅标准生命周期事件时执行对应权限检查；自定义事件无需额外权限
- `api.emit`：仅用于插件自定义事件，标准生命周期事件只能由启动器派发
- `api.http_get` / `http_post`（`net.http`）
- `api.read_data_file` / `write_data_file` / `read_plugin_data_file` / `write_plugin_data_file`（`fs.datapath`）
- `api.exec_process(args, cwd=..., timeout=...)`（`process.exec`）
- `api.register_web_route(method, path, handler, auth="oauth")`（`web.routes`）
  当前仅支持 `GET`/`ANY`，路径强制前缀为 `/api/v1/plugin/{plugin_id}/...`，并统一要求 OAuth

钩子函数签名推荐：`fn(api, ...)`；若不接受 `api` 也可直接 `fn(...)`。

## 标准钩子

| 钩子 | 权限 | 说明 |
|------|------|------|
| `on_enable` / `on_disable` | — | 启用/禁用 |
| `app.ready` / `app.quit` | — | 宿主启动完成 / 退出 |
| `launch.pre` | launch.hooks | 可返回 cancel |
| `launch.jvm_args` | launch.hooks | 返回 list 追加 |
| `launch.env` | launch.hooks | 返回 dict 合并 |
| `launch.post` | launch.hooks | `(version, pid)` |
| `launch.exit` | launch.hooks | `(version, pid, returncode, crashed)` |
| `download.start` | download.hooks | 安装开始 |
| `download.progress` | download.hooks | 进度（节流） |
| `download.post` / `download.complete` | download.hooks | 安装完成 |
| `download.error` | download.hooks | 安装失败 |
| `account.login` / `account.logout` | — | 账户摘要（无 token） |
| `passport.sync` | — | PassPort 同步完成 |
| `ui.page.open` | — | 导航切换 |
| `toolbar.action` | ui.toolbar | 小工具栏点击 |
| `theme.changed` / `config.changed` | — | 主题/配置变更 |

> **统一派发**：宿主通过 `invoke_hook` 同时调用 registry hooks 与 event bus。
> 因此 `api.register_hook("app.ready", ...)` 与 `api.on("app.ready", ...)` 都能收到。

## 主页 / 小工具 / 设置 UI 注入

### 主页卡片 `ui.home`

```json
"contributes": {
  "home": [{ "id": "news", "title": "MC 新闻", "qml": "ui/HomeCard.qml", "order": 50 }]
}
```

注入位置：`qml/pages/Home.qml` 活动横幅下方。示例：`examples/plugins/bloret.demo.home-news/`。

### 小工具卡片 `ui.tools`

```json
"contributes": {
  "tools": [{ "id": "t1", "title": "工具", "qml": "ui/ToolCard.qml" }]
}
```

示例：`examples/plugins/bloret.demo.tools/`。

### 设置页 `ui.settings`

```json
"contributes": {
  "settings": [{ "id": "cfg", "title": "Demo 设置", "qml": "ui/SettingsPage.qml" }]
}
```

设置中心 hub 会出现插件分类，详情区 Loader 加载 QML。示例：`examples/plugins/bloret.demo.settings/`。

### i18n

```json
"contributes": {
  "i18n": [{ "locale": "zh-cn", "path": "lang/zh-cn.json" }]
}
```

语言文件可为 `{ "texts": { "键": "译文" } }`，会在 `Backend.tr` / `i18nText` 中合并。

## 主题包

`theme/theme.json`：

```json
{
  "name": "Sakura",
  "mode": "dark",
  "accent": "#ff8fab",
  "colors": {
    "primaryColor": "#ff8fab",
    "backgroundColor": "#1a1020",
    "cardColor": "#2a1830",
    "textSecondaryColor": "#c9b0c0"
  }
}
```

宿主会应用 accent，并尽量写入 `Theme.currentTheme.colors` 白名单键。

## Web 路由

```python
def register(api):
    def hello(req):
        return {"status": "success", "data": {"path": req["path"]}}

    api.register_web_route("GET", "/hello", hello)
    # 实际路径: /api/v1/plugin/{plugin_id}/hello
    # 默认需 OAuth（与其它 /api/v1 一致）
```

## 使用 BLAPI 开发（推荐）

```bash
pip install BLAPI
BLAPI plugin init my-plugin --template python --id com.example.my-plugin --non-interactive
BLAPI plugin validate my-plugin --strict
BLAPI plugin install my-plugin
```

## 手动安装与调试

1. 将插件目录复制到 `{datapath}/Plugin/你的插件名/`
2. **设置 → 插件** 启用
3. 日志：`[PluginHost]`、`[Plugin:id]`；QML：`console.log`

## 官方示例

目录 `examples/plugins/`：

| 插件 | 演示 |
|------|------|
| `bloret.demo.nav` | 侧栏导航页 |
| `bloret.theme.sakura` | 主题 |
| `bloret.hooks.launch-banner` | 启动钩子 + toolbar |
| `bloret.agent.version-tool` | 络可工具 |
| `bloret.demo.home-news` | **主页新闻卡片** |
| `bloret.demo.settings` | 设置页 + i18n |
| `bloret.demo.tools` | 小工具卡片 |

## 安全

- 同进程插件与启动器同等信任，只安装可信来源。
- `process.exec` / `fs.datapath` / `config.write` 等高风险权限请谨慎声明。
- 账户钩子不包含 token / 密码。
- Web 路由强制 `/api/v1/plugin/{id}/` 前缀。

## 路线图（后续）

Core Manager 标签、Mods 内容源、Live 面板、通知渠道、AI 连接器 / Provider 等，见开发计划 Phase 2–5。
