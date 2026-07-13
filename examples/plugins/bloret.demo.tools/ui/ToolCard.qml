import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Frame {
    Layout.fillWidth: true
    padding: 15
    background: Rectangle {
        color: Theme.currentTheme.colors.cardColor
        radius: 8
        border.color: Theme.currentTheme.colors.controlBorderColor
    }

    Component.onCompleted: console.log("[DemoTools] 工具卡片已加载")

    RowLayout {
        width: parent.width
        spacing: 15
        ColumnLayout {
            Layout.fillWidth: true
            Label {
                text: Backend ? Backend.tr("插件工具示例") : "插件工具示例"
                font.weight: Font.DemiBold
                font.pixelSize: 16
                color: Theme.currentTheme.colors.textColor
            }
            Label {
                text: Backend
                      ? Backend.tr("由 contributes.tools / ui.tools 注入到小工具页。")
                      : "由 contributes.tools / ui.tools 注入到小工具页。"
                color: Theme.currentTheme.colors.textSecondaryColor
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
        Button {
            text: Backend ? Backend.tr("测试") : "测试"
            highlighted: true
            onClicked: console.log("[DemoTools] test clicked")
        }
    }
}
