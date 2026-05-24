import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: gitPage

    property var stagedFiles: []
    property var unstagedFiles: []
    property var commitHistory: []
    property string selectedFile: ""
    property string diffText: ""
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
        try {
            stagedFiles = JSON.parse(RPEditor.getStagedFiles())
        } catch(e) { stagedFiles = [] }
        try {
            unstagedFiles = JSON.parse(RPEditor.getUnstagedFiles())
        } catch(e) { unstagedFiles = [] }
        try {
            commitHistory = JSON.parse(RPEditor.getCommitLog(50))
        } catch(e) { commitHistory = [] }
    }

    function loadDiff(filePath) {
        if (!RPEditor) return
        selectedFile = filePath
        diffText = RPEditor.getDiff(filePath)
        if (!diffText) diffText = "(无差异或文件为新文件)"
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
                    text: "暂存全部"
                    enabled: unstagedFiles.length > 0
                    onClicked: {
                        if (RPEditor) {
                            RPEditor.stageAll()
                            refreshGitData()
                        }
                    }
                }

                Button {
                    text: "取消全部暂存"
                    enabled: stagedFiles.length > 0
                    onClicked: {
                        if (RPEditor) {
                            RPEditor.unstageAll()
                            refreshGitData()
                        }
                    }
                }

                Button {
                    text: "刷新"
                    flat: true
                    onClicked: refreshGitData()
                }
            }

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

            ColumnLayout {
                Layout.fillWidth: true
                visible: viewMode === "changes"
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(stagedColumn.implicitHeight + 32, 80)
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: stagedColumn
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: "#4CAF50"
                            }

                            Label {
                                text: "已暂存 (" + stagedFiles.length + ")"
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }

                            Item { Layout.fillWidth: true }
                        }

                        Repeater {
                            model: stagedFiles

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    width: 18
                                    height: 18
                                    radius: 3
                                    color: {
                                        var op = modelData.operation
                                        if (op === "add") return "#4CAF50"
                                        if (op === "modify") return "#FF9800"
                                        if (op === "delete") return "#9E9E9E"
                                        return "#2196F3"
                                    }

                                    Label {
                                        anchors.centerIn: parent
                                        text: {
                                            var op = modelData.operation
                                            if (op === "add") return "A"
                                            if (op === "modify") return "M"
                                            if (op === "delete") return "D"
                                            return "?"
                                        }
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                        color: "#FFFFFF"
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

                                Button {
                                    text: "取消暂存"
                                    flat: true
                                    onClicked: {
                                        if (RPEditor) {
                                            RPEditor.stagePath(modelData.path, "unstage")
                                            refreshGitData()
                                        }
                                    }
                                }
                            }
                        }

                        Label {
                            visible: stagedFiles.length === 0
                            text: "没有已暂存的文件"
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(unstagedColumn.implicitHeight + 32, 80)
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: unstagedColumn
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: "#FF9800"
                            }

                            Label {
                                text: "未暂存 (" + unstagedFiles.length + ")"
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }

                            Item { Layout.fillWidth: true }
                        }

                        Repeater {
                            model: unstagedFiles

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    width: 18
                                    height: 18
                                    radius: 3
                                    color: "#FF9800"

                                    Label {
                                        anchors.centerIn: parent
                                        text: "?"
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                        color: "#FFFFFF"
                                    }
                                }

                                Label {
                                    text: modelData
                                    font.pixelSize: 12
                                    font.family: "monospace"
                                    color: Theme.currentTheme.colors.textColor
                                    elide: Text.ElideMiddle
                                    Layout.fillWidth: true

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onDoubleClicked: loadDiff(modelData)
                                    }
                                }

                                Button {
                                    text: "暂存"
                                    flat: true
                                    onClicked: {
                                        if (RPEditor) {
                                            RPEditor.stageFile(modelData)
                                            refreshGitData()
                                        }
                                    }
                                }
                            }
                        }

                        Label {
                            visible: unstagedFiles.length === 0
                            text: "没有未暂存的更改"
                            font.pixelSize: 12
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: commitColumn.implicitHeight + 32
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: commitColumn
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        Label {
                            text: "提交"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        TextField {
                            id: commitInput
                            Layout.fillWidth: true
                            placeholderText: "输入提交信息..."
                            enabled: stagedFiles.length > 0

                            onAccepted: {
                                if (text.trim() && RPEditor) {
                                    RPEditor.commit(text.trim())
                                    text = ""
                                    refreshGitData()
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true

                            Item { Layout.fillWidth: true }

                            Button {
                                text: "提交"
                                highlighted: true
                                enabled: stagedFiles.length > 0 && commitInput.text.trim() !== ""
                                onClicked: {
                                    if (RPEditor) {
                                        RPEditor.commit(commitInput.text.trim())
                                        commitInput.text = ""
                                        refreshGitData()
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    visible: selectedFile !== ""
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(diffColumn.implicitHeight + 32, 120)
                    radius: 8
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor

                    ColumnLayout {
                        id: diffColumn
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "差异: " + selectedFile
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                                Layout.fillWidth: true
                            }

                            Button {
                                text: "关闭"
                                flat: true
                                onClicked: {
                                    selectedFile = ""
                                    diffText = ""
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 200
                            radius: 4
                            color: Theme.currentTheme.colors.controlAltSecondaryColor

                            Flickable {
                                anchors.fill: parent
                                anchors.margins: 8
                                clip: true
                                contentHeight: diffArea.height

                                TextArea {
                                    id: diffArea
                                    width: parent.width
                                    readOnly: true
                                    text: diffText
                                    font.family: "monospace"
                                    font.pixelSize: 11
                                    color: Theme.currentTheme.colors.textColor
                                    background: null
                                    wrapMode: Text.NoWrap
                                }
                            }
                        }
                    }
                }
            }

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
                                    width: 8
                                    height: 8
                                    radius: 4
                                    color: Theme.accentColor || "#0078D4"
                                }

                                Label {
                                    text: modelData.message
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
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
                                font.family: "monospace"
                                font.pixelSize: 10
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
