import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: modsPage
    title: qsTr("Mods")

    RowLayout {
        Layout.fillWidth: true
        Label {
            font.pixelSize: 24
            font.weight: Font.DemiBold
            text: qsTr("Mods")
            Layout.fillWidth: true
            visible: false // Hidden because FluentPage title is enough
        }
        Button {
            text: qsTr("打开 Modrinth")
            onClicked: Backend.openModrinth()
        }
    }

    // --- Bloriko AI Mod Suggestion ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                spacing: 15
                
                Image {
                    source: "../../icon/Bloriko.jpg"
                    sourceSize { width: 35; height: 35 }
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        font.weight: Font.DemiBold
                        text: qsTr("让络可帮你挑选合适的 Mod")
                    }
                    Label {
                        text: qsTr("无需一个一个找 Mod，让 Bloriko 帮你找齐。")
                        color: "#7f7f7f"
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                TextField {
                    id: askBlorikoInput
                    Layout.fillWidth: true
                    placeholderText: qsTr("告诉 Bloriko 你的需求，让 Bloriko 帮你挑选一批适合你的 Mod")
                }

                CheckBox {
                    id: deepThinkCheck
                    text: qsTr("深度思考")
                }

                Button {
                    text: qsTr("发送")
                    highlighted: true
                    onClicked: Backend.askBlorikoForMods(askBlorikoInput.text, deepThinkCheck.checked)
                }
            }
        }
    }

    Label {
        text: qsTr("Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。")
        color: "#7f7f7f"
        font.pixelSize: 12
    }

    // --- Modrinth Search Section ---
    TextField {
        id: modSearchInput
        Layout.fillWidth: true
        placeholderText: qsTr("在 Modrinth 上搜索")
        onAccepted: Backend.searchModrinth(modSearchInput.text)
    }

    // Mod List Placeholder
    // In a real implementation this would bound to a QAbstractListModel
    ListView {
        id: modListView
        Layout.fillWidth: true
        Layout.minimumHeight: 300
        model: Backend.getMockModList()
        delegate: Frame {
            width: ListView.view.width
            padding: 10
            background: Rectangle {
                color: Theme.currentTheme.colors.controlColorDefault
                radius: 8
                border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
            }
            RowLayout {
                width: parent.width
                spacing: 15
                Rectangle {
                    width: 50; height: 50
                    color: "#dddddd"
                    radius: 4
                    Label { text: "Icon"; anchors.centerIn: parent }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: modelData.name }
                    Label { text: modelData.description; color: "#7f7f7f" }
                }
                Button {
                    text: qsTr("下载")
                    onClicked: Backend.downloadMod(modelData.id)
                }
            }
        }
    }
}
