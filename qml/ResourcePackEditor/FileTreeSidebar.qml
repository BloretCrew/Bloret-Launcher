import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Rectangle {
    id: fileTreeRoot
    color: "transparent"

    property var model: []
    property var _expanded: ({})
    property var _visibleList: []

    signal fileSelected(string filePath)

    function rebuildVisible() {
        _visibleList = []
        var collapsedAncestor = ""
        for (var i = 0; i < model.length; i++) {
            var item = model[i]
            var path = item.path
            var depth = item.depth || 0

            if (collapsedAncestor && path.indexOf(collapsedAncestor) === 0 && path !== collapsedAncestor) {
                continue
            }

            _visibleList.push(item)
            collapsedAncestor = ""
        }
        listView.model = _visibleList
    }

    function toggleExpand(path) {
        if (_expanded[path] === false) {
            _expanded[path] = true
        } else {
            _expanded[path] = false
        }
        rebuildVisible()
    }

    function isExpanded(path) {
        return _expanded[path] !== false
    }

    function hasCollapsedAncestor(item) {
        for (var key in _expanded) {
            if (_expanded[key] === false && item.path !== key && item.path.indexOf(key) === 0) {
                return true
            }
        }
        return false
    }

    onModelChanged: rebuildVisible()
    Component.onCompleted: rebuildVisible()

    function resetTree() {
        _expanded = {}
        rebuildVisible()
    }

    ListView {
        id: listView
        anchors.fill: parent
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        delegate: Item {
            width: listView.width
            height: 28

            property var itemData: modelData

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8 + (itemData.depth || 0) * 16
                spacing: 4

                Item {
                    width: 16
                    height: 16

                    Label {
                        anchors.centerIn: parent
                        text: {
                            if (itemData.type !== "dir") return ""
                            return fileTreeRoot.isExpanded(itemData.path) ? "▼" : "▶"
                        }
                        font.pixelSize: 8
                        color: Theme.currentTheme.colors.textSecondaryColor
                        visible: itemData.type === "dir"
                    }

                    MouseArea {
                        anchors.fill: parent
                        visible: itemData.type === "dir"
                        onClicked: fileTreeRoot.toggleExpand(itemData.path)
                    }
                }

                Rectangle {
                    width: 18
                    height: 18
                    radius: 3
                    visible: itemData.gitStatus !== ""
                    color: {
                        var s = itemData.gitStatus
                        if (s === "A") return "#4CAF50"
                        if (s === "M") return "#FF9800"
                        if (s === "D") return "#9E9E9E"
                        if (s === "U") return "#2196F3"
                        if (s === "R") return "#FFEB3B"
                        return "transparent"
                    }

                    Label {
                        anchors.centerIn: parent
                        text: itemData.gitStatus
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        color: {
                            if (itemData.gitStatus === "R") return "#333333"
                            return "#FFFFFF"
                        }
                    }
                }

                Label {
                    text: itemData.name
                    font.pixelSize: 12
                    color: {
                        if (itemData.gitStatus === "D") return "#9E9E9E"
                        if (itemData.gitStatus === "U") return "#2196F3"
                        if (itemData.gitStatus === "M") return "#FF9800"
                        if (itemData.gitStatus === "A") return "#4CAF50"
                        if (itemData.type === "dir") return Theme.accentColor || "#0078D4"
                        return Theme.currentTheme.colors.textColor
                    }
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                cursorShape: Qt.PointingHandCursor
                onClicked: function(mouse) {
                    if (mouse.button === Qt.RightButton) {
                        contextMenu._contextItem = itemData
                        contextMenu.popup()
                    } else {
                        if (itemData.type === "dir") {
                            fileTreeRoot.toggleExpand(itemData.path)
                        } else {
                            fileTreeRoot.fileSelected(itemData.path)
                        }
                    }
                }
            }
        }
    }

    Menu {
        id: contextMenu
        property var _contextItem: null

        title: _contextItem ? _contextItem.name : ""

        MenuItem {
            text: "暂存"
            enabled: contextMenu._contextItem && contextMenu._contextItem.gitStatus !== "" && contextMenu._contextItem.gitStatus !== "A"
            onTriggered: {
                if (RPEditor && contextMenu._contextItem) {
                    RPEditor.stageFile(contextMenu._contextItem.path)
                }
            }
        }

        MenuItem {
            text: "取消暂存"
            enabled: contextMenu._contextItem && contextMenu._contextItem.gitStatus === "A"
            onTriggered: {
                if (RPEditor && contextMenu._contextItem) {
                    RPEditor.unstageFile(contextMenu._contextItem.path)
                }
            }
        }

        MenuSeparator {}

        MenuItem {
            text: "创建文件"
            onTriggered: {
                createFileDialog._parentPath = contextMenu._contextItem ? (contextMenu._contextItem.type === "dir" ? contextMenu._contextItem.path : "") : ""
                createFileDialog.open()
            }
        }

        MenuItem {
            text: "重命名"
            enabled: contextMenu._contextItem && contextMenu._contextItem.type === "file"
            onTriggered: {
                if (contextMenu._contextItem) {
                    renameDialog._oldPath = contextMenu._contextItem.path
                    renameDialog._oldName = contextMenu._contextItem.name
                    renameInput.text = contextMenu._contextItem.name
                    renameDialog.open()
                }
            }
        }

        MenuSeparator {}

        MenuItem {
            text: "删除"
            enabled: contextMenu._contextItem
            onTriggered: {
                if (RPEditor && contextMenu._contextItem) {
                    RPEditor.deleteFile(contextMenu._contextItem.path)
                }
            }
        }
    }

    Dialog {
        id: createFileDialog
        title: "创建文件"
        modal: true
        width: 360
        closePolicy: Popup.CloseOnEscape
        property string _parentPath: ""

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "文件名"
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            TextField {
                id: createFileNameInput
                Layout.fillWidth: true
                placeholderText: "例如: pack.mcmeta"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "取消"
                    flat: true
                    onClicked: createFileDialog.reject()
                }
                Button {
                    text: "创建"
                    highlighted: true
                    onClicked: createFileDialog.accept()
                }
            }
        }

        onAccepted: {
            if (createFileNameInput.text.trim() && RPEditor) {
                RPEditor.createFile(_parentPath, createFileNameInput.text.trim())
                createFileNameInput.text = ""
            }
        }
    }

    Dialog {
        id: renameDialog
        title: "重命名"
        modal: true
        width: 360
        closePolicy: Popup.CloseOnEscape
        property string _oldPath: ""
        property string _oldName: ""

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "新名称"
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            TextField {
                id: renameInput
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "取消"
                    flat: true
                    onClicked: renameDialog.reject()
                }
                Button {
                    text: "重命名"
                    highlighted: true
                    onClicked: renameDialog.accept()
                }
            }
        }

        onAccepted: {
            if (renameInput.text.trim() && RPEditor && _oldPath) {
                RPEditor.renameFile(_oldPath, renameInput.text.trim())
            }
        }
    }
}
