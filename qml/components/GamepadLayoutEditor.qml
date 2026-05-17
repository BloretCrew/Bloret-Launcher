import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import RinUI

Dialog {
    id: layoutEditorDialog
    
    title: Backend ? Backend.tr("编辑按键布局") : "编辑按键布局"
    modal: true
    width: 400
    height: 500
    
    property var buttons: []
    property string layoutName: "custom"
    
    signal layoutSaved(var newButtons)
    
    function loadLayout(layoutData) {
        buttons = JSON.parse(JSON.stringify(layoutData));
        canvas.requestPaint();
    }
    
    function getDefaultButtons() {
        return [
            { "key": "space", "label": "跳跃", "x": 0.5, "y": 0.3, "size": 1.0 },
            { "key": "shift", "label": "潜行", "x": 0.2, "y": 0.5, "size": 1.0 },
            { "key": "e", "label": "E", "x": 0.8, "y": 0.1, "size": 0.8 },
            { "key": "q", "label": "Q", "x": 0.2, "y": 0.1, "size": 0.8 },
            { "key": "f", "label": "F", "x": 0.7, "y": 0.5, "size": 0.8 },
            { "key": "t", "label": "T", "x": 0.9, "y": 0.3, "size": 0.8 }
        ];
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        
        // 提示文字
        Label {
            text: Backend ? Backend.tr("拖拽移动按键位置，点击选中后可删除") : "拖拽移动按键位置，点击选中后可删除"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            color: Theme.currentTheme.colors.textSecondaryColor
        }
        
        // 按键预览区域
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#1a1a2e"
            border.color: Theme.currentTheme.colors.cardBorderColor
            border.width: 1
            radius: 8
            
            Canvas {
                id: canvas
                anchors.fill: parent
                anchors.margins: 10
                
                property int selectedIndex: -1
                property real dragOffsetX: 0
                property real dragOffsetY: 0
                property bool isDragging: false
                
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                    
                    // 绘制网格
                    ctx.strokeStyle = "rgba(255,255,255,0.1)";
                    ctx.lineWidth = 1;
                    for (var i = 0; i <= 10; i++) {
                        ctx.beginPath();
                        ctx.moveTo(width * i / 10, 0);
                        ctx.lineTo(width * i / 10, height);
                        ctx.stroke();
                        ctx.beginPath();
                        ctx.moveTo(0, height * i / 10);
                        ctx.lineTo(width, height * i / 10);
                        ctx.stroke();
                    }
                    
                    // 绘制按键
                    for (var j = 0; j < buttons.length; j++) {
                        var btn = buttons[j];
                        var x = btn.x * width;
                        var y = btn.y * height;
                        var size = 40 * (btn.size || 1.0);
                        
                        // 按键背景
                        ctx.beginPath();
                        ctx.roundedRect(x - size/2, y - size/2, size, size, 8, 8);
                        ctx.fillStyle = (j === selectedIndex) ? "#0078d4" : "rgba(255,255,255,0.15)";
                        ctx.fill();
                        ctx.strokeStyle = (j === selectedIndex) ? "#0078d4" : "rgba(255,255,255,0.3)";
                        ctx.lineWidth = 2;
                        ctx.stroke();
                        
                        // 按键文字
                        ctx.fillStyle = "white";
                        ctx.font = "bold 12px sans-serif";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillText(btn.label, x, y);
                    }
                }
                
                MouseArea {
                    id: canvasMouseArea
                    anchors.fill: parent
                    
                    property int pressedIndex: -1
                    property real pressX: 0
                    property real pressY: 0
                    
                    onPressed: function(mouse) {
                        // 查找点击的按键
                        for (var i = buttons.length - 1; i >= 0; i--) {
                            var btn = buttons[i];
                            var x = btn.x * canvas.width;
                            var y = btn.y * canvas.height;
                            var size = 40 * (btn.size || 1.0);
                            
                            if (mouse.x >= x - size/2 && mouse.x <= x + size/2 &&
                                mouse.y >= y - size/2 && mouse.y <= y + size/2) {
                                pressedIndex = i;
                                canvas.selectedIndex = i;
                                pressX = mouse.x - x;
                                pressY = mouse.y - y;
                                canvas.isDragging = true;
                                canvas.requestPaint();
                                return;
                            }
                        }
                        pressedIndex = -1;
                        canvas.selectedIndex = -1;
                        canvas.isDragging = false;
                        canvas.requestPaint();
                    }
                    
                    onPositionChanged: function(mouse) {
                        if (pressedIndex >= 0 && canvas.isDragging) {
                            var newX = (mouse.x - pressX) / canvas.width;
                            var newY = (mouse.y - pressY) / canvas.height;
                            newX = Math.max(0.05, Math.min(0.95, newX));
                            newY = Math.max(0.05, Math.min(0.95, newY));
                            buttons[pressedIndex].x = newX;
                            buttons[pressedIndex].y = newY;
                            canvas.requestPaint();
                        }
                    }
                    
                    onReleased: {
                        pressedIndex = -1;
                        canvas.isDragging = false;
                    }
                }
            }
        }
        
        // 按键列表
        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: 120
            model: buttons
            clip: true
            
            delegate: ItemDelegate {
                width: ListView.view.width
                height: 40
                highlighted: canvas.selectedIndex === index
                
                contentItem: RowLayout {
                    spacing: 10
                    
                    Label {
                        text: modelData.label + " (" + modelData.key + ")"
                        Layout.fillWidth: true
                    }
                    
                    Label {
                        text: "X:" + (modelData.x * 100).toFixed(0) + "% Y:" + (modelData.y * 100).toFixed(0) + "%"
                        color: Theme.currentTheme.colors.textSecondaryColor
                    }
                    
                    Button {
                        icon.name: "ic_fluent_delete_20_regular"
                        flat: true
                        onClicked: {
                            buttons.splice(index, 1);
                            if (canvas.selectedIndex === index) canvas.selectedIndex = -1;
                            canvas.requestPaint();
                        }
                    }
                }
                
                onClicked: {
                    canvas.selectedIndex = index;
                    canvas.requestPaint();
                }
            }
        }
        
        // 底部按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Button {
                text: Backend ? Backend.tr("添加按键") : "添加按键"
                icon.name: "ic_fluent_add_20_regular"
                onClicked: addKeyDialog.open()
            }
            
            Button {
                text: Backend ? Backend.tr("重置默认") : "重置默认"
                icon.name: "ic_fluent_arrow_reset_20_regular"
                onClicked: {
                    buttons = getDefaultButtons();
                    canvas.selectedIndex = -1;
                    canvas.requestPaint();
                }
            }
            
            Item { Layout.fillWidth: true }
            
            Button {
                text: Backend ? Backend.tr("取消") : "取消"
                flat: true
                onClicked: layoutEditorDialog.close()
            }
            
            Button {
                text: Backend ? Backend.tr("保存") : "保存"
                highlighted: true
                onClicked: {
                    layoutSaved(buttons);
                    layoutEditorDialog.close();
                }
            }
        }
    }
    
    // 添加按键对话框
    Dialog {
        id: addKeyDialog
        title: Backend ? Backend.tr("添加按键") : "添加按键"
        modal: true
        width: 300
        
        property string selectedKey: ""
        property string selectedLabel: ""
        
        ColumnLayout {
            spacing: 10
            
            Label {
                text: Backend ? Backend.tr("选择按键:") : "选择按键:"
            }
            
            Flow {
                Layout.fillWidth: true
                spacing: 8
                
                Repeater {
                    model: [
                        { key: "space", label: "空格" },
                        { key: "shift", label: "Shift" },
                        { key: "ctrl", label: "Ctrl" },
                        { key: "e", label: "E" },
                        { key: "q", label: "Q" },
                        { key: "f", label: "F" },
                        { key: "t", label: "T" },
                        { key: "r", label: "R" },
                        { key: "1", label: "1" },
                        { key: "2", label: "2" },
                        { key: "3", label: "3" },
                        { key: "4", label: "4" },
                        { key: "5", label: "5" }
                    ]
                    
                    delegate: Button {
                        text: modelData.label
                        checkable: true
                        checked: addKeyDialog.selectedKey === modelData.key
                        onClicked: {
                            addKeyDialog.selectedKey = modelData.key;
                            addKeyDialog.selectedLabel = modelData.label;
                        }
                    }
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                
                Item { Layout.fillWidth: true }
                
                Button {
                    text: Backend ? Backend.tr("取消") : "取消"
                    flat: true
                    onClicked: addKeyDialog.close()
                }
                
                Button {
                    text: Backend ? Backend.tr("添加") : "添加"
                    highlighted: true
                    enabled: addKeyDialog.selectedKey !== ""
                    onClicked: {
                        buttons.push({
                            "key": addKeyDialog.selectedKey,
                            "label": addKeyDialog.selectedLabel,
                            "x": 0.5,
                            "y": 0.5,
                            "size": 1.0
                        });
                        canvas.requestPaint();
                        addKeyDialog.selectedKey = "";
                        addKeyDialog.selectedLabel = "";
                        addKeyDialog.close();
                    }
                }
            }
        }
    }
}
