import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: downloadDialog

    // ── 主题色 ──
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
    property int _activeCount: 0
    property int _completedCount: 0
    property int _maxThreads: 16
    property int _elapsedSeconds: 0
    property bool _refreshing: false

    // 稳定模型：按 task_id 就地更新，避免 Repeater 每秒销毁重建导致卡顿
    ListModel { id: taskModel }

    // 关键：不挡导航/页面切换（严重卡顿根因之一是遮罩吞掉点击）
    modal: false
    dim: false
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    title: ""

    padding: 0
    topPadding: 0
    bottomPadding: 0
    leftPadding: 0
    rightPadding: 0
    header: Item { implicitHeight: 0; height: 0; visible: false }
    footer: Item { implicitHeight: 0; height: 0; visible: false }

    // 不使用全屏 Overlay 烟幕；保持可点穿到主界面
    Overlay.modal: Item {}
    Overlay.modeless: Item {}

    width: _expanded
           ? Math.min(580, (parentWidth() - 48))
           : Math.min(440, (parentWidth() - 48))

    height: _expanded
            ? Math.min(520, parentHeight() - 64)
            : Math.max(64, contentColumn.implicitHeight)

    implicitHeight: height

    function parentWidth() {
        if (Overlay.overlay) return Overlay.overlay.width
        if (typeof window !== "undefined" && window) return window.width
        return 800
    }
    function parentHeight() {
        if (Overlay.overlay) return Overlay.overlay.height
        if (typeof window !== "undefined" && window) return window.height
        return 600
    }

    // 进度轮询：仅在可见时；间隔略放宽，配合信号增量更新
    Timer {
        id: refreshTimer
        interval: 1000
        repeat: true
        running: downloadDialog.visible
        onTriggered: refreshTasks(false)
    }

    // 秒表：有活跃下载时计时
    Timer {
        id: stopwatchTimer
        interval: 1000
        repeat: true
        running: downloadDialog.visible && _activeCount > 0
        onTriggered: _elapsedSeconds++
    }

    onOpened: {
        if (Backend && Backend.getMaxThread) {
            try { _maxThreads = Backend.getMaxThread() } catch (e) {}
        }
        refreshTasks(true)
    }
    onClosed: {
        refreshTimer.stop()
        stopwatchTimer.stop()
    }

    function _formatTime(totalSec) {
        var h = Math.floor(totalSec / 3600)
        var m = Math.floor((totalSec % 3600) / 60)
        var s = totalSec % 60
        var pad = function(n) { return n < 10 ? "0" + n : "" + n }
        return h > 0 ? pad(h) + ":" + pad(m) + ":" + pad(s) : pad(m) + ":" + pad(s)
    }

    function _progressValue(p) {
        var v = Number(p) || 0
        if (v > 0 && v <= 1.0) return v * 100
        return Math.max(0, Math.min(100, v))
    }

    function _parseSpeedEta(speedRaw) {
        var speedText = speedRaw || ""
        var etaText = ""
        if (speedText.indexOf("·") >= 0) {
            var parts = speedText.split("·")
            speedText = parts[0].trim()
            etaText = parts.slice(1).join("·").trim()
        } else if (speedText.indexOf("ETA") >= 0) {
            var idx = speedText.indexOf("ETA")
            etaText = speedText.substring(idx).trim()
            speedText = speedText.substring(0, idx).trim()
        }
        return { speed: speedText, eta: etaText }
    }

    function _loaderLabel(loader) {
        switch (loader) {
            case "fabric": return "Fabric"
            case "forge": return "Forge"
            case "neoforge": return "NeoForge"
            default: return ""
        }
    }

    function _taskTitleFrom(t) {
        var name = "Minecraft " + (t.version || "")
        var loader = _loaderLabel(t.loader)
        if (loader) name += " + " + loader
        if (t.version_name && t.version_name !== t.version)
            name += "  ·  " + t.version_name
        return name
    }

    function _statusLabel(status, statusText, errorMessage) {
        if (status === "queued")
            return Backend ? Backend.tr("排队中") : "排队中"
        if (status === "downloading")
            return statusText || (Backend ? Backend.tr("下载中...") : "下载中...")
        if (status === "paused")
            return Backend ? Backend.tr("已暂停") : "已暂停"
        if (status === "completed")
            return Backend ? Backend.tr("已完成") : "已完成"
        if (status === "failed")
            return (Backend ? Backend.tr("失败: ") : "失败: ") + (errorMessage || "")
        if (status === "cancelled")
            return Backend ? Backend.tr("已取消") : "已取消"
        return status || ""
    }

    function _statusColor(status) {
        switch (status) {
            case "completed": return _cSuccess
            case "failed":
            case "cancelled": return _cCritical
            case "paused":
            case "queued": return _cCaution
            default: return _cPrimary
        }
    }

    function _isLive(status) {
        return status === "downloading" || status === "paused" || status === "queued"
    }

    function _isTerminal(status) {
        return status === "completed" || status === "failed" || status === "cancelled"
    }

    function _rowObject(t) {
        var se = _parseSpeedEta(t.speed || "")
        var eta = t.eta || se.eta || ""
        return {
            task_id: t.task_id || "",
            version: t.version || "",
            version_name: t.version_name || "",
            loader: t.loader || "",
            status: t.status || "",
            progress: _progressValue(t.progress),
            status_text: t.status_text || "",
            status_label: _statusLabel(t.status, t.status_text, t.error_message),
            speed: se.speed,
            eta: eta,
            downloaded: t.downloaded || "",
            total: t.total || "",
            error_message: t.error_message || "",
            title: _taskTitleFrom(t)
        }
    }

    function _findIndexById(taskId) {
        for (var i = 0; i < taskModel.count; i++) {
            if (taskModel.get(i).task_id === taskId)
                return i
        }
        return -1
    }

    function _applyRowAt(index, row) {
        // set 会触发该行绑定更新，但不会销毁 delegate
        taskModel.set(index, row)
    }

    function refreshTasks(force) {
        if (!Backend || !Backend.getDownloadTasks) return
        if (_refreshing) return
        _refreshing = true
        try {
            var tasks = Backend.getDownloadTasks() || []
            var active = 0, completed = 0
            var seen = {}

            for (var i = 0; i < tasks.length; i++) {
                var row = _rowObject(tasks[i])
                seen[row.task_id] = true
                if (_isLive(row.status)) active++
                if (_isTerminal(row.status)) completed++

                var idx = _findIndexById(row.task_id)
                if (idx >= 0) {
                    var old = taskModel.get(idx)
                    // 仅在字段变化时 set，减少绑定抖动
                    if (force
                        || old.status !== row.status
                        || old.progress !== row.progress
                        || old.status_text !== row.status_text
                        || old.speed !== row.speed
                        || old.eta !== row.eta
                        || old.downloaded !== row.downloaded
                        || old.total !== row.total
                        || old.status_label !== row.status_label) {
                        _applyRowAt(idx, row)
                    }
                } else {
                    taskModel.append(row)
                }
            }

            // 移除已不存在的任务
            for (var j = taskModel.count - 1; j >= 0; j--) {
                var id = taskModel.get(j).task_id
                if (!seen[id])
                    taskModel.remove(j)
            }

            var prevActive = _activeCount
            _activeCount = active
            _completedCount = completed
            if (active > 0 && prevActive === 0)
                _elapsedSeconds = 0

            if (Backend && Backend.getMaxThread) {
                try { _maxThreads = Backend.getMaxThread() } catch (e2) {}
            }
        } catch (e) {
            console.log("[DownloadDialog] refresh error:", e)
        }
        _refreshing = false
    }

    function patchTaskProgress(taskId, progress, statusText, speed, downloaded, total) {
        var idx = _findIndexById(taskId)
        if (idx < 0) {
            // 未知任务，做一次全量同步
            refreshTasks(true)
            return
        }
        var se = _parseSpeedEta(speed || "")
        var prog = _progressValue(progress)
        var cur = taskModel.get(idx)
        var status = cur.status === "paused" || cur.status === "queued" ? cur.status : "downloading"
        taskModel.set(idx, {
            task_id: cur.task_id,
            version: cur.version,
            version_name: cur.version_name,
            loader: cur.loader,
            status: status,
            progress: prog,
            status_text: statusText || "",
            status_label: _statusLabel(status, statusText, cur.error_message),
            speed: se.speed,
            eta: se.eta || cur.eta,
            downloaded: downloaded || "",
            total: total || "",
            error_message: cur.error_message,
            title: cur.title
        })
    }

    function _anyDownloading() {
        for (var i = 0; i < taskModel.count; i++) {
            if (taskModel.get(i).status === "downloading") return true
        }
        return false
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

                // 秒表
                Text {
                    visible: _activeCount > 0
                    text: "⏱ " + _formatTime(_elapsedSeconds)
                    font.pixelSize: 12
                    font.family: "Consolas, monospace"
                    color: downloadDialog._cTextSecondary
                }

                Item { Layout.fillWidth: true }

                Button {
                    flat: true
                    text: _anyDownloading()
                          ? (Backend ? Backend.tr("全部暂停") : "全部暂停")
                          : (Backend ? Backend.tr("全部恢复") : "全部恢复")
                    visible: _activeCount > 0 && _expanded
                    onClicked: {
                        if (!Backend) return
                        for (var i = 0; i < taskModel.count; i++) {
                            var t = taskModel.get(i)
                            if (t.status === "downloading")
                                Backend.pauseDownloadTask(t.task_id)
                            else if (t.status === "paused")
                                Backend.resumeDownloadTask(t.task_id)
                        }
                        Qt.callLater(function() { refreshTasks(true) })
                    }
                }

                Button {
                    flat: true
                    icon.name: _expanded
                               ? "ic_fluent_chevron_down_20_regular"
                               : "ic_fluent_chevron_up_20_regular"
                    onClicked: _expanded = !_expanded
                }

                Button {
                    flat: true
                    icon.name: "ic_fluent_dismiss_20_regular"
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
            Layout.minimumHeight: _expanded ? 160 : 0
            visible: _expanded
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: Math.max(0, taskScroll.availableWidth - 16)
                x: 8
                spacing: 10

                Item { Layout.preferredHeight: 6; Layout.fillWidth: true }

                // 全局摘要：线程数 / 耗时
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 4
                    Layout.rightMargin: 4
                    spacing: 12
                    visible: taskModel.count > 0

                    Text {
                        text: (Backend ? Backend.tr("最大线程") : "最大线程") + ": " + _maxThreads
                        font.pixelSize: 11
                        color: downloadDialog._cTextSecondary
                    }
                    Text {
                        text: (Backend ? Backend.tr("耗时") : "耗时") + ": " + _formatTime(_elapsedSeconds)
                        font.pixelSize: 11
                        color: downloadDialog._cTextSecondary
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: (Backend ? Backend.tr("任务") : "任务")
                              + ": " + taskModel.count
                              + "  ·  "
                              + (Backend ? Backend.tr("进行中") : "进行中")
                              + " " + _activeCount
                        font.pixelSize: 11
                        color: downloadDialog._cTextSecondary
                    }
                }

                Repeater {
                    model: taskModel

                    delegate: Rectangle {
                        id: taskCard
                        // ListModel roles
                        required property string task_id
                        required property string version
                        required property string version_name
                        required property string loader
                        required property string status
                        required property real progress
                        required property string status_text
                        required property string status_label
                        required property string speed
                        required property string eta
                        required property string downloaded
                        required property string total
                        required property string error_message
                        required property string title
                        required property int index

                        Layout.fillWidth: true
                        implicitHeight: taskBody.implicitHeight + 24
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
                            anchors.margins: 14
                            spacing: 8

                            // 标题 + 百分比
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Text {
                                    text: title
                                    typography: Typography.Body
                                    font.weight: Font.DemiBold
                                    color: downloadDialog._cText
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                }

                                Text {
                                    text: downloadDialog._isLive(status)
                                          ? (Math.round(progress) + "%")
                                          : ""
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                    color: downloadDialog._cPrimary
                                    visible: downloadDialog._isLive(status)
                                }

                                Button {
                                    flat: true
                                    implicitWidth: 28
                                    implicitHeight: 28
                                    visible: downloadDialog._isTerminal(status)
                                    icon.name: "ic_fluent_dismiss_20_regular"
                                    onClicked: {
                                        if (Backend) Backend.removeDownloadTask(task_id)
                                        Qt.callLater(function() { refreshTasks(true) })
                                    }
                                }
                            }

                            // 详细状态行（完整 status_text，可换行）
                            Text {
                                Layout.fillWidth: true
                                text: status_label
                                font.pixelSize: 12
                                color: downloadDialog._statusColor(status)
                                wrapMode: Text.Wrap
                                maximumLineCount: 3
                                elide: Text.ElideRight
                            }

                            // 进度条
                            ProgressBar {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: progress
                                visible: downloadDialog._isLive(status) || status === "completed"
                                state: status === "paused" ? 1
                                     : (status === "failed" || status === "cancelled") ? 2
                                     : 0
                                indeterminate: status === "queued"
                                               || (status === "downloading" && progress <= 0)
                            }

                            // 大小 / 速度 / ETA
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                visible: downloadDialog._isLive(status)

                                Text {
                                    text: {
                                        if (downloaded && total)
                                            return downloaded + " / " + total
                                        return downloaded || total || ""
                                    }
                                    font.pixelSize: 11
                                    color: downloadDialog._cTextSecondary
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                }

                                Text {
                                    text: speed
                                    font.pixelSize: 11
                                    color: downloadDialog._cTextSecondary
                                    visible: speed && speed.length > 0
                                }

                                Text {
                                    text: eta
                                    font.pixelSize: 11
                                    color: downloadDialog._cTextSecondary
                                    visible: eta && eta.length > 0
                                }
                            }

                            // 操作
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                visible: status === "downloading" || status === "paused"

                                Item { Layout.fillWidth: true }

                                Button {
                                    text: status === "paused"
                                        ? (Backend ? Backend.tr("恢复") : "恢复")
                                        : (Backend ? Backend.tr("暂停") : "暂停")
                                    onClicked: {
                                        if (!Backend) return
                                        if (status === "paused")
                                            Backend.resumeDownloadTask(task_id)
                                        else
                                            Backend.pauseDownloadTask(task_id)
                                        Qt.callLater(function() { refreshTasks(true) })
                                    }
                                }

                                Button {
                                    text: Backend ? Backend.tr("终止") : "终止"
                                    onClicked: {
                                        if (!Backend) return
                                        Backend.cancelDownloadTask(task_id)
                                        Qt.callLater(function() { refreshTasks(true) })
                                    }
                                }
                            }
                        }
                    }
                }

                // 空态
                ColumnLayout {
                    visible: taskModel.count === 0
                    Layout.fillWidth: true
                    Layout.topMargin: 56
                    Layout.bottomMargin: 56
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
                        opacity: 0.85
                    }
                }

                Item { Layout.preferredHeight: 10; Layout.fillWidth: true }
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
                    if (_activeCount > 0)
                        parts.push("⏱ " + _formatTime(_elapsedSeconds))
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
                model: taskModel
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    required property string version
                    required property string status
                    required property real progress
                    required property string status_text
                    visible: status === "downloading" || status === "paused" || status === "queued"

                    Text {
                        text: "MC " + (version || "")
                        font.pixelSize: 11
                        color: downloadDialog._cText
                        elide: Text.ElideRight
                        Layout.preferredWidth: 90
                    }

                    ProgressBar {
                        from: 0
                        to: 100
                        value: progress
                        Layout.fillWidth: true
                        Layout.preferredHeight: 4
                        state: status === "paused" ? 1 : 0
                        indeterminate: status === "queued" || (status === "downloading" && progress <= 0)
                    }

                    Text {
                        text: status === "paused"
                              ? (Backend ? Backend.tr("暂停") : "暂停")
                              : (Math.round(progress) + "%")
                        font.pixelSize: 10
                        color: downloadDialog._cTextSecondary
                        Layout.preferredWidth: 40
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }
    }

    Connections {
        target: Backend
        function onDownloadTaskAdded(taskId) {
            refreshTasks(true)
            if (!downloadDialog.visible) {
                // 新任务：默认展开打开，但不遮挡主界面
                _expanded = true
                downloadDialog.open()
            }
        }
        function onDownloadTaskRemoved(taskId) {
            refreshTasks(true)
            if (_activeCount === 0 && _completedCount === 0 && downloadDialog.visible)
                downloadDialog.close()
        }
        function onDownloadTaskProgressUpdated(taskId, progress, statusText, speed, downloaded, total) {
            if (!downloadDialog.visible) return
            // 信号增量更新，避免整表重建
            patchTaskProgress(taskId, progress, statusText, speed, downloaded, total)
        }
        function onDownloadCompleted(message) {
            refreshTasks(true)
        }
        function onDownloadPaused(paused) {
            refreshTasks(true)
        }
    }
}
