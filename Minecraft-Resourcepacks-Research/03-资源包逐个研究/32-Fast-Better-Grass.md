# 32. Fast Better Grass

## 根目录结构

```
Fast Better Grass/
├── assets/
│   └── minecraft/
│       ├── blockstates/
│       │   ├── crimson_nylium.json
│       │   ├── dirt_path.json
│       │   ├── grass_block.json
│       │   ├── mycelium.json
│       │   ├── podzol.json
│       │   └── warped_nylium.json
│       └── models/
│           └── block/
│               ├── crimson_nylium.json
│               ├── dirt_path.json
│               ├── fast_better_grass.json
│               ├── grass_block.json
│               ├── grass_block_snow.json
│               ├── mycelium.json
│               ├── podzol.json
│               └── warped_nylium.json
├── pack.mcmeta
└── pack.png
```

## 包定位

Fast Better Grass 是一个专注于草地渲染优化的资源包，其目标是在视觉质量和渲染性能之间取得平衡。它的名字中带有"Fast"（快速）一词，表明它采用了OptiFine的"Better Grass"（快速模式）——即仅在草方块侧面使用顶部纹理进行着色，而不像"Better Grass"的精致模式那样渲染完整的3D草丛覆盖层。这种设计在保证草地侧面与顶部颜色一致的前提下，避免了额外的多边形渲染开销。

值得注意的是，包描述中明确标注了 "Must be the first to work"（必须排在首位才能工作），这意味着在加载资源包时，本包必须位于列表的最上方，否则可能无法正确覆盖其他资源包对草方块的处理。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "description": {
      "translate": "fo.resourcePack.fastbettergrass",
      "fallback": "OptiFine's Better Grass (fast)\n§4Must be the first to work"
    },
    "pack_format": 15,
    "min_format": 15,
    "max_format": 84,
    "supported_formats": [15, 64]
  }
}
```

该mcmeta使用了可翻译文本（translate），而不是直接硬编码描述字符串，这是一种规范的做法。pack_format为15（对应Minecraft 1.21），supported_formats范围为15-64，表明该包兼容1.21到未来多个版本。

## 资源内容结构

本资源包的主题非常集中，仅涉及**草类方块**的视觉优化，包括：

- **草方块 (grass_block)**：核心目标，覆盖了普通草方块及其雪覆变种
- **菌丝体 (mycelium)**：同样应用了侧面上色技术
- **灰化土 (podzol)**：针叶林生物群系特有的变种
- **绯红菌岩 (crimson_nylium)**：下界绯红森林地表
- **诡异菌岩 (warped_nylium)**：下界诡异森林地表
- **土径 (dirt_path)**：村民踩出的路径方块

## 关键目录功能

### blockstates/ 目录

blockstates定义了方块在不同状态下的模型映射。例如 `grass_block.json` 中：

- `snowy=false` 时使用 `grass_block` 模型，并且有4个旋转变体（0/90/180/270度），使视觉上更自然
- `snowy=true` 时使用 `grass_block_snow` 模型

对于下界的绯红菌岩和诡异菌岩，同样使用了旋转变体。

### models/block/ 目录

模型文件是整个资源包的核心创新所在。

**fast_better_grass.json** 定义了一个通用的父模型：
```json
{
  "parent": "minecraft:block/cube_bottom_top",
  "textures": {
    "bottom": "#bottom",
    "side": "#sidetop",
    "top": "#sidetop"
  }
}
```

这里的关键技巧是：`side` 和 `top` 都使用了同一个纹理变量 `#sidetop`。这意味着草方块的侧面将使用顶部纹理进行渲染，而不是使用默认的侧面模板纹理。这就实现了"Better Grass"的效果——草方块的侧面不再是土色加草皮纹理，而是与顶部颜色一致的绿色。

**grass_block.json** 则进一步自定义了模型元素，手动定义了6个面的UV映射，其中顶部、北、南、西、东5个面都使用了 `#top` 纹理并带有 `tintindex: 0`（生物群系着色索引），确保草的颜色会根据生物群系自动变化。

**grass_block_snow.json** 用于雪覆草方块，其侧面纹理使用雪纹理。

## 技术特点

1. **模板化设计**：所有草类方块都继承自 `fast_better_grass.json` 父模型，大幅减少了重复代码。

2. **纹理变量引用**：巧妙运用 `#sidetop` 这种变量引用机制，在不改动底层纹理文件的前提下改变了方块的视觉渲染方式。

3. **色温索引**：所有暴露在外的草面都带有 `tintindex: 0`，使草色随生物群系变化（沙漠中呈枯黄色，沼泽中呈深绿色等）。

4. **旋转变体**：每个草方块有4个可能的朝向，打破完全对称带来的视觉重复感。

5. **无纹理文件**：本包完全不含任何纹理文件（.png），仅通过修改模型和blockstates来实现视觉效果。这是一个极简设计，体积很小的资源包。

6. **版本兼容性**：通过 `supported_formats: [15, 64]` 支持多个Minecraft版本。

## 结论

Fast Better Grass 是一个典型的极简功能性资源包，专注于单一视觉优化目标。它通过巧妙地修改方块模型定义，实现了OptiFine的Better Grass（快速模式）效果，而无需对纹理本身做任何修改。这种做法对性能的影响极小，同时显著提升了草地视觉质量——草方块的侧面不再是难看的土绿色分层，而是与顶部一致的完整草绿色。

对于玩家来说，这个包是性能与视觉的完美平衡点，尤其适合那些希望提升游戏画面但又不愿牺牲帧率的用户。它的"Must be the first to work"要求也提醒用户，在资源包加载顺序中应当将其置于最优先位置，以确保其修改不被其他包覆盖。
