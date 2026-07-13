import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: toolsPage
    title: (Backend ? Backend.tr("小工具") : "小工具")

    property var pluginToolCards: []

    function loadPluginToolCards() {
        pluginToolCards = []
        if (typeof PluginHost === "undefined" || !PluginHost) {
            console.log("[Tools] PluginHost 不可用")
            return
        }
        try {
            var list = JSON.parse(PluginHost.getToolsContributionsJson() || "[]")
            console.log("[Tools] plugin tool cards:", list.length)
            pluginToolCards = list
        } catch (e) {
            console.log("[Tools] loadPluginToolCards error:", e)
            pluginToolCards = []
        }
    }

    Component.onCompleted: loadPluginToolCards()

    Connections {
        target: (typeof PluginHost !== "undefined") ? PluginHost : null
        enabled: (typeof PluginHost !== "undefined") && PluginHost !== null
        function onToolsContributionsChanged() {
            console.log("[Tools] toolsContributionsChanged")
            loadPluginToolCards()
        }
        function onPluginsChanged() {
            loadPluginToolCards()
        }
    }

    // Easytier status handler (not displayed in this page, but kept for backend communication)
    Connections {
        target: Backend
        function onQueryResultReceived(data) {
            if (data.type === "uuid") {
                uuidResult.text = data.success ? data.result : (Backend ? Backend.tr("查询失败") : "查询失败")
            } else if (data.type === "name") {
                nameResult.text = data.success ? data.result : (Backend ? Backend.tr("查询失败") : "查询失败")
            } else if (data.type === "textures") {
                if (data.success) {
                    skinResult.text = data.skin || (Backend ? Backend.tr("未找到皮肤") : "未找到皮肤")
                    capeResult.text = data.cape || (Backend ? Backend.tr("未找到披风") : "未找到披风")
                } else {
                    skinResult.text = (Backend ? Backend.tr("查询失败") : "查询失败")
                    capeResult.text = (Backend ? Backend.tr("查询失败") : "查询失败")
                }
            }
        }
        function onLogsCleared() {
            logClearedInfoBar.visible = true
            logClearedTimer.start()
        }
    }

    // Timer must be direct child of FluentPage, not inside ColumnLayout
    Timer {
        id: logClearedTimer
        interval: 3000
        onTriggered: logClearedInfoBar.visible = false
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.margins: 20
        spacing: 20

        InfoBar {
            id: logClearedInfoBar
            Layout.fillWidth: true
            title: (Backend ? Backend.tr("成功") : "成功")
            text: (Backend ? Backend.tr("日志已成功清空") : "日志已成功清空")
            severity: Severity.Success
            visible: false
        }

        // --- 插件小工具卡片 ---
        Label {
            visible: pluginToolCards && pluginToolCards.length > 0
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("插件工具") : "插件工具")
            Layout.topMargin: 10
            color: Theme.currentTheme.colors.textColor
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: pluginToolCards && pluginToolCards.length > 0
            Repeater {
                model: pluginToolCards
                delegate: Loader {
                    Layout.fillWidth: true
                    source: modelData.qml || ""
                    onStatusChanged: {
                        if (status === Loader.Error)
                            console.log("[Tools] plugin card error:", modelData.id, modelData.qml)
                        else if (status === Loader.Ready)
                            console.log("[Tools] plugin card ready:", modelData.id)
                    }
                }
            }
        }

        // --- Resource Pack Editor Section ---
        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("资源包工具") : "资源包工具")
            Layout.topMargin: 10
            color: Theme.currentTheme.colors.textColor
        }

        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                Image {
                    source: Qt.resolvedUrl("../../icon/BLRPE.png")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        font.weight: Font.DemiBold
                        font.pixelSize: 16
                        text: (Backend ? Backend.tr("Bloret Launcher 资源包编辑器") : "Bloret Launcher 资源包编辑器")
                        color: Theme.currentTheme.colors.textColor
                    }
                    Label {
                        text: (Backend ? Backend.tr("创建和编辑 Minecraft 资源包，内置 Git 版本管理，无需编程基础") : "创建和编辑 Minecraft 资源包，内置 Git 版本管理，无需编程基础")
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.Wrap
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("打开编辑器") : "打开编辑器")
                    highlighted: true
                    onClicked: {
                        if (Backend) Backend.openResourcePackEditor()
                    }
                }
            }
        }

        // --- Screen Cut Section ---
        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("屏幕截图") : "屏幕截图")
            Layout.topMargin: 10
            color: Theme.currentTheme.colors.textColor
        }

        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15

                    Image {
                        source: Qt.resolvedUrl("../../icon/imageres 017.png")
                        sourceSize { width: 40; height: 40 }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Label {
                            font.weight: Font.DemiBold
                            font.pixelSize: 16
                            text: (Backend ? Backend.tr("Bloret Launcher Screen Cut") : "Bloret Launcher Screen Cut")
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: (Backend ? Backend.tr("便捷地截取屏幕画面，包括 Minecraft 窗口") : "便捷地截取屏幕画面，包括 Minecraft 窗口")
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }
                    }

                    Button {
                        text: (Backend ? Backend.tr("截图") : "截图")
                        onClicked: { if (Backend) Backend.takeScreenCut() }
                    }
                }
            }
        }

        // --- Minecraft Data Lookup Section ---
        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("Minecraft 数据查询") : "Minecraft 数据查询")
            Layout.topMargin: 10
            color: Theme.currentTheme.colors.textColor
        }

        // UUID Lookup
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("查询玩家UUID") : "查询玩家UUID")
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                ColumnLayout {
                    Layout.maximumWidth: 450
                    Layout.preferredWidth: 350

                    TextField {
                        id: uuidInput
                        Layout.fillWidth: true
                        placeholderText: (Backend ? Backend.tr("玩家名称（正版）") : "玩家名称（正版）")
                    }

                    Button {
                        Layout.fillWidth: true
                        text: (Backend ? Backend.tr("查询") : "查询")
                        onClicked: {
                            uuidResult.text = (Backend ? Backend.tr("查询中...") : "查询中...")
                            if (Backend) Backend.queryUUID(uuidInput.text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: uuidResult
                            text: (Backend ? Backend.tr("查询的结果将显示在这里") : "查询的结果将显示在这里")
                            Layout.fillWidth: true
                            elide: Text.ElideMiddle
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Button {
                            text: (Backend ? Backend.tr("复制") : "复制")
                            onClicked: { if (Backend) Backend.copyToClipboard(uuidResult.text) }
                        }
                    }
                }
            }
        }

        // Name Lookup
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("查询玩家名字") : "查询玩家名字")
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                ColumnLayout {
                    Layout.maximumWidth: 450
                    Layout.preferredWidth: 350

                    TextField {
                        id: nameInput
                        Layout.fillWidth: true
                        placeholderText: (Backend ? Backend.tr("玩家UUID") : "玩家UUID")
                    }

                    Button {
                        Layout.fillWidth: true
                        text: (Backend ? Backend.tr("查询") : "查询")
                        onClicked: {
                            nameResult.text = (Backend ? Backend.tr("查询中...") : "查询中...")
                            if (Backend) Backend.queryName(nameInput.text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: nameResult
                            text: (Backend ? Backend.tr("查询的结果将显示在这里") : "查询的结果将显示在这里")
                            Layout.fillWidth: true
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Button {
                            text: (Backend ? Backend.tr("复制") : "复制")
                            onClicked: { if (Backend) Backend.copyToClipboard(nameResult.text) }
                        }
                    }
                }
            }
        }

        // Skin and Cape Lookup
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("获取玩家的皮肤和披风") : "获取玩家的皮肤和披风")
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                ColumnLayout {
                    Layout.maximumWidth: 450
                    Layout.preferredWidth: 350

                    TextField {
                        id: skinInput
                        Layout.fillWidth: true
                        placeholderText: (Backend ? Backend.tr("玩家UUID") : "玩家UUID")
                    }

                    Button {
                        Layout.fillWidth: true
                        text: (Backend ? Backend.tr("查询") : "查询")
                        onClicked: {
                            skinResult.text = (Backend ? Backend.tr("查询中...") : "查询中...")
                            capeResult.text = (Backend ? Backend.tr("查询中...") : "查询中...")
                            if (Backend) Backend.querySkin(skinInput.text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: skinResult
                            text: (Backend ? Backend.tr("皮肤的查询的结果") : "皮肤的查询的结果")
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Button {
                            text: (Backend ? Backend.tr("复制") : "复制")
                            onClicked: { if (Backend) Backend.copyToClipboard(skinResult.text) }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: capeResult
                            text: (Backend ? Backend.tr("披风的查询的结果") : "披风的查询的结果")
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Button {
                            text: (Backend ? Backend.tr("复制") : "复制")
                            onClicked: { if (Backend) Backend.copyToClipboard(capeResult.text) }
                        }
                    }
                }
            }
        }

    }
}
