import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

// Minecraft 聊天管理器
Rectangle {
    id: chatManager
    width: 350
    height: 450
    color: Theme.currentTheme.colors.cardColor
    radius: 8
    border.color: Theme.currentTheme.colors.controlBorderColor
    border.width: 1

    // 聊天消息列表
    property var chatMessages: []
    property int maxMessages: 100  // 最多显示 100 条消息

    // 添加聊天消息
    function addMessage(timestamp, message) {
        chatMessages.push({
            "timestamp": timestamp,
            "message": message
        })
        
        // 限制消息数量
        if (chatMessages.length > maxMessages) {
            chatMessages = chatMessages.slice(chatMessages.length - maxMessages)
        }
        
        // 滚动到底部
        chatFlickable.contentY = chatFlickable.contentHeight - chatFlickable.height
    }

    // 清空聊天
    function clearChat() {
        chatMessages = []
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // 标题栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "\uD83D\uDCAC"
                font.pixelSize: 18
            }

            Label {
                text: Backend ? Backend.tr("Minecraft 聊天") : "Minecraft 聊天"
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Item { Layout.fillWidth: true }

            // 清空按钮
            Button {
                text: Backend ? Backend.tr("清空") : "清空"
                flat: true
                onClicked: chatManager.clearChat()
            }
        }

        // 分隔线
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.currentTheme.colors.controlBorderColor
        }

        // 聊天消息列表
        Flickable {
            id: chatFlickable
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: chatColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            ColumnLayout {
                id: chatColumn
                width: chatFlickable.width
                spacing: 4

                Repeater {
                    model: chatManager.chatMessages

                    delegate: Rectangle {
                        width: chatFlickable.width - 10
                        height: messageRow.implicitHeight + 8
                        color: index % 2 === 0 ? "transparent" : Qt.rgba(0.5, 0.5, 0.5, 0.05)
                        radius: 4

                        RowLayout {
                            id: messageRow
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8

                            // 时间戳
                            Label {
                                text: modelData.timestamp
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                                font.family: "Consolas, monospace"
                            }

                            // 消息内容
                            Label {
                                text: modelData.message
                                font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }
        }

        // 状态栏
        Label {
            text: Backend ? Backend.tr("共 %1 条消息").arg(chatManager.chatMessages.length) : "共 %1 条消息".arg(chatManager.chatMessages.length)
            font.pixelSize: 11
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.alignment: Qt.AlignRight
        }
    }
}
