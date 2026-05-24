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
                cursorShape: Qt.PointingHandCursor
                onClicked: {
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
