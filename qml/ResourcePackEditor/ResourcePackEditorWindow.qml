import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1
import RinUI
import "pages"

FluentWindow {
    id: editorWindow
    visible: false
    title: "Bloret 资源包编辑器"
    width: 1200
    height: 800
    minimumWidth: 900
    minimumHeight: 600

    property string currentTab: "overview"
    property string currentFilePath: ""
    property var fileTreeModel: []

    navigationView.navExpandWidth: 0

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            var data = JSON.parse(info.stats)
            fileTreeModel = RPEditor.getFileTree()
            statsLabel.text = "文件: " + data.files + " | 贴图: " + data.textures + " | 语言: " + data.languages
            tabBar.enabled = true
        }

        function onFileTreeChanged(tree) {
            fileTreeModel = tree
        }

        function onStatusMessage(type, msg) {
            statusBarText.text = msg
        }

        function onErrorOccurred(msg) {
            statusBarText.text = "⚠ " + msg
            statusBarText.color = "#F44336"
            errorTimer.start()
        }
    }

    Component.onCompleted: {
        if (RPEditor && !RPEditor.isPackOpen()) {
            folderDialog.open()
        }
    }

    FolderDialog {
        id: folderDialog
        title: "选择资源包文件夹或压缩包"
        onAccepted: {
            if (folderDialog.folder) {
                var pathStr = folderDialog.folder.toString()
                if (pathStr.startsWith("file://")) {
                    pathStr = pathStr.slice(7)
                }
                pathStr = decodeURIComponent(pathStr)
                RPEditor.openPack(pathStr)
            } else {
                editorWindow.close()
            }
        }
        onRejected: {
            editorWindow.close()
        }
    }

    Item {
        anchors.fill: parent

        RowLayout {
            anchors.fill: parent
            spacing: 0

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                    Layout.topMargin: 8
                    spacing: 8

                    Segmented {
                        id: tabBar
                        enabled: false
                        Layout.fillWidth: true

                        SegmentedItem { text: "概览" }
                        SegmentedItem { text: "pack.mcmeta" }
                        SegmentedItem { text: "语言" }
                        SegmentedItem { text: "贴图" }
                        SegmentedItem { text: "文件" }
                        SegmentedItem { text: "Agent" }
                    }

                    Label {
                        id: statsLabel
                        font.pixelSize: 12
                        color: Theme.currentTheme.colors.textSecondaryColor
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                StackLayout {
                    id: tabContent
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 8
                    currentIndex: tabBar.currentIndex

                    OverviewTab {}
                    McmetaTab {}
                    LanguageTab {}
                    TextureTab {}
                    FileBrowserTab {}
                    AgentTab {}
                }
            }

            Rectangle {
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 36
                        color: Theme.currentTheme.colors.cardColor

                        Label {
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.verticalCenter: parent.verticalCenter
                            text: "文件列表"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.currentTheme.colors.controlBorderColor
                    }

                    FileTreeSidebar {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: fileTreeModel

                        onFileSelected: function(filePath) {
                            currentFilePath = filePath
                        }
                    }
                }
            }
        }

        Label {
            id: statusBarText
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            anchors.bottomMargin: 4
            height: 24
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 11
            color: Theme.currentTheme.colors.textSecondaryColor
        }
    }

    Timer {
        id: errorTimer
        interval: 5000
        onTriggered: {
            statusBarText.color = Theme.currentTheme.colors.textSecondaryColor
        }
    }
}
