import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "components"

FluentWindow {
    id: window
    visible: true
    title: (Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher")
    width: 1000
    height: 700
    minimumWidth: 800
    minimumHeight: 600

    // 用于保持 OOBE 窗口引用的属性
    property var oobeWindowRef: null

    onClosing: function(closeEvent) {
        if (Backend && Backend.handleWindowCloseRequest()) {
            closeEvent.accepted = false
        }
    }

    navigationView.navExpandWidth: 200

    property var navItems: [
        {
            title: (Backend ? Backend.tr("主页") : "主页"),
            page: Qt.resolvedUrl("pages/Home.qml"),
            icon: "ic_fluent_home_20_regular",
            position: Position.Top
        },
        {
            title: (Backend ? Backend.tr("络可") : "络可"),
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
            passportItem: true  // 标记为通行证项
        },
        {
            title: (Backend ? Backend.tr("下载") : "下载"),
            page: Qt.resolvedUrl("pages/Download.qml"),
            icon: "ic_fluent_arrow_download_20_regular"
        },
        {
            title: (Backend ? Backend.tr("核心") : "核心"),
            page: Qt.resolvedUrl("pages/Cores.qml"),
            icon: "ic_fluent_cube_20_regular"
        },
        {
            title: (Backend ? Backend.tr("小工具") : "小工具"),
            page: Qt.resolvedUrl("pages/Tools.qml"),
            icon: "ic_fluent_wrench_20_regular"
        },
        {
            title: (Backend ? Backend.tr("统计") : "统计"),
            page: Qt.resolvedUrl("pages/Statistics.qml"),
            icon: "ic_fluent_data_bar_horizontal_20_regular"
        },
        {
            title: (Backend ? Backend.tr("Mods") : "Mods"),
            page: Qt.resolvedUrl("pages/Mods.qml"),
            icon: "ic_fluent_puzzle_piece_20_regular"
        },
        {
            title: (Backend ? Backend.tr("BBBS") : "BBBS"),
            page: Qt.resolvedUrl("pages/BBBS.qml"),
            icon: "ic_fluent_chat_20_regular"
        },
        {
            title: (Backend ? Backend.tr("Live") : "Live"),
            page: Qt.resolvedUrl("pages/Live.qml"),
            icon: "ic_fluent_video_person_20_regular"
        },
        {
            title: (Backend ? Backend.tr("设置") : "设置"),
            page: Qt.resolvedUrl("pages/Settings.qml"),
            icon: "ic_fluent_settings_20_regular",
            position: Position.Bottom
        },
        {
            title: (Backend ? Backend.tr("关于") : "关于"),
            page: Qt.resolvedUrl("pages/Info.qml"),
            icon: "ic_fluent_info_20_regular",
            position: Position.Bottom
        }
    ]

    navigationItems: navItems

    function updatePassPortNavigation() {
        if (!Backend) return

        let isLoggedIn = Backend.getBloretPassPortLoginStatus()
        let passPortAvatar = Backend.getPassPortAvatar()
        let passPortName = Backend.getPassPortName()

        // 更新通行证导航项
        for (let i = 0; i < navItems.length; i++) {
            if (navItems[i].passportItem) {
                if (isLoggedIn && passPortAvatar) {
                    // 已登录：显示用户头像和名字
                    navItems[i].title = passPortName
                    navItems[i].source = passPortAvatar  // 使用source显示自定义图片
                    navItems[i].icon = ""  // 清除默认icon
                } else {
                    // 未登录：显示默认icon和"通行证"文本
                    navItems[i].title = (Backend ? Backend.tr("通行证") : "通行证")
                    navItems[i].source = ""
                    navItems[i].icon = "ic_fluent_person_20_regular"
                }
                break
            }
        }
        navigationItems = navItems  // 触发更新
    }

    Connections {
        target: Backend
        function onMinecraftAccountsChanged(accounts) {
            // 账户信息变化时更新导航
            updatePassPortNavigation()
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

        function onDownloadDialogRequested(title) {
            downloadDialog.resetDialog()
            downloadDialog.downloadTitle = title
            downloadDialog.downloadStatus = Backend ? Backend.tr("准备下载...") : "准备下载..."
            downloadDialog.open()
        }

        function onDownloadProgressUpdated(progress, status, speed, downloaded, total) {
            downloadDialog.updateProgress(progress, status, speed, downloaded, total)
        }

        function onDownloadDialogClosed() {
            downloadDialog.close()
        }

        function onDownloadCompleted(message) {
            downloadDialog.setCompleted(message)
        }

        function onDownloadPaused(paused) {
            downloadDialog.setPaused(paused)
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

    DownloadDialog {
        id: downloadDialog

        onPauseClicked: {
            if (Backend) Backend.toggleDownloadPause()
        }

        onCancelClicked: {
            if (Backend) Backend.cancelDownload()
        }
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
        standardButtons: Dialog.NoButton

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 16

            Text {
                text: downloadErrorDialog.errorMessage
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                typography: Typography.Body
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
                            Backend.retryDownload(downloadErrorDialog.loaderType, downloadErrorDialog.version, downloadErrorDialog.versionName)
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
            // 取消启动
            launchProgressDialog.close()
        }
    }

    UpdateDialog {
        id: updateDialog
    }

    ErrorAnalysisDialog {
        id: errorAnalysisDialog
    }

    CoreManagerDialog {
        id: coreManagerDialog
    }

    ExportMrpackDialog {
        id: exportMrpackDialog
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
        updatePassPortNavigation()

        // 检查是否是首次运行
        var firstRun = Backend ? Backend.isFirstRun() : false
        console.log("First run check:", firstRun)

        if (firstRun) {
            console.log("First run detected, loading OOBE overlay...")

            // 加载 OOBE 覆盖层
            oobeLoader.source = "OOBEOverlay.qml"
            oobeLoader.visible = true
        }
    }
}
