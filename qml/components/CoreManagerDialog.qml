import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: coreManagerDialog
    
    title: Backend ? Backend.tr("核心管理") : "核心管理"
    modal: true
    width: 600
    height: 500
    standardButtons: Dialog.Close
    
    property string versionName: ""
    property var coreData: ({})

    ColumnLayout {
        anchors.fill: parent
        spacing: 15
        
        // 标题
        Label {
            font.pixelSize: 20
            font.weight: Font.Bold
            text: (Backend ? Backend.tr("核心管理") : "核心管理") + ": " + versionName
            color: Theme.currentTheme.colors.textColor
        }
        
        // 标签页
        RowLayout {
            spacing: 10
            Button {
                id: tabBaseInfo
                text: Backend ? Backend.tr("基本信息") : "基本信息"
                checked: true
                onClicked: {
                    tabBaseInfo.checked = true
                    tabServer.checked = false
                    tabAdvanced.checked = false
                    stackedWidget.currentIndex = 0
                }
            }
            Button {
                id: tabServer
                text: Backend ? Backend.tr("服务器") : "服务器"
                onClicked: {
                    tabBaseInfo.checked = false
                    tabServer.checked = true
                    tabAdvanced.checked = false
                    stackedWidget.currentIndex = 1
                }
            }
            Button {
                id: tabAdvanced
                text: Backend ? Backend.tr("高级") : "高级"
                onClicked: {
                    tabBaseInfo.checked = false
                    tabServer.checked = false
                    tabAdvanced.checked = true
                    stackedWidget.currentIndex = 2
                }
            }
        }
        
        // 内容区域
        StackLayout {
            id: stackedWidget
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0
            
            // 基本信息页面
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 15
                    
                    RowLayout {
                        spacing: 15
                        Image {
                            id: coreIcon
                            source: coreData.icon || "../../icon/Grass_Block.png"
                            sourceSize { width: 64; height: 64 }
                        }
                        ColumnLayout {
                            spacing: 5
                            Label {
                                text: Backend ? Backend.tr("核心名称") : "核心名称"
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                            TextField {
                                id: nameEdit
                                text: versionName
                                placeholderText: Backend ? Backend.tr("输入核心名称") : "输入核心名称"
                            }
                        }
                    }
                    
                    Button {
                        text: Backend ? Backend.tr("选择图标") : "选择图标"
                        onClicked: {
                            if (Backend) {
                                var iconPath = Backend.selectCoreIcon(versionName)
                                if (iconPath) {
                                    coreIcon.source = iconPath
                                }
                            }
                        }
                    }
                }
            }
            
            // 服务器页面
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 15
                    
                    Label {
                        text: Backend ? Backend.tr("服务器地址") : "服务器地址"
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                    
                    TextField {
                        id: serverEdit
                        text: coreData.server || ""
                        placeholderText: "play.example.com:25565"
                    }
                    
                    Label {
                        text: Backend ? Backend.tr("拖动选择") : "拖动选择"
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                }
            }
            
            // 高级页面
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 15
                    
                    RowLayout {
                        Label {
                            text: Backend ? Backend.tr("实际版本") : "实际版本"
                            color: Theme.currentTheme.colors.textColor
                        }
                        Item { Layout.fillWidth: true }
                        TextField {
                            id: realVersionEdit
                            text: coreData.version || versionName
                            placeholderText: "1.21.8"
                        }
                    }
                    
                    RowLayout {
                        Label {
                            text: Backend ? Backend.tr("启用 Fabric") : "启用 Fabric"
                            color: Theme.currentTheme.colors.textColor
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            id: fabricSwitch
                            checked: coreData.Fabric || false
                        }
                    }
                    
                    RowLayout {
                        Label {
                            text: Backend ? Backend.tr("JVM 参数") : "JVM 参数"
                            color: Theme.currentTheme.colors.textColor
                        }
                    }
                    
                    TextField {
                        id: jvmArgsEdit
                        text: coreData.jvmArgs || ""
                        placeholderText: "-Xmx4G -XX:+UseG1GC"
                    }
                    
                    Item { height: 20 }
                    
                    Button {
                        text: Backend ? Backend.tr("删除核心") : "删除核心"
                        flat: true
                        highlighted: false
                        onClicked: {
                            if (Backend) {
                                var confirmed = Backend.confirmDeleteCore(versionName)
                                if (confirmed) {
                                    coreManagerDialog.close()
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // 底部按钮
        RowLayout {
            spacing: 10
            Item { Layout.fillWidth: true }
            Button {
                text: Backend ? Backend.tr("保存修改") : "保存修改"
                highlighted: true
                onClicked: {
                    if (Backend) {
                        var data = {
                            "name": nameEdit.text,
                            "icon": coreIcon.source,
                            "server": serverEdit.text,
                            "version": realVersionEdit.text,
                            "Fabric": fabricSwitch.checked,
                            "jvmArgs": jvmArgsEdit.text
                        }
                        Backend.saveCoreData(versionName, data)
                        coreManagerDialog.close()
                    }
                }
            }
            Button {
                text: Backend ? Backend.tr("关闭") : "关闭"
                onClicked: coreManagerDialog.close()
            }
        }
    }
    
    function openWithVersion(name) {
        versionName = name
        coreData = Backend ? Backend.getCoreData(name) : {}
        nameEdit.text = name
        coreIcon.source = coreData.icon || "../../icon/Grass_Block.png"
        serverEdit.text = coreData.server || ""
        realVersionEdit.text = coreData.version || name
        fabricSwitch.checked = coreData.Fabric || false
        jvmArgsEdit.text = coreData.jvmArgs || ""
        
        tabBaseInfo.checked = true
        tabServer.checked = false
        tabAdvanced.checked = false
        stackedWidget.currentIndex = 0
        
        open()
    }
}
