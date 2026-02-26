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
    SettingCard {
        Layout.fillWidth: true
        title: qsTr("当前版本")
        description: qsTr("Bloret Launcher v2")
        icon.name: "ic_fluent_info_20_regular"
        Label {
            text: Backend ? Backend.getBloretVersion() : "2.0.0-Beta"
            font.weight: Font.DemiBold
            color: Theme.accentColor
            Layout.alignment: Qt.AlignVCenter
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

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("Java")
            description: qsTr("选择用于启动 Minecraft 的 Java")
            icon.name: "ic_fluent_code_20_regular"
            ComboBox {
                id: javaCombo
                model: javaPaths
                Layout.preferredWidth: 250
                onActivated: {
                    if (Backend) Backend.setCurrentJavaPath(currentText)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("Minecraft 文件夹位置")
            description: currentMcDir
            icon.name: "ic_fluent_folder_20_regular"
            RowLayout {
                spacing: 8
                Button {
                    text: qsTr("浏览...")
                    onClicked: {
                        if (Backend) {
                            var path = Backend.browseMinecraftDir()
                            if (path !== "") currentMcDir = path
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

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("Minecraft 小工具栏")
            description: qsTr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏")
            icon.name: "ic_fluent_toolbar_20_regular"
            Switch {
                checked: true
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

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("语言 / language")
            description: qsTr("调整语言设置")
            icon.name: "ic_fluent_local_language_20_regular"
            ComboBox {
                model: ["简体中文", "English"]
                Layout.preferredWidth: 150
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("主题")
            description: qsTr("选择界面的颜色模式")
            icon.name: "ic_fluent_color_20_regular"
            ComboBox {
                id: themeCombo
                model: ["Auto", "Light", "Dark"]
                Layout.preferredWidth: 150
                onActivated: {
                    if (Backend) Backend.setThemeMode(currentText)
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

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("日志文件夹位置")
            description: qsTr("存储所有 Bloret Launcher 日志的文件夹位置")
            icon.name: "ic_fluent_text_bullet_list_square_20_regular"
            Button {
                flat: true
                text: "打开"
                onClicked: { if (Backend) Backend.openLogDir() }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: qsTr("清空日志")
            description: qsTr("清空 log 文件夹所有的日志文件")
            icon.name: "ic_fluent_delete_20_regular"
            Button {
                text: qsTr("清空")
                onClicked: { if (Backend) Backend.clearLogs() }
            }
        }
    }

    Label {
        text: qsTr("设置界面大部分内容需要重启程序后生效。")
        color: Theme.currentTheme.colors.textTertialyColor
        Layout.topMargin: 10
    }
}
