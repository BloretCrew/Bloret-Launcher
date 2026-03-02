import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: versionDialog
    property string version: ""
    property bool fabric: false
    property string resultName: ""

    signal confirmed(string versionName)
    property var validationResult: ({valid: true, error: "", exists: false})

    title: (fabric ? (Backend ? Backend.tr("安装 Fabric 版本 %1").arg(version) : "安装 Fabric 版本 " + version)
                    : (Backend ? Backend.tr("安装 Minecraft 版本 %1").arg(version) : "安装 Minecraft 版本 " + version))
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: 400

    ColumnLayout {
        spacing: 10
        Layout.margins: 15
        Layout.fillWidth: true
        onChildrenChanged: {
            // update ok button reference once created
            if (versionDialog.button(Dialog.Ok)) {
                updateButtons()
            }
        }

        Label {
            text: Backend ? Backend.tr("版本名:") : "版本名:"
            font.weight: Font.DemiBold
        }
        Label {
            id: tipLabel
            text: Backend ? Backend.tr("版本名将用于创建版本文件夹") : "版本名将用于创建版本文件夹"
            color: Theme.currentTheme.colors.textSecondaryColor
            font.pixelSize: 12
        }



        TextField {
            id: nameField
            text: version
            placeholderText: Backend ? Backend.tr("输入版本名（默认为版本号）") : "输入版本名（默认为版本号）"
            Layout.fillWidth: true
            onTextChanged: {
                validateName()
            }
        }
    }

    function updateButtons() {
        var okBtn = versionDialog.button(Dialog.Ok)
        if (!okBtn) return
        if (!validationResult.valid) {
            okBtn.enabled = false
            okBtn.text = Backend ? Backend.tr("确认") : "确认"
        } else if (validationResult.exists) {
            okBtn.enabled = true
            okBtn.text = Backend ? Backend.tr("修复已安装版本") : "修复已安装版本"
        } else {
            okBtn.enabled = true
            okBtn.text = Backend ? Backend.tr("确认") : "确认"
        }
    }

    function validateName() {
        var name = nameField.text.trim()
        if (Backend) {
            validationResult = Backend.validateVersionName(version, name)
        }
        if (!validationResult.valid) {
            tipLabel.text = validationResult.error
            tipLabel.color = "#ff0000"
        } else if (validationResult.exists) {
            tipLabel.text = Backend ? Backend.tr("当前版本已存在，继续安装将修复已安装的版本。") : "当前版本已存在，继续安装将修复已安装的版本。"
            tipLabel.color = "#ffa500" // orange
        } else {
            tipLabel.text = Backend ? Backend.tr("版本名将用于创建版本文件夹") : "版本名将用于创建版本文件夹"
            tipLabel.color = Theme.currentTheme.colors.textSecondaryColor
        }
        updateButtons()
    }

    onAccepted: {
        resultName = nameField.text.trim() === "" ? version : nameField.text.trim()
        confirmed(resultName)
    }
}