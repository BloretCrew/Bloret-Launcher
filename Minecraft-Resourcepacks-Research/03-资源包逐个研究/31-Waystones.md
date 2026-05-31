# 31. Waystones 1.21.8

## 根目录结构

```
waystones_1.21.8/
├── assets/
│   ├── minecraft/
│   │   ├── atlases/
│   │   │   ├── blocks.json    # 方块图集附加源
│   │   │   └── gui.json       # GUI 图集附加源
│   │   └── textures/
│   │       ├── waystone_overlays/
│   │       │   ├── portstone.png
│   │       │   ├── sharestone_color.png
│   │       │   └── waystone_active.png
│   │       └── waystones_gui/
│   │           ├── inventory_button.png
│   │           ├── modifier_button.png
│   │           ├── modifier_button_highlighted.png
│   │           ├── small_button_blank.png
│   │           ├── small_button_blank_highlighted.png
│   │           ├── visibility_button_activation.png
│   │           ├── visibility_button_activation_highlighted.png
│   │           ├── visibility_button_global.png
│   │           ├── visibility_button_global_highlighted.png
│   │           ├── visibility_button_shard_only.png
│   │           ├── visibility_button_shard_only_highlighted.png
│   │           ├── visibility_button_sharestone.png
│   │           └── visibility_button_sharestone_highlighted.png
│   └── waystones/
│       ├── blockstates/
│       │   ├── black_sharestone.json
│       │   ├── blue_sharestone.json
│       │   ├── brown_sharestone.json
│       │   ├── cyan_sharestone.json
│       │   ├── gray_sharestone.json
│       │   ├── green_sharestone.json
│       │   ├── light_blue_sharestone.json
│       │   ├── light_gray_sharestone.json
│       │   ├── lime_sharestone.json
│       │   ├── magenta_sharestone.json
│       │   ├── mossy_waystone.json
│       │   ├── orange_sharestone.json
│       │   ├── pink_sharestone.json
│       │   ├── portstone.json
│       │   ├── purple_sharestone.json
│       │   ├── red_sharestone.json
│       │   ├── sandy_waystone.json
│       │   ├── sharestone.json
│       │   ├── warp_plate.json
│       │   ├── waystone.json
│       │   ├── white_sharestone.json
│       │   └── yellow_sharestone.json
│       ├── lang/
│       │   ├── en_us.json
│       │   ├── fr_fr.json
│       │   ├── hu_hu.json
│       │   ├── ko_kr.json
│       │   ├── pt_br.json
│       │   ├── ru_ru.json
│       │   ├── uk_ua.json
│       │   ├── zh_cn.json
│       │   └── zh_tw.json
│       ├── models/
│       │   ├── block/
│       │   │   ├── blackstone_waystone_bottom.json
│       │   │   ├── blackstone_waystone_top.json
│       │   │   ├── deepslate_waystone_bottom.json
│       │   │   ├── deepslate_waystone_top.json
│       │   │   ├── end_stone_waystone_bottom.json
│       │   │   ├── end_stone_waystone_top.json
│       │   │   ├── landing_stone.json
│       │   │   ├── mossy_waystone_bottom.json
│       │   │   ├── mossy_waystone_top.json
│       │   │   ├── portstone_bottom.json
│       │   │   ├── portstone_top.json
│       │   │   ├── sandy_waystone_bottom.json
│       │   │   ├── sandy_waystone_top.json
│       │   │   ├── sharestone_bottom.json
│       │   │   ├── sharestone_top.json
│       │   │   ├── warp_plate.json
│       │   │   ├── waystone_bottom.json
│       │   │   └── waystone_top.json
│       │   ├── item/
│       │   │   ├── attuned_shard.json
│       │   │   ├── blackstone_waystone.json
│       │   │   ├── blank_scroll.json
│       │   │   ├── bound_scroll.json
│       │   │   ├── crumbling_attuned_shard.json
│       │   │   ├── deepslate_shard.json
│       │   │   ├── deepslate_waystone.json
│       │   │   ├── dormant_shard.json
│       │   │   ├── end_stone_waystone.json
│       │   │   ├── mossy_waystone.json
│       │   │   ├── portstone.json
│       │   │   ├── return_scroll.json
│       │   │   ├── sandy_waystone.json
│       │   │   ├── sharestone.json
│       │   │   ├── warp_dust.json
│       │   │   ├── warp_scroll.json
│       │   │   ├── warp_stone.json
│       │   │   └── waystone.json
│       │   └── scoped_sharestone.json
│       ├── textures/
│       │   ├── block/
│       │   │   ├── andesite_wayston.png
│       │   │   ├── andesite_wayston_top.png
│       │   │   ├── andesite_waystone_botton.png
│       │   │   ├── blackstone_waystone.png
│       │   │   ├── blackstone_waystone_botton.png
│       │   │   ├── blackstone_waystone_top.png
│       │   │   ├── chiseled_sandstone_waystone.png
│       │   │   ├── chiseled_sandstone_waystone_botton.png
│       │   │   ├── chiseled_sandstone_waystone_top.png
│       │   │   ├── deepslate_waystone.png
│       │   │   ├── deepslate_waystone_bottom.png
│       │   │   ├── deepslate_waystone_top.png
│       │   │   ├── end_stone_waystone.png
│       │   │   ├── end_stone_waystone_bottom.png
│       │   │   ├── end_stone_waystone_top.png
│       │   │   ├── landing_stone.png
│       │   │   ├── moss_template.png
│       │   │   ├── mossy_waystone.png
│       │   │   ├── mossy_waystone_botton.png
│       │   │   ├── mossy_waystone_top.png
│       │   │   ├── mossy_waystone_top_overlay.png
│       │   │   ├── portstone_runes.png
│       │   │   ├── portstone_top.png
│       │   │   ├── portstone_top_botton.png
│       │   │   ├── portstone_top_top.png
│       │   │   ├── sharestone_botton.png
│       │   │   ├── sharestone_top.png
│       │   │   └── warp_plate.png
│       │   ├── entity/
│       │   │   ├── portstone.png
│       │   │   ├── sharestone_color.png
│       │   │   └── waystone_active.png
│       │   ├── gui/
│       │   │   ├── checkbox.png
│       │   │   ├── inventory_button.png
│       │   │   └── jei/warp_plate.png
│       │   │   └── menu/warp_plate.png
│       │   └── item/
│       │       ├── attuned_shard.png
│       │       ├── blank_scroll.png
│       │       ├── bound_scroll.png
│       │       ├── crumbling_attuned_shard.png
│       │       ├── deepslate_shard.png
│       │       ├── dormant_shard.png
│       │       ├── return_scroll.png
│       │       ├── warp_dust.png
│       │       ├── warp_scroll.png
│       │       ├── warp_stone.png
│       │       └── waystone/
│       │           ├── andesite_waystone.png
│       │           ├── blackstone_waystone.png
│       │           ├── deepslate_waystone.png
│       │           ├── end_stone_waystone.png
│       │           ├── mossy_waystone.png
│       │           ├── portstone.png
│       │           ├── sandy_waystone.png
│       │           ├── sharestone.png
│       │           ├── sharestone_color.png
│       │           └── waystone.png
├── pack.mcmeta
└── pack.png
```

## 包定位

作者：zozozrob。目标版本 Minecraft 1.21.8。本包是 **Waystones Mod**（传送石碑 Mod）的配套资源包，提供传说石碑 Mod 所需的自定义纹理、模型、blockstates 以及语言文件。它是一个**辅助性/功能性**资源包，与 Mod 共同工作，本身不独立提供功能。

Waystones Mod（通常由 Blay09 开发，或 BlameJared 维护的 Fabric/Forge 版本）是 Minecraft 最流行的传送系统 Mod 之一，在全球范围内拥有大量用户。本资源包为该 Mod 提供了纹理增强、多语言支持和定制化的 GUI 元素。

值得注意的是，本包中的 Waystone 指代的是 Mod 中的传送石碑方块/物品，与 Minecraft 原版中的磨制安山岩/切制砂岩等结构相对应，为每种材质的传送石碑提供了独立的材质纹理。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 15,
    "supported_formats": {"min_inclusive": 15, "max_inclusive": 99},
    "description": "Author: zozozrob"
  }
}
```

- pack_format 15（对应 1.20），supported_formats 上限 99 覆盖到较远的未来版本。
- 描述简洁，仅有作者信息，未提供更多细节。

### assets/minecraft/atlases/ 图集配置

**blocks.json**:
```json
{
  "sources": [
    { "type": "directory", "source": "waystone_overlays", "prefix": "waystone_overlays/" }
  ]
}
```

**gui.json**:
```json
{
  "sources": [
    { "type": "directory", "source": "waystones_gui", "prefix": "waystones/" }
  ]
}
```

这两份配置文件利用 Minecraft 1.19.3+ 引入的图集（Atlas）系统，将自定义纹理目录注册到对应的纹理图集中：

- **blocks 图集**：注册 `waystone_overlays/` 目录，Mod 中的 Waystone 方块可以使用这些纹理作为覆盖层（overlays），在传送石碑激活时显示发光符文图案。
- **gui 图集**：注册 `waystones_gui/` 目录，Mod 的 GUI 界面可以加载这些按钮/控件纹理。

这种图集注册机制是 Mod 资源包的标准做法——Mod 通过原版图集系统加载自定义纹理，而无需使用 Mod 独有加载器。

### waystone_overlays（方块覆盖纹理）

- **waystone_active.png**：传送石碑激活状态下的符文覆盖纹理，在石碑的方块模型上叠加显示发光的传送符文。
- **portstone.png**：传送石（Portstone）的覆盖纹理。
- **sharestone_color.png**：共享石（Sharestone）的彩色覆盖纹理，可能用于区分不同颜色的共享石网络。

这些覆盖纹理利用 Minecraft 的方块模型叠加（overlay）机制，在原有石碑材质上增加一层符文/发光效果，使激活状态的石碑与未激活状态有明显视觉区分。

### waystones_gui（GUI 控件纹理）

该目录包含 Mod 自定义 GUI 的所有按钮和控件纹理：

- **inventory_button.png**：背包界面中的传送按钮，点击打开传送石碑 GUI。
- **modifier_button.png / modifier_button_highlighted.png**：修改器按钮及其高亮状态。
- **small_button_blank.png / small_button_blank_highlighted.png**：小型空白按钮及其高亮。
- **visibility_button_*** 系列：6 种可见性设置按钮（activation、global、shard_only、sharestone），每种都有普通和高亮两种状态，用于控制传送石碑的可见性和使用权限。

### blockstates/（方块状态）

22 个 blockstates 文件覆盖了 Waystones Mod 所有方块变体：

- **waystone.json**：基础传送石碑，使用 `waystone_bottom` 和 `waystone_top` 模型。
- **mossy_waystone.json**：覆苔传送石碑（自然生成在废墟中）。
- **sandy_waystone.json**：砂岩传送石碑（沙漠群系自然生成）。
- **blackstone_waystone.json**：黑石传送石碑（下界群系自然生成）。
- **deepslate_waystone.json**：深板岩传送石碑。
- **end_stone_waystone.json**：末地石传送石碑（末地生成）。
- **portstone.json**：传送石方块（允许传送到绑定的石碑）。
- **sharestone.json + 16 色彩色变体**：共享石（连接同一颜色网络的传送点），每种颜色对应一个独立的 blockstate 文件。
- **warp_plate.json**：传送板（类似压力板的传送装置）。
- **landing_stone.json**：着陆石（用于标记传送落点，仅含模型无 blockstate 引用）。

### models/（模型）

**block/（方块模型，18 个）**：
每个传送石碑由上下两部分组成（bottom + top），通过 blockstate 连接成一个完整的 2 方块高石碑模型。这种分离模型设计使得石碑可以适应不同高度和方向。此外还有 warp_plate（传送板，单方块）和 landing_stone（着陆石）。

**item/（物品模型，18 个）**：
物品模型包括各种传送道具：scroll（传送卷轴，含空白/绑定/回城/传送 4 种）、shard（碎片，含共鸣/深板岩/休眠/碎裂 4 种）、warp_stone（传送石）、warp_dust（传送粉）以及各种材质的石碑物品形式。

### textures/block/（方块纹理，28 个）

传送石碑使用了多种 Minecraft 原生石材的纹理风格设计：

| 石碑类型 | 纹理风格 |
|----------|----------|
| 默认（安山岩） | 灰色石材，带符文雕刻纹路 |
| 黑石 | 深色纹理，适合下界环境 |
| 深板岩 | 深色纹理，与深板岩风格一致 |
| 末地石 | 浅黄色，末地风格 |
| 砂岩 | 沙漠色，切制砂岩风格 |
| 覆苔 | 带苔藓覆盖层 |

每个石碑材质有三面纹理：主体侧面（waystone.png）、底部（_botton.png）、顶部（_top.png）。portstone 额外有符文纹理（portstone_runes.png）和顶部多层结构。

### textures/entity/（实体纹理，3 个）

实体纹理用于传送石碑在世界中的实体渲染：
- **waystone_active.png**：激活石碑实体的纹理。
- **portstone.png**：传送石实体纹理。
- **sharestone_color.png**：共享石彩色实体纹理。

### textures/item/（物品纹理，21 个）

包含所有 Waystones Mod 物品的纹理：
- **scroll/（卷轴）**：blank_scroll.png（空白）、bound_scroll.png（绑定）、return_scroll.png（回城）、warp_scroll.png（传送）。
- **shard/（碎片）**：attuned_shard.png（共鸣）、dormant_shard.png（休眠）、deepslate_shard.png（深板岩）、crumbling_attuned_shard.png（碎裂）。
- **warp_stone.png**：传送石，用于绑定石碑位置。
- **warp_dust.png**：传送粉，消耗品。
- **waystone/（物品栏中的石碑图标）**：每种材质对应一个 PNG，位于 waystone/ 子目录。

### lang/（语言文件，9 个）

包含多种语言的支持：英文（en_us）、法文（fr_fr）、匈牙利文（hu_hu）、韩文（ko_kr）、葡萄牙巴西文（pt_br）、俄文（ru_ru）、乌克兰文（uk_ua）、简体中文（zh_cn）、繁体中文（zh_tw）。

## 技术特点

1. **图集系统注册**：利用原版 Atlas 系统（atlases/）注册自定义纹理目录，供 Mod 使用，这是 Mod 资源包的标准兼容做法。

2. **分离式方块模型**：将 2 方块高的传送石碑拆分为 bottom 和 top 两个模型，通过 blockstate 组合。这种分离设计支持不同高度的石碑和灵活的世界放置。

3. **多材质变体**：传送石碑有 6 种材质变体（默认安山岩、黑石、深板岩、末地石、砂岩、覆苔），各材质纹理风格与对应的原版石材一致，保持了视觉一致性。

4. **完整的物品体系**：包括 4 种卷轴、4 种碎片、传送石、传送粉等在内的完整物品纹理和模型覆盖，形成了完善的传送道具体系。

5. **覆盖纹理叠加**：使用 overlay 机制在石碑方块上叠加符文发光效果，区分激活和未激活状态，这是 1.19.3+ 方块模型系统的特色功能。

6. **GUI 控件高亮系统**：所有按钮都有普通和高亮两种状态，提供完整的交互反馈。

7. **共享石颜色系统**：16 种颜色的共享石，每种有独立的 blockstate，通过纹理颜色区分不同的传送网络。

8. **多语言支持**：9 种语言，包括中韩日法俄等主要玩家语言，但相比 Enchant Icons（137 种语言）覆盖范围较小。

## 结论

Waystones 1.21.8 是一个功能完善的 Mod 配套资源包，为 Waystones Mod 提供了全套的自定义纹理、模型、blockstates、图集注册和多语言支持。包体量大但条理清晰，涵盖了传送石碑 Mod 的所有核心功能元素：多种材质的石碑、4 种传送卷轴、4 种碎片道具、激活状态符文覆盖、16 色共享石网络，以及完整的 GUI 控件体系。

技术实现上全面采用了 Minecraft 的最新机制（Atlas 系统、方块模型覆盖、分离式模型等），体现了对原版资源系统的深入理解。多材质石碑的纹理设计保持了与原版石材风格的一致性。不足之处在于包名未包含版本号格式规范，且无 README 或使用说明。整体而言，对于安装 Waystones Mod 的玩家来说，这是一个不可或缺的官方级资源包。
