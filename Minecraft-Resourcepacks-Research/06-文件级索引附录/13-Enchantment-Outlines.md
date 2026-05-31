# 13. Enchantment Outlines 文件索引

> 资源包全名：`Enchantment Outlines`
> 文件总数：728 个（不含 __MACOSX）
> 类型：着色器+纹理资源包，为附魔物品添加轮廓线高亮效果（当前仅实现斧类）

---

### 根目录

| 路径 | 功能 |
|---|---|
| `pack.mcmeta` | 资源包元数据，定义包格式版本与描述 |
| `pack.png` | 资源包封面图标 |
| `__MACOSX/` | macOS 压缩产生的元数据目录（可忽略） |
| `1.21.5/` | 1.21.5 版本专用文件 |
| `1.21.6/` | 1.21.6 版本专用文件 |
| `1.21.9/` | 1.21.9 版本专用文件 |
| `26.1/` | 26.1 版本专用文件 |
| `assets/` | 主资源目录 |

---

### 关键目录

| 路径 | 功能 |
|---|---|
| `1.21.5/assets/minecraft/textures/item/firstperson/` | 第一人称附魔斧纹理（6种材质+轮廓图） |
| `1.21.5/assets/minecraft/textures/item/thirdperson/` | 第三人称附魔斧纹理（6种材质+轮廓图+基础斧图） |
| `1.21.5/assets/minecraft/models/item/firstperson/axe/` | 第一人称附魔斧模型 JSON（6个） |
| `1.21.5/assets/minecraft/models/item/thirdperson/axe/` | 第三人称附魔斧模型 JSON（7个，含通用 enchanted_axe） |
| `1.21.5/assets/minecraft/shaders/core/` | 物品实体半透明剔除着色器（.fsh + .vsh） |
| `1.21.5/assets/minecraft/items/` | 物品定义 JSON（6种斧的附魔变体） |
| `1.21.6/assets/minecraft/shaders/core/` | 1.21.6 版本着色器适配 |
| `1.21.9/assets/minecraft/shaders/core/` | 1.21.9 版本着色器适配 |
| `26.1/assets/minecraft/shaders/core/` | 26.1 版本着色器适配 |
| `assets/minecraft/textures/item/firstperson/` | 默认版本第一人称纹理 |
| `assets/minecraft/textures/item/thirdperson/` | 默认版本第三人称纹理 |
| `assets/minecraft/models/item/firstperson/axe/` | 默认版本第一人称模型 |
| `assets/minecraft/models/item/thirdperson/axe/` | 默认版本第三人称模型 |
| `assets/minecraft/items/` | 默认版本物品定义 |

---

### 代表文件

| 路径 | 功能 |
|---|---|
| `1.21.5/assets/minecraft/textures/item/firstperson/enchanted_diamond_axe.png` | 第一人称附魔钻石斧纹理 |
| `1.21.5/assets/minecraft/textures/item/firstperson/axe_outline.png` | 斧头轮廓线贴图（高亮效果核心） |
| `1.21.5/assets/minecraft/textures/item/thirdperson/enchanted_netherite_axe.png` | 第三人称附魔下界合金斧纹理 |
| `1.21.5/assets/minecraft/textures/item/thirdperson/axe1.png` | 第三人称基础斧纹理 |
| `1.21.5/assets/minecraft/models/item/firstperson/axe/enchanted_diamond_axe.json` | 第一人称附魔钻石斧模型定义 |
| `1.21.5/assets/minecraft/models/item/thirdperson/axe/enchanted_axe.json` | 第三人称通用附魔斧模型 |
| `1.21.5/assets/minecraft/shaders/core/rendertype_item_entity_translucent_cull.fsh` | 物品实体半透明剔除片段着色器 |
| `1.21.5/assets/minecraft/shaders/core/rendertype_item_entity_translucent_cull.vsh` | 物品实体半透明剔除顶点着色器 |
| `1.21.5/assets/minecraft/items/diamond_axe.json` | 钻石斧物品定义（附魔变体映射） |
| `1.21.5/assets/minecraft/items/netherite_axe.json` | 下界合金斧物品定义 |
