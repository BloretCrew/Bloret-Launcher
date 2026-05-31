import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: downloadDialog

    property string downloadTitle: ""
    property string downloadStatus: ""
    property double downloadProgress: 0.0
    property string downloadSpeed: ""
    property string downloadedSize: ""
    property string totalSize: ""
    property bool isPaused: false
    property int maxThreads: 64
    property bool isCompleted: false

    // 秒表
    property int _elapsedSeconds: 0
    property string _elapsedText: _formatTime(_elapsedSeconds)

    modal: true
    closePolicy: Popup.NoAutoClose
    standardButtons: Dialog.Close

    width: 500

    signal pauseClicked()
    signal cancelClicked()

    // 秒表计时器
    Timer {
        id: stopwatchTimer
        interval: 1000
        repeat: true
        running: false
        onTriggered: _elapsedSeconds++
    }

    function _formatTime(totalSec) {
        var h = Math.floor(totalSec / 3600)
        var m = Math.floor((totalSec % 3600) / 60)
        var s = totalSec % 60
        var pad = function(n) { return n < 10 ? "0" + n : "" + n }
        return h > 0 ? pad(h) + ":" + pad(m) + ":" + pad(s) : pad(m) + ":" + pad(s)
    }

    // 标题行 + 秒表（替代 header 和 title，避免 RinUI Dialog 内置标题重复）
    contentItem: ColumnLayout {
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: downloadTitle
                typography: Typography.Subtitle
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Label {
                text: "⏱ " + _elapsedText
                font.pixelSize: 13
                font.family: "Consolas, monospace"
                color: isCompleted ? Theme.currentTheme.colors.systemSuccessColor : Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignVCenter
            }
        }

        Text {
            text: downloadStatus
            typography: Typography.Body
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            from: 0
            to: 100
            value: downloadProgress
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: downloadedSize + " / " + totalSize
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Item { Layout.fillWidth: true }

            Text {
                text: downloadSpeed
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: Backend ? Backend.tr("最大线程数") : "最大线程数"
                typography: Typography.Caption
            }

            Text {
                text: maxThreads.toString()
                typography: Typography.Caption
                font.weight: Font.DemiBold
            }

            Item { Layout.fillWidth: true }

            Button {
                visible: !isCompleted
                text: isPaused ? (Backend ? Backend.tr("恢复") : "恢复") : (Backend ? Backend.tr("暂停") : "暂停")
                onClicked: downloadDialog.pauseClicked()
            }

            Button {
                visible: !isCompleted
                text: Backend ? Backend.tr("终止") : "终止"
                onClicked: downloadDialog.cancelClicked()
            }
        }
    }
    
    function updateProgress(progress, status, speed, downloaded, total) {
        downloadProgress = progress
        downloadStatus = status
        downloadSpeed = speed
        downloadedSize = downloaded
        totalSize = total
        // 首次收到进度时启动秒表
        if (!stopwatchTimer.running && !isCompleted) {
            stopwatchTimer.start()
        }
    }

    function setPaused(paused) {
        isPaused = paused
    }

    function setCompleted(message) {
        isCompleted = true
        stopwatchTimer.stop()
        downloadProgress = 100
        downloadStatus = message || (Backend ? Backend.tr("安装完成") : "安装完成")
    }

    function resetDialog() {
        isCompleted = false
        _elapsedSeconds = 0
        stopwatchTimer.stop()
        downloadProgress = 0
        downloadStatus = ""
        downloadSpeed = ""
        downloadedSize = ""
        totalSize = ""
    }

    onClosed: {
        if (!isCompleted) {
            cancelClicked()
        }
    }
}
