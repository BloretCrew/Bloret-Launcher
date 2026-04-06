import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

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
        _homeSection = Backend ? Backend.tr("首页") : "首页";
        _showAccountTitle = Backend ? Backend.tr("显示账户信息") : "显示账户信息";
        _showAccountDesc = Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息";
        _closeToTrayTitle = Backend ? Backend.tr("关闭按钮最小化到托盘") : "关闭按钮最小化到托盘";
        _closeToTrayDesc = Backend ? Backend.tr("开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序") : "开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序";
        _closeToTrayUnavailableDesc = Backend ? Backend.tr("当前平台不支持托盘") : "当前平台不支持托盘";
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
    }

    property string _versionTitle: Backend ? Backend.tr("当前版本") : "当前版本"
    property string _versionDesc: Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher"
    property string _mcJavaSection: Backend ? Backend.tr("Minecraft 与 Java") : "Minecraft 与 Java"
    property string _javaTitle: Backend ? Backend.tr("Java") : "Java"
    property string _javaDesc: Backend ? Backend.tr("选择用于启动 Minecraft 的 Java") : "选择用于启动 Minecraft 的 Java"
    property string _mcFolderTitle: Backend ? Backend.tr("Minecraft 文件夹位置") : "Minecraft 文件夹位置"
    property string _mcToolbarTitle: Backend ? Backend.tr("Minecraft 小工具栏") : "Minecraft 小工具栏"
    property string _mcToolbarDesc: Backend ? Backend.tr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏") : "当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"
    property string _homeSection: Backend ? Backend.tr("首页") : "首页"
    property string _showAccountTitle: Backend ? Backend.tr("显示账户信息") : "显示账户信息"
    property string _showAccountDesc: Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息"
    property string _closeToTrayTitle: Backend ? Backend.tr("关闭按钮最小化到托盘") : "关闭按钮最小化到托盘"
    property string _closeToTrayDesc: Backend ? Backend.tr("开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序") : "开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序"
    property string _closeToTrayUnavailableDesc: Backend ? Backend.tr("当前平台不支持托盘") : "当前平台不支持托盘"
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

            showAccountSwitch.checked = Backend.getShowAccountOnHome();
            minimizeToTraySwitch.checked = Backend.getMinimizeToTrayOnClose();
            traySupported = Backend.isSystemTrayAvailable();
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
            color: Theme.accentColor
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
            Switch {
                id: showAccountSwitch
                checked: true
                onCheckedChanged: {
                    if (Backend)
                        Backend.setShowAccountOnHome(checked);
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
    }

    Label {
        font.pixelSize: 20
        font.weight: Font.DemiBold
        text: _appearanceSection
        Layout.topMargin: 10
        color: Theme.currentTheme.colors.textColor
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
        text: _restartTip
        color: Theme.currentTheme.colors.textTertialyColor
        Layout.topMargin: 10
    }
}
