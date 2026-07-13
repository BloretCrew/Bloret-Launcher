import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: modsPage
    title: (Backend ? Backend.tr("Mods") : "Mods")

    property var modResults: []
    property string blorikoStatus: ""
    property var fabricVersions: []
    property string selectedFabricVersion: ""
    property var blorikoSlugs: []
    property string blorikoThinkingLog: ""
    property string blorikoStreamText: ""

    // 导航 StackView 会保留历史页实例；仅当前活动页应处理 Backend 信号，
    // 否则多次进入 Mods 后会弹出多个相同的建议对话框。
    readonly property bool isActivePage: {
        if (modsPage.StackView.view)
            return modsPage.StackView.status === StackView.Active
        return modsPage.visible
    }

    Component.onCompleted: {
        if (Backend) {
            fabricVersions = Backend.getFabricVersions()
        }
        console.log("[Mods] page created, StackView.status=",
                    modsPage.StackView.view ? modsPage.StackView.status : "n/a")
    }

    function resetBlorikoProgress() {
        blorikoThinkingLog = ""
        blorikoStreamText = ""
        console.log("[Mods] resetBlorikoProgress")
    }

    function appendThinking(msg) {
        if (!msg || msg.length === 0)
            return
        if (blorikoThinkingLog.length > 0)
            blorikoThinkingLog += "\n"
        blorikoThinkingLog += msg
        // 限制长度，避免无限增长
        if (blorikoThinkingLog.length > 12000)
            blorikoThinkingLog = blorikoThinkingLog.substring(blorikoThinkingLog.length - 10000)
    }

    function showBlorikoSuggestion(response, slugs) {
        console.log(
            "[Mods] showBlorikoSuggestion active=", isActivePage,
            " dialogOpen=", blorikoDialog.opened,
            " slugs=", (slugs && slugs.length) || 0
        )
        if (!isActivePage) {
            console.log("[Mods] 忽略建议信号：当前不是活动页")
            return
        }
        blorikoStatus = response || ""
        versionSelectDialog.loading = false
        versionSelectDialog.close()
        blorikoDialog.text = response || ""
        blorikoDialog.slugs = slugs || []
        // 已打开时只更新内容，避免同实例重复 open 叠窗
        if (!blorikoDialog.opened)
            blorikoDialog.open()
    }

    Connections {
        target: Backend
        // 非活动页断开信号，避免历史页实例重复弹窗
        enabled: modsPage.isActivePage

        function onModrinthResultsReceived(results) {
            console.log("Received Modrinth results:", results)
            modResults = results
            searchBusyIndicator.visible = false
        }
        function onBlorikoModSuggestionStatus(msg) {
            console.log("[Mods] status:", (msg || "").substring(0, 120))
            appendThinking(msg)
        }
        function onBlorikoModSuggestionChunk(text) {
            blorikoStreamText = text || ""
        }
        function onBlorikoModSuggestionFailed(msg) {
            console.warn("[Mods] suggestion failed:", msg)
            appendThinking("❌ " + (msg || (Backend ? Backend.tr("失败") : "失败")))
        }
        // 仅处理模组推荐专用信号；勿再监听 blorikoResponseReceived，
        // 以免与其它入口共用 Backend 时误开弹窗。
        function onBlorikoModSuggestionReceived(response, slugs) {
            showBlorikoSuggestion(response, slugs)
        }
        function onDownloadNotify(title, text, success) {
            downloadInfoBar.severity = success ? Severity.Success : Severity.Error
            downloadInfoBar.title = title
            downloadInfoBar.text = text
            downloadInfoBar.visible = true
            downloadInfoBarTimer.start()
        }
    }

    Timer {
        id: downloadInfoBarTimer
        interval: 4000
        onTriggered: downloadInfoBar.visible = false
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + "M"
        if (num >= 1000) return (num / 1000).toFixed(1) + "K"
        return num.toString()
    }

    ColumnLayout {
        Layout.fillWidth: true
        // anchors.fill: parent // Removed to avoid layout conflict inside Flickable
        // anchors.margins: 20
        spacing: 20

        InfoBar {
            id: downloadInfoBar
            Layout.fillWidth: true
            visible: false
            timeout: 4000
        }

        // --- Header ---

        // --- Bloriko AI Mod Suggestion ---
        Frame {
            Layout.fillWidth: true
            padding: 15
            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 8
                border.color: Theme.currentTheme.colors.controlBorderColor
            }

            ColumnLayout {
                width: parent.width
                spacing: 15

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    Image {
                        source: Qt.resolvedUrl("../../icon/Bloriko.jpg")
                        sourceSize { width: 35; height: 35 }
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        Label {
                            font.weight: Font.DemiBold
                            text: (Backend ? Backend.tr("让Blora帮你挑选合适的 Mod") : "让Blora帮你挑选合适的 Mod")
                            color: Theme.currentTheme.colors.textColor
                        }
                        Label {
                            text: (Backend ? Backend.tr("无需一个一个找 Mod，让Blora帮你找齐。") : "无需一个一个找 Mod，让Blora帮你找齐。")
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    TextField {
                        id: askBlorikoInput
                        Layout.fillWidth: true
                        placeholderText: (Backend ? Backend.tr("告诉 Blora 你的需求...") : "告诉 Blora 你的需求...")
                        onAccepted: {
                            if (askBlorikoInput.text.trim() !== "" && Backend) {
                                console.log("[Mods] 回车发送 Blora Mod 建议:", askBlorikoInput.text.substring(0, 80))
                                versionSelectDialog.open()
                            }
                        }
                    }

                    Button {
                        text: (Backend ? Backend.tr("发送") : "发送")
                        highlighted: true
                        onClicked: {
                            if (askBlorikoInput.text.trim() !== "" && Backend) {
                                console.log("[Mods] 发送 Blora Mod 建议:", askBlorikoInput.text.substring(0, 80))
                                // 先打开版本选择对话框
                                versionSelectDialog.open()
                            }
                        }
                    }
                }
            }
        }

        Label {
            text: (Backend ? Backend.tr("Blora依靠 AI。Blora也可能犯错，请核实重要信息。") : "Blora依靠 AI。Blora也可能犯错，请核实重要信息。")
            color: Theme.currentTheme.colors.textTertialyColor
            font.pixelSize: 12
        }

        // --- Modrinth Search Section ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ComboBox {
                id: categoryFilter
                implicitWidth: 120
                model: [
                    Backend ? Backend.tr("全部") : "全部",
                    Backend ? Backend.tr("Mod") : "Mod",
                    Backend ? Backend.tr("资源包") : "资源包",
                    Backend ? Backend.tr("光影包") : "光影包",
                    Backend ? Backend.tr("数据包") : "数据包",
                    Backend ? Backend.tr("模组包") : "模组包"
                ]
                property var categoryValues: [
                    "",
                    "mod",
                    "resourcepack",
                    "shader",
                    "datapack",
                    "modpack"
                ]
            }

            TextField {
                id: modSearchInput
                Layout.fillWidth: true
                placeholderText: (Backend ? Backend.tr("在 Modrinth 上搜索...") : "在 Modrinth 上搜索...")
                onAccepted: {
                    if (Backend) {
                        searchBusyIndicator.visible = true
                        Backend.searchModrinth(modSearchInput.text, categoryFilter.categoryValues[categoryFilter.currentIndex])
                    }
                }
            }
            Button {
                text: (Backend ? Backend.tr("搜索") : "搜索")
                onClicked: {
                    if (Backend) {
                        searchBusyIndicator.visible = true
                        Backend.searchModrinth(modSearchInput.text, categoryFilter.categoryValues[categoryFilter.currentIndex])
                    }
                }
            }
        }

        BusyIndicator {
            id: searchBusyIndicator
            Layout.alignment: Qt.AlignHCenter
            running: visible
            visible: false
        }

        // Mod List
        ListView {
            id: modListView
            Layout.fillWidth: true
            // Layout.fillHeight: true // Removed, let it grow with content
            implicitHeight: contentHeight // Auto height based on content
            interactive: false // Disable internal scrolling, use page scroll
            model: modsPage.modResults
            clip: true
            spacing: 10
            delegate: Frame {
                width: ListView.view.width
                padding: 10
                background: Rectangle {
                    color: Theme.currentTheme.colors.cardColor
                    radius: 8
                    border.color: Theme.currentTheme.colors.controlBorderColor
                }
                RowLayout {
                    width: parent.width
                    spacing: 15
                    
                    // Icon
                    Rectangle {
                        Layout.preferredWidth: 64
                        Layout.preferredHeight: 64
                        Layout.alignment: Qt.AlignTop
                        color: "transparent"
                        
                        Image {
                            anchors.fill: parent
                            source: modelData.icon_url || ""
                            fillMode: Image.PreserveAspectFit
                            visible: modelData.icon_url !== ""
                        }
                        
                        Rectangle {
                            anchors.fill: parent
                            color: Theme.currentTheme.colors.controlFillSecondaryColor
                            radius: 8
                            visible: !modelData.icon_url
                            Label { text: "Icon"; anchors.centerIn: parent; color: Theme.currentTheme.colors.textTertialyColor }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        // Title & Author
                        RowLayout {
                            Label { 
                                font.weight: Font.DemiBold
                                font.pixelSize: 16
                                text: modelData.name
                                color: Theme.currentTheme.colors.textColor 
                            }
                            Label {
                                text: "by " + (modelData.author || "Unknown")
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                                Layout.alignment: Qt.AlignBaseline
                            }
                        }
                        
                        Label { 
                            text: modelData.description
                            color: Theme.currentTheme.colors.textSecondaryColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        
                        // Stats & Categories
                        RowLayout {
                            spacing: 15
                            
                            Label {
                                text: "⬇ " + formatNumber(modelData.downloads || 0)
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                            }
                            
                            Label {
                                text: "♥ " + formatNumber(modelData.follows || 0)
                                color: Theme.currentTheme.colors.textTertialyColor
                                font.pixelSize: 12
                            }
                            
                            Repeater {
                                model: (modelData.categories || []).slice(0, 3)
                                delegate: Rectangle {
                                    color: Theme.currentTheme.colors.controlFillSecondaryColor
                                    radius: 4
                                    width: catLabel.implicitWidth + 10
                                    height: 18
                                    Label {
                                        id: catLabel
                                        text: modelData
                                        anchors.centerIn: parent
                                        font.pixelSize: 10
                                        color: Theme.currentTheme.colors.textSecondaryColor
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                    spacing: 8
                    Button {
                        text: (Backend ? Backend.tr("查看") : "查看")
                        onClicked: { 
                            if (Backend) {
                                var ptype = modelData.project_type || "mod"
                                Backend.openUrl("https://modrinth.com/" + ptype + "/" + modelData.slug)
                            }
                        }
                    }
                    Button {
                        text: (Backend ? Backend.tr("下载") : "下载")
                        highlighted: true
                        onClicked: { 
                            if (modelData.project_type === "mod") {
                                downloadTargetDialog.modId = modelData.id
                                downloadTargetDialog.open()
                            } else {
                                folderDownloadDialog.modId = modelData.id
                                folderDownloadDialog.modName = modelData.name
                                folderDownloadDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }
    }

    Dialog {
        id: blorikoDialog
        title: (Backend ? Backend.tr("Blora 的建议") : "Blora 的建议")
        property string text: ""
        property var slugs: []
        width: Math.min(parent.width * 0.9, 650)
        modal: true

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15

            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 400
                clip: true

                TextArea {
                    text: blorikoDialog.text
                    wrapMode: Text.Wrap
                    readOnly: true
                    color: Theme.currentTheme.colors.textColor
                    selectByMouse: true
                    textFormat: Text.MarkdownText
                    font.pixelSize: 14
                    background: null
                    leftPadding: 0
                    topPadding: 0
                }
            }

            Label {
                text: (Backend ? Backend.tr("💡 提示：复制上方推荐中的模组名称，在搜索框搜索即可一键安装。") : "💡 提示：复制上方推荐中的模组名称，在搜索框搜索即可一键安装。")
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                visible: blorikoDialog.slugs.length === 0
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: (Backend ? Backend.tr("关闭") : "关闭")
                    onClicked: blorikoDialog.close()
                }

                Button {
                    text: blorikoDialog.slugs.length > 0
                        ? (Backend ? Backend.tr("一键安装全部") : "一键安装全部")
                        : (Backend ? Backend.tr("关闭") : "关闭")
                    highlighted: true
                    visible: blorikoDialog.slugs.length > 0
                    onClicked: {
                        if (blorikoDialog.slugs.length > 0 && Backend) {
                            var ver = modsPage.selectedFabricVersion
                            if (!ver || ver === "") {
                                console.warn("[Mods] 一键安装失败：未选择 Fabric 版本")
                                downloadInfoBar.severity = Severity.Error
                                downloadInfoBar.title = Backend.tr("安装失败")
                                downloadInfoBar.text = Backend.tr("未选择目标 Fabric 版本")
                                downloadInfoBar.visible = true
                                downloadInfoBarTimer.start()
                                return
                            }
                            // 先拷贝列表，再关弹窗（避免 close 后属性被清）
                            var slugList = []
                            for (var i = 0; i < blorikoDialog.slugs.length; i++)
                                slugList.push(blorikoDialog.slugs[i])
                            console.log(
                                "[Mods] 一键安装全部: n=",
                                slugList.length,
                                " version=",
                                ver
                            )
                            // 关闭推荐弹窗，改用全局 DownloadDialog 展示安装进度
                            blorikoDialog.close()
                            Backend.installModsBatch(slugList, ver)
                        }
                    }
                }
            }
        }
    }

    // --- Version Selection Dialog ---
    Dialog {
        id: versionSelectDialog
        title: versionSelectDialog.loading
            ? (Backend ? Backend.tr("Blora正在挑选 Mod…") : "Blora正在挑选 Mod…")
            : (Backend ? Backend.tr("选择 Minecraft 版本") : "选择 Minecraft 版本")
        width: versionSelectDialog.loading ? Math.min(modsPage.width * 0.92, 640) : 400
        modal: true
        closePolicy: Popup.NoAutoClose

        property bool loading: false

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 16

            Label {
                text: (Backend ? Backend.tr("请选择要推荐模组的 Minecraft 版本（仅支持 Fabric）：") : "请选择要推荐模组的 Minecraft 版本（仅支持 Fabric）：")
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
                visible: !versionSelectDialog.loading
            }

            ComboBox {
                id: fabricVersionCombo
                Layout.fillWidth: true
                model: modsPage.fabricVersions
                visible: !versionSelectDialog.loading
                
                Component.onCompleted: {
                    if (modsPage.fabricVersions.length > 0) {
                        currentIndex = 0
                    }
                }
            }

            // --- 加载中：思考过程 + 流式正文 ---
            ColumnLayout {
                Layout.fillWidth: true
                visible: versionSelectDialog.loading
                spacing: 12

                ProgressBar {
                    Layout.fillWidth: true
                    indeterminate: true
                }

                Label {
                    text: (Backend ? Backend.tr("思考过程 / 工具调用") : "思考过程 / 工具调用")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 140
                    clip: true
                    TextArea {
                        text: modsPage.blorikoThinkingLog.length > 0
                            ? modsPage.blorikoThinkingLog
                            : (Backend ? Backend.tr("等待Blora开始搜索…") : "等待Blora开始搜索…")
                        readOnly: true
                        wrapMode: Text.Wrap
                        selectByMouse: true
                        color: Theme.currentTheme.colors.textSecondaryColor
                        font.pixelSize: 12
                        background: null
                    }
                }

                Label {
                    text: (Backend ? Backend.tr("推荐正文（流式）") : "推荐正文（流式）")
                    color: Theme.currentTheme.colors.textSecondaryColor
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 180
                    clip: true
                    TextArea {
                        text: modsPage.blorikoStreamText.length > 0
                            ? modsPage.blorikoStreamText
                            : (Backend ? Backend.tr("Blora还在搜索与整理中，正文会显示在这里…") : "Blora还在搜索与整理中，正文会显示在这里…")
                        readOnly: true
                        wrapMode: Text.Wrap
                        selectByMouse: true
                        textFormat: Text.MarkdownText
                        color: Theme.currentTheme.colors.textColor
                        font.pixelSize: 13
                        background: null
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Item { Layout.fillWidth: true }
                
                Button {
                    text: (Backend ? Backend.tr("取消") : "取消")
                    onClicked: {
                        console.log("[Mods] 取消推荐, loading=", versionSelectDialog.loading)
                        if (versionSelectDialog.loading && Backend) {
                            Backend.cancelBlorikoModSuggestion()
                        }
                        versionSelectDialog.loading = false
                        versionSelectDialog.close()
                    }
                }
                
                Button {
                    text: (Backend ? Backend.tr("确定") : "确定")
                    highlighted: true
                    visible: !versionSelectDialog.loading
                    onClicked: {
                        if (fabricVersionCombo.currentIndex >= 0 && fabricVersionCombo.currentText !== "") {
                            modsPage.resetBlorikoProgress()
                            versionSelectDialog.loading = true
                            modsPage.selectedFabricVersion = fabricVersionCombo.currentText
                            if (Backend && askBlorikoInput.text.trim() !== "") {
                                console.log(
                                    "[Mods] 请求 Blora推荐: version=",
                                    modsPage.selectedFabricVersion,
                                    " query=",
                                    askBlorikoInput.text.substring(0, 80)
                                )
                                appendThinking(
                                    (Backend ? Backend.tr("开始请求…") : "开始请求…")
                                    + " " + modsPage.selectedFabricVersion
                                )
                                Backend.askBlorikoForModsWithVersion(
                                    askBlorikoInput.text.trim(),
                                    modsPage.selectedFabricVersion
                                )
                            }
                        }
                    }
                }
            }
        }

        onClosed: {
            if (loading && Backend) {
                // 关闭对话框时若仍在加载，取消后台 Agent
                Backend.cancelBlorikoModSuggestion()
            }
            loading = false
        }
    }

    Dialog {
        id: downloadTargetDialog
        title: (Backend ? Backend.tr("选择安装版本") : "选择安装版本")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 350
        modal: true

        property string modId: ""

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15

            Label {
                text: (Backend ? Backend.tr("请选择要安装此 Mod 的 Fabric 版本:") : "请选择要安装此 Mod 的 Fabric 版本:")
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }
            
            ComboBox {
                id: downloadVersionCombo
                Layout.fillWidth: true
                model: modsPage.fabricVersions
            }
        }
        
        onAccepted: {
            if (Backend && downloadVersionCombo.currentText !== "") {
                Backend.downloadMod(downloadTargetDialog.modId, downloadVersionCombo.currentText)
            }
        }
    }

    Dialog {
        id: folderDownloadDialog
        title: (Backend ? Backend.tr("选择保存位置") : "选择保存位置")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 400
        modal: true

        property string modId: ""
        property string modName: ""
        property string selectedFolder: ""

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12

            Label {
                text: (Backend ? Backend.tr("请选择保存「%1」的文件夹：").arg(folderDownloadDialog.modName) : "请选择保存「" + folderDownloadDialog.modName + "」的文件夹：")
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                TextField {
                    id: folderPathInput
                    Layout.fillWidth: true
                    placeholderText: (Backend ? Backend.tr("文件夹路径") : "文件夹路径")
                    text: folderDownloadDialog.selectedFolder
                    readOnly: true
                }

                Button {
                    text: (Backend ? Backend.tr("浏览...") : "浏览...")
                    onClicked: {
                        if (Backend) {
                            var folder = Backend.selectFolder()
                            if (folder && folder.length > 0) {
                                folderDownloadDialog.selectedFolder = folder
                                folderPathInput.text = folder
                            }
                        }
                    }
                }
            }
        }

        onAccepted: {
            if (Backend && folderDownloadDialog.selectedFolder !== "") {
                Backend.downloadToFile(folderDownloadDialog.modId, "", folderDownloadDialog.selectedFolder)
            }
        }

        onClosed: {
            selectedFolder = ""
        }
    }
}