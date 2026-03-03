import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: selectVersionDialog
    title: qsTr("选择 Minecraft 版本")
    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    
    signal versionSelected(string version)
    
    property var categories: ["百络谷支持版本", "正式版本", "快照版本", "远古版本"]
    property var currentVersions: []
    property string selectedVersion: ""
    property bool isLoading: false
    
    width: 450
    height: 350
    
    Component.onCompleted: {
        if (Backend) {
            // 初始加载第一个类别的版本
            updateVersionList(0)
        }
    }
    
    function updateVersionList(categoryIndex) {
        if (!Backend) return
        
        let category = categories[categoryIndex]
        
        // 如果是"百络谷支持版本"，直接加载（无需异步）
        if (category === "百络谷支持版本") {
            currentVersions = Backend.getVersionsByCategory(category)
            versionCombo.model = currentVersions
            if (currentVersions.length > 0) {
                versionCombo.currentIndex = 0
                selectedVersion = currentVersions[0]
            }
            isLoading = false
            return
        }
        
        // 其他类别：显示加载状态
        isLoading = true
        infoBar.open()
        
        // 使用 Timer 延迟执行，避免阻塞 UI
        loadingTimer.start()
    }
    
    Timer {
        id: loadingTimer
        interval: 100
        running: false
        onTriggered: {
            let category = selectVersionDialog.categories[categoryCombo.currentIndex]
            currentVersions = Backend.getVersionsByCategory(category)
            versionCombo.model = currentVersions
            if (currentVersions.length > 0) {
                versionCombo.currentIndex = 0
                selectedVersion = currentVersions[0]
            }
            isLoading = false
            infoBar.close()
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        
        InfoBar {
            id: infoBar
            Layout.fillWidth: true
            title: qsTr("加载中...")
            text: qsTr("正在获取 Minecraft 版本列表...")
            severity: Severity.Info
            closable: false
            visible: isLoading
        }
        
        Label {
            text: qsTr("选择版本类别:")
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }
        
        ComboBox {
            id: categoryCombo
            Layout.fillWidth: true
            model: selectVersionDialog.categories
            currentIndex: 0
            enabled: !isLoading
            onCurrentIndexChanged: {
                updateVersionList(currentIndex)
            }
        }
        
        Label {
            text: qsTr("选择版本:")
            font.weight: Font.DemiBold
            color: Theme.currentTheme.colors.textColor
        }
        
        ComboBox {
            id: versionCombo
            Layout.fillWidth: true
            model: currentVersions
            enabled: !isLoading
            onCurrentTextChanged: {
                selectedVersion = currentText
            }
        }
        
        Item { Layout.fillHeight: true }
    }
    
    footer: DialogButtonBox {
        Button {
            text: qsTr("确定")
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            highlighted: true
            enabled: !isLoading
            onClicked: {
                selectVersionDialog.versionSelected(selectedVersion)
                selectVersionDialog.accept()
            }
        }
        Button {
            text: qsTr("取消")
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            enabled: !isLoading
            onClicked: selectVersionDialog.reject()
        }
    }
}
