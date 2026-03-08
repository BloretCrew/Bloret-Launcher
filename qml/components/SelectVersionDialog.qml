import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: selectVersionDialog
    title: (Backend ? Backend.tr("选择 Minecraft 版本") : "选择 Minecraft 版本")
    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    
    signal versionSelected(string version)
    
    property var categories: ["百络谷支持版本", "正式版本", "快照版本", "远古版本"]
    property var currentVersions: []
    property string selectedVersion: ""
    property bool isLoading: false
    
    width: 500
    height: 320
    
    Component.onCompleted: {
        console.log("[SelectVersionDialog] Component.onCompleted")
        if (Backend) {
            updateVersionList(0)
        }
    }
    
    onAboutToShow: {
        console.log("[SelectVersionDialog] Dialog about to show")
        if (!currentVersions || currentVersions.length === 0) {
            console.log("[SelectVersionDialog] Versions not loaded, loading now...")
            updateVersionList(categoryCombo.currentIndex)
        }
    }
    
    function updateVersionList(categoryIndex) {
        if (!Backend) {
            console.error("[SelectVersionDialog] Backend not available")
            return
        }
        
        let category = categories[categoryIndex]
        console.log(`[SelectVersionDialog] updateVersionList: category=${category}`)
        
        if (category === "百络谷支持版本") {
            console.log("[SelectVersionDialog] Loading Bloret versions synchronously")
            currentVersions = Backend.getVersionsByCategory(category)
            console.log(`[SelectVersionDialog] Got ${currentVersions.length} Bloret versions`)
            versionCombo.model = currentVersions
            if (currentVersions.length > 0) {
                versionCombo.currentIndex = 0
                selectedVersion = currentVersions[0]
            }
            isLoading = false
            return
        }
        
        console.log(`[SelectVersionDialog] Loading ${category} asynchronously`)
        isLoading = true
        loadingTimer.start()
    }
    
    Timer {
        id: loadingTimer
        interval: 100
        running: false
        onTriggered: {
            console.log("[SelectVersionDialog] Timer triggered")
            let category = selectVersionDialog.categories[categoryCombo.currentIndex]
            console.log(`[SelectVersionDialog] Fetching ${category} from backend`)
            currentVersions = Backend.getVersionsByCategory(category)
            console.log(`[SelectVersionDialog] Got ${currentVersions.length} versions`)
            versionCombo.model = currentVersions
            if (currentVersions.length > 0) {
                versionCombo.currentIndex = 0
                selectedVersion = currentVersions[0]
            }
            isLoading = false
        }
    }
    
    contentItem: ColumnLayout {
        spacing: 15
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Label {
                text: (Backend ? Backend.tr("版本类别:") : "版本类别:")
                Layout.alignment: Qt.AlignVCenter
            }
            
            ComboBox {
                id: categoryCombo
                Layout.fillWidth: true
                model: selectVersionDialog.categories
                currentIndex: 0
                enabled: !isLoading
                onCurrentIndexChanged: {
                    console.log(`[SelectVersionDialog] Category changed to index ${currentIndex}`)
                    updateVersionList(currentIndex)
                }
            }
        }
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: isLoading
            
            ProgressBar {
                Layout.fillWidth: true
                indeterminate: true
            }
        }
        
        Label {
            text: (Backend ? Backend.tr("正在加载版本...") : "正在加载版本...")
            visible: isLoading
            Layout.alignment: Qt.AlignHCenter
        }
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: !isLoading
            
            Label {
                text: (Backend ? Backend.tr("选择版本:") : "选择版本:")
                Layout.alignment: Qt.AlignVCenter
            }
            
            ComboBox {
                id: versionCombo
                Layout.fillWidth: true
                model: currentVersions
                enabled: !isLoading
                onCurrentTextChanged: {
                    if (currentText) {
                        selectedVersion = currentText
                        console.log(`[SelectVersionDialog] Version selected: ${currentText}`)
                    }
                }
            }
        }
        
        Item {
            Layout.fillHeight: true
        }
    }
    
    footer: DialogButtonBox {
        Button {
            text: (Backend ? Backend.tr("确定") : "确定")
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            highlighted: true
            enabled: !isLoading && selectedVersion.length > 0
            onClicked: {
                console.log(`[SelectVersionDialog] User clicked OK, emitting versionSelected(${selectedVersion})`)
                selectVersionDialog.versionSelected(selectedVersion)
                selectVersionDialog.accept()
            }
        }
        Button {
            text: (Backend ? Backend.tr("取消") : "取消")
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            enabled: !isLoading
            onClicked: {
                console.log("[SelectVersionDialog] User clicked Cancel")
                selectVersionDialog.reject()
            }
        }
    }
}
