import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: mcmetaPage

    property var _mcmetaData: ({})

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            loadData()
        }
    }

    function loadData() {
        if (!RPEditor) return
        var raw = RPEditor.getMcmeta()
        try {
            _mcmetaData = JSON.parse(raw)
        } catch(e) {
            _mcmetaData = {}
        }

        var pack = _mcmetaData.pack || {}
        formatInput.text = String(pack.pack_format || "")
        var desc = pack.description
        if (typeof desc === "object" && desc !== null) {
            descInput.text = desc.text || desc.fallback || JSON.stringify(desc)
        } else {
            descInput.text = String(desc || "")
        }

        var sf = pack.supported_formats
        if (Array.isArray(sf)) {
            minFormatInput.text = String(sf[0] || "")
            maxFormatInput.text = String(sf[1] || "")
        } else if (typeof sf === "number") {
            minFormatInput.text = String(sf)
            maxFormatInput.text = ""
        } else {
            minFormatInput.text = String(pack.min_format || "")
            maxFormatInput.text = String(pack.max_format || "")
        }

        jsonPreview.text = raw
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
                text: "pack.mcmeta 编辑器"
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Label {
                text: "pack.mcmeta 是资源包的入口文件，定义了游戏如何识别和加载你的资源包。"
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: settingsColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: settingsColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Label {
                        text: "基础设置"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "pack_format（格式版本）"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                            TextField {
                                id: formatInput
                                Layout.fillWidth: true
                                placeholderText: "例如: 42"
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "最小兼容版本"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                            TextField {
                                id: minFormatInput
                                Layout.fillWidth: true
                                placeholderText: "可选"
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "最大兼容版本"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                            TextField {
                                id: maxFormatInput
                                Layout.fillWidth: true
                                placeholderText: "可选"
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Label { text: "描述"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        TextArea {
                            id: descInput
                            Layout.fillWidth: true
                            Layout.preferredHeight: 60
                            placeholderText: "资源包描述..."
                            wrapMode: Text.Wrap
                        }
                    }

                    RowLayout {
                        spacing: 8
                        Button {
                            text: "保存"
                            highlighted: true
                            onClicked: saveMcmeta()
                        }
                        Button {
                            text: "重置"
                            onClicked: loadData()
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: previewColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: previewColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Label {
                        text: "JSON 预览"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 200
                        radius: 4
                        color: Theme.currentTheme.colors.controlAltSecondaryColor

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            clip: true
                            contentHeight: jsonPreview.height

                            TextArea {
                                id: jsonPreview
                                width: parent.width
                                readOnly: true
                                font.family: "monospace"
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textColor
                                background: null
                                wrapMode: Text.NoWrap
                            }
                        }
                    }
                }
            }
        }
    }

    function saveMcmeta() {
        if (!RPEditor) return
        var pack = _mcmetaData.pack || {}
        pack.pack_format = parseInt(formatInput.text) || 0
        pack.description = descInput.text || ""

        if (minFormatInput.text && maxFormatInput.text) {
            pack.supported_formats = [parseInt(minFormatInput.text), parseInt(maxFormatInput.text)]
        } else if (minFormatInput.text) {
            pack.min_format = parseInt(minFormatInput.text)
            delete pack.supported_formats
        } else {
            delete pack.supported_formats
            delete pack.min_format
        }
        delete pack.max_format

        _mcmetaData.pack = pack
        var ok = RPEditor.saveMcmeta(JSON.stringify(_mcmetaData, null, 2))
        if (ok) {
            var raw = RPEditor.getMcmeta()
            jsonPreview.text = raw
        }
    }
}
