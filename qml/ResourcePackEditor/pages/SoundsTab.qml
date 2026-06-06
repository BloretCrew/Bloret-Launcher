import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: soundsPage

    property int _currentTab: 0
    property var _soundsJsonFiles: []
    property var _soundFiles: []
    property int _selectedJsonIndex: -1
    property string _selectedJsonPath: ""
    property string _selectedJsonNamespace: ""
    property string _originalJsonContent: ""
    property bool _jsonModified: false

    property string _detailName: ""
    property string _detailPath: ""
    property string _detailNamespace: ""
    property string _detailSize: ""

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshAll()
        }
    }

    function refreshAll() {
        refreshSoundsJson()
        refreshSoundFiles()
    }

    function refreshSoundsJson() {
        if (!RPEditor) return
        _soundsJsonFiles = RPEditor.getSoundsJson()
        jsonFileList.model = _soundsJsonFiles
        jsonCountLabel.text = "共 " + _soundsJsonFiles.length + " 个文件"
    }

    function refreshSoundFiles() {
        if (!RPEditor) return
        _soundFiles = RPEditor.getSoundFiles()
        soundGrid.model = _soundFiles
        soundCountLabel.text = "共 " + _soundFiles.length + " 个音频"
    }

    function selectSoundsJson(index) {
        if (index < 0 || index >= _soundsJsonFiles.length) return
        _selectedJsonIndex = index
        var item = _soundsJsonFiles[index]
        _selectedJsonPath = item.path
        _selectedJsonNamespace = item.namespace
        jsonEditorTitle.text = item.namespace + " — " + item.path

        if (RPEditor) {
            var content = RPEditor.getFileContent(item.path)
            _originalJsonContent = content
            jsonEditor.text = content
            _jsonModified = false
        }
    }

    function saveSoundsJson() {
        if (!_selectedJsonPath || !RPEditor) return
        RPEditor.saveFile(_selectedJsonPath, jsonEditor.text)
        _originalJsonContent = jsonEditor.text
        _jsonModified = false
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B"
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
        return (bytes / (1024 * 1024)).toFixed(2) + " MB"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Label {
                text: "音频管理"
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            Item { Layout.fillWidth: true }

            RowLayout {
                spacing: 4

                Rectangle {
                    width: segBtn1.implicitWidth + 24
                    height: 30
                    radius: 6
                    color: _currentTab === 0 ? Theme.currentTheme.colors.cardColor : "transparent"
                    border.color: _currentTab === 0 ? Theme.currentTheme.colors.controlBorderColor : "transparent"

                    Label {
                        id: segBtn1
                        anchors.centerIn: parent
                        text: "sounds.json 编辑器"
                        font.pixelSize: 12
                        color: _currentTab === 0 ? Theme.currentTheme.colors.textColor : Theme.currentTheme.colors.textSecondaryColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: _currentTab = 0
                    }
                }

                Rectangle {
                    width: segBtn2.implicitWidth + 24
                    height: 30
                    radius: 6
                    color: _currentTab === 1 ? Theme.currentTheme.colors.cardColor : "transparent"
                    border.color: _currentTab === 1 ? Theme.currentTheme.colors.controlBorderColor : "transparent"

                    Label {
                        id: segBtn2
                        anchors.centerIn: parent
                        text: "音频文件"
                        font.pixelSize: 12
                        color: _currentTab === 1 ? Theme.currentTheme.colors.textColor : Theme.currentTheme.colors.textSecondaryColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: _currentTab = 1
                    }
                }
            }
        }

        // sounds.json Editor View
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: _currentTab === 0
            radius: 8
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                ColumnLayout {
                    Layout.preferredWidth: 220
                    Layout.fillHeight: true
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "sounds.json 文件"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        Item { Layout.fillWidth: true }
                        Label {
                            id: jsonCountLabel
                            text: "共 0 个文件"
                            font.pixelSize: 11
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 4
                        color: Theme.currentTheme.colors.controlAltSecondaryColor
                        border.color: Theme.currentTheme.colors.controlBorderColor

                        ListView {
                            id: jsonFileList
                            anchors.fill: parent
                            anchors.margins: 4
                            clip: true
                            spacing: 2

                            delegate: Rectangle {
                                width: jsonFileList.width - 8
                                height: 36
                                radius: 4
                                color: _selectedJsonIndex === index ? (Theme.accentColor || "#0078D4") : "transparent"

                                ColumnLayout {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 8
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 1

                                    Label {
                                        text: modelData.namespace
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                        color: _selectedJsonIndex === index ? "#FFFFFF" : Theme.currentTheme.colors.textColor
                                    }
                                    Label {
                                        text: modelData.path
                                        font.pixelSize: 9
                                        font.family: "monospace"
                                        color: _selectedJsonIndex === index ? "#FFFFFF" : Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideMiddle
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        jsonFileList.currentIndex = index
                                        selectSoundsJson(index)
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 4
                    color: Theme.currentTheme.colors.controlAltSecondaryColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                id: jsonEditorTitle
                                text: "选择一个 sounds.json 文件"
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                font.family: "monospace"
                                color: Theme.currentTheme.colors.textColor
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                            }

                            Label {
                                visible: _jsonModified
                                text: "● 已修改"
                                font.pixelSize: 11
                                color: "#FF9800"
                            }

                            Button {
                                text: "保存"
                                highlighted: true
                                enabled: _selectedJsonPath && _jsonModified && RPEditor
                                onClicked: saveSoundsJson()
                            }

                            Button {
                                text: "重置"
                                enabled: _selectedJsonPath && _jsonModified
                                onClicked: {
                                    jsonEditor.text = _originalJsonContent
                                    _jsonModified = false
                                }
                            }
                        }

                        Flickable {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            contentHeight: jsonEditor.height

                            TextArea {
                                id: jsonEditor
                                width: parent.width
                                font.family: "monospace"
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textColor
                                background: null
                                wrapMode: Text.NoWrap
                                placeholderText: "选择左侧文件以编辑 JSON..."
                                onTextChanged: {
                                    _jsonModified = (text !== _originalJsonContent)
                                }
                            }
                        }
                    }
                }
            }
        }

        // Sound Files Browser View
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: _currentTab === 1
            radius: 8
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.controlBorderColor

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            text: "音频文件"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }

                        Item { Layout.fillWidth: true }

                        TextField {
                            id: soundSearchInput
                            Layout.preferredWidth: 200
                            placeholderText: "搜索音频..."
                            onTextChanged: {
                                if (!_soundFiles) return
                                var query = text.toLowerCase().trim()
                                if (!query) {
                                    soundGrid.model = _soundFiles
                                    soundCountLabel.text = "共 " + _soundFiles.length + " 个音频"
                                    return
                                }
                                var filtered = []
                                for (var i = 0; i < _soundFiles.length; i++) {
                                    var f = _soundFiles[i]
                                    if (f.name.toLowerCase().includes(query) ||
                                        f.path.toLowerCase().includes(query) ||
                                        f.namespace.toLowerCase().includes(query)) {
                                        filtered.push(f)
                                    }
                                }
                                soundGrid.model = filtered
                                soundCountLabel.text = "共 " + filtered.length + " 个音频"
                            }
                        }

                        Label {
                            id: soundCountLabel
                            text: "共 0 个音频"
                            font.pixelSize: 11
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentHeight: soundGrid.contentHeight

                        GridView {
                            id: soundGrid
                            anchors.fill: parent
                            cellWidth: 260
                            cellHeight: 64
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                width: 250
                                height: 56
                                radius: 6
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                border.color: Theme.currentTheme.colors.controlBorderColor

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 8

                                    Rectangle {
                                        width: 36
                                        height: 36
                                        radius: 6
                                        color: Theme.currentTheme.colors.cardColor

                                        Icon {
                                            anchors.centerIn: parent
                                            icon: "ic_fluent_music_note_20_regular"
                                            size: 20
                                            color: Theme.accentColor || "#0078D4"
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 2

                                        Label {
                                            text: modelData.name
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                            color: Theme.currentTheme.colors.textColor
                                            elide: Text.ElideMiddle
                                            Layout.fillWidth: true
                                        }

                                        Label {
                                            text: modelData.namespace
                                            font.pixelSize: 10
                                            color: Theme.accentColor || "#0078D4"
                                            Layout.fillWidth: true
                                        }

                                        Label {
                                            text: modelData.path
                                            font.pixelSize: 9
                                            font.family: "monospace"
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            elide: Text.ElideMiddle
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        _detailName = modelData.name
                                        _detailPath = modelData.path
                                        _detailNamespace = modelData.namespace
                                        _detailSize = ""
                                        if (RPEditor && RPEditor.getSoundFileSize) {
                                            var sz = RPEditor.getSoundFileSize(modelData.path)
                                            _detailSize = formatFileSize(sz)
                                        }
                                        soundDetailDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: soundDetailDialog
        title: "音频文件详情"
        modal: true
        width: 420
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 56
                radius: 8
                color: Theme.currentTheme.colors.controlAltSecondaryColor

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    Rectangle {
                        width: 36
                        height: 36
                        radius: 6
                        color: Theme.currentTheme.colors.cardColor

                        Icon {
                            anchors.centerIn: parent
                            icon: "ic_fluent_music_note_20_regular"
                            size: 22
                            color: Theme.accentColor || "#0078D4"
                        }
                    }

                    Label {
                        text: _detailName
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                        Layout.fillWidth: true
                    }
                }
            }

            ColumnLayout {
                spacing: 4

                Label {
                    text: "命名空间"
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                Label {
                    text: _detailNamespace
                    font.pixelSize: 12
                    font.family: "monospace"
                    color: Theme.accentColor || "#0078D4"
                }
            }

            ColumnLayout {
                spacing: 4

                Label {
                    text: "文件路径"
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                Label {
                    text: _detailPath
                    font.pixelSize: 12
                    font.family: "monospace"
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }

            ColumnLayout {
                visible: _detailSize !== ""
                spacing: 4

                Label {
                    text: "文件大小"
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                Label {
                    text: _detailSize
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textColor
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "关闭"
                    onClicked: soundDetailDialog.close()
                }
            }
        }
    }
}
