# 插件商店服务端 / 前端对接文档

面向：**商店网站后端、CDN、前端页面**开发者。  
目标：用户在商店点「安装到 Bloret Launcher」→ 激活启动器 → 原生确认 → 下载 ZIP 安装。

> 启动器侧实现版本：支持 `bloret://plugin/install` 与本机 `POST /plugin/store/propose`。  
> 相关文档：`PLUGIN_WEB_API.md` §5.4、`docs/PLUGIN_DEVELOPER.md`、BLAPI 打包说明。

---

## 1. 角色与边界

| 角色 | 职责 |
|------|------|
| **商店服务端** | 上架审核、元数据、静态/对象存储托管 ZIP、生成安装链接、（可选）列表 API |
| **商店前端** | 展示插件卡片；点击安装时跳转 `bloret://` 或探测本机后 `propose` |
| **Bloret Launcher** | 注册协议、弹出确认、下载 ZIP、校验、解压安装到 `{datapath}/Plugin/{id}/` |

**商店不负责**：

- 静默写入用户机器上的插件目录  
- 代替用户点击「确认安装」  
- 使用 OAuth 完成用户安装（OAuth 仅工具链 `/plugin/add`）

```text
┌─────────────┐    HTTPS 列表/详情     ┌──────────────────┐
│ 商店前端     │ ◄──────────────────► │ 商店 API / CDN   │
└──────┬──────┘                       └────────┬─────────┘
       │ ① bloret://plugin/install?...         │ 托管 ZIP
       │ 或 ② POST 127.0.0.1:25252/propose     │
       ▼                                       │
┌──────────────────────────────────────────────▼─┐
│              Bloret Launcher                   │
│  确认对话框 → 下载 download URL → 安装 ZIP     │
└────────────────────────────────────────────────┘
```

---

## 2. 分发包格式（必须）

启动器只接受 **BLAPI / BLDEV 打出的插件 ZIP**（或等价结构）。

### 2.1 ZIP 结构

```text
my-plugin-1.0.0.zip
├── plugin.json          # 或 cwplugin.json（根目录）
├── main.py              # 可选
├── ui/
│   └── HomeCard.qml     # 可选
└── ...
```

也允许 **仅一层包装目录**：

```text
archive.zip
└── my-plugin/
    ├── plugin.json
    └── ...
```

### 2.2 `plugin.json` 最低字段

```json
{
  "id": "com.example.news",
  "name": "Minecraft 新闻",
  "version": "1.0.0",
  "author": "Example",
  "description": "在主页展示新闻",
  "permissions": ["ui.home"]
}
```

| 字段 | 要求 |
|------|------|
| `id` | 安装目录名；建议反向域名；字符 `a-zA-Z0-9._-`，长度 ≤ 128 |
| `name` | 显示名 |
| `version` | 语义化版本字符串即可 |
| `author` / `description` | 建议提供，确认框会展示商店传入的副本 |

安装后路径：`{用户数据目录}/Plugin/{plugin.json 的 id}/`。  
**商店元数据中的 `id` 应与 ZIP 内 `plugin.json.id` 一致**，避免确认信息与安装结果不一致。

### 2.3 打包命令（作者侧）

```bash
# 校验
BLDEV plugin validate . --strict
# 打包（输出含 path / size / sha256）
BLDEV plugin package . -o dist/
```

服务端入库时建议保存 BLAPI 返回的 **`sha256`**，安装链接里带上。

---

## 3. 商店侧元数据模型（建议）

列表/详情 API 建议字段（可扩展，安装链路只依赖标注为「安装用」的字段）：

```json
{
  "id": "com.example.news",
  "name": "Minecraft 新闻",
  "version": "1.2.0",
  "author": "Example Studio",
  "description": "主页新闻卡片",
  "icon": "https://cdn.example.com/icons/news.png",
  "homepage": "https://example.com/plugins/news",
  "download": "https://cdn.example.com/plugins/com.example.news-1.2.0.zip",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "size": 123456,
  "permissions": ["ui.home"],
  "min_launcher": "27.2",
  "created_at": "2026-07-01T00:00:00Z",
  "updated_at": "2026-07-13T00:00:00Z",
  "tags": ["home", "news"]
}
```

| 字段 | 安装链路 | 说明 |
|------|----------|------|
| `download` | **必填** | 直链 **HTTPS** ZIP；启动器 `GET` 下载 |
| `id` | 强烈建议 | 展示与一致性 |
| `name` | 强烈建议 | 确认框标题 |
| `version` | 建议 | 确认框 |
| `author` | 建议 | 确认框 |
| `description` | 建议 | 确认框 |
| `sha256` | 强烈建议 | 64 位小写/大写 hex；有则下载后校验 |
| `icon` 等 | 否 | 仅商店 UI |

### 3.1 `download` URL 要求

1. **协议**：仅 `https://`（`http://` 会被启动器拒绝）。
2. **可直连**：响应体为 ZIP 文件（`200`），不要 HTML 登录页；不要强制多余 Cookie。
3. **CORS**：浏览器安装**不经过**商店 JS 读 ZIP，由启动器下载，**CDN 无需为安装给浏览器配 CORS**。若商店前端自己 `fetch` 校验包则另论。
4. **主机白名单**：见 [§6](#6-下载主机白名单)。官方商店域名应使用已在默认白名单中的主机，或引导用户在启动器配置信任主机。
5. **稳定性**：URL 应在一段时间内有效；若用带签名的临时 URL，过期时间要覆盖「用户点安装 → 确认 → 下载」窗口（建议 ≥ 1 小时）。

### 3.2 `sha256`

- 对 **ZIP 文件全文** 做 SHA-256，hex 编码，长度 64。  
- 与 BLAPI `plugin package` 输出的 `sha256` 一致。  
- 安装链接带上后，校验失败会中止安装并提示用户。

```bash
# 服务端示例
sha256sum com.example.news-1.2.0.zip
```

---

## 4. 安装协议（主路径，必做）

### 4.1 URL 形态

```text
bloret://plugin/install?{query}
```

兼容别名：

```text
bloret://install-plugin?{query}
```

### 4.2 Query 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `download` | **是** | HTTPS ZIP URL，需 URL-encode |
| `id` | 否 | 插件 id |
| `name` | 否 | 显示名 |
| `version` | 否 | 版本 |
| `author` | 否 | 作者（别名 `master` 也可被解析） |
| `description` | 否 | 简介（别名 `desc` / `summary`） |
| `sha256` | 否 | 64 hex |
| `source` | 否 | 默认 `store`；建议商店固定传 `store` |

**编码注意**：

- 整段 query 用标准 `URLSearchParams` / `urllib.parse.urlencode`。  
- `download` 本身含 `://`、`&` 时必须编码。  
- 不要把 OAuth secret 放进协议 URL。

### 4.3 服务端生成安装链接（推荐）

商店后端提供「一键安装」链接，前端只负责跳转，避免前端拼错字段。

**示例：Python**

```python
from urllib.parse import urlencode

def build_bloret_install_url(plugin: dict) -> str:
    """plugin 至少含 download；建议含 id/name/version/author/description/sha256。"""
    q = {
        "download": plugin["download"],
        "id": plugin.get("id") or "",
        "name": plugin.get("name") or "",
        "version": plugin.get("version") or "",
        "author": plugin.get("author") or "",
        "description": plugin.get("description") or "",
        "sha256": (plugin.get("sha256") or "").lower(),
        "source": "store",
    }
    # 去掉空值，缩短 URL
    q = {k: v for k, v in q.items() if v}
    return "bloret://" + "plugin/install?" + urlencode(q)
```

**示例：Node.js**

```js
function buildBloretInstallUrl(plugin) {
  const q = new URLSearchParams();
  q.set("download", plugin.download);
  for (const k of ["id", "name", "version", "author", "description", "sha256"]) {
    if (plugin[k]) q.set(k, String(plugin[k]));
  }
  q.set("source", "store");
  return `bloret://plugin/install?${q.toString()}`;
}
```

**示例：HTTP API（商店自己的接口）**

```http
GET /api/store/v1/plugins/{id}/install-link
→ 200
{
  "install_url": "bloret://plugin/install?download=...&id=...&name=...&sha256=...",
  "download": "https://cdn.../x.zip",
  "sha256": "..."
}
```

前端：

```js
const { install_url } = await api.getInstallLink(pluginId);
window.location.href = install_url;
// 或 <a href={install_url}>安装到 Bloret Launcher</a>
```

### 4.4 用户点击后的系统行为

| 状态 | 行为 |
|------|------|
| 启动器**未运行** | OS 按 `bloret` 协议启动启动器，argv 带 URL → 启动后弹确认 |
| 启动器**已运行** | 二次进程把 URL 经本机 IPC 转给首实例 → 窗口前置 + 弹确认 |
| 未安装启动器 / 未注册协议 | 浏览器通常无反应或提示找不到应用 → 商店应做 fallback UI |

---

## 5. 本机 HTTP 投递（增强路径，可选）

当用户**已经打开**启动器时，商店页可先尝试本机接口，失败再回退 `bloret://`。

### 5.1 端点

| 方法 | 路径 | OAuth |
|------|------|-------|
| `GET` / `POST` | `http://127.0.0.1:25252/plugin/store/propose` | **不需要** |
| 同上 | `http://127.0.0.1:25252/api/v1/plugin/store/propose` | **不需要** |

> 仅本机；**不会静默安装**，只投递到确认队列。

### 5.2 请求

**POST JSON（推荐）**

```http
POST /plugin/store/propose HTTP/1.1
Host: 127.0.0.1:25252
Content-Type: application/json

{
  "download": "https://cdn.example.com/plugins/com.example.news-1.2.0.zip",
  "id": "com.example.news",
  "name": "Minecraft 新闻",
  "version": "1.2.0",
  "author": "Example Studio",
  "description": "主页新闻卡片",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "source": "store"
}
```

**GET query**（参数同名字段）

```text
GET /plugin/store/propose?download=https%3A%2F%2F...&id=com.example.news&name=...
```

### 5.3 成功响应（示例）

```json
{
  "status": "success",
  "ok": true,
  "token": "随机 token",
  "pending": true,
  "request": {
    "token": "...",
    "download": "https://...",
    "id": "com.example.news",
    "name": "Minecraft 新闻",
    "version": "1.2.0",
    "author": "Example Studio",
    "description": "...",
    "sha256": "...",
    "source": "store",
    "status": "pending",
    "download_host": "cdn.example.com",
    "display_name": "Minecraft 新闻"
  },
  "message": "已提交安装请求，等待用户确认",
  "silent": false,
  "note": "已投递到启动器，需用户在原生对话框中确认后才会安装"
}
```

### 5.4 失败响应（示例）

| HTTP | 场景 |
|------|------|
| `400` | 缺 `download`、非 https、主机不在白名单、sha256 格式错误 |
| `500` | 启动器内部错误 |
| 网络错误 / 连接失败 | 启动器未开或端口占用 → 前端应回退 `bloret://` |

```json
{
  "status": "error",
  "ok": false,
  "message": "download 仅允许 https://（当前: http）",
  "hint": "需要 https download；确认在启动器内完成，不会静默安装"
}
```

### 5.5 前端推荐实现（智能安装）

```js
/**
 * @param {object} p 商店插件对象，至少 p.download
 */
async function installToBloretLauncher(p) {
  const payload = {
    download: p.download,
    id: p.id || "",
    name: p.name || "",
    version: p.version || "",
    author: p.author || "",
    description: p.description || "",
    sha256: p.sha256 || "",
    source: "store",
  };

  // 1) 尝试本机投递（启动器已开时体验更好）
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 800);
    const res = await fetch("http://127.0.0.1:25252/plugin/store/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
      mode: "cors", // 启动器若未回 CORS 头可能失败，见下方注意
    });
    clearTimeout(timer);
    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      if (data.ok !== false) {
        showTip("请在 Bloret Launcher 中确认安装");
        return { path: "localhost", data };
      }
    }
  } catch (_) {
    // 未运行或跨域失败 → 协议
  }

  // 2) 自定义协议（可冷启动）
  const q = new URLSearchParams();
  Object.entries(payload).forEach(([k, v]) => {
    if (v) q.set(k, v);
  });
  const url = `bloret://plugin/install?${q.toString()}`;
  window.location.href = url;

  // 3) 协议无回调：延迟提示下载启动器
  setTimeout(() => {
    showTip("若未自动打开启动器，请先安装并打开 Bloret Launcher，或检查是否允许打开 bloret 链接");
  }, 2500);

  return { path: "protocol", url };
}
```

**CORS 注意**：本机 `25252` 若未返回 `Access-Control-Allow-Origin`，浏览器 `fetch` 可能失败。这是预期情况——**直接回退 `bloret://` 即可**。不要因此阻塞安装。若需可靠探测，可用：

- 仅依赖 `bloret://`（最简单、最稳）  
- 或商店后端不探测，由用户点击「已打开启动器，再次安装」

服务端/文档侧**默认推荐以 `bloret://` 为主路径**。

---

## 6. 下载主机白名单

启动器默认信任（含子域匹配规则：`host == t` 或 `host.endswith("." + t)`）：

| 主机 |
|------|
| `github.com` / `www.github.com` |
| `raw.githubusercontent.com` |
| `objects.githubusercontent.com` |
| `release-assets.githubusercontent.com` |
| `cdn.jsdelivr.net` |
| `gitee.com` / `www.gitee.com` |
| `gitlab.com` / `www.gitlab.com` |
| `bloret.com` / `www.bloret.com` |
| `store.bloret.com` |
| `api.bloret.com` |

### 6.1 官方商店域名建议

- 将 ZIP 放在 **`store.bloret.com` / `cdn` 已在白名单的域名**，或 GitHub Releases。  
- 若使用自有 CDN（如 `cdn.your-store.com`）：
  1. **长期**：向启动器发版增加默认白名单；或  
  2. **短期**：用户在配置中设置：

```json
{
  "plugin_store_trusted_hosts": ["cdn.your-store.com", "files.your-store.com"]
}
```

或（不推荐生产默认打开）：

```json
{
  "plugin_store_allow_any_https": true
}
```

### 6.2 商店上架校验（服务端应做）

上传/发布时拒绝：

- 非 `https` 的 `download`
- 无法 HEAD/GET 到 ZIP（或 Content-Type 明显不是归档）
- `sha256` 与文件不一致
- ZIP 内无 `plugin.json` / `id` 不合法
- `plugin.json.id` 与商店 `id` 不一致

伪代码：

```python
def validate_listing(meta, zip_bytes):
    assert meta["download"].startswith("https://")
    assert re.fullmatch(r"[a-fA-F0-9]{64}", meta["sha256"])
    assert sha256(zip_bytes) == meta["sha256"].lower()
    # 解压检查 plugin.json
    manifest = read_plugin_json(zip_bytes)
    assert manifest["id"] == meta["id"]
```

---

## 7. 建议的商店 HTTP API 形状

以下为**商店自己的后端**约定示例（非启动器接口），便于前后端分工。

### 7.1 列表

```http
GET /api/store/v1/plugins?page=1&page_size=20&q=news&tag=home
```

```json
{
  "items": [ { "id", "name", "version", "author", "description", "icon", "download", "sha256", "tags" } ],
  "total": 42,
  "page": 1
}
```

### 7.2 详情

```http
GET /api/store/v1/plugins/{id}
```

### 7.3 安装链接

```http
GET /api/store/v1/plugins/{id}/install-link
→ { "install_url": "bloret://plugin/install?..." }
```

### 7.4 上传（作者/审核后台）

```http
POST /api/store/v1/admin/plugins
Content-Type: multipart/form-data
file: *.zip
meta: JSON
```

服务端：校验 ZIP → 算 sha256 → 上传对象存储 → 写库 → 状态 `pending_review` / `published`。

---

## 8. 错误场景与产品文案

| 场景 | 用户侧建议文案 |
|------|----------------|
| 未安装启动器 | 「请先安装 Bloret Launcher，安装后重新点击」+ 下载页链接 |
| 协议无反应 | 同上；Windows/Linux 首次启动启动器会注册协议 |
| 确认框主机不在白名单 | 「下载来源不受信任」→ 检查 CDN 域名或文档说明白名单 |
| sha256 失败 | 「安装包校验失败，请从官方商店重新下载」→ 检查 CDN 文件是否被替换 |
| 用户点取消 | 无操作即可 |
| ZIP 损坏 / 无 plugin.json | 「插件包无效」 |

---

## 9. 安全清单（服务端必读）

1. **只分发审核过的 ZIP**；不要信任用户随意提交的 `download` 指向第三方未知站。  
2. **`download` 固定为你们 CDN 上的对象**，不要开放「任意 URL 安装」的商店按钮（防钓鱼）。  
3. **始终带 `sha256`**，降低中间人/缓存污染风险。  
4. **不要在安装 URL 里塞 token/密钥**。  
5. **不要实现「远程静默安装」API** 面向公网；启动器也不会提供无确认安装。  
6. 与旧接口区分：  
   - 用户商店 → `bloret://` / `/plugin/store/propose`  
   - 自动化工具 → `localhost:25252/plugin/add` + OAuth  

---

## 10. 联调步骤（给商店开发）

1. 用 BLAPI 打一个示例 ZIP，上传到 **https** 且在白名单内的主机。  
2. 计算 sha256，拼好 `bloret://plugin/install?...`。  
3. **先打开** Bloret Launcher（完成一次启动以注册协议）。  
4. 在浏览器地址栏粘贴安装 URL，或页面按钮跳转。  
5. 期望：启动器前置，弹出确认框，显示名称/作者/版本/主机。  
6. 点安装 → 下载成功 → 设置页插件列表出现该 id。  
7. 关掉启动器再点一次 → 应冷启动后同样弹确认。  
8. （可选）启动器开着时测 `POST http://127.0.0.1:25252/plugin/store/propose`。

### 10.1 快速自测 URL 模板

```text
bloret://plugin/install?download=https%3A%2F%2Fgithub.com%2F%3Corg%3E%2F%3Crepo%3E%2Freleases%2Fdownload%2F%3Ctag%3E%2Fplugin.zip&id=com.example.demo&name=Demo&version=1.0.0&author=You&source=store
```

---

## 11. 字段对照速查

| 商店字段 | 协议 query | 本机 propose JSON | plugin.json |
|----------|------------|-------------------|-------------|
| `download` | `download` | `download` | — |
| `id` | `id` | `id` | `id` |
| `name` | `name` | `name` | `name` |
| `version` | `version` | `version` | `version` |
| `author` | `author` | `author` | `author` |
| `description` | `description` | `description` | `description` |
| `sha256` | `sha256` | `sha256` | （打包产物） |
| — | `source=store` | `source` | — |

---

## 12. 版本与兼容

| 能力 | 说明 |
|------|------|
| 自定义协议 | 启动器启动时尝试注册 `bloret` |
| 单实例转发 | 已运行时二次启动转发 deep link，不双开 |
| 无 OAuth 用户安装 | `bloret://` + `/plugin/store/propose` |
| 旧 OAuth 页 | `/plugin/add` 仍保留，**不要**给商店用户按钮用 |

若商店需声明兼容性，可对启动器版本字段做软提示（`min_launcher`），但安装协议本身不强制版本号参数。

---

## 13. 附录：完整最小商店页

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>插件商店示例</title>
</head>
<body>
  <h1>示例插件</h1>
  <button id="btn">安装到 Bloret Launcher</button>
  <p id="tip"></p>
  <script>
    const plugin = {
      id: "com.example.demo",
      name: "Demo",
      version: "1.0.0",
      author: "Demo Author",
      description: "示例插件",
      download: "https://github.com/org/repo/releases/download/v1.0.0/demo.zip",
      sha256: "", // 生产环境务必填写
    };

    function buildUrl(p) {
      const q = new URLSearchParams();
      q.set("download", p.download);
      ["id", "name", "version", "author", "description", "sha256"].forEach((k) => {
        if (p[k]) q.set(k, p[k]);
      });
      q.set("source", "store");
      return "bloret://plugin/install?" + q.toString();
    }

    document.getElementById("btn").onclick = () => {
      const url = buildUrl(plugin);
      document.getElementById("tip").textContent = "正在唤起启动器…";
      window.location.href = url;
    };
  </script>
</body>
</html>
```

---

*文档与启动器 `modules/plugin_install_request.py`、`modules/protocol_handler.py`、`modules/web.py`（`/plugin/store/propose`）行为对齐。若有差异，以当前启动器源码为准。*
