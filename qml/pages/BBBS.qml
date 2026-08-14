import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: page
    wrapperWidth: 100000
    horizontalPadding: 28

    property bool authenticated: false
    property bool loading: false
    property int view: 0 // 0 browse, 1 post
    property var boards: []
    property var sections: []
    property var posts: []
    property var comments: []
    property var chatMessages: []
    property var selectedPost: ({})
    property var selectedSection: ({})
    property string selectedBoardId: ""
    property string selectedSectionId: ""
    property string searchText: ""
    property string errorText: ""
    property bool chatMode: false
    property bool liked: false
    property bool sidebarCollapsed: false

    function tr(text) { return Backend ? Backend.tr(text) : text }
    function idOf(value, fallback) { return String(value.id || value._id || value[fallback] || value.filename || value.fullName || value.section || "") }
    function items(value) {
        if (typeof value === "string") {
            try { value = JSON.parse(value) } catch (error) { return [] }
        }
        if (Array.isArray(value)) return value
        if (!value) return []
        var result = value.items || value.posts || value.messages || value.data || []
        return Array.isArray(result) ? result : []
    }
    function postId(post) { return idOf(post, "postId") }
    function titleOf(post) {
        if (!post || typeof post !== "object") return tr("无标题")
        return post.title || post.name || post.filename || tr("无标题")
    }
    function normalizePosts(value) {
        var result = items(value)
        var normalized = []
        for (var i = 0; i < result.length; ++i) {
            var post = result[i]
            if (post && typeof post === "object" && (post.title || post.name || post.filename))
                normalized.push(post)
        }
        return normalized
    }
    function bodyOf(post) { return post.content || post.body || post.excerpt || "" }
    function sectionType(section) { return String(section.type || section.kind || section.sectionType || "text").toLowerCase() }
    function isChatSection(section) { return ["chat", "group", "chatroom", "络聊"].indexOf(sectionType(section)) >= 0 }
    function refreshPosts(force) {
        if (!Backend || !authenticated) return
        loading = true
        Backend.fetchBBBSPosts(selectedSectionId, selectedBoardId, searchText, 1, 30, !!force)
    }
    function openSection(section) {
        selectedSection = section || {}
        if (selectedSection.board)
            selectedBoardId = String(selectedSection.board)
        selectedSectionId = String(selectedSection.section || selectedSection.fullName || selectedSection.name || "")
        chatMode = isChatSection(selectedSection)
        view = 0
        if (chatMode) {
            loading = true
            chatMessages = []
            Backend.fetchBBBSChatMessages(selectedSectionId)
        } else {
            refreshPosts(true)
        }
    }
    function openPost(post) {
        if (!postId(post)) return
        selectedPost = post
        view = 1
        loading = true
        Backend.fetchBBBSPost(post.filename || postId(post))
        Backend.fetchBBBSComments(post.filename || postId(post))
    }
    function sendComment() {
        var content = commentInput.text.trim()
        var filename = String(selectedPost.filename || postId(selectedPost) || "")
        if (!content || !filename) return
        Backend.createBBBSComment(filename, content)
        commentInput.text = ""
    }
    function sendChat() {
        var content = chatInput.text.trim()
        if (!content || !selectedSectionId) return
        Backend.sendBBBSChatMessage(selectedSectionId, content)
        chatInput.text = ""
    }
    function reloadWorkspace() {
        if (!Backend || !authenticated) return
        loading = true
        Backend.fetchBBBSBoards(true)
        Backend.fetchBBBSSections(selectedBoardId, true)
        if (chatMode && selectedSectionId)
            Backend.fetchBBBSChatMessages(selectedSectionId)
        else
            refreshPosts(true)
    }

    Component.onCompleted: {
        console.log("[BBBS] page completed, backend=" + (!!Backend))
        authenticated = Backend && Backend.isBBBSAuthenticated()
        console.log("[BBBS] authenticated=" + authenticated)
        if (authenticated) {
            loading = true
            console.log("[BBBS] requesting boards, sections and all posts")
            Backend.fetchBBBSBoards()
            Backend.fetchBBBSSections("")
            Backend.fetchBBBSPosts("", "", "", 1, 30, false)
        }
    }

    Timer {
        interval: 8000
        repeat: true
        running: authenticated && chatMode && view === 0 && selectedSectionId.length > 0
        onTriggered: Backend.fetchBBBSChatMessages(selectedSectionId)
    }

    Connections {
        target: Backend
        function onBbbsBoardsReceived(value) {
            boards = items(value)
            console.log("[BBBS] boards received count=" + boards.length)
            loading = false
        }
        function onBbbsSectionsReceived(value) {
            sections = items(value)
            console.log("[BBBS] sections received count=" + sections.length)
        }
        function onBbbsPostsReceived(value) {
            var nextPosts = normalizePosts(value)
            if (nextPosts.length > 0 || posts.length === 0)
                posts = nextPosts
            console.log("[BBBS] posts received raw=" + items(value).length + " valid=" + nextPosts.length + " displayed=" + posts.length)
            loading = false
        }
        function onBbbsPostReceived(value) {
            var post = value
            if (typeof post === "string") {
                try { post = JSON.parse(post) } catch (error) { post = null }
            }
            if (post && typeof post === "object" && (post.title || post.name || post.filename))
                selectedPost = post
            console.log("[BBBS] post received title=" + titleOf(selectedPost))
            loading = false
        }
        function onBbbsCommentsReceived(value) { comments = items(value) }
        function onBbbsChatMessagesReceived(value) { chatMessages = items(value); loading = false }
        function onBbbsOperationFinished(operation, ok, result) {
            loading = false
            if (!ok) {
                errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("操作失败")
                errorDialog.open()
                return
            }
            if (operation === "comment") {
                var filename = String(selectedPost.filename || postId(selectedPost) || "")
                if (filename) Backend.fetchBBBSComments(filename)
            } else if (operation === "chat_message") {
                Backend.fetchBBBSChatMessages(selectedSectionId)
            }
        }
        function onBbbsErrorOccurred(message) {
            loading = false
            errorText = message
            errorDialog.open()
        }
    }

    content: ColumnLayout {
        spacing: 0

        PluginPanelHost { area: "bbbs"; Layout.fillWidth: true }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            spacing: 10
            Label { text: "BBBS"; font.pixelSize: 30; font.weight: Font.Bold; color: Theme.currentTheme.colors.textColor }
            Label { text: tr("百络论坛"); color: Theme.currentTheme.colors.textSecondaryColor }
            Badge { text: "Bloret BBS"; colorType: "Success" }
            Item { Layout.fillWidth: true }
            Button { text: tr("通知"); visible: authenticated; onClicked: { Backend.fetchBBBSNotifications(); infoDialog.title = tr("通知"); infoDialog.message = tr("通知列表已刷新。"); infoDialog.open() } }
            Button { text: sidebarCollapsed ? tr("显示导航") : tr("隐藏导航"); visible: authenticated; icon.name: sidebarCollapsed ? "ic_fluent_panel_left_20_regular" : "ic_fluent_panel_left_contract_20_regular"; onClicked: sidebarCollapsed = !sidebarCollapsed }
            Button { text: tr("刷新"); visible: authenticated; icon.name: "ic_fluent_arrow_sync_20_regular"; onClicked: reloadWorkspace() }
        }

        Frame {
            Layout.fillWidth: true
            visible: !authenticated
            padding: 24
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                Label { text: tr("请先登录 Bloret PassPort"); font.pixelSize: 18; font.weight: Font.DemiBold; Layout.alignment: Qt.AlignHCenter }
                Label { text: tr("登录后即可浏览 BBBS 内容"); color: Theme.currentTheme.colors.textSecondaryColor; Layout.alignment: Qt.AlignHCenter }
                Button { text: tr("前往登录"); highlighted: true; Layout.alignment: Qt.AlignHCenter; onClicked: Backend.loginBloretPassPort() }
            }
        }

        Item {
            id: workspace
            visible: authenticated
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(620, page.height - 150)
            Layout.minimumHeight: 620

            RowLayout {
                anchors.fill: parent
                spacing: 12

            Frame {
                visible: !sidebarCollapsed
                Layout.preferredWidth: 235
                Layout.minimumWidth: 180
                Layout.fillHeight: true
                padding: 10
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: tr("社区导航"); font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                        ToolButton { text: "‹"; onClicked: sidebarCollapsed = true; ToolTip.visible: hovered; ToolTip.text: tr("收起导航") }
                    }
                    Button {
                        text: tr("全部帖子")
                        Layout.fillWidth: true
                        highlighted: selectedBoardId === "" && selectedSectionId === ""
                        onClicked: { selectedBoardId = ""; selectedSectionId = ""; selectedSection = {}; chatMode = false; refreshPosts(true) }
                    }
                    Label { text: tr("板块"); color: Theme.currentTheme.colors.textSecondaryColor; Layout.leftMargin: 4; Layout.topMargin: 8 }
                    ListView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(150, contentHeight)
                        clip: true
                        model: boards
                        delegate: ItemDelegate {
                            width: ListView.view.width
                            text: modelData.name || modelData.title || ""
                            highlighted: selectedBoardId === String(modelData.name || modelData.alias || "")
                            onClicked: {
                                selectedBoardId = String(modelData.name || modelData.alias || "")
                                selectedSectionId = ""
                                selectedSection = {}
                                chatMode = false
                                Backend.fetchBBBSSections(selectedBoardId, true)
                                refreshPosts(true)
                            }
                        }
                    }
                    Label { text: tr("分区"); color: Theme.currentTheme.colors.textSecondaryColor; Layout.leftMargin: 4; Layout.topMargin: 8 }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: sections
                        delegate: ItemDelegate {
                            width: ListView.view.width
                            text: (isChatSection(modelData) ? "💬  " : "") + (modelData.name || modelData.title || "")
                            highlighted: selectedSectionId === String(modelData.section || modelData.fullName || modelData.name || "")
                            onClicked: openSection(modelData)
                        }
                    }
                }
            }
            ToolButton {
                visible: sidebarCollapsed
                Layout.preferredWidth: 38
                Layout.alignment: Qt.AlignTop
                text: "☰"
                onClicked: sidebarCollapsed = false
                ToolTip.visible: hovered
                ToolTip.text: tr("展开导航")
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 0
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: chatMode ? (selectedSection.name || tr("络聊")) : (selectedSection.name || tr("帖子列表"))
                        font.pixelSize: 22
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    TextField { id: searchInput; visible: !chatMode; Layout.preferredWidth: 200; placeholderText: tr("搜索帖子"); onAccepted: { searchText = text; refreshPosts(true) } }
                    Button { text: tr("搜索"); visible: !chatMode; onClicked: { searchText = searchInput.text; refreshPosts(true) } }
                }

                ProgressBar { visible: loading; indeterminate: true; Layout.fillWidth: true }

                // Regular post list
                ListView {
                    id: postList
                    visible: view === 0 && !chatMode
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    clip: true
                    spacing: 8
                    model: posts
                    header: Label {
                        width: postList.width
                        visible: posts.length === 0 && !loading
                        text: tr("这个位置还没有帖子")
                        color: Theme.currentTheme.colors.textSecondaryColor
                        topPadding: 20
                    }
                    delegate: Frame {
                        width: postList.width
                        implicitHeight: postCardContent.implicitHeight + topPadding + bottomPadding
                        padding: 16
                        background: Rectangle { color: Theme.currentTheme.colors.cardColor; radius: 8; border.color: Theme.currentTheme.colors.cardBorderColor }
                        ColumnLayout {
                            id: postCardContent
                            width: parent.width - parent.leftPadding - parent.rightPadding
                            spacing: 6
                            Label { text: titleOf(modelData); font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                            Label { text: bodyOf(modelData).substring(0, 220); visible: text.length > 0; maximumLineCount: 3; elide: Text.ElideRight; wrapMode: Text.Wrap; Layout.fillWidth: true; color: Theme.currentTheme.colors.textSecondaryColor }
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: modelData.author || modelData.username || tr("匿名"); color: Theme.currentTheme.colors.textSecondaryColor; elide: Text.ElideRight; Layout.maximumWidth: 160 }
                                Label { text: "❤ " + (modelData.likesCount || modelData.likes || 0); color: Theme.currentTheme.colors.textSecondaryColor }
                                Label { text: "💬 " + (modelData.commentsCount || modelData.comments || 0); color: Theme.currentTheme.colors.textSecondaryColor }
                                Item { Layout.fillWidth: true }
                                Button { text: tr("查看详情"); onClicked: openPost(modelData) }
                            }
                        }
                    }
                }

                // Real 络聊 view
                Frame {
                    visible: view === 0 && chatMode
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 0
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 42
                            color: Theme.currentTheme.colors.controlColor
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                Label { text: tr("络聊分区"); font.weight: Font.DemiBold }
                                Item { Layout.fillWidth: true }
                                Label { text: tr("自动刷新"); color: Theme.currentTheme.colors.textSecondaryColor }
                            }
                        }
                        ListView {
                            id: chatList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.margins: 12
                            clip: true
                            spacing: 8
                            model: chatMessages
                            delegate: Frame {
                                width: chatList.width
                                padding: 10
                                background: Rectangle { color: Theme.currentTheme.colors.cardColor; radius: 7 }
                                RowLayout {
                                    width: parent.width
                                    Label { text: modelData.author || modelData.username || modelData.from || "?"; font.weight: Font.DemiBold; Layout.preferredWidth: 110; elide: Text.ElideRight }
                                    Label { text: modelData.content || modelData.message || modelData.msg || (modelData.payload ? modelData.payload.msg : ""); wrapMode: Text.Wrap; Layout.fillWidth: true }
                                    Label { text: modelData.time || modelData.createdAt || ""; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 11 }
                                }
                            }
                            Label { anchors.centerIn: parent; visible: chatMessages.length === 0 && !loading; text: tr("暂无消息，发送第一条吧"); color: Theme.currentTheme.colors.textSecondaryColor }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.currentTheme.colors.cardBorderColor }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.margins: 12
                            TextField {
                                id: chatInput
                                Layout.fillWidth: true
                                placeholderText: tr("说点什么…")
                                onAccepted: sendChat()
                            }
                            Button {
                                text: tr("发送")
                                highlighted: true
                                enabled: chatInput.text.trim().length > 0
                                onClicked: sendChat()
                            }
                        }
                    }
                }

                // Post detail
                Flickable {
                    id: detailScroll
                    visible: view === 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    contentWidth: width
                    contentHeight: detailContentColumn.height
                    flickableDirection: Flickable.VerticalFlick
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                    Column {
                        id: detailContentColumn
                        width: detailScroll.width
                        spacing: 10
                        Button { text: tr("返回列表"); onClicked: view = 0 }
                        Rectangle {
                            id: detailCard
                            width: parent.width
                            implicitHeight: detailCardContent.implicitHeight + 36
                            color: Theme.currentTheme.colors.cardColor
                            radius: 8
                            border.color: Theme.currentTheme.colors.cardBorderColor
                            Column {
                                id: detailCardContent
                                x: 18
                                y: 18
                                width: detailCard.width - 36
                                spacing: 10
                                Label { width: parent.width; text: titleOf(selectedPost); font.pixelSize: 25; font.weight: Font.Bold; wrapMode: Text.Wrap }
                                Label { width: parent.width; text: (selectedPost.author || selectedPost.username || tr("匿名")) + "  " + (selectedPost.time || selectedPost.created_at || ""); color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap }
                                Label { width: parent.width; text: bodyOf(selectedPost); textFormat: Text.MarkdownText; wrapMode: Text.Wrap }
                            }
                        }
                        Label { text: tr("评论"); font.pixelSize: 18; font.weight: Font.DemiBold }
                        Frame {
                            width: parent.width
                            padding: 12
                            ColumnLayout {
                                width: parent.width - parent.leftPadding - parent.rightPadding
                                spacing: 8
                                TextArea {
                                    id: commentInput
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 90
                                    placeholderText: tr("写下你的评论…")
                                    wrapMode: TextEdit.Wrap
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    Item { Layout.fillWidth: true }
                                    Button {
                                        text: tr("发表评论")
                                        highlighted: true
                                        enabled: commentInput.text.trim().length > 0
                                        onClicked: sendComment()
                                    }
                                }
                            }
                        }
                        Repeater {
                            model: comments
                            Frame {
                                width: parent.width
                                implicitHeight: commentText.implicitHeight + topPadding + bottomPadding
                                padding: 12
                                Label { id: commentText; text: (modelData.author || modelData.username || tr("匿名")) + ":  " + (modelData.content || modelData.body || ""); wrapMode: Text.Wrap; width: parent.width - parent.leftPadding - parent.rightPadding }
                            }
                        }
                    }
                }

            }
            }
        }
    }

    Dialog {
        id: infoDialog
        modal: true
        property string message: ""
        title: tr("BBBS")
        standardButtons: Dialog.Close
        contentItem: Label { text: infoDialog.message; padding: 20; wrapMode: Text.Wrap; width: 380 }
    }
    Dialog {
        id: errorDialog
        modal: true
        title: tr("BBBS 提示")
        standardButtons: Dialog.Ok
        contentItem: Label { text: errorText; padding: 20; wrapMode: Text.Wrap; width: 380 }
    }
}
