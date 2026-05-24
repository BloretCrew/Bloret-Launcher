import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: langPage

    property var _languages: []
    property var _langData: ({})
    property string _currentLangPath: ""
    property var _filteredKeys: []

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshLanguages()
        }
    }

    function refreshLanguages() {
        if (!RPEditor) return
        _languages = RPEditor.getLanguages()
        langList.model = _languages

        if (_languages.length > 0) {
            langList.currentIndex = 0
            selectLanguage(0)
        }
    }

    function selectLanguage(index) {
        if (index < 0 || index >= _languages.length) return
        var lang = _languages[index]
        _currentLangPath = lang.path
        if (!RPEditor) return
        var raw = RPEditor.getLanguageData(lang.path)
        try {
            _langData = JSON.parse(raw)
        } catch(e) {
            _langData = {}
        }

        var keys = Object.keys(_langData)
        var items = []
        for (var i = 0; i < keys.length; i++) {
            items.push({ key: keys[i], value: _langData[keys[i]] })
        }
        _filteredKeys = items
        keyList.model = items
        langTitle.text = lang.name + " (" + lang.namespace + ")"
    }

    function doSearch() {
        var query = searchInput.text.toLowerCase().trim()
        if (!query) {
            var items = []
            for (var k in _langData) {
                items.push({ key: k, value: _langData[k] })
            }
            _filteredKeys = items
        } else {
            var filtered = []
            for (var k in _langData) {
                if (k.toLowerCase().includes(query) || String(_langData[k]).toLowerCase().includes(query)) {
                    filtered.push({ key: k, value: _langData[k] })
                }
            }
            _filteredKeys = filtered
        }
        keyList.model = _filteredKeys
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        ColumnLayout {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            spacing: 8

            Label {
                text: "语言文件"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            ListView {
                id: langList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                delegate: Rectangle {
                    width: langList.width
                    height: 32
                    color: ListView.isCurrentItem ? Theme.currentTheme.colors.accentColor : "transparent"
                    radius: 4

                    Label {
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.name
                        font.pixelSize: 12
                        color: ListView.isCurrentItem ? "#FFFFFF" : Theme.currentTheme.colors.textColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            langList.currentIndex = index
                            selectLanguage(index)
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            Label {
                id: langTitle
                text: "选择语言文件"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
            }

            TextField {
                id: searchInput
                Layout.fillWidth: true
                placeholderText: "搜索翻译键或值..."
                onTextChanged: doSearch()
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 4
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    ListView {
                        id: keyList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        delegate: Rectangle {
                            width: keyList.width
                            height: 48
                            color: index % 2 === 0 ? "transparent" : Theme.currentTheme.colors.controlAltSecondaryColor

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 8

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Label {
                                        text: modelData.key
                                        font.pixelSize: 11
                                        font.family: "monospace"
                                        color: Theme.currentTheme.colors.accentColor
                                        elide: Text.ElideMiddle
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        text: modelData.value
                                        font.pixelSize: 12
                                        color: Theme.currentTheme.colors.textColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        maximumLineCount: 1
                                    }
                                }

                                Button {
                                    text: "编辑"
                                    flat: true
                                    onClicked: {
                                        editKeyInput.text = modelData.key
                                        editValueInput.text = modelData.value
                                        editDialog.open()
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
        id: editDialog
        title: "编辑翻译键"
        modal: true
        width: 500
        standardButtons: Dialog.Save | Dialog.Cancel

        ColumnLayout {
            width: parent.width
            spacing: 8

            Label { text: "键"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
            TextField { id: editKeyInput; Layout.fillWidth: true }

            Label { text: "值"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
            TextArea { id: editValueInput; Layout.fillWidth: true; Layout.preferredHeight: 60; wrapMode: Text.Wrap }
        }

        onAccepted: {
            if (!_currentLangPath || !RPEditor) return
            _langData[editKeyInput.text] = editValueInput.text
            RPEditor.saveLanguageData(_currentLangPath, JSON.stringify(_langData, null, 2))
            selectLanguage(langList.currentIndex)
        }
    }
}
