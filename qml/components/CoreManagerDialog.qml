import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: coreManagerDialog
    
    title: Backend ? Backend.tr("核心管理") : "核心管理"
    modal: true
    width: 650
    height: 550
    standardButtons: Dialog.Close
    
    property string versionName: ""
    property var coreData: ({})
    property string iconPath: ""

    ColumnLayout {
        anchors.fill: parent
        spacing: 15
        
        Label {
            font.pixelSize: 18
            font.weight: Font.Bold
            text: (Backend ? Backend.tr("核心管理") : "核心管理") + ": " + versionName
            color: Theme.currentTheme.colors.textColor
        }
        
        RowLayout {
            spacing: 5
            
            Repeater {
                model: [
                    { key: "baseInfo", text: Backend ? Backend.tr("基本信息") : "基本信息" },
                    { key: "server", text: Backend ? Backend.tr("服务器") : "服务器" },
                    { key: "resource", text: Backend ? Backend.tr("资源包") : "资源包" },
                    { key: "mod", text: Backend ? Backend.tr("Mod") : "Mod" },
                    { key: "advanced", text: Backend ? Backend.tr("高级") : "高级" }
                ]
                
                Button {
                    text: modelData.text
                    flat: true
                    checked: stackedWidget.currentIndex === index
                    onClicked: stackedWidget.currentIndex = index
                }
            }
        }
        
        StackLayout {
            id: stackedWidget
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0
            
            ScrollView {
                id: baseInfoScroll
                ColumnLayout {
                    width: baseInfoScroll.width - 20
                    spacing: 20
                    
                    ColumnLayout {
                        spacing: 5
                        Layout.fillWidth: true
                        Label {
                            text: Backend ? Backend.tr("核心名称 (文件夹名)") : "核心名称 (文件夹名)"
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        TextField {
                            id: nameEdit
                            Layout.fillWidth: true
                            text: versionName
                            placeholderText: Backend ? Backend.tr("修改此项将重命名版本文件夹") : "修改此项将重命名版本文件夹"
                        }
                    }
                    
                    ColumnLayout {
                        spacing: 10
                        Layout.fillWidth: true
                        Label {
                            text: Backend ? Backend.tr("图标") : "图标"
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        RowLayout {
                            spacing: 15
                            Rectangle {
                                width: 50
                                height: 50
                                color: Theme.currentTheme.colors.subtleFillColorTertiary
                                radius: 4
                                border.color: Theme.currentTheme.colors.cardBorderColor
                                Image {
                                    id: coreIcon
                                    anchors.centerIn: parent
                                    source: iconPath || "../../icon/Grass_Block.png"
                                    sourceSize { width: 48; height: 48 }
                                    fillMode: Image.PreserveAspectFit
                                }
                            }
                            ColumnLayout {
                                spacing: 5
                                Button {
                                    text: Backend ? Backend.tr("选择其他图标") : "选择其他图标"
                                    icon.name: "ic_fluent_edit_20_regular"
                                    onClicked: {
                                        if (Backend) {
                                            var path = Backend.selectCoreIcon(versionName)
                                            if (path) {
                                                iconPath = path
                                                coreIcon.source = path
                                            }
                                        }
                                    }
                                }
                                Label {
                                    id: iconPathLabel
                                    text: iconPath ? iconPath.substring(iconPath.lastIndexOf("/") + 1) : (Backend ? Backend.tr("使用默认图标") : "使用默认图标")
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                    font.pixelSize: 12
                                }
                            }
                        }
                    }
                    
                    ColumnLayout {
                        spacing: 10
                        Layout.fillWidth: true
                        Label {
                            text: Backend ? Backend.tr("快速访问") : "快速访问"
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        GridLayout {
                            columns: 2
                            rowSpacing: 10
                            columnSpacing: 10
                            Layout.fillWidth: true
                            
                            Button {
                                text: Backend ? Backend.tr("版本文件夹") : "版本文件夹"
                                icon.name: "ic_fluent_folder_20_regular"
                                Layout.fillWidth: true
                                onClicked: if (Backend) Backend.openVersionFolder(versionName)
                            }
                            Button {
                                text: Backend ? Backend.tr("Mod 文件夹") : "Mod 文件夹"
                                icon.name: "ic_fluent_folder_zip_20_regular"
                                Layout.fillWidth: true
                                onClicked: if (Backend) Backend.openSubFolder(versionName, "mods")
                            }
                            Button {
                                text: Backend ? Backend.tr("资源包文件夹") : "资源包文件夹"
                                icon.name: "ic_fluent_album_20_regular"
                                Layout.fillWidth: true
                                onClicked: if (Backend) Backend.openSubFolder(versionName, "resourcepacks")
                            }
                            Button {
                                text: Backend ? Backend.tr("存档文件夹") : "存档文件夹"
                                icon.name: "ic_fluent_save_20_regular"
                                Layout.fillWidth: true
                                onClicked: if (Backend) Backend.openSubFolder(versionName, "saves")
                            }
                        }
                    }
                    
                    Item { Layout.fillHeight: true }
                }
            }
            
            ScrollView {
                id: serverScroll
                ColumnLayout {
                    width: serverScroll.width - 20
                    spacing: 15
                    
                    Label {
                        text: Backend ? Backend.tr("服务器地址") : "服务器地址"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    
                    TextField {
                        id: serverEdit
                        Layout.fillWidth: true
                        text: coreData.server || ""
                        placeholderText: "play.example.com:25565"
                    }
                    
                    Label {
                        text: Backend ? Backend.tr("启动时自动连接到此服务器") : "启动时自动连接到此服务器"
                        color: Theme.currentTheme.colors.textSecondaryColor
                        font.pixelSize: 12
                    }
                    
                    Item { Layout.fillHeight: true }
                }
            }
            
            ScrollView {
                id: resourceScroll
                ColumnLayout {
                    width: resourceScroll.width - 20
                    spacing: 15
                    
                    Label {
                        text: Backend ? Backend.tr("资源包管理") : "资源包管理"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    
                    Label {
                        text: Backend ? Backend.tr("点击下方按钮打开资源包文件夹") : "点击下方按钮打开资源包文件夹"
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                    
                    Button {
                        text: Backend ? Backend.tr("打开资源包文件夹") : "打开资源包文件夹"
                        icon.name: "ic_fluent_folder_open_20_regular"
                        onClicked: if (Backend) Backend.openSubFolder(versionName, "resourcepacks")
                    }
                    
                    Item { Layout.fillHeight: true }
                }
            }
            
            ScrollView {
                id: modScroll
                ColumnLayout {
                    width: modScroll.width - 20
                    spacing: 15
                    
                    Label {
                        text: Backend ? Backend.tr("Mod 管理") : "Mod 管理"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    
                    Label {
                        text: Backend ? Backend.tr("点击下方按钮打开 Mod 文件夹") : "点击下方按钮打开 Mod 文件夹"
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                    
                    Button {
                        text: Backend ? Backend.tr("打开 Mod 文件夹") : "打开 Mod 文件夹"
                        icon.name: "ic_fluent_folder_open_20_regular"
                        onClicked: if (Backend) Backend.openSubFolder(versionName, "mods")
                    }
                    
                    Item { Layout.fillHeight: true }
                }
            }
            
            ScrollView {
                id: advancedScroll
                ColumnLayout {
                    width: advancedScroll.width - 20
                    spacing: 20
                    
                    ColumnLayout {
                        spacing: 10
                        Layout.fillWidth: true
                        Label {
                            text: Backend ? Backend.tr("元数据设置") : "元数据设置"
                            font.weight: Font.DemiBold
                            color: Theme.currentTheme.colors.textColor
                        }
                        
                        Label {
                            text: Backend ? Backend.tr("真实游戏版本") : "真实游戏版本"
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                        TextField {
                            id: realVersionEdit
                            Layout.fillWidth: true
                            text: coreData.version || versionName
                            placeholderText: "1.21.8"
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: Backend ? Backend.tr("标记为 Fabric 版本") : "标记为 Fabric 版本"
                                color: Theme.currentTheme.colors.textColor
                            }
                            Item { Layout.fillWidth: true }
                            Switch {
                                id: fabricSwitch
                                checked: coreData.Fabric || false
                            }
                        }
                    }
                    
                    ColumnLayout {
                        spacing: 10
                        Layout.fillWidth: true
                        Label {
                            text: Backend ? Backend.tr("危险区域") : "危险区域"
                            font.weight: Font.DemiBold
                            color: "#cf1010"
                        }
                        Button {
                            text: Backend ? Backend.tr("删除此核心") : "删除此核心"
                            icon.name: "ic_fluent_delete_20_regular"
                            highlighted: true
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
                    
                    Item { Layout.fillHeight: true }
                }
            }
        }
        
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
                            "icon": iconPath,
                            "server": serverEdit.text,
                            "version": realVersionEdit.text,
                            "Fabric": fabricSwitch.checked
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
        iconPath = coreData.icon || ""
        coreIcon.source = iconPath || "../../icon/Grass_Block.png"
        iconPathLabel.text = iconPath ? iconPath.substring(iconPath.lastIndexOf("/") + 1) : (Backend ? Backend.tr("使用默认图标") : "使用默认图标")
        serverEdit.text = coreData.server || ""
        realVersionEdit.text = coreData.version || name
        fabricSwitch.checked = coreData.Fabric || false
        
        stackedWidget.currentIndex = 0
        open()
    }
}
