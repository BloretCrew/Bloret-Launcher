import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: statsPage
    title: (Backend ? Backend.tr("统计信息") : "统计信息")

    property var overview: ({})
    property var versionStats: []
    property var sessionList: []
    property var dateList: []
    property var allVersions: []
    property int currentPage: 1
    property int totalPages: 1
    property int totalSessions: 0
    property string selectedDateFilter: ""
    property string selectedVersionFilter: ""

    Component.onCompleted: {
        refreshAll()
    }

    Connections {
        target: Backend
        function onStatisticsUpdated() {
            refreshAll()
        }
    }

    function refreshAll() {
        if (!Backend) return
        overview = Backend.getPlayStatisticsOverview()
        versionStats = Backend.getPlayStatisticsVersions()
        dateList = Backend.getPlayStatisticsDates()
        allVersions = Backend.getPlayStatisticsAllVersions()
        currentPage = 1
        loadSessions()
    }

    function loadSessions() {
        if (!Backend) return
        var result = Backend.getPlayStatisticsPaginated(
            selectedDateFilter, selectedVersionFilter,
            currentPage, 15
        )
        sessionList = result.sessions || []
        totalPages = result.total_pages || 1
        totalSessions = result.total || 0
    }

    function formatTime(seconds) {
        if (!Backend) return "0s"
        return Backend.formatPlayTime(seconds)
    }

    content: ColumnLayout {
            id: contentColumn
            spacing: 20

            // ===== Overview Section =====
            Label {
                font.pixelSize: 22
                font.weight: Font.Bold
                text: (Backend ? Backend.tr("总览") : "总览")
                color: Theme.currentTheme.colors.textColor
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                // Total Time Card
                Frame {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 6
                        Label {
                            text: (Backend ? Backend.tr("总游戏时间") : "总游戏时间")
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime(overview.total || 0)
                            font.pixelSize: 24
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: (Backend ? Backend.tr("前台 ") : "前台 ") + formatTime(overview.total_foreground || 0) + " / " + (Backend ? Backend.tr("后台 ") : "后台 ") + formatTime(overview.total_background || 0)
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }
                }

                // Today Card
                Frame {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 6
                        Label {
                            text: (Backend ? Backend.tr("今日游玩") : "今日游玩")
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime((overview.today || {}).total || 0)
                            font.pixelSize: 24
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: ((overview.today || {}).sessions || 0) + (Backend ? Backend.tr(" 次会话") : " 次会话")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }
                }

                // This Week Card
                Frame {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 6
                        Label {
                            text: (Backend ? Backend.tr("本周游玩") : "本周游玩")
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime((overview.this_week || {}).total || 0)
                            font.pixelSize: 24
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: ((overview.this_week || {}).sessions || 0) + (Backend ? Backend.tr(" 次会话") : " 次会话")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }
                }

                // This Month Card
                Frame {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 6
                        Label {
                            text: (Backend ? Backend.tr("本月游玩") : "本月游玩")
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime((overview.this_month || {}).total || 0)
                            font.pixelSize: 24
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: ((overview.this_month || {}).sessions || 0) + (Backend ? Backend.tr(" 次会话") : " 次会话")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textTertialyColor
                        }
                    }
                }
            }

            // ===== Stats Row 2 =====
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Frame {
                    Layout.fillWidth: true
                    padding: 14
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 4
                        Label {
                            text: (Backend ? Backend.tr("游戏天数") : "游戏天数")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: (overview.unique_days || 0) + (Backend ? Backend.tr(" 天") : " 天")
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }

                Frame {
                    Layout.fillWidth: true
                    padding: 14
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 4
                        Label {
                            text: (Backend ? Backend.tr("日均游玩") : "日均游玩")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime(overview.avg_per_day || 0)
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }

                Frame {
                    Layout.fillWidth: true
                    padding: 14
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 4
                        Label {
                            text: (Backend ? Backend.tr("最长单日") : "最长单日")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: formatTime(overview.longest_day_time || 0)
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: overview.longest_day || ""
                            font.pixelSize: 11
                            color: Theme.currentTheme.colors.textTertialyColor
                            visible: text !== ""
                        }
                    }
                }

                Frame {
                    Layout.fillWidth: true
                    padding: 14
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    ColumnLayout {
                        width: parent.width
                        spacing: 4
                        Label {
                            text: (Backend ? Backend.tr("总会话数") : "总会话数")
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        Label {
                            text: (overview.total_sessions || 0) + (Backend ? Backend.tr(" 次") : " 次")
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                }
            }

            // ===== Version Breakdown =====
            Label {
                font.pixelSize: 22
                font.weight: Font.Bold
                text: (Backend ? Backend.tr("版本统计") : "版本统计")
                color: Theme.currentTheme.colors.textColor
                Layout.topMargin: 10
            }

            Frame {
                Layout.fillWidth: true
                padding: 0
                visible: versionStats.length === 0
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }
                Label {
                    anchors.centerIn: parent
                    padding: 30
                    text: (Backend ? Backend.tr("暂无数据") : "暂无数据")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Repeater {
                model: versionStats
                delegate: Frame {
                    Layout.fillWidth: true
                    padding: 14
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    RowLayout {
                        width: parent.width
                        spacing: 16

                        Rectangle {
                            width: 40; height: 40
                            radius: 8
                            color: Theme.currentTheme.colors.primaryColor
                            opacity: 0.15
                            Label {
                                anchors.centerIn: parent
                                text: modelData.version ? modelData.version.charAt(0).toUpperCase() : "?"
                                font.pixelSize: 16
                                font.weight: Font.Bold
                                color: Theme.currentTheme.colors.primaryColor
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: modelData.version || ""
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }
                            Label {
                                text: (modelData.sessions || 0) + (Backend ? Backend.tr(" 次会话") : " 次会话")
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        ColumnLayout {
                            spacing: 2
                            Label {
                                text: formatTime(modelData.total || 0)
                                font.pixelSize: 15
                                font.weight: Font.Bold
                                color: Theme.currentTheme.colors.textColor
                                Layout.alignment: Qt.AlignRight
                            }
                            Label {
                                text: (Backend ? Backend.tr("前") : "前") + formatTime(modelData.foreground || 0) + " / " + (Backend ? Backend.tr("后") : "后") + formatTime(modelData.background || 0)
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textTertialyColor
                                Layout.alignment: Qt.AlignRight
                            }
                        }
                    }
                }
            }

            // ===== Session History =====
            Label {
                font.pixelSize: 22
                font.weight: Font.Bold
                text: (Backend ? Backend.tr("会话记录") : "会话记录")
                color: Theme.currentTheme.colors.textColor
                Layout.topMargin: 10
            }

            // Filters
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ComboBox {
                    id: dateFilterCombo
                    Layout.preferredWidth: 180
                    textRole: "text"
                    valueRole: "value"
                    placeholderText: (Backend ? Backend.tr("按日期筛选") : "按日期筛选")
                    model: {
                        var items = [{text: (Backend ? Backend.tr("全部日期") : "全部日期"), value: ""}]
                        for (var i = 0; i < dateList.length; i++) {
                            items.push({text: dateList[i], value: dateList[i]})
                        }
                        return items
                    }
                    onCurrentValueChanged: {
                        selectedDateFilter = currentValue || ""
                        currentPage = 1
                        loadSessions()
                    }
                }

                ComboBox {
                    id: versionFilterCombo
                    Layout.preferredWidth: 180
                    textRole: "text"
                    valueRole: "value"
                    placeholderText: (Backend ? Backend.tr("按版本筛选") : "按版本筛选")
                    model: {
                        var items = [{text: (Backend ? Backend.tr("全部版本") : "全部版本"), value: ""}]
                        for (var i = 0; i < allVersions.length; i++) {
                            items.push({text: allVersions[i], value: allVersions[i]})
                        }
                        return items
                    }
                    onCurrentValueChanged: {
                        selectedVersionFilter = currentValue || ""
                        currentPage = 1
                        loadSessions()
                    }
                }

                Item { Layout.fillWidth: true }

                Label {
                    text: (Backend ? Backend.tr("共 ") : "共 ") + totalSessions + (Backend ? Backend.tr(" 条记录") : " 条记录")
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            // Session List
            Frame {
                Layout.fillWidth: true
                padding: 0
                visible: sessionList.length === 0
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }
                Label {
                    anchors.centerIn: parent
                    padding: 30
                    text: (Backend ? Backend.tr("暂无会话记录") : "暂无会话记录")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
            }

            Repeater {
                model: sessionList
                delegate: Frame {
                    Layout.fillWidth: true
                    padding: 12
                    background: Rectangle {
                        color: Theme.currentTheme.colors.cardColor
                        radius: 8
                        border.color: Theme.currentTheme.colors.controlBorderColor
                    }
                    RowLayout {
                        width: parent.width
                        spacing: 16

                        Rectangle {
                            width: 36; height: 36
                            radius: 8
                            color: Theme.currentTheme.colors.primaryColor
                            opacity: 0.12
                            Label {
                                anchors.centerIn: parent
                                text: modelData.version ? modelData.version.charAt(0).toUpperCase() : "?"
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: Theme.currentTheme.colors.primaryColor
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: modelData.version || ""
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }
                            RowLayout {
                                spacing: 8
                                Label {
                                    text: modelData.date || ""
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                                Label {
                                    text: (modelData.start_time || "") + " - " + (modelData.end_time || "")
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textTertialyColor
                                }
                            }
                        }

                        ColumnLayout {
                            spacing: 2
                            Label {
                                text: formatTime(modelData.total || 0)
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: Theme.currentTheme.colors.textColor
                                Layout.alignment: Qt.AlignRight
                            }
                            Label {
                                text: (Backend ? Backend.tr("前") : "前") + formatTime(modelData.foreground || 0) + " / " + (Backend ? Backend.tr("后") : "后") + formatTime(modelData.background || 0)
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textTertialyColor
                                Layout.alignment: Qt.AlignRight
                            }
                        }
                    }
                }
            }

            // Pagination
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                visible: totalPages > 1

                Item { Layout.fillWidth: true }

                Button {
                    icon.name: "ic_fluent_chevron_left_20_regular"
                    enabled: currentPage > 1
                    flat: true
                    onClicked: {
                        currentPage--
                        loadSessions()
                    }
                }

                Label {
                    text: currentPage + " / " + totalPages
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textColor
                    Layout.alignment: Qt.AlignVCenter
                }

                Button {
                    icon.name: "ic_fluent_chevron_right_20_regular"
                    enabled: currentPage < totalPages
                    flat: true
                    onClicked: {
                        currentPage++
                        loadSessions()
                    }
                }

                Item { Layout.fillWidth: true }
            }

            Item { height: 20 }
        }
}
