import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: fileBrowserPage

    property string _selectedFilePath: ""
    property bool _modified: false

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            fileListModel.model = RPEditor.getFileTree()
            editorArea.text = ""
            _selectedFilePath = ""
        }

        function onFileTreeChanged(tree) {
            fileListModel.model = tree
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        Label {
            text: "文件浏览器"
            font.pixelSize: 22
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            TextField {
                id: pathField
                Layout.fillWidth: true
                readOnly: true
                placeholderText: "选择文件以查看内容..."
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Button {
                text: "暂存"
                enabled: _selectedFilePath && RPEditor && RPEditor.isPackOpen()
                onClicked: {
                    if (RPEditor) RPEditor.stageFile(_selectedFilePath)
                }
            }

            Button {
                text: "提交"
                highlighted: true
                enabled: _selectedFilePath && RPEditor && RPEditor.isPackOpen()
                onClicked: commitDialog.open()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 6
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor

            RowLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.preferredWidth: 220
                    Layout.fillHeight: true
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor
                    border.width: 1

                    ListView {
                        id: fileListModel
                        anchors.fill: parent
                        clip: true

                        delegate: Item {
                            width: fileListModel.width
                            height: 28

                            property var fileItem: modelData

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 4 + (fileItem.depth || 0) * 12
                                spacing: 4

                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 3
                                    visible: fileItem.gitStatus !== ""
                                    color: {
                                        var s = fileItem.gitStatus
                                        if (s === "A") return "#4CAF50"
                                        if (s === "M") return "#FF9800"
                                        if (s === "D") return "#9E9E9E"
                                        if (s === "U") return "#2196F3"
                                        return "transparent"
                                    }

                                    Label {
                                        anchors.centerIn: parent
                                        text: fileItem.gitStatus
                                        font.pixelSize: 9
                                        font.weight: Font.Bold
                                        color: "#FFFFFF"
                                    }
                                }

                                Label {
                                    text: fileItem.name
                                    font.pixelSize: 11
                                    color: {
                                        if (fileItem.type === "dir") return Theme.currentTheme.colors.accentColor
                                        return Theme.currentTheme.colors.textColor
                                    }
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    if (fileItem.type === "file") {
                                        _selectedFilePath = fileItem.path
                                        pathField.text = fileItem.path
                                        if (RPEditor) {
                                            var content = RPEditor.getFileContent(fileItem.path)
                                            editorArea.text = content
                                            _modified = false
                                        }
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
                        placeholderText: "选择一个文件以编辑..."
                        onTextChanged: {
                            _modified = editorArea.text !== ""
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item { Layout.fillWidth: true }

            Button {
                text: "保存文件"
                highlighted: true
                enabled: _selectedFilePath && _modified && RPEditor && RPEditor.isPackOpen()
                onClicked: {
                    if (RPEditor && _selectedFilePath) {
                        RPEditor.saveFile(_selectedFilePath, editorArea.text)
                        _modified = false
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
            width: parent.width
            spacing: 8

            TextField {
                id: commitMsgInput2
                Layout.fillWidth: true
                placeholderText: "输入提交信息..."
            }
        }

        onAccepted: {
            if (commitMsgInput2.text.trim() && RPEditor) {
                RPEditor.commit(commitMsgInput2.text.trim())
                commitMsgInput2.text = ""
            }
        }
    }
}
