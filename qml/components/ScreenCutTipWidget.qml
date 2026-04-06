import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Frame {
    id: root

    property string titleText: "Bloret Launcher Screen Cut"
    property string tipText: ""

    hoverable: false
    radius: Theme.currentTheme.appearance.smallRadius
    color: Theme.currentTheme.colors.cardColor
    borderColor: Theme.currentTheme.colors.cardBorderColor

    implicitWidth: Math.max(420, tipColumn.implicitWidth + 72)
    implicitHeight: 66

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 10

        Rectangle {
            width: 28
            height: 28
            radius: 8
            color: Theme.currentTheme.colors.subtleFillColorSecondary
            border.width: Theme.currentTheme.appearance.borderWidth
            border.color: Theme.currentTheme.colors.cardBorderColor

            IconWidget {
                anchors.centerIn: parent
                name: "ic_fluent_crop_20_regular"
                size: 16
                color: Theme.currentTheme.colors.textColor
            }
        }

        ColumnLayout {
            id: tipColumn
            spacing: 2
            Layout.fillWidth: true

            Label {
                text: root.titleText
                font.pixelSize: 14
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
                elide: Label.ElideRight
                Layout.fillWidth: true
            }

            Label {
                id: tipLabel
                text: root.tipText
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                elide: Label.ElideRight
                Layout.fillWidth: true
            }
        }
    }
}