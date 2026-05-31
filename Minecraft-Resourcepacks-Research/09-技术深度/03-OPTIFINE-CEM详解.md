# OptiFine CEM 自定义实体模型详解

## 概述

CEM（Custom Entity Models）是 OptiFine 提供的一项强大功能，允许资源包开发者完全自定义 Minecraft 中实体的3D模型。通过 CEM，你可以修改任何实体的外观，添加新的部件、修改骨骼层级、应用动画表达式，而无需编写任何代码或使用模组加载器。

本文档全面介绍 CEM 系统的技术规格，包括 .jem 和 .jpm 文件格式、实体模型层级结构、动画API、常见实体修改实例以及工具链使用。

---

## 1. CEM 概述

### 1.1 CEM 的能力

```
CEM 可以做到：
  ✅ 替换实体的整个模型
  ✅ 修改现有模型部件（位置、旋转、缩放）
  ✅ 添加新的模型部件
  ✅ 添加动画表达式（使用动画API）
  ✅ 为不同部件使用不同纹理
  ✅ 修改模型部件的镜像属性
  ✅ 调整阴影大小和类型
  ✅ 为不同变体（如不同颜色的猫）使用不同模型
  ✅ 支持几乎所有原版实体

CEM 不能做到：
  ❌ 添加全新的实体类型
  ❌ 修改实体的碰撞箱
  ❌ 修改实体的 AI 行为
  ❌ 添加自定义粒子效果（需要 CIT/CPS）
  ❌ 超出原版骨骼层级的完全自定义骨骼系统
```

### 1.2 文件结构

```
assets/minecraft/optifine/
├── cem/                            # CEM 模型目录
│   ├── zombie.jem                  # 僵尸模型定义
│   ├── creeper.jem                 # 苦力怕模型定义
│   ├── villager.jem                # 村民模型定义
│   ├── enderman.jem                # 末影人模型定义
│   └── chest.jem                   # 箱子模型定义
├── cem/<entity>/                   # 复杂实体的子目录
│   ├── cat.jem                     # 猫模型
│   ├── cat_black.jpm               # 猫的部件文件
│   └── cat_collar.jpm              # 猫项圈部件
└── textures/                       # 自定义纹理
    └── entity/
        ├── zombie.png              # 自定义僵尸纹理
        └── creeper.png             # 自定义苦力怕纹理
```

---

## 2. .jem 文件格式

### 2.1 文件概述

`.jem`（JSON Entity Model）文件是 CEM 系统的核心配置文件，定义了实体模型的完整结构。

**文件命名**：必须与原版实体的注册名一致（小写）。

```
实体名称             → JEM 文件名
Zombie              → zombie.jem
Creeper             → creeper.jem
Villager            → villager.jem
Enderman            → enderman.jem
Cat                 → cat.jem
Wolf                → wolf.jem
Horse               → horse.jem
Chest               → chest.jem
```

### 2.2 完整 .jem 格式

```json
{
  "texture": "entity/zombie",
  "textureSize": [64, 64],
  "shadowSize": 0.5,
  "shadow": 1.0,
  "scale": 1.0,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, 0, 0],
      "rotate": [0, 0, 0],
      "scale": 1.0,
      "size": [8, 8, 8],
      "textureOffset": [0, 0],
      "textureSize": [64, 64],
      "mirror": false,
      "submodel": {
        "hat": {
          "size": [8, 8, 8],
          "textureOffset": [32, 0],
          "inflate": 0.5
        }
      }
    }
  ]
}
```

### 2.3 顶层属性详解

#### 2.3.1 texture

```json
{
  "texture": "entity/zombie"
}
```

- **类型**：string
- **必需**：否（默认使用原版纹理）
- **说明**：模型使用的默认纹理路径
- **路径格式**：相对于 `assets/minecraft/textures/`，不包含 `.png` 后缀
- **示例**：`"entity/zombie"` → `assets/minecraft/textures/entity/zombie.png`

#### 2.3.2 textureSize

```json
{
  "textureSize": [64, 64]
}
```

- **类型**：[width, height]
- **必需**：否（默认 [64, 64]）
- **说明**：纹理文件的尺寸（像素），用于自动计算 UV 坐标
- **注意**：如果纹理是高清版本（如 256x256），必须设置此值

#### 2.3.3 shadowSize

```json
{
  "shadowSize": 0.5
}
```

- **类型**：number
- **必需**：否（默认 0.5）
- **说明**：实体投影到地面的阴影大小
- **范围**：0.0（无阴影）到 1.0+（更大阴影）

#### 2.3.4 shadow

```json
{
  "shadow": 1.0
}
```

- **类型**：number
- **必需**：否（默认 1.0）
- **说明**：阴影的透明度/强度
- **范围**：0.0（完全透明）到 1.0（完全不透明）

#### 2.3.5 scale

```json
{
  "scale": 1.0
}
```

- **类型**：number
- **必需**：否（默认 1.0）
- **说明**：整个模型的全局缩放因子
- **注意**：这是整体缩放，不影响单个部件的缩放

---

## 3. 模型部件（models/part）

### 3.1 models 数组

`models` 数组定义实体的所有模型部件。每个部件对应原版实体模型中的一个 ModelPart。

```json
{
  "models": [
    { "part": "head", ... },
    { "part": "body", ... },
    { "part": "right_arm", ... },
    { "part": "left_arm", ... },
    { "part": "right_leg", ... },
    { "part": "left_leg", ... }
  ]
}
```

### 3.2 part 名称

`part` 字段指定该部件对应原版模型的哪个部分。名称必须与实体的 ModelPart 注册名一致。

**常见实体的 part 名称**：

```python
# 人形实体（僵尸、骷髅、村民等）
humanoid_parts = {
    "head": "头部",
    "body": "身体",
    "right_arm": "右臂",
    "left_arm": "左臂",
    "right_leg": "右腿",
    "left_leg": "左腿",
    "hat": "帽子层（如果存在）",
}

# 苦力怕
creeper_parts = {
    "head": "头部",
    "body": "身体",
    "leg1": "右前腿",
    "leg2": "左前腿",
    "leg3": "右后腿",
    "leg4": "左后腿",
}

# 蜘蛛
spider_parts = {
    "head0": "头部",
    "neck": "颈部",
    "body0": "前体",
    "body1": "后体",
    "leg0": "右前腿",
    "leg1": "左前腿",
    "leg2": "右中前腿",
    "leg3": "左中前腿",
    "leg4": "右中后腿",
    "leg5": "左中后腿",
    "leg6": "右后腿",
    "leg7": "左后腿",
}

# 马
horse_parts = {
    "head": "头部",
    "upper_mouth": "上颚",
    "lower_mouth": "下颚",
    "body": "身体",
    "tail": "尾巴",
    "leg1a": "右前腿上段",
    "leg1b": "右前腿下段",
    "leg2a": "左前腿上段",
    "leg2b": "左前腿下段",
    "leg3a": "右后腿上段",
    "leg3b": "右后腿下段",
    "leg4a": "左后腿上段",
    "leg4b": "左后腿下段",
    "saddle": "鞍",
    "saddle_mouth": "鞍口套",
    "saddle_line": "鞍线",
    "mane": "鬃毛",
    "ear": "耳朵",
}
```

### 3.3 id

```json
{
  "id": "head_custom"
}
```

- **类型**：string
- **必需**：否
- **说明**：部件的唯一标识符，用于在 submodel 引用时标识此部件
- **默认**：如果不指定，使用 `part` 的值

### 3.4 attach

```json
{
  "attach": true
}
```

- **类型**：boolean
- **必需**：否（默认 false）
- **说明**：
  - `false`：替换原版部件
  - `true`：附加到原版部件上（保留原版部件，同时添加此部件）

**使用场景**：
```json
{
  "//1": "替换头部 - 将 attach 设为 false 或省略",
  "part": "head",
  "attach": false,
  "size": [8, 8, 8],
  "textureOffset": [0, 0]
}

{
  "//2": "添加角 - 保留原版头部，额外添加角",
  "part": "head",
  "attach": true,
  "id": "horns",
  "size": [2, 6, 2],
  "textureOffset": [56, 0],
  "translate": [-3, -8, -1]
}
```

### 3.5 invertAxis

```json
{
  "invertAxis": "xy"
}
```

- **类型**：string
- **必需**：否（默认 ""）
- **说明**：反转指定轴的方向
- **可选值**：`""`, `"x"`, `"y"`, `"xy"`, `"xz"`, `"yz"`, `"xyz"`
- **注意**：Minecraft 的坐标系统和模型编辑器的坐标系统可能不同，invertAxis 用于修正差异

**坐标系说明**：
```
Minecraft 游戏坐标系：
  X: 向东
  Y: 向上
  Z: 向南

Minecraft 模型内部坐标系：
  X: 向右
  Y: 向上
  Z: 向前

大多数模型编辑器坐标系：
  X: 向右
  Y: 向上
  Z: 向外（远离观察者）

通常需要 "xy" 来匹配模型编辑器的坐标系
```

### 3.6 translate

```json
{
  "translate": [0, -24, 0]
}
```

- **类型**：[x, y, z]
- **必需**：否（默认 [0, 0, 0]）
- **说明**：部件相对于其父部件的位移（像素）
- **坐标系**：受 invertAxis 影响

### 3.7 rotate

```json
{
  "rotate": [0, 45, 0]
}
```

- **类型**：[x, y, z]
- **必需**：否（默认 [0, 0, 0]）
- **说明**：部件的初始旋转角度（度）
- **注意**：这是静态旋转，不包括动画旋转

### 3.8 scale

```json
{
  "scale": 1.0
}
```

- **类型**：number
- **必需**：否（默认 1.0）
- **说明**：部件的缩放因子
- **注意**：这是部件级别的缩放，独立于顶层的全局 scale

### 3.9 size

```json
{
  "size": [8, 8, 8]
}
```

- **类型**：[width, height, depth]
- **必需**：是（除非使用 attach=true 且不修改几何体）
- **说明**：长方体部件的尺寸（像素）
- **注意**：尺寸为 [0, 0, 0] 时部件不可见，但可以作为子模型的父节点

### 3.10 textureOffset

```json
{
  "textureOffset": [0, 0]
}
```

- **类型**：[u, v]
- **必需**：是（除非 size 为 [0, 0, 0]）
- **说明**：纹理中该部件 UV 映射的起始偏移（像素）
- **注意**：这是纹理上的绝对像素坐标，不是 0-16 的相对坐标

### 3.11 textureSize

```json
{
  "textureSize": [64, 64]
}
```

- **类型**：[width, height]
- **必需**：否（默认使用顶层的 textureSize）
- **说明**：为该部件单独指定纹理尺寸
- **使用场景**：不同部件使用不同尺寸的纹理

### 3.12 mirror

```json
{
  "mirror": false
}
```

- **类型**：boolean
- **必需**：否（默认 false）
- **说明**：是否在 X 轴上镜像部件
- **效果**：镜像后纹理也会水平翻转

### 3.13 inflate

```json
{
  "inflate": 0.5
}
```

- **类型**：number
- **必需**：否（默认 0.0）
- **说明**：部件的膨胀值，使部件在所有方向上扩大指定的像素数
- **使用场景**：帽子层、盔甲层等需要比主体稍大的部件
- **效果**：size 会变为 [width+2*inflate, height+2*inflate, depth+2*inflate]

---

## 4. 子模型（submodel）

### 4.1 基本语法

子模型附加到父部件上，跟随父部件移动和旋转：

```json
{
  "models": [
    {
      "part": "head",
      "size": [8, 8, 8],
      "textureOffset": [0, 0],
      "submodel": {
        "left_horn": {
          "size": [2, 6, 2],
          "textureOffset": [56, 0],
          "translate": [-3, -8, -1],
          "rotate": [0, 0, -15]
        },
        "right_horn": {
          "size": [2, 6, 2],
          "textureOffset": [56, 12],
          "translate": [9, -8, -1],
          "rotate": [0, 0, 15]
        }
      }
    }
  ]
}
```

### 4.2 子模型的属性

子模型支持与顶级模型相同的大部分属性：

```json
{
  "submodel": {
    "name": {
      "id": "unique_id",
      "invertAxis": "xy",
      "translate": [0, 0, 0],
      "rotate": [0, 0, 0],
      "scale": 1.0,
      "size": [8, 8, 8],
      "textureOffset": [0, 0],
      "textureSize": [64, 64],
      "mirror": false,
      "inflate": 0.0,
      "submodel": { ... }  // 子模型可以嵌套
    }
  }
}
```

### 4.3 嵌套子模型

子模型可以无限嵌套，形成骨骼层级结构：

```json
{
  "models": [
    {
      "part": "body",
      "size": [8, 12, 4],
      "textureOffset": [16, 16],
      "submodel": {
        "tail_base": {
          "size": [4, 6, 4],
          "textureOffset": [0, 0],
          "translate": [2, 10, -2],
          "rotate": [-45, 0, 0],
          "submodel": {
            "tail_tip": {
              "size": [2, 4, 2],
              "textureOffset": [0, 10],
              "translate": [1, 5, 1],
              "rotate": [-20, 0, 0]
            }
          }
        }
      }
    }
  ]
}
```

---

## 5. 实体模型层级结构

### 5.1 理解骨骼层级

Minecraft 的实体模型使用层级结构（骨骼系统），子部件跟随父部件运动：

```
层级结构示例（人形实体）：
  root
  ├── body (身体)
  │   ├── right_arm (右臂)
  │   │   └── [submodel: 盾牌/物品]
  │   └── left_arm (左臂)
  │       └── [submodel: 副手物品]
  ├── head (头部)
  │   ├── hat (帽子层)
  │   └── [submodel: 头盔装饰]
  ├── right_leg (右腿)
  │   └── right_boot (右靴)
  └── left_leg (左腿)
      └── left_boot (左靴)
```

### 5.2 常见实体的部件层级

**猫（Cat）**：
```
cat.jem
├── head (头部)
│   ├── left_ear (左耳)
│   └── right_ear (右耳)
├── body (身体)
│   └── tail (尾巴)
│       └── tail_tip (尾尖)
├── leg1 (右前腿)
├── leg2 (左前腿)
├── leg3 (右后腿)
├── leg4 (左后腿)
└── collar (项圈 - 仅驯服后可见)
```

**狼（Wolf）**：
```
wolf.jem
├── head (头部)
│   ├── left_ear (左耳)
│   ├── right_ear (右耳)
│   └── muzzle (口鼻)
├── body (身体)
├── leg1 (右前腿)
├── leg2 (左前腿)
├── leg3 (右后腿)
├── leg4 (左后腿)
└── tail (尾巴)
    └── [子模型: 尾尖]
```

**马（Horse）**：
```
horse.jem
├── head (头部)
│   ├── ear (耳朵)
│   ├── upper_mouth (上颚)
│   └── lower_mouth (下颚)
├── body (身体)
├── mane (鬃毛)
├── tail (尾巴)
├── leg1a (右前腿上段)
│   └── leg1b (右前腿下段)
├── leg2a (左前腿上段)
│   └── leg2b (左前腿下段)
├── leg3a (右后腿上段)
│   └── leg3b (右后腿下段)
├── leg4a (左后腿上段)
│   └── leg4b (左后腿下段)
├── saddle (鞍)
├── saddle_mouth (鞍口套)
└── saddle_line (鞍线)
```

**末影龙（Ender Dragon）**：
```
dragon.jem
├── head (头部)
│   ├── jaw (下颚)
│   └── neck (颈部)
├── spine (脊柱)
├── body (身体)
├── left_wing (左翼)
│   ├── left_wing_tip (左翼尖)
│   └── left_wing_membrane (左翼膜)
├── right_wing (右翼)
│   ├── right_wing_tip (右翼尖)
│   └── right_wing_membrane (右翼膜)
├── tail1 (尾巴1)
│   └── tail2 (尾巴2)
│       └── tail3 (尾巴3)
└── [其他子部件]
```

---

## 6. 动画 API

### 6.1 动画表达式概述

CEM 动画允许你使用数学表达式控制部件的位置、旋转和缩放。表达式在每个游戏帧（约 20fps）求值。

**语法**：
```json
{
  "models": [
    {
      "part": "head",
      "rotate": [
        "-Math.sin(ageInTicks * 0.1) * 10",
        "headYaw",
        0
      ]
    }
  ]
}
```

表达式支持字符串形式的数学表达式或直接的数值。

### 6.2 可用变量

#### 6.2.1 移动相关变量

```javascript
// limbSwing - 腿部摆动的累计值
// 类型: float
// 范围: 持续递增，用于腿部摆动动画
// 用途: 腿部、手臂的行走摆动
"limbSwing"

// limbSwingAmount - 腿部摆动的幅度
// 类型: float
// 范围: 0 (静止) 到 ~1 (快速移动)
// 用途: 控制行走动画的强度
"limbSwingAmount"

// moveForward - 实体向前移动的速度
// 类型: float
// 正值: 向前移动
// 负值: 向后移动
// 0: 静止
"moveForward"

// moveStrafing - 实体横向移动的速度
// 类型: float
// 正值: 向左移动
// 负值: 向右移动
"moveStrafing"
```

#### 6.2.2 视角相关变量

```javascript
// headYaw - 头部水平旋转角度
// 类型: float
// 范围: -180 到 180 (度)
// 用途: 头部跟随鼠标水平旋转
"headYaw"

// headPitch - 头部垂直旋转角度
// 类型: float
// 范围: -90 到 90 (度)
// 正值: 向下看
// 负值: 向上看
"headPitch"
```

#### 6.2.3 时间相关变量

```javascript
// ageInTicks - 实体存在的总游戏刻数
// 类型: float
// 范围: 0 到 持续递增
// 用途: 创建循环动画（配合 sin/cos 使用）
// 注意: 1 秒 = 20 刻
"ageInTicks"

// frameTime - 当前帧时间（增量时间）
// 类型: float
// 用途: 帧率无关的动画
"frameTime"

// dayTime - 游戏内时间（天内刻数）
// 类型: float
// 范围: 0 到 24000
// 用途: 日夜相关动画
"dayTime"
```

#### 6.2.4 生命值相关变量

```javascript
// health - 实体当前生命值
// 类型: float
// 范围: 0 到 maxHealth
"health"

// maxHealth - 实体最大生命值
// 类型: float
// 示例: 村民=20, 僵尸=20, 末影龙=200
"maxHealth"

// healthFraction - 生命值百分比
// 类型: float
// 范围: 0.0 到 1.0
"healthFraction"
```

#### 6.2.5 状态变量

```javascript
// isChild - 是否为幼年实体
// 类型: boolean (在表达式中作为 0 或 1)
// 用途: 调整幼年实体的模型比例
"isChild"

// isAggressive - 是否处于攻击状态
// 类型: boolean (0 或 1)
// 用途: 攻击时的视觉反馈
"isAggressive"

// isAlive - 是否存活
// 类型: boolean (0 或 1)
"isAlive"

// isRidden - 是否被骑乘
// 类型: boolean (0 或 1)
"isRidden"

// isRiding - 是否正在骑乘
// 类型: boolean (0 或 1)
"isRiding"

// isInWater - 是否在水中
// 类型: boolean (0 或 1)
// 用途: 水中游泳动画
"isInWater"

// isOnGround - 是否在地面上
// 类型: boolean (0 或 1)
"isOnGround"

// isInLava - 是否在岩浆中
// 类型: boolean (0 或 1)
"isInLava"

// isSneaking - 是否潜行
// 类型: boolean (0 或 1)
"isSneaking"

// isSprinting - 是否疾跑
// 类型: boolean (0 或 1)
"isSprinting"

// isGlowing - 是否发光（被标亮）
// 类型: boolean (0 或 1)
"isGlowing"

// isHoldingItem - 是否手持物品
// 类型: boolean (0 或 1)
"isHoldingItem"

// isHurt - 是否受伤
// 类型: boolean (0 或 1)
// 用途: 受伤闪烁效果
"isHurt"
```

#### 6.2.6 其他变量

```javascript
// limbAngle - 肢体角度
// 类型: float
// 说明: 由 limbSwing 和 limbSwingAmount 计算得出
"limbAngle"

// limbDistance - 肢体距离
// 类型: float
"limbDistance"

// uniqueSeed - 每个实体的唯一随机种子
// 类型: float
// 用途: 为不同实体创建变化
"uniqueSeed"

// modelScale - 模型缩放值
// 类型: float
"modelScale"
```

### 6.3 数学函数

CEM 表达式支持以下数学函数：

```javascript
// 三角函数
Math.sin(x)      // 正弦函数，x 为弧度
Math.cos(x)      // 余弦函数，x 为弧度
Math.tan(x)      // 正切函数
Math.asin(x)     // 反正弦
Math.acos(x)     // 反余弦
Math.atan(x)     // 反正切
Math.atan2(y, x) // 二参数反正切

// 绝对值
Math.abs(x)      // 绝对值

// 取整
Math.ceil(x)     // 向上取整
Math.floor(x)    // 向下取整
Math.round(x)    // 四舍五入

// 极值
Math.min(a, b)   // 最小值
Math.max(a, b)   // 最大值

// 幂运算
Math.pow(x, y)   // x 的 y 次方
Math.sqrt(x)     // 平方根
Math.exp(x)      // e 的 x 次方
Math.log(x)      // 自然对数

// 常量
Math.PI          // 圆周率 (3.14159...)
Math.E           // 自然常数 (2.71828...)

// 角度转换（需要手动计算）
// 弧度转角度: 弧度 * (180 / Math.PI)
// 角度转弧度: 角度 * (Math.PI / 180)
```

### 6.4 运算符

```javascript
// 算术运算符
+    // 加法
-    // 减法（也用于取负）
*    // 乘法
/    // 除法
%    // 取模（求余）

// 比较运算符
==   // 等于
!=   // 不等于
<    // 小于
>    // 大于
<=   // 小于等于
>=   // 大于等于

// 逻辑运算符
&&   // 逻辑与
||   // 逻辑或
!    // 逻辑非

// 条件运算符（三元运算符）
? :  // 条件 ? 值1 : 值2
```

### 6.5 动画表达式示例

```json
{
  "//": "头部上下点头动画",
  "rotate": [
    "Math.sin(ageInTicks * 0.05) * 5",
    0,
    0
  ]
}

{
  "//": "部件随行走摆动",
  "rotate": [
    "Math.cos(limbSwing * 0.6662) * limbSwingAmount * 1.4 * (180 / Math.PI)",
    0,
    0
  ]
}

{
  "//": "根据生命值调整缩放",
  "scale": "0.5 + (health / maxHealth) * 0.5"
}

{
  "//": "游泳时的摆动",
  "rotate": [
    "isInWater ? Math.sin(ageInTicks * 0.2) * 30 : 0",
    0,
    "isInWater ? Math.sin(ageInTicks * 0.15) * 20 : 0"
  ]
}

{
  "//": "根据头部朝向旋转",
  "rotate": [
    "-headPitch",
    "headYaw",
    0
  ]
}

{
  "//": "呼吸效果（缓慢缩放）",
  "scale": "1.0 + Math.sin(ageInTicks * 0.03) * 0.05"
}

{
  "//": "攻击时的手臂动画",
  "rotate": [
    "isAggressive ? -90 + Math.sin(ageInTicks * 0.4) * 10 : 0",
    0,
    0
  ]
}

{
  "//": "幼年实体放大头部",
  "scale": "isChild ? 1.5 : 1.0",
  "translate": [0, "isChild ? -4 : 0", 0]
}
```

---

## 7. .jpm 部件文件

### 7.1 概述

`.jpm`（JSON Part Model）文件允许将复杂的模型拆分为多个文件，便于管理和复用。

### 7.2 基本格式

```json
{
  "texture": "entity/cat/cat",
  "textureSize": [64, 32],
  "invertAxis": "xy",
  "models": [
    {
      "part": "head",
      "id": "cat_head",
      "size": [6, 6, 6],
      "textureOffset": [0, 0],
      "translate": [0, 9, -4]
    }
  ]
}
```

### 7.3 引用 .jpm 文件

在 .jem 文件中通过路径引用 .jpm 文件：

```json
{
  "models": [
    "cem/cat_head.jpm",     // 引用 .jpm 文件
    {
      "part": "body",         // 内联定义
      "size": [10, 7, 6],
      "textureOffset": [20, 0]
    }
  ]
}
```

### 7.4 变体支持

.jpm 文件支持变体（variants），允许同一个部件有多个版本：

```json
{
  "variants": {
    "black": {
      "texture": "entity/cat/cat_black",
      "textureSize": [64, 32],
      "invertAxis": "xy",
      "models": [
        {
          "part": "head",
          "size": [6, 6, 6],
          "textureOffset": [0, 0]
        }
      ]
    },
    "tabby": {
      "texture": "entity/cat/cat_tabby",
      "textureSize": [64, 32],
      "invertAxis": "xy",
      "models": [
        {
          "part": "head",
          "size": [6, 6, 6],
          "textureOffset": [0, 0]
        }
      ]
    }
  }
}
```

**变体选择机制**：
- Minecraft 根据实体的数据确定使用哪个变体
- 对于猫：根据 CatVariant 数据选择
- 对于狼：根据 WolfVariant 数据选择
- 对于马：根据 Markings 和 Color 数据选择

---

## 8. 常见实体修改实例

### 8.1 村民（Villager）

```json
{
  "texture": "entity/villager/villager",
  "textureSize": [64, 64],
  "shadowSize": 0.5,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, -24, 0],
      "size": [8, 10, 8],
      "textureOffset": [0, 0]
    },
    {
      "part": "head",
      "id": "hat_rim",
      "attach": true,
      "invertAxis": "xy",
      "translate": [-4, -30, -4],
      "size": [16, 2, 16],
      "textureOffset": [30, 0]
    },
    {
      "part": "body",
      "id": "body",
      "invertAxis": "xy",
      "translate": [0, -24, 0],
      "size": [8, 12, 4],
      "textureOffset": [16, 20]
    },
    {
      "part": "right_arm",
      "id": "right_arm",
      "invertAxis": "xy",
      "translate": [-12, -24, 0],
      "size": [4, 12, 4],
      "textureOffset": [44, 38]
    },
    {
      "part": "left_arm",
      "id": "left_arm",
      "invertAxis": "xy",
      "translate": [8, -24, 0],
      "size": [4, 12, 4],
      "textureOffset": [44, 38],
      "mirror": true
    },
    {
      "part": "right_leg",
      "id": "right_leg",
      "invertAxis": "xy",
      "translate": [-4, -12, 0],
      "size": [4, 12, 4],
      "textureOffset": [0, 38]
    },
    {
      "part": "left_leg",
      "id": "left_leg",
      "invertAxis": "xy",
      "translate": [4, -12, 0],
      "size": [4, 12, 4],
      "textureOffset": [0, 38],
      "mirror": true
    },
    {
      "part": "nose",
      "id": "nose",
      "invertAxis": "xy",
      "translate": [-1, -26, -4],
      "size": [2, 4, 2],
      "textureOffset": [24, 2]
    }
  ]
}
```

### 8.2 猫（Cat）

```json
{
  "texture": "entity/cat/cat",
  "textureSize": [64, 32],
  "shadowSize": 0.4,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, -9, -4],
      "size": [6, 6, 6],
      "textureOffset": [0, 0],
      "submodel": {
        "left_ear": {
          "size": [2, 2, 1],
          "textureOffset": [1, 0],
          "translate": [0, -2, 0],
          "rotate": [0, 0, 15]
        },
        "right_ear": {
          "size": [2, 2, 1],
          "textureOffset": [5, 0],
          "translate": [4, -2, 0],
          "rotate": [0, 0, -15]
        }
      }
    },
    {
      "part": "body",
      "id": "body",
      "invertAxis": "xy",
      "translate": [0, -7, 0],
      "rotate": ["90 * (Math.PI / 180)", 0, 0],
      "size": [10, 7, 6],
      "textureOffset": [20, 0]
    },
    {
      "part": "leg1",
      "id": "right_front_leg",
      "invertAxis": "xy",
      "translate": [-3, -4, -2],
      "size": [2, 6, 2],
      "textureOffset": [40, 0]
    },
    {
      "part": "leg2",
      "id": "left_front_leg",
      "invertAxis": "xy",
      "translate": [1, -4, -2],
      "size": [2, 6, 2],
      "textureOffset": [40, 0],
      "mirror": true
    },
    {
      "part": "leg3",
      "id": "right_back_leg",
      "invertAxis": "xy",
      "translate": [-3, -4, 5],
      "size": [2, 6, 2],
      "textureOffset": [48, 0]
    },
    {
      "part": "leg4",
      "id": "left_back_leg",
      "invertAxis": "xy",
      "translate": [1, -4, 5],
      "size": [2, 6, 2],
      "textureOffset": [48, 0],
      "mirror": true
    },
    {
      "part": "tail",
      "id": "tail",
      "invertAxis": "xy",
      "translate": [-1, -8, 7],
      "rotate": ["-90 * (Math.PI / 180)", 0, 0],
      "size": [2, 6, 2],
      "textureOffset": [0, 9]
    },
    {
      "part": "collar",
      "id": "collar",
      "invertAxis": "xy",
      "translate": [-2.5, -11, -3.5],
      "size": [5, 2, 5],
      "textureOffset": [48, 10],
      "inflate": 0.5
    }
  ]
}
```

### 8.3 狼（Wolf）

```json
{
  "texture": "entity/wolf/wolf",
  "textureSize": [64, 32],
  "shadowSize": 0.5,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, -13.5, -7],
      "size": [6, 6, 4],
      "textureOffset": [0, 0],
      "submodel": {
        "left_ear": {
          "size": [2, 3, 1],
          "textureOffset": [16, 14],
          "translate": [-1, -3, 1],
          "rotate": [0, 0, 15]
        },
        "right_ear": {
          "size": [2, 3, 1],
          "textureOffset": [16, 14],
          "translate": [5, -3, 1],
          "rotate": [0, 0, -15]
        },
        "muzzle": {
          "size": [4, 3, 4],
          "textureOffset": [0, 10],
          "translate": [1, -1, -4]
        }
      }
    },
    {
      "part": "body",
      "id": "body",
      "invertAxis": "xy",
      "translate": [0, -11, -2],
      "rotate": ["90 * (Math.PI / 180)", 0, 0],
      "size": [10, 8, 6],
      "textureOffset": [18, 14]
    },
    {
      "part": "leg1",
      "id": "right_front_leg",
      "invertAxis": "xy",
      "translate": [-4, -4, -2],
      "size": [2, 8, 2],
      "textureOffset": [0, 18]
    },
    {
      "part": "leg2",
      "id": "left_front_leg",
      "invertAxis": "xy",
      "translate": [2, -4, -2],
      "size": [2, 8, 2],
      "textureOffset": [0, 18]
    },
    {
      "part": "leg3",
      "id": "right_back_leg",
      "invertAxis": "xy",
      "translate": [-4, -4, 6],
      "size": [2, 8, 2],
      "textureOffset": [0, 18]
    },
    {
      "part": "leg4",
      "id": "left_back_leg",
      "invertAxis": "xy",
      "translate": [2, -4, 6],
      "size": [2, 8, 2],
      "textureOffset": [0, 18]
    },
    {
      "part": "tail",
      "id": "tail",
      "invertAxis": "xy",
      "translate": [-1, -10, 9],
      "rotate": ["-110 * (Math.PI / 180)", 0, 0],
      "size": [2, 6, 2],
      "textureOffset": [21, 0]
    }
  ]
}
```

### 8.4 马（Horse）

```json
{
  "texture": "entity/horse/horse",
  "textureSize": [64, 64],
  "shadowSize": 1.0,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, -21, -10],
      "size": [6, 7, 6],
      "textureOffset": [0, 0],
      "submodel": {
        "left_ear": {
          "size": [2, 3, 1],
          "textureOffset": [0, 0],
          "translate": [0, -3, 2],
          "rotate": [0, 0, 15]
        },
        "right_ear": {
          "size": [2, 3, 1],
          "textureOffset": [0, 0],
          "translate": [4, -3, 2],
          "rotate": [0, 0, -15]
        },
        "upper_mouth": {
          "size": [4, 3, 6],
          "textureOffset": [24, 0],
          "translate": [1, 3, -6],
          "inflate": 0.05
        },
        "lower_mouth": {
          "size": [4, 2, 6],
          "textureOffset": [24, 9],
          "translate": [1, 6, -6]
        }
      }
    },
    {
      "part": "body",
      "id": "body",
      "invertAxis": "xy",
      "translate": [0, -20, 5],
      "rotate": ["90 * (Math.PI / 180)", 0, 0],
      "size": [12, 14, 10],
      "textureOffset": [0, 34]
    },
    {
      "part": "mane",
      "id": "mane",
      "invertAxis": "xy",
      "translate": [-0.5, -22, -10],
      "size": [1, 8, 4],
      "textureOffset": [56, 36],
      "rotate": ["-60 * (Math.PI / 180)", 0, 0]
    },
    {
      "part": "tail",
      "id": "tail",
      "invertAxis": "xy",
      "translate": [-1, -25, 15],
      "size": [2, 9, 2],
      "textureOffset": [44, 0],
      "rotate": ["-60 * (Math.PI / 180)", 0, 0],
      "submodel": {
        "tail_tip": {
          "size": [2, 5, 2],
          "textureOffset": [42, 5],
          "translate": [0, 8, 0],
          "rotate": ["30 * (Math.PI / 180)", 0, 0]
        }
      }
    },
    {
      "part": "leg1a",
      "id": "right_front_upper",
      "invertAxis": "xy",
      "translate": [-6, -10, -4],
      "size": [4, 10, 4],
      "textureOffset": [48, 21],
      "submodel": {
        "leg1b": {
          "size": [4, 8, 4],
          "textureOffset": [48, 31],
          "translate": [0, 9, 0]
        }
      }
    },
    {
      "part": "leg2a",
      "id": "left_front_upper",
      "invertAxis": "xy",
      "translate": [2, -10, -4],
      "size": [4, 10, 4],
      "textureOffset": [48, 21],
      "mirror": true,
      "submodel": {
        "leg2b": {
          "size": [4, 8, 4],
          "textureOffset": [48, 31],
          "translate": [0, 9, 0],
          "mirror": true
        }
      }
    },
    {
      "part": "leg3a",
      "id": "right_rear_upper",
      "invertAxis": "xy",
      "translate": [-6, -10, 8],
      "size": [4, 10, 4],
      "textureOffset": [48, 21],
      "submodel": {
        "leg3b": {
          "size": [4, 8, 4],
          "textureOffset": [48, 31],
          "translate": [0, 9, 0]
        }
      }
    },
    {
      "part": "leg4a",
      "id": "left_rear_upper",
      "invertAxis": "xy",
      "translate": [2, -10, 8],
      "size": [4, 10, 4],
      "textureOffset": [48, 21],
      "mirror": true,
      "submodel": {
        "leg4b": {
          "size": [4, 8, 4],
          "textureOffset": [48, 31],
          "translate": [0, 9, 0],
          "mirror": true
        }
      }
    }
  ]
}
```

---

## 9. 工具链

### 9.1 Blockbench CEM 插件

Blockbench 是最推荐的 Minecraft 模型编辑器，支持 CEM 插件。

**安装步骤**：
1. 下载并安装 Blockbench：https://www.blockbench.net/
2. 打开 Blockbench → 文件 → 插件
3. 搜索 "OptiFine" 或 "CEM"
4. 安装 "OptiFine CEM" 插件

**使用流程**：
```
1. 新建模型 → 选择 "OptiFine Entity" 模板
2. 选择目标实体类型（如 Zombie、Creeper 等）
3. 插件自动创建对应的骨骼结构
4. 使用 Blockbench 的工具编辑模型
   - 移动、缩放、旋转部件
   - 添加新的立方体部件
   - 设置 UV 映射
   - 创建子模型
5. 设置动画表达式（在部件属性中）
6. 导出为 .jem/.jpm 格式
```

### 9.2 手动创建 CEM 模型

如果不使用 Blockbench，可以手动创建 JSON 文件：

```bash
# 1. 创建目录结构
mkdir -p assets/minecraft/optifine/cem
mkdir -p assets/minecraft/textures/entity/custom

# 2. 创建 .jem 文件
# 使用文本编辑器编写 JSON

# 3. 验证 JSON 语法
python -c "import json; json.load(open('assets/minecraft/optifine/cem/zombie.jem'))"

# 4. 打包为资源包（zip 格式）
# 包含 pack.mcmeta 和 assets/ 目录
```

### 9.3 调试技巧

```json
{
  "//": "调试技巧",
  "debug_steps": [
    "1. 先用简单几何体测试基本结构是否正确",
    "2. 逐步添加更多部件，每步都测试",
    "3. 使用明显的颜色标记不同的部件",
    "4. 检查游戏日志中的错误信息",
    "5. 使用 F3+B 显示实体碰撞箱",
    "6. 使用 OptiFine 的内置调试模式"
  ]
}
```

**启用 OptiFine 调试模式**：
- 打开视频设置 → 其他 → 显示 FPS：开启
- CEM 模型加载错误会在游戏日志中显示
- 日志文件：`.minecraft/logs/latest.log`

### 9.4 常见问题排查

```
问题：模型不显示
  排查：
    1. 检查 .jem 文件名是否与实体注册名一致（小写）
    2. 检查 JSON 语法是否正确
    3. 检查 part 名称是否正确
    4. 检查 size 是否为 [0, 0, 0]

问题：纹理错位
  排查：
    1. 检查 textureOffset 是否正确
    2. 检查 textureSize 是否匹配纹理实际尺寸
    3. 检查 invertAxis 设置

问题：部件位置错误
  排查：
    1. 检查 translate 值
    2. 检查 invertAxis 是否导致坐标系不匹配
    3. 检查父部件的 transform

问题：动画不工作
  排查：
    1. 检查表达式语法（必须是字符串）
    2. 确认变量名拼写正确
    3. 检查 Math 函数的大小写

问题：游戏崩溃
  排查：
    1. 检查 JSON 是否有语法错误
    2. 检查是否有循环引用
    3. 检查日志文件获取详细错误信息
```

---

## 10. 完整实战案例：自定义苦力怕模型

### 10.1 目标

创建一个增强版苦力怕模型：
- 更大的头部
- 添加触角
- 身体上有发光纹理区域
- 行走时触角摆动
- 靠近玩家时身体膨胀动画

### 10.2 纹理准备

自定义纹理文件（128x64 高清版本）：

```
纹理布局（128x64）：
┌────────────────────────────────────────────────────────────────────┐
│ 头部 (32x32, 左上角 0,0)          │ 触角 (16x8)   │ 保留 │
│                                    │                │      │
│                                    │                │      │
│                                    │                │      │
├────────────────────────────────────┼────────────────┼──────┤
│ 身体 (24x16)    │ 4腿各 (8x8)      │ 保留           │ 保留 │
│                  │                  │                │      │
│                  │                  │                │      │
└────────────────────────────────────────────────────────────────────┘
```

### 10.3 .jem 文件

```json
{
  "texture": "entity/creeper/creeper",
  "textureSize": [128, 64],
  "shadowSize": 0.5,
  "shadow": 1.0,
  "scale": 1.0,
  "models": [
    {
      "part": "head",
      "id": "head",
      "invertAxis": "xy",
      "translate": [0, -18, -4],
      "size": [10, 10, 10],
      "textureOffset": [0, 0],
      "textureSize": [128, 64],
      "mirror": false,
      "rotate": ["-headPitch * (Math.PI / 180)", "headYaw * (Math.PI / 180)", 0],
      "submodel": {
        "left_antenna": {
          "id": "left_antenna",
          "size": [2, 8, 2],
          "textureOffset": [0, 32],
          "textureSize": [128, 64],
          "translate": [1, -8, 4],
          "rotate": [
            "Math.sin(ageInTicks * 0.1) * 15",
            0,
            "10 + Math.sin(ageInTicks * 0.15) * 10"
          ],
          "mirror": false,
          "scale": 1.0
        },
        "right_antenna": {
          "id": "right_antenna",
          "size": [2, 8, 2],
          "textureOffset": [8, 32],
          "textureSize": [128, 64],
          "translate": [7, -8, 4],
          "rotate": [
            "Math.sin(ageInTicks * 0.1 + 1) * 15",
            0,
            "-10 - Math.sin(ageInTicks * 0.15 + 1) * 10"
          ],
          "mirror": false,
          "scale": 1.0
        },
        "glow_eyes": {
          "id": "glow_eyes",
          "size": [4, 4, 1],
          "textureOffset": [32, 0],
          "textureSize": [128, 64],
          "translate": [1, 2, -1],
          "rotate": [0, 0, 0],
          "mirror": false,
          "scale": 1.0
        }
      }
    },
    {
      "part": "body",
      "id": "body",
      "invertAxis": "xy",
      "translate": [0, -18, 0],
      "size": [8, 14, 4],
      "textureOffset": [20, 32],
      "textureSize": [128, 64],
      "mirror": false,
      "rotate": [
        0,
        0,
        0
      ],
      "scale": "1.0 + (isAggressive ? Math.sin(ageInTicks * 0.3) * 0.1 : 0)"
    },
    {
      "part": "leg1",
      "id": "right_front_leg",
      "invertAxis": "xy",
      "translate": [-4, -6, -2],
      "size": [4, 6, 4],
      "textureOffset": [0, 48],
      "textureSize": [128, 64],
      "mirror": false,
      "rotate": [
        "Math.cos(limbSwing * 0.6662) * limbSwingAmount * 1.4",
        0,
        0
      ]
    },
    {
      "part": "leg2",
      "id": "left_front_leg",
      "invertAxis": "xy",
      "translate": [0, -6, -2],
      "size": [4, 6, 4],
      "textureOffset": [0, 48],
      "textureSize": [128, 64],
      "mirror": true,
      "rotate": [
        "Math.cos(limbSwing * 0.6662 + Math.PI) * limbSwingAmount * 1.4",
        0,
        0
      ]
    },
    {
      "part": "leg3",
      "id": "right_back_leg",
      "invertAxis": "xy",
      "translate": [-4, -6, 4],
      "size": [4, 6, 4],
      "textureOffset": [0, 48],
      "textureSize": [128, 64],
      "mirror": false,
      "rotate": [
        "Math.cos(limbSwing * 0.6662 + Math.PI) * limbSwingAmount * 1.4",
        0,
        0
      ]
    },
    {
      "part": "leg4",
      "id": "left_back_leg",
      "invertAxis": "xy",
      "translate": [0, -6, 4],
      "size": [4, 6, 4],
      "textureOffset": [0, 48],
      "textureSize": [128, 64],
      "mirror": true,
      "rotate": [
        "Math.cos(limbSwing * 0.6662) * limbSwingAmount * 1.4",
        0,
        0
      ]
    }
  ]
}
```

### 10.4 动画效果说明

```
触角动画：
  - 使用 Math.sin(ageInTicks * 0.1) 创建周期性摆动
  - 两个触角使用不同的相位（+1）产生自然的错位效果
  - 摆动幅度为 15 度旋转

身体膨胀动画：
  - 仅在攻击状态（isAggressive）时激活
  - 使用 Math.sin(ageInTicks * 0.3) 创建脉动效果
  - 缩放范围在 0.9 到 1.1 之间

腿部行走动画：
  - 使用 limbSwing 和 limbSwingAmount 变量
  - 与原版行走动画同步
  - 前后腿使用 Math.PI 相位差产生交替摆动

头部跟随：
  - 使用 headYaw 和 headPitch 变量
  - 头部始终面向玩家视角方向
```

### 10.5 pack.mcmeta

```json
{
  "pack": {
    "pack_format": 15,
    "description": "Custom Creeper CEM Model"
  }
}
```

### 10.6 最终文件结构

```
Custom_Creeper_ResourcePack/
├── pack.mcmeta
├── pack.png
└── assets/
    └── minecraft/
        ├── optifine/
        │   └── cem/
        │       └── creeper.jem
        └── textures/
            └── entity/
                └── creeper/
                    └── creeper.png    (128x64 自定义纹理)
```

---

## 附录：CEM 支持的实体完整列表

| 实体 | .jem 文件名 | 主要部件 |
|------|-------------|----------|
| 僵尸 | zombie.jem | head, body, right_arm, left_arm, right_leg, left_leg |
| 僵尸村民 | zombie_villager.jem | head, body, right_arm, left_arm, right_leg, left_leg |
| 骷髅 | skeleton.jem | head, body, right_arm, left_arm, right_leg, left_leg |
| 凋灵骷髅 | wither_skeleton.jem | head, body, right_arm, left_arm, right_leg, left_leg |
| 苦力怕 | creeper.jem | head, body, leg1-4 |
| 蜘蛛 | spider.jem | head0, neck, body0, body1, leg0-7 |
| 洞穴蜘蛛 | cave_spider.jem | head0, neck, body0, body1, leg0-7 |
| 末影人 | enderman.jem | head, body, right_arm, left_arm, right_leg, left_leg |
| 村民 | villager.jem | head, body, right_arm, left_arm, right_leg, left_leg, nose, arms |
| 女巫 | witch.jem | head, body, right_arm, left_arm, right_leg, left_leg, mole, hat |
| 猫 | cat.jem | head, body, leg1-4, tail, collar |
| 狼 | wolf.jem | head, body, leg1-4, tail |
| 马 | horse.jem | head, body, leg1a-4a, leg1b-4b, tail, mane, saddle 等 |
| 驴 | donkey.jem | 类似马 |
| 骷髅马 | skeleton_horse.jem | 类似马 |
| 僵尸马 | zombie_horse.jem | 类似马 |
| 牛 | cow.jem | head, body, leg1-4, udder, horns |
| 羊 | sheep.jem | head, body, leg1-4, tail |
| 猪 | pig.jem | head, body, leg1-4, snout |
| 鸡 | chicken.jem | head, body, right_leg, left_leg, right_wing, left_wing, bill, chin |
| 末影龙 | ender_dragon.jem | head, jaw, neck, spine, body, wing 等 |
| 凋灵 | wither.jem | body1-3, head1-3 |
| 守卫者 | guardian.jem | body, eye, tail, spine, eye_spine |
| 远古守卫者 | elder_guardian.jem | 类似守卫者 |
| 潜影贝 | shulker.jem | head, lid, base |
| 海豚 | dolphin.jem | head, body, tail, tail_fin, left_fin, right_fin, back_fin |
| 鹦鹉 | parrot.jem | head, body, tail, left_wing, right_wing, left_leg, right_leg |
| 海龟 | turtle.jem | head, body, leg1-4, tail, egg_belly |
| 熊猫 | panda.jem | head, body, leg1-4, tail |
| 狐狸 | fox.jem | head, body, leg1-4, tail |
| 蜜蜂 | bee.jem | body, right_wing, left_wing, front_legs, middle_legs, stinger, back_legs |
| 哞菇 | mooshroom.jem | head, body, leg1-4, udder |
| 山羊 | goat.jem | head, body, leg1-4, left_horn, right_horn |
| 青蛙 | frog.jem | body, head, eyes, tongue, left_leg, right_leg |
| 骆驼 | camel.jem | head, body, left_front_leg, right_front_leg, left_hind_leg, right_hind_leg, tail, saddle |
| 悦灵 | allay.jem | head, body, right_arm, left_arm, right_wing, left_wing |
| 监守者 | warden.jem | head, body, right_arm, left_arm, right_leg, left_leg, right_tendril, left_tendril |

---

*本文档最后更新于：2026年5月*
