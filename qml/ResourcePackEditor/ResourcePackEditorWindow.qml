import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1
import RinUI
import "pages"
import "../components"

FluentWindowBase {
    id: editorWindow
    visible: false
    title: (Backend ? Backend.tr("Bloret Launcher 资源包编辑器") : "Bloret Launcher 资源包编辑器")
    width: 1200
    height: 800
    minimumWidth: 900
    minimumHeight: 600

    // 覆盖背景：动态创建的窗口无法应用系统 backdrop 特效，使用不透明背景
    background: Rectangle {
        anchors.fill: parent
        color: Theme.currentTheme.colors.backgroundColor
        border.color: Theme.currentTheme.colors.windowBorderColor
        layer.enabled: true
        border.width: 1
        radius: Theme.currentTheme.appearance.windowRadius
        z: -1
        clip: true

        Behavior on color {
            ColorAnimation { duration: 150 }
        }
    }

    property string currentFilePath: ""
    property var fileTreeModel: []
    property int currentTabIndex: 0
    property string pendingPackPath: ""
    property string pendingZipPath: ""

    ColumnLayout {
        anchors.fill: parent

        PluginPanelHost {
            area: "rpe"
            Layout.fillWidth: true
            z: 5
        }
        spacing: 0

        // ========== Copilot Agent 系统通知 ==========
        InfoBar {
            id: agentInfoBar
            Layout.fillWidth: true
            visible: false
            timeout: 4000
        }

        property var _toolCnMap: ({
            "read_file": (Backend ? Backend.tr("读取文件") : "读取文件"), "write_file": (Backend ? Backend.tr("写入文件") : "写入文件"), "edit_file": (Backend ? Backend.tr("编辑文件") : "编辑文件"),
            "list_files": (Backend ? Backend.tr("列出文件") : "列出文件"), "search_text": (Backend ? Backend.tr("搜索文本") : "搜索文本"), "get_pack_info": (Backend ? Backend.tr("获取资源包信息") : "获取资源包信息"),
            "analyze_pack": (Backend ? Backend.tr("分析资源包") : "分析资源包"), "read_language": (Backend ? Backend.tr("读取语言文件") : "读取语言文件"), "edit_language": (Backend ? Backend.tr("编辑语言文件") : "编辑语言文件"),
            "validate_json": (Backend ? Backend.tr("验证 JSON") : "验证 JSON"), "get_file_tree": (Backend ? Backend.tr("获取文件树") : "获取文件树"), "ask_user": (Backend ? Backend.tr("向用户提问") : "向用户提问"),
            "execute_command": (Backend ? Backend.tr("执行命令") : "执行命令"), "execute_command_background": (Backend ? Backend.tr("后台执行命令") : "后台执行命令"),
            "spawn_agent": (Backend ? Backend.tr("启动子 Agent") : "启动子 Agent"), "get_mc_reference": (Backend ? Backend.tr("查询 MC 参考") : "查询 MC 参考"),
            "validate_mcmeta_advanced": (Backend ? Backend.tr("验证 pack.mcmeta") : "验证 pack.mcmeta"), "create_resource_template": (Backend ? Backend.tr("创建资源模板") : "创建资源模板")
        })

        function _summarizeAgent(content, toolCallsJson) {
            var parts = []
            try {
                var calls = JSON.parse(toolCallsJson || "[]")
                if (calls.length > 0) {
                    var seen = {}, unique = []
                    for (var i = 0; i < calls.length; i++) {
                        var n = calls[i].name || ""
                        if (n && !seen[n]) { seen[n] = true; unique.push(_toolCnMap[n] || n) }
                    }
                    if (unique.length > 0)
                        parts.push((Backend ? Backend.tr("使用了 ") : "使用了 ") + unique.join("、"))
                }
            } catch(e) {}
            if (content) {
                var snippet = content.trim().split("\n")[0].substring(0, 80)
                if (snippet) parts.push(snippet)
            }
            return parts.length > 0 ? parts.join("；") : (Backend ? Backend.tr("已完成对话") : "已完成对话")
        }

        Connections {
            target: Agent; enabled: Agent !== null

            function onMessageAdded(role, content, toolCallsJson) {
                agentInfoBar.severity = Severity.Success
                agentInfoBar.title = Backend ? Backend.tr("Copilot 完成") : "Copilot 完成"
                agentInfoBar.text = _summarizeAgent(content, toolCallsJson)
                agentInfoBar.visible = true
            }

            function onPermissionRequested(toolName, argsJson, description, reasoning) {
                var cn = _toolCnMap[toolName] || toolName
                agentInfoBar.severity = Severity.Warning
                agentInfoBar.title = Backend ? Backend.tr("Copilot 需要授权") : "Copilot 需要授权"
                agentInfoBar.text = (Backend ? Backend.tr("请求") : "请求") + cn + (description ? ": " + description : "")
                agentInfoBar.visible = true
            }

            function onErrorOccurred(msg) {
                agentInfoBar.severity = Severity.Error
                agentInfoBar.title = Backend ? Backend.tr("Copilot 出错") : "Copilot 出错"
                agentInfoBar.text = msg
                agentInfoBar.visible = true
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.topMargin: 4
            spacing: 2

            Repeater {
                model: [(Backend ? Backend.tr("概览") : "概览"), (Backend ? Backend.tr("BLRPE Copilot") : "BLRPE Copilot"), (Backend ? Backend.tr("Git") : "Git"), (Backend ? Backend.tr("pack.mcmeta") : "pack.mcmeta"), "pack.png", (Backend ? Backend.tr("语言") : "语言"), (Backend ? Backend.tr("贴图") : "贴图"), (Backend ? Backend.tr("方块状态") : "方块状态"), (Backend ? Backend.tr("模型") : "模型"), (Backend ? Backend.tr("声音") : "声音"), (Backend ? Backend.tr("字体") : "字体"), (Backend ? Backend.tr("文本") : "文本"), (Backend ? Backend.tr("粒子") : "粒子"), (Backend ? Backend.tr("特殊文件") : "特殊文件"), (Backend ? Backend.tr("OptiFine") : "OptiFine"), (Backend ? Backend.tr("文件") : "文件"), (Backend ? Backend.tr("设置") : "设置")]

                Button {
                    text: modelData
                    flat: true
                    highlighted: currentTabIndex === index
                    onClicked: currentTabIndex = index
                }
            }

            Item { Layout.fillWidth: true }

            Label {
                id: statsLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                verticalAlignment: Text.AlignVCenter
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4

            RowLayout {
                anchors.fill: parent
                spacing: 0

                StackLayout {
                    id: tabContent
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: currentTabIndex

                    OverviewTab {}
                    AgentTab {}
                    GitTab {}
                    McmetaTab {}
                    PackIconTab {}
                    LanguageTab {}
                    TextureTab {}
                    BlockstatesTab {}
                    ModelsTab {}
                    SoundsTab {}
                    FontsTab {}
                    TextsTab {}
                    ParticlesTab {}
                    SpecialFilesTab {}
                    OptifineTab {}
                    FileBrowserTab {}
                    SettingsTab {}
                }

                Rectangle {
                    id: sidebar
                    Layout.preferredWidth: 280
                    Layout.fillHeight: true
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            color: "transparent"

                            Label {
                                anchors.left: parent.left
                                anchors.leftMargin: 12
                                anchors.verticalCenter: parent.verticalCenter
                                text: (Backend ? Backend.tr("文件列表") : "文件列表")
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Theme.currentTheme.colors.controlBorderColor
                        }

                        FileTreeSidebar {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: fileTreeModel
                            onFileSelected: function(fp) { currentFilePath = fp }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 24
            color: "transparent"

            Label {
                id: statusBarText
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 11
                color: Theme.currentTheme.colors.textSecondaryColor
            }
        }

        Connections {
            target: RPEditor
            function onPackLoaded(info) {
                var data = JSON.parse(info.stats)
                fileTreeModel = RPEditor.getFileTree()
                statsLabel.text = (Backend ? Backend.tr("文件: ") : "文件: ") + data.files
                    + " | " + (Backend ? Backend.tr("贴图: ") : "贴图: ") + data.textures
                    + " | " + (Backend ? Backend.tr("语言: ") : "语言: ") + data.languages
                // 同步资源包路径到 AI Agent
                if (Agent) {
                    Agent.setPackPath(info.path)
                    Agent.setRPEditor(RPEditor)
                }
            }

            function onFileTreeChanged(tree) {
                fileTreeModel = tree
            }

            function onStatusMessage(type, msg) {
                statusBarText.text = msg
                statusBarText.color = Theme.currentTheme.colors.textSecondaryColor
            }

            function onErrorOccurred(msg) {
                statusBarText.text = msg
                statusBarText.color = "#F44336"
                errorTimer.start()
            }

            function onPackMissingStructure(path) {
                pendingPackPath = path
                createStructureTimer.start()
            }
        }

        Component.onCompleted: {
            if (RPEditor && !RPEditor.isPackOpen()) {
                welcomeDialog.open()
            }
        }

        // ========== 欢迎对话框：选择打开方式 ==========
        Dialog {
            id: welcomeDialog
            title: (Backend ? Backend.tr("打开资源包") : "打开资源包")
            modal: true
            width: 440
            closePolicy: Popup.CloseOnEscape

            onRejected: {
                editorWindow.close()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 16

                Label {
                    text: (Backend ? Backend.tr("请选择要打开的资源包类型：") : "请选择要打开的资源包类型：")
                    font.pixelSize: 14
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                // 打开压缩包
                Button {
                    Layout.fillWidth: true
                    implicitHeight: 48
                    flat: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        spacing: 12

                        Icon {
                            icon: "ic_fluent_folder_zip_20_regular"
                            size: 24
                            color: Theme.currentTheme.colors.textColor
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                text: (Backend ? Backend.tr("打开压缩包") : "打开压缩包")
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }

                            Label {
                                text: (Backend ? Backend.tr("选择 .zip 格式的资源包压缩文件") : "选择 .zip 格式的资源包压缩文件")
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }

                    onClicked: {
                        welcomeDialog.accept()
                        zipFileDialog.open()
                    }
                }

                // 打开文件夹
                Button {
                    Layout.fillWidth: true
                    implicitHeight: 48
                    flat: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        spacing: 12

                        Icon {
                            icon: "ic_fluent_folder_20_regular"
                            size: 24
                            color: Theme.currentTheme.colors.textColor
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                text: (Backend ? Backend.tr("打开文件夹") : "打开文件夹")
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }

                            Label {
                                text: (Backend ? Backend.tr("选择已解压的资源包文件夹") : "选择已解压的资源包文件夹")
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }

                    onClicked: {
                        welcomeDialog.accept()
                        folderDialog.open()
                    }
                }

                // 打开最近打开的
                Button {
                    Layout.fillWidth: true
                    implicitHeight: 48
                    flat: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        spacing: 12

                        Icon {
                            icon: "ic_fluent_clock_20_regular"
                            size: 24
                            color: Theme.currentTheme.colors.textColor
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                text: (Backend ? Backend.tr("打开最近使用的") : "打开最近使用的")
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                color: Theme.currentTheme.colors.textColor
                            }

                            Label {
                                text: (Backend ? Backend.tr("从最近打开过的资源包中选择") : "从最近打开过的资源包中选择")
                                font.pixelSize: 11
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }
                    }

                    onClicked: {
                        welcomeDialog.accept()
                        recentPacksDialog.loadAndOpen()
                    }
                }

                // 取消按钮
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4

                    Item { Layout.fillWidth: true }

                    Button {
                        text: (Backend ? Backend.tr("取消") : "取消")
                        flat: true
                        onClicked: welcomeDialog.reject()
                    }
                }
            }
        }

        // ========== 压缩包文件选择对话框 ==========
        FileDialog {
            id: zipFileDialog
            title: (Backend ? Backend.tr("选择资源包压缩文件") : "选择资源包压缩文件")
            nameFilters: [Backend ? Backend.tr("ZIP 压缩包 (*.zip)") : "ZIP 压缩包 (*.zip)"]
            onAccepted: {
                if (zipFileDialog.file) {
                    var pathStr = zipFileDialog.file.toString()
                    if (pathStr.startsWith("file://")) {
                        pathStr = pathStr.slice(7)
                    }
                    pathStr = decodeURIComponent(pathStr)
                    if (Qt.platform.os === "windows" && pathStr.length > 1 && pathStr[0] === "/" && pathStr[1] !== "/") {
                        pathStr = pathStr.slice(1)
                    }
                    pendingZipPath = pathStr
                    extractConfirmDialog.open()
                }
            }
            onRejected: {
                // 用户取消选择压缩包，重新显示欢迎对话框
                welcomeDialog.open()
            }
        }

        // ========== 解压确认对话框 ==========
        Dialog {
            id: extractConfirmDialog
            title: (Backend ? Backend.tr("解压压缩包") : "解压压缩包")
            modal: true
            width: 480
            closePolicy: Popup.CloseOnEscape

            property string zipPath: pendingZipPath

            onRejected: {
                editorWindow.close()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                Label {
                    text: (Backend ? Backend.tr("需要解压压缩包") : "需要解压压缩包")
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    text: (Backend ? Backend.tr("资源包编辑器无法直接在压缩包中进行编辑，需要将压缩包解压到同目录下的文件夹中才能正常工作。\n\n即将解压到：\n") : "资源包编辑器无法直接在压缩包中进行编辑，需要将压缩包解压到同目录下的文件夹中才能正常工作。\n\n即将解压到：\n") + extractConfirmDialog.zipPath.replace(/\.zip$/, "") + "/"
                    font.pixelSize: 12
                    lineHeight: 1.5
                    wrapMode: Text.Wrap
                    color: Theme.currentTheme.colors.textSecondaryColor
                    Layout.fillWidth: true
                }

                Label {
                    text: (Backend ? Backend.tr("是否允许解压并打开？") : "是否允许解压并打开？")
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8

                    Item { Layout.fillWidth: true }

                    Button {
                        text: (Backend ? Backend.tr("拒绝并退出") : "拒绝并退出")
                        flat: true
                        onClicked: extractConfirmDialog.reject()
                    }

                    Button {
                        text: (Backend ? Backend.tr("允许并打开") : "允许并打开")
                        onClicked: extractConfirmDialog.accept()
                    }
                }
            }

            onAccepted: {
                var extractPath = RPEditor.extractZipToSameDir(extractConfirmDialog.zipPath)
                if (extractPath && extractPath.length > 0) {
                    RPEditor.openPack(extractPath)
                } else {
                    editorWindow.close()
                }
            }
        }

        // ========== 最近打开的资源包对话框 ==========
        Dialog {
            id: recentPacksDialog
            title: (Backend ? Backend.tr("最近打开的资源包") : "最近打开的资源包")
            modal: true
            width: 520
            closePolicy: Popup.CloseOnEscape

            property var recentList: []

            function loadAndOpen() {
                recentList = RPEditor.getRecentPacks()
                open()
            }

            onRejected: {
                welcomeDialog.open()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                Label {
                    text: recentPacksDialog.recentList.length > 0
                        ? (Backend ? Backend.tr("请选择要打开的资源包：") : "请选择要打开的资源包：")
                        : (Backend ? Backend.tr("暂无最近打开的资源包记录。") : "暂无最近打开的资源包记录。")
                    font.pixelSize: 13
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(recentPacksDialog.recentList.length * 48 + 16, 320)
                    color: Theme.currentTheme.colors.cardColor
                    border.color: Theme.currentTheme.colors.controlBorderColor
                    border.width: 1
                    radius: 4
                    visible: recentPacksDialog.recentList.length > 0

                    ListView {
                        id: recentListView
                        anchors.fill: parent
                        anchors.margins: 8
                        clip: true
                        model: recentPacksDialog.recentList

                        delegate: ItemDelegate {
                            width: recentListView.width
                            height: 44

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 10

                                Icon {
                                    icon: "ic_fluent_folder_20_regular"
                                    size: 20
                                    color: Theme.currentTheme.colors.textColor
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Label {
                                        text: modelData.name
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        color: Theme.currentTheme.colors.textColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Label {
                                        text: modelData.path
                                        font.pixelSize: 10
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                Label {
                                    text: modelData.lastOpen
                                    font.pixelSize: 10
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }

                            onClicked: {
                                recentPacksDialog.accept()
                                RPEditor.openPack(modelData.path)
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4

                    Item { Layout.fillWidth: true }

                    Button {
                        text: (Backend ? Backend.tr("返回") : "返回")
                        flat: true
                        onClicked: recentPacksDialog.reject()
                    }
                }
            }
        }

        // ========== 文件夹选择对话框 ==========
        FolderDialog {
            id: folderDialog
            title: (Backend ? Backend.tr("选择资源包文件夹") : "选择资源包文件夹")
            onAccepted: {
                if (folderDialog.folder) {
                    var pathStr = folderDialog.folder.toString()
                    if (pathStr.startsWith("file://")) {
                        pathStr = pathStr.slice(7)
                    }
                    pathStr = decodeURIComponent(pathStr)
                    // On Windows, file URL produces /C:/path — strip leading slash
                    if (Qt.platform.os === "windows" && pathStr.length > 1 && pathStr[0] === "/" && pathStr[1] !== "/") {
                        pathStr = pathStr.slice(1)
                    }
                    RPEditor.openPack(pathStr)
                }
            }
            onRejected: {
                // 用户取消选择文件夹，重新显示欢迎对话框
                welcomeDialog.open()
            }
        }

        Dialog {
            id: createStructureDialog
            title: (Backend ? Backend.tr("创建资源包") : "创建资源包")
            modal: true
            width: 480
            closePolicy: Popup.CloseOnEscape

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                Label {
                    text: (Backend ? Backend.tr("该目录不是有效的 Minecraft 资源包。") : "该目录不是有效的 Minecraft 资源包。")
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                }

                Label {
                    text: (Backend ? Backend.tr("是否自动创建基础资源包结构？\n\n将生成：\n  • pack.mcmeta（资源包元数据）\n  • assets/minecraft/（标准命名空间）\n  • assets/minecraft/lang/en_us.json（语言文件）\n  • assets/minecraft/textures/（贴图目录）\n  • assets/minecraft/models/（模型目录）") : "是否自动创建基础资源包结构？\n\n将生成：\n  • pack.mcmeta（资源包元数据）\n  • assets/minecraft/（标准命名空间）\n  • assets/minecraft/lang/en_us.json（语言文件）\n  • assets/minecraft/textures/（贴图目录）\n  • assets/minecraft/models/（模型目录）")
                    font.pixelSize: 12
                    lineHeight: 1.5
                    wrapMode: Text.Wrap
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8

                    Item { Layout.fillWidth: true }

                    Button {
                        text: (Backend ? Backend.tr("取消") : "取消")
                        flat: true
                        onClicked: createStructureDialog.reject()
                    }

                    Button {
                        text: (Backend ? Backend.tr("创建") : "创建")
                        onClicked: createStructureDialog.accept()
                    }
                }
            }

            onAccepted: {
                if (pendingPackPath && RPEditor) {
                    RPEditor.createBasicStructure(pendingPackPath)
                }
            }
            onRejected: {
                editorWindow.close()
            }
        }

        Timer {
            id: createStructureTimer
            interval: 0
            repeat: false
            onTriggered: {
                createStructureDialog.open()
            }
        }

        Timer {
            id: errorTimer
            interval: 5000
            onTriggered: {
                statusBarText.color = Theme.currentTheme.colors.textSecondaryColor
            }
        }
    }
}
