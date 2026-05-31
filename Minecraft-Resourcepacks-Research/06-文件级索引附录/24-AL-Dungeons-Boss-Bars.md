### 24. `AL's Dungeons Boss Bars 1.0.2` 文件索引

**包类型**: Boss 血条样式替换（Minecraft Dungeons 风格）
**文件规模**: 约 160 个文件
**技术原理**: 通过自定义字体纹理和字体定义，将原版 Boss 血条替换为 Minecraft Dungeons 风格的图标血条，支持 100+ 语言

#### 根目录
| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据文件 |
| `pack.png` | 资源包封面图标（约 121KB） |

#### 关键目录
| 路径 | 功能 |
|---|---|
| `assets/minecraft/font/` | 字体定义（`default.json`，注册自定义 Boss 血条字符） |
| `assets/minecraft/lang/` | 多语言文件（100+ 语言 JSON，含 `deprecated.json` 兼容文件） |
| `assets/minecraft/textures/font/boss_bar/` | Boss 血条字体纹理（核心素材） |
| `assets/minecraft/textures/gui/sprites/boss_bar/` | Boss 血条 GUI 精灵图 |

#### 代表文件
| 路径 | 功能 |
|---|---|
| `assets/minecraft/font/default.json` | 字体定义文件（将 Unicode 私用区字符映射到 Boss 血条纹理） |
| `assets/minecraft/textures/font/boss_bar/` | Boss 血条图标纹理集（不同 Boss 的血条样式 PNG） |
| `assets/minecraft/textures/gui/sprites/boss_bar/` | Boss 血条 GUI 精灵图（血条背景、进度条等） |
| `assets/minecraft/lang/en_us.json` | 英语语言文件（含 Boss 名称映射） |
| `assets/minecraft/lang/zh_cn.json` | 简体中文语言文件 |
| `assets/minecraft/lang/deprecated.json` | 已弃用字符串兼容文件 |
