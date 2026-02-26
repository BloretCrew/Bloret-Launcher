import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: homePage
    title: qsTr("首页")

    property var activityInfo: ({ "show": false })
    property var serverInfo: ({})
    property var launchItems: []
    property string currentVersion: ""

    Component.onCompleted: {
        activityInfo = Backend.getActivityInfo()
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

    // --- Header Row ---
    RowLayout {
        Layout.fillWidth: true
        Label {
            font.pixelSize: 24
            font.weight: Font.DemiBold
            text: qsTr("Bloret Launcher")
        }
        Label {
            text: Backend.getTips()
            color: "#7f7f7f"
            Layout.leftMargin: 10
        }
        Item { Layout.fillWidth: true }
    }

    // --- Minecraft Tab Bar ---
    TabBar {
        id: minecraftTab
        Layout.fillWidth: true
        
        Repeater {
            model: launchItems
            TabButton {
                text: modelData.name
                onClicked: currentVersion = modelData.name
            }
        }
    }

    // --- Activity Card ---
    Frame {
        Layout.fillWidth: true
        visible: activityInfo.show
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: activityInfo.icon || "../../icon/Grass_Block.png"
                sourceSize { width: 48; height: 48 }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: activityInfo.title || ""
                }
                Label {
                    text: activityInfo.description || ""
                    color: "#7f7f7f"
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
                Label {
                    text: qsTr("活动时间: ") + (activityInfo.time || "")
                    color: "#7f7f7f"
                    font.pixelSize: 12
                }
            }
            Button {
                text: activityInfo.status === "before" ? qsTr("尚未开始") : (activityInfo.status === "after" ? qsTr("已结束") : qsTr("前往"))
                enabled: activityInfo.status === "during"
                highlighted: enabled
                onClicked: Backend.openUrl(activityInfo.link)
            }
        }
    }

    // --- Ask Bloriko AI Chat ---
    RowLayout {
        Layout.fillWidth: true
        spacing: 10

        Image {
            source: "../../icon/Bloriko.jpg"
            sourceSize { width: 35; height: 35 }
        }

        TextField {
            id: aiInput
            placeholderText: qsTr("关于 Minecraft 的任何问题，可以问络可哦 ~")
            Layout.fillWidth: true
            onAccepted: sendBtn.clicked()
        }

        CheckBox {
            id: deepThinkCheck
            text: qsTr("深度思考")
        }

        Button {
            id: sendBtn
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
        color: "#7f7f7f"
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
    }

    // --- Server Info Card ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("信息")
        Layout.topMargin: 15
    }

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
                    source: "../../icon/bloret.png"
                    sourceSize { width: 50; height: 50 }
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            font.weight: Font.DemiBold
                            font.pixelSize: 16
                            text: "Bloret"
                        }
                        Item { Layout.fillWidth: true }
                        Label { text: "bloret.net " }
                        Label { 
                            text: serverInfo.realTimeStatus ? (serverInfo.realTimeStatus.playersOnline + " / " + serverInfo.realTimeStatus.playersMax) : "N/A"
                        }
                    }
                    
                    Label {
                        text: (serverInfo.realTimeStatus && serverInfo.realTimeStatus.motdClean && serverInfo.realTimeStatus.motdClean[0]) || qsTr("正在获取服务器状态...")
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Label {
                        text: (serverInfo.realTimeStatus && serverInfo.realTimeStatus.motdClean && serverInfo.realTimeStatus.motdClean[1]) || ""
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.currentTheme.colors.surfaceStrokeColorDefault
            }
            
            Label {
                font.weight: Font.DemiBold
                text: qsTr("络可推荐时间段")
            }
            
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: serverInfo.BestTime || qsTr("暂无推荐时间段信息")
            }
        }
    }

    Label {
        text: qsTr("Bloret Server 数据信息提供自 百络谷查服网")
        color: "#7f7f7f"
        font.pixelSize: 12
        Layout.topMargin: 5
    }

    // --- Launch Card ---
    Frame {
        Layout.fillWidth: true
        Layout.topMargin: 20
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
                Label {
                    font.pixelSize: 18
                    text: qsTr("您好,")
                }
                Label {
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    text: Backend.getPlayerName()
                }
                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Image {
                    source: "../../icon/Grass_Block.png"
                    sourceSize { width: 32; height: 32 }
                }
                Label {
                    font.weight: Font.DemiBold
                    text: currentVersion || qsTr("未选择版本")
                }
                Button {
                    text: qsTr("切换核心")
                    onClicked: {
                        // In a more complex app, this might open a menu or dialog
                        // For now we assume the TabBar handles it
                    }
                }
                Button {
                    text: qsTr("启动")
                    highlighted: true
                    Layout.fillWidth: true
                    enabled: currentVersion !== ""
                    onClicked: Backend.launchGame(currentVersion)
                }
            }
        }
    }
}
