import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: agentPage

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 80
            height: 80
            radius: 40
            color: Theme.currentTheme.colors.controlAltSecondaryColor

            Label {
                anchors.centerIn: parent
                text: "🤖"
                font.pixelSize: 36
            }
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "AI 助手"
            font.pixelSize: 20
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 400
            text: "AI 编辑功能正在开发中。\n未来你可以在这里让 AI 帮助你：\n\n• 自动修改语言文件\n• 生成资源包结构\n• 智能贴图推荐\n• 自动修复 JSON 错误"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 13
            lineHeight: 1.6
            color: Theme.currentTheme.colors.textSecondaryColor
            wrapMode: Text.Wrap
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.maximumWidth: 500
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 16
            radius: 8
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                Label {
                    text: "即将推出"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    text: "1. 自然语言编辑：用中文描述你的修改需求\n2. 批量翻译：一键翻译语言文件\n3. 结构生成：根据描述生成资源包结构\n4. 智能修复：自动检测并修复常见问题"
                    font.pixelSize: 12
                    lineHeight: 1.5
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                }
            }
        }
    }
}
