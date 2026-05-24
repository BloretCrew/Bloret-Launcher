import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

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

    ScrollView {
        anchors.fill: parent
        anchors.margins: 16
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: 16

            Label {
                text: "资源包概览"
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: "包信息"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "pack_format:"; color: Theme.currentTheme.colors.textSecondaryColor }
                        Label { id: formatField; text: "-"; color: Theme.currentTheme.colors.textColor }
                        Item { Layout.fillWidth: true }
                        Label { text: "提交数:"; color: Theme.currentTheme.colors.textSecondaryColor }
                        Label { id: commitCount; text: "0"; color: Theme.currentTheme.colors.textColor }
                    }

                    Label {
                        text: "描述"
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }

                    Label {
                        id: descField
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        text: "-"
                        color: Theme.currentTheme.colors.textColor
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: "文件统计"
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
                            Label { id: fileCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; color: Theme.currentTheme.colors.accentColor }
                            Label { text: "总文件"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Label { id: textureCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; color: "#FF9800" }
                            Label { text: "贴图"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Label { id: langCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; color: "#4CAF50" }
                            Label { text: "语言文件"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        ColumnLayout {
                            Label { id: modelCountLabel; text: "0"; font.pixelSize: 24; font.weight: Font.Bold; color: "#2196F3" }
                            Label { text: "模型"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: "快速操作"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        spacing: 12

                        Button {
                            text: "暂存所有更改"
                            enabled: RPEditor && RPEditor.isPackOpen()
                            onClicked: {
                                if (RPEditor) {
                                    var tree = RPEditor.getFileTree()
                                    for (var i = 0; i < tree.length; i++) {
                                        if (tree[i].gitStatus && tree[i].type !== "dir") {
                                            RPEditor.stageFile(tree[i].path)
                                        }
                                    }
                                }
                            }
                        }

                        Button {
                            text: "提交更改"
                            highlighted: true
                            enabled: RPEditor && RPEditor.isPackOpen()
                            onClicked: {
                                commitDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: commitDialog
        title: "提交更改"
        modal: true
        width: 400
        standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            anchors.fill: parent
            spacing: 8

            TextField {
                id: commitMsgInput
                Layout.fillWidth: true
                placeholderText: "输入提交信息..."
            }
        }

        onAccepted: {
            if (commitMsgInput.text.trim() && RPEditor) {
                RPEditor.commit(commitMsgInput.text.trim())
                commitMsgInput.text = ""
            }
        }
    }
}
