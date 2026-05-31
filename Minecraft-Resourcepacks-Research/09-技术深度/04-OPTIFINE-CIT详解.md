# OptiFine CIT 自定义物品纹理详解

## 1. CIT 概述

### 1.1 什么是 CIT

CIT（Custom Item Textures）是 OptiFine 提供的一项高级纹理替换功能，允许资源包开发者根据物品的特定属性（如耐久度、附魔类型、物品名称等）动态替换物品的纹理和模型。这项功能极大地扩展了 Minecraft 物品视觉表现的可能性，使得同一个物品可以根据不同条件显示不同的外观。

CIT 的核心价值在于：

- **条件化纹理替换**：根据物品的实际状态选择合适的纹理
- **动态视觉反馈**：让玩家能够通过外观直观了解物品属性
- **模型自定义**：不仅限于纹理，还可以替换整个物品模型
- **优先级控制**：通过权重系统管理多个匹配规则的优先顺序

### 1.2 CIT 与原版纹理系统的关系

在原版 Minecraft 中，物品的纹理由模型文件中的 `textures` 字段静态指定。一个物品 ID 对应一个固定的纹理（或通过模型变体系统进行有限的选择）。CIT 系统在此基础上增加了运行时的条件判断层，使得纹理选择可以基于物品的 NBT 数据动态进行。

```
原版系统：物品ID → 模型 → 纹理（静态映射）
CIT系统：物品ID + NBT属性 → 条件匹配 → 动态选择模型/纹理
```

### 1.3 兼容性说明

CIT 功能仅在安装了 OptiFine 的客户端上生效。使用原版客户端或 Sodium/Iris 等其他优化模组时，CIT 纹理不会被加载，物品将显示默认纹理。因此，CIT 应被视为增强体验的可选功能，而非必需的资源包组件。

支持的 Minecraft 版本取决于 OptiFine 版本。截至 OptiFine 1.20.x 系列，CIT 功能保持了良好的向后兼容性，但部分新特性的可用性需要查阅对应版本的 OptiFine 文档。

---

## 2. 目录结构

### 2.1 基本路径

CIT 资源文件必须放置在以下目录中：

```
assets/
└── minecraft/
    └── optifine/
        └── cit/
            ├── item1.properties
            ├── item1.png
            ├── item2.properties
            ├── item2.png
            ├── item2_model.json
            └── subfolder/
                ├── item3.properties
                └── item3.png
```

### 2.2 文件组织规范

CIT 目录下的文件组织遵循以下规则：

- **.properties 文件**：定义替换条件和目标，每个替换规则对应一个 .properties 文件
- **纹理文件**：.png 格式的纹理文件，通常与 .properties 文件放在同一目录
- **模型文件**：.json 格式的自定义模型文件，当需要替换物品模型时使用
- **子目录支持**：可以在 cit/ 下创建子目录来组织大量规则，OptiFine 会递归扫描所有子目录

### 2.3 命名建议

虽然 .properties 文件的命名不影响功能，但建议采用有意义的命名方案：

```
cit/
├── sword_diamond_enchanted.properties     # 钻石剑附魔纹理
├── sword_diamond_enchanted.png
├── sword_netherite_enchanted.properties   # 下届合金剑附魔纹理
├── sword_netherite_enchanted.png
├── bow_pulling_0.properties               # 弓拉伸阶段0
├── bow_pulling_0.png
├── bow_pulling_1.properties               # 弓拉伸阶段1
├── bow_pulling_1.png
└── armor/
    ├── diamond_helmet_custom.properties    # 自定义钻石头盔
    └── diamond_helmet_custom.png
```

---

## 3. .properties 文件格式

### 3.1 基础语法

.properties 文件使用标准的 Java 属性文件格式：

```properties
# 这是注释
items=minecraft:diamond_sword
texture=minecraft:item/diamond_sword_custom
```

每行定义一个键值对，格式为 `key=value`。键名不区分大小写（但建议使用小写）。空行和以 `#` 开头的注释行会被忽略。

### 3.2 核心属性详解

#### items

指定此规则适用于哪些物品。可以使用逗号分隔的物品 ID 列表。

```properties
# 单个物品
items=minecraft:diamond_sword

# 多个物品
items=minecraft:diamond_sword,minecraft:diamond_axe,minecraft:diamond_pickaxe

# 使用通配符匹配整个模组的物品
items=minecraft:*_sword

# 支持模组物品
items=modid:item_name
```

**特殊值说明**：
- `items=*` 匹配所有物品（极少使用，可能造成性能问题）
- 支持命名空间前缀，默认为 `minecraft:`
- 支持使用逗号分隔的列表

#### texture

指定替换纹理的路径。路径相对于 `assets/minecraft/textures/` 目录。

```properties
# 指定完整路径
texture=minecraft:item/custom_sword

# 省略命名空间时默认为 minecraft:
texture=item/custom_sword

# 使用子目录
texture=item/tools/swords/custom_diamond_sword
```

**注意事项**：
- 不需要包含 `.png` 扩展名
- 纹理文件需要放在对应的 textures 目录下，或者与 .properties 文件同目录
- 如果纹理文件与 .properties 文件同目录，直接使用文件名即可

#### model

指定替换模型的路径。用于完全替换物品的 3D 模型。

```properties
# 指定自定义模型
model=item/custom_sword_model

# 使用同目录下的模型文件
model=custom_sword.json
```

模型文件应为标准的 Minecraft 模型 JSON 格式，定义在 `assets/minecraft/models/` 目录下或与 .properties 文件同目录。

#### damage

根据物品的耐久度匹配。可以指定具体的耐久值或范围。

```properties
# 匹配特定耐久值
damage=100

# 匹配耐久度范围（百分比形式，0-1之间的小数）
damage=0.75-1.0

# 匹配耐久度范围（绝对值形式）
damage=500-1000

# 匹配未损坏的物品
damage=0
```

**格式说明**：
- 单个数值：精确匹配该耐久值
- `min-max`：匹配范围内的耐久度
- 值为 0-1 之间的浮点数时解释为百分比
- 值大于 1 时解释为绝对耐久值

#### stackSize

根据物品堆叠数量匹配。

```properties
# 匹配特定堆叠数量
stackSize=1

# 匹配堆叠数量范围
stackSize=1-16

# 匹配满堆叠
stackSize=64
```

#### enchantment

根据物品的附魔匹配。这是 CIT 中最常用的条件之一。

```properties
# 匹配任意附魔
enchantment=*

# 匹配特定附魔
enchantment=minecraft:sharpness

# 匹配多个附魔（任一匹配即可）
enchantment=minecraft:sharpness,minecraft:smite,minecraft:bane_of_arthropods

# 要求同时具有多个附魔
enchantment=minecraft:sharpness
enchantment=minecraft:fire_aspect
```

**注意**：多个 `enchantment` 行表示 AND 关系（必须同时满足），逗号分隔的列表表示 OR 关系（满足其一即可）。

#### enchantment.level

匹配附魔的等级。需要与 `enchantment` 配合使用。

```properties
# 匹配特定附魔等级
enchantment=minecraft:sharpness
enchantment.level=5

# 匹配附魔等级范围
enchantment=minecraft:sharpness
enchantment.level=3-5

# 匹配最高等级
enchantment=minecraft:sharpness
enchantment.level=5
```

#### enchantment.level

指定附魔等级的匹配条件。

```properties
enchantment=minecraft:sharpness
enchantment.level=1
```

#### enchantment.id

在使用通配符附魔时，指定附魔 ID 的匹配。

```properties
# 匹配所有附魔
enchantment=*

# 但只关注特定ID范围（某些版本支持）
enchantment.id=minecraft:sharpness
```

#### weight

指定规则的优先级权重。当多个规则同时匹配时，权重较高的规则优先应用。

```properties
# 默认权重为0
weight=0

# 高优先级规则
weight=10

# 最高优先级
weight=100
```

**权重系统说明**：
- 默认权重为 0
- 权重值越大，优先级越高
- 权重相同时，按文件名字母顺序决定
- 建议使用 0-100 的范围，留出调整空间

#### hand

指定物品在手中的显示方式。

```properties
# 在主手中显示
hand=main

# 在副手中显示
hand=off

# 在任何手中显示（默认）
hand=both
```

#### armor

用于盔甲纹理替换。指定盔甲的穿戴位置。

```properties
# 头盔
armor=head

# 胸甲
armor=chest

# 护腿
armor=legs

# 靴子
armor=feet
```

#### elytra

用于鞘翅纹理替换。当值为 `true` 时，此规则专门应用于鞘翅物品。

```properties
# 匹配鞘翅
items=minecraft:elytra
elytra=true
texture=item/custom_elytra
```

#### trim_material

匹配盔甲纹饰的材质（1.19.4+）。

```properties
# 匹配特定纹饰材质
trim_material=minecraft:netherite

# 匹配多个纹饰材质
trim_material=minecraft:diamond,minecraft:netherite,minecraft:emerald
```

#### trim_pattern

匹配盔甲纹饰的图案（1.19.4+）。

```properties
# 匹配特定纹饰图案
trim_pattern=minecraft:sentry

# 匹配多个纹饰图案
trim_pattern=minecraft:sentry,minecraft:vex,minecraft:wild
```

---

## 4. 物品纹理替换

### 4.1 基础物品纹理替换

最基本的 CIT 应用是替换物品的纹理。以下是一个完整的示例：

**文件结构**：
```
assets/minecraft/optifine/cit/
├── diamond_sword_fire.properties
└── diamond_sword_fire.png
```

**diamond_sword_fire.properties**：
```properties
items=minecraft:diamond_sword
texture=item/diamond_sword_fire
enchantment=minecraft:fire_aspect
enchantment.level=2
weight=10
```

这个配置的含义：
- 适用于 `minecraft:diamond_sword`
- 当物品附有 `fire_aspect` 等级 2 的附魔时
- 将纹理替换为 `diamond_sword_fire.png`
- 权重为 10（确保在多规则冲突时优先）

### 4.2 多状态物品纹理

许多物品有多个状态（如弓的拉伸阶段、药水的效果等）。CIT 可以为每个状态定义不同的纹理。

**弓的拉伸纹理示例**：

```properties
# bow_pulling_0.properties
items=minecraft:bow
texture=item/bow_pulling_0
damage=0-0.33

# bow_pulling_1.properties
items=minecraft:bow
texture=item/bow_pulling_1
damage=0.34-0.66

# bow_pulling_2.properties
items=minecraft:bow
texture=item/bow_pulling_2
damage=0.67-1.0
```

### 4.3 基于堆叠数量的纹理

某些游戏机制使用堆叠数量来表示状态（如经验瓶的数量表示等级）：

```properties
# 经验瓶根据数量显示不同纹理
items=minecraft:experience_bottle
texture=item/experience_bottle_full
stackSize=64

items=minecraft:experience_bottle
texture=item/experience_bottle_half
stackSize=32-63

items=minecraft:experience_bottle
texture=item/experience_bottle_low
stackSize=1-31
```

### 4.4 药水纹理替换

药水是 CIT 最常见的应用场景之一，因为不同的药水效果需要不同的视觉表现：

```properties
# 力量药水自定义纹理
items=minecraft:potion
texture=item/potion_strength_custom
enchantment=minecraft:strength
weight=5

# 治疗药水自定义纹理
items=minecraft:potion
texture=item/potion_healing_custom
enchantment=minecraft:healing
weight=5
```

**注意**：药水的附魔字段实际上匹配的是药水效果类型，而非传统意义上的附魔。

---

## 5. 盔甲纹理替换

### 5.1 基本盔甲纹理替换

CIT 允许为盔甲定义自定义纹理，当玩家穿戴时显示替换后的外观。

**文件结构**：
```
assets/minecraft/optifine/cit/
├── diamond_helmet_nether.properties
├── diamond_helmet_nether.png
├── diamond_chestplate_nether.properties
├── diamond_chestplate_nether.png
├── diamond_leggings_nether.properties
├── diamond_leggings_nether.png
├── diamond_boots_nether.properties
└── diamond_boots_nether.png
```

**diamond_helmet_nether.properties**：
```properties
items=minecraft:diamond_helmet
texture=armor/diamond_helmet_nether
armor=head
enchantment=minecraft:protection
enchantment.level=4
weight=20
```

### 5.2 盔甲纹饰系统（1.19.4+）

从 1.19.4 版本开始，Minecraft 引入了盔甲纹饰系统。CIT 可以根据纹饰材质和图案进行纹理替换：

```properties
# 钻石盔甲 + 下界合金纹饰材质
items=minecraft:diamond_helmet
texture=armor/diamond_helmet_netherite_trim
armor=head
trim_material=minecraft:netherite
weight=15

# 钻石盔甲 + 哨兵纹饰图案
items=minecraft:diamond_helmet
texture=armor/diamond_helmet_sentry_trim
armor=head
trim_pattern=minecraft:sentry
weight=15
```

### 5.3 鞘翅纹理替换

鞘翅作为特殊的穿戴物品，可以使用 `elytra` 属性进行专门的纹理替换：

```properties
# 附魔鞘翅的自定义纹理
items=minecraft:elytra
texture=item/custom_elytra_enchanted
elytra=true
enchantment=minecraft:unbreaking
weight=10
```

**自定义鞘翅模型**：
```properties
items=minecraft:elytra
model=item/custom_elytra_model
elytra=true
texture=item/custom_elytra_texture
weight=20
```

---

## 6. 工具纹理替换

### 6.1 基于耐久度的工具纹理

工具的纹理可以根据剩余耐久度进行动态替换，为玩家提供直观的磨损视觉反馈：

```properties
# 钻石镐 - 完好状态
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_new
damage=0-0.25
weight=5

# 钻石镐 - 轻微磨损
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_worn
damage=0.26-0.50
weight=5

# 钻石镐 - 中度磨损
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_damaged
damage=0.51-0.75
weight=5

# 钻石镐 - 严重磨损
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_broken
damage=0.76-1.0
weight=5
```

### 6.2 基于附魔的工具纹理

附魔可以为工具添加独特的视觉效果：

```properties
# 有效采集附魔的镐子
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_fortune
enchantment=minecraft:fortune
enchantment.level=3
weight=10

# 时运附魔 + 效率附魔的组合
items=minecraft:diamond_pickaxe
texture=item/diamond_pickaxe_ultimate
enchantment=minecraft:fortune
enchantment.level=3
enchantment=minecraft:efficiency
enchantment.level=5
weight=15
```

### 6.3 武器纹理替换

武器的 CIT 纹理替换可以根据附魔组合创建独特的视觉效果：

```properties
# 锋利V + 火焰附加II 的钻石剑
items=minecraft:diamond_sword
texture=item/diamond_sword_infernal
enchantment=minecraft:sharpness
enchantment.level=5
enchantment=minecraft:fire_aspect
enchantment.level=2
weight=20

# 亡灵杀手V 的钻石剑
items=minecraft:diamond_sword
texture=item/diamond_sword_holy
enchantment=minecraft:smite
enchantment.level=5
weight=10
```

---

## 7. CIT 模型替换

### 7.1 自定义物品模型

CIT 不仅可以替换纹理，还可以替换整个物品的 3D 模型。这需要在 .properties 文件中指定 `model` 属性。

**properties 文件**：
```properties
# custom_sword_model.properties
items=minecraft:diamond_sword
model=item/custom_sword_model
texture=item/custom_sword_texture
enchantment=minecraft:sharpness
enchantment.level=5
weight=15
```

**自定义模型文件** (custom_sword_model.json)：
```json
{
    "parent": "item/handheld",
    "textures": {
        "layer0": "item/custom_sword_texture"
    },
    "display": {
        "thirdperson_righthand": {
            "rotation": [0, -90, 55],
            "translation": [0, 4.0, 0.5],
            "scale": [0.85, 0.85, 0.85]
        },
        "firstperson_righthand": {
            "rotation": [0, -90, 25],
            "translation": [1.13, 3.2, 1.13],
            "scale": [0.68, 0.68, 0.68]
        }
    }
}
```

### 7.2 复杂自定义模型

可以创建完全自定义的 3D 模型来替换物品外观：

```json
{
    "textures": {
        "particle": "item/custom_sword_particle",
        "blade": "item/custom_sword_blade",
        "handle": "item/custom_sword_handle",
        "guard": "item/custom_sword_guard"
    },
    "elements": [
        {
            "from": [7, 0, 7.5],
            "to": [9, 12, 8.5],
            "faces": {
                "north": {"uv": [0, 0, 2, 12], "texture": "#blade"},
                "east": {"uv": [2, 0, 3, 12], "texture": "#blade"},
                "south": {"uv": [3, 0, 5, 12], "texture": "#blade"},
                "west": {"uv": [5, 0, 6, 12], "texture": "#blade"},
                "up": {"uv": [0, 0, 2, 1], "texture": "#blade"},
                "down": {"uv": [2, 0, 4, 1], "texture": "#blade"}
            }
        },
        {
            "from": [6, -1, 7],
            "to": [10, 0, 9],
            "faces": {
                "north": {"uv": [0, 0, 4, 1], "texture": "#guard"},
                "east": {"uv": [0, 0, 2, 1], "texture": "#guard"},
                "south": {"uv": [0, 0, 4, 1], "texture": "#guard"},
                "west": {"uv": [0, 0, 2, 1], "texture": "#guard"},
                "up": {"uv": [0, 0, 4, 2], "texture": "#guard"},
                "down": {"uv": [0, 0, 4, 2], "texture": "#guard"}
            }
        },
        {
            "from": [7.5, -5, 7.5],
            "to": [8.5, -1, 8.5],
            "faces": {
                "north": {"uv": [0, 0, 1, 4], "texture": "#handle"},
                "east": {"uv": [0, 0, 1, 4], "texture": "#handle"},
                "south": {"uv": [0, 0, 1, 4], "texture": "#handle"},
                "west": {"uv": [0, 0, 1, 4], "texture": "#handle"}
            }
        }
    ]
}
```

### 7.3 模型与纹理的配合

当同时指定 `model` 和 `texture` 时，需要确保模型文件中引用的纹理与 .properties 中指定的一致：

```properties
# 正确的配合方式
items=minecraft:diamond_sword
model=item/custom_sword_model
texture=item/custom_sword_texture
```

模型文件中的纹理引用：
```json
{
    "textures": {
        "layer0": "item/custom_sword_texture"
    }
}
```

---

## 8. 高级技巧与工具

### 8.1 权重系统深入理解

权重系统在复杂资源包中至关重要，特别是当多个规则可能同时匹配同一个物品时：

```properties
# 通用附魔纹理（低权重）
items=minecraft:diamond_sword
texture=item/diamond_sword_enchanted_generic
enchantment=*
weight=1

# 特定附魔纹理（中权重）
items=minecraft:diamond_sword
texture=item/diamond_sword_sharpness
enchantment=minecraft:sharpness
weight=5

# 特定附魔+等级纹理（高权重）
items=minecraft:diamond_sword
texture=item/diamond_sword_sharpness_max
enchantment=minecraft:sharpness
enchantment.level=5
weight=10

# 组合附魔纹理（最高权重）
items=minecraft:diamond_sword
texture=item/diamond_sword_god
enchantment=minecraft:sharpness
enchantment.level=5
enchantment=minecraft:fire_aspect
enchantment.level=2
enchantment=minecraft:looting
enchantment.level=3
weight=100
```

### 8.2 调试技巧

当 CIT 纹理不按预期工作时，可以使用以下调试方法：

1. **检查日志**：OptiFine 会在游戏日志中输出 CIT 加载信息
2. **简化规则**：先用最简单的规则测试，逐步添加条件
3. **检查路径**：确保纹理和模型路径正确无误
4. **验证 NBT**：使用 F3+H 显示高级提示框，检查物品的实际 NBT 数据

### 8.3 性能优化建议

大量 CIT 规则可能影响游戏性能，建议：

- 合理使用权重避免不必要的规则评估
- 避免使用 `items=*` 这样的宽泛匹配
- 将常用规则放在权重较高的位置
- 使用子目录合理组织规则文件
- 定期清理未使用的纹理文件

### 8.4 常用开发工具

| 工具 | 用途 | 链接 |
|------|------|------|
| Blockbench | 3D 模型编辑 | blockbench.net |
| Notepad++ | 属性文件编辑 | notepad-plus-plus.org |
| NBTExplorer | NBT 数据查看 | github.com/jaquadro/NBTExplorer |
| OptiFine CIT Generator | 在线 CIT 配置生成 | 各种社区工具 |

---

## 9. 实际应用案例

### 9.1 完整的附魔武器纹理包

以下是一个完整的附魔武器 CIT 资源包示例：

**目录结构**：
```
assets/minecraft/
├── optifine/cit/
│   ├── swords/
│   │   ├── diamond_fire.properties
│   │   ├── diamond_fire.png
│   │   ├── diamond_sharpness.properties
│   │   ├── diamond_sharpness.png
│   │   ├── netherite_fire.properties
│   │   └── netherite_fire.png
│   └── tools/
│       ├── diamond_fortune.properties
│       └── diamond_fortune.png
└── textures/
    └── item/
        ├── diamond_sword_fire.png
        ├── diamond_sword_sharpness.png
        ├── netherite_sword_fire.png
        └── diamond_pickaxe_fortune.png
```

**diamond_fire.properties**：
```properties
# 钻石剑 - 火焰附魔效果
items=minecraft:diamond_sword
texture=item/diamond_sword_fire
enchantment=minecraft:fire_aspect
weight=10
```

**diamond_sharpness.properties**：
```properties
# 钻石剑 - 锋利附魔效果
items=minecraft:diamond_sword
texture=item/diamond_sword_sharpness
enchantment=minecraft:sharpness
enchantment.level=5
weight=15
```

### 9.2 耐久度视觉反馈系统

为工具和武器创建基于耐久度的视觉磨损效果：

```properties
# 完好无损 (100%-75%)
items=minecraft:diamond_pickaxe,minecraft:diamond_axe,minecraft:diamond_shovel
texture=item/diamond_tool_perfect
damage=0.0-0.25
weight=5

# 轻微磨损 (75%-50%)
items=minecraft:diamond_pickaxe,minecraft:diamond_axe,minecraft:diamond_shovel
texture=item/diamond_tool_good
damage=0.26-0.50
weight=5

# 中度磨损 (50%-25%)
items=minecraft:diamond_pickaxe,minecraft:diamond_axe,minecraft:diamond_shovel
texture=item/diamond_tool_worn
damage=0.51-0.75
weight=5

# 严重磨损 (25%-0%)
items=minecraft:diamond_pickaxe,minecraft:diamond_axe,minecraft:diamond_shovel
texture=item/diamond_tool_broken
damage=0.76-1.0
weight=5
```

### 9.3 套装效果视觉系统

当玩家穿戴完整套装时，显示特殊的视觉效果：

```properties
# 下界合金套装 - 特殊头盔
items=minecraft:netherite_helmet
texture=armor/netherite_helmet_set
armor=head
enchantment=minecraft:protection
enchantment.level=4
enchantment=minecraft:unbreaking
enchantment.level=3
weight=50

# 下界合金套装 - 特殊胸甲
items=minecraft:netherite_chestplate
texture=armor/netherite_chestplate_set
armor=chest
enchantment=minecraft:protection
enchantment.level=4
enchantment=minecraft:unbreaking
enchantment.level=3
weight=50
```

---

## 10. 常见问题与解决方案

### 10.1 纹理不显示

**问题**：CIT 配置正确但纹理没有替换。

**可能原因**：
- 纹理文件路径错误
- 纹理文件格式不正确（应为 PNG 格式）
- OptiFine 版本与 Minecraft 版本不匹配
- 其他资源包覆盖了 CIT 配置

**解决方案**：
1. 检查纹理文件是否在正确的位置
2. 验证 PNG 文件格式和尺寸
3. 更新 OptiFine 到对应版本
4. 调整资源包加载顺序

### 10.2 多规则冲突

**问题**：多个 CIT 规则同时匹配，但显示了错误的纹理。

**解决方案**：
- 使用 `weight` 属性设置优先级
- 使规则条件更加具体
- 合并相似的规则

### 10.3 性能问题

**问题**：安装 CIT 资源包后游戏帧率下降。

**解决方案**：
- 减少 CIT 规则数量
- 避免过于宽泛的匹配条件
- 优化纹理文件尺寸
- 使用更高效的权重配置

---

## 11. 总结

OptiFine CIT 是一个强大而灵活的物品纹理替换系统，通过条件化的规则配置，可以实现丰富多样的物品视觉效果。掌握 CIT 的使用需要理解：

1. **基础语法**：.properties 文件的格式和各个属性的含义
2. **条件匹配**：如何使用各种条件属性精确匹配目标物品
3. **权重系统**：如何管理多个规则的优先级
4. **模型替换**：如何创建和应用自定义 3D 模型
5. **性能优化**：如何在视觉效果和性能之间取得平衡

通过合理运用这些知识，资源包开发者可以创造出令人印象深刻的视觉体验，让 Minecraft 的物品系统展现出前所未有的多样性和细节。
