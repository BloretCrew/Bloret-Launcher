# Minecraft 资源包研究报告

## 研究范围

本报告基于项目目录 `Resourcepacks/` 下的 5 个资源包样本，以及 `Minecraft Wiki` 中“资源包”条目的说明进行整理。

研究目标：

1. 说明 Minecraft 资源包的基础机制。
2. 逐个分析每个资源包的目录结构、关键文件与实际功能。
3. 标出文件路径对应的用途，帮助后续继续研究或二次整理。

---

## 一、Minecraft 资源包机制总览

根据 Minecraft Wiki，资源包的核心作用是替换、合并或移除游戏资源，而不修改游戏代码。资源包的加载顺序很重要：上层资源包可以覆盖下层资源包。

### 1.0 先给结论

如果把资源包当成一个“资源覆盖层系统”，那么它的通用逻辑可以概括为：

1. 游戏先读 `pack.mcmeta` 判断这个包是否可识别、支持哪些版本。
2. 游戏再按资源包顺序从上到下查找资源。
3. 同一路径下，优先级高的资源包覆盖优先级低的资源包。
4. 不同资源类型有各自的目录规范，例如贴图、模型、语言、声音、文本、字体。
5. 某些特殊 JSON 文件可以改变加载行为、兼容性提示、地区弹窗或 GPU 警告。

换句话说，资源包不是单纯“改贴图”，而是“按规则覆盖游戏资源树”。

### 1.1 标准结构

一个 Java 版资源包通常至少包含：

```text
<资源包根目录>/
  pack.mcmeta
  pack.png   # 可选图标
  assets/
    <命名空间>/
      textures/
      models/
      lang/
      sounds/
      font/
      blockstates/
      items/
      particles/
      shaders/
      texts/
      ...
```

### 1.2 关键规则

1. `pack.mcmeta` 是资源包元数据，决定游戏是否识别该包，以及包描述、格式版本、语言定义等信息。
2. `pack.png` 是资源包图标。
3. `assets/<namespace>/textures` 用于贴图替换。
4. `assets/<namespace>/models` 用于方块和物品模型替换。
5. `assets/<namespace>/blockstates` 决定方块状态如何映射到模型。
6. `assets/<namespace>/lang` 负责翻译文本覆盖与新增。
7. `assets/<namespace>/sounds.json` 与 `sounds/` 负责声音事件和音频文件。
8. `assets/<namespace>/texts` 负责标题页标语、终末之诗、鸣谢等纯文本或结构化文本。

### 1.3 Wiki 中特别值得注意的点

1. 资源包顺序影响覆盖关系。
2. 同名文件会按优先级覆盖，低层资源包可能完全被上层替换。
3. 语言文件可以只覆盖部分键，不必提供完整翻译。
4. `regional_compliancies.json`、`gpu_warnlist.json`、`deprecated.json` 这类特殊文件属于较新的资源包机制扩展。

### 1.4 通用工作流

任何资源包在游戏中的生效逻辑，通常都可以按以下流程理解：

1. 放入 `resourcepacks`。
2. 游戏扫描根目录下的文件夹或 `.zip`。
3. 读取 `pack.mcmeta`。
4. 按资源包顺序加载。
5. 遇到相同路径的资源时，优先级高者覆盖。
6. 对于语言、文本、模型、粒子、声音等资源，按各自规则解析。
7. 某些资源会依赖外部机制，例如 OptiFine、资源包版本、语言注册或特定的 JSON 扩展字段。

### 1.5 通用目录语义

下面这些目录是理解任意资源包的关键：

| 目录 | 通用作用 |
|---|---|
| `pack.mcmeta` | 包元数据，决定识别、版本兼容和描述 |
| `pack.png` | 包图标 |
| `assets/<namespace>/textures/` | 贴图资源 |
| `assets/<namespace>/models/` | 方块/物品模型 |
| `assets/<namespace>/blockstates/` | 方块状态到模型的映射 |
| `assets/<namespace>/items/` | 物品模型映射（新机制） |
| `assets/<namespace>/equipment/` | 装备模型 |
| `assets/<namespace>/font/` | 字体与字形定义 |
| `assets/<namespace>/lang/` | 翻译文本 |
| `assets/<namespace>/sounds/` | 声音文件 |
| `assets/<namespace>/sounds.json` | 声音事件定义 |
| `assets/<namespace>/particles/` | 粒子纹理定义 |
| `assets/<namespace>/texts/` | 标语、终末之诗、鸣谢等文本 |
| `assets/<namespace>/shaders/` | GLSL 着色器 |
| `assets/<namespace>/post_effect/` | 后处理管线 |
| `assets/<namespace>/atlases/` | 纹理图集定义 |

### 1.6 版本与兼容性逻辑

资源包兼容性不是只看“能不能打开”，而是看它是否符合当前游戏版本的资源格式。

关键点有三个：

1. `pack_format` 决定资源包格式版本。
2. `min_format` 和 `max_format` 或 `supported_formats` 决定兼容区间。
3. 新版本会引入新目录、新 JSON 结构或新字段，旧包不一定能直接适配。

Wiki 里列出的历史变化说明，资源包系统本身是逐步扩展的，例如：

1. 1.6.1 引入资源包。
2. 1.7.2 支持多个资源包。
3. 1.8 支持世界指定资源包。
4. 1.15、1.16、1.17、1.18、1.19、1.20、1.21 持续扩展了声音、粒子、警告、文本、过滤、叠加目录等能力。

### 1.7 加载优先级逻辑

资源包的覆盖规则是这项机制的核心。

1. 列表上方的包优先级更高。
2. 同路径资源会被上层覆盖。
3. 不同资源类型的合并行为不同：
   1. 贴图通常是直接替换。
   2. 语言文件是按键覆盖和补齐。
   3. 某些文本文件是“找到第一个就停止”。
   4. 模型和 blockstate 往往是直接重映射。

### 1.8 特殊文件逻辑

以下文件属于“通用机制里最容易被忽视，但很关键”的部分：

| 文件 | 作用 |
|---|---|
| `assets/minecraft/gpu_warnlist.json` | GPU/渲染器警告列表 |
| `assets/minecraft/regional_compliancies.json` | 按地区触发合规弹窗 |
| `assets/minecraft/lang/deprecated.json` | 标记本版本中弃用或重命名的翻译键 |
| `pack.mcmeta` 中的 `filter` | 过滤低优先级数据包中的命名空间/正则匹配资源 |
| `pack.mcmeta` 中的 `overlays` | 同一资源包的版本叠加目录机制 |

### 1.9 资源包到底能改什么

结合 Wiki 和样本包，可以把资源包能力划分为五类：

1. 视觉类：方块、物品、实体、GUI、粒子、字体。
2. 听觉类：声音文件、声音事件定义。
3. 文本类：语言、文本页、鸣谢、标语。
4. 结构类：模型、方块状态、物品模型、装备模型、纹理图集。
5. 交互提示类：GPU 警告、地区合规弹窗、聊天安全状态、路径点样式。

---

## 二、资源包逐个研究

---

## 2.1 `Better-Leaves-9.5`

### 2.1.1 根目录结构

路径：`Resourcepacks/Better-Leaves-9.5/`

```text
assets/
LICENSE
pack.mcmeta
pack.png
README.md
```

### 2.1.2 包定位

这是一个“树叶优化 / 美化”资源包，目标是让树叶呈现更饱满、更圆润的视觉效果，同时尽量降低性能损耗。

从 `README.md` 可以看出它的设计目标是：

1. 使用更少的模型元素。
2. 预先生成圆润纹理，而不是在渲染阶段伪造圆形。
3. 尽量通过单纹理方案减少贴图坐标查找和纹理图集开销。

### 2.1.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/Better-Leaves-9.5/pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 15,
    "supported_formats": [15, 255],
    "min_format": 15,
    "max_format": 255,
    "description": "§2Version 9.5 §aVanilla Edition\n§e©Motschen 2026 | MIT Licence"
  }
}
```

用途：

1. 指定资源包格式。
2. 说明该包面向较新版本。
3. 描述文本显示版本号、作者和许可证信息。

#### `README.md`

路径：`Resourcepacks/Better-Leaves-9.5/README.md`

作用：

1. 解释包的优化思路。
2. 说明与其他树叶纹理包相比的性能优势。
3. 提示可用脚本自建变体。

#### `LICENSE`

路径：`Resourcepacks/Better-Leaves-9.5/LICENSE`

作用：

1. 约束资源包使用方式。
2. 与包说明一起表明该包可被再分发或重制时的法律边界。

#### `pack.png`

路径：`Resourcepacks/Better-Leaves-9.5/pack.png`

作用：

1. 资源包图标。
2. 在资源包列表中显示。

### 2.1.4 资源内容结构

该包的主要内容位于 `assets/`，并且包含多个命名空间，例如：

1. `assets/dtru/`
2. `assets/dtnatures_spirit/`
3. `assets/dtecologics/`
4. `assets/dtbwg/`
5. `assets/enderscape/`
6. `assets/ars_elemental/`
7. `assets/aether/`

这说明它不是纯原版覆盖包，而是面向多个模组树叶方块的兼容美化包。

### 2.1.5 关键目录功能

#### `assets/<namespace>/blockstates/`

代表功能：为对应模组方块指定模型映射。

示例：

路径：`Resourcepacks/Better-Leaves-9.5/assets/dtru/blockstates/maple_leaves.json`

内容要点：

1. 一个方块状态列出多个 `variants`。
2. 每个 variant 指向不同模型，例如 `regions_unexplored:block/maple_leaves1` 到 `maple_leaves4`。
3. 同一模型配合 `y: 0/90/180/270` 旋转，制造多样化树叶外观。

这说明：

1. 树叶并不是只改一张贴图，而是通过多个模型变体增加随机感。
2. `blockstates` 在这里是“随机外观分发器”。

示例：

路径：`Resourcepacks/Better-Leaves-9.5/assets/dtru/blockstates/larch_leaves.json`

同样指向 `regions_unexplored:block/larch_leaves1` 到 `larch_leaves4`，说明这个包有一整套对树叶方块的模型重映射体系。

### 2.1.6 结论

`Better-Leaves-9.5` 是一个典型的“模组树叶美化 + 性能优化”资源包。

它的核心不是简单替换贴图，而是：

1. 通过 `blockstates` 让叶子模型变体更多。
2. 通过命名空间分区支持多个模组。
3. 用更少的渲染代价实现更饱满的树叶效果。

---

## 2.2 `Chat_Reporting_Helper`

### 2.2.1 根目录结构

路径：`Resourcepacks/Chat_Reporting_Helper/`

```text
assets/
pack.mcmeta
pack.png
```

### 2.2.2 包定位

这是一个面向聊天举报机制说明与提示界面的辅助资源包。

从 `pack.mcmeta` 的描述，以及语言文件中的大量短语，可以判断它的用途不是改游戏主视觉，而是：

1. 帮助玩家理解聊天举报状态。
2. 用更直白的文字替换原版提示。
3. 通过图标增强界面可读性。

### 2.2.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/Chat_Reporting_Helper/pack.mcmeta`

```json
{"pack":{"description":{"translate":"fo.resourcePack.chatreportinghelper","fallback":"§7Explains chat reporting with simple phrases and icons§r"},"pack_format":18,"min_format":18,"max_format":84,"supported_formats":[18,64]}}
```

用途：

1. 使用翻译键描述资源包名称。
2. 明确支持的资源包格式范围。
3. 表明包是跨版本兼容型资源包。

#### `pack.png`

路径：`Resourcepacks/Chat_Reporting_Helper/pack.png`

用途：资源包图标。

### 2.2.4 资源内容结构

该包包含两个关键命名空间：

1. `assets/fo/lang/`
2. `assets/nochatreports/textures/gui/sprites/safety_state/`

### 2.2.5 关键目录功能

#### `assets/fo/lang/`

代表功能：本地化文本覆盖。

这里包含大量语言文件，例如：

1. `en_us.json`
2. `zh_cn.json`
3. `zh_tw.json`
4. `fr_fr.json`
5. `de_de.json`
6. `ru_ru.json`
7. `ko_kr.json`
8. `pt_br.json`
9. `es_es.json`
10. `it_it.json`
11. 以及其他多语种文件

说明：

1. 这是一个面向国际玩家的辅助包。
2. 它不是只改英文，而是在多语言环境下都可工作。
3. 资源包利用语言覆盖机制，把原版社交提示替换成更易懂的说明。

代表文件：

路径：`Resourcepacks/Chat_Reporting_Helper/assets/fo/lang/en_us.json`

其中包含大量与聊天安全、举报、会话状态相关的键值，比如：

1. `chat.tag.modified`
2. `chat.tag.not_secure`
3. `gui.socialInteractions.tooltip.report`
4. `multiplayer.unsecureserver.toast.title`
5. `options.onlyShowSecureChat`

这表明该包主要服务于聊天举报 UI 与提示文本。

#### `assets/nochatreports/textures/gui/sprites/safety_state/`

代表功能：GUI 状态图标替换。

这里有多组状态图标：

1. `secure.png`
2. `secure_hovered.png`
3. `secure_disabled.png`
4. `insecure.png`
5. `insecure_hovered.png`
6. `insecure_disabled.png`
7. `unknown.png`
8. `unknown_disabled.png`
9. `undefined.png`
10. `undefined_disabled.png`
11. `unintrusive.png`
12. `unintrusive_disabled.png`
13. `realms.png`
14. `realms_disabled.png`
15. `verified_server.png`

功能判断：

1. 这些贴图用于聊天安全状态按钮和提示图标。
2. 通过图标让玩家快速判断聊天是否可举报、是否受限、是否来自 Realms 或验证服务器。

### 2.2.6 结论

`Chat_Reporting_Helper` 是一个“UI 文案 + 状态图标”型资源包。

它最核心的特征是：

1. 依赖语言文件大规模覆盖提示文本。
2. 用独立命名空间存放 GUI 状态图标。
3. 明显面向聊天举报和安全状态说明场景。

---

## 2.3 `FreshAnimations_v1.10.5`

### 2.3.1 根目录结构

路径：`Resourcepacks/FreshAnimations_v1.10.5/`

```text
assets/
changelog1.10.5.txt
FAterms&conditions.txt
pack.mcmeta
pack.png
```

### 2.3.2 包定位

这是一个非常典型的“实体动画增强”资源包。

它通过 OptiFine CEM 体系以及相关纹理替换，为大量生物添加更自然、更细致的动作表现。

从文件结构可以直接看出，它是围绕 `assets/minecraft/optifine/cem/` 构建的。

### 2.3.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/FreshAnimations_v1.10.5/pack.mcmeta`

```json
{
    "pack": {
        "description": "§4■ 1.10.5 BETA§8\n■ By FreshLX",
        "min_format": 84,
        "max_format": 999
    }
}
```

用途：

1. 标记资源包版本与作者。
2. 表明这是测试/预发布性质的版本。

#### `FAterms&conditions.txt`

路径：`Resourcepacks/FreshAnimations_v1.10.5/FAterms&conditions.txt`

作用：

1. 说明资源包资产的授权边界。
2. 明确某些资产不允许随意再分发或商用。
3. 提示公开内容中引用时需要署名。

#### `changelog1.10.5.txt`

路径：`Resourcepacks/FreshAnimations_v1.10.5/changelog1.10.5.txt`

作用：

1. 记录本次版本改动。
2. 说明添加了若干生物纹理路径。
3. 建议与 Entity Model Features / Entity Texture Features 结合使用。

#### `pack.png`

路径：`Resourcepacks/FreshAnimations_v1.10.5/pack.png`

作用：资源包图标。

### 2.3.4 资源内容结构

该包的主要资源集中在：

1. `assets/minecraft/optifine/cem/`
2. `assets/minecraft/textures/entity/`
3. `assets/minecraft/particles/`

### 2.3.5 关键目录功能

#### `assets/minecraft/optifine/cem/`

这是整包的核心。

这里有大量 `.jem` 和 `.jpm` 文件，例如：

1. `villager.jem`
2. `villager_animations.jpm`
3. `zombie.jem`
4. `wolf.jem`
5. `fox.jem`
6. `horse.jem`
7. `creeper.jem`
8. `dolphin.jem`
9. `allay_animations.jpm`
10. `frog_animations.jpm`
11. `sniffer_animations.jpm`
12. `happy_ghast.jem`

这说明：

1. 包通过 CEM 自定义实体模型。
2. `.jem` 负责实体模型定义。
3. `.jpm` 负责动画参数与运动公式。

代表文件：

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/optifine/cem/villager.jem`

内容特征：

1. `textureSize` 定义贴图尺寸。
2. `models` 中将 `root`、`head`、`body`、`arms`、`legs` 等部件拆开。
3. 通过 `submodels` 和 `boxes` 定义更细的面部、帽子、鼻子、眉毛等结构。

这说明村民模型被重构为更复杂的分层模型，而不是原版单一方块风格。

代表文件：

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/optifine/cem/villager_animations.jpm`

内容特征：

1. 以大量变量计算驱动头部、身体、腿部与脸部动画。
2. 通过 `var.walk`、`var.run`、`var.swim`、`var.dance` 等表达式控制动态姿态。
3. 允许面部细节、身体摇摆、视线偏移等更自然表现。

这是该包“Fresh Animations”名字的直接体现：它不是静态换皮，而是动态动画增强。

#### `assets/minecraft/textures/entity/`

这里存放大量实体纹理，例如：

1. `villager/villager.png`
2. `villager/type/desert.png`
3. `zombie/zombie.png`
4. `zombie/drowned.png`
5. `wolf/wolf.png`
6. `cat/cat_tabby.png`
7. `bee/bee.png`
8. `frog/frog_temperate.png`
9. `pig/pig_warm.png`
10. `cow/cow_temperate.png`
11. `shulker/shulker_red.png`
12. `illager/vindicator.png`

说明：

1. 该包不只换模型，也换实体贴图。
2. 很多纹理按变种分离，例如生物群系、状态、怒气、骑乘、寒热环境等。

#### `assets/minecraft/particles/mycelium.json`

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/particles/mycelium.json`

内容：

```json
{
  "textures": [
    "minecraft:fresh_animations/empty"
  ]
}
```

用途：

1. 让特定粒子引用一个空纹理。
2. 常用于隐藏不需要的视觉颗粒或占位。

### 2.3.6 结论

`FreshAnimations_v1.10.5` 是一个高复杂度的实体表现增强包。

它的结构显示出三层改造：

1. `.jem` 改模型。
2. `.jpm` 改动画。
3. `textures/entity` 改贴图。

它并不是普通意义上的“材质包换图”，而是把实体表现系统整体重做了一遍。

---

## 2.4 `MandalasGUI+Dakmode_1.21.6_v2.1`

### 2.4.1 根目录结构

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/`

```text
assets/
License.txt
pack.mcmeta
pack.png
```

### 2.4.2 包定位

这是一个 GUI 美化包，并且明显包含 Dark Mode 风格。

从文件命名看，它主要修改游戏界面、菜单、按钮、列表、提示框、容器 GUI 和各种交互图标。

### 2.4.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 64,
    "description": "§7By: §6§nCesarZorak\n§r§71.20.5 to 1.21.5"
  }
}
```

用途：

1. 标注支持版本区间。
2. 显示作者信息。
3. 说明这是一个跨多个 Minecraft 小版本兼容的 GUI 包。

#### `License.txt`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/License.txt`

说明：

1. 当前读取工具无法按文本打开该文件，可能是二进制或特殊编码。
2. 但从文件名可知它是许可证文件，用于约束资源使用。

#### `pack.png`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.png`

作用：资源包图标。

### 2.4.4 资源内容结构

大部分资源都在：

1. `assets/minecraft/textures/gui/`
2. `assets/minecraft/textures/item/`
3. `assets/minecraft/textures/particle/`

### 2.4.5 关键目录功能

#### `assets/minecraft/textures/gui/`

这是整个包最重要的目录。

这里包含：

1. `widgets.png`
2. `icons.png`
3. `resource_packs.png`
4. `server_selection.png`
5. `world_selection.png`
6. `inventory.png`
7. `crafting_table.png`
8. `beacon.png`
9. `anvil.png`
10. `smoker.png`
11. `grindstone.png`
12. `smithing.png`
13. `book.png`
14. `recipe_book.png`
15. `toasts.png`
16. `menu_background.png`
17. `light_dirt_background.png`
18. `stream_indicator.png`
19. `chat_tags.png`
20. `report_button.png`

功能判断：

1. 该包在重绘主菜单、设置界面、世界选择界面、服务器界面、容器界面和提示系统。
2. `widgets.png` 和一系列 `sprites/widget/` 文件说明按钮、滑条、复选框、文本框等控件都被重做。
3. `world_list/`、`toast/`、`dialog/` 说明连系统弹窗、世界列表按钮和对话框样式也被重绘。

代表性子目录：

1. `assets/minecraft/textures/gui/sprites/widget/`
2. `assets/minecraft/textures/gui/sprites/world_list/`
3. `assets/minecraft/textures/gui/sprites/dialog/`
4. `assets/minecraft/textures/gui/sprites/toast/`
5. `assets/minecraft/textures/gui/container/`

#### `assets/minecraft/textures/gui/container/`

这里包括：

1. `inventory.png`
2. `crafting_table.png`
3. `furnace.png`
4. `blast_furnace.png`
5. `smoker.png`
6. `smithing.png`
7. `stonecutter.png`
8. `loom.png`
9. `cartography_table.png`
10. `enchanting_table.png`
11. `grindstone.png`
12. `beacon.png`
13. `brewing_stand.png`
14. `villager.png`
15. `horse.png`
16. `shulker_box.png`
17. `crafter.png`
18. `legacy_smithing.png`

功能判断：

1. 整个包对常用容器界面做统一视觉重做。
2. 支持新旧 smithing 界面并存，说明它兼顾新版 GUI 机制。

#### `assets/minecraft/textures/item/`

这里是 GUI 中的槽位提示图标，例如：

1. `empty_slot_sword.png`
2. `empty_slot_pickaxe.png`
3. `empty_slot_shovel.png`
4. `empty_slot_axe.png`
5. `empty_slot_hoe.png`
6. `empty_slot_ingot.png`
7. `empty_slot_diamond.png`
8. `empty_slot_emerald.png`
9. `empty_slot_quartz.png`
10. `empty_slot_lapis_lazuli.png`
11. `empty_slot_amethyst_shard.png`
12. `empty_armor_slot_helmet.png`
13. `empty_armor_slot_chestplate.png`
14. `empty_armor_slot_leggings.png`
15. `empty_armor_slot_boots.png`
16. `empty_armor_slot_shield.png`

功能判断：

1. 用于槽位提示和物品图标占位。
2. 直接提升容器界面的可读性。

#### `assets/minecraft/textures/particle/`

这里包含：

1. `note.png`
2. `heart.png`
3. `damage.png`
4. `goldheart_0.png`
5. `goldheart_1.png`
6. `goldheart_2.png`
7. `damage_.png`

说明：

1. 包不仅修改界面，还对部分粒子和状态视觉做统一风格化。
2. `goldheart_*` 说明连与状态效果有关的局部视觉也被替换。

### 2.4.6 结论

`MandalasGUI+Dakmode_1.21.6_v2.1` 是一个纯度很高的 GUI/UI 风格化资源包。

它的特征是：

1. 高度集中在 `textures/gui`。
2. 兼顾主菜单、列表、容器、提示框、按钮与输入控件。
3. 具有明显的暗色界面风格和现代化视觉统一倾向。

---

## 2.5 `meme.teahouse.team-da0c28`

### 2.5.1 根目录结构

路径：`Resourcepacks/meme.teahouse.team-da0c28/`

```text
assets/
LICENSE
pack.mcmeta
pack.png
```

### 2.5.2 包定位

这是一个“梗体中文”资源包，目标明显不是单纯汉化，而是：

1. 把大量 Minecraft 文本改造成梗化表达。
2. 使用自定义字体与大量字形资源支撑特殊字符。
3. 同时改造部分模型、声音、文本和合规提示。

它是本次样本中最“综合型”的包之一。

### 2.5.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/meme.teahouse.team-da0c28/pack.mcmeta`

主要内容：

1. `pack_format: 34`。
2. 定义 `zh_meme` 语言条目。
3. 列出作者与特别鸣谢。
4. 包含主页链接与版权说明。

关键点：

1. 这是少见的在 `pack.mcmeta` 中主动声明语言元数据的包。
2. 说明它把 `zh_meme` 作为资源包语言正式注册。
3. `copyright` 字段明确采用 CC BY-SA 4.0。

#### `LICENSE`

路径：`Resourcepacks/meme.teahouse.team-da0c28/LICENSE`

作用：

1. 提供完整的 CC BY-SA 4.0 协议文本。
2. 明确该包允许署名、共享和演绎，但需遵守相同方式分享。

#### `pack.png`

路径：`Resourcepacks/meme.teahouse.team-da0c28/pack.png`

作用：资源包图标。

### 2.5.4 资源内容结构

该包的内容分布非常广：

1. `assets/minecraft/lang/`
2. `assets/minecraft/regional_compliancies.json`
3. `assets/minecraft/font/`
4. `assets/minecraft/models/`
5. `assets/minecraft/texts/`
6. `assets/minecraft/optifine/cit/`
7. `assets/minecraft/sounds/`
8. `assets/minecraft/textures/`
9. `assets/mcwzhmeme/textures/`

### 2.5.5 关键目录功能

#### `assets/minecraft/lang/zh_meme.json`

这是整个包最关键的文件之一。

它包含大量本地化键值，对原版 UI、进度、提示、世界状态、辅助信息等进行“梗化重写”。

从文件内容可以看到：

1. 大量基础界面词条被改写。
2. 大量进度文本被重新命名并换成梗化表达。
3. 这不是简单翻译，而是内容再创作。

该文件是“梗体中文”风格的核心来源。

#### `assets/minecraft/font/default.json`

这是一个非常重要的字体定义文件。

它使用 `providers` 数组定义 bitmap 字体资源，例如：

1. `minecraft:font/character-basic-supp-9fd0.png`
2. `minecraft:font/character-basic-supp-9fec.png`
3. `minecraft:font/character-30ede.png`
4. `minecraft:font/character-2c317.png`

文件作用：

1. 为大量特殊汉字和扩展字符提供字形。
2. 让梗体中文中的特殊字、异体字和视觉排版能被稳定渲染。
3. 支撑该包极其夸张的字体体系。

#### `assets/minecraft/models/item/`

代表文件：

1. `chicken_spawn_egg.json`
2. `wolf_spawn_egg.json`

示例：

路径：`Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/item/chicken_spawn_egg.json`

内容指向：`minecraft:item/locus_azzurro_spawn_egg`

说明：

1. 这个包不仅改文字，还会替换物品外观。
2. 物品模型通过 `textures.layer0` 指向新的自定义贴图。

示例：

路径：`Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/item/wolf_spawn_egg.json`

内容指向：`minecraft:item/doro_wolf_spawn_egg`

说明：

1. 同样属于物品重定向。
2. 说明“鸡蛋/狼蛋”等生成蛋也被重新设计。

#### `assets/minecraft/models/block/`

代表文件：

1. `observer_on.json`
2. `cake.json`

示例：

路径：`Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/block/observer_on.json`

内容指向：

1. `front: block/observer_front_on`
2. `bottom: block/observer_back_on`

说明：

1. 通过模型层替换观察者方块正面和背面。
2. 属于典型的方块模型覆盖。

示例：

路径：`Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/block/cake.json`

内容特征：

1. 使用 Blockbench 制作。
2. 引入了自定义纹理键 `two`。
3. 模型元素非常详细，说明该包有较强的模型改造能力。

#### `assets/minecraft/texts/credits.json`

这不是普通文本，而是结构化制作人员名单。

它使用数组和对象分层定义：

1. section
2. disciplines
3. titles
4. names

作用：

1. 替换或扩展游戏鸣谢页内容。
2. 体现该包有完整的“内容工程”组织方式。

#### `assets/minecraft/regional_compliancies.json`

这是一个非常关键的合规功能文件。

内容包括：

1. `CHN`
2. `USA`
3. `KOR`
4. `HKG`
5. `TWN`
6. `JPN`
7. `MAC`
8. `GBR`

每个地区都定义了：

1. `delay`
2. `period`
3. `title`
4. `message`

作用：

1. 按地区定时弹出提示。
2. 这是资源包中少见的“地区合规提醒”机制。
3. 说明该包在某些地区环境下不仅做美术改造，还会参与合规/提示逻辑。

#### `assets/minecraft/optifine/cit/suspicious_stew/`

这里包含大量 `.properties` 与 `.png` 文件，例如：

1. `wither.properties`
2. `wither.png`
3. `weakness.properties`
4. `poison.png`
5. `regeneration.png`
6. `fire_resistance.png`

作用判断：

1. 这属于 OptiFine CIT 风格的自定义纹理配置。
2. 用于让可疑炖菜根据效果显示不同图标或纹理。

#### `assets/minecraft/sounds/item/goat_horn/`

这里有：

1. `call0.ogg`
2. `call1.ogg`
3. `call2.ogg`
4. `call3.ogg`
5. `call4.ogg`
6. `call5.ogg`
7. `call6.ogg`
8. `call7.ogg`

作用：

1. 为山羊号角提供音频资源。
2. 说明该包不仅改文本，也改声音。

#### `assets/minecraft/textures/`

这里包括：

1. `textures/block/grass.png`
2. `textures/block/short_grass.png`
3. `textures/block/observer_front.png`
4. `textures/block/observer_front_on.png`
5. `textures/block/suspicious_sand_*.png`
6. `textures/block/suspicious_gravel_*.png`
7. `textures/misc/enchanted_glint_item.png`
8. `textures/misc/enchanted_glint_entity.png`
9. `textures/font/character-*.png`

作用：

1. 说明该包确实有大规模图像替换。
2. 不只是文字和字体，连魔法闪光、草方块、可疑砂砾和字体页都被重做。

#### `assets/mcwzhmeme/textures/block/two.png`

这是自定义命名空间中的贴图。

它被 `models/block/cake.json` 引用，说明：

1. 这个包使用自定义 namespace 存放专用素材。
2. 避免与原版资源冲突。

### 2.5.6 结论

`meme.teahouse.team-da0c28` 是一个跨越“语言、字体、模型、声音、合规提示”的综合资源包。

它的特点不是某一类资源特别多，而是类别特别全：

1. 文本是核心。
2. 字体是支撑。
3. 模型和贴图是补充表现层。
4. 合规提醒和 credits 说明它有成熟的发行与内容组织。

---

## 三、横向对比

### 3.1 类型对比

| 资源包 | 主要方向 | 核心目录 | 典型文件 |
|---|---|---|---|
| Better-Leaves-9.5 | 树叶美化 + 优化 | `blockstates`, `textures` | `assets/dtru/blockstates/maple_leaves.json` |
| Chat_Reporting_Helper | 聊天举报说明 UI | `lang`, `textures/gui/sprites` | `assets/fo/lang/en_us.json` |
| FreshAnimations_v1.10.5 | 实体动画增强 | `optifine/cem`, `textures/entity`, `particles` | `assets/minecraft/optifine/cem/villager.jem` |
| MandalasGUI+Dakmode_1.21.6_v2.1 | GUI / 暗色界面 | `textures/gui`, `textures/item`, `textures/particle` | `assets/minecraft/textures/gui/widgets.png` |
| meme.teahouse.team-da0c28 | 梗体中文综合包 | `lang`, `font`, `models`, `texts`, `sounds`, `cit` | `assets/minecraft/lang/zh_meme.json` |

### 3.2 结构复杂度对比

1. `Better-Leaves-9.5`：中等复杂，偏方块/模型映射。
2. `Chat_Reporting_Helper`：中等复杂，偏语言和 UI 图标。
3. `FreshAnimations_v1.10.5`：很高复杂度，涉及大量实体模型和动画参数。
4. `MandalasGUI+Dakmode_1.21.6_v2.1`：高密度 UI 资源，目录清晰但文件量大。
5. `meme.teahouse.team-da0c28`：类别最杂，属于综合型内容改造包。

### 3.3 与 Minecraft Wiki 规则的对应关系

1. `pack.mcmeta`：每个包都有，符合资源包标准结构。
2. `assets/<namespace>/textures`：五个包里都存在或被明显使用。
3. `assets/<namespace>/models`：`Better-Leaves` 与 `meme` 尤其明显。
4. `assets/<namespace>/lang`：`Chat_Reporting_Helper` 与 `meme` 是重点。
5. `assets/<namespace>/optifine/`：`FreshAnimations` 和 `meme` 体现了扩展生态使用。
6. `texts`：`meme` 使用了 `credits.json`，完全符合 Wiki 所述的文本类资源扩展机制。

---

## 四、结论

这批资源包的研究价值很高，因为它们分别覆盖了 Minecraft 资源包的几个典型方向：

1. 方块模型重映射与性能优化。
2. 聊天与举报系统的文本和图标辅助。
3. OptiFine CEM 实体模型和动画增强。
4. GUI 与暗色界面重绘。
5. 综合型本地化、字体、声音、模型、合规提示与自定义内容包。

如果要继续深入，下一步最值得做的事情是：

1. 对每个包进一步统计文件数量与命名空间分布。
2. 逐个打开代表性 `model` / `lang` / `json` 文件，整理成“功能索引表”。
3. 如果需要，我可以继续为你把这份报告扩展成“按目录逐项解释”的更长版本，或者补一份“适用版本与兼容性分析表”。

---

## 五、文件级索引附录

本附录按资源包列出“最关键、最有代表性”的文件与目录功能。它不是逐个穷尽所有文件，而是以研究和定位为目标，保留可以直接说明用途的路径。

### 5.1 `Better-Leaves-9.5` 文件索引

#### 根目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/Better-Leaves-9.5/pack.mcmeta` | 资源包元数据，定义格式、支持版本和描述 |
| `Resourcepacks/Better-Leaves-9.5/pack.png` | 资源包图标 |
| `Resourcepacks/Better-Leaves-9.5/README.md` | 说明包的优化思路、性能取向与构建方法 |
| `Resourcepacks/Better-Leaves-9.5/LICENSE` | 授权文本 |

#### 关键目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/Better-Leaves-9.5/assets/dtru/blockstates/` | `Regions Unexplored` 模组树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/dtnatures_spirit/blockstates/` | `Nature's Spirit` 模组树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/dtecologics/blockstates/` | `Ecologics` 模组树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/dtbwg/blockstates/` | `BWG` 相关树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/enderscape/blockstates/` | `Enderscape` 模组树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/ars_elemental/blockstates/` | `Ars Elemental` 相关树叶方块状态映射 |
| `Resourcepacks/Better-Leaves-9.5/assets/aether/textures/block/natural/` | Aether 树叶贴图 |
| `Resourcepacks/Better-Leaves-9.5/assets/betterleaves/models/block/` | 资源包自定义叶子模型库 |

#### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/dtru/blockstates/maple_leaves.json` | 枫叶方块映射到多种模型变体 |
| `assets/dtru/blockstates/larch_leaves.json` | 落叶松方块映射到多种模型变体 |
| `assets/dtru/blockstates/mauve_leaves_flowering.json` | 开花树叶的状态映射 |
| `assets/windswept/blockstates/pine_leaves.json` | `Windswept` 模组松叶映射 |
| `assets/ecologics/models/block/coconut_leaves4.json` | 椰子树叶模型的一个变体 |
| `assets/betterleaves/models/block/leaves_overlay.json` | 叶子覆盖层模型 |
| `assets/betterleaves/models/block/leaves_legacy.json` | 兼容旧样式的叶子模型 |

### 5.2 `Chat_Reporting_Helper` 文件索引

#### 根目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/Chat_Reporting_Helper/pack.mcmeta` | 资源包元数据与包描述 |
| `Resourcepacks/Chat_Reporting_Helper/pack.png` | 资源包图标 |

#### 关键目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/Chat_Reporting_Helper/assets/fo/lang/` | 多语言文本覆盖目录 |
| `Resourcepacks/Chat_Reporting_Helper/assets/nochatreports/textures/gui/sprites/safety_state/` | 聊天安全状态图标目录 |

#### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/fo/lang/en_us.json` | 英文聊天举报提示、说明和按钮文本 |
| `assets/fo/lang/zh_cn.json` | 简体中文聊天举报提示文本 |
| `assets/fo/lang/zh_tw.json` | 繁体中文聊天举报提示文本 |
| `assets/fo/lang/fr_fr.json` | 法语界面文本 |
| `assets/fo/lang/de_de.json` | 德语界面文本 |
| `assets/nochatreports/textures/gui/sprites/safety_state/secure.png` | 安全状态图标 |
| `assets/nochatreports/textures/gui/sprites/safety_state/insecure.png` | 不安全状态图标 |
| `assets/nochatreports/textures/gui/sprites/safety_state/unknown.png` | 未知状态图标 |
| `assets/nochatreports/textures/gui/sprites/verified_server.png` | 已验证服务器图标 |

### 5.3 `FreshAnimations_v1.10.5` 文件索引

#### 根目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/FreshAnimations_v1.10.5/pack.mcmeta` | 资源包格式和描述 |
| `Resourcepacks/FreshAnimations_v1.10.5/pack.png` | 资源包图标 |
| `Resourcepacks/FreshAnimations_v1.10.5/FAterms&conditions.txt` | 使用与再分发条款 |
| `Resourcepacks/FreshAnimations_v1.10.5/changelog1.10.5.txt` | 版本更新说明 |

#### 关键目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/optifine/cem/` | OptiFine CEM 实体模型与动画目录 |
| `Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/textures/entity/` | 实体贴图目录 |
| `Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/particles/` | 粒子定义目录 |

#### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/minecraft/optifine/cem/villager.jem` | 村民实体模型 |
| `assets/minecraft/optifine/cem/villager_animations.jpm` | 村民动画参数 |
| `assets/minecraft/optifine/cem/zombie.jem` | 僵尸实体模型 |
| `assets/minecraft/optifine/cem/wolf.jem` | 狼实体模型 |
| `assets/minecraft/optifine/cem/fox.jem` | 狐狸实体模型 |
| `assets/minecraft/optifine/cem/horse.jem` | 马实体模型 |
| `assets/minecraft/optifine/cem/creeper.jem` | 苦力怕实体模型 |
| `assets/minecraft/optifine/cem/frog_animations.jpm` | 青蛙动画参数 |
| `assets/minecraft/optifine/cem/sniffer_animations.jpm` | 嗅探兽动画参数 |
| `assets/minecraft/textures/entity/villager/villager.png` | 村民贴图 |
| `assets/minecraft/textures/entity/wolf/wolf_woods.png` | 狼变种贴图 |
| `assets/minecraft/textures/entity/frog/frog_temperate.png` | 温带青蛙贴图 |
| `assets/minecraft/particles/mycelium.json` | 粒子纹理引用定义 |

### 5.4 `MandalasGUI+Dakmode_1.21.6_v2.1` 文件索引

#### 根目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.mcmeta` | 资源包格式与支持版本 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.png` | 资源包图标 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/License.txt` | 授权说明文件 |

#### 关键目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/gui/` | 主 GUI 贴图目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/gui/container/` | 容器界面纹理目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/gui/sprites/widget/` | 按钮、滑条、复选框等控件图标目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/gui/sprites/world_list/` | 世界列表按钮图标目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/gui/sprites/toast/` | 提示 toast 图标目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/item/` | 槽位提示与空槽图标目录 |
| `Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/assets/minecraft/textures/particle/` | 粒子纹理目录 |

#### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/minecraft/textures/gui/widgets.png` | 通用 UI 控件主图集 |
| `assets/minecraft/textures/gui/icons.png` | 通用界面图标 |
| `assets/minecraft/textures/gui/resource_packs.png` | 资源包界面背景/元素 |
| `assets/minecraft/textures/gui/server_selection.png` | 服务器选择界面 |
| `assets/minecraft/textures/gui/world_selection.png` | 世界选择界面 |
| `assets/minecraft/textures/gui/container/inventory.png` | 背包界面 |
| `assets/minecraft/textures/gui/container/crafting_table.png` | 工作台界面 |
| `assets/minecraft/textures/gui/container/anvil.png` | 铁砧界面 |
| `assets/minecraft/textures/gui/container/beacon.png` | 信标界面 |
| `assets/minecraft/textures/gui/container/smithing.png` | 砂轮/锻造相关界面 |
| `assets/minecraft/textures/gui/container/legacy_smithing.png` | 旧版锻造台界面 |
| `assets/minecraft/textures/gui/sprites/widget/button.png` | 按钮默认状态 |
| `assets/minecraft/textures/gui/sprites/widget/button_highlighted.png` | 按钮高亮状态 |
| `assets/minecraft/textures/gui/sprites/widget/checkbox.png` | 复选框默认状态 |
| `assets/minecraft/textures/gui/sprites/widget/slider.png` | 滑条控件 |
| `assets/minecraft/textures/gui/sprites/world_list/join.png` | 世界/服务器加入按钮 |
| `assets/minecraft/textures/gui/sprites/dialog/warning_button.png` | 警告对话框按钮 |
| `assets/minecraft/textures/item/empty_slot_sword.png` | 武器槽位提示图标 |
| `assets/minecraft/textures/item/empty_armor_slot_helmet.png` | 头盔槽位提示图标 |
| `assets/minecraft/textures/particle/heart.png` | 粒子心形图标 |

### 5.5 `meme.teahouse.team-da0c28` 文件索引

#### 根目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/meme.teahouse.team-da0c28/pack.mcmeta` | 包元数据，含语言注册和作者信息 |
| `Resourcepacks/meme.teahouse.team-da0c28/pack.png` | 资源包图标 |
| `Resourcepacks/meme.teahouse.team-da0c28/LICENSE` | CC BY-SA 4.0 协议文本 |

#### 关键目录

| 路径 | 功能 |
|---|---|
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/lang/` | 梗体中文本地化目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/font/` | 自定义字体与字形映射目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/item/` | 自定义物品模型目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/models/block/` | 自定义方块模型目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/texts/` | credits 等文本目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/regional_compliancies.json` | 地区合规弹窗定义文件 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/optifine/cit/` | OptiFine CIT 配置目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/minecraft/sounds/item/goat_horn/` | 山羊号角音频目录 |
| `Resourcepacks/meme.teahouse.team-da0c28/assets/mcwzhmeme/textures/block/` | 自定义命名空间贴图目录 |

#### 代表文件

| 路径 | 功能 |
|---|---|
| `assets/minecraft/lang/zh_meme.json` | 核心梗体中文语言文件 |
| `assets/minecraft/font/default.json` | 字体 provider 定义，控制大量字形引用 |
| `assets/minecraft/models/item/chicken_spawn_egg.json` | 鸡生成蛋物品模型重定向 |
| `assets/minecraft/models/item/wolf_spawn_egg.json` | 狼生成蛋物品模型重定向 |
| `assets/minecraft/models/block/observer_on.json` | 观察者方块开启状态模型 |
| `assets/minecraft/models/block/cake.json` | 自定义蛋糕模型 |
| `assets/minecraft/texts/credits.json` | 结构化鸣谢名单 |
| `assets/minecraft/regional_compliancies.json` | 按地区控制定时弹窗与提示 |
| `assets/minecraft/optifine/cit/suspicious_stew/*.properties` | 可疑炖菜效果纹理条件配置 |
| `assets/minecraft/optifine/cit/suspicious_stew/*.png` | 可疑炖菜不同效果贴图 |
| `assets/minecraft/sounds/item/goat_horn/call0.ogg` | 山羊号角音效 |
| `assets/minecraft/textures/misc/enchanted_glint_item.png` | 附魔闪光贴图 |
| `assets/minecraft/textures/block/suspicious_sand_0.png` | 可疑砂砾/砂石纹理之一 |
| `assets/mcwzhmeme/textures/block/two.png` | 自定义方块纹理，被 `cake.json` 引用 |

---

## 六、附录使用建议

1. 如果你要继续做更细的研究，建议按“文件类型”继续拆：`lang`、`models`、`textures`、`optifine`、`texts`。
2. 如果你要做兼容性研究，建议下一步统计每个包的 `pack_format` 与资源包版本范围。
3. 如果你要做视觉研究，建议优先打开 `pack.png`、GUI 图集、实体主纹理和模型文件。
4. 如果你要做语言研究，建议优先比对 `zh_meme.json` 与 `en_us.json`、`zh_cn.json`。
