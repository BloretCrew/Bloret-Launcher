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
        if (Backend) {
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
    }

    // --- Version Card ---
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
            Label {
                font.weight: Font.DemiBold
                font.pixelSize: 16
                text: qsTr("当前版本")
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }
            Label {
                text: Backend ? Backend.getBloretVersion() : "2.0.0-Beta"
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.primaryColor
            }
        }
    }

    // --- Minecraft & Java Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("Minecraft 与 Java")
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            // Java Selection
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Java"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("选择用于启动 Minecraft 的 Java"); color: Theme.currentTheme.colors.textSecondaryColor }
                }
                ComboBox {
                    id: javaCombo
                    model: javaPaths
                    Layout.minimumWidth: 250
                    onActivated: {
                        if (Backend) Backend.setCurrentJavaPath(currentText)
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

            // Minecraft Dir
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 文件夹位置"); color: Theme.currentTheme.colors.textColor }
                    Label { text: currentMcDir; color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
                RowLayout {
                    Button {
                        text: qsTr("浏览...")
                        onClicked: {
                            if (Backend) {
                                var path = Backend.browseMinecraftDir()
                                if (path !== "") {
                                    currentMcDir = path
                                }
                            }
                        }
                    }
                    Button {
                        flat: true
                        text: qsTr("打开")
                        onClicked: { if (Backend) Backend.openMinecraftDir() }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

            // Mini Toolbar
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 小工具栏"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"); color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap }
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
        color: Theme.currentTheme.colors.textColor
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("语言 / language"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("调整语言设置"); color: Theme.currentTheme.colors.textSecondaryColor }
                }
                ComboBox {
                    model: ["简体中文", "English"]
                    Layout.minimumWidth: 150
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("主题"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("眼睛舒服了"); color: Theme.currentTheme.colors.textSecondaryColor }
                }
                ComboBox {
                    id: themeCombo
                    model: ["Auto", "Light", "Dark"]
                    Layout.minimumWidth: 150
                    onActivated: {
                        if (Backend) Backend.setThemeMode(currentText)
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
        color: Theme.currentTheme.colors.textColor
    }

    Frame {
        Layout.fillWidth: true
        padding: 15
        background: Rectangle {
            color: Theme.currentTheme.colors.cardColor
            radius: 8
            border.color: Theme.currentTheme.colors.controlBorderColor
        }

        ColumnLayout {
            width: parent.width
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("日志文件夹位置"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("存储所有 Bloret Launcher 日志的文件夹位置"); color: Theme.currentTheme.colors.textSecondaryColor }
                }
                Button {
                    flat: true
                    text: "log"
                    onClicked: { if (Backend) Backend.openLogDir() }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("清空日志"); color: Theme.currentTheme.colors.textColor }
                    Label { text: qsTr("清空 log 文件夹"); color: Theme.currentTheme.colors.textSecondaryColor }
                }
                Button {
                    text: qsTr("清空日志")
                    onClicked: { if (Backend) Backend.clearLogs() }
                }
            }
        }
    }

    Label {
        text: qsTr("设置界面大部分内容需要重启程序后生效。")
        color: Theme.currentTheme.colors.textTertialyColor
        Layout.topMargin: 10
    }
}
