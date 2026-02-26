import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: multiplayerPage
    title: qsTr("联机")

    // --- Network Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("网络")
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
            
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("IPV6")
                }
                Label {
                    text: qsTr("查看您计算机的 IPV6 配置")
                    color: "#7f7f7f"
                }
            }

            Label {
                id: ipv6AddressLabel
                font.weight: Font.DemiBold
                text: Backend.getIpv6Address()
            }
        }
    }

    Button {
        text: qsTr("获取 IPV6 联机地址")
        onClicked: ipv6AddressLabel.text = Backend.checkIpv6Address()
    }

    Label {
        text: "使用 IPV6 进行联机，可无需打开 Bloret Launcher 就能与其他人联机游玩。\n<b>IPV6 是您的运营商提供的一项免费服务，不额外收费。</b> 已拥有的用户点击上方按钮直接使用。\nIPV6 联机可能并不稳定，如果您追求稳定性，建议使用下方 Online Client 进行联机。"
        color: "#7f7f7f"
        textFormat: Text.RichText
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }

    // --- Easytier Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("Easytier")
        Layout.topMargin: 10
    }

    Label {
        text: "Easytier 是一项开源项目，可以为您提供高效的联机服务。\n<b>在此处开启联机服务 ，对方需要打开 Bloret Launcher 才能与您一起联机。</b>"
        color: "#7f7f7f"
        textFormat: Text.RichText
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }

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

            Frame {
                Layout.fillWidth: true
                padding: 15
                background: Rectangle {
                    color: Theme.currentTheme.colors.surfaceColorDefault
                    radius: 8
                    border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
                }
                
                ColumnLayout {
                    width: parent.width
                    Label {
                        font.weight: Font.DemiBold
                        text: Backend.getEasytierStatusTitle()
                    }
                    Label {
                        text: Backend.getEasytierStatusDesc()
                        color: "#7f7f7f"
                    }
                    RowLayout {
                        Label { text: Backend.getEasytierLinkTip(); color: "#7f7f7f" }
                        Label { text: Backend.getEasytierLinkShow(); font.weight: Font.DemiBold }
                    }
                }
            }

            RowLayout {
                Item { Layout.fillWidth: true }
                Button {
                    text: qsTr("开启 Easytier 联机服务")
                    onClicked: Backend.startEasytierHost()
                }
                Button {
                    text: qsTr("连接到对方的网络")
                    onClicked: Backend.startEasytierClient()
                    Layout.leftMargin: 15
                }
            }
        }
    }

    Label {
        text: qsTr("联机服务 Powered by Easytier")
        color: "#7f7f7f"
        wrapMode: Text.Wrap
    }
}
