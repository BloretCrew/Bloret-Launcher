import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt5Compat.GraphicalEffects
import RinUI

FluentPage {
    id: passportPage
    title: (Backend ? Backend.tr("通行证") : "通行证")

    property var accountList: []
    property string passportUser: ""

    Component.onCompleted: {
        // 延迟更新确保 Backend 完全初始化
        Qt.callLater(function() {
            updatePassportData()
        })
    }

    function updatePassportData() {
        if (Backend) {
            try {
                passportUser = Backend.getBloretPassPortUserName()
                accountList = Backend.getMinecraftAccounts()
            } catch(e) {
                console.log("Error updating passport data:", e)
            }
        }
    }

    Connections {
        target: Backend
        function onMinecraftAccountsChanged(accounts) {
            if (Backend) {
                try {
                    if (Array.isArray(accounts) && accounts.length > 0) {
                        accountList = accounts
                    } else {
                        accountList = Backend.getMinecraftAccounts()
                    }
                    passportUser = Backend.getBloretPassPortUserName()
                } catch(e) {
                    console.log("Error in onMinecraftAccountsChanged:", e)
                }
            }
        }
        function onSyncStatusChanged(status) {
            if (status && status.length > 0) {
                syncInfoBar.severity = status === "success" ? Severity.Success : Severity.Error
                syncInfoBar.title = status === "success" ? (Backend ? Backend.tr("同步成功") : "同步成功") : (Backend ? Backend.tr("同步失败") : "同步失败")
                syncInfoBar.text = status === "success" ? (Backend ? Backend.tr("已成功从云端同步账户") : "已成功从云端同步账户") : ((Backend ? Backend.tr("同步时出错: ") : "同步时出错: ") + String(status).substring(6))
                syncInfoBar.visible = true
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        InfoBar {
            id: syncInfoBar
            Layout.fillWidth: true
            visible: false
            timeout: 5000
        }

        // --- Bloret PassPort Section ---
        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("Bloret PassPort") : "Bloret PassPort")
            Layout.topMargin: 10
            color: Theme.currentTheme.colors.textColor
        }

        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                // 用户头像 - 圆角矩形
                Rectangle {
                    width: 48
                    height: 48
                    radius: 8
                    color: "transparent"
                    clip: true
                    
                    Image {
                        id: passportAvatar
                        anchors.fill: parent
                        layer.enabled: true
                        layer.effect: OpacityMask {
                            maskSource: Rectangle {
                                width: passportAvatar.width
                                height: passportAvatar.height
                                radius: 8
                            }
                        }
                        source: {
                            let url = Backend ? Backend.getPassPortAvatar() : ""
                            let finalUrl = url && url !== "" ? url : "../../icon/Grass_Block.png"
                            console.log("[PassPort.qml] Image source changed")
                            console.log("  Backend.getPassPortAvatar() returned:", url)
                            console.log("  Final Image source:", finalUrl)
                            return finalUrl
                        }
                        asynchronous: true
                        cache: false
                        fillMode: Image.PreserveAspectCrop
                        onStatusChanged: {
                            console.log("[PassPort.qml] Image status changed:", status, "source:", source)
                            if (status === Image.Loading) {
                                console.log("  正在加载图像...")
                            } else if (status === Image.Ready) {
                                console.log("  图像加载成功！")
                            } else if (status === Image.Error) {
                                console.log("  图像加载失败！使用默认头像")
                                source = "../../icon/Grass_Block.png"
                            }
                        }
                    }
                }

                Label {
                    id: bloretUserName
                    font.weight: Font.DemiBold
                    text: passportUser
                    Layout.fillWidth: true
                    color: Theme.currentTheme.colors.textColor
                }

                Button {
                    text: (Backend ? Backend.tr("登录") : "登录")
                    visible: passportUser === "未登录"
                    onClicked: { if (Backend) Backend.loginBloretPassPort() }
                }

                Button {
                    text: (Backend ? Backend.tr("退出登录") : "退出登录")
                    visible: passportUser !== "未登录"
                    onClicked: { if (Backend) Backend.logoutBloretPassPort() }
                }
            }
        }

        Label {
            text: (Backend ? Backend.tr("使用 Bloret 通行证，可享受几乎所有的 Bloret 服务。") : "使用 Bloret 通行证，可享受几乎所有的 Bloret 服务。")
            color: Theme.currentTheme.colors.textSecondaryColor
        }

        // --- Minecraft Account Section ---
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 10
            
            Label {
                font.pixelSize: 20
                font.weight: Font.DemiBold
                text: (Backend ? Backend.tr("Minecraft 账户") : "Minecraft 账户")
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }
            
            Button {
                text: (Backend ? Backend.tr("刷新") : "刷新")
                onClicked: { if (Backend) Backend.refreshMinecraftAccounts() }
            }
        }

        // Minecraft Accounts List
        ListView {
            id: accountsListView
            Layout.fillWidth: true
            Layout.minimumHeight: accountList.length > 0 ? contentHeight : 50
            implicitHeight: contentHeight
            interactive: false
            clip: true
            
            model: accountList
            spacing: 10
            
            delegate: Frame {
                width: ListView.view.width
                padding: 15
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: modelData.isDefault ? Theme.currentTheme.colors.primaryColor : Theme.currentTheme.colors.controlBorderColor
                    border.width: modelData.isDefault ? 2 : 1
                }
                RowLayout {
                    width: parent.width
                    spacing: 15
                    Image {
                        Layout.preferredWidth: 32; Layout.preferredHeight: 32
                        source: modelData.avatarUrl || "../../icon/DefaultHead.png"
                        fillMode: Image.PreserveAspectFit
                        layer.enabled: true
                        layer.effect: OpacityMask {
                            maskSource: Rectangle {
                                width: 32
                                height: 32
                                radius: 8
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Label { font.weight: Font.DemiBold; text: modelData.name; color: Theme.currentTheme.colors.textColor }
                        Label { text: modelData.type; color: Theme.currentTheme.colors.textSecondaryColor }
                    }
                    Button {
                        text: modelData.isDefault ? (Backend ? Backend.tr("正在使用") : "正在使用") : (Backend ? Backend.tr("使用此账户") : "使用此账户")
                        enabled: !modelData.isDefault
                        onClicked: { if (Backend) Backend.setDefaultMinecraftAccount(modelData.index) }
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                text: (Backend ? Backend.tr("暂无账户，请从云端同步") : "暂无账户，请从云端同步")
                visible: accountList.length === 0
                color: Theme.currentTheme.colors.textTertialyColor
            }
        }

        // --- Cloud Management Section ---
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("通过 Bloret PassPort 管理你的账户") : "通过 Bloret PassPort 管理你的账户")
                        color: Theme.currentTheme.colors.textColor
                    }
                    Label {
                        text: (Backend ? Backend.tr("轻松登录你的 Minecraft Account，便捷地进行操作。") : "轻松登录你的 Minecraft Account，便捷地进行操作。")
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15

                    Button {
                        text: (Backend ? Backend.tr("网站管理") : "网站管理")
                        onClicked: { if (Backend) Backend.manageAccountOnWebsite() }
                    }

                    Button {
                        text: (Backend ? Backend.tr("云端同步") : "云端同步")
                        highlighted: true
                        onClicked: { if (Backend) Backend.syncAccountFromPassPort() }
                    }
                    
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
}
