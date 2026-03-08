import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: modsPage
    title: (Backend ? Backend.tr("Mods") : "Mods")

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
            versionSelectDialog.close()
            blorikoDialog.text = response
            blorikoDialog.open()
        }
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + "M"
        if (num >= 1000) return (num / 1000).toFixed(1) + "K"
        return num.toString()
    }

    ColumnLayout {
        Layout.fillWidth: true
        // anchors.fill: parent // Removed to avoid layout conflict inside Flickable
        // anchors.margins: 20
        spacing: 20

        // --- Header ---

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
                            text: (Backend ? Backend.tr("让络可帮你挑选合适的 Mod") : "让络可帮你挑选合适的 Mod")
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: (Backend ? Backend.tr("无需一个一个找 Mod，让 Bloriko 帮你找齐。") : "无需一个一个找 Mod，让 Bloriko 帮你找齐。")
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
                        placeholderText: (Backend ? Backend.tr("告诉 Bloriko 你的需求...") : "告诉 Bloriko 你的需求...")
                    }

                    CheckBox {
                        id: deepThinkCheck
                        text: (Backend ? Backend.tr("深度思考") : "深度思考")
                    }

                    Button {
                        text: (Backend ? Backend.tr("发送") : "发送")
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
            text: (Backend ? Backend.tr("Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。") : "Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        // --- Modrinth Search Section ---
        RowLayout {
            Layout.fillWidth: true
            TextField {
                id: modSearchInput
                Layout.fillWidth: true
                placeholderText: (Backend ? Backend.tr("在 Modrinth 上搜索...") : "在 Modrinth 上搜索...")
                onAccepted: { if (Backend) Backend.searchModrinth(modSearchInput.text) }
            }
            Button {
                text: (Backend ? Backend.tr("搜索") : "搜索")
                onClicked: { if (Backend) Backend.searchModrinth(modSearchInput.text) }
            }
        }

        // Mod List
        ListView {
            id: modListView
            Layout.fillWidth: true
            // Layout.fillHeight: true // Removed, let it grow with content
            implicitHeight: contentHeight // Auto height based on content
            interactive: false // Disable internal scrolling, use page scroll
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
                    
                    // Icon
                    Rectangle {
                        Layout.preferredWidth: 64
                        Layout.preferredHeight: 64
                        Layout.alignment: Qt.AlignTop
                        color: "transparent"
                        
                        Image {
                            anchors.fill: parent
                            source: modelData.icon_url || ""
                            fillMode: Image.PreserveAspectFit
                            visible: modelData.icon_url !== ""
                        }
                        
                        Rectangle {
                            anchors.fill: parent
                            color: Theme.currentTheme.colors.controlFillSecondaryColor
                            radius: 8
                            visible: !modelData.icon_url
                            Label { text: "Icon"; anchors.centerIn: parent; color: Theme.currentTheme.colors.textTertialyColor }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        // Title & Author
                        RowLayout {
                            Label { 
                                font.weight: Font.DemiBold
                                font.pixelSize: 16
                                text: modelData.name
                                color: Theme.currentTheme.colors.textColor 
                            }
                            Label {
                                text: "by " + (modelData.author || "Unknown")
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                                Layout.alignment: Qt.AlignBaseline
                            }
                        }
                        
                        Label { 
                            text: modelData.description
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        
                        // Stats & Categories
                        RowLayout {
                            spacing: 15
                            
                            Label {
                                text: "⬇ " + formatNumber(modelData.downloads || 0)
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                            }
                            
                            Label {
                                text: "♥ " + formatNumber(modelData.follows || 0)
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                            }
                            
                            Repeater {
                                model: (modelData.categories || []).slice(0, 3)
                                delegate: Rectangle {
                                    color: Theme.currentTheme.colors.controlFillSecondaryColor
                                    radius: 4
                                    width: catLabel.implicitWidth + 10
                                    height: 18
                                    Label {
                                        id: catLabel
                                        text: modelData
                                        anchors.centerIn: parent
                                        font.pixelSize: 10
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                    spacing: 8
                    Button {
                        text: (Backend ? Backend.tr("查看") : "查看")
                        onClicked: { 
                            if (Backend) Backend.openUrl("https://modrinth.com/mod/" + modelData.slug) 
                        }
                    }
                    Button {
                        text: (Backend ? Backend.tr("下载") : "下载")
                        highlighted: true
                        onClicked: { 
                            downloadTargetDialog.modId = modelData.id
                            downloadTargetDialog.open()
                        }
                    }
                }
            }
        }
    }
    }

    Dialog {
        id: blorikoDialog
        title: (Backend ? Backend.tr("Bloriko 的建议") : "Bloriko 的建议")
        property string text: ""
        width: Math.min(parent.width * 0.9, 650)
        height: Math.min(parent.height * 0.9, 550)
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        modal: true
        
        // 显式设置 Padding 以避开 Dialog 的标题区域
        padding: 0
        topPadding: 60
        leftPadding: 20
        rightPadding: 20
        bottomPadding: 20

        contentItem: ColumnLayout {
            spacing: 15

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                TextArea {
                    text: blorikoDialog.text
                    wrapMode: Text.Wrap
                    readOnly: true
                    color: Theme.currentTheme.colors.textColor
                    selectByMouse: true
                    textFormat: Text.MarkdownText
                    font.pixelSize: 14
                    background: null
                    leftPadding: 0
                    topPadding: 0
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 15

                Label {
                    text: (Backend ? Backend.tr("💡 提示：复制上方推荐中的模组名称，在搜索框搜索即可一键安装。") : "💡 提示：复制上方推荐中的模组名称，在搜索框搜索即可一键安装。")
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                Button {
                    text: (Backend ? Backend.tr("关闭") : "关闭")
                    onClicked: blorikoDialog.close()
                }
            }
        }
    }

    // --- Version Selection Dialog ---
    Dialog {
        id: versionSelectDialog
        title: (Backend ? Backend.tr("选择 Minecraft 版本") : "选择 Minecraft 版本")
        width: 400
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        modal: true
        closePolicy: Popup.NoAutoClose

        property bool loading: false

        ColumnLayout {
            anchors.fill: parent
            anchors.topMargin: 56
            anchors.leftMargin: 15
            anchors.rightMargin: 15
            anchors.bottomMargin: 15
            spacing: 20

            Label {
                text: (Backend ? Backend.tr("请选择要推荐模组的 Minecraft 版本（仅支持 Fabric）：") : "请选择要推荐模组的 Minecraft 版本（仅支持 Fabric）：")
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
                visible: !versionSelectDialog.loading
            }

            ComboBox {
                id: fabricVersionCombo
                Layout.fillWidth: true
                model: modsPage.fabricVersions
                visible: !versionSelectDialog.loading
                
                Component.onCompleted: {
                    if (modsPage.fabricVersions.length > 0) {
                        currentIndex = 0
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                visible: versionSelectDialog.loading
                spacing: 15
                
                ProgressBar {
                    Layout.fillWidth: true
                    indeterminate: true
                }
                
                Label {
                    text: (Backend ? Backend.tr("络可正在思考建议...") : "络可正在思考建议...")
                    Layout.alignment: Qt.AlignHCenter
                    color: Theme.currentTheme.colors.textColor
                    font.pixelSize: 14
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                visible: !versionSelectDialog.loading
                
                Item { Layout.fillWidth: true }
                
                Button {
                    text: (Backend ? Backend.tr("取消") : "取消")
                    onClicked: versionSelectDialog.close()
                }
                
                Button {
                    text: (Backend ? Backend.tr("确定") : "确定")
                    highlighted: true
                    onClicked: {
                        if (fabricVersionCombo.currentIndex >= 0 && fabricVersionCombo.currentText !== "") {
                            versionSelectDialog.loading = true
                            modsPage.selectedFabricVersion = fabricVersionCombo.currentText
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
        }

        onClosed: {
            loading = false
        }
    }

    Dialog {
        id: downloadTargetDialog
        title: (Backend ? Backend.tr("选择安装版本") : "选择安装版本")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 350
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        modal: true
        
        property string modId: ""

        ColumnLayout {
            anchors.fill: parent
            anchors.topMargin: 56
            anchors.leftMargin: 15
            anchors.rightMargin: 15
            anchors.bottomMargin: 15
            spacing: 15
            
            Label {
                text: (Backend ? Backend.tr("请选择要安装此 Mod 的 Fabric 版本:") : "请选择要安装此 Mod 的 Fabric 版本:")
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }
            
            ComboBox {
                id: downloadVersionCombo
                Layout.fillWidth: true
                model: modsPage.fabricVersions
            }
        }
        
        onAccepted: {
            if (Backend && downloadVersionCombo.currentText !== "") {
                Backend.downloadMod(downloadTargetDialog.modId, downloadVersionCombo.currentText)
            }
        }
    }
}