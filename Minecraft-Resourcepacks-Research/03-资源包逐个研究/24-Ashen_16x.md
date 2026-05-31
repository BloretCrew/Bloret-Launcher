# 23. Ashen_16x
## 根目录结构
```
Ashen_16x/
├── pack.mcmeta
├── pack.png
├── overlay_22-43/
├── overlay_22-46/
├── overlay_22-54/
├── overlay_22-83/
└── assets/
    ├── ashen/
    │   └── polytone/
    │       └── colormaps/
    ├── cursors_extended/
    │   └── textures/
    │       └── gui/sprites/cursors/
    ├── entity_features/
    │   └── textures/gui/
    ├── minecraft/
    │   ├── blockstates/
    │   ├── items/
    │   ├── lang/
    │   ├── models/
    │   │   ├── block/
    │   │   └── item/
    │   ├── optifine/
    │   │   ├── cit/ (axolotls, bread, bushels, display/shields, display/swords, egg, incendium, map)
    │   │   ├── colormap/custom/
    │   │   ├── ctm/ (bricks, fire, flowers, glass, overlays, stones, tiles, wools)
    │   │   └── random/entity/ (chicken, cow, creeper, illager, pig, piglin, rabbit, skeleton, sniffer, villager, warden, zombie, zombie_villager)
    │   ├── particles/
    │   ├── polytone/
    │   │   ├── biome_effects/
    │   │   └── block_modifiers/
    │   └── textures/
    │       ├── block/
    │       ├── colormap/
    │       ├── entity/ (数十种生物)
    │       ├── environment/
    │       ├── gui/ (container, sprites 等)
    │       ├── item/
    │       ├── map/
    │       ├── misc/
    │       ├── mob_effect/
    │       ├── painting/
    │       └── particle/
    ├── minecraft-cursor/
    ├── modmenu/
    └── realms/
```

## 包定位
Ashen_16x 是一款 16x 分辨率的中世纪奇幻风格 Minecraft 资源包，版本号为 v1.15.5。它的核心定位是在保持与原版相同分辨率（16x）的前提下，对游戏的视觉风格进行全面的中世纪化改造。不同于 Faithful 32x 追求"高清原版"，Ashen 追求的是"风格化重制"——用灰暗、粗犷、中世纪 fantasy 的美学重新诠释 Minecraft 的每一寸纹理。

本包兼容从 1.20（pack_format 22）到最新版本的 Minecraft，通过四个 Overlay 目录实现跨版本兼容。

## 关键文件说明

### pack.mcmeta
```json
{
  "pack": {
    "pack_format": 84,
    "min_format": [22,0],
    "max_format": [84,0],
    "supported_formats": [22,84],
    "description": "A 16px, medieval-fantasy take on Minecraft. v1.15.5"
  },
  "overlays": {
    "entries": [
      {"directory": "overlay_22-43", "formats": [22, 43]},
      {"directory": "overlay_22-46", "formats": [22, 46]},
      {"directory": "overlay_22-54", "formats": [22, 54]},
      {"directory": "overlay_22-83", "formats": [22, 83]}
    ]
  }
}
```
采用了极其完善的版本兼容策略：
- 基础目录适用于 pack_format 84（Minecraft 1.21.5-1.21.8）
- 四个 Overlay 分别覆盖 22-43、22-46、22-54、22-83 的版本区间
- 这种设置确保了从 1.20 到 1.21.8 的所有版本都能正确加载对应的资源

### 总览
Ashen_16x 共有 9360 个文件和目录（其中目录约 430 个），总大小约 2.3GB，是本次分析中规模最庞大的资源包。其完整的资源覆盖包括方块纹理、生物纹理、GUI、粒子、音效配置、模型、语言文件、粒子配置等。

## 资源内容结构

### 纹理系统
Ashen_16x 拥有几乎完整的纹理覆盖：

**block/** 方块纹理目录包含所有原版方块的中世纪风格重新纹理。从石材、木材到金属和有机方块，每种纹理都经过重新设计，呈现出风化、古老、手工打造的外观。色调偏向灰暗、棕色和暗绿色系，营造中世纪 fantasy 氛围。

**entity/** 生物纹理覆盖极其全面，包括：
- 被动生物：allay, armadillo, axolotl, bat, bee, camel, cat, chicken, cow, fish (多种), fox, frog, goat, horse (多种), llama, panda, parrot, pig, rabbit, sheep, sniffer, squid, strider, tadpole, turtle, wolf
- 中立/敌对生物：blaze, breeze, cave_spider, creeper, ender_dragon, enderman, ghast, hoglin, illager (多种), iron_golem, piglin (多种), shulker, skeleton (多种), slime, spider, warden, wither, zombie (多种)
- 特殊实体：armorstand, boat (多种), chest, chest_boat, conduit, copper_golem, decorated_pot, end_crystal, minecart, shield, signs (含悬挂式), projectile
- 村民系列：villager（含职业和等级变体）、zombie_villager（含职业和等级变体）
- 1.21 新增：breeze, creaking

**equipment/** 装备纹理包括狼铠、骆驼鞍、马铠、猪鞍、翼等。

### 模型系统
Ashen 拥有大量的自定义模型：
- **models/block/** - 方块的 Block Model 定义
- **models/item/** - 物品的 Item Model 定义

### 物品定义
**items/** 目录使用 Minecraft 1.21 的新物品定义系统，替代了旧版的模型定义。

### 粒子系统
**particles/** 包含自定义粒子效果配置。

### OptiFine 扩展
Ashen 拥有巨大的 OptiFine 扩展体系：

**ctm/**（连接纹理）：
- **glass/** - 16 种染色玻璃 + 普通玻璃 + 遮光玻璃的连接纹理
- **overlays/** - 超过 40 种方块的叠加纹理系统（用于草地、菌丝、雪地、石头、砖块等）
- **bricks/** - 砖块连接纹理（含下界砖、红砖等）
- **wools/** - 羊毛及地毯连接纹理（16 色）
- **stones/** - 石质方块连接纹理（砂岩、红砂岩等）
- **tiles/** - 深板岩连接纹理
- **flowers/** - 植物连接纹理（仙人掌、地衣、甘蔗、藤蔓）
- **fire/** - 火焰连接纹理

**cit/**（自定义物品纹理）：
- axolotls - 美西螈桶 CIT
- bread - 面包自定义纹理
- bushels - 蒲式耳（农作物）自定义纹理
- display/shields - 盾牌展示
- display/swords - 剑展示
- egg - 鸡蛋
- incendium - 针对 Incendium 模组的自定义纹理
- map - 地图

**random/entity/**（随机生物纹理）：
- 为 chicken, cow, creeper, illager, iron_golem, pig, piglin, rabbit, skeleton, sniffer, villager, warden, zombie, zombie_villager 提供随机纹理变体

**colormap/** 自定义色彩映射。

### 模组兼容
- **ashen/polytone/** - Polytone 模组支持，包含自定义色彩映射（colormaps）
- **cursors_extended/** - 自定义鼠标光标扩展
- **entity_features/** - 生物特征模组支持
- **minecraft-cursor/** - Minecraft Cursor 模组支持
- **modmenu/** - Mod Menu 模组图标
- **realms/** - Realms 界面纹理

### Polytone 模组集成
**polytone/** 目录包含：
- **biome_effects/** - 生物群系特效配置（自定义生物群系的视觉效果）
- **block_modifiers/** - 方块修改器配置

## Overlay 版本系统
四个 Overlay 目录确保了跨版本兼容：
- overlay_22-43: 覆盖 pack_format 22-43 (1.20-1.20.4)
- overlay_22-46: 覆盖 pack_format 22-46 (扩展至 1.20.5+)
- overlay_22-54: 覆盖 pack_format 22-54 (扩展至 1.21-1.21.3)
- overlay_22-83: 覆盖 pack_format 22-83 (扩展至 1.21.4-1.21.5)

每个 Overlay 可能包含与主目录结构相同的子目录，用于提供适用于特定版本的纹理变体。

## 技术特点

1. **全面覆盖的规模**：9360 个文件、2.3GB 大小使其成为社区中规模最大的 16x 风格化资源包之一。其纹理覆盖范围几乎与原版 1:1 对应。

2. **统一的美术风格**：不同于许多风格化包只修改部分纹理，Ashen 对几乎所有视觉元素进行了统一的中世纪风格化处理。从方块到生物、从 GUI 到粒子，呈现出高度一致的艺术风格。

3. **OptiFine 深度利用**：充分利用 OptiFine 的连接纹理（CTM）、自定义物品纹理（CIT）、随机生物纹理三大系统，极大丰富了视觉效果。

4. **叠加纹理系统**：overlays CTM 系统是本包最突出的技术亮点之一——通过对草地、菌丝、灰化土、石头、砖块等方块使用叠加纹理，实现了丰富的纹理变体，避免了重复纹理带来的单调感。将 overlay 系统与 CTM 结合使用，在 16x 基础上创造了视觉丰富度远超原版的体验。

5. **Overlay 版本兼容**：使用四个 Overlay 目录覆盖从 1.20 到最新的所有版本。这意味着包体虽然庞大，但在不同版本中都能正确加载，不会出现纹理丢失或格式错误。

6. **Polytone 集成**：通过 Polytone 模组实现自定义生物群系特效和方块修改器，进一步增强了中世纪氛围的沉浸感。

7. **光标自定义**：通过 cursors_extended 和 minecraft-cursor 模组支持自定义鼠标光标，细节体验拉满。

8. **模组生态兼容**：不仅覆盖原版内容，还为 Incendium 等模组提供 CIT 支持，同时为多个模组提供兼容纹理。

## 结论
Ashen_16x 是本分析中规模最大、覆盖最全的风格化资源包。它用 16x 的分辨率实现了堪比甚至超越原版纹理丰富度的视觉体验，这得益于其对 OptiFine CTM 叠加纹理系统的深度运用。

Ashen 的核心优势在于其统一且富有沉浸感的中世纪美术风格。不同于高清资源包追求细节清晰度，Ashen 在 16x 的限制下通过色彩、色调、纹理图案的设计传达出独特的氛围——古老、粗粝、充满 fantasy 风格。这种风格一致性是其最大的卖点。

从技术角度看，Ashen 展示了如何在低分辨率下创造高视觉丰富度的方法论：利用 CTM 叠加纹理消除重复感、利用随机纹理增加生物多样性、利用 CIT 自定义物品外观。这些技术的组合使用使其成为 16x 风格化资源包的技术标杆。

本包适合追求视觉风格统一和沉浸式体验的玩家，尤其适合喜欢中世纪 fantasy 主题的玩家。由于体积极大（2.3GB），建议有足够存储空间的玩家使用，并与 OptiFine 或兼容的模组加载器配合使用以体验全部功能。
