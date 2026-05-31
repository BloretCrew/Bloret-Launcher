# 34. DetailedAnimationsReworked - V1.15 PATCH

## 根目录结构

```
DetailedAnimationsReworked - V1.15 PATCH/
├── assets/
│   └── minecraft/
│       └── emf/
│           └── cem/
│               ├── elytra.jem
│               ├── player.jem
│               ├── player_cape.jem
│               └── player_slim.jem
├── pack.mcmeta
└── pack.png
```

## 包定位

DetailedAnimationsReworked 是一个专注于**玩家模型动画增强**的资源包，由 Cymock 制作。它通过 EMF（Entity Model Features）系统为玩家模型提供高度精细的自定义动画，涵盖行走、奔跑、游泳、攀爬、滑翔、漂浮等几乎所有运动状态。

V1.15 PATCH 表明了这是一个特定版本的补丁包。该包不依赖 OptiFine，仅使用 EMF 技术，因此主要适用于 Fabric/NeoForge 模组环境。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "description": "Detailed Animations Reworked by Cymock",
    "pack_format": 15,
    "supported_formats": {"min_inclusive": 15, "max_inclusive": 99}
  }
}
```

pack_format 为15（Minecraft 1.21），支持到99，表明兼容从现在到未来的多个版本。描述简洁，直接注明作者。

**核心文件构成：**
- `player.jem`: 玩家标准模型（宽型手臂）的完整动画定义
- `player_slim.jem`: 玩家纤细模型（窄型手臂，如皮肤模型为Slim类型）的动画定义
- `elytra.jem`: 鞘翅的动画定义
- `player_cape.jem`: 披风的动画定义

## 资源内容结构

本包的结构极其精简，仅包含EMF格式的自定义实体模型文件。全部内容都集中在玩家实体的动画增强上，没有纹理文件，没有blockstates，没有其他任何多余的资源。

### 模型定义

以 `player.jem` 为例，它定义了玩家模型的各个部件：

- **身体部件**：cloak（披风）、ear（耳朵）、head（头部）、headwear（头部装饰）、body（身体）、jacket（外套）、right_arm/left_arm（左右手臂）、right_sleeve/left_sleeve（左右袖子）、right_leg/left_leg（左右腿）、right_pants/left_pants（左右裤腿）
- 每个部件都使用标准UV贴图，与默认玩家模型完全兼容

### 动画系统

动画部分是此包最大的亮点。它包含大量精心计算的数学表达式，通过游戏引擎提供的变量来实现各类动态效果：

**核心动画变量：**
- `frame_time`: 平滑的帧时间，用于控制动画速度
- `LimbSwing_Delta`: 四肢摆动增量，用于步行/奔跑循环
- `HeightVelocity`: 垂直速度，用于计算跳跃和下落动画
- `TurningVelocity`: 转向速度，用于身体转向动画

**复杂状态机：**

包中定义了一个高度复杂的姿态状态机，覆盖了以下场景：

1. **行走/奔跑动画**：使用正弦/余弦函数驱动四肢摆动，hand-walk cycle与leg-walk cycle保持180度相位差（自然的人体运动模式）

2. **跳跃/冲刺跳跃 (HopRunning)**：检测玩家跳跃状态并启用专门的跳跃动画，与奔跑状态平滑过渡

3. **游泳动画**：检测 `is_swimming` 状态，切换肢体动作为游泳模式

4. **鞘翅滑翔 (Gliding)**：`GlideIntensity` 变量控制滑翔状态的肢体位置调整

5. **漂浮/飞行 (Levitation)**：为漂浮状态设计了对肢体位置的调整，使玩家在悬空时呈现失重感

6. **攀爬动画**：检测 `is_climbing` 状态，手臂和腿的位置会根据攀爬进度（pos_y）进行计算

7. **下落动画 (AirFall)**：包含空气阻力、自由落体姿态，坠落时四肢的自然展开

8. **潜行动画**：潜行时的身体倾斜和微妙的"潜行舞蹈"效果

9. **受伤反应 (Hurt)**：受到伤害时身体会有轻微的震颤反馈

10. **着火动画 (Flaming/Boiling)**：身体着火时会有不自主的抽搐动作

11. **水下姿态 (WaterPose/WetPose)**：在水中的浮力效果和出水后的滴水状态

**物理模拟：**
包中包含了一定程度的物理模拟，如：
- `VerticalMotion1/2` 和 `StrafeMotion1/2` 模拟身体的惯性和弹性
- 对不同状态进行平滑插值（使用加权移动平均），避免动作突变
- 针对不同动作有不同的响应速度和阻尼系数

## 技术特点

1. **纯 EMF 实现**：不依赖 OptiFine，只使用 EMF 标准，适合现代模组加载器。

2. **极致的动画细节**：从简单的走路到复杂的攀爬着火状态，每个动作都有对应的动画逻辑，是目前市面上最精细的玩家动画包之一。

3. **平滑状态切换**：所有状态转换都使用插值（lerp）实现，动作过渡自然流畅。

4. **应用干扰叠加**：多个动画状态可以叠加（例如行走时着火），通过权重系统（如 `var.WalkIntensity * (1 - var.GlideIntensity)`）实现优先级控制。

5. **资源高效**：虽然动画逻辑极其复杂，但所有计算都在着色器级别的模型中完成，对性能影响相对可控。

## 结论

DetailedAnimationsReworked V1.15 PATCH 是一个技术含量极高的玩家动画增强资源包。它通过 EMF 系统的强大能力，为玩家模型注入了前所未有的生命力。从最简单的行走摆臂到复杂的多状态叠加，每个细节都体现了作者对游戏动画的深刻理解。

尤其值得称道的是其状态管理系统的设计——通过巧妙的数学插值，实现了各种动作之间的平滑过渡，使玩家角色的运动看起来自然而真实。即使是在攀爬、着火等非正常状态下，动画也保持了合理的物理反馈。

这个包适合那些希望在游戏体验中获得更高沉浸感的玩家，特别是喜欢录制动感视频或纯粹享受视觉细节的 Minecraft 爱好者。
