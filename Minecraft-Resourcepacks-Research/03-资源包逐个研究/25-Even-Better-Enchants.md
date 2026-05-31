# 25. Even Better Enchants v3

## 根目录结构

```
EvenBetterEnchants_v3_1.21.5+/
├── assets/
│   └── minecraft/
│       ├── items/
│       │   └── enchanted_book.json
│       ├── models/
│       │   └── item/
│       │       ├── .big_enchanted_book.json
│       │       └── [129 个附魔等级模型]
│       └── textures/
│           └── item/
│               ├── .big_enchanted_book.png
│               └── [129 个对应纹理]
├── pack.mcmeta
├── pack.png
└── README.txt
```

## 包定位

作者：Mythitorium，基于 Yomna 的 Better Enchant Books 素材进行二次开发。版本 v3，目标版本为 Minecraft 1.21.5+。本包为典型的"附魔书美化"类资源包，核心目标是为每种附魔的每一等级分配独立的 Custom Model Data 覆盖模型，使附魔书在物品栏中呈现不同的图标外观。

与传统的单纹理替换不同，Even Better Enchants 使用了 **Custom Model Data 覆盖系统**，通过一个统一的 `enchanted_book.json` 总入口，映射到 125 个（含大图标共 129 个）独立的等级模型文件。这是一种典型的程序化/数据驱动资源包设计模式。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 32,
    "min_format": [32,0],
    "max_format": [999,0],
    "supported_formats": [32, 999],
    "description": "by Mythitorium\nv3 - 1.21.5+"
  }
}
```

- pack_format 为 32（对应 Minecraft 1.21.5+）。
- supported_formats 范围从 32 到 999，意味着向后兼容 1.21.5 以上所有预期版本，同时向前兼容到几乎无限远（999）。这是一种激进的做法，意味着作者认为模型/纹理格式在未来不会发生破坏性变更。
- 未使用 overlays 系统，因为整体修改范围单一且集中。

### README.txt

明确说明使用了 Yomna 的 Better Enchant Books 素材，保留所有权利（All rights reserved）。在资源包许可证方面采用了保守策略。

### assets/minecraft/items/enchanted_book.json

这是 1.21.5+ 新增的 items 数据格式文件。该文件控制游戏中 `enchanted_book` 物品的模型映射。在 1.21.5 中，Mojang 引入了独立的 items JSON 层，将物品 ID 与模型 ID 解耦。

## 资源内容结构

### 模型系统架构

所有附魔模型都位于 `assets/minecraft/models/item/` 目录下。核心设计为：

1. **入口模型**：`enchanted_book.json`，继承自 `item/generated`，图层 0 指向 `item/enchanted_book`（基础纹理）。
2. **覆盖规则**：在该模型上定义了 125 个 `overrides`，每个覆盖规则根据 `custom_model_data` 谓词（predicate）值触发：
   - custom_model_data 1 → `aqua_affinity_1`
   - custom_model_data 2 → `bane_of_arthropods_1`
   - ...以此类推，覆盖所有附魔类型和等级的组合。
3. **独立模型**：每个附魔等级对应一个独立的 JSON 模型文件，继承自 `item/generated`，指向对应的自定义纹理。例如 `sharpness_5.json` 引用 `item/sharpness_5`。

这种架构使得每个附魔书图标可以根据其 NBT 中的 CustomModelData 标签动态切换外观。

### 附魔覆盖范围

包覆盖了 Minecraft 1.21.5 中所有 39 种附魔类型，包括：

- **武器附魔**：sharpness (1-5), smite (1-5), bane_of_arthropods (1-5), fire_aspect (1-2), looting (1-3), sweeping_edge (1-3), knockback (1-2)
- **护甲附魔**：protection (1-4), blast_protection (1-4), fire_protection (1-4), projectile_protection (1-4), feather_falling (1-4), thorns (1-3), respiration (1-3), aqua_affinity (1), depth_strider (1-3), frost_walker (1-2), soul_speed (1-3), swift_sneak (1-3), binding_curse (1)
- **工具附魔**：efficiency (1-5), fortune (1-3), silk_touch (1), unbreaking (1-3), mending (1)
- **弓/弩附魔**：power (1-5), punch (1-2), flame (1), infinity (1), quick_charge (1-3), multishot (1), piercing (1-4)
- **三叉戟附魔**：loyalty (1-3), impaling (1-5), riptide (1-3), channeling (1)
- **钓鱼附魔**：luck_of_the_sea (1-3), lure (1-3)
- **1.21+ 新附魔**：density (1-5), breach (1-4), wind_burst (1-3), mace 系
- **诅咒**：vanishing_curse (1), binding_curse (1)
- **其他**：lunge (1-3), 注意 lunge 为 1.21.5+ 的新增附魔

## 关键目录功能

### models/item/ 目录

- 129 个 JSON 模型文件，每个模型对应一个附魔等级。
- 额外包含一个 `.big_enchanted_book.json`（带点前缀的隐藏文件），可能是备用大图标模型。
- 每个模型的父级均为 `minecraft:item/generated`，纹理引用 `minecraft:item/<附魔名称>_<等级>`。

### textures/item/ 目录

- 129 个 PNG 纹理文件，每个尺寸为标准的 16x16。
- 每个纹理在原始附魔书紫色背景上叠加了不同的附魔主题图标，部分带有等级标识数字。
- 通过重新设计每个附魔的图案和颜色，使玩家可以一眼识别附魔类型和等级，无需悬停查看名称。

### items/ 目录

- 1 个文件 `enchanted_book.json`，这是 1.21.5 新增的 items 数据格式。
- 在该文件中定义了附魔书的模型引用，指向 `minecraft:item/enchanted_book`（即 models/item/enchanted_book.json）。

## 技术特点

1. **Custom Model Data 系统**：利用 Minecraft 原版的 `overrides` + `custom_model_data` 谓词机制，实现在单一物品 ID 上呈现多种视觉变体。这是目前最兼容的模型替换方式，不需要任何 Mod 支持。

2. **等级可视化**：为每个附魔的每个等级都制作了独立的纹理，而不仅仅是替换基础纹理。这在原版机制下需要服务端配合设置 CustomModelData，但在纯视觉资源包中，通常配合附魔描述 Mod（如 Enchantment Descriptions）使用。

3. **覆盖所有新附魔**：包含了 1.21 新增的 density、breach、wind_burst 以及 lunge 附魔，说明版本更新及时，覆盖面完整。

4. **标准继承链**：所有模型都继承自 `item/generated`，这是最简单的物品模型基类，保证了最大的兼容性。

5. **超大支持格式范围**：`supported_formats` 设置为 32 到 999，覆盖了从当前版本到未来任何版本。简化了维护，但风险在于如果 Mojang 更改模型格式，该包在未来的版本中可能会加载异常。

## 结论

Even Better Enchants v3 是一个高质量、高度细化的附魔书美化资源包。通过自定义模型覆盖系统，为每种附魔的每一等级提供了独立的纹理设计。技术实现上完全基于原版机制（Custom Model Data），不需要 OptiFine 或其他 Mod。总计 129 个模型/纹理对，覆盖了 Minecraft 1.21.5 的全部 39 种附魔，是同类资源包中覆盖最全面、等级区分最精细的作品之一。配合附魔描述类 Mod 使用时可以充分发挥其视觉优势，是目前附魔美化领域的标杆级资源包。
