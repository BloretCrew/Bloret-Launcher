"""
资源包知识库

从 Minecraft-Resourcepacks-Research 研究文档中提取的结构化知识，
供 Agent 系统提示词和工具使用。
"""

# ============================================================
# pack_format 版本对照表
# ============================================================

PACK_FORMAT_TABLE = {
    1: "1.6.1",
    2: "1.6.2 - 1.7.2",
    3: "1.7.2 - 1.7.10",
    4: "1.8 - 1.8.9",
    5: "1.9 - 1.10.2",
    6: "1.11 - 1.12.2",
    7: "1.13 - 1.14.4",
    8: "1.15 - 1.16.1",
    9: "1.16.2 - 1.16.5",
    15: "1.17 - 1.17.1",
    18: "1.18 - 1.18.1",
    19: "1.18.2",
    22: "1.19 - 1.19.2",
    25: "1.19.3",
    26: "1.19.4",
    32: "1.20 - 1.20.1",
    34: "1.20.2",
    36: "1.20.3 - 1.20.4",
    41: "1.20.5 - 1.20.6",
    42: "1.21 - 1.21.1",
    46: "1.21.2 - 1.21.3",
    47: "1.21.4",
    48: "1.21.5",
    49: "1.21.6",
}

# pack_format 到 pack_format 范围的映射（用于 supported_formats）
PACK_FORMAT_RANGES = {
    "1.20.2-1.20.4": {"min": 34, "max": 36},
    "1.20-1.20.1": {"min": 32, "max": 32},
    "1.21-1.21.1": {"min": 42, "max": 42},
    "1.21.2-1.21.3": {"min": 46, "max": 46},
    "1.21.4": {"min": 47, "max": 47},
}

# ============================================================
# 标准目录结构
# ============================================================

DIRECTORY_GUIDE = """
## 资源包标准目录结构

```
<资源包根目录>/
  pack.mcmeta          # 必须 - 资源包元数据
  pack.png             # 推荐 - 资源包图标 (推荐 128x128 或 256x256 PNG)
  assets/
    <命名空间>/         # 默认 "minecraft" 用于覆盖原版资源
      textures/         # 纹理资源
        block/          # 方块纹理 (16x16 标准)
        item/           # 物品纹理 (16x16 标准)
        entity/         # 实体纹理 (尺寸不固定)
        gui/            # GUI 纹理
        misc/           # 杂项纹理
        particle/       # 粒子纹理
        font/           # 字体纹理
        map/            # 地图纹理
        painting/       # 画作纹理
        environment/    # 环境纹理 (天空、太阳、月亮)
        models/         # 模型相关纹理 (如盔甲)
        mob_effect/     # 药水效果图标
        trims/          # 盔甲装饰纹理
      models/           # 模型定义 (JSON)
        block/          # 方块模型
        item/           # 物品模型
      blockstates/      # 方块状态映射 (JSON)
      items/            # 物品模型映射 (1.21.2+ 新机制)
      equipment/        # 装备模型 (1.21.2+)
      lang/             # 语言文件 (JSON key-value)
      font/             # 字体定义 (JSON)
      sounds/           # 声音文件 (.ogg)
      sounds.json       # 声音事件定义
      particles/        # 粒子纹理定义 (JSON)
      texts/            # 文本资源
        splashes.txt    # 标语
        end.txt         # 终末之诗
        credits.json    # 鸣谢
      shaders/          # GLSL 着色器
        core/           # 核心着色器
        post/           # 后处理着色器
      post_effect/      # 后处理管线配置
      atlases/          # 纹理图集定义
```

### 非标准但常见的目录（OptiFine 扩展）

```
assets/minecraft/optifine/
  cem/                # 自定义实体模型 (.jem/.jpm)
  cit/                # 自定义物品纹理 (.properties)
  ctm/                # 连接纹理 (.properties)
  colormap/           # 颜色映射
  labpbr/             # PBR 材质
```

### 覆盖层目录（1.21.2+）

```
<根目录>/
  overlay_<格式范围>/  # 例如 overlay_1_21_2-1_21_3/
    assets/...
```
""".strip()


# ============================================================
# 文件格式规范
# ============================================================

FILE_FORMAT_SPECS = {
    "texture": {
        "format": "PNG-32 (RGBA, 8-bit/channel)",
        "size_rules": [
            "必须是 2 的幂次方 (16, 32, 64, 128, 256, 512...)",
            "原版标准: 16x16 (方块/物品), 64x32 (实体), 不固定 (GUI)",
            "高分辨率包: 32x32, 64x64, 128x128, 256x256, 512x512",
        ],
        "naming": "小写字母 + 下划线, 与方块/物品 ID 对齐",
        "animation": "垂直堆叠帧 + .png.mcmeta 配置文件",
        "mcmeta_format": """{
  "animation": {
    "frametime": 2,           # 每帧持续 tick 数 (1tick=50ms)
    "interpolate": false,     # 是否在帧之间插值
    "frames": [0, 1, 2, 3]   # 帧索引数组, 或 [{index:0, time:3}, ...]
  }
}""",
    },
    "model": {
        "format": "JSON",
        "key_fields": ["parent", "textures", "elements", "display", "gui_light"],
        "parent_chain": "支持继承链, 如 block/cube_all → block/cube → builtin/entity",
        "texture_variable": "#变量名 引用 textures 中定义的纹理",
        "display_positions": ["thirdperson_righthand", "thirdperson_lefthand",
                              "firstperson_righthand", "firstperson_lefthand",
                              "gui", "head", "fixed", "ground"],
    },
    "blockstate": {
        "format": "JSON",
        "systems": {
            "variants": "按方块状态字符串映射到模型, 支持随机模型数组",
            "multipart": "组合渲染, 适用于栅栏、红石等多状态方块",
        },
    },
    "sound": {
        "format": "OGG Vorbis (仅支持此格式)",
        "sample_rate": "推荐 44100Hz, 环境音可降至 22050Hz",
        "channels": "单声道=空间音效, 立体声=音乐/环境",
        "sounds_json": """{
  "event_name": {
    "replace": false,              # 是否替换已有声音
    "subtitle": "subtitles.event", # 字幕翻译键
    "sounds": [
      {
        "name": "namespace:path/to/sound",
        "volume": 1.0,             # 音量 0.0-1.0
        "pitch": [0.8, 1.2],      # 音高, 固定值或范围
        "weight": 1,               # 权重 (随机选择概率)
        "stream": false,           # 流式加载 (长音频建议 true)
        "attenuation_distance": 16, # 衰减距离
        "preload": false,          # 是否预加载
        "type": "sound"            # sound 或 event
      }
    ]
  }
}""",
    },
    "language": {
        "format": "JSON (flat key-value)",
        "naming": "xx_yy.json (如 zh_cn.json, en_us.json)",
        "key_pattern": "type.minecraft.id (如 block.minecraft.stone)",
        "placeholders": "%s %d %f %n$s (n=参数位置)",
        "format_codes": "§0-§f 颜色, §l 粗体, §o 斜体, §n 下划线, §m 删除线, §k 混淆, §r 重置",
        "colors": {
            "§0": "黑色", "§1": "深蓝", "§2": "深绿", "§3": "深青",
            "§4": "深红", "§5": "紫色", "§6": "金色", "§7": "灰色",
            "§8": "深灰", "§9": "蓝色", "§a": "绿色", "§b": "青色",
            "§c": "红色", "§d": "粉色", "§e": "黄色", "§f": "白色",
        },
    },
    "font": {
        "format": "JSON",
        "provider_types": ["bitmap", "ttf", "space", "reference", "unihex", "legacy_unicode"],
    },
    "shader": {
        "format": "GLSL 150 (.vsh, .fsh, .glsl) + JSON config",
        "render_stages": [
            "rendertype_solid", "rendertype_cutout", "rendertype_translucent",
            "rendertype_entity_solid", "rendertype_entity_cutout",
            "rendertype_entity_translucent", "rendertype_glint",
            "rendertype_entity_glint", "rendertype_beacon_beam",
        ],
    },
    "particle": {
        "format": "JSON",
        "note": "只能修改已有粒子类型的纹理列表, 不能添加新粒子类型",
    },
}


# ============================================================
# 纹理制作规范
# ============================================================

TEXTURE_GUIDELINES = """
## 纹理制作规范

### 尺寸标准
- 1x (16x16): 原版风格, 性能最优, 兼容性最广
- 2x (32x32): 常见高质量选择, 性能影响可控
- 4x (64x64): 高质量, 需要考虑目标用户硬件
- 8x (128x128): 专业级, 显存占用明显增加
- 16x (256x256) 及以上: 仅在必要时使用

### Alpha 通道模式
- Opaque (不透明): alpha=255, 完全不透明
- Cutout (裁剪): alpha=0 或 255, 无半透明 (树叶、草)
- Translucent (半透明): 0 < alpha < 255 (水、玻璃、传送门)

### 光照方向约定
- 光源方向: 左上方
- 顶面: 最亮
- 右面/前面: 中等亮度
- 左面/背面: 较暗
- 底面: 最暗

### 动画纹理
- 帧垂直堆叠在同一个 PNG 文件中
- 每帧宽度 = 纹理宽度, 高度 = 纹理高度
- 总高度 = 帧数 × 单帧高度
- 配置文件: <纹理名>.png.mcmeta
- 帧率计算: FPS = 20 / frametime

### 命名规范
- 小写字母 + 下划线: stone_bricks.png
- 与方块/物品 ID 对齐: diamond_sword.png
- 自定义资源带命名空间前缀: mypack_custom_sky.png
- 避免: 大写字母、空格、特殊字符、中文
""".strip()


# ============================================================
# 模型开发规范
# ============================================================

MODEL_GUIDELINES = """
## 模型开发规范

### JSON 模型基础结构
```json
{
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "minecraft:block/stone"
  },
  "elements": [...],
  "display": {...},
  "gui_light": "front"
}
```

### 常用 parent 模型
- block/cube_all: 六面相同纹理的方块
- block/cube_column: 顶面/侧面不同 (原木、石英)
- block/cube_bottom_top: 顶面/底面/侧面不同 (工作台)
- block/cross: 十字交叉 (花、草)
- block/slab: 半砖
- block/stairs: 楼梯
- block/fence: 栅栏
- item/generated: 物品默认 (layer0-layer4)
- item/handheld: 手持物品 (剑、工具)

### 元素 (elements) 定义
```json
{
  "from": [0, 0, 0],
  "to": [16, 16, 16],
  "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": false},
  "shade": true,
  "faces": {
    "north": {"uv": [0, 0, 16, 16], "texture": "#all", "cullface": "north"},
    "south": {"uv": [0, 0, 16, 16], "texture": "#all"},
    "east": {"uv": [0, 0, 16, 16], "texture": "#all"},
    "west": {"uv": [0, 0, 16, 16], "texture": "#all"},
    "up": {"uv": [0, 0, 16, 16], "texture": "#all"},
    "down": {"uv": [0, 0, 16, 16], "texture": "#all"}
  }
}
```

### 物品模型覆盖 (1.21.2+)
```json
{
  "parent": "minecraft:item/generated",
  "textures": {"layer0": "minecraft:item/custom_model_data"},
  "overrides": [
    {"predicate": {"custom_model_data": 1}, "model": "minecraft:item/model1"},
    {"predicate": {"custom_model_data": 2}, "model": "minecraft:item/model2"}
  ]
}
```

### 方块状态 (blockstates)
- variants: 按状态字符串映射模型
- multipart: 组合渲染 (栅栏、红石)
- 支持随机模型数组 (带 weight 权重)
""".strip()


# ============================================================
# 声音开发规范
# ============================================================

SOUND_GUIDELINES = """
## 声音开发规范

### 格式要求
- 仅支持 OGG Vorbis 格式
- 采样率: 推荐 44100Hz, 环境音可降至 22050Hz
- 单声道 = 空间音效 (有方向感)
- 立体声 = 音乐/环境音 (无方向感)

### 声音分类
- ambient: 环境音 (洞穴、天气)
- entity: 实体音效 (怪物、玩家)
- block: 方块音效 (挖掘、放置)
- item: 物品音效 (使用、吃)
- ui: 界面音效 (按钮、通知)
- music: 背景音乐

### sounds.json 关键字段
- name: 声音文件路径 (不含 .ogg 后缀, 含命名空间)
- volume: 音量 (0.0-1.0, 或范围如 [0.8, 1.2])
- pitch: 音高 (默认 1.0, 或范围如 [0.8, 1.2])
- weight: 随机选择权重
- stream: 流式加载 (长音频建议 true, 减少内存)
- attenuation_distance: 衰减距离 (默认 16)
- preload: 是否预加载
- replace: 是否替换已有声音事件
- subtitle: 字幕翻译键

### 优化建议
- 使用 44100Hz 或 22050Hz 采样率
- 循环音效应包含干净的循环点
- 长音频使用 stream: true
- 使用 Audacity 或 FFmpeg 压缩
""".strip()


# ============================================================
# 语言文件规范
# ============================================================

LANGUAGE_GUIDELINES = """
## 语言文件规范

### 文件格式
- 路径: assets/<namespace>/lang/<locale>.json
- 格式: JSON flat key-value
- 编码: UTF-8

### 翻译键命名模式
- 方块: block.minecraft.<id> (如 block.minecraft.stone)
- 物品: item.minecraft.<id> (如 item.minecraft.diamond_sword)
- 实体: entity.minecraft.<id> (如 entity.minecraft.zombie)
- GUI: gui.<功能> (如 gui.done, gui.cancel)
- 选项: options.<选项名> (如 options.music)
- 按键: key.<动作> (如 key.forward)
- 死亡: death.attack.<类型> (如 death.attack.mob)
- 命令: commands.<命令名> (如 commands.give.success)

### 格式化占位符
- %s: 字符串
- %d: 整数
- %f: 浮点数
- %n$s: 第 n 个参数 (从 1 开始), 用于重排参数顺序

### § 格式化代码
- §0-§f: 颜色 (见颜色表)
- §l: 粗体
- §o: 斜体
- §n: 下划线
- §m: 删除线
- §k: 混淆 (随机字符)
- §r: 重置所有格式

### 重要规则
- 语言文件可以只覆盖部分键 (不必提供完整翻译)
- 合并行为: 按键覆盖和补齐
- 自定义语言需要在 pack.mcmeta 的 language 字段注册
- deprecated.json 标记弃用或重命名的翻译键
""".strip()


# ============================================================
# GUI 纹理规范
# ============================================================

GUI_GUIDELINES = """
## GUI 纹理规范

### 核心文件
- textures/gui/widgets.png: 按钮、滑块等控件
- textures/gui/icons.png: HUD 图标 (生命、护甲、饥饿等)
- textures/gui/container/: 容器界面 (箱子、工作台等)
- textures/gui/title/: 标题画面

### 精灵系统 (1.19.3+)
- textures/gui/sprites/: 精灵图目录
- 支持 .mcmeta 定义九宫格缩放 (nine-slice)
- 后缀 _dark.png: 暗色模式自动切换

### 暗色模式实现
- 在原文件同目录放置 _dark.png 后缀文件
- 游戏在暗色模式下自动加载 _dark.png 版本
- 例如: widget.png → widget_dark.png

### widgets.png 布局
- 按钮: 200x20 像素, 3 行 (正常/悬停/禁用)
- 滑块: 滑块轨道 + 滑块头
- 复选框: 选中/未选中状态

### icons.png 布局
- 每个图标 9x9 像素
- 行: 生命值、护甲值、饥饿值、经验条、氧气等
- 支持容器/背景/硬化/亡灵等变体
""".strip()


# ============================================================
# OptiFine 扩展规范
# ============================================================

OPTIFINE_GUIDELINES = """
## OptiFine 扩展规范

### CEM (Custom Entity Models)
- 路径: assets/minecraft/optifine/cem/<entity>.jem
- 格式: JSON, 定义实体模型的几何体和动画
- 附件模型: <entity>/<part>.jpm
- 动画变量: limbSwing, headYaw, health, timer 等
- 支持 JavaScript 风格脚本 (Math.sin, Math.cos 等)

### CIT (Custom Item Textures)
- 路径: assets/minecraft/optifine/cit/<name>.properties
- 按条件替换物品纹理 (附魔、名称、NBT 等)
- 关键属性: type, items, texture, model, damage, stackSize, enchantment, nbt

### CTM (Connected Textures)
- 路径: assets/minecraft/optifine/ctm/<name>.properties
- 连接纹理: 方块根据相邻方块自动选择纹理
- 方法: ctm, random, repeat, fixed, horizontal, vertical, top, etc.
- 47-tile atlas 标准布局

### Colormap
- 路径: assets/minecraft/optifine/colormap/
- 颜色映射: 根据生物群系和高度动态着色
- 文件: foliage.png, grass.png, water.png 等

### labPBR
- PBR 材质贴图
- 法线贴图、高光贴图、视差贴图等
""".strip()


# ============================================================
# 覆盖层系统
# ============================================================

OVERLAY_GUIDE = """
## 覆盖层系统 (Overlays)

### 概述
覆盖层系统允许在同一资源包内为不同 Minecraft 版本提供不同资源。
从 1.21.2 开始支持。

### 配置方式
在 pack.mcmeta 中定义:
```json
{
  "pack": {
    "pack_format": 46,
    "description": "My Pack"
  },
  "overlays": {
    "entries": [
      {
        "directory": "overlay_1_21_2-1_21_3",
        "formats": {"min_inclusive": 46, "max_inclusive": 46}
      },
      {
        "directory": "overlay_1_21_4",
        "formats": {"min_inclusive": 47, "max_inclusive": 47}
      }
    ]
  }
}
```

### 目录结构
```
<根目录>/
  pack.mcmeta
  assets/...           # 基础资源 (最低版本)
  overlay_1_21_2-1_21_3/
    assets/...         # 1.21.2-1.21.3 特定资源
  overlay_1_21_4/
    assets/...         # 1.21.4 特定资源
```

### 加载逻辑
- 游戏根据当前版本的 pack_format 选择匹配的覆盖层目录
- 覆盖层中的资源覆盖基础资源
- 未匹配的版本使用基础资源

### Filter 系统
在 pack.mcmeta 中定义:
```json
{
  "pack": {...},
  "filter": {
    "block": [
      {"namespace": "minecraft", "path": "textures/block/.*"},
      {"namespace": "other_mod", "path": ".*"}
    ]
  }
}
```
- block: 阻止匹配的资源被加载
- 用于排除低优先级数据包中的资源
""".strip()


# ============================================================
# 质量评估标准
# ============================================================

QUALITY_CHECKLIST = """
## 资源包质量评估维度 (每项 1-5 分, 3 分合格)

### 1. 结构规范性 (25%)
- [ ] pack.mcmeta 存在且 JSON 格式正确
- [ ] pack_format 与目标游戏版本匹配
- [ ] 目录结构与 assets/<namespace>/ 规范一致
- [ ] 无游离文件 (.DS_Store, Thumbs.db, .git)
- [ ] 命名空间不含大写字母或特殊字符

### 2. 命名一致性 (20%)
- [ ] 所有文件名使用小写字母
- [ ] 多词连接风格统一 (下划线或连字符)
- [ ] 自定义资源带命名空间前缀
- [ ] 目录名与文件名风格一致

### 3. 性能友好性 (20%)
- [ ] 纹理分辨率在目标范围内
- [ ] 无不必要的超大纹理
- [ ] 模型面数合理
- [ ] 声音文件已压缩
- [ ] 着色器有兼容性说明

### 4. 兼容性考虑 (20%)
- [ ] pack_format 已正确设置
- [ ] supported_formats 范围合理
- [ ] 模组兼容性已测试或声明
- [ ] 不与其他资源包严重冲突

### 5. 文档完整性 (15%)
- [ ] README.md 存在且内容完整
- [ ] 包含支持的游戏版本信息
- [ ] 包含安装说明
- [ ] 许可证已声明
""".strip()


# ============================================================
# 常见错误速查
# ============================================================

COMMON_ERRORS = """
## 常见错误速查表

| 症状 | 可能原因 | 解决方法 |
|------|---------|---------|
| 资源包不显示 | 缺少 pack.mcmeta 或 JSON 格式错误 | 检查文件存在性和 JSON 语法 |
| 纹理显示为紫黑色 | 纹理路径错误或文件名不匹配 | 核对路径与文件名 (区分大小写) |
| 模型显示异常 | JSON 模型语法错误或引用了不存在的纹理 | 验证 JSON 结构和纹理引用 |
| 语言不生效 | 语言文件路径错误或 JSON 格式错误 | 检查 lang/<locale>.json 路径和内容 |
| 声音不播放 | 声音事件未在 sounds.json 中注册 | 检查 sounds.json 的事件定义 |
| 游戏崩溃 | 着色器编译错误或模型面数异常 | 移除自定义着色器或简化模型 |
| 动画不工作 | .mcmeta 文件格式错误或帧数不匹配 | 检查 .mcmeta 的 frames 和尺寸 |
| 物品模型不显示 | 模型继承链断裂或 texture 变量未定义 | 检查 parent 链和 textures 定义 |
| 方块状态错误 | blockstate JSON 格式错误或缺少默认状态 | 验证 variants/multipart 格式 |
| 声音循环有杂音 | 循环点不干净 | 用 Audacity 重新编辑循环点 |
""".strip()


# ============================================================
# 开发工作流指导
# ============================================================

DEVELOPMENT_WORKFLOW = """
## 资源包开发工作流

### 阶段 1: 规划
1. 明确资源包类型 (纯纹理/模型改造/声音替换/综合型)
2. 确定目标分辨率 (16x/32x/64x/更高)
3. 确定目标 Minecraft 版本 (单版本/多版本区间)
4. 列出需要修改的资源清单
5. 确定命名空间 (建议使用独立命名空间)

### 阶段 2: 搭建骨架
1. 创建 pack.mcmeta (正确设置 pack_format 和 supported_formats)
2. 创建 assets/<namespace>/ 目录结构
3. 添加 pack.png (可选但推荐)
4. 在游戏中加载测试, 确认被正确识别

### 阶段 3: 资源制作 (从简单到复杂)
1. 纹理替换 — 最基础, 立竿见影
2. 模型修改 — 需要理解 JSON 模型语法
3. 语言文件 — 相对独立, 可并行进行
4. 声音替换 — 需要音频处理工具
5. 高级功能 — 着色器、粒子、字体等

### 阶段 4: 测试与优化
1. 功能测试: 所有资源正确显示/播放
2. 兼容性测试: 与其他资源包/模组叠加
3. 性能测试: 加载时间、帧率影响
4. 按 F3+T 重新加载资源包, 无需重启游戏

### 阶段 5: 文档与发布
1. 编写 README.md
2. 删除无关文件 (.git, .psd 等)
3. 打包为 .zip
4. 发布到 Modrinth/CurseForge/GitHub
""".strip()


# ============================================================
# Agent 系统提示词模板
# ============================================================

AGENT_SYSTEM_PROMPT_TEMPLATE = """你是 Bloret Launcher 资源包编辑器的 AI 助手 BLPRE Copilot。你是 Minecraft Java 版资源包开发专家，精通资源包的结构规范、文件格式、开发流程和最佳实践。

你当前正在编辑的资源包: {pack_path}

## 你的核心知识

### 资源包本质
资源包是"资源覆盖层系统"。游戏先读 pack.mcmeta 判断版本兼容性，然后按优先级从上到下加载资源。同路径资源被高优先级包覆盖。

### pack_format 版本对照 (常用)
- 22: 1.20.3-1.20.4
- 32: 1.20.5-1.20.6
- 34: 1.21-1.21.1
- 42: 1.21.2-1.21.3
- 46: 1.21.4
- 47: 1.21.5
- 48: 1.21.6
(完整表可通过 get_mc_reference 工具查询)

### 标准目录结构
assets/<namespace>/ 下的标准目录:
- textures/ (block/item/entity/gui/...) — 纹理资源 (PNG, RGBA, 2的幂次方尺寸)
- models/ (block/item/) — 模型定义 (JSON, 支持 parent 继承)
- blockstates/ — 方块状态映射 (variants 或 multipart)
- items/ — 物品模型映射 (1.21.2+ 新机制)
- equipment/ — 装备模型 (1.21.2+)
- lang/ — 语言文件 (JSON key-value, 可部分覆盖)
- font/ — 字体定义 (bitmap/ttf/space/reference/unihex)
- sounds/ + sounds.json — 声音文件 (仅 OGG) + 事件定义
- particles/ — 粒子纹理定义
- texts/ — 文本资源 (splashes.txt, end.txt, credits.json)
- shaders/ — GLSL 着色器
- atlases/ — 纹理图集定义

### 文件格式要点
- 纹理: PNG-32 RGBA, 必须2的幂次方尺寸 (16/32/64/128/256/512)
- 模型: JSON, 支持 parent 继承链 (如 cube_all → cube → builtin/entity)
- 声音: 仅 OGG Vorbis, 推荐 44100Hz
- 语言: JSON flat key-value, 支持 § 格式化代码和 %s/%d 占位符
- 着色器: GLSL 150 (.vsh/.fsh)
- 动画: 垂直堆叠帧 + .png.mcmeta 配置

### 质量五维度
1. 结构规范性 (25%): 遵循 Minecraft 目录约定
2. 命名一致性 (20%): 文件名风格统一
3. 性能友好性 (20%): 纹理尺寸合理, 模型面数适中
4. 兼容性考虑 (20%): 版本范围明确, 模组兼容
5. 文档完整性 (15%): README、LICENSE、CHANGELOG

## 你的能力 (通过工具调用)

- read_file: 读取文件内容
- write_file: 写入文件 (注意: PNG 需要二进制, JSON 需要 UTF-8)
- edit_file: 精确替换文件中的文本
- list_files: 列出匹配 glob 模式的文件 (如 **/*.json, textures/**/*.png)
- search_text: 搜索文件内容 (如搜索翻译键、纹理路径引用)
- get_pack_info: 获取资源包基本信息
- analyze_pack: 分析资源包结构和统计
- read_language: 读取语言文件 (指定语言代码)
- edit_language: 编辑语言文件 (添加/修改/删除条目)
- validate_json: 验证 JSON 格式
- get_file_tree: 获取文件树结构
- ask_user: 向用户提问 (支持单选、多选、文本输入)
- execute_command: 前台执行终端命令
- execute_command_background: 后台执行终端命令
- spawn_agent: 生成子 Agent (explore=只读探索, plan=规划, general=通用)
- get_mc_reference: 查询 Minecraft 资源包技术参考 (版本对照、目录规范、文件格式等)
- validate_mcmeta_advanced: 对 pack.mcmeta 进行深度验证
- create_resource_template: 创建标准资源模板文件

## 规则

1. 所有文件路径都是相对于资源包根目录的
2. 修改文件前，先用 read_file 确认当前内容
3. 修改后告知用户做了什么改动
4. JSON 文件必须保持有效格式（用 validate_json 验证）
5. 对于批量操作，先列出计划再执行
6. 如果不确定用户的意图，先提问
7. 回复使用中文
8. 当用户问到 pack_format 版本、目录规范、文件格式等技术细节时，优先使用 get_mc_reference 工具查询准确信息
9. 创建新资源包时，使用 create_resource_template 工具生成标准骨架
10. 修改 pack.mcmeta 前，使用 validate_mcmeta_advanced 进行验证

{dynamic_context}
"""


def build_dynamic_context(pack_path, pack_mcmeta=None, file_stats=None, namespaces=None):
    """构建动态上下文信息"""
    context_parts = []

    # pack.mcmeta 信息
    if pack_mcmeta:
        pack_info = pack_mcmeta.get("pack", {})
        pack_format = pack_info.get("pack_format", "未知")
        description = pack_info.get("description", "无描述")
        version_name = PACK_FORMAT_TABLE.get(pack_format, "未知版本")
        context_parts.append(f"资源包信息: pack_format={pack_format} (对应 Minecraft {version_name}), 描述={description}")

        # supported_formats
        sf = pack_info.get("supported_formats")
        if sf:
            context_parts.append(f"supported_formats: {sf}")
        min_f = pack_info.get("min_format")
        max_f = pack_info.get("max_format")
        if min_f is not None and max_f is not None:
            context_parts.append(f"兼容范围: {min_f}-{max_f} ({PACK_FORMAT_TABLE.get(min_f, '?')} ~ {PACK_FORMAT_TABLE.get(max_f, '?')})")

        # overlays
        overlays = pack_mcmeta.get("overlays", {}).get("entries", [])
        if overlays:
            context_parts.append(f"覆盖层数量: {len(overlays)}")

        # language registrations
        languages = pack_info.get("language", {})
        if languages:
            lang_codes = list(languages.keys())
            context_parts.append(f"注册的自定义语言: {', '.join(lang_codes)}")

    # 文件统计
    if file_stats:
        context_parts.append(f"文件总数: {file_stats.get('total_files', 0)}")
        stats_parts = []
        for key, label in [("textures_count", "纹理"), ("models_count", "模型"),
                           ("blockstates_count", "方块状态"), ("sounds_count", "声音"),
                           ("fonts_count", "字体"), ("particles_count", "粒子")]:
            count = file_stats.get(key, 0)
            if count > 0:
                stats_parts.append(f"{label}={count}")
        if stats_parts:
            context_parts.append("资源统计: " + ", ".join(stats_parts))

    # 命名空间
    if namespaces:
        context_parts.append(f"命名空间: {', '.join(namespaces)}")

    return "\n".join(context_parts) if context_parts else ""
