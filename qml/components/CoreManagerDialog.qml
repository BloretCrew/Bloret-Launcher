import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: coreManagerDialog
    
    title: (Backend ? Backend.tr("核心管理") : "核心管理") + (versionName ? ": " + versionName : "")
    modal: true
    width: 650
    height: 550
    standardButtons: Dialog.Close
    
    property string versionName: ""
    property var coreData: ({})
    property string iconPath: ""
    property var servers: []
    property var mods: []
    property var resourcePacks: []
    property bool isOpening: false

    ColumnLayout {
        width: parent.width
        height: parent.height
        spacing: 15
        
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
                    onClicked: {
                        stackedWidget.currentIndex = index
                        if (index === 1) loadServers()
                        if (index === 2) loadResourcePacks()
                        if (index === 3) loadMods()
                    }
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
            
            ColumnLayout {
                spacing: 10
                
                RowLayout {
                    spacing: 10
                    Label {
                        text: Backend ? Backend.tr("服务器列表") : "服务器列表"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        icon.name: "ic_fluent_arrow_sync_20_regular"
                        flat: true
                        onClicked: loadServers()
                    }
                    Button {
                        text: Backend ? Backend.tr("添加服务器") : "添加服务器"
                        icon.name: "ic_fluent_add_20_regular"
                        onClicked: addServerDialog.open()
                    }
                }
                
                ScrollView {
                    id: serverScroll
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    ColumnLayout {
                        width: serverScroll.width - 20
                        spacing: 8
                        
                        Repeater {
                            model: servers
                            
                            Rectangle {
                                id: serverCard
                                Layout.fillWidth: true
                                height: contentRow.implicitHeight + 20
                                radius: 8
                                color: serverMouseArea.containsMouse ? Theme.currentTheme.colors.subtleFillColorSecondary : Theme.currentTheme.colors.cardColor
                                border.color: Theme.currentTheme.colors.cardBorderColor
                                
                                property var serverData: modelData
                                property string statusText: Backend ? Backend.tr("正在获取状态...") : "正在获取状态..."
                                property color statusColor: "#0078D4"
                                property string motd: ""
                                property string fetchedIcon: ""
                                
                                Component.onCompleted: {
                                    var xhr = new XMLHttpRequest();
                                    xhr.open("GET", "https://api.mcsrvstat.us/3/" + modelData.ip);
                                    xhr.onreadystatechange = function() {
                                        if (xhr.readyState === XMLHttpRequest.DONE) {
                                            if (xhr.status === 200) {
                                                var res = JSON.parse(xhr.responseText);
                                                if (res.online) {
                                                    var players = res.players ? res.players.online + "/" + res.players.max : "0/0";
                                                    var cleanMotd = res.motd && res.motd.clean ? res.motd.clean.join("\n") : "Online";
                                                    statusText = "🟢 " + players;
                                                    motd = cleanMotd;
                                                    statusColor = "#107C10";
                                                    if (res.icon) fetchedIcon = res.icon;
                                                } else {
                                                    statusText = Backend ? Backend.tr("🔴 无法连接服务器") : "🔴 无法连接服务器";
                                                    statusColor = "#D13438";
                                                }
                                            } else {
                                                statusText = Backend ? Backend.tr("⚠️ 网络错误") : "⚠️ 网络错误";
                                                statusColor = "#D13438";
                                            }
                                        }
                                    }
                                    xhr.send();
                                }
                                
                                RowLayout {
                                    id: contentRow
                                    width: parent.width - 30
                                    anchors.centerIn: parent
                                    spacing: 15
                                    
                                    Image {
                                        property string rawIcon: serverCard.fetchedIcon || modelData.icon
                                        source: (rawIcon && rawIcon.indexOf("data:") === 0) ? rawIcon :
                                                (rawIcon && rawIcon.indexOf("://") === -1 ? "file:///" + rawIcon.replace(/\\/g, "/") :
                                                 rawIcon) || "../../icon/Grass_Block.png"
                                        sourceSize { width: 48; height: 48 }
                                        fillMode: Image.PreserveAspectFit
                                        Layout.alignment: Qt.AlignTop
                                    }
                                    
                                    ColumnLayout {
                                        spacing: 2
                                        Layout.fillWidth: true
                                        Label {
                                            text: modelData.name
                                            font.weight: Font.DemiBold
                                            font.pixelSize: 14
                                            color: Theme.currentTheme.colors.textColor
                                        }
                                        Label {
                                            text: modelData.ip
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            font.pixelSize: 12
                                        }
                                        Label {
                                            text: serverCard.statusText
                                            color: serverCard.statusColor
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                        Label {
                                            visible: serverCard.motd !== ""
                                            text: serverCard.motd
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                    
                                    Item { Layout.fillWidth: true }
                                    
                                    Button {
                                        icon.name: "ic_fluent_delete_20_regular"
                                        flat: true
                                        Layout.alignment: Qt.AlignVCenter
                                        onClicked: {
                                            if (Backend) {
                                                Backend.deleteServer(versionName, modelData.name)
                                                loadServers()
                                            }
                                        }
                                    }
                                }
                                
                                MouseArea {
                                    id: serverMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    acceptedButtons: Qt.NoButton
                                }
                            }
                        }
                        
                        Label {
                            visible: servers.length === 0
                            text: Backend ? Backend.tr("暂无服务器") : "暂无服务器"
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }
            
            ColumnLayout {
                spacing: 10
                
                RowLayout {
                    spacing: 10
                    Label {
                        text: Backend ? Backend.tr("资源包列表") : "资源包列表"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        icon.name: "ic_fluent_arrow_sync_20_regular"
                        flat: true
                        onClicked: loadResourcePacks()
                    }
                    Button {
                        text: Backend ? Backend.tr("打开文件夹") : "打开文件夹"
                        icon.name: "ic_fluent_folder_open_20_regular"
                        onClicked: if (Backend) Backend.openSubFolder(versionName, "resourcepacks")
                    }
                }
                
                ScrollView {
                    id: resourceScroll
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    ColumnLayout {
                        width: resourceScroll.width - 20
                        spacing: 8
                        
                        Repeater {
                            model: resourcePacks
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: rpContentRow.implicitHeight + 20
                                radius: 8
                                color: Theme.currentTheme.colors.cardColor
                                border.color: Theme.currentTheme.colors.cardBorderColor
                                
                                RowLayout {
                                    id: rpContentRow
                                    width: parent.width - 30
                                    Layout.alignment: Qt.AlignTop    // ensure children stay top-aligned when height varies
                                    anchors.top: parent.top
                                    spacing: 15
                                    
                                    Image {
                                        property string rawIcon: modelData.icon
                                        source: (rawIcon && rawIcon.indexOf("data:") === 0) ? rawIcon :
                                                (rawIcon && rawIcon.indexOf("://") === -1 ? "file:///" + rawIcon.replace(/\\/g, "/") :
                                                 rawIcon) || "../../icon/Grass_Block.png"
                                        sourceSize { width: 32; height: 32 }
                                        fillMode: Image.PreserveAspectFit
                                        Layout.alignment: Qt.AlignTop
                                    }
                                    
                                    ColumnLayout {
                                        spacing: 2
                                        Layout.fillWidth: true
                                        Label {
                                            text: modelData.name
                                            font.weight: Font.DemiBold
                                            color: Theme.currentTheme.colors.textColor
                                        }
                                        Label {
                                            text: modelData.description
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                            maximumLineCount: 2
                                            elide: Text.ElideRight
                                        }
                                    }
                                    
                                    Item { Layout.fillWidth: true }
                                    
                                    Button {
                                        icon.name: "ic_fluent_delete_20_regular"
                                        flat: true
                                        Layout.alignment: Qt.AlignVCenter
                                        onClicked: {
                                            if (Backend) {
                                                var deleted = Backend.deleteResourcePack(modelData.path)
                                                if (deleted) loadResourcePacks()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        
                        Label {
                            visible: resourcePacks.length === 0
                            text: Backend ? Backend.tr("暂无资源包") : "暂无资源包"
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }
            
            ColumnLayout {
                spacing: 10
                
                RowLayout {
                    spacing: 10
                    Label {
                        text: Backend ? Backend.tr("Mod 列表") : "Mod 列表"
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        icon.name: "ic_fluent_arrow_sync_20_regular"
                        flat: true
                        onClicked: loadMods()
                    }
                    Button {
                        text: Backend ? Backend.tr("打开文件夹") : "打开文件夹"
                        icon.name: "ic_fluent_folder_open_20_regular"
                        onClicked: if (Backend) Backend.openSubFolder(versionName, "mods")
                    }
                }
                
                ScrollView {
                    id: modScroll
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    ColumnLayout {
                        width: modScroll.width - 20
                        spacing: 8
                        
                        Repeater {
                            model: mods
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: modContentRow.implicitHeight + 20
                                radius: 8
                                color: Theme.currentTheme.colors.cardColor
                                border.color: Theme.currentTheme.colors.cardBorderColor
                                
                                RowLayout {
                                    id: modContentRow
                                    width: parent.width - 30
                                    Layout.alignment: Qt.AlignTop    // align row to top to avoid vertical centering
                                    anchors.top: parent.top
                                    spacing: 15
                                    
                                    Image {
                                        property string rawIcon: modelData.icon
                                        source: (rawIcon && rawIcon.indexOf("data:") === 0) ? rawIcon :
                                                (rawIcon && rawIcon.indexOf("://") === -1 ? "file:///" + rawIcon.replace(/\\/g, "/") :
                                                 rawIcon) || "../../icon/Grass_Block.png"
                                        sourceSize { width: 32; height: 32 }
                                        fillMode: Image.PreserveAspectFit
                                        Layout.alignment: Qt.AlignTop
                                    }
                                    
                                    ColumnLayout {
                                        spacing: 2
                                        Layout.fillWidth: true
                                        RowLayout {
                                            Label {
                                                text: modelData.name
                                                font.weight: Font.DemiBold
                                                color: Theme.currentTheme.colors.textColor
                                            }
                                            Label {
                                                text: modelData.version
                                                color: Theme.currentTheme.colors.textSecondaryColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Label {
                                            text: modelData.description
                                            color: Theme.currentTheme.colors.textSecondaryColor
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                            maximumLineCount: 3
                                            elide: Text.ElideRight
                                        }
                                    }
                                    
                                    Item { Layout.fillWidth: true }
                                    
                                    Switch {
                                        checked: modelData.enabled
                                        Layout.alignment: Qt.AlignVCenter
                                        onCheckedChanged: {
                                            if (Backend && typeof checked !== 'undefined' && checked !== modelData.enabled) {
                                                Backend.toggleMod(modelData.path, checked)
                                            }
                                        }
                                    }
                                    
                                    Button {
                                        icon.name: "ic_fluent_delete_20_regular"
                                        flat: true
                                        Layout.alignment: Qt.AlignVCenter
                                        onClicked: {
                                            if (Backend) {
                                                var deleted = Backend.deleteMod(modelData.path)
                                                if (deleted) loadMods()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        
                        Label {
                            visible: mods.length === 0
                            text: Backend ? Backend.tr("暂无 Mod") : "暂无 Mod"
                            color: Theme.currentTheme.colors.textSecondaryColor
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
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
    }
    
    Dialog {
        id: addServerDialog
        title: Backend ? Backend.tr("添加服务器") : "添加服务器"
        modal: true
        width: 350
        
        ColumnLayout {
            width: parent.width
            spacing: 15
            
            ColumnLayout {
                width: parent.width
                spacing: 10
                
                Label {
                    text: Backend ? Backend.tr("服务器名称") : "服务器名称"
                    color: Theme.currentTheme.colors.textColor
                }
                TextField {
                    id: newServerName
                    Layout.fillWidth: true
                    placeholderText: "My Server"
                }
                
                Label {
                    text: Backend ? Backend.tr("服务器地址") : "服务器地址"
                    color: Theme.currentTheme.colors.textColor
                }
                TextField {
                    id: newServerIp
                    Layout.fillWidth: true
                    placeholderText: "play.example.com:25565"
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: Backend ? Backend.tr("添加") : "添加"
                    highlighted: true
                    onClicked: {
                        if (Backend && newServerName.text && newServerIp.text) {
                            Backend.addServer(versionName, newServerName.text, newServerIp.text)
                            newServerName.text = ""
                            newServerIp.text = ""
                            loadServers()
                            addServerDialog.close()
                        }
                    }
                }
                Button {
                    text: Backend ? Backend.tr("取消") : "取消"
                    onClicked: addServerDialog.close()
                }
            }
        }
    }
    
    function loadServers() {
        if (Backend) {
            servers = Backend.getServers(versionName)
        }
    }
    
    function loadMods() {
        if (Backend) {
            mods = Backend.getMods(versionName)
        }
    }
    
    function loadResourcePacks() {
        if (Backend) {
            resourcePacks = Backend.getResourcePacks(versionName)
        }
    }
    
    function openWithVersion(name) {
        // 防止重复打开
        if (isOpening) {
            return
        }
        
        isOpening = true
        
        versionName = name
        coreData = Backend ? Backend.getCoreData(name) : {}
        nameEdit.text = name
        iconPath = coreData.icon || ""
        coreIcon.source = iconPath || "../../icon/Grass_Block.png"
        iconPathLabel.text = iconPath ? iconPath.substring(iconPath.lastIndexOf("/") + 1) : (Backend ? Backend.tr("使用默认图标") : "使用默认图标")
        realVersionEdit.text = coreData.version || name
        fabricSwitch.checked = coreData.Fabric || false
        
        servers = []
        mods = []
        resourcePacks = []
        
        stackedWidget.currentIndex = 0
        open()
        
        // 重置标志
        isOpening = false
    }
}
