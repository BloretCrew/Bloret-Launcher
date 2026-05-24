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
    property bool isCompletionPhase: false  // 是否处于文件补全阶段

    title: launchTitle
    modal: true
    closePolicy: Popup.NoAutoClose
    standardButtons: Dialog.Close
    width: 520

    signal skipCompletionClicked()
    signal cancelLaunchClicked()

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

        // 文件补全阶段显示的按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: isCompletionPhase

            Button {
                text: (Backend ? Backend.tr("跳过补全") : "跳过补全")
                icon.name: "ic_fluent_skip_forward_tab_20_regular"
                onClicked: {
                    skipCompletionClicked()
                }
            }

            Button {
                text: (Backend ? Backend.tr("取消启动") : "取消启动")
                icon.name: "ic_fluent_dismiss_20_regular"
                onClicked: {
                    cancelLaunchClicked()
                }
            }

            Item { Layout.fillWidth: true }
        }
    }

    function updateLaunchProgress(progress, status, detail) {
        launchProgress = progress
        launchStatus = status
        launchDetail = detail || ""
        
        // 检测是否处于文件补全阶段
        isCompletionPhase = (status.indexOf("补全文件") >= 0 || status.indexOf("跳过文件补全") >= 0) && progress < 95
    }

    onOpened: {
        if (standardButton(Dialog.Close)) {
            standardButton(Dialog.Close).text = Backend ? Backend.tr("后台运行") : "后台运行"
        }
    }
}