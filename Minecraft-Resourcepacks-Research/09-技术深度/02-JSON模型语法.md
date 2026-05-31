# JSON 模型语法参考

## 概述

Minecraft 的方块和物品模型通过 JSON 文件定义。本文档全面解析 JSON 模型的完整语法规范，涵盖文件格式、顶层结构、纹理定义、元素（elements）数组、显示（display）位置、模型覆盖（overrides）以及继承机制。

---

## 1. 文件格式与路径

### 1.1 文件位置

模型文件存放在 `assets/<namespace>/models/` 目录下：

```
assets/minecraft/models/
├── block/              # 方块模型
│   ├── stone.json
│   ├── oak_log.json
│   ├── furnace.json
│   └── chest.json
├── item/               # 物品模型
│   ├── diamond_sword.json
│   ├── bread.json
│   └── bow.json
└── (自定义命名空间)
    └── my_model.json
```

### 1.2 引用路径

模型的引用路径不包含 `assets/` 前缀和 `.json` 后缀：

```
文件路径:  assets/minecraft/models/block/stone.json
引用路径:  minecraft:block/stone

文件路径:  assets/mypack/models/item/custom_sword.json
引用路径:  mypack:item/custom_sword
```

### 1.3 JSON 格式要求

```json
{
  "//": "JSON 格式要求",
  "//1": "使用标准 JSON 格式（非 JSONC）",
  "//2": "不支持注释（使用空键名 '//') 来添加说明",
  "//3": "键名必须用双引号包围",
  "//4": "字符串值必须用双引号包围",
  "//5": "数值不加引号",
  "//6": "最后一个键值对后不能有逗号"
}
```

---

## 2. 顶层结构

模型 JSON 文件的顶层结构如下：

```json
{
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/stone"
  },
  "elements": [],
  "display": {},
  "gui_light": "front",
  "overrides": []
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `parent` | string | 否 | 父模型的资源路径 |
| `textures` | object | 否 | 纹理变量定义 |
| `elements` | array | 否 | 模型元素（几何体）定义 |
| `display` | object | 否 | 不同显示位置的变换参数 |
| `gui_light` | string | 否 | GUI 中的光照模式 |
| `overrides` | array | 否 | 模型覆盖规则（仅物品模型） |

---

## 3. 纹理定义（textures）

### 3.1 基本语法

纹理定义将变量名映射到纹理路径：

```json
{
  "textures": {
    "particle": "minecraft:block/stone",
    "down": "minecraft:block/stone",
    "up": "minecraft:block/stone",
    "north": "minecraft:block/stone",
    "south": "minecraft:block/stone",
    "east": "minecraft:block/stone",
    "west": "minecraft:block/stone"
  }
}
```

### 3.2 变量引用

在 `elements` 中，使用 `#变量名` 引用纹理变量：

```json
{
  "textures": {
    "all": "minecraft:block/stone"
  },
  "elements": [
    {
      "faces": {
        "north": { "texture": "#all" },
        "south": { "texture": "#all" },
        "east": { "texture": "#all" },
        "west": { "texture": "#all" },
        "up": { "texture": "#all" },
        "down": { "texture": "#all" }
      }
    }
  ]
}
```

### 3.3 特殊变量

| 变量名 | 用途 | 说明 |
|--------|------|------|
| `particle` | 粒子效果纹理 | 破坏方块时的粒子效果使用的纹理 |
| `#particle` | 粒子变量引用 | 在 elements 中引用粒子纹理 |

### 3.4 纹理路径格式

```
完整路径格式:  <namespace>:<path/to/texture>
示例:          minecraft:block/stone
示例:          mypack:item/custom_sword

不带命名空间:  block/stone
等价于:        minecraft:block/stone
```

**注意**：纹理路径不包含 `assets/<namespace>/textures/` 前缀和 `.png` 后缀。

### 3.5 纹理继承

当模型有 `parent` 时，纹理可以被子模型覆盖或补充：

```json
{
  "//": "父模型：定义变量但不赋值",
  "parent": "minecraft:block/cube",
  "textures": {
    "down": "#all",
    "up": "#all",
    "north": "#all",
    "south": "#all",
    "east": "#all",
    "west": "#all"
  }
}
```

```json
{
  "//": "子模型：为变量赋值",
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/stone"
  }
}
```

继承链中的纹理解析：
1. 子模型定义的纹理优先级最高
2. 父模型定义的纹理次之
3. 祖先模型定义的纹理再次之
4. 最终所有变量必须被解析为具体纹理路径

---

## 4. 元素数组（elements）

### 4.1 元素结构

`elements` 数组定义模型的几何体，每个元素是一个长方体（box）：

```json
{
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "rotation": {
        "origin": [8, 8, 8],
        "axis": "y",
        "angle": 45,
        "rescale": false
      },
      "shade": true,
      "faces": {
        "down": {
          "uv": [0, 0, 16, 16],
          "texture": "#all",
          "cullface": "down",
          "rotation": 0,
          "tintindex": -1
        },
        "up": { "texture": "#all" },
        "north": { "texture": "#all" },
        "south": { "texture": "#all" },
        "east": { "texture": "#all" },
        "west": { "texture": "#all" }
      }
    }
  ]
}
```

### 4.2 from 和 to

定义长方体的两个对角顶点，坐标范围为 -16 到 32：

```json
{
  "from": [0, 0, 0],
  "to": [16, 16, 16]
}
```

**坐标系统**：
```
         Y (向上)
         │
         │
         │
         └───────── X (向右)
        /
       /
      Z (向南/向前)

原点 (0,0,0) 位于方块的西南下角
(16,16,16) 位于方块的东北上角

坐标范围：
  最小值: -16
  最大值: 32
  允许超出标准方块范围（用于特殊效果）
```

**from 和 to 的约束**：
- 每个轴上 `from` 的值必须小于 `to` 的值
- 三个轴上差值的绝对值必须 >= 0.001（不能是平面）
- 差值的绝对值必须 <= 16

### 4.3 rotation

元素级别的旋转：

```json
{
  "rotation": {
    "origin": [8, 8, 8],
    "axis": "y",
    "angle": 45,
    "rescale": false
  }
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `origin` | [x, y, z] | 旋转中心点，默认 [0, 0, 0] |
| `axis` | string | 旋转轴：`"x"`、`"y"` 或 `"z"` |
| `angle` | number | 旋转角度：`-45`、`-22.5`、`0`、`22.5`、`45`（只能是这些值） |
| `rescale` | bool | 是否对旋转后的面进行缩放以保持原始尺寸，默认 `false` |

**角度限制说明**：
```json
{
  "//1": "只支持以下角度值: -45, -22.5, 0, 22.5, 45",
  "//2": "不支持任意角度（这是模型系统的限制）",
  "//3": "需要其他角度时，使用多个元素组合或 OptiFine 的自定义模型"
}
```

**rescale 效果**：
- `false`：旋转后元素保持原始形状
- `true`：旋转后的面会被缩放，使元素看起来像一个斜切的长方体

### 4.4 shade

控制元素是否接收来自不同方向的环境光照阴影：

```json
{
  "shade": true
}
```

| 值 | 效果 |
|----|------|
| `true`（默认） | 元素的各个面根据朝向显示不同的亮度（上亮、下暗、北暗等） |
| `false` | 所有面使用相同亮度，无方向性阴影 |

**使用场景**：
- `true`：大多数方块和物品，需要立体感
- `false`：平面元素（如告示牌文字）、光源相关元素（如火把火焰）

### 4.5 faces

定义元素六个面的纹理和属性：

```json
{
  "faces": {
    "down":  { "uv": [0, 0, 16, 16], "texture": "#down",  "cullface": "down",  "rotation": 0, "tintindex": -1 },
    "up":    { "uv": [0, 0, 16, 16], "texture": "#up",    "cullface": "up",    "rotation": 0 },
    "north": { "uv": [0, 0, 16, 16], "texture": "#north", "cullface": "north", "rotation": 0 },
    "south": { "uv": [0, 0, 16, 16], "texture": "#south", "cullface": "south", "rotation": 0 },
    "east":  { "uv": [0, 0, 16, 16], "texture": "#east",  "cullface": "east",  "rotation": 0 },
    "west":  { "uv": [0, 0, 16, 16], "texture": "#west",  "cullface": "west",  "rotation": 0 }
  }
}
```

**面的方向定义**：
```
        up (顶部, Y+)
         │
         │
  west ──┼── east (X+, X-)
        /│
       / │
     north│   south (Z+, Z-)
         │
       down (底部, Y-)
```

#### 4.5.1 uv

UV 坐标定义纹理在面上的映射区域：

```json
{
  "uv": [u1, v1, u2, v2]
}
```

- `[u1, v1]`：左上角坐标
- `[u2, v2]`：右下角坐标
- 范围：0 到 16（对于 16×16 纹理）
- **省略时**：Minecraft 会自动根据元素的坐标计算 UV（按像素 1:1 映射）

```json
{
  "//": "UV 自动计算示例",
  "from": [0, 0, 0],
  "to": [8, 8, 8],
  "faces": {
    "north": {
      "//": "省略 uv 时，自动计算为 [0, 0, 8, 8]",
      "texture": "#all"
    }
  }
}
```

**UV 坐标与纹理分辨率的关系**：
- UV 坐标始终在 0-16 的范围内（即使纹理实际分辨率为 128×128）
- Minecraft 会自动将 UV 坐标映射到实际纹理像素

#### 4.5.2 texture

纹理引用，使用 `#变量名` 格式：

```json
{
  "texture": "#all"       // 引用 textures 中定义的 #all 变量
}
```

**特殊情况**：
```json
{
  "texture": "#missing"   // 引用缺失的变量，显示紫黑棋盘格（用于调试）
}
```

#### 4.5.3 cullface

指定当相邻方块为不透明时，该面是否应被剔除（不渲染）：

```json
{
  "cullface": "north"
}
```

| 值 | 说明 |
|----|------|
| `"down"` | 当下方方块不透明时剔除此面 |
| `"up"` | 当上方方块不透明时剔除此面 |
| `"north"` | 当北方方块不透明时剔除此面 |
| `"south"` | 当南方方块不透明时剔除此面 |
| `"east"` | 当东方方块不透明时剔除此面 |
| `"west"` | 当西方方块不透明时剔除此面 |

**cullface 的优化意义**：
- 正确设置 cullface 可以显著减少渲染的面数
- 标准方块（如石头）的所有面都设置 cullface，当被其他方块包围时，所有面都被剔除
- 这是 Minecraft 性能优化的重要机制

#### 4.5.4 rotation

面级别的纹理旋转：

```json
{
  "rotation": 0    // 0, 90, 180, 270（顺时针）
}
```

| 值 | 效果 |
|----|------|
| `0`（默认） | 不旋转 |
| `90` | 顺时针旋转 90 度 |
| `180` | 旋转 180 度 |
| `270` | 顺时针旋转 270 度（等价于逆时针 90 度） |

#### 4.5.5 tintindex

颜色着色索引，用于与颜色映射系统配合：

```json
{
  "tintindex": 0
}
```

| 值 | 说明 |
|----|------|
| 省略或 `-1` | 不应用颜色着色 |
| `0` | 应用草地/树叶颜色着色（Grass/Leaves Tint） |
| `1` | 应用传送门颜色着色 |
| `2` | 应用水颜色着色 |
| `3+` | 自定义着色（需要 mod 支持） |

**tintindex 0 的工作原理**：
1. Minecraft 读取 `colormap/grass.png` 或 `colormap/foliage.png`
2. 根据方块在世界中的位置确定温度和湿度
3. 从颜色映射图中查找对应的颜色
4. 将查找结果与纹理颜色相乘
5. 最终颜色 = 纹理颜色 × 着色颜色

---

## 5. 显示位置（display）

### 5.1 概述

`display` 字段定义模型在不同显示场景中的变换（旋转、平移、缩放）：

```json
{
  "display": {
    "thirdperson_righthand": {},
    "thirdperson_lefthand": {},
    "firstperson_righthand": {},
    "firstperson_lefthand": {},
    "gui": {},
    "head": {},
    "ground": {},
    "fixed": {}
  }
}
```

### 5.2 显示位置详解

| 位置 | 说明 | 典型应用 |
|------|------|----------|
| `thirdperson_righthand` | 第三人称右手 | 玩家右手持握物品 |
| `thirdperson_lefthand` | 第三人称左手 | 玩家左手持握物品 |
| `firstperson_righthand` | 第一人称右手 | 主视角右手显示 |
| `firstperson_lefthand` | 第一人称左手 | 主视角左手显示 |
| `gui` | GUI 渲染 | 背包、物品栏中的显示 |
| `head` | 头部佩戴 | 头盔、生物头颅 |
| `ground` | 地面掉落物 | 物品掉落在地上 |
| `fixed` | 固定显示 | 展示框中的物品 |

### 5.3 变换参数

每个显示位置可以包含以下变换参数：

```json
{
  "display": {
    "thirdperson_righthand": {
      "rotation": [75, 45, 0],
      "translation": [0, 2.5, 0],
      "scale": [0.375, 0.375, 0.375]
    }
  }
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `rotation` | [x, y, z] | 绕 X、Y、Z 轴旋转的角度（度） |
| `translation` | [x, y, z] | 沿 X、Y、Z 轴的平移量（像素） |
| `scale` | [x, y, z] | X、Y、Z 轴方向的缩放因子 |

**参数约束**：
```
rotation:
  范围: -180 到 180
  步长: 任意（不限于 22.5 的倍数）

translation:
  范围: -80 到 80
  单位: 像素（1像素 = 1/16 方块）

scale:
  范围: -4 到 4
  负值: 翻转
```

### 5.4 典型配置

**物品（工具/武器）**：

```json
{
  "display": {
    "thirdperson_righthand": {
      "rotation": [0, -90, 55],
      "translation": [0, 4, 0.5],
      "scale": [0.85, 0.85, 0.85]
    },
    "thirdperson_lefthand": {
      "rotation": [0, 90, -55],
      "translation": [0, 4, 0.5],
      "scale": [0.85, 0.85, 0.85]
    },
    "firstperson_righthand": {
      "rotation": [0, -90, 25],
      "translation": [1.13, 3.2, 1.13],
      "scale": [0.68, 0.68, 0.68]
    },
    "firstperson_lefthand": {
      "rotation": [0, 90, -25],
      "translation": [1.13, 3.2, 1.13],
      "scale": [0.68, 0.68, 0.68]
    },
    "gui": {
      "rotation": [30, 45, 0],
      "translation": [0, 0, 0],
      "scale": [0.625, 0.625, 0.625]
    },
    "ground": {
      "rotation": [0, 0, 0],
      "translation": [0, 3, 0],
      "scale": [0.25, 0.25, 0.25]
    },
    "fixed": {
      "rotation": [0, 0, 0],
      "translation": [0, 0, 0],
      "scale": [0.5, 0.5, 0.5]
    }
  }
}
```

**方块**：

```json
{
  "display": {
    "gui": {
      "rotation": [30, 45, 0],
      "translation": [0, 0, 0],
      "scale": [0.625, 0.625, 0.625]
    },
    "ground": {
      "rotation": [0, 0, 0],
      "translation": [0, 3, 0],
      "scale": [0.25, 0.25, 0.25]
    },
    "fixed": {
      "rotation": [0, 0, 0],
      "translation": [0, 0, 0],
      "scale": [0.5, 0.5, 0.5]
    },
    "firstperson_righthand": {
      "rotation": [0, 45, 0],
      "translation": [0, 0, 0],
      "scale": [0.4, 0.4, 0.4]
    },
    "firstperson_lefthand": {
      "rotation": [0, 45, 0],
      "translation": [0, 0, 0],
      "scale": [0.4, 0.4, 0.4]
    }
  }
}
```

### 5.5 gui_light

控制物品在 GUI 中的光照效果：

```json
{
  "gui_light": "front"
}
```

| 值 | 效果 |
|----|------|
| `"front"`（默认） | 使用正面光照，物品看起来像是被前方光源照亮 |
| `"side"` | 使用侧面光照，物品看起来有明显的侧面阴影 |

---

## 6. 覆盖系统（overrides）

### 6.1 概述

`overrides` 允许物品根据特定条件使用不同的模型：

```json
{
  "overrides": [
    {
      "predicate": {
        "custom_model_data": 1001
      },
      "model": "mypack:item/custom_sword_1"
    },
    {
      "predicate": {
        "custom_model_data": 1002
      },
      "model": "mypack:item/custom_sword_2"
    }
  ]
}
```

### 6.2 predicate 谓词

谓词定义模型切换的条件。覆盖规则按数组顺序检查，第一个匹配的规则生效。

**custom_model_data**：
```json
{
  "predicate": {
    "custom_model_data": 1001
  },
  "model": "mypack:item/custom_model"
}
```
- 与物品 NBT 中的 `CustomModelData` 整数值匹配
- 是资源包自定义物品模型最常用的方式

**物品耐久度相关**：
```json
{
  "predicate": {
    "damage": 0.5
  },
  "model": "mypack:item/damaged_sword"
}
```
- `damage`：物品损伤程度（0.0 = 完好，1.0 = 完全损坏）

**拉弓进度**：
```json
{
  "predicate": {
    "pulling": 1,
    "pull": 0.65
  },
  "model": "mypack:item/bow_pulling_1"
}
```
- `pulling`：是否正在拉弓（0 或 1）
- `pull`：拉弓进度（0.0 到 1.0）

**其他常用谓词**：

```json
{
  "predicate": {
    "time": 0.5,          // 钟表：时间值
    "angle": 0.25,        // 指南针：角度值
    "level": 3,           // 望远镜：缩放级别
    "filled": 0.8,        // 气泡柱：填充程度
    "cast": 1,            // 钓鱼竿：是否投掷
    "throwing": 1,        // 三叉戟：是否投掷
    "charged": 1,         // 弩：是否装填
    "firework": 1,        // 弩：是否装填烟花
    "pulling": 1,         // 弓：是否拉弓
    "pull": 0.5,          // 弓：拉弓进度
    "blocking": 1,        // 盾牌：是否格挡
    "broken": 0,          // 工具：是否损坏
    "damaged": 0,         // 工具：是否受损
    "lefthanded": 0       // 是否左手
  }
}
```

### 6.3 覆盖规则处理

```python
# 覆盖规则处理逻辑（伪代码）
def resolve_model(base_model, item_stack):
    # overrides 数组按顺序检查
    for override in base_model.overrides:
        if match_predicate(override.predicate, item_stack):
            return override.model  # 返回第一个匹配的模型

    return base_model  # 没有匹配则使用基础模型
```

---

## 7. 继承机制

### 7.1 parent 字段

模型可以通过 `parent` 字段继承另一个模型的所有属性：

```json
{
  "//": "子模型",
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/stone"
  }
}
```

**继承规则**：
1. 子模型可以覆盖父模型的任何属性
2. 子模型可以添加父模型没有的属性
3. 未被子模型覆盖的属性从父模型继承
4. `textures` 对象中的键值对是**合并**而非整体覆盖

### 7.2 继承链

```
继承链示例：
  孙子模型 → 子模型 → 父模型 → 祖先模型

解析过程：
  1. 加载孙子模型
  2. 发现 parent → 加载子模型
  3. 发现 parent → 加载父模型
  4. 发现 parent → 加载祖先模型
  5. 从祖先模型开始，逐级合并属性
  6. 最终返回完全解析的模型
```

### 7.3 内置父模型

Minecraft 提供了一系列内置父模型，可以作为自定义模型的基础：

#### 7.3.1 方块父模型

```json
{
  "//1": "minecraft:block/block - 最基础的空模型，需要完全自定义 elements",

  "//2": "minecraft:block/cube - 六面体模型",
  "//2-detail": "需要定义: down, up, north, south, east, west 纹理",

  "//3": "minecraft:block/cube_column - 柱状方块（如原木）",
  "//3-detail": "需要定义: end (顶/底), side (四个侧面) 纹理",

  "//4": "minecraft:block/cube_all - 六面相同纹理的方块",
  "//4-detail": "需要定义: all 纹理",

  "//5": "minecraft:block/cross - 十字形模型（如花、草）",
  "//5-detail": "需要定义: cross 纹理",

  "//6": "minecraft:block/orientable - 可朝向的方块（如熔炉）",
  "//6-detail": "需要定义: front, side, top 纹理",

  "//7": "minecraft:block/orientable_with_rotation - 可旋转朝向的方块",

  "//8": "minecraft:block/cube_bottom_top - 带特殊底面的方块",
  "//8-detail": "需要定义: bottom, top, side 纹理",

  "//9": "minecraft:block/cube_top - 顶部特殊的方块",
  "//9-detail": "需要定义: top, side 纹理",

  "//10": "minecraft:block/cube_mirrored - 镜像方块",

  "//11": "minecraft:block/leaves - 树叶方块",
  "//11-detail": "需要定义: all 纹理，使用 cutout 渲染类型"
}
```

#### 7.3.2 物品父模型

```json
{
  "//1": "minecraft:item/generated - 自动生成的物品模型",
  "//1-detail": "需要定义: layer0 (可选: layer1, layer2, ...)",
  "//1-usage": "大多数平面物品（如食物、材料）使用此父模型",

  "//2": "minecraft:item/handheld - 手持物品模型",
  "//2-detail": "需要定义: layer0 (可选: layer1, layer2, ...)",
  "//2-usage": "工具和武器使用此父模型（自带手持显示设置）",

  "//3": "minecraft:item/rod - 钓鱼竿类物品",
  "//3-detail": "类似 handheld 但有不同的默认 display 设置"
}
```

### 7.4 继承示例

```json
{
  "//": "层级1: 最基础的空方块模型",
  "parent": "minecraft:block/block",
  "textures": {
    "particle": "#all"
  },
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "down":  { "texture": "#all", "cullface": "down" },
        "up":    { "texture": "#all", "cullface": "up" },
        "north": { "texture": "#all", "cullface": "north" },
        "south": { "texture": "#all", "cullface": "south" },
        "east":  { "texture": "#all", "cullface": "east" },
        "west":  { "texture": "#all", "cullface": "west" }
      }
    }
  ]
}
```

```json
{
  "//": "层级2: cube_all",
  "parent": "minecraft:block/block",
  "textures": {
    "particle": "#all"
  }
}
```

```json
{
  "//": "层级3: 具体方块（stone）",
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/stone"
  }
}
```

**继承链解析结果**：
```
stone
  → cube_all (定义了 elements 和纹理变量结构)
    → block (最基础的空模型)
      → (无 parent，解析完成)

最终模型：
  textures.particle = "minecraft:block/stone"
  textures.all      = "minecraft:block/stone"
  elements[0]       = 标准16x16x16方体
    faces.down.texture  = "minecraft:block/stone"
    faces.up.texture    = "minecraft:block/stone"
    faces.north.texture = "minecraft:block/stone"
    faces.south.texture = "minecraft:block/stone"
    faces.east.texture  = "minecraft:block/stone"
    faces.west.texture  = "minecraft:block/stone"
```

---

## 8. 特殊建模技巧

### 8.1 平面模型（十字形）

用于花朵、草等平面物体：

```json
{
  "parent": "minecraft:block/cross",
  "textures": {
    "cross": "minecraft:block/dandelion"
  }
}
```

cross 父模型的内部定义：
```json
{
  "elements": [
    {
      "from": [0.8, 0, 8],
      "to": [15.2, 16, 8],
      "shade": false,
      "faces": {
        "north": { "uv": [0, 0, 16, 16], "texture": "#cross" },
        "south": { "uv": [0, 0, 16, 16], "texture": "#cross" }
      }
    },
    {
      "from": [8, 0, 0.8],
      "to": [8, 16, 15.2],
      "shade": false,
      "faces": {
        "east": { "uv": [0, 0, 16, 16], "texture": "#cross" },
        "west": { "uv": [0, 0, 16, 16], "texture": "#cross" }
      }
    }
  ]
}
```

### 8.2 多部件方块

```json
{
  "parent": "minecraft:block/block",
  "textures": {
    "bottom": "minecraft:block/smoker_bottom",
    "top": "minecraft:block/smoker_top",
    "front": "minecraft:block/smoker_front",
    "side": "minecraft:block/smoker_side"
  },
  "elements": [
    {
      "name": "body",
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "down":  { "texture": "#bottom", "cullface": "down" },
        "up":    { "texture": "#top",    "cullface": "up" },
        "north": { "texture": "#front",  "cullface": "north" },
        "south": { "texture": "#side",   "cullface": "south" },
        "east":  { "texture": "#side",   "cullface": "east" },
        "west":  { "texture": "#side",   "cullface": "west" }
      }
    },
    {
      "name": "chimney",
      "from": [4, 16, 4],
      "to": [12, 20, 12],
      "faces": {
        "down":  { "texture": "#top" },
        "up":    { "texture": "#top" },
        "north": { "texture": "#side" },
        "south": { "texture": "#side" },
        "east":  { "texture": "#side" },
        "west":  { "texture": "#side" }
      }
    }
  ]
}
```

### 8.3 部分透明方块

```json
{
  "parent": "minecraft:block/block",
  "textures": {
    "glass": "minecraft:block/glass"
  },
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "north": { "texture": "#glass", "cullface": "north" },
        "south": { "texture": "#glass", "cullface": "south" },
        "east":  { "texture": "#glass", "cullface": "east" },
        "west":  { "texture": "#glass", "cullface": "west" },
        "up":    { "texture": "#glass", "cullface": "up" },
        "down":  { "texture": "#glass", "cullface": "down" }
      }
    }
  ]
}
```

### 8.4 带颜色着色的方块

```json
{
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/grass_block_top"
  },
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "up": { "texture": "#all", "tintindex": 0, "cullface": "up" },
        "down": { "texture": "#all", "cullface": "down" },
        "north": { "texture": "#all", "cullface": "north" },
        "south": { "texture": "#all", "cullface": "south" },
        "east": { "texture": "#all", "cullface": "east" },
        "west": { "texture": "#all", "cullface": "west" }
      }
    }
  ]
}
```

### 8.5 旋转元素

```json
{
  "parent": "minecraft:block/block",
  "textures": {
    "torch": "minecraft:block/torch"
  },
  "elements": [
    {
      "from": [7, 0, 7],
      "to": [9, 10, 9],
      "rotation": {
        "origin": [8, 8, 8],
        "axis": "z",
        "angle": -6,
        "rescale": true
      },
      "shade": false,
      "faces": {
        "north": { "uv": [7, 3, 9, 13], "texture": "#torch" },
        "south": { "uv": [7, 3, 9, 13], "texture": "#torch" },
        "west":  { "uv": [7, 3, 9, 13], "texture": "#torch" },
        "east":  { "uv": [7, 3, 9, 13], "texture": "#torch" }
      }
    }
  ]
}
```

---

## 9. 验证方法

### 9.1 JSON 语法验证

使用在线工具或命令行验证 JSON 语法：

```bash
# 使用 Python 验证
python -c "import json; json.load(open('model.json'))"

# 使用 Node.js 验证
node -e "JSON.parse(require('fs').readFileSync('model.json'))"

# 使用 jq 验证
jq empty model.json
```

### 9.2 模型结构验证

```python
# 模型验证检查清单
validation_checklist = {
    "from_to": [
        "from 的每个分量 < to 的对应分量",
        "差值绝对值 >= 0.001",
        "差值绝对值 <= 16",
        "所有坐标值在 -16 到 32 之间",
    ],
    "rotation": [
        "angle 只能是 -45, -22.5, 0, 22.5, 45",
        "axis 只能是 'x', 'y', 'z'",
        "origin 的每个分量在 -16 到 32 之间",
    ],
    "uv": [
        "u1 < u2, v1 < v2",
        "值在 0 到 16 之间",
    ],
    "display": [
        "rotation 各分量在 -180 到 180 之间",
        "translation 各分量在 -80 到 80 之间",
        "scale 各分量在 -4 到 4 之间",
    ],
    "textures": [
        "所有引用的变量（#xxx）都有定义",
        "纹理路径格式正确",
    ],
}
```

### 9.3 常见错误排查

```json
{
  "// 错误1: 循环继承",
  "// 症状: 游戏启动时崩溃或模型不显示",
  "parent": "mymodel"  // 如果 mymodel 的 parent 又指向自己

  "// 错误2: 缺少纹理变量",
  "// 症状: 紫黑棋盘格",
  "textures": {},  // 父模型需要 #all 但未提供

  "// 错误3: 非法的 UV 坐标",
  "// 症状: 纹理扭曲",
  "uv": [0, 0, 32, 32]  // 超出 0-16 范围

  "// 错误4: 非法的旋转角度",
  "// 症状: 模型不显示或控制台报错",
  "angle": 30  // 只能是 -45, -22.5, 0, 22.5, 45
}
```

---

## 10. 完整示例

### 10.1 自定义方块模型

```json
{
  "parent": "minecraft:block/block",
  "textures": {
    "particle": "mypack:block/custom_block",
    "top": "mypack:block/custom_block_top",
    "bottom": "mypack:block/custom_block_bottom",
    "side": "mypack:block/custom_block_side",
    "front": "mypack:block/custom_block_front",
    "decoration": "mypack:block/custom_block_decoration"
  },
  "elements": [
    {
      "name": "base",
      "from": [0, 0, 0],
      "to": [16, 12, 16],
      "faces": {
        "down":  { "uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down" },
        "up":    { "uv": [0, 0, 16, 16], "texture": "#top" },
        "north": { "uv": [0, 4, 16, 16], "texture": "#front", "cullface": "north" },
        "south": { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "south" },
        "east":  { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "east" },
        "west":  { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "west" }
      }
    },
    {
      "name": "pillar",
      "from": [4, 12, 4],
      "to": [12, 16, 12],
      "faces": {
        "up":    { "uv": [4, 4, 12, 12], "texture": "#top" },
        "north": { "uv": [4, 0, 12, 4], "texture": "#side" },
        "south": { "uv": [4, 0, 12, 4], "texture": "#side" },
        "east":  { "uv": [4, 0, 12, 4], "texture": "#side" },
        "west":  { "uv": [4, 0, 12, 4], "texture": "#side" }
      }
    },
    {
      "name": "decoration_north",
      "from": [3, 4, 0],
      "to": [13, 12, 0.5],
      "faces": {
        "north": { "uv": [3, 4, 13, 12], "texture": "#decoration" },
        "south": { "uv": [3, 4, 13, 12], "texture": "#decoration" }
      }
    }
  ],
  "display": {
    "gui": {
      "rotation": [30, 45, 0],
      "translation": [0, 0, 0],
      "scale": [0.625, 0.625, 0.625]
    },
    "ground": {
      "rotation": [0, 0, 0],
      "translation": [0, 3, 0],
      "scale": [0.25, 0.25, 0.25]
    },
    "fixed": {
      "rotation": [0, 0, 0],
      "translation": [0, 0, 0],
      "scale": [0.5, 0.5, 0.5]
    }
  }
}
```

### 10.2 自定义物品模型（带覆盖）

```json
{
  "parent": "minecraft:item/handheld",
  "textures": {
    "layer0": "mypack:item/magic_wand"
  },
  "display": {
    "thirdperson_righthand": {
      "rotation": [0, -90, 55],
      "translation": [0, 4, 0.5],
      "scale": [0.85, 0.85, 0.85]
    },
    "firstperson_righthand": {
      "rotation": [0, -90, 25],
      "translation": [1.13, 3.2, 1.13],
      "scale": [0.68, 0.68, 0.68]
    },
    "gui": {
      "rotation": [30, 45, 0],
      "translation": [0, 0, 0],
      "scale": [1, 1, 1]
    }
  },
  "overrides": [
    {
      "predicate": { "custom_model_data": 1001 },
      "model": "mypack:item/magic_wand_fire"
    },
    {
      "predicate": { "custom_model_data": 1002 },
      "model": "mypack:item/magic_wand_ice"
    },
    {
      "predicate": { "custom_model_data": 1003 },
      "model": "mypack:item/magic_wand_lightning"
    }
  ]
}
```

---

## 附录：内置父模型速查表

| 父模型路径 | 用途 | 必需纹理变量 |
|------------|------|--------------|
| `minecraft:block/block` | 基础空方块 | 无（需自定义 elements） |
| `minecraft:block/cube` | 标准六面体 | down, up, north, south, east, west |
| `minecraft:block/cube_all` | 六面相同纹理 | all |
| `minecraft:block/cube_column` | 柱状方块 | end, side |
| `minecraft:block/cube_bottom_top` | 顶底侧面 | bottom, top, side |
| `minecraft:block/cube_top` | 特殊顶部 | top, side |
| `minecraft:block/orientable` | 可朝向方块 | front, side, top |
| `minecraft:block/orientable_with_rotation` | 可旋转朝向 | front, side, top |
| `minecraft:block/cross` | 十字形 | cross |
| `minecraft:block/tinted_cross` | 带着色十字 | cross |
| `minecraft:block/leaves` | 树叶 | all |
| `minecraft:block/slab` | 半砖 | bottom, top, side |
| `minecraft:block/slab_top` | 上半砖 | bottom, top, side |
| `minecraft:block/stairs` | 楼梯 | bottom, top, side |
| `minecraft:block/inner_stairs` | 内角楼梯 | bottom, top, side |
| `minecraft:block/outer_stairs` | 外角楼梯 | bottom, top, side |
| `minecraft:block/rotatable_block` | 可旋转方块 | front, side, top, bottom |
| `minecraft:item/generated` | 生成物品 | layer0 |
| `minecraft:item/handheld` | 手持物品 | layer0 |
| `minecraft:item/rod` | 钓竿物品 | layer0 |

---

*本文档最后更新于：2026年5月*
