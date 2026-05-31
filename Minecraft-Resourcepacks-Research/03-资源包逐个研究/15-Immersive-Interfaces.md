# 15. Immersive Interfaces

## 根目录结构
```text
_1.20.2_shaders/
_1.21.1_shader_fix/
_1.21.2-.4_json_fix/
_1.21.6_shaders/
_26.1_shaders/
assets/
pack.mcmeta
pack.png
```

## 包定位
Immersive Interfaces 是由作者 Shrimpsnail 创作的完整 GUI 大修资源包，目前处于 Beta V0.8.2 阶段。该包的定位非常明确——对 Minecraft 的整个图形用户界面进行全面的视觉重设计，涵盖容器界面、信标界面、村民交易界面、命令方块界面、创造模式物品栏、快捷栏 HUD 等几乎所有游戏内 UI 元素。

与传统的 GUI 资源包不同，Immersive Interfaces 不仅仅替换纹理贴图，它还深度利用了 Minecraft 的着色器（Shader）系统来实现更复杂的界面效果。通过自定义顶点着色器和片段着色器，该包能够在渲染层面实现传统资源包无法完成的界面变换，例如动态动画、位置偏移、尺寸调整和条件性显示。

pack_format 为 15（对应 Minecraft 1.20.x），并使用 `supported_formats` 声明兼容范围为 [15, 84]，覆盖了从 1.20 到未来多个版本。更重要的是，该包大量使用了 Minecraft 的 overlay 系统，针对不同 Minecraft 版本提供了不同的着色器变体，确保在各个版本中都能正确渲染。

该包共包含 468 个文件，是本次研究样本中规模较大、技术复杂度较高的 GUI 资源包之一。

## 关键文件说明

### pack.mcmeta
```json
{
    "pack": {
        "description": "Complete GUI overhaul\n§cBeta V0.8.2 §8| By Shrimpsnail",
        "pack_format": 15,
        "supported_formats": [15, 84],
        "min_format": 15,
        "max_format": 84
    },
    "overlays": {
        "entries": [
            {
                "directory": "_1.21_lang",
                "formats": [18, 100],
                "min_format": 18,
                "max_format": 100
            },
            {
                "directory": "_1.20.2_shaders",
                "formats": [42, 56],
                "min_format": 42,
                "max_format": 56
            },
            {
                "directory": "_1.21.1_shader_fix",
                "formats": [34, 41],
                "min_format": 34,
                "max_format": 41
            },
            {
                "directory": "_1.21.2-.4_json_fix",
                "formats": [42, 46],
                "min_format": 42,
                "max_format": 46
            },
            {
                "directory": "_1.21.5_shader_fix",
                "formats": [54, 56],
                "min_format": 54,
                "max_format": 56
            },
            {
                "directory": "_1.21.6_shaders",
                "formats": [57, 100],
                "min_format": 57,
                "max_format": 100
            },
            {
                "directory": "_26.1_shaders",
                "formats": [84, 100],
                "min_format": 84,
                "max_format": 100
            }
        ]
    },
    "language": {
        "aa_dev": {
            "name": "Developer§a",
            "region": "Immersive Interfaces"
        }
    }
}
```

该文件展示了资源包系统中较为高级的配置技术：

1. **Overlay 系统**：定义了 7 个不同的 overlay 目录，每个目录针对特定的 Minecraft 版本范围提供不同的资源覆盖。这是处理跨版本兼容性的关键机制——不同版本的 Minecraft 使用不同的着色器语法和 JSON 格式，通过 overlay 可以为每个版本范围提供正确的资源。

2. **版本范围覆盖**：
   - `_1.21_lang`：针对 pack_format 18-100 的语言文件覆盖
   - `_1.20.2_shaders`：针对 pack_format 42-56 的着色器
   - `_1.21.1_shader_fix`：针对 pack_format 34-41 的着色器修复
   - `_1.21.2-.4_json_fix`：针对 pack_format 42-46 的 JSON 格式修复
   - `_1.21.5_shader_fix`：针对 pack_format 54-56 的着色器修复
   - `_1.21.6_shaders`：针对 pack_format 57-100 的着色器
   - `_26.1_shaders`：针对 pack_format 84-100 的着色器

3. **自定义语言条目**：通过 `language` 字段注册了一个自定义语言 `aa_dev`（Developer），名称为 "Developer"，区域为 "Immersive Interfaces"。这可能是用于开发调试的特殊语言选项。

### assets/minecraft/shaders/ 着色器目录
这是该包最核心的技术目录，包含自定义着色器文件：

**rendertype_text.json**：定义了文本渲染着色器的配置，包含混合模式（alpha blending）、顶点/片段着色器引用、属性列表（Position, Color, UV0, UV2）和 uniform 变量（ModelViewMat, ProjMat, GameTime 等）。

**rendertype_text.vsh**：顶点着色器主文件，导入了 `interfaces.glsl` 库，通过 `interfaces_text()` 函数处理文本渲染的位置和颜色变换。

**interfaces.glsl**：该包的核心着色器库文件，包含约 380 行 GLSL 代码，实现了完整的界面变换逻辑。主要功能包括：
- `Data` 结构体：封装位置、UV 坐标和颜色数据
- `posCheck()` 系列函数：基于屏幕坐标的位置检测，用于识别特定 UI 元素
- `interfaces()` 函数：处理纹理精灵的位置和 UV 变换
- `interfaces_text()` 函数：处理文本元素的位置和颜色变换
- 支持多种容器类型的位置/尺寸调整（箱子、信标、村民交易、命令方块、创造模式等）

**position_tex.json / position_tex_old.vsh / position_tex_old.fsh**：纹理位置着色器，用于处理纹理渲染管线。

**shaders/include/interfaces.glsl**：着色器包含文件，供其他着色器引用。

### assets/minecraft/textures/gui/ 纹理目录
包含大量的 GUI 纹理替换文件：

**container/**：容器界面纹理（anvil.png, beacon.png, crafting_table.png 等）

**interfaces/**：自定义界面元素纹理，包括：
- `chests/`：各种箱子界面（chest.png, ender_chest.png, large_chest.png, barrel.png 等）
- `slots/`：物品槽位纹理
- `villager/`：村民交易界面元素
- 命令方块界面（command_00-11.png, chain_command_*.png, repeat_command_*.png）
- 信标界面元素（beacon_curtain.png, beacon_glow.png）
- 其他容器界面（dispenser_block.png, dropper_block.png, hopper_minecart.png）

**sprites/**：新版精灵系统纹理，包含 174 个文件，覆盖：
- `container/`：所有容器类型的精灵（anvil, beacon, blast_furnace, brewing_stand, bundle, cartography_table, crafter, creative_inventory, enchanting_table, furnace, horse, loom, slot, smoker, stonecutter, villager）
- `hud/`：HUD 元素精灵
- `recipe_book/`：配方书精灵
- `tooltip/`：工具提示精灵
- `widget/`：控件精灵

**book.png**：书本界面纹理

### assets/minecraft/lang/ 语言文件目录
包含 135 个语言文件，覆盖了 Minecraft 支持的几乎所有语言。这些语言文件用于替换游戏界面中的文本内容，使得 GUI 的视觉改造与文本内容保持一致。语言文件的广泛覆盖表明该包是一个国际化的资源包，支持全球不同语言的玩家使用。

### assets/minecraft/optifine/ OptiFine 兼容目录
包含 OptiFine 特定的资源：
- `gui/container/shulkers/`：16 种颜色的潜影盒界面纹理和属性文件（black, blue, brown, cyan, green, grey, light_blue, light_grey, lime, magenta, orange, pink, purple, red, white, yellow）
- 每种颜色包含一个 `.png` 纹理和一个 `.properties` 配置文件

这是为了兼容 OptiFine 模组的潜影盒自定义界面功能——OptiFine 允许资源包为不同颜色的潜影盒提供不同的界面纹理。

### assets/minecraft/atlases/blocks.json
```json
{
    "sources": [
        {
            "type": "single",
            "resource": "block/missingno",
            "sprite": "missingo"
        }
    ]
}
```

该文件配置了方块纹理图集，添加了一个 `missingno` 精灵资源。这可能是为了处理纹理缺失时的回退显示，或者是着色器系统需要的一个占位纹理。

## 资源内容结构
```text
_1.20.2_shaders/                    ← 1.20.2 版本专用着色器
  assets/minecraft/shaders/core/
    position_tex_color.json/vsh
    rendertype_text.fsh/vsh
_1.21.1_shader_fix/                 ← 1.21.1 着色器修复
  assets/minecraft/shaders/core/
    rendertype_text.vsh
_1.21.2-.4_json_fix/                ← 1.21.2-1.21.4 JSON 修复
  assets/minecraft/shaders/core/
    position_tex.json
    rendertype_text.json
_1.21.6_shaders/                    ← 1.21.6 版本专用着色器
  assets/minecraft/shaders/core/
    position_tex_color.fsh/vsh
    rendertype_text.vsh
_26.1_shaders/                      ← 26.1 版本专用着色器
  assets/minecraft/shaders/core/
    rendertype_text.vsh
assets/
  minecraft/
    atlases/
      blocks.json                   ← 纹理图集配置
    font/
      default.json                  ← 自定义字体定义
    lang/
      135 个语言文件                 ← 多语言支持
    optifine/
      gui/container/shulkers/       ← OptiFine 潜影盒界面
    shaders/
      core/
        position_tex.json
        position_tex_old.fsh/vsh
        rendertype_text.json
        rendertype_text.vsh
      include/
        interfaces.glsl             ← 核心着色器库
    textures/
      gui/
        book.png
        container/                  ← 容器界面纹理
        interfaces/                 ← 自定义界面元素
          chests/                   ← 箱子界面变体
          slots/                    ← 物品槽位
          villager/                 ← 村民交易界面
        sprites/                    ← 新版精灵系统纹理 (174 个文件)
          container/                ← 容器精灵
          hud/                      ← HUD 精灵
          recipe_book/              ← 配方书精灵
          tooltip/                  ← 工具提示精灵
          widget/                   ← 控件精灵
      item/                         ← 物品纹理
      mob_effect/                   ← 状态效果图标
pack.mcmeta
pack.png
```

## 关键目录功能

### shaders/core/ 着色器核心目录
这是该包区别于普通 GUI 资源包的核心技术目录。通过自定义着色器，该包能够实现传统资源包无法完成的界面变换效果：

1. **位置变换**：通过修改顶点着色器中的位置计算，实现 UI 元素的位移、缩放和重排
2. **UV 映射调整**：动态修改纹理坐标，实现动画效果和条件性纹理显示
3. **颜色处理**：通过颜色混合和条件性着色，实现特殊的视觉效果
4. **条件渲染**：基于屏幕坐标检测特定 UI 元素，实现针对性的界面修改

### shaders/include/interfaces.glsl 核心着色器库
这是整个包最核心的技术文件，约 380 行 GLSL 代码，实现了完整的界面变换逻辑：

- **位置检测系统**：`posCheck()` 系列函数通过计算屏幕坐标和顶点位置，识别特定的 UI 元素（如信标按钮、村民交易槽位等）
- **多容器支持**：支持箱子、信标、村民交易、命令方块、创造模式、配方书、马匹界面等多种容器类型
- **动画系统**：使用 `GameTime` uniform 变量实现基于时间的动画效果（如切石机动画、村民交易界面动画）
- **精灵替换**：通过 UV 坐标映射，将原版纹理替换为自定义精灵

### textures/gui/interfaces/ 自定义界面元素目录
该目录包含大量自定义界面元素纹理，用于配合着色器实现完整的界面改造：

- **chests/**：10 种箱子界面变体（普通箱子、末影箱、大箱子、矿车箱子、船箱子等）
- **slots/**：物品槽位纹理
- **villager/**：村民交易界面元素
- 命令方块界面（普通、连锁、重复三种类型，各有四种状态）
- 信标界面元素（窗帘、光晕效果）
- 其他容器界面

### textures/gui/sprites/ 新版精灵系统目录
包含 174 个精灵文件，覆盖了 Minecraft 1.20+ 引入的新版精灵系统中的所有 GUI 元素。这些精灵文件按功能分类：

- **container/**：所有容器类型的精灵纹理
- **hud/**：HUD 元素精灵
- **recipe_book/**：配方书精灵
- **tooltip/**：工具提示精灵
- **widget/**：控件精灵（按钮、滑条等）

### lang/ 多语言目录
135 个语言文件覆盖了 Minecraft 支持的所有语言，包括：
- 主要语言：en_us, zh_cn, zh_tw, ja_jp, ko_kr, de_de, fr_fr, es_es, pt_br, ru_ru 等
- 地区变体：en_gb, en_au, en_ca, pt_pt, zh_hk 等
- 少数语言：ast_es, ba_ru, fur_it, lmo, szl 等
- 虚构语言：qya_aa（昆雅语）、tlh_aa（克林贡语）等
- 开发语言：aa_dev（Developer）

### optifine/ OptiFine 兼容目录
包含 16 种颜色的潜影盒界面纹理和配置文件，用于兼容 OptiFine 模组的潜影盒自定义功能。每种颜色（black, blue, brown, cyan, green, grey, light_blue, light_grey, lime, magenta, orange, pink, purple, red, white, yellow）都有独立的 `.png` 纹理和 `.properties` 配置文件。

## 技术特点

1. **着色器驱动的界面改造**：这是该包最显著的技术特点。与传统 GUI 资源包仅替换纹理不同，Immersive Interfaces 通过自定义着色器在渲染层面实现界面变换。这种方法的优势在于可以实现更复杂的界面效果（如动态动画、条件性显示、精确的位置调整），但缺点是依赖于 Minecraft 的着色器系统，可能与某些模组不兼容。

2. **Overlay 系统的深度使用**：该包定义了 7 个 overlay 目录，针对不同 Minecraft 版本提供不同的着色器变体。这是处理跨版本兼容性的高级技术——不同版本的 Minecraft 使用不同的着色器语法和 JSON 格式，通过 overlay 可以为每个版本范围提供正确的资源。

3. **屏幕坐标检测系统**：`interfaces.glsl` 中的 `posCheck()` 系列函数通过计算屏幕坐标和顶点位置，实现了精确的 UI 元素识别。这种技术允许着色器针对特定的界面元素进行定制化处理，而不仅仅是全局性的视觉效果。

4. **多容器统一处理**：通过着色器中的条件分支，该包能够统一处理多种容器类型（箱子、信标、村民交易、命令方块等），每种容器都有独立的位置/尺寸/动画配置。

5. **OptiFine 兼容性**：通过 `optifine/` 目录提供潜影盒界面的自定义纹理，展示了如何同时兼容原版 Minecraft 和 OptiFine 模组的资源加载机制。

6. **国际化支持**：135 个语言文件的广泛覆盖表明该包是一个国际化的资源包，支持全球不同语言的玩家使用。

7. **新版精灵系统适配**：174 个精灵文件覆盖了 Minecraft 1.20+ 引入的新版精灵系统，表明该包积极适配 Minecraft 的最新 GUI 渲染机制。

8. **字体系统扩展**：通过 `font/default.json` 定义了大量自定义字体字符（使用 Unicode 私用区），映射到各种自定义界面元素纹理。这是实现复杂界面布局的关键技术——通过字体字符可以在文本渲染层插入自定义图形元素。

## 结论
Immersive Interfaces 是一个技术复杂度极高的 GUI 大修资源包，其核心创新在于：

1. **着色器驱动的界面改造**：通过自定义 GLSL 着色器在渲染层面实现界面变换，突破了传统资源包仅能替换纹理的限制。

2. **精确的 UI 元素识别**：基于屏幕坐标的位置检测系统，能够针对特定界面元素进行定制化处理。

3. **深度版本兼容**：通过 overlay 系统为不同 Minecraft 版本提供正确的着色器变体，展示了资源包跨版本兼容的高级技术。

4. **全面的界面覆盖**：从容器界面到 HUD 元素，从信标到命令方块，几乎覆盖了 Minecraft 的所有 GUI 元素。

该包目前处于 Beta V0.8.2 阶段，仍有部分界面尚未完全实现。但从已实现的内容来看，它展示了资源包系统在 GUI 改造方面的强大潜力——通过着色器技术，资源包不仅能够替换纹理，还能在渲染层面实现复杂的界面变换和动画效果。

对于资源包开发者而言，Immersive Interfaces 是学习着色器驱动 GUI 改造的极佳参考案例，特别是其 `interfaces.glsl` 文件中的位置检测系统和多容器处理逻辑，展示了如何在不修改游戏代码的情况下实现深度的界面定制。同时，该包的 overlay 系统配置也为跨版本兼容性处理提供了实用的参考模式。
