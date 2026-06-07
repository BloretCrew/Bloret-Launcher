import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: settingsPage

    property string _title: Backend ? Backend.tr("设置") : "设置"
    title: _title

    property string currentMcDir: ""
    property var javaPaths: []
    property string currentJavaPath: ""
    property string themeMode: ""
    property var languages: []
    property bool traySupported: true
    property string localIPAddress: ""

    Component.onCompleted: {
        refreshData();
    }

    Connections {
        target: Backend
        function onLanguageChanged() {
            refreshTranslations();
        }
    }

    function refreshTranslations() {
        _title = Backend ? Backend.tr("设置") : "设置";
        _versionTitle = Backend ? Backend.tr("当前版本") : "当前版本";
        _versionDesc = Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher";
        _mcJavaSection = Backend ? Backend.tr("Minecraft 与 Java") : "Minecraft 与 Java";
        _javaTitle = Backend ? Backend.tr("Java") : "Java";
        _javaDesc = Backend ? Backend.tr("选择用于启动 Minecraft 的 Java") : "选择用于启动 Minecraft 的 Java";
        _mcFolderTitle = Backend ? Backend.tr("Minecraft 文件夹位置") : "Minecraft 文件夹位置";
        _mcToolbarTitle = Backend ? Backend.tr("Minecraft 小工具栏") : "Minecraft 小工具栏";
        _mcToolbarDesc = Backend ? Backend.tr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏") : "当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏";
        _sourceTitle = Backend ? Backend.tr("下载源") : "下载源";
        _sourceDesc = Backend ? Backend.tr("选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连") : "选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连";
        _homeSection = Backend ? Backend.tr("首页") : "首页";
        _showAccountTitle = Backend ? Backend.tr("显示账户信息") : "显示账户信息";
        _showAccountDesc = Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息";
        _showAccountModeCompact = Backend ? Backend.tr("简略展示") : "简略展示";
        _showAccountModeFull = Backend ? Backend.tr("完整展示") : "完整展示";
        _showAccountModeHidden = Backend ? Backend.tr("隐藏") : "隐藏";
        _webRemoterSection = Backend ? Backend.tr("Web 遥控器") : "Web 遥控器";
        _webRemoterTitle = Backend ? Backend.tr("启用 Web 遥控器") : "启用 Web 遥控器";
        _webRemoterDesc = Backend ? Backend.tr("开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft") : "开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft";
        _webRemoterQRTitle = Backend ? Backend.tr("连接二维码") : "连接二维码";
        _webRemoterQRDesc = Backend ? Backend.tr("扫描二维码快速访问遥控器页面") : "扫描二维码快速访问遥控器页面";
        _closeToTrayTitle = Backend ? Backend.tr("关闭按钮最小化到托盘") : "关闭按钮最小化到托盘";
        _closeToTrayDesc = Backend ? Backend.tr("开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序") : "开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序";
        _closeToTrayUnavailableDesc = Backend ? Backend.tr("当前平台不支持托盘") : "当前平台不支持托盘";
        _repeatRunTitle = Backend ? Backend.tr("允许重复打开 Bloret Launcher") : "允许重复打开 Bloret Launcher";
        _repeatRunDesc = Backend ? Backend.tr("开启后可同时打开多个 Bloret Launcher 实例") : "开启后可同时打开多个 Bloret Launcher 实例";
        _appearanceSection = Backend ? Backend.tr("外观") : "外观";
        _langTitle = Backend ? Backend.tr("语言 / language") : "语言 / language";
        _langDesc = Backend ? Backend.tr("调整语言设置") : "调整语言设置";
        _themeTitle = Backend ? Backend.tr("主题") : "主题";
        _themeDesc = Backend ? Backend.tr("选择界面的颜色模式") : "选择界面的颜色模式";
        _logSection = Backend ? Backend.tr("日志") : "日志";
        _logFolderTitle = Backend ? Backend.tr("日志文件夹位置") : "日志文件夹位置";
        _logFolderDesc = Backend ? Backend.tr("存储所有 Bloret Launcher 日志的文件夹位置") : "存储所有 Bloret Launcher 日志的文件夹位置";
        _clearLogTitle = Backend ? Backend.tr("清空日志") : "清空日志";
        _clearLogDesc = Backend ? Backend.tr("清空 log 文件夹所有的日志文件") : "清空 log 文件夹所有的日志文件";
        _browseText = Backend ? Backend.tr("浏览...") : "浏览...";
        _openText = Backend ? Backend.tr("打开") : "打开";
        _clearText = Backend ? Backend.tr("清空") : "清空";
        _restartTip = Backend ? Backend.tr("设置界面大部分内容需要重启程序后生效。") : "设置界面大部分内容需要重启程序后生效。";
        _gamepadSection = Backend ? Backend.tr("虚拟手柄") : "虚拟手柄";
        _moveSensitivityTitle = Backend ? Backend.tr("移动摇杆灵敏度") : "移动摇杆灵敏度";
        _moveSensitivityDesc = Backend ? Backend.tr("控制移动摇杆的响应速度") : "控制移动摇杆的响应速度";
        _viewSensitivityTitle = Backend ? Backend.tr("视角摇杆灵敏度") : "视角摇杆灵敏度";
        _viewSensitivityDesc = Backend ? Backend.tr("控制视角旋转的速度") : "控制视角旋转的速度";
        _networkSection = Backend ? Backend.tr("网络") : "网络";
        _notificationSection = Backend ? Backend.tr("通知") : "通知";
        _notifMasterTitle = Backend ? Backend.tr("启用系统通知") : "启用系统通知";
        _notifMasterDesc = Backend ? Backend.tr("关闭后将不再发送任何系统通知") : "关闭后将不再发送任何系统通知";
        _notifConfigTitle = Backend ? Backend.tr("通知偏好设置") : "通知偏好设置";
        _notifConfigDesc = Backend ? Backend.tr("选择要接收哪些类别的系统通知") : "选择要接收哪些类别的系统通知";
        _notifDialogTitle = Backend ? Backend.tr("通知偏好设置") : "通知偏好设置";
        _notifLaunchReady = Backend ? Backend.tr("Minecraft 启动完成") : "Minecraft 启动完成";
        _notifLaunchError = Backend ? Backend.tr("启动失败 / 崩溃 / 超时") : "启动失败 / 崩溃 / 超时";
        _notifDownload = Backend ? Backend.tr("下载完成及失败") : "下载完成及失败";
        _notifInstall = Backend ? Backend.tr("安装完成及失败") : "安装完成及失败";
        _notifUpdate = Backend ? Backend.tr("应用更新") : "应用更新";
        _notifChatMessage = Backend ? Backend.tr("Minecraft 聊天消息") : "Minecraft 聊天消息";
        _notifCopilot = Backend ? Backend.tr("Copilot Agent") : "Copilot Agent";
        _notifAccount = Backend ? Backend.tr("账户登录 / 同步") : "账户登录 / 同步";
        _notifConfigBtn = Backend ? Backend.tr("配置通知...") : "配置通知...";
        _notifCloseBtn = Backend ? Backend.tr("关闭") : "关闭";
        _barkTitle = Backend ? Backend.tr("Bark 推送") : "Bark 推送";
        _barkDesc = Backend ? Backend.tr("配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备") : "配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备";
        _barkPlaceholder = Backend ? Backend.tr("https://api.day.app/your_device_key") : "https://api.day.app/your_device_key";
        _notifSystemLabel = Backend ? Backend.tr("系统") : "系统";
        _notifBarkLabel = Backend ? Backend.tr("Bark") : "Bark";
        _barkTestBtn = Backend ? Backend.tr("测试") : "测试";
        _barkTestSuccess = Backend ? Backend.tr("Bark 推送测试成功") : "Bark 推送测试成功";
        _barkTestFail = Backend ? Backend.tr("Bark 推送测试失败") : "Bark 推送测试失败";
        _proxyTitle = Backend ? Backend.tr("网络代理") : "网络代理";
        _proxyDesc = Backend ? Backend.tr("设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理") : "设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理";
        _proxyPlaceholder = Backend ? Backend.tr("不使用代理") : "不使用代理";
    }

    property string _versionTitle: Backend ? Backend.tr("当前版本") : "当前版本"
    property string _versionDesc: Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher"
    property string _mcJavaSection: Backend ? Backend.tr("Minecraft 与 Java") : "Minecraft 与 Java"
    property string _javaTitle: Backend ? Backend.tr("Java") : "Java"
    property string _javaDesc: Backend ? Backend.tr("选择用于启动 Minecraft 的 Java") : "选择用于启动 Minecraft 的 Java"
    property string _mcFolderTitle: Backend ? Backend.tr("Minecraft 文件夹位置") : "Minecraft 文件夹位置"
    property string _mcToolbarTitle: Backend ? Backend.tr("Minecraft 小工具栏") : "Minecraft 小工具栏"
    property string _mcToolbarDesc: Backend ? Backend.tr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏") : "当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"
    property string _sourceTitle: Backend ? Backend.tr("下载源") : "下载源"
    property string _sourceDesc: Backend ? Backend.tr("选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连") : "选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连"
    property string _homeSection: Backend ? Backend.tr("首页") : "首页"
    property string _showAccountTitle: Backend ? Backend.tr("显示账户信息") : "显示账户信息"
    property string _showAccountDesc: Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息"
    property string _showAccountModeCompact: Backend ? Backend.tr("简略展示") : "简略展示"
    property string _showAccountModeFull: Backend ? Backend.tr("完整展示") : "完整展示"
    property string _showAccountModeHidden: Backend ? Backend.tr("隐藏") : "隐藏"
    property string _webRemoterSection: Backend ? Backend.tr("Web 遥控器") : "Web 遥控器"
    property string _webRemoterTitle: Backend ? Backend.tr("启用 Web 遥控器") : "启用 Web 遥控器"
    property string _webRemoterDesc: Backend ? Backend.tr("开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft") : "开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft"
    property string _webRemoterQRTitle: Backend ? Backend.tr("连接二维码") : "连接二维码"
    property string _webRemoterQRDesc: Backend ? Backend.tr("扫描二维码快速访问遥控器页面") : "扫描二维码快速访问遥控器页面"
    property string _closeToTrayTitle: Backend ? Backend.tr("关闭按钮最小化到托盘") : "关闭按钮最小化到托盘"
    property string _closeToTrayDesc: Backend ? Backend.tr("开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序") : "开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序"
    property string _closeToTrayUnavailableDesc: Backend ? Backend.tr("当前平台不支持托盘") : "当前平台不支持托盘"
    property string _repeatRunTitle: Backend ? Backend.tr("允许重复打开 Bloret Launcher") : "允许重复打开 Bloret Launcher"
    property string _repeatRunDesc: Backend ? Backend.tr("开启后可同时打开多个 Bloret Launcher 实例") : "开启后可同时打开多个 Bloret Launcher 实例"
    property string _appearanceSection: Backend ? Backend.tr("外观") : "外观"
    property string _langTitle: Backend ? Backend.tr("语言 / language") : "语言 / language"
    property string _langDesc: Backend ? Backend.tr("调整语言设置") : "调整语言设置"
    property string _themeTitle: Backend ? Backend.tr("主题") : "主题"
    property string _themeDesc: Backend ? Backend.tr("选择界面的颜色模式") : "选择界面的颜色模式"
    property string _logSection: Backend ? Backend.tr("日志") : "日志"
    property string _logFolderTitle: Backend ? Backend.tr("日志文件夹位置") : "日志文件夹位置"
    property string _logFolderDesc: Backend ? Backend.tr("存储所有 Bloret Launcher 日志的文件夹位置") : "存储所有 Bloret Launcher 日志的文件夹位置"
    property string _clearLogTitle: Backend ? Backend.tr("清空日志") : "清空日志"
    property string _clearLogDesc: Backend ? Backend.tr("清空 log 文件夹所有的日志文件") : "清空 log 文件夹所有的日志文件"
    property string _browseText: Backend ? Backend.tr("浏览...") : "浏览..."
    property string _openText: Backend ? Backend.tr("打开") : "打开"
    property string _clearText: Backend ? Backend.tr("清空") : "清空"
    property string _restartTip: Backend ? Backend.tr("设置界面大部分内容需要重启程序后生效。") : "设置界面大部分内容需要重启程序后生效。"
    property string _gamepadSection: Backend ? Backend.tr("虚拟手柄") : "虚拟手柄"
    property string _moveSensitivityTitle: Backend ? Backend.tr("移动摇杆灵敏度") : "移动摇杆灵敏度"
    property string _moveSensitivityDesc: Backend ? Backend.tr("控制移动摇杆的响应速度") : "控制移动摇杆的响应速度"
    property string _viewSensitivityTitle: Backend ? Backend.tr("视角摇杆灵敏度") : "视角摇杆灵敏度"
    property string _viewSensitivityDesc: Backend ? Backend.tr("控制视角旋转的速度") : "控制视角旋转的速度"
    property string _networkSection: Backend ? Backend.tr("网络") : "网络"
    property string _notificationSection: Backend ? Backend.tr("通知") : "通知"
    property string _notifMasterTitle: Backend ? Backend.tr("启用系统通知") : "启用系统通知"
    property string _notifMasterDesc: Backend ? Backend.tr("关闭后将不再发送任何系统通知") : "关闭后将不再发送任何系统通知"
    property string _notifConfigTitle: Backend ? Backend.tr("通知偏好设置") : "通知偏好设置"
    property string _notifConfigDesc: Backend ? Backend.tr("选择要接收哪些类别的系统通知") : "选择要接收哪些类别的系统通知"
    property string _notifDialogTitle: Backend ? Backend.tr("通知偏好设置") : "通知偏好设置"
    property string _notifLaunchReady: Backend ? Backend.tr("Minecraft 启动完成") : "Minecraft 启动完成"
    property string _notifLaunchError: Backend ? Backend.tr("启动失败 / 崩溃 / 超时") : "启动失败 / 崩溃 / 超时"
    property string _notifDownload: Backend ? Backend.tr("下载完成及失败") : "下载完成及失败"
    property string _notifInstall: Backend ? Backend.tr("安装完成及失败") : "安装完成及失败"
    property string _notifUpdate: Backend ? Backend.tr("应用更新") : "应用更新"
    property string _notifChatMessage: Backend ? Backend.tr("Minecraft 聊天消息") : "Minecraft 聊天消息"
    property string _notifCopilot: Backend ? Backend.tr("Copilot Agent") : "Copilot Agent"
    property string _notifAccount: Backend ? Backend.tr("账户登录 / 同步") : "账户登录 / 同步"
    property string _notifConfigBtn: Backend ? Backend.tr("配置通知...") : "配置通知..."
    property string _notifCloseBtn: Backend ? Backend.tr("关闭") : "关闭"
    property string _barkTitle: Backend ? Backend.tr("Bark 推送") : "Bark 推送"
    property string _barkDesc: Backend ? Backend.tr("配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备") : "配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备"
    property string _barkPlaceholder: Backend ? Backend.tr("https://api.day.app/your_device_key") : "https://api.day.app/your_device_key"
    property string _notifSystemLabel: Backend ? Backend.tr("系统") : "系统"
    property string _notifBarkLabel: Backend ? Backend.tr("Bark") : "Bark"
    property string _barkTestBtn: Backend ? Backend.tr("测试") : "测试"
    property string _barkTestSuccess: Backend ? Backend.tr("Bark 推送测试成功") : "Bark 推送测试成功"
    property string _barkTestFail: Backend ? Backend.tr("Bark 推送测试失败") : "Bark 推送测试失败"
    property string _proxyTitle: Backend ? Backend.tr("网络代理") : "网络代理"
    property string _proxyDesc: Backend ? Backend.tr("设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理") : "设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理"
    property string _proxyPlaceholder: Backend ? Backend.tr("不使用代理") : "不使用代理"

    function refreshData() {
        refreshTranslations();
        if (Backend) {
            currentMcDir = Backend.getMinecraftDir();
            javaPaths = Backend.getSystemJavas();
            currentJavaPath = Backend.getCurrentJavaPath();
            themeMode = Backend.getThemeMode();

            if (javaPaths.indexOf("Auto") === -1) {
                javaPaths.unshift("Auto");
            }

            javaCombo.currentIndex = javaPaths.indexOf(currentJavaPath);
            if (javaCombo.currentIndex === -1) {
                javaPaths.push(currentJavaPath);
                javaCombo.currentIndex = javaPaths.length - 1;
            }

            themeCombo.currentIndex = ["Auto", "Light", "Dark"].indexOf(themeMode);

            languages = Backend.getLanguages();
            for (var i = 0; i < languages.length; i++) {
                if (languages[i].code === Backend.getLanguageCode()) {
                    langCombo.currentIndex = i;
                    break;
                }
            }

            showAccountCombo.currentIndex = ["compact", "full", "hidden"].indexOf(Backend.getShowAccountOnHome());
            minimizeToTraySwitch.checked = Backend.getMinimizeToTrayOnClose();
            traySupported = Backend.isSystemTrayAvailable();
            repeatRunSwitch.checked = Backend.getRepeatRun();
            webRemoterSwitch.checked = Backend.getWebRemoterEnabled();
            localIPAddress = Backend.getLocalIPAddress();
            notifMasterSwitch.checked = Backend.getNotificationSetting("enabled");
            barkUrlField.text = Backend.getBarkUrl();
        }
    }

    SettingCard {
        Layout.fillWidth: true
        title: _versionTitle
        description: _versionDesc
        icon.name: "ic_fluent_info_20_regular"
        Label {
            text: Backend ? Backend.getBloretVersion() : "2.0.0-Beta"
            font.weight: Font.DemiBold
            color: Theme.accentColor || Theme.currentTheme.colors.textColor
            Layout.alignment: Qt.AlignVCenter
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _mcJavaSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _javaTitle
            description: _javaDesc
            icon.name: "ic_fluent_code_20_regular"
            ComboBox {
                id: javaCombo
                model: javaPaths
                Layout.preferredWidth: 250
                onActivated: {
                    if (Backend)
                        Backend.setCurrentJavaPath(currentText);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _mcFolderTitle
            description: currentMcDir
            icon.name: "ic_fluent_folder_20_regular"
            RowLayout {
                spacing: 8
                Button {
                    text: _browseText
                    onClicked: {
                        if (Backend) {
                            var path = Backend.browseMinecraftDir();
                            if (path !== "")
                                currentMcDir = path;
                        }
                    }
                }
                Button {
                    flat: true
                    text: _openText
                    onClicked: {
                        if (Backend)
                            Backend.openMinecraftDir();
                    }
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _mcToolbarTitle
            description: _mcToolbarDesc
            icon.name: "ic_fluent_window_dev_tools_20_filled"
            Switch {
                checked: true
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _sourceTitle
            description: _sourceDesc
            icon.name: "ic_fluent_globe_20_regular"
            ComboBox {
                id: sourceCombo
                width: 220
                height: 32
                model: [
                    { text: qsTr("BMCLAPI"), value: "bmclapi" },
                    { text: qsTr("Bloret"), value: "gitcode" },
                    { text: qsTr("Mojang"), value: "official" }
                ]
                textRole: "text"
                valueRole: "value"
                currentIndex: {
                    if (!Backend) return 1;
                    var src = Backend.getDownloadSource();
                    for (var i = 0; i < sourceCombo.model.length; i++) {
                        if (sourceCombo.model[i].value === src)
                            return i;
                    }
                    return 1;
                }
                onCurrentValueChanged: {
                    if (Backend)
                        Backend.setDownloadSource(currentValue);
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _homeSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _showAccountTitle
            description: _showAccountDesc
            icon.name: "ic_fluent_person_20_regular"
            ComboBox {
                id: showAccountCombo
                model: [
                    { text: _showAccountModeCompact, value: "compact" },
                    { text: _showAccountModeFull, value: "full" },
                    { text: _showAccountModeHidden, value: "hidden" }
                ]
                textRole: "text"
                valueRole: "value"
                Layout.preferredWidth: 150
                onActivated: {
                    if (Backend)
                        Backend.setShowAccountOnHome(currentValue);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _closeToTrayTitle
            description: traySupported ? _closeToTrayDesc : _closeToTrayUnavailableDesc
            icon.name: "ic_fluent_settings_20_regular"
            Switch {
                id: minimizeToTraySwitch
                checked: true
                enabled: traySupported
                onCheckedChanged: {
                    if (Backend)
                        Backend.setMinimizeToTrayOnClose(checked);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _repeatRunTitle
            description: _repeatRunDesc
            icon.name: "ic_fluent_window_multiple_20_regular"
            Switch {
                id: repeatRunSwitch
                checked: false
                onCheckedChanged: {
                    if (Backend)
                        Backend.setRepeatRun(checked);
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _webRemoterSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _webRemoterTitle
            description: _webRemoterDesc
            icon.name: "ic_fluent_game_controller_20_regular"
            Switch {
                id: webRemoterSwitch
                checked: true
                onCheckedChanged: {
                    if (Backend)
                        Backend.setWebRemoterEnabled(checked);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _webRemoterQRTitle
            description: "http://" + localIPAddress + ":25252/"
            icon.name: "ic_fluent_qr_code_20_regular"
            Rectangle {
                width: 120
                height: 120
                color: "transparent"
                Layout.alignment: Qt.AlignVCenter
                Image {
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectFit
                    source: Backend ? Backend.getWebRemoterQRCode() : ""
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _gamepadSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _moveSensitivityTitle
            description: _moveSensitivityDesc
            icon.name: "ic_fluent_thumb_like_20_regular"
            RowLayout {
                spacing: 10
                Slider {
                    id: moveSensitivitySlider
                    from: 10
                    to: 100
                    stepSize: 5
                    value: Backend ? Backend.getGamepadMoveSensitivity() : 50
                    onMoved: {
                        if (Backend) Backend.setGamepadMoveSensitivity(value);
                    }
                }
                Label {
                    text: moveSensitivitySlider.value.toFixed(0)
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    Layout.preferredWidth: 30
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _viewSensitivityTitle
            description: _viewSensitivityDesc
            icon.name: "ic_fluent_eye_20_regular"
            RowLayout {
                spacing: 10
                Slider {
                    id: viewSensitivitySlider
                    from: 10
                    to: 100
                    stepSize: 5
                    value: Backend ? Backend.getGamepadViewSensitivity() : 50
                    onMoved: {
                        if (Backend) Backend.setGamepadViewSensitivity(value);
                    }
                }
                Label {
                    text: viewSensitivitySlider.value.toFixed(0)
                    font.weight: Font.DemiBold
                    color: Theme.currentTheme.colors.textColor
                    Layout.preferredWidth: 30
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _notificationSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _notifMasterTitle
            description: _notifMasterDesc
            icon.name: "ic_fluent_alert_20_regular"
            Switch {
                id: notifMasterSwitch
                checked: true
                onCheckedChanged: {
                    if (Backend) Backend.setNotificationSetting("enabled", checked);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _notifConfigTitle
            description: _notifConfigDesc
            icon.name: "ic_fluent_settings_20_regular"
            Button {
                text: _notifConfigBtn
                onClicked: notifDialog.open()
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _barkTitle
            description: _barkDesc
            icon.name: "ic_fluent_phone_20_regular"
            RowLayout {
                spacing: 8
                TextField {
                    id: barkUrlField
                    placeholderText: _barkPlaceholder
                    Layout.preferredWidth: 240
                    text: Backend ? Backend.getBarkUrl() : ""
                    onEditingFinished: {
                        if (Backend) Backend.setBarkUrl(text);
                    }
                }
                Button {
                    text: _barkTestBtn
                    enabled: barkUrlField.text.length > 0
                    onClicked: {
                        if (Backend) {
                            var result = Backend.testBark()
                            barkTestInfoBar.severity = result === "发送成功" ? Severity.Success : Severity.Error
                            barkTestInfoBar.title = result === "发送成功" ? _barkTestSuccess : _barkTestFail
                            barkTestInfoBar.text = result
                            barkTestInfoBar.visible = true
                        }
                    }
                }
            }
        }

        InfoBar {
            id: barkTestInfoBar
            Layout.fillWidth: true
            visible: false
            timeout: 4000
        }
    }

    property var _notifCategories: [
        { key: "launch_ready", title: _notifLaunchReady, icon: "ic_fluent_checkmark_circle_20_regular" },
        { key: "launch_error", title: _notifLaunchError, icon: "ic_fluent_dismiss_circle_20_regular" },
        { key: "download", title: _notifDownload, icon: "ic_fluent_arrow_download_20_regular" },
        { key: "install", title: _notifInstall, icon: "ic_fluent_apps_20_regular" },
        { key: "update", title: _notifUpdate, icon: "ic_fluent_arrow_sync_20_regular" },
        { key: "chat_message", title: _notifChatMessage, icon: "ic_fluent_chat_20_regular" },
        { key: "copilot", title: _notifCopilot, icon: "ic_fluent_bot_20_regular" },
        { key: "account", title: _notifAccount, icon: "ic_fluent_person_20_regular" }
    ]

    property bool _barkConfigured: barkUrlField.text.length > 0

    Dialog {
        id: notifDialog
        title: _notifDialogTitle
        modal: true
        width: 520
        closePolicy: Popup.CloseOnEscape

        Flickable {
            Layout.fillWidth: true
            Layout.maximumHeight: 450
            Layout.preferredHeight: notifLayout.implicitHeight
            contentHeight: notifLayout.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: notifLayout
                width: parent.width
                spacing: 4

                // 表头
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 15
                    Layout.rightMargin: 15
                    Layout.bottomMargin: 4

                    Item { Layout.fillWidth: true }

                    Label {
                        text: _notifSystemLabel
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.preferredWidth: 50
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Label {
                        text: _notifBarkLabel
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: _barkConfigured ? Theme.currentTheme.colors.textSecondaryColor : Theme.currentTheme.colors.textTertialyColor
                        Layout.preferredWidth: 50
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                Repeater {
                    id: notifRepeater
                    model: _notifCategories

                    delegate: SettingCard {
                        Layout.fillWidth: true
                        title: modelData.title
                        icon.name: modelData.icon
                        property string notifKey: modelData.key
                        RowLayout {
                            spacing: 16
                            Switch {
                                id: notifCatSwitch
                                Component.onCompleted: {
                                    checked = Backend ? Backend.getNotificationSetting(modelData.key) : true
                                }
                                onCheckedChanged: {
                                    if (Backend) Backend.setNotificationSetting(modelData.key, checked);
                                }
                            }
                            Switch {
                                id: notifBarkSwitch
                                enabled: _barkConfigured
                                Component.onCompleted: {
                                    checked = Backend ? Backend.getNotificationSetting("bark_" + modelData.key) : true
                                }
                                onCheckedChanged: {
                                    if (Backend) Backend.setNotificationSetting("bark_" + modelData.key, checked);
                                }
                            }
                        }
                    }
                }
            }
        }

        onOpened: {
            notifMasterSwitch.checked = Backend ? Backend.getNotificationSetting("enabled") : true
            for (var i = 0; i < notifRepeater.count; i++) {
                var item = notifRepeater.itemAt(i)
                if (item) {
                    var switches = findChildSwitches(item)
                    if (switches.length >= 1) {
                        switches[0].checked = Backend ? Backend.getNotificationSetting(item.notifKey) : true
                    }
                    if (switches.length >= 2) {
                        switches[1].checked = Backend ? Backend.getNotificationSetting("bark_" + item.notifKey) : true
                        switches[1].enabled = barkUrlField.text.length > 0
                    }
                }
            }
        }

        function findChildSwitches(item) {
            var result = []
            for (var i = 0; i < item.children.length; i++) {
                var child = item.children[i]
                if (child && child.toString().indexOf("RowLayout") !== -1) {
                    for (var j = 0; j < child.children.length; j++) {
                        var grandchild = child.children[j]
                        if (grandchild && grandchild.toString().indexOf("Switch") !== -1) {
                            result.push(grandchild)
                        }
                    }
                }
            }
            return result
        }

        footer: RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                text: _notifCloseBtn
                flat: true
                onClicked: notifDialog.close()
            }
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _langTitle
            description: _langDesc
            icon.name: "ic_fluent_local_language_20_regular"
            ComboBox {
                id: langCombo
                model: languages
                textRole: "name"
                Layout.preferredWidth: 150
                onActivated: function(index) {
                    if (!Backend)
                        return;

                    var selected = (languages && index >= 0 && index < languages.length) ? languages[index] : null;
                    if (selected && selected.code)
                        Backend.setLanguage(selected.code);
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _themeTitle
            description: _themeDesc
            icon.name: "ic_fluent_color_20_regular"
            ComboBox {
                id: themeCombo
                model: ["Auto", "Light", "Dark"]
                Layout.preferredWidth: 150
                onActivated: {
                    if (Backend)
                        Backend.setThemeMode(currentText);
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _logSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _logFolderTitle
            description: _logFolderDesc
            icon.name: "ic_fluent_text_bullet_list_square_20_regular"
            Button {
                flat: true
                text: _openText
                onClicked: {
                    if (Backend)
                        Backend.openLogDir();
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            title: _clearLogTitle
            description: _clearLogDesc
            icon.name: "ic_fluent_delete_20_regular"
            Button {
                text: _clearText
                onClicked: {
                    if (Backend)
                        Backend.clearLogs();
                }
            }
        }
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _networkSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true
            title: _proxyTitle
            description: _proxyDesc
            icon.name: "ic_fluent_shield_20_regular"
            TextField {
                id: proxyField
                placeholderText: _proxyPlaceholder
                Layout.preferredWidth: 250
                text: Backend ? Backend.getProxy() : ""
                onEditingFinished: {
                    if (Backend)
                        Backend.setProxy(text);
                }
            }
        }
    }

    Label {
        text: _restartTip
        color: Theme.currentTheme.colors.textTertialyColor
        Layout.topMargin: 10
    }
}
