import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: settingsPage
    title: qsTr("设置")

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
                    model: Backend.getSystemJavas()
                    Layout.minimumWidth: 250
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            // Minecraft Dir
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 文件夹位置") }
                    Label { text: qsTr("存储所有 Minecraft 信息、资源以及各种版本的文件夹位置"); color: "#7f7f7f"; wrapMode: Text.Wrap }
                }
                Button {
                    flat: true
                    text: ".minecraft"
                    onClicked: Backend.openMinecraftDir()
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            // Mini Toolbar
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("Minecraft 小工具栏") }
                    Label { text: qsTr("当游玩 Minecraft 时，在 Minecraft 窗口上方\n显示一个快捷小工具栏，方便快速操作"); color: "#7f7f7f"; wrapMode: Text.Wrap }
                }
                Switch {
                    checked: true
                }
            }
        }
    }

    // --- Download Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("下载")
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

        RowLayout {
            width: parent.width
            ColumnLayout {
                Layout.fillWidth: true
                Label { font.weight: Font.DemiBold; text: qsTr("最大线程数") }
                Label { text: qsTr("下载文件时允许同时下载文件的最大数量\n该数字越大,下载速度越快,但会占用计算机更多性能。"); color: "#7f7f7f"; wrapMode: Text.Wrap }
            }
            SpinBox {
                from: 1
                to: 10000
                value: 100
            }
        }
    }

    // --- Interface Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("界面")
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

        RowLayout {
            width: parent.width
            ColumnLayout {
                Layout.fillWidth: true
                Label { font.weight: Font.DemiBold; text: qsTr("缩放") }
                Label { text: qsTr("默认启动的窗口大小(重新启动程序后生效)"); color: "#7f7f7f" }
            }
            SpinBox {
                from: 50
                to: 200
                value: 100
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
                    model: ["浅色", "深色", "跟随系统"]
                    Layout.minimumWidth: 150
                    enabled: false
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

    // --- Behavior Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("行为")
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
                    Label { font.weight: Font.DemiBold; text: qsTr("开机自启动") }
                    Label { text: qsTr("开机时一并打开 Bloret Launcher, 并最小化至系统托盘"); color: "#7f7f7f" }
                }
                Switch {
                    checked: false
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("重复启动程序") }
                    Label { text: qsTr("防止 Bloret Launcher 占满您的计算机"); color: "#7f7f7f" }
                }
                Switch {
                    checked: false
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("显示软件打开过程") }
                    Label { text: qsTr("在软件打开前以通知的形式显示软件在做什么"); color: "#7f7f7f" }
                }
                Switch {
                    checked: true
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("在首页上 显示 Minecraft 账户登录方式") }
                    Label { text: qsTr("展示你为微软登录或是离线登录"); color: "#7f7f7f" }
                }
                Switch {
                    checked: false
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.currentTheme.colors.surfaceStrokeColorDefault }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    Label { font.weight: Font.DemiBold; text: qsTr("本地模式") }
                    Label { text: qsTr("不连接一部分的互联网，不允许使用 PCFS 服务。"); color: "#7f7f7f" }
                }
                Switch {
                    checked: false
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
