import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: downloadPage
    title: (Backend ? Backend.tr("下载") : "下载")

    // ── 主题色别名（消除不存在的 Theme.accentColor 引用）──
    readonly property color _cPrimary: Theme.currentTheme.colors.primaryColor
    readonly property color _cText: Theme.currentTheme.colors.textColor
    readonly property color _cTextSecondary: Theme.currentTheme.colors.textSecondaryColor
    readonly property color _cCard: Theme.currentTheme.colors.cardColor
    readonly property color _cCardBorder: Theme.currentTheme.colors.cardBorderColor
    readonly property color _cCaution: Theme.currentTheme.colors.systemCautionColor
    readonly property color _cSuccess: Theme.currentTheme.colors.systemSuccessColor

    // ── 下载源（配置映射）──
    property string _currentSource: Backend ? Backend.getDownloadSource() : "gitcode"

    function _sourceLabel(source) {
        switch (source) {
            case "gitcode": return "Bloret"
            case "bmclapi": return "BMCLAPI"
            case "official": return "Mojang Official"
            default: return source || "Bloret"
        }
    }

    function _sourceColor(source) {
        switch (source) {
            case "gitcode": return "Success"
            case "bmclapi": return "Info"
            case "official": return "Warning"
            default: return "Info"
        }
    }

    // 下载源 Badge 放到页面头部右侧
    extraHeaderItems: Badge {
        text: downloadPage._sourceLabel(downloadPage._currentSource)
        colorType: downloadPage._sourceColor(downloadPage._currentSource)
    }

    // 配置变更监听
    Connections {
        target: Backend
        function onConfigChanged(key, value) {
            if (key === "download_source" || key === "*") {
                _currentSource = Backend.getDownloadSource()
            }
        }
        function onImportInstancesReady(items) {
            importableInstances = items || []
            importStatusText = importableInstances.length
                ? ((Backend ? Backend.tr("找到实例") : "找到实例") + ": " + importableInstances.length)
                : (Backend ? Backend.tr("未找到可导入实例") : "未找到可导入实例")
        }
        function onImportInstanceFinished(ok, name, message) {
            importStatusText = ok
                ? ((Backend ? Backend.tr("导入成功") : "导入成功") + ": " + name + (message ? (" — " + message) : ""))
                : ((Backend ? Backend.tr("导入失败") : "导入失败") + ": " + (message || name || ""))
            if (ok && Backend && Backend.invalidateLaunchItemsCache)
                Backend.invalidateLaunchItemsCache()
        }
    }

    property var importableInstances: []
    property string importBasePath: ""
    property string importStatusText: ""
    property string importTargetName: ""

    // ── 下载任务状态（稳定 ListModel，避免每秒销毁重建）──
    property int _dlActive: 0
    ListModel { id: dlStatusModel }

    // StackView 保留历史页；仅当前活动页轮询，避免切页时多实例同时刷 Backend 卡死
    readonly property bool isActivePage: {
        if (downloadPage.StackView.view)
            return downloadPage.StackView.status === StackView.Active
        return downloadPage.visible
    }

    function _progressPct(p) {
        var v = Number(p) || 0
        if (v > 0 && v <= 1.0) return v * 100
        return Math.max(0, Math.min(100, v))
    }

    function _findDlStatusIndex(taskId) {
        for (var i = 0; i < dlStatusModel.count; i++) {
            if (dlStatusModel.get(i).task_id === taskId)
                return i
        }
        return -1
    }

    function refreshDlStatusBar() {
        if (!Backend || !Backend.getDownloadTasks) return
        // 页面不可见时也允许同步一次（从其它页返回时 onIsActivePageChanged 会再刷）
        try {
            var tasks = Backend.getDownloadTasks() || []
            var live = []
            for (var i = 0; i < tasks.length; i++) {
                var t = tasks[i]
                var s = (t && t.status) ? String(t.status) : ""
                if (s === "downloading" || s === "paused" || s === "queued")
                    live.push(t)
            }
            // 以任务列表为准；getActiveDownloadCount 作兜底
            var counted = Backend.getActiveDownloadCount
                          ? Backend.getActiveDownloadCount()
                          : live.length
            _dlActive = Math.max(live.length, counted)

            // 全量重建最多 3 条，避免 set/append 角色不同步导致空列表
            var next = live.slice(0, 3)
            // 若 count 有活跃但列表过滤后为空，仍展示原始任务前几条
            if (next.length === 0 && _dlActive > 0) {
                next = tasks.slice(0, Math.min(3, tasks.length))
            }

            dlStatusModel.clear()
            for (var k = 0; k < next.length; k++) {
                var item = next[k] || {}
                dlStatusModel.append({
                    task_id: item.task_id || ("tmp-" + k),
                    version: item.version || "",
                    status: item.status || "downloading",
                    progress: _progressPct(item.progress),
                    status_text: item.status_text || "",
                    speed: item.speed || ""
                })
            }
        } catch (e) {
            console.log("[Download] status bar refresh error:", e)
        }
    }

    Timer {
        id: dlBarTimer
        interval: 1200
        repeat: true
        // 仅活动页且有可见任务时跑；没有活动任务时仍低频探测一次（_dlActive 可能从 0 变 1）
        running: downloadPage.isActivePage
        onTriggered: refreshDlStatusBar()
    }

    onIsActivePageChanged: {
        if (isActivePage)
            refreshDlStatusBar()
    }

    Connections {
        target: Backend
        enabled: downloadPage.isActivePage
        function onDownloadTaskAdded(taskId) { refreshDlStatusBar() }
        function onDownloadTaskRemoved(taskId) { refreshDlStatusBar() }
        function onDownloadTaskProgressUpdated(taskId, progress, statusText, speed, downloaded, total) {
            var idx = _findDlStatusIndex(taskId)
            if (idx < 0) {
                refreshDlStatusBar()
                return
            }
            var cur = dlStatusModel.get(idx)
            dlStatusModel.set(idx, {
                task_id: cur.task_id,
                version: cur.version,
                status: cur.status === "paused" || cur.status === "queued" ? cur.status : "downloading",
                progress: downloadPage._progressPct(progress),
                status_text: statusText || "",
                speed: speed || ""
            })
        }
    }

    // ── 对话框（挂到 Overlay，避免随页面销毁/切页错位）──
    VersionNameDialog {
        id: versionDialog
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    SelectVersionDialog {
        id: selectVersionDialog
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    // ── 版本数据 ──
    property var vanillaVersions: []
    property var fabricVersions: []
    property var forgeVersions: []
    property var neoForgeVersions: []
    property var javaVersions: []
    property var bloretVersions: []
    property var minecraftVersionList: []
    property var fabricVersionList: []
    property var forgeVersionList: []
    property var neoForgeVersionList: []
    property var quiltVersionList: []
    property string currentSelectionTarget: ""
    property bool _ignoreIndexChange: false

    function updateBloretVersionLists() {
        if (!Backend) return
        bloretVersions = Backend.getVersionsByCategory("百络谷支持版本")
        if (bloretVersions.length === 0) return

        minecraftVersionList = bloretVersions.slice()
        minecraftVersionList.push(Backend.tr("其他版本..."))
        vanillaCombo.model = minecraftVersionList

        fabricVersionList = bloretVersions.slice()
        fabricVersionList.push(Backend.tr("其他版本..."))
        fabricCombo.model = fabricVersionList

        forgeVersionList = bloretVersions.slice()
        forgeVersionList.push(Backend.tr("其他版本..."))
        forgeCombo.model = forgeVersionList

        neoForgeVersionList = bloretVersions.slice()
        neoForgeVersionList.push(Backend.tr("其他版本..."))
        neoForgeCombo.model = neoForgeVersionList

        quiltVersionList = bloretVersions.slice()
        quiltVersionList.push(Backend.tr("其他版本..."))
        if (typeof quiltCombo !== "undefined" && quiltCombo)
            quiltCombo.model = quiltVersionList
    }

    Component.onCompleted: {
        if (Backend) {
            updateBloretVersionLists()
            javaVersions = Backend.getJavaDownloadVersions()

            versionDialog.confirmed.connect(function(name) {
                if (versionDialog.loaderType === "fabric") {
                    Backend.downloadFabric(fabricCombo.currentText, name)
                } else if (versionDialog.loaderType === "quilt") {
                    Backend.downloadQuilt(quiltCombo.currentText, name)
                } else if (versionDialog.loaderType === "forge") {
                    Backend.downloadForge(forgeCombo.currentText, name)
                } else if (versionDialog.loaderType === "neoforge") {
                    Backend.downloadNeoForge(neoForgeCombo.currentText, name)
                } else {
                    Backend.downloadVanilla(vanillaCombo.currentText, name)
                }
            })

            selectVersionDialog.versionSelected.connect(onVersionSelected)
        }
        refreshDlStatusBar()
    }

    function onVersionSelected(version) {
        _ignoreIndexChange = true
        if (currentSelectionTarget === "vanilla") {
            let index = minecraftVersionList.indexOf(version)
            if (index === -1) {
                minecraftVersionList.splice(minecraftVersionList.length - 1, 0, version)
                vanillaCombo.model = minecraftVersionList
            }
            vanillaCombo.currentIndex = minecraftVersionList.indexOf(version)
        } else if (currentSelectionTarget === "fabric") {
            let index = fabricVersionList.indexOf(version)
            if (index === -1) {
                fabricVersionList.splice(fabricVersionList.length - 1, 0, version)
                fabricCombo.model = fabricVersionList
            }
            fabricCombo.currentIndex = fabricVersionList.indexOf(version)
        } else if (currentSelectionTarget === "forge") {
            let index = forgeVersionList.indexOf(version)
            if (index === -1) {
                forgeVersionList.splice(forgeVersionList.length - 1, 0, version)
                forgeCombo.model = forgeVersionList
            }
            forgeCombo.currentIndex = forgeVersionList.indexOf(version)
        } else if (currentSelectionTarget === "neoforge") {
            let index = neoForgeVersionList.indexOf(version)
            if (index === -1) {
                neoForgeVersionList.splice(neoForgeVersionList.length - 1, 0, version)
                neoForgeCombo.model = neoForgeVersionList
            }
            neoForgeCombo.currentIndex = neoForgeVersionList.indexOf(version)
        } else if (currentSelectionTarget === "quilt") {
            let index = quiltVersionList.indexOf(version)
            if (index === -1) {
                quiltVersionList.splice(quiltVersionList.length - 1, 0, version)
                quiltCombo.model = quiltVersionList
            }
            quiltCombo.currentIndex = quiltVersionList.indexOf(version)
        }
        _ignoreIndexChange = false
    }

    // ── 分组标题统一样式 ──
    component SectionHeader: Label {
        font.weight: Font.DemiBold
        font.pixelSize: 13
        color: downloadPage._cTextSecondary
        Layout.fillWidth: true
        Layout.topMargin: 4
    }

    // ── 卡片壳统一样式 ──
    component DownloadCard: Frame {
        Layout.fillWidth: true
        padding: 16
        hoverable: false

        background: Rectangle {
            color: downloadPage._cCard
            radius: 8
            border.color: downloadPage._cCardBorder
            border.width: 1
        }
    }

    // ── 卡片内图标 ──
    component CardIcon: Image {
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        Layout.alignment: Qt.AlignVCenter
        sourceSize.width: 40
        sourceSize.height: 40
        fillMode: Image.PreserveAspectFit
        asynchronous: true
    }

    // ── 页面内容主体 ──
    content: ColumnLayout {
        spacing: 12

        // ── 当前下载（仅当有任务时显示）──
        // 注意：不要用 RinUI Frame(clip:true) + MouseArea(anchors.fill)
        // 否则 childrenRect 高度只算到标题行，进度内容被裁成一条细带。
        SectionHeader {
            text: (Backend ? Backend.tr("当前下载") : "当前下载")
            visible: _dlActive > 0 || dlStatusModel.count > 0
        }

        Rectangle {
            id: dlStatusCard
            visible: _dlActive > 0 || dlStatusModel.count > 0
            Layout.fillWidth: true
            // 高度完全由内容撑开，并设下限避免再塌成细条
            implicitHeight: statusContent.implicitHeight + 28
            Layout.preferredHeight: Math.max(88, statusContent.implicitHeight + 28)
            Layout.minimumHeight: 88
            radius: 8
            color: statusClickArea.containsMouse
                   ? Qt.rgba(downloadPage._cPrimary.r, downloadPage._cPrimary.g, downloadPage._cPrimary.b, 0.08)
                   : downloadPage._cCard
            border.color: statusClickArea.containsMouse
                          ? downloadPage._cPrimary
                          : downloadPage._cCardBorder
            border.width: 1
            clip: false

            Behavior on color { ColorAnimation { duration: 120 } }
            Behavior on border.color { ColorAnimation { duration: 120 } }

            MouseArea {
                id: statusClickArea
                anchors.fill: parent
                z: 10
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (Backend) Backend.openDownloadManager()
                }
            }

            ColumnLayout {
                id: statusContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 14
                spacing: 12

                // 标题行
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Rectangle {
                        Layout.preferredWidth: 4
                        Layout.preferredHeight: 22
                        radius: 2
                        color: downloadPage._cPrimary
                    }

                    Text {
                        text: (Backend ? Backend.tr("下载中") : "下载中")
                              + " (" + Math.max(_dlActive, dlStatusModel.count) + ")"
                        font.weight: Font.DemiBold
                        font.pixelSize: 13
                        color: downloadPage._cPrimary
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: Backend ? Backend.tr("查看详情") : "查看详情"
                        font.pixelSize: 12
                        color: downloadPage._cTextSecondary
                    }

                    Text {
                        text: "›"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        color: downloadPage._cPrimary
                        Layout.alignment: Qt.AlignVCenter
                    }
                }

                // 任务行：版本 + 进度 + 百分比 + 状态/速度
                Repeater {
                    model: dlStatusModel
                    delegate: ColumnLayout {
                        id: taskRow
                        Layout.fillWidth: true
                        spacing: 6

                        required property int index
                        required property string task_id
                        required property string version
                        required property string status
                        required property real progress
                        required property string status_text
                        required property string speed

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Text {
                                text: "Minecraft " + (taskRow.version || "")
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                color: downloadPage._cText
                                elide: Text.ElideRight
                                Layout.preferredWidth: 150
                                Layout.maximumWidth: 200
                            }

                            ProgressBar {
                                from: 0
                                to: 100
                                value: taskRow.progress
                                Layout.fillWidth: true
                                Layout.preferredHeight: 6
                                Layout.minimumWidth: 80
                                state: taskRow.status === "paused" ? 1 : 0
                                indeterminate: taskRow.status === "queued"
                                               || (taskRow.status === "downloading" && taskRow.progress <= 0)
                            }

                            Text {
                                text: taskRow.status === "paused"
                                      ? (Backend ? Backend.tr("已暂停") : "已暂停")
                                      : (Math.round(taskRow.progress) + "%")
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                color: taskRow.status === "paused"
                                       ? downloadPage._cCaution
                                       : downloadPage._cPrimary
                                Layout.preferredWidth: 52
                                horizontalAlignment: Text.AlignRight
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: taskRow.status_text && taskRow.status_text.length > 0
                                      ? taskRow.status_text
                                      : (taskRow.status === "paused"
                                         ? (Backend ? Backend.tr("已暂停") : "已暂停")
                                         : (Backend ? Backend.tr("正在准备下载…") : "正在准备下载…"))
                                font.pixelSize: 11
                                color: downloadPage._cTextSecondary
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                            }

                            Text {
                                text: taskRow.speed || ""
                                font.pixelSize: 11
                                color: downloadPage._cTextSecondary
                                visible: taskRow.speed && taskRow.speed.length > 0
                            }
                        }
                    }
                }

                // 模型暂时为空时的占位进度，避免再出现“只有标题的细条”
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    visible: dlStatusModel.count === 0 && _dlActive > 0

                    ProgressBar {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 6
                        indeterminate: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: Backend ? Backend.tr("正在同步下载进度…") : "正在同步下载进度…"
                        font.pixelSize: 11
                        color: downloadPage._cTextSecondary
                    }
                }

                Text {
                    visible: _dlActive > dlStatusModel.count && dlStatusModel.count > 0
                    text: Backend
                          ? Backend.tr("另有 %1 个任务…").arg(Math.max(0, _dlActive - dlStatusModel.count))
                          : ("另有 " + Math.max(0, _dlActive - dlStatusModel.count) + " 个任务…")
                    font.pixelSize: 11
                    color: downloadPage._cTextSecondary
                }
            }
        }

        // ── 分组1：游戏版本 ──
        SectionHeader {
            text: (Backend ? Backend.tr("游戏版本") : "游戏版本")
        }

        // Vanilla
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/Grass_Block.png")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("Minecraft 官方版本") : "Minecraft 官方版本")
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("下载并安装原生 Minecraft 核心") : "下载并安装原生 Minecraft 核心")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: vanillaCombo
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    onCurrentIndexChanged: {
                        if (_ignoreIndexChange) return
                        if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "vanilla"
                            selectVersionDialog.open()
                        }
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (!Backend) return
                        let ver = vanillaCombo.currentText
                        if (ver === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "vanilla"
                            selectVersionDialog.open()
                            return
                        }
                        versionDialog.version = ver
                        versionDialog.fabric = false
                        versionDialog.loaderType = "vanilla"
                        versionDialog.open()
                    }
                }
            }
        }

        // Fabric
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/fabric.png")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "Fabric Loader"
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 Fabric 加载器以使用 modern Mod") : "安装 Fabric 加载器以使用 modern Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: fabricCombo
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    onCurrentIndexChanged: {
                        if (_ignoreIndexChange) return
                        if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "fabric"
                            selectVersionDialog.open()
                        }
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (!Backend) return
                        let ver = fabricCombo.currentText
                        if (ver === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "fabric"
                            selectVersionDialog.open()
                            return
                        }
                        versionDialog.version = ver
                        versionDialog.fabric = true
                        versionDialog.loaderType = "fabric"
                        versionDialog.open()
                    }
                }
            }
        }

        // Quilt
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/fabric.png")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "Quilt Loader"
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 Quilt 加载器（Fabric 兼容生态）") : "安装 Quilt 加载器（Fabric 兼容生态）")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: quiltCombo
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    onCurrentIndexChanged: {
                        if (_ignoreIndexChange) return
                        if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "quilt"
                            selectVersionDialog.open()
                        }
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (!Backend) return
                        let ver = quiltCombo.currentText
                        if (ver === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "quilt"
                            selectVersionDialog.open()
                            return
                        }
                        versionDialog.version = ver
                        versionDialog.fabric = false
                        versionDialog.loaderType = "quilt"
                        versionDialog.open()
                    }
                }
            }
        }

        // Forge
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "Forge Loader"
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 Forge 加载器以使用 Forge Mod") : "安装 Forge 加载器以使用 Forge Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: forgeCombo
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    onCurrentIndexChanged: {
                        if (_ignoreIndexChange) return
                        if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "forge"
                            selectVersionDialog.open()
                        }
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (!Backend) return
                        let ver = forgeCombo.currentText
                        if (ver === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "forge"
                            selectVersionDialog.open()
                            return
                        }
                        versionDialog.version = ver
                        versionDialog.fabric = false
                        versionDialog.loaderType = "forge"
                        versionDialog.open()
                    }
                }
            }
        }

        // NeoForge
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "NeoForge Loader"
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 NeoForge 加载器以使用 NeoForge Mod") : "安装 NeoForge 加载器以使用 NeoForge Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: neoForgeCombo
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    onCurrentIndexChanged: {
                        if (_ignoreIndexChange) return
                        if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "neoforge"
                            selectVersionDialog.open()
                        }
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (!Backend) return
                        let ver = neoForgeCombo.currentText
                        if (ver === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                            currentSelectionTarget = "neoforge"
                            selectVersionDialog.open()
                            return
                        }
                        versionDialog.version = ver
                        versionDialog.fabric = false
                        versionDialog.loaderType = "neoforge"
                        versionDialog.open()
                    }
                }
            }
        }

        // ── 分组2：运行环境 ──
        SectionHeader {
            text: (Backend ? Backend.tr("运行环境") : "运行环境")
        }

        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/java.png")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            font.weight: Font.DemiBold
                            text: (Backend ? Backend.tr("Java 运行时环境") : "Java 运行时环境")
                            color: downloadPage._cText
                            elide: Text.ElideRight
                        }

                        Badge {
                            text: Qt.platform.os === "windows" ? "Windows √" : "Only For Windows ×"
                            colorType: Qt.platform.os === "windows" ? "Success" : "Error"
                        }
                    }

                    Label {
                        text: (Backend ? Backend.tr("运行 Minecraft 所需的 Java 环境") : "运行 Minecraft 所需的 Java 环境")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                ComboBox {
                    id: javaVersionCombo
                    model: javaVersions
                    Layout.preferredWidth: 160
                    Layout.minimumWidth: 120
                    enabled: Qt.platform.os === "windows"
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    enabled: Qt.platform.os === "windows"
                    onClicked: {
                        if (Backend) Backend.downloadJava(javaVersionCombo.currentText)
                    }
                }
            }
        }

        // ── 分组3：导入 / 自定义 ──
        SectionHeader {
            text: (Backend ? Backend.tr("导入 / 自定义") : "导入 / 自定义")
        }

        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    source: Qt.resolvedUrl("../../icon/exeapps.png")
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("外部程序/整合包") : "外部程序/整合包")
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("添加您的自定义启动项或整合包文件") : "添加您的自定义启动项或整合包文件")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("添加自定义项目") : "添加自定义项目")
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (Backend) Backend.addCustomApp()
                    }
                }
            }
        }

        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                CardIcon {
                    id: modrinthIcon
                    source: Qt.resolvedUrl("../../icon/modrinth.png")
                    cache: false
                    onStatusChanged: {
                        if (status === Image.Error)
                            console.log("[Download] Modrinth icon failed to load:", source)
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("Modrinth 整合包") : "Modrinth 整合包")
                        color: downloadPage._cText
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: (Backend ? Backend.tr("导入 .mrpack 格式的 Modrinth 整合包") : "导入 .mrpack 格式的 Modrinth 整合包")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                    }
                }

                Button {
                    text: (Backend ? Backend.tr("导入整合包") : "导入整合包")
                    highlighted: true
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: {
                        if (Backend) Backend.importMrpack()
                    }
                }
            }
        }

        DownloadCard {
            ColumnLayout {
                width: parent.width
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    CardIcon {
                        source: Qt.resolvedUrl("../../icon/exeapps.png")
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            font.weight: Font.DemiBold
                            text: (Backend ? Backend.tr("从 Prism / MultiMC 导入") : "从 Prism / MultiMC 导入")
                            color: downloadPage._cText
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        Label {
                            text: (Backend ? Backend.tr("选择启动器根目录或 instances 目录，导入 mods/config/saves") : "选择启动器根目录或 instances 目录，导入 mods/config/saves")
                            color: downloadPage._cTextSecondary
                            font.pixelSize: 12
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    TextField {
                        id: importPathField
                        Layout.fillWidth: true
                        text: importBasePath
                        placeholderText: (Backend ? Backend.tr("PrismLauncher / MultiMC 路径") : "PrismLauncher / MultiMC 路径")
                        onTextChanged: importBasePath = text
                    }
                    Button {
                        text: (Backend ? Backend.tr("浏览") : "浏览")
                        onClicked: {
                            if (!Backend) return
                            var p = Backend.selectImportLauncherFolder()
                            if (p) {
                                importBasePath = p
                                importPathField.text = p
                            }
                        }
                    }
                    Button {
                        text: (Backend ? Backend.tr("自动检测") : "自动检测")
                        onClicked: {
                            if (!Backend) return
                            var paths = Backend.getDefaultImportPaths() || {}
                            var p = paths.prism || paths.multimc || ""
                            if (p) {
                                importBasePath = p
                                importPathField.text = p
                                importStatusText = (Backend.tr("已定位") + ": " + p)
                            } else {
                                importStatusText = Backend.tr("未找到默认路径，请手动浏览")
                            }
                        }
                    }
                    Button {
                        text: (Backend ? Backend.tr("扫描") : "扫描")
                        highlighted: true
                        onClicked: {
                            if (!Backend || !importBasePath) return
                            importStatusText = Backend.tr("扫描中...")
                            Backend.requestImportableInstances(importBasePath)
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: importStatusText
                    color: downloadPage._cTextSecondary
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    model: importableInstances
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 52
                        radius: 8
                        color: downloadPage._cCard
                        border.color: downloadPage._cCardBorder
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: modelData.name || modelData.folder || ""
                                    font.weight: Font.DemiBold
                                    color: downloadPage._cText
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: (modelData.minecraft_version || "") + (modelData.path ? (" · " + modelData.path) : "")
                                    color: downloadPage._cTextSecondary
                                    font.pixelSize: 11
                                    elide: Text.ElideMiddle
                                    Layout.fillWidth: true
                                }
                            }
                            Button {
                                text: (Backend ? Backend.tr("导入") : "导入")
                                onClicked: {
                                    if (!Backend) return
                                    importStatusText = (Backend.tr("正在导入") + ": " + (modelData.name || modelData.folder))
                                    Backend.importExternalInstance(modelData.path, "")
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── 插件扩展面板 ──
        SectionHeader {
            text: (Backend ? Backend.tr("插件扩展") : "插件扩展")
            visible: pluginPanelHost.pluginPanels && pluginPanelHost.pluginPanels.length > 0
        }

        PluginPanelHost {
            id: pluginPanelHost
            area: "download"
            Layout.fillWidth: true
        }
    }
}
