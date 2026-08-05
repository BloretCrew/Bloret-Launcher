# Modrinth Modpack Format (.mrpack) 研究文档

> 权威实现参考：`/data/modrinth-code`（Modrinth App）  
> - 导出：`packages/app-lib/src/api/instance/export_mrpack.rs`  
> - 导入：`packages/app-lib/src/api/pack/install_mrpack.rs`  
> - 格式：`packages/app-lib/src/api/pack/install_from.rs`  
>
> Bloret 实现：`modules/mrpack_export.py`、`modules/mrpack_import.py`

## 概述

`.mrpack` 是 Modrinth 平台的整合包文件格式，本质是 **ZIP**，用于分发 Minecraft 模组整合包。

## 文件结构（官方）

```
example.mrpack (ZIP)
├── modrinth.index.json       # 必需：清单
├── overrides/                # 本地覆盖文件 → 解压到实例根目录
│   ├── config/...
│   ├── mods/本地未上架.jar
│   └── ...
├── client-overrides/         # 仅客户端覆盖
└── server-overrides/         # 仅服务端（App 哈希会扫；客户端导入主路径用 overrides + client-overrides）
```

### 重要更正

| 错误（旧文档 / 旧 Bloret 导出） | 正确（Modrinth App） |
|--------------------------------|----------------------|
| ZIP 内使用 `files/{path}` 嵌入全部内容 | **不使用** `files/` 目录 |
| index 中文件可不带 `downloads` | 远程内容必须有 `downloads` + 哈希；本地内容进 `overrides/` |
| 所有文件既进 index 又进 ZIP | **有 CDN 的只进 index；无 CDN 的只进 overrides** |

旧版 Bloret 导出的 `files/` 包与官方 App **不兼容**。新实现已改为 `overrides/` + 可选 `downloads` 分流。

## modrinth.index.json（PackFormat）

```json
{
  "formatVersion": 1,
  "game": "minecraft",
  "versionId": "1.0.0",
  "name": "我的整合包",
  "summary": "简介（可选）",
  "files": [
    {
      "path": "mods/example-mod.jar",
      "hashes": {
        "sha1": "...",
        "sha512": "..."
      },
      "env": {
        "client": "required",
        "server": "required"
      },
      "downloads": [
        "https://cdn.modrinth.com/data/.../....jar"
      ],
      "fileSize": 123456
    }
  ],
  "dependencies": {
    "minecraft": "1.20.1",
    "fabric-loader": "0.15.0"
  }
}
```

### 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `formatVersion` | int | ✓ | 当前为 `1` |
| `game` | string | ✓ | 必须为 `"minecraft"`，否则官方导入失败 |
| `versionId` | string | ✓ | 整合包版本号 |
| `name` | string | ✓ | 名称 |
| `summary` | string | ✗ | 简介 |
| `files` | array | ✓ | **可远程下载**的内容清单 |
| `dependencies` | object | ✓ | 游戏 / 加载器依赖 |

### files[] 字段

| 字段 | 说明 |
|------|------|
| `path` | 相对实例根路径（如 `mods/foo.jar`） |
| `hashes.sha1` | 官方下载校验主要用 sha1 |
| `hashes.sha512` | 推荐一并写出 |
| `downloads` | URL 列表（多镜像回退） |
| `fileSize` | 字节数 |
| `env.client` / `env.server` | `required` \| `optional` \| `unsupported` |

客户端安装时：`env.client == "unsupported"` 的文件会跳过。

### dependencies 常见键

- `minecraft`
- `fabric-loader` / `quilt-loader` / `forge` / `neoforge`

## 导出流程（对齐 App）

1. 扫描候选路径；默认勾选：`mods`、`datapacks`、`resourcepacks`、`shaderpacks`、`config`
2. 黑名单跳过：日志、`.fabric`、`natives`、缓存等
3. 对能反查到 Modrinth CDN 的文件：只写入 `files[]`（hashes + downloads），**不打进 ZIP**
4. 其余选中文件：写入 `overrides/{相对路径}`
5. 写入 `modrinth.index.json`

反查失败时降级为 overrides 内嵌（包可变大，但保证可装）。

## 导入流程（对齐 App）

1. 打开 ZIP，定位 `modrinth.index.json`
2. 校验 `game == "minecraft"`
3. 按 `dependencies` 安装 Minecraft + 加载器到目标版本目录
4. 并发/串行下载 `files[]`（多 URL、sha1 校验；跳过 client unsupported）
5. 解压 `overrides/` 与 `client-overrides/` 到实例根
6. （可选）兼容旧 Bloret 错误格式：若存在 ZIP 内 `files/` 也解压

## Bloret 代码入口

| 能力 | 模块 / 槽 |
|------|-----------|
| 导出 | `modules/mrpack_export.py` → `Backend.requestMrpackExport*` |
| 导入 | `modules/mrpack_import.py` → `Backend.importMrpack` / `add_mrpack` |
| UI | `qml/components/ExportMrpackDialog.qml`、`qml/pages/Download.qml` |

## 验收

1. 导出包结构：`modrinth.index.json` + `overrides/`，无错误 `files/` 根目录
2. 带 downloads 的条目不在 ZIP 中重复嵌入
3. Bloret 可导入标准 `.mrpack`（无需 `mrpack-install`）
4. 往返：Bloret 导出 → Bloret 导入，关键 mods/config 一致
