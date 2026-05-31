# 21. Icons v.1.13.3
## 根目录结构
```
Icons v.1.13.3/
├── pack.mcmeta
├── pack.png
├── readme.md
├── readme.txt
├── respackopts.json5
├── 1.20.11-26.1/             # Overlay 目录
│   └── assets/
│       └── icons/
│           └── textures/
│               └── menu/
└── assets/
    ├── apothic_enchanting/
    │   ├── lang/
    │   └── lang_rpo/
    ├── barebones_icons/
    │   └── textures/
    │       ├── chat/
    │       ├── menu/
    │       └── tooltip/ (bee, firework, info, magic, map, music, smithing)
    ├── icons/ (核心)
    │   └── textures/
    │       ├── advancement/ (adventure, end, husbandry, nether, story)
    │       ├── chat/
    │       ├── gui/
    │       ├── menu/
    │       ├── respackopts/
    │       ├── splash/
    │       ├── statistic/
    │       ├── toast/
    │       └── tooltip/ (banner_pattern, bee, firework, info, magic, map, music, smithing, tropical_fish)
    ├── minecraft/
    │   ├── font/
    │   │   ├── default.json
    │   │   └── include/ (18个分类JSON文件)
    │   ├── lang/
    │   ├── lang_rpo/
    │   └── texts/
    ├── simple_icons/
    │   └── textures/ (chat, menu)
    ├── small_icons/
    │   └── textures/ (chat, menu)
    └── small_simple_icons/
        └── textures/ (chat, menu)
```

## 包定位
Icons（由 WeNAN Studios 开发）是一款专注于替换 Minecraft 各类符号和图标的资源包。它的核心理念是通过"字体系统 + 自定义纹理"的方式，将游戏中的各类文本符号（如聊天栏中的玩家名字前的图标、进度条、物品提示框中的图标、菜单按钮图标、统计界面的图标等）替换为精美的手绘风格小图标。

本包版本为 1.13.3，支持从 1.20.1 到最新版本的 Minecraft（pack_format 15 到 200），是一款通过 Overlay 系统实现跨版本兼容的先进资源包。

## 关键文件说明

### pack.mcmeta
采用 JSON 富文本描述格式，使用颜色代码显示版本号 "1.20 - 26.1"，并标明作者 WeNAN Studios。支持格式范围 [15, 200]，意味着兼容性极广。Overlay 系统将 "1.20.11-26.1" 目录应用于较高版本（min_format 75 起），以适配新版资源格式。

### respackopts.json5
这是 RespackOpts 模组的配置文件，允许玩家在游戏内自定义资源包的选项。说明 Icons 包支持可配置性，玩家可以选择启用/禁用某些图标类别。

### readme.md 和 readme.txt
Readme 文件提供了资源包的介绍、安装说明和作者信息。

## 资源内容结构

本包共有 1296 个文件，总大小约 324MB。其核心架构是字体系统驱动的图标替换。

### 字体系统（核心机制）
Icons 包的核心技术是基于 Minecraft 的"位图字体"（bitmap font）系统。通过修改 `assets/minecraft/font/default.json` 文件，将游戏中的 Unicode 字符映射到自定义图标纹理上。

**default.json** 通过 `include` 指令引入了 18 个分类定义文件：
- `advancement.json` - 进度/成就图标
- `banner_pattern.json` - 旗帜图案图标
- `bee.json` - 蜜蜂相关图标
- `firework.json` - 烟花相关图标
- `gui.json` - GUI 元素图标
- `hud.json` - HUD 图标
- `info.json` - 信息图标
- `language.json` - 语言选择图标
- `magic.json` - 魔法/附魔图标
- `map.json` - 地图相关图标
- `menus.json` - 菜单图标
- `music.json` - 音乐相关图标
- `respackopts.json` - 资源包选项图标
- `smithing.json` - 锻造相关图标
- `splash.json` - 加载画面提示文本
- `statistics.json` - 统计图标
- `toast.json` - 通知弹出图标
- `tropical_fish.json` - 热带鱼图标

### 多风格变体
包内包含四种不同的图标风格变体：
1. **icons/**（默认风格）- 完整的图标集，包含所有分类
2. **simple_icons/** - 简化版图标，线条更简洁
3. **small_icons/** - 小型图标，尺寸更小
4. **small_simple_icons/** - 小型简化图标，兼具两种特点
5. **barebones_icons/** - Bare Bones 风格变体，专为与 Bare Bones 资源包搭配使用设计

每种变体都包含 chat、menu 和 tooltip 等核心目录。

### 模组兼容
- **apothic_enchanting/** - 为 Apothic Enchanting 模组提供本地化和图标支持
- **minecraft/lang/** 和 **minecraft/lang_rpo/** - 语言文件

### Overlay 兼容层
**1.20.11-26.1/** 目录包含对新版 Minecraft（1.20.5+，对应 resource pack format 75+）的兼容内容。

### 关键纹理目录
| 目录 | 功能 |
|------|------|
| textures/advancement | 进度系统图标（冒险、末地、农牧、下界、故事五大类） |
| textures/chat | 聊天栏中的玩家头像前缀、系统消息图标 |
| textures/gui | GUI 组件图标 |
| textures/menu | 主菜单和暂停菜单的按钮图标 |
| textures/splash | 加载画面中的闪烁标语纹理 |
| textures/statistic | 统计界面的分类图标 |
| textures/toast | 成就通知和图鉴提示图标 |
| textures/tooltip | 物品提示框中的各类标记图标（旗帜图案、蜜蜂、烟花、信息、魔法、地图、音乐等） |

## 技术特点

1. **字体驱动的图标系统**：这是本包最核心的技术创新。相比于传统的纹理替换方式（直接替换 GUI 贴图），通过字体系统注入图标更加灵活——图标可以出现在任何支持文本渲染的位置（聊天栏、书与笔、命令方块等），而不局限于特定的 GUI 界面。

2. **多风格并行**：同时提供四种风格变体和一套兼容变体，玩家可以根据自己的喜好和搭配的资源包选择合适的版本。这种"包中包"的设计非常罕见，体现了对用户体验的细致考虑。

3. **分片式 JSON 管理**：使用 `include` 指令将不同类别的图标定义分散到 18 个独立的 JSON 文件中，而非塞入一个巨大的 default.json。这种模块化的管理方式大大提高了可维护性和可扩展性。

4. **RespackOpts 可配置**：支持 RespackOpts 模组，允许玩家在游戏内动态启用/禁用特定类别的图标。

5. **广泛的版本兼容性**：利用新版 Overlay 系统兼容 Minecraft 1.20 到最新版本，覆盖范围极其广泛。

6. **跨模组支持**：为 Apothic Enchanting 模组提供专门的图标支持，说明其生态开放性和扩展性。

7. **Bare Bones 兼容**：提供 barebones_icons 变体，专门适配 Bare Bones 资源包的极简风格，体现了良好的互操作性。

## 结论
Icons v.1.13.3 是 Minecraft 字体类资源包中的精品之作。它巧妙地利用游戏的字体系系统来注入自定义图标，实现了一种传统纹理替换无法达到的效果——图标可以出现在任何文本渲染的上下文中。这种方法论上的创新为资源包开发提供了新的思路。

WeNAN Studios 对细节的追求体现在多个方面：四种风格变体满足不同审美偏好、18 个分类文件实现模块化管理、RespackOpts 支持允许游戏内配置、专门的模组兼容层和资源包兼容变体。这些特性使得 Icons 不仅仅是一个"贴图包"，而是一个成熟的、可定制的图标系统。

本包最适合那些希望丰富游戏内图标表现的玩家——无论是聊天栏、进度界面、物品提示框还是菜单按钮，Icons 都以统一的美术风格提供了高质量的手绘图标。它与 Faithful 32x 等基础纹理包配合使用效果最佳，因为其字体系统的覆盖范围恰好能补充基础纹理包无法覆盖的文本符号区域。
