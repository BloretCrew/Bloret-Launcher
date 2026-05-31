# 29. Low Fire

## 根目录结构

```
Low Fire/
├── assets/
│   └── minecraft/
│       ├── models/
│       │   └── block/
│       │       ├── fire_floor1.json         # 地面火焰模型
│       │       ├── fire_side1.json          # 侧面火焰模型
│       │       ├── fire_side_alt1.json      # 侧面火焰备选模型
│       │       ├── fire_up1.json            # 向上火焰模型
│       │       ├── fire_up_alt1.json        # 向上火焰备选模型
│       │       ├── soul_fire_floor1.json    # 灵魂火地面模型
│       │       ├── soul_fire_side1.json     # 灵魂火侧面模型
│       │       └── soul_fire_side_alt1.json # 灵魂火侧面备选模型
│       └── textures/
│           └── block/
│               ├── fire_1.png              # 火焰动画帧1
│               ├── fire_1.png.mcmeta       # 动画配置
│               ├── fire_2.png              # 火焰动画帧2
│               ├── fire_2.png.mcmeta       # 动画配置
│               ├── soul_fire_1.png         # 灵魂火动画帧1
│               ├── soul_fire_1.png.mcmeta  # 动画配置
│               ├── soul_fire_2.png         # 灵魂火动画帧2
│               └── soul_fire_2.png.mcmeta  # 动画配置
├── pack.mcmeta
└── pack.png
```

## 包定位

作者：Oculie。版本 1.1.1。本包是一个极其精简的"降低火焰高度"资源包，核心目标就是让 Minecraft 中的火焰（包括普通火焰和灵魂火）在视觉上变得更低，减少火焰遮挡视野的问题。

这是一个典型的 **QoL（Quality of Life，生活质量）** 资源包——不改变游戏机制，仅通过调整模型使游戏体验更加舒适。包体量极小，仅 8 个模型文件和 4 个纹理文件（含对应的 .mcmeta 动画配置），专注于单一功能的极致实现。

Low Fire 在 Minecraft 资源包社区中属于"小而精"的经典品类，类似的还有"Lower Shield"（降低盾牌）等。这类包通常仅修改少量模型的几何参数即可实现显著的游戏体验改善。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 64,
    "description": "• Version 1.1.1\n• by Oculie"
  }
}
```

- pack_format 64（对应 Minecraft 1.21.8 - 即当前最新版本）。
- 描述简洁，包含版本号和作者信息，未使用 JSON text component 格式。
- 没有声明 supported_formats 范围，意味着仅在 pack_format 64 的版本中验证可用。

### 模型文件（models/block/）

每个火焰模型都继承自原版对应的模板模型，并将纹理引用切换到第二个动画帧：

```json
{
  "parent": "minecraft:block/template_fire_floor",
  "textures": {
    "fire": "minecraft:block/fire_2"
  }
}
```

- **fire_floor1.json**：继承 `template_fire_floor`，引用 `block/fire_2` 纹理。这是地面火焰的主要模型。
- **fire_side1.json**：继承 `template_fire_side`，引用 `block/fire_2`。
- **fire_side_alt1.json**：继承 `template_fire_side_alt`，引用 `block/fire_2`。
- **fire_up1.json**：继承 `template_fire_up`，引用 `block/fire_2`。
- **fire_up_alt1.json**：继承 `template_fire_up_alt`，引用 `block/fire_2`。
- 灵魂火对应模型同理，引用 `block/soul_fire_2`。

原版火焰 blockstate 定义了 3 组模型变体（0、1、2 三个随机变体），每组包含 floor、side、side_alt、up、up_alt 五个方向的模型。本包只覆盖了第 1 组变体（suffix `1`），而未覆盖第 0 组和备选变体。这是因为原版 blockstate 的变体通过随机权重分配，当某个变体的模型被覆盖时，火焰渲染仍然可以工作。

### 纹理文件（textures/block/）

本包的纹理策略是直接复用原版的第二个动画帧作为静态纹理：

- **fire_1.png / fire_2.png**：原版火焰的两个动画帧。本包将模型的纹理引用全部指向 `fire_2`（较矮的帧），使火焰在视觉上始终显示为较低的状态。
- **fire_1.png.mcmeta / fire_2.png.mcmeta**：
  ```json
  { "animation": {} }
  ```
  这些 .mcmeta 标记纹理为动画纹理。然而由于模型只引用了 fire_2，而 fire_1 虽然被标记为动画但实际上未被引用，因此该 .mcmeta 实际上没有效果。这可能是误留或为了兼容性保留。

实际上，本包降低火焰高度的机制不在于纹理替换，而在于**选择哪个动画帧**。原版火焰纹理有两个动画帧：fire_1 是较高的火焰，fire_2 是较矮的火焰。原版模型交替引用两个帧形成闪烁动画，而本包所有模型都仅引用 fire_2，从而固定显示为矮火焰。

不过这里有值得注意的地方：原版火焰纹理是动画纹理，fire_1 和 fire_2 各自独立动画。但本包将模型全部指向 fire_2，而 fire_2 本身也是动画纹理（包含多个子帧）。实际上 fire_2 本身的高度就在原版中较低，所以即使 fire_2 播放完整动画，整体火焰也比默认状态低。

灵魂火同理，soul_fire_2 比 soul_fire_1 的火焰轮廓更低。

## 技术特点

1. **极简设计**：仅 8 个模型 + 4 个纹理，代码逻辑极简。通过修改纹理引用实现功能，而不需要任何自定义模型或脚本。

2. **模型继承链**：所有火焰模型继承自原版的模板模型（`template_fire_floor`、`template_fire_side` 等），这些模板定义了火焰面片的几何结构和旋转方式。Low Fire 只修改纹理引用，充分利用了原版模板的几何定义。

3. **帧选择技巧**：这是本包的核心技术——通过选择原版火焰动画中的较矮帧来达到降低火焰视觉效果的目的。不是重新绘制纹理，也不是修改模型几何，而是在现有资源中选择合适的帧。

4. **静态帧锁定**：取消了原版火焰在两个高度帧之间的交替闪烁，使火焰始终保持较矮状态。副作用是火焰失去了部分动画效果（高度变化减少），但 Oculie 可能认为这是提升视野的合理取舍。

5. **灵魂火同步支持**：除了普通火焰，灵魂火也做了相同的处理，保持了两种火焰的风格统一。

## 结论

Low Fire 1.1.1 是一个极致简约但功能明确的 QoL 资源包，核心目标是在不破坏原版火焰视觉效果的前提下降低火焰高度，减少火焰对玩家视野的遮挡。其技术实现出奇简单——仅通过修改模型中的纹理引用，将火焰从较高的 fire_1 帧切换到较矮的 fire_2 帧，同时避免了两个帧之间的动态交替。

包的极简设计（仅 4 个纹理 + 8 个模型，大小几乎可以忽略不计）体现了"少即是多"的设计理念。不足之处在于：
1. 火焰动画效果有所减弱（高度变化减少）。
2. 只覆盖了随机变体 1，未覆盖全部变体，可能在某些视角下出现纹理错位。
3. 不支持 Overlay 系统，版本兼容性有限。

整体而言，对于受到火焰遮挡困扰的玩家来说，这是一个"装上就能解决问题"的轻量级实用型资源包。
