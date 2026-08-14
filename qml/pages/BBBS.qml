import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: page

    property bool authenticated: false
    property bool loading: false
    property int view: 0
    property var boards: []
    property var sections: []
    property var posts: []
    property var selectedPost: ({})
    property var comments: []
    property string selectedBoardId: ""
    property string selectedSectionId: ""
    property string searchText: ""
    property string errorText: ""
    property bool liked: false

    function tr(text) { return Backend ? Backend.tr(text) : text }
    function resultItems(value) {
        if (Array.isArray(value)) return value
        if (!value) return []
        var nested = value.items || value.posts || value.data || []
        return Array.isArray(nested) ? nested : []
    }
    function postId(post) { return String(post.id || post._id || post.postId || "") }
    function postTitle(post) { return post.title || post.name || tr("无标题") }
    function postContent(post) { return post.content || post.body || post.excerpt || "" }
    function refresh() {
        if (!authenticated || !Backend) return
        loading = true
        Backend.fetchBBBSBoards(true)
        if (selectedBoardId) Backend.fetchBBBSSections(selectedBoardId, true)
        Backend.fetchBBBSPosts(selectedSectionId, selectedBoardId, searchText, 1, 20, true)
    }
    function openPost(post) {
        var id = postId(post)
        if (!id) return
        selectedPost = post
        view = 1
        loading = true
        Backend.fetchBBBSPost(id)
        Backend.fetchBBBSComments(id)
    }

    Component.onCompleted: {
        if (!Backend) return
        authenticated = Backend.isBBBSAuthenticated()
        if (authenticated) {
            loading = true
            Backend.fetchBBBSBoards()
            Backend.fetchBBBSSummary()
            Backend.fetchBBBSPosts("", "", "", 1, 20, false)
        }
    }

    Connections {
        target: Backend
        function onBbbsBoardsReceived(value) {
            boards = resultItems(value)
            loading = false
        }
        function onBbbsSectionsReceived(value) { sections = resultItems(value) }
        function onBbbsPostsReceived(value) {
            posts = resultItems(value)
            loading = false
        }
        function onBbbsPostReceived(value) {
            selectedPost = value || selectedPost
            loading = false
        }
        function onBbbsCommentsReceived(value) { comments = resultItems(value) }
        function onBbbsOperationFinished(operation, ok, result) {
            loading = false
            if (!ok) {
                errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("操作失败")
                errorDialog.open()
                return
            }
            if (operation === "comment" || operation === "like") {
                if (operation === "comment") commentField.text = ""
                openPost(selectedPost)
            } else if (operation === "create_post" || operation === "create_board" || operation === "create_section") {
                view = 0
                refresh()
            } else if (operation === "delete_post") {
                view = 0
                refresh()
            }
        }
        function onBbbsErrorOccurred(message) {
            loading = false
            errorText = message
            errorDialog.open()
        }
    }

    content: ColumnLayout {
        spacing: 12

        PluginPanelHost { area: "bbbs"; Layout.fillWidth: true }

        RowLayout {
            Layout.fillWidth: true
            Label { text: "BBBS"; font.pixelSize: 30; font.weight: Font.Bold; color: Theme.currentTheme.colors.textColor }
            Label { text: tr("百络论坛"); color: Theme.currentTheme.colors.textSecondaryColor; Layout.alignment: Qt.AlignBottom; Layout.bottomMargin: 4 }
            Badge { text: "Bloret BBS"; colorType: "Success" }
            Item { Layout.fillWidth: true }
            Button {
                text: tr("通知")
                visible: authenticated
                onClicked: { Backend.fetchBBBSNotifications(); noticeDialog.open() }
            }
            Button {
                text: tr("任务")
                visible: authenticated
                onClicked: { Backend.fetchBBBSTasks(); taskDialog.open() }
            }
            Button {
                text: tr("刷新")
                visible: authenticated
                icon.name: "ic_fluent_arrow_sync_20_regular"
                onClicked: refresh()
            }
        }

        Frame {
            Layout.fillWidth: true
            visible: !authenticated
            padding: 24
            ColumnLayout {
                anchors.fill: parent
                Label { text: tr("请先登录 Bloret PassPort"); font.pixelSize: 18; font.weight: Font.DemiBold; Layout.alignment: Qt.AlignHCenter }
                Label { text: tr("登录后即可浏览、发布和管理 BBBS 内容"); color: Theme.currentTheme.colors.textSecondaryColor; Layout.alignment: Qt.AlignHCenter }
                Button { text: tr("前往登录"); highlighted: true; Layout.alignment: Qt.AlignHCenter; onClicked: Backend.loginBloretPassPort() }
            }
        }

        RowLayout {
            visible: authenticated
            Layout.fillWidth: true
            spacing: 8
            Button { text: tr("浏览"); highlighted: view === 0; onClicked: view = 0 }
            Button { text: tr("发布主题"); highlighted: view === 2; onClicked: view = 2 }
            Button { text: tr("统计与设置"); onClicked: { Backend.fetchBBBSStatistics(); Backend.fetchBBBSSettings(); settingsDialog.open() } }
            Item { Layout.fillWidth: true }
            TextField { id: searchField; Layout.preferredWidth: 220; placeholderText: tr("搜索帖子"); onAccepted: { searchText = text; refresh() } }
            Button { text: tr("搜索"); onClicked: { searchText = searchField.text; refresh() } }
        }

        ProgressBar { visible: loading && authenticated; indeterminate: true; Layout.fillWidth: true }

        RowLayout {
            visible: authenticated && view === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12
            Frame {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent
                    Label { text: tr("板块"); font.weight: Font.DemiBold }
                    Button {
                        text: tr("全部帖子")
                        Layout.fillWidth: true
                        onClicked: { selectedBoardId = ""; selectedSectionId = ""; refresh() }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: boards
                        delegate: ItemDelegate {
                            width: ListView.view.width
                            text: modelData.name || modelData.title || ""
                            onClicked: {
                                selectedBoardId = String(modelData.id || modelData._id || modelData.boardId || "")
                                selectedSectionId = ""
                                Backend.fetchBBBSSections(selectedBoardId)
                                Backend.fetchBBBSPosts("", selectedBoardId, searchText, 1, 20, false)
                            }
                        }
                    }
                    Button { text: tr("新建板块"); Layout.fillWidth: true; onClicked: boardDialog.open() }
                }
            }
            Frame {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent
                    Label { text: tr("分区"); font.weight: Font.DemiBold }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: sections
                        delegate: ItemDelegate {
                            width: ListView.view.width
                            text: modelData.name || modelData.title || ""
                            onClicked: {
                                selectedSectionId = String(modelData.id || modelData._id || modelData.sectionId || "")
                                Backend.fetchBBBSPosts(selectedSectionId, selectedBoardId, searchText, 1, 20, true)
                            }
                        }
                    }
                    Button { text: tr("新建分区"); Layout.fillWidth: true; enabled: !!selectedBoardId; onClicked: sectionDialog.open() }
                }
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                ColumnLayout {
                    width: Math.max(parent.width, 420)
                    spacing: 8
                    Label { visible: posts.length === 0 && !loading; text: tr("暂无帖子"); color: Theme.currentTheme.colors.textSecondaryColor }
                    Repeater {
                        model: posts
                        Frame {
                            Layout.fillWidth: true
                            padding: 14
                            background: Rectangle { color: Theme.currentTheme.colors.cardColor; radius: 8; border.color: Theme.currentTheme.colors.cardBorderColor }
                            ColumnLayout {
                                width: parent.width
                                spacing: 6
                                Label { text: postTitle(modelData); font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                                Label { text: postContent(modelData).substring(0, 220); visible: text.length > 0; Layout.fillWidth: true; maximumLineCount: 3; elide: Text.ElideRight; wrapMode: Text.Wrap; color: Theme.currentTheme.colors.textSecondaryColor }
                                RowLayout {
                                    Label { text: modelData.author || modelData.username || ""; color: Theme.currentTheme.colors.textSecondaryColor }
                                    Label { text: "❤ " + (modelData.likesCount || modelData.likes || 0); color: Theme.currentTheme.colors.textSecondaryColor }
                                    Label { text: "💬 " + (modelData.commentsCount || modelData.comments || 0); color: Theme.currentTheme.colors.textSecondaryColor }
                                    Item { Layout.fillWidth: true }
                                    Button { text: tr("查看"); onClicked: openPost(modelData) }
                                }
                            }
                        }
                    }
                    Item { height: 20 }
                }
            }
        }

        ScrollView {
            visible: authenticated && view === 1
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                width: Math.max(parent.width, 420)
                spacing: 12
                Button { text: tr("返回帖子列表"); onClicked: view = 0 }
                Frame {
                    Layout.fillWidth: true
                    padding: 18
                    ColumnLayout {
                        width: parent.width
                        Label { text: postTitle(selectedPost); font.pixelSize: 24; font.weight: Font.Bold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Label { text: (selectedPost.author || selectedPost.username || "") + "  " + (selectedPost.time || selectedPost.created_at || ""); color: Theme.currentTheme.colors.textSecondaryColor }
                        Label { text: postContent(selectedPost); textFormat: Text.MarkdownText; Layout.fillWidth: true; wrapMode: Text.Wrap; color: Theme.currentTheme.colors.textColor }
                        RowLayout {
                            Button { text: liked ? tr("取消点赞") : tr("点赞"); onClicked: { liked = !liked; Backend.toggleBBBSLike(postId(selectedPost)) } }
                            Button { text: tr("举报"); onClicked: reportDialog.open() }
                            Button { text: tr("删除"); visible: !!selectedPost.canDelete; onClicked: deleteDialog.open() }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
                Label { text: tr("评论"); font.pixelSize: 18; font.weight: Font.DemiBold }
                Repeater {
                    model: comments
                    Frame {
                        Layout.fillWidth: true
                        padding: 10
                        Label { text: (modelData.author || modelData.username || "") + ": " + (modelData.content || modelData.body || ""); wrapMode: Text.Wrap; width: parent.width }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    TextField { id: commentField; Layout.fillWidth: true; placeholderText: tr("写下评论") }
                    Button { text: tr("发送"); enabled: commentField.text.length > 0; onClicked: Backend.createBBBSComment(postId(selectedPost), commentField.text) }
                }
            }
        }

        ScrollView {
            visible: authenticated && view === 2
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                width: Math.max(parent.width, 420)
                spacing: 10
                Label { text: tr("发布新主题"); font.pixelSize: 22; font.weight: Font.Bold }
                ComboBox { id: sectionCombo; Layout.fillWidth: true; model: sections; textRole: "name"; enabled: sections.length > 0 }
                TextField { id: titleField; Layout.fillWidth: true; placeholderText: tr("标题") }
                TextArea { id: contentField; Layout.fillWidth: true; Layout.preferredHeight: 260; placeholderText: tr("内容（支持 Markdown）"); wrapMode: TextArea.Wrap }
                Label { text: tr("发布前请确认内容、分区和标题正确。图片上传将在后续接口确认后启用。"); color: Theme.currentTheme.colors.textSecondaryColor; wrapMode: Text.Wrap; Layout.fillWidth: true }
                RowLayout {
                    Button { text: tr("取消"); onClicked: view = 0 }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: tr("发布")
                        highlighted: true
                        enabled: titleField.text.length > 0 && contentField.text.length > 0 && sectionCombo.currentIndex >= 0
                        onClicked: {
                            var section = sections[sectionCombo.currentIndex]
                            var id = section ? (section.id || section._id || section.sectionId || "") : ""
                            loading = true
                            Backend.createBBBSPost(String(id), titleField.text, contentField.text, "text", "", "")
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: boardDialog
        modal: true
        title: tr("新建板块")
        standardButtons: Dialog.Cancel
        contentItem: ColumnLayout {
            width: 360
            TextField { id: boardName; placeholderText: tr("板块名称") }
            Button { text: tr("创建"); onClicked: { Backend.createBBBSBoard(boardName.text); boardDialog.close() } }
        }
    }
    Dialog {
        id: sectionDialog
        modal: true
        title: tr("新建分区")
        standardButtons: Dialog.Cancel
        contentItem: ColumnLayout {
            width: 360
            TextField { id: sectionName; placeholderText: tr("分区名称") }
            ComboBox { id: sectionType; model: [tr("文字分区"), tr("图片分区"), tr("络聊分区")] }
            Button { text: tr("创建"); onClicked: { Backend.createBBBSSection(selectedBoardId, sectionName.text, ["text", "image", "chat"][sectionType.currentIndex], ""); sectionDialog.close() } }
        }
    }
    Dialog {
        id: errorDialog
        modal: true
        title: tr("BBBS 提示")
        standardButtons: Dialog.Ok
        contentItem: Label { text: errorText; wrapMode: Text.Wrap; padding: 20; width: 360 }
    }
    Dialog {
        id: deleteDialog
        modal: true
        title: tr("确认删除")
        standardButtons: Dialog.Cancel
        contentItem: ColumnLayout {
            width: 360
            Label { text: tr("删除后无法恢复，确定继续吗？"); wrapMode: Text.Wrap }
            Button { text: tr("确认删除"); onClicked: { Backend.deleteBBBSPost(postId(selectedPost)); deleteDialog.close() } }
        }
    }
    Dialog {
        id: reportDialog
        modal: true
        title: tr("举报")
        standardButtons: Dialog.Cancel
        contentItem: ColumnLayout {
            width: 360
            TextField { id: reportReason; placeholderText: tr("举报原因") }
            TextArea { id: reportDetail; placeholderText: tr("详细说明（选填）") }
            Button { text: tr("提交"); onClicked: reportDialog.close() }
        }
    }
    Dialog {
        id: noticeDialog
        modal: true
        title: tr("通知")
        standardButtons: Dialog.Close
        contentItem: Label { text: tr("通知已请求，当前版本将通过后续数据回调展示。"); padding: 20; wrapMode: Text.Wrap; width: 360 }
    }
    Dialog {
        id: taskDialog
        modal: true
        title: tr("定时任务")
        standardButtons: Dialog.Close
        contentItem: Label { text: tr("任务已请求，当前版本将通过后续数据回调展示。"); padding: 20; wrapMode: Text.Wrap; width: 360 }
    }
    Dialog {
        id: settingsDialog
        modal: true
        title: tr("统计与设置")
        standardButtons: Dialog.Close
        contentItem: ColumnLayout {
            width: 420
            Label { text: tr("统计、用户设置和权限数据已请求。敏感信息不会在此页面显示。"); wrapMode: Text.Wrap }
            Button { text: tr("打开 BBBS 网页版"); onClicked: { Qt.openUrlExternally("https://bbs.bloret.net/"); settingsDialog.close() } }
        }
    }
}
