import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Item {
    id: settingsPage

    property bool _autoApprove: false
    property bool _toolCallsExpanded: false
    property bool _showThinking: false
    property string _projectNotes: ""

    Component.onCompleted: loadSettings()

    function loadSettings() {
        if (Backend) {
            _autoApprove = Backend.getRpeSetting("agent_auto_approve", "false") === "true"
            _toolCallsExpanded = Backend.getRpeSetting("tool_calls_expanded", "false") === "true"
            _showThinking = Backend.getRpeSetting("show_thinking", "false") === "true"
        }
        if (Agent) {
            _projectNotes = Agent.getProjectSetting("notes", "")
        }
    }

    Flickable {
        anchors.fill: parent
        contentHeight: settingsColumn.implicitHeight + 40
        clip: true

        ColumnLayout {
            id: settingsColumn
            anchors.left: parent.left; anchors.right: parent.right
            anchors.top: parent.top; anchors.margins: 20
            spacing: 20

            // ========== 全局设置 ==========
            Label {
                font.pixelSize: 20
                font.weight: Font.DemiBold
                text: (Backend ? Backend.tr("全局设置") : "全局设置")
                color: Theme.currentTheme.colors.textColor
            }

            Frame {
                Layout.fillWidth: true
                padding: 15
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    // Agent 自动批准写入
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                text: (Backend ? Backend.tr("Agent 自动批准写入") : "Agent 自动批准写入")
                                color: Theme.currentTheme.colors.textColor
                            }
                            Label {
                                font.pixelSize: 12
                                text: (Backend ? Backend.tr("开启后，Agent 的写入操作（写入文件、编辑文件等）将自动批准，无需手动确认") : "开启后，Agent 的写入操作（写入文件、编辑文件等）将自动批准，无需手动确认")
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.Wrap
                            }
                        }

                        Switch {
                            checked: _autoApprove
                            onCheckedChanged: {
                                _autoApprove = checked
                                if (Backend) Backend.setRpeSetting("agent_auto_approve", checked ? "true" : "false")
                                if (Agent) Agent.setAutoApproveWrites(checked)
                            }
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                    // 工具调用默认展开
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                text: (Backend ? Backend.tr("工具调用默认展开") : "工具调用默认展开")
                                color: Theme.currentTheme.colors.textColor
                            }
                            Label {
                                font.pixelSize: 12
                                text: (Backend ? Backend.tr("开启后，Agent 的工具调用结果将默认展开显示；关闭则默认折叠") : "开启后，Agent 的工具调用结果将默认展开显示；关闭则默认折叠")
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.Wrap
                            }
                        }

                        Switch {
                            checked: _toolCallsExpanded
                            onCheckedChanged: {
                                _toolCallsExpanded = checked
                                if (Backend) Backend.setRpeSetting("tool_calls_expanded", checked ? "true" : "false")
                            }
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: Theme.currentTheme.colors.controlBorderColor }

                    // 显示思考过程
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                text: (Backend ? Backend.tr("显示思考过程") : "显示思考过程")
                                color: Theme.currentTheme.colors.textColor
                            }
                            Label {
                                font.pixelSize: 12
                                text: (Backend ? Backend.tr("开启后，将显示 Agent 的思考过程（需要模型支持）") : "开启后，将显示 Agent 的思考过程（需要模型支持）")
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.Wrap
                            }
                        }

                        Switch {
                            checked: _showThinking
                            onCheckedChanged: {
                                _showThinking = checked
                                if (Backend) Backend.setRpeSetting("show_thinking", checked ? "true" : "false")
                            }
                        }
                    }
                }
            }

            // ========== 项目设置 ==========
            Label {
                font.pixelSize: 20
                font.weight: Font.DemiBold
                text: (Backend ? Backend.tr("项目设置") : "项目设置")
                Layout.topMargin: 10
                color: Theme.currentTheme.colors.textColor
            }

            Frame {
                Layout.fillWidth: true
                padding: 15
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    // 项目备注
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Label {
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            text: (Backend ? Backend.tr("项目备注") : "项目备注")
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            font.pixelSize: 12
                            text: (Backend ? Backend.tr("记录与此资源包相关的备注信息，存储在 .BLRPE/config.json 中") : "记录与此资源包相关的备注信息，存储在 .BLRPE/config.json 中")
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 100
                            radius: 6
                            color: Theme.currentTheme.colors.controlAltSecondaryColor || "#F5F5F5"
                            border.color: notesTextArea.activeFocus ? (Theme.accentColor || "#0078D4") : Theme.currentTheme.colors.controlBorderColor
                            border.width: 1

                            TextArea {
                                id: notesTextArea
                                anchors.fill: parent; anchors.margins: 6
                                text: _projectNotes
                                wrapMode: TextArea.Wrap
                                font.pixelSize: 13
                                color: Theme.currentTheme.colors.textColor
                                background: Item {}
                                onTextChanged: {
                                    if (Agent) Agent.setProjectSetting("notes", text)
                                }
                            }
                        }
                    }
                }
            }

            // 底部间距
            Item { Layout.preferredHeight: 20 }
        }
    }
}
