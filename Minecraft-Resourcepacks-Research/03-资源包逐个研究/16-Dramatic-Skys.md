# 16. Dramatic Skys Demo 1.5.3.36.4

## 根目录结构

```
Dramatic Skys Demo 1.5.3.36.4/
├── pack.mcmeta
├── pack.png
├── credit.txt
├── assets/
│   ├── celestial/
│   │   └── sky/
│   │       ├── dimensions.json
│   │       ├── variables.json
│   │       ├── overworld/
│   │       │   ├── sky.json
│   │       │   └── objects/
│   │       │       ├── sky1_stars.json
│   │       │       ├── sky2_mask_moon.json
│   │       │       ├── sky3_mask.json
│   │       │       ├── sky4_day.json
│   │       │       ├── sky5_night.json
│   │       │       ├── sky6_sunset.json
│   │       │       ├── sky7_sunrise.json
│   │       │       ├── sky8_sunflare_sunset.json
│   │       │       ├── sky9_sunflare_sunrise.json
│   │       │       ├── sun.json
│   │       │       └── moon.json
│   ├── fabricskyboxes/
│   │   └── sky/
│   │       ├── sky0_overworld.json
│   │       ├── sky1_stars.json
│   │       ├── sky2_day.json
│   │       ├── sky2_mask_moon.json
│   │       ├── sky3_mask.json
│   │       ├── sky3_night.json
│   │       ├── sky4_day.json
│   │       ├── sky4_sunset.json
│   │       ├── sky5_night.json
│   │       ├── sky5_sunrise.json
│   │       ├── sky6_sunflare_sunset.json
│   │       ├── sky6_sunset.json
│   │       ├── sky7_sunflare_sunrise.json
│   │       ├── sky7_sunrise.json
│   │       ├── sky8_sunflare_sunset.json
│   │       ├── sky8_sunmoon.json
│   │       ├── sky9_sunflare_sunrise.json
│   │       ├── sunmoon.json
│   │       └── press_f12_to_hide_this_text.json
│   ├── skybox/
│   │   ├── day.png
│   │   ├── night.png
│   │   ├── stars.png
│   │   ├── sun.png
│   │   ├── sunflare.png
│   │   ├── mask.png
│   │   └── mask_moon.png
│   └── minecraft/
│       ├── texts/
│       │   └── splashes.txt
│       ├── textures/
│       │   └── environment/
│       │       ├── clouds.png
│       │       ├── sun.png
│       │       ├── moon_phases.png
│       │       └── celestial/
│       │           ├── sun.png
│       │           └── moon/
│       │               ├── first_quarter.png
│       │               ├── full_moon.png
│       │               ├── new_moon.png
│       │               ├── third_quarter.png
│       │               ├── waning_crescent.png
│       │               ├── waning_gibbous.png
│       │               ├── waxing_crescent.png
│       │               └── waxing_gibbous.png
│       └── mcpatcher/
│           └── sky/world0/
│               ├── sky1.properties ~ sky9.properties
│       (optifine/ 目录与 mcpatcher/ 结构完全相同)
```

## 概述

Dramatic Skys（戏剧天空）是由 thebaum64 开发的天空替换资源包，当前版本为 Demo/Alpha 1.5.3.36.4。这是一个高度专业化的环境类资源包，专注于替换 Minecraft 主世界（Overworld）的天空盒渲染。它的独特之处在于同时支持 Fabric Sky Boxes、OptiFine / MCPatcher 和 Celestial 三种天空渲染系统，实现了广泛兼容性。

pack.mcmeta 中 pack_format 为 15（对应 Minecraft 1.20+），并通过 `supported_formats: [15, 1000]` 声明了对未来版本的向前兼容。

## 有三套天空系统 / 命名空间

本包最为突出的技术特征是同一套天空效果通过三套完全不同的系统实现：

### 1. Fabric Sky Boxes 命名空间 (`fabricskyboxes`)

这是 Fabric 模组环境下的天空渲染方案。使用 JSON 格式定义，采用 schemaVersion 2。每个 JSON 文件定义了一个天空层（layer），包含类型、纹理、混合模式、优先级、淡入淡出时间、旋转和天气条件。

关键定义举例：
- `sky0_overworld.json`: 类型为 "overworld"，priority=0，禁用原版太阳/月亮/星星显示，所有天气下始终开启。
- `sky1_stars.json`: 类型为 "single-sprite-square-textured"，使用 `skybox:stars.png`，alpha 混合，在夜晚时段淡入淡出（tick 13333~13666 淡入，22333~22666 淡出），绕 Z 轴旋转。
- `sky8_sunmoon.json`: 类型为 "monocolor"，priority=8，始终开启，重新启用原版的太阳和月亮显示。
- `press_f12_to_hide_this_text.json`: 有趣的小彩蛋，monocolor 类型，极高优先级 9999999，在所有天气下显示，用于提示玩家按 F12 隐藏叠加文字。

这些定义运用了 `blend` 混合模式（alpha、screen、add）以及 `rotation` 系统，包括绕 Y 轴和 Z 轴的独立旋转。

### 2. OptiFine / MCPatcher 命名空间 (`minecraft/mcpatcher/sky/` 和 `minecraft/optifine/sky/`)

这两个目录结构完全相同，每个 world0 文件夹包含 sky1.properties ~ sky9.properties 共 9 个配置文件。这种冗余设计确保了无论玩家使用 OptiFine 还是 MCPatcher，天空效果都能正常工作。

配置文件使用 properties 格式，示例：
```
source=skybox:stars.png
blend=alpha
startFadeIn=19:20
endFadeIn=19:40
startFadeOut=4:20
endFadeOut=4:40
rotate=true
axis=0.0 0.0 1.0
weather=clear
```

这里使用了游戏内时间格式（例如 19:20 表示夜晚开始），旋转轴设置为 Z 轴（axis=0.0 0.0 1.0）。

### 3. Celestial 系统 (`celestial` 命名空间)

这是一套自定义的、基于 JSON 的天空对象系统，可能对应某个特定的模组。它的结构更加精细复杂：

- `dimensions.json`: 声明适用的维度列表（仅 "overworld"）。
- `variables.json`: 定义了四个时间变量——sunset_fade、sunrise_fade、night_fade、day_fade。这些使用嵌套的 ifElse 条件表达式计算，基于 dayTime 值动态计算淡出/淡入因子。这是包中最为精细的技术实现。
- `overworld/sky.json`: 主配置文件，列出了 13 个 sky_objects 的引用顺序，并配置了环境参数（雾、云高度/颜色、虚空剔除距离）。
- `overworld/objects/`: 每个对象独立文件，包含顶点数据（vertex）、纹理坐标映射（uv_x/uv_y）、旋转参数和透明度控制。

Celestial 对象的顶点使用三维坐标定义，将纹理映射到天空盒立方体的各个面上。旋转系统使用 `degrees_x/y/z` 和 `base_degrees_x/y/z` 参数，结合 `skyAngle` 变量实现与游戏时间的同步旋转。透明度通过数学表达式动态计算，例如 `night_fade * (1-rainAlpha)` 实现了夜晚淡入和在雨天隐藏的效果。

## 纹理资源分析

包内包含丰富的自定义纹理：

### `assets/skybox/` 命名空间
- `day.png`: 白天天空球纹理，推测使用 screen 混合模式叠加。
- `night.png`: 夜晚天空球纹理，包含星空和银河效果。
- `stars.png`: 单独的高分辨率星星纹理，alpha 混合。
- `sun.png`: 太阳光晕纹理，screen 混合。
- `sunflare.png`: 日光镜头光晕。
- `mask.png` / `mask_moon.png`: 用于遮罩效果的灰度纹理。

### `assets/minecraft/textures/environment/`
- 替换了 vanilla 的 `sun.png`、`moon_phases.png`、`clouds.png`。
- `celestial/` 目录下包含完整的月相系统，有 8 张独立的高分辨率月相贴图（蛾眉月、凸月、满月、新月等），以及一张太阳贴图。这些纹理的特点是分辨率高于原版，色彩更丰富。

## 技术特点与创新

1. **三系统冗余兼容**：同一套天空效果通过 Fabric Sky Boxes、OptiFine/MCPatcher 和 Celestial 三套系统实现，覆盖了几乎所有流行的天空渲染模组。这种设计在资源包中极为罕见。

2. **动态变量系统**：Celestial 的 variables.json 使用数学表达式实现了昼夜循环的平滑过渡，这是对原版硬切换方式的重大改进。

3. **纹理混合技巧**：使用多层纹理叠加（stars + mask + day + night + sunflare + sun）构建出丰富的天空效果，每一层的混合模式（alpha/screen/add）和淡入淡出时序都精心设计。

4. **多层次优先级系统**：Fabric Sky Boxes 中通过 priority 值（0~99+）控制渲染顺序，确保正确的叠加层次。

5. **跨版本兼容**：通过设置极大的 max_format（1000），包声明了对未来 Minecraft 版本的兼容性。

## 总结

Dramatic Skys Demo 是一个技术含量极高的天空替换资源包。它的核心价值在于同时支持 Fabric、OptiFine、MCPatcher 和自定义 Celestial 四种天空渲染方案，是研究 Minecraft 天空渲染系统兼容性设计的绝佳案例。虽然当前版本标注为 Demo/Alpha，但其纹理质量和系统架构已相当成熟。包中还包含了一些幽默元素（如 F12 提示文本和自定义 Splash 文本），体现了作者的个性。
