# Launcher 实时译文

Bloret Launcher 在启动和切换语言时通过 `tr.bloret.net` 的公开 API 同步语言包。

## API

1. `GET /api/v1/orgs/bloret/projects/bloret-launcher/manifest`
2. `GET /api/v1/orgs/bloret/projects/bloret-launcher/files/cd3f495d-eb9e-466f-888e-93df7eeef861/translated?locale={locale}&mode=top_voted`

## 行为

- 软件首先加载本地内容并显示界面，网络请求在后台执行，不阻塞首帧。
- 切换语言时立即加载 AppData 缓存或安装包内置语言，随后后台更新。
- 成功下载后原子保存并热重载界面。
- 请求、校验或写入失败时不会删除、清空或覆盖旧缓存。
- API 返回空译文时保留内置目标语言或中文源文，避免空白 UI。

加载优先级：

1. 安装包内置 `lang/zh-cn.json`（基础结构和最终中文回退）
2. 安装包内置目标语言
3. AppData 中已缓存的 API 语言包（仅非空值覆盖）
4. 插件 `contributes.i18n`（最后覆盖）

## 跨平台缓存路径

| 平台 | 路径 |
|------|------|
| Windows | `%APPDATA%/Bloret-Launcher/lang` |
| macOS | `~/Library/Application Support/Bloret-Launcher/lang` |
| Linux / FreeBSD | `$XDG_DATA_HOME/Bloret-Launcher/lang`，未设置时 `~/.local/share/Bloret-Launcher/lang` |

manifest 缓存为 `_manifest.json`，语言文件继续使用 Launcher code，例如 `en-GB.json`。

## Locale 映射

| Launcher | API |
|----------|-----|
| `en-GB` | `en` |
| `gt-ZH` | `gt` |
| `ja-JP` | `ja` |
| `ru-RU` | `ru` |
| `zh-wy` | `wy` |
| `zh-TW` | `zh-TW` |
| `zh-cn` | 源语言，继续使用内置文件 |

## 配置

源码默认配置：

```json
{
  "translationApi": {
    "enabled": true,
    "baseUrl": "https://tr.bloret.net",
    "mode": "top_voted",
    "connectTimeout": 5,
    "readTimeout": 12
  }
}
```

设置 `enabled: false` 可关闭远程同步；本地语言仍正常使用。

## 清理缓存

关闭 Launcher 后删除用户数据目录中的 `lang/` 即可。下次启动或切换语言会重新下载；离线时仍可用安装包内置语言。
