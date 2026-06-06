import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: downloadPage
    title: (Backend ? Backend.tr("下载") : "下载")

    Badge {
        text: "bangbang93/BMCLAPI"
        colorType: "Success"
    }

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

    property var vanillaVersions: []
    property var fabricVersions: []
    property var forgeVersions: []
    property var neoForgeVersions: []
    property var javaVersions: []
    property var bloretVersions: []
    property var minecraftVersionList: []
    property var fabricVersionList: [] // 新增：Fabric 版本列表
    property var forgeVersionList: []
    property var neoForgeVersionList: []
    property string currentSelectionTarget: "" // 新增：记录当前选择的是原版还是Fabric
    property bool _ignoreIndexChange: false // 防止 onCurrentIndexChanged 循环触发

    function updateBloretVersionLists() {
        if (!Backend) return
        bloretVersions = Backend.getVersionsByCategory("百络谷支持版本")
        if (bloretVersions.length === 0) return

        // 初始化原版列表：百络谷版本 + "其他版本..."
        minecraftVersionList = bloretVersions.slice()
        minecraftVersionList.push(Backend.tr("其他版本..."))
        vanillaCombo.model = minecraftVersionList

        // 初始化加载器列表：使用相同的百络谷版本作为推荐 + "其他版本..."
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
        if (Backend) {
            updateBloretVersionLists()
            
            javaVersions = Backend.getJavaDownloadVersions()
            
            versionDialog.confirmed.connect(function(name){
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
        console.log("[Download] onVersionSelected:", version, "target:", currentSelectionTarget)
        _ignoreIndexChange = true
        if (currentSelectionTarget === "vanilla") {
            let index = minecraftVersionList.indexOf(version)
            if (index === -1) {
                // 插入到倒数第二个位置（"其他版本..."之前）
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

    // --- Vanilla Minecraft Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/Grass_Block.png")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("Minecraft 官方版本") : "Minecraft 官方版本")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("下载并安装原生 Minecraft 核心") : "下载并安装原生 Minecraft 核心")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: vanillaCombo
                Layout.preferredWidth: 150
                onCurrentIndexChanged: {
                    if (_ignoreIndexChange) return
                    console.log("[Download] vanillaCombo index changed:", currentIndex, "text:", model[currentIndex])
                    if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                        currentSelectionTarget = "vanilla"
                        console.log("[Download] Opening SelectVersionDialog for vanilla")
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

    // --- Fabric Loader Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/fabric.png")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("Fabric Loader") : "Fabric Loader")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("安装 Fabric 加载器以使用 modern Mod") : "安装 Fabric 加载器以使用 modern Mod")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: fabricCombo
                Layout.preferredWidth: 150
                // model 已经在 Component.onCompleted 中设置
                onCurrentIndexChanged: {
                    if (_ignoreIndexChange) return
                    console.log("[Download] fabricCombo index changed:", currentIndex, "text:", model[currentIndex])
                    if (model[currentIndex] === (Backend ? Backend.tr("其他版本...") : "其他版本...")) {
                        currentSelectionTarget = "fabric"
                        console.log("[Download] Opening SelectVersionDialog for fabric")
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
                    // 如果当前选中的是“其他版本...”，则打开选择框
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

    // --- Forge Loader Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("Forge Loader") : "Forge Loader")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("安装 Forge 加载器以使用 Forge Mod") : "安装 Forge 加载器以使用 Forge Mod")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: forgeCombo
                Layout.preferredWidth: 150
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

    // --- NeoForge Loader Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/Command_Block.gif")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("NeoForge Loader") : "NeoForge Loader")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("安装 NeoForge 加载器以使用 NeoForge Mod") : "安装 NeoForge 加载器以使用 NeoForge Mod")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: neoForgeCombo
                Layout.preferredWidth: 150
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

    // --- Java Tool Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/java.png")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                    Badge {
                        text: Qt.platform.os === "windows" ? "Windows √" : "Only For Windows ×"
                        colorType: Qt.platform.os === "windows" ? "Success" : "Error"
                    }
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("Java 运行时环境") : "Java 运行时环境")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("运行 Minecraft 所需的 Java 环境") : "运行 Minecraft 所需的 Java 环境")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: javaVersionCombo
                model: javaVersions
                Layout.preferredWidth: 150
            }

            Button {
                text: (Backend ? Backend.tr("下载并安装") : "下载并安装")
                onClicked: {
                    if (Backend) Backend.downloadJava(javaVersionCombo.currentText)
                }
            }
        }
    }

    // --- Customize Apps Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                source: Qt.resolvedUrl("../../icon/exeapps.png")
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("外部程序/整合包") : "外部程序/整合包")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("添加您的自定义启动项或整合包文件") : "添加您的自定义启动项或整合包文件")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Button {
                text: (Backend ? Backend.tr("添加自定义项目") : "添加自定义项目")
                onClicked: {
                    if (Backend) Backend.addCustomApp()
                }
            }
        }
    }

    // --- Modrinth Modpack Import Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        RowLayout {
            width: parent.width
            spacing: 15

            Image {
                id: modrinthIcon
                source: Qt.resolvedUrl("../../icon/modrinth.png")
                sourceSize { width: 40; height: 40 }
                cache: false
                fillMode: Image.PreserveAspectFit
                Component.onCompleted: {
                    console.log("[ModrinthIcon] source:", modrinthIcon.source)
                    console.log("[ModrinthIcon] status:", modrinthIcon.status)
                }
                onStatusChanged: {
                    console.log("[ModrinthIcon] status ->", modrinthIcon.status, "source:", modrinthIcon.source)
                    if (modrinthIcon.status === Image.Error) console.log("[ModrinthIcon] ERROR loading image")
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: (Backend ? Backend.tr("Modrinth 整合包") : "Modrinth 整合包")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("导入 .mrpack 格式的 Modrinth 整合包") : "导入 .mrpack 格式的 Modrinth 整合包")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Button {
                text: (Backend ? Backend.tr("导入整合包") : "导入整合包")
                highlighted: true
                onClicked: {
                    if (Backend) Backend.importMrpack()
                }
            }
        }
    }
}
