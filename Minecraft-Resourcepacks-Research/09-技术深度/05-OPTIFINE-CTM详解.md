# OptiFine CTM 连接纹理详解

## 1. CTM 概述

### 1.1 什么是 CTM

CTM（Connected Textures，连接纹理）是 OptiFine 提供的一项核心视觉增强功能，它允许相邻的相同方块共享纹理边缘，从而创造出无缝连接的视觉效果。这项技术极大地提升了 Minecraft 世界的视觉连贯性，使得玻璃、石头、沙砾等方块能够呈现出更加自然和美观的外观。

CTM 的工作原理是根据相邻方块的类型和位置，动态选择纹理的特定部分进行渲染。通过预定义的纹理图集和匹配规则，系统能够在运行时为每个方块面选择正确的纹理变体。

### 1.2 CTM 的视觉效果

连接纹理带来的视觉改进包括：

- **无缝玻璃**：相邻的玻璃方块边缘自然连接，消除粗黑边框
- **连续石材**：石头、砖块等建筑材料呈现统一的表面纹理
- **自然草地**：草地边缘根据相邻方块自然过渡
- **装饰细节**：书架、箱子等根据相邻关系显示不同的纹理

### 1.3 CTM 与原版渲染的对比

```
原版渲染：
┌─────┐ ┌─────┐ ┌─────┐
│  A  │ │  A  │ │  A  │  ← 每个方块独立渲染
└─────┘ └─────┘ └─────┘  ← 边缘明显可见

CTM渲染：
┌─────────────────────┐
│    A    │    A    │    A    │  ← 纹理无缝连接
└─────────────────────┘  ← 边缘不可见
```

### 1.4 兼容性与性能

CTM 功能仅在 OptiFine 客户端上生效。连接纹理的计算会带来一定的性能开销，主要体现在：

- 纹理变体的动态选择
- 相邻方块状态的检查
- 额外的纹理内存占用

OptiFine 通过缓存机制和优化算法将性能影响降至最低，但在大规模使用 CTM 时仍需注意性能监控。

---

## 2. 目录结构

### 2.1 基本路径

CTM 资源文件必须放置在以下目录中：

```
assets/
└── minecraft/
    └── optifine/
        └── ctm/
            ├── glass/
            │   ├── glass.properties
            │   ├── glass.png          # 纹理图集
            │   └── glass_overlay.png  # 可选的覆盖层
            ├── stone/
            │   ├── stone.properties
            │   └── stone.png
            └── bookshelf/
                ├── bookshelf.properties
                └── bookshelf.png
```

### 2.2 推荐的目录组织

为了便于管理和维护，建议按方块类型或功能分组：

```
optifine/ctm/
├── building/           # 建筑材料
│   ├── glass/
│   ├── stone/
│   ├── brick/
│   └── wood/
├── natural/            # 自然方块
│   ├── grass/
│   ├── dirt/
│   ├── sand/
│   └── stone_variants/
├── decorative/         # 装饰方块
│   ├── bookshelf/
│   ├── chest/
│   └── flower_pot/
└── special/            # 特殊用途
    ├── spawner/
    └── portal/
```

### 2.3 纹理文件格式

CTM 纹理文件通常是包含多个变体的图集（atlas），具体布局取决于所使用的 CTM 方法：

- **标准 CTM**：47 个变体（46 个连接状态 + 1 个默认状态）
- **紧凑 CTM**：47 个变体，更紧凑的布局
- **水平连接**：3 个变体（左、中、右）
- **垂直连接**：3 个变体（上、中、下）
- **随机变体**：任意数量的随机纹理

---

## 3. CTM 方法类型

### 3.1 ctm（标准连接）

标准 CTM 是最常用的连接纹理方法，它根据 4 个相邻方块（上、下、左、右）和 4 个对角相邻方块的状态来选择纹理变体。

**纹理图集布局**（47 个变体）：

```
┌───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │  ← 行 0
├───┼───┼───┼───┼───┼───┼───┤
│ 7 │ 8 │ 9 │10 │11 │12 │13 │  ← 行 1
├───┼───┼───┼───┼───┼───┼───┤
│14 │15 │16 │17 │18 │19 │20 │  ← 行 2
├───┼───┼───┼───┼───┼───┼───┤
│21 │22 │23 │24 │25 │26 │27 │  ← 行 3
├───┼───┼───┼───┼───┼───┼───┤
│28 │29 │30 │31 │32 │33 │34 │  ← 行 4
├───┼───┼───┼───┼───┼───┼───┤
│35 │36 │37 │38 │39 │40 │41 │  ← 行 5
├───┼───┼───┼───┼───┼───┼───┤
│42 │43 │44 │45 │46 │   │   │  ← 行 6
└───┴───┴───┴───┴───┴───┴───┘
```

每个变体对应一种特定的相邻方块组合，索引 0-46 共 47 个变体。

**properties 配置示例**：
```properties
method=ctm
tiles=0-46
matchBlocks=minecraft:glass
connect=block
faces=sides top bottom
```

### 3.2 ctm_compact（紧凑连接）

紧凑 CTM 与标准 CTM 功能相同，但使用不同的纹理图集布局，更节省纹理空间。

**纹理图集布局**（47 个变体，7x7 网格）：

```
┌───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
├───┼───┼───┼───┼───┼───┼───┤
│ 7 │ 8 │ 9 │10 │11 │12 │13 │
├───┼───┼───┼───┼───┼───┼───┤
│14 │15 │16 │17 │18 │19 │20 │
├───┼───┼───┼───┼───┼───┼───┤
│21 │22 │23 │24 │25 │26 │27 │
├───┼───┼───┼───┼───┼───┼───┤
│28 │29 │30 │31 │32 │33 │34 │
├───┼───┼───┼───┼───┼───┼───┤
│35 │36 │37 │38 │39 │40 │41 │
├───┼───┼───┼───┼───┼───┼───┤
│42 │43 │44 │45 │46 │   │   │
└───┴───┴───┴───┴───┴───┴───┘
```

### 3.3 horizontal（水平连接）

水平连接仅根据左右相邻的方块选择纹理，适用于横向连续的纹理效果。

**纹理变体**（3 个）：

```
┌───┬───┬───┐
│ 0 │ 1 │ 2 │
└───┴───┴───┘
  左  中  右
```

**应用场景**：
- 横向连续的栅栏
- 水平排列的书架
- 连续的管道

**配置示例**：
```properties
method=horizontal
tiles=0-2
matchBlocks=minecraft:oak_fence
connect=block
```

### 3.4 vertical（垂直连接）

垂直连接根据上下相邻的方块选择纹理，适用于垂直连续的纹理效果。

**纹理变体**（3 个）：

```
┌───┐
│ 0 │  ← 上
├───┤
│ 1 │  ← 中
├───┤
│ 2 │  ← 下
└───┘
```

**应用场景**：
- 垂直连续的栅栏
- 链条
- 藤蔓

**配置示例**：
```properties
method=vertical
tiles=0-2
matchBlocks=minecraft:iron_bars
connect=block
```

### 3.5 top（顶部连接）

顶部连接仅检查上方相邻的方块，用于实现只有顶部边缘连接的效果。

**纹理变体**（2 个）：

```
┌───┐
│ 0 │  ← 无连接
├───┤
│ 1 │  ← 顶部连接
└───┘
```

**应用场景**：
- 草地顶部
- 雪层顶部
- 植物顶部

**配置示例**：
```properties
method=top
tiles=0-1
matchBlocks=minecraft:grass_block
faces=top
```

### 3.6 random（随机变体）

随机方法从一组纹理中随机选择一个作为方块的纹理，不考虑相邻方块的状态。

**配置示例**：
```properties
method=random
tiles=0-8
matchBlocks=minecraft:stone
weights=1 1 1 1 2 2 2 3 3
connect=block
faces=all
```

**权重系统**：
- `weights` 属性指定每个变体的出现概率
- 权重值越大，该变体出现的概率越高
- 不指定权重时，所有变体概率相等

### 3.7 repeat（重复平铺）

重复方法将纹理在一定范围内重复平铺，创建大面积的规律纹理。

**配置示例**：
```properties
method=repeat
tiles=0
matchBlocks=minecraft:sand
width=3
height=3
connect=block
faces=all
```

**参数说明**：
- `width`：重复单元的宽度（方块数）
- `height`：重复单元的高度（方块数）

### 3.8 pattern（图案匹配）

图案方法根据特定的相邻方块组合选择纹理，用于创建复杂的装饰图案。

**配置示例**：
```properties
method=pattern
tiles=0-15
matchBlocks=minecraft:bricks
connect=block
faces=all
```

### 3.9 linked（链接连接）

链接方法检查一定范围内的相同方块，创建更大范围的连接效果。

**配置示例**：
```properties
method=linked
tiles=0-46
matchBlocks=minecraft:glass
connect=block
searchRadius=2
faces=sides top bottom
```

**参数说明**：
- `searchRadius`：搜索相邻方块的范围（默认为 1）

### 3.10 fixed（固定纹理）

固定方法为特定方块状态指定固定的纹理，不进行任何连接计算。

**配置示例**：
```properties
method=fixed
tiles=0
matchBlocks=minecraft:grass_block
metadata=0
connect=block
faces=top
```

---

## 4. .properties 文件详解

### 4.1 核心属性

#### method

指定 CTM 的连接方法，决定纹理选择的算法。

```properties
# 可选值
method=ctm            # 标准连接
method=ctm_compact    # 紧凑连接
method=horizontal     # 水平连接
method=vertical       # 垂直连接
method=top            # 顶部连接
method=random         # 随机变体
method=repeat         # 重复平铺
method=pattern        # 图案匹配
method=linked         # 链接连接
method=fixed          # 固定纹理
```

#### tiles

指定纹理变体的索引或范围。

```properties
# 单个变体
tiles=0

# 范围（包含两端）
tiles=0-46

# 逗号分隔的列表
tiles=0,1,2,3,4,5,6,7,8

# 混合格式
tiles=0-10,15,20-25

# 使用外部纹理文件
tiles=glass/glass_0.png
tiles=glass/glass_0.png glass/glass_1.png glass/glass_2.png
```

#### matchBlocks

指定此 CTM 规则应用于哪些方块。

```properties
# 单个方块
matchBlocks=minecraft:glass

# 多个方块
matchBlocks=minecraft:glass,minecraft:glass_pane,minecraft:white_stained_glass

# 使用方块状态
matchBlocks=minecraft:oak_stairs[facing=north,half=bottom,shape=straight]

# 通配符
matchBlocks=minecraft:*_glass

# 支持模组方块
matchBlocks=modid:block_name
```

#### matchTiles

根据方块当前使用的纹理进行匹配，而非方块 ID。

```properties
# 匹配特定纹理
matchTiles=minecraft:block/glass

# 匹配多个纹理
matchTiles=minecraft:block/glass,minecraft:block/glass_pane_top
```

#### metadata

匹配方块的元数据值（主要用于旧版本 Minecraft）。

```properties
# 匹配特定元数据
metadata=0

# 匹配多个元数据
metadata=0,1,2,3

# 匹配元数据范围
metadata=0-15
```

**注意**：在 1.13+ 版本中，方块状态系统取代了元数据，此属性主要用于向后兼容。

### 4.2 连接控制属性

#### connect

指定连接的检测方式。

```properties
# 连接相同方块（默认）
connect=block

# 连接相同纹理的方块
connect=tile

# 连接相同材质的方块
connect=material
```

**详细说明**：
- `block`：只连接完全相同的方块（包括方块状态）
- `tile`：连接使用相同纹理的方块（忽略方块状态差异）
- `material`：连接相同材质类别的方块（如所有玻璃类型）

#### faces

指定 CTM 应用于方块的哪些面。

```properties
# 应用于所有面（默认）
faces=all

# 仅应用于侧面
faces=sides

# 仅应用于顶面
faces=top

# 仅应用于底面
faces=bottom

# 组合指定
faces=sides top bottom

# 使用数字索引
faces=0 1 2 3 4 5  # 对应 down up north south east west
```

#### symmetry

指定纹理的对称性，减少需要创建的变体数量。

```properties
# 无对称（默认）
symmetry=none

# 完全对称
symmetry=all

# 仅水平对称
symmetry=horizontal

# 仅垂直对称
symmetry=vertical
```

### 4.3 高级匹配属性

#### minHeight / maxHeight

限制 CTM 规则在特定高度范围内生效。

```properties
# 仅在 Y=0 到 Y=64 之间生效
minHeight=0
maxHeight=64

# 仅在地下生效
maxHeight=0

# 仅在地表以上生效
minHeight=64
```

#### biomes

限制 CTM 规则在特定生物群系中生效。

```properties
# 在指定生物群系中生效
biomes=minecraft:plains,minecraft:forest,minecraft:flower_forest

# 在所有森林类群系中生效
biomes=minecraft:*_forest
```

#### yPositions

指定 CTM 规则生效的精确 Y 坐标列表。

```properties
# 仅在特定高度生效
yPositions=0,64,128

# 在一系列高度生效
yPositions=0-64
```

---

## 5. 纹理图集布局

### 5.1 标准 CTM 的 47 个变体

标准 CTM 使用 47 个纹理变体来覆盖所有可能的相邻方块组合。每个变体对应一种特定的连接状态。

**变体索引对应的连接状态**：

```
索引 0：无连接（独立方块）
索引 1-4：单边连接（上、右、下、左）
索引 5-8：双边连接（上下、左右、对角）
索引 9-16：三边连接
索引 17-24：四边连接的各个变体
索引 25-46：包含对角连接的复杂状态
```

### 5.2 纹理图集创建指南

创建标准 CTM 纹理图集时，需要按照特定的布局排列 47 个变体：

**推荐的图集尺寸**：
- 单个变体：16x16 像素
- 7x7 网格布局：112x112 像素
- 含边距的布局：128x128 像素

**创建步骤**：

1. 准备基础纹理（16x16 像素）
2. 根据连接状态创建各个变体
3. 按照索引顺序排列在图集中
4. 保存为 PNG 格式

### 5.3 常用连接类型的纹理设计

#### 边缘连接

边缘连接是最常见的 CTM 效果，相邻方块共享边缘纹理：

```
┌─────┐ ┌─────┐
│     │ │     │
│  A  ├─┤  A  │  ← 边缘自然连接
│     │ │     │
└─────┘ └─────┘
```

#### 角落连接

角落连接处理对角相邻方块的纹理过渡：

```
┌─────┐
│  A  ├─────┐
├─────┤  A  │
│  A  ├─────┘
└─────┘
```

### 5.4 纹理变体命名规范

虽然 CTM 使用数字索引来引用变体，但为了便于管理，建议为原始纹理文件使用描述性命名：

```
glass_ctm_atlas.png       # 标准 CTM 图集
glass_ctm_compact.png     # 紧凑 CTM 图集
glass_horizontal.png      # 水平连接图集
glass_random_0.png        # 随机变体 0
glass_random_1.png        # 随机变体 1
```

---

## 6. 常见应用场景

### 6.1 连接玻璃

连接玻璃是 CTM 最经典的应用，消除了原版玻璃的粗黑边框。

**glass.properties**：
```properties
method=ctm
tiles=0-46
matchBlocks=minecraft:glass,minecraft:white_stained_glass,minecraft:light_blue_stained_glass
connect=tile
faces=sides top bottom
symmetry=all
```

**纹理设计要点**：
- 基础纹理保持半透明
- 边缘变体确保过渡自然
- 使用 alpha 通道控制透明度

### 6.2 连接石头/石材

为石头、花岗岩、闪长岩等创建连续的纹理效果。

**stone.properties**：
```properties
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
connect=block
faces=all
```

**变体设计建议**：
- 保持基础纹理的色调一致
- 边缘变体添加微妙的阴影
- 角落变体确保自然过渡

### 6.3 连接草地

草地的 CTM 通常只应用于顶面，创建自然的草地边缘效果。

**grass_block.properties**：
```properties
method=top
tiles=0-1
matchBlocks=minecraft:grass_block
faces=top
connect=block
```

**设计要点**：
- 使用 `top` 方法只连接顶部
- 边缘纹理应与泥土自然过渡
- 考虑不同生物群系的颜色变化

### 6.4 连接书架

书架的 CTM 通常应用于侧面，创建连续的书架效果。

**bookshelf.properties**：
```properties
method=ctm
tiles=0-46
matchBlocks=minecraft:bookshelf
faces=north south east west
connect=block
```

**设计要点**：
- 顶面和底面保持原版纹理
- 侧面创建连续的书架效果
- 书籍的排列应自然随机

### 6.5 随机纹理变体

为方块添加视觉多样性，使用随机方法选择不同的纹理变体。

**stone_random.properties**：
```properties
method=random
tiles=0-8
matchBlocks=minecraft:stone
weights=10 8 6 4 3 2 2 1 1
connect=block
faces=all
```

**权重说明**：
- 权重 10：最常见的变体
- 权重 1：最稀有的变体
- 总权重越大，稀有变体出现的概率越低

---

## 7. 高级技巧

### 7.1 多层 CTM

可以为同一个方块定义多个 CTM 层，实现更复杂的效果：

```properties
# 第一层：基础连接
method=ctm
tiles=0-46
matchBlocks=minecraft:glass
connect=tile
faces=sides
layer=cutout
priority=0

# 第二层：覆盖层（可选）
method=ctm
tiles=0-46
matchBlocks=minecraft:glass
connect=tile
faces=sides
layer=cutout_mipped
priority=1
```

### 7.2 条件化 CTM

结合其他 OptiFine 特性（如生物群系、高度等）创建条件化的 CTM 效果：

```properties
# 高海拔石头纹理
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
minHeight=128
connect=block
faces=all

# 深层石头纹理
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
maxHeight=0
connect=block
faces=all
```

### 7.3 性能优化技巧

CTM 的性能优化主要从以下几个方面入手：

1. **减少规则数量**：合并相似的规则
2. **使用合适的方法**：简单效果使用 `horizontal` 或 `vertical` 而非 `ctm`
3. **优化纹理尺寸**：使用适当大小的纹理图集
4. **合理使用对称性**：利用 `symmetry` 属性减少变体数量

```properties
# 优化前：使用完整的 47 变体 CTM
method=ctm
tiles=0-46

# 优化后：使用对称性减少变体
method=ctm
tiles=0-46
symmetry=all
```

### 7.4 调试 CTM 问题

当 CTM 效果不符合预期时，可以使用以下调试方法：

1. **检查规则优先级**：多个规则冲突时，检查文件名字母顺序
2. **验证纹理图集**：确保变体数量与 tiles 属性匹配
3. **测试连接类型**：尝试不同的 connect 值
4. **检查方块状态**：使用 F3 调试屏幕查看方块状态信息

---

## 8. 工具与资源

### 8.1 CTM 纹理生成工具

| 工具 | 用途 | 说明 |
|------|------|------|
| CTM Generator | 自动生成 CTM 图集 | 根据基础纹理生成 47 个变体 |
| Connected Textures Mod | 参考实现 | 了解 CTM 的工作原理 |
| Blockbench | 纹理编辑 | 创建和编辑 CTM 纹理变体 |
| GIMP/Photoshop | 图像处理 | 批量处理纹理变体 |

### 8.2 在线资源

- **OptiFine 官方文档**：最新的 CTM 规范说明
- **Minecraft 论坛**：社区分享的 CTM 资源包
- **GitHub 仓库**：开源的 CTM 纹理资源

### 8.3 推荐的资源包

以下是一些优秀的 CTM 资源包示例，可以作为学习参考：

- **ConnectedTexturesMod**：CTM 的参考实现
- **Vanilla CTM**：原版风格的 CTM 纹理
- **Faithful CTM**：高分辨率的 CTM 纹理

---

## 9. 实际应用案例

### 9.1 完整的玻璃 CTM 资源包

**目录结构**：
```
assets/minecraft/
├── optifine/ctm/
│   ├── glass/
│   │   ├── glass.properties
│   │   └── glass.png
│   ├── stained_glass/
│   │   ├── white_stained_glass.properties
│   │   ├── white_stained_glass.png
│   │   ├── light_blue_stained_glass.properties
│   │   └── light_blue_stained_glass.png
│   └── glass_pane/
│       ├── glass_pane.properties
│       └── glass_pane.png
└── textures/
    └── block/
        ├── glass_ctm.png
        ├── white_stained_glass_ctm.png
        └── glass_pane_ctm.png
```

**glass.properties**：
```properties
# 标准玻璃 CTM 配置
method=ctm
tiles=0-46
matchBlocks=minecraft:glass
connect=tile
faces=sides top bottom
symmetry=all
```

### 9.2 多变体石材纹理

为石头创建多个随机变体，增加视觉多样性：

**stone_variants.properties**：
```properties
# 石头随机变体
method=random
tiles=0-12
matchBlocks=minecraft:stone
weights=20 15 12 10 8 6 5 4 3 2 2 1 1
connect=block
faces=all
```

### 9.3 高度敏感的石头纹理

根据海拔高度显示不同的石头纹理：

```properties
# 地表石头
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
minHeight=64
connect=block
faces=all

# 中层石头
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
minHeight=0
maxHeight=63
connect=block
faces=all

# 深层石头
method=ctm
tiles=0-46
matchBlocks=minecraft:stone
maxHeight=-1
connect=block
faces=all
```

---

## 10. 常见问题与解决方案

### 10.1 CTM 纹理不显示

**问题**：配置正确但纹理没有连接效果。

**可能原因**：
- 纹理文件路径错误
- 纹理变体数量与 tiles 属性不匹配
- connect 属性设置不当
- OptiFine 版本不支持某些特性

**解决方案**：
1. 检查纹理文件是否在正确的位置
2. 验证纹理图集的变体数量
3. 尝试不同的 connect 值
4. 更新 OptiFine 版本

### 10.2 CTM 效果不正确

**问题**：纹理连接效果不符合预期。

**可能原因**：
- 使用了错误的 CTM 方法
- 纹理变体的索引顺序错误
- 对角连接的处理不当

**解决方案**：
1. 根据需求选择合适的 CTM 方法
2. 检查纹理图集的布局
3. 测试不同的 symmetry 设置

### 10.3 性能问题

**问题**：使用 CTM 后游戏帧率下降。

**解决方案**：
- 减少 CTM 规则数量
- 使用更简单的方法（如 horizontal 替代 ctm）
- 优化纹理图集尺寸
- 关闭不需要的 CTM 效果

---

## 11. 总结

OptiFine CTM 是一个功能强大且灵活的连接纹理系统，通过合理运用各种 CTM 方法和配置选项，可以显著提升 Minecraft 世界的视觉质量。掌握 CTM 的关键要点包括：

1. **方法选择**：根据视觉需求选择合适的 CTM 方法
2. **纹理图集**：理解不同方法的纹理布局要求
3. **连接控制**：合理设置 connect、faces、symmetry 等属性
4. **性能优化**：在视觉效果和性能之间取得平衡
5. **调试技巧**：快速定位和解决 CTM 问题

通过系统学习和实践，资源包开发者可以创建出令人印象深刻的连接纹理效果，为玩家带来更加沉浸式的游戏体验。
