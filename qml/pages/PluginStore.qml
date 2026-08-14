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
        width: Math.min(640, storePage.width - 32)
        height: Math.min(680, storePage.height - 48)
        title: tr("插件详情")
        standardButtons: Dialog.NoButton
        closePolicy: Popup.CloseOnEscape

        contentItem: ColumnLayout {
            spacing: 16

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AlwaysOff }

                ColumnLayout {
                    width: parent.width
                    Layout.fillWidth: true
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        Image {
                            Layout.preferredWidth: 72
                            Layout.preferredHeight: 72
                            source: selectedPlugin && selectedPlugin.icon ? selectedPlugin.icon : Qt.resolvedUrl("../../icon/Bloret.png")
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: 144
                            sourceSize.height: 144
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                Layout.fillWidth: true
                                text: selectedPlugin ? (selectedPlugin.name || selectedPlugin.id) : ""
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: selectedPlugin && selectedPlugin.author ? selectedPlugin.author : tr("未知作者")
                                color: Theme.currentTheme.colors.textSecondaryColor
                                elide: Text.ElideRight
                            }
                            Label {
                                visible: selectedPlugin && selectedPlugin.author_username
                                text: selectedPlugin ? "@" + selectedPlugin.author_username : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                                elide: Text.ElideRight
                            }
                            Label {
                                visible: selectedPlugin && selectedPlugin.version
                                text: selectedPlugin ? "v" + selectedPlugin.version : ""
                                color: Theme.currentTheme.colors.primaryColor
                                font.weight: Font.DemiBold
                            }
                            Label {
                                visible: selectedPlugin && selectedPlugin.status
                                text: selectedPlugin ? tr("状态") + ": " + selectedPlugin.status : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: selectedPlugin ? (selectedPlugin.description || tr("暂无插件描述")) : ""
                        wrapMode: Text.Wrap
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Label {
                        Layout.fillWidth: true
                        visible: selectedPlugin && selectedPlugin.long_description
                        text: selectedPlugin ? selectedPlugin.long_description : ""
                        wrapMode: Text.Wrap
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: selectedPlugin && selectedPlugin.tags && selectedPlugin.tags.length > 0
                        Repeater {
                            model: selectedPlugin && selectedPlugin.tags ? selectedPlugin.tags : []
                            delegate: Rectangle {
                                width: tagLabel.implicitWidth + 18
                                height: 26
                                radius: 13
                                color: Theme.currentTheme.colors.controlFillColor
                                border.color: Theme.currentTheme.colors.controlBorderColor
                                Label {
                                    id: tagLabel
                                    anchors.centerIn: parent
                                    text: "#" + modelData
                                    color: Theme.currentTheme.colors.primaryColor
                                    font.pixelSize: 12
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: metadataColumn.implicitHeight + 24
                        radius: 10
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor

                        ColumnLayout {
                            id: metadataColumn
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Label {
                                text: tr("插件信息")
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: selectedPlugin ? tr("ID") + ": " + selectedPlugin.id : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.WrapAnywhere
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.min_launcher
                                text: selectedPlugin ? tr("最低启动器版本") + ": " + selectedPlugin.min_launcher : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.sha256
                                text: selectedPlugin ? "SHA256: " + selectedPlugin.sha256 : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.WrapAnywhere
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.download
                                text: selectedPlugin ? tr("下载地址") + ": " + selectedPlugin.download : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.WrapAnywhere
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.size
                                text: selectedPlugin ? tr("文件大小") + ": " + selectedPlugin.size : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.install_count
                                text: selectedPlugin ? tr("安装次数") + ": " + selectedPlugin.install_count : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.rating_count
                                text: selectedPlugin ? tr("评分") + ": " + selectedPlugin.rating_average + " (" + selectedPlugin.rating_count + ")" : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.created_at
                                text: selectedPlugin ? tr("创建时间") + ": " + selectedPlugin.created_at : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: selectedPlugin && selectedPlugin.updated_at
                                text: selectedPlugin ? tr("更新时间") + ": " + selectedPlugin.updated_at : ""
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }

                    Image {
                        Layout.fillWidth: true
                        visible: selectedPlugin && selectedPlugin.screenshots && selectedPlugin.screenshots.length > 0
                        source: selectedPlugin && selectedPlugin.screenshots && selectedPlugin.screenshots.length > 0
                                ? (selectedPlugin.screenshots[0].webpUrl || selectedPlugin.screenshots[0].url || "") : ""
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: 1100
                        asynchronous: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: selectedPlugin && selectedPlugin.permissions && selectedPlugin.permissions.length > 0

                        Label {
                            text: tr("所需权限")
                            font.weight: Font.DemiBold
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            Repeater {
                                model: selectedPlugin && selectedPlugin.permissions ? selectedPlugin.permissions : []
                                delegate: Rectangle {
                                    width: permissionLabel.implicitWidth + 18
                                    height: 28
                                    radius: 14
                                    color: Theme.currentTheme.colors.controlFillColor
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    Label {
                                        id: permissionLabel
                                        anchors.centerIn: parent
                                        text: modelData
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        font.pixelSize: 12
                                    }
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Button {
                    Layout.fillWidth: true
                    visible: selectedPlugin && selectedPlugin.detail_url
                    text: tr("在浏览器中打开")
                    onClicked: {
                        if (Backend)
                            Backend.openUrl(selectedPlugin.detail_url)
                    }
                }
                Button {
                    Layout.fillWidth: true
                    text: tr("取消")
                    onClicked: detailDialog.close()
                }
                Button {
                    Layout.fillWidth: true
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
