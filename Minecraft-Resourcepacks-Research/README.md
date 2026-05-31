# Minecraft 资源包研究报告（拆分版）

> 原始文件：`Resourcepacks_research_report.md`
>
> 本报告对 41 个 Minecraft Java 版资源包进行了系统化研究，涵盖资源包机制总览、逐个深度分析、横向对比、文件级索引、开发指南、技术深度和最佳实践七大板块。

---

## 目录

### 00 - 研究范围与目标

- [00-研究范围与目标](00-研究范围与目标.md)

### 01 - 资源包机制总览

- [01-资源包机制总览](01-资源包机制总览.md)

### 02 - 资源包全目录详解（18 篇）

> 对 Minecraft 资源包标准目录结构的逐项详解。

- [00-总览](02-资源包全目录详解/00-总览.md)
- [01-根目录文件](02-资源包全目录详解/01-根目录文件.md)
- [02-纹理资源](02-资源包全目录详解/02-纹理资源.md)
- [03-烘焙模型](02-资源包全目录详解/03-烘焙模型.md)
- [04-方块状态映射](02-资源包全目录详解/04-方块状态映射.md)
- [05-物品模型映射](02-资源包全目录详解/05-物品模型映射.md)
- [06-装备模型](02-资源包全目录详解/06-装备模型.md)
- [07-语言文件](02-资源包全目录详解/07-语言文件.md)
- [08-字体定义](02-资源包全目录详解/08-字体定义.md)
- [09-声音资源](02-资源包全目录详解/09-声音资源.md)
- [10-粒子纹理定义](02-资源包全目录详解/10-粒子纹理定义.md)
- [11-文本资源](02-资源包全目录详解/11-文本资源.md)
- [12-着色器](02-资源包全目录详解/12-着色器.md)
- [13-纹理图集](02-资源包全目录详解/13-纹理图集.md)
- [14-gpu_warnlist](02-资源包全目录详解/14-gpu_warnlist.md)
- [15-regional_compliancies](02-资源包全目录详解/15-regional_compliancies.md)
- [16-路径点样式](02-资源包全目录详解/16-路径点样式.md)
- [17-生态扩展目录](02-资源包全目录详解/17-生态扩展目录.md)

### 03 - 资源包逐个研究（41 篇）

> 对 41 个资源包的逐一深度分析，包含根目录结构、包定位、关键文件说明、资源内容结构和结论。

- [00-总览](03-资源包逐个研究/00-总览.md)
- [01-Better-Leaves-9.5](03-资源包逐个研究/01-Better-Leaves.md)
- [02-Chat_Reporting_Helper](03-资源包逐个研究/02-Chat_Reporting_Helper.md)
- [03-FreshAnimations_v1.10.5](03-资源包逐个研究/03-FreshAnimations.md)
- [04-MandalasGUI+Dakmode_1.21.6_v2.1](03-资源包逐个研究/04-MandalasGUI.md)
- [05-meme.teahouse.team-da0c28](03-资源包逐个研究/05-meme-teahouse.md)
- [06-Enhanced-Audio-r7](03-资源包逐个研究/06-Enhanced-Audio-r7.md)
- [07-Gentler-Weather-Sounds-2.2.0](03-资源包逐个研究/07-Gentler-Weather-Sounds.md)
- [08-golden-days-base-1.21.x-1.15.5](03-资源包逐个研究/08-golden-days-base.md)
- [09-MC_Dungeons_Crit-1.21.7](03-资源包逐个研究/09-MC_Dungeons_Crit.md)
- [10-ALs-Dungeons-Boss-Bars（缺失）](03-资源包逐个研究/41-AL-Dungeons-Boss-Bars.md)
- [11-Fullbright-UB-1.21](03-资源包逐个研究/11-Fullbright-UB.md)
- [12-Default-Dark-Mode-1.21.11](03-资源包逐个研究/12-Default-Dark-Mode.md)
- [13-Enchantment-Outlines](03-资源包逐个研究/13-Enchantment-Outlines.md)
- [14-Recolourful-Containers-3.1.1](03-资源包逐个研究/14-Recolourful-Containers.md)
- [15-（保留编号）](03-资源包逐个研究/)
- [16-Dramatic-Skys-Demo-1.5.3](03-资源包逐个研究/16-Dramatic-Skys.md)
- [17-Bare-Bones-1.21.11](03-资源包逐个研究/17-Bare-Bones.md)
- [18-Simple-Grass-Flowers-v1.9.6](03-资源包逐个研究/18-Simple-Grass-Flowers.md)
- [19-cubic-sun-moon-v1.8.5](03-资源包逐个研究/19-cubic-sun-moon.md)
- [20-Default-HD-128x-Demo-1.8.2.5](03-资源包逐个研究/20-Default-HD-128x.md)
- [21-Faithful-32x-1.21.8](03-资源包逐个研究/21-Faithful-32x.md)
- [22-Icons-v.1.13.3](03-资源包逐个研究/22-Icons.md)
- [23-qrafty's-capitalized-font-3.1](03-资源包逐个研究/23-qrafty-capitalized-font.md)
- [24-Ashen_16x](03-资源包逐个研究/24-Ashen_16x.md)
- [25-Even-Better-Enchants-v3](03-资源包逐个研究/25-Even-Better-Enchants.md)
- [26-Fancy-Crops-v1.3](03-资源包逐个研究/26-Fancy-Crops.md)
- [27-ProgrammerArtFix-26.0](03-资源包逐个研究/27-ProgrammerArtFix.md)
- [28-NewGlowingOres-Border](03-资源包逐个研究/28-NewGlowingOres.md)
- [29-Low-Fire-1.1.1](03-资源包逐个研究/29-Low-Fire.md)
- [30-Enchant-Icons-v1.3](03-资源包逐个研究/30-Enchant-Icons.md)
- [31-Waystones-1.21.8](03-资源包逐个研究/31-Waystones.md)
- [32-Fast-Better-Grass](03-资源包逐个研究/32-Fast-Better-Grass.md)
- [33-FA-All-Extensions-v1.8.1](03-资源包逐个研究/33-FA-All-Extensions.md)
- [34-DetailedAnimationsReworked-V1.15](03-资源包逐个研究/34-DetailedAnimationsReworked.md)
- [35-Icon-Xaero's-1.22](03-资源包逐个研究/35-Icon-Xaeros.md)
- [36-SodiumTranslations](03-资源包逐个研究/36-SodiumTranslations.md)
- [37-探险者指南针结构汉化-v3.1](03-资源包逐个研究/37-ExplorersCompass-CHS.md)
- [38-Teddy-Totems](03-资源包逐个研究/38-Teddy-Totems.md)
- [39-NoFog](03-资源包逐个研究/39-NoFog.md)
- [40-Roman-Numerals-Enchant-Icons](03-资源包逐个研究/40-Roman-Numerals-Enchant-Icons.md)
- [41-AL-Dungeons-Boss-Bars-1.0.2](03-资源包逐个研究/41-AL-Dungeons-Boss-Bars.md)

### 04 - 横向对比

> 对全部 41 个资源包的类型对比、复杂度排名、技术手段对比和常见模式分析。

- [04-横向对比](04-横向对比.md)

### 05 - 结论

> 研究总结、各类别关键发现、技术模式与创新、开发者建议和未来研究方向。

- [05-结论](05-结论.md)

### 06 - 文件级索引附录（41 篇）

> 按资源包列出最关键、最有代表性的文件与目录功能索引。

- [00-总览](06-文件级索引附录/00-总览.md)
- [01-Better-Leaves](06-文件级索引附录/01-Better-Leaves.md)
- [02-Chat_Reporting_Helper](06-文件级索引附录/02-Chat_Reporting_Helper.md)
- [03-FreshAnimations](06-文件级索引附录/03-FreshAnimations.md)
- [04-MandalasGUI](06-文件级索引附录/04-MandalasGUI.md)
- [05-meme-teahouse](06-文件级索引附录/05-meme-teahouse.md)
- 06 至 41：待补充

### 07 - 附录使用建议

- [07-附录使用建议](07-附录使用建议.md)

### 08 - 开发指南（13 篇）

> 面向资源包开发者的系统性实践指南，从入门到进阶的完整开发路径。

- [00-总览](08-开发指南/00-总览.md)
- [01-纹理包开发](08-开发指南/01-纹理包开发.md)
- [02-模型包开发](08-开发指南/02-模型包开发.md)
- [03-声音包开发](08-开发指南/03-声音包开发.md)
- [04-语言包开发](08-开发指南/04-语言包开发.md)
- [05-着色器包开发](08-开发指南/05-着色器包开发.md)
- [06-GUI包开发](08-开发指南/06-GUI包开发.md)
- [07-动画包开发](08-开发指南/07-动画包开发.md)
- [08-字体包开发](08-开发指南/08-字体包开发.md)
- [09-粒子效果开发](08-开发指南/09-粒子效果开发.md)
- [10-性能优化开发](08-开发指南/10-性能优化开发.md)
- [11-模组兼容开发](08-开发指南/11-模组兼容开发.md)
- [12-版本兼容指南](08-开发指南/12-版本兼容指南.md)

### 09 - 技术深度（12 篇）

> 面向技术人员的 Minecraft 资源加载与渲染机制全面剖析。

- [00-总览](09-技术深度/00-总览.md)
- [01-纹理制作规范](09-技术深度/01-纹理制作规范.md)
- [02-JSON模型语法](09-技术深度/02-JSON模型语法.md)
- [03-OPTIFINE-CEM详解](09-技术深度/03-OPTIFINE-CEM详解.md)
- [04-OPTIFINE-CIT详解](09-技术深度/04-OPTIFINE-CIT详解.md)
- [05-OPTIFINE-CTM详解](09-技术深度/05-OPTIFINE-CTM详解.md)
- [06-纹理图集机制](09-技术深度/06-纹理图集机制.md)
- [07-动画系统](09-技术深度/07-动画系统.md)
- [08-着色器管线](09-技术深度/08-着色器管线.md)
- [09-声音系统](09-技术深度/09-声音系统.md)
- [10-字体渲染](09-技术深度/10-字体渲染.md)
- [11-覆盖层系统](09-技术深度/11-覆盖层系统.md)

### 10 - 最佳实践（6 篇）

> 资源包开发的系统化质量标准、评估维度和开发工作流程。

- [00-总览](10-最佳实践/00-总览.md)
- [01-命名规范](10-最佳实践/01-命名规范.md)
- [02-目录结构最佳实践](10-最佳实践/02-目录结构最佳实践.md)
- [03-性能优化技巧](10-最佳实践/03-性能优化技巧.md)
- [04-兼容性处理](10-最佳实践/04-兼容性处理.md)
- [05-发布与分发](10-最佳实践/05-发布与分发.md)

### 附录 - Modrinth 扩展样本

- [Modrinth扩展样本](Modrinth扩展样本.md)
- [Modrinth扩展样本详细报告](Modrinth扩展样本详细报告.md)

---

## 文档统计

| 板块 | 文档数 | 说明 |
|---|---|---|
| 00-研究范围与目标 | 1 | 研究目标与范围定义 |
| 01-资源包机制总览 | 1 | 资源包系统机制概述 |
| 02-资源包全目录详解 | 18 | 标准目录结构逐项详解 |
| 03-资源包逐个研究 | 41 | 41 个资源包逐一深度分析 |
| 04-横向对比 | 1 | 类型对比、复杂度排名、技术手段对比 |
| 05-结论 | 1 | 研究总结与建议 |
| 06-文件级索引附录 | 41 | 文件级功能索引（部分待补充） |
| 07-附录使用建议 | 1 | 索引使用方法 |
| 08-开发指南 | 13 | 开发实践指南 |
| 09-技术深度 | 12 | 底层技术剖析 |
| 10-最佳实践 | 6 | 质量标准与工作流程 |
| 附录 | 2 | Modrinth 扩展样本 |
| **合计** | **138** | |

---

*本报告最后更新：2026 年 5 月*
