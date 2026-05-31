# 40. Roman Numerals for Enchant Icons (gray)

## 根目录结构

```
Roman Numerals for Enchant Icons (gray)/
├── assets/
│   └── minecraft/
│       └── lang/
│           ├── af_za.json       # 南非荷兰语
│           ├── ar_sa.json       # 阿拉伯语
│           ├── ast_es.json      # 阿斯图里亚斯语
│           ├── az_az.json       # 阿塞拜疆语
│           ├── ba_ru.json       # 巴什基尔语
│           ├── bar.json         # 巴伐利亚语
│           ├── ...              # 共约 100+ 种语言
│           ├── zh_cn.json       # 简体中文
│           ├── zh_hk.json       # 繁体中文（香港）
│           ├── zh_tw.json       # 繁体中文（台湾）
│           └── zlm_arab.json    # 马来语（阿拉伯文）
├── pack.mcmeta
└── pack.png
```

## 包定位

Roman Numerals for Enchant Icons (gray) 是一个专门配合 **Enchant Icons（附魔图标）** 资源包使用的辅助语言包。它的功能是在附魔等级显示中使用**灰色罗马数字**（I, II, III, IV, V...）替代默认的阿拉伯数字（1, 2, 3, 4, 5...）。

"Enchant Icons" 是一个流行的资源包，它在物品的附魔信息中为每个附魔添加了对应的图标，使其看起来更加直观美观。而 Roman Numerals 则进一步改善了显示效果——将原本的数字等级显示替换为更加优雅的罗马数字。

"(gray)" 后缀表明这是一个**灰色版本**的罗马数字显示风格。与黑色或其他颜色的版本不同，灰色罗马数字更低调，不会与 Enchant Icons 的彩色图标产生视觉冲突。

**重要提示**：包描述中明确写着 "Load after Enchant Icons!"（请排在 Enchant Icons 之后加载），表明这个包需要依赖 Enchant Icons 包，并且在加载顺序上必须位于 Enchant Icons 之后。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "pack_format": 15,
    "description": "Load after Enchant Icons! Gray version."
  }
}
```

描述非常简短但关键信息明确。pack_format 为15（Minecraft 1.21）。

**语言文件样例（en_us.json）：**
语言文件的主要内容是修改附魔等级显示。Minecraft 中附魔等级的翻译键是 `enchantment.level.X`，其中 X 是数字等级。默认情况下，这些键的对应值也是数字（1, 2, 3...）。本包将其替换为罗马数字：

```json
"enchantment.level.1": "I",
"enchantment.level.2": "II",
"enchantment.level.3": "III",
"enchantment.level.4": "IV",
"enchantment.level.5": "V",
...
"enchantment.level.10": "X",
"enchantment.level.20": "XX",
"enchantment.level.50": "L",
"enchantment.level.100": "C",
...
"enchantment.level.250": "CCL",
```

覆盖范围从 1 级到 255 级，涵盖了附魔可能出现的所有等级。罗马数字的表示遵循标准规则：
- 1-10: I, II, III, IV, V, VI, VII, VIII, IX, X
- 更大的数字使用组合形式，如 50 = L, 100 = C, 250 = CCL

### 灰色版本

在 Enchant Icons 系统中，附魔等级使用不同的颜色来区分（如白色、金色、绿色等）。灰色版本将所有等级显示为灰色文本，视觉上更加统一和低调，不会喧宾夺主地抢夺 Enchant Icons 图标本身的视觉焦点。

### 多语言覆盖

本包提供了 **100+ 种语言**的翻译文件。虽然所有语言文件中都使用了相同的罗马数字（因为罗马数字是通用的），但这种多语言支持确保了无论玩家使用什么语言界面，附魔等级都能正确显示为罗马数字。这是一种兼容性做法——覆盖所有语言文件以避免某些语言版本仍然显示阿拉伯数字。

## 资源内容结构

本包的结构极度精简：

1. **语言文件**：约100+个JSON语言文件，每个文件都包含从1到255级的罗马数字映射
2. **元数据**：pack.mcmeta 和 pack.png

没有模型、纹理、声音或其他任何额外资源。

## 技术特点

1. **纯语言替换**：通过修改 `enchantment.level.X` 翻译键的值来实现显示效果，不涉及任何模型或纹理资源

2. **极广的语言覆盖**：提供了100+种语言的支持，确保在所有界面语言下都能使用罗马数字

3. **完全覆盖范围**：从1级到255级，全面覆盖了Minecraft附魔系统可能达到的所有等级

4. **依赖其他资源包**：需要配合 Enchant Icons 资源包使用，并确保加载顺序正确（在Enchant Icons之后）

5. **颜色定制**：专门的灰色版本，与其他颜色版本（金色、白色等）区分，提供不同的视觉风格选择

6. **低体积高效率**：通过小型的JSON语言文件实现显著的视觉效果改变，不需要替换任何模型或纹理

## 结论

Roman Numerals for Enchant Icons (gray) 是一个精致的小型辅助资源包。它不创造新内容，不改变游戏玩法，不对纹理做任何修改——它只做一件简单的事情：将附魔等级的数字改为罗马数字。

这个改动虽然小，却能很大程度上提升游戏界面的视觉品质。在 Enchant Icons 提供了图标后，默认的阿拉伯数字（1, 2, 3...）与精美的图标放在一起显得有些不够协调。罗马数字（I, II, III...）则更加古典优雅，与Minecraft的中世纪奇幻主题更加契合。

灰色版本的选择也显示了作者的审美考量——灰色不会与 Enchant Icons 的彩色图标产生视觉竞争，而是恰到好处地作为辅助信息存在。

对于安装了 Enchant Icons 的玩家来说，这个包是一个完美的视觉完善方案。它也是资源包组合搭配的一个好例子——多个包协同工作，各自的修改互不冲突，最终达到 1+1 > 2 的效果。
