import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 2.15
import Qt5Compat.GraphicalEffects
import "../../themes"
import "../../components"

Popup {
    id: popup
    property int position: Position.None
    property Item anchorItem: parent
    property real posX: {
        if (typeof x === "number" && x !== 0 && position=== Position.None)
            return x
        switch (position) {
            case Position.Top:
            case Position.Bottom:
                return (anchorItem ? (anchorItem.width - popup.width) / 2 : 0)
            case Position.Left:
                return -(popup.width + 5)
            case Position.Right:
                return (anchorItem ? anchorItem.width + 5 : 0)
            default:
                return (anchorItem ? (anchorItem.width - popup.width) / 2 : 0)
        }
    }

    property real posY: {
        if (typeof y === "number" && y !== 0 && position=== Position.None)
            return y
        switch (position) {
            case Position.Top:
                return -(popup.height + 5)
            case Position.Bottom:
                return (anchorItem ? anchorItem.height + 5 : 0)
            case Position.Left:
            case Position.Center:
            case Position.Right:
                return (anchorItem ? (anchorItem.height - popup.height) / 2 : 0)
            default:
                return -(popup.height + 5)
        }
    }

    onVisibleChanged: {  // 自动调整位置
        if (visible) {
            console.log("visible changed")
            Qt.callLater(function() {
                if (
                    (position === Position.None || position === undefined) &&
                    (popup.x === 0 || popup.x === undefined) &&
                    (popup.y === 0 || popup.y === undefined)
                ) {
                    console.log("auto position")
                    popup.autoPosition()
                }
            })
        }
    }

    function autoPosition() {
        if (!anchorItem) return

        // 获取按钮的屏幕坐标
        var btnGlobal = anchorItem.mapToGlobal(0, 0)

        var btnTop = btnGlobal.y
        var btnBottom = btnTop + anchorItem.height

        var screenH = Qt.application.primaryScreen ? Qt.application.primaryScreen.height : 1080
        var popupH = Math.max(popup.implicitHeight, popup.height)
        var spaceAbove = btnTop
        var spaceBelow = screenH - btnBottom

        console.log("autoPosition", {btnTop, btnBottom, screenH, popupH, spaceAbove, spaceBelow})

        popup.position = (spaceBelow >= popupH) ? Position.Bottom : Position.Top
    }


    Overlay.modal: Rectangle {
        color: Theme.currentTheme.colors.backgroundSmokeColor
    }

    background: Rectangle {
        id: background
        anchors.fill: parent
        y: -6

        radius: Theme.currentTheme.appearance.windowRadius
        color: Theme.currentTheme.colors.backgroundAcrylicColor
        border.color: Theme.currentTheme.colors.flyoutBorderColor

        Behavior on color {
            ColorAnimation {
                duration: Utils.appearanceSpeed
                easing.type: Easing.OutQuart
            }
        }

        layer.enabled: true
        layer.effect: Shadow {
            style: "flyout"
            source: background
        }
    }

    // 动画 / Animation //
    enter: Transition {
        ParallelAnimation {
            NumberAnimation {
                target: popup
                property: "opacity"
                from: 0
                to: 1
                duration: Utils.appearanceSpeed
                easing.type: Easing.OutQuint
            }
            NumberAnimation {
                target: popup
                property: "y"
                from: posY + (position !== Position.Center
                    ? (position === Position.Top ? 15 : position === Position.Bottom ? -15 : 0) : 0)
                to: posY
                duration: Utils.animationSpeedMiddle * 1.25
                easing.type: Easing.OutQuint
            }
            NumberAnimation {
                target: popup
                property: "x"
                from: posX + (position !== Position.Center
                    ? (position === Position.Left ? 15 : position === Position.Right ? -15 : 0) : 0)
                to: posX
                duration: Utils.animationSpeedMiddle * 1.25
                easing.type: Easing.OutQuint
            }
        }
    }
    exit: Transition {
        ParallelAnimation {
            NumberAnimation {
                target: popup
                property: "opacity"
                from: 1
                to: 0
                duration: Utils.animationSpeed
                easing.type: Easing.OutQuint
            }
        }
    }
}
