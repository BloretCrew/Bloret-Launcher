import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: downloadDialog

    property bool _expanded: true
    property var _tasks: []           // 缓存的任务列表
    property int _activeCount: 0      // 活跃任务数
    property int _completedCount: 0   // 已完成任务数

    modal: true
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.NoButton

    width: _expanded ? 560 : 400
    height: _expanded ? Math.min(520, contentHeight) : 80

    // 定时刷新任务列表
    Timer {
        id: refreshTimer
        interval: 800
        repeat: true
        running: visible
        onTriggered: refreshTasks()
    }

    // 初始刷新
    onOpened: {
        refreshTasks()
        refreshTimer.start()
    }
    onClosed: {
        refreshTimer.stop()
    }

    function refreshTasks() {
        if (!Backend || !Backend.getDownloadTasks) return
        try {
            _tasks = Backend.getDownloadTasks()
            // 计算统计
            var active = 0, completed = 0
            for (var i = 0; i < _tasks.length; i++) {
                var s = _tasks[i].status
                if (s === "downloading" || s === "paused") active++
                if (s === "completed" || s === "failed" || s === "cancelled") completed++
            }
            _activeCount = active
            _completedCount = completed
        } catch (e) {
            console.log("[DownloadDialog] refresh error:", e)
        }
    }

    function _statusText(task) {
        if (task.status === "downloading") return task.status_text || (Backend ? Backend.tr("下载中...") : "下载中...")
        if (task.status === "paused") return Backend ? Backend.tr("已暂停") : "已暂停"
        if (task.status === "completed") return Backend ? Backend.tr("已完成 ✓") : "已完成 ✓"
        if (task.status === "failed") return (Backend ? Backend.tr("失败: ") : "失败: ") + task.error_message
        if (task.status === "cancelled") return Backend ? Backend.tr("已取消") : "已取消"
        return task.status
    }

    function _loaderLabel(loader) {
        switch (loader) {
            case "fabric": return "Fabric"
            case "forge": return "Forge"
            case "neoforge": return "NeoForge"
            default: return ""
        }
    }

    function _timeStr(seconds) {
        var m = Math.floor(seconds / 60)
        var s = Math.floor(seconds % 60)
        var pad = function(n) { return n < 10 ? "0" + n : "" + n }
        return (m > 0 ? pad(m) + ":" : "") + pad(s)
    }

    contentItem: ColumnLayout {
        spacing: 0

        // ── 标题栏（展开/收起）──
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 8

                Text {
                    text: Backend ? Backend.tr("下载管理") : "下载管理"
                    typography: Typography.Subtitle
                    color: Theme.currentTheme.colors.textColor
                }

                // 活跃数胶囊
                Rectangle {
                    visible: _activeCount > 0
                    height: 20
                    radius: 10
                    color: Theme.accentColor || "#3b82f6"
                    implicitWidth: badgeText.implicitWidth + 16
                    Text {
                        id: badgeText
                        anchors.centerIn: parent
                        text: _activeCount.toString()
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        color: "#ffffff"
                    }
                }

                Item { Layout.fillWidth: true }

                // 全部暂停 / 全部恢复
                Button {
                    id: bulkPauseBtn
                    flat: true
                    text: _anyDownloading() ? (Backend ? Backend.tr("全部暂停") : "全部暂停")
                                            : (Backend ? Backend.tr("全部恢复") : "全部恢复")
                    visible: _activeCount > 0 && _expanded
                    onClicked: {
                        for (var i = 0; i < _tasks.length; i++) {
                            var t = _tasks[i]
                            if (t.status === "downloading")
                                Backend.pauseDownloadTask(t.task_id)
                            else if (t.status === "paused")
                                Backend.resumeDownloadTask(t.task_id)
                        }
                        refreshTasks()
                    }
                }

                // 收起/展开
                Button {
                    flat: true
                    icon.name: _expanded ? "ic_fluent_chevron_down_20_regular" : "ic_fluent_chevron_up_20_regular"
                    onClicked: {
                        _expanded = !_expanded
                    }
                }

                // 关闭
                Button {
                    flat: true
                    icon.name: "ic_fluent_dismiss_20_regular"
                    onClicked: downloadDialog.close()
                }
            }
        }

        // ── 分隔线 ──
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.currentTheme.colors.controlBorderColor
            visible: _expanded
        }

        // ── 展开态：任务列表 ──
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: _expanded
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                width: parent.availableWidth - 16
                x: 8
                spacing: 2

                Repeater {
                    model: _tasks

                    delegate: Rectangle {
                        id: taskCard
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskBody.implicitHeight + 20
                        radius: 8
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        ColumnLayout {
                            id: taskBody
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 6

                            // 标题行
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6

                                Text {
                                    text: {
                                        var name = "Minecraft " + modelData.version
                                        var loader = _loaderLabel(modelData.loader)
                                        if (loader) name += " + " + loader
                                        return name
                                    }
                                    typography: Typography.Body
                                    font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                // 状态文本
                                Text {
                                    text: _statusText(modelData)
                                    font.pixelSize: 11
                                    color: {
                                        switch (modelData.status) {
                                            case "completed": return "#10b981"
                                            case "failed": case "cancelled": return "#ef4444"
                                            case "paused": return "#f59e0b"
                                            default: return Theme.currentTheme.colors.textSecondaryColor
                                        }
                                    }
                                }

                                // 关闭/移除按钮
                                Button {
                                    flat: true
                                    visible: modelData.status === "completed"
                                           || modelData.status === "failed"
                                           || modelData.status === "cancelled"
                                    icon.name: "ic_fluent_dismiss_20_regular"
                                    onClicked: {
                                        if (Backend) Backend.removeDownloadTask(modelData.task_id)
                                        refreshTasks()
                                    }
                                }
                            }

                            // 进度条
                            ProgressBar {
                                id: taskProgress
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: modelData.progress
                                visible: modelData.status === "downloading" || modelData.status === "paused"
                            }

                            // 进度信息行
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                visible: modelData.status === "downloading" || modelData.status === "paused"

                                Text {
                                    text: (modelData.downloaded || "") + (modelData.downloaded && modelData.total ? " / " : "") + (modelData.total || "")
                                    typography: Typography.Caption
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }

                                Item { Layout.fillWidth: true }

                                Text {
                                    text: modelData.speed || ""
                                    typography: Typography.Caption
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }

                                Text {
                                    text: modelData.eta || ""
                                    typography: Typography.Caption
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }

                            // 操作按钮行
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                visible: modelData.status === "downloading"
                                      || modelData.status === "paused"

                                Item { Layout.fillWidth: true }

                                Button {
                                    flat: true
                                    text: modelData.status === "paused"
                                        ? (Backend ? Backend.tr("恢复") : "恢复")
                                        : (Backend ? Backend.tr("暂停") : "暂停")
                                    onClicked: {
                                        if (!Backend) return
                                        if (modelData.status === "paused")
                                            Backend.resumeDownloadTask(modelData.task_id)
                                        else
                                            Backend.pauseDownloadTask(modelData.task_id)
                                        refreshTasks()
                                    }
                                }

                                Button {
                                    flat: true
                                    text: Backend ? Backend.tr("终止") : "终止"
                                    onClicked: {
                                        if (!Backend) return
                                        Backend.cancelDownloadTask(modelData.task_id)
                                        refreshTasks()
                                    }
                                }
                            }
                        }
                    }
                }

                // 空态提示
                Text {
                    visible: _tasks.length === 0
                    Layout.fillWidth: true
                    Layout.topMargin: 40
                    horizontalAlignment: Text.AlignHCenter
                    text: Backend ? Backend.tr("没有下载任务") : "没有下载任务"
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 14
                }
            }
        }

        // ── 收起态：紧凑摘要 ──
        ColumnLayout {
            visible: !_expanded
            Layout.fillWidth: true
            Layout.margins: 8
            spacing: 2

            Text {
                text: {
                    var parts = []
                    if (_activeCount > 0) parts.push((Backend ? Backend.tr("下载中") : "下载中") + " (" + _activeCount + ")")
                    if (_completedCount > 0) parts.push((Backend ? Backend.tr("已完成") : "已完成") + " (" + _completedCount + ")")
                    return parts.length > 0 ? parts.join(" · ") : (Backend ? Backend.tr("没有下载任务") : "没有下载任务")
                }
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            // 显示每个活跃任务的摘要
            Repeater {
                model: {
                    var active = []
                    for (var i = 0; i < _tasks.length; i++) {
                        if (_tasks[i].status === "downloading" || _tasks[i].status === "paused")
                            active.push(_tasks[i])
                    }
                    return active
                }
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    required property var modelData

                    Text {
                        text: "Minecraft " + modelData.version
                        font.pixelSize: 11
                        color: Theme.currentTheme.colors.textColor
                        elide: Text.ElideRight
                        Layout.preferredWidth: 120
                    }

                    ProgressBar {
                        from: 0
                        to: 100
                        value: modelData.progress
                        Layout.fillWidth: true
                        height: 6
                    }

                    Text {
                        text: Math.round(modelData.progress) + "%"
                        font.pixelSize: 10
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.preferredWidth: 32
                    }
                }
            }
        }
    }

    function _anyDownloading() {
        for (var i = 0; i < _tasks.length; i++) {
            if (_tasks[i].status === "downloading") return true
        }
        return false
    }

    // 自动显示/隐藏：有活跃任务时自动弹出，全部完成后自动收起
    Connections {
        target: Backend
        function onDownloadTaskAdded(taskId) {
            refreshTasks()
            if (!downloadDialog.visible) {
                downloadDialog.open()
            }
        }
        function onDownloadTaskRemoved(taskId) {
            refreshTasks()
            if (_activeCount === 0 && _completedCount === 0) {
                downloadDialog.close()
            }
        }
    }
}
