import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: updateDialog

    property bool isDownloading: false
    property string currentVersion: ""
    property string latestVersion: ""
    property string updateDescription: ""
    property double progress: 0.0
    property string statusText: ""

    title: Backend ? Backend.tr("发现新版本") : "发现新版本"
    modal: true
    closePolicy: isDownloading ? Popup.NoAutoClose : Popup.CloseOnEscape
    standardButtons: isDownloading ? Dialog.NoButton : Dialog.NoButton
    width: 450

    ColumnLayout {
        spacing: 16
        Layout.fillWidth: true

        // Prompt state
        ColumnLayout {
            visible: !isDownloading
            spacing: 12
            Layout.fillWidth: true

            Text {
                text: (Backend ? Backend.tr("当前版本") : "当前版本") + ": " + currentVersion
                typography: Typography.Body
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }

            Text {
                text: (Backend ? Backend.tr("最新版本") : "最新版本") + ": " + latestVersion
                typography: Typography.Body
                font.weight: Font.DemiBold
                color: Theme.accentColor
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }

            Text {
                visible: updateDescription.length > 0
                text: updateDescription
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 8

                Item { Layout.fillWidth: true }

                Button {
                    text: Backend ? Backend.tr("取消") : "取消"
                    onClicked: updateDialog.close()
                }

                Button {
                    highlighted: true
                    text: Backend ? Backend.tr("立即更新") : "立即更新"
                    onClicked: {
                        if (Backend) Backend.startUpdate()
                    }
                }
            }
        }

        // Downloading state
        ColumnLayout {
            visible: isDownloading
            spacing: 12
            Layout.fillWidth: true

            Text {
                text: statusText
                typography: Typography.Body
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }

            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: 1
                value: progress
            }

            Text {
                text: Math.round(progress * 100) + "%"
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }
    }

    function showUpdate(currentVer, latestVer, updateText) {
        currentVersion = currentVer
        latestVersion = latestVer
        updateDescription = updateText
        isDownloading = false
        progress = 0
        statusText = ""
        open()
    }

    function updateProgress(prog, status) {
        isDownloading = true
        progress = prog
        statusText = status
    }

    function showError(message) {
        isDownloading = false
        statusText = message
    }
}
