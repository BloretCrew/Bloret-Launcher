import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: textsPage

    property var _texts: []
    property string _currentPath: ""
    property bool _modified: false

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshTexts()
        }
    }

    function refreshTexts() {
        if (!RPEditor) return
        _texts = RPEditor.getTexts()
        textsList.model = _texts

        if (_texts.length > 0) {
            textsList.currentIndex = 0
            selectText(0)
        } else {
            _currentPath = ""
            editorArea.text = ""
            pathLabel.text = ""
            _modified = false
        }
    }

    function selectText(index) {
        if (index < 0 || index >= _texts.length) return
        var item = _texts[index]
        _currentPath = item.path
        pathLabel.text = item.path
        _modified = false

        if (!RPEditor) return
        var content = RPEditor.getFileContent(item.path) || ""
        editorArea.text = content
    }

    function saveCurrent() {
        if (!_currentPath || !RPEditor) return
        RPEditor.saveFile(_currentPath, editorArea.text)
        _modified = false
    }

    on_ModifiedChanged: {
        if (_modified) {
            unsavedIndicator.visible = true
        } else {
            unsavedIndicator.visible = false
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        ColumnLayout {
            Layout.preferredWidth: 240
            Layout.fillHeight: true
            spacing: 8

            Label {
                text: "文本文件"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ListView {
                    id: textsList
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    spacing: 2

                    delegate: Rectangle {
                        width: textsList.width
                        height: 48
                        color: ListView.isCurrentItem ? (Theme.accentColor || "#0078D4") : "transparent"
                        radius: 4

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: modelData.name
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
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

                            Rectangle {
                                width: badgeText.implicitWidth + 12
                                height: 18
                                radius: 4
                                color: modelData.type === "json" ? "#2563EB" : "#6B7280"

                                Label {
                                    id: badgeText
                                    anchors.centerIn: parent
                                    text: modelData.type.toUpperCase()
                                    font.pixelSize: 9
                                    font.weight: Font.DemiBold
                                    color: "#FFFFFF"
                                }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                textsList.currentIndex = index
                                selectText(index)
                            }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8

                    Label {
                        id: pathLabel
                        text: "选择一个文本文件"
                        font.pixelSize: 11
                        font.family: "monospace"
                        color: Theme.currentTheme.colors.textSecondaryColor
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        id: unsavedIndicator
                        width: 8
                        height: 8
                        radius: 4
                        color: "#F59E0B"
                        visible: false
                    }

                    Button {
                        text: "保存"
                        highlighted: true
                        enabled: _modified && _currentPath !== ""
                        onClicked: saveCurrent()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                TextArea {
                    id: editorArea
                    anchors.fill: parent
                    anchors.margins: 8
                    font.family: "monospace"
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: Text.Wrap
                    selectByMouse: true
                    background: null
                    onTextChanged: {
                        _modified = true
                    }
                }
            }
        }
    }

    Dialog {
        id: saveConfirmDialog
        title: "保存更改"
        modal: true
        width: 360
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "当前文件有未保存的更改。是否保存？"
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textColor
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
                    flat: true
                    onClicked: saveConfirmDialog.discard()
                }
                Button {
                    text: "保存"
                    highlighted: true
                    onClicked: saveConfirmDialog.accept()
                }
            }
        }

        onAccepted: {
            saveCurrent()
            saveConfirmDialog.close()
        }

        onDiscarded: {
            saveConfirmDialog.close()
        }

        function discard() {
            _modified = false
            saveConfirmDialog.close()
        }
    }
}
