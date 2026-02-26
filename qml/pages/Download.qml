import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: downloadPage
    title: qsTr("下载")

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
                    font.pixelSize: 16
                    text: qsTr("原版 Minecraft")
                }
                Label {
                    text: qsTr("一键下载安装原版 Minecraft")
                    color: "#7f7f7f"
                }
            }

            ComboBox {
                id: vanillaVersionCombo
                model: Backend.getVanillaVersions()
                Layout.minimumWidth: 150
            }

            Button {
                text: qsTr("下载并安装")
                onClicked: {
                    Backend.downloadVanilla(vanillaVersionCombo.currentText)
                }
            }
        }
    }

    // --- Fabric Minecraft Card ---
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
                    font.pixelSize: 16
                    text: qsTr("Minecraft + Fabric")
                }
                Label {
                    text: qsTr("可以添加 Mod 的 Minecraft 版本")
                    color: "#7f7f7f"
                }
            }

            ComboBox {
                id: fabricVersionCombo
                model: Backend.getFabricVersions()
                Layout.minimumWidth: 150
            }

            Button {
                text: qsTr("下载并安装")
                onClicked: {
                    Backend.downloadFabric(fabricVersionCombo.currentText)
                }
            }
        }
    }

    // --- Java Card ---
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
                    font.pixelSize: 16
                    text: qsTr("Java")
                }
                Label {
                    text: qsTr("一键下载安装 Java")
                    color: "#7f7f7f"
                }
            }

            Label {
                text: qsTr("Java")
                font.weight: Font.DemiBold
            }

            ComboBox {
                id: javaVersionCombo
                model: ["8", "17", "21"]
                Layout.minimumWidth: 100
            }

            Label {
                text: qsTr("Windows x64")
                font.weight: Font.DemiBold
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
                    font.pixelSize: 16
                    text: qsTr("自定义程序")
                }
                Label {
                    text: qsTr("添加自定义启动项")
                    color: "#7f7f7f"
                }
            }

            Button {
                text: qsTr("添加")
                onClicked: {
                    Backend.addCustomApp()
                }
            }
        }
    }
}
