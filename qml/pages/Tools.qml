import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: toolsPage
    title: qsTr("小工具")

    Connections {
        target: Backend
        onQueryResultReceived: (data) => {
            if (data.type === "uuid") {
                uuidResult.text = data.success ? data.result : qsTr("查询失败")
            } else if (data.type === "name") {
                nameResult.text = data.success ? data.result : qsTr("查询失败")
            } else if (data.type === "textures") {
                if (data.success) {
                    skinResult.text = data.skin || qsTr("未找到皮肤")
                    capeResult.text = data.cape || qsTr("未找到披风")
                } else {
                    skinResult.text = qsTr("查询失败")
                    capeResult.text = qsTr("查询失败")
                }
            }
        }
        onEasytierStatusChanged: (title, desc) => {
            etStatusTitle.text = title
            etStatusDesc.text = desc
        }
    }

    // --- Screen Cut Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("屏幕截图")
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
                spacing: 15

                Image {
                    source: "../../icon/imageres 017.png"
                    sourceSize { width: 40; height: 40 }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        font.weight: Font.DemiBold
                        font.pixelSize: 16
                        text: qsTr("Bloret Launcher Screen Cut")
                    }
                    Label {
                        text: qsTr("便捷地截取屏幕画面，包括 Minecraft 窗口")
                        color: "#7f7f7f"
                        wrapMode: Text.Wrap
                    }
                }

                Button {
                    text: qsTr("截图")
                    onClicked: Backend.takeScreenCut()
                }
            }
        }
    }

    // --- Minecraft Data Lookup Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("Minecraft 数据查询")
        Layout.topMargin: 10
    }

    // UUID Lookup
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

            Label {
                font.weight: Font.DemiBold
                text: qsTr("查询玩家UUID")
            }

            Item { Layout.fillWidth: true }

            ColumnLayout {
                Layout.maximumWidth: 450
                Layout.preferredWidth: 350

                TextField {
                    id: uuidInput
                    Layout.fillWidth: true
                    placeholderText: qsTr("玩家名称（正版）")
                }
                
                Button {
                    Layout.fillWidth: true
                    text: qsTr("查询")
                    onClicked: {
                        uuidResult.text = qsTr("查询中...")
                        Backend.queryUUID(uuidInput.text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        id: uuidResult
                        text: qsTr("查询的结果将显示在这里")
                        Layout.fillWidth: true
                        elide: Text.ElideMiddle
                    }
                    Button {
                        text: qsTr("复制")
                        onClicked: Backend.copyToClipboard(uuidResult.text)
                    }
                }
            }
        }
    }

    // Name Lookup
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

            Label {
                font.weight: Font.DemiBold
                text: qsTr("查询玩家名字")
            }

            Item { Layout.fillWidth: true }

            ColumnLayout {
                Layout.maximumWidth: 450
                Layout.preferredWidth: 350

                TextField {
                    id: nameInput
                    Layout.fillWidth: true
                    placeholderText: qsTr("玩家UUID")
                }
                
                Button {
                    Layout.fillWidth: true
                    text: qsTr("查询")
                    onClicked: {
                        nameResult.text = qsTr("查询中...")
                        Backend.queryName(nameInput.text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        id: nameResult
                        text: qsTr("查询的结果将显示在这里")
                        Layout.fillWidth: true
                    }
                    Button {
                        text: qsTr("复制")
                        onClicked: Backend.copyToClipboard(nameResult.text)
                    }
                }
            }
        }
    }

    // Skin and Cape Lookup
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

            Label {
                font.weight: Font.DemiBold
                text: qsTr("获取玩家的皮肤和披风")
            }

            Item { Layout.fillWidth: true }

            ColumnLayout {
                Layout.maximumWidth: 450
                Layout.preferredWidth: 350

                TextField {
                    id: skinInput
                    Layout.fillWidth: true
                    placeholderText: qsTr("玩家UUID")
                }
                
                Button {
                    Layout.fillWidth: true
                    text: qsTr("查询")
                    onClicked: {
                        skinResult.text = qsTr("查询中...")
                        capeResult.text = qsTr("查询中...")
                        Backend.querySkin(skinInput.text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        id: skinResult
                        text: qsTr("皮肤的查询的结果")
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    Button {
                        text: qsTr("复制")
                        onClicked: Backend.copyToClipboard(skinResult.text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        id: capeResult
                        text: qsTr("披风的查询的结果")
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    Button {
                        text: qsTr("复制")
                        onClicked: Backend.copyToClipboard(capeResult.text)
                    }
                }
            }
        }
    }

    // --- EasyTier Section ---
    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: qsTr("EasyTier 组网")
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
            spacing: 15

            Image {
                source: "../../icon/easytier.png"
                sourceSize { width: 40; height: 40 }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    id: etStatusTitle
                    font.weight: Font.DemiBold
                    text: Backend.getEasytierStatusTitle()
                }
                Label {
                    id: etStatusDesc
                    text: Backend.getEasytierStatusDesc()
                    color: "#7f7f7f"
                }
            }

            Button {
                text: qsTr("启动服务器")
                onClicked: Backend.startEasytierHost()
            }
            Button {
                text: qsTr("连接节点")
                onClicked: Backend.startEasytierClient()
            }
        }
    }
}
