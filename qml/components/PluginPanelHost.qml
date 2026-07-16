import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

/**
 * 通用插件面板宿主：按 area 加载 PluginHost 贡献的 QML 面板。
 * 用法: PluginPanelHost { area: "mods"; Layout.fillWidth: true }
 */
ColumnLayout {
    id: root
    property string area: ""
    property var pluginPanels: []
    spacing: 12
    visible: pluginPanels && pluginPanels.length > 0

    function reloadPanels() {
        pluginPanels = []
        if (!area || typeof PluginHost === "undefined" || !PluginHost) {
            console.log("[PluginPanelHost] skip area=", area, " PluginHost unavailable")
            return
        }
        try {
            var raw = PluginHost.getPanelContributionsJson(area)
            var list = JSON.parse(raw || "[]")
            console.log("[PluginPanelHost] area=", area, " count=", list.length)
            pluginPanels = list
        } catch (e) {
            console.log("[PluginPanelHost] reload error area=", area, e)
            pluginPanels = []
        }
    }

    Component.onCompleted: reloadPanels()

    Connections {
        target: (typeof PluginHost !== "undefined") ? PluginHost : null
        enabled: (typeof PluginHost !== "undefined") && PluginHost !== null
        function onPanelsContributionsChanged() {
            root.reloadPanels()
        }
        function onPluginsChanged() {
            root.reloadPanels()
        }
    }

    Label {
        visible: root.pluginPanels && root.pluginPanels.length > 0
        text: (Backend ? Backend.tr("插件扩展") : "插件扩展")
        font.pixelSize: 14
        font.weight: Font.DemiBold
        color: Theme.currentTheme.colors.textSecondaryColor
        Layout.fillWidth: true
    }

    Repeater {
        model: root.pluginPanels
        delegate: Loader {
            Layout.fillWidth: true
            Layout.preferredHeight: item ? item.implicitHeight || item.height || 80 : 80
            source: modelData.qml || ""
            asynchronous: true
            onStatusChanged: {
                if (status === Loader.Error)
                    console.log("[PluginPanelHost] panel error area=", root.area, "id=", modelData.id, modelData.qml)
                else if (status === Loader.Ready)
                    console.log("[PluginPanelHost] panel ready area=", root.area, "id=", modelData.id)
            }
        }
    }
}
