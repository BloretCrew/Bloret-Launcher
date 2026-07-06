import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: agentPage

    // 消息模型
    ListModel { id: messageModel }
    ListModel { id: providerModel }
    ListModel { id: modelModel }
    ListModel { id: roleModel }
    ListModel { id: historyListModel }

    property bool historyPanelOpen: false
    property string conversationTitle: ""

    function loadProviders() {
        providerModel.clear()
        if (!Agent) return
        try {
            var providers = JSON.parse(Agent.getProviders())
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
        } catch(e) {}
    }

    function loadModels() {
        modelModel.clear()
        if (!Agent) return
        try {
            var models = JSON.parse(Agent.getModels())
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
        } catch(e) {}
    }

    function loadRoles() {
        roleModel.clear()
        if (!Agent) return
        try {
            var roles = JSON.parse(Agent.getAgentRoles())
            for (var i = 0; i < roles.length; i++)
                roleModel.append(roles[i])
            syncRoleCombo()
        } catch(e) {}
    }

    function syncRoleCombo() {
        if (!Agent || roleModel.count === 0) {
            roleCombo.currentIndex = -1
            return
        }

        var currentRole = Agent.agentRole
        for (var j = 0; j < roleModel.count; j++) {
            if (roleModel.get(j).key === currentRole) {
                roleCombo.currentIndex = j
                return
            }
        }

        roleCombo.currentIndex = 0
        Agent.setAgentRole(roleModel.get(0).key)
    }

    function loadHistoryList() {
        historyListModel.clear()
        if (!Agent) return
        try {
            var sessions = JSON.parse(Agent.getSessionList())
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
        if (!Agent) return
        try {
            var msgs = JSON.parse(Agent.getHistoryMessages())
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
        loadProviders()
        loadRoles()
        if (Agent) Agent.loadLatestSession()
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
                                if (Agent) Agent.clearHistory()
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
                            Agent.loadSession(model.filename)
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
                        Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/BLRPE.png"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                    }

                    Text {
                        text: "BLRPE Copilot"
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

                    Text {
                        text: Agent && Agent.busy ? "思考中..." : "就绪"
                        font.pixelSize: 11
                        color: Agent && Agent.busy ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                    }

                    ComboBox {
                        id: roleCombo
                        Layout.preferredWidth: 80
                        model: roleModel
                        textRole: "name"
                        font.pixelSize: 10
                        enabled: Agent && !Agent.busy && roleModel.count > 0
                        onActivated: function(index) {
                            if (index >= 0 && index < roleModel.count)
                                Agent.setAgentRole(roleModel.get(index).key)
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "新对话"
                        flat: true
                        font.pixelSize: 11
                        enabled: Agent && !Agent.busy
                        onClicked: { messageModel.clear(); if (Agent) Agent.clearHistory() }
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
                            width: 56; height: 56; radius: 28; clip: true; color: "transparent"
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/BLRPE.png"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "BLRPE Copilot"
                            font.pixelSize: 18; font.bold: true
                            color: Theme.currentTheme.colors.textColor
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.maximumWidth: 260
                            text: "用自然语言描述你想做的修改\nAI 会帮你操作资源包\n\n试试：\n• 帮我看看这个资源包\n• 读取 pack.mcmeta\n• 把描述改成 '我的资源包'"
                            horizontalAlignment: Text.AlignHCenter
                            font.pixelSize: 11
                            lineHeight: 1.4
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }
                    }
                }

                // ===== 内联委托（无 Loader/Component）=====
                delegate: Item {
                    width: msgView.width
                    height: {
                        var h = 0
                        if (role === "user") h = userCol.height + 8
                        else if (role === "assistant") h = aiCol.height + 8
                        else if (role === "tool_call") h = tcCol.height + (toolResult && toolResult.length > 0 && expanded ? trResultCol.height + 4 : 0) + 4
                        else if (role === "error") h = errCol.height + 6
                        else if (role === "system") h = sysCol.height + 4
                        if (role === "tool_call") console.log("[AgentTab] tool_call height: tcCol=" + tcCol.height + ", item=" + h)
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
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/BLRPE.png"); fillMode: Image.PreserveAspectCrop; mipmap: true }
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
                        Component.onCompleted: console.log("[AgentTab] tcCol 创建: role=" + role + ", toolName=" + toolName + ", height=" + height)
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

                            // 点击切换展开/折叠
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
                                                // 生成人类可读摘要
                                                if (n === "read_file") a = obj.path || ""
                                                else if (n === "write_file") a = obj.path || ""
                                                else if (n === "edit_file") a = obj.path || ""
                                                else if (n === "list_files") a = obj.pattern || "*"
                                                else if (n === "search_text") a = obj.query || ""
                                                else if (n === "get_pack_info") a = ""
                                                else if (n === "analyze_pack") a = ""
                                                else if (n === "read_language") a = obj.lang || ""
                                                else if (n === "edit_language") a = obj.lang || ""
                                                else if (n === "validate_json") a = obj.path || ""
                                                else if (n === "get_file_tree") a = ""
                                                else if (n === "ask_user") a = obj.question || ""
                                                else if (n === "execute_command") a = obj.command || ""
                                                else if (n === "execute_command_background") a = obj.command || ""
                                                else if (n === "spawn_agent") a = (obj.agent_type || "general") + ": " + (obj.prompt || "").substring(0, 40)
                                                else {
                                                    // fallback: 显示参数摘要
                                                    var parts = []
                                                    for (var k in obj) {
                                                        var v = String(obj[k])
                                                        if (v.length > 40) v = v.substring(0, 40) + "…"
                                                        parts.push(v)
                                                    }
                                                    a = parts.join(", ")
                                                }
                                                // 截断过长内容
                                                if (a.length > 80) a = a.substring(0, 80) + "…"
                                            } catch(e) { a = toolArgs || "" }

                                            // 工具名中文映射
                                            var nameMap = {
                                                "read_file": "读取",
                                                "write_file": "写入",
                                                "edit_file": "编辑",
                                                "list_files": "列出文件",
                                                "search_text": "搜索",
                                                "get_pack_info": "获取资源包信息",
                                                "analyze_pack": "分析资源包",
                                                "read_language": "读取语言文件",
                                                "edit_language": "编辑语言文件",
                                                "validate_json": "验证 JSON",
                                                "get_file_tree": "获取文件树",
                                                "ask_user": "向用户提问",
                                                "execute_command": "执行命令",
                                                "execute_command_background": "后台执行",
                                                "spawn_agent": "生成子 Agent"
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
                Layout.preferredHeight: (Agent && Agent.busy ? progressBar.height + 4 : 0) + inputRow.implicitHeight + 16
                color: Theme.currentTheme.colors.cardColor || "#FFFFFF"
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                // 生成中的进度条
                ProgressBar {
                    id: progressBar
                    anchors.top: parent.top; anchors.topMargin: 1
                    width: parent.width
                    indeterminate: Agent && Agent.busy
                    visible: Agent && Agent.busy
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
                            enabled: Agent && !Agent.busy
                            onActivated: function(index) {
                                var item = providerModel.get(index)
                                Agent.setProvider(item.key); loadModels()
                            }
                        }

                        ComboBox {
                            id: modelCombo
                            Layout.fillWidth: true
                            model: modelModel; textRole: "name"
                            font.pixelSize: 10
                            enabled: Agent && !Agent.busy && modelModel.count > 0
                            onActivated: function(index) {
                                if (modelModel.count > 0) Agent.setModel(modelModel.get(index).id)
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
                                placeholderText: "输入消息... (Enter 发送, Shift+Enter 换行)"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                                enabled: Agent && !Agent.busy
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
                            icon.name: Agent && Agent.busy ? "ic_fluent_stop_20_regular" : "ic_fluent_send_20_regular"
                            Layout.preferredWidth: 36; Layout.preferredHeight: 36
                            highlighted: true
                            enabled: {
                                if (!Agent) return false
                                if (Agent.busy) return true
                                return inputField.text.trim().length > 0
                            }
                            onClicked: {
                                if (Agent.busy) { Agent.cancelAgent(); return }
                                var text = inputField.text.trim()
                                if (text.length === 0) return
                                messageModel.append({role: "user", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
                                Agent.sendMessage(text)
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
            Text { text: "AI 想要执行写入操作："; font.pixelSize: 13; font.bold: true; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: permTxt.implicitHeight + 12; radius: 6
                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#FFF3CD"
                border.color: Theme.currentTheme.colors.controlBorderColor; border.width: 1
                Text { id: permTxt; anchors.fill: parent; anchors.margins: 6; text: permDlg.pName + "\n" + permDlg.pDesc; font.pixelSize: 12; font.family: "Consolas, monospace"; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap }
            }
            // AI 理由
            ColumnLayout {
                visible: permDlg.pReason.length > 0
                spacing: 4
                Text { text: "AI 的理由："; font.pixelSize: 11; font.bold: true; color: Theme.currentTheme.colors.textSecondaryColor }
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
                Button { text: "拒绝"; flat: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Agent) Agent.denyPermission() } }
                Button { text: "允许"; highlighted: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Agent) Agent.approvePermission() } }
            }
        }
    }

    // AI 提问对话框
    Dialog {
        id: askDlg
        title: "AI 提问"; modal: true; width: 400; closePolicy: Popup.NoAutoClose
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
            // 清除所有选项选择
            for (var k in selectedOptions)
                selectedOptions[k] = false
            showCustomInput = true
            var tmp = selectedOptions
            selectedOptions = {}
            selectedOptions = tmp
        }

        contentItem: ColumnLayout {
            spacing: 10

            // 问题文本
            Text { text: askDlg.qText; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }

            // 单项选择
            ColumnLayout {
                visible: askDlg.qType === "single_choice"
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: askDlg.qOptions
                    delegate: Rectangle {
                        Component.onCompleted: console.log("[AgentTab] single_choice delegate: " + modelData)
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
                            Text {
                                text: modelData; font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                            }
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
                        Text {
                            text: "✏ 我想给出我的答案"
                            font.pixelSize: 13
                            font.italic: true
                            color: Theme.currentTheme.colors.textColor
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: askDlg.selectCustomInput()
                    }
                }
                // 自定义输入框
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
                        Component.onCompleted: console.log("[AgentTab] multiple_choice delegate: " + modelData)
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
                            Text {
                                text: modelData; font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                            }
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
                        Text {
                            text: "✏ 我想给出我的答案"
                            font.pixelSize: 13
                            font.italic: true
                            color: Theme.currentTheme.colors.textColor
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: askDlg.selectCustomInput()
                    }
                }
                // 自定义输入框
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

            // 按钮行
            RowLayout { Layout.fillWidth: true; spacing: 8
                Button { text: "取消"; flat: true; Layout.fillWidth: true; onClicked: { askDlg.close(); if (Agent) Agent.answerQuestion("用户取消") } }
                Button {
                    text: askDlg.qType === "text" ? "发送" : "确认"; highlighted: true; Layout.fillWidth: true
                    onClicked: {
                        var answer = askDlg.collectAnswer()
                        askDlg.close()
                        if (Agent) Agent.answerQuestion(answer)
                    }
                }
            }
        }
    }

    // ============================================================
    // Agent 信号
    // ============================================================
    Connections {
        target: Agent; enabled: Agent !== null

        function onTextUpdated(text) {
            var lastIdx = messageModel.count - 1
            if (lastIdx >= 0 && messageModel.get(lastIdx).role === "assistant" && messageModel.get(lastIdx).streaming) {
                messageModel.set(lastIdx, {role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true})
            } else {
                messageModel.append({role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true, expanded: false})
            }
        }

        function onToolCallStarted(toolName, argsJson) {
            console.log("[AgentTab] onToolCallStarted: " + toolName)
            // 找到最后一个 tool_call 之后的位置（连续的 tool_calls 应该在一起）
            var insertIdx = messageModel.count
            for (var i = messageModel.count - 1; i >= 0; i--) {
                var item = messageModel.get(i)
                if (item.role === "tool_call") {
                    insertIdx = i + 1
                    break
                }
                if (item.role === "assistant") {
                    // 在 assistant 之后插入（tool calls 紧跟在 text 之后）
                    insertIdx = i + 1
                    break
                }
            }
            messageModel.insert(insertIdx, {role: "tool_call", content: "", toolName: toolName, toolArgs: argsJson, toolResult: "", streaming: false, expanded: false})
        }

        function onToolCallFinished(toolName, argsJson, result) {
            // 更新最后一条 tool_call 的结果，而非新增条目
            for (var i = messageModel.count - 1; i >= 0; i--) {
                var item = messageModel.get(i)
                if (item.role === "tool_call" && item.toolName === toolName && item.toolResult === "") {
                    messageModel.set(i, {toolResult: result})
                    return
                }
            }
            // 兜底：如果没有找到匹配的 tool_call，追加一条
            messageModel.append({role: "tool_call", content: "", toolName: toolName, toolArgs: argsJson, toolResult: result, streaming: false, expanded: false})
        }

        function onErrorOccurred(msg) {
            messageModel.append({role: "error", content: msg, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }

        function onMessageAdded(role, content, toolCallsJson) {
            // 找到流式 assistant 消息并终结
            for (var i = messageModel.count - 1; i >= 0; i--) {
                if (messageModel.get(i).role === "assistant" && messageModel.get(i).streaming) {
                    messageModel.set(i, {role: "assistant", content: content, streaming: false})
                    return
                }
            }
            // 没有流式消息（历史恢复场景），直接追加
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
            console.log("[AgentTab] onQuestionAsked: type=" + questionType + ", optionsJson=" + optionsJson)
            askDlg.qText = question
            askDlg.qType = questionType || "text"
            askDlg.showCustomInput = false
            // 解析 JSON 字符串为数组
            try {
                askDlg.qOptions = JSON.parse(optionsJson || "[]")
            } catch(e) {
                console.log("[AgentTab] options JSON 解析失败: " + e)
                askDlg.qOptions = []
            }
            console.log("[AgentTab] askDlg.qType=" + askDlg.qType + ", askDlg.qOptions.length=" + askDlg.qOptions.length)
            // 在打开前初始化选择状态
            askDlg.selectedOptions = {}
            if (askDlg.qType === "single_choice" || askDlg.qType === "multiple_choice") {
                for (var i = 0; i < askDlg.qOptions.length; i++)
                    askDlg.selectedOptions[askDlg.qOptions[i]] = false
            }
            console.log("[AgentTab] selectedOptions=" + JSON.stringify(askDlg.selectedOptions))
            console.log("[AgentTab] 打开对话框: qType=" + askDlg.qType + ", qOptions.length=" + askDlg.qOptions.length + ", options=" + JSON.stringify(askDlg.qOptions))
            askDlg.open()
        }

        function onSessionLoaded() {
            rebuildMessageModelFromHistory()
            conversationTitle = Agent ? (Agent.title || "") : ""
            syncRoleCombo()
        }

        function onRoleChanged() {
            syncRoleCombo()
        }

        function onTitleChanged(title) {
            conversationTitle = title
        }

        function onStatusMessage(msg) {
            messageModel.append({role: "system", content: msg, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }
    }
}
