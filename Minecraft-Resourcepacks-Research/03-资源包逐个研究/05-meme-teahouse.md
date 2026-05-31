## 2.5 `meme.teahouse.team-da0c28`

### 3.5.1 根目录结构

路径：`Resourcepacks/meme.teahouse.team-da0c28/`

```text
assets/
LICENSE
pack.mcmeta
pack.png
```

### 3.5.2 包定位

这是一个“梗体中文”资源包，目标明显不是单纯汉化，而是：

1. 把大量 Minecraft 文本改造成梗化表达。
2. 使用自定义字体与大量字形资源支撑特殊字符。
3. 同时改造部分模型、声音、文本和合规提示。

它是本次样本中最“综合型”的包之一。

### 3.5.3 关键文件说明

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

### 3.5.4 资源内容结构

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

### 3.5.5 关键目录功能

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

### 3.5.6 结论

`meme.teahouse.team-da0c28` 是一个跨越“语言、字体、模型、声音、合规提示”的综合资源包。

它的特点不是某一类资源特别多，而是类别特别全：

1. 文本是核心。
2. 字体是支撑。
3. 模型和贴图是补充表现层。
4. 合规提醒和 credits 说明它有成熟的发行与内容组织。

---

