# 35. Icon Xaero's 1.22

## 根目录结构

```
Icon Xaero's 1.22/
├── assets/
│   └── xaerominimap/
│       └── entity/
│           └── icon/
│               └── definition/
│                   ├── ad_astra/          # 模组：Ad Astra（太空模组）
│                   ├── adventurez/        # 模组：AdventureZ
│                   ├── aether/            # 模组：The Aether（天境）
│                   ├── alexscaves/        # 模组：Alex's Caves（Alex的洞穴）
│                   ├── alexsmobs/         # 模组：Alex's Mobs（Alex的生物）
│                   ├── allay/             # 模组：Allay（悦灵相关）
│                   ├── ambientadditions/  # 模组：Ambient Additions
│                   ├── aquaculture/       # 模组：Aquaculture（水产养殖）
│                   ├── aquamirae/         # 模组：Aquamirae（海灵物语）
│                   ├── aqupd/             # 模组：Aqupd
│                   ├── ars_elemental/     # 模组：Ars Elemental
│                   ├── ars_nouveau/       # 模组：Ars Nouveau（新生魔艺）
│                   ├── artifacts/         # 模组：Artifacts（神器）
│                   ├── betteranimalsplus/ # 模组：Better Animals Plus
│                   ├── betterend/         # 模组：Better End（更好的末地）
│                   ├── betternether/      # 模组：Better Nether（更好的下界）
│                   ├── bewitchment/       # 模组：Bewitchment（巫术）
│                   ├── biomemakeover/     # 模组：Biome Makeover
│                   ├── biomeswevegone/    # 模组：Biomes We've Gone
│                   ├── blue_skies/        # 模组：Blue Skies
│                   ├── born_in_chaos_v1/  # 模组：Born in Chaos
│                   ├── bosses_of_mass_destruction/ # 模组：Bosses of Mass Destruction
│                   ├── byg/              # 模组：Oh The Biomes You'll Go
│                   ├── capybara/          # 模组：Capybara
│                   ├── capybaramod/       # 模组：Capybara Mod
│                   ├── cataclysm/         # 模组：Cataclysm（灾变）
│                   ├── cave_dweller/      # 模组：Cave Dweller
│                   ├── cftlc/            # 模组：Cftlc
│                   ├── cobblemon/         # 模组：Cobblemon（宝可梦）
│                   ├── coppergolem/       # 模组：Copper Golem
│                   ├── crabbersdelight/   # 模组：Crabber's Delight
│                   ├── creatures_from_the_snow/  # 雪中生物
│                   ├── creatures_of_the_jungle/  # 丛林生物
│                   ├── creeperoverhaul/   # 模组：Creeper Overhaul
│                   ├── darkwaters/        # 模组：Dark Waters
│                   ├── dawnera/           # 模组：Dawn Era
│                   ├── deeperdarker/      # 模组：Deeper and Darker
│                   ├── divinerpg/         # 模组：DivineRPG
│                   ├── duckling/          # 模组：Duckling
│                   ├── earth/             # 模组：Minecraft Earth
│                   ├── earthmobsmod/      # 模组：Earth Mobs Mod
│                   ├── earthtojavamobs/   # 模组：Earth to Java Mobs
│                   ├── ecologics/         # 模组：Ecologics
│                   ├── endermanoverhaul/  # 模组：Enderman Overhaul
│                   ├── enemyexpansion/    # 模组：Enemy Expansion
│                   ├── epicsamurai/       # 模组：Epic Samurai
│                   ├── evilcraft/         # 模组：EvilCraft
│                   ├── exoticbirds/       # 模组：Exotic Birds
│                   ├── feywild/           # 模组：Feywild
│                   ├── fishofthieves/     # 模组：Fish of Thieves
│                   ├── forbidden_arcanus/ # 模组：Forbidden and Arcanus
│                   ├── friendsandfoes/    # 模组：Friends and Foes
│                   ├── frostiful/         # 模组：Frostiful
│                   ├── galosphere/        # 模组：Galosphere
│                   ├── glare/             # 模组：Glare
│                   ├── gnumus/            # 模组：Gnumus
│                   ├── goblinsanddungeons/ # 模组：Goblins and Dungeons
│                   ├── goodall/           # 模组：Good All
│                   ├── goodending/        # 模组：Good Ending
│                   ├── gothic/            # 模组：Gothic
│                   ├── graveyard/         # 模组：Graveyard
│                   ├── hamsters/          # 模组：Hamsters
│                   ├── hedgehog/          # 模组：Hedgehog
│                   ├── hem/              # 模组：Hem
│                   ├── hybrid-aquatic/    # 模组：Hybrid Aquatic
│                   ├── iceandfire/        # 模组：Ice and Fire（冰与火）
│                   ├── infernalexp/       # 模组：Infernal Expansion
│                   ├── irons_spellbooks/  # 模组：Iron's Spells 'n Spellbooks
│                   ├── knightquest/       # 模组：Knight Quest
│                   ├── kobolds/           # 模组：Kobolds
│                   ├── llamarama/         # 模组：Llama Rama
│                   ├── lovely_snails/     # 模组：Lovely Snails
│                   ├── magehand/          # 模组：Mage Hand
│                   ├── magma_monsters/    # 模组：Magma Monsters
│                   └── ... （共约180+个模组）
├── pack.mcmeta
└── pack.png
```

*注：本包共含811个目录和大量JSON文件，覆盖约180多个模组的实体图标定义。*

## 包定位

Icon Xaero's 是一个为 **Xaero的小地图 (Xaero's Minimap)** 和 **Xaero的世界地图 (Xaero's WorldMap)** 模组提供实体图标支持的资源包。由 godkyo98（又名 Kyo98）制作，版本 1.22。

Xaero的小地图/世界地图是Minecraft最受欢迎的地图模组之一，它可以在屏幕上显示小地图，并在小地图或世界地图上标记各种实体（生物、怪物、动物等）的位置。默认情况下，这些模组只支持原版实体的图标，而本资源包则为大量模组添加的生物提供了对应的图标定义。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "pack_format": 16,
    "min_format": 1,
    "max_format": 75,
    "supported_formats": {"min_inclusive": 1, "max_inclusive": 75},
    "description": "§6Kyo98(godkyo98) - §7Adds icons mod to Xaero's Minimap and WorldMap"
  }
}
```

pack_format 为16（Minecraft 1.21.2+），但 `supported_formats` 从1到75，覆盖了极为广泛的版本范围——从最早的版本到最新版本。这种极端的兼容性设置表明作者希望无论玩家使用哪个Minecraft版本都能正常使用。

**实体图标定义文件样例（piglin.json）：**
```json
{
  "variants": {
    "default": "outlined_sprite:minecraft/piglin/piglin.png",
    "layersAllowed": true
  }
}
```

每个JSON文件定义了一个实体的图标映射。`outlined_sprite` 表示使用带有轮廓的精灵图显示，使图标在小地图上更清晰可见。`layersAllowed: true` 允许分层渲染。

## 资源内容结构

本包的内容结构非常单一但极其庞大——全部由实体图标定义文件组成：

1. **原版Minecraft实体**：覆盖所有原版生物（苦力怕、末影人、猪灵等）
2. **大型模组实体**：为众多知名模组中的生物添加图标，覆盖范围极广

### 已支持的部分模组列表（不完全统计）：

| 模组命名空间 | 模组名称 |
|---|---|
| ad_astra | Ad Astra（太空模组） |
| alexsmobs | Alex's Mobs（Alex的生物） |
| alexscaves | Alex's Caves（Alex的洞穴） |
| ars_nouveau | Ars Nouveau（新生魔艺） |
| betterend | Better End（更好的末地） |
| betternether | Better Nether（更好的下界） |
| biomemakeover | Biome Makeover（生物群系改造） |
| cataclysm | Cataclysm（灾变） |
| cobblemon | Cobblemon（宝可梦） |
| deeperdarker | Deeper and Darker（幽邃黑暗） |
| friendsandfoes | Friends and Foes |
| iceandfire | Ice and Fire（冰与火） |
| irons_spellbooks | Iron's Spells 'n Spellbooks |
| mowziesmobs | Mowzie's Mobs |
| quark | Quark |
| sushigocrafting | Sushi Go Crafting |
| twilightforest | Twilight Forest（暮色森林） |
| twigs | Twigs |
| underground_bunkers | Underground Bunkers |
| unnatural_end | Unnatural End |
| upd2524 | Update 2.5.2.4 |
| valkyrien_skies | Valkyrien Skies |
| vampirism | Vampirism（吸血鬼） |
| various_world | Various World |
| verdantvibes | Verdant Vibes |
| vintagedelight | Vintage Delight |
| wildbackport | Wild Backport |
| withers_overhaul | Withers Overhaul |
| wondercaves | Wonder Caves |
| woodarmor | Wood Armor |
| wyrmroost | Wyrmroost |
| xerca | Xerca |
| xercamod | Xerca Mod |
| yungsapi | YUNG's API |
| yungsbetterdeserttemples | YUNG's Better Desert Temples |
| yungsbridges | YUNG's Bridges |

## 技术特点

1. **极广的模组覆盖**：本包支持约180多个模组，几乎涵盖了主流和常见的Minecraft生物模组，用户数量庞大。

2. **轮廓精灵图**：所有图标都使用 `outlined_sprite` 格式，确保在小地图的小尺寸显示下仍清晰可辨。

3. **版本兼容范围极宽**：pack_format从1到75，覆盖了几乎所有Minecraft版本。

4. **按模组命名空间组织**：每个模组的实体图标定义文件按模组命名空间分目录存放，结构清晰，便于维护和扩展。

5. **轻量化**：每个定义文件体积很小（通常只有几行JSON），但整体覆盖量巨大。

## 结论

Icon Xaero's 1.22 是一个功能明确的资源包，专门为 Xaero的小地图/世界地图 模组提供实体图标支持。它的定位非常精准——解决了一个玩家社区的特定需求：当安装了各种模组添加的生物后，小地图上无法正确显示这些生物的图标。

该包最大的价值在于其**广泛的模组兼容性**，覆盖了180+个模组。对于玩模组整合包的玩家来说，这是一个近乎必备的资源包，它能确保你在小地图上准确识别周围的生物，无论是普通的牛还是来自 Alex's Caves 的奇特生物。作者 godkyo98 维持着一个庞大的图标库，并持续更新以支持新模组，这也是该包能够长期受到欢迎的原因。
