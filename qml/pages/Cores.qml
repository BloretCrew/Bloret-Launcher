import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"
import "../components"

FluentPage {
    id: coresPage
    title: Backend ? Backend.tr("核心") : "核心"

    property var launchItems: []

    Component.onCompleted: {
        refreshLaunchItems()
    }

    function refreshLaunchItems() {
        launchItems = Backend ? Backend.getLaunchItemsSortedByPlayTime() : []
    }

    content: ColumnLayout {
        spacing: 10

        PluginPanelHost {
            area: "cores"
            Layout.fillWidth: true
        }

        Label {
            text: Backend ? Backend.tr("右键单击启动项可进行管理。") : "右键单击启动项可进行管理。"
            color: Theme.currentTheme.colors.textSecondaryColor
            font.pixelSize: 12
        }

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: scrollView.width - 20
                spacing: 10

                Repeater {
                    model: launchItems

                    Rectangle {
                        id: card
                        Layout.fillWidth: true
                        height: 60
                        radius: 8
                        color: mouseArea.containsMouse ? Theme.currentTheme.colors.subtleFillColorSecondary : Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.cardBorderColor

                        property var itemData: modelData
                        property bool isHovered: mouseArea.containsMouse

                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.RightButton

                            onClicked: function(mouse) {
                                if (mouse.button === Qt.RightButton) {
                                    contextMenu.popup()
                                }
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 15
                            anchors.rightMargin: 15
                            spacing: 15

                            Image {
                                source: itemData.icon || "../../icon/Grass_Block.png"
                                sourceSize { width: 32; height: 32 }
                                fillMode: Image.PreserveAspectFit
                            }

                            Label {
                                text: itemData.name
                                font.weight: Font.DemiBold
                                font.pixelSize: 14
                                color: Theme.currentTheme.colors.textColor
                                Layout.fillWidth: true
                            }

                            Label {
                                text: itemData.type === "minecraft" ? "Minecraft" : (Backend ? Backend.tr("自定义") : "自定义")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                visible: itemData.playTimeFormatted && itemData.playTimeFormatted !== ""
                                text: itemData.playTimeFormatted
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textTertialyColor
                            }

                            Button {
                                icon.name: "ic_fluent_settings_20_regular"
                                flat: true
                                Layout.preferredWidth: 36
                                Layout.preferredHeight: 36
                                ToolTip.visible: hovered
                                ToolTip.text: Backend ? Backend.tr("核心管理") : "核心管理"
                                visible: itemData.type === "minecraft"
                                onClicked: {
                                    if (Backend) Backend.showCoreManager(itemData.name)
                                }
                            }
                        }

                        Menu {
                            id: contextMenu

                            MenuItem {
                                text: Backend ? Backend.tr("启动") : "启动"
                                icon.name: "ic_fluent_play_20_regular"
                                onTriggered: {
                                    if (Backend) Backend.launchGame(itemData.name)
                                }
                            }

                            MenuSeparator {
                                visible: itemData.type === "minecraft"
                            }

                            MenuItem {
                                id: coreManageItem
                                text: Backend ? Backend.tr("核心管理") : "核心管理"
                                icon.name: "ic_fluent_settings_20_regular"
                                visible: itemData.type === "minecraft"
                                onTriggered: {
                                    if (Backend) Backend.showCoreManager(itemData.name)
                                }
                            }

                            MenuItem {
                                id: exportMrpackItem
                                text: Backend ? Backend.tr("导出为 Modrinth 整合包") : "导出为 Modrinth 整合包"
                                icon.name: "ic_fluent_arrow_export_20_regular"
                                visible: itemData.type === "minecraft"
                                onTriggered: {
                                    if (Backend) Backend.showMrpackExport(itemData.name)
                                }
                            }

                            MenuItem {
                                id: openFolderItem
                                text: Backend ? Backend.tr("打开文件位置") : "打开文件位置"
                                icon.name: "ic_fluent_folder_20_regular"
                                visible: itemData.type === "minecraft"
                                onTriggered: {
                                    if (Backend) Backend.openVersionFolder(itemData.name)
                                }
                            }

                            MenuSeparator {
                                visible: itemData.type === "custom"
                            }

                            MenuItem {
                                id: renameItem
                                text: Backend ? Backend.tr("更名") : "更名"
                                icon.name: "ic_fluent_edit_20_regular"
                                visible: itemData.type === "custom"
                                onTriggered: {
                                    console.log("Rename item: " + itemData.name)
                                }
                            }

                            MenuItem {
                                id: deleteItem
                                text: Backend ? Backend.tr("删除") : "删除"
                                icon.name: "ic_fluent_delete_20_regular"
                                visible: itemData.type === "custom"
                                onTriggered: {
                                    if (Backend) Backend.deleteCustomItem(itemData.name)
                                    refreshLaunchItems()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
