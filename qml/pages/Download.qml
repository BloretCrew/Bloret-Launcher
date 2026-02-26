import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: downloadPage
    title: qsTr("下载")

    property var vanillaVersions: []
    property var fabricVersions: []
    property var javaVersions: []

    Component.onCompleted: {
        vanillaVersions = Backend.getVanillaVersions()
        fabricVersions = Backend.getFabricVersions()
        javaVersions = Backend.getJavaDownloadVersions()
    }

    // --- Vanilla Minecraft Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
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
                }
                Label {
                    text: qsTr("下载并安装原生 Minecraft 核心")
                    color: "#7f7f7f"
                }
            }

            ComboBox {
                id: vanillaCombo
                model: vanillaVersions
                Layout.preferredWidth: 150
            }

            Button {
                text: qsTr("下载并安装")
                highlighted: true
                onClicked: {
                    Backend.downloadVanilla(vanillaCombo.currentText)
                }
            }
        }
    }

    // --- Fabric Loader Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
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
                }
                Label {
                    text: qsTr("安装 Fabric 加载器以使用现代 Mod")
                    color: "#7f7f7f"
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
                    Backend.downloadFabric(fabricCombo.currentText)
                }
            }
        }
    }

    // --- Java Tool Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
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
                }
                Label {
                    text: qsTr("运行 Minecraft 所需的 Java 环境")
                    color: "#7f7f7f"
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
                    Backend.downloadJava(javaVersionCombo.currentText)
                }
            }
        }
    }

    // --- Customize Apps Card ---
    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
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
                }
                Label {
                    text: qsTr("添加您的自定义启动项或整合包文件")
                    color: "#7f7f7f"
                }
            }

            Button {
                text: qsTr("添加自定义项目")
                onClicked: Backend.addCustomApp()
            }
        }
    }
}
