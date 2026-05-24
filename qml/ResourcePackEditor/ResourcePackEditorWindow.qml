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

    property string currentFilePath: ""
    property var fileTreeModel: []
    property int currentTabIndex: 0

    navigationView.navExpandWidth: 0
    navigationItems: []

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            var data = JSON.parse(info.stats)
            fileTreeModel = RPEditor.getFileTree()
            statsLabel.text = "文件: " + data.files + " | 贴图: " + data.textures + " | 语言: " + data.languages
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

        Rectangle {
            id: sidebar
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
            width: 280
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    color: "transparent"

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
                    onFileSelected: function(fp) { currentFilePath = fp }
                }
            }
        }

        ColumnLayout {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: sidebar.left
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 28
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.topMargin: 8
                spacing: 8

                Button {
                    id: tab0
                    text: "概览"
                    flat: true
                    highlighted: currentTabIndex === 0
                    onClicked: currentTabIndex = 0
                }
                Button {
                    id: tab1
                    text: "pack.mcmeta"
                    flat: true
                    highlighted: currentTabIndex === 1
                    onClicked: currentTabIndex = 1
                }
                Button {
                    id: tab2
                    text: "语言"
                    flat: true
                    highlighted: currentTabIndex === 2
                    onClicked: currentTabIndex = 2
                }
                Button {
                    id: tab3
                    text: "贴图"
                    flat: true
                    highlighted: currentTabIndex === 3
                    onClicked: currentTabIndex = 3
                }
                Button {
                    id: tab4
                    text: "文件"
                    flat: true
                    highlighted: currentTabIndex === 4
                    onClicked: currentTabIndex = 4
                }
                Button {
                    id: tab5
                    text: "Agent"
                    flat: true
                    highlighted: currentTabIndex === 5
                    onClicked: currentTabIndex = 5
                }

                Item { Layout.fillWidth: true }

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
                currentIndex: currentTabIndex

                OverviewTab {}
                McmetaTab {}
                LanguageTab {}
                TextureTab {}
                FileBrowserTab {}
                AgentTab {}
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: sidebar.left
            anchors.bottom: parent.bottom
            height: 28
            color: "transparent"

            Label {
                id: statusBarText
                anchors.fill: parent
                anchors.leftMargin: 16
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 11
                color: Theme.currentTheme.colors.textSecondaryColor
            }
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
