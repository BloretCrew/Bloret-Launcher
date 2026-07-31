import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: pluginInstallDialog

    property string token: ""
    property string pluginId: ""
    property string pluginName: ""
    property string pluginVersion: ""
    property string pluginAuthor: ""
    property string pluginDescription: ""
    property string downloadUrl: ""
    property string downloadHost: ""
    property string sha256: ""
    property string source: ""
    property string stage: "pending" // pending | installing | done | failed | cancelled
    property string statusMessage: ""
    property double progress: 0.0
    /** 权限详情 JSON：[{id,label,risk},...] */
    property string permissionDetailsJson: "[]"

    title: {
        if (stage === "installing")
            return Backend ? Backend.tr("正在安装插件") : "正在安装插件"
        if (stage === "done")
            return Backend ? Backend.tr("插件安装成功") : "插件安装成功"
        if (stage === "failed")
            return Backend ? Backend.tr("插件安装失败") : "插件安装失败"
        return Backend ? Backend.tr("确认安装插件") : "确认安装插件"
    }
    modal: true
    closePolicy: (stage === "installing") ? Popup.NoAutoClose : Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    width: Math.min(480, parent ? parent.width - 80 : 480)
    implicitHeight: 420

    function tr(s) {
        return Backend ? Backend.tr(s) : s
    }

    function resetState() {
        token = ""
        pluginId = ""
        pluginName = ""
        pluginVersion = ""
        pluginAuthor = ""
        pluginDescription = ""
        downloadUrl = ""
        downloadHost = ""
        sha256 = ""
        source = ""
        stage = "pending"
        statusMessage = ""
        progress = 0.0
        permissionDetailsJson = "[]"
    }

    function _buildPermissionDetails(meta) {
        // 优先使用服务端/宿主已解析的 permission_details
        if (meta.permission_details) {
            try {
                return typeof meta.permission_details === "string"
                    ? meta.permission_details
                    : JSON.stringify(meta.permission_details)
            } catch (e) {
                console.log("[PluginInstallDialog] stringify permission_details failed:", e)
            }
        }
        var ids = meta.permissions || meta.requestedPermissions || meta.permission || []
        if (typeof ids === "string") {
            try {
                ids = JSON.parse(ids)
            } catch (e2) {
                ids = ids.split(/[,;\s]+/).filter(function (s) { return s && s.length > 0 })
            }
        }
        if (!ids || ids.length === 0)
            return "[]"
        if (typeof PluginHost !== "undefined" && PluginHost
                && typeof PluginHost.resolvePermissionsJson === "function") {
            try {
                return PluginHost.resolvePermissionsJson(JSON.stringify(ids))
            } catch (e3) {
                console.log("[PluginInstallDialog] resolvePermissionsJson failed:", e3)
            }
        }
        try {
            return JSON.stringify(ids.map(function (id) {
                return { id: id, label: id, risk: "high" }
            }))
        } catch (e4) {
            return "[]"
        }
    }

    function showProposal(meta) {
        if (!meta)
            return
        console.log("[PluginInstallDialog] showProposal", meta.name || meta.id, meta.download_host || "")
        token = meta.token || ""
        pluginId = meta.id || ""
        pluginName = meta.display_name || meta.name || meta.id || "Plugin"
        pluginVersion = meta.version || ""
        pluginAuthor = meta.author || ""
        pluginDescription = meta.description || ""
        downloadUrl = meta.download || ""
        downloadHost = meta.download_host || ""
        sha256 = meta.sha256 || ""
        source = meta.source || ""
        permissionDetailsJson = _buildPermissionDetails(meta)
        console.log("[PluginInstallDialog] permissions chips:",
                    String(permissionDetailsJson).substring(0, 200))
        stage = "pending"
        statusMessage = ""
        progress = 0.0
        open()
    }

    function applyProgress(t, st, message, prog) {
        if (token && t && t !== token)
            return
        console.log("[PluginInstallDialog] progress", st, message, prog)
        stage = st || stage
        statusMessage = message || ""
        if (typeof prog === "number")
            progress = prog
        if (st === "done" || st === "failed" || st === "cancelled") {
            // keep dialog open so user can read result
        }
    }

    ColumnLayout {
        spacing: 14
        Layout.fillWidth: true

        // 确认信息
        ColumnLayout {
            visible: stage === "pending"
            spacing: 10
            Layout.fillWidth: true

            Text {
                text: tr("即将安装以下插件。请确认来源与信息后再继续。")
                typography: Typography.Body
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: Theme.currentTheme.colors.cardColor || "#f5f5f5"
                border.color: Theme.currentTheme.colors.cardBorderColor || "#ddd"
                border.width: 1
                implicitHeight: infoCol.implicitHeight + 24

                ColumnLayout {
                    id: infoCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 6

                    Text {
                        text: pluginName
                        typography: Typography.BodyStrong
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: pluginId.length > 0
                        text: tr("ID") + ": " + pluginId
                        typography: Typography.Caption
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: pluginVersion.length > 0
                        text: tr("版本") + ": " + pluginVersion
                        typography: Typography.Caption
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: pluginAuthor.length > 0
                        text: tr("作者") + ": " + pluginAuthor
                        typography: Typography.Caption
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: downloadHost.length > 0 || downloadUrl.length > 0
                        text: tr("下载来源") + ": " + (downloadHost || downloadUrl)
                        typography: Typography.Caption
                        color: Theme.currentTheme.colors.textSecondaryColor
                        wrapMode: Text.WrapAnywhere
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: sha256.length > 0
                        text: "SHA256: " + sha256.substring(0, 16) + "…"
                        typography: Typography.Caption
                        color: Theme.currentTheme.colors.textSecondaryColor
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: pluginDescription.length > 0
                        text: pluginDescription
                        typography: Typography.Caption
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }

                    PluginPermissionChips {
                        Layout.fillWidth: true
                        Layout.topMargin: 4
                        compact: true
                        showTitle: true
                        title: tr("此插件将获得以下权限")
                        detailsJson: permissionDetailsJson
                        hideWhenEmpty: true
                    }

                    Text {
                        visible: {
                            try {
                                var arr = JSON.parse(permissionDetailsJson || "[]")
                                if (!Array.isArray(arr))
                                    return false
                                for (var i = 0; i < arr.length; i++) {
                                    if ((arr[i].risk || "") === "high")
                                        return true
                                }
                            } catch (e) {}
                            return false
                        }
                        text: tr("橙色为高风险权限，安装前请仔细确认")
                        typography: Typography.Caption
                        color: "#c2410c"
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }

            Text {
                text: tr("警告：插件可扩展启动器功能，仅安装来自可信来源的包。安装前请确认作者与下载主机。")
                typography: Typography.Caption
                color: "#c43e1c"
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: tr("取消")
                    onClicked: {
                        console.log("[PluginInstallDialog] user cancel", token)
                        if (typeof PluginHost !== "undefined" && PluginHost && token)
                            PluginHost.cancelInstall(token)
                        pluginInstallDialog.close()
                    }
                }
                Button {
                    highlighted: true
                    text: tr("安装")
                    onClicked: {
                        console.log("[PluginInstallDialog] user confirm", token)
                        if (typeof PluginHost === "undefined" || !PluginHost || !token) {
                            statusMessage = tr("PluginHost 不可用")
                            stage = "failed"
                            return
                        }
                        stage = "installing"
                        statusMessage = tr("正在下载插件…")
                        progress = 0.1
                        var raw = PluginHost.confirmInstall(token)
                        console.log("[PluginInstallDialog] confirmInstall →", raw)
                        try {
                            var r = JSON.parse(raw || "{}")
                            if (!r.ok) {
                                stage = "failed"
                                statusMessage = r.message || r.error || tr("无法开始安装")
                            }
                        } catch (e) {
                            console.log("[PluginInstallDialog] parse confirm result:", e)
                        }
                    }
                }
            }
        }

        // 安装中 / 结果
        ColumnLayout {
            visible: stage !== "pending"
            spacing: 12
            Layout.fillWidth: true

            Text {
                text: statusMessage || (
                    stage === "done" ? tr("安装完成") :
                    stage === "failed" ? tr("安装失败") :
                    stage === "cancelled" ? tr("已取消") :
                    tr("正在安装…")
                )
                typography: Typography.Body
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            ProgressBar {
                visible: stage === "installing"
                Layout.fillWidth: true
                from: 0
                to: 1
                value: progress
                indeterminate: progress <= 0.05
            }

            Text {
                visible: stage === "installing"
                text: Math.round(progress * 100) + "%"
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
            }

            Text {
                visible: stage === "done" && pluginName.length > 0
                text: tr("已安装") + ": " + pluginName
                typography: Typography.Caption
                color: Theme.currentTheme.colors.textSecondaryColor
                Layout.fillWidth: true
            }

            RowLayout {
                visible: stage === "done" || stage === "failed" || stage === "cancelled"
                Layout.fillWidth: true
                spacing: 8
                Item { Layout.fillWidth: true }
                Button {
                    highlighted: stage === "done"
                    text: tr("关闭")
                    onClicked: pluginInstallDialog.close()
                }
            }
        }
    }
}
