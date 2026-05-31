# 28. New Glowing Ores [Border]

## 根目录结构

```
NewGlowingOres-§6[Border]§r/
├── assets/
│   ├── create/
│   │   ├── optifine/ctm/ores/
│   │   │   ├── deepslate_zinc_ore/  [connect.properties + 10 PNG]
│   │   │   └── zinc_ore/           [connect.properties + 10 PNG]
│   │   └── textures/block/
│   │       └── [锌矿纹理]
│   ├── mekanism/
│   │   ├── optifine/ctm/ores/
│   │   │   ├── deepslate_fluorite_ore/
│   │   │   ├── deepslate_lead_ore/
│   │   │   ├── deepslate_osmium_ore/
│   │   │   ├── deepslate_tin_ore/
│   │   │   ├── deepslate_uranium_ore/
│   │   │   ├── fluorite_ore/
│   │   │   ├── lead_ore/
│   │   │   ├── osmium_ore/
│   │   │   ├── tin_ore/
│   │   │   └── uranium_ore/
│   │   └── textures/block/
│   │       └── [矿石纹理]
│   ├── minecraft/
│   │   ├── optifine/ctm/ores/
│   │   │   ├── coal_ore/            [connect.properties + 10 PNG]
│   │   │   ├── copper_ore/          [connect.properties + 10 PNG]
│   │   │   ├── deepslate_coal_ore/  [connect.properties + 10 PNG]
│   │   │   ├── deepslate_copper_ore/
│   │   │   ├── deepslate_diamond_ore/
│   │   │   ├── deepslate_emerald_ore/
│   │   │   ├── deepslate_gold_ore/
│   │   │   ├── deepslate_iron_ore/
│   │   │   ├── deepslate_lapis_ore/
│   │   │   ├── deepslate_redstone_ore/
│   │   │   ├── diamond_ore/
│   │   │   ├── emerald_ore/
│   │   │   ├── gold_ore/
│   │   │   ├── iron_ore/
│   │   │   ├── lapis_ore/
│   │   │   ├── nether_gold_ore/
│   │   │   ├── nether_quartz_ore/
│   │   │   └── redstone_ore/
│   │   └── textures/block/
│   │       ├── [所有原版矿石基础纹理] (*.png)
│   │       └── [所有原版矿石发光纹理] (*_e.png)
│   └── werewolves/
│       ├── optifine/ctm/ores/
│       │   ├── deepslate_silver_ore/
│       │   └── silver_ore/
│       └── textures/block/
│           └── [银矿纹理]
├── pack.mcmeta
└── pack.png
```

## 包定位

作者：GridExpert。版本 v2.0，目标 Minecraft 1.21+。本包是一个专注于**矿石发光美化**的资源包，核心功能是让所有矿石在黑暗中具有发光效果（类似 OptiFine 的发光纹理特性），同时也可以选择性地添加矿石粒子发光效果。

包名中的 `[Border]` 表示此版本添加了矿石的"边框"发光效果——矿石纹理的矿簇部分周围有光晕边框，增强了视觉辨识度。

本包覆盖范围极全：包括原版 Minecraft 全部 18 种矿石变体（9 种主世界矿石 x 普通/深板岩两种变体 + 2 种下界矿石），以及三个流行 Mod 的矿石：Create（锌矿）、Mekanism（氟石、铅、锇、锡、铀）、Werewolves（银矿），总计约 32 种矿石的发光纹理。

## 关键文件说明

### pack.mcmeta

```json
{
  "pack": {
    "pack_format": 34,
    "supported_formats": { "min_inclusive": 8, "max_inclusive": 69 },
    "description": "v2.0-1.21+ | by GridExpert"
  }
}
```

- pack_format 34（对应 1.21.5），但 supported_formats 下限为 8（1.16.2），上限 69。说明作者希望尽可能向下兼容。
- 这是典型的"格式保守"策略——虽然基于新版本制作，但通过声明较宽的支持范围允许在旧版本中加载。

### OptiFine CTM 结构

每个矿石类型目录包含以下结构：

```
diamond_ore/
├── connect.properties  # CTM 连接属性配置
├── 0.png               # 无连接的单个矿石纹理
├── 1.png - 4.png       # CTM 连接纹理（常规光照）
├── 0_e.png             # 无连接发光纹理
└── 1_e.png - 4_e.png   # CTM 连接发光纹理
```

**connect.properties**:
```properties
matchTiles=diamond_ore
method=ctm_compact
innerSeams=true
tiles=0-4
```

- `matchTiles=diamond_ore`：匹配原版钻石矿石纹理，当相邻方块也使用 diamond_ore 纹理时触发连接。
- `method=ctm_compact`：使用紧凑型 CTM 算法，需要 5 个纹理切片（0-4），比标准 CTM（47 切片）节省大量纹理空间。
- `innerSeams=true`：内部接缝开启，使连接后的纹理在方块交界处有细小分割线，避免完全无缝导致的视觉模糊。
- `tiles=0-4`：定义使用的纹理范围。

### 纹理系统

每个矿石类型有两套纹理：

1. **基础纹理**（如 `diamond_ore.png`）：用于正常光照环境下的矿石外观，采用 OptiFine CTM 连接纹理系统。
2. **发光纹理**（如 `diamond_ore_e.png`）：OptiFine 的 emissive 纹理，后缀 `_e` 表示 emissive layer。游戏加载时将此纹理作为自发光叠加层，使矿石在黑暗中发光。

这种 `_e` 后缀是 OptiFine 的约定规范（在 properties 中也可以显式配置）。

### Mod 支持

包包含了三个主流 Mod 的矿石支持：

- **Create（机械动力）**：锌矿及其深板岩变体
- **Mekanism（通用机械）**：氟石、铅、锇、锡、铀矿及其深板岩变体（共 10 种）
- **Werewolves（狼人）**：银矿及其深板岩变体（共 2 种）

每种 Mod 矿石都遵循与原版矿石相同的 CTM + emissive 纹理体系。

### 原版矿物覆盖

包覆盖了原版游戏中所有矿石类型：

| 矿石 | 普通 | 深板岩 | 下界 |
|------|------|--------|------|
| 煤矿 | v | v | - |
| 铜矿 | v | v | - |
| 钻石矿 | v | v | - |
| 绿宝石矿 | v | v | - |
| 金矿 | v | v | v (下界金矿) |
| 铁矿 | v | v | - |
| 青金石矿 | v | v | - |
| 红石矿 | v | v | - |
| 下界石英矿 | - | - | v |

## 技术特点

1. **OptiFine CTM + Emissive 双机制**：核心依赖于 OptiFine 的两个扩展特性——CTM（连接纹理）使相邻矿石方块呈现连续矿脉的视觉效果；Emissive 纹理使矿石在暗处发光。两者结合是本包全部功能的基础。

2. **紧凑型 CTM（ctm_compact）**：使用 5 切片紧凑 CTM 模式而非 47 切片标准 CTM，大幅减少了纹理数量和包体量。这也是为什么每个矿石目录只有 10 个 PNG（5 基础 + 5 发光）而不是 94 个。

3. **多 Mod 命名空间**：为三个 Mod 提供独立的 assets 命名空间（create、mekanism、werewolves），每个命名空间下的纹理路径符合 Mod 的资源约定。

4. **发光边框设计**：`[Border]` 版本的特征是矿石纹理周围带有发光边框（光晕效果），区别于无边框版本。这种效果通过精细设计 emissive 纹理的像素来实现——矿石中的宝石/金属部分被绘制成自发光像素，周围有柔和的光晕过渡。

5. **纯客户端优化**：所有发光效果都是视觉层面的，不改变矿石的实际光照行为或生成逻辑，完全依赖于 OptiFine 的客户端渲染。

6. **无原版模型/blockstate 修改**：包只包含 textures 和 optifine 配置，没有修改原版的 models、blockstates 或 items。这意味着它完全作为 OptiFine 的资源层工作，对其他 Mod 的兼容性极好。

## 结论

New Glowing Ores [Border] v2.0 是一个专注于矿石视觉增强的专项资源包，通过 OptiFine 的 CTM 连接纹理和 Emissive 发光纹理双机制，为原版及三个主流 Mod 的矿石提供了高质量的发光视觉效果。包采用了紧凑型 CTM（ctm_compact）方案节省纹理资源，同时增加了发光边框以增强辨识度。

技术上，本包完全依赖于 OptiFine 客户端特性，不修改原版资源路径，因此与其他资源包兼容性好。不足之处在于需要 OptiFine 或其分支（如 CIT Resewn、Custom Entity Models）才能正常工作。对于使用 OptiFine 且有矿石发光需求的玩家来说，这是一个功能完善、覆盖全面（原版 18 种 + 3 Mod 共 32 种矿石）的优秀选择。
