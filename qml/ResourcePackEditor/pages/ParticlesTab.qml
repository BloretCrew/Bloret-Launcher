import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: particlesPage

    property var _particles: []
    property string _selectedPath: ""
    property bool _modified: false

    Connections {
        target: RPEditor
        function onPackLoaded(info) {
            refreshParticles()
        }
    }

    function refreshParticles() {
        if (!RPEditor) return
        _particles = RPEditor.getParticles()
        particleList.model = _particles
        countLabel.text = (Backend ? Backend.tr("共 ") : "共 ") + _particles.length + (Backend ? Backend.tr(" 个粒子定义") : " 个粒子定义")

        if (_particles.length > 0) {
            particleList.currentIndex = 0
            selectParticle(0)
        } else {
            _selectedPath = ""
            editorArea.text = ""
            pathField.text = ""
        }
    }

    function selectParticle(index) {
        if (index < 0 || index >= _particles.length) return
        var particle = _particles[index]
        _selectedPath = particle.path
        pathField.text = particle.path

        if (!RPEditor) return
        var content = RPEditor.getFileContent(particle.path)
        editorArea.text = content
        _modified = false
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentHeight: mainColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: mainColumn
            width: parent.width
            spacing: 16

            RowLayout {
                Layout.fillWidth: true

                Label {
                    text: (Backend ? Backend.tr("粒子定义编辑器") : "粒子定义编辑器")
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Item { Layout.fillWidth: true }

                Label {
                    id: countLabel
                    text: (Backend ? Backend.tr("加载中...") : "加载中...")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 12
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                TextField {
                    id: pathField
                    Layout.fillWidth: true
                    readOnly: true
                    placeholderText: (Backend ? Backend.tr("选择粒子文件以编辑...") : "选择粒子文件以编辑...")
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                Button {
                    text: (Backend ? Backend.tr("保存") : "保存")
                    highlighted: true
                    enabled: _selectedPath !== "" && _modified && RPEditor && RPEditor.isPackOpen()
                    onClicked: {
                        if (RPEditor && _selectedPath) {
                            RPEditor.saveFile(_selectedPath, editorArea.text)
                            _modified = false
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 500
                radius: 8
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.controlBorderColor

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.preferredWidth: 220
                        Layout.fillHeight: true
                        color: Theme.currentTheme.colors.cardColor
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1

                        ListView {
                            id: particleList
                            anchors.fill: parent
                            clip: true

                            delegate: Rectangle {
                                width: particleList.width
                                height: 40
                                color: ListView.isCurrentItem ? (Theme.accentColor || "#0078D4") : "transparent"
                                radius: 4

                                ColumnLayout {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 8
                                    anchors.right: parent.right
                                    anchors.rightMargin: 8
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 2

                                    Label {
                                        text: modelData.name
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        color: ListView.isCurrentItem ? "#FFFFFF" : Theme.currentTheme.colors.textColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Label {
                                        text: modelData.namespace
                                        font.pixelSize: 10
                                        color: ListView.isCurrentItem ? "#CCFFFFFF" : Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        particleList.currentIndex = index
                                        selectParticle(index)
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: Theme.currentTheme.colors.controlAltSecondaryColor

                        Flickable {
                            id: editorFlickable
                            anchors.fill: parent
                            anchors.margins: 8
                            clip: true
                            contentHeight: editorArea.height
                            contentWidth: editorArea.width
                            boundsBehavior: Flickable.StopAtBounds

                            TextArea {
                                id: editorArea
                                width: parent.width
                                font.family: "monospace"
                                font.pixelSize: 12
                                color: Theme.currentTheme.colors.textColor
                                background: null
                                wrapMode: Text.NoWrap
                                placeholderText: (Backend ? Backend.tr("选择一个粒子文件以编辑...") : "选择一个粒子文件以编辑...")
                                selectByMouse: true

                                onTextChanged: {
                                    if (_selectedPath !== "") {
                                        _modified = true
                                    }
                                }
                            }

                            ScrollBar.vertical: ScrollBar {
                                policy: editorArea.contentHeight > editorFlickable.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                            }

                            ScrollBar.horizontal: ScrollBar {
                                policy: editorArea.contentWidth > editorFlickable.width ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                            }
                        }
                    }
                }
            }
        }
    }
}
