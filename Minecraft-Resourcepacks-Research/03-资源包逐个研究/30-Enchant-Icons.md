# 30. Enchant Icons v1.3

## 根目录结构

```
enchant-icons-1.21.7-1.21.8-v1.3/
├── assets/
│   └── minecraft/
│       ├── font/
│       │   └── default.json          # 自定义字体定义
│       ├── lang/
│       │   └── [137 个语言文件]*.json # 所有语言版本的附魔名称修改
│       └── textures/
│           └── misc/
│               ├── boots.png         # 靴子图标
│               ├── bow.png           # 弓图标
│               ├── chestplate.png    # 胸甲图标
│               ├── crosbow.png       # 弩图标
│               ├── fishing.png       # 钓鱼竿图标
│               ├── helmet.png        # 头盔图标
│               ├── leggings.png      # 护腿图标
│               ├── mace.png          # 重锤图标 (1.21+)
│               ├── pickaxe.png       # 镐图标
│               ├── skull.png         # 头颅/诅咒图标
│               ├── spear.png         # 长矛/密技图标 (1.21.7+)
│               ├── star.png          # 星星/经验修复图标
│               ├── sword.png         # 剑图标
│               └── trident.png       # 三叉戟图标
├── .gitattributes
├── pack.mcmeta
├── pack.png
└── README.md
```

## 包定位

作者：CountX（或 CountXD）。版本 v1.3，目标版本 Minecraft 1.21.7-1.21.8。本包是一个利用 **Minecraft 自定义字体系统**在附魔名称前添加图标（icon）的资源包，使玩家在查看物品上的附魔时，可以通过图标快速识别附魔类型。

与 Even Better Enchants（第 25 号包）不同，Enchant Icons 不修改附魔书的物品模型，而是通过**重写语言文件 + 自定义字体**的方式，在所有显示附魔名称的地方（物品工具提示、附魔台界面、铁砧界面等）添加设备类型图标。

包的设计理念是"设备标识"——每种图标代表附魔适用的装备类型（头盔、胸甲、护腿、靴子、剑、镐、弓、弩、三叉戟、钓鱼竿等），而非附魔本身的魔法属性。这使得玩家可以通过图标快速判断某附魔适用于哪种装备。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 64,
    "description": "         "
  }
}
```

- pack_format 64（对应 1.21.8）。
- 描述中使用的是 Unicode 私有区域字符（ 等），这些字符在安装了本包后会被字体纹理映射为图标。这是本包所有功能的"元展示"——包描述本身就在展示其图标系统。

### font/default.json

这是本包的核心技术文件。它利用 Minecraft 的字体系统，将 Unicode 私有区域（Private Use Area）字符映射为位图图标：

```json
{
  "providers": [
    { "type": "bitmap", "file": "minecraft:misc/helmet.png",    "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/chestplate.png","ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/leggings.png",  "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/boots.png",     "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/sword.png",     "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/pickaxe.png",   "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/trident.png",   "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/bow.png",       "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/crosbow.png",   "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/fishing.png",   "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/star.png",      "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/skull.png",     "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/mace.png",      "ascent": 8, "height": 16, "chars": [""] },
    { "type": "bitmap", "file": "minecraft:misc/spear.png",     "ascent": 8, "height": 16, "chars": [""] }
  ]
}
```

每个定义项包含：
- **type**：`bitmap`，表示这是一个位图字体提供者。
- **file**：纹理文件的资源路径。
- **ascent**：8，字符的基线偏移量，控制图标在文本行中的垂直位置。
- **height**：16，每个字符的高度（像素），Minecraft 默认字体高度为 8，设为 16 使图标高度为普通字符的两倍。
- **chars**：一个字符数组，每个元素是一个 Unicode 码点，对应一个图标映射。

映射关系：
| 码点 | 图标 | 用途 |
|------|------|------|
|  | 头盔 | 头盔类附魔（水下呼吸、水下速掘等） |
|  | 胸甲 | 护甲保护类附魔 |
|  | 护腿 | 护腿类附魔（迅捷潜行等） |
|  | 靴子 | 靴子类附魔（摔落保护、冰霜行者、深海探索者、灵魂疾行） |
|  | 剑 | 武器类附魔（锋利、亡灵杀手、节肢杀手、火焰附加、抢夺、击退、横扫之刃） |
|  | 镐 | 工具类附魔（效率、精准采集、时运、丝触） |
|  | 三叉戟 | 三叉戟附魔（忠诚、穿刺、激流、引雷） |
|  | 弓 | 弓类附魔（力量、冲击、火焰、无限） |
|  | 弩 | 弩类附魔（快速装填、多重射击、穿透） |
|  | 钓鱼竿 | 钓鱼附魔（海之眷顾、诱饵） |
|  | 星星 | 通用附魔（经验修补、耐久、消失诅咒） |
|  | 头颅 | 诅咒类（绑定诅咒、消失诅咒） |
|  | 重锤 | 1.21+ 重锤附魔（风爆、致密、破盾） |
|  | 长矛 | 1.21.7+ 密技附魔（lunge） |

### lang/ 目录（137 个语言文件）

这是本包的第二大技术组件。每个语言文件（如 `en_us.json`）中，将所有附魔名称翻译条目修改为在名称前加上对应的图标字符和颜色代码：

```json
{
  "enchantment.minecraft.aqua_affinity": "§b Aqua Affinity",
  "enchantment.minecraft.sharpness": "§a Sharpness",
  "enchantment.minecraft.protection": "§d Protection",
  "enchantment.minecraft.mending": "§e Mending",
  ...
}
```

- `§b`：浅蓝色颜色代码（`§b`）。
- ``：图标字符，被字体系统渲染为图标。
- 每个附魔使用不同的颜色和图标组合，实现了一致的视觉体系。

**颜色编码体系**：
- 浅蓝色（§b）：头盔/靴子/三叉戟/钓鱼竿/工具类附魔
- 浅绿色（§a）：剑/远程武器/重锤类附魔
- 浅紫色/粉红色（§d）：通用/护甲类附魔
- 黄色（§e）：耐久/经验修补类
- 红色（§c）：火焰/诅咒类
- 深绿色（§2）：爆炸保护、荆棘
- 深蓝色（§1）：忠诚
- 金色（§6）：穿透、力量、亡灵杀手
- 深灰色（§7）：未使用
- 深红色（§4）：诅咒

**多语言支持**：137 个语言文件覆盖了 Minecraft 全部官方语言及社区语言变体，包括稀有语言如海盗语（en_pt）、克林贡语（tlh_aa）、托尔金精灵语（qya_aa）等。这是该包最具扩展性的技术成就。

### textures/misc/ 中的图标纹理

14 个 PNG 纹理文件，每个都是 16x16 像素的图标，使用白色线稿风格：

- 盔甲类（头盔、胸甲、护腿、靴子）：以装备轮廓为设计
- 武器类（剑、弓、弩）：以武器形状为设计
- 工具类（镐）：以镐头为设计
- 特殊类（三叉戟、钓鱼竿、重锤、长矛）：对应特殊装备
- 状态类（星星：通用/修复；头颅：诅咒）

自发光白色纹理配合 Minecraft 的颜色代码可以渲染为任意颜色，这是字体位图的优势——一个纹理可以配合不同颜色代码呈现多种颜色效果。

## 技术特点

1. **自定义字体系统**：这是本包的核心技术，利用 Minecraft 1.16+ 引入的自定义字体系统（font/default.json 的 bitmap provider）将 Unicode 私有区域字符映射为位图图标。这是最轻量、最通用的图标添加方式。

2. **语言文件重写**：通过修改 137 个语言文件中的附魔名称条目，在每个附魔名前插入图标字符和颜色代码。这意味着图标会出现在任何显示附魔名称的地方——物品工具提示、附魔台、铁砧、命令输出等。

3. **通用兼容性**：字体系统和语言文件重写都是原版机制，不依赖任何 Mod 或 OptiFine。兼容性极佳，可以在任何客户端环境下工作。

4. **颜色 + 图标双编码**：每个附魔通过颜色代码和图标字符的组合实现双重视觉标识。玩家可以通过颜色快速判断附魔类别（红色=火/诅咒，绿色=剑/武器），通过图标判断适用装备类型。

5. **137 种语言覆盖**：语言文件覆盖范围极广，包括几乎所有 Minecraft 社区支持的语言。这在资源包中非常罕见，是全球化设计的典范。

6. **无纹理替换**：本包不替换任何原版纹理或模型，完全在字体和语言层面工作，因此与任何纹理包完全兼容，不会产生冲突。

7. **版本针对性强**：包名明确标注 1.21.7-1.21.8，说明这是针对特定版本的制作，包含了 1.21.7 新增的 lunge 附魔（spear 图标）。

## 结论

Enchant Icons v1.3 是一个设计精巧、技术优雅的 UI 增强型资源包。它利用 Minecraft 原版的字体系统和语言文件机制，在所有附魔名称前添加了设备类型图标和颜色标识，使玩家可以快速识别附魔种类和适用装备。

其最大优势在于**通用兼容性**——不需要 OptiFine、不需要 Mod，纯原版机制，与其他任何资源包完美共存。137 种语言覆盖体现了全球化设计思维。14 种图标覆盖了所有附魔类型，包括 1.21+ 新附魔。

不足之处：
1. 图标不可自定义开关，只能全量启用。
2. 字体修改可能与其他也修改 default.json 的资源包冲突。
3. 语言文件覆盖所有语言版本意味着包体较大，且需要随 Minecraft 版本更新同步语言文件。

总体而言，这是目前 Minecraft 附魔美化领域最优雅、兼容性最好的解决方案之一，适合追求 UI 体验优化的任何玩家。
