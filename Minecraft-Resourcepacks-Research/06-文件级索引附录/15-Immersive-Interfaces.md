# 15. Immersive Interfaces 文件索引

> 资源包全名：`Immersive Interfaces`（显示名含颜色代码 `§6Immersive§8_§6Interfaces§8`）
> 文件总数：约 460+ 个
> 类型：UI 纹理+着色器资源包，为容器 GUI 添加沉浸式背景效果（如信标光晕、酿造台窗帘等），支持多版本着色器适配

---

### 根目录

| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据，定义包格式版本与描述 |
| `pack.png` | 资源包封面图标 |
| `assets/` | 主资源目录 |
| `_1.20.2_shaders/` | 1.20.2 版本着色器适配 |
| `_1.21.1_shader_fix/` | 1.21.1 版本着色器修复 |
| `_1.21.2-.4_json_fix/` | 1.21.2~1.21.4 版本 JSON 修复 |
| `_1.21.6_shaders/` | 1.21.6 版本着色器适配 |
| `_26.1_shaders/` | 26.1 版本着色器适配 |

---

### 关键目录

| 路径 | 功能 |
|---|---|
| `assets/minecraft/` | Minecraft 命名空间 |
| `assets/minecraft/atlases/` | 纹理图集配置（blocks.json） |
| `assets/minecraft/font/` | 字体配置（default.json） |
| `assets/minecraft/lang/` | 多语言翻译文件（60+ 语言） |
| `assets/minecraft/optifine/` | OptiFine 兼容纹理 |
| `assets/minecraft/shaders/` | 着色器文件 |
| `assets/minecraft/textures/gui/` | GUI 纹理根目录 |
| `assets/minecraft/textures/gui/container/` | 容器 GUI 纹理（铁砧、信标、高炉、酿造台等 20+ 种） |
| `assets/minecraft/textures/gui/container/creative_inventory/` | 创造模式物品栏纹理（标签页、物品栏、搜索） |
| `assets/minecraft/textures/gui/interfaces/` | 自定义沉浸式界面效果纹理（信标光晕、窗帘、酿造指南等） |
| `assets/minecraft/textures/gui/sprites/` | GUI 精灵图 |
| `assets/minecraft/textures/item/` | 物品纹理 |
| `assets/minecraft/textures/mob_effect/` | 药水效果图标 |
| `_1.20.2_shaders/assets/minecraft/shaders/core/` | 1.20.2 着色器（position_tex_color、rendertype_text） |
| `_1.21.1_shader_fix/assets/minecraft/shaders/core/` | 1.21.1 着色器修复（rendertype_text.vsh） |
| `_1.21.2-.4_json_fix/assets/minecraft/shaders/core/` | 1.21.2~1.21.4 着色器 JSON 修复 |
| `_1.21.6_shaders/assets/minecraft/shaders/core/` | 1.21.6 着色器（position_tex_color、rendertype_text） |
| `_26.1_shaders/assets/minecraft/shaders/core/` | 26.1 着色器（rendertype_text.vsh） |

---

### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/minecraft/atlases/blocks.json` | 方块纹理图集配置 |
| `assets/minecraft/font/default.json` | 字体配置文件 |
| `assets/minecraft/lang/en_us.json` | 英语语言文件 |
| `assets/minecraft/lang/zh_cn.json` | 简体中文语言文件 |
| `assets/minecraft/textures/gui/container/anvil.png` | 铁砧沉浸式 GUI |
| `assets/minecraft/textures/gui/container/beacon.png` | 信标沉浸式 GUI |
| `assets/minecraft/textures/gui/container/brewing_stand.png` | 酿造台沉浸式 GUI |
| `assets/minecraft/textures/gui/container/crafting_table.png` | 工作台沉浸式 GUI |
| `assets/minecraft/textures/gui/container/enchanting_table.png` | 附魔台沉浸式 GUI |
| `assets/minecraft/textures/gui/container/furnace.png` | 熔炉沉浸式 GUI |
| `assets/minecraft/textures/gui/container/villager.png` | 村民交易沉浸式 GUI |
| `assets/minecraft/textures/gui/interfaces/beacon_curtain.png` | 信标窗帘效果纹理 |
| `assets/minecraft/textures/gui/interfaces/beacon_glow.png` | 信标光晕效果纹理 |
| `assets/minecraft/textures/gui/interfaces/brewing_guide.png` | 酿造指南效果纹理 |
| `assets/minecraft/textures/gui/book.png` | 书本界面沉浸式纹理 |
| `_1.20.2_shaders/assets/minecraft/shaders/core/position_tex_color.vsh` | 位置纹理颜色顶点着色器 |
| `_1.20.2_shaders/assets/minecraft/shaders/core/rendertype_text.fsh` | 文本渲染片段着色器 |
