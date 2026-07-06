import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: blorikoPage

    // 消息模型
    ListModel { id: messageModel }
    ListModel { id: providerModel }
    ListModel { id: modelModel }
    ListModel { id: roleModel }
    ListModel { id: historyListModel }

    property bool historyPanelOpen: false
    property string conversationTitle: ""
    property string currentEmotion: "neutral"

    // 情感状态 → emoji 映射
    property var emotionMap: ({
        "neutral": "😌 平静",
        "happy": "😊 开心",
        "shy": "😳 害羞",
        "angry": "😤 生气",
        "sad": "😢 难过",
        "excited": "🤩 兴奋",
        "curious": "🤔 好奇"
    })

    function getEmotionDisplay(emotion) {
        return emotionMap[emotion] || "😌 平静"
    }

    function loadProviders() {
        providerModel.clear()
        if (!Bloriko) return
        try {
            var providers = JSON.parse(Bloriko.getProviders())
            for (var i = 0; i < providers.length; i++)
                providerModel.append(providers[i])
            // 根据全局设置选中当前供应商
            if (Backend) {
                var globalProvider = Backend.getGlobalAIProvider()
                for (var j = 0; j < providerModel.count; j++) {
                    if (providerModel.get(j).key === globalProvider) {
                        providerCombo.currentIndex = j
                        break
                    }
                }
            }
            loadModels()
        } catch(e) { console.error("[Bloriko] loadProviders error:", e) }
    }

    function loadModels() {
        modelModel.clear()
        if (!Bloriko) return
        try {
            var models = JSON.parse(Bloriko.getModels())
            for (var i = 0; i < models.length; i++)
                modelModel.append(models[i])
            // 根据全局设置选中当前模型
            if (Backend) {
                var globalModel = Backend.getGlobalAIModel()
                for (var j = 0; j < modelModel.count; j++) {
                    if (modelModel.get(j).id === globalModel) {
                        modelCombo.currentIndex = j
                        return
                    }
                }
            }
            if (modelCombo.currentIndex < 0 && modelModel.count > 0)
                modelCombo.currentIndex = 0
        } catch(e) { console.error("[Bloriko] loadModels error:", e) }
    }

    function loadRoles() {
        roleModel.clear()
        if (!Bloriko) return
        try {
            var roles = JSON.parse(Bloriko.getAgentRoles())
            for (var i = 0; i < roles.length; i++)
                roleModel.append(roles[i])
        } catch(e) { console.error("[Bloriko] loadRoles error:", e) }
    }

    function loadHistoryList() {
        historyListModel.clear()
        if (!Bloriko) return
        try {
            var sessions = JSON.parse(Bloriko.getSessionList())
            for (var i = 0; i < sessions.length; i++) {
                var d = new Date(sessions[i].timestamp * 1000)
                var dateStr = d.toLocaleDateString() + " " + d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                var title = sessions[i].title || ""
                historyListModel.append({
                    filename: sessions[i].filename,
                    displayText: title.length > 0 ? title : dateStr,
                    subText: title.length > 0 ? dateStr + " · " + sessions[i].message_count + " 条" : sessions[i].message_count + " 条"
                })
            }
        } catch(e) {}
    }

    function rebuildMessageModelFromHistory() {
        messageModel.clear()
        if (!Bloriko) return
        try {
            var msgs = JSON.parse(Bloriko.getHistoryMessages())
            for (var i = 0; i < msgs.length; i++) {
                messageModel.append({
                    role: msgs[i].role,
                    content: msgs[i].content,
                    toolName: msgs[i].toolName || "",
                    toolArgs: msgs[i].toolArgs || "",
                    toolResult: msgs[i].toolResult || "",
                    streaming: false,
                    expanded: false
                })
            }
        } catch(e) {}
    }

    Component.onCompleted: {
        console.log("[Bloriko] onCompleted, Bloriko:", Bloriko)
        loadProviders()
        loadRoles()
        if (Bloriko) Bloriko.loadLatestSession()
        // 延迟重试：防止上下文属性延迟加载导致数据为空
        retryTimer.start()
    }

    Timer {
        id: retryTimer
        interval: 500
        repeat: false
        onTriggered: {
            if (providerModel.count === 0) {
                console.log("[Bloriko] Retrying data load (Bloriko:", Bloriko, ")")
                loadProviders()
                loadRoles()
            }
        }
    }

    // ============================================================
    // 主布局：左侧历史栏 + 右侧聊天区
    // ============================================================
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ========== 左侧历史栏 ==========
        Rectangle {
            id: historyPanel
            Layout.fillHeight: true
            Layout.preferredWidth: historyPanelOpen ? 220 : 0
            clip: true
            color: Theme.currentTheme.colors.cardColor || "#FAFAFA"
            border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
            border.width: historyPanelOpen ? 1 : 0

            Behavior on Layout.preferredWidth { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                visible: historyPanelOpen

                // 标题栏
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    color: "transparent"

                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 8
                        spacing: 8

                        Text {
                            text: "历史对话"
                            font.pixelSize: 13
                            font.bold: true
                            color: Theme.currentTheme.colors.textColor
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            text: "＋"
                            flat: true
                            implicitWidth: 28; implicitHeight: 28
                            font.pixelSize: 14
                            onClicked: {
                                messageModel.clear()
                                if (Bloriko) Bloriko.clearHistory()
                            }
                        }
                    }

                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }
                }

                // 历史列表
                ListView {
                    id: historyListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: historyListModel

                    delegate: ItemDelegate {
                        width: historyListView.width
                        height: 52

                        background: Rectangle {
                            color: hovered ? (Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0") : "transparent"
                        }

                        contentItem: ColumnLayout {
                            spacing: 2
                            anchors.leftMargin: 12; anchors.rightMargin: 8

                            Text {
                                text: model.displayText
                                font.pixelSize: 12
                                font.bold: model.displayText !== model.subText
                                color: Theme.currentTheme.colors.textColor
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }

                            Text {
                                text: model.subText
                                font.pixelSize: 10
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        onClicked: {
                            Bloriko.loadSession(model.filename)
                        }
                    }

                    // 空状态
                    Text {
                        anchors.centerIn: parent
                        text: "暂无历史记录"
                        font.pixelSize: 11
                        color: Theme.currentTheme.colors.textSecondaryColor
                        visible: historyListModel.count === 0
                    }
                }

                // 底部按钮
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    color: "transparent"

                    Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                    Button {
                        anchors.centerIn: parent
                        text: "刷新列表"
                        flat: true
                        font.pixelSize: 11
                        onClicked: loadHistoryList()
                    }
                }
            }
        }

        // ========== 右侧聊天区 ==========
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ===== 顶部栏 =====
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                color: "transparent"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 10

                    // 历史按钮
                    Button {
                        id: historyToggleBtn
                        icon.name: "ic_fluent_line_horizontal_3_20_regular"
                        flat: true
                        implicitWidth: 32; implicitHeight: 32
                        font.pixelSize: 16
                        onClicked: {
                            historyPanelOpen = !historyPanelOpen
                            if (historyPanelOpen) loadHistoryList()
                        }
                    }

                    Rectangle {
                        width: 24; height: 24; radius: 12; clip: true; color: "transparent"
                        Image { anchors.fill: parent; source: Qt.resolvedUrl("../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                    }

                    Text {
                        text: "络可"
                        font.pixelSize: 14
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }

                    Text {
                        text: conversationTitle ? "— " + conversationTitle : ""
                        font.pixelSize: 12
                        font.italic: true
                        color: Theme.currentTheme.colors.textSecondaryColor
                        visible: conversationTitle.length > 0
                    }

                    // 情感状态显示
                    Rectangle {
                        Layout.preferredWidth: emotionText.implicitWidth + 12
                        Layout.preferredHeight: 22
                        radius: 11
                        color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                        border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                        border.width: 1

                        Text {
                            id: emotionText
                            anchors.centerIn: parent
                            text: getEmotionDisplay(currentEmotion)
                            font.pixelSize: 10
                            color: Theme.currentTheme.colors.textColor
                        }
                    }

                    Text {
                        text: Bloriko && Bloriko.busy ? "思考中..." : "就绪"
                        font.pixelSize: 11
                        color: Bloriko && Bloriko.busy ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                    }

                    ComboBox {
                        id: roleCombo
                        Layout.preferredWidth: 80
                        model: roleModel
                        textRole: "name"
                        font.pixelSize: 10
                        enabled: Bloriko && !Bloriko.busy
                        onActivated: function(index) {
                            if (roleModel.count > 0) Bloriko.setAgentRole(roleModel.get(index).key)
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "新对话"
                        flat: true
                        font.pixelSize: 11
                        enabled: Bloriko && !Bloriko.busy
                        onClicked: { messageModel.clear(); if (Bloriko) Bloriko.clearHistory() }
                    }
                }

                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }
            }

            // ===== 消息列表 =====
            ListView {
                id: msgView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                model: messageModel

                onCountChanged: Qt.callLater(function() { msgView.positionViewAtEnd() })

                // 空状态
                Item {
                    anchors.centerIn: parent
                    width: 280; height: emptyCol.implicitHeight
                    visible: messageModel.count === 0

                    ColumnLayout {
                        id: emptyCol
                        width: parent.width; spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 64; height: 64; radius: 32; clip: true; color: "transparent"
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "络可"
                            font.pixelSize: 20; font.bold: true
                            color: Theme.currentTheme.colors.textColor
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.maximumWidth: 260
                            text: "哥哥好呀！络可在这里等你很久啦~(开心地挥挥小手)\n\n试试跟络可说：\n• 帮我创建一个文件\n• 搜索一下项目里的 TODO\n• 执行一个命令看看\n• 记住我的偏好是..."
                            horizontalAlignment: Text.AlignHCenter
                            font.pixelSize: 11
                            lineHeight: 1.4
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }
                    }
                }

                // ===== 内联委托 =====
                delegate: Item {
                    width: msgView.width
                    height: {
                        var h = 0
                        if (role === "user") h = userCol.height + 8
                        else if (role === "assistant") h = aiCol.height + 8
                        else if (role === "tool_call") h = tcCol.height + (toolResult && toolResult.length > 0 && expanded ? trResultCol.height + 4 : 0) + 4
                        else if (role === "error") h = errCol.height + 6
                        else if (role === "system") h = sysCol.height + 4
                        return h
                    }

                    // --- 用户消息 ---
                    Column {
                        id: userCol
                        visible: role === "user"
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.top: parent.top; anchors.topMargin: 4
                        width: Math.min(Math.max(userTxt.contentWidth + 24, 50), parent.width * 0.65)
                        spacing: 0

                        Rectangle {
                            width: parent.width; height: userTxt.contentHeight + 16
                            radius: 8
                            color: Theme.accentColor || "#0078D4"

                            TextEdit {
                                id: userTxt
                                anchors.fill: parent; anchors.margins: 8
                                text: content; color: "white"
                                font.pixelSize: 13
                                wrapMode: TextEdit.Wrap
                                readOnly: true; selectByMouse: true
                            }
                        }
                    }

                    // --- AI 文本 ---
                    RowLayout {
                        id: aiCol
                        visible: role === "assistant"
                        anchors.left: parent.left; anchors.leftMargin: 16
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.top: parent.top; anchors.topMargin: 4
                        spacing: 8

                        Rectangle {
                            width: 22; height: 22; radius: 11; clip: true; color: "transparent"
                            Layout.alignment: Qt.AlignTop
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: content || "..."
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textColor
                            wrapMode: Text.Wrap
                            textFormat: Text.MarkdownText
                            onLinkActivated: function(link) { Qt.openUrlExternally(link) }
                        }
                    }

                    // --- 工具调用（含可折叠结果） ---
                    Column {
                        id: tcCol
                        visible: role === "tool_call"
                        anchors.left: parent.left; anchors.leftMargin: 44
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.top: parent.top; anchors.topMargin: 2
                        width: parent.width - 60
                        spacing: 4

                        // 工具调用摘要（始终显示）
                        RowLayout {
                            width: parent.width
                            Layout.preferredHeight: 20
                            spacing: 6

                            MouseArea {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 20
                                cursorShape: toolResult && toolResult.length > 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: {
                                    if (toolResult && toolResult.length > 0) {
                                        messageModel.setProperty(index, "expanded", !expanded)
                                    }
                                }

                                RowLayout {
                                    width: parent.width
                                    spacing: 6

                                    Icon {
                                        icon: "ic_fluent_lightbulb_20_regular"
                                        size: 14
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        Layout.alignment: Qt.AlignTop
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: {
                                            var n = toolName || ""
                                            var a = ""
                                            try {
                                                var obj = JSON.parse(toolArgs || "{}")
                                                if (n === "read_file") a = obj.path || ""
                                                else if (n === "write_file") a = obj.path || ""
                                                else if (n === "edit_file") a = obj.path || ""
                                                else if (n === "list_files") a = obj.pattern || "*"
                                                else if (n === "search_text") a = obj.query || ""
                                                else if (n === "get_directory_tree") a = obj.path || ""
                                                else if (n === "ask_user") a = obj.question || ""
                                                else if (n === "execute_command") a = obj.command || ""
                                                else if (n === "execute_command_background") a = obj.command || ""
                                                else if (n === "spawn_agent") a = (obj.agent_type || "general") + ": " + (obj.prompt || "").substring(0, 40)
                                                else if (n === "memory") a = obj.action + " " + obj.target + ": " + (obj.content || obj.old_text || "").substring(0, 30)
                                                else if (n === "set_emotion") a = obj.emotion || ""
                                                else {
                                                    var parts = []
                                                    for (var k in obj) {
                                                        var v = String(obj[k])
                                                        if (v.length > 40) v = v.substring(0, 40) + "…"
                                                        parts.push(v)
                                                    }
                                                    a = parts.join(", ")
                                                }
                                                if (a.length > 80) a = a.substring(0, 80) + "…"
                                            } catch(e) { a = toolArgs || "" }

                                            var nameMap = {
                                                "read_file": "读取",
                                                "write_file": "写入",
                                                "edit_file": "编辑",
                                                "list_files": "列出文件",
                                                "search_text": "搜索",
                                                "get_directory_tree": "查看目录树",
                                                "ask_user": "向用户提问",
                                                "execute_command": "执行命令",
                                                "execute_command_background": "后台执行",
                                                "spawn_agent": "生成子 Agent",
                                                "memory": "管理记忆",
                                                "set_emotion": "更新情感"
                                            }
                                            var displayName = nameMap[n] || n
                                            return a ? displayName + " " + a : displayName
                                        }
                                        font.pixelSize: 12
                                        color: Theme.currentTheme.colors.textColor
                                        opacity: 0.7
                                        wrapMode: Text.Wrap
                                    }

                                    Text {
                                        text: toolResult && toolResult.length > 0 ? (expanded ? "▼" : "▶") : ""
                                        font.pixelSize: 11
                                        color: Theme.currentTheme.colors.textColor
                                        opacity: 0.5
                                        Layout.alignment: Qt.AlignTop
                                    }
                                }
                            }
                        }

                        // 工具结果（可折叠）
                        RowLayout {
                            id: trResultCol
                            visible: toolResult && toolResult.length > 0 && expanded
                            width: parent.width
                            spacing: 6

                            Text {
                                text: "└"
                                font.pixelSize: 11
                                font.family: "Consolas, monospace"
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.alignment: Qt.AlignTop
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: Math.min(trResultTxt.contentHeight + 12, 160)
                                radius: 4
                                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F5F5F5"
                                border.color: Theme.currentTheme.colors.controlBorderColor || "#E8E8E8"
                                border.width: 1

                                Flickable {
                                    anchors.fill: parent; anchors.margins: 6
                                    contentHeight: trResultTxt.contentHeight
                                    clip: true
                                    interactive: contentHeight > height

                                    TextEdit {
                                        id: trResultTxt
                                        width: parent.width
                                        text: {
                                            var r = toolResult || ""
                                            if (r.length > 500) r = r.substring(0, 500) + "\n... (已截断)"
                                            return r
                                        }
                                        font.pixelSize: 11
                                        font.family: "Consolas, monospace"
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        wrapMode: TextEdit.Wrap
                                        readOnly: true; selectByMouse: true
                                    }
                                }
                            }
                        }
                    }

                    // --- 错误消息 ---
                    RowLayout {
                        id: errCol
                        visible: role === "error"
                        anchors.left: parent.left; anchors.leftMargin: 44
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.top: parent.top; anchors.topMargin: 3
                        spacing: 6

                        Icon { icon: "ic_fluent_warning_20_regular"; size: 14; color: "#E8A33D"; Layout.alignment: Qt.AlignTop }

                        Text {
                            Layout.fillWidth: true
                            text: content
                            font.pixelSize: 12
                            color: "#E8A33D"
                            wrapMode: Text.Wrap
                        }
                    }

                    // --- 系统消息 ---
                    RowLayout {
                        id: sysCol
                        visible: role === "system"
                        anchors.left: parent.left; anchors.leftMargin: 44
                        anchors.right: parent.right; anchors.rightMargin: 16
                        anchors.top: parent.top; anchors.topMargin: 2
                        spacing: 6

                        Text { text: "ℹ"; font.pixelSize: 10; color: Theme.currentTheme.colors.textSecondaryColor; Layout.alignment: Qt.AlignTop }

                        Text {
                            Layout.fillWidth: true
                            text: content
                            font.pixelSize: 11
                            font.italic: true
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            // ===== 输入栏 =====
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: (Bloriko && Bloriko.busy ? progressBar.height + 4 : 0) + inputRow.implicitHeight + 16
                color: Theme.currentTheme.colors.cardColor || "#FFFFFF"
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                // 生成中的进度条
                ProgressBar {
                    id: progressBar
                    anchors.top: parent.top; anchors.topMargin: 1
                    width: parent.width
                    indeterminate: Bloriko && Bloriko.busy
                    visible: Bloriko && Bloriko.busy
                }

                ColumnLayout {
                    id: inputRow
                    anchors.fill: parent; anchors.margins: 8; anchors.leftMargin: 12; anchors.rightMargin: 12
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true; spacing: 8

                        ComboBox {
                            id: providerCombo
                            Layout.preferredWidth: 130
                            model: providerModel; textRole: "name"
                            font.pixelSize: 10
                            enabled: Bloriko && !Bloriko.busy
                            onActivated: function(index) {
                                var item = providerModel.get(index)
                                // 写入全局配置，所有 AI 功能同步
                                if (Backend) Backend.setGlobalAIProvider(item.key)
                                loadModels()
                            }
                        }

                        ComboBox {
                            id: modelCombo
                            Layout.fillWidth: true
                            model: modelModel; textRole: "name"
                            font.pixelSize: 10
                            enabled: Bloriko && !Bloriko.busy && modelModel.count > 0
                            onActivated: function(index) {
                                if (modelModel.count > 0 && Backend)
                                    Backend.setGlobalAIModel(modelModel.get(index).id)
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(inputField.implicitHeight + 12, 36)
                            radius: 8
                            color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                            border.color: inputField.activeFocus ? (Theme.accentColor || "#0078D4") : (Theme.currentTheme.colors.controlBorderColor || "#E0E0E0")
                            border.width: 1

                            TextArea {
                                id: inputField
                                anchors.fill: parent; anchors.margins: 6
                                placeholderText: "向络可说些什么... (Enter 发送, Shift+Enter 换行)"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                                enabled: Bloriko && !Bloriko.busy
                                background: Item {}

                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                        if (event.modifiers & Qt.ShiftModifier) {
                                            inputField.insert(inputField.cursorPosition, "\n")
                                        } else {
                                            sendBtn.clicked(); event.accepted = true
                                        }
                                    }
                                }
                            }
                        }

                        Button {
                            id: sendBtn
                            icon.name: Bloriko && Bloriko.busy ? "ic_fluent_stop_20_regular" : "ic_fluent_send_20_regular"
                            Layout.preferredWidth: 36; Layout.preferredHeight: 36
                            highlighted: true
                            enabled: {
                                if (!Bloriko) return false
                                if (Bloriko.busy) return true
                                return inputField.text.trim().length > 0
                            }
                            onClicked: {
                                if (Bloriko.busy) { Bloriko.cancelAgent(); return }
                                var text = inputField.text.trim()
                                if (text.length === 0) return
                                messageModel.append({role: "user", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
                                Bloriko.sendMessage(text)
                                inputField.text = ""
                            }
                        }
                    }
                }
            }
        }
    }

    // ============================================================
    // 对话框
    // ============================================================

    // 权限对话框
    Dialog {
        id: permDlg
        title: "权限请求"; modal: true; width: 400; closePolicy: Popup.NoAutoClose
        property string pName: ""; property string pDesc: ""; property string pReason: ""

        contentItem: ColumnLayout {
            spacing: 10
            Text { text: "络可想要执行写入操作："; font.pixelSize: 13; font.bold: true; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: permTxt.implicitHeight + 12; radius: 6
                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#FFF3CD"
                border.color: Theme.currentTheme.colors.controlBorderColor; border.width: 1
                Text { id: permTxt; anchors.fill: parent; anchors.margins: 6; text: permDlg.pName + "\n" + permDlg.pDesc; font.pixelSize: 12; font.family: "Consolas, monospace"; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap }
            }
            ColumnLayout {
                visible: permDlg.pReason.length > 0
                spacing: 4
                Text { text: "络可的理由："; font.pixelSize: 11; font.bold: true; color: Theme.currentTheme.colors.textSecondaryColor }
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: Math.min(reasonTxt.implicitHeight + 12, 120); radius: 6
                    color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                    border.color: Theme.currentTheme.colors.controlBorderColor; border.width: 1
                    Flickable {
                        anchors.fill: parent; anchors.margins: 6
                        contentHeight: reasonTxt.contentHeight
                        clip: true; interactive: contentHeight > height
                        Text { id: reasonTxt; width: parent.width; text: permDlg.pReason; font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap }
                    }
                }
            }
            RowLayout { Layout.fillWidth: true; spacing: 8
                Button { text: "拒绝"; flat: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Bloriko) Bloriko.denyPermission() } }
                Button { text: "允许"; highlighted: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Bloriko) Bloriko.approvePermission() } }
            }
        }
    }

    // AI 提问对话框
    Dialog {
        id: askDlg
        title: "络可提问"; modal: true; width: 400; closePolicy: Popup.NoAutoClose
        property string qText: ""
        property string qType: "text"
        property var qOptions: []
        property var selectedOptions: ({})
        property bool showCustomInput: false

        function collectAnswer() {
            if (qType === "single_choice") {
                if (showCustomInput) {
                    var ca = askCustomField.text.trim()
                    return ca.length > 0 ? ca : "用户未回答"
                }
                for (var key in selectedOptions) {
                    if (selectedOptions[key]) return key
                }
                return "用户未选择"
            } else if (qType === "multiple_choice") {
                if (showCustomInput) {
                    var ca2 = askCustomField2.text.trim()
                    return ca2.length > 0 ? ca2 : "用户未回答"
                }
                var selected = []
                for (var k in selectedOptions) {
                    if (selectedOptions[k]) selected.push(k)
                }
                return selected.length > 0 ? selected.join(", ") : "用户未选择"
            } else {
                var a = askAnsField.text.trim()
                return a.length > 0 ? a : "用户未回答"
            }
        }

        function selectCustomInput() {
            for (var k in selectedOptions)
                selectedOptions[k] = false
            showCustomInput = true
            var tmp = selectedOptions
            selectedOptions = {}
            selectedOptions = tmp
        }

        contentItem: ColumnLayout {
            spacing: 10

            Text { text: askDlg.qText; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }

            // 单项选择
            ColumnLayout {
                visible: askDlg.qType === "single_choice"
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: askDlg.qOptions
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: 6
                        color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") + "15" : "transparent"
                        border.color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                            spacing: 8
                            Rectangle {
                                width: 16; height: 16; radius: 8
                                border.color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                                border.width: 2
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 8; height: 8; radius: 4
                                    color: Theme.accentColor || "#0078D4"
                                    visible: !!askDlg.selectedOptions[modelData]
                                }
                            }
                            Text { text: modelData; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                askDlg.showCustomInput = false
                                for (var k in askDlg.selectedOptions)
                                    askDlg.selectedOptions[k] = false
                                askDlg.selectedOptions[modelData] = true
                                var tmp = askDlg.selectedOptions
                                askDlg.selectedOptions = {}
                                askDlg.selectedOptions = tmp
                            }
                        }
                    }
                }
                // "我想给出我的答案" 选项
                Rectangle {
                    Layout.fillWidth: true
                    height: 36; radius: 6
                    color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") + "15" : "transparent"
                    border.color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                        spacing: 8
                        Rectangle {
                            width: 16; height: 16; radius: 8
                            border.color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                            border.width: 2
                            Rectangle {
                                anchors.centerIn: parent
                                width: 8; height: 8; radius: 4
                                color: Theme.accentColor || "#0078D4"
                                visible: askDlg.showCustomInput
                            }
                        }
                        Text { text: "✏ 我想给出我的答案"; font.pixelSize: 13; font.italic: true; color: Theme.currentTheme.colors.textColor }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: askDlg.selectCustomInput()
                    }
                }
                Rectangle {
                    visible: askDlg.showCustomInput
                    Layout.fillWidth: true; Layout.preferredHeight: 56; radius: 6
                    color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                    border.color: askCustomField.activeFocus ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor; border.width: 1
                    TextArea { id: askCustomField; anchors.fill: parent; anchors.margins: 6; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: TextArea.Wrap; placeholderText: "输入你的回答..."; background: Item {} }
                }
            }

            // 多项选择
            ColumnLayout {
                visible: askDlg.qType === "multiple_choice"
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: askDlg.qOptions
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 36; radius: 6
                        color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") + "15" : "transparent"
                        border.color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                            spacing: 8
                            Rectangle {
                                width: 16; height: 16; radius: 3
                                border.color: !!askDlg.selectedOptions[modelData] ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                                border.width: 2
                                color: "transparent"
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 8; height: 8; radius: 1
                                    color: Theme.accentColor || "#0078D4"
                                    visible: !!askDlg.selectedOptions[modelData]
                                }
                            }
                            Text { text: modelData; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                askDlg.showCustomInput = false
                                askDlg.selectedOptions[modelData] = !askDlg.selectedOptions[modelData]
                                var tmp = askDlg.selectedOptions
                                askDlg.selectedOptions = {}
                                askDlg.selectedOptions = tmp
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 36; radius: 6
                    color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") + "15" : "transparent"
                    border.color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                        spacing: 8
                        Rectangle {
                            width: 16; height: 16; radius: 3
                            border.color: askDlg.showCustomInput ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                            border.width: 2
                            color: "transparent"
                            Rectangle {
                                anchors.centerIn: parent
                                width: 8; height: 8; radius: 1
                                color: Theme.accentColor || "#0078D4"
                                visible: askDlg.showCustomInput
                            }
                        }
                        Text { text: "✏ 我想给出我的答案"; font.pixelSize: 13; font.italic: true; color: Theme.currentTheme.colors.textColor }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: askDlg.selectCustomInput()
                    }
                }
                Rectangle {
                    visible: askDlg.showCustomInput
                    Layout.fillWidth: true; Layout.preferredHeight: 56; radius: 6
                    color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                    border.color: askCustomField2.activeFocus ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor; border.width: 1
                    TextArea { id: askCustomField2; anchors.fill: parent; anchors.margins: 6; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: TextArea.Wrap; placeholderText: "输入你的回答..."; background: Item {} }
                }
            }

            // 文本输入
            Rectangle {
                visible: askDlg.qType === "text"
                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: 6
                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                border.color: askAnsField.activeFocus ? (Theme.accentColor || "#0078D4") : (Theme.currentTheme.colors.controlBorderColor); border.width: 1
                TextEdit { id: askAnsField; anchors.fill: parent; anchors.margins: 6; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: TextEdit.Wrap; focus: true }
            }

            RowLayout { Layout.fillWidth: true; spacing: 8
                Button { text: "取消"; flat: true; Layout.fillWidth: true; onClicked: { askDlg.close(); if (Bloriko) Bloriko.answerQuestion("用户取消") } }
                Button {
                    text: askDlg.qType === "text" ? "发送" : "确认"; highlighted: true; Layout.fillWidth: true
                    onClicked: {
                        var answer = askDlg.collectAnswer()
                        askDlg.close()
                        if (Bloriko) Bloriko.answerQuestion(answer)
                    }
                }
            }
        }
    }

    // ============================================================
    // Bloriko 信号
    // ============================================================
    Connections {
        target: Bloriko; enabled: Bloriko !== null

        function onTextUpdated(text) {
            var lastIdx = messageModel.count - 1
            if (lastIdx >= 0 && messageModel.get(lastIdx).role === "assistant" && messageModel.get(lastIdx).streaming) {
                messageModel.set(lastIdx, {role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true})
            } else {
                messageModel.append({role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true, expanded: false})
            }
        }

        function onToolCallStarted(toolName, argsJson) {
            var insertIdx = messageModel.count
            for (var i = messageModel.count - 1; i >= 0; i--) {
                var item = messageModel.get(i)
                if (item.role === "tool_call") {
                    insertIdx = i + 1
                    break
                }
                if (item.role === "assistant") {
                    insertIdx = i + 1
                    break
                }
            }
            messageModel.insert(insertIdx, {role: "tool_call", content: "", toolName: toolName, toolArgs: argsJson, toolResult: "", streaming: false, expanded: false})
        }

        function onToolCallFinished(toolName, argsJson, result) {
            for (var i = messageModel.count - 1; i >= 0; i--) {
                var item = messageModel.get(i)
                if (item.role === "tool_call" && item.toolName === toolName && item.toolResult === "") {
                    messageModel.set(i, {toolResult: result})
                    return
                }
            }
            messageModel.append({role: "tool_call", content: "", toolName: toolName, toolArgs: argsJson, toolResult: result, streaming: false, expanded: false})
        }

        function onErrorOccurred(msg) {
            messageModel.append({role: "error", content: msg, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }

        function onMessageAdded(role, content, toolCallsJson) {
            for (var i = messageModel.count - 1; i >= 0; i--) {
                if (messageModel.get(i).role === "assistant" && messageModel.get(i).streaming) {
                    messageModel.set(i, {role: "assistant", content: content, streaming: false})
                    return
                }
            }
            messageModel.append({role: role, content: content, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }

        function onProvidersChanged() { loadProviders() }

        function onPermissionRequested(toolName, argsJson, description, reasoning) {
            permDlg.pName = toolName
            permDlg.pDesc = description
            permDlg.pReason = reasoning || ""
            permDlg.open()
        }

        function onQuestionAsked(question, questionType, optionsJson) {
            askDlg.qText = question
            askDlg.qType = questionType || "text"
            askDlg.showCustomInput = false
            try {
                askDlg.qOptions = JSON.parse(optionsJson || "[]")
            } catch(e) {
                askDlg.qOptions = []
            }
            askDlg.selectedOptions = {}
            if (askDlg.qType === "single_choice" || askDlg.qType === "multiple_choice") {
                for (var i = 0; i < askDlg.qOptions.length; i++)
                    askDlg.selectedOptions[askDlg.qOptions[i]] = false
            }
            askDlg.open()
        }

        function onSessionLoaded() {
            rebuildMessageModelFromHistory()
            conversationTitle = Bloriko ? (Bloriko.title || "") : ""
            currentEmotion = Bloriko ? (Bloriko.emotion || "neutral") : "neutral"
        }

        function onTitleChanged(title) {
            conversationTitle = title
        }

        function onStatusMessage(msg) {
            messageModel.append({role: "system", content: msg, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }

        function onEmotionChanged(emotion) {
            currentEmotion = emotion
        }
    }
}
