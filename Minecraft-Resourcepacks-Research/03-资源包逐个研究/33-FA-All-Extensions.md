# 33. FA+All_Extensions-v1.8.1

## 根目录结构

```
FA+All_Extensions-v1.8.1/
├── 21-2/              # Overlay for pack_format 42-999
│   └── assets/minecraft/
│       ├── emf/cem/           # EMF 自定义实体模型
│       │   ├── chest_left.jem
│       │   ├── chest_right.jem
│       │   ├── trapped_chest_left.jem
│       │   └── trapped_chest_right.jem
│       └── optifine/cem/      # OptiFine 自定义实体模型
│           ├── boat.jem
│           ├── chest_boat.jem
│           ├── chest_left.jem
│           ├── chest_right.jem
│           ├── donkey.jem
│           ├── mule.jem
│           ├── trapped_chest_left.jem
│           └── trapped_chest_right.jem
├── 21-5/              # Overlay for pack_format 55-999
│   └── assets/minecraft/optifine/cem/
│       ├── donkey.jem
│       └── mule.jem
├── 21-6/              # Overlay for pack_format 63-999
│   └── assets/minecraft/textures/entity/ghast/
│       └── ghast.png
├── assets/
│   └── minecraft/
│       ├── emf/cem/           # EMF 自定义实体模型
│       │   ├── ... (多种实体 jem/jpm 文件)
│       └── optifine/          # OptiFine 资源
│           ├── cem/           # 自定义实体模型
│           │   ├── boat/
│           │   ├── ... (多种实体 jem/jpm 文件)
│           └── random/        # 随机实体纹理
│               └── entity/
│                   ├── chicken/
│                   ├── cow/
│                   ├── creeper/
│                   ├── enderman/
│                   ├── fish/
│                   ├── illager/
│                   ├── iron_golem/
│                   ├── pig/
│                   ├── sheep/
│                   ├── slime/
│                   └── villager/
├── pack.mcmeta
├── pack.png
└── FAterms&conditions.txt
```

## 包定位

FA+All_Extensions 是著名资源包 **Fresh Animations (FA)** 的扩展包，由 FreshLX 制作。Fresh Animations 是一个极具影响力的Minecraft实体动画增强包，为游戏中的各种生物添加了流畅、生动的自定义动画。而 All_Extensions 则是其扩展集合，整合了多个第三方扩展子包，方便用户一次性安装。

本包版本为 1.8.1，使用先进的 **EMF (Entity Model Features)** 和 **OptiFine CEM (Custom Entity Models)** 两种技术方案来实现自定义实体模型和动画。包名中 "All Extensions" 表明这是一个集合包，将原本各自独立的FA扩展合并为一个统一的包。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "description": "§a█ 1.8.1 : All Extensions",
    "pack_format": 15,
    "supported_formats": {"min_inclusive": 15, "max_inclusive": 999},
    "min_format": 15,
    "max_format": 999
  },
  "overlays": {
    "entries": [
      { "directory": "21-2", "formats": {"min_inclusive": 42, "max_inclusive": 999} },
      { "directory": "21-5", "formats": {"min_inclusive": 55, "max_inclusive": 999} },
      { "directory": "21-6", "formats": {"min_inclusive": 63, "max_inclusive": 999} }
    ]
  }
}
```

该mcmeta展示了Minecraft 1.21引入的**Overlay（覆层）** 特性。通过多个overlay目录，一个资源包可以同时兼容多个Minecraft版本，不同版本的游戏会加载对应overlay中的文件，覆盖基础目录中的同名文件。

- overlay `21-2`: 适用于 pack_format 42-999，包含针对新版 chest/boat 实体模型的修正
- overlay `21-5`: 适用于 pack_format 55-999，针对 donkey/mule 的修正
- overlay `21-6`: 适用于 pack_format 63-999，针对 ghast 纹理的修正

**FAterms&conditions.txt:**
包含详细的许可协议。明确规定了不允许再分发、不允许移植到基岩版、未经许可不允许将未编辑的素材包含在付费产品中。但允许个人修改、在视频/直播中使用、在整合包中收录。

## 资源内容结构

本包的内容非常丰富，主要分为以下几大类：

1. **自定义实体模型 (.jem/.jpm 文件)**：这是核心内容，为各种生物定义了骨骼结构、模型几何体和动画逻辑
2. **随机实体纹理 (random/entity/)**：为常见生物提供多种随机纹理变种，使同一生物群系中的个体呈现不同的外观
3. **模型动画系统**：通过.jem文件中的复杂数学表达式实现流畅的肢体动作和物理效果

## 关键目录功能

### assets/minecraft/optifine/cem/
这是最重要的目录，包含了大量自定义实体模型文件。对于每个生物，通常包含一个 `.jem`（模型定义）和一个 `.jpm`（动画定义）文件。支持的生物包括：

- 蝙蝠 (bat)
- 船 (boat) + 带箱子的船 (chest_boat)
- 猫 (cat) + 项圈 (cat_collar)
- 鸡 (chicken)
- 牛 (cow)
- 苦力怕 (creeper)
- 驴 (donkey) + 箱子 (donkey_chest)
- 溺尸 (drowned)
- 末影龙 (ender_dragon)
- 末影人 (enderman)
- 唤魔者 (evoker)
- 狐狸 (fox)
- 恶魂 (ghast)
- 山羊 (goat)
- 铁傀儡 (iron_golem)
- 杀手兔 (killer_bunny)
- 羊驼 (llama) + 装饰 (llama_decoration)
- 岩浆怪 (magma_cube)
- 幻翼 (phantom)
- 猪 (pig)
- 猪灵 (piglin) + 猪灵蛮兵 (piglin_brute)
- 掠夺者 (pillager)
- 玩家 (player)
- 北极熊 (polar_bear)
- 河豚 (pufferfish)
- 劫掠兽 (ravager)
- 鲑鱼 (salmon)
- 羊 (sheep)
- 潜影贝 (shulker)
- 骷髅 (skeleton)
- 史莱姆 (slime)
- 蜘蛛 (spider)
- 鱿鱼 (squid)
- 流浪者 (stray)
- 行商羊驼 (trader_llama)
- 村民 (villager) + 僵尸村民 (zombie_villager)
- 卫道士 (vindicator)
- 流浪商人 (wandering_trader)
-  witches
- 狼 (wolf) + 项圈 (wolf_collar)
- 僵尸 (zombie)
- 僵尸猪灵 (zombified_piglin)

### assets/minecraft/emf/cem/
EMF（Entity Model Features）是比 OptiFine CEM 更新的技术方案，作为 Fabric/NeoForge 模组提供相同的自定义实体模型功能。此处包含的模型与 OptiFine 版本类似，但文件格式略有不同。

### assets/minecraft/optifine/random/entity/
为多种生物提供了随机纹理变种，使游戏世界中的生物外观更加多样：

- **chicken/**: 多种小鸡纹理变种
- **cow/**: 多种奶牛纹理变种（经典黑白、棕色等）
- **creeper/**: 苦力怕纹理变种
- **enderman/**: 末影人纹理变种
- **fish/**: 鱼类纹理变种
- **illager/**: 灾厄村民纹理变种
- **iron_golem/**: 铁傀儡纹理变种
- **pig/**: 猪纹理变种
- **sheep/**: 羊纹理变种
- **slime/**: 史莱姆纹理变种
- **villager/**: 村民纹理变种

## 技术特点

1. **双重兼容性**：同时支持 OptiFine CEM 和 EMF 两种自定义实体模型系统，无论用户使用 OptiFine 还是 Fabric + EMF 模组都能获得完整的动画效果。

2. **精细的动画系统**：Fresh Animations 的核心竞争力在于其精心制作的动画。每个 .jem 文件中都包含了复杂的动画数学表达式，利用游戏引擎提供的变量（如 `limb_swing`、`head_yaw`、`is_sneaking` 等）计算实体的姿态、位移和旋转，实现了流畅自然的肢体运动。

3. **Overlay版本兼容**：使用Minecraft 1.21的overlay机制，针对不同版本的游戏提供不同的模型文件，确保在新版本中也能正常渲染。

4. **随机纹理系统**：利用 OptiFine 的随机纹理功能，为生物提供多种外观变种，增强了游戏世界的丰富性和真实感。

5. **完整的实体覆盖**：几乎覆盖了游戏中所有主要生物，从被动生物到敌对生物，从主世界到下界和末地。

## 结论

FA+All_Extensions-v1.8.1 是一个高质量的 Fresh Animations 扩展聚合包，为Minecraft的实体动画系统带来了质的飞跃。它通过精细的骨骼动画、流畅的肢体运动和丰富的纹理变种，让游戏中的生物变得生动有趣。无论是动物行走时身体的起伏、苦力怕靠近时的姿态变化，还是村民的肢体动作，都展现了作者在动画设计方面的高超技术。

技术上，该包同时支持 EMF 和 OptiFine CEM 两种标准，并利用 overlay 机制实现了跨版本兼容，体现了作者对Minecraft资源包技术的深入理解。这个包特别适合追求视觉体验升级的模组玩家，配合 Fresh Animations 本体使用效果最佳。
