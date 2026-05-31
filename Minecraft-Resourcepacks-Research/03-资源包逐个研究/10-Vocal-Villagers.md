# 10. Vocal Villagers 1.2

## 根目录结构
```text
assets/
  minecraft/
    font/
      default.json
    sounds.json
  vocal_villagers/
    sounds/
      mob/
        villager/
          celebrate1-8.ogg
          haggle4-6.ogg
          idle4-25.ogg
          yes4-13.ogg
    textures/
      font/
        credit.png
pack.mcmeta
pack.png
```

## 包定位
Vocal Villagers 是由作者 Oweh 创作的声音扩展资源包，专注于为村民（Villager）添加更多语音变体。该包的核心理念是"让村民更有生命力"——通过大幅增加村民在不同交互场景下的声音数量，使玩家在与村民互动时能听到更加多样化的语音反馈。

该包声称添加了 43 种额外的村民声音，覆盖了村民的五种核心交互状态：闲聊（idle）、交易（trade）、同意（yes）、拒绝（no）和庆祝（celebrate）。这种设计使得村民不再反复播放同一组单调的音效，而是能以更自然、更丰富的方式与玩家互动。

pack_format 为 15（对应 Minecraft 1.20.x），并使用 `supported_formats` 声明最低兼容版本为 15，最高兼容至 999，表明作者希望该包能在未来版本中持续使用。

## 关键文件说明

### pack.mcmeta
```json
{
    "pack": {
        "pack_format": 15,
        "supported_formats": {
            "min_inclusive": 15,
            "max_inclusive": 999
        },
        "description": "43 extra villager sounds!\n                     §f  §7- by §aOweh"
    }
}
```

该文件使用了 `supported_formats` 的对象格式（`min_inclusive` 和 `max_inclusive`），这是一种较新的写法，相比数组格式 `[15, 999]` 更加语义化。最大值设为 999 表明作者期望该包在未来所有 Minecraft 版本中都能工作——这在纯声音资源包中是合理的，因为村民音效的底层机制不太可能发生根本性变化。

描述文本使用了 Minecraft 的段落符号颜色代码：§f（白色）、§7（灰色）和 §a（绿色），用于在资源包列表中美化显示。其中还包含一个特殊 Unicode 字符 ``，该字符通过自定义字体映射到 `credit.png` 纹理，用于在描述中显示一个自定义图标。

### assets/minecraft/sounds.json
这是该包的核心配置文件，定义了声音事件到音频文件的映射关系。文件覆盖了以下六个村民声音事件：

1. **entity.villager.ambient**（闲聊）：映射了 22 个音频文件（idle4 到 idle25），没有使用 `replace: true`，意味着这些声音会与原版声音合并播放。
2. **entity.villager.celebrate**（庆祝）：映射了 8 个音频文件（celebrate1 到 celebrate8），使用了 `"replace": "true"`，完全替换了原版庆祝音效。
3. **entity.villager.death**（死亡）：映射了 1 个音频文件。
4. **entity.villager.no**（拒绝）：映射了 3 个音频文件（no1 到 no3）。
5. **entity.villager.trade**（交易）：映射了 3 个音频文件（haggle4 到 haggle6）。
6. **entity.villager.yes**（同意）：映射了 10 个音频文件（yes4 到 yes13）。

值得注意的是，闲聊、拒绝和同意事件没有使用 `replace: true`，这意味着这些新声音会与原版声音叠加，进一步增加了声音的多样性。而庆祝事件使用了完全替换，可能是为了用全新的庆祝音效风格取代原版。

所有音频文件都引用了自定义命名空间 `vocal_villagers`，而非直接放在 `minecraft` 命名空间下。这是资源包开发中的良好实践——使用独立命名空间可以避免与原版文件或其他资源包产生冲突。

### assets/minecraft/font/default.json
```json
{
    "providers": [
        {
            "type": "bitmap",
            "file": "vocal_villagers:font/credit.png",
            "ascent": 8,
            "height": 10,
            "chars": [""]
        }
    ]
}
```

该文件定义了一个自定义字体字符，将 Unicode 私用区字符 `` 映射到一张自定义位图纹理。这个字符被用于 pack.mcmeta 的描述文本中，以便在资源包列表中显示一个自定义图标（可能是作者 Oweh 的标志或装饰性图案）。`ascent: 8` 控制字符的基线位置，`height: 10` 定义字符高度。

## 资源内容结构
```text
assets/
  minecraft/
    font/
      default.json              ← 自定义字体定义
    sounds.json                 ← 声音事件映射配置
  vocal_villagers/              ← 自定义命名空间
    sounds/
      mob/
        villager/
          celebrate1-8.ogg      ← 8 个庆祝音效
          haggle4-6.ogg         ← 3 个交易音效
          idle4-25.ogg          ← 22 个闲聊音效
          yes4-13.ogg           ← 10 个同意音效
    textures/
      font/
        credit.png              ← 自定义字体位图
pack.mcmeta
pack.png
```

该包共包含 48 个文件，结构非常清晰。所有音频文件都集中在 `vocal_villagers` 命名空间的 `sounds/mob/villager/` 目录下，按声音类型分组命名。

## 关键目录功能

### assets/vocal_villagers/sounds/mob/villager/ 村民音效目录
这是该包最核心的目录，包含所有新增的村民音效文件。文件命名遵循清晰的编号规则：

- **idle4-25.ogg**：22 个闲聊音效，编号从 4 开始（暗示原版已有 idle1-3）
- **celebrate1-8.ogg**：8 个庆祝音效，编号从 1 开始（完全替换原版）
- **yes4-13.ogg**：10 个同意音效，编号从 4 开始（暗示原版已有 yes1-3）
- **haggle4-6.ogg**：3 个交易音效，编号从 4 开始（暗示原版已有 haggle1-3）
- **no1-3.ogg**：3 个拒绝音效（sounds.json 中引用但文件未在目录列表中显示，可能被遗漏或使用原版文件）
- **death.ogg**：1 个死亡音效

编号从 4 开始的设计非常巧妙——它避免了与原版已有的 1-3 号文件冲突，同时保持了编号的连续性。

### assets/vocal_villagers/textures/font/ 自定义字体纹理目录
该目录仅包含一个 `credit.png` 文件，用于 pack.mcmeta 描述中显示的自定义图标。这是一种常见的资源包品牌展示技巧。

### assets/minecraft/ 原版命名空间覆盖
该目录下有两个关键文件：
- `sounds.json`：覆盖原版声音定义，将村民声音事件指向新的音频文件
- `font/default.json`：扩展原版字体系统，添加自定义字符

## 技术特点

1. **自定义命名空间的使用**：所有音频文件都放在 `vocal_villagers` 命名空间下，而非直接覆盖 `minecraft` 命名空间的文件。这是资源包开发的最佳实践，避免了命名冲突，也使得包的内容更加清晰可辨。

2. **声音合并与替换的混合策略**：该包巧妙地混合使用了两种声音添加方式——闲聊、拒绝和同意事件不使用 `replace`，让新声音与原版声音叠加；而庆祝事件使用 `replace: true` 完全替换原版。这种策略既增加了声音多样性，又对特定场景进行了风格化定制。

3. **无限版本兼容声明**：`supported_formats` 的最大值设为 999，这是一种"面向未来"的设计。对于纯声音资源包而言，只要 Minecraft 不改变村民的声音事件名称，该包就可以在任何版本中工作。

4. **字体系统扩展**：通过自定义字体字符在 pack.mcmeta 描述中显示图标，展示了对 Minecraft 字体系统的巧妙利用。这种技术通常用于在资源包列表中展示品牌标识。

5. **编号起始值的选择**：音频文件编号从 4 开始（如 idle4、yes4），而非从 1 开始，暗示作者有意避免与原版文件冲突，同时保持了编号的逻辑连续性。

6. **无纹理/模型修改**：该包完全不涉及任何视觉内容的修改，是纯粹的听觉增强包。这种单一职责的设计使得它可以轻松与其他视觉类资源包叠加使用。

## 结论
Vocal Villagers 1.2 是一个设计精良的声音扩展资源包，其技术价值体现在以下几个方面：

1. **命名空间隔离**：使用独立的 `vocal_villagers` 命名空间存放所有新增资源，是资源包开发的最佳实践示范。

2. **声音映射策略**：混合使用 `replace` 和非 `replace` 模式，在增加声音多样性的同时保留了原版特色。

3. **版本兼容设计**：通过 `supported_formats` 的宽范围声明和纯声音资源的本质特性，实现了优秀的向前兼容性。

4. **字体系统扩展**：展示了如何利用自定义字体在 pack.mcmeta 中显示品牌标识。

该包的设计理念——"通过增加声音变体提升游戏沉浸感"——是资源包社区中一种常见且受欢迎的创作方向。它不改变游戏的视觉风格，只通过听觉层面的丰富来增强游戏体验，这使得它可以与几乎所有视觉类资源包兼容使用。对于资源包开发者而言，该包是学习声音资源包开发的优秀参考案例，特别是其命名空间使用和声音事件映射的设计值得借鉴。
