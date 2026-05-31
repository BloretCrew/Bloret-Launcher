import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import RinUI 1.0

Flickable {
    id: root
    contentHeight: mainLayout.implicitHeight + 32
    clip: true
    flickableDirection: Flickable.VerticalFlick

    property var mcmetaData: ({})

    Connections {
        target: RPEditor
        function onPackLoaded(info) { loadData() }
    }

    function loadData() {
        var raw = RPEditor.getMcmeta()
        if (!raw) return
        try {
            mcmetaData = JSON.parse(raw)
        } catch (e) {
            mcmetaData = {}
        }
        loadBasic()
        loadLanguage()
        loadFilter()
        loadOverlays()
        loadCopyright()
        jsonPreview.text = JSON.stringify(mcmetaData, null, 2)
    }

    function saveAll() {
        saveBasic()
        saveLanguage()
        saveFilter()
        saveOverlays()
        saveCopyright()
        RPEditor.saveMcmeta(JSON.stringify(mcmetaData, null, 2))
        jsonPreview.text = JSON.stringify(mcmetaData, null, 2)
    }

    function loadBasic() {
        var pack = mcmetaData["pack"] || {}
        packFormatField.text = pack["pack_format"] !== undefined ? String(pack["pack_format"]) : ""
        descriptionArea.text = pack["description"] || ""
        var sf = pack["supported_formats"]
        if (sf && typeof sf === "object" && !Array.isArray(sf)) {
            minFormatField.text = sf["min_inclusive"] !== undefined ? String(sf["min_inclusive"]) : ""
            maxFormatField.text = sf["max_inclusive"] !== undefined ? String(sf["max_inclusive"]) : ""
            supportedFormatMode.checked = true
        } else if (sf && Array.isArray(sf)) {
            minFormatField.text = sf.length > 0 ? String(sf[0]) : ""
            maxFormatField.text = sf.length > 1 ? String(sf[1]) : ""
            supportedFormatMode.checked = true
        } else {
            minFormatField.text = pack["min_format"] !== undefined ? String(pack["min_format"]) : ""
            maxFormatField.text = pack["max_format"] !== undefined ? String(pack["max_format"]) : ""
            supportedFormatMode.checked = false
        }
    }

    function saveBasic() {
        if (!mcmetaData["pack"]) mcmetaData["pack"] = {}
        var pack = mcmetaData["pack"]
        var fmt = parseInt(packFormatField.text)
        if (!isNaN(fmt)) pack["pack_format"] = fmt
        pack["description"] = descriptionArea.text
        if (minFormatField.text || maxFormatField.text) {
            var minF = parseInt(minFormatField.text)
            var maxF = parseInt(maxFormatField.text)
            if (supportedFormatMode.checked) {
                var obj = {}
                if (!isNaN(minF)) obj["min_inclusive"] = minF
                if (!isNaN(maxF)) obj["max_inclusive"] = maxF
                pack["supported_formats"] = obj
            } else {
                delete pack["supported_formats"]
                if (!isNaN(minF)) pack["min_format"] = minF
                if (!isNaN(maxF)) pack["max_format"] = maxF
            }
        }
    }

    function loadLanguage() {
        languageModel.clear()
        var lang = mcmetaData["language"] || {}
        var keys = Object.keys(lang)
        for (var i = 0; i < keys.length; i++) {
            var entry = lang[keys[i]]
            languageModel.append({
                code: keys[i],
                name: entry["name"] || "",
                bidirectional: entry["bidirectional"] || false
            })
        }
    }

    function saveLanguage() {
        var lang = {}
        for (var i = 0; i < languageModel.count; i++) {
            var item = languageModel.get(i)
            if (item.code) {
                lang[item.code] = {
                    "name": item.name,
                    "bidirectional": item.bidirectional
                }
            }
        }
        if (Object.keys(lang).length > 0) {
            mcmetaData["language"] = lang
        } else {
            delete mcmetaData["language"]
        }
    }

    function loadFilter() {
        filterNamespaceModel.clear()
        filterPathModel.clear()
        var filter = mcmetaData["filter"] || {}
        var block = filter["block"] || {}
        var ns = block["namespace"] || {}
        var nsPatterns = ns["pattern"] || []
        var nsReplace = ns["replace"] || ""
        for (var i = 0; i < nsPatterns.length; i++) {
            filterNamespaceModel.append({ pattern: nsPatterns[i], replace: nsReplace })
        }
        var path = block["path"] || {}
        var pathPatterns = path["pattern"] || []
        var pathReplace = path["replace"] || ""
        for (var j = 0; j < pathPatterns.length; j++) {
            filterPathModel.append({ pattern: pathPatterns[j], replace: pathReplace })
        }
    }

    function saveFilter() {
        var hasNs = filterNamespaceModel.count > 0
        var hasPath = filterPathModel.count > 0
        if (!hasNs && !hasPath) {
            delete mcmetaData["filter"]
            return
        }
        var block = {}
        if (hasNs) {
            var nsPatterns = []
            var nsReplace = ""
            for (var i = 0; i < filterNamespaceModel.count; i++) {
                var nsItem = filterNamespaceModel.get(i)
                nsPatterns.push(nsItem.pattern)
                nsReplace = nsItem.replace
            }
            block["namespace"] = { "pattern": nsPatterns, "replace": nsReplace }
        }
        if (hasPath) {
            var pathPatterns = []
            var pathReplace = ""
            for (var j = 0; j < filterPathModel.count; j++) {
                var pathItem = filterPathModel.get(j)
                pathPatterns.push(pathItem.pattern)
                pathReplace = pathItem.replace
            }
            block["path"] = { "pattern": pathPatterns, "replace": pathReplace }
        }
        mcmetaData["filter"] = { "block": block }
    }

    function loadOverlays() {
        overlayModel.clear()
        var overlays = mcmetaData["overlays"] || {}
        var entries = overlays["entries"] || []
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i]
            var fmt = e["formats"] || {}
            overlayModel.append({
                dirName: e["directory"] || "",
                minFormat: fmt["min_inclusive"] !== undefined ? String(fmt["min_inclusive"]) : "",
                maxFormat: fmt["max_inclusive"] !== undefined ? String(fmt["max_inclusive"]) : ""
            })
        }
    }

    function saveOverlays() {
        var entries = []
        for (var i = 0; i < overlayModel.count; i++) {
            var item = overlayModel.get(i)
            var fmt = {}
            var minF = parseInt(item.minFormat)
            var maxF = parseInt(item.maxFormat)
            if (!isNaN(minF)) fmt["min_inclusive"] = minF
            if (!isNaN(maxF)) fmt["max_inclusive"] = maxF
            entries.push({
                "directory": item.dirName,
                "formats": fmt
            })
        }
        if (entries.length > 0) {
            mcmetaData["overlays"] = { "entries": entries }
        } else {
            delete mcmetaData["overlays"]
        }
    }

    function loadCopyright() {
        copyrightField.text = mcmetaData["copyright"] || ""
    }

    function saveCopyright() {
        if (copyrightField.text) {
            mcmetaData["copyright"] = copyrightField.text
        } else {
            delete mcmetaData["copyright"]
        }
    }

    ListModel { id: languageModel }
    ListModel { id: filterNamespaceModel }
    ListModel { id: filterPathModel }
    ListModel { id: overlayModel }

    ColumnLayout {
        id: mainLayout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 16

        // ===== Basic Info Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: basicColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: basicColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Basic Info"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: basicCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    visible: !basicCollapseBtn.collapsed

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "pack_format:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 13 }
                        TextField {
                            id: packFormatField
                            Layout.preferredWidth: 120
                            placeholderText: "e.g. 15"
                            color: Theme.currentTheme.colors.textColor
                            background: Rectangle {
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                radius: 6
                                border.color: Theme.currentTheme.colors.controlBorderColor
                                border.width: 1
                            }
                        }
                    }

                    Text { text: "description:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 13 }
                    TextArea {
                        id: descriptionArea
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        placeholderText: "Pack description (supports JSON text component)"
                        color: Theme.currentTheme.colors.textColor
                        wrapMode: TextArea.Wrap
                        background: Rectangle {
                            color: Theme.currentTheme.colors.controlAltSecondaryColor
                            radius: 6
                            border.color: Theme.currentTheme.colors.controlBorderColor
                            border.width: 1
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        CheckBox {
                            id: supportedFormatMode
                            text: "Use supported_formats (range)"
                            checked: false
                            contentItem: Text {
                                text: supportedFormatMode.text
                                color: Theme.currentTheme.colors.textColor
                                font.pixelSize: 13
                                leftPadding: supportedFormatMode.indicator.width + 8
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: supportedFormatMode.checked ? "min_inclusive:" : "min_format:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 13 }
                        TextField {
                            id: minFormatField
                            Layout.preferredWidth: 100
                            placeholderText: "min"
                            color: Theme.currentTheme.colors.textColor
                            background: Rectangle {
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                radius: 6
                                border.color: Theme.currentTheme.colors.controlBorderColor
                                border.width: 1
                            }
                        }
                        Text { text: supportedFormatMode.checked ? "max_inclusive:" : "max_format:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 13 }
                        TextField {
                            id: maxFormatField
                            Layout.preferredWidth: 100
                            placeholderText: "max"
                            color: Theme.currentTheme.colors.textColor
                            background: Rectangle {
                                color: Theme.currentTheme.colors.controlAltSecondaryColor
                                radius: 6
                                border.color: Theme.currentTheme.colors.controlBorderColor
                                border.width: 1
                            }
                        }
                    }
                }
            }
        }

        // ===== Language Registration Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: langColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: langColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Language Registration"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: langCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    visible: !langCollapseBtn.collapsed

                    Repeater {
                        model: languageModel
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            TextField {
                                text: model.code
                                onEditingFinished: languageModel.setProperty(index, "code", text)
                                placeholderText: "code (e.g. en_us)"
                                Layout.preferredWidth: 100
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            TextField {
                                text: model.name
                                onEditingFinished: languageModel.setProperty(index, "name", text)
                                placeholderText: "Display Name"
                                Layout.fillWidth: true
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            CheckBox {
                                checked: model.bidirectional
                                onCheckedChanged: languageModel.setProperty(index, "bidirectional", checked)
                                contentItem: Text {
                                    text: "RTL"
                                    color: Theme.currentTheme.colors.textColor
                                    font.pixelSize: 12
                                    leftPadding: 24
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            Button {
                                icon.name: "ic_fluent_dismiss_20_regular"
                                flat: true
                                implicitWidth: 28
                                implicitHeight: 28
                                onClicked: languageModel.remove(index)
                            }
                        }
                    }

                    Button {
                        text: "+ Add Language"
                        flat: true
                        Layout.alignment: Qt.AlignLeft
                        contentItem: Text {
                            text: "+ Add Language"
                            color: Theme.currentTheme.colors.textColor
                            font.pixelSize: 13
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: languageModel.append({ code: "", name: "", bidirectional: false })
                    }
                }
            }
        }

        // ===== Filter Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: filterColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: filterColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Filter"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: filterCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    visible: !filterCollapseBtn.collapsed

                    // Namespace patterns
                    Text { text: "Namespace:"; font.pixelSize: 14; font.bold: true; color: Theme.currentTheme.colors.textColor }

                    Repeater {
                        model: filterNamespaceModel
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            TextField {
                                text: model.pattern
                                onEditingFinished: filterNamespaceModel.setProperty(index, "pattern", text)
                                placeholderText: "Regex pattern"
                                Layout.fillWidth: true
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            TextField {
                                text: model.replace
                                onEditingFinished: filterNamespaceModel.setProperty(index, "replace", text)
                                placeholderText: "Replace"
                                Layout.preferredWidth: 120
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            Button {
                                icon.name: "ic_fluent_dismiss_20_regular"
                                flat: true
                                implicitWidth: 28
                                implicitHeight: 28
                                onClicked: filterNamespaceModel.remove(index)
                            }
                        }
                    }

                    Button {
                        text: "+ Add Namespace Pattern"
                        flat: true
                        Layout.alignment: Qt.AlignLeft
                        contentItem: Text {
                            text: "+ Add Namespace Pattern"
                            color: Theme.currentTheme.colors.textColor
                            font.pixelSize: 13
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: filterNamespaceModel.append({ pattern: "", replace: "" })
                    }

                    // Path patterns
                    Text { text: "Path:"; font.pixelSize: 14; font.bold: true; color: Theme.currentTheme.colors.textColor }

                    Repeater {
                        model: filterPathModel
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            TextField {
                                text: model.pattern
                                onEditingFinished: filterPathModel.setProperty(index, "pattern", text)
                                placeholderText: "Regex pattern"
                                Layout.fillWidth: true
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            TextField {
                                text: model.replace
                                onEditingFinished: filterPathModel.setProperty(index, "replace", text)
                                placeholderText: "Replace"
                                Layout.preferredWidth: 120
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            Button {
                                icon.name: "ic_fluent_dismiss_20_regular"
                                flat: true
                                implicitWidth: 28
                                implicitHeight: 28
                                onClicked: filterPathModel.remove(index)
                            }
                        }
                    }

                    Button {
                        text: "+ Add Path Pattern"
                        flat: true
                        Layout.alignment: Qt.AlignLeft
                        contentItem: Text {
                            text: "+ Add Path Pattern"
                            color: Theme.currentTheme.colors.textColor
                            font.pixelSize: 13
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: filterPathModel.append({ pattern: "", replace: "" })
                    }
                }
            }
        }

        // ===== Overlays Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: overlayColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: overlayColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Overlays"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: overlayCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    visible: !overlayCollapseBtn.collapsed

                    Repeater {
                        model: overlayModel
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            TextField {
                                text: model.dirName
                                onEditingFinished: overlayModel.setProperty(index, "dirName", text)
                                placeholderText: "directory"
                                Layout.preferredWidth: 120
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            Text { text: "min:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                            TextField {
                                text: model.minFormat
                                onEditingFinished: overlayModel.setProperty(index, "minFormat", text)
                                placeholderText: "min"
                                Layout.preferredWidth: 60
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            Text { text: "max:"; color: Theme.currentTheme.colors.textSecondaryColor; font.pixelSize: 12 }
                            TextField {
                                text: model.maxFormat
                                onEditingFinished: overlayModel.setProperty(index, "maxFormat", text)
                                placeholderText: "max"
                                Layout.preferredWidth: 60
                                color: Theme.currentTheme.colors.textColor
                                background: Rectangle {
                                    color: Theme.currentTheme.colors.controlAltSecondaryColor
                                    radius: 6
                                    border.color: Theme.currentTheme.colors.controlBorderColor
                                    border.width: 1
                                }
                            }
                            Button {
                                icon.name: "ic_fluent_dismiss_20_regular"
                                flat: true
                                implicitWidth: 28
                                implicitHeight: 28
                                onClicked: overlayModel.remove(index)
                            }
                        }
                    }

                    Button {
                        text: "+ Add Overlay"
                        flat: true
                        Layout.alignment: Qt.AlignLeft
                        contentItem: Text {
                            text: "+ Add Overlay"
                            color: Theme.currentTheme.colors.textColor
                            font.pixelSize: 13
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: overlayModel.append({ dirName: "", minFormat: "", maxFormat: "" })
                    }
                }
            }
        }

        // ===== Copyright Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: copyrightColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: copyrightColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Copyright"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: copyrightCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    visible: !copyrightCollapseBtn.collapsed

                    TextField {
                        id: copyrightField
                        Layout.fillWidth: true
                        placeholderText: "Copyright text"
                        color: Theme.currentTheme.colors.textColor
                        background: Rectangle {
                            color: Theme.currentTheme.colors.controlAltSecondaryColor
                            radius: 6
                            border.color: Theme.currentTheme.colors.controlBorderColor
                            border.width: 1
                        }
                    }
                }
            }
        }

        // ===== JSON Preview Card =====
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: jsonColumn.implicitHeight + 32
            color: Theme.currentTheme.colors.cardColor
            radius: 12
            border.color: Theme.currentTheme.colors.controlBorderColor
            border.width: 1

            ColumnLayout {
                id: jsonColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "JSON Preview"
                        font.pixelSize: 16
                        font.bold: true
                        color: Theme.currentTheme.colors.textColor
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        id: jsonCollapseBtn
                        text: "▼"
                        flat: true
                        implicitWidth: 28
                        implicitHeight: 28
                        property bool collapsed: false
                        onClicked: { collapsed = !collapsed; text = collapsed ? "▶" : "▼" }
                    }
                }

                TextArea {
                    id: jsonPreview
                    Layout.fillWidth: true
                    Layout.preferredHeight: 300
                    readOnly: true
                    color: Theme.currentTheme.colors.textColor
                    wrapMode: TextArea.Wrap
                    font.family: "monospace"
                    font.pixelSize: 12
                    background: Rectangle {
                        color: Theme.currentTheme.colors.controlAltSecondaryColor
                        radius: 6
                        border.color: Theme.currentTheme.colors.controlBorderColor
                        border.width: 1
                    }
                    visible: !jsonCollapseBtn.collapsed
                }
            }
        }

        // ===== Save Button =====
        Button {
            id: saveBtn
            Layout.alignment: Qt.AlignRight
            text: "Save pack.mcmeta"
            highlighted: true
            onClicked: {
                saveDialog.open()
            }
        }

        Dialog {
            id: saveDialog
            title: "Save pack.mcmeta"
            anchors.centerIn: parent
            modal: true
            width: 400
            height: 180
            visible: false

            contentItem: ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 16

                Text {
                    text: "Save changes to pack.mcmeta?"
                    color: Theme.currentTheme.colors.textColor
                    font.pixelSize: 14
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Item { Layout.fillWidth: true }

                    Button {
                        text: "取消"
                        flat: true
                        onClicked: saveDialog.close()
                    }

                    Button {
                        text: "保存"
                        highlighted: true
                        onClicked: {
                            saveAll()
                            saveDialog.close()
                        }
                    }
                }
            }

            background: Rectangle {
                color: Theme.currentTheme.colors.cardColor
                radius: 12
                border.color: Theme.currentTheme.colors.controlBorderColor
                border.width: 1
            }
        }
    }
}
