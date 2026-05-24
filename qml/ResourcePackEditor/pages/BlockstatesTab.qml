import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: blockstatesPage

    property var _blockstates: []
    property string _currentPath: ""
    property string _currentName: ""
    property string _currentNamespace: ""
    property bool _modified: false
    property string _originalContent: ""

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshBlockstates()
        }
    }

    function refreshBlockstates() {
        if (!RPEditor) return
        _blockstates = RPEditor.getBlockstates()
        blockstateList.model = _blockstates
        countLabel.text = "共 " + _blockstates.length + " 个方块状态文件"

        if (_blockstates.length > 0) {
            blockstateList.currentIndex = 0
            selectBlockstate(0)
        } else {
            _currentPath = ""
            _currentName = ""
            _currentNamespace = ""
            editorArea.text = ""
            _modified = false
            _originalContent = ""
            pathLabel.text = ""
        }
    }

    function selectBlockstate(index) {
        if (index < 0 || index >= _blockstates.length) return
        var item = _blockstates[index]
        _currentPath = item.path
        _currentName = item.name
        _currentNamespace = item.namespace
        pathLabel.text = item.namespace + "/" + item.name

        if (!RPEditor) return
        var content = RPEditor.getFileContent(item.path)
        editorArea.text = content
        _originalContent = content
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
            spacing: 8

            RowLayout {
                Layout.fillWidth: true

                Label {
                    text: "方块状态编辑器"
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                Label {
                    id: countLabel
                    text: "加载中..."
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 12
                }
            }

            Label {
                text: "编辑资源包中的方块状态 JSON 文件，定义方块的视觉状态映射。"
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "路径："
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                Label {
                    id: pathLabel
                    text: ""
                    font.pixelSize: 12
                    font.family: "monospace"
                    color: Theme.currentTheme.colors.textColor
                    elide: Text.ElideMiddle
                    Layout.fillWidth: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "保存"
                    highlighted: true
                    enabled: _currentPath && _modified && RPEditor && RPEditor.isPackOpen()
                    onClicked: {
                        if (RPEditor && _currentPath) {
                            RPEditor.saveFile(_currentPath, editorArea.text)
                            _originalContent = editorArea.text
                            _modified = false
                        }
                    }
                }

                Button {
                    text: "重置"
                    enabled: _modified
                    onClicked: {
                        editorArea.text = _originalContent
                        _modified = false
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 500
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.preferredWidth: 240
                        Layout.fillHeight: true
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        ListView {
                            id: blockstateList
                            anchors.fill: parent
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                width: blockstateList.width
                                height: 44
                                color: ListView.isCurrentItem
                                    ? (Theme.accentColor || "#0078D4")
                                    : (index % 2 === 0 ? "transparent" : Theme.currentTheme.colors.controlAltSecondaryColor)
                                radius: 0

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    anchors.leftMargin: 12
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
                                        color: ListView.isCurrentItem ? "rgba(255,255,255,0.7)" : Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        blockstateList.currentIndex = index
                                        selectBlockstate(index)
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
                            placeholderText: "选择一个方块状态文件以编辑..."
                            selectByMouse: true
                            onTextChanged: {
                                _modified = (editorArea.text !== _originalContent)
                            }
                        }
                    }
                }
            }

            Dialog {
                id: saveConfirmDialog
                title: "保存更改"
                modal: true
                width: 400
                closePolicy: Popup.CloseOnEscape

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "当前文件有未保存的更改。是否保存？"
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                        color: Theme.currentTheme.colors.textColor
                    }

                    Label {
                        text: _currentPath
                        font.pixelSize: 11
                        font.family: "monospace"
                        color: Theme.currentTheme.colors.textSecondaryColor
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 8

                        Item { Layout.fillWidth: true }

                        Button {
                            text: "取消"
                            flat: true
                            onClicked: saveConfirmDialog.reject()
                        }

                        Button {
                            text: "不保存"
                            onClicked: saveConfirmDialog.reject()
                        }

                        Button {
                            text: "保存"
                            highlighted: true
                            onClicked: saveConfirmDialog.accept()
                        }
                    }
                }

                onAccepted: {
                    if (RPEditor && _currentPath) {
                        RPEditor.saveFile(_currentPath, editorArea.text)
                        _originalContent = editorArea.text
                        _modified = false
                    }
                }
            }
        }
    }
}
