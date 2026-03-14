import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt5Compat.GraphicalEffects
import RinUI
import "../components"

FluentPage {
    id: homePage

    property var activityInfo: ({ "show": false, "title": "", "description": "", "time": "", "icon": "", "status": "", "link": "" })
    property var serverInfo: ({})
    property var launchItems: []
    property string currentVersion: ""
    property bool showAccountOnHome: true

    Component.onCompleted: {
        // 从后端获取活动信息（从 API https://launcher.bloret.net/api/info 获取）
        Backend.refreshActivityInfo()
        
        let realInfo = Backend.getActivityInfo()
        if (realInfo && Object.keys(realInfo).length > 0) {
            activityInfo = realInfo
        }
        
        launchItems = Backend.getLaunchItems()
        if (launchItems.length > 0) {
            currentVersion = launchItems[0].name
        }
        
        showAccountOnHome = Backend.getShowAccountOnHome()
        
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
        function onActivityInfoChanged(data) {
            if (data && Object.keys(data).length > 0) {
                activityInfo = data
            }
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

    CoreManagerDialog {
        id: coreManagerDialog
    }

    RunningInstancesDialog {
        id: runningInstancesDialog
    }

    Connections {
        target: Backend
        function onCoreManagerRequested(versionName, coreData) {
            // 确保只打开一次对话框
            coreManagerDialog.close()
            coreManagerDialog.openWithVersion(versionName)
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
                color: (Theme.currentTheme && Theme.currentTheme.colors) ? Theme.currentTheme.colors.textColor : (Theme.dark ? "#ffffff" : "#000000")
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

                Rectangle {
                    width: 80; height: 80
                    radius: 12
                    color: "transparent"
                    clip: true
                    Image {
                        anchors.fill: parent
                        source: activityInfo.icon && activityInfo.icon !== "" ? activityInfo.icon : "../../icon/Grass_Block.png"
                        asynchronous: true
                        cache: false
                        fillMode: Image.PreserveAspectFit
                        onStatusChanged: {
                            if (status === Image.Error) {
                                source = "../../icon/Grass_Block.png"
                            }
                        }
                    }
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
                    text: (Backend ? Backend.tr("前往") : "前往")
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
                        radius: 8
                    }
                }
            }
            
            TextField {
                id: aiInput
                placeholderText: (Backend ? Backend.tr("关于 Minecraft 的任何问题，可以问络可哦 ~") : "关于 Minecraft 的任何问题，可以问络可哦 ~")
                Layout.fillWidth: true
                padding: 10
                onAccepted: sendBtn.clicked()
            }

            CheckBox {
                id: deepThinkCheck
                text: (Backend ? Backend.tr("深度思考") : "深度思考")
            }

            Button {
                id: sendBtn
                icon.name: "ic_fluent_send_20_regular"
                text: (Backend ? Backend.tr("发送") : "发送")
                highlighted: true
                onClicked: {
                    if (aiInput.text.trim() !== "") {
                        blorikoThinking.visible = true
                        askBlorikoAnswer.text = (Backend ? Backend.tr("让络可好好想想...") : "让络可好好想想...")
                        Backend.askBloriko(aiInput.text, deepThinkCheck.checked)
                    }
                }
            }
        }
        
        Label {
            text: (Backend ? Backend.tr("Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。") : "Bloriko 依靠 AI。Bloriko 也可能犯错，请核实重要信息。")
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
            text: (Backend ? Backend.tr("信息") : "信息")
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
                                color: Theme.accentColor ? Theme.accentColor : Theme.currentTheme.colors.textColor
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
                    text: (Backend ? Backend.tr("络可推荐时间段") : "络可推荐时间段")
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
            text: (Backend ? Backend.tr("Bloret Server 数据信息提供自 百络谷查服网") : "Bloret Server 数据信息提供自 百络谷查服网")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        Item { height: 24 }
    }

    pageFooter: Rectangle {
        height: 80
        anchors.left: parent.left
        anchors.right: parent.right
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

Rectangle {
                    width: 44; height: 44
                    radius: 8
                    color: "transparent"
                    clip: true
                    Image {
                        anchors.fill: parent
                        source: {
                            let currentItem = launchItems.find(item => item.name === currentVersion)
                            if (currentItem && currentItem.icon) {
                                return currentItem.icon
                            }
                            return "../../icon/Grass_Block.png"
                        }
                        fillMode: Image.PreserveAspectFit
                    }
                Layout.alignment: Qt.AlignVCenter
            }
            
            ColumnLayout {
                Layout.alignment: Qt.AlignVCenter
                spacing: 2
                
                RowLayout {
                    spacing: 8
                    Layout.fillWidth: true
                    visible: showAccountOnHome
                    
                    // 用户头像
                    Rectangle {
                        width: 32; height: 32
                        radius: 8
                        color: "transparent"
                        clip: true
                        Image {
                            id: avatarImage
                            anchors.fill: parent
                            layer.enabled: true
                            layer.effect: OpacityMask {
                                maskSource: Rectangle {
                                    width: avatarImage.width
                                    height: avatarImage.height
                                    radius: 8
                                }
                            }
                            source: {
                                let url = Backend ? Backend.getPassPortAvatar() : ""
                                let finalUrl = url && url !== "" ? url : "../../icon/Grass_Block.png"
                                console.log("[Home.qml] Avatar Image source:", finalUrl)
                                return finalUrl
                            }
                            asynchronous: true
                            cache: false
                            fillMode: Image.PreserveAspectCrop
                            onStatusChanged: {
                                console.log("[Home.qml] Avatar Image status:", status)
                                if (status === Image.Error) {
                                    console.log("[Home.qml] Avatar Image loading failed, using default")
                                    source = "../../icon/Grass_Block.png"
                                }
                            }
                        }
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            text: Backend ? Backend.getPassPortName() : (Backend ? Backend.tr("访客") : "访客")
                            color: (Theme.currentTheme && Theme.currentTheme.colors) ? Theme.currentTheme.colors.textColor : (Theme.dark ? "#ffffff" : "#000000")
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: (Backend ? "以身份 " + Backend.getPlayerName() + " 来登录 Minecraft" : (Backend ? Backend.tr("无档案") : "无档案"))
                            color: Theme.currentTheme.colors.textSecondaryColor
                            font.pixelSize: 12
                        }
                    }
                }
                
                RowLayout {
                    spacing: 10
                    Label {
                        id: versionLabel
                        text: currentVersion || (launchItems.length > 0 ? launchItems[0].name : "Checking...")
                        color: Theme.currentTheme.colors.textColor
                        font.weight: Font.Bold
                        font.pixelSize: 18
                    }
                    Button {
                        icon.name: "ic_fluent_camera_switch_20_filled"
                        text: (Backend ? Backend.tr("切换核心") : "切换核心")
                        highlighted: true
                        flat: true
                        onClicked: launchSelectorDialog.open()
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                icon.name: "ic_fluent_screen_cut_20_filled"
                flat: true
                ToolTip.visible: hovered
                ToolTip.text: (Backend ? Backend.tr("截图") : "截图")
                onClicked: { if (Backend) Backend.takeScreenCut() }
            }

            Button {
                text: (Backend ? Backend.tr("正在运行") : "正在运行")
                icon.name: "ic_fluent_apps_list_20_regular"
                flat: true
                onClicked: runningInstancesDialog.open()
            }

            Button {
                id: launchBtn
                icon.name: "ic_fluent_caret_right_20_filled"
                text: (Backend ? Backend.tr("启动") : "启动")
                highlighted: true
                Layout.preferredWidth: 120
                Layout.preferredHeight: 36
                onClicked: {
                    if (currentVersion && Backend) Backend.launchGame(currentVersion)
                }
            }
        }
    }
}
