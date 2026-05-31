# 20. Faithful 32x - 1.21.8
## 根目录结构
```
Faithful 32x - 1.21.8/
├── pack.mcmeta
├── pack.png
├── LICENSE.txt
└── assets/
    ├── fabric/
    ├── forge/
    ├── minecraft/
    ├── modmenu/
    └── neoforge/
```

## 包定位
Faithful 32x 是 Minecraft 社区中最负盛名的高清资源包之一，由 Vattic 创立并由 Faithful 团队持续维护。本包的核心定位是将原版 Minecraft 的像素风格完整保留，但将分辨率从默认的 16x 提升至 32x，即在保持原版美术风格不变的前提下提供四倍的纹理细节。本版本对应 Minecraft 1.21.8 正式版，于 2025 年 12 月发布，pack.mcmeta 中标明支持格式范围为 56 至 64。描述信息为 "The go-to 32x resource pack."，简洁而自信地宣告了其在社区中的标杆地位。

本包不是对原版风格的颠覆，而是"原版风格的高清重制版"。它适用于所有希望在保持原汁原味 Minecraft 视觉体验的前提下获得更清晰画面的玩家，也是众多衍生资源包和补丁包的基础平台。

## 关键文件说明

### pack.mcmeta
```json
{
  "pack": {
    "description": "The go-to 32x resource pack.\n§8December 2025 Release",
    "min_format": 56,
    "max_format": 64
  }
}
```
采用新版 metadata 格式（Minecraft 1.21.5+ 引入的 min_format/max_format 字段），以明确声明支持的版本区间为 1.21.5 至 1.21.8。这种写法允许资源包在未来的兼容性版本中继续工作，同时避免在过老的版本中加载。

### pack.png
约 74KB 的缩略图，用于在游戏中资源包选择界面显示。

### LICENSE.txt
3225 字节的许可文件，明确规定了资源包的使用、分发和修改条款。

## 资源内容结构
本包共包含 4365 个文件，总大小约 1.1GB，是相当庞大的资源包。其 assets 目录结构如下：

### assets/minecraft/（核心资产，占绝大多数文件）
包含完整的 Minecraft 原版资源覆盖：
- **textures/block/**：所有方块纹理的 32x 重制版
- **textures/entity/**：所有生物实体纹理 (allay, axolotl, bee, camel, cat, chicken, cow, creeper, enderman, horse, piglin, villager, warden, wolf 等数十种生物)
- **textures/entity/equipment/**：坐骑装备纹理，包括骆驼鞍、驴鞍、马铠、Happy Ghast 躯体、狼铠、翅膀等 1.21 新增内容
- **textures/environment/**：环境纹理（天空盒、云雾等）
- **textures/font/**：字体纹理（32x 高清字体）
- **textures/gui/**：游戏界面纹理
  - **textures/gui/sprites/**：新版 Sprite 系统纹理，包含 advancements、boss_bar、container（铁砧、信标、高炉、酿造台、束口袋、制图台、合成器、附魔台、熔炉、磨石、马匹界面、织布机、锻造台、烟熏炉、切石机、村民交易）、dialog、hud、icon、notification、popup、recipe_book、toast、tooltip、widget 等
  - **textures/gui/title/**：标题画面及背景纹理
- **textures/item/**：物品纹理
- **textures/map/**：地图及地图标记纹理
- **textures/mob_effect/**：状态效果图标
- **textures/painting/**：画作纹理
- **textures/particle/**：粒子效果纹理
- **textures/trims/**：盔甲纹饰纹理（包括实体和物品两种变体）
- **models/item/redstone_torch.json**：自定义物品模型

### optifine/ 扩展
本包包含大量的 OptiFine 兼容扩展：
- **optifine/ctm/glass/**：所有 16 种染色玻璃及普通玻璃的连接纹理（CTM），每种玻璃各包含 47 张子纹理和 .properties 配置文件，实现无缝连接的视觉效果
- **optifine/ctm/bookshelf/**：书架纹理的连接纹理
- **optifine/ctm/red_sandstone/** 和 **optifine/ctm/sandstone/**：砂岩类连接纹理

### 模组兼容层
- **assets/fabric/**：Fabric API 的 GUI 按钮纹理
- **assets/forge/**：Forge 的牛奶流体纹理、流体桶遮罩、GUI 版本检查图标等
- **assets/neoforge/**：NeoForge 的对应内容（与 Forge 部分结构完全镜像）
- **assets/modmenu/**：Mod Menu 模组的图标纹理

## 关键目录功能
| 目录 | 功能 |
|------|------|
| textures/block | 所有方块纹理，32x32 分辨率，覆盖超过 200 种方块 |
| textures/entity | 生物实体及其变体纹理，涵盖 1.21 全部生物 |
| textures/entity/equipment | 1.21 新增的装备系统分离纹理 |
| textures/gui/sprites | 新版 Sprite 系统，替代旧版 GUI 大图 |
| textures/trims | 盔甲纹饰系统的纹理文件 |
| optifine/ctm | OptiFine 连接纹理支持，主要用于玻璃和无缝方块 |
| optifine/ctm/glass | 共 17 种玻璃/染色玻璃的 47 方向 CTM 纹理 |
| fabric/forge/neoforge | 三大主流模组加载器的兼容纹理 |

## 技术特点

1. **像素完美缩放**：Faithful 32x 最核心的技术成就是其像素完美（pixel perfect）的放大算法。每个像素从 16x 放大到 32x 时，不是简单的最近邻插值，而是人工逐像素重新绘制，确保线条的锐利度和细节的准确性。这使得 32x 版本看起来"就是原版，只是更清晰了"。

2. **全面的版本覆盖**：本包覆盖了 Minecraft 1.21.8 的所有新增内容，包括 Creaking 生物、Happy Ghast、新的狼铠变种、Breeze 等，以及盔甲纹饰系统的所有新样式。

3. **模组加载器兼容**：同时为 Fabric、Forge、NeoForge 三大主流模组加载器提供兼容纹理，是极少数能做到如此全面兼容的资源包之一。

4. **完整的 GUI 覆盖**：全面支持 Minecraft 1.21 引入的 Sprite 系统，GUI 纹理不再使用旧版的大图拼接方式，而是使用独立的 sprite 文件，这大大提高了资源包的可维护性和模组兼容性。

5. **OptiFine CTM 支持**：玻璃类方块使用 47 方向连接纹理（基于 OptiFine 的 CTM 格式），使得玻璃在放置时能够无缝连接，大幅提升视觉效果。这是 Faithful 32x 的传统强项之一。

6. **庞大的规模**：4365 个文件，1.1GB 的总大小，使其成为社区中资产最完整的资源包之一，几乎覆盖了游戏的所有视觉元素。

7. **固定的更新节奏**：Faithful 团队保持与 Minecraft 版本更新同步的发布节奏，每个大版本和小版本都有对应的 Faithful 更新。

## 结论
Faithful 32x 是 Minecraft 高清资源包的行业标杆。它不追求风格的创新或颠覆，而是专注于将原版体验以更高的分辨率呈现给玩家。其 32x 的分辨率选择是经过深思熟虑的——16x 太粗糙，64x 和 128x 又需要远高于原版的性能开销，32x 在视觉提升和性能影响之间取得了最佳的平衡点。

在分类上，本包虽然主要贡献在纹理领域，但其字体纹理（textures/font/）的重制也属于字体类别的重要部分。它是其他所有字体类和纹理类资源包的基础参考——许多字体补丁包和纹理补丁包都明确标注"需要 Faithful 32x 作为基础"。

本包的社区地位无可撼动：它是 CurseForge 和 Modrinth 上下载量最高的资源包之一，是无数玩家入门高清 Minecraft 的首选，也是其他资源包作者参考和学习的范本。Faithful 团队的专业维护、庞大的社区贡献者网络、以及持续十多年的更新历史，使其成为 Minecraft 资源包生态中最值得信赖的基石之一。
