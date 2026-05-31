## 2.4 `MandalasGUI+Dakmode_1.21.6_v2.1`

### 3.4.1 根目录结构

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/`

```text
assets/
License.txt
pack.mcmeta
pack.png
```

### 3.4.2 包定位

这是一个 GUI 美化包，并且明显包含 Dark Mode 风格。

从文件命名看，它主要修改游戏界面、菜单、按钮、列表、提示框、容器 GUI 和各种交互图标。

### 3.4.3 关键文件说明

#### `pack.mcmeta`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 64,
    "description": "§7By: §6§nCesarZorak\n§r§71.20.5 to 1.21.5"
  }
}
```

用途：

1. 标注支持版本区间。
2. 显示作者信息。
3. 说明这是一个跨多个 Minecraft 小版本兼容的 GUI 包。

#### `License.txt`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/License.txt`

说明：

1. 当前读取工具无法按文本打开该文件，可能是二进制或特殊编码。
2. 但从文件名可知它是许可证文件，用于约束资源使用。

#### `pack.png`

路径：`Resourcepacks/MandalasGUI+Dakmode_1.21.6_v2.1/pack.png`

作用：资源包图标。

### 3.4.4 资源内容结构

大部分资源都在：

1. `assets/minecraft/textures/gui/`
2. `assets/minecraft/textures/item/`
3. `assets/minecraft/textures/particle/`

### 3.4.5 关键目录功能

#### `assets/minecraft/textures/gui/`

这是整个包最重要的目录。

这里包含：

1. `widgets.png`
2. `icons.png`
3. `resource_packs.png`
4. `server_selection.png`
5. `world_selection.png`
6. `inventory.png`
7. `crafting_table.png`
8. `beacon.png`
9. `anvil.png`
10. `smoker.png`
11. `grindstone.png`
12. `smithing.png`
13. `book.png`
14. `recipe_book.png`
15. `toasts.png`
16. `menu_background.png`
17. `light_dirt_background.png`
18. `stream_indicator.png`
19. `chat_tags.png`
20. `report_button.png`

功能判断：

1. 该包在重绘主菜单、设置界面、世界选择界面、服务器界面、容器界面和提示系统。
2. `widgets.png` 和一系列 `sprites/widget/` 文件说明按钮、滑条、复选框、文本框等控件都被重做。
3. `world_list/`、`toast/`、`dialog/` 说明连系统弹窗、世界列表按钮和对话框样式也被重绘。

代表性子目录：

1. `assets/minecraft/textures/gui/sprites/widget/`
2. `assets/minecraft/textures/gui/sprites/world_list/`
3. `assets/minecraft/textures/gui/sprites/dialog/`
4. `assets/minecraft/textures/gui/sprites/toast/`
5. `assets/minecraft/textures/gui/container/`

#### `assets/minecraft/textures/gui/container/`

这里包括：

1. `inventory.png`
2. `crafting_table.png`
3. `furnace.png`
4. `blast_furnace.png`
5. `smoker.png`
6. `smithing.png`
7. `stonecutter.png`
8. `loom.png`
9. `cartography_table.png`
10. `enchanting_table.png`
11. `grindstone.png`
12. `beacon.png`
13. `brewing_stand.png`
14. `villager.png`
15. `horse.png`
16. `shulker_box.png`
17. `crafter.png`
18. `legacy_smithing.png`

功能判断：

1. 整个包对常用容器界面做统一视觉重做。
2. 支持新旧 smithing 界面并存，说明它兼顾新版 GUI 机制。

#### `assets/minecraft/textures/item/`

这里是 GUI 中的槽位提示图标，例如：

1. `empty_slot_sword.png`
2. `empty_slot_pickaxe.png`
3. `empty_slot_shovel.png`
4. `empty_slot_axe.png`
5. `empty_slot_hoe.png`
6. `empty_slot_ingot.png`
7. `empty_slot_diamond.png`
8. `empty_slot_emerald.png`
9. `empty_slot_quartz.png`
10. `empty_slot_lapis_lazuli.png`
11. `empty_slot_amethyst_shard.png`
12. `empty_armor_slot_helmet.png`
13. `empty_armor_slot_chestplate.png`
14. `empty_armor_slot_leggings.png`
15. `empty_armor_slot_boots.png`
16. `empty_armor_slot_shield.png`

功能判断：

1. 用于槽位提示和物品图标占位。
2. 直接提升容器界面的可读性。

#### `assets/minecraft/textures/particle/`

这里包含：

1. `note.png`
2. `heart.png`
3. `damage.png`
4. `goldheart_0.png`
5. `goldheart_1.png`
6. `goldheart_2.png`
7. `damage_.png`

说明：

1. 包不仅修改界面，还对部分粒子和状态视觉做统一风格化。
2. `goldheart_*` 说明连与状态效果有关的局部视觉也被替换。

### 3.4.6 结论

`MandalasGUI+Dakmode_1.21.6_v2.1` 是一个纯度很高的 GUI/UI 风格化资源包。

它的特征是：

1. 高度集中在 `textures/gui`。
2. 兼顾主菜单、列表、容器、提示框、按钮与输入控件。
3. 具有明显的暗色界面风格和现代化视觉统一倾向。

---

