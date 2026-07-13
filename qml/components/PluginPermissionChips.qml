import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

/**
 * 插件权限胶囊列表。
 * 支持：
 *  - detailsJson: JSON 数组 [{id, label, risk}, ...]
 *  - permissionIds: 字符串数组或逗号分隔；会经 PluginHost.resolvePermissionsJson 国际化
 */
Item {
    id: root
    // 高度随内容；宽度由父级 Layout / anchors 约束，防止胶囊撑破卡片
    implicitHeight: col.implicitHeight
    implicitWidth: 200
    height: col.implicitHeight
    Layout.fillWidth: true
    Layout.preferredHeight: col.implicitHeight
    clip: true

    property string detailsJson: ""
    property var permissionIds: []
    property string title: ""
    property bool showTitle: title.length > 0
    property bool compact: false
    /** 空数据时是否占位隐藏 */
    property bool hideWhenEmpty: true
    /** 单枚胶囊最大宽度（相对容器），过长标签省略 */
    property real chipMaxWidthRatio: 0.92

    property var _items: []

    function tr(s) {
        return Backend ? Backend.tr(s) : s
    }

    function _parseDetails(raw) {
        if (!raw)
            return []
        try {
            var arr = typeof raw === "string" ? JSON.parse(raw || "[]") : raw
            if (!Array.isArray(arr))
                return []
            var out = []
            for (var i = 0; i < arr.length; i++) {
                var it = arr[i]
                if (typeof it === "string") {
                    out.push({ id: it, label: it, risk: "high" })
                } else if (it && typeof it === "object") {
                    out.push({
                        id: it.id || "",
                        label: it.label || it.id || "",
                        risk: it.risk || "safe"
                    })
                }
            }
            return out
        } catch (e) {
            console.log("[PluginPermissionChips] parse details failed:", e)
            return []
        }
    }

    function refresh() {
        var items = _parseDetails(detailsJson)
        if (items.length === 0 && permissionIds && (permissionIds.length > 0 || typeof permissionIds === "string")) {
            var ids = permissionIds
            if (typeof ids === "string") {
                ids = ids.split(/[,;\s]+/).filter(function (s) { return s && s.length > 0 })
            }
            if (typeof PluginHost !== "undefined" && PluginHost && typeof PluginHost.resolvePermissionsJson === "function") {
                try {
                    items = _parseDetails(PluginHost.resolvePermissionsJson(JSON.stringify(ids)))
                } catch (e) {
                    console.log("[PluginPermissionChips] resolvePermissionsJson failed:", e)
                    items = ids.map(function (id) { return { id: id, label: id, risk: "high" } })
                }
            } else {
                items = ids.map(function (id) { return { id: id, label: id, risk: "high" } })
            }
        }
        _items = items
        console.log("[PluginPermissionChips] refresh count=", items.length,
                    "title=", title || "(none)", "width=", root.width)
    }

    onDetailsJsonChanged: refresh()
    onPermissionIdsChanged: refresh()
    Component.onCompleted: refresh()

    visible: !hideWhenEmpty || _items.length > 0 || (showTitle && title.length > 0)

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        width: parent.width
        spacing: compact ? 4 : 6

        Text {
            visible: showTitle && title.length > 0
            text: title
            typography: Typography.Caption
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.fillWidth: true
        }

        Flow {
            id: chipFlow
            Layout.fillWidth: true
            // Flow 需要明确宽度才会在容器内换行，否则会横向撑出父级
            width: root.width > 0 ? root.width : parent.width
            spacing: 6
            visible: _items.length > 0

            Repeater {
                model: _items
                delegate: Rectangle {
                    id: chip
                    property string riskLevel: (modelData.risk || "safe").toLowerCase()
                    property bool isHigh: riskLevel === "high" || riskLevel === "warning" || riskLevel === "error"
                    // 胶囊不得宽过 Flow，否则会“跑出”卡片
                    property real maxChipW: {
                        var flowW = chipFlow.width > 0 ? chipFlow.width : root.width
                        return Math.max(72, flowW * root.chipMaxWidthRatio)
                    }
                    property real hPad: compact ? 14 : 16
                    property real textMaxW: Math.max(32, maxChipW - hPad - 10)

                    radius: height / 2
                    height: compact ? 20 : 22
                    // 自然宽度，但封顶在容器内
                    width: Math.min(chipRow.implicitWidth + hPad, maxChipW)
                    clip: true

                    // 不依赖 darkMode 属性：浅色半透明底 + 实色边框，深浅主题都可读
                    color: chip.isHigh ? "#33f59e0b" : "#333b82f6"
                    border.width: 1
                    border.color: chip.isHigh ? "#f59e0b" : (Theme.accentColor || "#3b82f6")

                    Row {
                        id: chipRow
                        anchors.centerIn: parent
                        spacing: 4

                        // 风险圆点
                        Rectangle {
                            width: 6
                            height: 6
                            radius: 3
                            anchors.verticalCenter: parent.verticalCenter
                            color: chip.isHigh
                                   ? "#ea580c"
                                   : (Theme.accentColor || "#3b82f6")
                        }

                        Text {
                            text: modelData.label || modelData.id || ""
                            font.pixelSize: compact ? 11 : 12
                            font.weight: Font.Medium
                            color: Theme.currentTheme.colors.textColor
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            // 用固定上限 elide，避免与 chip.width 互相绑定
                            width: Math.min(implicitWidth, chip.textMaxW)
                        }
                    }

                    ToolTip.visible: chipMa.containsMouse
                    ToolTip.delay: 400
                    ToolTip.text: {
                        var label = modelData.label || modelData.id || ""
                        var idPart = modelData.id ? String(modelData.id) : ""
                        var riskText = chip.isHigh
                            ? (Backend ? Backend.tr("高风险") : "高风险")
                            : (Backend ? Backend.tr("低风险") : "低风险")
                        if (idPart && label && idPart !== label)
                            return label + "\n" + idPart + " · " + riskText
                        if (idPart)
                            return idPart + " · " + riskText
                        return (label ? label + " · " : "") + riskText
                    }

                    MouseArea {
                        id: chipMa
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }
                }
            }
        }

        Text {
            visible: _items.length === 0 && showTitle
            text: Backend ? Backend.tr("无额外权限") : "无额外权限"
            typography: Typography.Caption
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.fillWidth: true
        }
    }
}
