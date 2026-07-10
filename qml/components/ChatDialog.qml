import QtQuick 2.15
import QtQuick.Controls 2.15
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
        // 无参 popup() 使用当前鼠标位置；position=-1 保留该坐标且不把高度从 0 动画展开
        msgContextMenu.popup()
    }

    // 使用 Item 包裹以避免 Dialog 默认 contentItem 的布局冲突
    Item {
        anchors.fill: parent

        // 共享右键菜单：放在 Dialog 内容树内、列表委托外，保证 MenuItem 进入 contentModel
        Menu {
            id: msgContextMenu
            // 与 TextInputMenu 一致：-1 表示上下文菜单，保留 popup() 光标坐标，高度不从 0 动画
            position: -1

            MenuItem {
                text: Backend ? Backend.tr("复制消息") : "复制消息"
                icon.name: "ic_fluent_copy_20_regular"
                onTriggered: {
                    console.log("[ChatDialog] 菜单: 复制消息")
                    chatDialog.copyToClipboard(chatDialog._ctxRawMessage)
                }
            }

            MenuItem {
                text: Backend ? Backend.tr("复制内容") : "复制内容"
                icon.name: "ic_fluent_clipboard_bullet_list_20_regular"
                visible: chatDialog._ctxUsername !== ""
                height: visible ? implicitHeight : 0
                onTriggered: {
                    console.log("[ChatDialog] 菜单: 复制内容")
                    chatDialog.copyToClipboard(chatDialog._ctxContent)
                }
            }

            MenuSeparator {
                visible: chatDialog._ctxUsername !== ""
            }

            MenuItem {
                text: Backend ? Backend.tr("复制用户名") : "复制用户名"
                icon.name: "ic_fluent_person_20_regular"
                visible: chatDialog._ctxUsername !== ""
                height: visible ? implicitHeight : 0
                onTriggered: {
                    console.log("[ChatDialog] 菜单: 复制用户名")
                    chatDialog.copyToClipboard(chatDialog._ctxUsername)
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
                                ? Theme.currentTheme.colors.subtleFillColorSecondary
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
