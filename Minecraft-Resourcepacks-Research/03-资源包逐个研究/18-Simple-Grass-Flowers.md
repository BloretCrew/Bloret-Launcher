# 18. Simple Grass Flowers v1.9.6

## 根目录结构

```
Simple Grass Flowers v1.9.6/
├── pack.mcmeta
├── pack.png
├── Cat.png
├── Read Me.txt
├── assets/
│   └── minecraft/
│       ├── blockstates/
│       │   ├── crimson_nylium.json
│       │   ├── grass_block.json
│       │   ├── mycelium.json
│       │   ├── podzol.json
│       │   └── warped_nylium.json
│       ├── models/
│       │   └── block/
│       │       ├── grass_block_decor.json
│       │       ├── grass_block/
│       │       │   ├── grass_block.json
│       │       │   ├── grass_block_clover.json
│       │       │   ├── grass_block_clover_small.json
│       │       │   ├── grass_block_flower_big.json
│       │       │   ├── grass_block_flower_small.json
│       │       │   └── grass_block_rock.json
│       │       ├── mycelium/
│       │       │   ├── mycelium.json
│       │       │   ├── mycelium_clover.json
│       │       │   ├── mycelium_clover_small.json
│       │       │   ├── mycelium_mushroom_brown.json
│       │       │   └── mycelium_mushroom_red.json
│       │       ├── podzol/
│       │       │   ├── podzol.json
│       │       │   ├── podzol_clover.json
│       │       │   ├── podzol_clover_small.json
│       │       │   ├── podzol_flower_big.json
│       │       │   ├── podzol_flower_small.json
│       │       │   └── podzol_rock.json
│       │       ├── crimson_nylium/
│       │       │   ├── crimson_nylium.json
│       │       │   ├── crimson_nylium_clover.json
│       │       │   ├── crimson_nylium_clover_small.json
│       │       │   ├── crimson_nylium_wart.json
│       │       │   └── crimson_nylium_wart_small.json
│       │       └── warped_nylium/
│       │           ├── warped_nylium.json
│       │           ├── warped_nylium_clover.json
│       │           ├── warped_nylium_clover_small.json
│       │           ├── warped_nylium_wart.json
│       │           └── warped_nylium_wart_small.json
│       └── textures/
│           ├── block/
│           │   ├── wildflowers.png
│           │   ├── grass_block/
│           │   │   ├── grass_block_top_clover.png
│           │   │   ├── grass_block_top_clover_small.png
│           │   │   ├── grass_block_top_flower_big.png
│           │   │   ├── grass_block_top_flower_small.png
│           │   │   └── grass_block_top_rock.png
│           │   ├── mycelium/
│           │   │   ├── mycelium_top_clover.png
│           │   │   ├── mycelium_top_clover_small.png
│           │   │   ├── mycelium_top_mushroom_brown.png
│           │   │   └── mycelium_top_red_mushroom.png
│           │   ├── podzol/
│           │   │   ├── podzol_top_clover.png
│           │   │   ├── podzol_top_clover_small.png
│           │   │   ├── podzol_top_flower_big.png
│           │   │   ├── podzol_top_flower_small.png
│           │   │   └── podzol_top_rock.png
│           │   ├── crimson_nylium/
│           │   │   ├── crimson_nylium_clover.png
│           │   │   ├── crimson_nylium_clover_small.png
│           │   │   ├── crimson_nylium_wart.png
│           │   │   └── crimson_nylium_wart_small.png
│           │   └── warped_nylium/
│           │       ├── warped_nylium_clover.png
│           │       ├── warped_nylium_clover_small.png
│           │       ├── warped_nylium_wart.png
│           │       └── warped_nylium_wart_small.png
│           └── colormap/
│               ├── foliage.png
│               └── grass.png
```

## 概述

Simple Grass Flowers（简洁草地花朵）是由 2DWisp 开发的专注型环境美化资源包，版本 v1.9.6。pack.mcmeta 的 pack_format 为 15（对应 Minecraft 1.20+），supported_formats 为 [15, 1000]。描述文字使用了 JSON text component 格式，以绿色 "#6fe031" 显示标题 "Grass > Flowery Grass"。

这是一个**极度专注**的资源包——它的全部功能只有一个：为草地类方块（草方块、菌丝、灰化土、绯红菌岩、诡异菌岩）的顶面添加随机的小装饰物，如三叶草、小石子、花朵和蘑菇。包内仅包含 62 个文件，是所有 4 个包中规模最小的，但功能明确，执行出色。

## 核心机制：加权随机变体系统

Simple Grass Flowers 的核心技术是 Minecraft 的 blockstate `variants` 加权随机系统。以 `grass_block.json` 为例：

```json
{
  "variants": {
    "snowy=false": [
      {"model": "block/grass_block/grass_block", "weight": 120},
      {"model": "block/grass_block/grass_block_clover", "weight": 8},
      {"model": "block/grass_block/grass_block_clover_small", "weight": 12},
      {"model": "block/grass_block/grass_block_rock", "weight": 1},
      {"model": "block/grass_block/grass_block_flower_small", "weight": 4},
      {"model": "block/grass_block/grass_block_flower_big", "weight": 2}
    ],
    "snowy=true": { "model": "block/grass_block_snow" }
  }
}
```

每个模型都有权重（weight）值，Minecraft 会根据权重随机选择显示的模型。每个变体还包含 4 个旋转方向（0 / 90 / 180 / 270 度），通过 y 参数控制。总计 24 种可能的视觉效果（6 种变体 x 4 个方向），概率分布为：

| 效果 | 权重（合计4方向） | 出现概率 |
|---|---|---|
| 基本草地（无装饰） | 480 | ~81.6% |
| 小三叶草 | 48 | ~8.2% |
| 大三叶草 | 32 | ~5.4% |
| 小花 | 16 | ~2.7% |
| 大花 | 8 | ~1.4% |
| 小石子 | 4 | ~0.7% |

这种设计使草地看起来自然多变，大部分时候是普通草地，偶尔点缀一些小装饰，视觉效果丰富但不突兀。

## 五种草地类型的变体

### 草方块 (Grass Block)
- 基础模型、大三叶草、小三叶草、小石子、小花、大花（共 6 种）

### 菌丝 (Mycelium)
- 基础模型、大三叶草、小三叶草、棕色蘑菇、红色蘑菇（共 5 种）

### 灰化土 (Podzol)
- 基础模型、大三叶草、小三叶草、小石子、小花、大花（共 6 种）

### 绯红菌岩 (Crimson Nylium)
- 基础模型、大三叶草、小三叶草、大疣、小疣（共 5 种）

### 诡异菌岩 (Warped Nylium)
- 基础模型、大三叶草、小三叶草、大疣、小疣（共 5 种）

## 模型层级设计

Simple Grass Flowers 使用了巧妙的两层模型系统：

### 第一层：基础草地模型 (`grass_block/grass_block.json`)

这是一个"常规"草地模型，包含两个 element：
1. 底基层（16x16x16）：使用 dirt（底部）、grass_block_top（顶部，tintindex=0 支持生物群系着色）和 grass_block_side（侧面）纹理。
2. 侧面覆盖层：使用 grass_block_side_overlay 纹理叠加在侧面，同样使用 tintindex=0 实现生物群系着色。

### 第二层：装饰层模型 (`grass_block_decor.json`)

这是一个特殊的"装饰"模型，由 JamieCubed 创建（在 credit 中标注）。它在基础模型之上增加了第三个 element：
- 一个位于 y=16.075 的极薄平面（0 像素厚），作为装饰物（decor）的载体。
- 使用 rotation 系统旋转原点至 (0, -0.25, 0)。

这个装饰层模型被所有带装饰的变体继承使用。例如 `grass_block_flower_big.json`：
```json
{
  "parent": "minecraft:block/grass_block_decor",
  "textures": {
    "decor": "minecraft:block/grass_block/grass_block_top_flower_big"
  }
}
```

它继承父模型的几何结构，仅替换 decor 纹理为具体装饰图案。这是 Minecraft 模型系统中 parent-child 继承机制的优雅运用。

## 纹理特点

装饰纹理都是 16x16 像素的 PNG 文件，与标准 Minecraft 分辨率一致。图案包括：

- **三叶草 (Clover)**: 绿色的小叶片图案
- **花朵 (Flower)**: 彩色的小花图案
- **石子 (Rock)**: 灰色的小石子
- **蘑菇 (Mushroom)**: 棕色/红色的蘑菇
- **疣 (Wart)**: 下界疣状装饰

纹理设计简单明快，与草地的绿色顶面纹理融合自然。

## 生态系统兼容

包内还包含了 `colormap/foliage.png` 和 `colormap/grass.png`，确保装饰物在不同生物群系中能正确匹配颜色变化（如沼泽中的灰绿色草地、丛林中的鲜绿色草地等）。这是通过模型的 `tintindex: 0` 标记实现的，Minecraft 会根据生物群系着色图自动为带有 tintindex 的面着色。

## 设计理念与局限性

Simple Grass Flowers 的设计理念是"less is more"。它不做任何其他改动——不改变天空、不改变生物、不改变物品。它的唯一目标是让地表看起来更生动有趣。这种极简主义风格使它易于与其他资源包兼容叠加使用。

需要注意的是，本包不包含 textures/block/ 目录下的基础纹理文件（如 grass_block_top.png、grass_block_side.png 等）。这意味着它必须与其他提供基础纹理的资源包配合使用，或者依赖于原版纹理。它只提供装饰层纹理和模型配置。

## 总结

Simple Grass Flowers 是"小而美"资源包的典范。它使用 Minecraft 原版的加权随机模型变体系统、模型继承（parent-child）和 tintindex 生物群系着色三大机制，以极少的文件实现了显著的地表美化效果。它的架构清晰、设计优雅，非常值得作为 Minecraft blockstate variants 系统和模型继承技术的教学案例。62 个文件全部用于单一功能，体现了极高的功能密度和执行精准度。
