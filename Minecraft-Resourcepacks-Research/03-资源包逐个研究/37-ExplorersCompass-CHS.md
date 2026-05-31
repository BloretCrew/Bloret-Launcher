# 37. 探险者指南针结构汉化 v3.1

## 根目录结构

```
探险者指南针结构汉化 v3.1/
├── assets/
│   └── explorerscompass/
│       └── lang/
│           └── zh_cn.json
├── pack.mcmeta
├── pack.png
└── README.md
```

## 包定位

"探险者指南针结构汉化"（Explorer's Compass 结构汉化补充包）是一个专注于为 **Explorer's Compass（探险者指南针）** 模组提供简体中文结构名称翻译的语言补充包。由 CLOTLIU 制作，版本 v3.1。

Explorer's Compass 是一个实用的Minecraft模组，它允许玩家搜索和定位游戏世界中的各种结构（如村庄、神殿、要塞等），以及模组添加的自定义结构。该模组支持通过名称搜索结构，并显示距离和坐标信息。然而，对于中文玩家而言，当安装了大量模组（尤其是结构类模组）后，许多结构名称仍然是英文显示，使用起来不够方便。

这个资源包的出现正是为了解决这一问题——它为探险者指南针模组添加了全面的简体中文结构名称翻译，特别聚焦于那些模组添加的自定义结构，让中文玩家能够更直观地识别和搜索目标结构。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "pack_format": 15,
    "description": "探险者指南针 - 结构补充汉化包\n功能：为探险者指南针模组提供更完整的中文翻译支持\n作者：CLOTLIU"
  }
}
```

pack_format 为 15（Minecraft 1.21+），描述中直接使用中文文字，明确说明了包的功能和作者信息。

**README.md:**
该包的 GitHub 项目介绍文件，提供了详细说明：
- 项目地址：https://github.com/CLOT-LIU/explorerscompass-CHS
- 项目目标是为探险者指南针模组提供全面的结构汉化支持
- 采用社区驱动模式，欢迎玩家提交新的汉化需求
- 提供了一个B站视频教程链接：https://www.bilibili.com/video/BV12EQbBWEaF/

**语言文件（zh_cn.json）：**
这是一个非常庞大的语言文件（2182行，78471 tokens），包含了极为丰富的翻译内容。其结构分为多个部分：

### 原版结构翻译（约30条）
涵盖了原版Minecraft的所有结构名称：
```json
"structure.minecraft.ancient_city": "远古城市"
"structure.minecraft.bastion_remnant": "堡垒遗迹"
"structure.minecraft.desert_pyramid": "沙漠神殿"
"structure.minecraft.trial_chambers": "试炼密室"
```

### 模组结构翻译（1500+条）
涵盖了大量模组添加的结构的翻译，每个模组作为一个独立区块，用注释分隔。部分支持的模组包括：

| 模组命名空间 | 模组名称 | 翻译结构数 |
|---|---|---|
| abridged | 桥梁 | 3 |
| alexscaves | Alex的洞穴 | 14 |
| aquamirae | 海灵物语 | 6 |
| atmospheric | 悠然一派 | 3 |
| autumnity | 秋原 | 1 |
| beautify | 美化！ | 5 |
| betterend | 更好的末地 | 8 |
| betternether | 更好的下界 | 10 |
| biomemakeover | 生物群系改造 | 4 |
| born_in_chaos_v1 | 生于混沌 | 25 |
| bosses_of_mass_destruction | 祸乱鬼魅 | 4 |
| call_of_drowner | 溺亡者之嚎 | 2 |
| call_of_yucutan | 尤卡坦的呼唤 | 2 |
| cataclysm | 灾变 | 14 |
| caupona | 分茶 | 1 |
| deeperdarker | 幽邃黑暗 | 1 |
| eeeabsmobs | EEEAB的生物 | 2 |
| endlessbiomes | 末地群系 | 2 |
| exquisito | 末域奇馔 | 1 |
| mowziesmobs | Mowzie的生物 | 4 |
| soulsweapons | Marium的魂类武器 | 4 |
| dungeons_arise | 地牢浮现之时 | 36 |
| dungeons_arise_seven_seas | 地牢浮现之时 - 海洋扩展 | 5 |
| legendary_monsters | 传奇怪物 | 13 |
| youkaishomecoming | 妖怪们的归家 | 3 |
| idas | 地牢建筑统合 | 80+ |
| betterdeserttemples等 | YUNG系列 | 24 |
| subterrestrial | Subterrestrial | 8 |
| create_structures_arise | 机械动力 | 22 |
| tetra | Tetra | 2 |
| adorabuild_structures | AdoraBuild | 100+ |
| cobblemon | Cobblemon | 30+ |

## 资源内容结构

本包的结构极简，只包含一个语言文件。但这个文件的内容极其丰富，涵盖了几乎所有主流结构类模组中的自定义结构名称翻译。

### 翻译特色

该包的翻译风格具有以下特点：

1. **规范译名**：对于有官方中文译名的模组和结构，使用公认的规范译名（如 "要塞"、"林地府邸"）

2. **模组前缀标注**：每条翻译都包含 [模组名] 前缀，方便用户识别结构来自哪个模组，例如 `[Alex的洞穴]`

3. **双语对照**：在中文翻译后保留括号英文原名，例如 `"深渊遗迹(Abyssal Ruins)"`，方便双语对照

4. **注释组织**：使用 `_comment` 注释键按模组分区块组织，便于维护和阅读

5. **特殊处理**：对于赞助者相关的结构（如 `born_in_chaos_v1` 中的墓碑），在翻译中标注了身份信息

## 技术特点

1. **纯语言包**：仅包含语言文件，不涉及任何模型、纹理或声音

2. **海量翻译量**：翻译了约2000+条结构名称，覆盖约60+个结构模组

3. **社区维护**：作为开源项目，通过GitHub Issue区收集新需求

4. **详细注释**：语言文件中包含详细的注释区块，便于后期维护和扩展

5. **与原模组互补**：此包不覆盖原模组的语言文件，仅补充原模组未翻译的部分

## 结论

"探险者指南针结构汉化 v3.1" 是一个对中文模组玩家极为实用的本地化资源包。它解决了一个很实际的问题：在安装了大量模组后，探险者指南针中列出的结构名称往往是英文的，对于不熟悉英文的中文玩家来说，使用起来很困难。

该包的作者 CLOTLIU 投入了大量精力来翻译各种模组中的结构名称，从常见的大型模组（如"灾变"、"地牢浮现之时"）到小众模组都有覆盖。翻译质量较高，既有规范译名又保留了英文原名供对照，还贴心地加上了模组前缀。

对于使用探险者指南针模组的中文玩家来说，这个资源包几乎是必装的辅助包。它极大地降低了查找特定结构时的认知负担，让探索游戏世界变得更加直观和方便。该包持续在GitHub上更新，社区参与度高，也保证了其长期可用性。
