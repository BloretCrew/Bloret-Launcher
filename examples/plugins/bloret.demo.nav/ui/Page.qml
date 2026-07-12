import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: page
    title: "插件示例"

    Component.onCompleted: {
        console.log("[DemoNav] 插件页面已加载")
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: "这是由插件 bloret.demo.nav 贡献的导航页。"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            font.pixelSize: 14
        }

        Label {
            text: {
                if (typeof PluginHost === "undefined" || !PluginHost)
                    return "PluginHost 不可用"
                try {
                    var list = JSON.parse(PluginHost.getPluginsJson())
                    return "当前已加载插件数: " + list.length
                } catch (e) {
                    return "读取插件列表失败: " + e
                }
            }
            Layout.fillWidth: true
            color: Theme.currentTheme.colors.textSecondaryColor
        }

        Button {
            text: "打开插件目录"
            highlighted: true
            onClicked: {
                console.log("[DemoNav] openPluginDir")
                if (typeof PluginHost !== "undefined" && PluginHost)
                    PluginHost.openPluginDir()
            }
        }

        Item { Layout.fillHeight: true }
    }
}
