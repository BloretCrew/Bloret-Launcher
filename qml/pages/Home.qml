import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import QtQuick.Window 2.15
import Qt5Compat.GraphicalEffects
import RinUI
import "../components"

FluentPage {
    id: homePage

    property var activityInfo: ({ "show": false, "title": "", "description": "", "time": "", "icon": "", "status": "", "link": "" })
    property var serverInfo: ({})
    property var launchItems: []
    property string currentVersion: ""
    property string showAccountOnHome: "compact"
    property var pluginHomeCards: []

    function loadPluginHomeCards() {
        pluginHomeCards = []
        if (typeof PluginHost === "undefined" || !PluginHost) {
            console.log("[Home] PluginHost 不可用，跳过主页插件卡片")
            return
        }
        try {
            var raw = PluginHost.getHomeContributionsJson()
            var list = JSON.parse(raw || "[]")
            console.log("[Home] plugin home cards:", list.length)
            pluginHomeCards = list
        } catch (e) {
            console.log("[Home] loadPluginHomeCards error:", e)
            pluginHomeCards = []
        }
    }

    Component.onCompleted: {
        // 同步路径只读本地缓存：先出页面骨架，再延后远程刷新，减轻侧边栏切换卡顿。
        // NavigationView 每次切页会 replace 重建实例，故 onCompleted 会反复执行。
        if (!Backend)
            return

        let realInfo = Backend.getActivityInfo()
        if (realInfo && Object.keys(realInfo).length > 0) {
            activityInfo = realInfo
        }

        launchItems = Backend.getLaunchItems()

        // 优先使用配置中保存的核心选择，若不存在或无效则回退到第一项
        var saved = Backend.getSelectedLaunchItem()
        var found = launchItems.find(function(item) { return item.name === saved })
        if (found) {
            currentVersion = found.name
            console.log("[Home] Restored saved core selection:", found.name)
        } else if (launchItems.length > 0) {
            currentVersion = launchItems[0].name
        }

        showAccountOnHome = Backend.getShowAccountOnHome()

        // 插件卡片与远程刷新放到下一帧，让 StackView 动画/首帧先完成；
        // Backend 内还有 TTL / in-flight，短时间反复进入不会重复打网。
        Qt.callLater(function() {
            if (!homePage)
                return
            loadPluginHomeCards()
            if (Backend) {
                Backend.refreshActivityInfo()
                Backend.refreshServerInfo()
            }
        })
    }

    Connections {
        target: Backend
        function onServerInfoChanged(data) {
            serverInfo = data
        }
        function onActivityInfoChanged(data) {
            if (data && Object.keys(data).length > 0) {
                activityInfo = data
            }
        }
        function onPassportAvatarChanged(url) {
            avatarImage.source = url && url !== "" ? url : "../../icon/Grass_Block.png"
        }
    }

    Connections {
        target: (typeof PluginHost !== "undefined") ? PluginHost : null
        enabled: (typeof PluginHost !== "undefined") && PluginHost !== null
        function onHomeContributionsChanged() {
            console.log("[Home] PluginHost.homeContributionsChanged")
            loadPluginHomeCards()
        }
        function onPluginsChanged() {
            console.log("[Home] PluginHost.pluginsChanged -> reload home cards")
            loadPluginHomeCards()
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

    RunningInstancesDialog {
        id: runningInstancesDialog
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

        // 插件主页卡片插槽（contributes.home / ui.home）
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: pluginHomeCards && pluginHomeCards.length > 0

            Repeater {
                model: pluginHomeCards
                delegate: Loader {
                    Layout.fillWidth: true
                    // 高度由子项决定
                    asynchronous: false
                    source: modelData.qml || ""
                    onStatusChanged: {
                        if (status === Loader.Error)
                            console.log("[Home] plugin card load error:", modelData.id, modelData.qml, sourceComponent)
                        else if (status === Loader.Ready)
                            console.log("[Home] plugin card ready:", modelData.id, modelData.title)
                    }
                    onLoaded: {
                        if (item) {
                            if (item.pluginId === undefined && modelData.plugin_id)
                                try { item.pluginId = modelData.plugin_id } catch (e) {}
                            if (item.cardTitle === undefined && modelData.title)
                                try { item.cardTitle = modelData.title } catch (e2) {}
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Image {
                source: Qt.resolvedUrl("../../icon/Bloriko.jpg")
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
                placeholderText: (Backend ? Backend.tr("关于 Minecraft 的任何问题，可以问 Blora Agent 哦 ~") : "关于 Minecraft 的任何问题，可以问 Blora Agent 哦 ~")
                Layout.fillWidth: true
                padding: 10
                onAccepted: sendBtn.clicked()
            }

            Button {
                id: sendBtn
                icon.name: "ic_fluent_send_20_regular"
                text: (Backend ? Backend.tr("发送") : "发送")
                highlighted: true
                onClicked: {
                    var text = aiInput.text.trim()
                    if (text === "")
                        return
                    console.log("[Home] 发送到 Blora Agent 页处理:", text.substring(0, 80))
                    // 跳转到 Blora Agent 页面并由 Blora Agent 处理
                    var win = Window.window
                    if (win && typeof win.navigateToBlorikoWithMessage === "function") {
                        win.navigateToBlorikoWithMessage(text)
                    } else {
                        console.error("[Home] 无法获取主窗口或 navigateToBlorikoWithMessage")
                    }
                    aiInput.text = ""
                }
            }
        }
        
        Label {
            text: (Backend ? Backend.tr("Blora Agent 依靠 AI。 Blora Agent 也可能犯错，请核实重要信息。") : "Blora Agent 依靠 AI。 Blora Agent 也可能犯错，请核实重要信息。")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
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
                        source: Qt.resolvedUrl("../../icon/bloret.png")
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
                                source: Qt.resolvedUrl("../../icon/Grass_Block.png")
                                sourceSize { width: 16; height: 16 }
                            }
                            Label {
                                text: Backend ? Backend.tr("Bloret 百络谷 | 筑岁同欢 ✨") : "Bloret 百络谷 | 筑岁同欢 ✨"
                                font.weight: Font.DemiBold
                                color: Theme.accentColor ? Theme.accentColor : Theme.currentTheme.colors.textColor
                            }
                        }
                        Label {
                            text: Backend ? Backend.tr("「盛夏！新启？百络谷！」") : "「盛夏！新启？百络谷！」"
                            Layout.alignment: Qt.AlignRight
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }

                Label {
                    font.weight: Font.Bold
                    text: (Backend ? Backend.tr("Blora Agent 推荐时间段") : "Blora Agent 推荐时间段")
                    color: Theme.currentTheme.colors.textColor
                }
                
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: serverInfo.BestTime || (Backend ? Backend.tr("嗨嗨~ Blora Agent 来啦！Bloret 百络谷的玩家人数变化超有趣的！让我来告诉你一些最佳游玩时间段吧~") : "嗨嗨~ Blora Agent 来啦！Bloret 百络谷的玩家人数变化超有趣的！让我来告诉你一些最佳游玩时间段吧~")
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
                
                // 完整展示：头像 + PassPort 名 + Minecraft 身份
                RowLayout {
                    spacing: 8
                    Layout.fillWidth: true
                    visible: showAccountOnHome === "full"

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
                                return url && url !== "" ? url : "../../icon/Grass_Block.png"
                            }
                            asynchronous: true
                            cache: false
                            fillMode: Image.PreserveAspectCrop
                            onStatusChanged: {
                                if (status === Image.Error)
                                    source = "../../icon/Grass_Block.png"
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

                // 简略展示：单行文本
                Label {
                    Layout.fillWidth: true
                    visible: showAccountOnHome === "compact"
                    text: Backend ? Backend.tr("以身份 ") + Backend.getPlayerName() + Backend.tr(" 启动 Minecraft") : ""
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 12
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

            Label {
                id: homeSessionTime
                text: ""
                font.pixelSize: 13
                color: Theme.currentTheme.colors.textSecondaryColor
                visible: text !== ""

                Connections {
                    target: Backend
                    function onPlayTimeTick() {
                        if (Backend)
                            homeSessionTime.text = Backend.getSessionPlayTimeFormatted()
                    }
                }

                Component.onCompleted: {
                    if (Backend)
                        homeSessionTime.text = Backend.getSessionPlayTimeFormatted()
                }
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
                
                // 添加右键菜单支持跳过补全启动
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.LeftButton) {
                            if (currentVersion && Backend) Backend.launchGame(currentVersion)
                        } else if (mouse.button === Qt.RightButton) {
                            skipCompletionMenu.popup()
                        }
                    }
                    onPressAndHold: function(mouse) {
                        skipCompletionMenu.popup()
                    }
                }
                
                Menu {
                    id: skipCompletionMenu
                    
                    MenuItem {
                        text: (Backend ? Backend.tr("正常启动（补全文件）") : "正常启动（补全文件）")
                        icon.name: "ic_fluent_play_20_regular"
                        onTriggered: {
                            if (currentVersion && Backend) Backend.launchGame(currentVersion)
                        }
                    }
                    
                    MenuItem {
                        text: (Backend ? Backend.tr("跳过补全启动") : "跳过补全启动")
                        icon.name: "ic_fluent_skip_forward_20_regular"
                        onTriggered: {
                            if (currentVersion && Backend) Backend.launchGameWithSkip(currentVersion, true)
                        }
                    }
                }
            }
        }
    }
}
