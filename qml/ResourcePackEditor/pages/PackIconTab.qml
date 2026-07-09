import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: packIconPage

    property string _iconPath: ""
    property bool _iconExists: false
    property int _imgWidth: 0
    property int _imgHeight: 0
    property string _fileSize: ""

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshIcon()
        }
    }

    function refreshIcon() {
        if (!RPEditor) return
        _iconPath = RPEditor.getPackPngPath()
        _iconExists = _iconPath !== ""
        if (_iconExists) {
            packImage.source = _iconPath + "?t=" + Date.now()
            _fileSize = _getFileSize(_iconPath)
        } else {
            packImage.source = ""
            _imgWidth = 0
            _imgHeight = 0
            _fileSize = ""
        }
    }

    function _getFileSize(url) {
        if (!url) return ""
        try {
            var xhr = new XMLHttpRequest()
            xhr.open("HEAD", url, false)
            xhr.send()
            var len = xhr.getResponseHeader("Content-Length")
            if (!len) return ""
            var bytes = parseInt(len)
            if (isNaN(bytes)) return ""
            if (bytes < 1024) return bytes + " B"
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
            return (bytes / (1024 * 1024)).toFixed(2) + " MB"
        } catch(e) {
            return ""
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
                text: (Backend ? Backend.tr("资源包图标") : "资源包图标")
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Label {
                text: (Backend ? Backend.tr("pack.png 是资源包在 Minecraft 中显示的图标，建议尺寸为 256x256。") : "pack.png 是资源包在 Minecraft 中显示的图标，建议尺寸为 256x256。")
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: previewCardColumn.implicitHeight + 32
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: previewCardColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            text: (Backend ? Backend.tr("图标预览") : "图标预览")
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            text: (Backend ? Backend.tr("刷新") : "刷新")
                            flat: true
                            onClicked: refreshIcon()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: _iconExists ? Math.max(packImage.sourceSize.height, 128) + 32 : 200
                        radius: 8
                        color: Theme.currentTheme.colors.controlAltSecondaryColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                visible: !_iconExists
                                text: (Backend ? Backend.tr("未设置资源包图标") : "未设置资源包图标")
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                visible: !_iconExists
                                text: (Backend ? Backend.tr("请在资源包根目录放置 pack.png 文件") : "请在资源包根目录放置 pack.png 文件")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                                opacity: 0.7
                            }

                            Image {
                                id: packImage
                                Layout.alignment: Qt.AlignHCenter
                                visible: _iconExists
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                                cache: false
                                sourceSize.width: 256
                                sourceSize.height: 256

                                onStatusChanged: {
                                    if (status === Image.Ready) {
                                        _imgWidth = sourceSize.width
                                        _imgHeight = sourceSize.height
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: infoCardColumn.implicitHeight + 32
                visible: _iconExists
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    id: infoCardColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Label {
                        text: (Backend ? Backend.tr("文件信息") : "文件信息")
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 24

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: (Backend ? Backend.tr("文件路径") : "文件路径")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                Layout.fillWidth: true
                                text: _iconPath ? _iconPath.replace("file://", "") : "-"
                                font.pixelSize: 12
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                                elide: Text.ElideMiddle
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 24

                        ColumnLayout {
                            spacing: 4

                            Label {
                                text: (Backend ? Backend.tr("图像尺寸") : "图像尺寸")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                text: _imgWidth > 0 ? _imgWidth + " x " + _imgHeight + " px" : "-"
                                font.pixelSize: 12
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                            }
                        }

                        ColumnLayout {
                            spacing: 4

                            Label {
                                text: (Backend ? Backend.tr("文件大小") : "文件大小")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                text: _fileSize || "-"
                                font.pixelSize: 12
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                            }
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: refreshIcon()
}
