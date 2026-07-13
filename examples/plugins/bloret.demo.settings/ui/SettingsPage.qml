import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

ColumnLayout {
    id: root
    spacing: 12

    Component.onCompleted: {
        console.log("[DemoSettings] 插件设置页已加载")
    }

    Label {
        text: Backend ? Backend.tr("插件设置示例") : "插件设置示例"
        font.pixelSize: 16
        font.weight: Font.DemiBold
        color: Theme.currentTheme.colors.textColor
    }

    Label {
        text: Backend
              ? Backend.tr("此页面由 bloret.demo.settings 通过 contributes.settings 注入。")
              : "此页面由 bloret.demo.settings 通过 contributes.settings 注入。"
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        color: Theme.currentTheme.colors.textSecondaryColor
    }

    Frame {
        Layout.fillWidth: true
        padding: 12
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }
        ColumnLayout {
            width: parent.width
            spacing: 8
            Switch {
                id: demoSwitch
                text: Backend ? Backend.tr("示例开关") : "示例开关"
                checked: true
                onToggled: console.log("[DemoSettings] switch=", checked)
            }
            Label {
                text: (Backend ? Backend.tr("当前状态") : "当前状态") + ": "
                      + (demoSwitch.checked
                         ? (Backend ? Backend.tr("开启") : "开启")
                         : (Backend ? Backend.tr("关闭") : "关闭"))
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }
    }
}
