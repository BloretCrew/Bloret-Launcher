import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: downloadDialog
    
    property string downloadTitle: ""
    property string downloadStatus: ""
    property double downloadProgress: 0.0
    property string downloadSpeed: ""
    property string downloadedSize: ""
    property string totalSize: ""
    property bool isPaused: false
    property int maxThreads: 64
    
    title: downloadTitle
    modal: true
    closePolicy: Popup.NoAutoClose
    standardButtons: Dialog.Close
    
    width: 500
    
    signal pauseClicked()
    signal cancelClicked()
    
    ColumnLayout {
        spacing: 16
        Layout.fillWidth: true
        
        Text {
            text: downloadStatus
            typography: Typography.Body
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }
        
        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            from: 0
            to: 100
            value: downloadProgress
        }
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Text {
                text: downloadedSize + " / " + totalSize
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }
            
            Item { Layout.fillWidth: true }
            
            Text {
                text: downloadSpeed
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Text {
                text: Backend ? Backend.tr("最大线程数") : "最大线程数"
                typography: Typography.Caption
            }
            
            Text {
                text: maxThreads.toString()
                typography: Typography.Caption
                font.weight: Font.DemiBold
            }
            
            Item { Layout.fillWidth: true }
            
            Button {
                id: pauseButton
                text: isPaused ? (Backend ? Backend.tr("恢复") : "恢复") : (Backend ? Backend.tr("暂停") : "暂停")
                onClicked: {
                    downloadDialog.pauseClicked()
                }
            }
        }
    }
    
    function updateProgress(progress, status, speed, downloaded, total) {
        downloadProgress = progress
        downloadStatus = status
        downloadSpeed = speed
        downloadedSize = downloaded
        totalSize = total
    }
    
    function setPaused(paused) {
        isPaused = paused
    }
    
    onClosed: {
        cancelClicked()
    }
}
