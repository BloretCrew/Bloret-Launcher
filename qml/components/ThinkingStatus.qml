import QtQuick 2.15
import QtQuick.Layouts 2.15
import RinUI

/**
 * 思考状态行：点阵球 + 「正在思考」+ 可选脉冲点。
 * active 切换时淡入淡出（不 abrupt visible 跳变）。
 */
Item {
    id: root

    property bool active: false
    property int orbSize: 22
    property string orbState: "composing"
    property real orbSpeed: 1.15
    property color orbInk: Theme.currentTheme.colors.textColor
    property color labelColor: Theme.currentTheme.colors.textSecondaryColor
    property int labelPixelSize: 13
    property bool showAvatar: false
    property url avatarSource: ""
    property bool showPulseDots: true
    property int fadeMs: 320

    // 布局占用：淡出后高度收为 0，避免占位
    readonly property real contentHeight: row.implicitHeight
    implicitWidth: row.implicitWidth
    implicitHeight: opacity > 0.01 ? contentHeight : 0
    height: implicitHeight
    width: parent ? parent.width : row.implicitWidth

    opacity: active ? 1 : 0
    visible: opacity > 0.01
    clip: true

    Behavior on opacity {
        NumberAnimation {
            duration: root.fadeMs
            easing.type: Easing.InOutQuad
        }
    }
    Behavior on implicitHeight {
        enabled: root.visible || root.active
        NumberAnimation {
            duration: root.fadeMs
            easing.type: Easing.InOutQuad
        }
    }

    // 轻微上浮：淡入时从略下方进入
    transform: Translate {
        id: slide
        y: root.active ? 0 : 6
        Behavior on y {
            NumberAnimation {
                duration: root.fadeMs
                easing.type: Easing.OutCubic
            }
        }
    }

    RowLayout {
        id: row
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Rectangle {
            visible: root.showAvatar
            width: 22
            height: 22
            radius: 11
            clip: true
            color: "transparent"
            Layout.alignment: Qt.AlignVCenter
            Image {
                anchors.fill: parent
                source: root.avatarSource
                fillMode: Image.PreserveAspectCrop
                mipmap: true
                visible: root.avatarSource.toString().length > 0
            }
        }

        ThinkingOrb {
            size: root.orbSize
            running: root.active && root.visible
            state: root.orbState
            speed: root.orbSpeed
            ink: root.orbInk
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            text: Backend ? Backend.tr("正在思考") : "正在思考"
            font.pixelSize: root.labelPixelSize
            color: root.labelColor
            Layout.alignment: Qt.AlignVCenter
        }

        Row {
            visible: root.showPulseDots
            spacing: 3
            Layout.alignment: Qt.AlignVCenter
            Repeater {
                model: 3
                Rectangle {
                    width: 4
                    height: 4
                    radius: 2
                    color: root.labelColor
                    opacity: 0.35
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        running: root.active && root.visible && root.showPulseDots
                        PauseAnimation { duration: index * 160 }
                        NumberAnimation { to: 1.0; duration: 320; easing.type: Easing.InOutQuad }
                        NumberAnimation { to: 0.35; duration: 320; easing.type: Easing.InOutQuad }
                        PauseAnimation { duration: (2 - index) * 160 }
                    }
                }
            }
        }

        Item { Layout.fillWidth: true }
    }
}
