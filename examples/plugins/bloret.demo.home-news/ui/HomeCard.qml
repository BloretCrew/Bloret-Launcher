import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Frame {
    id: root
    Layout.fillWidth: true
    padding: 15

    property string cardTitle: "Minecraft 新闻"
    property string pluginId: "bloret.demo.home-news"
    property var newsItems: [
        {
            "title": "示例：Minecraft 周刊",
            "summary": "这是插件主页卡片示例。可替换为 RSS / 自建 API 真实新闻。",
            "time": "今天",
            "link": "https://www.minecraft.net/"
        },
        {
            "title": "示例：快照更新提示",
            "summary": "启用本插件后，卡片会出现在主页活动横幅下方。禁用插件后自动消失。",
            "time": "示例数据",
            "link": "https://www.minecraft.net/en-us/article"
        }
    ]

    background: Rectangle {
        color: Theme.currentTheme.colors.cardColor
        radius: 8
        border.color: Theme.currentTheme.colors.cardBorderColor || Theme.currentTheme.colors.controlBorderColor
    }

    Component.onCompleted: {
        console.log("[HomeNews] 主页新闻卡片已加载 pluginId=", pluginId)
    }

    ColumnLayout {
        width: parent.width
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: cardTitle || "Minecraft 新闻"
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
                Layout.fillWidth: true
            }
            Button {
                flat: true
                text: Backend ? Backend.tr("刷新") : "刷新"
                onClicked: {
                    console.log("[HomeNews] 刷新点击（示例使用本地 mock）")
                    // 真实插件可在此请求 API，再更新 newsItems
                    newsItems = newsItems.slice(0) // 触发刷新
                }
            }
        }

        Repeater {
            model: newsItems
            delegate: ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: modelData.title || ""
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
                Label {
                    text: modelData.summary || ""
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                    font.pixelSize: 13
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: modelData.time || ""
                        color: Theme.currentTheme.colors.textTertialyColor || Theme.currentTheme.colors.textSecondaryColor
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }
                    Button {
                        flat: true
                        text: Backend ? Backend.tr("打开") : "打开"
                        onClicked: {
                            console.log("[HomeNews] open", modelData.link)
                            if (Backend && modelData.link)
                                Backend.openUrl(modelData.link)
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Theme.currentTheme.colors.controlBorderColor
                    opacity: 0.4
                    visible: index < newsItems.length - 1
                }
            }
        }
    }
}
