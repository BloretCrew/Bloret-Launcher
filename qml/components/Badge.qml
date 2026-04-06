import QtQuick 2.15
import QtQuick.Controls 2.15
import RinUI

Rectangle {
    id: badge
    radius: 10
    implicitWidth: textItem.implicitWidth + 16
    implicitHeight: 20

    property string text: ""
    // colorType: "Info" | "Success" | "Warning" | "Error"
    property string colorType: "Info"

    color: {
        switch (badge.colorType) {
            case "Success": return "#10b981"  // Green
            case "Warning": return "#f59e0b"  // Yellow
            case "Error": return "#ef4444"    // Red
            case "Info": default: return "#3b82f6"  // Blue
        }
    }

    Text {
        id: textItem
        text: badge.text
        anchors.centerIn: parent
        font.pixelSize: 11
        font.weight: Font.Medium
        color: "#ffffff"
    }
}
