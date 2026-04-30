import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: runningInstancesDialog
    title: Backend ? Backend.tr("正在运行") : "正在运行"
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    standardButtons: Dialog.Close
    width: 600

    property var instances: []
    property var recentRuns: []
    property var chatHistory: ({})

    function refresh() {
        instances = Backend ? Backend.getRunningInstances() : []
        recentRuns = Backend ? Backend.getRecentRuns() : []
    }

    function getSessionTime() {
        return Backend ? Backend.getSessionPlayTimeFormatted() : ""
    }

    onOpened: refresh()

    Component.onCompleted: {
        if (Backend) {
            var raw = Backend.loadChatHistory("all")
            try {
                chatHistory = JSON.parse(raw)
            } catch(e) {
                chatHistory = {}
            }
        }
    }

    Connections {
        target: Backend
        function onRunningInstancesChanged(list) { instances = list }
        function onMinecraftChatMessage(timestamp, message) {
            var msg = {timestamp: timestamp, message: message}
            var dirtyVersions = []
            for (var i = 0; i < instances.length; i++) {
                var verName = instances[i].name
                if (!chatHistory[verName]) chatHistory[verName] = []
                chatHistory[verName].push(msg)
                dirtyVersions.push(verName)
            }

            if (Backend) {
                for (var j = 0; j < dirtyVersions.length; j++) {
                    var v = dirtyVersions[j]
                    Backend.saveChatHistory(v, JSON.stringify(chatHistory[v]))
                }
            }

            if (chatDialog.visible) {
                chatDialog.addMessage(timestamp, message)
            }
        }
    }

    ColumnLayout {
        spacing: 8
        Layout.fillWidth: true

        // ========== 正在运行的实例 ==========
        Text {
            visible: instances.length > 0
            text: Backend ? Backend.tr("正在运行") : "正在运行"
            typography: Typography.Body
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }

        Repeater {
            model: instances

            delegate: Rectangle {
                Layout.fillWidth: true
                height: rowContent.implicitHeight + 16
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.cardBorderColor
                border.width: 1

                RowLayout {
                    id: rowContent
                    anchors {
                        left: parent.left
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        leftMargin: 12
                        rightMargin: 8
                    }
                    spacing: 8

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true

                        Text {
                            text: modelData.name
                            typography: Typography.Body
                            color: Theme.currentTheme.colors.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        RowLayout {
                            spacing: 8

                            Text {
                                text: modelData.type === "minecraft" ? "Minecraft" : (Backend ? Backend.tr("自定义程序") : "自定义程序")
                                typography: Typography.Caption
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Text {
                                id: sessionTimeLabel
                                text: ""
                                typography: Typography.Caption
                                color: Theme.currentTheme.colors.textTertialyColor
                                visible: text !== ""

                                Connections {
                                    target: Backend
                                    function onPlayTimeTick() {
                                        if (Backend)
                                            sessionTimeLabel.text = Backend.getSessionPlayTimeFormatted()
                                    }
                                }

                                Component.onCompleted: {
                                    if (Backend)
                                        sessionTimeLabel.text = Backend.getSessionPlayTimeFormatted()
                                }
                            }
                        }
                    }

                    Button {
                        visible: modelData.type === "minecraft"
                        text: Backend ? Backend.tr("聊天管理") : "聊天管理"
                        flat: true
                        onClicked: {
                            chatDialog.instanceId = modelData.id
                            chatDialog.mcVersion = modelData.name
                            chatDialog.chatMessages = chatHistory[modelData.name] || []
                            chatDialog.open()
                        }
                    }

                    Button {
                        text: modelData.suspended
                            ? (Backend ? Backend.tr("恢复") : "恢复")
                            : (Backend ? Backend.tr("挂起") : "挂起")
                        flat: true
                        onClicked: { if (Backend) Backend.suspendInstance(modelData.id) }
                    }

                    Button {
                        text: Backend ? Backend.tr("结束") : "结束"
                        highlighted: true
                        onClicked: { if (Backend) Backend.terminateInstance(modelData.id) }
                    }
                }
            }
        }

        // ========== 分隔线 ==========
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.currentTheme.colors.controlBorderColor
            visible: instances.length > 0 && recentRuns.length > 0
        }

        // ========== 最近运行 ==========
        Text {
            visible: recentRuns.length > 0 && instances.length === 0
            text: Backend ? Backend.tr("没有正在运行的实例，显示最近运行") : "没有正在运行的实例，显示最近运行"
            typography: Typography.Body
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.alignment: Qt.AlignHCenter
            topPadding: 8
            bottomPadding: 4
        }

        Text {
            visible: instances.length === 0 && recentRuns.length === 0
            text: Backend ? Backend.tr("暂无运行记录") : "暂无运行记录"
            typography: Typography.Body
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.alignment: Qt.AlignHCenter
            topPadding: 8
            bottomPadding: 8
        }

        Text {
            visible: recentRuns.length > 0
            text: Backend ? Backend.tr("最近运行") : "最近运行"
            typography: Typography.Caption
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textSecondaryColor
        }

        Repeater {
            model: recentRuns

            delegate: Rectangle {
                Layout.fillWidth: true
                height: recentRowContent.implicitHeight + 16
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.cardBorderColor
                border.width: 1

                RowLayout {
                    id: recentRowContent
                    anchors {
                        left: parent.left
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        leftMargin: 12
                        rightMargin: 8
                    }
                    spacing: 8

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true

                        Text {
                            text: modelData.name
                            typography: Typography.Body
                            color: Theme.currentTheme.colors.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: (modelData.type === "minecraft" ? "Minecraft" : (Backend ? Backend.tr("自定义程序") : "自定义程序"))
                                + "  ·  " + (modelData.lastRun || "")
                            typography: Typography.Caption
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }

                    Button {
                        visible: modelData.type === "minecraft"
                        text: Backend ? Backend.tr("聊天记录") : "聊天记录"
                        flat: true
                        onClicked: {
                            chatDialog.instanceId = ""
                            chatDialog.mcVersion = modelData.name
                            chatDialog.chatMessages = chatHistory[modelData.name] || []
                            chatDialog.open()
                        }
                    }

                    Button {
                        text: Backend ? Backend.tr("启动") : "启动"
                        highlighted: true
                        onClicked: {
                            if (Backend) Backend.launchGame(modelData.name)
                        }
                    }
                }
            }
        }
    }

    ChatDialog {
        id: chatDialog
    }
}
