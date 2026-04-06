import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: multiplayerPage
    title: (Backend ? Backend.tr("联机") : "联机")

    property string etStatusTitle: Backend ? Backend.getEasytierStatusTitle() : ""
    property string etStatusDesc: Backend ? Backend.getEasytierStatusDesc() : ""

    Connections {
        target: Backend
        function onEasytierStatusChanged(title, desc) {
            etStatusTitle = title
            etStatusDesc = desc
        }
    }

    // --- Network Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: (Backend ? Backend.tr("网络") : "网络")
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
            
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("IPV6") : "IPV6")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("查看您计算机的 IPV6 配置") : "查看您计算机的 IPV6 配置")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Label {
                id: ipv6AddressLabel
                font.weight: Font.DemiBold
                text: Backend ? Backend.getIpv6Address() : "N/A"
                elide: Text.ElideMiddle
                Layout.maximumWidth: 200
                color: Theme.currentTheme.colors.textColor
            }

            Button {
                text: (Backend ? Backend.tr("刷新") : "刷新")
                onClicked: { if (Backend) ipv6AddressLabel.text = Backend.checkIpv6Address() }
            }
        }
    }

    Label {
        text: "使用 IPV6 进行联机，可无需打开 Bloret Launcher 就能与其他人联机游玩。\n<b>IPV6 是您的运营商提供的一项免费服务，不额外收费。</b> 已拥有的用户点击刷新直接显示。\nIPV6 联机可能并不稳定，如果您追求稳定性，建议使用下方 Online Client 进行联机。"
        color: Theme.currentTheme.colors.textSecondaryColor
        textFormat: Text.RichText
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        font.pixelSize: 12
    }

    // --- Easytier Section ---
    RowLayout {
        spacing: 10
        Layout.topMargin: 10

        Label {
            font.pixelSize: 20
            font.weight: Font.DemiBold
            text: (Backend ? Backend.tr("EasyTier 组网") : "EasyTier 组网")
            color: Theme.currentTheme.colors.textColor
        }

        Badge {
            text: "Pre-alpha"
            colorType: "Warning"
        }
        Badge {
            text: "EasyTier"
            colorType: "Success"
        }
        
    }

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

            // Status Card
            Frame {
                Layout.fillWidth: true
                padding: 15
                background: Rectangle {
                    color: Theme.currentTheme.colors.controlFillSecondaryColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }
                
                RowLayout {
                    width: parent.width
                    spacing: 15
                    Image {
                        source: "../../icon/java.png"
                        sourceSize { width: 32; height: 32 }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Label {
                            text: etStatusTitle
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: etStatusDesc
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            // Controls
            RowLayout {
                Layout.fillWidth: true
                spacing: 20

                // Host Side
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { text: (Backend ? Backend.tr("作为房主") : "作为房主"); font.weight: Font.DemiBold; color: Theme.currentTheme.colors.textColor }
                    RowLayout {
                        TextField {
                            id: mcPortInput
                            placeholderText: "MC 端口 (默认 25565)"
                            text: "25565"
                            Layout.fillWidth: true
                        }
                        TextField {
                            id: hostPasswordInput
                            placeholderText: "组网密码"
                            echoMode: TextInput.Password
                            Layout.fillWidth: true
                        }
                    }
                    Button {
                        text: (Backend ? Backend.tr("开启联机服务") : "开启联机服务")
                        highlighted: true
                        Layout.fillWidth: true
                        onClicked: { if (Backend) Backend.startEasytierWithConfig(mcPortInput.text, hostPasswordInput.text) }
                    }
                }

                Rectangle { width: 1; Layout.fillHeight: true; color: Theme.currentTheme.colors.dividerBorderColor }

                // Client Side
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { text: (Backend ? Backend.tr("作为加入者") : "作为加入者"); font.weight: Font.DemiBold; color: Theme.currentTheme.colors.textColor }
                    TextField {
                        id: joinPasswordInput
                        placeholderText: "对方告知您的组网密码"
                        echoMode: TextInput.Password
                        Layout.fillWidth: true
                    }
                    Button {
                        text: (Backend ? Backend.tr("连接到对方") : "连接到对方")
                        Layout.fillWidth: true
                        onClicked: { if (Backend) Backend.joinEasytierWithConfig("", joinPasswordInput.text) }
                    }
                    Item { height: 40 } // Spacer to align buttons
                }
            }
        }
    }

    Label {
        text: (Backend ? Backend.tr("联机服务 Powered by EasyTier. 对方也需要安装 Bloret Launcher 或 EasyTier 才能加入。") : "联机服务 Powered by EasyTier. 对方也需要安装 Bloret Launcher 或 EasyTier 才能加入。")
        color: Theme.currentTheme.colors.textTertialyColor
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        font.pixelSize: 12
    }
}
