import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: settingsPage
    title: qsTr("设置")

    property string currentMcDir: ""
    property var javaPaths: []
    property string currentJavaPath: ""
    property string themeMode: ""

    Component.onCompleted: {
        refreshData()
    }

    function refreshData() {
        currentMcDir = Backend.getMinecraftDir()
        javaPaths = Backend.getSystemJavas()
        currentJavaPath = Backend.getCurrentJavaPath()
        themeMode = Backend.getThemeMode()
        
        // Ensure "Auto" is in the list
        if (javaPaths.indexOf("Auto") === -1) {
            javaPaths.unshift("Auto")
        }
        
        javaCombo.currentIndex = javaPaths.indexOf(currentJavaPath)
        if (javaCombo.currentIndex === -1) {
            javaPaths.push(currentJavaPath)
            javaCombo.currentIndex = javaPaths.length - 1
        }

        themeCombo.currentIndex = ["Auto", "Light", "Dark"].indexOf(themeMode)
    }

    // --- Version Card ---
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
            Label {
                font.weight: Font.DemiBold
                font.pixelSize: 16
                text: qsTr("当前版本")
                Layout.fillWidth: true
            }
            Label {
                text: Backend.getBloretVersion()
                font.weight: Font.DemiBold
            }
        }
    }

    // --- Minecraft & Java Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("Minecraft 与 Java")
        Layout.topMargin: 10
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            // Java Selection
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Java") }
                    Label { text: qsTr("选择用于启动 Minecraft 的 Java"); color: "#7f7f7f" }
                }
                ComboBox {
                    id: javaCombo
                    model: javaPaths
                    Layout.minimumWidth: 250
                    onActivated: {
                        Backend.setCurrentJavaPath(currentText)
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            // Minecraft Dir
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 文件夹位置") }
                    Label { text: currentMcDir; color: "#7f7f7f"; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
                RowLayout {
                    Button {
                        text: qsTr("浏览...")
                        onClicked: {
                            var path = Backend.browseMinecraftDir()
                            if (path !== "") {
                                currentMcDir = path
                            }
                        }
                    }
                    Button {
                        flat: true
                        text: qsTr("打开")
                        onClicked: Backend.openMinecraftDir()
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            // Mini Toolbar
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 小工具栏") }
                    Label { text: qsTr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"); color: "#7f7f7f"; wrapMode: Text.Wrap }
                }
                Switch {
                    checked: true
                }
            }
        }
    }

    // --- Appearance Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("外观")
        Layout.topMargin: 10
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("语言 / language") }
                    Label { text: qsTr("调整语言设置"); color: "#7f7f7f" }
                }
                ComboBox {
                    model: ["简体中文", "English"]
                    Layout.minimumWidth: 150
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("主题") }
                    Label { text: qsTr("眼睛舒服了"); color: "#7f7f7f" }
                }
                ComboBox {
                    id: themeCombo
                    model: ["Auto", "Light", "Dark"]
                    Layout.minimumWidth: 150
                    onActivated: {
                        Backend.setThemeMode(currentText)
                    }
                }
            }
        }
    }

    // --- Log Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("日志")
        Layout.topMargin: 10
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.controlColorDefault
            radius: 8
            border.color: Theme.currentTheme.colors.surfaceStrokeColorDefault
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("日志文件夹位置") }
                    Label { text: qsTr("存储所有 Bloret Launcher 日志的文件夹位置"); color: "#7f7f7f" }
                }
                Button {
                    flat: true
                    text: "log"
                    onClicked: Backend.openLogDir()
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("清空日志") }
                    Label { text: qsTr("清空 log 文件夹"); color: "#7f7f7f" }
                }
                Button {
                    text: qsTr("清空日志")
                    onClicked: Backend.clearLogs()
                }
            }
        }
    }

    Label {
        text: qsTr("设置界面大部分内容需要重启程序后生效。")
        color: "#7f7f7f"
        Layout.topMargin: 10
    }
}
