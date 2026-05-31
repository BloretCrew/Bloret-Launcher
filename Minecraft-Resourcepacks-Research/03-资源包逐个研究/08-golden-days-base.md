# 08. golden-days-base-1.21.x-1.15.5

## 根目录结构
```text
assets/
credits.txt
pack.mcmeta
pack.png
usage.txt
mod_continuity_option_no_grass_tint/
mod_continuity_option_overlay_ctm/
mod_emf_option_chest_fat_animated/
mod_emf_option_chest_use_cem/
mod_polytone/
old_lightmaps/
option_bamboo_planks_consistent/
option_bamboo_planks_smooth/
option_bricks_modern/
option_bushy_leaves/
option_bushy_leaves_shadowed/
option_cobblestone_hybrid/
option_cobblestone_modern/
option_cuboid_bamboo/
option_disable_flat_items/
option_end_custom/
option_end_modern/
option_fast_grass/
option_flat_candles/
option_flatten_skin_layers/
option_hide_xp_bar/
option_matching_coals/
option_modern_bow_holding/
option_modern_xp_bar/
option_oak_log_tops/
option_picture_perfect/
option_shadowed_leaves/
option_silent_chests/
option_solid_items/
patch_20_2_neoforge/
patch_20_3_bat_update/
patch_21_11/
patch_21_4_chest_fat/
patch_21_4_item_definitions/
patch_21_6_no_rotation_snap/
patch_21_9/
patch_26_1/
patch_26_2/
shaders_core_21_11/
shaders_core_21_9/
shaders_light_21_9/
shaders_light_26_1/
```

## 包定位
Golden Days Base 是由 PoeticRainbow 创作的一款极具野心的复古风格资源包，旨在将 Minecraft 的视觉体验还原到 Beta/Alpha 时代的美学风格，同时保留现代版本的内容和特性。该包被描述为 "Golden Days Base (Beta)"，目标是作为 Programmer Art 资源包的覆盖层使用（见 usage.txt 中的说明）。

其设计理念是"怀旧但不守旧"——它不是在简单地复制旧版纹理，而是通过全新的纹理绘制、模型改造、着色器编程、音效替换和配置系统，精确还原旧版本的视觉感受。该包大量使用了 Polytone 模组（一个用于资源包的条件配置和视觉修改的模组）来实现复杂的可配置特性。

该包支持从 Minecraft 1.20（pack_format 15）到 1.21.8+（pack_format 420）的广泛版本范围，并通过大量 overlay 系统实现版本特定调整。包体极其庞大，包含约 4074 个文件、1525 个 JSON 配置和 2248 个纹理图片，是本次研究样本中规模和复杂度都达到顶级的资源包。

主要目标用户是怀念旧版本 Minecraft 视觉风格的老玩家，以及希望在最新版本中获得复古体验的玩家。

## 关键文件说明
### pack.mcmeta
路径：`Resourcepacks/golden-days-base-1.21.x-1.15.5/pack.mcmeta`

这是整个研究中最为复杂和详尽的 pack.mcmeta 文件之一。它不仅定义了包的基本信息（pack_format 15，supported_formats [15, 420]），还包含两个重要扩展：

1. **sodium 配置段**：声明了 sodium 模组应忽略的着色器列表（fog.glsl、lightmap.fsh、rendertype_clouds.fsh、sky.fsh、terrain.fsh），让这些着色器由资源包自己的实现接管。

2. **大量的 overlay 条目**：定义了超过 30 个 overlay 目录，分为几个类别：
   - **版本补丁** (patch_*)：针对特定 Minecraft 版本调整（如 patch_20_2_neoforge 修复 NeoForge 兼容性）
   - **着色器核心** (shaders_core_*)：核心着色器实现，按版本分叉
   - **着色器光照** (shaders_light_*)：光照着色的不同版本
   - **模组兼容** (mod_*)：与 Polytone、Continuity、EMF 等模组的集成
   - **配置选项** (option_*)：通过 Polytone 条件实现的可切换功能
   - **旧版光照图** (old_lightmaps)：旧版光照映射

overlay 条目的格式使用了新的 JSON 格式（min_format/max_format）和旧格式（formats 数组）的混合写法，体现了过渡期的兼容性设计。其中一些条目还使用了 `polytone_condition` 字段，这是与 Polytone 模组深度集成的标志，允许通过模组的配置系统动态启用/禁用 overlay。

### usage.txt
路径：`Resourcepacks/golden-days-base-1.21.x-1.15.5/usage.txt`

内容为："This pack is meant to be put over Programmer Art." 简明扼要地说明了该包的使用方式——它设计为在 Programmer Art（原版经典纹理）之上加载，而非替代现代纹理。

### credits.txt
路径：`Resourcepacks/golden-days-base-1.21.x-1.15.5/credits.txt`

列出了关键贡献者：Mojang（原始纹理和游戏）、E404NNF（猪灵皮革纹理）、tygical（旧风格木材纹理）、zippa（光照图调整）、coyo-t（灰度光照着色器）、InboundBark（着色器黑手修复）、shmoobalizer（水纹理教学）和 Adrenix（Nostalgic Tweaks 模组及 fog.glsl 提供）。

### assets/golden_days/lang/en_us.json
路径：`Resourcepacks/golden-days-base-1.21.x-1.15.5/assets/golden_days/lang/en_us.json`

这是一个配置语言文件，定义了 Polytone 模组中所有配置选项的显示名称和提示文本。每个配置项都明确了其历史版本对照，例如：
- `bamboo_planks_style`：提供 Classic/Consistent/Smooth 三种样式
- `beta_lighting`：Indev->Beta 1.7 为 true，Beta 1.8+ 为 false
- `bricks` / `cobblestone`：提供 Alpha/Modern/Classic 等纹理风格切换
- `bushy_leaves`：类似 Better Foliage 的茂盛树叶
- `chest_model`：Beta/Modern/Hybrid 三种箱子模型样式
- `cloud_height`：不同版本的云层高度（108/128/192）
- `xp_bar_style`：hidden/modern/custom 三种经验条样式
- `end_style`：Early Release/Modern/Custom 三种末地风格

这个文件实际上成为了一个"版本演进可视化手册"，每个配置选项都标注了它在不同 Minecraft 版本中的默认值。

### assets/golden_days/shaders/include/general.glsl
路径：`Resourcepacks/golden-days-base-1.21.x-1.15.5/assets/golden_days/shaders/include/general.glsl`

这是一个核心着色器头文件，包含了 Golden Days 的视觉核心算法：

- **goldenDaysTexture()**：实现像素化纹理采样，移除像素间的平滑过渡，恢复旧版的块状纹理外观
- **goldenDaysLight()**：实现旧版光照算法，使用公式 `(1.0 - darkness) / (darkness * 3.0 + 1.0)` 计算光照衰减
- **goldenDaysLinearFogFactor() / goldenDaysExpFogFactor()**：实现线性/指数雾效算法，精确模拟旧版 Beta 1.7.3 的雾效行为
- **goldenDaysApplyFog() / goldenDaysApplySkyFog()**：集成雾效应用到渲染颜色

着色器代码中包含了大量注释，引用了 Beta 1.7.3 版本中的实际代码行为（如 fog mode、renderDistance 映射等），展示了逆向工程旧版渲染管线并移植到现代版本的技术深度。

## 资源内容结构
### 核心 assets/minecraft 目录
```text
assets/minecraft/
  blockstates/              (大量方块状态定义)
  equipment/               (装备模型)
  items/                   (物品定义)
  lang/                    (语言文件)
  models/block/            (方块模型)
  models/item/             (物品模型)
  models/equipment/        (装备模型)
  models/obj/              (OBJ格式模型)
  optifine/cem/            (自定义实体模型)
  optifine/colormap/       (自定义色图)
  optifine/ctm/            (连接纹理)
  particles/               (粒子定义)
  polytone/colors.json     (Polytone颜色配置)
  sounds/                  (音效文件 - 71个ogg文件)
  texts/                   (游戏文本)
  textures/block/          (方块纹理)
  textures/colormap/       (色图纹理)
  textures/entity/         (实体纹理)
  textures/environment/    (环境纹理)
  textures/font/           (字体纹理)
  textures/gui/            (GUI纹理)
  textures/item/           (物品纹理)
  textures/misc/           (杂项纹理)
  textures/models/         (模型纹理)
  textures/painting/       (画纹理)
  textures/particle/       (粒子纹理)
  textures/trims/          (装饰纹理)
```

### assets/golden_days 自定义命名空间
包含 Polytone 配置系统和自定义资源：
- `polytone/`：完整的 Polytone 配置目录
- `shaders/include/`：核心着色器头文件
- `textures/`：自定义纹理资源

### Overlay 目录
根目录下存在大量 overlay 子目录，每个都包含版本特定的资源修改：
- `patch_*`：版本兼容性修复
- `option_*`：可切换的视觉配置
- `mod_*`：模组兼容性补丁
- `shaders_*`：着色器版本分叉
- `old_lightmaps/`：旧版光照映射

## 关键目录功能

### assets/minecraft/blockstates/ 方块状态定义
包含大量经过修改的方块状态 JSON 文件，覆盖了门、栅栏、玻璃板、混凝土粉末、命令方块、铜质方块、南瓜等。这些文件重新定义了方块变体的模型映射，是实现复古外观的基础。

### assets/minecraft/models/ 模型系统
模型目录包含 block/、item/、equipment/ 和 obj/ 四个子目录。大量模型被修改以匹配旧版视觉效果，包括使用 OBJ 格式实现的复杂模型。models/obj/ 目录的存在标志着该包超越了标准的 JSON 模型格式。

### assets/minecraft/optifine/ OptiFine 扩展
该包大量使用 OptiFine 的自定义实体模型（CEM）和连接纹理（CTM）系统：

- **CEM 目录**：包含 allay、armor_stand、bed、boat、breeze、chest、cow、drowned、husk、mooshroom、piglin、skeleton 等多个实体的 .jem 模型文件和 .png 纹理。这展示了如何通过 OptiFine 系统替换实体模型。
- **CTM 目录**：包含所有 16 种染色玻璃、普通玻璃、冰、浮冰、蓝冰、书架、砂岩等方块的连接纹理配置。其中 overlay_* 系列用于草方块、泥土、沙砾、沙子、雪、石头等方块的覆盖纹理。
- **block.properties**：OptiFine 的方块属性配置。
- **colormap/**：自定义色图配置。

这些系统共同工作，实现了旧版中玻璃无缝连接、草地覆盖等视觉特性。

### assets/golden_days/polytone/ Polytone 配置系统
这是该包最具技术深度的目录：

- **biome_modifiers/**：群系修改器（如下界、沼泽、苍白花园、移除草地修饰）
- **block_modifiers/**：方块修改器（蜡烛、模型居中、地图颜色清除、水锅）
- **colormaps/**：自定义色图（雾颜色、 foliage 颜色、草颜色、彩虹、天空颜色），配合 .png 纹理实现精确的颜色映射
- **config_entries/**：22 个可配置选项（从竹子木板样式到经验条样式）
- **custom_particles/**：自定义粒子效果（白色眼睛粒子）
- **dimension_modifiers/**：维度修改器（主世界、末地、下界）
- **entity_modifiers/**：实体修改器（船/筏的水迹）
- **fluid_modifiers/**：流体修改器（水）
- **item_modifiers/**：物品修改器（移除稀有度标识）
- **noises/**：噪声配置

这个系统使得资源包的大多数功能可以通过 Polytone 模组的配置界面开关调整，实现了极高程度的用户可定制性。

### assets/minecraft/shaders/ 着色器系统
通过 overlay 系统分发的着色器文件，包含：
- 旧版雾效（线性雾、指数雾）
- 旧版光照（Beta 光照算法）
- 旧版天空渲染
- 地形渲染修改

着色器覆盖了 minecraft 和 sodium 两个命名空间，确保在不使用 OptiFine 的现代渲染环境下也能正常工作。

## 技术特点

1. **Polytone 深度集成**：该包是 Polytone 模组能力的极限展示。通过 `polytone_condition` 在 overlay 中实现条件性资源加载，再配合 config_entries 实现用户可配置的视觉切换，将资源包的可定制性提升到了接近模组的水平。

2. **多版本兼容体系**：通过 pack.mcmeta 中的 30+ 个 overlay 条目，实现对 Minecraft 1.20 到 1.21.8+ 的全面覆盖。每个 overlay 都有精确的版本范围，部分还有模组条件。

3. **着色器逆向工程**：general.glsl 中的着色器代码是基于对 Beta 1.7.3 原版渲染器的逆向分析编写的，包含了精确的数学公式和算法实现。

4. **模组生态协同**：与 Sodium（着色器忽略列表）、Polytone（条件加载）、Continuity（覆盖 CTM）、EMF（实体模型）等模组深度整合，展示了资源包与模组协同工作的最佳实践。

5. **OptiFine CEM + CTM 全面使用**：对实体模型和连接纹理的全面覆盖，展示了传统 OptiFine 扩展系统的使用。

6. **自定义命名空间**：使用 `golden_days` 作为独立命名空间承载着色器、Polytone 配置和纹理，避免与 minecraft 命名空间冲突。

## 结论
Golden Days Base 是本次研究样本中技术和设计复杂度最高的资源包之一。它是一个"元资源包"——不仅提供了大量的视觉资源，还构建了一个完整的版本模拟和配置切换系统。

其技术贡献在于：
1. **可配置性革命**：通过 Polytone 模组实现了资源包层面的条件加载和用户配置，大幅扩展了资源包的可能性边界。
2. **着色器编程**：展示了资源包如何通过着色器实现全局视觉改造（雾效、光照、纹理过滤），而不仅仅是纹理替换。
3. **版本模拟方法论**：通过细致的版本对照表（从 Classic 到现代）系统化地实现了版本特定视觉的精确还原。
4. **Overlay 系统的高级用法**：在其 pack.mcmeta 中可以找到几乎每个 overlay 特性的使用示例，是学习 overlay 系统的活教材。

对于资源包开发者而言，该包是学习如何整合多种技术（着色器、OptiFine、Polytone、overlay）构建大型可配置资源包的终极参考。
