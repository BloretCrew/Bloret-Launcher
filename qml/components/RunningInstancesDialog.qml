import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: runningInstancesDialog

    title: Backend ? Backend.tr("正在运行") : "正在运行"
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    standardButtons: Dialog.Close
    width: 500

    property var instances: []

    function refresh() {
        instances = Backend ? Backend.getRunningInstances() : []
    }

    onOpened: refresh()

    Connections {
        target: Backend
        function onRunningInstancesChanged(list) { instances = list }
    }

    ColumnLayout {
        spacing: 8
        Layout.fillWidth: true

        Text {
            visible: instances.length === 0
            text: Backend ? Backend.tr("当前没有正在运行的实例") : "当前没有正在运行的实例"
            typography: Typography.Body
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.alignment: Qt.AlignHCenter
            topPadding: 8
            bottomPadding: 8
        }

        Repeater {
            model: instances

            delegate: Rectangle {
                Layout.fillWidth: true
                height: rowContent.implicitHeight + 16
                radius: 6
                color: Theme.currentTheme.colors.cardColor
                border.color: Theme.currentTheme.colors.cardBorderColor
                border.width: 1

                RowLayout {
                    id: rowContent
                    anchors {
                        left: parent.left
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        leftMargin: 12
                        rightMargin: 8
                    }
                    spacing: 8

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true

                        Text {
                            text: modelData.name
                            typography: Typography.Body
                            color: Theme.currentTheme.colors.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.type === "minecraft" ? "Minecraft" : (Backend ? Backend.tr("自定义程序") : "自定义程序")
                            typography: Typography.Caption
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }

                    Button {
                        text: modelData.suspended
                            ? (Backend ? Backend.tr("恢复") : "恢复")
                            : (Backend ? Backend.tr("挂起") : "挂起")
                        flat: true
                        onClicked: { if (Backend) Backend.suspendInstance(modelData.id) }
                    }

                    Button {
                        text: Backend ? Backend.tr("结束") : "结束"
                        highlighted: true
                        onClicked: { if (Backend) Backend.terminateInstance(modelData.id) }
                    }
                }
            }
        }
    }
}
