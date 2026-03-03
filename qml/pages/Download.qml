import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: downloadPage
    title: qsTr("下载")

    VersionNameDialog { id: versionDialog }
    SelectVersionDialog { id: selectVersionDialog }

    property var vanillaVersions: []
    property var fabricVersions: []
    property var javaVersions: []
    property var bloretVersions: []
    property var minecraftVersionList: []
    property bool isSettingIndex: false  // 防止在代码中设置 index 时打开对话框

    Component.onCompleted: {
        if (Backend) {
            bloretVersions = Backend.getVersionsByCategory("百络谷支持版本")
            
            // 合并版本列表：百络谷版本 + "其他版本..."
            minecraftVersionList = bloretVersions.slice()  // 复制数组
            minecraftVersionList.push(qsTr("其他版本..."))
            vanillaCombo.model = minecraftVersionList
            
            fabricVersions = Backend.getFabricVersions()
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
        // 将选中的版本添加到列表中（如果不存在）
        let index = minecraftVersionList.indexOf(version)
        if (index === -1) {
            // 移除"其他版本..."并重新添加版本
            minecraftVersionList.pop()
            minecraftVersionList.push(version)
            minecraftVersionList.push(qsTr("其他版本..."))
            vanillaCombo.model = minecraftVersionList
        }
        // 使用标志位防止打开对话框
        isSettingIndex = true
        vanillaCombo.currentIndex = minecraftVersionList.indexOf(version)
        isSettingIndex = false
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
                    // 只在用户手动选择时打开对话框，不在代码设置 index 时打开
                    if (isSettingIndex) return
                    
                    let currentText = vanillaCombo.currentText
                    if (currentText === qsTr("其他版本...")) {
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
                model: fabricVersions
                Layout.preferredWidth: 150
            }

            Button {
                text: qsTr("下载并安装")
                highlighted: true
                onClicked: {
                    if (!Backend) return
                    let ver = fabricCombo.currentText
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
