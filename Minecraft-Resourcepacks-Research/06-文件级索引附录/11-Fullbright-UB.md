# 11. Fullbright-UB-1.21 文件索引

> 资源包全名：`Fullbright-UB-1.21`
> 文件总数：6 个
> 类型：着色器资源包，实现全亮度（Fullbright）效果，消除黑暗区域

---

### 根目录

| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据，定义包格式版本与描述 |
| `pack.png` | 资源包封面图标 |
| `shader/` | 着色器方案 1（Underwater Bright 水下全亮版本） |
| `shader2/` | 着色器方案 2（替代全亮版本） |

---

### 关键目录

| 路径 | 功能 |
|---|---|
| `shader/assets/minecraft/shaders/core/` | 核心着色器目录（方案 1） |
| `shader/assets/minecraft/shaders/include/` | 着色器包含文件目录（方案 1） |
| `shader2/assets/minecraft/shaders/core/` | 核心着色器目录（方案 2） |
| `shader2/assets/minecraft/shaders/include/` | 着色器包含文件目录（方案 2） |

---

### 代表文件

| 路径 | 功能 |
|---|---|
| `shader/assets/minecraft/shaders/core/lightmap.fsh` | 光照贴图片段着色器（方案 1），强制最大亮度 |
| `shader/assets/minecraft/shaders/include/fog.glsl` | 雾效包含文件（方案 1），移除黑暗雾效 |
| `shader2/assets/minecraft/shaders/core/lightmap.fsh` | 光照贴图片段着色器（方案 2），替代全亮实现 |
| `shader2/assets/minecraft/shaders/include/fog.glsl` | 雾效包含文件（方案 2），替代雾效处理 |
| `pack.mcmeta` | 资源包元数据定义 |
| `pack.png` | 资源包封面 |
