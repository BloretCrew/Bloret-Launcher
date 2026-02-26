import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: infoPage
    title: qsTr("关于")

    // --- Header Card ---
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
            spacing: 20

            Image {
                source: "../../icon/home.png"
                sourceSize { width: 100; height: 100 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                
                Label {
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                    text: "Bloret Launcher"
                }
                
                Label {
                    text: qsTr("Conveniently manage your Minecraft, conveniently play Bloret.\n便捷地管理你的 Minecraft，便捷地游玩 Bloret。")
                    color: "#7f7f7f"
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    // --- Detailed Info text ---
    Label {
        text: "Bloret Launcher Website: <a href='https://launcher.bloret.net/'>https://launcher.bloret.net/</a><br>" +
              "Bloret PassPort: <a href='https://passport.bloret.net/'>https://passport.bloret.net/</a><br>" +
              "百络百科: <a href='https://wiki.bloret.net/'>https://wiki.bloret.net/</a><br>" +
              "Bloret Launcher 将百络谷带到您的计算机上。<br>" +
              "Bloret Launcher 是由 Bloret 所有的无广告免费开源软件。<br><br>" +
              "© 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.<br>" +
              "要查看 Bloret Launcher 的源代码，请前往: <a href='https://github.com/BloretCrew/Bloret-Launcher/'>https://github.com/BloretCrew/Bloret-Launcher/</a><br>" +
              "要查看 Bloret Launcher Setup 的源代码，请前往: <a href='https://github.com/BloretCrew/Bloret-Launcher-Setup/'>https://github.com/BloretCrew/Bloret-Launcher-Setup/</a><br>" +
              "要提交问题，请前往: <a href='https://github.com/BloretCrew/Bloret-Launcher/issues/new/choose'>https://github.com/BloretCrew/Bloret-Launcher/issues/new/choose</a><br><br>" +
              "Bloret Launcher 遵循 <a href='https://www.minecraft.net/zh-hans/eula'>Mojang Eula (Minecraft 最终用户许可协议)</a> ，Bloret Launcher 的 微软登录 功能已获 Mojang 批准，Bloret Launcher 本身未包含 Minecraft 二进制文件和其他资源文件。Bloret Launcher 是无广告免费开源软件。我们鼓励各位玩家购买 <a href='https://www.minecraft.net/zh-hans/choose-your-game'>Minecraft 正版账户</a> 进行游玩。"
        color: "#7f7f7f"
        textFormat: Text.RichText
        onLinkActivated: Backend.openUrl(link)
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }

    // --- QQ Card ---
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
            
            Rectangle {
                width: 50; height: 50
                color: "transparent"
                border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
                Image {
                    anchors.centerIn: parent
                    source: "../../icon/qq.png"
                    sourceSize { width: 40; height: 40 }
                }
            }

            Label {
                font.weight: Font.DemiBold
                text: "QQ"
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Bloret"
                onClicked: Backend.joinQQBloret()
            }

            Button {
                text: "Bloret Software Community"
                onClicked: Backend.joinQQCommunity()
            }
        }
    }

    // --- Github Card ---
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
            
            Image {
                source: "../../icon/github.png"
                sourceSize { width: 50; height: 50 }
            }

            Label {
                font.weight: Font.DemiBold
                text: "Github"
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Bloret Github 组织页面"
                onClicked: Backend.openGithubOrg()
            }

            Button {
                text: "此项目的 Github"
                onClicked: Backend.openGithubRepo()
            }
        }
    }

    Item { Layout.fillHeight: true } // spacer

    // Footer
    Label {
        text: "© 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved."
        color: "#7f7f7f"
        horizontalAlignment: Text.AlignHCenter
        Layout.fillWidth: true
        Layout.topMargin: 20
        Layout.bottomMargin: 10
    }
}
