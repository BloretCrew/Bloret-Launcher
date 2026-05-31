# GUI 资源包开发指南

## 一、Minecraft GUI 系统概述

### 1.1 GUI 渲染架构

Minecraft 的图形用户界面（GUI）系统负责渲染游戏内的所有交互界面元素，包括主菜单、游戏内 HUD、容器界面、聊天框、进度条等。GUI 系统的渲染基于 2D 纹理系统，所有界面元素都是由纹理图集中的特定区域映射而成。

GUI 渲染的核心特点：

- **固定分辨率**：GUI 渲染基于固定的 GUI 缩放比例（1x、2x、3x、4x），而非屏幕原生分辨率。这使得 GUI 纹理需要在不同缩放级别下保持清晰。
- **九宫格缩放（Nine-Patch Slicing）**：容器的背景面板使用九宫格技术，确保面板在不同尺寸下保持边角不变形。
- **精灵系统（Sprite System）**：从 1.19.3 版本开始，Minecraft 引入了新的精灵系统，改变了 GUI 纹理的组织方式。
- **双渲染模式**：GUI 元素在 3D 场景上方以正交投影方式渲染，与 3D 世界的渲染管线分离。

### 1.2 GUI 纹理的挑战

GUI 纹理开发面临以下挑战：

1. **多分辨率适配**：GUI 纹理需要在高分辨率和低分辨率缩放比例下都保持可用。
2. **版本差异**：不同 Minecraft 版本之间 GUI 布局和纹理组织方式有显著差异。
3. **暗色模式支持**：1.16 版本后，Mojang 开始推进 GUI 暗色模式支持，需要额外的纹理文件。
4. **自定义字体兼容**：GUI 纹理与字体系统相互关联，修改时需确保兼容性。

## 二、GUI 纹理目录结构

### 2.1 基础目录

GUI 纹理（单文本包括材质、布局、图片等视觉资源）主要存储在 `assets/minecraft/textures/gui/` 目录下：

```
assets/minecraft/textures/gui/
├── title/                  # 标题界面（主菜单）纹理
│   ├── background/         # 全景背景
│   │   └── panorama_*.png  # 全景图帧（共 6 帧）
│   └── minecraft_logo.png  # Minecraft 徽标
├── container/              # 容器界面纹理
│   ├── creative_inventory/ # 创造模式物品栏
│   │   └── tabs.png        # 创造模式标签页
│   ├── enchanting_table.png # 附魔台界面
│   ├── furnace.png         # 熔炉界面
│   ├── crafting_table.png  # 工作台界面
│   ├── chest.png           # 箱子界面
│   ├──-inventory.png       # 生存模式物品栏
│   ├── dispenser.png       # 发射器界面
│   ├── hopper.png          # 漏斗界面
│   ├── brewing_stand.png   # 酿造台界面
│   ├── beacon.png          # 信标界面
│   ├── anvil.png           # 铁砧界面
│   ├── smithing.png        # 锻造台界面
│   ├── villager.png        # 村民交易界面
│   ├── horse.png           # 马匹界面
│   ├── lectern.png         # 讲台界面
│   ├── loom.png            # 织布机界面
│   ├── stonecutter.png     # 切石机界面
│   ├── grindstone.png      # 砂轮界面
│   ├── cartography_table.png # 制图台界面
│   └── ...
├── sprites/                # 精灵系统纹理（1.19.3+）
│   ├── container/          # 容器精灵
│   ├── hud/                # HUD 精灵
│   └── ...
├── widgets.png             # 默认 GUI 控件纹理
├── icons.png               # 图标纹理
├── recipe_book.png         # 合成配方书
├── social_interactions.png # 社交互动界面
├── tab_list.png            # Tab 玩家列表
├── access_widgets.png      # 辅助功能控件
├── advancements.png        # 进度界面
├── spectator_widgets.png   # 旁观者模式控件
├── chat_tags.png           # 聊天标签
├── checkpoint.png          # 检查点图标
├── demo_background.png     # 演示版背景
├── options_background.png  # 选项背景
├── presets.png             # 预设
├── report_button.png       # 举报按钮
├── server_selection.png    # 服务器选择
├── toasts.png              # 弹窗通知
├── world_list.png          # 世界列表
└── pumpkin_blur.png        # 南瓜头模糊效果
```

### 2.2 各目录详细说明

#### 2.2.1 `title/` —— 主界面纹理

**全景背景（Panorama）**：

主菜单的背景由 6 张全景纹理构成，放置在 `background/` 子目录中：

```
title/background/
├── panorama_0.png    # 正面（-Z）
├── panorama_1.png    # 右面（+X）
├── panorama_2.png    # 后面（+Z）
├── panorama_3.png    # 左面（-X）
├── panorama_4.png    # 上面（+Y）
└── panorama_5.png    # 下面（-Y）
```

全景纹理需要是 1:1 的正方形，推荐的尺寸为 1024x1024 像素。全景图以立方体贴图（Cubemap）的方式渲染在主菜单背景上。

**Minecraft 徽标**：

`minecraft_logo.png` 是显示在主菜单顶部的游戏标题。纹理尺寸为 256x128 像素，包含标准徽标和 Minceraft（彩蛋变体）两个状态。

#### 2.2.2 `container/` —— 容器界面纹理

每个容器界面使用独立的纹理文件。纹理通常包含：

- **背景面板（Background Panel）**：使用九宫格技术缩放的界面背景。
- **槽位（Slots）**：物品放置槽位的边框。
- **进度指示器（Progress Indicators）**：如熔炉的燃烧进度、酿造台的酿造进度条。
- **特殊元素**：如附魔台的符文、铁砧的伤害指示器等。

**纹理尺寸示例**：

| 容器 | 纹理尺寸 | 特色元素 |
|-----|---------|---------|
| 箱子 | 256x256 | 主面板、槽位区域 |
| 熔炉 | 256x256 | 燃烧火焰、进度箭头 |
| 工作台 | 256x256 | 3x3 合成网格、箭头 |
| 附魔台 | 256x256 | 符文动画、槽位 |
| 酿造台 | 256x256 | 燃料槽、药水瓶槽 |

#### 2.2.3 `sprites/` —— 精灵系统（1.19.3+）

从 1.19.3 版本开始，Minecraft 引入了精灵系统，将 GUI 元素拆分为独立的纹理文件，替代了传统的合并纹理图集方式。

**精灵目录结构**：

```
gui/sprites/
├── container/
│   ├── creative_inventory/
│   │   └── tabs/
│   ├── crafting_pin.png
│   ├── crafting_slot.png
│   └── ...
├── hud/
│   ├── heart/
│   ├── food/
│   ├── air/
│   ├── experience_bar/
│   ├── hotbar/
│   ├── cross_attack_indicator/
│   ├── jump_bar/
│   └── ...
├── advancement/
├── chat/
├── recipe_book/
├── icon/
│   ├── beacon_effect.png
│   ├── boss_bar.png
│   └── ...  
└── widget/
    ├── button.png
    ├── button_disabled.png
    ├── button_highlighted.png
    ├── checkbox.png
    ├── slider.png
    ├── tab.png
    ├── scrollbar.png
    └── ...
```

**精灵系统的优势**：

1. **更精确的纹理映射**：每个精灵独立定位，无需关心在图集中的坐标。
2. **更易于替换**：可以只替换单个精灵而不影响整个图集。
3. **更好的 Mod 兼容性**：模组可以直接添加新的精灵而不必修改现有的图集文件。
4. **九宫格支持**：精灵系统原生支持九宫格缩放配置。

**精灵的元数据（.mcmeta）**：

精灵可以附带 `.mcmeta` 文件定义其行为：

```json
{
  "sprite": {
    "ppi": 64,
    "nine_slice": {
      "width": 8,
      "height": 8,
      "left": 4,
      "right": 4,
      "top": 4,
      "bottom": 4
    },
    "name": "container/slot"
  }
}
```

## 三、核心 GUI 纹理文件解析

### 3.1 `widgets.png`

`widgets.png` 是 GUI 控件的基础纹理，包含按钮、文本框、滑动条等控件的不同状态。

**纹理布局**（256x256）：

- **按钮**：包含普通态（Normal）、悬停态（Hovered）和按下态（Pressed），每个状态 200x20 像素。
- **文本框**：输入框的背景和光标。
- **滑动条**：滑块和滑道。
- **复选框**：选中和未选中状态。
- **标签页（Tabs）**：选中和未选中。

**自定义按钮纹理**：

修改 `widgets.png` 中按钮区域可以实现自定义按钮样式。需要保持按钮分区的坐标和尺寸不变：

- 按钮宽度：200 像素
- 按钮高度：20 像素（每状态）
- 按钮区域从 y=0 开始

### 3.2 `icons.png`

`icons.png` 包含游戏内使用的各种小图标，如状态效果、特效指示器等。

**常见图标区域**：

- **状态效果图标**：32x32 像素每个，排列在纹理中。
- **移动端按钮**：触摸控制按钮。
- **游戏模式指示器**：生存/创造/冒险/旁观者模式图标。
- **难度指示器**：和平/简单/普通/困难模式图标。

### 3.3 HUD 纹理

HUD（Heads-Up Display）纹理分散在多个文件中，主要位于 `sprites/hud/` 目录（1.19.3+）：

**生命值相关**：
- `heart/`：包含全系列生命值图标（普通、毒、饥饿、凋零等状态）。
- `food/`：饱食度图标（全满、半满、空）。
- `air/`：氧气值图标。

**快捷栏相关**：
- `hotbar/`：快捷栏背景和选中指示器。
- `cross_attack_indicator.png`：攻击充能指示器。
- `experience_bar.png`：经验条纹理。

**其他 HUD 元素**：
- `jump_bar.png`：跳跃（马匹）蓄力条。
- `mount_health.png`：坐骑生命值。
- `vehicle_container.png`：载具容器背景。

## 四、暗色模式实现

### 4.1 暗色模式概述

从 Minecraft 1.16 开始，Mojang 逐步为 GUI 系统引入了暗色模式支持。暗色模式通过**两份独立的纹理**实现——一份用于亮色主题（Light Mode），一份用于暗色主题（Dark Mode）。

### 4.2 纹理放置规则

暗色模式的纹理文件通过特定的命名规范与对应的亮色模式纹理配对：

- 亮色模式：`textures/gui/<file>.png`
- 暗色模式：`textures/gui/<file>_dark.png`（或其他约定后缀）

部分暗色纹理的存放位置：

```
textures/gui/
├── container/
│   ├── inventory.png      # 亮色物品栏
│   └── inventory_dark.png # 暗色物品栏
├── widgets.png            # 亮色控件
├── widgets_dark.png       # 暗色控件
├── recipe_book.png        # 亮色配方书
└── recipe_book_dark.png   # 暗色配方书
```

### 4.3 暗色模式设计原则

1. **保持对比度**：暗色模式下文本和控件的对比度不能太低，确保可读性。
2. **统一的暗色调**：建议使用深灰色（#1a1a1a 到 #2d2d2d）而非纯黑色（#000000），以减少视觉疲劳。
3. **高亮颜色**：暗色模式下的悬停高亮建议使用更亮的色调（如 #4a4a4a）。
4. **图标清晰度**：图标线条需要更亮或更粗，以在深色背景下保持可见。
5. **状态区分**：选中/未选中、禁用/可用的颜色区分需要更加明显。

### 4.4 暗色模式切换机制

玩家可在"选项"→"界面"→"界面颜色"中选择"深色"或"浅色"主题。切换后游戏自动加载对应的纹理文件。

开发者需要注意：
1. 如果资源包只提供了亮色纹理而未提供暗色纹理，暗色模式开启后游戏仍会使用亮色纹理，可能导致设计上的不一致。
2. 建议同时提供两套纹理以确保在所有模式下的一致性。
3. 某些 GUI 元素可能不支持暗色模式切换，超出资源包控制范围。

## 五、精灵系统详解（1.19.3+）

### 5.1 精灵图集生成

Minecraft 在启动时会根据 `textures/gui/sprites/` 目录下的文件自动生成精灵图集。每个 PNG 文件被视为一个独立精灵，游戏为每个精灵分配唯一的标识符和纹理坐标。

**精灵注册**：

游戏基于文件路径注册精灵。例如 `textures/gui/sprites/hud/heart/full.png` 注册为 `hud/heart/full` 精灵。

### 5.2 精灵覆盖规则

资源包通过提供具有相同路径的精灵文件来覆盖原版精灵。例如要替换心形图标：

1. 创建 `assets/minecraft/textures/gui/sprites/hud/heart/full.png`。
2. 按照所需的尺寸和设计绘制纹理。
3. 游戏加载资源包后自动使用新文件替换原版精灵。

### 5.3 九宫格精灵

对于需要缩放的 GUI 元素（如按钮、面板背景），精灵系统支持九宫格（Nine-Slice）缩放。通过精灵的 `.mcmeta` 文件定义：

```json
// textures/gui/sprites/widget/button.png.mcmeta
{
  "sprite": {
    "nine_slice": {
      "width": 200,
      "height": 20,
      "left": 4,
      "right": 4,
      "top": 4,
      "bottom": 4
    }
  }
}
```

九宫格参数：

- `width/height`：精灵的原始尺寸（像素）。
- `left/right/top/bottom`：四个边距，定义不变形的角落区域。
  - 四角（左上、右上、左下、右下）保持不变。
  - 四边（上、下、左、右）沿一个方向拉伸。
  - 中央区域沿两个方向拉伸。

### 5.4 精灵变体

某些精灵支持变体（Variants），用于表示不同状态。变体通过在文件名中添加特定后缀实现：

- `button.png` —— 默认状态
- `button_highlighted.png` —— 悬停高亮
- `button_disabled.png` —— 禁用状态

## 六、自定义 GUI 元素

### 6.1 添加自定义按钮

要创建自定义风格的按钮，需要修改：

1. **精灵文件**（1.19.3+）：`sprites/widget/button.png` 及变体。
2. **传统纹理**（<1.19.3）：`widgets.png` 中的按钮区域。

**精灵方式示例**：

创建三个精灵文件：
- `sprites/widget/button.png`：普通态（尺寸 200x20）
- `sprites/widget/button_highlighted.png`：悬停态
- `sprites/widget/button_disabled.png`：禁用态

同时创建 `.mcmeta` 文件定义九宫格参数。

### 6.2 自定义进度条

**进度条精灵**：

- `sprites/widget/progress_bar.png`：背景
- `sprites/widget/progress_bar_fill.png`：填充部分
- `sprites/widget/progress_bar_fill_top.png`（某些容器使用）

**熔炉进度条**：

熔炉的燃烧进度和冶炼进度使用 `container/furnace.png` 中的特定区域：
- 火焰区域：表示燃烧剩余时间。
- 箭头区域：表示冶炼进度。

### 6.3 自定义槽位样式

物品槽位可以通过修改以下文件自定义：

- `sprites/container/slot.png`：普通槽位
- `sprites/container/slot_highlight.png`：高亮槽位（鼠标悬停）
- `sprites/container/slot_overlay.png`：覆盖槽位

### 6.4 自定义效果图标

状态效果图标位于 `sprites/container/effect/` 目录或 `container/inventory.png` 中的特定区域。每个效果图标为 32x32 像素。

**添加自定义效果图标**：需要模组或数据包配合注册新的状态效果。资源包负责提供对应的图标纹理。

## 七、GUI 开发优化

### 7.1 纹理尺寸优化

- **选择合适的尺寸**：GUI 纹理通常使用 256x256 或 512x512 像素。过大的纹理增加加载时间，过小的纹理在缩放时模糊。
- **使用 2 的幂次尺寸**：虽然非 2 的幂次纹理在现代 GPU 上也能工作，但 2 的幂次（128、256、512）可以提供更好的兼容性和性能。
- **减少空白区域**：在纹理图集中紧凑排列元素，减少无用的透明区域。

### 7.2 色彩管理

- **使用 sRGB 色彩空间**：Minecraft 的 GUI 纹理使用 sRGB 色彩空间。在图像编辑软件中工作时，建议使用 sRGB 模式。
- **颜色一致性**：确保不同纹理文件中的颜色保持一致。可以在编辑软件中创建调色板，统一管理颜色。
- **对比度测试**：在不同亮度的显示器上测试纹理的可读性。

### 7.3 版本适配

- **精灵系统适配**：如果你的资源包需要支持 1.19.3+ 版本，推荐使用精灵系统。
- **传统纹理适配**：同时保留传统纹理文件以支持旧版本。
- **使用 overlay 系统**：通过 1.20.2+ 的 overlay 系统管理不同版本的纹理。

### 7.4 文件组织

- 使用清晰的命名规范，便于管理和后期维护。
- 为每个容器界面创建单独的文件夹。
- 保留一份设计源文件（PSD、XCF 等）以便后期修改。

## 八、实践案例：创建自定义箱子界面

### 8.1 设计目标

创建一个带有深色木质边框和水晶风格背景的自定义箱子界面。

### 8.2 步骤 1：创建纹理文件

1. 复制原版 `container/chest.png`（256x256 像素）作为基础。
2. 在图像编辑软件中打开并修改：
   - 修改背景面板为深色木质纹理。
   - 调整槽位边框为金色。
   - 添加装饰性水晶边框。
   - 调整颜色以适应暗色主题。

### 8.3 步骤 2：预览纹理文件结构

使用 1.19.3+ 精灵系统时：

```
assets/minecraft/textures/gui/sprites/container/
├── chest_background.png      # 箱子背景面板
├── chest_background.png.mcmeta  # 九宫格定义
├── chest_slot.png            # 箱子槽位
└── chest_slot.png.mcmeta     # 槽位九宫格定义
```

### 8.4 步骤 3：`pack.mcmeta` 配置

```json
{
  "pack": {
    "pack_format": 15,
    "description": "定制GUI界面资源包"
  }
}
```

### 8.5 步骤 4：测试与调试

1. 在单机世界中放置箱子，测试纹理显示。
2. 检查不同 GUI 缩放比例下的显示效果。
3. 测试暗色模式切换。
4. 在多人服务器中测试兼容性。

## 九、常见问题与解决方案

### 9.1 纹理显示偏移

**现象**：GUI 元素显示位置不正确，与其他元素重叠。

**原因**：纹理尺寸或精灵区域定义不正确。

**解决方案**：
- 确保纹理的尺寸与原版一致。
- 精灵文件的 `.mcmeta` 中的九宫格参数需正确对应纹理实际布局。
- 检查精灵文件路径是否完全匹配原版路径。

### 9.2 纹理模糊或锯齿严重

**现象**：GUI 元素边缘模糊或有明显锯齿。

**解决方案**：
- 使用更高分辨率的纹理（如需）。
- 确保纹理设计时考虑了像素对齐。
- 为需要锐利边缘的元素使用像素级对齐绘制。
- 避免在纹理中使用半透明渐变进行抗锯齿。

### 9.3 暗色模式不生效

**现象**：切换到暗色模式后 GUI 仍然使用亮色纹理。

**原因**：未提供对应的暗色纹理文件，或版本不支持暗色模式。

**解决方案**：
- 提供 `*_dark.png` 命名的暗色版本纹理。
- 确认游戏版本支持暗色模式（1.16+）。
- 检查资源包优先级，确保你的包在其他包之上。

### 9.4 精灵系统兼容性

**现象**：资源包在 1.19.3+ 版本中 GUI 不显示或错乱。

**解决方案**：
- 删除 `textures/gui/` 顶层的大图文件（如 `widgets.png`）。
- 重新组织为精灵文件结构。
- 使用 overlay 系统管理不同版本的纹理目录。

## 十、小结

GUI 资源包开发是 Minecraft 资源包中最具视觉影响力的领域之一。通过本指南，你应当掌握了：

1. GUI 系统的目录结构和主要纹理文件的功能。
2. 暗色模式的实现方法和设计原则。
3. 精灵系统的原理和配置（1.19.3+）。
4. 九宫格缩放的原理和应用场景。
5. 自定义 GUI 元素的开发流程。
6. 纹理优化和版本兼容的策略。

GUI 开发需要耐心和细节把控，建议从简单的纹理替换开始，逐步深入到复杂的界面重设计，结合版本兼容策略，打造出优秀的 GUI 资源包。
