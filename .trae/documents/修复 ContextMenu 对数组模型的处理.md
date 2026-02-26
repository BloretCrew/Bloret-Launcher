## 问题根源

`ContextMenu.qml` 使用 `control.delegateModel` 作为 ListView 的 model。当 ComboBox 的 model 是 Python 返回的字典列表时，delegate 中的 `model` 是 Qt 内部的 `QQmIDMListAccessorData` 对象，需要使用 `modelData` 来访问实际数据。

## 修复方案

修改 `g:\Work\git\Bloret-Launcher\RinUI\components\ContextMenu.qml` 第 75-85 行的 text 绑定逻辑：

```qml
text: {
    var role = contextMenu.parent && contextMenu.parent.textRole ? contextMenu.parent.textRole : ""
    // 优先使用 modelData（数组模型）
    if (typeof modelData !== 'undefined') {
        if (role && modelData[role] !== undefined) {
            return modelData[role]
        }
        if (typeof modelData === 'string') {
            return modelData
        }
        if (typeof modelData === 'object' && role in modelData) {
            return modelData[role]
        }
        if (typeof modelData === 'object' && "name" in modelData) {
            return modelData.name
        }
    }
    // 回退到 model（ListModel 等）
    if (role && model[role] !== undefined) {
        return model[role]
    }
    if (typeof model === 'string') {
        return model
    }
    return String(model)
}
```

这样可以正确处理：
1. Python 返回的字典列表（使用 `modelData`）
2. QML ListModel（使用 `model`）
3. 字符串数组