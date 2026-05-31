# 20. Default-HD-128x

## 根目录结构

路径：`Resourcepacks/Default HD 128x Demo 1.8.2.5/`

```text
Default HD 128x Demo 1.8.2.5/
├── pack.mcmeta
├── pack.png
└── assets/
    └── minecraft/
        ├── mcpatcher/                    # MCPatcher兼容层（旧版）
        │   ├── colormap/                 # 空目录
        │   ├── ctm/glass/                # CTM玻璃连接纹理 (88 PNG + 5 properties)
        │   ├── lightmap/                 # 空目录
        │   └── mob/
        │       ├── cow/cow2.png          # 牛变种纹理
        │       └── wolf/                 # 狼变种纹理 (wolf_tame2~4.png)
        ├── optifine/                     # OptiFine兼容层（新版）
        │   ├── colormap/                 # 空目录
        │   ├── ctm/glass/                # CTM玻璃连接纹理 (88 PNG + 5 properties)
        │   ├── lightmap/                 # 空目录
        │   └── mob/
        │       ├── cow/cow2.png
        │       └── wolf/                 # wolf_tame2~4.png
        ├── texts/
        │   ├── credits.txt               # 自定义鸣谢
        │   ├── end.txt                   # 末地文字
        │   └── splashes.txt              # 自定义启动标语
        └── textures/
            ├── block/                    # 方块纹理 (1022文件)
            ├── colormap/                 # 色彩映射 (2文件)
            ├── effect/                   # 特效纹理 (1文件)
            ├── entity/                   # 实体纹理 (416文件)
            ├── environment/              # 环境纹理 (2文件)
            ├── item/                     # 物品纹理 (435文件)
            ├── map/                      # 地图纹理 (3文件)
            ├── misc/                     # 杂项纹理 (13文件)
            ├── mob_effect/               # 药水效果纹理 (32文件)
            ├── models/armor/             # 护甲模型纹理 (17文件)
            ├── painting/                 # 画作纹理 (27文件)
            └── particle/                 # 粒子纹理 (139文件)
```

## 包定位

这是一个"综合高清化"资源包，目标是将 Minecraft 原版 16x 分辨率的全部纹理提升至 128x（即原版的 8 倍），在保持原版美术风格的前提下显著提升视觉清晰度与细节表现。

与单纯的贴图替换包不同，该包还做了以下工作：

1. 覆盖几乎全部纹理类别——方块、实体、物品、粒子、护甲、药水效果、画作、环境、地图等。
2. 提供 OptiFine / MCPatcher 双重 CTM 连接纹理支持（玻璃方块 47 瓦片系统）。
3. 提供 OptiFine 生物变种纹理（牛、狼随机纹理）。
4. 包含 69 个动画纹理 mcmeta 文件，覆盖火焰、岩浆、命令方块、海带、灯笼、灵魂火焰等动态方块。
5. 自定义游戏文本（启动标语、鸣谢、末地文字）。

其目标用户是希望在不使用大量模组的情况下获得显著画质提升、同时保持原版"味道"的玩家。

## 关键文件说明

### pack.mcmeta

路径：`Resourcepacks/Default HD 128x Demo 1.8.2.5/pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 15,
    "min_format": [15, 0],
    "max_format": [1000, 0],
    "supported_formats": [15, 1000],
    "description": "Default HD 128x Demo 1.8.2.5 by thebaum64"
  }
}
```

用途：

1. `pack_format: 15` 对应 Minecraft 1.20.1。
2. `supported_formats` 范围为 15~1000，声称兼容几乎所有现代版本。
3. 描述文本标注版本号（1.8.2.5）和作者（thebaum64）。
4. 这是一个 Demo 版本，暗示完整版可能有更多内容或更高分辨率。

### pack.png

路径：`Resourcepacks/Default HD 128x Demo 1.8.2.5/pack.png`

作用：资源包图标，在游戏资源包选择界面中显示。

### 其他关键文件

**README.md**：不存在。作者信息只能从 pack.mcmeta 的 description 和 texts/splashes.txt 中提取。

**texts/splashes.txt**：自定义启动界面标语，包含作者社交信息——Discord（thebaum64#1425 / discord.gg/AdTUsPUxyA）、Patreon（patreon.com/thebaum64）、Planet Minecraft（planetminecraft.com/member/thebaum64/）。

**texts/credits.txt**：自定义鸣谢文件，替换原版 Minecraft 制作人员名单。

**texts/end.txt**：自定义末地终末之诗文本。

## 资源内容结构

该包的主要资源集中在 `assets/minecraft/textures/` 下，按 Minecraft 标准纹理目录组织：

| 资源类型 | 路径 | 文件数量 | 说明 |
|----------|------|----------|------|
| 方块纹理 | `textures/block/` | 1022 | 核心内容，覆盖全部原版方块 |
| 实体纹理 | `textures/entity/` | 416 | 生物、箱子、船、旗帜、盾牌等 |
| 物品纹理 | `textures/item/` | 435 | 工具、武器、食物、药水等 |
| 粒子纹理 | `textures/particle/` | 139 | 全部粒子效果纹理 |
| 药水效果 | `textures/mob_effect/` | 32 | 状态效果图标 |
| 画作 | `textures/painting/` | 27 | 全部原版画作 |
| 护甲模型 | `textures/models/armor/` | 17 | 各材质护甲层纹理 |
| 杂项 | `textures/misc/` | 13 | 附魔光效、传送门等 |
| 地图 | `textures/map/` | 3 | 地图相关纹理 |
| 环境 | `textures/environment/` | 2 | 天空、云等 |
| 色彩映射 | `textures/colormap/` | 2 | 生物群系色彩映射 |
| 特效 | `textures/effect/` | 1 | 特殊效果纹理 |

此外还有 OptiFine/MCPatcher 扩展目录和 texts 文本目录。

## 关键目录功能

### `assets/minecraft/textures/block/`

方块纹理目录，包含 1022 个 PNG 文件。这是该包文件数量最多的目录，覆盖了 Minecraft 中几乎所有原版方块的 128x 高清版本。其中包括：

- 基础方块（石头、泥土、草方块、木头等）
- 矿石方块（煤矿、铁矿、金矿、钻石矿等）
- 建筑方块（砖、石英、混凝土等）
- 红石方块（红石、中继器、比较器等）
- 植物（花、草、树苗、农作物等）
- 液体（水、岩浆）
- 含动画 mcmeta 的动态方块（火焰、灵魂火焰、海带、灯笼、命令方块等）

### `assets/minecraft/textures/entity/`

实体纹理目录，包含 416 个 PNG 文件。覆盖范围包括：

- 生物纹理（牛、羊、猪、鸡、苦力怕、末影人、僵尸、骷髅等）
- 生物变种（村民职业/等级、猫品种、马铠、狼项圈等）
- 建筑实体（箱子、陷阱箱、末影箱、信标、旗帜等）
- 交通工具（各类船）
- 其他（盔甲架、传送门、信标光束等）

### `assets/minecraft/textures/item/`

物品纹理目录，包含 435 个 PNG 文件。覆盖全部原版物品的高清纹理，包括工具、武器、盔甲、食物、药水、附魔书、唱片等。

### `assets/minecraft/textures/particle/`

粒子纹理目录，包含 139 个 PNG 文件。将原版粒子效果全部替换为 128x 高清版本，使火焰、烟雾、爆炸、治疗等视觉效果更加精细。

### `assets/minecraft/textures/models/armor/`

护甲模型纹理目录，包含 17 个文件。覆盖全部护甲材质（锁链、钻石、金、铁、皮革、下界合金、猪灵皮革、海龟）的 layer1/layer2 及 overlay 纹理。

### `assets/minecraft/textures/mob_effect/`

药水效果纹理目录，包含 32 个 PNG 文件。替换原版状态效果图标为高清版本。

### `assets/minecraft/textures/painting/`

画作纹理目录，包含 27 个 PNG 文件。将原版画作全部替换为高清版本。

### `assets/minecraft/optifine/ctm/glass/`

OptiFine CTM 连接纹理目录。包含 88 个 PNG 子纹理瓦片和 5 个 properties 配置文件，实现玻璃方块的无缝连接效果。使用 47 个子纹理瓦片（编号 0-11, 16-27, 32-43, 48-59），采用 `method=ctm` 连接方式。

### `assets/minecraft/optifine/mob/`

OptiFine 生物变种纹理目录。包含：

- `cow/cow2.png`：牛的第二纹理变种
- `wolf/wolf_tame2.png`、`wolf_tame3.png`、`wolf_tame4.png`：狼的驯服状态变种纹理

这些文件使同一生物在世界中呈现不同的外观，增加视觉多样性。

### `assets/minecraft/mcpatcher/`

MCPatcher 兼容层目录。内容与 `optifine/` 目录完全镜像（CTM 玻璃纹理、牛/狼变种纹理），确保使用旧版 MCPatcher 的玩家也能获得相同效果。

### `assets/minecraft/texts/`

自定义文本目录，包含 3 个文件：

- `splashes.txt`：启动界面标语，包含作者社交信息
- `credits.txt`：自定义鸣谢
- `end.txt`：自定义末地终末之诗

## 技术特点

### 1. 双重 CTM 兼容

该包同时提供 `optifine/ctm/` 和 `mcpatcher/ctm/` 两套完全镜像的连接纹理文件。这是一种兼容性策略：

- OptiFine 用户读取 `optifine/` 目录
- MCPatcher 用户读取 `mcpatcher/` 目录
- 两者内容完全一致，确保不同模组加载器下表现相同

### 2. 47 瓦片 CTM 系统

玻璃方块使用了标准的 47 瓦片 CTM 系统，子纹理编号范围为 0-11, 16-27, 32-43, 48-59。这种编号方式对应 CTM 系统中 4x4 瓦片网格的特定位置，通过 `method=ctm` 属性让相邻的玻璃方块无缝连接，消除原版玻璃之间的黑色边框。

### 3. 动画纹理系统

包含 69 个 `.mcmeta` 动画配置文件，覆盖以下动态方块/效果：

- 火焰与灵魂火焰
- 岩浆
- 命令方块
- 海带
- 灯笼
- 其他需要动态效果的方块/纹理

这些 mcmeta 文件定义了纹理动画的帧序列和速度，使高清纹理也能呈现流畅的动态效果。

### 4. 生物变种纹理

通过 OptiFine 的 `mob/` 目录机制，为牛和狼提供了额外的纹理变种。游戏会在生成这些生物时随机选择纹理，增加世界的视觉多样性。这是一种轻量级的随机化方案，不需要修改模型或代码。

### 5. 无高级技术依赖

该包未使用以下高级技术：

- 无自定义模型（.jem/.jpm）——纯纹理替换
- 无着色器（.vsh/.fsh/.glsl）
- 无自定义粒子定义
- 无语言文件覆盖
- 无声音替换
- 无 overlay 覆盖层

这意味着该包在不安装任何辅助模组的情况下也能正常工作（CTM 和生物变种除外，它们需要 OptiFine 或 MCPatcher）。

## 与其他包的关系

1. **OptiFine**：CTM 连接纹理和生物变种纹理需要 OptiFine 支持。如果未安装 OptiFine，这些功能将不生效，但基础纹理替换仍然正常工作。
2. **MCPatcher**：通过 `mcpatcher/` 目录提供兼容支持，但 MCPatcher 已是较旧的工具，现代玩家通常使用 OptiFine。
3. **Demo 版限制**：这是一个 Demo 版本（文件名中标注 "Demo"），完整版可能包含更高分辨率（如 256x）或更多内容。
4. **作者 thebaum64**：在 Planet Minecraft 和 Patreon 上发布资源包，Discord 社区为 discord.gg/AdTUsPUxyA。

## 结论

`Default HD 128x Demo 1.8.2.5` 是一个典型的"综合高清化"资源包，其核心价值在于：

1. **全面覆盖**：2320 个文件覆盖了 Minecraft 几乎全部纹理类别，是研究"全量纹理替换"策略的优秀样本。
2. **兼容性设计**：同时提供 OptiFine 和 MCPatcher 两套 CTM 文件的做法值得借鉴，体现了对不同用户环境的考虑。
3. **128x 分辨率基准**：作为 16x 原版的 8 倍，128x 是一个在清晰度与性能之间取得平衡的常见选择，适合作为高清纹理包的标准参考。
4. **纯纹理方案**：未使用自定义模型或着色器，说明"仅靠纹理替换"就能实现显著的视觉提升。
5. **Demo 局限**：作为 Demo 版本，许可证未明确声明，商业使用需谨慎。

对于资源包开发者而言，该包展示了如何系统化地组织大规模纹理替换项目——按 Minecraft 标准目录分类、提供 CTM 兼容层、使用 mcmeta 动画文件——这些组织方式可以直接参考。
