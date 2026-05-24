import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import RinUI 1.0

Flickable {
    id: root

    contentHeight: mainLayout.height
    clip: true
    flickableDirection: Flickable.VerticalFlick

    property var models: []
    property var filteredModels: []
    property string selectedPath: ""
    property string fileContent: ""
    property string currentFilter: "all"

    Component.onCompleted: loadModels()

    function loadModels() {
        models = RPEditor.getModels()
        applyFilter()
    }

    function applyFilter() {
        if (currentFilter === "all") {
            filteredModels = models
        } else {
            filteredModels = models.filter(function(m) {
                return m.kind === currentFilter
            })
        }
    }

    function openModel(path) {
        selectedPath = path
        fileContent = RPEditor.getFileContent(path)
    }

    function saveModel() {
        if (selectedPath !== "") {
            RPEditor.saveFile(selectedPath, fileContent)
        }
    }

    function kindBadgeColor(kind) {
        if (kind === "block") return "#3B82F6"
        if (kind === "item") return "#F97316"
        return "#6B7280"
    }

    function kindBadgeText(kind) {
        if (kind === "block") return "方块"
        if (kind === "item") return "物品"
        return kind
    }

    ColumnLayout {
        id: mainLayout
        width: parent.width
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 48
            color: Theme.currentTheme.colors.cardColor

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 8

                Repeater {
                    model: ListModel {
                        ListElement { label: "全部"; filter: "all" }
                        ListElement { label: "方块模型"; filter: "block" }
                        ListElement { label: "物品模型"; filter: "item" }
                    }

                    delegate: Rectangle {
                        Layout.preferredWidth: filterLabel.implicitWidth + 24
                        Layout.fillHeight: true
                        radius: 6
                        color: currentFilter === model.filter ? Theme.currentTheme.colors.controlAltSecondaryColor : "transparent"

                        border.width: 1
                        border.color: currentFilter === model.filter ? Theme.currentTheme.colors.controlBorderColor : "transparent"

                        Text {
                            id: filterLabel
                            anchors.centerIn: parent
                            text: model.label
                            font.pixelSize: 13
                            color: currentFilter === model.filter ? Theme.currentTheme.colors.textColor : Theme.currentTheme.colors.textSecondaryColor
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                currentFilter = model.filter
                                applyFilter()
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: filteredModels.length + " 个模型"
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: 600
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                color: Theme.currentTheme.colors.cardColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    ListView {
                        id: modelList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: filteredModels
                        spacing: 2

                        delegate: Rectangle {
                            width: modelList.width
                            height: 52
                            radius: 6
                            color: selectedPath === modelData.path ? Theme.currentTheme.colors.controlAltSecondaryColor : "transparent"

                            border.width: selectedPath === modelData.path ? 1 : 0
                            border.color: Theme.currentTheme.colors.controlBorderColor

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 2

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Rectangle {
                                        Layout.preferredWidth: kindLabel.implicitWidth + 12
                                        Layout.preferredHeight: 18
                                        radius: 4
                                        color: Qt.rgba(
                                            Qt.colorEqual(kindBadgeColor(modelData.kind), "#3B82F6") ? 0.23 : (Qt.colorEqual(kindBadgeColor(modelData.kind), "#F97316") ? 0.98 : 0.42),
                                            Qt.colorEqual(kindBadgeColor(modelData.kind), "#3B82F6") ? 0.51 : (Qt.colorEqual(kindBadgeColor(modelData.kind), "#F97316") ? 0.45 : 0.47),
                                            Qt.colorEqual(kindBadgeColor(modelData.kind), "#3B82F6") ? 0.96 : (Qt.colorEqual(kindBadgeColor(modelData.kind), "#F97316") ? 0.09 : 0.50),
                                            0.2
                                        )

                                        Text {
                                            id: kindLabel
                                            anchors.centerIn: parent
                                            text: kindBadgeText(modelData.kind)
                                            font.pixelSize: 10
                                            font.bold: true
                                            color: kindBadgeColor(modelData.kind)
                                        }
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.name
                                        font.pixelSize: 13
                                        font.bold: true
                                        color: Theme.currentTheme.colors.textColor
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.namespace
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                    elide: Text.ElideRight
                                    maximumLineCount: 1
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: openModel(modelData.path)
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.currentTheme.colors.cardColor

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        height: 44
                        color: Theme.currentTheme.colors.controlAltSecondaryColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 12

                            Text {
                                text: selectedPath !== "" ? selectedPath : "未选择模型"
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                                Layout.fillWidth: true
                                elide: Text.ElideMiddle
                            }

                            Rectangle {
                                Layout.preferredWidth: saveBtn.implicitWidth + 24
                                Layout.preferredHeight: 30
                                radius: 6
                                color: selectedPath !== "" ? "#3B82F6" : Theme.currentTheme.colors.controlAltSecondaryColor
                                border.width: 1
                                border.color: selectedPath !== "" ? "#3B82F6" : Theme.currentTheme.colors.controlBorderColor

                                Text {
                                    id: saveBtn
                                    anchors.centerIn: parent
                                    text: "保存"
                                    font.pixelSize: 13
                                    color: selectedPath !== "" ? "#FFFFFF" : Theme.currentTheme.colors.textSecondaryColor
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: selectedPath !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: {
                                        if (selectedPath !== "") {
                                            saveModel()
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.currentTheme.colors.controlBorderColor
                    }

                    TextArea {
                        id: jsonEditor
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: fileContent
                        font.family: "Menlo, Consolas, monospace"
                        font.pixelSize: 13
                        color: Theme.currentTheme.colors.textColor
                        selectionColor: Qt.rgba(0.23, 0.51, 0.96, 0.3)
                        wrapMode: TextArea.NoWrap
                        selectByMouse: true
                        background: Rectangle {
                            color: Theme.currentTheme.colors.cardColor
                        }

                        onTextChanged: {
                            fileContent = text
                        }
                    }
                }
            }
        }
    }
}
