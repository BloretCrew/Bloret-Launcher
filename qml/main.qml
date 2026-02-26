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

    navigationItems: [
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
            position: Position.Bottom
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

    DownloadDialog {
        id: downloadDialog
        
        onPauseClicked: {
            if (Backend) Backend.toggleDownloadPause()
        }
        
        onCancelClicked: {
            if (Backend) Backend.cancelDownload()
        }
    }

    Connections {
        target: Backend
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
}
