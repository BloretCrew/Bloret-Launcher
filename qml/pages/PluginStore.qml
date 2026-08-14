import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import RinUI
import "../components"

FluentPage {
    id: storePage
    title: Backend ? Backend.tr("插件商店") : "插件商店"

    property var plugins: []
    property string searchText: ""
    property string selectedTag: ""
    property string errorText: ""
    property bool loading: false
    property var selectedPlugin: null
    property var storeBackend: (typeof StoreBackend !== "undefined") ? StoreBackend : null

    function tr(text) { return Backend ? Backend.tr(text) : text }

    function reloadFromJson(raw) {
        try {
            var parsed = JSON.parse(raw || "[]")
            plugins = Array.isArray(parsed) ? parsed : []
        } catch (e) {
            plugins = []
            errorText = tr("商店返回的数据格式无效") + ": " + e
        }
    }

    function visiblePlugins() {
        var query = searchText.trim().toLowerCase()
        return plugins.filter(function (p) {
            var text = [p.name, p.id, p.author, p.description, (p.tags || []).join(" ")].join(" ").toLowerCase()
            var matchesSearch = query.length === 0 || text.indexOf(query) >= 0
            var matchesTag = selectedTag.length === 0 || (p.tags || []).indexOf(selectedTag) >= 0
            return matchesSearch && matchesTag
        })
    }

    function allTags() {
        var result = []
        plugins.forEach(function (p) {
            ;(p.tags || []).forEach(function (tag) {
                if (result.indexOf(tag) < 0) result.push(tag)
            })
        })
        return result.sort()
    }

    function propose(item) {
        if (!item || !storeBackend)
            return
        var raw = storeBackend.proposeInstall(JSON.stringify({
            id: item.id, name: item.name, version: item.version,
            author: item.author, description: item.description,
            download: item.download, sha256: item.sha256,
            permissions: item.permissions, source: "store"
        }))
        try {
            var result = JSON.parse(raw || "{}")
            if (!result.ok)
                errorText = result.message || result.error || tr("无法提出安装请求")
        } catch (e) {
            errorText = String(e)
        }
    }

    Component.onCompleted: {
        reloadFromJson(storeBackend ? storeBackend.getPluginsJson() : "[]")
        if (storeBackend) storeBackend.refresh()
    }

    Connections {
        target: storeBackend
        enabled: storeBackend !== null
        function onPluginsChanged(raw) { reloadFromJson(raw) }
        function onLoadingChanged(value) { loading = value }
        function onErrorChanged(message) { errorText = message || "" }
    }

    Connections {
        target: (typeof PluginHost !== "undefined") ? PluginHost : null
        enabled: (typeof PluginHost !== "undefined") && PluginHost !== null
        function onPluginsChanged() {
            if (storeBackend) storeBackend.refreshInstallState()
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.margins: 20
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Label {
                text: tr("插件商店")
                font.pixelSize: 24
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }
            Item { Layout.fillWidth: true }
            Button {
                text: loading ? tr("加载中…") : tr("刷新")
                enabled: !loading && storeBackend !== null
                onClicked: { errorText = ""; if (storeBackend) storeBackend.refresh() }
            }
        }

        Label {
            Layout.fillWidth: true
            text: storeBackend && storeBackend.getApiBase() ? tr("来源") + ": " + storeBackend.getApiBase() : tr("尚未配置商店接口，请在设置中填写 HTTPS 列表地址")
            color: Theme.currentTheme.colors.textSecondaryColor
            elide: Text.ElideMiddle
        }

        RowLayout {
            Layout.fillWidth: true
            TextField {
                Layout.fillWidth: true
                placeholderText: tr("搜索插件名称、作者或标签")
                onTextChanged: { searchText = text; storeRepeater.model = visiblePlugins() }
            }
            ComboBox {
                id: tagCombo
                Layout.preferredWidth: 150
                model: [tr("全部标签")].concat(allTags())
                onActivated: {
                    selectedTag = currentIndex === 0 ? "" : String(currentText)
                    storeRepeater.model = visiblePlugins()
                }
            }
        }

        InfoBar {
            Layout.fillWidth: true
            visible: errorText.length > 0
            severity: Severity.Error
            title: tr("加载插件商店失败")
            text: errorText
        }

        Label {
            Layout.fillWidth: true
            visible: !loading && plugins.length === 0 && errorText.length === 0
            text: tr("暂无可用插件")
            color: Theme.currentTheme.colors.textSecondaryColor
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 1

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                GridLayout {
                id: storeGrid
                width: Math.max(implicitWidth, parent.width)
                columns: width >= 760 ? 2 : 1
                columnSpacing: 14
                rowSpacing: 14

                Repeater {
                    id: storeRepeater
                    model: visiblePlugins()
                    delegate: Frame {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 280
                        padding: 16
                        background: Rectangle {
                            color: Theme.currentTheme.colors.cardColor
                            radius: 8
                            border.color: Theme.currentTheme.colors.controlBorderColor
                        }
                        ColumnLayout {
                            width: parent.width
                            spacing: 8
                            RowLayout {
                                Layout.fillWidth: true
                                Image {
                                    Layout.preferredWidth: 48
                                    Layout.preferredHeight: 48
                                    source: modelData.icon || Qt.resolvedUrl("../../icon/Bloret.png")
                                    fillMode: Image.PreserveAspectFit
                                    sourceSize.width: 96
                                    sourceSize.height: 96
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Label {
                                        Layout.fillWidth: true
                                        text: modelData.name || modelData.id
                                        font.pixelSize: 17
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: (modelData.author || tr("未知作者")) + (modelData.version ? " · v" + modelData.version : "")
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.description || tr("暂无插件描述")
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.Wrap
                                maximumLineCount: 3
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: (modelData.tags || []).length > 0
                                text: "#" + (modelData.tags || []).join("  #")
                                color: Theme.currentTheme.colors.primaryColor
                                elide: Text.ElideRight
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Button {
                                    text: tr("详情")
                                    onClicked: { selectedPlugin = modelData; detailDialog.open() }
                                }
                                Item { Layout.fillWidth: true }
                                Button {
                                    highlighted: true
                                    text: modelData.update_available ? tr("更新") : (modelData.installed ? tr("已安装") : tr("安装"))
                                    enabled: !modelData.installed || modelData.update_available
                                    onClicked: propose(modelData)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: detailDialog
        modal: true
        width: Math.min(560, storePage.width - 40)
        title: selectedPlugin ? selectedPlugin.name : tr("插件详情")
        standardButtons: Dialog.Close
        contentItem: ScrollView {
            implicitHeight: Math.min(520, storePage.height - 120)
            ColumnLayout {
                width: parent.width
                spacing: 10
                Label { Layout.fillWidth: true; text: selectedPlugin ? (selectedPlugin.description || tr("暂无插件描述")) : ""; wrapMode: Text.Wrap }
                Label { Layout.fillWidth: true; text: selectedPlugin ? tr("ID") + ": " + selectedPlugin.id : ""; wrapMode: Text.WrapAnywhere }
                Label { Layout.fillWidth: true; text: selectedPlugin && selectedPlugin.version ? tr("版本") + ": " + selectedPlugin.version : "" }
                Label { Layout.fillWidth: true; text: selectedPlugin && selectedPlugin.author ? tr("作者") + ": " + selectedPlugin.author : "" }
                Label { Layout.fillWidth: true; text: selectedPlugin && selectedPlugin.permissions.length ? tr("权限") + ": " + selectedPlugin.permissions.join(", ") : ""; wrapMode: Text.Wrap }
                Label { Layout.fillWidth: true; text: selectedPlugin && selectedPlugin.sha256 ? "SHA256: " + selectedPlugin.sha256 : ""; wrapMode: Text.WrapAnywhere }
                Label { Layout.fillWidth: true; text: selectedPlugin && selectedPlugin.min_launcher ? tr("最低启动器版本") + ": " + selectedPlugin.min_launcher : "" }
                Button {
                    visible: selectedPlugin && selectedPlugin.homepage
                    text: tr("打开项目主页")
                    onClicked: {
                        if (Backend)
                            Backend.openUrl(selectedPlugin.homepage)
                    }
                }
                Button {
                    highlighted: true
                    text: selectedPlugin && selectedPlugin.update_available ? tr("更新") : tr("安装")
                    enabled: selectedPlugin && (!selectedPlugin.installed || selectedPlugin.update_available)
                    onClicked: { propose(selectedPlugin); detailDialog.close() }
                }
            }
        }
    }
}
}
