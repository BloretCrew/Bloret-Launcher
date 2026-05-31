## 2.1 `Better-Leaves-9.5`

### 3.1.1 根目录结构

路径：`Resourcepacks/Better-Leaves-9.5/`

```text
assets/
LICENSE
pack.mcmeta
pack.png
README.md
```

### 3.1.2 包定位

这是一个“树叶优化 / 美化”资源包，目标是让树叶呈现更饱满、更圆润的视觉效果，同时尽量降低性能损耗。

从 `README.md` 可以看出它的设计目标是：

1. 使用更少的模型元素。
2. 预先生成圆润纹理，而不是在渲染阶段伪造圆形。
3. 尽量通过单纹理方案减少贴图坐标查找和纹理图集开销。

### 3.1.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/Better-Leaves-9.5/pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 15,
    "supported_formats": [15, 255],
    "min_format": 15,
    "max_format": 255,
    "description": "§2Version 9.5 §aVanilla Edition\n§e©Motschen 2026 | MIT Licence"
  }
}
```

用途：

1. 指定资源包格式。
2. 说明该包面向较新版本。
3. 描述文本显示版本号、作者和许可证信息。

#### `README.md`

路径：`Resourcepacks/Better-Leaves-9.5/README.md`

作用：

1. 解释包的优化思路。
2. 说明与其他树叶纹理包相比的性能优势。
3. 提示可用脚本自建变体。

#### `LICENSE`

路径：`Resourcepacks/Better-Leaves-9.5/LICENSE`

作用：

1. 约束资源包使用方式。
2. 与包说明一起表明该包可被再分发或重制时的法律边界。

#### `pack.png`

路径：`Resourcepacks/Better-Leaves-9.5/pack.png`

作用：

1. 资源包图标。
2. 在资源包列表中显示。

### 3.1.4 资源内容结构

该包的主要内容位于 `assets/`，并且包含多个命名空间，例如：

1. `assets/dtru/`
2. `assets/dtnatures_spirit/`
3. `assets/dtecologics/`
4. `assets/dtbwg/`
5. `assets/enderscape/`
6. `assets/ars_elemental/`
7. `assets/aether/`

这说明它不是纯原版覆盖包，而是面向多个模组树叶方块的兼容美化包。

### 3.1.5 关键目录功能

#### `assets/<namespace>/blockstates/`

代表功能：为对应模组方块指定模型映射。

示例：

路径：`Resourcepacks/Better-Leaves-9.5/assets/dtru/blockstates/maple_leaves.json`

内容要点：

1. 一个方块状态列出多个 `variants`。
2. 每个 variant 指向不同模型，例如 `regions_unexplored:block/maple_leaves1` 到 `maple_leaves4`。
3. 同一模型配合 `y: 0/90/180/270` 旋转，制造多样化树叶外观。

这说明：

1. 树叶并不是只改一张贴图，而是通过多个模型变体增加随机感。
2. `blockstates` 在这里是“随机外观分发器”。

示例：

路径：`Resourcepacks/Better-Leaves-9.5/assets/dtru/blockstates/larch_leaves.json`

同样指向 `regions_unexplored:block/larch_leaves1` 到 `larch_leaves4`，说明这个包有一整套对树叶方块的模型重映射体系。

### 3.1.6 结论

`Better-Leaves-9.5` 是一个典型的“模组树叶美化 + 性能优化”资源包。

它的核心不是简单替换贴图，而是：

1. 通过 `blockstates` 让叶子模型变体更多。
2. 通过命名空间分区支持多个模组。
3. 用更少的渲染代价实现更饱满的树叶效果。

---

