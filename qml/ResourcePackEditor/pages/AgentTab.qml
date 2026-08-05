import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1 as Platform
import RinUI
import "../../components"

Item {
    id: agentPage

    // 消息模型
    ListModel { id: messageModel }
    ListModel { id: providerModel }
    ListModel { id: modelModel }
    ListModel { id: roleModel }
    ListModel { id: historyListModel }
    ListModel { id: pendingImagesModel }

    property bool historyPanelOpen: false
    property string conversationTitle: ""
    property string currentModelLabel: (Backend ? Backend.tr("选择模型") : "选择模型")
    property string voiceState: "idle"
    property int maxPendingImages: 4

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
            var selected = false
            if (Backend) {
                var globalModel = Backend.getGlobalAIModel()
                for (var j = 0; j < modelModel.count; j++) {
                    if (modelModel.get(j).id === globalModel) {
                        if (modelCombo) modelCombo.currentIndex = j
                        selected = true
                        break
                    }
                }
            }
            if (!selected && modelModel.count > 0) {
                if (modelCombo) modelCombo.currentIndex = 0
            }
            updateCurrentModelLabel()
        } catch(e) {}
    }

    function updateCurrentModelLabel() {
        if (modelModel.count > 0 && modelCombo && modelCombo.currentIndex >= 0 && modelCombo.currentIndex < modelModel.count) {
            currentModelLabel = modelModel.get(modelCombo.currentIndex).name || modelModel.get(modelCombo.currentIndex).id || (Backend ? Backend.tr("选择模型") : "选择模型")
            return
        }
        if (Agent && typeof Agent.getCurrentModelName === "function") {
            var n = Agent.getCurrentModelName()
            if (n && n.length > 0) { currentModelLabel = n; return }
        }
        currentModelLabel = Backend ? Backend.tr("选择模型") : "选择模型"
    }

    function pathFromFileUrl(url) {
        var s = (url || "").toString()
        if (s.indexOf("file://") === 0)
            s = decodeURIComponent(s.substring(Qt.platform.os === "windows" ? 8 : 7))
        return s
    }

    function fileUrlFromPath(path) {
        if (!path) return ""
        var s = path.toString()
        if (s.indexOf("file://") === 0) return s
        if (Qt.platform.os === "windows")
            return "file:///" + s.replace(/\\/g, "/")
        return "file://" + s
    }

    function pendingImagesJson() {
        var arr = []
        for (var i = 0; i < pendingImagesModel.count; i++)
            arr.push(pendingImagesModel.get(i).path)
        return JSON.stringify(arr)
    }

    function addPendingImage(path) {
        if (!path || path.length === 0) return
        if (pendingImagesModel.count >= maxPendingImages) return
        for (var i = 0; i < pendingImagesModel.count; i++) {
            if (pendingImagesModel.get(i).path === path) return
        }
        pendingImagesModel.append({ path: path, previewUrl: fileUrlFromPath(path) })
    }

    function clearPendingImages() { pendingImagesModel.clear() }

    function doSendMessage() {
        if (!Agent) return
        if (Agent.busy) { Agent.cancelAgent(); return }
        var text = inputField.text.trim()
        var imagesJson = pendingImagesJson()
        if (text.length === 0 && pendingImagesModel.count === 0) return
        messageModel.append({
            role: "user", content: text, imagesJson: imagesJson,
            toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false
        })
        Agent.sendMessage(text, imagesJson)
        inputField.text = ""
        clearPendingImages()
    }

    function appendTranscription(text) {
        if (!text || text.length === 0) return
        var cur = inputField.text || ""
        if (cur.length > 0 && !/\s$/.test(cur)) cur += " "
        inputField.text = cur + text
        inputField.cursorPosition = inputField.text.length
        inputField.forceActiveFocus()
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
                    subText: title.length > 0
                        ? dateStr + " · " + sessions[i].message_count + (Backend ? Backend.tr(" 条") : " 条")
                        : sessions[i].message_count + (Backend ? Backend.tr(" 条") : " 条")
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
                var imgs = msgs[i].imagesJson || "[]"
                if ((!imgs || imgs === "[]") && msgs[i].images && msgs[i].images.length)
                    imgs = JSON.stringify(msgs[i].images)
                messageModel.append({
                    role: msgs[i].role,
                    content: msgs[i].content,
                    imagesJson: imgs || "[]",
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
        updateCurrentModelLabel()
        if (Agent) {
            voiceState = Agent.voiceState || "idle"
            Agent.loadLatestSession()
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
                            text: (Backend ? Backend.tr("历史对话") : "历史对话")
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
                        text: (Backend ? Backend.tr("暂无历史记录") : "暂无历史记录")
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
                        text: (Backend ? Backend.tr("刷新列表") : "刷新列表")
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
                        Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                    }

                    Text {
                        text: (Backend ? Backend.tr("Blora Agent") : "Blora Agent")
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

                    RowLayout {
                        spacing: 6
                        visible: Agent && Agent.busy
                        ThinkingOrb {
                            size: 18
                            running: visible
                            state: "composing"
                            speed: 1.1
                            ink: Theme.accentColor || Theme.currentTheme.colors.primaryColor || "#0078D4"
                        }
                        Text {
                            text: Backend ? Backend.tr("正在思考") : "正在思考"
                            font.pixelSize: 11
                            color: Theme.accentColor || "#0078D4"
                        }
                    }
                    Text {
                        visible: !(Agent && Agent.busy)
                        text: Backend ? Backend.tr("就绪") : "就绪"
                        font.pixelSize: 11
                        color: Theme.currentTheme.colors.textSecondaryColor
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
                        text: (Backend ? Backend.tr("新对话") : "新对话")
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

                footer: Item {
                    width: msgView.width
                    height: agentThinkingFooter.visible ? agentThinkingFooter.height + 12 : 0
                    visible: Agent && Agent.busy

                    RowLayout {
                        id: agentThinkingFooter
                        anchors.left: parent.left
                        anchors.leftMargin: 16
                        anchors.right: parent.right
                        anchors.rightMargin: 16
                        anchors.top: parent.top
                        anchors.topMargin: 8
                        spacing: 10

                        Rectangle {
                            width: 22; height: 22; radius: 11; clip: true; color: "transparent"
                            Layout.alignment: Qt.AlignVCenter
                            Image {
                                anchors.fill: parent
                                source: Qt.resolvedUrl("../../../icon/Bloriko.jpg")
                                fillMode: Image.PreserveAspectCrop
                                mipmap: true
                            }
                        }
                        ThinkingOrb {
                            size: 22
                            running: agentThinkingFooter.visible
                            state: "composing"
                            speed: 1.15
                            ink: Theme.currentTheme.colors.textColor
                            Layout.alignment: Qt.AlignVCenter
                        }
                        Text {
                            text: Backend ? Backend.tr("正在思考") : "正在思考"
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.alignment: Qt.AlignVCenter
                        }
                        Row {
                            spacing: 3
                            Layout.alignment: Qt.AlignVCenter
                            Repeater {
                                model: 3
                                Rectangle {
                                    width: 4; height: 4; radius: 2
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                    opacity: 0.35
                                    SequentialAnimation on opacity {
                                        loops: Animation.Infinite
                                        running: agentThinkingFooter.visible
                                        PauseAnimation { duration: index * 160 }
                                        NumberAnimation { to: 1.0; duration: 320; easing.type: Easing.InOutQuad }
                                        NumberAnimation { to: 0.35; duration: 320; easing.type: Easing.InOutQuad }
                                        PauseAnimation { duration: (2 - index) * 160 }
                                    }
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Connections {
                        target: Agent
                        enabled: Agent !== null
                        function onBusyChanged() {
                            if (Agent && Agent.busy)
                                Qt.callLater(function() { msgView.positionViewAtEnd() })
                        }
                    }
                }

                // 空状态
                Item {
                    anchors.centerIn: parent
                    width: 280; height: emptyCol.implicitHeight
                    visible: messageModel.count === 0 && !(Agent && Agent.busy)

                    ColumnLayout {
                        id: emptyCol
                        width: parent.width; spacing: 10

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 56; height: 56; radius: 28; clip: true; color: "transparent"
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: (Backend ? Backend.tr("Blora Agent") : "Blora Agent")
                            font.pixelSize: 18; font.bold: true
                            color: Theme.currentTheme.colors.textColor
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.maximumWidth: 260
                            text: (Backend ? Backend.tr("用自然语言描述你想做的修改\nAI 会帮你操作资源包\n\n试试：\n• 帮我看看这个资源包\n• 读取 pack.mcmeta\n• 把描述改成 '我的资源包'") : "用自然语言描述你想做的修改\nAI 会帮你操作资源包\n\n试试：\n• 帮我看看这个资源包\n• 读取 pack.mcmeta\n• 把描述改成 '我的资源包'")
                            horizontalAlignment: Text.AlignHCenter
                            font.pixelSize: 11
                            lineHeightMode: Text.ProportionalHeight
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
                        width: Math.min(Math.max(
                            Math.max(userTxt.implicitWidth + 24, userImagesRow.visible ? 120 : 0),
                            50
                        ), parent.width * 0.65)
                        spacing: 6

                        Flow {
                            id: userImagesRow
                            width: parent.width
                            spacing: 4
                            visible: {
                                try {
                                    var arr = JSON.parse(imagesJson || "[]")
                                    return arr && arr.length > 0
                                } catch (e) { return false }
                            }
                            property var imageList: {
                                try { return JSON.parse(imagesJson || "[]") } catch (e) { return [] }
                            }
                            Repeater {
                                model: userImagesRow.imageList
                                delegate: Rectangle {
                                    width: 88; height: 88
                                    radius: 8
                                    color: "#00000022"
                                    clip: true
                                    Image {
                                        anchors.fill: parent
                                        source: {
                                            var p = modelData || ""
                                            if (!p) return ""
                                            if (p.indexOf("file://") === 0 || p.indexOf("data:") === 0) return p
                                            return agentPage.fileUrlFromPath(p)
                                        }
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                    }
                                }
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: (content && content.length > 0) ? (userTxt.contentHeight + 16) : 0
                            visible: content && content.length > 0
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
                            Image { anchors.fill: parent; source: Qt.resolvedUrl("../../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            visible: streaming && (!content || content.length === 0)
                            ThinkingOrb {
                                size: 20
                                running: visible
                                state: "composing"
                                speed: 1.1
                                ink: Theme.currentTheme.colors.textColor
                                Layout.alignment: Qt.AlignVCenter
                            }
                            Text {
                                text: Backend ? Backend.tr("正在思考") : "正在思考"
                                font.pixelSize: 13
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.alignment: Qt.AlignVCenter
                            }
                            Item { Layout.fillWidth: true }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: !(streaming && (!content || content.length === 0))
                            text: content || ""
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
                                                "read_file": (Backend ? Backend.tr("读取") : "读取"),
                                                "write_file": (Backend ? Backend.tr("写入") : "写入"),
                                                "edit_file": (Backend ? Backend.tr("编辑") : "编辑"),
                                                "list_files": (Backend ? Backend.tr("列出文件") : "列出文件"),
                                                "search_text": (Backend ? Backend.tr("搜索") : "搜索"),
                                                "get_pack_info": (Backend ? Backend.tr("获取资源包信息") : "获取资源包信息"),
                                                "analyze_pack": (Backend ? Backend.tr("分析资源包") : "分析资源包"),
                                                "read_language": (Backend ? Backend.tr("读取语言文件") : "读取语言文件"),
                                                "edit_language": (Backend ? Backend.tr("编辑语言文件") : "编辑语言文件"),
                                                "validate_json": (Backend ? Backend.tr("验证 JSON") : "验证 JSON"),
                                                "get_file_tree": (Backend ? Backend.tr("获取文件树") : "获取文件树"),
                                                "ask_user": (Backend ? Backend.tr("向用户提问") : "向用户提问"),
                                                "execute_command": (Backend ? Backend.tr("执行命令") : "执行命令"),
                                                "execute_command_background": (Backend ? Backend.tr("后台执行") : "后台执行"),
                                                "spawn_agent": (Backend ? Backend.tr("生成子 Agent") : "生成子 Agent")
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
                                            if (r.length > 500) r = r.substring(0, 500) + "\n" + (Backend ? Backend.tr("... (已截断)") : "... (已截断)")
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
                Layout.preferredHeight: (Agent && Agent.busy ? progressBar.height + 4 : 0) + inputCard.implicitHeight + 20
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

                // 一体输入卡片
                Rectangle {
                    id: inputCard
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 10
                    implicitHeight: inputCardCol.implicitHeight + 16
                    radius: 22
                    color: Theme.currentTheme.colors.controlColor || Theme.currentTheme.colors.cardColor || "#FFFFFF"
                    border.color: inputField.activeFocus
                        ? (Theme.accentColor || "#0078D4")
                        : (Theme.currentTheme.colors.controlBorderColor || "#E0E0E0")
                    border.width: 1

                    ColumnLayout {
                        id: inputCardCol
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            visible: pendingImagesModel.count > 0
                            Repeater {
                                model: pendingImagesModel
                                delegate: Item {
                                    width: 64; height: 64
                                    Rectangle {
                                        anchors.fill: parent
                                        radius: 10
                                        color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                                        clip: true
                                        Image {
                                            anchors.fill: parent
                                            source: model.previewUrl
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                        }
                                    }
                                    RoundButton {
                                        anchors.top: parent.top
                                        anchors.right: parent.right
                                        anchors.margins: -4
                                        width: 20; height: 20
                                        flat: true
                                        icon.name: "ic_fluent_dismiss_20_regular"
                                        onClicked: pendingImagesModel.remove(index)
                                    }
                                }
                            }
                        }

                        TextArea {
                            id: inputField
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(Math.max(implicitHeight, 28), 120)
                            placeholderText: (Backend ? Backend.tr("向 Blora Agent 说些什么...") : "向 Blora Agent 说些什么...")
                            wrapMode: TextArea.Wrap
                            font.pixelSize: 14
                            color: Theme.currentTheme.colors.textColor
                            enabled: Agent && !Agent.busy
                            background: Item {}
                            topPadding: 2; bottomPadding: 2; leftPadding: 4; rightPadding: 4
                            Keys.onPressed: function(event) {
                                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                    if (event.modifiers & Qt.ShiftModifier) {
                                        inputField.insert(inputField.cursorPosition, "\n")
                                    } else {
                                        doSendMessage(); event.accepted = true
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            RoundButton {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                flat: true
                                icon.name: "ic_fluent_add_20_regular"
                                enabled: Agent && !Agent.busy && pendingImagesModel.count < maxPendingImages
                                ToolTip.visible: hovered
                                ToolTip.text: Backend ? Backend.tr("添加图片") : "添加图片"
                                ToolTip.delay: 400
                                onClicked: imageFileDialog.open()
                            }

                            Rectangle {
                                Layout.preferredHeight: 32
                                Layout.preferredWidth: Math.min(modelPillRow.implicitWidth + 16, 180)
                                Layout.maximumWidth: 200
                                radius: 16
                                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                                border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                                border.width: 1
                                opacity: Agent && !Agent.busy ? 1.0 : 0.55
                                RowLayout {
                                    id: modelPillRow
                                    anchors.centerIn: parent
                                    anchors.leftMargin: 8; anchors.rightMargin: 8
                                    spacing: 4
                                    Icon { icon: "ic_fluent_lightbulb_20_regular"; size: 14; color: Theme.currentTheme.colors.textColor }
                                    Text {
                                        text: currentModelLabel
                                        font.pixelSize: 12
                                        color: Theme.currentTheme.colors.textColor
                                        elide: Text.ElideRight
                                        Layout.maximumWidth: 140
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    enabled: Agent && !Agent.busy
                                    onClicked: modelSelectDlg.open()
                                }
                            }

                            Item { Layout.fillWidth: true }

                            RoundButton {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                flat: true
                                highlighted: voiceState === "recording"
                                icon.name: voiceState === "recording"
                                    ? "ic_fluent_mic_record_20_filled"
                                    : (voiceState === "transcribing"
                                        ? "ic_fluent_spinner_ios_20_regular"
                                        : "ic_fluent_mic_20_regular")
                                enabled: Agent && !Agent.busy && voiceState !== "transcribing"
                                ToolTip.visible: hovered
                                ToolTip.text: voiceState === "recording"
                                    ? (Backend ? Backend.tr("录音中，再次点击结束") : "录音中，再次点击结束")
                                    : (Backend ? Backend.tr("语音输入") : "语音输入")
                                ToolTip.delay: 400
                                onClicked: {
                                    if (!Agent) return
                                    if (voiceState === "recording")
                                        Agent.stopVoiceCaptureAndTranscribe()
                                    else if (voiceState === "idle")
                                        Agent.startVoiceCapture()
                                }
                            }

                            RoundButton {
                                id: sendBtn
                                Layout.preferredWidth: 34
                                Layout.preferredHeight: 34
                                highlighted: true
                                icon.name: Agent && Agent.busy
                                    ? "ic_fluent_stop_20_regular"
                                    : "ic_fluent_arrow_up_20_filled"
                                enabled: {
                                    if (!Agent) return false
                                    if (Agent.busy) return true
                                    return inputField.text.trim().length > 0 || pendingImagesModel.count > 0
                                }
                                onClicked: doSendMessage()
                            }
                        }
                    }
                }

                Item {
                    width: 0; height: 0; visible: false
                    ComboBox {
                        id: providerCombo
                        model: providerModel; textRole: "name"
                        onActivated: function(index) {
                            var item = providerModel.get(index)
                            Agent.setProvider(item.key); loadModels()
                        }
                    }
                    ComboBox {
                        id: modelCombo
                        model: modelModel; textRole: "name"
                        onActivated: function(index) {
                            if (modelModel.count > 0) Agent.setModel(modelModel.get(index).id)
                            updateCurrentModelLabel()
                        }
                    }
                }
            }
        }
    }

    Platform.FileDialog {
        id: imageFileDialog
        title: Backend ? Backend.tr("选择图片") : "选择图片"
        fileMode: Platform.FileDialog.OpenFiles
        nameFilters: [
            Backend ? Backend.tr("图片 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)") : "图片 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)",
            Backend ? Backend.tr("所有文件 (*)") : "所有文件 (*)"
        ]
        onAccepted: {
            var files = imageFileDialog.files || []
            for (var i = 0; i < files.length; i++) {
                if (pendingImagesModel.count >= maxPendingImages) break
                addPendingImage(pathFromFileUrl(files[i]))
            }
            if (files.length === 0 && imageFileDialog.file)
                addPendingImage(pathFromFileUrl(imageFileDialog.file))
        }
    }

    Dialog {
        id: modelSelectDlg
        title: Backend ? Backend.tr("切换模型") : "切换模型"
        modal: true
        width: 360
        standardButtons: Dialog.NoButton
        onOpened: {
            loadProviders()
            providerComboDlg.currentIndex = providerCombo.currentIndex
            modelComboDlg.currentIndex = modelCombo.currentIndex
        }
        contentItem: ColumnLayout {
            spacing: 12
            Text {
                text: modelSelectDlg.title
                font.pixelSize: 16; font.bold: true
                color: Theme.currentTheme.colors.textColor
                Layout.fillWidth: true
            }
            Text {
                text: Backend ? Backend.tr("供应商") : "供应商"
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }
            ComboBox {
                id: providerComboDlg
                Layout.fillWidth: true
                model: providerModel; textRole: "name"
                onActivated: function(index) {
                    var item = providerModel.get(index)
                    Agent.setProvider(item.key)
                    providerCombo.currentIndex = index
                    loadModels()
                    modelComboDlg.currentIndex = modelCombo.currentIndex >= 0 ? modelCombo.currentIndex : 0
                }
            }
            Text {
                text: Backend ? Backend.tr("模型") : "模型"
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }
            ComboBox {
                id: modelComboDlg
                Layout.fillWidth: true
                model: modelModel; textRole: "name"
                onActivated: function(index) {
                    if (index < 0 || index >= modelModel.count) return
                    var m = modelModel.get(index)
                    Agent.setModel(m.id)
                    modelCombo.currentIndex = index
                    updateCurrentModelLabel()
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    text: Backend ? Backend.tr("取消") : "取消"
                    flat: true
                    Layout.fillWidth: true
                    onClicked: modelSelectDlg.close()
                }
                Button {
                    text: Backend ? Backend.tr("确定") : "确定"
                    highlighted: true
                    Layout.fillWidth: true
                    onClicked: {
                        // 先保存选中的模型 id，避免 loadModels clear 冲掉 ComboBox 索引
                        var selectedModelId = ""
                        var selectedModelIndex = modelComboDlg.currentIndex
                        if (selectedModelIndex >= 0 && selectedModelIndex < modelModel.count)
                            selectedModelId = modelModel.get(selectedModelIndex).id || ""

                        if (providerComboDlg.currentIndex >= 0 && providerComboDlg.currentIndex < providerModel.count) {
                            var p = providerModel.get(providerComboDlg.currentIndex)
                            Agent.setProvider(p.key)
                            providerCombo.currentIndex = providerComboDlg.currentIndex
                        }

                        if (selectedModelId.length > 0)
                            Agent.setModel(selectedModelId)

                        loadModels()
                        if (selectedModelId.length > 0) {
                            for (var i = 0; i < modelModel.count; i++) {
                                if (modelModel.get(i).id === selectedModelId) {
                                    modelCombo.currentIndex = i
                                    modelComboDlg.currentIndex = i
                                    break
                                }
                            }
                        }
                        updateCurrentModelLabel()
                        modelSelectDlg.close()
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
        title: (Backend ? Backend.tr("权限请求") : "权限请求"); modal: true; width: 400; closePolicy: Popup.NoAutoClose
        property string pName: ""; property string pDesc: ""; property string pReason: ""

        contentItem: ColumnLayout {
            spacing: 10
            Text { text: (Backend ? Backend.tr("AI 想要执行写入操作：") : "AI 想要执行写入操作："); font.pixelSize: 13; font.bold: true; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
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
                Text { text: (Backend ? Backend.tr("AI 的理由：") : "AI 的理由："); font.pixelSize: 11; font.bold: true; color: Theme.currentTheme.colors.textSecondaryColor }
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
                Button { text: (Backend ? Backend.tr("拒绝") : "拒绝"); flat: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Agent) Agent.denyPermission() } }
                Button { text: (Backend ? Backend.tr("允许") : "允许"); highlighted: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Agent) Agent.approvePermission() } }
            }
        }
    }

    // AI 提问对话框
    Dialog {
        id: askDlg
        title: (Backend ? Backend.tr("AI 提问") : "AI 提问"); modal: true; width: 400; closePolicy: Popup.NoAutoClose
        property string qText: ""
        property string qType: "text"
        property var qOptions: []
        property var selectedOptions: ({})
        property bool showCustomInput: false

        function collectAnswer() {
            if (qType === "single_choice") {
                if (showCustomInput) {
                    var ca = askCustomField.text.trim()
                    return ca.length > 0 ? ca : (Backend ? Backend.tr("用户未回答") : "用户未回答")
                }
                for (var key in selectedOptions) {
                    if (selectedOptions[key]) return key
                }
                return Backend ? Backend.tr("用户未选择") : "用户未选择"
            } else if (qType === "multiple_choice") {
                if (showCustomInput) {
                    var ca2 = askCustomField2.text.trim()
                    return ca2.length > 0 ? ca2 : (Backend ? Backend.tr("用户未回答") : "用户未回答")
                }
                var selected = []
                for (var k in selectedOptions) {
                    if (selectedOptions[k]) selected.push(k)
                }
                return selected.length > 0 ? selected.join(", ") : (Backend ? Backend.tr("用户未选择") : "用户未选择")
            } else {
                var a = askAnsField.text.trim()
                return a.length > 0 ? a : (Backend ? Backend.tr("用户未回答") : "用户未回答")
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
                            text: (Backend ? Backend.tr("✏ 我想给出我的答案") : "✏ 我想给出我的答案")
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
                    TextArea { id: askCustomField; anchors.fill: parent; anchors.margins: 6; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: TextArea.Wrap; placeholderText: (Backend ? Backend.tr("输入你的回答...") : "输入你的回答..."); background: Item {} }
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
                            text: (Backend ? Backend.tr("✏ 我想给出我的答案") : "✏ 我想给出我的答案")
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
                    TextArea { id: askCustomField2; anchors.fill: parent; anchors.margins: 6; font.pixelSize: 13; color: Theme.currentTheme.colors.textColor; wrapMode: TextArea.Wrap; placeholderText: (Backend ? Backend.tr("输入你的回答...") : "输入你的回答..."); background: Item {} }
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
                Button { text: (Backend ? Backend.tr("取消") : "取消"); flat: true; Layout.fillWidth: true; onClicked: { askDlg.close(); if (Agent) Agent.answerQuestion("用户取消") } }
                Button {
                    text: askDlg.qType === "text" ? (Backend ? Backend.tr("发送") : "发送") : (Backend ? Backend.tr("确认") : "确认"); highlighted: true; Layout.fillWidth: true
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

        function onVoiceStateChanged(state) {
            voiceState = state || "idle"
        }

        function onTranscriptionReady(text) {
            if (agentPage.visible)
                appendTranscription(text)
        }

        function onTranscriptionFailed(msg) {
            if (!agentPage.visible) return
            messageModel.append({
                role: "error",
                content: msg || (Backend ? Backend.tr("语音识别失败") : "语音识别失败"),
                imagesJson: "[]",
                toolName: "", toolArgs: "", toolResult: "",
                streaming: false, expanded: false
            })
        }

        function onBusyChanged() {
            if (Agent && Agent.busy)
                Qt.callLater(function() { msgView.positionViewAtEnd() })
        }

        function onTextUpdated(text) {
            var lastIdx = messageModel.count - 1
            if (lastIdx >= 0 && messageModel.get(lastIdx).role === "assistant" && messageModel.get(lastIdx).streaming) {
                messageModel.set(lastIdx, {role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true})
            } else {
                messageModel.append({role: "assistant", content: text, toolName: "", toolArgs: "", toolResult: "", streaming: true, expanded: false})
            }
            Qt.callLater(function() { msgView.positionViewAtEnd() })
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
            loadProviders()
            updateCurrentModelLabel()
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
