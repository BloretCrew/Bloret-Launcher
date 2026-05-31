# 36. SodiumTranslations

## 根目录结构

```
SodiumTranslations/
├── assets/
│   └── sodium/
│       └── lang/
│           ├── ar_sa.json      # 阿拉伯语
│           ├── be_by.json      # 白俄罗斯语
│           ├── bg_bg.json      # 保加利亚语
│           ├── bs_ba.json      # 波斯尼亚语
│           ├── cs_cz.json      # 捷克语
│           ├── da_dk.json      # 丹麦语
│           ├── de_de.json      # 德语
│           ├── el_gr.json      # 希腊语
│           ├── en_us.json      # 英语（美国）
│           ├── es_ar.json      # 西班牙语（阿根廷）
│           ├── es_es.json      # 西班牙语（西班牙）
│           ├── es_mx.json      # 西班牙语（墨西哥）
│           ├── et_ee.json      # 爱沙尼亚语
│           ├── fa_ir.json      # 波斯语
│           ├── fi_fi.json      # 芬兰语
│           ├── fil_ph.json     # 菲律宾语
│           ├── fr_fr.json      # 法语
│           ├── gl_es.json      # 加利西亚语
│           ├── he_il.json      # 希伯来语
│           ├── hi_in.json      # 印地语
│           ├── hu_hu.json      # 匈牙利语
│           ├── id_id.json      # 印尼语
│           ├── it_it.json      # 意大利语
│           ├── ja_jp.json      # 日语
│           ├── ko_kr.json      # 韩语
│           ├── lt_lt.json      # 立陶宛语
│           ├── lv_lv.json      # 拉脱维亚语
│           ├── ms_my.json      # 马来语
│           ├── nb_no.json      # 挪威语（布克莫尔）
│           ├── nl_nl.json      # 荷兰语
│           ├── nn_no.json      # 挪威语（尼诺斯克）
│           ├── pl_pl.json      # 波兰语
│           ├── pt_br.json      # 葡萄牙语（巴西）
│           ├── pt_pt.json      # 葡萄牙语（葡萄牙）
│           ├── ro_ro.json      # 罗马尼亚语
│           ├── ru_ru.json      # 俄语
│           ├── sr_sp.json      # 塞尔维亚语
│           ├── sv_se.json      # 瑞典语
│           ├── test.json       # 测试文件
│           ├── th_th.json      # 泰语
│           ├── tl_ph.json      # 他加禄语
│           ├── tr_tr.json      # 土耳其语
│           ├── uk_ua.json      # 乌克兰语
│           ├── ur_pk.json      # 乌尔都语
│           ├── uzb_uz.json     # 乌兹别克语
│           ├── vi_vn.json      # 越南语
│           ├── zh_cn.json      # 简体中文
│           ├── zh_hk.json      # 繁体中文（香港）
│           ├── zh_tw.json      # 繁体中文（台湾）
│           ├── zlm_arab.json   # 马来语（阿拉伯文）
│           └── zlm_my.json     # 马来语（马来西亚）
├── pack.mcmeta
└── pack.png
```

## 包定位

SodiumTranslations 是一个**语言翻译资源包**，专门为知名性能优化模组 **Sodium（钠）** 提供多语言界面翻译。Sodium 是 Minecraft 最重要、最广泛使用的渲染优化模组之一，它大幅提升了游戏的帧率和渲染性能，同时修复了许多图形问题。

由于 Sodium 本身是一个面向全球玩家的模组，其各语言界面翻译需要一个庞大的社区来维护。这个资源包汇集了来自社区贡献的翻译内容，将其整合为一个资源包，方便玩家安装使用。这也是一个典型的非官方翻译资源包。

## 关键文件说明

**pack.mcmeta:**
```json
{
  "pack": {
    "description": {
      "translate": "sodium.resource_pack.unofficial",
      "fallback": "Unofficial translations for Sodium"
    },
    "pack_format": 15,
    "min_format": 15,
    "max_format": 84,
    "supported_formats": [15, 64]
  }
}
```

描述字段使用了可翻译文本，指向 Sodium 模组中的一个语言键 `sodium.resource_pack.unofficial`。这是一种良好的做法，确保描述文字也能够被当前使用的语言文件翻译。

**语言文件样例（zh_cn.json）：**
简体中文翻译文件的内容包含了Sodium设置界面中所有选项的详细翻译，包括：

- 常规设置（渲染距离、模拟距离、亮度等）
- 质量设置（图形质量、云渲染、树叶渲染等）
- 性能设置（区块更新、实体剔除等）
- 高级设置（OpenGL错误检查、内存分配器等）

示例翻译条目：
```json
"sodium.options.view_distance.tooltip": "渲染距离控制渲染多远的地形。更短的距离意味着会渲染更少的地形，从而提高帧率。"
"sodium.options.use_fog_occlusion.name": "启用迷雾遮挡"
"sodium.console.broken_nvidia_driver": "你的NVIDIA驱动程序过旧！..."
```

## 资源内容结构

本包的结构非常简单，只包含语言文件。每个语言文件都是一个JSON对象，键值对格式。翻译覆盖了Sodium模组的所有UI文本：

- **选项名称和描述**：包括所有视频设置的中文名称和悬停说明文字
- **性能影响标签**：低/中/高/极高/视情况
- **控制台消息**：包括驱动兼容性警告、模组冲突提示等
- **按钮文本**：撤销、应用、赞助等

### 语言覆盖情况

本包提供了 **50种语言** 的翻译支持，覆盖了全球主要语言，包括：

- **印欧语系**：英语、西班牙语（3种变体）、法语、德语、俄语、葡萄牙语（2种变体）、意大利语、波兰语、荷兰语等
- **汉藏语系**：简体中文、繁体中文（2种变体）
- **闪含语系**：阿拉伯语、希伯来语
- **阿尔泰语系**：日语、韩语、土耳其语
- **南亚语系**：泰语、越南语
- **其他**：匈牙利语、芬兰语、罗马尼亚语等

## 关键目录功能

### assets/sodium/lang/

这是唯一的资源目录，存放所有 JSON 格式的语言文件。每个文件遵循 `locale_code.json` 的命名规范（如 `zh_cn.json`、`ja_jp.json`、`ru_ru.json`），与Minecraft标准语言代码一致。

语言文件的结构直接对应于Sodium模组内部使用的翻译键（Translation Key），例如：
- `sodium.options.view_distance.tooltip` → 渲染距离的提示文本
- `sodium.options.buttons.donate` → "赞助我们！" 按钮
- `sodium.console.broken_nvidia_driver` → Nvidia驱动过期的警告

## 技术特点

1. **纯语言资源包**：不包含任何模型、纹理、声音等其他资源，专注提供翻译文本。

2. **社区驱动**：翻译内容来自全球社区贡献，非官方但经过审核，质量有保障。

3. **覆盖全面**：包含约115条翻译键（以简体中文为例），覆盖所有Sodium设置项。

4. **兼容性设计**：使用 `pack_format: 15` 配合 `supported_formats: [15, 64]`，兼容多个Minecraft版本。

5. **可翻译的描述**：mcmeta中的描述文字也使用可翻译键，体现了对多语言支持的认真态度。

6. **UTF-8编码**：所有语言文件使用UTF-8编码，完美支持非拉丁字符集（如中文、日文、阿拉伯文）。

## 结论

SodiumTranslations 是一个实用价值极高的辅助性资源包。它解决的是一个实实在在的问题——大量非英语母语的Sodium用户在使用默认的英文界面时可能感到困惑，而本包让这些用户能够以自己熟悉的语言操作Sodium的各种优化设置。

虽然翻译工作的技术含量看起来不高，但实际上需要翻译人员对Sodium模组的技术细节有深入了解，才能准确传达每个选项的功能含义。特别是像"区块更新线程"、"持久内存映射"、"四边形分割"这类专业术语的翻译，需要兼顾准确性和易懂性。

对于中文玩家来说，安装这个资源包后，Sodium原本复杂的设置界面将变得清晰易懂，有助于更好地理解和利用Sodium的各项优化功能。建议所有非英语的Sodium用户都安装此包。
