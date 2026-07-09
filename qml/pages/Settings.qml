import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI
import "../components"

FluentPage {
    id: settingsPage

    property string _title: Backend ? Backend.tr("设置") : "设置"
    title: _title

    // "" = hub (category cards); otherwise category id
    property string currentCategory: ""

    property string currentMcDir: ""
    property var javaPaths: []
    property string currentJavaPath: ""
    property string themeMode: ""
    property var languages: []
    property bool traySupported: true
    property string localIPAddress: ""

    Component.onCompleted: {
        console.log("[Settings] page loaded, showing category hub")
        refreshData()
    }

    Connections {
        target: Backend
        function onLanguageChanged() {
            refreshTranslations()
            updatePageTitle()
        }
    }

    Connections {
        target: Agent
        enabled: Agent !== null
        function onProvidersChanged() {
            console.log("[Settings] Agent providers changed, reloading")
            loadSettingsProviders()
        }
        function onErrorOccurred(msg) {
            console.log("[Settings] Agent error:", msg)
            providerInfoBar.severity = Severity.Error
            providerInfoBar.title = _providerErrorTitle
            providerInfoBar.text = msg
            providerInfoBar.visible = true
        }
    }

    function setDefaultProvider(key) {
        console.log("[Settings] set default provider:", key)
        if (Backend)
            Backend.setGlobalAIProvider(key)
        loadGlobalModels(key, "")
        // sync combo index
        for (var j = 0; j < settingsGlobalProviderModel.count; j++) {
            if (settingsGlobalProviderModel.get(j).key === key) {
                settingsGlobalProviderCombo.currentIndex = j
                break
            }
        }
        providerInfoBar.severity = Severity.Success
        providerInfoBar.title = _setAsDefaultTitle
        providerInfoBar.text = key
        providerInfoBar.visible = true
    }

    function openEditProvider(key) {
        console.log("[Settings] open edit provider:", key)
        if (!Agent) return
        try {
            var detail = JSON.parse(Agent.getProviderDetail(key))
            if (detail.error) {
                providerInfoBar.severity = Severity.Error
                providerInfoBar.title = _providerErrorTitle
                providerInfoBar.text = _providerNotFound
                providerInfoBar.visible = true
                return
            }
            settingsEditProviderDialog.editKey = detail.key || key
            settingsEditNameField.text = detail.name || ""
            settingsEditUrlField.text = detail.api || ""
            settingsEditKeyField.text = ""
            settingsEditKeyField.placeholderText = detail.has_key
                ? _keepKeyPlaceholder
                : _apiKeyPlaceholder
            var lines = []
            var models = detail.models || []
            for (var i = 0; i < models.length; i++)
                lines.push(models[i].id || models[i].name || "")
            settingsEditModelsArea.text = lines.join("\n")
            settingsEditProviderDialog.open()
        } catch (e) {
            console.log("[Settings] openEditProvider error:", e)
        }
    }

    function modelsTextToJson(text) {
        var lines = (text || "").split("\n")
        var arr = []
        for (var i = 0; i < lines.length; i++) {
            var mid = lines[i].trim()
            if (mid.length > 0 && mid.charAt(0) !== "#")
                arr.push({ id: mid, name: mid })
        }
        return JSON.stringify(arr)
    }


    function openCategory(id) {
        console.log("[Settings] open category:", id)
        currentCategory = id
        updatePageTitle()
        if (id === "ai")
            loadSettingsProviders()
    }

    function goBack() {
        console.log("[Settings] back to hub from:", currentCategory)
        currentCategory = ""
        updatePageTitle()
    }

    function updatePageTitle() {
        if (currentCategory === "") {
            _title = Backend ? Backend.tr("设置") : "设置"
            return
        }
        var catTitle = categoryTitle(currentCategory)
        _title = (Backend ? Backend.tr("设置") : "设置") + " · " + catTitle
    }

    function categoryTitle(id) {
        switch (id) {
        case "minecraft": return _mcJavaSection
        case "home": return _homeSection
        case "webremoter": return _webRemoterSection
        case "gamepad": return _gamepadSection
        case "notification": return _notificationSection
        case "appearance": return _appearanceSection
        case "log": return _logSection
        case "network": return _networkSection
        case "ai": return _aiProvidersSection
        default: return id
        }
    }

    function refreshTranslations() {
        _titleBase = Backend ? Backend.tr("设置") : "设置"
        _versionTitle = Backend ? Backend.tr("当前版本") : "当前版本"
        _versionDesc = Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher"
        _mcJavaSection = Backend ? Backend.tr("Minecraft 与 Java") : "Minecraft 与 Java"
        _mcJavaHubDesc = Backend ? Backend.tr("Java、游戏目录与下载源") : "Java、游戏目录与下载源"
        _javaTitle = Backend ? Backend.tr("Java") : "Java"
        _javaDesc = Backend ? Backend.tr("选择用于启动 Minecraft 的 Java") : "选择用于启动 Minecraft 的 Java"
        _mcFolderTitle = Backend ? Backend.tr("Minecraft 文件夹位置") : "Minecraft 文件夹位置"
        _mcToolbarTitle = Backend ? Backend.tr("Minecraft 小工具栏") : "Minecraft 小工具栏"
        _mcToolbarDesc = Backend ? Backend.tr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏") : "当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"
        _sourceTitle = Backend ? Backend.tr("下载源") : "下载源"
        _sourceDesc = Backend ? Backend.tr("选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连") : "选择下载来源：BMCLAPI（优先镜像，失败回退官方）、Bloret (以非常规方式快速下载，只支持部分版本) 或 Mojang 官方直连"
        _homeSection = Backend ? Backend.tr("首页") : "首页"
        _homeHubDesc = Backend ? Backend.tr("账户展示、托盘与多开") : "账户展示、托盘与多开"
        _showAccountTitle = Backend ? Backend.tr("显示账户信息") : "显示账户信息"
        _showAccountDesc = Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息"
        _showAccountModeCompact = Backend ? Backend.tr("简略展示") : "简略展示"
        _showAccountModeFull = Backend ? Backend.tr("完整展示") : "完整展示"
        _showAccountModeHidden = Backend ? Backend.tr("隐藏") : "隐藏"
        _webRemoterSection = Backend ? Backend.tr("Web 遥控器") : "Web 遥控器"
        _webRemoterHubDesc = Backend ? Backend.tr("手机浏览器遥控 Minecraft") : "手机浏览器遥控 Minecraft"
        _webRemoterTitle = Backend ? Backend.tr("启用 Web 遥控器") : "启用 Web 遥控器"
        _webRemoterDesc = Backend ? Backend.tr("开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft") : "开启后可通过手机浏览器访问 http://电脑IP:25252 遥控 Minecraft"
        _webRemoterQRTitle = Backend ? Backend.tr("连接二维码") : "连接二维码"
        _webRemoterQRDesc = Backend ? Backend.tr("扫描二维码快速访问遥控器页面") : "扫描二维码快速访问遥控器页面"
        _closeToTrayTitle = Backend ? Backend.tr("关闭按钮最小化到托盘") : "关闭按钮最小化到托盘"
        _closeToTrayDesc = Backend ? Backend.tr("开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序") : "开启后点击窗口关闭按钮仅隐藏到系统托盘；关闭后将直接退出程序"
        _closeToTrayUnavailableDesc = Backend ? Backend.tr("当前平台不支持托盘") : "当前平台不支持托盘"
        _repeatRunTitle = Backend ? Backend.tr("允许重复打开 Bloret Launcher") : "允许重复打开 Bloret Launcher"
        _repeatRunDesc = Backend ? Backend.tr("开启后可同时打开多个 Bloret Launcher 实例") : "开启后可同时打开多个 Bloret Launcher 实例"
        _appearanceSection = Backend ? Backend.tr("外观") : "外观"
        _appearanceHubDesc = Backend ? Backend.tr("语言与主题") : "语言与主题"
        _langTitle = Backend ? Backend.tr("语言 / language") : "语言 / language"
        _langDesc = Backend ? Backend.tr("调整语言设置") : "调整语言设置"
        _themeTitle = Backend ? Backend.tr("主题") : "主题"
        _themeDesc = Backend ? Backend.tr("选择界面的颜色模式") : "选择界面的颜色模式"
        _logSection = Backend ? Backend.tr("日志") : "日志"
        _logHubDesc = Backend ? Backend.tr("打开或清空日志文件") : "打开或清空日志文件"
        _logFolderTitle = Backend ? Backend.tr("日志文件夹位置") : "日志文件夹位置"
        _logFolderDesc = Backend ? Backend.tr("存储所有 Bloret Launcher 日志的文件夹位置") : "存储所有 Bloret Launcher 日志的文件夹位置"
        _clearLogTitle = Backend ? Backend.tr("清空日志") : "清空日志"
        _clearLogDesc = Backend ? Backend.tr("清空 log 文件夹所有的日志文件") : "清空 log 文件夹所有的日志文件"
        _browseText = Backend ? Backend.tr("浏览...") : "浏览..."
        _openText = Backend ? Backend.tr("打开") : "打开"
        _clearText = Backend ? Backend.tr("清空") : "清空"
        _restartTip = Backend ? Backend.tr("设置界面大部分内容需要重启程序后生效。") : "设置界面大部分内容需要重启程序后生效。"
        _gamepadSection = Backend ? Backend.tr("虚拟手柄") : "虚拟手柄"
        _gamepadHubDesc = Backend ? Backend.tr("移动与视角摇杆灵敏度") : "移动与视角摇杆灵敏度"
        _moveSensitivityTitle = Backend ? Backend.tr("移动摇杆灵敏度") : "移动摇杆灵敏度"
        _moveSensitivityDesc = Backend ? Backend.tr("控制移动摇杆的响应速度") : "控制移动摇杆的响应速度"
        _viewSensitivityTitle = Backend ? Backend.tr("视角摇杆灵敏度") : "视角摇杆灵敏度"
        _viewSensitivityDesc = Backend ? Backend.tr("控制视角旋转的速度") : "控制视角旋转的速度"
        _networkSection = Backend ? Backend.tr("网络") : "网络"
        _networkHubDesc = Backend ? Backend.tr("HTTP / HTTPS / SOCKS5 代理") : "HTTP / HTTPS / SOCKS5 代理"
        _notificationSection = Backend ? Backend.tr("通知") : "通知"
        _notificationHubDesc = Backend ? Backend.tr("系统通知与 Bark 推送") : "系统通知与 Bark 推送"
        _notifMasterTitle = Backend ? Backend.tr("启用系统通知") : "启用系统通知"
        _notifMasterDesc = Backend ? Backend.tr("关闭后将不再发送任何系统通知") : "关闭后将不再发送任何系统通知"
        _notifConfigTitle = Backend ? Backend.tr("通知偏好设置") : "通知偏好设置"
        _notifConfigDesc = Backend ? Backend.tr("选择要接收哪些类别的系统通知") : "选择要接收哪些类别的系统通知"
        _notifDialogTitle = Backend ? Backend.tr("通知偏好设置") : "通知偏好设置"
        _notifLaunchReady = Backend ? Backend.tr("Minecraft 启动完成") : "Minecraft 启动完成"
        _notifLaunchError = Backend ? Backend.tr("启动失败 / 崩溃 / 超时") : "启动失败 / 崩溃 / 超时"
        _notifDownload = Backend ? Backend.tr("下载完成及失败") : "下载完成及失败"
        _notifInstall = Backend ? Backend.tr("安装完成及失败") : "安装完成及失败"
        _notifUpdate = Backend ? Backend.tr("应用更新") : "应用更新"
        _notifChatMessage = Backend ? Backend.tr("Minecraft 聊天消息") : "Minecraft 聊天消息"
        _notifCopilot = Backend ? Backend.tr("Copilot Agent") : "Copilot Agent"
        _notifBloriko = Backend ? Backend.tr("络可 Agent") : "络可 Agent"
        _notifAccount = Backend ? Backend.tr("账户登录 / 同步") : "账户登录 / 同步"
        _notifConfigBtn = Backend ? Backend.tr("配置通知...") : "配置通知..."
        _notifCloseBtn = Backend ? Backend.tr("关闭") : "关闭"
        _barkTitle = Backend ? Backend.tr("Bark 推送") : "Bark 推送"
        _barkDesc = Backend ? Backend.tr("配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备") : "配置 Bark 终结点 URL，启用后可将通知推送到 iOS 设备"
        _barkPlaceholder = Backend ? Backend.tr("https://api.day.app/your_device_key") : "https://api.day.app/your_device_key"
        _notifSystemLabel = Backend ? Backend.tr("系统") : "系统"
        _notifBarkLabel = Backend ? Backend.tr("Bark") : "Bark"
        _barkTestBtn = Backend ? Backend.tr("测试") : "测试"
        _barkTestSuccess = Backend ? Backend.tr("Bark 推送测试成功") : "Bark 推送测试成功"
        _barkTestFail = Backend ? Backend.tr("Bark 推送测试失败") : "Bark 推送测试失败"
        _proxyTitle = Backend ? Backend.tr("网络代理") : "网络代理"
        _proxyDesc = Backend ? Backend.tr("设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理") : "设置 HTTP/HTTPS/SOCKS5 代理地址，如 http://127.0.0.1:7890，留空表示不使用代理"
        _proxyPlaceholder = Backend ? Backend.tr("不使用代理") : "不使用代理"
        _aiProvidersSection = Backend ? Backend.tr("AI 供应商") : "AI 供应商"
        _aiHubDesc = Backend ? Backend.tr("默认模型与自定义供应商") : "默认模型与自定义供应商"
        _aiProvidersTitle = Backend ? Backend.tr("AI 供应商管理") : "AI 供应商管理"
        _aiProvidersDesc = Backend ? Backend.tr("管理自定义 AI 供应商，添加后可在资源包编辑器 Copilot 中使用") : "管理自定义 AI 供应商，添加后可在资源包编辑器 Copilot 中使用"
        _addProviderBtn = Backend ? Backend.tr("添加供应商") : "添加供应商"
        _addProviderDialogTitle = Backend ? Backend.tr("添加 AI 供应商") : "添加 AI 供应商"
        _selectProviderLabel = Backend ? Backend.tr("选择 AI 供应商：") : "选择 AI 供应商："
        _searchPlaceholder = Backend ? Backend.tr("搜索...") : "搜索..."
        _loadingText = Backend ? Backend.tr("加载中...") : "加载中..."
        _apiKeyLabel = Backend ? Backend.tr("请输入 API 密钥：") : "请输入 API 密钥："
        _apiKeyPlaceholder = Backend ? Backend.tr("sk-...") : "sk-..."
        _apiKeyNotice = Backend ? Backend.tr("密钥保存在本地，仅用于请求 AI 服务。") : "密钥保存在本地，仅用于请求 AI 服务。"
        _addBtn = Backend ? Backend.tr("添加") : "添加"
        _cancelBtn = Backend ? Backend.tr("取消") : "取消"
        _backBtn = Backend ? Backend.tr("返回") : "返回"
        _builtinLabel = Backend ? Backend.tr("内置") : "内置"
        _customLabel = Backend ? Backend.tr("自定义") : "自定义"
        _removeProviderTooltip = Backend ? Backend.tr("删除此供应商") : "删除此供应商"
        _chooseCategoryHint = Backend ? Backend.tr("选择一个类别以管理相关设置") : "选择一个类别以管理相关设置"
        _defaultAIProviderTitle = Backend ? Backend.tr("默认 AI 供应商") : "默认 AI 供应商"
        _defaultAIProviderDesc = Backend ? Backend.tr("选择所有 AI 功能使用的供应商和模型") : "选择所有 AI 功能使用的供应商和模型"
        _providerErrorTitle = Backend ? Backend.tr("供应商错误") : "供应商错误"
        _setAsDefaultTitle = Backend ? Backend.tr("已设为默认") : "已设为默认"
        _providerNotFound = Backend ? Backend.tr("未找到供应商") : "未找到供应商"
        _keepKeyPlaceholder = Backend ? Backend.tr("留空则不修改密钥") : "留空则不修改密钥"
        _agentNotReady = Backend ? Backend.tr("AI 后端未就绪，无法管理供应商") : "AI 后端未就绪，无法管理供应商"
        _setDefaultBtn = Backend ? Backend.tr("默认") : "默认"
        _editBtn = Backend ? Backend.tr("编辑") : "编辑"
        _deleteBtn = Backend ? Backend.tr("删除") : "删除"
        _deletedTitle = Backend ? Backend.tr("已删除") : "已删除"
        _addFromCatalog = Backend ? Backend.tr("从目录添加") : "从目录添加"
        _addManually = Backend ? Backend.tr("手动添加") : "手动添加"
        _manualProviderTitle = Backend ? Backend.tr("手动添加 OpenAI 兼容供应商") : "手动添加 OpenAI 兼容供应商"
        _providerIdLabel = Backend ? Backend.tr("供应商 ID（唯一标识）") : "供应商 ID（唯一标识）"
        _displayNameLabel = Backend ? Backend.tr("显示名称") : "显示名称"
        _apiBaseUrlLabel = Backend ? Backend.tr("API Base URL") : "API Base URL"
        _modelsListLabel = Backend ? Backend.tr("模型列表（每行一个模型 ID）") : "模型列表（每行一个模型 ID）"
        _addSuccessTitle = Backend ? Backend.tr("添加成功") : "添加成功"
        _editProviderTitle = Backend ? Backend.tr("编辑供应商") : "编辑供应商"
        _providerIdPrefix = Backend ? Backend.tr("供应商 ID: ") : "供应商 ID: "
        _providerColonPrefix = Backend ? Backend.tr("供应商: ") : "供应商: "
        _saveBtn = Backend ? Backend.tr("保存") : "保存"
        _savedTitle = Backend ? Backend.tr("已保存") : "已保存"
        _modelsSuffix = Backend ? Backend.tr(" 模型") : " 模型"
        _modelsDotSuffix = Backend ? Backend.tr(" 模型 · ") : " 模型 · "
        _noProvidersYet = Backend ? Backend.tr("暂无已添加的供应商") : "暂无已添加的供应商"
        updatePageTitle()
    }

    property string _titleBase: Backend ? Backend.tr("设置") : "设置"
    property string _versionTitle: Backend ? Backend.tr("当前版本") : "当前版本"
    property string _versionDesc: Backend ? Backend.tr("Bloret Launcher") : "Bloret Launcher"
    property string _mcJavaSection: Backend ? Backend.tr("Minecraft 与 Java") : "Minecraft 与 Java"
    property string _mcJavaHubDesc: Backend ? Backend.tr("Java、游戏目录与下载源") : "Java、游戏目录与下载源"
    property string _javaTitle: Backend ? Backend.tr("Java") : "Java"
    property string _javaDesc: Backend ? Backend.tr("选择用于启动 Minecraft 的 Java") : "选择用于启动 Minecraft 的 Java"
    property string _mcFolderTitle: Backend ? Backend.tr("Minecraft 文件夹位置") : "Minecraft 文件夹位置"
    property string _mcToolbarTitle: Backend ? Backend.tr("Minecraft 小工具栏") : "Minecraft 小工具栏"
    property string _mcToolbarDesc: Backend ? Backend.tr("当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏") : "当游玩 Minecraft 时，在 Minecraft 窗口上方显示快捷小工具栏"
    property string _sourceTitle: Backend ? Backend.tr("下载源") : "下载源"
    property string _sourceDesc: Backend ? Backend.tr("选择下载来源：Bloret (以非常规方式快速下载，只支持部分版本)、Mojang 官方直连 或 BMCLAPI（优先镜像，失败回退官方）") : "选择下载来源：Bloret (以非常规方式快速下载，只支持部分版本)、Mojang 官方直连 或 BMCLAPI（优先镜像，失败回退官方）"
    property string _homeSection: Backend ? Backend.tr("首页") : "首页"
    property string _homeHubDesc: Backend ? Backend.tr("账户展示、托盘与多开") : "账户展示、托盘与多开"
    property string _showAccountTitle: Backend ? Backend.tr("显示账户信息") : "显示账户信息"
    property string _showAccountDesc: Backend ? Backend.tr("在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息") : "在首页启动卡片上显示 Bloret PassPort 和 Minecraft 账户信息"
    property string _showAccountModeCompact: Backend ? Backend.tr("简略展示") : "简略展示"
    property string _showAccountModeFull: Backend ? Backend.tr("完整展示") : "完整展示"
    property string _showAccountModeHidden: Backend ? Backend.tr("隐藏") : "隐藏"
    property string _webRemoterSection: Backend ? Backend.tr("Web 遥控器") : "Web 遥控器"
    property string _webRemoterHubDesc: Backend ? Backend.tr("手机浏览器遥控 Minecraft") : "手机浏览器遥控 Minecraft"
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
    property string _appearanceHubDesc: Backend ? Backend.tr("语言与主题") : "语言与主题"
    property string _langTitle: Backend ? Backend.tr("语言 / language") : "语言 / language"
    property string _langDesc: Backend ? Backend.tr("调整语言设置") : "调整语言设置"
    property string _themeTitle: Backend ? Backend.tr("主题") : "主题"
    property string _themeDesc: Backend ? Backend.tr("选择界面的颜色模式") : "选择界面的颜色模式"
    property string _logSection: Backend ? Backend.tr("日志") : "日志"
    property string _logHubDesc: Backend ? Backend.tr("打开或清空日志文件") : "打开或清空日志文件"
    property string _logFolderTitle: Backend ? Backend.tr("日志文件夹位置") : "日志文件夹位置"
    property string _logFolderDesc: Backend ? Backend.tr("存储所有 Bloret Launcher 日志的文件夹位置") : "存储所有 Bloret Launcher 日志的文件夹位置"
    property string _clearLogTitle: Backend ? Backend.tr("清空日志") : "清空日志"
    property string _clearLogDesc: Backend ? Backend.tr("清空 log 文件夹所有的日志文件") : "清空 log 文件夹所有的日志文件"
    property string _browseText: Backend ? Backend.tr("浏览...") : "浏览..."
    property string _openText: Backend ? Backend.tr("打开") : "打开"
    property string _clearText: Backend ? Backend.tr("清空") : "清空"
    property string _restartTip: Backend ? Backend.tr("设置界面大部分内容需要重启程序后生效。") : "设置界面大部分内容需要重启程序后生效。"
    property string _gamepadSection: Backend ? Backend.tr("虚拟手柄") : "虚拟手柄"
    property string _gamepadHubDesc: Backend ? Backend.tr("移动与视角摇杆灵敏度") : "移动与视角摇杆灵敏度"
    property string _moveSensitivityTitle: Backend ? Backend.tr("移动摇杆灵敏度") : "移动摇杆灵敏度"
    property string _moveSensitivityDesc: Backend ? Backend.tr("控制移动摇杆的响应速度") : "控制移动摇杆的响应速度"
    property string _viewSensitivityTitle: Backend ? Backend.tr("视角摇杆灵敏度") : "视角摇杆灵敏度"
    property string _viewSensitivityDesc: Backend ? Backend.tr("控制视角旋转的速度") : "控制视角旋转的速度"
    property string _networkSection: Backend ? Backend.tr("网络") : "网络"
    property string _networkHubDesc: Backend ? Backend.tr("HTTP / HTTPS / SOCKS5 代理") : "HTTP / HTTPS / SOCKS5 代理"
    property string _notificationSection: Backend ? Backend.tr("通知") : "通知"
    property string _notificationHubDesc: Backend ? Backend.tr("系统通知与 Bark 推送") : "系统通知与 Bark 推送"
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
    property string _notifBloriko: Backend ? Backend.tr("络可 Agent") : "络可 Agent"
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
    property string _aiProvidersSection: Backend ? Backend.tr("AI 供应商") : "AI 供应商"
    property string _aiHubDesc: Backend ? Backend.tr("默认模型与自定义供应商") : "默认模型与自定义供应商"
    property string _aiProvidersTitle: Backend ? Backend.tr("AI 供应商管理") : "AI 供应商管理"
    property string _aiProvidersDesc: Backend ? Backend.tr("管理自定义 AI 供应商，添加后可在资源包编辑器 Copilot 中使用") : "管理自定义 AI 供应商，添加后可在资源包编辑器 Copilot 中使用"
    property string _addProviderBtn: Backend ? Backend.tr("添加供应商") : "添加供应商"
    property string _addProviderDialogTitle: Backend ? Backend.tr("添加 AI 供应商") : "添加 AI 供应商"
    property string _selectProviderLabel: Backend ? Backend.tr("选择 AI 供应商：") : "选择 AI 供应商："
    property string _searchPlaceholder: Backend ? Backend.tr("搜索...") : "搜索..."
    property string _loadingText: Backend ? Backend.tr("加载中...") : "加载中..."
    property string _apiKeyLabel: Backend ? Backend.tr("请输入 API 密钥：") : "请输入 API 密钥："
    property string _apiKeyPlaceholder: Backend ? Backend.tr("sk-...") : "sk-..."
    property string _apiKeyNotice: Backend ? Backend.tr("密钥保存在本地，仅用于请求 AI 服务。") : "密钥保存在本地，仅用于请求 AI 服务。"
    property string _addBtn: Backend ? Backend.tr("添加") : "添加"
    property string _cancelBtn: Backend ? Backend.tr("取消") : "取消"
    property string _backBtn: Backend ? Backend.tr("返回") : "返回"
    property string _builtinLabel: Backend ? Backend.tr("内置") : "内置"
    property string _customLabel: Backend ? Backend.tr("自定义") : "自定义"
    property string _removeProviderTooltip: Backend ? Backend.tr("删除此供应商") : "删除此供应商"
    property string _chooseCategoryHint: Backend ? Backend.tr("选择一个类别以管理相关设置") : "选择一个类别以管理相关设置"
    property string _defaultAIProviderTitle: Backend ? Backend.tr("默认 AI 供应商") : "默认 AI 供应商"
    property string _defaultAIProviderDesc: Backend ? Backend.tr("选择所有 AI 功能使用的供应商和模型") : "选择所有 AI 功能使用的供应商和模型"
    property string _providerErrorTitle: Backend ? Backend.tr("供应商错误") : "供应商错误"
    property string _setAsDefaultTitle: Backend ? Backend.tr("已设为默认") : "已设为默认"
    property string _providerNotFound: Backend ? Backend.tr("未找到供应商") : "未找到供应商"
    property string _keepKeyPlaceholder: Backend ? Backend.tr("留空则不修改密钥") : "留空则不修改密钥"
    property string _agentNotReady: Backend ? Backend.tr("AI 后端未就绪，无法管理供应商") : "AI 后端未就绪，无法管理供应商"
    property string _setDefaultBtn: Backend ? Backend.tr("默认") : "默认"
    property string _editBtn: Backend ? Backend.tr("编辑") : "编辑"
    property string _deleteBtn: Backend ? Backend.tr("删除") : "删除"
    property string _deletedTitle: Backend ? Backend.tr("已删除") : "已删除"
    property string _addFromCatalog: Backend ? Backend.tr("从目录添加") : "从目录添加"
    property string _addManually: Backend ? Backend.tr("手动添加") : "手动添加"
    property string _manualProviderTitle: Backend ? Backend.tr("手动添加 OpenAI 兼容供应商") : "手动添加 OpenAI 兼容供应商"
    property string _providerIdLabel: Backend ? Backend.tr("供应商 ID（唯一标识）") : "供应商 ID（唯一标识）"
    property string _displayNameLabel: Backend ? Backend.tr("显示名称") : "显示名称"
    property string _apiBaseUrlLabel: Backend ? Backend.tr("API Base URL") : "API Base URL"
    property string _modelsListLabel: Backend ? Backend.tr("模型列表（每行一个模型 ID）") : "模型列表（每行一个模型 ID）"
    property string _addSuccessTitle: Backend ? Backend.tr("添加成功") : "添加成功"
    property string _editProviderTitle: Backend ? Backend.tr("编辑供应商") : "编辑供应商"
    property string _providerIdPrefix: Backend ? Backend.tr("供应商 ID: ") : "供应商 ID: "
    property string _providerColonPrefix: Backend ? Backend.tr("供应商: ") : "供应商: "
    property string _saveBtn: Backend ? Backend.tr("保存") : "保存"
    property string _savedTitle: Backend ? Backend.tr("已保存") : "已保存"
    property string _modelsSuffix: Backend ? Backend.tr(" 模型") : " 模型"
    property string _modelsDotSuffix: Backend ? Backend.tr(" 模型 · ") : " 模型 · "
    property string _noProvidersYet: Backend ? Backend.tr("暂无已添加的供应商") : "暂无已添加的供应商"

    // Category cards model for hub
    property var categoryCards: [
        { id: "minecraft", title: _mcJavaSection, desc: _mcJavaHubDesc, icon: "ic_fluent_cube_20_regular" },
        { id: "home", title: _homeSection, desc: _homeHubDesc, icon: "ic_fluent_home_20_regular" },
        { id: "webremoter", title: _webRemoterSection, desc: _webRemoterHubDesc, icon: "ic_fluent_phone_20_regular" },
        { id: "gamepad", title: _gamepadSection, desc: _gamepadHubDesc, icon: "ic_fluent_xbox_controller_20_regular" },
        { id: "notification", title: _notificationSection, desc: _notificationHubDesc, icon: "ic_fluent_alert_20_regular" },
        { id: "appearance", title: _appearanceSection, desc: _appearanceHubDesc, icon: "ic_fluent_color_20_regular" },
        { id: "log", title: _logSection, desc: _logHubDesc, icon: "ic_fluent_text_bullet_list_square_20_regular" },
        { id: "network", title: _networkSection, desc: _networkHubDesc, icon: "ic_fluent_globe_20_regular" },
        { id: "ai", title: _aiProvidersSection, desc: _aiHubDesc, icon: "ic_fluent_bot_20_regular" }
    ]

    ListModel { id: settingsProviderModel }
    ListModel { id: settingsGlobalProviderModel }
    ListModel { id: settingsGlobalModelModel }

    function loadSettingsProviders() {
        console.log("[Settings] loadSettingsProviders")
        settingsProviderModel.clear()
        settingsGlobalProviderModel.clear()
        settingsGlobalModelModel.clear()
        if (!Agent) {
            console.log("[Settings] Agent is null, skip loading providers")
            return
        }
        try {
            var providers = JSON.parse(Agent.getProviders())
            console.log("[Settings] loaded providers count:", providers.length)
            for (var i = 0; i < providers.length; i++) {
                settingsProviderModel.append(providers[i])
                settingsGlobalProviderModel.append(providers[i])
            }
            if (Backend) {
                var globalProvider = Backend.getGlobalAIProvider()
                var globalModel = Backend.getGlobalAIModel()
                for (var j = 0; j < settingsGlobalProviderModel.count; j++) {
                    if (settingsGlobalProviderModel.get(j).key === globalProvider) {
                        settingsGlobalProviderCombo.currentIndex = j
                        loadGlobalModels(globalProvider, globalModel)
                        break
                    }
                }
            }
        } catch (e) {
            console.log("[Settings] loadSettingsProviders error:", e)
        }
    }

    function loadGlobalModels(providerKey, selectedModel) {
        console.log("[Settings] loadGlobalModels for:", providerKey)
        settingsGlobalModelModel.clear()
        if (!Agent) return
        try {
            var models = JSON.parse(Agent.getModelsFor(providerKey))
            for (var i = 0; i < models.length; i++)
                settingsGlobalModelModel.append(models[i])
            if (selectedModel) {
                for (var j = 0; j < settingsGlobalModelModel.count; j++) {
                    if (settingsGlobalModelModel.get(j).id === selectedModel) {
                        settingsGlobalModelCombo.currentIndex = j
                        break
                    }
                }
            }
            if (settingsGlobalModelCombo.currentIndex < 0 && settingsGlobalModelModel.count > 0)
                settingsGlobalModelCombo.currentIndex = 0
        } catch (e) {
            console.log("[Settings] loadGlobalModels error:", e)
        }
    }

    function refreshData() {
        refreshTranslations()
        loadSettingsProviders()
        if (Backend) {
            currentMcDir = Backend.getMinecraftDir()
            javaPaths = Backend.getSystemJavas()
            currentJavaPath = Backend.getCurrentJavaPath()
            themeMode = Backend.getThemeMode()

            if (javaPaths.indexOf("Auto") === -1)
                javaPaths.unshift("Auto")

            javaCombo.currentIndex = javaPaths.indexOf(currentJavaPath)
            if (javaCombo.currentIndex === -1) {
                javaPaths.push(currentJavaPath)
                javaCombo.currentIndex = javaPaths.length - 1
            }

            themeCombo.currentIndex = ["Auto", "Light", "Dark"].indexOf(themeMode)

            languages = Backend.getLanguages()
            for (var i = 0; i < languages.length; i++) {
                if (languages[i].code === Backend.getLanguageCode()) {
                    langCombo.currentIndex = i
                    break
                }
            }

            showAccountCombo.currentIndex = ["compact", "full", "hidden"].indexOf(Backend.getShowAccountOnHome())
            minimizeToTraySwitch.checked = Backend.getMinimizeToTrayOnClose()
            traySupported = Backend.isSystemTrayAvailable()
            repeatRunSwitch.checked = Backend.getRepeatRun()
            webRemoterSwitch.checked = Backend.getWebRemoterEnabled()
            localIPAddress = Backend.getLocalIPAddress()
            notifMasterSwitch.checked = Backend.getNotificationSetting("enabled")
            barkUrlField.text = Backend.getBarkUrl()
            console.log("[Settings] refreshData done, mcDir=", currentMcDir, "java=", currentJavaPath)
        }
    }

    // ========== HUB: category cards ==========
    ColumnLayout {
        id: hubView
        Layout.fillWidth: true
        spacing: 12
        visible: currentCategory === ""

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
            text: _chooseCategoryHint
            font.pixelSize: 13
            color: Theme.currentTheme.colors.textSecondaryColor
            Layout.topMargin: 4
        }

        Flow {
            id: categoryFlow
            Layout.fillWidth: true
            spacing: 12

            Repeater {
                model: categoryCards

                Frame {
                    id: catCard
                    width: {
                        var w = categoryFlow.width
                        if (w <= 0) return 280
                        // two columns when wide enough
                        if (w >= 560)
                            return Math.floor((w - categoryFlow.spacing) / 2)
                        return w
                    }
                    padding: 16
                    hoverable: false  // hover driven by content MouseArea below

                    property string catId: modelData.id

                    contentItem: Item {
                        implicitWidth: catRow.implicitWidth
                        implicitHeight: Math.max(catRow.implicitHeight, 48)

                        RowLayout {
                            id: catRow
                            anchors.fill: parent
                            spacing: 14

                            Icon {
                                name: modelData.icon
                                size: 28
                                Layout.alignment: Qt.AlignVCenter
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: modelData.title
                                    font.pixelSize: 15
                                    font.weight: Font.DemiBold
                                    color: Theme.currentTheme.colors.textColor
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.desc
                                    font.pixelSize: 12
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }

                            Icon {
                                name: "ic_fluent_chevron_right_20_regular"
                                size: 16
                                Layout.alignment: Qt.AlignVCenter
                                color: Theme.currentTheme.colors.textSecondaryColor
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            z: 10
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: catCard.hover = true
                            onExited: catCard.hover = false
                            onClicked: {
                                console.log("[Settings] category card clicked:", catCard.catId)
                                settingsPage.openCategory(catCard.catId)
                            }
                        }
                    }
                }
            }
        }

        Label {
            text: _restartTip
            color: Theme.currentTheme.colors.textTertialyColor
            Layout.topMargin: 8
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }

    // ========== DETAIL: back + category content ==========
    ColumnLayout {
        id: detailView
        Layout.fillWidth: true
        spacing: 12
        visible: currentCategory !== ""

        // Back bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                flat: true
                text: _backBtn
                icon.name: "ic_fluent_arrow_left_20_regular"
                onClicked: settingsPage.goBack()
            }

            Label {
                text: settingsPage.categoryTitle(currentCategory)
                font.pixelSize: 18
                font.weight: Font.DemiBold
                color: Theme.currentTheme.colors.textColor
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
        }

        // --- Minecraft & Java ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "minecraft"

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
                            Backend.setCurrentJavaPath(currentText)
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
                                var path = Backend.browseMinecraftDir()
                                if (path !== "")
                                    currentMcDir = path
                            }
                        }
                    }
                    Button {
                        flat: true
                        text: _openText
                        onClicked: {
                            if (Backend)
                                Backend.openMinecraftDir()
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
                        { text: qsTr("Bloret"), value: "gitcode" },
                        { text: qsTr("Mojang"), value: "official" },
                        { text: qsTr("BMCLAPI"), value: "bmclapi" }
                    ]
                    textRole: "text"
                    valueRole: "value"
                    currentIndex: {
                        if (!Backend) return 0
                        var src = Backend.getDownloadSource()
                        for (var i = 0; i < sourceCombo.model.length; i++) {
                            if (sourceCombo.model[i].value === src)
                                return i
                        }
                        return 0
                    }
                    onCurrentValueChanged: {
                        if (Backend)
                            Backend.setDownloadSource(currentValue)
                    }
                }
            }
        }

        // --- Home ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "home"

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
                            Backend.setShowAccountOnHome(currentValue)
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
                            Backend.setMinimizeToTrayOnClose(checked)
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
                            Backend.setRepeatRun(checked)
                    }
                }
            }
        }

        // --- Web remoter ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "webremoter"

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
                            Backend.setWebRemoterEnabled(checked)
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

        // --- Gamepad ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "gamepad"

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
                            if (Backend) Backend.setGamepadMoveSensitivity(value)
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
                            if (Backend) Backend.setGamepadViewSensitivity(value)
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

        // --- Notification ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "notification"

            SettingCard {
                Layout.fillWidth: true
                title: _notifMasterTitle
                description: _notifMasterDesc
                icon.name: "ic_fluent_alert_20_regular"
                Switch {
                    id: notifMasterSwitch
                    checked: true
                    onCheckedChanged: {
                        if (Backend) Backend.setNotificationSetting("enabled", checked)
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
                            if (Backend) Backend.setBarkUrl(text)
                        }
                    }
                    Button {
                        text: _barkTestBtn
                        enabled: barkUrlField.text.length > 0
                        onClicked: {
                            if (Backend) {
                                var result = Backend.testBark()
                                var successText = Backend.tr("发送成功")
                                barkTestInfoBar.severity = result === successText || result === "发送成功" ? Severity.Success : Severity.Error
                                barkTestInfoBar.title = (result === successText || result === "发送成功") ? _barkTestSuccess : _barkTestFail
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

        // --- Appearance ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "appearance"

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
                            return
                        var selected = (languages && index >= 0 && index < languages.length) ? languages[index] : null
                        if (selected && selected.code)
                            Backend.setLanguage(selected.code)
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
                            Backend.setThemeMode(currentText)
                    }
                }
            }
        }

        // --- Log ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "log"

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
                            Backend.openLogDir()
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
                            Backend.clearLogs()
                    }
                }
            }
        }

        // --- Network ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "network"

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
                            Backend.setProxy(text)
                    }
                }
            }
        }

        // --- AI providers ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: currentCategory === "ai"

            InfoBar {
                id: providerInfoBar
                Layout.fillWidth: true
                visible: false
                timeout: 5000
            }

            SettingCard {
                Layout.fillWidth: true
                title: _defaultAIProviderTitle
                description: _defaultAIProviderDesc
                icon.name: "ic_fluent_bot_settings_20_regular"
                RowLayout {
                    spacing: 8
                    ComboBox {
                        id: settingsGlobalProviderCombo
                        Layout.preferredWidth: 140
                        model: settingsGlobalProviderModel
                        textRole: "name"
                        font.pixelSize: 10
                        onActivated: function(index) {
                            var item = settingsGlobalProviderModel.get(index)
                            if (Backend) Backend.setGlobalAIProvider(item.key)
                            loadGlobalModels(item.key, "")
                        }
                    }
                    ComboBox {
                        id: settingsGlobalModelCombo
                        Layout.preferredWidth: 200
                        model: settingsGlobalModelModel
                        textRole: "name"
                        font.pixelSize: 10
                        onActivated: function(index) {
                            if (settingsGlobalModelModel.count > 0 && Backend)
                                Backend.setGlobalAIModel(settingsGlobalModelModel.get(index).id)
                        }
                    }
                }
            }

            SettingCard {
                Layout.fillWidth: true
                title: _aiProvidersTitle
                description: _aiProvidersDesc
                icon.name: "ic_fluent_bot_20_regular"
                Button {
                    text: _addProviderBtn
                    highlighted: true
                    enabled: Agent !== null
                    onClicked: {
                        console.log("[Settings] open add provider dialog")
                        settingsAddProviderDialog.open()
                    }
                }
            }

            Label {
                visible: Agent === null
                text: _agentNotReady
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            Repeater {
                model: settingsProviderModel
                delegate: SettingCard {
                    Layout.fillWidth: true
                    title: model.name
                    description: (model.builtin ? _builtinLabel : _customLabel)
                        + " · " + model.model_count + _modelsSuffix
                        + (model.builtin ? "" : (model.has_key ? " · ✓" : ""))
                    icon.name: model.builtin ? "ic_fluent_bot_20_regular" : "ic_fluent_person_20_regular"
                    RowLayout {
                        spacing: 4
                        Button {
                            flat: true
                            text: _setDefaultBtn
                            font.pixelSize: 11
                            onClicked: settingsPage.setDefaultProvider(model.key)
                        }
                        Button {
                            flat: true
                            text: _editBtn
                            font.pixelSize: 11
                            visible: !model.builtin
                            onClicked: settingsPage.openEditProvider(model.key)
                        }
                        Button {
                            flat: true
                            text: _deleteBtn
                            font.pixelSize: 11
                            visible: !model.builtin
                            onClicked: {
                                if (Agent) {
                                    console.log("[Settings] remove provider:", model.key)
                                    if (Agent.removeProvider(model.key)) {
                                        loadSettingsProviders()
                                        providerInfoBar.severity = Severity.Success
                                        providerInfoBar.title = _deletedTitle
                                        providerInfoBar.text = model.name
                                        providerInfoBar.visible = true
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Label {
                visible: settingsProviderModel.count === 0
                text: _noProvidersYet
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 8
                Layout.bottomMargin: 8
            }
        }

        Label {
            text: _restartTip
            color: Theme.currentTheme.colors.textTertialyColor
            Layout.topMargin: 8
            wrapMode: Text.Wrap
            Layout.fillWidth: true
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
        { key: "bloriko", title: _notifBloriko, icon: "ic_fluent_bot_20_regular" },
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
                                    if (Backend) Backend.setNotificationSetting(modelData.key, checked)
                                }
                            }
                            Switch {
                                id: notifBarkSwitch
                                enabled: _barkConfigured
                                Component.onCompleted: {
                                    checked = Backend ? Backend.getNotificationSetting("bark_" + modelData.key) : true
                                }
                                onCheckedChanged: {
                                    if (Backend) Backend.setNotificationSetting("bark_" + modelData.key, checked)
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
                    if (switches.length >= 1)
                        switches[0].checked = Backend ? Backend.getNotificationSetting(item.notifKey) : true
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
                        if (grandchild && grandchild.toString().indexOf("Switch") !== -1)
                            result.push(grandchild)
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

    Dialog {
        id: settingsAddProviderDialog
        title: _addProviderDialogTitle
        modal: true
        width: 520
        closePolicy: Popup.CloseOnEscape
        // mode: "catalog" | "manual"
        property string mode: "catalog"
        property int step: 1

        ListModel { id: settingsModelsDevModel }
        ListModel { id: settingsFilteredModel }
        property string apiStep2Id: ""

        onOpened: {
            console.log("[Settings] add provider dialog opened, mode=", mode)
            step = 1
            mode = "catalog"
            settingsApiKeyField.text = ""
            settingsProviderSearchField.text = ""
            apiStep2Id = ""
            settingsManualIdField.text = ""
            settingsManualNameField.text = ""
            settingsManualUrlField.text = "https://api.openai.com/v1"
            settingsManualKeyField.text = ""
            settingsManualModelsArea.text = ""
            settingsLoadLabel.visible = true
            settingsModelsDevModel.clear()
            settingsFilteredModel.clear()
            loadCatalogProviders()
        }

        function loadCatalogProviders() {
            settingsLoadLabel.visible = true
            Qt.callLater(function() {
                try {
                    if (!Agent) return
                    var json = Agent.fetchModelsDev()
                    var providers = JSON.parse(json)
                    settingsModelsDevModel.clear()
                    for (var i = 0; i < providers.length; i++)
                        settingsModelsDevModel.append(providers[i])
                    filterProv()
                    console.log("[Settings] models.dev providers loaded:", providers.length)
                } catch (e) {
                    console.log("[Settings] fetchModelsDev error:", e)
                }
                settingsLoadLabel.visible = false
            })
        }

        function filterProv() {
            settingsFilteredModel.clear()
            var q = settingsProviderSearchField.text.toLowerCase()
            for (var i = 0; i < settingsModelsDevModel.count; i++) {
                var item = settingsModelsDevModel.get(i)
                if (q === "" || item.name.toLowerCase().indexOf(q) >= 0 || item.id.toLowerCase().indexOf(q) >= 0)
                    settingsFilteredModel.append(item)
            }
        }

        contentItem: ColumnLayout {
            spacing: 12

            // Mode switch
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    text: _addFromCatalog
                    highlighted: settingsAddProviderDialog.mode === "catalog"
                    flat: settingsAddProviderDialog.mode !== "catalog"
                    onClicked: {
                        settingsAddProviderDialog.mode = "catalog"
                        settingsAddProviderDialog.step = 1
                        if (settingsModelsDevModel.count === 0)
                            settingsAddProviderDialog.loadCatalogProviders()
                    }
                }
                Button {
                    text: _addManually
                    highlighted: settingsAddProviderDialog.mode === "manual"
                    flat: settingsAddProviderDialog.mode !== "manual"
                    onClicked: {
                        settingsAddProviderDialog.mode = "manual"
                        settingsAddProviderDialog.step = 1
                    }
                }
            }

            // ===== Catalog: step 1 =====
            ColumnLayout {
                visible: settingsAddProviderDialog.mode === "catalog" && settingsAddProviderDialog.step === 1
                spacing: 10
                Layout.fillWidth: true

                Text {
                    text: _selectProviderLabel
                    font.pixelSize: 13
                    font.bold: true
                    color: Theme.currentTheme.colors.textColor
                }

                TextField {
                    id: settingsProviderSearchField
                    Layout.fillWidth: true
                    placeholderText: _searchPlaceholder
                    font.pixelSize: 12
                    visible: !settingsLoadLabel.visible
                    clearEnabled: true
                    onTextChanged: settingsAddProviderDialog.filterProv()
                }

                Text {
                    id: settingsLoadLabel
                    text: _loadingText
                    font.pixelSize: 11
                    color: Theme.currentTheme.colors.textSecondaryColor
                    visible: false
                }

                Frame {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(Math.max(settingsFilteredModel.count, 1) * 40 + 8, 280)
                    visible: settingsFilteredModel.count > 0
                    background: Rectangle {
                        radius: 6
                        color: Theme.currentTheme.colors.cardColor || "#FFF"
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1
                    }

                    contentItem: ListView {
                        id: settingsProvLV
                        clip: true
                        model: settingsFilteredModel
                        delegate: ItemDelegate {
                            width: settingsProvLV.width
                            height: 36
                            contentItem: Column {
                                spacing: 0
                                anchors.leftMargin: 8
                                Text {
                                    text: model.name
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: Theme.currentTheme.colors.textColor
                                }
                                Text {
                                    text: model.model_count + _modelsDotSuffix + model.id
                                    font.pixelSize: 10
                                    color: Theme.currentTheme.colors.textSecondaryColor
                                }
                            }
                            onClicked: {
                                settingsAddProviderDialog.apiStep2Id = model.id
                                settingsAddProviderDialog.step = 2
                                settingsApiKeyField.forceActiveFocus()
                            }
                        }
                    }
                }
            }

            // ===== Catalog: step 2 =====
            ColumnLayout {
                visible: settingsAddProviderDialog.mode === "catalog" && settingsAddProviderDialog.step === 2
                spacing: 10
                Layout.fillWidth: true

                Text {
                    text: _providerColonPrefix + settingsAddProviderDialog.apiStep2Id
                    font.pixelSize: 13
                    font.bold: true
                    color: Theme.currentTheme.colors.textColor
                }

                Text {
                    text: _apiKeyLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }

                TextField {
                    id: settingsApiKeyField
                    Layout.fillWidth: true
                    placeholderText: _apiKeyPlaceholder
                    echoMode: TextInput.Password
                    clearEnabled: true
                    Keys.onReturnPressed: settingsConfirmBtn.clicked()
                }

                Text {
                    text: _apiKeyNotice
                    font.pixelSize: 10
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }

            // ===== Manual form =====
            ColumnLayout {
                visible: settingsAddProviderDialog.mode === "manual"
                spacing: 8
                Layout.fillWidth: true

                Text {
                    text: _manualProviderTitle
                    font.pixelSize: 13
                    font.bold: true
                    color: Theme.currentTheme.colors.textColor
                }

                Text {
                    text: _providerIdLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: settingsManualIdField
                    Layout.fillWidth: true
                    placeholderText: "my-openai"
                    clearEnabled: true
                }

                Text {
                    text: _displayNameLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: settingsManualNameField
                    Layout.fillWidth: true
                    placeholderText: "My OpenAI"
                    clearEnabled: true
                }

                Text {
                    text: _apiBaseUrlLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: settingsManualUrlField
                    Layout.fillWidth: true
                    placeholderText: "https://api.openai.com/v1"
                    clearEnabled: true
                }

                Text {
                    text: _apiKeyLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: settingsManualKeyField
                    Layout.fillWidth: true
                    placeholderText: _apiKeyPlaceholder
                    echoMode: TextInput.Password
                    clearEnabled: true
                }

                Text {
                    text: _modelsListLabel
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextArea {
                    id: settingsManualModelsArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    placeholderText: "gpt-4o-mini\ngpt-4o"
                    wrapMode: TextEdit.NoWrap
                }

                Text {
                    text: _apiKeyNotice
                    font.pixelSize: 10
                    color: Theme.currentTheme.colors.textSecondaryColor
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Button {
                    text: {
                        if (settingsAddProviderDialog.mode === "catalog" && settingsAddProviderDialog.step === 2)
                            return _backBtn
                        return _cancelBtn
                    }
                    flat: true
                    onClicked: {
                        if (settingsAddProviderDialog.mode === "catalog" && settingsAddProviderDialog.step === 2)
                            settingsAddProviderDialog.step = 1
                        else
                            settingsAddProviderDialog.close()
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    id: settingsConfirmBtn
                    text: _addBtn
                    highlighted: true
                    visible: settingsAddProviderDialog.mode === "catalog" && settingsAddProviderDialog.step === 2
                    enabled: settingsApiKeyField.text.trim().length > 0
                    onClicked: {
                        if (Agent && Agent.addProvider(settingsAddProviderDialog.apiStep2Id, settingsApiKeyField.text.trim())) {
                            console.log("[Settings] catalog provider added:", settingsAddProviderDialog.apiStep2Id)
                            settingsAddProviderDialog.close()
                            loadSettingsProviders()
                            providerInfoBar.severity = Severity.Success
                            providerInfoBar.title = _addSuccessTitle
                            providerInfoBar.text = settingsAddProviderDialog.apiStep2Id
                            providerInfoBar.visible = true
                        }
                    }
                }
                Button {
                    text: _addBtn
                    highlighted: true
                    visible: settingsAddProviderDialog.mode === "manual"
                    enabled: settingsManualIdField.text.trim().length > 0
                             && settingsManualUrlField.text.trim().length > 0
                             && settingsManualKeyField.text.trim().length > 0
                             && settingsManualModelsArea.text.trim().length > 0
                    onClicked: {
                        if (!Agent) return
                        var key = settingsManualIdField.text.trim()
                        var name = settingsManualNameField.text.trim() || key
                        var url = settingsManualUrlField.text.trim()
                        var apiKey = settingsManualKeyField.text.trim()
                        var modelsJson = settingsPage.modelsTextToJson(settingsManualModelsArea.text)
                        console.log("[Settings] addCustomProvider", key, url)
                        if (Agent.addCustomProvider(key, name, url, apiKey, modelsJson)) {
                            settingsAddProviderDialog.close()
                            loadSettingsProviders()
                            providerInfoBar.severity = Severity.Success
                            providerInfoBar.title = _addSuccessTitle
                            providerInfoBar.text = name
                            providerInfoBar.visible = true
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: settingsEditProviderDialog
        title: _editProviderTitle
        modal: true
        width: 520
        closePolicy: Popup.CloseOnEscape
        property string editKey: ""

        contentItem: ColumnLayout {
            spacing: 8

            Text {
                text: _providerIdPrefix + settingsEditProviderDialog.editKey
                font.pixelSize: 13
                font.bold: true
                color: Theme.currentTheme.colors.textColor
            }

            Text {
                text: _displayNameLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }
            TextField {
                id: settingsEditNameField
                Layout.fillWidth: true
                clearEnabled: true
            }

            Text {
                text: _apiBaseUrlLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }
            TextField {
                id: settingsEditUrlField
                Layout.fillWidth: true
                clearEnabled: true
            }

            Text {
                text: _apiKeyLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }
            TextField {
                id: settingsEditKeyField
                Layout.fillWidth: true
                echoMode: TextInput.Password
                clearEnabled: true
            }

            Text {
                text: _modelsListLabel
                font.pixelSize: 12
                color: Theme.currentTheme.colors.textSecondaryColor
            }
            TextArea {
                id: settingsEditModelsArea
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                wrapMode: TextEdit.NoWrap
            }

            RowLayout {
                Layout.fillWidth: true
                Button {
                    text: _cancelBtn
                    flat: true
                    onClicked: settingsEditProviderDialog.close()
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: _saveBtn
                    highlighted: true
                    enabled: settingsEditUrlField.text.trim().length > 0
                             && settingsEditModelsArea.text.trim().length > 0
                    onClicked: {
                        if (!Agent) return
                        var modelsJson = settingsPage.modelsTextToJson(settingsEditModelsArea.text)
                        console.log("[Settings] updateProvider", settingsEditProviderDialog.editKey)
                        if (Agent.updateProvider(
                                settingsEditProviderDialog.editKey,
                                settingsEditNameField.text.trim(),
                                settingsEditUrlField.text.trim(),
                                settingsEditKeyField.text.trim(),
                                modelsJson)) {
                            settingsEditProviderDialog.close()
                            loadSettingsProviders()
                            providerInfoBar.severity = Severity.Success
                            providerInfoBar.title = _savedTitle
                            providerInfoBar.text = settingsEditProviderDialog.editKey
                            providerInfoBar.visible = true
                        }
                    }
                }
            }
        }
    }
}

