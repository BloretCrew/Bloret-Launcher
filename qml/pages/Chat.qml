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
    property var selectedSection: ({})
    property var messages: []

    function tr(text) { return Backend ? Backend.tr(text) : text }
    function items(value) {
        if (typeof value === "string") {
            try { value = JSON.parse(value) } catch (error) { return [] }
        }
        if (Array.isArray(value)) return value
        return value && Array.isArray(value.items) ? value.items : []
    }
    function sectionName(section) { return String(section.section || section.fullName || section.name || "") }
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
    function openSection(section) {
        selectedSection = section || ({})
        messages = []
        if (!selectedSection.board || !sectionName(selectedSection)) return
        loading = true
        Backend.fetchBBBSChatMessages(String(selectedSection.board), sectionName(selectedSection))
    }
    function sendMessage() {
        var content = messageInput.text.trim()
        if (sending || !content || !selectedSection.board || !sectionName(selectedSection)) return
        pendingContent = content
        sending = true
        Backend.sendBBBSChatMessage(String(selectedSection.board), sectionName(selectedSection), content)
    }

    Component.onCompleted: {
        authenticated = !!Backend && !!Backend.isBBBSAuthenticated()
        if (authenticated) {
            loading = true
            Backend.fetchBBBSSections("")
        }
    }

    Timer {
        interval: 8000
        repeat: true
        running: authenticated && !!selectedSection.board && sectionName(selectedSection).length > 0
        onTriggered: Backend.fetchBBBSChatMessages(String(selectedSection.board), sectionName(selectedSection))
    }

    Connections {
        target: Backend
        function onBbbsSectionsReceived(value) {
            sections = chatSections(value)
            loading = false
        }
        function onBbbsChatMessagesReceived(value) {
            messages = items(value)
            loading = false
            if (messages.length > 0) chatList.positionViewAtEnd()
        }
        function onBbbsOperationFinished(operation, ok, result) {
            if (operation !== "chat_message") return
            sending = false
            if (!ok) {
                errorText = result && (result.error || result.message) ? (result.error || result.message) : tr("发送失败")
                errorDialog.open()
                return
            }
            messageInput.text = ""
            pendingContent = ""
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
            Button { text: tr("刷新"); onClicked: { Backend.fetchBBBSSections(""); if (selectedSection.board) openSection(selectedSection) } }
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
                    Layout.preferredWidth: 260
                    Layout.fillHeight: true
                    padding: 10
                    ColumnLayout {
                        anchors.fill: parent
                        Label { text: tr("聊天室"); font.pixelSize: 17; font.weight: Font.DemiBold }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: sections
                            delegate: ItemDelegate {
                                width: ListView.view.width
                                text: (modelData.board || "") + " / " + (modelData.name || modelData.section || "")
                                highlighted: sectionName(modelData) === sectionName(selectedSection) && modelData.board === selectedSection.board
                                onClicked: openSection(modelData)
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
                            Label { text: selectedSection.name || selectedSection.section || tr("选择一个聊天室"); font.pixelSize: 18; font.weight: Font.DemiBold; Layout.fillWidth: true }
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
                                implicitHeight: messageRow.implicitHeight + topPadding + bottomPadding
                                padding: 10
                                RowLayout {
                                    id: messageRow
                                    width: parent.width - parent.leftPadding - parent.rightPadding
                                    Label { text: senderOf(modelData); font.weight: Font.DemiBold; Layout.preferredWidth: 120; elide: Text.ElideRight }
                                    Label { text: contentOf(modelData); wrapMode: Text.Wrap; Layout.fillWidth: true }
                                    Label { text: timeOf(modelData); color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 11 }
                                }
                            }
                            Label { anchors.centerIn: parent; visible: !loading && !!selectedSection.board && messages.length === 0; text: tr("暂无消息") }
                            Label { anchors.centerIn: parent; visible: !selectedSection.board; text: tr("从左侧选择一个聊天室") }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.currentTheme.colors.cardBorderColor }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.margins: 12
                            TextField { id: messageInput; Layout.fillWidth: true; placeholderText: tr("说点什么…"); enabled: !!selectedSection.board && !sending; onAccepted: sendMessage() }
                            Button { text: sending ? tr("发送中…") : tr("发送"); highlighted: true; enabled: !!selectedSection.board && !sending && messageInput.text.trim().length > 0; onClicked: sendMessage() }
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
