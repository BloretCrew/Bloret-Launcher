# 06. Enhanced Audio r7

## 根目录结构
```text
assets/
pack.mcmeta
pack.png
```

## 包定位
Enhanced Audio r7 是一个全面性的声音增强资源包，由作者 Frawzy 创作。该包的目标是彻底替换 Minecraft 原版的声音系统，为游戏中的方块交互、实体行为、环境氛围、玩家动作和 UI 反馈提供更加丰富、真实且具有沉浸感的音频体验。Release 7 版本包含了超过 660 个独立音频文件，覆盖了从洞穴环境音到玩家受伤音效的几乎所有游戏内声音事件。该包适用于 1.20（pack_format 15）及以上所有版本，通过 overlay 系统实现了对未来的向前兼容。

该包的设计理念是"增强而非改变"——它保留了原版声音事件的结构和分类方式，但提供了更高品质、更多变种和更细腻的音频素材。主要目标用户是追求沉浸式游戏体验的玩家，以及认为原版音效过于单薄或重复的玩家。

## 关键文件说明
### pack.mcmeta
路径：`Resourcepacks/Enhanced Audio r7/pack.mcmeta`

该文件定义了包的基本信息和版本兼容性。pack_format 为 15（对应 Minecraft 1.20），但 `supported_formats` 设置为 `min_inclusive: 15, max_inclusive: 999`，意味着该包声明兼容从 1.20 到任意未来版本。

最引人注目的是其 overlay 系统定义：
- `20-3`：格式范围 22-999（对应 1.20.3+）
- `21-2`：格式范围 42-999（对应 1.21.2+）
- `21-5`：格式范围 55-999（对应 1.21.5+）

然而，实际的资源包根目录中并未创建这些 overlay 目录。这意味着这些 overlay 声明是"预留性质"的——它们为未来可能添加的版本特定声音修复预留了位置，但目前所有声音文件都位于默认的 `assets/minecraft/sounds/` 路径下。这是一种值得注意的前向兼容设计模式。

### pack.png
路径：`Resourcepacks/Enhanced Audio r7/pack.png`

资源包选择器图标。

### assets/minecraft/sounds.json
路径：`Resourcepacks/Enhanced Audio r7/assets/minecraft/sounds.json`

这是一个体积庞大的 JSON 文件（超过 1100 行），定义了全部声音事件的资源映射。该文件是理解整个包的核心。每个声音事件都使用 `"replace": true` 标记，确保完全覆盖原版声音定义。

声音条目分为两大类：
1. **简单列表形式**：直接列出音频文件路径，如 `"block.stone.break"` 使用 `["block/stone/break1", "break2", ...]`，游戏随机选取。
2. **对象数组形式**：每个条目包含 `name`、`volume` 和 `pitch` 参数，如 `"block.stone.hit"` 对每个声音设置了 `volume: 1, pitch: 1.3`。这允许对单个音频片段进行精细调整。

所有声音引用都遵循省略 `.ogg` 扩展名的路径格式（Minecraft 标准做法），路径相对于 `sounds/` 目录。

## 资源内容结构
该包仅使用 `minecraft` 命名空间，所有资源集中在 `assets/minecraft/sounds/` 目录下。目录结构如下：

```text
assets/minecraft/
  sounds.json
  sounds/
    ambient/
      cave/          (23个洞穴环境音文件)
      underwater/
        additions/   (14个水下环境音 + 音效)
      weather/       (14个天气音效：雨、雷、闪电)
    block/
      barrel/        (3个桶开关音效)
      blastfurnace/  (5个高炉运行音效)
      brewing_stand/ (2个酿造音效)
      campfire/      (6个营火噼啪音效)
      cherry_wood/   (9个樱花木音效)
      cherrywood_door/ (4个樱花木门音效)
      chest/         (3个箱子开关音效)
      cobweb/        (14个蜘蛛网音效)
      composter/     (8个堆肥桶音效)
      deepslate/     (4个深板岩音效)
      enderchest/    (4个末影箱音效)
      furnace/       (4个熔炉音效)
      glass/         (4个玻璃音效)
      grass/         (4个草音效)
      gravel/        (4个沙砾音效)
      iron/          (8个铁质方块音效)
      pumpkin/       (4个南瓜音效)
      rooted_dirt/   (6个缠根泥土音效)
      sand/          (4个沙子音效)
      smoker/        (5个烟熏炉音效)
      snow/          (4个雪音效)
      stone/         (12个石头音效)
      sweet_berry_bush/ (4个甜浆果丛音效)
      vine/          (10个藤蔓音效)
      wood/          (4个木头音效)
      wooden_door/   (10个木门音效)
    damage/
      fall_type/     (多种材质摔落音效)
      gore/          (8个血腥受伤/死亡音效)
    dig/             (4个挖掘音效)
    entity/
      fish/          (鱼类音效)
      player/
        attack/      (攻击音效)
        eating/      (7个咀嚼音效)
        hurt/        (3个火焰受伤音效)
    fire/
      on/            (7个火焰燃烧/熄灭音效)
    fireworks/       (8个烟花音效)
    item/
      anvil/         (9个铁砧音效)
      break/         (4个物品破坏音效)
      bucket/        (桶音效)
      bundle/        (4个收纳袋音效)
      elytra/        (2个鞘翅飞行音效)
      plant/         (4个收获音效)
      throwables/    (10+个投掷物音效)
        bottle/      (3个药水破裂音效)
    liquid/          (5个液体音效)
    minecart/        (矿车音效)
    mob/
      chicken/       (鸡音效)
      cow/           (牛音效)
      irongolem/     (铁傀儡音效)
      pig/           (猪音效)
      sheep/         (羊音效)
      skeleton/      (2个骷髅射击音效)
      wolf/
        classic/     (10+个经典狼音效)
    portal/          (5个传送门音效)
    random/          (5个随机音效)
    step/            (4个玻璃脚步声)
    tile/
      piston/        (活塞音效)
    ui/
      hud/           (HUD音效)
      toast/         (吐司通知音效)
```

## 关键目录功能

### ambient/ 环境音效
这是该包最突出的改进领域之一。洞穴环境音从原版的少量文件扩展到了 23 个变种，大幅减少了重复感。水下环境音新增了丰富的音效层，包括动物声、鲸鱼低鸣、气泡、噼啪声、黑暗氛围音、水滴声和流水声，营造出极为沉浸的水下体验。天气音效同样经过全面重制，雨声有 8 个变种，雷声有 3 组（近距离、远距离、长距离），闪电打击有 3 种不同音效。

### block/ 方块音效
对方块交互音效进行了全面增强。每个方块类型（石头、木头、草、沙砾、沙子、玻璃、铁、雪、深板岩等）都获得了专门的 break、hit、step、place、fall 音效，且大多包含 4-8 个随机变种。特别值得注意的是为 1.20 新增的樱花木系列和 1.19 深板岩系列提供了专属音效，体现了对最新版本内容的跟进。setp 音效作为独立的音效文件存在，这在一般资源包中较为少见。

### damage/gore/ 受伤音效
该包引入了"血腥"风格的受伤音效，包含 6 种出血声和 2 种死亡声。这些音效被同时分配给玩家、敌对生物和通用实体，统一了受伤反馈体验。此外还有针对不同方块类型的摔落音效（石头、草地、沙砾、羊毛、沙子、木头、雪、玻璃），使摔落在不同表面上的声音更具差异性。

### item/throwables/ 投掷物音效
对游戏中的各种投掷物（鸡蛋、末影珍珠、经验瓶、钓鱼线、滞留药水、雪球、喷溅药水、女巫药水）分别提供了定制音效，每个都经过音调和音量调整。药水破裂声也有 3 个独立变种。这种细粒度的区分在大多数字资源包中很少见。

### mob/wolf/classic/ 经典狼音效
为狼的六种变体（愤怒的、大的、可爱的、暴躁的、猪灵似的、悲伤的）分别定义了完整的音效集（ambient、death、growl、hurt、pant、whine）。所有变体共用了相同的经典音源，但通过不同的 pitches 和 volumes 实现了声音上的微妙区分。

## 技术特点

1. **大规模变种系统**：许多声音事件提供 4-8 个变种，大幅降低了重复感。洞穴环境音甚至有 23 个变种。

2. **精细的音量/音调控制**：在 sounds.json 中使用对象语法为每个音效片段单独设置 volume 和 pitch，实现了比简单文件名列表更精细的控制。例如，投掷物音效统一使用 pitch: 2.0 创造"投掷"的急促感，而方块 hit 音效使用 pitch: 1.3-1.5 模拟敲击的清脆感。

3. **前向兼容 overlay 设计**：pack.mcmeta 中声明了三个版本特定的 overlay 目录（20-3、21-2、21-5），虽然目前为空，但这种设计允许在不破坏旧版本兼容性的前提下，为未来的 Minecraft 版本添加版本特定的声音修复。

4. **材质类型化摔落音效**：为 8 种不同材质分别设计了摔落音效，比原版仅区分"摔落"和"重摔"的方式大大细化。

5. **无 README/license 文件**：该包没有附带 README 或许可证文件，仅通过 pack.png 和 pack.mcmeta 中的描述（"Enhanced Audio | Release 7"）提供识别信息。`assets/minecraft/sounds/ui/toast/c.txt` 文件中仅包含作者信息。

## 结论
Enhanced Audio r7 是一个极其全面和高质量的声音增强资源包，代表了 Minecraft 声音资源包的最高复杂度水平。它的技术价值在于：

1. 展示了如何大规模替换游戏声音资源而不引入任何纹理、模型或语言资源——这是一个纯粹的声音包。
2. 其 sounds.json 文件是研究 Minecraft 声音事件系统的绝佳参考，涵盖了从 1.20 到最新版本的几乎所有声音事件。
3. 变种系统的使用和精细的音调/音量控制提供了可借鉴的最佳实践。
4. 尽管定义了 overlay 但未创建对应目录的做法，展示了"声明式向前兼容"的设计思路。

对于资源包开发者而言，该包是学习如何在 sounds.json 中正确使用对象语法、设置资源替换标志、以及组织大规模音频资源目录结构的优秀参考。
