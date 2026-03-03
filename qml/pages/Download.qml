import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: downloadPage
    title: qsTr("下载")

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
    property var javaVersions: []
    property var bloretVersions: []
    property var minecraftVersionList: []
    property var fabricVersionList: [] // 新增：Fabric 版本列表
    property string currentSelectionTarget: "" // 新增：记录当前选择的是原版还是Fabric
    property bool _ignoreIndexChange: false // 防止 onCurrentIndexChanged 循环触发

    Component.onCompleted: {
        if (Backend) {
            bloretVersions = Backend.getVersionsByCategory("百络谷支持版本")
            
            // 初始化原版列表：百络谷版本 + "其他版本..."
            minecraftVersionList = bloretVersions.slice()
            minecraftVersionList.push(qsTr("其他版本..."))
            vanillaCombo.model = minecraftVersionList
            
            // 初始化 Fabric 列表：使用相同的百络谷版本作为推荐 + "其他版本..."
            // Fabric 支持几乎所有版本，所以逻辑和原版下载类似，让用户从"其他版本"里选
            fabricVersionList = bloretVersions.slice()
            fabricVersionList.push(qsTr("其他版本..."))
            fabricCombo.model = fabricVersionList
            
            javaVersions = Backend.getJavaDownloadVersions()
            
            versionDialog.confirmed.connect(function(name){
                if (versionDialog.fabric) {
                    Backend.downloadFabric(fabricCombo.currentText, name)
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
                source: "../../icon/Grass_Block.png"
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("Minecraft 官方版本")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: qsTr("下载并安装原生 Minecraft 核心")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: vanillaCombo
                Layout.preferredWidth: 150
                onCurrentIndexChanged: {
                    if (_ignoreIndexChange) return
                    console.log("[Download] vanillaCombo index changed:", currentIndex, "text:", model[currentIndex])
                    if (model[currentIndex] === qsTr("其他版本...")) {
                        currentSelectionTarget = "vanilla"
                        console.log("[Download] Opening SelectVersionDialog for vanilla")
                        selectVersionDialog.open()
                    }
                }
            }

            Button {
                text: qsTr("下载并安装")
                highlighted: true
                onClicked: {
                    if (!Backend) return
                    let ver = vanillaCombo.currentText
                    if (ver === qsTr("其他版本...")) {
                        currentSelectionTarget = "vanilla"
                        selectVersionDialog.open()
                        return
                    }
                    versionDialog.version = ver
                    versionDialog.fabric = false
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
                source: "../../icon/fabric.png"
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("Fabric Loader")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: qsTr("安装 Fabric 加载器以使用 modern Mod")
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
                    if (model[currentIndex] === qsTr("其他版本...")) {
                        currentSelectionTarget = "fabric"
                        console.log("[Download] Opening SelectVersionDialog for fabric")
                        selectVersionDialog.open()
                    }
                }
            }

            Button {
                text: qsTr("下载并安装")
                highlighted: true
                onClicked: {
                    if (!Backend) return
                    let ver = fabricCombo.currentText
                    // 如果当前选中的是“其他版本...”，则打开选择框
                    if (ver === qsTr("其他版本...")) {
                        currentSelectionTarget = "fabric"
                        selectVersionDialog.open()
                        return
                    }
                    versionDialog.version = ver
                    versionDialog.fabric = true
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
                source: "../../icon/java.png"
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("Java 运行时环境")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: qsTr("运行 Minecraft 所需的 Java 环境")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            ComboBox {
                id: javaVersionCombo
                model: javaVersions
                Layout.preferredWidth: 150
            }

            Button {
                text: qsTr("下载并安装")
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
                source: "../../icon/exeapps.png"
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    font.weight: Font.DemiBold
                    text: qsTr("外部程序/整合包")
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: qsTr("添加您的自定义启动项或整合包文件")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Button {
                text: qsTr("添加自定义项目")
                onClicked: {
                    if (Backend) Backend.addCustomApp()
                }
            }
        }
    }
}
