import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: livePage

    property var spaceList: []
    property bool inSpace: false
    property var currentSpace: ({})
    property var chatMessages: []
    property var onlineUsers: []
    property string connectionState: "disconnected"
    property bool audioEnabled: false
    property bool videoEnabled: false
    property bool isLoading: false
    property bool isAuthenticated: false
    property var easytierState: ({
        active: false,
        ready: false,
        hostAddress: "",
        localRunning: false,
        localMode: "",
        localVirtualIp: "",
        localProxyPort: null,
        localGamePort: null,
        localIsHost: false,
        localIsClient: false,
        localError: ""
    })
    property string liveErrorText: ""
    property string currentUserName: ""
    property bool easytierStartPending: false

    function t(text) {
        return Backend ? Backend.tr(text) : text
    }

    function normalizeUsers(users) {
        return Array.isArray(users) ? users : []
    }

    function normalizeChatHistory(history) {
        return Array.isArray(history) ? history : []
    }

    function restoreLiveStateFromBackend() {
        if (!Backend)
            return
        inSpace = Backend.isInLiveSpace()
        connectionState = Backend.getCurrentLiveConnectionState()
        easytierState = Backend.getCurrentLiveEasyTierState() || {}
        if (inSpace) {
            var liveSpace = Backend.getCurrentLiveSpace() || {}
            currentSpace = liveSpace
            chatMessages = normalizeChatHistory(liveSpace.chatHistory)
            onlineUsers = normalizeUsers(liveSpace.users)
            liveErrorText = ""
        } else {
            currentSpace = {}
            chatMessages = []
            onlineUsers = []
            easytierState = {}
        }
    }

    function upsertUser(user) {
        if (!user || !user.username)
            return
        var found = false
        var nextUsers = []
        for (var i = 0; i < onlineUsers.length; i++) {
            var existing = onlineUsers[i]
            if (existing.username === user.username) {
                nextUsers.push(user)
                found = true
            } else {
                nextUsers.push(existing)
            }
        }
        if (!found)
            nextUsers.push(user)
        onlineUsers = nextUsers
    }

    function removeUser(user) {
        if (!user || !user.username)
            return
        var filtered = []
        for (var i = 0; i < onlineUsers.length; i++) {
            if (onlineUsers[i].username !== user.username)
                filtered.push(onlineUsers[i])
        }
        onlineUsers = filtered
    }

    function resolveChatText(message) {
        if (message && message.payload) {
            if (message.payload.recalled)
                return t("此消息已撤回")
            if (message.payload.msg)
                return message.payload.msg
            if (message.payload.message)
                return message.payload.message
        }
        return (message && (message.message || message.msg)) || ""
    }

    function easytierSummaryText() {
        if (!easytierState.active)
            return t("房主尚未在这个 Live 中开启 EasyTier 网络")
        if (easytierState.ready) {
            if (currentSpace.isOwner)
                return t("房间地址已经同步到 Live，其他成员现在可以一键连接，并通过启动器启动 Minecraft。")
            if (easytierState.localIsClient)
                return t("你已连接到房主网络。请通过启动器启动 Minecraft，代理和服务器列表会自动配置。")
            return t("房主已经开放局域网。连接后通过启动器启动 Minecraft，即可在多人游戏中看到房间。")
        }
        if (currentSpace.isOwner && easytierState.localIsHost)
            return t("网络已启动。请通过启动器启动游戏，并在游戏内点击“对局域网开放”，端口会自动同步到 Live。")
        return t("房主已启动 EasyTier，正在等待游戏内开放局域网。")
    }

    Component.onCompleted: {
        console.log("[Live.qml] ========== Page loaded ==========")
        if (!Backend) {
            isLoading = false
            return
        }

        try {
            isAuthenticated = Backend.getBloretPassPortLoginStatus()
            currentUserName = Backend.getBloretPassPortUserName()
            restoreLiveStateFromBackend()
            if (isAuthenticated) {
                isLoading = true
                Backend.fetchLiveSpaceList()
            }
        } catch (e) {
            console.log("[Live.qml] ERROR during initialization:", e)
            isLoading = false
        }
    }

    onVisibleChanged: {
        if (visible && Backend) {
            isAuthenticated = Backend.getBloretPassPortLoginStatus()
            currentUserName = Backend.getBloretPassPortUserName()
            restoreLiveStateFromBackend()
        }
    }

    Component.onDestruction: {
        console.log("[Live.qml] Page destroyed")
    }

    Connections {
        target: Backend

        function onMinecraftAccountsChanged(accounts) {
            if (!Backend)
                return
            isAuthenticated = Backend.getBloretPassPortLoginStatus()
            currentUserName = Backend.getBloretPassPortUserName()
            restoreLiveStateFromBackend()
            if (isAuthenticated && spaceList.length === 0 && !isLoading) {
                isLoading = true
                Backend.fetchLiveSpaceList()
            } else if (!isAuthenticated && inSpace) {
                Backend.leaveLiveSpace()
            }
        }

        function onLiveSpaceListReceived(data) {
            spaceList = data || []
            isLoading = false
        }

        function onLiveJoinedSpace(data) {
            inSpace = true
            currentSpace = data || {}
            chatMessages = normalizeChatHistory(currentSpace.chatHistory)
            onlineUsers = normalizeUsers(currentSpace.users)
            easytierState = currentSpace.easytier || {}
            liveErrorText = ""
        }

        function onLiveLeftSpace() {
            inSpace = false
            currentSpace = {}
            chatMessages = []
            onlineUsers = []
            audioEnabled = false
            videoEnabled = false
            easytierState = {}
            liveErrorText = ""
            easytierStartPending = false
        }

        function onLiveUserEvent(data) {
            var type = data.type || ""
            if (type === "user-joined" && data.user)
                upsertUser(data.user)
            else if (type === "user-left" && data.user)
                removeUser(data.user)
        }

        function onLiveChatMessageReceived(data) {
            var msgs = chatMessages.slice()
            msgs.push(data)
            chatMessages = msgs
            Qt.callLater(function() {
                if (chatListView)
                    chatListView.positionViewAtEnd()
            })
        }

        function onLiveConnectionStateChanged(state) {
            connectionState = state
        }

        function onLiveErrorOccurred(msg) {
            isLoading = false
            liveErrorText = msg
            easytierStartPending = false
        }

        function onLiveEasyTierStateChanged(data) {
            easytierState = data || {}
            if (easytierStartPending && (easytierState.active || easytierState.localRunning))
                easytierStartPending = false
        }
    }

    Dialog {
        id: passwordDialog
        modal: true
        title: t("输入密码")
        width: 360
        implicitHeight: 280

        property string targetSpaceId: ""

        ColumnLayout {
            width: parent.width
            spacing: 12

            Label {
                text: t("该 Live 空间需要密码才能加入")
                color: Theme.currentTheme.colors.textSecondaryColor
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            TextField {
                id: passwordInput
                placeholderText: t("请输入密码")
                Layout.fillWidth: true
                echoMode: TextInput.Password
                onAccepted: joinWithPasswordBtn.clicked()
            }

            RowLayout {
                Layout.fillWidth: true

                Item { Layout.fillWidth: true }

                Button {
                    text: t("取消")
                    onClicked: passwordDialog.close()
                }

                Button {
                    id: joinWithPasswordBtn
                    text: t("加入")
                    highlighted: true
                    onClicked: {
                        if (passwordInput.text.trim() !== "") {
                            Backend.joinLiveSpace(passwordDialog.targetSpaceId, passwordInput.text)
                            passwordDialog.close()
                            passwordInput.text = ""
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: createSpaceDialog
        modal: true
        title: t("创建 Live 空间")
        width: 360
        implicitHeight: 280

        ColumnLayout {
            width: parent.width
            spacing: 12

            TextField {
                id: spaceNameInput
                placeholderText: t("空间名称")
                Layout.fillWidth: true
                onAccepted: createSpaceBtn.clicked()
            }

            RowLayout {
                Layout.fillWidth: true

                Item { Layout.fillWidth: true }

                Button {
                    text: t("取消")
                    onClicked: createSpaceDialog.close()
                }

                Button {
                    id: createSpaceBtn
                    text: t("创建")
                    highlighted: true
                    onClicked: {
                        if (spaceNameInput.text.trim() !== "") {
                            Backend.createLiveSpace(spaceNameInput.text)
                            createSpaceDialog.close()
                            spaceNameInput.text = ""
                        }
                    }
                }
            }
        }
    }

    content: ColumnLayout {
        spacing: 18

        PluginPanelHost {
            area: "live"
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Label {
                text: "Live"
                font.pixelSize: 32
                font.weight: Font.Bold
                color: Theme.currentTheme.colors.textColor
            }

            Label {
                text: t("实时空间")
                font.pixelSize: 14
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 5
            }

            Badge {
                text: "Bloret BBS"
                colorType: "Success"
            }

            Item { Layout.fillWidth: true }
        }

        Frame {
            Layout.fillWidth: true
            visible: !isAuthenticated
            padding: 20
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15
                Layout.alignment: Qt.AlignHCenter

                Label {
                    text: t("请先登录 Bloret PassPort")
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    Layout.alignment: Qt.AlignHCenter
                }

                Label {
                    text: t("登录后即可加入 Live 空间，进行实时聊天和联机。")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.alignment: Qt.AlignHCenter
                }

                Button {
                    text: t("前往登录")
                    highlighted: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: {
                        if (Backend)
                            Backend.loginBloretPassPort()
                    }
                }
            }
        }

        ProgressBar {
            Layout.fillWidth: true
            indeterminate: true
            visible: isLoading && isAuthenticated
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && !inSpace
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    text: t("刷新")
                    icon.name: "ic_fluent_arrow_sync_20_regular"
                    flat: true
                    onClicked: {
                        isLoading = true
                        Backend.fetchLiveSpaceList()
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: t("创建空间")
                    icon.name: "ic_fluent_add_20_regular"
                    highlighted: true
                    onClicked: createSpaceDialog.open()
                }
            }

            Label {
                visible: spaceList.length === 0 && !isLoading
                text: t("暂无 Live 空间")
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Repeater {
                model: spaceList

                Frame {
                    Layout.fillWidth: true
                    padding: 15
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.cardBorderColor
                    }

                    RowLayout {
                        width: parent.width
                        spacing: 15

                        Rectangle {
                            width: 44
                            height: 44
                            radius: 10
                            color: Theme.currentTheme.colors.controlColor

                            Label {
                                anchors.centerIn: parent
                                text: (modelData.name || "L").charAt(0).toUpperCase()
                                font.pixelSize: 20
                                font.weight: Font.Bold
                                color: Theme.currentTheme.colors.textColor
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            RowLayout {
                                spacing: 8

                                Label {
                                    text: modelData.name || ""
                                    font.pixelSize: 15
                                    font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                }

                                Rectangle {
                                    visible: modelData.hasPassword || false
                                    width: lockIcon.implicitWidth + 10
                                    height: 20
                                    radius: 4
                                    color: Theme.currentTheme.colors.systemCautionColor
                                    opacity: 0.3

                                    Label {
                                        id: lockIcon
                                        anchors.centerIn: parent
                                        text: t("锁")
                                        font.pixelSize: 11
                                    }
                                }
                            }

                            RowLayout {
                                spacing: 10

                                Label {
                                    text: t("创建者: ") + (modelData.owner || "")
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }

                                Label {
                                    text: t("在线: ") + String(modelData.userCount || 0)
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }
                        }

                        Button {
                            text: t("加入")
                            highlighted: true
                            onClicked: {
                                if (modelData.hasPassword) {
                                    passwordDialog.targetSpaceId = modelData.id || ""
                                    passwordDialog.open()
                                } else {
                                    Backend.joinLiveSpace(modelData.id || "", "")
                                }
                            }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && inSpace
            spacing: 12

            Frame {
                Layout.fillWidth: true
                padding: 12
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.cardBorderColor
                }

                RowLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: currentSpace.name || currentSpace.spaceName || "Live"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: {
                            if (connectionState === "connected")
                                return Theme.currentTheme.colors.systemSuccessColor
                            if (connectionState === "connecting")
                                return Theme.currentTheme.colors.systemCautionColor
                            return Theme.currentTheme.colors.textTertialyColor
                        }
                    }

                    Label {
                        text: {
                            if (connectionState === "connected")
                                return t("已连接")
                            if (connectionState === "connecting")
                                return t("连接中...")
                            return t("未连接")
                        }
                        font.pixelSize: 12
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        icon.name: audioEnabled ? "ic_fluent_mic_on_20_regular" : "ic_fluent_mic_off_20_regular"
                        flat: true
                        ToolTip.visible: hovered
                        ToolTip.text: audioEnabled ? t("关闭麦克风") : t("开启麦克风")
                        onClicked: {
                            audioEnabled = !audioEnabled
                            Backend.toggleLiveAudio(audioEnabled)
                        }
                    }

                    Button {
                        icon.name: videoEnabled ? "ic_fluent_video_20_regular" : "ic_fluent_video_off_20_regular"
                        flat: true
                        ToolTip.visible: hovered
                        ToolTip.text: videoEnabled ? t("关闭摄像头") : t("开启摄像头")
                        onClicked: {
                            videoEnabled = !videoEnabled
                            Backend.toggleLiveVideo(videoEnabled)
                        }
                    }

                    Button {
                        text: t("离开")
                        onClicked: Backend.leaveLiveSpace()
                    }
                }
            }

            Frame {
                Layout.fillWidth: true
                padding: 10
                visible: onlineUsers.length > 0
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.cardBorderColor
                }

                RowLayout {
                    width: parent.width
                    spacing: 8

                    Label {
                        text: t("在线: ")
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Repeater {
                        model: onlineUsers

                        Rectangle {
                            width: userNameLabel.implicitWidth + 16
                            height: 28
                            radius: 14
                            color: Theme.currentTheme.colors.controlColor

                            Label {
                                id: userNameLabel
                                anchors.centerIn: parent
                                text: modelData.username || modelData.name || "?"
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textColor
                            }
                        }
                    }
                }
            }

            Frame {
                Layout.fillWidth: true
                padding: 12
                visible: inSpace
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.cardBorderColor
                }

                ColumnLayout {
                    width: parent.width
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            text: "EasyTier"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        Badge {
                            text: {
                                if (!easytierState.active)
                                    return t("未启用")
                                if (easytierState.ready)
                                    return t("就绪")
                                if (easytierState.localRunning)
                                    return t("已连接")
                                return t("启动中")
                            }
                            colorType: {
                                if (!easytierState.active)
                                    return "Default"
                                if (easytierState.ready)
                                    return "Success"
                                return "Caution"
                            }
                        }

                        Item { Layout.fillWidth: true }

                        RowLayout {
                            spacing: 8

                            BusyIndicator {
                                visible: easytierStartPending
                                running: easytierStartPending
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                            }

                            Button {
                                visible: (currentSpace.isOwner === true) && (easytierState.localRunning !== true)
                                enabled: !easytierStartPending
                                text: t("开始网络")
                                highlighted: true
                                onClicked: {
                                    easytierStartPending = true
                                    Backend.startLiveEasyTier()
                                }
                            }
                        }

                        Button {
                            visible: (currentSpace.isOwner === true) && (easytierState.localRunning === true)
                            text: t("关闭网络")
                            onClicked: Backend.disconnectLiveEasyTier()
                        }

                        Button {
                            visible: (currentSpace.isOwner !== true) && (easytierState.active === true) && (easytierState.localRunning !== true)
                            text: t("连接房主网络")
                            highlighted: true
                            enabled: easytierState.ready === true
                            onClicked: Backend.connectLiveEasyTier()
                        }

                        Button {
                            visible: (currentSpace.isOwner !== true) && (easytierState.localRunning === true)
                            text: t("断开连接")
                            onClicked: Backend.disconnectLiveEasyTier()
                        }
                    }

                    // --- 操作提示（未启动网络时显示步骤引导）---
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !easytierState.active && !easytierState.localRunning
                        spacing: 6

                        Label {
                            text: currentSpace.isOwner
                                ? t("房主操作步骤：")
                                : t("加入者操作步骤：")
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        Label {
                            visible: currentSpace.isOwner
                            Layout.fillWidth: true
                            text: t("1. 点击「开始网络」启动 EasyTier\n2. 通过启动器启动 Minecraft 并进入存档\n3. 在游戏内点击「对局域网开放」\n4. 端口号会自动检测，如未检测到可手动输入")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }

                        Label {
                            visible: !currentSpace.isOwner
                            Layout.fillWidth: true
                            text: t("1. 等待房主启动 EasyTier 网络\n2. 网络就绪后点击「连接房主网络」\n3. 通过启动器启动 Minecraft\n4. 在多人游戏里使用下方房主地址直连")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: (currentSpace.isOwner !== true) && (easytierState.ready === true)
                        spacing: 8

                        Label {
                            text: t("房主地址:")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }

                        TextField {
                            Layout.fillWidth: true
                            readOnly: true
                            selectByMouse: true
                            text: easytierState.hostAddress || ""
                            placeholderText: t("等待房主开放局域网")
                        }
                    }

                    // --- 网络运行中的状态摘要 ---
                    Label {
                        Layout.fillWidth: true
                        visible: easytierState.active || easytierState.localRunning
                        text: easytierSummaryText()
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.Wrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: easytierState.localRunning
                        spacing: 16

                        Label {
                            visible: easytierState.localVirtualIp && easytierState.localVirtualIp !== ""
                            text: t("虚拟 IP: ") + easytierState.localVirtualIp
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }

                        Label {
                            visible: (typeof easytierState.localProxyPort === 'number' && easytierState.localProxyPort > 0) && (easytierState.localIsClient === true)
                            text: t("代理端口: ") + easytierState.localProxyPort
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }

                        Label {
                            visible: easytierState.hostAddress && easytierState.hostAddress !== ""
                            text: t("目标地址: ") + easytierState.hostAddress
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }

                        Label {
                            visible: (typeof easytierState.localGamePort === 'number' && easytierState.localGamePort > 0) && (easytierState.localIsHost === true)
                            text: t("局域网端口: ") + easytierState.localGamePort
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }

                    // --- 房主手动输入端口（网络运行中始终可用）---
                    RowLayout {
                        Layout.fillWidth: true
                        visible: (easytierState.localRunning === true) && (easytierState.localIsHost === true)
                        spacing: 8

                        Label {
                            text: typeof easytierState.localGamePort === 'number' && easytierState.localGamePort > 0
                                ? t("游戏端口（已自动检测，可手动修改）:")
                                : t("游戏端口（请输入局域网开放后显示的端口号）:")
                            font.pixelSize: 12
                            color: typeof easytierState.localGamePort === 'number' && easytierState.localGamePort > 0
                                ? Theme.currentTheme.colors.textTertialyColor
                                : Theme.currentTheme.colors.systemCautionColor
                        }

                        TextField {
                            id: gamePortInput
                            Layout.preferredWidth: 100
                            placeholderText: "25565"
                            inputMethodHints: Qt.ImhDigitsOnly
                            text: {
                                if (typeof easytierState.localGamePort === 'number' && easytierState.localGamePort > 0)
                                    return String(easytierState.localGamePort)
                                return "25565"
                            }
                        }

                        Button {
                            text: t("应用")
                            onClicked: {
                                var port = parseInt(gamePortInput.text)
                                if (port > 0 && port <= 65535) {
                                    Backend.setLiveGamePort(port)
                                } else {
                                    liveErrorText = t("端口号必须在 1 到 65535 之间")
                                }
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Label {
                            text: t("Minecraft 默认: 25565，局域网开放端口在游戏聊天中显示")
                            font.pixelSize: 11
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        visible: easytierState.localError !== ""
                        text: easytierState.localError || ""
                        font.pixelSize: 12
                        color: Theme.currentTheme.colors.systemCriticalColor
                        wrapMode: Text.Wrap
                    }
                }
            }

            Frame {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 300
                padding: 0
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.cardBorderColor
                }

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    ListView {
                        id: chatListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.margins: 10
                        clip: true
                        spacing: 8
                        model: chatMessages

                        delegate: RowLayout {
                            width: chatListView.width - 20
                            spacing: 8

                            Rectangle {
                                width: 28
                                height: 28
                                radius: 14
                                color: Theme.currentTheme.colors.controlColor

                                Label {
                                    anchors.centerIn: parent
                                    text: {
                                        var name = modelData.user || modelData.from || "?"
                                        return name.charAt(0).toUpperCase()
                                    }
                                    font.weight: Font.Bold
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textColor
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: modelData.user || modelData.from || ""
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                }

                                Label {
                                    text: resolveChatText(modelData)
                                    font.pixelSize: 13
                                    color: Theme.currentTheme.colors.textColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: chatMessages.length === 0
                            text: t("暂无消息，发送第一条吧")
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.currentTheme.colors.cardBorderColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.margins: 10
                        spacing: 10

                        TextField {
                            id: chatInput
                            placeholderText: t("输入消息...")
                            Layout.fillWidth: true
                            onAccepted: sendChatBtn.clicked()
                        }

                        Button {
                            id: sendChatBtn
                            icon.name: "ic_fluent_send_20_regular"
                            text: t("发送")
                            highlighted: true
                            onClicked: {
                                if (chatInput.text.trim() !== "" && Backend) {
                                    Backend.sendLiveChatMessage(chatInput.text)
                                    chatInput.text = ""
                                }
                            }
                        }
                    }
                }
            }
        }

        Item { height: 24 }
    }
}
