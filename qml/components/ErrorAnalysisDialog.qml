import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: errorAnalysisDialog

    property string errorTitle: ""
    property string errorMessage: ""
    property string errorStackTrace: ""
    property string errorSuggestion: ""

    title: Backend ? Backend.tr("启动错误分析") : "启动错误分析"
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    standardButtons: Dialog.Close
    width: 580
    height: 450

    property var _copyButton: null

    onOpened: {
        if (standardButton(Dialog.Close)) {
            standardButton(Dialog.Close).text = Backend ? Backend.tr("关闭") : "关闭"
        }
        // 动态添加复制按钮
        if (!_copyButton && footer && footer.contentItem) {
            var copyBtn = copyButtonComponent.createObject(footer.contentItem)
            if (copyBtn) {
                var layout = footer.contentItem.children[0]
                if (layout && layout.children) {
                    layout.children.insert(0, copyBtn)
                }
                _copyButton = copyBtn
            }
        }
    }

    Component {
        id: copyButtonComponent
        Button {
            text: Backend ? Backend.tr("复制错误信息") : "复制错误信息"
            Layout.alignment: Qt.AlignRight
            Layout.preferredWidth: footer ? footer.availableWidth / 2 : 120
            onClicked: {
                var fullText = ""
                if (errorTitle) fullText += errorTitle + "\n\n"
                if (errorMessage) fullText += errorMessage + "\n\n"
                if (errorStackTrace) fullText += errorStackTrace
                if (Backend) Backend.copyToClipboard(fullText)
            }
        }
    }

    // 主内容区域
    ColumnLayout {
        spacing: 12

        // Error icon and title
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            Text {
                text: "\uE783"
                font.family: "Segoe Fluent Icons"
                font.pixelSize: 28
                color: Theme.currentTheme.colors.systemCriticalColor
            }

            Text {
                text: errorTitle || (Backend ? Backend.tr("Minecraft 启动失败") : "Minecraft 启动失败")
                typography: Typography.BodyStrong
                font.pixelSize: 16
                color: Theme.currentTheme.colors.textColor
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.currentTheme.colors.cardBorderColor
        }

        // Scrollable content area
        Flickable {
            id: contentFlickable
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: contentColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            ColumnLayout {
                id: contentColumn
                spacing: 12
                width: contentFlickable.width

                // Error message
                Text {
                    text: errorMessage
                    visible: errorMessage.length > 0
                    typography: Typography.Body
                    color: Theme.currentTheme.colors.textColor
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }

                // Stack trace (collapsible)
                ColumnLayout {
                    visible: errorStackTrace.length > 0
                    spacing: 6
                    Layout.fillWidth: true

                    Button {
                        flat: true
                        text: (stackTraceRect.visible
                               ? (Backend ? Backend.tr("隐藏详细信息") : "隐藏详细信息")
                               : (Backend ? Backend.tr("显示详细信息") : "显示详细信息"))
                        onClicked: stackTraceRect.visible = !stackTraceRect.visible
                    }

                    Rectangle {
                        id: stackTraceRect
                        visible: false
                        Layout.fillWidth: true
                        implicitHeight: Math.min(stackTraceText.implicitHeight + 16, 200)
                        color: Theme.currentTheme.colors.controlColor
                        border.color: Theme.currentTheme.colors.cardBorderColor
                        border.width: 1
                        radius: 4

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            contentWidth: stackTraceText.implicitWidth
                            contentHeight: stackTraceText.implicitHeight
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds

                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                            }

                            Text {
                                id: stackTraceText
                                text: errorStackTrace
                                typography: Typography.Caption
                                font.family: "Consolas, Courier New, monospace"
                                color: Theme.currentTheme.colors.textSecondaryColor
                                wrapMode: Text.WrapAnywhere
                                width: parent.width
                            }
                        }
                    }
                }

                // Suggestion
                Rectangle {
                    visible: errorSuggestion.length > 0
                    Layout.fillWidth: true
                    implicitHeight: suggestionContent.implicitHeight + 20
                    radius: 6
                    color: Qt.rgba(0, 0.4, 0.6, 0.08)
                    border.color: Qt.rgba(0, 0.4, 0.6, 0.2)
                    border.width: 1

                    RowLayout {
                        id: suggestionContent
                        anchors {
                            left: parent.left
                            right: parent.right
                            top: parent.top
                            margins: 10
                        }
                        spacing: 8

                        Text {
                            text: "\uE946"
                            font.family: "Segoe Fluent Icons"
                            font.pixelSize: 18
                            color: Theme.accentColor
                        }

                        Text {
                            text: errorSuggestion
                            typography: Typography.Body
                            font.pixelSize: 13
                            color: Theme.currentTheme.colors.textColor
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
    }

    function showError(title, message, stackTrace) {
        errorTitle = title || ""
        errorMessage = message || ""
        errorStackTrace = stackTrace || ""
        errorSuggestion = analyzeError(message + "\n" + stackTrace)
        stackTraceRect.visible = false
        open()
    }

    function analyzeError(text) {
        if (!text) return ""

        var tips = []

        if (text.indexOf("NullPointerException") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到空指针异常 (NullPointerException)。这通常是由于 Mod 冲突、版本不兼容或 Java 环境问题导致的。建议检查 Mod 兼容性，或尝试移除最近添加的 Mod 后重新启动。")
                      : "检测到空指针异常 (NullPointerException)。这通常是由于 Mod 冲突、版本不兼容或 Java 环境问题导致的。建议检查 Mod 兼容性，或尝试移除最近添加的 Mod 后重新启动。")
        }

        if (text.indexOf("OutOfMemoryError") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到内存不足错误 (OutOfMemoryError)。建议在启动设置中增加 JVM 最大内存分配（如 -Xmx4G）。")
                      : "检测到内存不足错误 (OutOfMemoryError)。建议在启动设置中增加 JVM 最大内存分配（如 -Xmx4G）。")
        }

        if (text.indexOf("ClassNotFoundException") !== -1 || text.indexOf("NoClassDefFoundError") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到类未找到错误。这表示缺少必要的库文件。建议重新下载该版本的核心文件，或检查是否有 Mod 依赖缺失。")
                      : "检测到类未找到错误。这表示缺少必要的库文件。建议重新下载该版本的核心文件，或检查是否有 Mod 依赖缺失。")
        }

        if (text.indexOf("NoSuchMethodError") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到方法未找到错误。这通常表示 Mod 与当前 Minecraft 版本不兼容。建议检查 Mod 是否适配当前游戏版本。")
                      : "检测到方法未找到错误。这通常表示 Mod 与当前 Minecraft 版本不兼容。建议检查 Mod 是否适配当前游戏版本。")
        }

        if (text.indexOf("ConcurrentHashMap") !== -1 || text.indexOf("ConcurrentModification") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到并发修改错误。这可能是由于 Mod 的线程安全问题或 Java 版本不兼容导致的。建议尝试更换 Java 版本或更新相关 Mod。")
                      : "检测到并发修改错误。这可能是由于 Mod 的线程安全问题或 Java 版本不兼容导致的。建议尝试更换 Java 版本或更新相关 Mod。")
        }

        if (text.indexOf("hs_err_pid") !== -1 || text.indexOf("EXCEPTION_ACCESS_VIOLATION") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到 JVM 崩溃。这通常与 Java 版本、显卡驱动或 Mod 的 native 库有关。建议更新显卡驱动、更换 Java 版本或检查 Mod 的 native 依赖。")
                      : "检测到 JVM 崩溃。这通常与 Java 版本、显卡驱动或 Mod 的 native 库有关。建议更新显卡驱动、更换 Java 版本或检查 Mod 的 native 依赖。")
        }

        if (text.indexOf("java.lang.reflect") !== -1 || text.indexOf("IllegalAccess") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到反射访问错误。这可能是由于 Java 模块系统限制导致的。建议更换 Java 版本（推荐 Java 8 或 Java 17）。")
                      : "检测到反射访问错误。这可能是由于 Java 模块系统限制导致的。建议更换 Java 版本（推荐 Java 8 或 Java 17）。")
        }

        if (text.indexOf("GLFW") !== -1 || text.indexOf("OpenGL") !== -1 || text.indexOf("LWJGL") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到图形库错误。这通常与显卡驱动或 LWJGL 版本有关。建议更新显卡驱动，或在设置中尝试更换 LWJGL 版本。")
                      : "检测到图形库错误。这通常与显卡驱动或 LWJGL 版本有关。建议更新显卡驱动，或在设置中尝试更换 LWJGL 版本。")
        }

        if (text.indexOf("SecurityException") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到安全异常。可能是安全软件（如杀毒软件）阻止了 Minecraft 运行。建议将启动器和游戏目录添加到安全软件的白名单中。")
                      : "检测到安全异常。可能是安全软件（如杀毒软件）阻止了 Minecraft 运行。建议将启动器和游戏目录添加到安全软件的白名单中。")
        }

        if (text.indexOf("FileNotFoundException") !== -1 || text.indexOf("ENOENT") !== -1) {
            tips.push(Backend
                      ? Backend.tr("检测到文件缺失错误。关键游戏文件可能已损坏或被删除。建议在下载页面重新下载该版本的核心文件。")
                      : "检测到文件缺失错误。关键游戏文件可能已损坏或被删除。建议在下载页面重新下载该版本的核心文件。")
        }

        if (tips.length === 0) {
            return Backend
                    ? Backend.tr("游戏启动过程中遇到未知错误。你可以复制错误信息并向社区寻求帮助。")
                    : "游戏启动过程中遇到未知错误。你可以复制错误信息并向社区寻求帮助。"
        }

        return tips.join("\n")
    }
}
