### 40. `NoFog` 文件索引

**包类型**: 去除迷雾包 | **文件总数**: 8 | **功能**: 通过着色器移除各种迷雾效果 | **特性**: 多版本覆盖

#### 根目录
| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据定义 |
| `pack.png` | 资源包图标 |
| `assets/` | 主资源包资产目录 |
| `overlay_1/` | 覆盖层1资源（版本兼容） |
| `overlay_42/` | 覆盖层42资源（版本兼容） |

#### 关键目录
| 路径 | 功能 |
|---|---|
| `assets/minecraft/shaders/core/` | 核心着色器目录 |
| `assets/minecraft/shaders/include/` | 着色器包含文件目录 |
| `overlay_1/assets/minecraft/shaders/core/` | 覆盖层1着色器 |
| `overlay_1/assets/minecraft/shaders/include/` | 覆盖层1包含文件 |
| `overlay_42/assets/minecraft/shaders/core/` | 覆盖层42着色器 |
| `overlay_42/assets/minecraft/shaders/include/` | 覆盖层42包含文件 |

#### 代表文件
| 路径 | 功能 |
|---|---|
| `assets/minecraft/shaders/core/position.fsh` | 位置片段着色器（移除迷雾核心） |
| `assets/minecraft/shaders/include/fog.glsl` | 迷雾计算包含文件（禁用迷雾效果） |
| `overlay_1/assets/minecraft/shaders/core/position.fsh` | 覆盖层1位置着色器 |
| `overlay_1/assets/minecraft/shaders/include/fog.glsl` | 覆盖层1迷雾配置 |
| `overlay_42/assets/minecraft/shaders/core/position.fsh` | 覆盖层42位置着色器 |
| `overlay_42/assets/minecraft/shaders/include/fog.glsl` | 覆盖层42迷雾配置 |
