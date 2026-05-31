import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: gitPage

    property var changedFiles: []  // [{path, status, selected}]
    property var commitHistory: []
    property string viewMode: "changes"

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshGitData()
        }
        function onFileTreeChanged(tree) {
            refreshGitData()
        }
    }

    function refreshGitData() {
        if (!RPEditor) return
        // 获取所有变更文件（合并 staged + unstaged）
        var files = []
        try {
            var status = JSON.parse(RPEditor.getGitStatus())
            for (var path in status) {
                files.push({path: path, status: status[path], selected: true})
            }
        } catch(e) {}
        changedFiles = files

        try {
            commitHistory = JSON.parse(RPEditor.getCommitLog(50))
        } catch(e) { commitHistory = [] }
    }

    function toggleAll() {
        var allSelected = true
        for (var i = 0; i < changedFiles.length; i++) {
            if (!changedFiles[i].selected) { allSelected = false; break }
        }
        var newArr = []
        for (var j = 0; j < changedFiles.length; j++) {
            var f = changedFiles[j]
            newArr.push({path: f.path, status: f.status, selected: !allSelected})
        }
        changedFiles = newArr
    }

    function toggleFile(index) {
        var f = changedFiles[index]
        var newArr = changedFiles.slice()
        newArr[index] = {path: f.path, status: f.status, selected: !f.selected}
        changedFiles = newArr
    }

    function getSelectedPaths() {
        var paths = []
        for (var i = 0; i < changedFiles.length; i++) {
            if (changedFiles[i].selected) paths.push(changedFiles[i].path)
        }
        return paths
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentHeight: rootColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: rootColumn
            width: parent.width
            spacing: 16

            // 顶部标题栏
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Label {
                    text: "Git 管理"
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "刷新"
                    flat: true
                    onClicked: refreshGitData()
                }
            }

            // 视图切换
            RowLayout {
                Layout.fillWidth: true
                spacing: 2

                Button {
                    text: "更改"
                    flat: true
                    highlighted: viewMode === "changes"
                    onClicked: viewMode = "changes"
                }

                Button {
                    text: "提交历史"
                    flat: true
                    highlighted: viewMode === "history"
                    onClicked: viewMode = "history"
                }
            }

            // ===== 更改视图 =====
            ColumnLayout {
                Layout.fillWidth: true
                visible: viewMode === "changes"
                spacing: 12

                // 全选 + 提交按钮栏
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16; anchors.rightMargin: 16
                        spacing: 12

                        // 全选 Checkbox
                        CheckBox {
                            id: selectAllBox
                            text: "全选 (" + changedFiles.length + " 个文件)"
                            checked: {
                                if (changedFiles.length === 0) return false
                                for (var i = 0; i < changedFiles.length; i++) {
                                    if (!changedFiles[i].selected) return false
                                }
                                return true
                            }
                            tristate: false
                            font.pixelSize: 13
                            onToggled: toggleAll()
                        }

                        Item { Layout.fillWidth: true }

                        // AI 生成提交信息
                        Button {
                            icon.name: "ic_fluent_bot_20_regular"
                            font.pixelSize: 14
                            Layout.preferredWidth: 36; Layout.preferredHeight: 36
                            enabled: getSelectedPaths().length > 0
                            onClicked: {
                                if (!Agent) return
                                var filesJson = JSON.stringify(changedFiles.filter(function(f) { return f.selected }))
                                commitMsgInput.text = "生成中..."
                                var msg = Agent.generateCommitMessage(filesJson)
                                commitMsgInput.text = msg
                            }
                        }

                        // 提交信息
                        TextField {
                            id: commitMsgInput
                            Layout.preferredWidth: 250
                            placeholderText: "输入提交信息..."
                            font.pixelSize: 12
                        }

                        // 提交按钮
                        Button {
                            text: "提交 (" + getSelectedPaths().length + ")"
                            highlighted: true
                            enabled: getSelectedPaths().length > 0 && commitMsgInput.text.trim() !== ""
                            onClicked: {
                                if (!RPEditor) return
                                // 先 stage 选中的文件
                                var paths = getSelectedPaths()
                                for (var i = 0; i < paths.length; i++) {
                                    RPEditor.stageFile(paths[i])
                                }
                                // 提交
                                RPEditor.commit(commitMsgInput.text.trim())
                                commitMsgInput.text = ""
                                refreshGitData()
                            }
                        }
                    }
                }

                // 文件列表
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(fileColumn.implicitHeight + 24, 120)
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: fileColumn
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 4

                        Label {
                            text: "变更文件"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                            Layout.bottomMargin: 4
                        }

                        Repeater {
                            model: changedFiles

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 32
                                radius: 4
                                color: index % 2 === 0 ? "transparent" : (Theme.currentTheme.colors.controlAltSecondaryColor || "#F8F8F8")

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8; anchors.rightMargin: 8
                                    spacing: 8

                                    CheckBox {
                                        checked: modelData.selected
                                        onToggled: toggleFile(index)
                                        padding: 0
                                    }

                                    // 状态标记
                                    Rectangle {
                                        width: 18; height: 18; radius: 3
                                        color: {
                                            var s = modelData.status
                                            if (s === "A") return "#4CAF50"
                                            if (s === "M") return "#FF9800"
                                            if (s === "D") return "#9E9E9E"
                                            if (s === "U") return "#2196F3"
                                            return "#757575"
                                        }
                                        Label {
                                            anchors.centerIn: parent
                                            text: modelData.status || "?"
                                            font.pixelSize: 10; font.bold: true; color: "#FFFFFF"
                                        }
                                    }

                                    Label {
                                        text: modelData.path
                                        font.pixelSize: 12
                                        font.family: "monospace"
                                        color: Theme.currentTheme.colors.textColor
                                        elide: Text.ElideMiddle
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }

                        Label {
                            visible: changedFiles.length === 0
                            text: "没有变更的文件"
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.fillWidth: true
                            Layout.topMargin: 16
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }

                // 状态说明
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Layout.topMargin: 4

                    Row { spacing: 4
                        Rectangle { width: 10; height: 10; radius: 2; color: "#4CAF50" }
                        Label { text: "新增"; font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor }
                    }
                    Row { spacing: 4
                        Rectangle { width: 10; height: 10; radius: 2; color: "#FF9800" }
                        Label { text: "修改"; font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor }
                    }
                    Row { spacing: 4
                        Rectangle { width: 10; height: 10; radius: 2; color: "#9E9E9E" }
                        Label { text: "删除"; font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor }
                    }
                    Row { spacing: 4
                        Rectangle { width: 10; height: 10; radius: 2; color: "#2196F3" }
                        Label { text: "未跟踪"; font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor }
                    }
                }
            }

            // ===== 提交历史视图 =====
            ColumnLayout {
                Layout.fillWidth: true
                visible: viewMode === "history"
                spacing: 12

                Repeater {
                    model: commitHistory

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 60
                        radius: 8
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 4

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    width: 8; height: 8; radius: 4
                                    color: Theme.accentColor || "#0078D4"
                                }

                                Label {
                                    text: modelData.message
                                    font.pixelSize: 13; font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }

                            Label {
                                text: modelData.author + " · " + new Date(modelData.timestamp * 1000).toLocaleString()
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }

                            Label {
                                text: modelData.id.substring(0, 12)
                                font.family: "monospace"; font.pixelSize: 10
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }
                }

                Label {
                    visible: commitHistory.length === 0
                    text: "没有提交历史"
                    font.pixelSize: 14
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.topMargin: 32
                }
            }
        }
    }
}
