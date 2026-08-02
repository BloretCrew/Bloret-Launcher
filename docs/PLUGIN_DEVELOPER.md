# Bloret Launcher 插件开发文档

规范版本：**2.0.0**（机器可读：`docs/plugin-spec.json`；兼容 1.1 清单）  
Wiki 同步页：[插件开发规范](https://github.com/BloretCrew/Bloret-Launcher/wiki/插件开发规范)

---

## 插件能做什么？（先看这里）

不改启动器源码即可扩展主要功能。按目标选路径：

| 我想… | 怎么做 | 权限示例 |
|--------|--------|----------|
| 主题 / 侧栏页 / 主页卡片 / 设置页 | `contributes.theme` / `nav` / `home` / `settings` | `ui.theme` / `ui.nav` / `ui.home` / `ui.settings` |
| 在 Mods、下载、Live、核心、通行证、统计、关于、论坛、络可、联机等页插入 UI | `contributes.panels` 或 `api.register_panel(area, …)` | `ui.mods` / `ui.download` / `ui.live` / … |
| 拦截启动、加 JVM 参数、改环境变量 | `launch.pre` / `jvm_args` / `env` 钩子 | `launch.hooks` |
| 下载进度、改镜像 URL | `download.*` / `download.resolve_url` | `download.hooks` |
| 监听登录、配置变更、切页 | `account.*` / `config.changed` / `ui.page.open` | 多为安全权限 |
| Live / EasyTier | `live.*` / `easytier.*` 钩子 | `live.control` |
| 扩展络可 / Blora Agent | `register_agent_tool` / `prompts` | `agent.bloriko` / `agent.blrpe` |
| 读版本 / Mods / 资源包 | `list_versions*` / `list_mods` / Web `/api/v1/…` | `versions.read` / `mods.read` |
| 自定义本地 HTTP、通知渠道、`bloret://` 路径 | `register_web_route` / `register_notification_channel` / `register_protocol_handler` | `web.routes` / `notify.channel` / `protocol.handle` |

**三层模型**（可组合）：① `contributes` 声明式 UI → ② `hooks` 拦截回调 → ③ `PluginAPI` / Web API 主动调用。

**三种形态**：声明式（无代码）/ Python（`register(api)`）/ 外部进程（`main.exe` + Web API）。

**5 分钟上手**：

```bash
pip install BLAPI
BLDEV plugin init my-plugin --template python --id com.example.my-plugin --non-interactive
BLDEV plugin package my-plugin -o dist
# 设置 → 插件 → 从文件安装
```

官方示例：`examples/plugins/`。完整对照与 FAQ 见 Wiki「插件开发规范」。

**安全边界**：钩子无 token/密码；高风险权限需用户授权；只装可信源。

---

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

1. **contributes**：UI / 资源注入（nav、home、tools、settings、theme、**panels**…）
2. **hooks + 事件总线**：生命周期（`invoke_hook` 会同时通知 `register_hook` 与 `api.on`）
3. **PluginAPI**：受权限保护的能力调用（HTTP、FS、进程、通知、版本/内容只读…）

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

完整列表见 `docs/plugin-spec.json`。常用项：

| 权限 | 风险 | 用途 |
|------|------|------|
| `ui.nav` | safe | 侧栏导航页 |
| `ui.theme` | safe | 主题包（accent + colors） |
| `ui.settings` | safe | 设置中心分类 + QML 页 |
| `ui.toolbar` | safe | Minecraft 小工具栏按钮 |
| `ui.home` / `ui.tools` | safe | 主页 / 小工具卡片 |
| `ui.cores` / `ui.mods` / `ui.download` / `ui.live` / … | safe | 各功能页 **panel** 注入 |
| `launch.hooks` / `launch.control` | high | 启动拦截 / 控制进程 |
| `download.hooks` / `download.source` | high | 下载钩子 / 自定义源 |
| `versions.read` / `versions.write` | safe/high | 版本列表与修改 |
| `mods.read` / `mods.write` / `mods.source` | safe/high | Mods 读写与内容源 |
| `content.read` / `content.write` | safe/high | 资源包 / 服务器等 |
| `live.control` | high | Live / EasyTier |
| `agent.bloriko` / `agent.blrpe` / `agent.provider` | high | Agent 与 AI 供应商 |
| `notify.send` / `notify.channel` | safe/high | 通知与渠道 |
| `config.read` / `config.write` | safe/high | 读写启动器配置 |
| `fs.datapath` | high | 读写 datapath / PluginData 文件 |
| `net.http` | high | HTTP 请求 |
| `process.exec` | high | 执行外部进程（cwd 限 datapath/插件目录） |
| `web.routes` | high | 注册本地 Web 路由（GET/POST/PUT/DELETE/PATCH） |

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
- `api.register_panel(area, id, title, qml, ...)`（需 `ui.{area}`，如 `live` → `ui.live`）
- `api.register_content_source(kind, id, title, ...)`（`mods` / `download`）
- `api.apply_theme_override(dict)`
- `api.register_agent_tool` / `append_system_prompt`
- `api.list_versions()` / `list_versions_detail()` / `get_version_path()` / `get_minecraft_dir()`
- `api.list_running_instances()`
- `api.on` / `api.once`：订阅标准生命周期事件时执行对应权限检查；自定义事件无需额外权限
- `api.emit`：仅用于插件自定义事件，标准生命周期事件只能由启动器派发
- `api.http_get` / `http_post`（`net.http`）
- `api.read_data_file` / `write_data_file` / `read_plugin_data_file` / `write_plugin_data_file`（`fs.datapath`）
- `api.exec_process(args, cwd=..., timeout=...)`（`process.exec`）
- `api.register_web_route(method, path, handler, auth="oauth")`（`web.routes`）
  支持 `GET`/`POST`/`PUT`/`DELETE`/`PATCH`/`ANY`，路径强制前缀为 `/api/v1/plugin/{plugin_id}/...`，并统一要求 OAuth

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

## 功能页面板注入（2.0）

```json
"contributes": {
  "panels": {
    "live": [{ "id": "status", "title": "状态", "qml": "ui/LivePanel.qml", "order": 50 }],
    "mods": [{ "id": "extra", "title": "扩展", "qml": "ui/ModsPanel.qml" }]
  }
}
```

或使用简写键：`"live": [{ "qml": "..." }]`（需 `ui.live`）。

QML 侧通过 `PluginHost.getPanelContributionsJson("live")` 读取；宿主信号 `panelsContributionsChanged`。  
主要功能页（Mods / Download / Live / Cores / PassPort / Statistics / Info / BBBS / Bloriko / Multiplayer / CoreManager / RPE）已接入 `PluginPanelHost`。

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
# 安装 CLI（命令名 BLDEV / BLAPI / BLCLI 均可）
pip install BLAPI
# 或开发模式: pip install ./BLAPI

BLDEV plugin init my-plugin --template python --id com.example.my-plugin --non-interactive
BLDEV plugin validate my-plugin --strict
BLDEV plugin package my-plugin -o dist
# 产物: dist/com.example.my-plugin-1.0.0.zip

# 开发机直接安装到本机启动器数据目录
BLDEV plugin install dist/com.example.my-plugin-1.0.0.zip --force
# 或安装源码目录:
BLDEV plugin install my-plugin --force
```

`plugin package` 与 `plugin build` 等价。`-o dist` 表示输出到目录，文件名自动为 `{id}-{version}.zip`。

## 发布与分发流程

推荐链路：

1. **开发**：`plugin init` / 手写 `plugin.json` + QML/Python
2. **校验**：`BLDEV plugin validate . --strict`
3. **打包**：`BLDEV plugin package . -o dist` → 得到可分发 ZIP
4. **CI 自动打包**：仓库已提供 `.github/workflows/plugin-package.yml`
   - 对 `examples/plugins/*` 执行 validate + package
   - 上传 artifact：`bloret-plugins`（内含各插件 ZIP）
5. **用户安装**
   - 启动器：**设置 → 插件 → 从文件安装**，选择 ZIP
   - 开发者：`BLDEV plugin install xxx.zip --force`
   - **商店 / 网页一键安装（推荐）**：
     ```text
     bloret://plugin/install?download=https://.../plugin.zip&id=...&name=...&version=...&author=...&sha256=...
     ```
     打开链接 → 激活 Bloret Launcher → **原生确认** → 用户确认后下载安装（无 OAuth，禁止静默安装）。
   - 启动器已在运行时：`POST http://127.0.0.1:25252/plugin/store/propose`（无 OAuth，仅投递确认队列）
   - 旧工具链：`/plugin/add?download=...zip`（**需要 OAuth**，不适合商店用户按钮）
6. **插件商店**：分发 BLAPI 打出的同一 ZIP；元数据字段与 `plugin.json` 对齐  
   - **服务端 / 商店前端对接文档**：[`docs/PLUGIN_STORE_SERVER.md`](PLUGIN_STORE_SERVER.md)

ZIP 要求：

- 根目录（或仅一层包装目录）含 `plugin.json` / `cwplugin.json`
- 由 BLAPI 打包时已做路径校验，安装时会按清单 `id` 写入 `{datapath}/Plugin/{id}/`

## 手动安装与调试

1. **推荐**：设置 → 插件 → **从文件安装**（选择 `*.zip`）
2. 或将插件目录复制到 `{datapath}/Plugin/{plugin_id}/`
3. **设置 → 插件** 启用 / 刷新
4. 日志：`[PluginHost]`、`[Plugin]`、`[Plugin:id]`；QML：`console.log`

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

| Phase | 内容 | 状态 |
|-------|------|------|
| 0 | Service 门面、Registry 泛化 panels/sources、权限/钩子 2.0、Web POST、spec 2.0 | **已落地** |
| 1 | 钩子接线审计 + 版本/启动/内容只读 API + Web 镜像 | **已落地** |
| 2 | Mods / 资源包 / Core / servers 钩子 + 页面板 | **已落地** |
| 3 | `download.resolve_url` + Download 面板 | **已落地** |
| 4 | Live / EasyTier 钩子 + 各功能页 PluginPanelHost | **已落地** |
| 5 | 通知渠道、协议 handler、notify.send 钩子 | **已落地**（AI Provider / 托盘热键注册表就绪，运行时替换可后续深化） |
| 6 | 契约测试 `test_plugin_extensibility.py` + 文档 | **已落地** |
