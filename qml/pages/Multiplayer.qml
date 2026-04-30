import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: multiplayerPage
    title: (Backend ? Backend.tr("联机") : "联机")

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
        text: "使用 IPV6 进行联机，可无需打开 Bloret Launcher 就能与其他人联机游玩。\n<b>IPV6 是您的运营商提供的一项免费服务，不额外收费。</b> 已拥有的用户点击刷新直接显示。\nIPV6 联机可能并不稳定。"
        color: Theme.currentTheme.colors.textSecondaryColor
        textFormat: Text.RichText
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        font.pixelSize: 12
    }
}
