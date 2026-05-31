# 39. NoFog

## 根目录结构

```
NoFog/
├── assets/
│   └── minecraft/
│       └── shaders/
│           ├── core/
│           │   └── position.fsh     # 核心着色器：位置片段着色器
│           └── include/
│               └── fog.glsl         # 雾效计算函数库
├── overlay_1/
│   └── assets/
│       └── minecraft/
│           └── shaders/
│               ├── core/
│               │   └── position.fsh
│               └── include/
│                   └── fog.glsl
├── overlay_42/
│   └── assets/
│       └── minecraft/
│           └── shaders/
│               ├── core/
│               │   └── position.fsh
│               └── include/
│                   └── fog.glsl
├── pack.mcmeta
└── pack.png
```

## 包定位

NoFog（无雾）是一个**性能/视觉优化类**资源包，由 Hxndrik 在 Modrinth 上发布。它的功能非常明确——**移除游戏中的所有雾效**。这包括但不限于：

- 地形雾效（远处地形的淡出效果）
- 水下雾效
- 熔岩雾效
- 虚空雾效

移除雾效有两个主要好处：
1. **视觉效果**：让玩家可以看到更远的地形，获得更广阔清晰的视野
2. **性能优化**：在某些情况下可以略微减轻GPU的渲染负担（因为雾效本身也需要计算）

该包在 Modrinth 上非常受欢迎，下载量超过百万，说明对雾效不满的玩家数量相当可观。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "pack_format": 1,
    "supported_formats": {"min_inclusive": 1, "max_inclusive": 99},
    "description": "Removes Fog!"
  },
  "overlays": {
    "entries": [
      {
        "formats": {"min_inclusive": 1, "max_inclusive": 99},
        "directory": "overlay_42"
      },
      {
        "formats": {"min_inclusive": 1, "max_inclusive": 99},
        "directory": "overlay_1"
      }
    ]
  }
}
```

pack_format 为1（Minecraft 1.6.1-1.8.9），但 `supported_formats` 覆盖了1到99的全部范围，提供了极端的向下兼容性。有趣的是，虽然pack_format设置为1，但两个overlay同样覆盖了相同的版本范围（1-99），这意味着在所有版本中，overlay文件都会覆盖基础文件。

**fog.glsl（基础版）：**
```
// Created by and for modrinth.com/user/Hxndrik
#version 150

// Calculates linear fog without altering the input color
vec4 compute_linear_fog(vec4 inputColor, float distance, float start, float end, vec4 color) {
    return inputColor;
}

// Determines fog fade based on distance
float compute_fog_fade(float distance, float start, float end) {
    return 1.0;
}

// Calculates fog distance based on position and shape
float compute_fog_distance(vec3 position, int shapeType) {
    if (shapeType == 0) {
        return length(position);
    } else {
        float horizontalDist = length(position.xz);
        float verticalDist = abs(position.y);
        return max(horizontalDist, verticalDist);
    }
}
```

实现原理非常直接：
- `compute_linear_fog()`: 无论输入什么距离和颜色，直接返回原始颜色（不应用雾效）
- `compute_fog_fade()`: 始终返回 1.0（完全不雾化）
- `compute_fog_distance()`: 虽然保留了雾距计算函数，但因为前两个函数已经无视了雾效，所以这个函数实际上不会被用于雾效效果

**position.fsh（基础版）：**
这个片段着色器文件保留了 `linear_fog()` 函数的完整实现，但在实际渲染中因为 `fog.glsl` 中的函数被覆盖为无操作版本，因此雾效不会生效。

**overlay_1/ 和 overlay_42/ 版本：**
这两个overlay目录中的 `fog.glsl` 使用了不同的函数签名（例如 `linear_fog()` 而不是 `compute_linear_fog()`），对应于不同Minecraft版本中的着色器API变化。这样做是为了确保在不同版本中都能正确移除雾效。

## 资源内容结构

本包的资源目录结构专注于一个目标——修改Minecraft的着色器系统。涉及的着色器文件：

- **fog.glsl**：包含雾效计算函数，是本包的核心修改对象
- **position.fsh**：位置相关的片段着色器，调用了 fog.glsl 中的函数

### 三个版本的着色器

本包通过 overlay 系统提供了3个版本的着色器：

| 目录 | fog.glsl 函数名 | 用途 |
|---|---|---|
| 基础 | compute_linear_fog / compute_fog_fade | 早期版本（1.6-1.16） |
| overlay_1 | linear_fog / linear_fog_fade | 1.17+ 新着色器API |
| overlay_42 | 同基础版但不同包格式 | 适用于 pack_format 42+ |

## 技术特点

1. **内核级修改**：不满足于普通的资源替换，而是深入到游戏的着色器层面。通过修改GLSL着色器代码，直接从渲染管线上禁用了雾效计算。

2. **极致的版本兼容**：借助Overlay系统和多个版本的文件，使一个资源包可以在Minecraft 1.6到最新版本的所有游戏中正常工作。

3. **极简实现**：实现方式非常优雅简单——只需要让雾效函数返回原始颜色，而不需要修改其他任何内容。这种做法的好处是兼容性好，不会破坏其他渲染效果。

4. **着色器知识依赖**：需要理解Minecraft的渲染管线工作原理和GLSL着色器语言，才能制作这样的资源包。

5. **副作用极小**：只禁用雾效，不影响光照、阴影、透明效果等其他视觉功能。

6. **同时移除所有雾效**：不仅是地形雾，还包括水下、熔岩、虚空、药水效果迷雾等所有类型的雾效。

## 结论

NoFog 是一个功能高度专一的资源包，它的设计哲学很清晰——"只做一件事，并把它做好"。通过直接修改Minecraft的片段着色器，它有效地移除了游戏中所有形式的雾效，为玩家提供了清晰无碍的视野。

对于喜欢探索大型地形、建造大型建筑、或者单纯不喜欢雾效遮住视线的玩家来说，这个包非常实用。在PVP场景中，移除雾效也能带来一定的战术优势（如更早发现远处的敌人）。对于性能敏感的用户，移除雾效也可能带来非常微小的帧率提升。

此外，NoFog 的着色器实现方式也为其他资源包作者提供了一个很好的参考模板——如何通过着色器修改来实现特定的视觉效果。如果你也想制作类似的视觉效果修改包，NoFog 的代码结构是一个很好的起点。
