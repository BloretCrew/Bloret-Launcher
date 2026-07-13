# Bloret Launcher 插件开发文档

## 概述

Bloret Launcher 支持混合插件模型：

| 类型 | 说明 |
|------|------|
| **Python 扩展** | `main.py` 中 `register(api)`，可注册钩子、Agent 工具、工具栏等 |
| **声明式资源** | 仅 `plugin.json` + theme/qml/lang，不执行任意代码 |
| **外部进程** | `main.exe`，兼容旧插件，注册为自定义启动项，可走 Web API |

插件安装目录：`{datapath}/Plugin/{folder}/`  
私有数据目录：`{datapath}/PluginData/{plugin_id}/`

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
  "permissions": ["ui.nav", "launch.hooks", "agent.bloriko"],
  "contributes": {
    "nav": [{ "id": "demo", "title": "Demo", "page": "ui/Page.qml", "icon": "ic_fluent_puzzle_piece_20_regular" }],
    "theme": { "path": "theme/theme.json", "accent": "#ff8fab" },
    "toolbar": [{ "id": "btn", "label": "Demo", "action": "python:on_click" }],
    "prompts": { "bloriko_append": "prompts/extra.md", "blrpe_append": "prompts/rp.md" }
  },
  "hooks": {
    "on_enable": "main:on_enable",
    "launch.pre": "main:before_launch",
    "launch.jvm_args": "main:jvm_args",
    "launch.post": "main:after_launch",
    "download.post": "main:after_download"
  }
}
```

## 权限

| 权限 | 用途 |
|------|------|
| `ui.nav` | 侧栏导航页 |
| `ui.theme` | 主题包 |
| `ui.settings` | 设置页扩展 |
| `ui.toolbar` | Minecraft 小工具栏按钮 |
| `launch.hooks` | 启动前后 / JVM / 环境变量 |
| `download.hooks` | 下载安装完成钩子 |
| `agent.bloriko` | 络可工具与提示词 |
| `agent.blrpe` | BLRPE Copilot 工具与提示词 |
| `config.read` / `config.write` | 读写启动器配置 |
| `net.http` | HTTP 请求 |
| `process.exec` | 执行外部进程 |
| `web.routes` | 本地 Web 路由（规划中） |

## Python 插件

```python
def register(api):
    api.log("hello")
    api.register_hook("launch.jvm_args", lambda version, args: ["-Ddemo=1"])
    # 或使用 manifest hooks 指向函数

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
- `api.register_hook(name, fn)`
- `api.register_nav(...)` / `register_toolbar(...)` / `apply_theme_override(dict)`
- `api.register_agent_tool(target, definition, executor, kind="read")`
- `api.append_system_prompt(target, text)`
- `api.list_versions()` / `get_minecraft_dir()`
- `api.on(event, cb)` / `api.emit(event, ...)`
- `api.http_get` / `http_post`（需 `net.http`）

钩子函数签名推荐：`fn(api, ...)`；若不接受 `api` 也可直接 `fn(...)`。

## 标准钩子

| 钩子 | 参数 | 说明 |
|------|------|------|
| `on_enable` / `on_disable` | `(api)` | 启用/禁用 |
| `launch.pre` | `(api, version, context)` | 可返回 cancel |
| `launch.jvm_args` | `(api, version, base_args)` | 返回 list |
| `launch.env` | `(api, version, env)` | 返回 dict 合并 |
| `launch.post` | `(api, version, pid)` | 进程已启动 |
| `download.post` | `(api, version, loader, path)` | 安装完成 |

## 事件总线

```python
api.on("download.complete", lambda ctx: api.log(str(ctx)))
api.emit("my.event", 1, 2)
```

内置事件包括：`app.ready`、`app.quit`、`launch.pre`、`launch.post`、`download.complete`、`download.post`、`theme.changed`、`toolbar.action`、`config.changed` 等。

## 主题包

`theme/theme.json`：

```json
{
  "name": "Sakura",
  "mode": "dark",
  "accent": "#ff8fab",
  "colors": {
    "primaryColor": "#ff8fab",
    "backgroundColor": "#1a1020"
  }
}
```

用户可在 **设置 → 插件** 中选择活动主题插件。

## Agent 工具

```python
def register(api):
    def my_tool(working_dir=None, **kwargs):
        return "result"

    api.register_agent_tool("bloriko", {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "...",
            "parameters": {"type": "object", "properties": {}}
        }
    }, my_tool, kind="read")
```

`target` 为 `bloriko` 或 `blrpe`。

## 使用 BLAPI 开发（推荐）

安装 PyPI 工具后，可以从脚手架到本地联调完成整个开发流程：

```bash
pip install BLAPI
BLAPI plugin init my-plugin --template python --id com.example.my-plugin --non-interactive
BLAPI plugin validate my-plugin --strict
BLAPI plugin inspect my-plugin
BLAPI plugin build my-plugin -o dist
BLAPI plugin install my-plugin
```

`plugin init` 支持 `declarative`、`python`、`theme`、`nav`、`agent` 模板。生成的 Python 与 QML 模板默认包含详细日志，便于分别从 `[Plugin:插件ID]` 和浏览器/Qt 控制台排查问题。

需要与正在运行的启动器联调时，可使用：

```bash
BLAPI plugin dev my-plugin --oauth-name YOUR_APP --oauth-secret YOUR_SECRET
```

该命令会先校验并同步插件，再通过本地 Launcher Web API 检查插件状态。纯本地的 `init`、`validate`、`inspect` 和 `build` 不需要 OAuth，也不会联网。

插件规范的机器可读版本位于 `docs/plugin-spec.json`。BLAPI 内置同版本快照用于离线校验；规范版本不一致时应先升级 BLAPI。

## 手动安装与调试

1. 将插件目录复制到 `{datapath}/Plugin/你的插件名/`，或打包 zip 后通过 Web API `/plugin/add` 安装。ZIP 根目录必须直接包含 `plugin.json`，不要额外套一层目录。
2. 打开 **设置 → 插件** 启用/禁用/卸载。
3. 日志前缀：`[PluginHost]`、`[Plugin:id]`；QML 用 `console.log`。

### Web API（OAuth 必填）

- `GET /api/v1/plugin/list`
- `GET /api/v1/plugin/install?download=...&name=...`
- `GET /api/v1/plugin/uninstall?name=...`
- `GET /api/v1/plugin/enable?name=...`
- `GET /api/v1/plugin/disable?name=...`
- `GET /api/v1/plugin/info?name=...`

详见 `PLUGIN_WEB_API.md`。

## 官方示例

目录 `examples/plugins/`：

| 插件 | 作用 |
|------|------|
| `bloret.theme.sakura` | 声明式主题 |
| `bloret.demo.nav` | 侧栏示例页 |
| `bloret.hooks.launch-banner` | 启动/下载钩子 + 工具栏 |
| `bloret.agent.version-tool` | 络可 list_local_mc_versions |

复制到 Plugin 目录即可测试：

```bash
cp -r examples/plugins/bloret.theme.sakura "$DATA/Plugin/"
```

## 安全建议

- 仅安装可信来源插件；Python 插件与启动器同进程运行。
- 高危权限（`launch.hooks`、`process.exec`、`config.write`）应在 UI 中明确告知用户。
- 钩子应快速返回；长任务用 `api.run_async`。
