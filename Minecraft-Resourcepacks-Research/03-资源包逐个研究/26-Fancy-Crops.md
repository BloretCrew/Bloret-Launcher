# 26. Fancy Crops v1.3

## 根目录结构

```
Fancy Crops v1.3/
├── assets/
│   ├── farmersdelight/
│   │   ├── blockstates/
│   │   │   ├── cabbages.json
│   │   │   └── onions.json
│   │   ├── models/
│   │   │   └── block/
│   │   │       ├── cabbages.json
│   │   │       ├── cabbages_stage6.json
│   │   │       ├── cabbages_stage7.json
│   │   │       ├── cabbages_stage7a.json
│   │   │       ├── cabbages_stage7b.json
│   │   │       ├── onions_stage0.json
│   │   │       ├── onions_stage1.json
│   │   │       ├── onions_stage2.json
│   │   │       ├── onions_stage2a.json
│   │   │       ├── onions_stage3.json
│   │   │       ├── onions_stage3a.json
│   │   │       └── onions_stage3b.json
│   │   └── textures/
│   │       ├── block/
│   │       │   ├── cabbages_stage7.png
│   │       │   ├── cabbages_stage7a.png
│   │       │   ├── cabbages_stage7b.png
│   │       │   ├── onions_stage0.png
│   │       │   ├── onions_stage1.png
│   │       │   ├── onions_stage2.png
│   │       │   ├── onions_stage2a.png
│   │       │   ├── onions_stage3.png
│   │       │   ├── onions_stage3a.png
│   │       │   └── onions_stage3b.png
│   │       └── item/
│   │           ├── cabbage_seeds.png
│   │           └── tomato_seeds.png
│   └── minecraft/
│       ├── blockstates/
│       │   ├── beetroots.json
│       │   ├── carrots.json
│       │   ├── potatoes.json
│       │   ├── sugar_cane.json
│       │   └── wheat.json
│       ├── models/
│       │   └── block/
│       │       ├── attached_melon_stem.json
│       │       ├── attached_pumpkin_stem.json
│       │       ├── beetroots_stage0-3,3a,3b.json
│       │       ├── carrots_stage0-3,3a,3b.json
│       │       ├── crop.json
│       │       ├── hay_block.json
│       │       ├── hay_block_horizontal.json
│       │       ├── melon_stem_fruit.json
│       │       ├── potatoes_stage0-3,3a,3b.json
│       │       ├── pumpkin_stem_fruit.json
│       │       ├── stem_growth0-7.json
│       │       ├── sugar_cane.json
│       │       ├── tall_crop.json
│       │       ├── tall_wheat_crop.json
│       │       ├── wheat_stage0-7,7a,7b.json
│       └── textures/
│           ├── block/
│           │   ├── attached_melon_stem.png
│           │   ├── attached_pumpkin_stem.png
│           │   ├── beetroots_stage0-3,3a,3b.png
│           │   ├── carrots_stage0-3,3a,3b.png
│           │   ├── hay_block_side.png
│           │   ├── hay_block_top.png
│           │   ├── melon_stem.png
│           │   ├── potatoes_stage0-3,3a,3b.png
│           │   ├── pumpkin_side.png
│           │   ├── pumpkin_stem.png
│           │   ├── pumpkin_top.png
│           │   ├── sugar_cane.png
│           │   ├── sugar_cane-variant.png
│           │   ├── torchflower_crop_stage0.png
│           │   ├── torchflower_crop_stage1.png
│           │   ├── wheat_stage0-7,7a,7b.png
│           └── item/
│               ├── beetroot_seeds.png
│               ├── egg.png
│               ├── melon_seeds.png
│               ├── pumpkin_seeds.png
│               └── wheat_seeds.png
├── pack.mcmeta
└── pack.png
```

## 包定位

作者：Bee。来源：Modrinth。版本 v1.3。本包是一个专注于改善 Minecraft 农作物视觉效果的资源包，采用"高耸作物"（tall crops）设计理念，使农作物在生长成熟时呈现更高的 3D 模型，而非原版的扁平十字形纹理。同时包涵盖了 Farmer's Delight Mod 的兼容作物，是为原版+模组农业玩法服务的专项美化包。

覆盖范围包括全部原版农作物（小麦、胡萝卜、马铃薯、甜菜根、甘蔗、西瓜茎、南瓜茎、火把花）以及 Farmer's Delight 模组的卷心菜和洋葱。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "name": "Fancy Crops",
    "version": "1.3",
    "source": "https://modrinth.com/resourcepack/fancy-crops",
    "pack_format": 15,
    "supported_formats": { "min_inclusive": 15, "max_inclusive": 1024 },
    "description": "A take on prettier Minecraft farming by Bee"
  }
}
```

- pack_format 15（对应 1.20+），但 supported_formats 范围极宽（15-1024），覆盖从 1.20 到无限未来。
- 元数据中包含了 name、version、source 等完备字段，在 Modrinth 生态下用于自动化展示。

### blockstates/

对每种作物修改其 blockstate JSON，引用自定义模型。例如 `wheat.json` 定义了小麦各生长阶段对应的模型：

- stages 0-6：使用 `minecraft:block/crop`（标准低矮作物模型）
- stage 7（完全成熟）：使用 `minecraft:block/tall_wheat_crop`（高耸模型）
- 此外为成熟阶段额外引入了 3a、3b 等变种，给予视觉随机性。

类似地，`beetroots.json`、`carrots.json`、`potatoes.json` 等也做了同样的处理。`sugar_cane.json` 被修改以使用 3D 甘蔗模型。

### models/block/ 中的关键模型

**tall_wheat_crop.json（高耸作物模型）**：
这是本包的核心创新。它构建了一个由 6 个面片（quad）组成的高耸作物模型：
- 作物从 y=-1 延伸到 y=31，高度为 32 像素（2 个方块高）。
- 6 个面片分别位于不同位置和旋转角度，形成十字交叉 + 斜向交叉的 6 向结构。
- 每个面片的高度为 32 像素，使作物看起来比原版的 16 像素扁平十字形高出一倍。
- 使用 `"ambientocclusion": false` 和 `"shade": false` 确保作物方块无环境光遮蔽，呈现更柔和的光照效果。
- 这种高耸模型模拟了作物从上方看时更加饱满、立体的视觉效果。

**tall_crop.json**：
用于胡萝卜、马铃薯等根茎类作物的高耸模型基类，结构与 tall_wheat_crop 类似。

**crop.json**：
原版作物的基础模型，用于生长阶段的早期。

**stem_growth0-7.json、melon_stem_fruit.json、pumpkin_stem_fruit.json**：
为西瓜/南瓜藤提供了更细致的分阶段模型，在结果时显示果实连接的立体结构。

**sugar_cane.json**：
甘蔗的 3D 模型，在原版的扁平十字形基础上增加了厚度感。

### textures/block/

所有作物纹理均经过重新绘制，风格为:

- 保留原版色彩的写实风格，增加了细节和立体感。
- 成熟阶段（stage 3 或 7）的纹理区分了多个变体（如 wheat_stage7、wheat_stage7a、wheat_stage7b），用于模型的随机变体，使田间作物不再千篇一律。
- 西瓜和南瓜的侧面纹理被修改以与茎部模型更好衔接。
- 干草块侧面/顶部也重新绘制以匹配新的作物美学风格。

## 技术特点

1. **模型高度拓展**：使用 y 轴范围延伸（从 y=-1 到 y=31）的超高面片模型，使作物在原版 1 方块空间中呈现 2 方块高的视觉效果。这是一种"视觉欺骗"，利用了模型坐标可以超出方块边界的特性。

2. **多面片交叉结构**：使用 6 个面片组成作物的"枝叶"，每一个面片围绕不同轴线（z 轴、y 轴 45 度旋转、x 轴）旋转，形成比原版更密集、更立体的作物外观。

3. **分阶段细致建模**：每种作物按生长阶段细分模型：
   - 早期（stage 0-2）：低矮的基础 crop 模型
   - 中期（stage 3-6）：逐渐增高
   - 成熟期（stage 7）：切换到高耸模型，并有多个视觉变体

4. **Mod 兼容性**：专门为 Farmer's Delight 的卷心菜和洋葱编写了 blockstates、models 和 textures，体现了对主流农业 Mod 的兼容支持。

5. **变体随机**：成熟作物使用了多个纹理变体（如 wheat_stage7、7a、7b），通过 blockstate 的 weight 机制实现随机选择，增加了田野的视觉多样性。

6. **纹理重绘**：所有作物纹理都重新绘制，风格统一，包括种子等物品纹理也做了配套修改。

## 结论

Fancy Crops v1.3 是一个高质量、专注垂直领域的农作物美化资源包。其核心亮点是使用高耸 3D 模型替代原版扁平十字形作物，通过模型面片的多轴交叉排列实现了远超原版的立体感和饱满度。包体量精悍但改动精准，覆盖了所有原版作物并兼容 Farmer's Delight 模组。纹理重绘风格统一、完成度高，成熟作物的多变体机制增加了视觉层次感。在技术实现上使用了 blockstate + 自定义模型的典型方案，同时巧妙地利用模型坐标越界技巧实现超高作物效果，是 Minecraft 农业美化的优秀范例。
