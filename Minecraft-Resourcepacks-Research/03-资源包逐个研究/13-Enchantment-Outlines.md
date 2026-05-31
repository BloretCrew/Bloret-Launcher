# 13. Enchantment Outlines

## 根目录结构

```
Enchantment Outlines/
├── pack.mcmeta
├── pack.png
├── credits.txt
├── respackopts.json5
├── assets/
│   └── minecraft/
│       ├── items/                    (物品模型定义 - 附魔条件分支)
│       ├── models/                   (3D 模型 - 附魔轮廓)
│       └── textures/item/            (2D 纹理 - 各材质工具)
├── 1.21.5/  (overlay - pack_format 46-55)
│   └── assets/minecraft/
│       ├── items/                    (附魔条件模型)
│       ├── models/                   (第一/三人称 3D 模型)
│       ├── textures/                 (第一/三人称附魔纹理)
│       └── shaders/core/             (物品实体渲染着色器)
├── 1.21.6/  (overlay - pack_format 56-65)
│   └── assets/minecraft/shaders/core/
├── 1.21.9/  (overlay - pack_format 65-75)
│   └── assets/minecraft/
│       ├── items/                    (含铜工具氧化版、盾牌、三叉戟、狼牙棒)
│       └── shaders/core/
├── 26.1/    (overlay - pack_format 84-128)
│   └── assets/minecraft/
│       ├── items/                    (含新版盾牌、铜工具氧化版)
│       └── shaders/core/
│           ├── item.fsh
│           └── item.vsh
└── __MACOSX/ (macOS 残留，忽略)
```

## 包定位

Enchantment Outlines 是一个专注于物品附魔外观增强的资源包，由 Tixul 制作（版本 1.10.5）。其核心功能是给所有附魔工具/武器添加 3D 轮廓线（outline），使附魔物品在手中有显著的视觉区分度。它不修改原版附魔闪光效果，而是额外叠加一层发光的轮廓模型。用户可以通过 Vanilla Tweaks 风格的选项配置（respackopts.json5）自定义显示风格。

## 关键文件说明

### pack.mcmeta

- **路径**: `Enchantment Outlines/pack.mcmeta`
- **pack_format**: 46
- **supported_formats**: [46, 84] — 覆盖 1.21.5 到 26.1
- **描述**: "Enchantment Outlines V1.10.5 | By Tixul"

使用了四层 overlay 系统：

| Overlay 目录 | pack_format 范围 | 版本对应 |
|---|---|---|
| `1.21.5` | 46~55 | 1.21.5 快照/正式版 |
| `1.21.6` | 56~65 | 1.21.6+ |
| `1.21.9` | 65~75 | 1.21.9+（含铜工具氧化版） |
| `26.1` | 84~128 | 26w+（含新版着色器管线） |

### credits.txt

- 致谢 Vanilla Tweaks、Orevill Studios 等多位贡献者和团队

### respackopts.json5

- 选项配置文件，包含功能切换能力：
  - `mace`: 支持 3D 或 2D 模式
  - `bow`: 支持 3D 或 2D 模式
  - `shieldIcon`: 支持 2D 或 3D 模式
  - 兼容性选项：
    - `bottleOEnchanting`: 原版 / Vanilla Tweaks 喷溅型
    - `shield`: 原版 / Vanilla Tweaks 低盾 / 侧面盾
    - `sword`: 原版 / Vanilla Tweaks 短剑
    - `copperTools`: 原版 / danis 氧化铜工具

## 资源内容结构

```
assets/minecraft/
├── items/              (物品模型定义文件 - JSON)
│   ├── bow.json
│   ├── diamond_axe.json
│   ├── diamond_sword.json
│   ├── shield.json
│   ├── trident.json
│   ├── mace.json
│   ├── copper_*.json
│   └── ...
├── models/             (3D 模型文件 - Blockbench JSON 格式)
│   ├── item/firstperson/<工具类型>/enchanted_*.json
│   └── item/thirdperson/<工具类型>/enchanted_*.json
└── textures/           (纹理贴图 - PNG)
    ├── item/<材质>/   (各材质工具的基础纹理)
    │   ├── sword.png
    │   ├── axe.png
    │   ├── pickaxe.png
    │   ├── shovel.png
    │   ├── hoe.png
    │   └── spear.png
    ├── item/misc/       (杂项 - 瓶子、盾牌、三叉戟等)
    └── item/bow/        (弓及附魔弓)
```

## 关键目录功能

### items/ - 附魔条件物品模型

这是 1.21.5+ 引入的最新物品模型系统。通过 `condition` 属性的 `has_component` 检测物品是否有 `minecraft:enchantments` 组件，实现附魔状态的条件分支。

**以钻石斧为例** (`items/diamond_axe.json`):
```json
{
  "model": {
    "type": "minecraft:condition",
    "property": "minecraft:has_component",
    "component": "minecraft:enchantments",
    "ignore_default": true,
    "on_true": {
      "type": "minecraft:select",
      "property": "minecraft:display_context",
      "cases": [
        { "when": ["firstperson_lefthand", "firstperson_righthand"],
          "model": { "type": "minecraft:model", "model": "item/firstperson/axe/enchanted_diamond_axe" } },
        { "when": ["gui"],
          "model": { "type": "minecraft:model", "model": "minecraft:item/diamond_axe" } }
      ],
      "fallback": { "type": "minecraft:model", "model": "item/thirdperson/axe/enchanted_diamond_axe" }
    },
    "on_false": { "type": "minecraft:model", "model": "minecraft:item/diamond_axe" }
  }
}
```

**核心逻辑**：
- 检测附魔组件 → 是 → 使用带轮廓的自定义 3D 模型
- 检测附魔组件 → 否 → 使用原版模型

第一人称和第三人称使用不同的 3D 模型文件（视角适配），GUI 中则保持原版显示以节省性能。

**弓的特殊处理** (`items/bow.json`)：
弓的模型更为复杂，因为弓有多个 pulling 状态。包通过 `range_dispatch` 基于 `use_duration` 属性实现附魔弓的拉弓动画分支，同样区分第一人称/第三人称/GUI 三种显示上下文。

### models/ - 3D 轮廓模型

使用 Blockbench 格式的 JSON 模型，核心特征是所有轮廓元素都设置了 `"light_emission": 15`（最大发光值），使得轮廓在任何光照条件下始终可见。

**模型结构**：
- 由本体元素群组（enchanted_*）和轮廓元素群组（outline）组成
- 本体使用各工具纹理映射（texture #0）
- 轮廓使用专门的 `axe_outline.png` 纹理（texture #1）
- 使用 `display` 字段定义不同的透视变换（第三人称、第一人称）

### textures/ - 纹理资产

纹理系统分为两层：

1. **各材质工具基础纹理**：`item/<材质>/` 目录下包含剑、斧、镐、锹、锄、矛的 PNG 纹理，覆盖所有六种工具材质（木、石、铁、金、钻、下界合金、铜）。

2. **杂项物品纹理**：`item/misc/` 包含附魔瓶、盾牌、三叉戟、狼牙棒、刷子、打火石、不死图腾、鞘翅等物品的附魔版本纹理。

3. **弓与弩**：`item/bow/` 和 `item/crossbow/` 包含拉弓各阶段的附魔纹理。

4. **第一/三人称专用纹理**：overlay 目录中的 `textures/item/firstperson/` 和 `textures/item/thirdperson/` 包含视角校正后的纹理。

### shaders/ - 透明物品渲染着色器

**核心着色器**: `rendertype_item_entity_translucent_cull`（顶点 + 片元）

该着色器根据纹理像素的 Alpha 通道值分流渲染：

```glsl
switch (icol.a) {
    case 200: break;                   // 特殊标记，不乘 vertexColor
    case 252: color *= vertexColor;    // 自定义渲染
    case 253: color *= vertexColor;
    default: color *= lightColor * vertexColor;  // 标准物品渲染
}
```

- Alpha=200 的像素：专为轮廓预留的通道，不会被光照颜色修正
- Alpha=252/253：自定义渲染路径
- 默认：使用光照颜色和顶点颜色的标准乘法

**新版着色器**（26.1 overlay）：使用了全新的 `item.fsh` / `item.vsh` 着色器管线，适配 Minecraft 26w+ 的渲染架构变化。

## 技术特点

1. **组件化条件模型系统**：使用 1.21.5+ 的 `has_component` 物品组件条件检测，替代了旧版的 NBT 检测或 CTM/ CIT，这是 Minecraft 原版资源包系统的最新进化。

2. **多视角 3D 模型**：每个工具都拥有独立的第一人称和第三人称 3D 模型，确保在不同视角下都能正确显示轮廓。

3. **Overlay 多版本支持**：通过 4 层 overlay 覆盖从 1.21.5 到最新 26w+ 的所有版本，每一层适配对应版本的着色器和物品格式变化。

4. **发光轮廓（light_emission: 15）**：所有轮廓模型元素设置最大自发光值，使其不依赖环境光照即可可见。

5. **Respack-Opts 配置系统**：使用 `respackopts.json5` 提供用户可配置选项（弓/盾/剑的风格选择，铜工具氧化兼容）。

6. **铜工具氧化兼容**：`1.21.9` 和 `26.1` overlay 中包含铜工具氧化变体的模型定义和 `.rpo` 选项文件。

7. **着色器 Alpha 通道分流**：通过自定义着色器实现 alpha 通道的特殊处理，使得轮廓渲染不受标准光照影响。

## 结论

Enchantment Outlines 是 Minecraft 1.21.5+ 版本物品模型系统的典范级应用。它深度使用了条件物品模型（condition + has_component）、多视角 3D Blockbench 模型、自定义着色器（透明物品实体渲染）以及 overlay 版本管理系统。该包的技术亮点在于完全利用原版资源包能力（而非模改）实现附魔物品的视觉增强，同时通过 respackopts 系统提供用户自定义配置。这在技术上代表了 Minecraft 资源包开发在 1.21.5+ 时代的先进水平。
