import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: versionDialog
    property string version: ""
    property bool fabric: false
    property string loaderType: fabric ? "fabric" : "vanilla"
    property string resultName: ""

    signal confirmed(string versionName)
    property var validationResult: ({valid: true, error: "", exists: false})

    title: {
        if (loaderType === "fabric")
            return Backend ? Backend.tr("安装 Fabric 版本 %1").arg(version) : ("安装 Fabric 版本 " + version)
        if (loaderType === "forge")
            return Backend ? Backend.tr("安装 Forge 版本 %1").arg(version) : ("安装 Forge 版本 " + version)
        if (loaderType === "neoforge")
            return Backend ? Backend.tr("安装 NeoForge 版本 %1").arg(version) : ("安装 NeoForge 版本 " + version)
        return Backend ? Backend.tr("安装 Minecraft 版本 %1").arg(version) : ("安装 Minecraft 版本 " + version)
    }

    modal: true
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: Math.min(440, Overlay.overlay ? Overlay.overlay.width - 48 : 440)
    // RinUI Dialog: padding 24*2 + 标题 + 表单 + footer 按钮区，220 会裁掉输入框
    implicitHeight: 320
    height: Math.max(300, Math.min(360, (Overlay.overlay ? Overlay.overlay.height : 360) - 80))

    // 用 contentItem 明确布局，避免内容被 footer/padding 挤出可视区
    contentItem: ColumnLayout {
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: Backend ? Backend.tr("版本名:") : "版本名:"
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }

        Label {
            id: tipLabel
            Layout.fillWidth: true
            text: Backend ? Backend.tr("版本名将用于创建版本文件夹") : "版本名将用于创建版本文件夹"
            color: Theme.currentTheme.colors.textSecondaryColor
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        TextField {
            id: nameField
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            text: version
            placeholderText: Backend ? Backend.tr("输入版本名（默认为版本号）") : "输入版本名（默认为版本号）"
            selectByMouse: true
            onTextChanged: validateName()
        }

        Item { Layout.fillHeight: true }
    }

    function updateButtons() {
        var okBtn = versionDialog.standardButton(Dialog.Ok)
        if (!okBtn)
            okBtn = versionDialog.button ? versionDialog.button(Dialog.Ok) : null
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
        } else {
            validationResult = ({valid: true, error: "", exists: false})
        }
        if (!validationResult.valid) {
            tipLabel.text = validationResult.error || (Backend ? Backend.tr("版本名无效") : "版本名无效")
            tipLabel.color = Theme.currentTheme.colors.systemCriticalColor || "#ef4444"
        } else if (validationResult.exists) {
            tipLabel.text = Backend
                ? Backend.tr("当前版本已存在，继续安装将修复已安装的版本。")
                : "当前版本已存在，继续安装将修复已安装的版本。"
            tipLabel.color = Theme.currentTheme.colors.systemCautionColor || "#f59e0b"
        } else {
            tipLabel.text = Backend ? Backend.tr("版本名将用于创建版本文件夹") : "版本名将用于创建版本文件夹"
            tipLabel.color = Theme.currentTheme.colors.textSecondaryColor
        }
        updateButtons()
    }

    onAboutToShow: {
        nameField.text = version
        validateName()
        Qt.callLater(function() {
            nameField.forceActiveFocus()
            nameField.selectAll()
            updateButtons()
        })
    }

    onOpened: {
        updateButtons()
    }

    onAccepted: {
        resultName = nameField.text.trim() === "" ? version : nameField.text.trim()
        confirmed(resultName)
    }
}
