import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt5Compat.GraphicalEffects
import RinUI
import "../components"

FluentPage {
    id: homePage

    property var activityInfo: ({ "show": true, "title": "Bloret Launcher 春节小游戏", "description": "完成一个简单的小游戏（大约半分钟），感受春节氛围，可获得最多 50 络琅 + 200 金币奖励！", "time": "2026-02-14 到 2026-03-03", "icon": "../../icon/Grass_Block.png", "status": "during", "link": "https://bloret.net" })
    property var serverInfo: ({})
    property var launchItems: []
    property string currentVersion: ""

    Component.onCompleted: {
        let realInfo = Backend.getActivityInfo()
        if (realInfo && realInfo.title) activityInfo = realInfo
        
        launchItems = Backend.getLaunchItems()
        if (launchItems.length > 0) {
            currentVersion = launchItems[0].name
        }
        Backend.refreshServerInfo()
    }

    Connections {
        target: Backend
        function onServerInfoChanged(data) {
            serverInfo = data
        }
        function onBlorikoResponseReceived(response) {
            blorikoThinking.visible = false
            askBlorikoAnswer.text = response
        }
    }

    LaunchSelectorDialog {
        id: launchSelectorDialog
        
        onItemSelected: function(name, type) {
            currentVersion = name
            if (Backend) Backend.selectLaunchItem(name)
        }
        
        onManageCore: function(name) {
            if (Backend) Backend.showCoreManager(name)
        }
        
        onOpenFolder: function(name) {
            if (Backend) Backend.openVersionFolder(name)
        }
        
        onRenameItem: function(name) {
            console.log("Rename item: " + name)
        }
        
        onDeleteItem: function(name) {
            if (Backend) Backend.deleteCustomItem(name)
            launchItems = Backend.getLaunchItems()
        }
    }

    content: ColumnLayout {
        spacing: 18

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Label {
                text: "Bloret Launcher"
                font.pixelSize: 32
                font.weight: Font.Bold
                color: Theme.currentTheme.colors.textColor
            }
            Label {
                text: Backend ? Backend.getTips() : "最贴近 Windows 11 设计的 Minecraft 启动器"
                font.pixelSize: 14
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 5
            }
            Item { Layout.fillWidth: true }
        }

        Frame {
            Layout.fillWidth: true
            visible: activityInfo.show
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            RowLayout {
                width: parent.width
                spacing: 20

                Image {
                    source: activityInfo.icon || "../../icon/Grass_Block.png"
                    sourceSize { width: 80; height: 80 }
                    fillMode: Image.PreserveAspectFit
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    Label {
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        text: activityInfo.title
                        color: Theme.currentTheme.colors.textColor
                    }
                    Label {
                        text: activityInfo.description
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                        font.pixelSize: 14
                    }
                    Label {
                        text: activityInfo.time
                        color: Theme.currentTheme.colors.textTertialyColor
                        font.pixelSize: 12
                    }
                }
                Button {
                    text: qsTr("前往")
                    highlighted: true
                    onClicked: Backend.openUrl(activityInfo.link)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Image {
                source: "../../icon/Bloriko.jpg"
                sourceSize { width: 35; height: 35 }
                fillMode: Image.PreserveAspectCrop
                layer.enabled: true
                layer.effect: OpacityMask {
                    maskSource: Rectangle {
                        width: 35
                        height: 35
                        radius: 17.5
                    }
                }
            }
            
            TextField {
                id: aiInput
                placeholderText: qsTr("关于 Minecraft 的任何问题，可以问络可哦 ~")
                Layout.fillWidth: true
                padding: 10
                onAccepted: sendBtn.clicked()
            }

            CheckBox {
                id: deepThinkCheck
                text: qsTr("深度思考")
            }

            Button {
                id: sendBtn
                icon.name: "ic_fluent_send_20_regular"
                text: qsTr("发送")
                highlighted: true
                onClicked: {
                    if (aiInput.text.trim() !== "") {
                        blorikoThinking.visible = true
                        askBlorikoAnswer.text = qsTr("让络可好好想想...")
                        Backend.askBloriko(aiInput.text, deepThinkCheck.checked)
                    }
                }
            }
        }
        
        Label {
            text: qsTr("Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        ProgressBar {
            id: blorikoThinking
            Layout.fillWidth: true
            indeterminate: true
            visible: false
        }

        Label {
            id: askBlorikoAnswer
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            text: ""
            textFormat: Text.MarkdownText
            color: Theme.currentTheme.colors.textColor
        }

        Label {
            font.pixelSize: 24
            font.weight: Font.Bold
            text: qsTr("信息")
            color: Theme.currentTheme.colors.textColor
        }

        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    Image {
                        source: "../../icon/bloret.png"
                        sourceSize { width: 50; height: 50 }
                        fillMode: Image.PreserveAspectFit
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                font.weight: Font.Bold
                                font.pixelSize: 16
                                text: "Bloret"
                                color: Theme.currentTheme.colors.textColor
                            }
                            Item { Layout.fillWidth: true }
                            Label { 
                                text: "bloret.net "
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label { 
                                text: serverInfo.realTimeStatus ? (serverInfo.realTimeStatus.playersOnline + " / " + serverInfo.realTimeStatus.playersMax) : "... / 2025"
                                color: Theme.currentTheme.colors.textColor
                                font.weight: Font.DemiBold
                            }
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            Image {
                                source: "../../icon/Grass_Block.png"
                                sourceSize { width: 16; height: 16 }
                            }
                            Label {
                                text: "Bloret 百络谷 | 筑岁同欢 ✨"
                                font.weight: Font.DemiBold
                                color: Theme.accentColor
                            }
                        }
                        Label {
                            text: "「盛夏！新启？百络谷！」"
                            Layout.alignment: Qt.AlignRight
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }

                Label {
                    font.weight: Font.Bold
                    text: qsTr("络可推荐时间段")
                    color: Theme.currentTheme.colors.textColor
                }
                
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: serverInfo.BestTime || "嗨嗨~络可来啦！Bloret 百络谷的玩家人数变化超有趣的！让我来告诉你一些最佳游玩时间段吧~"
                    textFormat: Text.MarkdownText
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }
        }

        Label {
            text: qsTr("Bloret Server 数据信息提供自 百络谷查服网")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        Item { height: 24 }
    }

    pageFooter: Rectangle {
        height: 100
        color: Theme.currentTheme.colors.backgroundAcrylicColor
        
        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: Theme.currentTheme.colors.windowBorderColor
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.rightMargin: 24
            spacing: 15

            ColumnLayout {
                spacing: 2
                Label {
                    text: qsTr("您好, ") + (Backend ? Backend.getPassPortName() : qsTr("访客")) + " ! " + qsTr("将使用") + " " + (Backend ? Backend.getPlayerName() : qsTr("无档案")) + " " + qsTr("来登录 Minecraft")
                    color: Theme.currentTheme.colors.textColor
                    font.pixelSize: 14
                }
                RowLayout {
                    spacing: 10
                    Image {
                        source: {
                            let currentItem = launchItems.find(item => item.name === currentVersion)
                            if (currentItem && currentItem.icon) {
                                return currentItem.icon
                            }
                            return "../../icon/Grass_Block.png"
                        }
                        sourceSize { width: 32; height: 32 }
                        fillMode: Image.PreserveAspectFit
                    }
                    Label {
                        id: versionLabel
                        text: currentVersion || (launchItems.length > 0 ? launchItems[0].name : "Checking...")
                        color: Theme.currentTheme.colors.textColor
                        font.weight: Font.Bold
                        font.pixelSize: 18
                    }
                    Button {
                        text: qsTr("切换核心")
                        icon.name: "ic_fluent_arrow_swap_20_regular"
                        flat: true
                        onClicked: launchSelectorDialog.open()
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                icon.name: "ic_fluent_screenshot_20_regular"
                flat: true
                highlighted: false
                onClicked: { if (Backend) Backend.takeScreenCut() }
                ToolTip.visible: hovered
                ToolTip.text: qsTr("截图")
            }

            Button {
                id: launchBtn
                height: 40
                text: qsTr("启动")
                highlighted: true
                Layout.preferredWidth: 150
                onClicked: {
                    if (currentVersion && Backend) Backend.launchGame(currentVersion)
                }
            }
        }
    }
}
