### 2.15 特殊文件：`regional_compliancies.json`

**功能定位**：按系统地区定时弹出合规弹窗。

**格式要求**：

```json
{
  "CHN": [
    { "delay": 1440, "period": 60, "title": "...", "message": "..." }
  ]
}
```

**游戏处理逻辑**：

1. 按 ISO 3166-1 三位字母地区代码分组。
2. `delay` 设置首次弹窗延迟（分钟）。
3. `period` 设置循环弹窗周期。
4. `title` 和 `message` 引用本地化键名。

**样本包中的体现**：

1. `meme.teahouse.team-da0c28/assets/minecraft/regional_compliancies.json`：定义了 CHN、USA、KOR、HKG、TWN、JPN、MAC、GBR 共 8 个地区的弹窗规则。
2. 每个地区：首次弹窗 1440 分钟（24 小时），周期 60 分钟。

---

