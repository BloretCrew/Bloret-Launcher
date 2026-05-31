### 18. `Simple Grass Flowers v1.9.6` 文件索引

**包类型**: 草地方块装饰增强
**文件规模**: 约 62 个文件
**技术原理**: 通过自定义方块模型和纹理为草方块等添加随机装饰物（三叶草、花朵、蘑菇、石头等）

#### 根目录
| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据文件 |
| `pack.png` | 资源包封面图标 |
| `Read Me.txt` | 使用说明文档 |
| `Cat.png` | 猫咪彩蛋图片（约 107KB） |

#### 关键目录
| 路径 | 功能 |
|---|---|
| `assets/minecraft/blockstates/` | 方块状态定义（草方块、菌丝、灰化土、绯红/诡异菌岩，5 个 JSON） |
| `assets/minecraft/models/block/grass_block/` | 草方块装饰模型（6 个变体：基础、三叶草、小花、大花、石头） |
| `assets/minecraft/models/block/mycelium/` | 菌丝装饰模型（5 个变体：基础、三叶草、红蘑菇、棕蘑菇） |
| `assets/minecraft/models/block/podzol/` | 灰化土装饰模型（6 个变体） |
| `assets/minecraft/models/block/crimson_nylium/` | 绯红菌岩装饰模型（5 个变体） |
| `assets/minecraft/models/block/warped_nylium/` | 诡异菌岩装饰模型（5 个变体） |
| `assets/minecraft/textures/block/grass_block/` | 草方块装饰纹理（三叶草、花朵、石头等 PNG） |
| `assets/minecraft/textures/block/mycelium/` | 菌丝装饰纹理（三叶草、蘑菇等 PNG） |
| `assets/minecraft/textures/block/podzol/` | 灰化土装饰纹理 |
| `assets/minecraft/textures/block/crimson_nylium/` | 绯红菌岩装饰纹理 |
| `assets/minecraft/textures/block/warped_nylium/` | 诡异菌岩装饰纹理 |
| `assets/minecraft/textures/colormap/` | 颜色映射（`grass.png` 和 `foliage.png`，控制生物群系颜色） |

#### 代表文件
| 路径 | 功能 |
|---|---|
| `assets/minecraft/blockstates/grass_block.json` | 草方块状态定义（含随机模型选择） |
| `assets/minecraft/models/block/grass_block/grass_block.json` | 草方块基础模型 |
| `assets/minecraft/models/block/grass_block/grass_block_flower_big.json` | 草方块大花装饰模型 |
| `assets/minecraft/models/block/grass_block/grass_block_clover.json` | 草方块三叶草装饰模型 |
| `assets/minecraft/models/block/grass_block_decor.json` | 草方块装饰层模型 |
| `assets/minecraft/textures/block/grass_block/grass_block_top_clover.png` | 三叶草装饰纹理 |
| `assets/minecraft/textures/block/grass_block/grass_block_top_flower_big.png` | 大花朵装饰纹理 |
| `assets/minecraft/textures/block/wildflowers.png` | 野花纹理 |
| `assets/minecraft/textures/colormap/grass.png` | 草地颜色映射图 |
