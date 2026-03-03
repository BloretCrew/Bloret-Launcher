import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: pluginsPage
    title: qsTr("插件")

    property var pluginList: []
    property string pluginRoot: ""
    property string pendingUninstallName: ""
    property string pendingUninstallDisplay: ""

    Component.onCompleted: {
        refreshPlugins()
    }

    function refreshPlugins() {
        if (!Backend) return
        pluginList = Backend.getInstalledPlugins()
        pluginRoot = Backend.getPluginRoot()
    }

    function showStatus(titleText, messageText, severityValue) {
        statusBar.title = titleText
        statusBar.text = messageText
        statusBar.severity = severityValue
        statusBar.visible = true
        statusTimer.restart()
    }

    Timer {
        id: statusTimer
        interval: 3000
        onTriggered: statusBar.visible = false
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        InfoBar {
            id: statusBar
            Layout.fillWidth: true
            visible: false
        }

        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 15

                Image {
                    source: "../../icon/Grass_Block.png"
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        font.weight: Font.DemiBold
                        font.pixelSize: 16
                        text: qsTr("已安装的插件")
                        color: Theme.currentTheme.colors.textColor
                    }
                    Label {
                        text: qsTr("管理已安装插件，查看信息或卸载")
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                }

                Button {
                    text: qsTr("刷新")
                    onClicked: refreshPlugins()
                }

                Button {
                    text: qsTr("打开插件目录")
                    onClicked: { if (Backend) Backend.openPluginRoot() }
                }
            }
        }

        ListView {
            id: pluginListView
            Layout.fillWidth: true
            implicitHeight: contentHeight
            interactive: false
            spacing: 10
            model: pluginsPage.pluginList
            clip: true

            delegate: Frame {
                width: ListView.view.width
                padding: 12
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }

                RowLayout {
                    width: parent.width
                    spacing: 15

                    Rectangle {
                        Layout.preferredWidth: 48
                        Layout.preferredHeight: 48
                        radius: 8
                        color: Theme.currentTheme.colors.controlFillSecondaryColor
                        clip: true

                        Image {
                            anchors.fill: parent
                            source: modelData.icon || ""
                            fillMode: Image.PreserveAspectFit
                            visible: modelData.icon && modelData.icon !== ""
                        }

                        Label {
                            anchors.centerIn: parent
                            text: "Plugin"
                            font.pixelSize: 10
                            color: Theme.currentTheme.colors.textTertialyColor
                            visible: !modelData.icon || modelData.icon === ""
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                font.weight: Font.DemiBold
                                font.pixelSize: 16
                                text: modelData.name || qsTr("未命名插件")
                                color: Theme.currentTheme.colors.textColor
                            }

                            Label {
                                text: modelData.version ? ("v" + modelData.version) : qsTr("v未知")
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                                Layout.alignment: Qt.AlignBaseline
                            }
                        }

                        Label {
                            text: modelData.author ? (qsTr("作者: ") + modelData.author) : qsTr("作者: 未知")
                            color: Theme.currentTheme.colors.textSecondaryColor
                            font.pixelSize: 12
                        }

                        Label {
                            text: modelData.description || qsTr("暂无插件描述")
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        spacing: 8

                        Button {
                            text: qsTr("主页")
                            visible: modelData.url && modelData.url !== ""
                            onClicked: { if (Backend) Backend.openUrl(modelData.url) }
                        }

                        Button {
                            text: qsTr("打开文件夹")
                            onClicked: { if (Backend) Backend.openPluginFolder(modelData.folderName) }
                        }

                        Button {
                            text: qsTr("卸载")
                            highlighted: true
                            onClicked: {
                                pendingUninstallName = modelData.folderName
                                pendingUninstallDisplay = modelData.name || modelData.folderName
                                uninstallDialog.open()
                            }
                        }
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                text: qsTr("暂无插件")
                color: Theme.currentTheme.colors.textTertialyColor
                visible: pluginListView.count === 0
            }
        }
    }

    Dialog {
        id: uninstallDialog
        title: qsTr("卸载插件")
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            spacing: 8
            Label {
                text: qsTr("确认卸载插件：") + pendingUninstallDisplay + qsTr("？")
                wrapMode: Text.Wrap
            }
            Label {
                text: qsTr("卸载后会删除插件文件，并移除相关启动项。")
                color: Theme.currentTheme.colors.textSecondaryColor
                wrapMode: Text.Wrap
            }
        }

        onAccepted: {
            if (Backend) {
                let result = Backend.uninstallPlugin(pendingUninstallName)
                if (result && result.success) {
                    showStatus(qsTr("卸载成功"), result.message || qsTr("插件已卸载"), Severity.Success)
                } else {
                    let msg = result && result.message ? result.message : qsTr("卸载失败")
                    showStatus(qsTr("卸载失败"), msg, Severity.Error)
                }
                refreshPlugins()
            }
        }
    }
}
