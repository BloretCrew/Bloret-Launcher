import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

Item {
    id: overviewPage

    property var _mcmeta: ({})
    property var _stats: ({})

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            try {
                _mcmeta = JSON.parse(info.mcmeta)
                _stats = JSON.parse(info.stats)
            } catch(e) {}
            refreshView()
        }
    }

    function refreshView() {
        var desc = ""
        var packFmt = ""
        if (_mcmeta && _mcmeta.pack) {
            desc = _mcmeta.pack.description || ""
            packFmt = String(_mcmeta.pack.pack_format || "")
        }
        descField.text = desc
        formatField.text = packFmt
        fileCountLabel.text = String(_stats.files || "0")
        textureCountLabel.text = String(_stats.textures || "0")
        langCountLabel.text = String(_stats.languages || "0")
        modelCountLabel.text = String(_stats.models || "0")
        commitCount.text = String(RPEditor ? RPEditor.getCommitCount() : 0)
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentHeight: contentColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: contentColumn
            width: parent.width
            spacing: 16

            Label {
                text: (Backend ? Backend.tr("资源包概览") : "资源包概览")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: cardInfoColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: cardInfoColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: (Backend ? Backend.tr("包信息") : "包信息")
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "pack_format:"; color: Theme.currentTheme.colors.textSecondaryColor }
                        Label { id: formatField; text: "-"; color: Theme.currentTheme.colors.textColor }
                        Item { Layout.fillWidth: true }
                        Label { text: (Backend ? Backend.tr("提交数:") : "提交数:"); color: Theme.currentTheme.colors.textSecondaryColor }
                        Label { id: commitCount; text: "0"; color: Theme.currentTheme.colors.textColor }
                    }

                    Label {
                        text: (Backend ? Backend.tr("描述") : "描述")
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    MinecraftFormattedText {
                        id: descField
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        rawText: "-"
                        color: Theme.currentTheme.colors.textColor
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: cardStatsColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: cardStatsColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: (Backend ? Backend.tr("文件统计") : "文件统计")
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    GridLayout {
                        columns: 4
                        columnSpacing: 24
                        rowSpacing: 12
                        Layout.fillWidth: true

                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { id: fileCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; Layout.alignment: Qt.AlignHCenter; color: Theme.accentColor || "#0078D4" }
                            Label { text: (Backend ? Backend.tr("总文件") : "总文件"); Layout.alignment: Qt.AlignHCenter; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { id: textureCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; Layout.alignment: Qt.AlignHCenter; color: "#FF9800" }
                            Label { text: (Backend ? Backend.tr("贴图") : "贴图"); Layout.alignment: Qt.AlignHCenter; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { id: langCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; Layout.alignment: Qt.AlignHCenter; color: "#4CAF50" }
                            Label { text: (Backend ? Backend.tr("语言文件") : "语言文件"); Layout.alignment: Qt.AlignHCenter; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { id: modelCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; Layout.alignment: Qt.AlignHCenter; color: "#2196F3" }
                            Label { text: (Backend ? Backend.tr("模型") : "模型"); Layout.alignment: Qt.AlignHCenter; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: cardActionsColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: cardActionsColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: (Backend ? Backend.tr("快速操作") : "快速操作")
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        spacing: 12

                        Button {
                            text: (Backend ? Backend.tr("导出为 ZIP") : "导出为 ZIP")
                            icon.name: "ic_fluent_arrow_download_20_regular"
                            enabled: RPEditor && RPEditor.isPackOpen
                            onClicked: {
                                if (RPEditor) {
                                    var zipPath = RPEditor.exportAsZip()
                                    if (zipPath) {
                                        exportResult.text = (Backend ? Backend.tr("已导出: ") : "已导出: ") + zipPath
                                        exportResult.visible = true
                                        exportTimer.start()
                                    }
                                }
                            }
                        }

                        Button {
                            text: RPEditor ? RPEditor.getExplorerLabel() : (Backend ? Backend.tr("文件管理器") : "文件管理器")
                            icon.name: "ic_fluent_folder_open_20_regular"
                            enabled: RPEditor && RPEditor.isPackOpen
                            onClicked: { if (RPEditor) RPEditor.showInExplorer() }
                        }

                        Button {
                            text: "VS Code"
                            icon.name: "ic_fluent_code_20_regular"
                            enabled: RPEditor && RPEditor.isPackOpen
                            onClicked: { if (RPEditor) RPEditor.openInVSCode() }
                        }

                        Button {
                            text: (Backend ? Backend.tr("终端") : "终端")
                            icon.name: "ic_fluent_window_console_20_regular"
                            enabled: RPEditor && RPEditor.isPackOpen
                            onClicked: { if (RPEditor) RPEditor.openInTerminal() }
                        }
                    }

                    Label {
                        id: exportResult
                        visible: false
                        font.pixelSize: 12
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.fillWidth: true
                    }

                    Timer {
                        id: exportTimer
                        interval: 3000
                        onTriggered: exportResult.visible = false
                    }
                }
            }
        }
    }
}
