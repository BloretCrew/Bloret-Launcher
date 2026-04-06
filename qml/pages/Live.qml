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

    Component.onCompleted: {
        if (!Backend) return
        isAuthenticated = Backend.isBBBSAuthenticated()
        if (isAuthenticated) {
            isLoading = true
            Backend.fetchLiveSpaceList()
        }
    }

    Component.onDestruction: {
        if (inSpace && Backend) {
            Backend.leaveLiveSpace()
        }
    }

    Connections {
        target: Backend
        function onLiveSpaceListReceived(data) {
            spaceList = data
            isLoading = false
        }
        function onLiveJoinedSpace(data) {
            inSpace = true
            currentSpace = data
            chatMessages = []
            if (data.users) {
                onlineUsers = data.users
            }
        }
        function onLiveLeftSpace() {
            inSpace = false
            currentSpace = {}
            chatMessages = []
            onlineUsers = []
            audioEnabled = false
            videoEnabled = false
        }
        function onLiveUserEvent(data) {
            var type = data.type || ""
            if (type === "user-joined" && data.user) {
                var users = onlineUsers.slice()
                users.push(data.user)
                onlineUsers = users
            } else if (type === "user-left" && data.user) {
                var filtered = []
                for (var i = 0; i < onlineUsers.length; i++) {
                    if (onlineUsers[i].username !== data.user.username) {
                        filtered.push(onlineUsers[i])
                    }
                }
                onlineUsers = filtered
            }
        }
        function onLiveChatMessageReceived(data) {
            var msgs = chatMessages.slice()
            msgs.push(data)
            chatMessages = msgs
            chatListView.positionViewAtEnd()
        }
        function onLiveConnectionStateChanged(state) {
            connectionState = state
        }
        function onLiveErrorOccurred(msg) {
            isLoading = false
            console.log("[Live] Error:", msg)
        }
    }

    // 密码对话框
    Dialog {
        id: passwordDialog
        modal: true
        title: (Backend ? Backend.tr("输入密码") : "输入密码")
        width: 360

        property string targetSpaceId: ""

        ColumnLayout {
            width: parent.width
            spacing: 12

            Label {
                text: (Backend ? Backend.tr("该 Live 空间需要密码才能加入") : "该 Live 空间需要密码才能加入")
                color: Theme.currentTheme.colors.textSecondaryColor
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            TextField {
                id: passwordInput
                placeholderText: (Backend ? Backend.tr("请输入密码") : "请输入密码")
                Layout.fillWidth: true
                echoMode: TextInput.Password
                onAccepted: joinWithPasswordBtn.clicked()
            }

            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: (Backend ? Backend.tr("取消") : "取消")
                    onClicked: passwordDialog.close()
                }
                Button {
                    id: joinWithPasswordBtn
                    text: (Backend ? Backend.tr("加入") : "加入")
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

    // 创建空间对话框
    Dialog {
        id: createSpaceDialog
        modal: true
        title: (Backend ? Backend.tr("创建 Live 空间") : "创建 Live 空间")
        width: 360

        ColumnLayout {
            width: parent.width
            spacing: 12

            TextField {
                id: spaceNameInput
                placeholderText: (Backend ? Backend.tr("空间名称") : "空间名称")
                Layout.fillWidth: true
                onAccepted: createSpaceBtn.clicked()
            }

            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: (Backend ? Backend.tr("取消") : "取消")
                    onClicked: createSpaceDialog.close()
                }
                Button {
                    id: createSpaceBtn
                    text: (Backend ? Backend.tr("创建") : "创建")
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

        // 页面标题
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
                text: (Backend ? Backend.tr("实时空间") : "实时空间")
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

        // 未登录提示
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
                    text: (Backend ? Backend.tr("请先登录 Bloret PassPort") : "请先登录 Bloret PassPort")
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: (Backend ? Backend.tr("登录后即可加入 Live 空间进行实时聊天和共享") : "登录后即可加入 Live 空间进行实时聊天和共享")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.alignment: Qt.AlignHCenter
                }
                Button {
                    text: (Backend ? Backend.tr("前往登录") : "前往登录")
                    highlighted: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: {
                        if (Backend) Backend.loginBloretPassPort()
                    }
                }
            }
        }

        // 加载中
        ProgressBar {
            Layout.fillWidth: true
            indeterminate: true
            visible: isLoading && isAuthenticated
        }

        // ==================== 空间列表视图 ====================
        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && !inSpace
            spacing: 12

            // 操作栏
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    text: (Backend ? Backend.tr("刷新") : "刷新")
                    icon.name: "ic_fluent_arrow_sync_20_regular"
                    flat: true
                    onClicked: {
                        isLoading = true
                        Backend.fetchLiveSpaceList()
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: (Backend ? Backend.tr("创建空间") : "创建空间")
                    icon.name: "ic_fluent_add_20_regular"
                    highlighted: true
                    onClicked: createSpaceDialog.open()
                }
            }

            // 空间列表
            Label {
                visible: spaceList.length === 0 && !isLoading
                text: (Backend ? Backend.tr("暂无 Live 空间") : "暂无 Live 空间")
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

                        // 空间图标
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

                        // 空间信息
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
                                // 密码标识
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
                                        text: "🔒"
                                        font.pixelSize: 11
                                    }
                                }
                            }

                            RowLayout {
                                spacing: 10
                                Label {
                                    text: (Backend ? Backend.tr("创建者: ") : "创建者: ") + (modelData.owner || "")
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                                Label {
                                    text: (Backend ? Backend.tr("在线: ") : "在线: ") + String(modelData.userCount || 0)
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }
                        }

                        // 加入按钮
                        Button {
                            text: (Backend ? Backend.tr("加入") : "加入")
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

        // ==================== 活跃空间视图 ====================
        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && inSpace
            spacing: 12

            // 顶部栏
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

                    // 连接状态
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: {
                            if (connectionState === "connected") return Theme.currentTheme.colors.systemSuccessColor
                            if (connectionState === "connecting") return Theme.currentTheme.colors.systemCautionColor
                            return Theme.currentTheme.colors.textTertialyColor
                        }
                    }
                    Label {
                        text: {
                            if (connectionState === "connected") return (Backend ? Backend.tr("已连接") : "已连接")
                            if (connectionState === "connecting") return (Backend ? Backend.tr("连接中...") : "连接中...")
                            return (Backend ? Backend.tr("未连接") : "未连接")
                        }
                        font.pixelSize: 12
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Item { Layout.fillWidth: true }

                    // 媒体控制
                    Button {
                        icon.name: audioEnabled ? "ic_fluent_mic_on_20_regular" : "ic_fluent_mic_off_20_regular"
                        flat: true
                        ToolTip.visible: hovered
                        ToolTip.text: audioEnabled ? (Backend ? Backend.tr("关闭麦克风") : "关闭麦克风") : (Backend ? Backend.tr("开启麦克风") : "开启麦克风")
                        onClicked: {
                            audioEnabled = !audioEnabled
                            Backend.toggleLiveAudio(audioEnabled)
                        }
                    }
                    Button {
                        icon.name: videoEnabled ? "ic_fluent_video_20_regular" : "ic_fluent_video_off_20_regular"
                        flat: true
                        ToolTip.visible: hovered
                        ToolTip.text: videoEnabled ? (Backend ? Backend.tr("关闭摄像头") : "关闭摄像头") : (Backend ? Backend.tr("开启摄像头") : "开启摄像头")
                        onClicked: {
                            videoEnabled = !videoEnabled
                            Backend.toggleLiveVideo(videoEnabled)
                        }
                    }

                    Button {
                        text: (Backend ? Backend.tr("离开") : "离开")
                        onClicked: Backend.leaveLiveSpace()
                    }
                }
            }

            // 在线用户
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
                        text: (Backend ? Backend.tr("在线: ") : "在线: ")
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

            // 聊天区域
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

                    // 消息列表
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

                            // 用户头像
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

                            // 消息内容
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
                                    text: {
                                        if (modelData.payload && modelData.payload.message) {
                                            return modelData.payload.message
                                        }
                                        return modelData.message || ""
                                    }
                                    font.pixelSize: 13
                                    color: Theme.currentTheme.colors.textColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        // 空消息提示
                        Label {
                            anchors.centerIn: parent
                            visible: chatMessages.length === 0
                            text: (Backend ? Backend.tr("暂无消息，发送第一条吧") : "暂无消息，发送第一条吧")
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }

                    // 分隔线
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.currentTheme.colors.cardBorderColor
                    }

                    // 输入区域
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.margins: 10
                        spacing: 10

                        TextField {
                            id: chatInput
                            placeholderText: (Backend ? Backend.tr("输入消息...") : "输入消息...")
                            Layout.fillWidth: true
                            onAccepted: sendChatBtn.clicked()
                        }

                        Button {
                            id: sendChatBtn
                            icon.name: "ic_fluent_send_20_regular"
                            text: (Backend ? Backend.tr("发送") : "发送")
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

        // 底部留白
        Item { height: 24 }
    }
}
