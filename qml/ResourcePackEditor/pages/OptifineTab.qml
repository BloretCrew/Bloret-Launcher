import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: optifinePage

    property var _cemFiles: []
    property var _citFiles: []
    property int _activeTab: 0
    property string _selectedFilePath: ""
    property string _selectedFileName: ""
    property string _fileContent: ""

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshData()
        }
    }

    function refreshData() {
        if (!RPEditor) return
        _cemFiles = RPEditor.getOptifineCem()
        _citFiles = RPEditor.getOptifineCit()
        cemList.model = _cemFiles
        citList.model = _citFiles
    }

    function openFile(path, name) {
        if (!RPEditor) return
        _selectedFilePath = path
        _selectedFileName = name
        var isPng = path.endsWith(".png")
        if (isPng) {
            fileContentArea.text = Backend ? Backend.tr("二进制文件") : "二进制文件"
        } else {
            fileContentArea.text = RPEditor.getFileContent(path)
        }
        fileViewDialog.open()
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentHeight: rootColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: rootColumn
            width: parent.width
            spacing: 16

            Label {
                text: (Backend ? Backend.tr("OptiFine 资源") : "OptiFine 资源")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 2

                Button {
                    text: "CEM"
                    flat: true
                    highlighted: _activeTab === 0
                    onClicked: _activeTab = 0
                }

                Button {
                    text: "CIT"
                    flat: true
                    highlighted: _activeTab === 1
                    onClicked: _activeTab = 1
                }
            }

            Rectangle {
                Layout.fillWidth: true
                visible: _cemFiles.length === 0 && _citFiles.length === 0
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor
                Layout.preferredHeight: emptyColumn.implicitHeight + 48

                ColumnLayout {
                    id: emptyColumn
                    anchors.centerIn: parent
                    width: parent.width - 32
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        text: (Backend ? Backend.tr("当前资源包没有 OptiFine 资源文件") : "当前资源包没有 OptiFine 资源文件")
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Label {
                        Layout.fillWidth: true
                        text: (Backend ? Backend.tr("CEM (.jem/.jpm) 用于自定义实体模型和动画\nCIT (.properties) 用于自定义纹理条件配置") : "CEM (.jem/.jpm) 用于自定义实体模型和动画\nCIT (.properties) 用于自定义纹理条件配置")
                        font.pixelSize: 12
                        lineHeight: 1.6
                        color: Theme.currentTheme.colors.textSecondaryColor
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: _activeTab === 0 && _cemFiles.length > 0
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ListView {
                    id: cemList
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    spacing: 2

                    delegate: Rectangle {
                        width: cemList.width
                        height: 40
                        radius: 4
                        color: mouseArea.containsMouse ? Theme.currentTheme.colors.controlAltSecondaryColor : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 8

                            Rectangle {
                                width: 24
                                height: 18
                                radius: 4
                                color: modelData.kind === "jem" ? "#2196F3" : "#FF9800"

                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.kind.toUpperCase()
                                    font.pixelSize: 9
                                    font.weight: Font.Bold
                                    color: "#FFFFFF"
                                }
                            }

                            Label {
                                text: modelData.name
                                font.pixelSize: 12
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Label {
                                text: modelData.namespace
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: openFile(modelData.path, modelData.name)
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: _activeTab === 1 && _citFiles.length > 0
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ListView {
                    id: citList
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    spacing: 2

                    delegate: Rectangle {
                        width: citList.width
                        height: 40
                        radius: 4
                        color: citMouse.containsMouse ? Theme.currentTheme.colors.controlAltSecondaryColor : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 8

                            Rectangle {
                                width: 24
                                height: 18
                                radius: 4
                                color: {
                                    if (modelData.type === "properties") return "#4CAF50"
                                    return "#9C27B0"
                                }

                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.type === "properties" ? "PRO" : "IMG"
                                    font.pixelSize: 9
                                    font.weight: Font.Bold
                                    color: "#FFFFFF"
                                }
                            }

                            Label {
                                text: modelData.name
                                font.pixelSize: 12
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Label {
                                text: modelData.namespace
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        MouseArea {
                            id: citMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: openFile(modelData.path, modelData.name)
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: fileViewDialog
        title: _selectedFileName
        modal: true
        width: 600
        height: 500
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: _selectedFilePath
                font.pixelSize: 11
                font.family: "monospace"
                color: Theme.currentTheme.colors.textSecondaryColor
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 4
                color: Theme.currentTheme.colors.controlAltSecondaryColor

                Flickable {
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    contentHeight: fileContentArea.height

                    TextArea {
                        id: fileContentArea
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

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: (Backend ? Backend.tr("关闭") : "关闭")
                    onClicked: fileViewDialog.close()
                }
            }
        }
    }
}
