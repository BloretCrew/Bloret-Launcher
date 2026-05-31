### 26. `EvenBetterEnchants_v3_1.21.5+` 文件索引

**包类型**: 附魔书视觉增强
**文件规模**: 约 264 个文件
**技术原理**: 通过自定义物品模型和纹理，为每种附魔（含不同等级）提供独立的附魔书图标，使附魔书在背包中可直观区分
**兼容版本**: Minecraft 1.21.5+

#### 根目录
| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据文件 |
| `pack.png` | 资源包封面图标 |
| `README.txt` | 说明文档 |

#### 关键目录
| 路径 | 功能 |
|---|---|
| `assets/minecraft/items/` | 物品定义（`enchanted_book.json`，1.21+ 物品选择器格式） |
| `assets/minecraft/models/item/` | 附魔书物品模型（每种附魔每个等级一个 JSON，约 130 个） |
| `assets/minecraft/textures/item/` | 附魔书纹理（每种附魔每个等级一个 PNG，约 130 张） |

#### 代表文件
| 路径 | 功能 |
|---|---|
| `assets/minecraft/items/enchanted_book.json` | 附魔书物品定义（基于附魔类型/等级选择模型） |
| `assets/minecraft/models/item/enchanted_book.json` | 附魔书基础模型（无附魔时） |
| `assets/minecraft/models/item/.big_enchanted_book.json` | 大尺寸附魔书基础模型 |
| `assets/minecraft/models/item/efficiency_1.json` ~ `efficiency_5.json` | 效率 I-V 附魔书模型 |
| `assets/minecraft/models/item/fortune_1.json` ~ `fortune_3.json` | 时运 I-III 附魔书模型 |
| `assets/minecraft/models/item/protection_1.json` ~ `protection_4.json` | 保护 I-IV 附魔书模型 |
| `assets/minecraft/models/item/sharpness_1.json` ~ `sharpness_5.json` | 锋利 I-V 附魔书模型 |
| `assets/minecraft/models/item/mending_1.json` | 经验修补附魔书模型 |
| `assets/minecraft/models/item/feather_falling_1.json` ~ `feather_falling_4.json` | 摔落保护 I-IV 模型 |
| `assets/minecraft/models/item/breach_1.json` ~ `breach_4.json` | 破甲 I-IV 模型（1.21 新附魔） |
| `assets/minecraft/models/item/density_1.json` ~ `density_5.json` | 密度 I-V 模型（1.21 新附魔） |
| `assets/minecraft/models/item/lunge_1.json` ~ `lunge_3.json` | 突刺 I-III 模型（1.21 新附魔） |
