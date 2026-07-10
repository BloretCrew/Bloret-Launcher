import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic as BasicControls
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: chatDialog
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    standardButtons: Dialog.Close
    width: 550
    height: 500

    property string instanceId: ""
    property string mcVersion: ""
    property var chatMessages: []
    property int maxMessages: 100

    // 根据用户名生成确定性颜色
    function usernameColor(name) {
        if (!name) return Theme.currentTheme.colors.textColor
        var hash = 0
        for (var i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash)
        }
        var hue = Math.abs(hash) % 360
        return Qt.hsla(hue / 360, 0.55, 0.55, 1.0)
    }

    // 从消息中解析用户名
    // 格式1: "<Detritalw> hello"     （本地/单人）
    // 格式2: "똂 Detritalw: hello"    （百络谷服务器等）
    // 格式3: "[+] Detritalw 加入了游戏"（系统消息，无用户名）
    function parseUsername(message) {
        // 格式1: <Username>
        var match = message.match(/^<([^>]+)>/)
        if (match) return match[1]
        // 格式2: 前缀字符 Username:
        match = message.match(/^[^a-zA-Z@]*([a-zA-Z@]\w*)\s*:/)
        if (match) return match[1]
        return ""
    }

    // 从消息中提取内容
    function parseContent(message) {
        // 格式1: <Username> content
        var match = message.match(/^<[^>]+>\s*/)
        if (match) return message.substring(match[0].length)
        // 格式2: 前缀 Username: content
        match = message.match(/^[^a-zA-Z@]*[a-zA-Z@]\w*\s*:\s*/)
        if (match) return message.substring(match[0].length)
        return message
    }

    function addMessage(timestamp, message) {
        // 必须 .slice() 创建新数组，否则 QML 检测不到引用变化，Repeater 不会更新
        var list = chatMessages.slice()
        list.push({ "timestamp": timestamp, "message": message })
        if (list.length > maxMessages) {
            list = list.slice(list.length - maxMessages)
        }
        chatMessages = list

        // 延迟滚动到底部
        Qt.callLater(function() {
            chatFlickable.contentY = chatFlickable.contentHeight - chatFlickable.height
        })
    }

    function clearChat() {
        chatMessages = []
    }

    // 隐藏的 TextEdit 用于复制到剪贴板
    TextEdit {
        id: clipHelper
        visible: false
    }

    function copyToClipboard(text) {
        console.log("[ChatDialog] copyToClipboard, length=", (text || "").length)
        clipHelper.text = text || ""
        clipHelper.selectAll()
        clipHelper.copy()
    }

    // 右键菜单上下文（菜单提到 Dialog 级，避免嵌在 Repeater 委托内导致 contentModel 为空）
    property string _ctxRawMessage: ""
    property string _ctxContent: ""
    property string _ctxUsername: ""

    function openMessageMenu(delegateItem, mouse) {
        if (!delegateItem) {
            console.warn("[ChatDialog] openMessageMenu: delegateItem is null")
            return
        }
        // modelData 仅在委托作用域内有效；委托上缓存 rawMessage
        _ctxRawMessage = delegateItem.rawMessage || ""
        _ctxUsername = delegateItem.msgUsername || ""
        _ctxContent = delegateItem.msgContent || ""
        console.log(
            "[ChatDialog] 打开消息右键菜单:",
            "username=", _ctxUsername,
            "rawLen=", _ctxRawMessage.length,
            "contentLen=", _ctxContent.length
        )
        // 不用 Qt Menu：Linux/KDE 会加载 org.kde.desktop/Menu.qml 并因 hasCheckables 报错导致空菜单
        // 使用 Basic.Popup 自定义菜单，相对消息行定位
        var pos = delegateItem.mapToItem(chatDialogContent, mouse.x, mouse.y)
        msgContextMenu.open()
        // 打开后再量尺寸并夹紧，避免 height 仍为 0 时定位错误
        Qt.callLater(function() {
            var w = msgContextMenu.width || 190
            var h = msgContextMenu.height || 120
            msgContextMenu.x = Math.max(0, Math.min(pos.x, chatDialogContent.width - w - 8))
            msgContextMenu.y = Math.max(0, Math.min(pos.y, chatDialogContent.height - h - 8))
            console.log("[ChatDialog] 自定义右键菜单已打开 at", msgContextMenu.x, msgContextMenu.y, "size", w, h)
        })
    }

    // 使用 Item 包裹以避免 Dialog 默认 contentItem 的布局冲突
    Item {
        id: chatDialogContent
        anchors.fill: parent

        // 自定义右键菜单：强制 Basic.Popup，彻底避开 org.kde.desktop/Menu.qml 的 hasCheckables 错误
        BasicControls.Popup {
            id: msgContextMenu
            modal: false
            focus: true
            padding: 6
            width: 190
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
            parent: chatDialogContent

            background: Rectangle {
                radius: 8
                color: (Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.backgroundAcrylicColor)
                    ? Theme.currentTheme.colors.backgroundAcrylicColor
                    : ((Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.cardColor)
                        ? Theme.currentTheme.colors.cardColor
                        : "#F9F9F9")
                border.color: (Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.controlBorderColor)
                    ? Theme.currentTheme.colors.controlBorderColor
                    : "#E0E0E0"
                border.width: 1
            }

            contentItem: Column {
                id: menuColumn
                spacing: 2
                width: msgContextMenu.availableWidth

                Rectangle {
                    width: parent.width
                    height: 34
                    radius: 6
                    color: copyMsgMouse.containsMouse
                        ? ((Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.subtleSecondaryColor)
                            ? Theme.currentTheme.colors.subtleSecondaryColor
                            : Qt.rgba(0, 0, 0, 0.06))
                        : "transparent"
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 12
                        spacing: 10
                        Text {
                            text: "📋"
                            font.pixelSize: 14
                            anchors.verticalCenter: parent.verticalCenter
                            width: 18
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Text {
                            text: Backend ? Backend.tr("复制消息") : "复制消息"
                            font.pixelSize: 13
                            color: (Theme.currentTheme && Theme.currentTheme.colors)
                                ? Theme.currentTheme.colors.textColor : "#000"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    MouseArea {
                        id: copyMsgMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            console.log("[ChatDialog] 菜单: 复制消息")
                            chatDialog.copyToClipboard(chatDialog._ctxRawMessage)
                            msgContextMenu.close()
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: chatDialog._ctxUsername !== "" ? 34 : 0
                    visible: chatDialog._ctxUsername !== ""
                    radius: 6
                    color: copyContentMouse.containsMouse
                        ? ((Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.subtleSecondaryColor)
                            ? Theme.currentTheme.colors.subtleSecondaryColor
                            : Qt.rgba(0, 0, 0, 0.06))
                        : "transparent"
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 12
                        spacing: 10
                        visible: parent.visible
                        Text {
                            text: "📄"
                            font.pixelSize: 14
                            anchors.verticalCenter: parent.verticalCenter
                            width: 18
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Text {
                            text: Backend ? Backend.tr("复制内容") : "复制内容"
                            font.pixelSize: 13
                            color: (Theme.currentTheme && Theme.currentTheme.colors)
                                ? Theme.currentTheme.colors.textColor : "#000"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    MouseArea {
                        id: copyContentMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: parent.visible
                        onClicked: {
                            console.log("[ChatDialog] 菜单: 复制内容")
                            chatDialog.copyToClipboard(chatDialog._ctxContent)
                            msgContextMenu.close()
                        }
                    }
                }

                Rectangle {
                    width: parent.width - 16
                    height: chatDialog._ctxUsername !== "" ? 1 : 0
                    visible: chatDialog._ctxUsername !== ""
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: (Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.controlBorderColor)
                        ? Theme.currentTheme.colors.controlBorderColor
                        : "#E0E0E0"
                }

                Rectangle {
                    width: parent.width
                    height: chatDialog._ctxUsername !== "" ? 34 : 0
                    visible: chatDialog._ctxUsername !== ""
                    radius: 6
                    color: copyUserMouse.containsMouse
                        ? ((Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.subtleSecondaryColor)
                            ? Theme.currentTheme.colors.subtleSecondaryColor
                            : Qt.rgba(0, 0, 0, 0.06))
                        : "transparent"
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 12
                        spacing: 10
                        visible: parent.visible
                        Text {
                            text: "👤"
                            font.pixelSize: 14
                            anchors.verticalCenter: parent.verticalCenter
                            width: 18
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Text {
                            text: Backend ? Backend.tr("复制用户名") : "复制用户名"
                            font.pixelSize: 13
                            color: (Theme.currentTheme && Theme.currentTheme.colors)
                                ? Theme.currentTheme.colors.textColor : "#000"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    MouseArea {
                        id: copyUserMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: parent.visible
                        onClicked: {
                            console.log("[ChatDialog] 菜单: 复制用户名")
                            chatDialog.copyToClipboard(chatDialog._ctxUsername)
                            msgContextMenu.close()
                        }
                    }
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            // 标题信息
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "\uD83D\uDCAC"
                        font.pixelSize: 18
                    }
                    Text {
                        text: (Backend ? Backend.tr("Minecraft %1 - 聊天").arg(chatDialog.mcVersion) : "Minecraft %1 - 聊天".arg(chatDialog.mcVersion))
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                        Layout.fillWidth: true
                    }
                }
                Text {
                    text: (Backend ? Backend.tr("实时跟踪游戏内聊天消息") : "实时跟踪游戏内聊天消息")
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.currentTheme.colors.controlBorderColor
            }

            Flickable {
                id: chatFlickable
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: chatColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    id: chatColumn
                    width: parent.width
                    spacing: 2

                    Repeater {
                        model: chatDialog.chatMessages
                        delegate: Rectangle {
                            id: msgDelegate
                            width: chatColumn.width
                            height: messageRow.implicitHeight + 12
                            color: msgMouseArea.containsMouse
                                ? ((Theme.currentTheme && Theme.currentTheme.colors && Theme.currentTheme.colors.subtleSecondaryColor)
                                    ? Theme.currentTheme.colors.subtleSecondaryColor
                                    : Qt.rgba(0, 0, 0, 0.06))
                                : (index % 2 === 0 ? "transparent" : Qt.rgba(0.5, 0.5, 0.5, 0.05))
                            radius: 4

                            property string rawMessage: modelData.message || ""
                            property string msgUsername: chatDialog.parseUsername(modelData.message)
                            property string msgContent: chatDialog.parseContent(modelData.message)

                            MouseArea {
                                id: msgMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                // 确保右键由本层处理，不与 Flickable 拖拽冲突
                                preventStealing: true

                                onClicked: function(mouse) {
                                    if (mouse.button === Qt.RightButton) {
                                        console.log("[ChatDialog] 右键消息 index=", index, "username=", msgDelegate.msgUsername)
                                        chatDialog.openMessageMenu(msgDelegate, mouse)
                                    }
                                }
                            }

                            RowLayout {
                                id: messageRow
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                anchors.topMargin: 6
                                anchors.bottomMargin: 6
                                spacing: 8

                                // 头像
                                Rectangle {
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    Layout.alignment: Qt.AlignTop
                                    radius: 14
                                    color: msgDelegate.msgUsername
                                        ? chatDialog.usernameColor(msgDelegate.msgUsername)
                                        : Theme.currentTheme.colors.controlQuaternaryColor
                                    clip: true

                                    // 文字回退（无用户名或头像加载失败时显示）
                                    Text {
                                        id: avatarFallback
                                        anchors.centerIn: parent
                                        text: msgDelegate.msgUsername
                                            ? msgDelegate.msgUsername[0].toUpperCase()
                                            : "\u2699"
                                        color: "white"
                                        font.pixelSize: msgDelegate.msgUsername ? 13 : 12
                                        font.bold: msgDelegate.msgUsername
                                        font.family: msgDelegate.msgUsername ? "Segoe UI" : "Segoe UI Emoji"
                                        visible: !msgDelegate.msgUsername || avatarImg.status !== Image.Ready
                                    }

                                    // Minecraft 真实头像（与通行证页面同一接口）
                                    Image {
                                        id: avatarImg
                                        anchors.fill: parent
                                        source: msgDelegate.msgUsername
                                            ? "https://visage.surgeplay.com/face/28/" + msgDelegate.msgUsername
                                            : ""
                                        fillMode: Image.PreserveAspectCrop
                                        smooth: true
                                        asynchronous: true
                                        cache: true
                                        visible: status === Image.Ready
                                    }

                                    BusyIndicator {
                                        anchors.centerIn: parent
                                        width: 16
                                        height: 16
                                        running: avatarImg.status === Image.Loading
                                        visible: running
                                    }
                                }

                                // 时间戳
                                Text {
                                    text: modelData.timestamp
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                    font.family: "Consolas, monospace"
                                    Layout.alignment: Qt.AlignTop
                                }

                                // 消息内容（用独立 Text 元素避免 RichText 中文乱码）
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Text {
                                        visible: msgDelegate.msgUsername !== ""
                                        text: msgDelegate.msgUsername
                                        font.pixelSize: 13
                                        font.bold: true
                                        color: chatDialog.usernameColor(msgDelegate.msgUsername)
                                    }

                                    Text {
                                        text: msgDelegate.msgContent || modelData.message
                                        font.pixelSize: 13
                                        color: Theme.currentTheme.colors.textColor
                                        wrapMode: Text.WrapAnywhere
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }

                    Text {
                        visible: chatDialog.chatMessages.length === 0
                        text: Backend ? Backend.tr("等待聊天消息...") : "等待聊天消息..."
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 50
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: Backend ? Backend.tr("共 %1 条消息").arg(chatDialog.chatMessages.length) : "共 %1 条消息".arg(chatDialog.chatMessages.length)
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: Backend ? Backend.tr("清空") : "清空"
                    flat: true
                    onClicked: chatDialog.clearChat()
                }
            }
        }
    }
}
