import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import QtQuick.Window 2.15
import Qt.labs.platform 1.1 as Platform
import RinUI
import "../components"

Item {
    id: blorikoPage

    // 消息模型
    ListModel { id: messageModel }
    ListModel { id: providerModel }
    ListModel { id: modelModel }
    ListModel { id: roleModel }
    ListModel { id: historyListModel }
    ListModel { id: pendingImagesModel }

    property bool historyPanelOpen: false
    property string conversationTitle: ""
    property string currentEmotion: "neutral"
    property string currentModelLabel: (Backend ? Backend.tr("选择模型") : "选择模型")
    property string voiceState: "idle"  // idle | recording | transcribing
    property int maxPendingImages: 4

    // 情感状态 → emoji 映射
    property var emotionMap: ({
        "neutral": (Backend ? Backend.tr("😌 平静") : "😌 平静"),
        "happy": (Backend ? Backend.tr("😊 开心") : "😊 开心"),
        "shy": (Backend ? Backend.tr("😳 害羞") : "😳 害羞"),
        "angry": (Backend ? Backend.tr("😤 生气") : "😤 生气"),
        "sad": (Backend ? Backend.tr("😢 难过") : "😢 难过"),
        "excited": (Backend ? Backend.tr("🤩 兴奋") : "🤩 兴奋"),
        "curious": (Backend ? Backend.tr("🤔 好奇") : "🤔 好奇")
    })

    function getEmotionDisplay(emotion) {
        return emotionMap[emotion] || (Backend ? Backend.tr("😌 平静") : "😌 平静")
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
        } catch(e) { console.error("[Bloriko] loadModels error:", e) }
    }

    function updateCurrentModelLabel() {
        if (modelModel.count > 0 && modelCombo && modelCombo.currentIndex >= 0 && modelCombo.currentIndex < modelModel.count) {
            currentModelLabel = modelModel.get(modelCombo.currentIndex).name || modelModel.get(modelCombo.currentIndex).id || (Backend ? Backend.tr("选择模型") : "选择模型")
            return
        }
        if (Bloriko && typeof Bloriko.getCurrentModelName === "function") {
            var n = Bloriko.getCurrentModelName()
            if (n && n.length > 0) {
                currentModelLabel = n
                return
            }
        }
        currentModelLabel = Backend ? Backend.tr("选择模型") : "选择模型"
    }

    function pathFromFileUrl(url) {
        var s = (url || "").toString()
        if (s.indexOf("file://") === 0) {
            s = decodeURIComponent(s.substring(Qt.platform.os === "windows" ? 8 : 7))
        }
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
        if (pendingImagesModel.count >= maxPendingImages) {
            console.warn("[Bloriko] 已达最大图片数", maxPendingImages)
            return
        }
        for (var i = 0; i < pendingImagesModel.count; i++) {
            if (pendingImagesModel.get(i).path === path)
                return
        }
        pendingImagesModel.append({ path: path, previewUrl: fileUrlFromPath(path) })
    }

    function clearPendingImages() {
        pendingImagesModel.clear()
    }

    function doSendMessage() {
        if (!Bloriko) return
        if (Bloriko.busy) {
            Bloriko.cancelAgent()
            return
        }
        var text = inputField.text.trim()
        var imagesJson = pendingImagesJson()
        var hasImages = pendingImagesModel.count > 0
        if (text.length === 0 && !hasImages)
            return
        messageModel.append({
            role: "user",
            content: text,
            imagesJson: imagesJson,
            toolName: "",
            toolArgs: "",
            toolResult: "",
            streaming: false,
            expanded: false
        })
        Bloriko.sendMessage(text, imagesJson)
        inputField.text = ""
        clearPendingImages()
    }

    function appendTranscription(text) {
        if (!text || text.length === 0) return
        var cur = inputField.text || ""
        if (cur.length > 0 && !/\s$/.test(cur))
            cur += " "
        inputField.text = cur + text
        inputField.cursorPosition = inputField.text.length
        inputField.forceActiveFocus()
    }

    function loadRoles() {
        roleModel.clear()
        if (!Bloriko) return
        try {
            var roles = JSON.parse(Bloriko.getAgentRoles())
            for (var i = 0; i < roles.length; i++)
                roleModel.append(roles[i])
            syncRoleCombo()
        } catch(e) { console.error("[Bloriko] loadRoles error:", e) }
    }

    function syncRoleCombo() {
        if (!Bloriko || roleModel.count === 0) {
            roleCombo.currentIndex = -1
            return
        }

        var currentRole = Bloriko.agentRole
        for (var j = 0; j < roleModel.count; j++) {
            if (roleModel.get(j).key === currentRole) {
                roleCombo.currentIndex = j
                return
            }
        }

        roleCombo.currentIndex = 0
        Bloriko.setAgentRole(roleModel.get(0).key)
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
                    subText: title.length > 0 ? dateStr + " · " + sessions[i].message_count + (Backend ? Backend.tr(" 条") : " 条") : sessions[i].message_count + (Backend ? Backend.tr(" 条") : " 条")
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

    // 消费首页跳转带来的待发送消息，并交给 Agent 处理
    function processPendingHomeMessage() {
        var win = Window.window
        if (!win) {
            console.log("[Bloriko] processPendingHomeMessage: 无主窗口")
            return
        }
        var text = (win.pendingBlorikoMessage || "").trim()
        var imagesJson = win.pendingBlorikoImagesJson || "[]"
        var hasImages = false
        try {
            var arr = JSON.parse(imagesJson)
            hasImages = arr && arr.length > 0
        } catch (e) { hasImages = false }
        if (text.length === 0 && !hasImages)
            return

        console.log("[Bloriko] 收到首页待处理消息:", text.substring(0, 80), "images=", imagesJson)
        win.pendingBlorikoMessage = ""
        win.pendingBlorikoImagesJson = "[]"

        if (!Bloriko) {
            console.error("[Bloriko] processPendingHomeMessage: Bloriko 后端不可用")
            return
        }
        if (Bloriko.busy) {
            console.warn("[Bloriko] Agent 正忙，延迟重试首页消息")
            win.pendingBlorikoMessage = text
            win.pendingBlorikoImagesJson = imagesJson
            pendingMessageRetryTimer.restart()
            return
        }

        messageModel.append({
            role: "user",
            content: text,
            imagesJson: imagesJson || "[]",
            toolName: "",
            toolArgs: "",
            toolResult: "",
            streaming: false,
            expanded: false
        })
        console.log("[Bloriko] 自动发送首页消息到 Agent")
        Bloriko.sendMessage(text, imagesJson || "[]")
    }

    Component.onCompleted: {
        console.log("[Bloriko] onCompleted, Bloriko:", Bloriko)
        loadProviders()
        loadRoles()
        updateCurrentModelLabel()
        if (Bloriko) {
            voiceState = Bloriko.voiceState || "idle"
            Bloriko.loadLatestSession()
        }
        // 延迟重试：防止上下文属性延迟加载导致数据为空
        retryTimer.start()
        // 页面首次加载后处理首页跳转消息（在会话加载之后）
        Qt.callLater(processPendingHomeMessage)
    }

    // 从首页导航进入时再尝试一次，避免首次挂载时 Window 尚未就绪
    onVisibleChanged: {
        if (visible) {
            console.log("[Bloriko] 页面可见，检查首页待处理消息")
            Qt.callLater(processPendingHomeMessage)
        }
    }

    // 监听主窗口 pendingBlorikoMessage（页面已缓存时仍可收到）
    Connections {
        target: Window.window
        enabled: Window.window !== null
        function onPendingBlorikoMessageChanged() {
            if (Window.window && (Window.window.pendingBlorikoMessage || "").trim().length > 0) {
                console.log("[Bloriko] pendingBlorikoMessage 变更，准备处理")
                Qt.callLater(processPendingHomeMessage)
            }
        }
    }

    Timer {
        id: pendingMessageRetryTimer
        interval: 400
        repeat: false
        onTriggered: processPendingHomeMessage()
    }

    Timer {
        id: retryTimer
        interval: 500
        repeat: false
        onTriggered: {
            if (providerModel.count === 0 || roleModel.count === 0) {
                console.log("[Bloriko] Retrying data load (providers:", providerModel.count, "roles:", roleModel.count, "Bloriko:", Bloriko, ")")
                if (providerModel.count === 0) loadProviders()
                if (roleModel.count === 0) loadRoles()
            }
        }
    }

    // ============================================================
    // 主布局：左侧历史栏 + 右侧聊天区
    // ============================================================
    // 顶部插件面板（络可页扩展）
    PluginPanelHost {
        id: blorikoPluginPanels
        area: "bloriko"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        z: 10
    }

    RowLayout {
        anchors.fill: parent
        anchors.topMargin: blorikoPluginPanels.visible ? blorikoPluginPanels.height + 8 : 0
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
                            width: parent ? parent.width : undefined
                            anchors.leftMargin: 12; anchors.rightMargin: 8

                            Text {
                                text: model.displayText
                                font.pixelSize: 12
                                font.bold: model.displayText !== model.subText
                                color: Theme.currentTheme.colors.textColor
                                Layout.fillWidth: true
                                Layout.maximumWidth: historyListView.width - 24
                                elide: Text.ElideRight
                                wrapMode: Text.NoWrap
                                maximumLineCount: 1
                            }

                            Text {
                                text: model.subText
                                font.pixelSize: 10
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.fillWidth: true
                                Layout.maximumWidth: historyListView.width - 24
                                elide: Text.ElideRight
                                wrapMode: Text.NoWrap
                                maximumLineCount: 1
                            }
                        }

                        onClicked: {
                            Bloriko.loadSession(model.filename)
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
                Layout.maximumHeight: 48
                color: "transparent"
                clip: true

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
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        font.pixelSize: 16
                        onClicked: {
                            historyPanelOpen = !historyPanelOpen
                            if (historyPanelOpen) loadHistoryList()
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        width: 24; height: 24; radius: 12; clip: true; color: "transparent"
                        Image { anchors.fill: parent; source: Qt.resolvedUrl("../../icon/Bloriko.jpg"); fillMode: Image.PreserveAspectCrop; mipmap: true }
                    }

                    Text {
                        text: (Backend ? Backend.tr("Blora Agent") : "Blora Agent")
                        font.pixelSize: 14
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                        Layout.alignment: Qt.AlignVCenter
                    }

                    // 对话标题：占满中间剩余空间，过长时右侧省略，避免顶栏被撑爆
                    Item {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredHeight: 24
                        Layout.alignment: Qt.AlignVCenter
                        clip: true

                        Text {
                            id: conversationTitleLabel
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: conversationTitle ? "— " + conversationTitle : ""
                            font.pixelSize: 12
                            font.italic: true
                            color: Theme.currentTheme.colors.textSecondaryColor
                            elide: Text.ElideRight
                            wrapMode: Text.NoWrap
                            maximumLineCount: 1
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                            ToolTip.visible: containsMouse && conversationTitle.length > 0
                            ToolTip.text: conversationTitle
                            ToolTip.delay: 400
                        }
                    }

                    // 情感状态显示
                    Rectangle {
                        Layout.preferredWidth: emotionText.implicitWidth + 12
                        Layout.maximumWidth: 120
                        Layout.preferredHeight: 22
                        Layout.alignment: Qt.AlignVCenter
                        radius: 11
                        color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                        border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                        border.width: 1
                        clip: true

                        Text {
                            id: emotionText
                            anchors.centerIn: parent
                            width: parent.width - 8
                            text: getEmotionDisplay(currentEmotion)
                            font.pixelSize: 10
                            color: Theme.currentTheme.colors.textColor
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    Text {
                        text: Bloriko && Bloriko.busy ? (Backend ? Backend.tr("思考中...") : "思考中...") : (Backend ? Backend.tr("就绪") : "就绪")
                        font.pixelSize: 11
                        color: Bloriko && Bloriko.busy ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.textSecondaryColor
                        Layout.alignment: Qt.AlignVCenter
                    }

                    ComboBox {
                        id: roleCombo
                        Layout.preferredWidth: 80
                        Layout.maximumWidth: 100
                        Layout.alignment: Qt.AlignVCenter
                        model: roleModel
                        textRole: "name"
                        font.pixelSize: 10
                        enabled: Bloriko && !Bloriko.busy && roleModel.count > 0
                        onActivated: function(index) {
                            if (index >= 0 && index < roleModel.count)
                                Bloriko.setAgentRole(roleModel.get(index).key)
                        }
                    }

                    Button {
                        text: (Backend ? Backend.tr("新对话") : "新对话")
                        flat: true
                        font.pixelSize: 11
                        Layout.alignment: Qt.AlignVCenter
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
                            text: (Backend ? Backend.tr("Blora Agent") : "Blora Agent")
                            font.pixelSize: 20; font.bold: true
                            color: Theme.currentTheme.colors.textColor
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.maximumWidth: 260
                            text: (Backend ? Backend.tr("哥哥好呀！ Blora Agent 在这里等你很久啦~(开心地挥挥小手)\n\n试试跟 Blora Agent 说：\n• 帮我创建一个文件\n• 搜索一下项目里的 TODO\n• 执行一个命令看看\n• 记住我的偏好是...") : "哥哥好呀！ Blora Agent 在这里等你很久啦~(开心地挥挥小手)\n\n试试跟 Blora Agent 说：\n• 帮我创建一个文件\n• 搜索一下项目里的 TODO\n• 执行一个命令看看\n• 记住我的偏好是...")
                            horizontalAlignment: Text.AlignHCenter
                            font.pixelSize: 11
                            lineHeightMode: Text.ProportionalHeight
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
                        width: Math.min(Math.max(
                            Math.max(userTxt.implicitWidth + 24, userImagesRow.visible ? 120 : 0),
                            50
                        ), parent.width * 0.65)
                        spacing: 6

                        // 图片附件预览
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
                                            return blorikoPage.fileUrlFromPath(p)
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
                                textFormat: TextEdit.PlainText
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
                                                "read_file": (Backend ? Backend.tr("读取") : "读取"),
                                                "write_file": (Backend ? Backend.tr("写入") : "写入"),
                                                "edit_file": (Backend ? Backend.tr("编辑") : "编辑"),
                                                "list_files": (Backend ? Backend.tr("列出文件") : "列出文件"),
                                                "search_text": (Backend ? Backend.tr("搜索") : "搜索"),
                                                "get_directory_tree": (Backend ? Backend.tr("查看目录树") : "查看目录树"),
                                                "ask_user": (Backend ? Backend.tr("向用户提问") : "向用户提问"),
                                                "execute_command": (Backend ? Backend.tr("执行命令") : "执行命令"),
                                                "execute_command_background": (Backend ? Backend.tr("后台执行") : "后台执行"),
                                                "spawn_agent": (Backend ? Backend.tr("生成子 Agent") : "生成子 Agent"),
                                                "memory": (Backend ? Backend.tr("管理记忆") : "管理记忆"),
                                                "set_emotion": (Backend ? Backend.tr("更新情感") : "更新情感")
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
                                            if (r.length > 500) r = r.substring(0, 500) + (Backend ? Backend.tr("\n... (已截断)") : "\n... (已截断)")
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

            // ===== 输入栏（图示一体圆角卡片） =====
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: (Bloriko && Bloriko.busy ? progressBar.height + 4 : 0) + inputCard.implicitHeight + 20
                color: Theme.currentTheme.colors.cardColor || "#FFFFFF"
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                ProgressBar {
                    id: progressBar
                    anchors.top: parent.top; anchors.topMargin: 1
                    width: parent.width
                    indeterminate: Bloriko && Bloriko.busy
                    visible: Bloriko && Bloriko.busy
                }

                // 一体输入卡片
                Rectangle {
                    id: inputCard
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 10
                    anchors.topMargin: Bloriko && Bloriko.busy ? progressBar.height + 8 : 10
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

                        // 待发送图片预览
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
                                        font.pixelSize: 10
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
                            enabled: Bloriko && !Bloriko.busy
                            background: Item {}
                            topPadding: 2
                            bottomPadding: 2
                            leftPadding: 4
                            rightPadding: 4

                            Keys.onPressed: function(event) {
                                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                    if (event.modifiers & Qt.ShiftModifier) {
                                        inputField.insert(inputField.cursorPosition, "\n")
                                    } else {
                                        doSendMessage()
                                        event.accepted = true
                                    }
                                }
                            }
                        }

                        // 底栏：+ | 模型胶囊 | spacer | mic | send
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            RoundButton {
                                id: addImageBtn
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                flat: true
                                icon.name: "ic_fluent_add_20_regular"
                                enabled: Bloriko && !Bloriko.busy && pendingImagesModel.count < maxPendingImages
                                ToolTip.visible: hovered
                                ToolTip.text: Backend ? Backend.tr("添加图片") : "添加图片"
                                ToolTip.delay: 400
                                onClicked: imageFileDialog.open()
                            }

                            // 模型胶囊（单击打开模型切换对话框）
                            Rectangle {
                                id: modelPill
                                Layout.preferredHeight: 32
                                Layout.preferredWidth: Math.min(modelPillRow.implicitWidth + 16, 180)
                                Layout.maximumWidth: 200
                                radius: 16
                                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F0F0F0"
                                border.color: Theme.currentTheme.colors.controlBorderColor || "#E0E0E0"
                                border.width: 1
                                opacity: Bloriko && !Bloriko.busy ? 1.0 : 0.55

                                RowLayout {
                                    id: modelPillRow
                                    anchors.centerIn: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    spacing: 4
                                    Icon {
                                        icon: "ic_fluent_lightbulb_20_regular"
                                        size: 14
                                        color: Theme.currentTheme.colors.textColor
                                    }
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
                                    enabled: Bloriko && !Bloriko.busy
                                    onClicked: modelSelectDlg.open()
                                }
                            }

                            Item { Layout.fillWidth: true }

                            RoundButton {
                                id: micBtn
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                flat: true
                                icon.name: voiceState === "recording"
                                    ? "ic_fluent_mic_record_20_filled"
                                    : (voiceState === "transcribing"
                                        ? "ic_fluent_spinner_ios_20_regular"
                                        : "ic_fluent_mic_20_regular")
                                highlighted: voiceState === "recording"
                                enabled: Bloriko && !Bloriko.busy && voiceState !== "transcribing"
                                ToolTip.visible: hovered
                                ToolTip.text: {
                                    if (voiceState === "recording")
                                        return Backend ? Backend.tr("录音中，再次点击结束") : "录音中，再次点击结束"
                                    if (voiceState === "transcribing")
                                        return Backend ? Backend.tr("识别中...") : "识别中..."
                                    return Backend ? Backend.tr("语音输入") : "语音输入"
                                }
                                ToolTip.delay: 400
                                onClicked: {
                                    if (!Bloriko) return
                                    if (voiceState === "recording")
                                        Bloriko.stopVoiceCaptureAndTranscribe()
                                    else if (voiceState === "idle")
                                        Bloriko.startVoiceCapture()
                                }
                            }

                            RoundButton {
                                id: sendBtn
                                Layout.preferredWidth: 34
                                Layout.preferredHeight: 34
                                highlighted: true
                                icon.name: Bloriko && Bloriko.busy
                                    ? "ic_fluent_stop_20_regular"
                                    : "ic_fluent_arrow_up_20_filled"
                                enabled: {
                                    if (!Bloriko) return false
                                    if (Bloriko.busy) return true
                                    return inputField.text.trim().length > 0 || pendingImagesModel.count > 0
                                }
                                ToolTip.visible: hovered
                                ToolTip.text: Bloriko && Bloriko.busy
                                    ? (Backend ? Backend.tr("停止") : "停止")
                                    : (Backend ? Backend.tr("发送") : "发送")
                                ToolTip.delay: 400
                                onClicked: doSendMessage()
                            }
                        }
                    }
                }

                // 隐藏的 modelCombo / providerCombo：保留 id 供 loadModels 使用
                Item {
                    width: 0; height: 0; visible: false
                    ComboBox {
                        id: providerCombo
                        model: providerModel
                        textRole: "name"
                        onActivated: function(index) {
                            var item = providerModel.get(index)
                            if (Backend) Backend.setGlobalAIProvider(item.key)
                            loadModels()
                        }
                    }
                    ComboBox {
                        id: modelCombo
                        model: modelModel
                        textRole: "name"
                        onActivated: function(index) {
                            if (modelModel.count > 0 && Backend)
                                Backend.setGlobalAIModel(modelModel.get(index).id)
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
                if (pendingImagesModel.count >= maxPendingImages)
                    break
                addPendingImage(pathFromFileUrl(files[i]))
            }
            // 部分平台也提供 file 单选
            if (files.length === 0 && imageFileDialog.file)
                addPendingImage(pathFromFileUrl(imageFileDialog.file))
        }
    }

    // 模型切换对话框
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
                font.pixelSize: 16
                font.bold: true
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
                model: providerModel
                textRole: "name"
                onActivated: function(index) {
                    var item = providerModel.get(index)
                    if (Backend) Backend.setGlobalAIProvider(item.key)
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
                model: modelModel
                textRole: "name"
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
                        if (providerComboDlg.currentIndex >= 0 && providerComboDlg.currentIndex < providerModel.count) {
                            var p = providerModel.get(providerComboDlg.currentIndex)
                            if (Backend) Backend.setGlobalAIProvider(p.key)
                            providerCombo.currentIndex = providerComboDlg.currentIndex
                        }
                        loadModels()
                        if (modelComboDlg.currentIndex >= 0 && modelComboDlg.currentIndex < modelModel.count) {
                            var m = modelModel.get(modelComboDlg.currentIndex)
                            if (Backend) Backend.setGlobalAIModel(m.id)
                            modelCombo.currentIndex = modelComboDlg.currentIndex
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
        implicitHeight: 380
        property string pName: ""; property string pDesc: ""; property string pReason: ""

        contentItem: ColumnLayout {
            spacing: 10
            Text { text: (Backend ? Backend.tr("Blora Agent 想要执行写入操作：") : "Blora Agent 想要执行写入操作："); font.pixelSize: 13; font.bold: true; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: permTxt.implicitHeight + 12; radius: 6
                color: Theme.currentTheme.colors.controlAltSecondaryColor || "#FFF3CD"
                border.color: Theme.currentTheme.colors.controlBorderColor; border.width: 1
                Text { id: permTxt; anchors.fill: parent; anchors.margins: 6; text: permDlg.pName + "\n" + permDlg.pDesc; font.pixelSize: 12; font.family: "Consolas, monospace"; color: Theme.currentTheme.colors.textColor; wrapMode: Text.Wrap }
            }
            ColumnLayout {
                visible: permDlg.pReason.length > 0
                spacing: 4
                Text { text: (Backend ? Backend.tr("Blora Agent 的理由：") : "Blora Agent 的理由："); font.pixelSize: 11; font.bold: true; color: Theme.currentTheme.colors.textSecondaryColor }
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
                Button { text: (Backend ? Backend.tr("拒绝") : "拒绝"); flat: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Bloriko) Bloriko.denyPermission() } }
                Button { text: (Backend ? Backend.tr("允许") : "允许"); highlighted: true; Layout.fillWidth: true; onClicked: { permDlg.close(); if (Bloriko) Bloriko.approvePermission() } }
            }
        }
    }

    // AI 提问对话框
    Dialog {
        id: askDlg
        title: (Backend ? Backend.tr("Blora Agent 提问") : "Blora Agent 提问"); modal: true; width: 400; closePolicy: Popup.NoAutoClose
        implicitHeight: 450
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
                return (Backend ? Backend.tr("用户未选择") : "用户未选择")
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
                        Text { text: (Backend ? Backend.tr("✏ 我想给出我的答案") : "✏ 我想给出我的答案"); font.pixelSize: 13; font.italic: true; color: Theme.currentTheme.colors.textColor }
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
                        Text { text: (Backend ? Backend.tr("✏ 我想给出我的答案") : "✏ 我想给出我的答案"); font.pixelSize: 13; font.italic: true; color: Theme.currentTheme.colors.textColor }
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

            RowLayout { Layout.fillWidth: true; spacing: 8
                Button { text: (Backend ? Backend.tr("取消") : "取消"); flat: true; Layout.fillWidth: true; onClicked: { askDlg.close(); if (Bloriko) Bloriko.answerQuestion((Backend ? Backend.tr("用户取消") : "用户取消")) } }
                Button {
                    text: askDlg.qType === "text" ? (Backend ? Backend.tr("发送") : "发送") : (Backend ? Backend.tr("确认") : "确认"); highlighted: true; Layout.fillWidth: true
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

        function onVoiceStateChanged(state) {
            voiceState = state || "idle"
        }

        function onTranscriptionReady(text) {
            // 仅当前页可见时写入，避免与首页输入条抢结果
            if (blorikoPage.visible)
                appendTranscription(text)
        }

        function onTranscriptionFailed(msg) {
            if (!blorikoPage.visible)
                return
            messageModel.append({
                role: "error",
                content: msg || (Backend ? Backend.tr("语音识别失败") : "语音识别失败"),
                imagesJson: "[]",
                toolName: "",
                toolArgs: "",
                toolResult: "",
                streaming: false,
                expanded: false
            })
        }

        function onStatusMessage(msg) {
            messageModel.append({role: "system", content: msg, toolName: "", toolArgs: "", toolResult: "", streaming: false, expanded: false})
        }

        function onEmotionChanged(emotion) {
            currentEmotion = emotion
        }
    }
}
