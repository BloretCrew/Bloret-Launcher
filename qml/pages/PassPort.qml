import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: passportPage
    title: qsTr("通行证")

    // --- Bloret PassPort Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("Bloret PassPort")
        Layout.topMargin: 10
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Label {
                id: bloretUserName
                font.weight: Font.DemiBold
                text: Backend.getBloretPassPortUserName()
                Layout.fillWidth: true
            }

            Button {
                text: qsTr("登录至 Bloret PassPort")
                onClicked: Backend.loginBloretPassPort()
            }

            Button {
                text: qsTr("退出登录")
                onClicked: Backend.logoutBloretPassPort()
            }
        }
    }

    Label {
        text: qsTr("使用 Bloret 通行证，可享受几乎所有的 Bloret 服务。")
        color: "#7f7f7f"
    }

    // --- Minecraft Account Section ---
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 10
        
        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: qsTr("Minecraft 账户")
            Layout.fillWidth: true
        }
        
        Button {
            text: qsTr("刷新")
            onClicked: Backend.refreshMinecraftAccounts()
        }
    }

    // Minecraft Accounts List Placeholder
    ListView {
        id: accountsListView
        Layout.fillWidth: true
        // dynamically adjust height based on model count if needed, or set minimum height
        Layout.minimumHeight: 100
        implicitHeight: contentHeight
        interactive: false
        
        model: Backend.getMinecraftAccounts()
        spacing: 10
        
        delegate: Frame {
            width: ListView.view.width
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.controlColorDefault
                radius: 8
                border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
            }
            RowLayout {
                width: parent.width
                spacing: 15
                Rectangle {
                    width: 40; height: 40
                    color: "#dddddd"
                    radius: 4
                    Label { text: "Face"; anchors.centerIn: parent }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: modelData.name }
                    Label { text: modelData.type; color: "#7f7f7f" }
                }
                Button {
                    text: qsTr("设为默认")
                    enabled: !modelData.isDefault
                    onClicked: Backend.setDefaultMinecraftAccount(modelData.id)
                }
            }
        }
    }

    // --- Cloud Management Section ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("通过 Bloret PassPort 管理你的账户")
                }
                Label {
                    text: qsTr("轻松登录你的 Minecraft Account，便捷地进行操作。")
                    color: "#7f7f7f"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 15

                Button {
                    text: qsTr("在 Bloret PassPort 上管理你的账户")
                    onClicked: Backend.manageAccountOnWebsite()
                }

                Button {
                    text: qsTr("从 Bloret PassPort 上同步账户")
                    onClicked: Backend.syncAccountFromPassPort()
                }
                
                Item { Layout.fillWidth: true }
            }
        }
    }
}
