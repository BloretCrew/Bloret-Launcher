import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: launchProgressDialog

    property string launchTitle: ""
    property string launchStatus: ""
    property string launchDetail: ""
    property double launchProgress: 0.0

    title: launchTitle
    modal: true
    closePolicy: Popup.NoAutoClose
    standardButtons: Dialog.Close
    width: 520

    ColumnLayout {
        spacing: 12
        Layout.fillWidth: true

        Text {
            text: launchStatus
            typography: Typography.Body
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        ProgressBar {
            Layout.fillWidth: true
            from: 0
            to: 100
            value: launchProgress
        }

        Text {
            text: launchDetail
            visible: launchDetail && launchDetail.length > 0
            typography: Typography.Caption
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }
    }

    function updateLaunchProgress(progress, status, detail) {
        launchProgress = progress
        launchStatus = status
        launchDetail = detail || ""
    }

    onOpened: {
        if (standardButton(Dialog.Close)) {
            standardButton(Dialog.Close).text = Backend ? Backend.tr("后台运行") : "后台运行"
        }
    }
}