# 12. Default-Dark-Mode-1.21.11-2026.4.0

## 根目录结构

```
Default-Dark-Mode-1.21.11-2026.4.0/
├── pack.mcmeta
├── pack.png
└── assets/
    ├── minecraft/
    │   ├── optifine/color.properties
    │   ├── shaders/core/
    │   │   ├── rendertype_text.fsh
    │   │   └── rendertype_text_intensity.fsh
    │   └── textures/gui/
    │       ├── advancements/
    │       ├── container/          (20+ 容器 GUI 贴图)
    │       ├── sprites/            (GUI 精灵图)
    │       └── ... (book.png, recipe_book.png, etc.)
    ├── (60+ 模组命名空间)/
    │   ├── textures/gui/           (各模组 GUI 贴图)
    │   └── (README.md / LICENSE)
    └── ...
```

## 包定位

Default-Dark-Mode 是一个全面的大型 GUI 暗色模式资源包，由 nebulr 制作。它将 Minecraft 全部 GUI 界面以及 60 多个主流模组的界面从原版亮色调转换为统一的深色主题。目标用户是所有倾向于暗色 UI 的玩家，尤其是整合包玩家，因为该包同时覆盖了大量 Fabric/Forge 模组。

版本标识："1.21.11 - 2026.4.0" 表示支持 pack_format 63~75（1.21.2 ~ 1.21.11+）。

## 关键文件说明

### pack.mcmeta

- **路径**: `Default-Dark-Mode-1.21.11-2026.4.0/pack.mcmeta`
- **pack_format**: 63
- **supported_formats**: min_inclusive=63, max_inclusive=75
- **描述**: "Welcome to the dark side! by nebulr - 1.21.11 - 2026.4.0"

这是一个非常简洁的 pack.mcmeta，没有使用 overlay 系统，意味着所有资源直接放在 assets 目录下。

### optifine/color.properties

- **路径**: `assets/minecraft/optifine/color.properties`
- 内容：
```
screen.loading=202020
screen.loading.bar=202020
screen.loading.outline=4e4e4e
screen.loading.progress=4e4e4e
```
- **用途**: 将 Minecraft 加载屏幕的默认浅色背景改为深色（#202020），加载进度条和轮廓也变深。这是 OptiFine/Optifabric 特性，非原版功能。

### rendertype_text.fsh / rendertype_text_intensity.fsh

- **路径**: `assets/minecraft/shaders/core/`
- **用途**: 修改文本渲染着色器，将特定深灰色（#3F3F3F）文本替换为浅灰色（#AAAAAA）

**关键代码片段**：
```glsl
if (color.r > 0.2479 && color.r < 0.2481
    && color.g > 0.2479 && color.g < 0.2481
    && color.b > 0.2479 && color.b < 0.2481) {
    color = vec4(0.6667, 0.6667, 0.6667, 1.0);
}
```

- RGB 0.2479 ~ 0.2481 对应十六进制 #3F3F3F（原版深灰色文字）
- 替换为 RGB 0.6667 对应十六进制 #AAAAAA（浅灰色）
- **核心作用**: 在暗色 GUI 背景上，原本难以看清的深灰文字被提升为更亮的灰色，确保可读性。

两个着色器分别对应不同的文本渲染管线：`rendertype_text` 用于标准文本，`rendertype_text_intensity` 用于强度纹理（如发光文字效果）。

## 资源内容结构

该资源包完全由 GUI 纹理贴图组成，目录结构遵循 Minecraft 资源包标准：

```
assets/
├── <命名空间>/
│   ├── textures/gui/
│   │   ├── container/         (容器界面背景)
│   │   ├── sprites/           (UI 精灵图 - 1.21+)
│   │   └── ...                (其他 GUI 元素)
│   ├── README.md              (许可声明)
│   └── LICENSE                (许可协议)
```

## 关键目录功能

### 模组支持体系

该包支持超过 60 个模组的暗色化 GUI，覆盖范围极广：

**存储/背包类**：
- `sophisticatedbackpacks`、`sophisticatedcore` - 精妙背包
- `travelersbackpack` - 旅行者背包
- `usefulbackpacks` - 实用背包
- `inventorio`、`inventoryhud` - 背包增强
- `ironchest`、`expandedstorage` - 铁箱子/扩展存储
- `shulkerboxtooltip`、`shulkertooltip` - 潜影盒预览

**科技类**：
- `ae2`、`ae2wtlib` - AE2 应用能源
- `toms_storage` - Tom 存储

**农业/食物类**：
- `farmersdelight`、`farmersrespite` - 农夫乐事
- `brewinandchewin`、`expandeddelight`、`vinery` - 扩展食物/酿酒

**魔法/附魔类**：
- `easymagic`、`enchantinginfuser` - 附魔增强
- `transmog` - 幻化

**生物群系/世界类**：
- `betterend`、`byg`、`galosphere`、`the_bumblezone`、`twilightforest`、`paradise_lost`

**信息显示类**：
- `jei`、`emi`、`roughlyenoughitems`、`jeresources` - 物品管理器
- `inventoryprofilesnext`、`inventorysorter` - 背包整理

**装饰/功能类**：
- `adorn`、`charm`、`frame`、`lovely_snails`、`origins`

**UI 库**：
- `cloth-config2`、`owo`、`libgui`、`modmenu`、`languagereload`

### 原版 Minecraft GUI 覆盖

`assets/minecraft/textures/gui/` 目录覆盖了所有原版 GUI 组件：

- **container/**: 铁砧、信标、高炉、酿造台、制图台、合成器、工作台、附魔台、熔炉、砂轮、漏斗、马匹、物品栏、讲台、织布机、锻造台、烟熏炉、切石机、村民交易等
- **advancements/**: 进度界面窗口
- **sprites/**: 1.21+ 的新版精灵图系统，包含容器/状态效果等 sprite
- **book.png**: 书本界面
- **recipe_book.png**: 配方书界面
- **demo_background.png**: 演示模式背景

## 技术特点

1. **纯纹理替换，无 Overlay 系统**：整个包没有使用 overlay，所有资源都通过目录覆盖。pack_format 63 直接对应 1.21.2+。

2. **着色器辅助的文本颜色修正**：通过修改 rendertype_text.fsh 和 rendertype_text_intensity.fsh，将暗色 GUI 中不可读的深灰色文字（#3F3F3F）自动提升为浅灰色（#AAAAAA）。这是一种轻量级的 GPU 修补方案，避免修改语言文件。

3. **OptiFine 颜色属性配置**：使用 `optifine/color.properties` 修改加载屏幕颜色为深色。这是 OptiFine/OptiFabric 的专有特性。

4. **全面模组兼容**：支持 60+ 模组的 GUI 暗色化，每个模组都有独立的命名空间目录。许多模组资产同时附带了 README.md 和 LICENSE 文件，表明作者尊重原始模组的许可证要求。

5. **Sprites 系统支持**：包内包含 `gui/sprites/` 目录，覆盖了 1.21+ 引入的新精灵图系统，而不仅限于旧版 `gui/container/` 直接贴图。

## 结论

Default-Dark-Mode 是一个规模极其庞大（260+ 子目录、覆盖 60+ 模组）的 GUI 暗色模式资源包。其核心工作是纹理替换，但巧妙结合了着色器修改和 OptiFine 配置来实现完整的暗色体验。该包展现了现代 Minecraft 资源包开发中模组兼容性的设计模式——每个模组作为独立的命名空间处理，配合许可证文件保持合规性。对于整合包作者和暗色 UI 爱好者来说，这是一个几乎必备的资源包。
