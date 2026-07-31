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
    }

    // ── 下载任务状态 ──
    property var _dlTasks: []
    property int _dlActive: 0

    Timer {
        id: dlBarTimer
        interval: 1000
        repeat: true
        running: visible
        onTriggered: {
            if (!Backend || !Backend.getDownloadTasks) return
            _dlTasks = Backend.getDownloadTasks()
            _dlActive = Backend.getActiveDownloadCount()
        }
    }

    // ── 对话框（非布局项，平铺在外层）──
    VersionNameDialog {
        id: versionDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
    }

    SelectVersionDialog {
        id: selectVersionDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
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
    }

    Component.onCompleted: {
        dlBarTimer.start()
        if (Backend) {
            updateBloretVersionLists()
            javaVersions = Backend.getJavaDownloadVersions()

            versionDialog.confirmed.connect(function(name) {
                if (versionDialog.loaderType === "fabric") {
                    Backend.downloadFabric(fabricCombo.currentText, name)
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

        background: Rectangle {
            color: downloadPage._cCard
            radius: 8
            border.color: downloadPage._cCardBorder
            border.width: 1
        }
    }

    // ── 页面内容主体 ──
    content: ColumnLayout {
        spacing: 12

        // ── 当前下载（仅当有任务时显示）──
        SectionHeader {
            text: (Backend ? Backend.tr("当前下载") : "当前下载")
            visible: _dlActive > 0
        }

        Frame {
            visible: _dlActive > 0
            Layout.fillWidth: true
            padding: 12
            background: Rectangle {
                color: downloadPage._cCard
                radius: 8
                border.color: downloadPage._cCardBorder
                border.width: 1
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (Backend) Backend.openDownloadManager()
                }
            }

            RowLayout {
                width: parent.width
                spacing: 12

                // 强调竖条
                Rectangle {
                    width: 4
                    height: 44
                    radius: 2
                    color: downloadPage._cPrimary
                }

                Text {
                    text: "⬇ " + (Backend ? Backend.tr("下载中") : "下载中") + " (" + _dlActive + ")"
                    font.weight: Font.DemiBold
                    font.pixelSize: 13
                    color: downloadPage._cPrimary
                }

                Repeater {
                    model: {
                        var active = []
                        for (var i = 0; i < _dlTasks.length; i++) {
                            if (_dlTasks[i].status === "downloading")
                                active.push(_dlTasks[i])
                        }
                        return active.slice(0, 3)
                    }
                    delegate: RowLayout {
                        spacing: 6
                        required property var modelData

                        Text {
                            text: "Minecraft " + modelData.version
                            font.pixelSize: 11
                            color: downloadPage._cPrimary
                            elide: Text.ElideRight
                            Layout.maximumWidth: 120
                        }

                        ProgressBar {
                            from: 0
                            to: 100
                            value: modelData.progress
                            width: 80
                            implicitHeight: 4
                        }

                        Text {
                            text: Math.round(modelData.progress) + "%"
                            font.pixelSize: 10
                            color: downloadPage._cTextSecondary
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "▶"
                    font.pixelSize: 14
                    color: downloadPage._cPrimary
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

                Image {
                    source: Qt.resolvedUrl("../../icon/Grass_Block.png")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("Minecraft 官方版本") : "Minecraft 官方版本")
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("下载并安装原生 Minecraft 核心") : "下载并安装原生 Minecraft 核心")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: vanillaCombo
                    Layout.preferredWidth: 180
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

                Image {
                    source: Qt.resolvedUrl("../../icon/fabric.png")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "Fabric Loader"
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 Fabric 加载器以使用 modern Mod") : "安装 Fabric 加载器以使用 modern Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: fabricCombo
                    Layout.preferredWidth: 180
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

        // Forge
        DownloadCard {
            RowLayout {
                width: parent.width
                spacing: 16

                Image {
                    source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "Forge Loader"
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 Forge 加载器以使用 Forge Mod") : "安装 Forge 加载器以使用 Forge Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: forgeCombo
                    Layout.preferredWidth: 180
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

                Image {
                    source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: "NeoForge Loader"
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("安装 NeoForge 加载器以使用 NeoForge Mod") : "安装 NeoForge 加载器以使用 NeoForge Mod")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: neoForgeCombo
                    Layout.preferredWidth: 180
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

                Image {
                    source: Qt.resolvedUrl("../../icon/java.png")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    RowLayout {
                        spacing: 8

                        Label {
                            font.weight: Font.DemiBold
                            text: (Backend ? Backend.tr("Java 运行时环境") : "Java 运行时环境")
                            color: downloadPage._cText
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
                    }
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: javaVersionCombo
                    model: javaVersions
                    Layout.preferredWidth: 180
                }

                Button {
                    text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                    highlighted: true
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

                Image {
                    source: Qt.resolvedUrl("../../icon/exeapps.png")
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("外部程序/整合包") : "外部程序/整合包")
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("添加您的自定义启动项或整合包文件") : "添加您的自定义启动项或整合包文件")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: (Backend ? Backend.tr("添加自定义项目") : "添加自定义项目")
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

                Image {
                    id: modrinthIcon
                    source: Qt.resolvedUrl("../../icon/modrinth.png")
                    sourceSize { width: 40; height: 40 }
                    cache: false
                    fillMode: Image.PreserveAspectFit
                    onStatusChanged: {
                        if (status === Image.Error)
                            console.log("[Download] Modrinth icon failed to load:", source)
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        font.weight: Font.DemiBold
                        text: (Backend ? Backend.tr("Modrinth 整合包") : "Modrinth 整合包")
                        color: downloadPage._cText
                    }

                    Label {
                        text: (Backend ? Backend.tr("导入 .mrpack 格式的 Modrinth 整合包") : "导入 .mrpack 格式的 Modrinth 整合包")
                        color: downloadPage._cTextSecondary
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: (Backend ? Backend.tr("导入整合包") : "导入整合包")
                    highlighted: true
                    onClicked: {
                        if (Backend) Backend.importMrpack()
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
