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
    
    property var categories: ["正式版本", "快照版本", "远古版本"]
    property var currentVersions: []
    property string selectedVersion: ""
    property bool isLoading: false
    property string loadError: ""
    
    width: 420
    height: 280
    
    Component.onCompleted: {
        if (Backend) {
            refreshCurrentCategory()
        }
    }

    onAboutToShow: {
        if (!currentVersions || currentVersions.length === 0) {
            refreshCurrentCategory()
        }
    }

    Connections {
        target: Backend
        function onVersionListReady(category, versions) {
            console.log(`[SelectVersionDialog] Version list ready: ${category}, count=${versions ? versions.length : 0}`)
            if (category === categories[categoryCombo.currentIndex]) {
                loadError = ""
                refreshCurrentCategory()
            }
        }
        function onVersionListLoadFailed(message) {
            console.log(`[SelectVersionDialog] Version list load failed: ${message}`)
            isLoading = false
            loadError = message || (Backend ? Backend.tr("版本列表加载失败") : "版本列表加载失败")
        }
    }

    function refreshCurrentCategory() {
        if (!Backend) {
            isLoading = false
            loadError = "Backend unavailable"
            return
        }
        let category = categories[categoryCombo.currentIndex]
        console.log(`[SelectVersionDialog] Refreshing category: ${category}`)
        currentVersions = Backend.getVersionsByCategory(category)
        versionCombo.model = currentVersions
        if (currentVersions.length > 0) {
            versionCombo.currentIndex = 0
            selectedVersion = currentVersions[0]
            isLoading = false
            loadError = ""
        } else {
            selectedVersion = ""
            isLoading = true
        }
    }

    function retryLoad() {
        if (!Backend) return
        console.log("[SelectVersionDialog] Retrying version list load")
        loadError = ""
        isLoading = true
        Backend.retryVersionListLoad()
    }

    function updateVersionList(categoryIndex) {
        categoryCombo.currentIndex = categoryIndex
        refreshCurrentCategory()
    }
    
    contentItem: ColumnLayout {
        spacing: 12
        
        Frame {
            Layout.fillWidth: true
            padding: 12
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 10
                
                Label {
                    text: (Backend ? Backend.tr("版本类别") : "版本类别")
                    font.weight: Font.DemiBold
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textColor
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
        }
        
        Frame {
            Layout.fillWidth: true
            padding: 12
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.cardBorderColor
            }
            visible: !isLoading

            ColumnLayout {
                width: parent.width
                spacing: 10
                
                Label {
                    text: (Backend ? Backend.tr("选择版本") : "选择版本")
                    font.weight: Font.DemiBold
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textColor
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
            font.pixelSize: 13
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.alignment: Qt.AlignHCenter
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: loadError.length > 0
            spacing: 8

            Label {
                Layout.fillWidth: true
                text: loadError
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 13
                color: Theme.currentTheme.colors.errorColor || "#d13438"
            }

            Button {
                Layout.alignment: Qt.AlignHCenter
                text: (Backend ? Backend.tr("重新加载") : "重新加载")
                onClicked: retryLoad()
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
            enabled: true
            onClicked: {
                console.log("[SelectVersionDialog] User clicked Cancel")
                selectVersionDialog.reject()
            }
        }
    }
}
