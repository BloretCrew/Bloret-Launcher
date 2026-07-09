import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: texturePage

    property var _textures: []

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshTextures()
        }
    }

    function refreshTextures() {
        if (!RPEditor) return
        _textures = RPEditor.getTextures()
        gridView.model = _textures
        countLabel.text = (Backend ? Backend.tr("共 ") : "共 ") + _textures.length + (Backend ? Backend.tr(" 张贴图") : " 张贴图")
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: (Backend ? Backend.tr("贴图预览") : "贴图预览")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }
            Item { Layout.fillWidth: true }
            Label {
                id: countLabel
                text: (Backend ? Backend.tr("加载中...") : "加载中...")
                color: Theme.currentTheme.colors.textSecondaryColor
                font.pixelSize: 12
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 8
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor

            ScrollView {
                anchors.fill: parent
                clip: true

                GridView {
                    id: gridView
                    cellWidth: 100
                    cellHeight: 110
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        width: 96
                        height: 106
                        radius: 6
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4

                            Rectangle {
                                Layout.preferredWidth: 64
                                Layout.preferredHeight: 64
                                radius: 4
                                color: "#1E1E1E"

                                Image {
                                    anchors.centerIn: parent
                                    width: 56
                                    height: 56
                                    source: {
                                        if (!RPEditor || !RPEditor.isPackOpen()) return ""
                                        var basePath = RPEditor.getPackPath()
                                        if (!basePath) return ""
                                        return "file://" + basePath + "/" + modelData.path
                                    }
                                    fillMode: Image.PreserveAspectFit
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 88
                                text: modelData.name
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideMiddle
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                previewImage.source = "file://" + RPEditor.getPackPath() + "/" + modelData.path
                                previewLabel.text = modelData.path
                                previewDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: previewDialog
        title: (Backend ? Backend.tr("贴图预览") : "贴图预览")
        modal: true
        width: 400
        height: 450
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 4
                color: "#1E1E1E"

                Image {
                    id: previewImage
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 16, implicitWidth)
                    height: Math.min(parent.height - 16, implicitHeight)
                    fillMode: Image.PreserveAspectFit
                }
            }

            Label {
                id: previewLabel
                Layout.fillWidth: true
                font.pixelSize: 11
                font.family: "monospace"
                elide: Text.ElideMiddle
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: (Backend ? Backend.tr("关闭") : "关闭")
                    onClicked: previewDialog.close()
                }
            }
        }
    }
}
