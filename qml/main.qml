import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "components"

FluentWindow {
    id: window
    visible: true
    title: (Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher")
    // macOS 原生标题区依赖 TitleBar / NavigationBar leading 显示应用名；
    // 保持 title 始终为有效字符串，避免系统栏与自定义栏同时空白。
    width: 1000
    height: 700
    minimumWidth: 800
    minimumHeight: 600

    // 用于保持 OOBE 窗口引用的属性
    property var oobeWindowRef: null

    // 首页发送给 Blora Agent 的待处理消息（跳转到 Blora Agent 页后消费）
    property string pendingBlorikoMessage: ""
    property string pendingBlorikoImagesJson: "[]"

    function navigateToBlorikoWithMessage(message, imagesJson) {
        var text = (message || "").trim()
        var imgs = (imagesJson && imagesJson.length > 0) ? imagesJson : "[]"
        var hasImages = false
        try {
            var arr = JSON.parse(imgs)
            hasImages = arr && arr.length > 0
        } catch (e) { hasImages = false }
        if (text.length === 0 && !hasImages) {
            console.log("[Main] navigateToBlorikoWithMessage: 空消息，忽略")
            return
        }
        console.log("[Main] 跳转 Blora Agent 页处理消息:", text.substring(0, 80), "images=", imgs)
        pendingBlorikoMessage = text
        pendingBlorikoImagesJson = imgs
        // currentPage 只更新导航高亮，真正切页需 navigationView.push / safePush
        if (navItems && navItems.length > 1 && navigationView) {
            var blorikoPage = navItems[1].page
            console.log("[Main] safePush Blora Agent 页:", blorikoPage)
            navigationView.push(blorikoPage)
        } else {
            console.error("[Main] 无法找到 Blora Agent 导航项或 navigationView")
        }
    }

    onClosing: function(closeEvent) {
        if (Backend && Backend.handleWindowCloseRequest()) {
            closeEvent.accepted = false
        }
    }

    navigationView.navExpandWidth: 200

    function createBaseNavItems() {
        return [
            {
                title: (Backend ? Backend.tr("主页") : "主页"),
                page: Qt.resolvedUrl("pages/Home.qml"),
                icon: "ic_fluent_home_20_regular",
                position: Position.Top
            },
            {
                title: (Backend ? Backend.tr("Blora Agent") : "Blora Agent"),
                page: Qt.resolvedUrl("pages/BlorikoPage.qml"),
                source: Qt.resolvedUrl("../icon/Bloriko.jpg"),
                icon: "",
                position: Position.Top
            },
            {
                title: (Backend ? Backend.tr("通行证") : "通行证"),
                page: Qt.resolvedUrl("pages/PassPort.qml"),
                icon: "ic_fluent_person_20_regular",
                position: Position.Bottom,
                passportItem: true
            },
            { title: (Backend ? Backend.tr("下载") : "下载"), page: Qt.resolvedUrl("pages/Download.qml"), icon: "ic_fluent_arrow_download_20_regular" },
            { title: (Backend ? Backend.tr("核心") : "核心"), page: Qt.resolvedUrl("pages/Cores.qml"), icon: "ic_fluent_cube_20_regular" },
            { title: (Backend ? Backend.tr("小工具") : "小工具"), page: Qt.resolvedUrl("pages/Tools.qml"), icon: "ic_fluent_wrench_20_regular" },
            { title: (Backend ? Backend.tr("统计") : "统计"), page: Qt.resolvedUrl("pages/Statistics.qml"), icon: "ic_fluent_data_bar_horizontal_20_regular" },
            { title: (Backend ? Backend.tr("Mods") : "Mods"), page: Qt.resolvedUrl("pages/Mods.qml"), icon: "ic_fluent_puzzle_piece_20_regular" },
            { title: (Backend ? Backend.tr("BBBS") : "BBBS"), page: Qt.resolvedUrl("pages/BBBS.qml"), icon: "ic_fluent_chat_20_regular" },
            { title: (Backend ? Backend.tr("Live") : "Live"), page: Qt.resolvedUrl("pages/Live.qml"), icon: "ic_fluent_video_person_20_regular" },
            { title: (Backend ? Backend.tr("设置") : "设置"), page: Qt.resolvedUrl("pages/Settings.qml"), icon: "ic_fluent_settings_20_regular", position: Position.Bottom },
            { title: (Backend ? Backend.tr("关于") : "关于"), page: Qt.resolvedUrl("pages/Info.qml"), icon: "ic_fluent_info_20_regular", position: Position.Bottom }
        ]
    }

    property var baseNavItems: createBaseNavItems()
    property var navItems: baseNavItems
    navigationItems: navItems

    function rebuildNavigation() {
        console.log("[Main] rebuildNavigation")
        var items = baseNavItems.slice()
        // 在「设置」之前插入插件导航
        var insertAt = items.length
        for (var i = 0; i < items.length; i++) {
            if (items[i].position === Position.Bottom && items[i].icon === "ic_fluent_settings_20_regular") {
                insertAt = i
                break
            }
        }
        if (typeof PluginHost !== "undefined" && PluginHost) {
            try {
                var contrib = JSON.parse(PluginHost.getNavContributionsJson())
                console.log("[Main] plugin nav count:", contrib.length)
                for (var c = 0; c < contrib.length; c++) {
                    var n = contrib[c]
                    var pageUrl = n.page || ""
                    items.splice(insertAt, 0, {
                        title: n.title || n.id || "Plugin",
                        page: pageUrl,
                        icon: n.icon || "ic_fluent_puzzle_piece_20_regular",
                        position: (n.position === "bottom") ? Position.Bottom : Position.Top,
                        pluginNav: true,
                        pluginId: n.plugin_id || ""
                    })
                    insertAt++
                }
            } catch (e) {
                console.log("[Main] plugin nav merge error:", e)
            }
        }
        navItems = items
        navigationItems = navItems
        updatePassPortNavigation()
    }

    function applyPluginTheme() {
        if (typeof PluginHost === "undefined" || !PluginHost)
            return
        try {
            var raw = PluginHost.getActiveThemeJson()
            if (!raw || raw === "{}") {
                console.log("[Main] no active plugin theme")
                return
            }
            var theme = JSON.parse(raw)
            var colors = theme.colors || {}
            var accent = theme.accent || colors.primaryColor || ""
            console.log("[Main] apply plugin theme:", theme.name || theme.plugin_id, "accent=", accent,
                        "colorKeys=", Object.keys(colors))
            if (!Theme)
                return
            try {
                // RinUI 可能暴露 themeColor / accentColor
                if (accent) {
                    if (typeof Theme.setThemeColor === "function")
                        Theme.setThemeColor(accent)
                    else if (Theme.themeColor !== undefined)
                        Theme.themeColor = accent
                    else if (Theme.accentColor !== undefined)
                        Theme.accentColor = accent
                }
                // 尝试写入 Theme.currentTheme.colors 白名单键
                var target = (Theme.currentTheme && Theme.currentTheme.colors)
                    ? Theme.currentTheme.colors
                    : (Theme.colors || null)
                if (target) {
                    var keys = [
                        "primaryColor", "backgroundColor", "cardColor", "cardBorderColor",
                        "textColor", "textSecondaryColor", "textTertialyColor", "textTertiaryColor",
                        "controlBorderColor", "controlColor", "systemAccentColor"
                    ]
                    for (var i = 0; i < keys.length; i++) {
                        var k = keys[i]
                        if (colors[k]) {
                            try {
                                target[k] = colors[k]
                                console.log("[Main] theme color applied:", k, colors[k])
                            } catch (ck) {
                                console.log("[Main] theme color skip:", k, ck)
                            }
                        }
                    }
                    // accent 同步到 primary
                    if (accent && !colors.primaryColor) {
                        try { target.primaryColor = accent } catch (e2) {}
                    }
                }
            } catch (te) {
                console.log("[Main] set theme failed:", te)
            }
        } catch (e) {
            console.log("[Main] applyPluginTheme error:", e)
        }
    }

    function notifyPluginPageOpen(item) {
        if (typeof PluginHost === "undefined" || !PluginHost || !item)
            return
        try {
            var pageId = item.pluginId || item.page || item.title || ""
            var title = item.title || ""
            var pluginId = item.pluginId || ""
            console.log("[Main] ui.page.open", title, pageId, pluginId)
            PluginHost.notifyPageOpen(String(pageId), String(title), String(pluginId))
        } catch (e) {
            console.log("[Main] notifyPluginPageOpen error:", e)
        }
    }

    Connections {
        target: (typeof PluginHost !== "undefined") ? PluginHost : null
        enabled: (typeof PluginHost !== "undefined") && PluginHost !== null
        function onNavContributionsChanged() {
            console.log("[Main] PluginHost.navContributionsChanged")
            rebuildNavigation()
        }
        function onThemeOverrideChanged(pluginId) {
            console.log("[Main] PluginHost.themeOverrideChanged:", pluginId)
            applyPluginTheme()
        }
        function onPluginsChanged() {
            console.log("[Main] PluginHost.pluginsChanged")
            rebuildNavigation()
            applyPluginTheme()
        }
        function onPluginInstallProposed(payloadJson) {
            console.log("[Main] PluginHost.pluginInstallProposed", String(payloadJson || "").substring(0, 200))
            try {
                var meta = JSON.parse(payloadJson || "{}")
                // 激活窗口到前台
                window.raise()
                window.requestActivate()
                pluginInstallDialog.showProposal(meta)
            } catch (e) {
                console.log("[Main] pluginInstallProposed parse error:", e)
            }
        }
        function onPluginInstallProgress(token, stage, message, progress) {
            console.log("[Main] PluginHost.pluginInstallProgress", token, stage, message, progress)
            pluginInstallDialog.applyProgress(token, stage, message, progress)
        }
    }

    // RinUI NavigationView 明确暴露 pageChanged/currentPage；按页面 URL 反查贡献元数据。
    Connections {
        target: navigationView
        function onPageChanged() {
            try {
                var current = String(navigationView.currentPage || "")
                var matched = { title: "", page: current, pluginId: "" }
                for (var i = 0; i < window.navItems.length; i++) {
                    var item = window.navItems[i]
                    if (String(item.page || "") === current) {
                        matched = item
                        break
                    }
                }
                console.log("[Main] navigation page changed:", current, matched.title || "")
                window.notifyPluginPageOpen(matched)
            } catch (e) {
                console.log("[Main] onPageChanged error:", e)
            }
        }
    }

    function updatePassPortNavigation() {
        if (!Backend) return

        let isLoggedIn = Backend.getBloretPassPortLoginStatus()
        let passPortAvatar = Backend.getPassPortAvatar()
        let passPortName = Backend.getPassPortName()

        // 更新通行证导航项（同时同步 baseNavItems，避免 rebuild 覆盖）
        function patchPassport(list) {
            for (let i = 0; i < list.length; i++) {
                if (list[i].passportItem) {
                    if (isLoggedIn && passPortAvatar) {
                        list[i].title = passPortName
                        list[i].source = passPortAvatar
                        list[i].size = 22
                        list[i].circular = true  // 圆形头像（Icon.circular + NavigationItem）
                        list[i].radius = 11
                        list[i].cropToFit = true
                        list[i].icon = ""
                    } else {
                        list[i].title = (Backend ? Backend.tr("通行证") : "通行证")
                        list[i].source = ""
                        list[i].size = undefined
                        list[i].circular = false
                        list[i].radius = 0
                        list[i].cropToFit = true
                        list[i].icon = "ic_fluent_person_20_regular"
                    }
                    break
                }
            }
        }
        patchPassport(baseNavItems)
        patchPassport(navItems)
        navigationItems = navItems  // 触发更新
    }

    Connections {
        target: Backend
        function onMinecraftAccountsChanged(accounts) {
            // 账户信息变化时更新导航并异步刷新头像缓存
            updatePassPortNavigation()
            Backend.refreshPassPortAvatarAsync()
        }

        function onPassportAvatarChanged(url) {
            updatePassPortNavigation()
        }

        function onLanguageChanged() {
            // Recreate translated navigation values; active pages that bind to
            // Backend.tr also receive this signal through their own Connections.
            var keepLanguageDialog = languageSyncDialog.visible
            baseNavItems = createBaseNavItems()
            rebuildNavigation()
            updatePassPortNavigation()
            title = (Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher")
            // Most pages evaluate Backend.tr while being created. Reload only
            // the active page so live updates become visible without restarting
            // the whole QML engine or disturbing background tasks.
            var current = String(navigationView.currentPage || "")
            if (current.length > 0)
                navigationView.safePush(current, true, false)
            // Page reloads can steal focus; keep the download dialog on top
            // until languageSyncFinished closes it.
            if (keepLanguageDialog) {
                languageSyncDialog.open()
                languageSyncDialog.raise()
            }
        }

        function onLanguageSyncStarted(language) {
            // Open immediately when the user switches language, before any
            // heavy page reload or network work runs on the UI thread.
            languageSyncDialog.languageCode = language
            languageSyncDialog.open()
            languageSyncDialog.raise()
        }

        function onLanguageSyncFinished(language, ok, error) {
            if (languageSyncDialog.languageCode === language)
                languageSyncDialog.close()
        }

        function onBackdropEffectChanged(effect) {
            Utils.backdropEnabled = (effect === "acrylic")
        }

        function onLaunchDialogRequested(title) {
            launchProgressDialog.launchTitle = title
            launchProgressDialog.updateLaunchProgress(0, Backend ? Backend.tr("正在准备启动环境...") : "正在准备启动环境...", "")
            launchProgressDialog.open()
        }

        function onLaunchProgressUpdated(progress, status, detail) {
            launchProgressDialog.updateLaunchProgress(progress, status, detail)
        }

        function onLaunchDialogClosed() {
            launchProgressDialog.close()
        }

        // 多任务下载面板自己通过 Timer + signals 管理刷新
        function onDownloadTaskAdded(taskId) {
            // DownloadDialog 内部的 Connections 已经处理了
        }

        function onDownloadTaskRemoved(taskId) {
            // DownloadDialog 内部的 Connections 已经处理了
        }

        function onDownloadManagerOpenRequested() {
            downloadDialog.open()
        }

        function onDownloadErrorOccurred(title, message, version, versionName, loaderType) {
            downloadErrorDialog.errorTitle = title
            downloadErrorDialog.errorMessage = message
            downloadErrorDialog.version = version
            downloadErrorDialog.versionName = versionName
            downloadErrorDialog.loaderType = loaderType
            downloadErrorDialog.open()
        }

        function onUpdateAvailable(currentVer, latestVer, updateText) {
            updateDialog.showUpdate(currentVer, latestVer, updateText)
        }

        function onUpdateProgressUpdated(progress, status) {
            updateDialog.updateProgress(progress, status)
        }

        function onUpdateFailed(message) {
            updateDialog.showError(message)
        }

        function onCoreManagerRequested(versionName, coreData) {
            coreManagerDialog.close()
            coreManagerDialog.openWithVersion(versionName)
        }

        function onMrpackExportRequested(versionName) {
            exportMrpackDialog.openForVersion(versionName)
        }

        function onMinecraftCrashDetected(title, message, stackTrace) {
            errorAnalysisDialog.showError(title, message, stackTrace)
        }

        function onResourcePackEditorRequested() {
            var component = Qt.createComponent("ResourcePackEditor/ResourcePackEditorWindow.qml")
            if (component.status === Component.Ready) {
                var editorWindow = component.createObject(null)
                editorWindow.show()
            } else {
                console.error("Failed to create ResourcePackEditor window:", component.errorString())
            }
        }
    }

    Dialog {
        id: languageSyncDialog

        property string languageCode: ""

        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        modal: true
        dim: true
        width: Math.min(440, window.width - 64)
        implicitHeight: languageSyncContent.implicitHeight + 72
        standardButtons: Dialog.NoButton
        closePolicy: Popup.NoAutoClose
        padding: 24

        ColumnLayout {
            id: languageSyncContent
            width: parent.width
            spacing: 16

            ProgressRing {
                Layout.alignment: Qt.AlignHCenter
                size: 44
                indeterminate: true
                state: ProgressRing.Running
            }

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                typography: Typography.Title
                color: Theme.currentTheme.colors.textColor
                text: Backend
                    ? Backend.tr("Bloret Launcher 正在下载语言并应用")
                    : "Bloret Launcher is downloading and applying the language"
            }

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                typography: Typography.Body
                color: Theme.currentTheme.colors.textSecondaryColor
                text: Backend
                    ? Backend.tr("请稍候，完成后将自动应用。")
                    : "Please wait. It will be applied automatically when ready."
            }
        }
    }

    DownloadDialog {
        id: downloadDialog
        // 挂到窗口 Overlay，避免随页面销毁；非模态 + 无遮罩以便下载时切页
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    Dialog {
        id: downloadErrorDialog

        property string errorTitle: ""
        property string errorMessage: ""
        property string version: ""
        property string versionName: ""
        property string loaderType: "vanilla"

        title: errorTitle
        modal: true
        width: Math.min(520, window.width - 80)
        implicitHeight: Math.max(200, errorContent.implicitHeight + 96)
        standardButtons: Dialog.NoButton
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            id: errorContent
            Layout.fillWidth: true
            spacing: 16

            Text {
                text: downloadErrorDialog.errorMessage
                Layout.fillWidth: true
                Layout.maximumWidth: downloadErrorDialog.availableWidth
                    ? downloadErrorDialog.availableWidth - 8
                    : 480
                wrapMode: Text.Wrap
                typography: Typography.Body
                color: Theme.currentTheme.colors.textColor
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Item { Layout.fillWidth: true }

                Button {
                    text: Backend ? Backend.tr("关闭") : "关闭"
                    onClicked: downloadErrorDialog.close()
                }

                Button {
                    text: Backend ? Backend.tr("重试") : "重试"
                    highlighted: true
                    onClicked: {
                        downloadErrorDialog.close()
                        if (Backend) {
                            Backend.retryDownload(
                                downloadErrorDialog.loaderType,
                                downloadErrorDialog.version,
                                downloadErrorDialog.versionName
                            )
                        }
                    }
                }
            }
        }
    }

    LaunchProgressDialog {
        id: launchProgressDialog

        onSkipCompletionClicked: {
            // 跳过补全，直接启动
            if (Backend) {
                Backend.skipCurrentLaunchCompletion()
            }
        }

        onCancelLaunchClicked: {
            // 取消后台启动任务并释放启动状态，不能只关闭对话框。
            if (Backend) {
                Backend.cancelCurrentLaunch()
            } else {
                launchProgressDialog.close()
            }
        }
    }

    UpdateDialog {
        id: updateDialog
    }

    ErrorAnalysisDialog {
        id: errorAnalysisDialog
        onAskBlorikoRequested: function(prompt) {
            console.log("[Main] 从 Minecraft 错误分析跳转 Blora Agent ，提示词长度:", prompt.length)
            window.navigateToBlorikoWithMessage(prompt)
        }
    }

    CoreManagerDialog {
        id: coreManagerDialog
    }

    ExportMrpackDialog {
        id: exportMrpackDialog
    }

    PluginInstallDialog {
        id: pluginInstallDialog
    }

    // OOBE 覆盖层
    Loader {
        id: oobeLoader
        anchors.fill: parent
        visible: false
        z: 1000  // 确保在最上层
        
        onLoaded: {
            console.log("OOBE Loader loaded")
            // 连接 OOBE 的导航信号（保留备用）
            if (oobeLoader.item) {
                oobeLoader.item.requestNavigateToPassPort.connect(function() {
                    console.log("OOBE requested navigation to PassPort page")
                    // 导航到通行证页面
                    if (window.navItems && window.navItems.length > 1) {
                        window.currentPage = window.navItems[1].page
                    }
                })
            }
        }
    }

    // 监听通行证登录状态变化
    Connections {
        target: Backend
        function onMinecraftAccountsChanged(accounts) {
            // 当账户信息变化时，检查 OOBE 是否需要重新显示
            if (oobeLoader.visible === false && oobeLoader.source === "OOBEOverlay.qml") {
                // OOBE 覆盖层之前加载过但现在不可见，可能是用户去登录了
                // 检查是否是首次运行且未完成 OOBE
                var firstRun = Backend ? Backend.isFirstRun() : false
                if (firstRun) {
                    // 重新显示 OOBE 覆盖层
                    oobeLoader.visible = true
                    // 重新加载以刷新状态
                    oobeLoader.source = ""
                    Qt.callLater(function() {
                        oobeLoader.source = "OOBEOverlay.qml"
                    })
                }
            }
        }
    }

    Component.onCompleted: {
        console.log("[Main] Component.onCompleted")
        rebuildNavigation()
        applyPluginTheme()
        updatePassPortNavigation()
        Backend.refreshPassPortAvatarAsync()

        // 初始化背景效果
        if (Backend) {
            var effect = Backend.getBackdropEffect()
            Utils.backdropEnabled = (effect === "acrylic")
        }

        // 检查是否是首次运行
        var firstRun = Backend ? Backend.isFirstRun() : false
        console.log("First run check:", firstRun)

        if (firstRun) {
            console.log("First run detected, loading OOBE overlay...")

            // 加载 OOBE 覆盖层
            oobeLoader.source = "OOBEOverlay.qml"
            oobeLoader.visible = true
        }

        // 通知 PluginHost：QML 已就绪，可弹出商店安装确认 / 处理 deep link
        if (typeof PluginHost !== "undefined" && PluginHost) {
            try {
                console.log("[Main] PluginHost.mark_ui_ready")
                PluginHost.mark_ui_ready()
            } catch (e) {
                console.log("[Main] mark_ui_ready failed:", e)
            }
        }
    }
}
