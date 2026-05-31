# 14. Recolourful Containers 3.1.1 (1.19.4+)

## 根目录结构

```
Recolourful Containers 3.1.1 (1.19.4+)/
├── pack.mcmeta
├── pack.png
├── respackopts.json5
├── assets/
│   ├── minecraft/
│   │   ├── font/default.json
│   │   ├── lang/             (100+ 语言文件)
│   │   ├── optifine/         (OptiFine 动画/CIT)
│   │   ├── optigui/          (OptiGUI 配置)
│   │   ├── shaders/include/interfaces.glsl
│   │   └── textures/gui/     (GUI 容器纹理 - 全部)
│   ├── (15+ 模组命名空间)/
│   └── (realms 等)/
├── 1.20.2-1.20.4/   (overlay)
├── 1.20.5-1.20.6/   (overlay)
├── 1.21.0-1.21.1/   (overlay)
├── -1.21.2_assets/  (overlay - 负号前缀)
├── 1.21.2-1.21.5/   (overlay)
├── 1.21.6-1.21.11/  (overlay)
└── 26.1/            (overlay)
```

## 包定位

Recolourful Containers (又名 rcGUI) 是由 Vi_Tul 开发的大型彩色 GUI 重制资源包 (3.1.1 版本)。其核心理念是给 Minecraft 的容器界面添加色彩——不同于原版的灰褐色容器背景，该包为每种容器 (箱子、熔炉、附魔台等) 赋予独特的色彩方案和视觉风格。目标用户是希望获得更鲜艳、更具个性游戏界面体验的玩家。该包支持从 1.19.4 到最新版本的广泛范围 (pack_format 0~99)，并包含对 15+ 模组的兼容。

## 关键文件说明

### pack.mcmeta

- **路径**: `pack.mcmeta`
- **pack_format**: 15 (通过 overlay 覆盖全版本)
- **supported_formats**: [0, 99] -- 覆盖几乎所有 Minecraft 版本
- **描述**: "Bring color to GUIs! By Vi_Tul"
- **自定义语言**: 定义了 "en_us_vanilla" 语言，名称 "English (Vanilla+)"

**Overlay 系统**：7 层 overlay 覆盖不同 pack_format 范围：

| Overlay 目录 | 格式范围 | 说明 |
|---|---|---|
| 1.20.2-1.20.4 | 18~31 | 1.20.2 至 1.20.4 |
| 1.20.5-1.20.6 | 32~33 | 1.20.5-1.20.6 (着色器 JSON 定义变化) |
| 1.21.0-1.21.1 | 34~41 | 1.21 早期版本 |
| -1.21.2_assets | 42~99 | 1.21.2+ 版本资产 (负号前缀排序用) |
| 1.21.2-1.21.5 | 42~56 | 1.21.2-1.21.5 版着色器 |
| 1.21.6-1.21.11 | 57~78 | 1.21.6+ 版着色器 (含新动画系统) |
| 26.1 | 79~99 | 最新版着色器与字体 |

### respackopts.json5

提供可配置选项:
- **HUD 元素开关**: 快捷栏、心、食物、护甲、空气、经验条
- **动画开关**: 铁砧、制图台、发射器、投掷器、附魔台、末影箱、熔炉火、锻造台、切石机
- **自定义精灵**: 村民按钮、信标按钮

### 自定义着色器核心: interfaces.glsl

- **路径**: `assets/minecraft/shaders/include/interfaces.glsl`
- **核心功能**: 实现 GPU 层面的 GUI 动态重排和动画

该着色器库定义了多功能着色器函数系统:

**一、`position_tex()` 函数**: 用于 position_tex 顶点着色器，处理 GUI 定位和 UV 坐标转换。

1. **自定义精灵颜色标记系统**: 通过采样纹理像素 RGBA 值进行行为路由:
   - Alpha=255: 跳过 (标准渲染)
   - Alpha=2 (color.g=1): 信标按钮/图标处理
     - color.b=1: 信标状态图标的位置偏移
     - color.b=2: 信标按钮的物理定位
   - Alpha=2 (color.g=2): 物品槽位 (青金石槽、锻造模板槽)
   - Alpha=2 (color.g=3): 合成器槽位
   - Alpha=2 (color.g=5): 村民交易槽
   - Alpha=2 (color.g=6): 配方书按钮

2. **位置检测机制**: 通过 posCheckX/Y() 函数使用 gl_VertexID % 4 确定顶点在四边形中的角位置，以屏幕坐标精确检测 GUI 元素位置，相应调整纹理 UV 和顶点位置。

**二、`rendertype_text()` 函数**: 用于 rendertype_text 顶点着色器，处理 GTx (GameText) 动画系统。

1. **动画系统**: 通过 animation() 和 applyAnimation() 函数实现基于 GameTime 的逐帧动画:
   - 信标光束动画 (8 帧)
   - 制图台动画 (11 帧、40 个自定义帧时间控制)
   - 末影箱动画 (9 帧)
   - 投掷器红石/活塞动画 (3~4 帧)
   - 发射器红石/弓动画 (3 帧)
   - 铁砧动画 (12 帧)
   - 锻造台动画 (12 帧)
   - 切石机动画 (2 帧)

2. **插值动画支持**: 部分动画使用线性插值实现帧间平滑过渡 (interpFactor + texCoordNext)。

3. **村民交易界面**: 特殊的村民动画 (8 帧、4 行布局、纹理偏移计算)

### rendertype_text.fsh

- **路径**: `1.21.6-1.21.11/assets/minecraft/shaders/core/rendertype_text.fsh`
- 实现文字颜色替换: 检测特定黄色 (#FEFE7A) 替换为深棕色 (#676849)
- 支持帧间插值混合

### font/default.json

- 使用 bitmap 字体定义自定义字符映射 (U+EB00~U+ECxx 私有使用区)
- 包含空格调整、空纹理、动画指南针、末影之眼等
- 使用 opti_vi_tul 命名空间的纹理作为字体贴图

### 语言文件

覆盖 100+ 语言，每个语言文件包含自定义 GUI 文本颜色的翻译键。

## 资源内容结构

```
assets/
├── minecraft/
│   ├── font/default.json
│   ├── lang/*.json
│   ├── optifine/anim/
│   ├── optigui/
│   ├── shaders/include/interfaces.glsl
│   └── textures/gui/
├── 15+ 模组命名空间/
```

### 模组兼容性

支持 15+ 模组: accessories, axiom, backslot, betterenchanting, cloth-config2, detailab, fabric, horseman, itemswapper, languagereload, modmenu, recursiveresources, sawmill, trinkets, watut.

## 技术特点

1. **GPU 驱动的 GUI 重排**: 核心技术创新。通过自定义 interfaces.glsl 着色器包含文件，在 GPU 层面 (顶点着色器) 动态计算 GUI 元素的位置、大小和纹理坐标。一个纹理贴图可驱动多个不同 GUI 布局。

2. **像素颜色 Alpha 通道行为路由**: 纹理中特定颜色值 (Alpha=1, 2, 254, 255) 作为控制信号，驱动着色器条件分支逻辑，实现 GUI 元素大小调整、偏移和纹理切换。

3. **帧动画系统**: 使用 GameTime 驱动的复杂帧动画，支持自定义帧序列、帧持续时间和帧间插值，超越普通 OptiFine 动画能力。

4. **OptiFine/OptiGUI 协同**: 同时使用 OptiFine 动画属性文件 (.properties + 精灵图) 和 OptiGUI 容器配置，提供多层后备方案。

5. **Bitmap 字体系统**: 使用 font/default.json 的 bitmap 字体提供额外精灵渲染通道，通过 Unicode 私有使用区 (PUA) 字符映射 GUI 元素。

6. **多 overlay 版本管理**: 7 层 overlay 覆盖 1.19.4 到最新版本，每层仅包含该版本所需的着色器/纹理变化，最小化冗余。

## 结论

Recolourful Containers 3.1.1 是一个技术深度极高的 GUI 重制资源包。其核心创新在于使用自定义 GLSL 着色器包含文件 (interfaces.glsl) 在 GPU 层面动态控制 GUI 布局，这代表了 Minecraft 资源包开发中"着色器驱动 UI"的前沿技术方向。配合 OptiFine 动画、Bitmap 字体系统、百种语言支持和丰富的模组兼容性，该包在视觉效果和技术实现上都达到很高水准。