import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: exportDialog

    title: (Backend ? Backend.tr("导出 Modrinth 整合包") : "导出 Modrinth 整合包")
    modal: true
    width: 520
    implicitHeight: 560
    height: Math.min(640, Overlay.overlay ? Overlay.overlay.height - 40 : 560)
    standardButtons: Dialog.NoButton

    property string versionName: ""
    property var instanceInfo: ({})
    property var exportCandidates: []
    property var selectedPaths: ({})

    property bool exporting: false
    property bool exportDone: false
    property bool exportSuccess: false
    property string outputPath: ""
    property int exportRequestSerial: 0
    property string activeExportRequestId: ""
    property string exportError: ""

    Connections {
        target: Backend
        function onMrpackExportFinished(requestId, success, actualOutputPath, errorMessage) {
            if (requestId !== activeExportRequestId) return
            exporting = false
            exportDone = true
            exportSuccess = success
            outputPath = actualOutputPath
            exportError = errorMessage
        }
    }

    function loadCandidates() {
        exportCandidates = []
        selectedPaths = ({})
        if (!Backend || !versionName) return
        var res = Backend.getMrpackExportCandidates(versionName) || {}
        var list = (res && res.ok) ? (res.data || []) : []
        exportCandidates = list
        var sel = ({})
        for (var i = 0; i < list.length; i++) {
            var c = list[i]
            if (c && c.path && c.default_selected)
                sel[c.path] = true
        }
        selectedPaths = sel
    }

    function selectedPathList() {
        var out = []
        var keys = Object.keys(selectedPaths)
        for (var i = 0; i < keys.length; i++) {
            if (selectedPaths[keys[i]]) out.push(keys[i])
        }
        return out
    }

    function openForVersion(name) {
        versionName = name
        exporting = false
        exportDone = false
        exportSuccess = false
        outputPath = ""
        exportError = ""
        if (Backend) {
            instanceInfo = Backend.getMrpackInstanceInfo(name) || {}
        }
        packNameField.text = instanceInfo.name || name
        packVersionField.text = "1.0.0"
        loadCandidates()
        open()
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: infoLayout.implicitHeight + 16
            radius: 6
            color: Theme.currentTheme.colors.cardColor
            border.color: Theme.currentTheme.colors.cardBorderColor
            border.width: 1
            visible: !exporting && !exportDone

            ColumnLayout {
                id: infoLayout
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4

                Label {
                    text: (Backend ? Backend.tr("实例信息") : "实例信息")
                    font.weight: Font.DemiBold
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                Label {
                    text: (Backend ? Backend.tr("游戏版本: %1").arg(instanceInfo.game_version || "-") : "游戏版本: " + (instanceInfo.game_version || "-"))
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textColor
                }
                Label {
                    text: (Backend ? Backend.tr("加载器: %1").arg(instanceInfo.loader || "-") : "加载器: " + (instanceInfo.loader || "-"))
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textColor
                    visible: instanceInfo.loader && instanceInfo.loader !== "unknown"
                }
                Label {
                    text: (Backend ? Backend.tr("候选文件: %1 / 已选 %2").arg(exportCandidates.length).arg(selectedPathList().length)
                                   : ("候选: " + exportCandidates.length + " 已选: " + selectedPathList().length))
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textColor
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: !exporting && !exportDone

            ColumnLayout {
                spacing: 4
                Label {
                    text: (Backend ? Backend.tr("整合包名称") : "整合包名称")
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: packNameField
                    Layout.fillWidth: true
                    placeholderText: (Backend ? Backend.tr("输入整合包名称") : "输入整合包名称")
                }
            }

            ColumnLayout {
                spacing: 4
                Label {
                    text: (Backend ? Backend.tr("版本号") : "版本号")
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                TextField {
                    id: packVersionField
                    Layout.fillWidth: true
                    placeholderText: "1.0.0"
                }
            }

            ColumnLayout {
                spacing: 4
                Label {
                    text: (Backend ? Backend.tr("保存位置") : "保存位置")
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textSecondaryColor
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    TextField {
                        id: savePathField
                        Layout.fillWidth: true
                        readOnly: true
                        placeholderText: (Backend ? Backend.tr("点击浏览选择保存位置") : "点击浏览选择保存位置")
                        text: exportDialog.outputPath
                    }
                    Button {
                        text: (Backend ? Backend.tr("浏览...") : "浏览...")
                        onClicked: {
                            if (Backend) {
                                var defaultName = packNameField.text + "-" + packVersionField.text + ".mrpack"
                                var path = Backend.selectSaveFile(
                                    Backend.tr("保存 Modrinth 整合包"),
                                    defaultName,
                                    "Modrinth Modpack Files (*.mrpack)"
                                )
                                if (path && path.length > 0)
                                    exportDialog.outputPath = path
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: (Backend ? Backend.tr("导出内容") : "导出内容")
                        font.weight: Font.DemiBold
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: (Backend ? Backend.tr("全选默认") : "全选默认")
                        flat: true
                        onClicked: loadCandidates()
                    }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 160
                    clip: true
                    ColumnLayout {
                        width: parent.width - 12
                        spacing: 4
                        Repeater {
                            model: exportCandidates
                            CheckBox {
                                text: {
                                    var sz = modelData.size ? (" · " + Math.round(modelData.size / 1024) + "KB") : ""
                                    return (modelData.path || "") + sz
                                }
                                checked: !!(selectedPaths[modelData.path])
                                onCheckedChanged: {
                                    var s = Object.assign({}, selectedPaths)
                                    if (checked) s[modelData.path] = true
                                    else delete s[modelData.path]
                                    selectedPaths = s
                                }
                            }
                        }
                        Label {
                            visible: exportCandidates.length === 0
                            text: (Backend ? Backend.tr("无可导出文件（或未扫描到）") : "无可导出文件")
                            color: Theme.currentTheme.colors.textSecondaryColor
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: exporting
            ProgressBar { Layout.fillWidth: true; indeterminate: true }
            Label {
                text: (Backend ? Backend.tr("正在导出整合包...") : "正在导出整合包...")
                Layout.alignment: Qt.AlignHCenter
                color: Theme.currentTheme.colors.textColor
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: exportDone
            Label {
                text: exportDialog.exportSuccess
                    ? (Backend ? Backend.tr("整合包已成功导出到:") : "整合包已成功导出到:")
                    : (exportDialog.exportError || (Backend ? Backend.tr("导出整合包时发生错误。") : "导出整合包时发生错误。"))
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textColor
            }
            Label {
                text: exportDialog.outputPath
                wrapMode: Text.WrapAnywhere
                Layout.fillWidth: true
                color: Theme.currentTheme.colors.textSecondaryColor
                font.pixelSize: 12
                visible: exportDialog.exportSuccess
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: !exporting
            Item { Layout.fillWidth: true }
            Button {
                text: (Backend ? Backend.tr("取消") : "取消")
                onClicked: exportDialog.close()
            }
            Button {
                text: exportDialog.exportDone
                    ? (Backend ? Backend.tr("关闭") : "关闭")
                    : (Backend ? Backend.tr("导出") : "导出")
                highlighted: true
                enabled: exportDialog.exportDone
                    || (packNameField.text.trim() !== "" && packVersionField.text.trim() !== "" && exportDialog.outputPath !== "")
                onClicked: {
                    if (exportDialog.exportDone) {
                        exportDialog.close()
                        return
                    }
                    exportDialog.exporting = true
                    exportDialog.exportRequestSerial++
                    exportDialog.activeExportRequestId = "export:" + exportDialog.exportRequestSerial
                    var paths = selectedPathList()
                    var submitted = false
                    if (Backend && Backend.requestMrpackExportWithSelection) {
                        submitted = Backend.requestMrpackExportWithSelection(
                            exportDialog.versionName,
                            packNameField.text.trim(),
                            packVersionField.text.trim(),
                            exportDialog.outputPath,
                            exportDialog.activeExportRequestId,
                            paths
                        )
                    } else if (Backend) {
                        submitted = Backend.requestMrpackExport(
                            exportDialog.versionName,
                            packNameField.text.trim(),
                            packVersionField.text.trim(),
                            exportDialog.outputPath,
                            exportDialog.activeExportRequestId
                        )
                    }
                    if (!submitted) {
                        exportDialog.exporting = false
                        exportDialog.exportDone = true
                        exportDialog.exportSuccess = false
                        exportDialog.exportError = Backend ? Backend.tr("相同路径已有导出任务") : "An export is already running for this path"
                    }
                }
            }
        }
    }
}
