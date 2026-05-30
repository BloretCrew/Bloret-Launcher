import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: agentPage

    // 消息模型
    ListModel {
        id: messageModel
    }

    // 提供商列表
    ListModel {
        id: providerModel
    }

    // 模型列表
    ListModel {
        id: modelModel
    }

    // 加载提供商和模型
    function loadProviders() {
        providerModel.clear()
        modelModel.clear()
        if (!Agent) return
        try {
            var providers = JSON.parse(Agent.getProviders())
            for (var i = 0; i < providers.length; i++) {
                providerModel.append(providers[i])
            }
            loadModels()
        } catch(e) {}
    }

    function loadModels() {
        modelModel.clear()
        if (!Agent) return
        try {
            var models = JSON.parse(Agent.getModels())
            for (var i = 0; i < models.length; i++) {
                modelModel.append(models[i])
            }
        } catch(e) {}
    }

    Component.onCompleted: {
        loadProviders()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ========== 顶部栏 ==========
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                Label {
                    text: "🤖"
                    font.pixelSize: 20
                }

                Label {
                    text: "AI 助手"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    text: Agent && Agent.busy ? "思考中..." : "就绪"
                    font.pixelSize: 12
                    color: Agent && Agent.busy ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "清除对话"
                    flat: true
                    enabled: Agent && !Agent.busy
                    onClicked: {
                        messageModel.clear()
                        if (Agent) Agent.clearHistory()
                    }
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Theme.currentTheme.colors.controlBorderColor
            }
        }

        // ========== 消息列表 ==========
        ListView {
            id: messageListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 12
            model: messageModel

            onCountChanged: {
                Qt.callLater(function() {
                    messageListView.positionViewAtEnd()
                })
            }

            // 空状态
            Item {
                anchors.centerIn: parent
                width: 300
                height: emptyColumn.height
                visible: messageModel.count === 0

                ColumnLayout {
                    id: emptyColumn
                    width: parent.width
                    spacing: 12

                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "🤖"
                        font.pixelSize: 48
                    }

                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "AI 助手"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.maximumWidth: 280
                        text: "用自然语言描述你想做的修改，AI 会帮你操作资源包。\n\n试试：\n• 帮我看看这个资源包有什么文件\n• 读取 pack.mcmeta\n• 把描述改成 '我的资源包'"
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 12
                        lineHeight: 1.5
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.Wrap
                    }
                }
            }

            delegate: Item {
                width: messageListView.width
                height: {
                    if (role === "user") return userBubbleColumn.height + 8
                    return aiColumn.height + 8
                }

                // 用户消息（右对齐）
                Column {
                    id: userBubbleColumn
                    visible: role === "user"
                    anchors.right: parent.right
                    anchors.rightMargin: 16
                    width: Math.min(Math.max(userText.contentWidth + 32, 60), parent.width * 0.7)
                    spacing: 0

                    Rectangle {
                        width: parent.width
                        height: userText.implicitHeight + 24
                        radius: 12
                        color: Theme.accentColor || "#0078D4"

                        TextEdit {
                            id: userText
                            anchors.fill: parent
                            anchors.margins: 12
                            text: content
                            color: "white"
                            font.pixelSize: 13
                            wrapMode: TextEdit.Wrap
                            readOnly: true
                            selectByMouse: true
                            textFormat: TextEdit.PlainText
                        }
                    }
                }

                // AI 消息（左对齐）
                ColumnLayout {
                    id: aiColumn
                    visible: role === "assistant"
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    width: Math.min(parent.width * 0.8, 600)
                    spacing: 6

                    RowLayout {
                        spacing: 8
                        Layout.fillWidth: true

                        Rectangle {
                            width: 28
                            height: 28
                            radius: 14
                            color: Theme.currentTheme.colors.controlAltSecondaryColor || "#E0E0E0"
                            Layout.alignment: Qt.AlignTop

                            Label {
                                anchors.centerIn: parent
                                text: "🤖"
                                font.pixelSize: 14
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 12
                            color: Theme.currentTheme.colors.cardColor || "#FFFFFF"
                            border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                            border.width: 1
                            implicitHeight: aiTextContent.implicitHeight + 24

                            TextEdit {
                                id: aiTextContent
                                anchors.fill: parent
                                anchors.margins: 12
                                text: content
                                color: Theme.currentTheme.colors.textColor || "#000000"
                                font.pixelSize: 13
                                wrapMode: TextEdit.Wrap
                                readOnly: true
                                selectByMouse: true
                                textFormat: TextEdit.MarkdownText
                                onLinkActivated: function(link) {
                                    Qt.openUrlExternally(link)
                                }
                            }
                        }
                    }

                    // 工具调用列表
                    Repeater {
                        id: toolRepeater
                        model: {
                            try {
                                return JSON.parse(toolCalls || "[]")
                            } catch(e) {
                                return []
                            }
                        }

                        delegate: Rectangle {
                            Layout.fillWidth: true
                            Layout.leftMargin: 36
                            radius: 8
                            color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                            border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                            border.width: 1
                            implicitHeight: toolCol.implicitHeight + 16
                            property var toolData: model.modelData !== undefined ? model.modelData : modelData

                            ColumnLayout {
                                id: toolCol
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 4

                                RowLayout {
                                    spacing: 6

                                    Label {
                                        text: "🔧"
                                        font.pixelSize: 12
                                    }

                                    Label {
                                        text: toolData.name || ""
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        font.family: "Consolas, monospace"
                                        color: Theme.currentTheme.colors.textColor || "#000000"
                                    }
                                }

                                Label {
                                    text: {
                                        try {
                                            var args = JSON.parse(toolData.arguments || "{}")
                                            var parts = []
                                            for (var key in args) {
                                                var val = String(args[key])
                                                if (val.length > 60) val = val.substring(0, 60) + "..."
                                                parts.push(key + ": " + val)
                                            }
                                            return parts.join(", ")
                                        } catch(e) {
                                            return toolData.arguments || ""
                                        }
                                    }
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textSecondaryColor || "#808080"
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                    font.family: "Consolas, monospace"
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 1
                                    color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                                    visible: toolData.result !== undefined && toolData.result !== ""
                                }

                                Label {
                                    text: {
                                        if (toolData.result === undefined || toolData.result === "") return ""
                                        var r = toolData.result || ""
                                        if (r.length > 200) r = r.substring(0, 200) + "..."
                                        return "✅ " + r
                                    }
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textSecondaryColor || "#808080"
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                    visible: toolData.result !== undefined && toolData.result !== ""
                                }
                            }
                        }
                    }
                }
            }
        }

        // ========== 正在执行的工具 ==========
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: (Agent && Agent.busy && activeToolName.text !== "") ? 36 : 0
            color: "transparent"
            clip: true

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                spacing: 8

                BusyIndicator {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    running: true
                }

                Label {
                    id: activeToolName
                    text: ""
                    font.pixelSize: 12
                    font.family: "Consolas, monospace"
                    color: Theme.currentTheme.colors.textSecondaryColor || "#808080"
                }
            }
        }

        // ========== 输入栏 ==========
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: inputRow.implicitHeight + 20
            color: Theme.currentTheme.colors.cardColor || "#FFFFFF"

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
            }

            ColumnLayout {
                id: inputRow
                anchors.fill: parent
                anchors.margins: 8
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    // 提供商选择
                    ComboBox {
                        id: providerCombo
                        Layout.preferredWidth: 130
                        model: providerModel
                        textRole: "name"
                        currentIndex: 0
                        font.pixelSize: 11
                        enabled: Agent && !Agent.busy

                        onCurrentIndexChanged: {
                            if (providerModel.count > 0 && Agent) {
                                var key = providerModel.get(currentIndex).key
                                Agent.setProvider(key)
                                loadModels()
                            }
                        }
                    }

                    // 模型选择
                    ComboBox {
                        id: modelCombo
                        Layout.fillWidth: true
                        model: modelModel
                        textRole: "name"
                        currentIndex: 0
                        font.pixelSize: 11
                        enabled: Agent && !Agent.busy

                        onCurrentIndexChanged: {
                            if (modelModel.count > 0 && Agent) {
                                Agent.setModel(modelModel.get(currentIndex).id)
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextArea {
                        id: inputField
                        Layout.fillWidth: true
                        Layout.minimumHeight: 36
                        Layout.maximumHeight: 120
                        placeholderText: "输入消息... (Enter 发送, Shift+Enter 换行)"
                        wrapMode: TextArea.Wrap
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textColor || "#000000"
                        enabled: Agent && !Agent.busy

                        background: Rectangle {
                            radius: 8
                            color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                            border.color: inputField.activeFocus
                                ? (Theme.accentColor || "#0078D4")
                                : (Theme.currentTheme.colors.controlBorderColor || "#E0E0E0")
                            border.width: 1
                        }

                        Keys.onPressed: function(event) {
                            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                if (event.modifiers & Qt.ShiftModifier) {
                                    inputField.insert(inputField.cursorPosition, "\n")
                                } else {
                                    sendButton.clicked()
                                    event.accepted = true
                                }
                            }
                        }
                    }

                    Button {
                        id: sendButton
                        text: Agent && Agent.busy ? "⏹" : "➤"
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 36
                        enabled: {
                            if (!Agent) return false
                            if (Agent.busy) return true
                            return inputField.text.trim().length > 0
                        }

                        onClicked: {
                            if (Agent.busy) {
                                Agent.cancelAgent()
                                return
                            }
                            var text = inputField.text.trim()
                            if (text.length === 0) return

                            messageModel.append({
                                role: "user",
                                content: text,
                                toolCalls: "[]",
                                streaming: false
                            })

                            Agent.sendMessage(text)
                            inputField.text = ""
                        }
                    }
                }
            }
        }
    }

    // ========== Agent 信号 ==========
    Connections {
        target: Agent
        enabled: Agent !== null

        function onTextUpdated(text) {
            var lastIdx = messageModel.count - 1
            if (lastIdx >= 0 && messageModel.get(lastIdx).role === "assistant" && messageModel.get(lastIdx).streaming) {
                messageModel.set(lastIdx, {
                    role: "assistant",
                    content: text,
                    toolCalls: messageModel.get(lastIdx).toolCalls,
                    streaming: true
                })
            } else {
                messageModel.append({
                    role: "assistant",
                    content: text,
                    toolCalls: "[]",
                    streaming: true
                })
            }
        }

        function onToolCallStarted(toolName, argsJson) {
            activeToolName.text = "调用工具: " + toolName
        }

        function onToolCallFinished(toolName, argsJson, result) {
            activeToolName.text = ""
        }

        function onErrorOccurred(msg) {
            messageModel.append({
                role: "assistant",
                content: "⚠ " + msg,
                toolCalls: "[]",
                streaming: false
            })
        }

        function onMessageAdded(role, content, toolCallsJson) {
            for (var i = messageModel.count - 1; i >= 0; i--) {
                if (messageModel.get(i).role === role && messageModel.get(i).streaming) {
                    messageModel.set(i, {
                        role: role,
                        content: content,
                        toolCalls: toolCallsJson,
                        streaming: false
                    })
                    return
                }
            }
            messageModel.append({
                role: role,
                content: content,
                toolCalls: toolCallsJson,
                streaming: false
            })
        }
    }
}
