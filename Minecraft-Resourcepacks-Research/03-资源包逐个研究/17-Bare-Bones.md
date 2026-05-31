# 17. Bare Bones 1.21.11

## 根目录结构

```
Bare Bones 1.21.11/
├── pack.mcmeta
├── pack.png
├── assets/
│   └── minecraft/
│       ├── blockstates/
│       │   ├── black_concrete_powder.json  (以及其它15种混凝土粉末)
│       │   ├── blue_concrete_powder.json
│       │   ├── brown_concrete_powder.json
│       │   ├── deepslate.json
│       │   ├── dirt.json
│       │   ├── dirt_path.json
│       │   ├── grass_block.json
│       │   ├── mycelium.json
│       │   ├── red_sand.json
│       │   ├── sand.json
│       │   └── stone.json
│       ├── models/
│       │   └── block/
│       │       ├── crop.json
│       │       ├── dirt_path.json
│       │       ├── fern.json
│       │       ├── grass.json
│       │       ├── large_fern_bottom.json
│       │       ├── large_fern_top.json
│       │       ├── lever.json
│       │       ├── lever_on.json
│       │       ├── tall_grass_bottom.json
│       │       ├── tall_grass_top.json
│       │       ├── template_torch.json
│       │       ├── torch_wall.json
│       │       └── wall_torch.json
│       ├── texts/
│       │   └── splashes.txt
│       └── textures/
│           ├── block/           (约 700+ 纹理文件)
│           ├── colormap/
│           ├── entity/          (约 80+ 子目录，涵盖所有生物)
│           ├── environment/
│           ├── font/
│           ├── gui/
│           ├── item/
│           ├── map/
│           ├── misc/
│           ├── models/
│           ├── mob_effect/
│           ├── painting/
│           ├── particle/
│           └── renderdata/
├── overlay_1_21_2/
│   └── assets/minecraft/textures/
│       ├── block/
│       ├── entity/
│       ├── gui/
│       └── item/
├── overlay_1_21_4/
│   └── assets/minecraft/textures/
│       ├── block/               (苍白之园系列方块)
│       ├── entity/
│       └── item/
├── overlay_1_21_5/
│   └── assets/minecraft/textures/
│       ├── block/               (灌木、花、萤火虫丛等)
│       ├── colormap/
│       ├── entity/
│       └── item/
├── overlay_1_21_6/
│   └── assets/minecraft/textures/
│       ├── block/
│       ├── entity/              (快乐恶魂)
│       ├── gui/
│       └── item/
└── overlay_1_21_9/
    └── assets/minecraft/textures/
        ├── entity/              (铜傀儡、新装备系统)
        └── item/
```

## 概述

Bare Bones（骨架）是由开发团队制作的高完善度资源包，版本对应 Minecraft 1.21.11。pack_format 为 34（适用于 1.21.2+），通过 `supported_formats: [34, 75]` 声明支持至未来版本。其宣传语 "Just like the trailers!" 点明了核心设计理念：模仿 Minecraft 官方预告片中的美术风格——简洁、明快、轮廓清晰。

包内共包含约 3539 个文件，是这 4 个包中规模最大的，覆盖面极广：从方块纹理到生物实体、从 GUI 界面到粒子效果、从地图材质到字体渲染，几乎无所不包。

## 版本兼容架构：Overlay 系统

Bare Bones 最引人注目的技术特征是使用了 Minecraft 1.21.2+ 引入的 Overlay 系统。pack.mcmeta 中定义了 6 个 overlay 层，对应不同游戏版本的纹理需求：

| Overlay 目录 | 格式版本范围 | 主要新增内容 |
|---|---|---|
| `overlay_1_21_2` | 42-75 | 装备系统纹理（马铠、盔甲）、红石火把重绘 |
| `overlay_1_21_4` | 46-75 | 苍白之园生物群系方块（苍白橡木、吱吱之心、眼斑花） |
| `overlay_1_21_5` | 55-75 | 生物群系变种（鸡、牛、骆驼）、萤火虫丛、落叶 |
| `overlay_1_21_6` | 55-75 | 快乐恶魂、新的 HUD 定位器 |
| `overlay_1_21_9` | 65-75 | 铜傀儡、新装备渲染系统（人类/马装备槽） |
| `overlay_1_21_11` | 70-75 | 最新版本适配 |

这种设计体现了极高的工程水准：基础包覆盖核心纹理，overlay 层按版本增量更新，确保包在多个 Minecraft 版本间都能正确工作，而不会因为版本变更导致纹理丢失或错误。

## 核心方块与模型改造

### Concrete Powder 方块状态（混凝土粉末）
包内为全部 16 种混凝土粉末重写了 blockstates。这是因为 Bare Bones 修改了 sand、red_sand 和 gravel 的纹理与物理属性，而混凝土粉末继承了沙子的行为逻辑。

### 草方块与耕地
- `grass_block.json`: 使用 variants 系统，在 snowy=false 时引用自定义模型，snowy=true 时引用原版下雪模型。
- `dirt_path.json`: 自定义模型文件，通过 block/block 父模型构建，使用 15 像素高度（非完整的 16 像素），实现了耕地的实际凹陷效果。包含 ambinentocclusion=true，保持了光照一致性。
- 侧面纹理使用自定义 UV 映射（从 y=1 开始），确保纹理对齐。

### 拉杆（Lever）
拉杆模型被完全重写。`lever.json` 和 `lever_on.json` 使用自定义 element 构建，包含底座（5, -0.02, 4 到 11, 2.98, 12 的扁立方体）和拉杆柄（7, 1, 7 到 9, 11, 9），拉杆柄使用 rotation 系统绕原点 (8, 1, 8) 沿 X 轴旋转 -45 度（关）或 +45 度（开）。

### 火把
template_torch.json、torch_wall.json、wall_torch.json 被重写。这些模型调整了火把的几何形状和 UV 映射，以匹配 Bare Bones 特有的"简洁方框"风格。

## 纹理设计风格

Bare Bones 的纹理风格可概括为：

1. **高对比度轮廓**：所有方块和物品的边缘都有清晰的深色轮廓，如同动画片中的人物描边效果。
2. **减少渐变和噪点**：相较于原版的噪点丰富纹理，Bare Bones 使用大块纯色区域和有限的渐变。
3. **扁平化色彩**：色彩饱和度高于原版，但过渡更简单直接。
4. **统一视觉语言**：所有材质都遵循同一种简洁美学，从石头到钻石块都有统一的阴影和高光处理。

纹理目录结构完整覆盖了 Minecraft 的全部类别：
- `block/`: 约 700+ 方块纹理，全面重绘
- `entity/`: 约 80+ 子目录，覆盖从 allay（悦灵）到 zombie（僵尸）的所有生物
- `item/`: 物品栏图标，包括工具、武器、食物等
- `gui/`: 界面元素，容器背景、按钮等
- `environment/`: 天空、云雾、太阳/月亮
- `colormap/`: 生物群系着色图

## 实体纹理覆盖

Bare Bones 的实体纹理覆盖极为全面，包括：

- 所有被动生物：牛、猪、羊、鸡、兔子、狐狸、山羊、骆驼等
- 所有中立/敌对生物：苦力怕、骷髅、僵尸、蜘蛛、末影人、猪灵等
- BOSS 生物：末影龙、凋灵
- 村民系列：村民、灾厄村民、女巫
- 装备实体：马铠（多种材质）、盔甲纹饰
- 功能实体：船、箱子、潜影贝、告示牌、画作等
- 新版本生物：微风、犰狳、沼泽骷髅等

## 技术特点

1. **版本前瞻性**：通过 overlays 系统支持到 format 75（预计对应未来多个大版本）。
2. **模型精度控制**：在保持简洁风格的前提下，使用了精确定位的 UV 映射和旋转参数。
3. **混凝土系统兼容**：全面处理了混凝土粉末与沙子/砾石的关联逻辑。
4. **路径方块凹陷效果**：通过模型高度从 16 降至 15 像素，真实再现了非完整方块效果。
5. **Biome 兼容性**：包含 colormap 纹理，确保了在不同生物群系中的颜色适应性。

## 理念与设计哲学

Bare Bones 的设计哲学是"回归预告片的美术风格"。在 Minecraft 官方的宣传材料中，游戏画面通常经过精心布置，色调和对比度都经过调整。Bare Bones 试图让实际游戏画面达到这种效果。它并非简单的纹理替换，而是一种整体视觉重设计——通过统一的轮廓线、简化的纹理细节和增强的色彩对比，创造出干净、清晰、富有表现力的视觉效果。

## 总结

Bare Bones 是一个成熟度高、工程架构优秀的全面型资源包。其 overlay 系统设计是 1.21+ 版本资源包开发的最佳实践范本。超过 3500 个文件的规模体现了其全面性，而统一的艺术风格则展示了其设计深度。它适合作为研究 Minecraft 资源包 overlay 系统、模型自定义和统一美学设计的参考案例。
