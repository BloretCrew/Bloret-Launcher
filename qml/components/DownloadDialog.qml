import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: downloadDialog

    // ── 主题色（避免 Theme.accentColor 不存在）──
    readonly property color _cPrimary: Theme.currentTheme.colors.primaryColor
    readonly property color _cText: Theme.currentTheme.colors.textColor
    readonly property color _cTextSecondary: Theme.currentTheme.colors.textSecondaryColor
    readonly property color _cCard: Theme.currentTheme.colors.cardColor
    readonly property color _cBorder: Theme.currentTheme.colors.controlBorderColor
        || Theme.currentTheme.colors.cardBorderColor
    readonly property color _cSuccess: Theme.currentTheme.colors.systemSuccessColor || "#10b981"
    readonly property color _cCaution: Theme.currentTheme.colors.systemCautionColor || "#f59e0b"
    readonly property color _cCritical: Theme.currentTheme.colors.systemCriticalColor || "#ef4444"

    property bool _expanded: true
    property var _tasks: []
    property int _activeCount: 0
    property int _completedCount: 0

    // 下载管理应允许后台继续操作主界面
    modal: false
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    title: ""

    // RinUI Dialog 默认 padding:24 + footer DialogButtonBox padding:24，
    // 会把收起态高度 80 压到几乎不可见；清空边距与空 footer。
    padding: 0
    topPadding: 0
    bottomPadding: 0
    leftPadding: 0
    rightPadding: 0
    header: Item { implicitHeight: 0; height: 0; visible: false }
    footer: Item { implicitHeight: 0; height: 0; visible: false }

    width: _expanded
           ? Math.min(560, (Overlay.overlay ? Overlay.overlay.width : 560) - 48)
           : Math.min(420, (Overlay.overlay ? Overlay.overlay.width : 420) - 48)

    // 展开固定可视高度；收起随内容自适应（标题栏 + 摘要）
    height: _expanded
            ? Math.min(480, (Overlay.overlay ? Overlay.overlay.height : 480) - 80)
            : Math.max(56, contentColumn.implicitHeight)
    implicitHeight: height

    Timer {
        id: refreshTimer
        interval: 800
        repeat: true
        running: visible
        onTriggered: refreshTasks()
    }

    onOpened: {
        _expanded = true
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
            var active = 0, completed = 0
            for (var i = 0; i < _tasks.length; i++) {
                var s = _tasks[i].status
                if (s === "downloading" || s === "paused" || s === "queued")
                    active++
                if (s === "completed" || s === "failed" || s === "cancelled")
                    completed++
            }
            _activeCount = active
            _completedCount = completed
        } catch (e) {
            console.log("[DownloadDialog] refresh error:", e)
        }
    }

    function _statusText(task) {
        if (!task) return ""
        if (task.status === "queued")
            return Backend ? Backend.tr("排队中") : "排队中"
        if (task.status === "downloading")
            return task.status_text || (Backend ? Backend.tr("下载中...") : "下载中...")
        if (task.status === "paused")
            return Backend ? Backend.tr("已暂停") : "已暂停"
        if (task.status === "completed")
            return Backend ? Backend.tr("已完成") : "已完成"
        if (task.status === "failed")
            return (Backend ? Backend.tr("失败: ") : "失败: ") + (task.error_message || "")
        if (task.status === "cancelled")
            return Backend ? Backend.tr("已取消") : "已取消"
        return task.status || ""
    }

    function _statusColor(status) {
        switch (status) {
            case "completed": return _cSuccess
            case "failed":
            case "cancelled": return _cCritical
            case "paused":
            case "queued": return _cCaution
            default: return _cTextSecondary
        }
    }

    function _loaderLabel(loader) {
        switch (loader) {
            case "fabric": return "Fabric"
            case "forge": return "Forge"
            case "neoforge": return "NeoForge"
            default: return ""
        }
    }

    function _taskTitle(task) {
        if (!task) return ""
        var name = "Minecraft " + (task.version || "")
        var loader = _loaderLabel(task.loader)
        if (loader) name += " + " + loader
        if (task.version_name && task.version_name !== task.version)
            name += " (" + task.version_name + ")"
        return name
    }

    function _progressValue(task) {
        if (!task) return 0
        var p = Number(task.progress) || 0
        // 兼容 0–1 与 0–100 两种进度尺度
        if (p > 0 && p <= 1.0)
            return p * 100
        return Math.max(0, Math.min(100, p))
    }

    function _anyDownloading() {
        for (var i = 0; i < _tasks.length; i++) {
            if (_tasks[i].status === "downloading") return true
        }
        return false
    }

    function _activeTasks() {
        var active = []
        for (var i = 0; i < _tasks.length; i++) {
            var s = _tasks[i].status
            if (s === "downloading" || s === "paused" || s === "queued")
                active.push(_tasks[i])
        }
        return active
    }

    function _isLive(status) {
        return status === "downloading" || status === "paused" || status === "queued"
    }

    function _isTerminal(status) {
        return status === "completed" || status === "failed" || status === "cancelled"
    }

    contentItem: ColumnLayout {
        id: contentColumn
        spacing: 0

        // ── 标题栏 ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 8
                spacing: 8

                Text {
                    text: Backend ? Backend.tr("下载管理") : "下载管理"
                    typography: Typography.Subtitle
                    color: downloadDialog._cText
                }

                // 活跃数胶囊
                Rectangle {
                    visible: _activeCount > 0
                    Layout.preferredHeight: 20
                    Layout.preferredWidth: Math.max(20, badgeText.implicitWidth + 14)
                    implicitHeight: 20
                    implicitWidth: Math.max(20, badgeText.implicitWidth + 14)
                    radius: 10
                    color: downloadDialog._cPrimary
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

                Button {
                    id: bulkPauseBtn
                    flat: true
                    text: _anyDownloading()
                          ? (Backend ? Backend.tr("全部暂停") : "全部暂停")
                          : (Backend ? Backend.tr("全部恢复") : "全部恢复")
                    visible: _activeCount > 0 && _expanded
                    onClicked: {
                        if (!Backend) return
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

                Button {
                    flat: true
                    icon.name: _expanded
                               ? "ic_fluent_chevron_down_20_regular"
                               : "ic_fluent_chevron_up_20_regular"
                    ToolTip.visible: hovered
                    ToolTip.text: _expanded
                                  ? (Backend ? Backend.tr("收起") : "收起")
                                  : (Backend ? Backend.tr("展开") : "展开")
                    onClicked: _expanded = !_expanded
                }

                Button {
                    flat: true
                    icon.name: "ic_fluent_dismiss_20_regular"
                    ToolTip.visible: hovered
                    ToolTip.text: Backend ? Backend.tr("关闭") : "关闭"
                    onClicked: downloadDialog.close()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            implicitHeight: 1
            color: downloadDialog._cBorder
            visible: _expanded
        }

        // ── 展开：任务列表 ──
        ScrollView {
            id: taskScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: _expanded ? 120 : 0
            visible: _expanded
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                // 绑定到 ScrollView.availableWidth，避免 parent.availableWidth 为 0
                width: Math.max(0, taskScroll.availableWidth - 16)
                x: 8
                spacing: 8

                // 顶部内边距
                Item { Layout.preferredHeight: 4; Layout.fillWidth: true }

                Repeater {
                    model: _tasks

                    delegate: Rectangle {
                        id: taskCard
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        // 高度由内容驱动，避免 anchors.fill 与 preferredHeight 环依赖
                        implicitHeight: taskBody.implicitHeight + 20
                        Layout.preferredHeight: implicitHeight
                        radius: 8
                        color: downloadDialog._cCard
                        border.color: downloadDialog._cBorder
                        border.width: 1

                        ColumnLayout {
                            id: taskBody
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 12
                            spacing: 8

                            // 标题行
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Text {
                                    text: downloadDialog._taskTitle(modelData)
                                    typography: Typography.Body
                                    font.weight: Font.DemiBold
                                    color: downloadDialog._cText
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                }

                                Text {
                                    text: downloadDialog._statusText(modelData)
                                    font.pixelSize: 11
                                    color: downloadDialog._statusColor(modelData.status)
                                    elide: Text.ElideRight
                                    Layout.maximumWidth: 160
                                    horizontalAlignment: Text.AlignRight
                                }

                                Button {
                                    flat: true
                                    implicitWidth: 28
                                    implicitHeight: 28
                                    visible: downloadDialog._isTerminal(modelData.status)
                                    icon.name: "ic_fluent_dismiss_20_regular"
                                    onClicked: {
                                        if (Backend) Backend.removeDownloadTask(modelData.task_id)
                                        refreshTasks()
                                    }
                                }
                            }

                            // 进度条
                            ProgressBar {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: downloadDialog._progressValue(modelData)
                                visible: downloadDialog._isLive(modelData.status)
                                // RinUI ProgressBar.State: 0 Running, 1 Paused, 2 Error
                                state: modelData.status === "paused" ? 1 : 0
                                indeterminate: modelData.status === "queued"
                                               || (modelData.status === "downloading"
                                                   && downloadDialog._progressValue(modelData) <= 0)
                            }

                            // 进度信息
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                visible: downloadDialog._isLive(modelData.status)

                                Text {
                                    text: {
                                        var d = modelData.downloaded || ""
                                        var t = modelData.total || ""
                                        if (d && t) return d + " / " + t
                                        return d || t || ""
                                    }
                                    typography: Typography.Caption
                                    color: downloadDialog._cTextSecondary
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                }

                                Text {
                                    text: modelData.speed || ""
                                    typography: Typography.Caption
                                    color: downloadDialog._cTextSecondary
                                    visible: !!(modelData.speed)
                                }

                                Text {
                                    text: modelData.eta || ""
                                    typography: Typography.Caption
                                    color: downloadDialog._cTextSecondary
                                    visible: !!(modelData.eta)
                                }

                                Text {
                                    text: Math.round(downloadDialog._progressValue(modelData)) + "%"
                                    typography: Typography.Caption
                                    font.weight: Font.DemiBold
                                    color: downloadDialog._cTextSecondary
                                    visible: modelData.status !== "queued"
                                             && !(modelData.status === "downloading"
                                                  && downloadDialog._progressValue(modelData) <= 0)
                                }
                            }

                            // 操作
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

                // 空态
                ColumnLayout {
                    visible: _tasks.length === 0
                    Layout.fillWidth: true
                    Layout.topMargin: 48
                    Layout.bottomMargin: 48
                    spacing: 8

                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        text: Backend ? Backend.tr("没有下载任务") : "没有下载任务"
                        color: downloadDialog._cTextSecondary
                        font.pixelSize: 14
                    }

                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        text: Backend ? Backend.tr("从下载页添加版本后将显示在这里") : "从下载页添加版本后将显示在这里"
                        color: downloadDialog._cTextSecondary
                        font.pixelSize: 12
                        opacity: 0.8
                    }
                }

                Item { Layout.preferredHeight: 8; Layout.fillWidth: true }
            }
        }

        // ── 收起：紧凑摘要 ──
        ColumnLayout {
            visible: !_expanded
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.bottomMargin: 12
            spacing: 6

            Text {
                Layout.fillWidth: true
                text: {
                    var parts = []
                    if (_activeCount > 0)
                        parts.push((Backend ? Backend.tr("下载中") : "下载中") + " (" + _activeCount + ")")
                    if (_completedCount > 0)
                        parts.push((Backend ? Backend.tr("已完成") : "已完成") + " (" + _completedCount + ")")
                    return parts.length > 0
                           ? parts.join(" · ")
                           : (Backend ? Backend.tr("没有下载任务") : "没有下载任务")
                }
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: downloadDialog._cText
                elide: Text.ElideRight
            }

            Repeater {
                model: {
                    var active = downloadDialog._activeTasks()
                    return active.slice(0, 3)
                }
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    required property var modelData

                    Text {
                        text: "Minecraft " + (modelData.version || "")
                        font.pixelSize: 11
                        color: downloadDialog._cText
                        elide: Text.ElideRight
                        Layout.preferredWidth: 110
                        Layout.maximumWidth: 140
                    }

                    ProgressBar {
                        from: 0
                        to: 100
                        value: downloadDialog._progressValue(modelData)
                        Layout.fillWidth: true
                        Layout.preferredHeight: 4
                        state: modelData.status === "paused" ? 1 : 0
                        indeterminate: modelData.status === "queued"
                    }

                    Text {
                        text: Math.round(downloadDialog._progressValue(modelData)) + "%"
                        font.pixelSize: 10
                        color: downloadDialog._cTextSecondary
                        Layout.preferredWidth: 36
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }
    }

    Connections {
        target: Backend
        function onDownloadTaskAdded(taskId) {
            refreshTasks()
            if (!downloadDialog.visible)
                downloadDialog.open()
        }
        function onDownloadTaskRemoved(taskId) {
            // 后端在任务结束时也会 emit 此信号（任务仍保留在列表中一段时间）
            refreshTasks()
            if (_activeCount === 0 && _completedCount === 0 && downloadDialog.visible)
                downloadDialog.close()
        }
    }
}
