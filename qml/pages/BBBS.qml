import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: bbbsPage

    property var summaryData: ({})
    property var leaderboardData: []
    property var allPostsData: []
    property bool isLoading: true
    property bool isAuthenticated: false
    property int currentTab: 0

    Component.onCompleted: {
        if (!Backend) return
        isAuthenticated = Backend.isBBBSAuthenticated()
        if (isAuthenticated) {
            Backend.fetchBBBSSummary()
            Backend.fetchBBBSLeaderboard()
            Backend.fetchBBBSAllPosts()
        } else {
            isLoading = false
        }
    }

    Connections {
        target: Backend
        function onBbbsSummaryReceived(data) {
            summaryData = data
            isLoading = false
        }
        function onBbbsLeaderboardReceived(data) {
            leaderboardData = data
        }
        function onBbbsAllPostsReceived(data) {
            allPostsData = data
        }
        function onBbbsErrorOccurred(msg) {
            isLoading = false
            console.log("[BBBS] Error:", msg)
        }
    }

    content: ColumnLayout {
        spacing: 18

        // 页面标题
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Label {
                text: "BBBS"
                font.pixelSize: 32
                font.weight: Font.Bold
                color: Theme.currentTheme.colors.textColor
            }
            Label {
                text: (Backend ? Backend.tr("百络论坛") : "百络论坛")
                font.pixelSize: 14
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 5
            }
            
            Badge {
                text: "Bloret BBS"
                colorType: "Success"
            }

            Item { Layout.fillWidth: true }
            Button {
                text: (Backend ? Backend.tr("刷新") : "刷新")
                icon.name: "ic_fluent_arrow_sync_20_regular"
                flat: true
                visible: isAuthenticated
                onClicked: {
                    isLoading = true
                    Backend.fetchBBBSSummary()
                    Backend.fetchBBBSLeaderboard()
                    Backend.fetchBBBSAllPosts()
                }
            }
        }

        // 未登录提示
        Frame {
            Layout.fillWidth: true
            visible: !isAuthenticated
            padding: 20
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15
                Layout.alignment: Qt.AlignHCenter

                Label {
                    text: (Backend ? Backend.tr("请先登录 Bloret PassPort") : "请先登录 Bloret PassPort")
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: (Backend ? Backend.tr("登录后即可查看 BBBS 的每日摘要、热帖和最新内容") : "登录后即可查看 BBBS 的每日摘要、热帖和最新内容")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.alignment: Qt.AlignHCenter
                }
                Button {
                    text: (Backend ? Backend.tr("前往登录") : "前往登录")
                    highlighted: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: {
                        if (Backend) Backend.loginBloretPassPort()
                    }
                }
            }
        }

        // 加载中
        ProgressBar {
            Layout.fillWidth: true
            indeterminate: true
            visible: isLoading && isAuthenticated
        }

        // Tab 切换
        SelectorBar {
            id: tabBar
            visible: isAuthenticated
            Layout.fillWidth: true

            SelectorBarItem {
                text: (Backend ? Backend.tr("每日摘要") : "每日摘要")
                onClicked: currentTab = 0
            }
            SelectorBarItem {
                text: (Backend ? Backend.tr("热帖排行") : "热帖排行")
                onClicked: currentTab = 1
            }
            SelectorBarItem {
                text: (Backend ? Backend.tr("最新帖子") : "最新帖子")
                onClicked: currentTab = 2
            }
        }

        // ==================== 每日摘要 ====================
        Frame {
            Layout.fillWidth: true
            visible: isAuthenticated && currentTab === 0 && !isLoading
            padding: 20
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 10

                Label {
                    text: (Backend ? Backend.tr("AI 每日摘要") : "AI 每日摘要")
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    textFormat: Text.MarkdownText
                    text: {
                        if (!summaryData || Object.keys(summaryData).length === 0) {
                            return (Backend ? Backend.tr("暂无每日摘要") : "暂无每日摘要")
                        }
                        return summaryData.text || summaryData.content || summaryData.summary || JSON.stringify(summaryData)
                    }
                    color: Theme.currentTheme.colors.textColor
                }
            }
        }

        // ==================== 热帖排行 ====================
        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && currentTab === 1 && !isLoading
            spacing: 10

            Label {
                visible: leaderboardData.length === 0
                text: (Backend ? Backend.tr("暂无热帖数据") : "暂无热帖数据")
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Repeater {
                model: leaderboardData

                Frame {
                    Layout.fillWidth: true
                    padding: 15
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.cardBorderColor
                    }

                    RowLayout {
                        width: parent.width
                        spacing: 15

                        // 排名
                        Rectangle {
                            width: 36
                            height: 36
                            radius: 18
                            color: {
                                if (index === 0) return "#FFD700"
                                if (index === 1) return "#C0C0C0"
                                if (index === 2) return "#CD7F32"
                                return Theme.currentTheme.colors.controlColor
                            }

                            Label {
                                anchors.centerIn: parent
                                text: (index + 1).toString()
                                font.weight: Font.Bold
                                font.pixelSize: 14
                                color: index < 3 ? "#FFFFFF" : Theme.currentTheme.colors.textColor
                            }
                        }

                        // 帖子信息
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: modelData.title || modelData.name || ""
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            RowLayout {
                                spacing: 15
                                Label {
                                    text: (modelData.board || "") + (modelData.section ? " / " + modelData.section : "")
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }
                        }

                        // 统计数据
                        RowLayout {
                            spacing: 12

                            ColumnLayout {
                                spacing: 2
                                Label {
                                    text: String(modelData.likesCount || modelData.likes || 0)
                                    font.weight: Font.DemiBold
                                    font.pixelSize: 13
                                    color: Theme.currentTheme.colors.textColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: (Backend ? Backend.tr("赞") : "赞")
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textTertialyColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                            ColumnLayout {
                                spacing: 2
                                Label {
                                    text: String(modelData.commentsCount || modelData.comments || 0)
                                    font.weight: Font.DemiBold
                                    font.pixelSize: 13
                                    color: Theme.currentTheme.colors.textColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: (Backend ? Backend.tr("评论") : "评论")
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textTertialyColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                            ColumnLayout {
                                spacing: 2
                                Label {
                                    text: String(modelData.views || 0)
                                    font.weight: Font.DemiBold
                                    font.pixelSize: 13
                                    color: Theme.currentTheme.colors.textColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: (Backend ? Backend.tr("浏览") : "浏览")
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textTertialyColor
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }
                }
            }
        }

        // ==================== 最新帖子 ====================
        ColumnLayout {
            Layout.fillWidth: true
            visible: isAuthenticated && currentTab === 2 && !isLoading
            spacing: 10

            Label {
                visible: allPostsData.length === 0
                text: (Backend ? Backend.tr("暂无帖子") : "暂无帖子")
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Repeater {
                model: allPostsData

                Frame {
                    Layout.fillWidth: true
                    padding: 15
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.cardBorderColor
                    }

                    ColumnLayout {
                        width: parent.width
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            // 作者头像
                            Rectangle {
                                width: 32
                                height: 32
                                radius: 16
                                color: Theme.currentTheme.colors.controlColor
                                clip: true

                                Label {
                                    anchors.centerIn: parent
                                    text: (modelData.author || modelData.username || "?").charAt(0).toUpperCase()
                                    font.weight: Font.Bold
                                    font.pixelSize: 14
                                    color: Theme.currentTheme.colors.textColor
                                }
                            }

                            // 作者和时间
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: modelData.author || modelData.username || ""
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                }
                                Label {
                                    text: {
                                        var t = modelData.time || modelData.created_at || modelData.date || ""
                                        if (t && typeof t === "string" && t.length > 16) {
                                            return t.substring(0, 16)
                                        }
                                        return t
                                    }
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textTertialyColor
                                }
                            }

                            // 版块标签
                            Rectangle {
                                visible: !!(modelData.board)
                                width: boardLabel.implicitWidth + 16
                                height: 22
                                radius: 4
                                color: Theme.currentTheme.colors.controlColor

                                Label {
                                    id: boardLabel
                                    anchors.centerIn: parent
                                    text: modelData.board || ""
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }
                        }

                        // 标题
                        Label {
                            text: modelData.title || ""
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }

                        // 内容摘要
                        Label {
                            visible: !!(modelData.content || modelData.excerpt)
                            text: {
                                var c = modelData.content || modelData.excerpt || ""
                                if (c.length > 120) c = c.substring(0, 120) + "..."
                                return c
                            }
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            maximumLineCount: 3
                            elide: Text.ElideRight
                        }

                        // 底部统计
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 15

                            Label {
                                text: "❤ " + String(modelData.likesCount || modelData.likes || 0)
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                text: "💬 " + String(modelData.commentsCount || modelData.comments || 0)
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Label {
                                text: "👁 " + String(modelData.views || 0)
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }
        }

        // 底部留白
        Item { height: 24 }
    }
}
