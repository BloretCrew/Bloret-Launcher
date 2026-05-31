# 11. Fullbright-UB-1.21

## 根目录结构

```
Fullbright-UB-1.21/
├── pack.mcmeta
├── pack.png
├── shader/
│   └── assets/minecraft/shaders/
│       ├── core/lightmap.fsh
│       └── include/fog.glsl
└── shader2/
    └── assets/minecraft/shaders/
        ├── core/lightmap.fsh
        └── include/fog.glsl
```

## 包定位

Fullbright-UB-1.21（全称 Fullbright Ubiquitous，FUB 5.0）是一个纯着色器修改类资源包，核心功能是移除游戏中的黑暗环境照明，使所有场景始终保持明亮（Fullbright）。该包不包含任何纹理贴图，完全通过修改 Minecraft 核心着色器来实现照明和雾效控制。适合需要在黑暗区域（洞穴、夜间）获得无障碍视野的玩家，尤其是建筑玩家或探索玩家。

## 关键文件说明

### pack.mcmeta

- **路径**: `Fullbright-UB-1.21/pack.mcmeta`
- **pack_format**: 4（基版本很低，但通过 supported_formats 覆盖广泛版本）
- **supported_formats**: [4, 1000] —— 覆盖极广的范围
- **描述**: "Fullbright Ubiquitous (FUB 5.0)"

**Overlay 系统分析**：该包使用了五个 overlay 条目，巧妙的版本控制展示了 Minecraft 版本演进中着色器接口的变化：

| Overlay 目录 | 适用格式范围 | 版本说明 |
|---|---|---|
| `fixes` | 18~1000 | 修复层，适用于几乎所有现代版本 |
| `bat` | 19~1000 | 蝙蝠相关修复 |
| `shader` | 25~62 | 1.21 快照/正式版（旧版 UBO 之前的着色器） |
| `shader2` | 63~1000 | 1.21.2+（引入了 std140 UBO 的新版着色器） |
| `cow` | 55~1000 | 牛相关修复 |

### pack.png

- 资源包图标，未做特别分析。

## 资源内容结构

资源包仅包含着色器文件，无任何 `textures`、`models`、`lang` 等传统资源。全部资源集中在两个 overlay 目录中：

- `shader/` —— 旧版着色器（pack_format 25-62，对应 1.21 早期版本）
- `shader2/` —— 新版着色器（pack_format 63+，对应 1.21.2+）

## 关键目录功能

### shader/ 目录（旧版接口）

**核心文件**: `shader/assets/minecraft/shaders/core/lightmap.fsh`

使用独立的 uniform 变量声明（非 UBO 方式）：

```glsl
uniform float AmbientLightFactor;
uniform float SkyFactor;
uniform float BlockFactor;
uniform int UseBrightLightmap;
uniform vec3 SkyLightColor;
uniform float NightVisionFactor;
uniform float DarknessScale;
uniform float DarkenWorldFactor;
uniform float BrightnessFactor;
```

这是 1.21 早期版本的着色器格式，所有 uniform 变量都是顶层声明。

**技术实现**：
- `get_brightness()` 函数使用曲线插值 `level / (4.0 - 3.0 * level)` 混合环境光因子
- `notGamma()` 函数实现了反伽马校正 `1.0 - (1.0 - x)^4`
- 当 `BrightnessFactor >= 0.10` 时，方块亮度被除以 3 并变色为蓝紫色调
- 当 `BrightnessFactor <= 0.10` 时，直接输出纯白色 `vec3(1.0)` —— 实现完全全亮
- 夜视效果通过颜色分量归一化实现
- 黑暗缩放（DarknessScale）从颜色中减去

**雾效文件**: `shader/assets/minecraft/shaders/include/fog.glsl`

这是一个独立的雾效实现（未使用 std140 UBO），包含：
- `linear_fog()` —— 混合雾颜色的主函数
- 末影龙迷雾/细雪迷雾/熔岩迷雾的特殊处理（通过 RGB 值判断）
- 失明与黑暗效果的特殊雾处理
- 地狱与末地的无雾逻辑
- `linear_fog_fade()` —— 雾渐隐辅助函数
- `fog_distance()` —— 根据形状（球形/圆柱形）计算距离

### shader2/ 目录（新版接口）

**核心文件**: `shader2/assets/minecraft/shaders/core/lightmap.fsh`

使用 `std140` 布局的 UBO 统一块：

```glsl
layout(std140) uniform LightmapInfo {
    float AmbientLightFactor;
    float SkyFactor;
    float BlockFactor;
    int UseBrightLightmap;
    float NightVisionFactor;
    float DarknessScale;
    float DarkenWorldFactor;
    float BrightnessFactor;
    vec3 SkyLightColor;
} lightmapInfo;
```

这是 1.21.2+ 引入的新格式。功能逻辑与旧版相同，但通过 UBO 访问成员。

**雾效文件**: `shader2/assets/minecraft/shaders/include/fog.glsl`

使用 std140 UBO：

```glsl
layout(std140) uniform Fog {
    vec4 FogColor;
    float FogEnvironmentalStart;
    float FogEnvironmentalEnd;
    float FogRenderDistanceStart;
    float FogRenderDistanceEnd;
    float FogSkyEnd;
    float FogCloudsEnd;
};
```

提供更标准化的雾效计算，包含 `apply_fog()` 函数和环境雾+渲染距离雾的双重计算。

## 技术特点

1. **纯着色器修改**：不包含任何纹理/模型/语言文件，完全通过 GPU 着色器实现功能。

2. **双版本着色器兼容**：通过 Overlay 系统同时支持旧版（独立 uniform）和新版（std140 UBO）两种着色器接口格式，覆盖从 1.17 到最新版本的广泛范围。

3. **复杂的亮度控制逻辑**：核心 lightmap.fsh 包含亮度曲线、伽马校正、夜视模拟、环境光混合等多重照明处理，并非简单地设置为全白。

4. **雾效系统全面重写**：fog.glsl 包含对不同雾类型（末影龙、细雪、熔岩、失明、普通雾）的特殊处理逻辑，以及球形/圆柱形两种距离计算模式。

5. **亮度因子分级**：代码中存在 `BrightnessFactor` 的多级阈值判断（0.10, 0.80, 1.00），不同阈值对应不同的亮度和色彩表现。

## 结论

Fullbright-UB-1.21 是一个高度专业化的纯粹着色器修改资源包。其核心价值在于通过 GPU 层面的着色器修改实现照明控制，而非传统资源包使用的纹理替换。该包展现了 Minecraft 版本演进中着色器接口的变化（从独立 uniform 到 std140 UBO），以及如何通过 overlay 系统实现跨版本兼容。其代码组织清晰，对 fog.glsl 和 lightmap.fsh 的修改体现了对 Minecraft 渲染管线的深入理解。
