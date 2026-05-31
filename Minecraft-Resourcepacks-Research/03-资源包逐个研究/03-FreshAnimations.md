## 2.3 `FreshAnimations_v1.10.5`

### 3.3.1 根目录结构

路径：`Resourcepacks/FreshAnimations_v1.10.5/`

```text
assets/
changelog1.10.5.txt
FAterms&conditions.txt
pack.mcmeta
pack.png
```

### 3.3.2 包定位

这是一个非常典型的“实体动画增强”资源包。

它通过 OptiFine CEM 体系以及相关纹理替换，为大量生物添加更自然、更细致的动作表现。

从文件结构可以直接看出，它是围绕 `assets/minecraft/optifine/cem/` 构建的。

### 3.3.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/FreshAnimations_v1.10.5/pack.mcmeta`

```json
{
    "pack": {
        "description": "§4■ 1.10.5 BETA§8\n■ By FreshLX",
        "min_format": 84,
        "max_format": 999
    }
}
```

用途：

1. 标记资源包版本与作者。
2. 表明这是测试/预发布性质的版本。

#### `FAterms&conditions.txt`

路径：`Resourcepacks/FreshAnimations_v1.10.5/FAterms&conditions.txt`

作用：

1. 说明资源包资产的授权边界。
2. 明确某些资产不允许随意再分发或商用。
3. 提示公开内容中引用时需要署名。

#### `changelog1.10.5.txt`

路径：`Resourcepacks/FreshAnimations_v1.10.5/changelog1.10.5.txt`

作用：

1. 记录本次版本改动。
2. 说明添加了若干生物纹理路径。
3. 建议与 Entity Model Features / Entity Texture Features 结合使用。

#### `pack.png`

路径：`Resourcepacks/FreshAnimations_v1.10.5/pack.png`

作用：资源包图标。

### 3.3.4 资源内容结构

该包的主要资源集中在：

1. `assets/minecraft/optifine/cem/`
2. `assets/minecraft/textures/entity/`
3. `assets/minecraft/particles/`

### 3.3.5 关键目录功能

#### `assets/minecraft/optifine/cem/`

这是整包的核心。

这里有大量 `.jem` 和 `.jpm` 文件，例如：

1. `villager.jem`
2. `villager_animations.jpm`
3. `zombie.jem`
4. `wolf.jem`
5. `fox.jem`
6. `horse.jem`
7. `creeper.jem`
8. `dolphin.jem`
9. `allay_animations.jpm`
10. `frog_animations.jpm`
11. `sniffer_animations.jpm`
12. `happy_ghast.jem`

这说明：

1. 包通过 CEM 自定义实体模型。
2. `.jem` 负责实体模型定义。
3. `.jpm` 负责动画参数与运动公式。

代表文件：

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/optifine/cem/villager.jem`

内容特征：

1. `textureSize` 定义贴图尺寸。
2. `models` 中将 `root`、`head`、`body`、`arms`、`legs` 等部件拆开。
3. 通过 `submodels` 和 `boxes` 定义更细的面部、帽子、鼻子、眉毛等结构。

这说明村民模型被重构为更复杂的分层模型，而不是原版单一方块风格。

代表文件：

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/optifine/cem/villager_animations.jpm`

内容特征：

1. 以大量变量计算驱动头部、身体、腿部与脸部动画。
2. 通过 `var.walk`、`var.run`、`var.swim`、`var.dance` 等表达式控制动态姿态。
3. 允许面部细节、身体摇摆、视线偏移等更自然表现。

这是该包“Fresh Animations”名字的直接体现：它不是静态换皮，而是动态动画增强。

#### `assets/minecraft/textures/entity/`

这里存放大量实体纹理，例如：

1. `villager/villager.png`
2. `villager/type/desert.png`
3. `zombie/zombie.png`
4. `zombie/drowned.png`
5. `wolf/wolf.png`
6. `cat/cat_tabby.png`
7. `bee/bee.png`
8. `frog/frog_temperate.png`
9. `pig/pig_warm.png`
10. `cow/cow_temperate.png`
11. `shulker/shulker_red.png`
12. `illager/vindicator.png`

说明：

1. 该包不只换模型，也换实体贴图。
2. 很多纹理按变种分离，例如生物群系、状态、怒气、骑乘、寒热环境等。

#### `assets/minecraft/particles/mycelium.json`

路径：`Resourcepacks/FreshAnimations_v1.10.5/assets/minecraft/particles/mycelium.json`

内容：

```json
{
  "textures": [
    "minecraft:fresh_animations/empty"
  ]
}
```

用途：

1. 让特定粒子引用一个空纹理。
2. 常用于隐藏不需要的视觉颗粒或占位。

### 3.3.6 结论

`FreshAnimations_v1.10.5` 是一个高复杂度的实体表现增强包。

它的结构显示出三层改造：

1. `.jem` 改模型。
2. `.jpm` 改动画。
3. `textures/entity` 改贴图。

它并不是普通意义上的“材质包换图”，而是把实体表现系统整体重做了一遍。

---

