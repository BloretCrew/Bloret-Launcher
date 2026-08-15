import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentPage {
    id: page
    wrapperWidth: 100000
    horizontalPadding: 28

    property bool authenticated: false
    property bool loading: false
    property bool sending: false
    property string errorText: ""
    property string pendingContent: ""
    property var sections: []
    property var rooms: []
    property var users: []
    property var selectedRoom: ({})
    property var selectedSection: ({})
    property var messages: []
    property string selectedRoomId: ""
    property string roomQuery: ""
    property bool sidebarCollapsed: false

    function tr(text) { return Backend ? Backend.tr(text) : text }
    function items(value) {
        if (typeof value === "string") {
            try { value = JSON.parse(value) } catch (error) { return [] }
        }
        if (Array.isArray(value)) return value
        return value && Array.isArray(value.items) ? value.items : []
    }
    function sectionName(section) { return String(section.section || section.fullName || section.name || "") }
    function roomKind(room) { return String(room.kind || "") }
    function roomTitle(room) { return String(room.title || room.name || room.section_name || "络聊") }
    function roomPreview(room) { return String(room.last_message_preview || tr("暂无消息")) }
    function roomBadge(room) {
        var kind = roomKind(room)
        return kind === "global" ? tr("大群") : kind === "dm" ? tr("私聊") : tr("群聊")
    }
    function roomAvatarText(room) {
        var title = roomTitle(room)
        return title.length > 0 ? title.charAt(0).toUpperCase() : "?"
    }
    function senderOf(message) { return String(message.sender || message.author || message.username || message.from || "?") }
    function contentOf(message) { return String(message.content || message.message || message.msg || "") }
    function timeOf(message) {
        var value = message.created_at || message.createdAt || message.time || ""
        if (typeof value === "number") {
            try { return Qt.formatDateTime(new Date(value), "yyyy-MM-dd HH:mm") } catch (error) {}
        }
        return String(value)
    }
    function chatSections(value) {
        var result = []
        var source = items(value)
        for (var i = 0; i < source.length; ++i) {
            var section = source[i]
            if (section && String(section.type || "").toLowerCase() === "chat") result.push(section)
        }
        return result
    }
    function openRoom(room) {
        selectedRoom = room || ({})
        selectedRoomId = String(selectedRoom.id || "")
        selectedSection = ({})
        messages = []
        if (!selectedRoomId) return
        loading = true
        Backend.fetchBBBSRoomMessages(selectedRoomId, "", "")
    }
    function hasActiveConversation() {
        return selectedRoomId.length > 0 || (!!selectedSection.board && sectionName(selectedSection).length > 0)
    }
    function openSection(section) {
        selectedSection = section || ({})
        selectedRoom = ({})
        selectedRoomId = ""
        messages = []
        if (!selectedSection.board || !sectionName(selectedSection)) return
        loading = true
        Backend.fetchBBBSChatMessages(String(selectedSection.board), sectionName(selectedSection))
    }
    function openDm(peer) {
        if (!peer) return
        loading = true
        Backend.createBBBSDirectMessage(String(peer))
    }
    function reloadRooms() {
        if (authenticated) Backend.fetchBBBSChatRooms(roomQuery)
    }
    function sendMessage() {
        var content = messageInput.text.trim()
        if (sending || !content) return
        pendingContent = content
        sending = true
        if (selectedRoomId) Backend.sendBBBSRoomMessage(selectedRoomId, content)
        else if (selectedSection.board && sectionName(selectedSection)) Backend.sendBBBSChatMessage(String(selectedSection.board), sectionName(selectedSection), content)
        else sending = false
    }

    Component.onCompleted: {
        authenticated = !!Backend && !!Backend.isBBBSAuthenticated()
        if (authenticated) {
            loading = true
            Backend.fetchBBBSChatRooms("")
            Backend.fetchBBBSSections("")
        }
    }

    Timer {
        interval: 8000
        repeat: true
        running: authenticated && (!!selectedRoomId || (!!selectedSection.board && sectionName(selectedSection).length > 0))
        onTriggered: {
            if (selectedRoomId) Backend.fetchBBBSRoomMessages(selectedRoomId, "", "")
            else Backend.fetchBBBSChatMessages(String(selectedSection.board), sectionName(selectedSection))
        }
    }

    Connections {
        target: Backend
        function onBbbsSectionsReceived(value) {
            sections = chatSections(value)
            loading = false
        }
        function onBbbsChatRoomsReceived(value) {
            var data = typeof value === "string" ? JSON.parse(value) : value
            rooms = data && Array.isArray(data.rooms) ? data.rooms : []
            users = data && Array.isArray(data.users) ? data.users : []
            loading = false
        }
        function onBbbsChatMessagesReceived(value) {
            var data = typeof value === "string" ? JSON.parse(value) : value
            messages = Array.isArray(data) ? data : (data && Array.isArray(data.messages) ? data.messages : [])
            loading = false
            if (messages.length > 0) chatList.positionViewAtEnd()
        }
        function onBbbsOperationFinished(operation, ok, result) {
            if (operation === "create_dm") {
                loading = false
                if (!ok) {
                    errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("无法创建私聊")
                    errorDialog.open()
                    return
                }
                var data = result && result.data ? result.data : result
                var room = data && data.room ? data.room : data
                if (room && room.id) {
                    rooms.unshift(room)
                    openRoom(room)
                }
                return
            }
            if (operation === "room_message") {
                sending = false
                if (!ok) {
                    errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("发送失败")
                    errorDialog.open()
                    return
                }
                messageInput.text = ""
                loading = true
                Backend.fetchBBBSRoomMessages(selectedRoomId, "", "")
                return
            }
            if (operation !== "chat_message") return
            sending = false
            if (!ok) {
                errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("发送失败")
                errorDialog.open()
                return
            }
            messageInput.text = ""
            loading = true
            Backend.fetchBBBSChatMessages(String(selectedSection.board), sectionName(selectedSection))
        }
    }

    content: ColumnLayout {
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            Label { text: String(tr("络聊")); font.pixelSize: 30; font.weight: Font.Bold; color: Theme.currentTheme.colors.textColor }
            Label { text: String(tr("实时聊天室")); color: Theme.currentTheme.colors.textSecondaryColor }
            Item { Layout.fillWidth: true }
            Button {
                text: sidebarCollapsed ? tr("显示侧边栏") : tr("隐藏侧边栏")
                icon.name: sidebarCollapsed ? "ic_fluent_panel_left_expand_20_regular" : "ic_fluent_panel_left_contract_20_regular"
                onClicked: sidebarCollapsed = !sidebarCollapsed
            }
            Button { text: tr("刷新"); onClicked: { reloadRooms(); Backend.fetchBBBSSections(""); if (selectedRoomId) openRoom(selectedRoom); else if (selectedSection.board) openSection(selectedSection) } }
        }
        Frame {
            Layout.fillWidth: true
            visible: !authenticated
            padding: 24
            Label { anchors.centerIn: parent; text: tr("请先登录 Bloret PassPort") }
        }
        Item {
            visible: authenticated
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(620, page.height - 150)
            RowLayout {
                anchors.fill: parent
                spacing: 12
                Frame {
                    visible: !sidebarCollapsed
                    Layout.preferredWidth: 300
                    Layout.minimumWidth: 260
                    Layout.fillHeight: true
                    padding: 12
                    ColumnLayout {
                        anchors.fill: parent
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: tr("会话"); font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            Label { text: rooms.length + tr(" 个"); color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                        }
                        TextField { Layout.fillWidth: true; placeholderText: tr("搜索用户或会话"); onAccepted: { roomQuery = text.trim(); reloadRooms() } }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: rooms
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: 76
                                radius: 10
                                color: String(modelData.id || "") === selectedRoomId ? Theme.currentTheme.colors.controlAltSecondaryColor : "transparent"
                                border.width: String(modelData.id || "") === selectedRoomId ? 1 : 0
                                border.color: Theme.currentTheme.colors.primaryColor
                                property bool hovered: false
                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onEntered: parent.hovered = true
                                    onExited: parent.hovered = false
                                    onClicked: openRoom(modelData)
                                }
                                Rectangle {
                                    x: 10; y: 10; width: 46; height: 46; radius: 23
                                    color: roomKind(modelData) === "global" ? Theme.currentTheme.colors.primaryColor : Theme.currentTheme.colors.controlColor
                                    Label { anchors.centerIn: parent; text: roomAvatarText(modelData); font.pixelSize: 20; font.weight: Font.DemiBold; color: Theme.currentTheme.colors.textColor }
                                }
                                Column {
                                    x: 68; y: 10; width: parent.width - 78; spacing: 4
                                    Row {
                                        width: parent.width; spacing: 6
                                        Label { text: roomTitle(modelData); font.weight: Font.DemiBold; elide: Text.ElideRight; width: parent.width - 48 }
                                        Label { text: roomBadge(modelData); font.pixelSize: 11; color: Theme.currentTheme.colors.textSecondaryColor }
                                    }
                                    Label { text: roomPreview(modelData); width: parent.width; elide: Text.ElideRight; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                                }
                                Label { visible: modelData.unread_count > 0; anchors.right: parent.right; anchors.top: parent.top; anchors.rightMargin: 8; anchors.topMargin: 8; text: String(modelData.unread_count); color: "white"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; width: 20; height: 20; verticalAlignment: Text.AlignVCenter; background: Rectangle { radius: 10; color: Theme.currentTheme.colors.primaryColor } }
                            }
                        }
                        Label { text: tr("络聊分区"); color: Theme.currentTheme.colors.textSecondaryColor }
                        ListView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(110, contentHeight)
                            clip: true
                            model: sections
                            delegate: ItemDelegate {
                                width: ListView.view.width
                                text: (modelData.board || "") + " / " + (modelData.name || modelData.section || "")
                                highlighted: sectionName(modelData) === sectionName(selectedSection) && modelData.board === selectedSection.board
                                onClicked: openSection(modelData)
                            }
                        }
                        Label { text: tr("用户"); color: Theme.currentTheme.colors.textSecondaryColor; visible: users.length > 0 }
                        ListView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(100, contentHeight)
                            clip: true
                            model: users
                            visible: users.length > 0
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: 44
                                radius: 8
                                color: "transparent"
                                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: openDm(modelData.username || modelData.name) }
                                Rectangle { x: 8; y: 6; width: 32; height: 32; radius: 16; color: Theme.currentTheme.colors.controlColor; Label { anchors.centerIn: parent; text: String(modelData.username || modelData.name || "?").charAt(0).toUpperCase(); font.weight: Font.DemiBold } }
                                Label { anchors.left: parent.left; anchors.leftMargin: 50; anchors.verticalCenter: parent.verticalCenter; text: String(modelData.username || modelData.name || ""); color: Theme.currentTheme.colors.textColor }
                            }
                        }
                    }
                }
                Frame {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 0
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            Layout.leftMargin: 14
                            Layout.rightMargin: 14
                            Label { text: selectedRoomId ? roomTitle(selectedRoom) : (selectedSection.name || selectedSection.section || tr("选择一个聊天室")); font.pixelSize: 18; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            BusyIndicator { visible: loading; running: visible; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.currentTheme.colors.cardBorderColor }
                        ListView {
                            id: chatList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.margins: 12
                            clip: true
                            spacing: 8
                            model: messages
                            delegate: Frame {
                                width: chatList.width
                                padding: 10
                                implicitHeight: messageColumn.height + topPadding + bottomPadding
                                Column {
                                    id: messageColumn
                                    x: leftPadding
                                    y: topPadding
                                    width: Math.max(1, parent.width - leftPadding - rightPadding)
                                    spacing: 5
                                    Label {
                                        width: parent.width
                                        text: senderOf(modelData)
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        id: messageContent
                                        width: parent.width
                                        text: contentOf(modelData)
                                        color: Theme.currentTheme.colors.textColor
                                        wrapMode: Text.WrapAnywhere
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignTop
                                    }
                                }
                            }
                            Label { anchors.centerIn: parent; visible: !loading && (!!selectedRoomId || !!selectedSection.board) && messages.length === 0; text: tr("暂无消息") }
                            Label { anchors.centerIn: parent; visible: !selectedRoomId && !selectedSection.board; text: tr("从左侧选择一个会话") }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.currentTheme.colors.cardBorderColor }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.margins: 12
                            TextField { id: messageInput; Layout.fillWidth: true; placeholderText: tr("说点什么…"); enabled: hasActiveConversation() && !sending; onAccepted: sendMessage() }
                            Button { text: sending ? tr("发送中…") : tr("发送"); highlighted: true; enabled: hasActiveConversation() && !sending && messageInput.text.trim().length > 0; onClicked: sendMessage() }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: errorDialog
        modal: true
        title: tr("络聊提示")
        standardButtons: Dialog.Ok
        contentItem: Label { text: errorText; padding: 20; wrapMode: Text.Wrap; width: 380 }
    }
}
