import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

FluentWindow {
    id: oobeWindow
    visible: true
    title: Backend ? Backend.tr("欢迎使用 Bloret Launcher") : "Welcome to Bloret Launcher"
    width: 850
    height: 600
    minimumWidth: 800
    minimumHeight: 550

    // 不显示导航栏
    navigationView.navExpandWidth: 0

    property int currentPage: 0
    property int totalPages: 6
    property var selectedLanguage: "zh-cn"
    property string selectedJavaPath: ""
    property string minecraftDirPath: ""
    property bool javaInstalled: false
    property bool isCheckingJava: false
    property bool isInstallingJava: false
    property bool isWaitingForLogin: false  // 等待登录状态
    property bool isSyncingAccounts: false  // 同步账户中
    property var minecraftAccounts: []      // Minecraft 账户列表

    Component.onCompleted: {
        minecraftDirPath = Backend.getDefaultMinecraftDir()
        // 自动检查 Java 环境
        if (Backend) {
            Backend.checkJavaEnvironment()
        }
    }

    // 登录状态检查定时器
    Timer {
        id: loginCheckTimer
        interval: 1000  // 1秒检查一次
        repeat: true
        onTriggered: {
            if (oobeWindow.isWaitingForLogin && Backend) {
                if (Backend.getBloretPassPortLoginStatus()) {
                    // 登录成功，停止定时器并继续
                    oobeWindow.isWaitingForLogin = false
                    loginCheckTimer.stop()
                    // 自动进入下一步
                    if (oobeWindow.currentPage < oobeWindow.totalPages - 1) {
                        oobeWindow.currentPage++
                    }
                }
            }
        }
    }

    // 同步账户刷新定时器
    Timer {
        id: syncRefreshTimer
        interval: 2000  // 2秒后刷新
        repeat: false
        onTriggered: {
            if (Backend) {
                oobeWindow.minecraftAccounts = Backend.getMinecraftAccounts()
                oobeWindow.isSyncingAccounts = false
            }
        }
    }

    // 使用 FluentPage 作为内容容器
    navigationItems: []

    // 主内容区域
    Item {
        anchors.fill: parent

        // 顶部进度指示器
        Rectangle {
            id: headerBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 80
            color: "#F9F9F9"

            RowLayout {
                anchors.centerIn: parent
                spacing: 12

                Repeater {
                    model: totalPages
                    delegate: Item {
                        width: 60
                        height: 32

                        Rectangle {
                            anchors.centerIn: parent
                            width: oobeWindow.currentPage === index ? 32 : 12
                            height: 12
                            radius: 6
                            color: {
                                if (oobeWindow.currentPage === index) {
                                    return "#0078D4"
                                } else if (index < oobeWindow.currentPage) {
                                    return "#4CAF50"
                                } else {
                                    return "#E0E0E0"
                                }
                            }
                            Behavior on width { NumberAnimation { duration: 200 } }
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }

                        Text {
                            anchors.top: parent.bottom
                            anchors.topMargin: 4
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: {
                                switch (index) {
                                    case 0: return Backend ? Backend.tr("欢迎") : "Welcome"
                                    case 1: return Backend ? Backend.tr("语言") : "Language"
                                    case 2: return Backend ? Backend.tr("登录") : "Login"
                                    case 3: return Backend ? Backend.tr("同步") : "Sync"
                                    case 4: return "Java"
                                    case 5: return Backend ? Backend.tr("目录") : "Folder"
                                    default: return ""
                                }
                            }
                            font.pixelSize: 11
                            color: "#666666"
                            visible: oobeWindow.currentPage === index || index < oobeWindow.currentPage + 2
                        }
                    }
                }
            }
        }

        // 内容区域
        ScrollView {
            anchors.top: headerBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: footerBar.top
            clip: true

            Item {
                width: parent.width
                height: Math.max(contentColumn.implicitHeight + 40, 400)

                ColumnLayout {
                    id: contentColumn
                    anchors.centerIn: parent
                    spacing: 24
                    width: Math.min(parent.width - 80, 650)

                    // 第 0 页：欢迎
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 0

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Image {
                                source: Qt.platform.os === "osx" ? "../Bloret-Fluent.png" : "../Bloret.png"
                                Layout.alignment: Qt.AlignHCenter
                                sourceSize.width: 100
                                sourceSize.height: 100
                                fillMode: Image.PreserveAspectFit
                            }

                            Text {
                                text: Backend ? Backend.tr("欢迎使用 Bloret Launcher") : "Welcome to Bloret Launcher"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.TitleLarge
                            }

                            Text {
                                text: Backend ? Backend.tr("欢迎！让我们一起开启 Bloret Launcher 的旅程！接下来，我们需要进行一些必备操作。") : "Welcome! This will help you quickly set up Bloret Launcher for a better Minecraft experience."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Body
                                color: "#666666"
                            }
                        }
                    }

                    // 第 1 页：语言选择
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 1

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Text {
                                text: Backend ? Backend.tr("选择语言") : "Choose Language"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Title
                            }

                            Text {
                                text: Backend ? Backend.tr("请选择您希望使用的界面语言：") : "Please select your preferred interface language:"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Body
                                color: "#666666"
                            }

                            ComboBox {
                                id: languageComboBox
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: 350
                                model: [
                                    { text: "简体中文", value: "zh-cn" },
                                    { text: "English", value: "en-us" }
                                ]
                                textRole: "text"
                                valueRole: "value"
                                currentIndex: 0

                                onActivated: function(index) {
                                    oobeWindow.selectedLanguage = model[index].value
                                    if (Backend) {
                                        Backend.setLanguage(oobeWindow.selectedLanguage)
                                    }
                                }
                            }
                        }
                    }

                    // 第 2 页：登录 Bloret PassPort
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 2

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Text {
                                text: Backend ? Backend.tr("登录 Bloret PassPort") : "Login to Bloret PassPort"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Title
                            }

                            Text {
                                text: Backend ? Backend.tr("登录 Bloret PassPort 以同步您的 Minecraft 账户和设置。") : "Login to Bloret PassPort to sync your Minecraft accounts and settings."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Body
                                color: "#666666"
                            }

                            // 等待登录状态显示
                            ColumnLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 12
                                visible: oobeWindow.isWaitingForLogin

                                RowLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 8

                                    BusyIndicator {
                                        running: oobeWindow.isWaitingForLogin
                                        implicitWidth: 20
                                        implicitHeight: 20
                                    }

                                    Text {
                                        text: Backend ? Backend.tr("正在等待登录完成...") : "Waiting for login..."
                                        typography: Typography.Body
                                        color: "#666666"
                                    }
                                }

                                Text {
                                    text: Backend ? Backend.tr("请在浏览器中完成登录，登录成功后将自动继续。") : "Please complete login in the browser. It will continue automatically after login."
                                    Layout.alignment: Qt.AlignHCenter
                                    wrapMode: Text.Wrap
                                    Layout.preferredWidth: 450
                                    horizontalAlignment: Text.AlignHCenter
                                    typography: Typography.Caption
                                    color: "#666666"
                                }
                            }

                            Button {
                                Layout.alignment: Qt.AlignHCenter
                                text: {
                                    if (oobeWindow.isWaitingForLogin) {
                                        return Backend ? Backend.tr("重新打开登录页面") : "Reopen Login Page"
                                    } else if (Backend && Backend.getBloretPassPortLoginStatus()) {
                                        return Backend.tr("已登录，继续")
                                    }
                                    return Backend ? Backend.tr("前往登录") : "Go to Login"
                                }
                                highlighted: !oobeWindow.isWaitingForLogin
                                onClicked: {
                                    if (Backend && Backend.getBloretPassPortLoginStatus()) {
                                        // 已登录，继续下一步
                                        if (oobeWindow.currentPage < oobeWindow.totalPages - 1) {
                                            oobeWindow.currentPage++
                                        }
                                    } else {
                                        // 未登录，打开浏览器并开始等待
                                        Backend.loginBloretPassPort()
                                        oobeWindow.isWaitingForLogin = true
                                        loginCheckTimer.start()
                                    }
                                }
                            }

                            Text {
                                text: Backend ? Backend.tr("提示：您必须登录 Bloret PassPort 才能继续使用。") : "Tip: You must login to Bloret PassPort to continue."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Caption
                                color: "#666666"
                                visible: !oobeWindow.isWaitingForLogin
                            }
                        }
                    }

                    // 第 3 页：同步 Minecraft 账户
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 3

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Text {
                                text: Backend ? Backend.tr("同步 Minecraft 账户") : "Sync Minecraft Account"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Title
                            }

                            Text {
                                text: Backend ? Backend.tr("从 Bloret PassPort 同步您的 Minecraft 账户信息。") : "Sync your Minecraft account information from Bloret PassPort."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Body
                                color: "#666666"
                            }

                            // 同步状态/账户列表
                            ColumnLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 12
                                Layout.preferredWidth: 500

                                // 同步中显示
                                RowLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 8
                                    visible: oobeWindow.isSyncingAccounts

                                    BusyIndicator {
                                        running: oobeWindow.isSyncingAccounts
                                        implicitWidth: 20
                                        implicitHeight: 20
                                    }

                                    Text {
                                        text: Backend ? Backend.tr("正在同步账户...") : "Syncing accounts..."
                                        typography: Typography.Body
                                        color: "#666666"
                                    }
                                }

                                // 已同步的账户列表
                                ColumnLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 8
                                    visible: !oobeWindow.isSyncingAccounts && oobeWindow.minecraftAccounts.length > 0

                                    Text {
                                        text: Backend ? Backend.tr("已同步的账户：") : "Synced accounts:"
                                        typography: Typography.BodyStrong
                                        color: "#666666"
                                    }

                                    Repeater {
                                        model: oobeWindow.minecraftAccounts

                                        Rectangle {
                                            width: 400
                                            height: 50
                                            radius: 8
                                            color: "#FFFFFF"
                                            border.width: 1
                                            border.color: "#E0E0E0"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 12

                                                // 头像显示 - 使用矩形裁剪实现圆形
                                                Rectangle {
                                                    width: 32
                                                    height: 32
                                                    radius: 16  // 圆形
                                                    clip: true
                                                    color: "#E0E0E0"

                                                    Image {
                                                        id: avatarImageWnd
                                                        anchors.fill: parent
                                                        source: modelData.avatarUrl || ""
                                                        fillMode: Image.PreserveAspectCrop
                                                        cache: true
                                                        asynchronous: true

                                                        // 加载失败时显示默认头像字符
                                                        onStatusChanged: {
                                                            if (status === Image.Error) {
                                                                source = ""
                                                            }
                                                        }

                                                        // 加载中或失败时显示的占位符
                                                        Text {
                                                            anchors.centerIn: parent
                                                            text: modelData.name ? modelData.name.charAt(0).toUpperCase() : "?"
                                                            font.pixelSize: 16
                                                            font.bold: true
                                                            color: "#0078D4"
                                                            visible: avatarImageWnd.status === Image.Loading || avatarImageWnd.status === Image.Error || avatarImageWnd.source === ""
                                                        }
                                                    }
                                                }

                                                ColumnLayout {
                                                    spacing: 2
                                                    Text {
                                                        text: modelData.name || "Unknown"
                                                        typography: Typography.BodyStrong
                                                    }
                                                    Text {
                                                        text: modelData.type || "Offline"
                                                        typography: Typography.Caption
                                                        color: "#666666"
                                                    }
                                                    Item { Layout.fillWidth: true }
                                                }

                                                Item { Layout.fillWidth: true }

                                                // 默认账户标记
                                                Rectangle {
                                                    visible: modelData.isDefault
                                                    width: defaultLabelWnd.implicitWidth + 12
                                                    height: 20
                                                    radius: 10
                                                    color: "#0078D4"

                                                    Text {
                                                        id: defaultLabelWnd
                                                        anchors.centerIn: parent
                                                        text: Backend ? Backend.tr("默认") : "Default"
                                                        font.pixelSize: 11
                                                        color: "#FFFFFF"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // 没有账户时的提示
                                ColumnLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 8
                                    visible: !oobeWindow.isSyncingAccounts && oobeWindow.minecraftAccounts.length === 0

                                    Text {
                                        text: Backend ? Backend.tr("❌ 未找到 Minecraft 账户") : "❌ No Minecraft accounts found"
                                        Layout.alignment: Qt.AlignHCenter
                                        typography: Typography.Body
                                        color: "#E74C3C"
                                    }

                                    Text {
                                        text: Backend ? Backend.tr("请先前往 passport.bloret.net ，添加一个离线账户或微软账户，然后点击这里的同步按钮再继续。") : "Please go to passport.bloret.net to add an offline or Microsoft account, then click the sync button to continue."
                                        Layout.alignment: Qt.AlignHCenter
                                        wrapMode: Text.Wrap
                                        Layout.preferredWidth: 450
                                        horizontalAlignment: Text.AlignHCenter
                                        typography: Typography.Caption
                                        color: "#666666"
                                    }

                                    Button {
                                        text: Backend ? Backend.tr("打开 passport.bloret.net") : "Open passport.bloret.net"
                                        Layout.alignment: Qt.AlignHCenter
                                        onClicked: {
                                            if (Backend) {
                                                Backend.manageAccountOnWebsite()
                                            }
                                        }
                                    }
                                }
                            }

                            // 同步按钮
                            Button {
                                Layout.alignment: Qt.AlignHCenter
                                text: {
                                    if (oobeWindow.isSyncingAccounts) {
                                        return Backend ? Backend.tr("同步中...") : "Syncing..."
                                    } else if (oobeWindow.minecraftAccounts.length > 0) {
                                        return Backend.tr("重新同步")
                                    }
                                    return Backend ? Backend.tr("同步账户") : "Sync Account"
                                }
                                highlighted: true
                                enabled: !oobeWindow.isSyncingAccounts
                                onClicked: {
                                    if (Backend) {
                                        oobeWindow.isSyncingAccounts = true
                                        Backend.syncMinecraftAccount()
                                        // 延迟刷新账户列表
                                        syncRefreshTimer.start()
                                    }
                                }
                            }
                        }
                    }

                    // 第 4 页：Java 环境检测
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 4

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Text {
                                text: Backend ? Backend.tr("Java 运行环境") : "Java Runtime Environment"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Title
                            }

                            Text {
                                text: {
                                    if (oobeWindow.isCheckingJava) {
                                        return Backend ? Backend.tr("正在检查 Java 环境...") : "Checking Java runtime environment..."
                                    } else if (oobeWindow.javaInstalled) {
                                        return Backend ? Backend.tr("✅ 已检测到 Java 运行环境。") : "✅ Java runtime environment detected."
                                    } else {
                                        return Backend ? Backend.tr("❌ 未检测到 Java 运行环境。请安装 Java 以继续。") : "❌ No Java runtime environment detected. Please install Java to continue."
                                    }
                                }
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Body
                            }

                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 16

                                Button {
                                    text: Backend ? Backend.tr("重新检测") : "Check Again"
                                    enabled: !oobeWindow.isCheckingJava && !oobeWindow.isInstallingJava
                                    onClicked: {
                                        if (Backend) {
                                            oobeWindow.isCheckingJava = true
                                            Backend.checkJavaEnvironment()
                                        }
                                    }
                                }

                                Button {
                                    text: {
                                        if (oobeWindow.isInstallingJava) {
                                            return Backend ? Backend.tr("正在安装...") : "Installing..."
                                        }
                                        return Backend ? Backend.tr("安装 Java 21") : "Install Java 21"
                                    }
                                    highlighted: !oobeWindow.javaInstalled
                                    enabled: !oobeWindow.isCheckingJava && !oobeWindow.isInstallingJava
                                    onClicked: {
                                        if (Backend) {
                                            oobeWindow.isInstallingJava = true
                                            Backend.installJava("21")
                                        }
                                    }
                                }
                            }

                            Text {
                                text: Backend ? Backend.tr("推荐安装 Java 21，这是 Minecraft 最新版本的推荐版本。") : "Java 21 is recommended for the latest Minecraft versions."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Caption
                                color: "#666666"
                            }
                        }
                    }

                    // 第 5 页：Minecraft 目录设置
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: oobeWindow.currentPage === 5

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 24

                            Text {
                                text: Backend ? Backend.tr("Minecraft 游戏文件夹") : "Minecraft Game Folder"
                                Layout.alignment: Qt.AlignHCenter
                                typography: Typography.Title
                            }

                            Text {
                                text: Backend ? Backend.tr("请选择或确认您的 Minecraft 游戏文件夹位置。\n如果您已有 Minecraft 版本文件夹，请选择该文件夹。") : "Please select or confirm your Minecraft game folder location.\nIf you already have Minecraft versions folders, please select that folder."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Body
                                color: "#666666"
                            }

                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 12

                                TextField {
                                    id: minecraftDirEdit
                                    text: oobeWindow.minecraftDirPath
                                    placeholderText: Backend ? Backend.tr("Minecraft 文件夹路径") : "Minecraft folder path"
                                    Layout.preferredWidth: 400
                                    readOnly: true
                                }

                                Button {
                                    text: Backend ? Backend.tr("浏览...") : "Browse..."
                                    onClicked: {
                                        if (Backend) {
                                            var selectedDir = Backend.selectMinecraftDirectory()
                                            if (selectedDir && selectedDir !== "") {
                                                oobeWindow.minecraftDirPath = selectedDir
                                            }
                                        }
                                    }
                                }
                            }

                            Text {
                                text: Backend ? Backend.tr("默认路径: %appdata%/Bloret-Launcher").replace("%appdata%", Backend ? Backend.getAppDataPath() : "") : "Default path: %appdata%/Bloret-Launcher"
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Caption
                                color: "#666666"
                            }

                            Text {
                                text: Backend ? Backend.tr("提示：如果您不确定，可以使用默认路径，稍后可以在设置中更改。") : "Tip: If you're not sure, you can use the default path and change it later in settings."
                                Layout.alignment: Qt.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.preferredWidth: 550
                                horizontalAlignment: Text.AlignHCenter
                                typography: Typography.Caption
                                color: "#666666"
                            }
                        }
                    }
                }
            }
        }

        // 底部按钮栏
        Rectangle {
            id: footerBar
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 70
            color: "#F9F9F9"

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 24
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Button {
                    id: backButton
                    text: Backend ? Backend.tr("返回") : "Back"
                    visible: oobeWindow.currentPage > 0
                    onClicked: {
                        if (oobeWindow.currentPage > 0) {
                            oobeWindow.currentPage--
                        }
                    }
                }

                Button {
                    id: nextButton
                    text: {
                        if (oobeWindow.currentPage === oobeWindow.totalPages - 1) {
                            return Backend ? Backend.tr("完成") : "Finish"
                        }
                        return Backend ? Backend.tr("下一步") : "Next"
                    }
                    highlighted: true
                    enabled: canProceed()
                    onClicked: {
                        if (oobeWindow.currentPage === oobeWindow.totalPages - 1) {
                            finishOOBE()
                        } else {
                            oobeWindow.currentPage++
                        }
                    }
                }
            }
        }
    }

    function canProceed() {
        switch (oobeWindow.currentPage) {
            case 0: return true
            case 1: return true
            case 2: return Backend && Backend.getBloretPassPortLoginStatus()
            case 3: return oobeWindow.minecraftAccounts.length > 0
            case 4: return oobeWindow.javaInstalled
            case 5: return true
            default: return false
        }
    }

    function finishOOBE() {
        if (Backend) {
            Backend.setMinecraftDirectory(oobeWindow.minecraftDirPath)
            Backend.completeOOBE()
        }
        oobeWindow.close()
    }

    Connections {
        target: Backend

        function onJavaEnvironmentChecked(installed, javaPath) {
            oobeWindow.isCheckingJava = false
            oobeWindow.javaInstalled = installed
            if (installed) {
                oobeWindow.selectedJavaPath = javaPath
            }
        }

        function onJavaInstalled(javaPath) {
            oobeWindow.isInstallingJava = false
            if (javaPath && javaPath !== "") {
                oobeWindow.javaInstalled = true
                oobeWindow.selectedJavaPath = javaPath
            }
        }
    }
}
