# 19. cubic-sun-moon-v1.8.5

## 根目录结构

```
cubic-sun-moon-v1.8.5/
├── pack.mcmeta
├── pack.png
├── pack.txt
├── LICENSE.txt
├── art/
│   └── kz.png
├── terrain/
│   ├── sun.png
│   ├── moon.png
│   └── moon_phases.png
├── assets/
│   ├── minecraft/
│   │   ├── texts/
│   │   │   └── splashes.txt
│   │   └── textures/
│   │       ├── environment/
│   │       │   ├── sun.png
│   │       │   ├── moon_phases.png
│   │       │   ├── earth.png
│   │       │   ├── earth_1.png
│   │       │   ├── earth_a.png
│   │       │   ├── earth_prime.png
│   │       │   └── celestial/
│   │       │       ├── sun.png
│   │       │       └── moon/
│   │       │           ├── full_moon.png
│   │       │           ├── new_moon.png
│   │       │           ├── first_quarter.png
│   │       │           ├── third_quarter.png
│   │       │           ├── waning_crescent.png
│   │       │           ├── waning_gibbous.png
│   │       │           ├── waxing_crescent.png
│   │       │           └── waxing_gibbous.png
│   │       └── painting/
│   │           ├── burning_skull.png
│   │           └── paintings_kristoffer_zetterstrand.png
│   ├── ad_astra/
│   │   └── textures/environment/
│   │       ├── sun.png
│   │       ├── blue_sun.png
│   │       ├── red_sun.png
│   │       ├── backlight.png
│   │       ├── earth.png
│   │       ├── mars.png
│   │       ├── moon.png
│   │       ├── mercury.png
│   │       ├── venus.png
│   │       ├── glacio.png
│   │       ├── deimos.png
│   │       ├── phobos.png
│   │       └── vicinus.png
│   ├── astrocraft/
│   │   └── textures/
│   │       ├── glare.png
│   │       └── planets/
│   │           ├── banded.png
│   │           ├── cloudy-phases.png
│   │           ├── moon.png
│   │           ├── ring.png
│   │           ├── rocky-phases.png
│   │           └── smooth.png
│   ├── galacticraftcore/
│   │   └── textures/gui/
│   │       ├── celestialbodies/
│   │       │   ├── sun.png
│   │       │   ├── moon.png
│   │       │   ├── mercury.png
│   │       │   ├── venus.png
│   │       │   ├── mars.png
│   │       │   ├── jupiter.png
│   │       │   ├── saturn.png
│   │       │   ├── saturn_rings.png
│   │       │   ├── uranus.png
│   │       │   ├── uranus_rings.png
│   │       │   └── neptune.png
│   │       └── planets/
│   │           ├── sun.png
│   │           ├── atmosphericsun.png
│   │           ├── orbitalsun.png
│   │           └── moon.png
│   └── stellarview/
│       └── textures/environment/
│           ├── halo_template.png
│           ├── moon.png
│           ├── moon_phases.png
│           ├── moon_halo_phases.png
│           └── planet/sol/
│               ├── mercury.png
│               ├── venus.png
│               ├── mars.png
│               ├── jupiter.png
│               ├── saturn.png
│               ├── uranus.png
│               └── neptune.png
```

## 概述

Cubic Sun & Moon（立体太阳与月亮）由 JoeFly 制作，版本 v1.8.5。这是一个"纯纹理替换"型环境资源包，唯一的修改目标是将 Minecraft 中默认的太阳和月亮从正方形精灵图（sprite）替换为具有立体感的球体纹理。

pack.mcmeta 的 pack_format 为 15（Minecraft 1.20+），通过 supported_formats: [1, 75] 声明了对几乎所有 Minecraft 版本（从远古版本到未来版本）的兼容性——这是极为宽泛的版本声明，体现了该包仅替换纹理、不涉及任何格式敏感资源的特性。

包内共包含 72 个文件，其中大部分是 PNG 纹理图片。

## 跨模组兼容性架构

cubic-sun-moon 最突出的特征是广泛的多模组兼容性。它同时为 5 个不同的命名空间提供纹理资源：

### 1. `minecraft`（原版）
- 替换了 `textures/environment/sun.png` 和 `moon_phases.png`
- 新增了 8 张独立月相纹理（`celestial/moon/` 目录）
- 新增了独立的 `celestial/sun.png`
- 额外包含 4 张"地球"风格纹理（earth.png、earth_1.png、earth_a.png、earth_prime.png）
- 替换了画作纹理（增加了 3D 风格画作）

### 2. `ad_astra`（Ad Astra 星球旅行模组）
- 为该模组的各个天体提供 3D 纹理
- 包括太阳（蓝太阳、红太阳两种变体）、背光、地球、火星、月亮、水星、金星、Glacio、火卫一（Deimos）、火卫二（Phobos）、Vicinus

### 3. `astrocraft`（AstroCraft 模组）
- 提供强光（glare）纹理和多种行星类别纹理
- 行星类型包括 banded（带状）、cloudy-phases（云层月相）、moon（月亮）、ring（环状）、rocky-phases（岩石月相）、smooth（光滑）

### 4. `galacticraftcore`（Galacticraft 经典太空模组）
- 替换 GUI 天球图中的天体图标
- 覆盖太阳系八大行星（水星到海王星）以及土星环和天王星环
- 额外提供大气太阳、轨道太阳和月亮等环境的 GUI 纹理

### 5. `stellarview`（Stellar View 模组）
- 提供光晕模板、月亮光晕月相、月亮月相等环境纹理
- 提供太阳系行星的贴图（位于 `planet/sol/`），使用类似 NASA 的真实风格

## 纹理设计分析

### 核心实现：立体太阳/月亮

传统 Minecraft 中，太阳和月亮是被渲染为屏幕对齐的精灵图（billboard sprite）——一个永远面向玩家的正方形纹理。cubic-sun-moon 本质上并不改变渲染方式，而是通过**纹理绘画技巧**创造出立体的视觉错觉。

**太阳纹理**：
- 使用径向渐变绘制圆形球体
- 中心亮黄色/白色向边缘渐变为橙色/红色
- 添加微妙的纹理细节模拟太阳表面活动
- 四角为透明，使圆形太阳从方形纹理中凸显

**月亮纹理**：
- 使用灰白色调的圆形球体
- 通过光影模拟出凹凸不平的月面质感
- 月相通过独立纹理的明暗区域分布实现
- 最大特色是月面上的陨石坑细节

### Legacy 兼容

`terrain/` 目录下的 sun.png、moon.png、moon_phases.png 是为了兼容更早期的 Minecraft 版本（如 alpha/beta 时期版本）而保留的。这些目录不在现代资源包的标准结构中，属于向前兼容的遗产资源。

### 画作纹理

包内包含两张画作纹理替换，其中 `paintings_kristoffer_zetterstrand.png` 可能加入了 3D 太阳/月亮元素到经典画作中。

### 多版本地球纹理

`earth.png` 及其变体（earth_1.png、earth_a.png、earth_prime.png）可能对应不同的模组或不同的渲染需求，提供了多种"从太空看地球"的视觉效果。

## 兼容性优势

cubic-sun-moon 的跨模组架构带来显著优势：

1. **一套安装，到处生效**：用户只需安装此包，所有已安装的太空模组都会自动获得 3D 太阳/月亮纹理。
2. **视觉一致性**：不同模组中的同一颗行星（如火星）在不同模组界面中拥有统一的视觉效果。
3. **低冲突风险**：仅替换纹理文件，不涉及任何 JSON 配置、模型或着色器，因此几乎不会与其他资源包发生冲突。

## 版本声明分析

supported_formats: [1, 75] 是一个极端的版本范围。format 1 对应 Minecraft 1.6.1（Java Edition 的第一个资源包版本），format 75+ 对应未来尚未发布的版本。这种声明方式之所以可行，是因为该包仅包含 textures 资源，而纹理文件在不同版本间的格式变化极小。

不过，`celestial/moon/` 子目录下的独立月相纹理使用了 `textures/environment/celestial/` 路径，这是 1.21+ 才引入的新月相系统路径。在旧版本中，这些文件会被忽略，只有 sun.png 和 moon_phases.png 生效。

## 艺术风格

cubic-sun-moon 的艺术风格偏向写实与 stylized 的折中：
- 太阳具有炽热的动态感，色彩丰富
- 月亮具有细腻的陨石坑和反照率变化
- 行星纹理参考了真实天体的外观（如木星的条纹、土星的光环）
- 保持 16x16 及更高分辨率以适应不同模组的渲染需求

## 其他内容

- `splashes.txt`：替换了游戏标题画面的闪屏文本，包含对作者 JoeFly 的订阅号召（"Subscribe to JoeFly!"多次出现）以及各种幽默文本如 "3D Moon!"、"3D Sun!"、"Hello There!" 等。
- `LICENSE.txt`：包含许可证信息。
- `art/kz.png`：可能是作者或贡献者的艺术标识。
- `pack.png`：资源包选择界面的缩略图。

## 总结

Cubic Sun & Moon 是一个精悍而高效的环境美化资源包。虽然它只有一个简单的目标——让太阳和月亮看起来是立体的——但它通过覆盖 5 个不同模组的命名空间，实现了广泛的兼容性。它完美诠释了"纹理替换类资源包"的核心理念：通过最小的技术投入（仅替换 PNG 文件），获得最大的视觉回报。其支持的模组涵盖 Ad Astra、AstroCraft、Galacticraft 和 Stellar View 四大太空模组生态，是太空主题整合包中不可或缺的视觉增强组件。
