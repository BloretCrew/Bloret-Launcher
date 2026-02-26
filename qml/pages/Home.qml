import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: homePage
    title: "" // We use a custom header

    property var activityInfo: ({ "show": true, "title": "Bloret Launcher 春节小游戏", "description": "完成一个简单的小游戏（大约半分钟），感受春节氛围，可获得最多 50 络琅 + 200 金币奖励！", "time": "2026-02-14 到 2026-03-03", "icon": "../../icon/new_year.png", "status": "during", "link": "https://bloret.net" })
    property var serverInfo: ({})
    property var launchItems: []
    property string currentVersion: ""

    Component.onCompleted: {
        // Try to get real activity info, fallback to our mock for visual consistency
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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // --- Header ---
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
                text: "最贴近 Windows 11 设计的 Minecraft 启动器"
                font.pixelSize: 14
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 5
            }
            Item { Layout.fillWidth: true }
        }

        // --- Activity Card ---
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

        // --- AI Chat ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
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

        // --- Info Section ---
        Label {
            font.pixelSize: 24
            font.weight: Font.Bold
            text: qsTr("Info")
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
                        sourceSize { width: 48; height: 48 }
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
                                text: serverInfo.realTimeStatus ? (serverInfo.realTimeStatus.playersOnline + " / " + serverInfo.realTimeStatus.playersMax) : "12 / 2025"
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
                            text: "「我们的QQ群: 724060512」"
                            Layout.alignment: Qt.AlignRight
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }
            }
        }

        // --- Recommended Time ---
        Label {
            text: qsTr("络可推荐时间段")
            font.weight: Font.Bold
            color: Theme.currentTheme.colors.textColor
        }
        
        Label {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            text: serverInfo.BestTime || "嗨嗨~络可来啦！Bloret 百络谷的玩家人数变化超有趣的！让我来告诉你一些最佳游玩时间段吧~"
            color: Theme.currentTheme.colors.textSecondaryColor
        }

        Item { Layout.fillHeight: true } // Spacer
    }

    // --- Floating Blue Launch Bar ---
    Rectangle {
        id: launchBar
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 15
        height: 80
        radius: 12
        color: Theme.accentColor // Use the accent color for the bar
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 20

            Image {
                id: currentVersionIcon
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                source: "../../icon/DefaultVersion.png" // Fallback
                fillMode: Image.PreserveAspectFit
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: "Hello, " + (Backend ? Backend.getPlayerName() : "User") + " ! 将使用 [Microsoft Login] 登录 Minecraft"
                    color: "white"
                    font.pixelSize: 14
                }
                Label {
                    id: versionLabel
                    text: currentVersion || (launchItems.length > 0 ? launchItems[0].name : "Checking...")
                    color: "white"
                    font.weight: Font.Bold
                    font.pixelSize: 18
                }
            }

            RowLayout {
                spacing: 10
                
                Button {
                    icon.name: "ic_fluent_screenshot_20_regular"
                    flat: true
                    highlighted: false
                    onClicked: { if (Backend) Backend.screenshot() }
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("截图")
                }

                Button {
                    text: qsTr("切换核心")
                    icon.name: "ic_fluent_arrow_swap_20_regular"
                    flat: true
                    onClicked: versionMenu.open()
                    
                    Menu {
                        id: versionMenu
                        width: 250
                        Repeater {
                            model: launchItems
                            MenuItem {
                                text: modelData.name
                                onClicked: currentVersion = modelData.name
                            }
                        }
                    }
                }
            }

            Button {
                id: launchBtn
                height: 50
                Layout.preferredWidth: 200
                Layout.preferredHeight: 45
                background: Rectangle {
                    color: "white"
                    radius: 8
                    opacity: parent.pressed ? 0.8 : 1.0
                }
                contentItem: Label {
                    text: qsTr("启动游戏")
                    color: Theme.accentColor
                    font.weight: Font.Bold
                    font.pixelSize: 18
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: {
                    if (currentVersion && Backend) Backend.launchGame(currentVersion)
                }
            }
        }
    }
}
