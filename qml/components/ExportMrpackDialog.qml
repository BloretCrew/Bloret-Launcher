import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: exportDialog

    title: (Backend ? Backend.tr("导出 Modrinth 整合包") : "导出 Modrinth 整合包")
    modal: true
    width: 450
    implicitHeight: 480
    standardButtons: Dialog.NoButton

    property string versionName: ""
    property var instanceInfo: ({})

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

    function openForVersion(name) {
        versionName = name
        exporting = false
        exportDone = false
        exportSuccess = false
        outputPath = ""
        exportError = ""
        if (Backend) {
            instanceInfo = Backend.getMrpackInstanceInfo(name)
        }
        packNameField.text = instanceInfo.name || name
        packVersionField.text = "1.0.0"
        open()
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 16

        // 实例信息
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
                    text: (Backend ? Backend.tr("文件数: %1").arg(instanceInfo.file_count || 0) : "文件数: " + (instanceInfo.file_count || 0))
                    font.pixelSize: 12
                    color: Theme.currentTheme.colors.textColor
                }
            }
        }

        // 输入区域
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
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
                                if (path && path.length > 0) {
                                    exportDialog.outputPath = path
                                }
                            }
                        }
                    }
                }
            }
        }

        // 导出中
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: exporting

            ProgressBar {
                Layout.fillWidth: true
                indeterminate: true
            }

            Label {
                text: (Backend ? Backend.tr("正在导出整合包...") : "正在导出整合包...")
                Layout.alignment: Qt.AlignHCenter
                color: Theme.currentTheme.colors.textColor
            }
        }

        // 导出结果
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

        // 按钮区域
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
                    } else {
                        exportDialog.exporting = true
                        exportDialog.exportRequestSerial++
                        exportDialog.activeExportRequestId = "export:" + exportDialog.exportRequestSerial
                        var submitted = Backend && Backend.requestMrpackExport(
                            exportDialog.versionName,
                            packNameField.text.trim(),
                            packVersionField.text.trim(),
                            exportDialog.outputPath,
                            exportDialog.activeExportRequestId
                        )
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

}
