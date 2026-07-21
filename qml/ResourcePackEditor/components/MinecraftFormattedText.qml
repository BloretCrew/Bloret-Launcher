import QtQuick 2.15

Text {
    id: root
    textFormat: Text.RichText
    property string rawText: ""
    onRawTextChanged: {
        if (RPEditor && RPEditor.formatMcText) {
            root.text = RPEditor.formatMcText(rawText)
        } else {
            root.text = rawText
        }
    }
}
