# 27. ProgrammerArtFix 26.0

## 根目录结构

```
ProgrammerArtFix-26.0/
├── assets/
│   └── minecraft/
│       ├── models/
│       │   └── block/
│       │       └── cocoa_stage2.json
│       ├── optifine/
│       │   └── ctm/
│       │       └── tinted_glass/
│       │           └── [47 个 CTM 纹理切片]
│       ├── particles/
│       │   └── [粒子纹理]
│       └── textures/
│           ├── block/           [207 个方块纹理]
│           ├── entity/          [63 个实体纹理]
│           │   ├── boat/
│           │   ├── chest_boat/
│           │   ├── conduit/
│           │   ├── cow/
│           │   ├── hoglin/
│           │   ├── horse/
│           │   ├── illager/
│           │   ├── iron_golem/
│           │   ├── piglin/
│           │   ├── player/ (slim/ wide)
│           │   ├── signs/ (hanging/)
│           │   ├── squid/
│           │   ├── strider/
│           │   ├── villager/ (profession/ type/)
│           │   ├── wolf/
│           │   └── zombie_villager/ (profession/ type/)
│           ├── gui/             [29 个 GUI 纹理]
│           │   ├── container/
│           │   ├── hanging_signs/
│           │   ├── realms/
│           │   └── sprites/ (icon/ recipe_book/ social_interactions/ spectator/ toast/ widget/)
│           ├── item/            [162 个物品纹理]
│           ├── map/ (decorations/)
│           ├── mob_effect/
│           ├── particle/
│           └── trims/ (color_palettes/ items/)
├── deprecated37/               [overlay, 格式 17-36]
│   └── assets/minecraft/textures/entity/horse/armor/ + models/armor/
├── deprecated43/               [overlay, 格式 17-42]
│   └── assets/minecraft/textures/item/ (empty_armor_slot_* etc.)
├── patch37/                    [overlay, 格式 37-75]
│   └── assets/minecraft/textures/entity/equipment/ (horse_body/ etc.)
├── patch43/                    [overlay, 格式 43-75]
│   └── assets/minecraft/textures/gui/sprites/container/slot/
├── drop1_20/                   [overlay, 格式 20-75]
│   └── assets/minecraft/textures/entity/ (bat/ wolf/ etc.)
├── update1_21/                 [overlay, 格式 33-75]
│   └── assets/minecraft/textures/ (block/ entity/ item/ mob_effect/ painting/)
├── drop24_3/                   [overlay, 格式 35-75]
│   └── assets/minecraft/models/block/ + textures/item/
├── drop24_4/                   [overlay, 格式 40-75]
│   └── assets/minecraft/textures/ (block/ entity/ item/ particle/)
├── drop25_1/                   [overlay, 格式 52-75]
│   └── assets/minecraft/textures/ (block/ entity/ item/ particle/)
├── drop25_2/                   [overlay, 格式 56-75]
│   ├── assets/minecraft/models/block/ + textures/
│   └── (block/ entity/ equipment/ environment/ item/)
├── drop25_3/                   [overlay, 格式 56-75]
│   └── assets/minecraft/textures/ (block/ entity/ equipment/ item/)
├── drop25_4/                   [overlay, 格式 71-75]
│   └── assets/minecraft/textures/ (block/ entity/ equipment/ item/ mob_effect/)
├── pack.mcmeta
└── pack.png
```

## 包定位

ProgrammerArtFix（作者不详）是一个大规模的历史性修复资源包，旨在将 Minecraft "程序员美术"（Programmer Art，即原版默认纹理风格，俗称"旧版风格"）中因版本更新而损坏或缺失的纹理修复为与当前版本兼容的格式。

从 v26.0 版本来看，本包的核心理念是：为旧版纹理风格在新版中的兼容性提供系统化的修复方案。它不是一个风格美化包，而是一个**兼容性/修复性**资源包——确保使用旧版 Programmer Art 纹理的玩家在新版本中不会遇到纹理丢失、模型错误或渲染异常。

包中包含了从 Minecraft 1.20（pack_format 15）至今所有版本迭代中变更的纹理和模型，并通过 overlays 系统实现了针对不同游戏版本的条件加载。总纹理数量超过 800 个，覆盖了方块、物品、实体、GUI、粒子、状态效果、旗帜图案等多个领域。

同时包也提供了 OptiFine CTM（连接纹理）支持，用于着色玻璃的平滑连接效果，共 47 个纹理切片。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 15,
    "supported_formats": [15, 75],
    "description": "A patch for Programmer Art"
  },
  "overlays": {
    "entries": [
      { "directory": "deprecated37", "formats": [17, 36] },
      { "directory": "deprecated43", "formats": [17, 42] },
      { "directory": "patch37", "formats": [37, 75] },
      { "directory": "patch43", "formats": [43, 75] },
      { "directory": "drop1_20", "formats": [20, 75] },
      { "directory": "update1_21", "formats": [33, 75] },
      { "directory": "drop24_3", "formats": [35, 75] },
      { "directory": "drop24_4", "formats": [40, 75] },
      { "directory": "drop25_1", "formats": [52, 75] },
      { "directory": "drop25_2", "formats": [56, 75] },
      { "directory": "drop25_3", "formats": [56, 75] },
      { "directory": "drop25_4", "formats": [71, 75] }
    ]
  }
}
```

这是本包最核心的设计文件。它通过 **Minecraft 1.20 引入的 overlays 系统**，将资源包拆分为多个独立的覆盖层，每个覆盖层只在特定的 pack_format 版本范围内生效。其设计哲学如下：

- **基础包**（pack_format 15）：提供所有版本的通用纹理修复，格式为 15 及以上。
- **deprecated37**（格式 17-36）：包含在 1.16.2-1.19.2 期间有效的旧纹理（如旧的马铠模型路径），在 1.19.3+ 中被弃用前仍保持兼容。
- **deprecated43**（格式 17-42）：包含在 1.20.3 之前使用的旧 GUI 空槽位纹理路径。
- **patch37**（格式 37-75）：1.19.3+ 之后，马铠和装备模型改为新的 equipment 路径系统，这里提供对应的新路径纹理。
- **patch43**（格式 43-75）：1.20.3+ 中 GUI 槽位变为 sprite 系统后的对应纹理。
- **drop1_20**（格式 20-75）：1.20+ 版本中新增/修改的生物纹理（如新的狼变种）。
- **update1_21**（格式 33-75）：1.21+ 新增的方块、物品、生物等纹理。
- **drop24_3**（格式 35-75）：1.21.2+ 模型变更（如红石比较器、龙蛋模型）。
- **drop24_4**（格式 40-75）：1.21.4+ 纹理变更（Creaking 生物、新告示牌等）。
- **drop25_1**（格式 52-75）：1.21.5+ 第一次更新（新方块如 Bush、Cactus Flower 等）。
- **drop25_2**（格式 56-75）：1.21.5+ 第二次更新（酿造台模型、新生物 Ghast、Happy Ghast 等）。
- **drop25_3**（格式 56-75）：1.21.5+ 第三次更新（铜傀儡、铜箱子、新装备渲染系统等）。
- **drop25_4**（格式 71-75）：1.21.5+ 第四次更新（树叶方块闪烁亮度、骷髅变体、马装备、Nautilus Saddle 等）。

## 资源内容结构

### 方块纹理（textures/block/，207 个）

覆盖了从树叶、木板、栅栏门到铜块、凝灰岩等几乎所有新老方块。采用了 Programmer Art 风格，即与原版默认纹理一致的像素风格，但针对新版方块（如竹板、樱花木、铜块等）进行了风格兼容的补充绘制。

### 物品纹理（textures/item/，162 个）

包括全部工具、武器、盔甲、食物、附魔书、刷怪蛋等物品，以及新版 1.21+ 物品（如重锤、旋风棒、试炼钥匙等）的 Programmer Art 风格化。

### 实体纹理（textures/entity/，63 个）

修复了多个实体的纹理路径适应性问题：
- **村民/僵尸村民**：所有职业和生物群系变体
- **狼**：多个生物群系变种（ashen、black、chestnut、rusty、snowy、spotted、striped、woods）
- **猪灵**：基础纹理
- **铁傀儡**：开裂纹理
- **牛、鱿鱼、炽足兽**：基础纹理
- **船/运输船**：所有木材种类
- **告示牌**：普通和悬挂式，所有木材种类
- **玩家**：slim（纤细）和 wide（宽大）模型

### GUI 纹理（textures/gui/，29 个）

- **container/**：容器背景（如箱子、合成台等）
- **hanging_signs/**：悬挂式告示牌 GUI
- **sprites/**：采用 1.20.3+ 的 GUI sprite 系统格式，包括：
  - **widget/**：按钮、滑块、文本框等控件
  - **icon/**：图标
  - **recipe_book/**：合成配方书
  - **social_interactions/**：社交互动面板
  - **spectator/**：旁观模式菜单
  - **toast/**：通知弹窗

### OptiFine CTM 玻璃

`optifine/ctm/tinted_glass/` 目录包含 47 个纹理切片，利用 OptiFine 的连接纹理系统使着色玻璃在相邻放置时无缝连接，消除标准纹理的边框分割感。这是一种纯粹的 OptiFine 特性支持，不依赖原版机制。

### 模型（models/block/cocoa_stage2.json）

唯一一个需要模型修正的方块（可可豆第二阶段）。在旧版中可可豆的模型在不同版本间发生了 UV 映射变化，此修正确保在旧纹理下渲染正确。

## 技术特点

1. **复杂的 overlays 系统**：使用 12 个覆盖层来针对不同 Minecraft 版本提供不同纹理路径。每个覆盖层都包含特定版本范围内需要的纹理变体，覆盖层的格式范围经过精心设计，有重叠也有排斥，确保在不同版本中都能正确加载。

2. **路径迁移兼容**：针对 Mojang 在多个版本中变更的资源路径（如实体装备从 `models/armor/` 迁移到 `entity/equipment/`、GUI 槽位从 `item/` 迁移到 `gui/sprites/container/slot/`），提供了双向兼容。

3. **历史纹理归档**：`deprecated37` 和 `deprecated43` 不是修复，而是提供旧路径版本所需的纹理，确保使用旧版本加载资源包时能正确显示。这种"覆盖而非覆盖"的策略最大化了兼容性。

4. **持续追踪版本更新**：从 `drop1_20` 到 `drop25_4`，每个覆盖层对应一次 Minecraft 版本更新或快照中的资源变更，说明作者一直在追踪上游变更并及时更新。

5. **新旧风格融合**：所有新版本添加的方块/物品/实体纹理都采用与 Programmer Art 一致的像素风格，风格统一，没有视觉撕裂感。

## 结论

ProgrammerArtFix 26.0 是一个高度专业化、系统化的兼容性资源包。它不改变游戏的美术风格，而是确保旧版 Programmer Art 风格在新版本 Minecraft 中保持完整和可用。其最突出的技术成就是实现了复杂的 overlays 系统架构——12 个覆盖层按版本范围精细切割，覆盖从 1.20 到 1.21.5+ 之间所有主要版本的资源路径和格式变更。

包体量庞大（800+ 纹理），覆盖面极广，从方块、物品、生物、GUI 到粒子、状态效果、地图装饰等无所不包。对于希望在新版本中使用经典旧版纹理的玩家来说，这是一个必不可少的修复包。同时，对 OptiFine CTM 的支持（着色玻璃）也体现了对主流优化 Mod 的兼容意识。
