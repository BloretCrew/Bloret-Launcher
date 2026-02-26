import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: modsPage
    title: qsTr("Mods")

    property var modResults: []
    property string blorikoStatus: ""
    property var fabricVersions: []
    property string selectedFabricVersion: ""

    Component.onCompleted: {
        if (Backend) {
            fabricVersions = Backend.getFabricVersions()
        }
    }

    Connections {
        target: Backend
        function onModrinthResultsReceived(results) {
            console.log("Received Modrinth results:", results)
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
                                // 先打开版本选择对话框
                                versionSelectDialog.open()
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
        property string selectedVersion: ""
        standardButtons: Dialog.Close
        width: parent.width * 0.85
        height: parent.height * 0.8
        anchors.centerIn: parent
        modal: true
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                TextEdit {
                    text: blorikoDialog.text
                    wrapMode: Text.Wrap
                    readOnly: true
                    width: parent.width
                    color: Theme.currentTheme.colors.textColor
                    selectByMouse: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Label {
                    text: qsTr("一键安装提示：复制上方推荐中的模组名称，在下方搜索框进行搜索和安装")
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                Button {
                    text: qsTr("关闭")
                    onClicked: {
                        blorikoDialog.close()
                    }
                }
            }
        }
    }

    // --- Version Selection Dialog ---
    Dialog {
        id: versionSelectDialog
        title: qsTr("选择 Minecraft 版本")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 400
        anchors.centerIn: parent
        modal: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Label {
                text: qsTr("请选择要推荐模组的 Minecraft 版本（仅支持 Fabric）：")
                wrapMode: Text.Wrap
                color: Theme.currentTheme.colors.textColor
            }

            ComboBox {
                id: fabricVersionCombo
                Layout.fillWidth: true
                model: modsPage.fabricVersions
                
                Component.onCompleted: {
                    if (modsPage.fabricVersions.length > 0) {
                        currentIndex = 0
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }

        onAccepted: {
            // 用户确认版本选择
            if (fabricVersionCombo.currentIndex >= 0 && fabricVersionCombo.currentText !== "") {
                modsPage.selectedFabricVersion = fabricVersionCombo.currentText
                // 调用带版本参数的推荐函数
                if (Backend && askBlorikoInput.text !== "") {
                    Backend.askBlorikoForModsWithVersion(
                        askBlorikoInput.text,
                        modsPage.selectedFabricVersion,
                        deepThinkCheck.checked
                    )
                }
            }
        }
    }
}

