import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: fontsPage

    property var _fonts: []
    property string _selectedPath: ""
    property bool _modified: false

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshFonts()
        }
    }

    function refreshFonts() {
        if (!RPEditor) return
        _fonts = RPEditor.getFonts()
        fontList.model = _fonts

        if (_fonts.length > 0) {
            fontList.currentIndex = 0
            selectFont(0)
        } else {
            _selectedPath = ""
            editorArea.text = ""
            fontTitle.text = Backend ? Backend.tr("选择字体文件") : "选择字体文件"
            pathLabel.text = ""
        }
    }

    function selectFont(index) {
        if (index < 0 || index >= _fonts.length) return
        var font = _fonts[index]
        _selectedPath = font.path
        pathLabel.text = font.path

        if (!RPEditor) return
        var content = RPEditor.getFileContent(font.path)
        editorArea.text = content
        _modified = false

        fontTitle.text = font.name + " (" + font.namespace + ")"
    }

    function saveCurrentFont() {
        if (!_selectedPath || !RPEditor) return
        RPEditor.saveFile(_selectedPath, editorArea.text)
        _modified = false
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
                text: (Backend ? Backend.tr("字体定义编辑器") : "字体定义编辑器")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Label {
                text: (Backend ? Backend.tr("编辑 Minecraft 资源包中的字体 JSON 定义文件。") : "编辑 Minecraft 资源包中的字体 JSON 定义文件。")
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 400
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.preferredWidth: 200
                        Layout.fillHeight: true
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            Label {
                                text: (Backend ? Backend.tr("字体文件") : "字体文件")
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                                Layout.fillWidth: true
                                Layout.margins: 8
                            }

                            ListView {
                                id: fontList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true

                                delegate: Rectangle {
                                    width: fontList.width
                                    height: 40
                                    color: ListView.isCurrentItem ? (Theme.accentColor || "#0078D4") : (index % 2 === 0 ? "transparent" : Theme.currentTheme.colors.controlAltSecondaryColor)
                                    radius: 4

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 1

                                        Label {
                                            text: modelData.name
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                            color: ListView.isCurrentItem ? "#FFFFFF" : Theme.currentTheme.colors.textColor
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }

                                        Label {
                                            text: modelData.namespace
                                            font.pixelSize: 10
                                            color: ListView.isCurrentItem ? "#CCFFFFFF" : Theme.currentTheme.colors.textSecondaryColor
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            fontList.currentIndex = index
                                            selectFont(index)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: Theme.currentTheme.colors.controlAltSecondaryColor

                        TextArea {
                            id: editorArea
                            anchors.fill: parent
                            anchors.margins: 8
                            font.family: "monospace"
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textColor
                            background: null
                            wrapMode: Text.NoWrap
                            placeholderText: (Backend ? Backend.tr("选择一个字体文件以编辑...") : "选择一个字体文件以编辑...")
                            onTextChanged: {
                                _modified = editorArea.text !== "" && _selectedPath !== ""
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    id: fontTitle
                    text: (Backend ? Backend.tr("选择字体文件") : "选择字体文件")
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                Label {
                    id: pathLabel
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                    elide: Text.ElideMiddle
                    Layout.maximumWidth: 300
                }

                Button {
                    text: (Backend ? Backend.tr("保存") : "保存")
                    highlighted: true
                    enabled: _selectedPath !== "" && _modified && RPEditor
                    onClicked: saveCurrentFont()
                }

                Button {
                    text: (Backend ? Backend.tr("刷新") : "刷新")
                    enabled: RPEditor
                    onClicked: refreshFonts()
                }
            }
        }
    }
}
