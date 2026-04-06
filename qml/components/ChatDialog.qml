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
        clipHelper.text = text
        clipHelper.selectAll()
        clipHelper.copy()
    }

    // 使用 Item 包裹以避免 Dialog 默认 contentItem 的布局冲突
    Item {
        anchors.fill: parent

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

                            property string msgUsername: chatDialog.parseUsername(modelData.message)
                            property string msgContent: chatDialog.parseContent(modelData.message)

                            MouseArea {
                                id: msgMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.RightButton

                                onClicked: function(mouse) {
                                    if (mouse.button === Qt.RightButton) {
                                        msgContextMenu.popup()
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
                                        visible: status === Image.Ready
                                        layer.enabled: true
                                        layer.effect: Item {
                                            // 圆形遮罩用 clip + radius 实现在外层 Rectangle
                                        }
                                    }

                                    // 加载中指示
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

                            // 右键菜单
                            Menu {
                                id: msgContextMenu

                                MenuItem {
                                    text: Backend ? Backend.tr("复制消息") : "复制消息"
                                    icon.name: "ic_fluent_copy_20_regular"
                                    onTriggered: {
                                        chatDialog.copyToClipboard(modelData.message)
                                    }
                                }

                                MenuItem {
                                    text: Backend ? Backend.tr("复制内容") : "复制内容"
                                    icon.name: "ic_fluent_clipboard_text_20_regular"
                                    onTriggered: {
                                        chatDialog.copyToClipboard(msgDelegate.msgContent)
                                    }
                                    visible: msgDelegate.msgUsername !== ""
                                }

                                MenuSeparator {}

                                MenuItem {
                                    text: Backend ? Backend.tr("复制用户名") : "复制用户名"
                                    icon.name: "ic_fluent_person_20_regular"
                                    onTriggered: {
                                        chatDialog.copyToClipboard(msgDelegate.msgUsername)
                                    }
                                    visible: msgDelegate.msgUsername !== ""
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
