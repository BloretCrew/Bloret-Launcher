import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "components"

FluentWindow {
    id: window
    visible: true
    title: qsTr("Bloret Launcher")
    width: 1000
    height: 700
    minimumWidth: 800
    minimumHeight: 600

    navigationView.navExpandWidth: 200

    property var navItems: [
        {
            title: qsTr("主页"),
            page: Qt.resolvedUrl("pages/Home.qml"),
            icon: "ic_fluent_home_20_regular",
            position: Position.Top
        },
        {
            title: qsTr("通行证"),
            page: Qt.resolvedUrl("pages/PassPort.qml"),
            icon: "ic_fluent_person_20_regular",
            position: Position.Bottom,
            passportItem: true  // 标记为通行证项
        },
        {
            title: qsTr("下载"),
            page: Qt.resolvedUrl("pages/Download.qml"),
            icon: "ic_fluent_arrow_download_20_regular"
        },
        {
            title: qsTr("小工具"),
            page: Qt.resolvedUrl("pages/Tools.qml"),
            icon: "ic_fluent_wrench_20_regular"
        },
        {
            title: qsTr("Mods"),
            page: Qt.resolvedUrl("pages/Mods.qml"),
            icon: "ic_fluent_puzzle_piece_20_regular"
        },
        {
            title: qsTr("联机"),
            page: Qt.resolvedUrl("pages/Multiplayer.qml"),
            icon: "ic_fluent_plug_connected_20_regular"
        },
        {
            title: qsTr("设置"),
            page: Qt.resolvedUrl("pages/Settings.qml"),
            icon: "ic_fluent_settings_20_regular",
            position: Position.Bottom
        },
        {
            title: qsTr("关于"),
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
                    navItems[i].title = qsTr("通行证")
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
            downloadDialog.downloadTitle = title
            downloadDialog.downloadProgress = 0
            downloadDialog.downloadStatus = Backend ? Backend.tr("准备下载...") : "准备下载..."
            downloadDialog.downloadSpeed = ""
            downloadDialog.downloadedSize = ""
            downloadDialog.totalSize = ""
            downloadDialog.isPaused = false
            downloadDialog.open()
        }
        
        function onDownloadProgressUpdated(progress, status, speed, downloaded, total) {
            downloadDialog.updateProgress(progress, status, speed, downloaded, total)
        }
        
        function onDownloadDialogClosed() {
            downloadDialog.close()
        }
        
        function onDownloadPaused(paused) {
            downloadDialog.setPaused(paused)
        }
    }
    
    Component.onCompleted: {
        updatePassPortNavigation()
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

    LaunchProgressDialog {
        id: launchProgressDialog
    }
}
