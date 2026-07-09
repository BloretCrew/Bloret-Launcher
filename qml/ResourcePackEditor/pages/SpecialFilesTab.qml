import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: specialFilesPage

    property var _files: []
    property string _currentPath: ""
    property string _currentName: ""

    property var _fileDescriptions: ({
        "regional_compliancies.json": (Backend ? Backend.tr("按地区控制定时弹窗与提示") : "按地区控制定时弹窗与提示"),
        "gpu_warnlist.json": (Backend ? Backend.tr("GPU/渲染器警告列表") : "GPU/渲染器警告列表"),
        "deprecated.json": (Backend ? Backend.tr("标记本版本中弃用或重命名的翻译键") : "标记本版本中弃用或重命名的翻译键")
    })

    property var _fileExplanations: ({
        "regional_compliancies.json": (Backend ? Backend.tr("该文件允许你按地区/语言配置定时弹窗提示和合规性提醒。适用于需要在不同地区展示不同法律或通知信息的资源包。") : "该文件允许你按地区/语言配置定时弹窗提示和合规性提醒。适用于需要在不同地区展示不同法律或通知信息的资源包。"),
        "gpu_warnlist.json": (Backend ? Backend.tr("该文件定义了 GPU 或渲染器的兼容性警告列表。当玩家使用被标记的硬件时，游戏会显示相应的警告信息。") : "该文件定义了 GPU 或渲染器的兼容性警告列表。当玩家使用被标记的硬件时，游戏会显示相应的警告信息。"),
        "deprecated.json": (Backend ? Backend.tr("该文件记录了当前版本中已被弃用或重命名的翻译键，方便维护者追踪需要更新的内容。") : "该文件记录了当前版本中已被弃用或重命名的翻译键，方便维护者追踪需要更新的内容。")
    })

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshFiles()
        }
    }

    function refreshFiles() {
        if (!RPEditor) return
        _files = RPEditor.getSpecialFiles()
        fileList.model = _files

        if (_files.length > 0) {
            fileList.currentIndex = 0
            selectFile(0)
        } else {
            _currentPath = ""
            _currentName = ""
            fileEditor.text = ""
            pathLabel.text = ""
            emptyState.visible = true
            editorCard.visible = false
        }
    }

    function selectFile(index) {
        if (index < 0 || index >= _files.length) return
        var file = _files[index]
        _currentPath = file.path
        _currentName = file.name
        pathLabel.text = file.path

        var desc = _fileDescriptions[file.name] || ""
        descLabel.text = desc

        var explanation = _fileExplanations[file.name] || ""
        explanationLabel.text = explanation
        explanationCard.visible = explanation !== ""

        if (RPEditor) {
            var content = RPEditor.getFileContent(file.path)
            fileEditor.text = content || ""
        }

        emptyState.visible = false
        editorCard.visible = true
    }

    function saveCurrentFile() {
        if (!RPEditor || !_currentPath) return
        var ok = RPEditor.saveFile(_currentPath, fileEditor.text)
        if (ok) {
            saveToast.visible = true
            saveToastTimer.restart()
        }
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
                text: (Backend ? Backend.tr("特殊配置文件") : "特殊配置文件")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Label {
                text: (Backend ? Backend.tr("管理资源包中的特殊配置文件，如地区合规设置、GPU 警告列表、弃用翻译键等。") : "管理资源包中的特殊配置文件，如地区合规设置、GPU 警告列表、弃用翻译键等。")
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    Layout.preferredWidth: 200
                    Layout.fillHeight: true
                    implicitHeight: fileListCard.implicitHeight + 32
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: fileListCard
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        Label {
                            text: (Backend ? Backend.tr("文件列表") : "文件列表")
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        Label {
                            text: (Backend ? Backend.tr("共 ") : "共 ") + _files.length + " 个文件"
                            font.pixelSize: 11
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }

                        ListView {
                            id: fileList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            delegate: Rectangle {
                                width: fileList.width
                                height: 52
                                color: ListView.isCurrentItem ? (Theme.accentColor || "#0078D4") : "transparent"
                                radius: 4

                                ColumnLayout {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.margins: 8
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
                                        text: {
                                            var desc = _fileDescriptions[modelData.name]
                                            return desc || modelData.path
                                        }
                                        font.pixelSize: 10
                                        color: ListView.isCurrentItem ? "#CCFFFFFF" : Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        fileList.currentIndex = index
                                        selectFile(index)
                                    }
                                }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 12

                    Rectangle {
                        id: emptyState
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 8
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        visible: _files.length === 0

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 8

                            Label {
                                text: (Backend ? Backend.tr("当前资源包没有特殊配置文件") : "当前资源包没有特殊配置文件")
                                font.pixelSize: 14
                                font.weight: Font.Medium
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.alignment: Qt.AlignHCenter
                            }

                            Label {
                                text: (Backend ? Backend.tr("特殊配置文件包括 regional_compliancies.json、gpu_warnlist.json 等") : "特殊配置文件包括 regional_compliancies.json、gpu_warnlist.json 等")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }

                    Rectangle {
                        id: editorCard
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 8
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        visible: false

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Label {
                                        text: _currentName || (Backend ? Backend.tr("选择一个文件") : "选择一个文件")
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                        color: Theme.currentTheme.colors.textColor
                                    }

                                    RowLayout {
                                        spacing: 6

                                        Label {
                                            text: (Backend ? Backend.tr("路径:") : "路径:")
                                            font.pixelSize: 11
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                        }

                                        Label {
                                            id: pathLabel
                                            text: ""
                                            font.pixelSize: 11
                                            font.family: "monospace"
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            elide: Text.ElideMiddle
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                Button {
                                    text: (Backend ? Backend.tr("保存") : "保存")
                                    highlighted: true
                                    enabled: _currentPath !== ""
                                    onClicked: saveCurrentFile()
                                }
                            }

                            Rectangle {
                                id: explanationCard
                                Layout.fillWidth: true
                                implicitHeight: explanationColumn.implicitHeight + 24
                                radius: 6
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                border.color: Theme.currentTheme.colors.controlBorderColor
                                visible: false

                                ColumnLayout {
                                    id: explanationColumn
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 4

                                    Label {
                                        text: _currentName || ""
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        color: Theme.currentTheme.colors.textColor
                                    }

                                    Label {
                                        id: descLabel
                                        text: ""
                                        font.pixelSize: 11
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                    }

                                    Label {
                                        id: explanationLabel
                                        text: ""
                                        font.pixelSize: 11
                                        wrapMode: Text.Wrap
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 4
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                border.color: Theme.currentTheme.colors.controlBorderColor

                                ScrollView {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    clip: true

                                    TextArea {
                                        id: fileEditor
                                        width: parent.width
                                        font.family: "monospace"
                                        font.pixelSize: 12
                                        color: Theme.currentTheme.colors.textColor
                                        wrapMode: Text.NoWrap
                                        selectByMouse: true
                                        background: null
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: saveToast
        visible: false
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        width: saveToastLabel.implicitWidth + 32
        height: 36
        radius: 18
        color: "#4CAF50"

        Label {
            id: saveToastLabel
            anchors.centerIn: parent
            text: (Backend ? Backend.tr("已保存") : "已保存")
            font.pixelSize: 12
            color: "#FFFFFF"
        }

        Timer {
            id: saveToastTimer
            interval: 2000
            onTriggered: saveToast.visible = false
        }
    }
}
