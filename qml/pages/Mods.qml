import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: modsPage
    title: qsTr("Mods")

    property var modResults: []
    property string blorikoStatus: ""

    Connections {
        target: Backend
        function onModrinthResultsReceived(results) {
            modResults = results
        }
        function onBlorikoResponseReceived(response) {
            blorikoStatus = response
            blorikoDialog.text = response
            blorikoDialog.open()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // --- Header ---
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("打开 Modrinth")
                onClicked: { if (Backend) Backend.openUrl("https://modrinth.com") }
            }
        }

        // --- Bloriko AI Mod Suggestion ---
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
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
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: qsTr("无需一个一个找 Mod，让 Bloriko 帮你找齐。")
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    TextField {
                        id: askBlorikoInput
                        Layout.fillWidth: true
                        placeholderText: qsTr("告诉 Bloriko 你的需求...")
                    }

                    CheckBox {
                        id: deepThinkCheck
                        text: qsTr("深度思考")
                    }

                    Button {
                        text: qsTr("发送")
                        highlighted: true
                        onClicked: {
                            if (askBlorikoInput.text !== "" && Backend) {
                                Backend.askBlorikoForMods(askBlorikoInput.text, deepThinkCheck.checked)
                            }
                        }
                    }
                }
            }
        }

        Label {
            text: qsTr("Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        // --- Modrinth Search Section ---
        RowLayout {
            Layout.fillWidth: true
            TextField {
                id: modSearchInput
                Layout.fillWidth: true
                placeholderText: qsTr("在 Modrinth 上搜索...")
                onAccepted: { if (Backend) Backend.searchModrinth(modSearchInput.text) }
            }
            Button {
                text: qsTr("搜索")
                onClicked: { if (Backend) Backend.searchModrinth(modSearchInput.text) }
            }
        }

        // Mod List
        ListView {
            id: modListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: modsPage.modResults
            clip: true
            spacing: 10
            delegate: Frame {
                width: ListView.view.width
                padding: 10
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }
                RowLayout {
                    width: parent.width
                    spacing: 15
                    Image {
                        width: 50; height: 50
                        source: modelData.icon_url || ""
                        fillMode: Image.PreserveAspectFit
                        visible: modelData.icon_url !== ""
                    }
                    Rectangle {
                        width: 50; height: 50
                        color: Theme.currentTheme.colors.controlFillSecondaryColor
                        radius: 4
                        visible: !modelData.icon_url
                        Label { text: "Icon"; anchors.centerIn: parent; color: Theme.currentTheme.colors.textTertialyColor }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Label { font.weight: Font.DemiBold; text: modelData.name; color: Theme.currentTheme.colors.textColor }
                        Label { text: modelData.description; color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap; Layout.fillWidth: true; maximumLineCount: 2; elide: Text.ElideRight }
                    }
                    Button {
                        text: qsTr("下载")
                        onClicked: { if (Backend) Backend.downloadMod(modelData.id) }
                    }
                }
            }
        }
    }

    Dialog {
        id: blorikoDialog
        title: qsTr("Bloriko 的建议")
        property string text: ""
        standardButtons: Dialog.Ok
        width: parent.width * 0.8
        anchors.centerIn: parent
        modal: true
        
        ScrollView {
            anchors.fill: parent
            Label {
                text: blorikoDialog.text
                wrapMode: Text.Wrap
                width: parent.width
                color: Theme.currentTheme.colors.textColor
            }
        }
    }
}
