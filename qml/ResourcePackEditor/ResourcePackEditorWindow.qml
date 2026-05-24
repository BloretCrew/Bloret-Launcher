import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1
import RinUI
import "pages"

FluentWindowBase {
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
    property string pendingPackPath: ""

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.topMargin: 4
            spacing: 2

            Repeater {
                model: ["概览", "pack.mcmeta", "pack.png", "语言", "贴图", "方块状态", "模型", "声音", "字体", "文本", "粒子", "特殊文件", "OptiFine", "文件", "Git", "Agent"]

                Button {
                    text: modelData
                    flat: true
                    highlighted: currentTabIndex === index
                    onClicked: currentTabIndex = index
                }
            }

            Item { Layout.fillWidth: true }

            Label {
                id: statsLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                verticalAlignment: Text.AlignVCenter
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4

            RowLayout {
                anchors.fill: parent
                spacing: 0

                StackLayout {
                    id: tabContent
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: currentTabIndex

                    OverviewTab {}
                    McmetaTab {}
                    PackIconTab {}
                    LanguageTab {}
                    TextureTab {}
                    BlockstatesTab {}
                    ModelsTab {}
                    SoundsTab {}
                    FontsTab {}
                    TextsTab {}
                    ParticlesTab {}
                    SpecialFilesTab {}
                    OptifineTab {}
                    FileBrowserTab {}
                    GitTab {}
                    AgentTab {}
                }

                Rectangle {
                    id: sidebar
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
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 24
            color: "transparent"

            Label {
                id: statusBarText
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 11
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }

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
                statusBarText.color = Theme.currentTheme.colors.textSecondaryColor
            }

            function onErrorOccurred(msg) {
                statusBarText.text = "⚠ " + msg
                statusBarText.color = "#F44336"
                errorTimer.start()
            }

            function onPackMissingStructure(path) {
                pendingPackPath = path
                createStructureTimer.start()
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

        Dialog {
            id: createStructureDialog
            title: "创建资源包"
            modal: true
            width: 480
            closePolicy: Popup.CloseOnEscape

            ColumnLayout {
                width: parent.width
                spacing: 12

                Label {
                    text: "该目录不是有效的 Minecraft 资源包。"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    text: "是否自动创建基础资源包结构？\n\n将生成：\n  • pack.mcmeta（资源包元数据）\n  • assets/minecraft/（标准命名空间）\n  • assets/minecraft/lang/en_us.json（语言文件）\n  • assets/minecraft/textures/（贴图目录）\n  • assets/minecraft/models/（模型目录）"
                    font.pixelSize: 12
                    lineHeight: 1.5
                    wrapMode: Text.Wrap
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "取消"
                        flat: true
                        onClicked: createStructureDialog.reject()
                    }

                    Button {
                        text: "创建"
                        onClicked: createStructureDialog.accept()
                    }
                }
            }

            onAccepted: {
                if (pendingPackPath && RPEditor) {
                    RPEditor.createBasicStructure(pendingPackPath)
                }
            }
            onRejected: {
                editorWindow.close()
            }
        }

        Timer {
            id: createStructureTimer
            interval: 0
            repeat: false
            onTriggered: {
                createStructureDialog.open()
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
}
