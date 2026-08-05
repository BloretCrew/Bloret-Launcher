.pragma library

/**
 * Shared helpers for collapsing consecutive tool_call rows into Claude-style
 * summary groups: 「查看了 5 个文件，编辑了 6 个文件，…」
 */

// .pragma library 无 QML 上下文属性；文案用中文，需要 i18n 时由调用方再包 Backend.tr
function tr(s, fallback) {
    return fallback !== undefined ? fallback : s
}

/** Map tool name → summary category key */
function toolCategory(name) {
    switch (name) {
    case "read_file":
    case "list_files":
    case "search_text":
    case "get_directory_tree":
    case "get_pack_info":
    case "analyze_pack":
    case "get_file_tree":
    case "read_language":
    case "validate_json":
        return "view"
    case "write_file":
    case "edit_file":
    case "edit_language":
        return "edit"
    case "execute_command":
    case "execute_command_background":
        return "command"
    case "set_emotion":
        return "emotion"
    case "memory":
        return "memory"
    case "ask_user":
        return "ask"
    case "spawn_agent":
        return "spawn"
    default:
        return "other"
    }
}

function categoryLabel(cat, count) {
    // Claude Code style plurals in Chinese
    switch (cat) {
    case "view":
        return count === 1
            ? tr("查看了 1 个文件", "查看了 1 个文件")
            : tr("查看了 %1 个文件", "查看了 %1 个文件").replace("%1", count)
    case "edit":
        return count === 1
            ? tr("编辑了 1 个文件", "编辑了 1 个文件")
            : tr("编辑了 %1 个文件", "编辑了 %1 个文件").replace("%1", count)
    case "command":
        return count === 1
            ? tr("执行了 1 个命令", "执行了 1 个命令")
            : tr("执行了 %1 个命令", "执行了 %1 个命令").replace("%1", count)
    case "emotion":
        return tr("更新了情感", "更新了情感")
    case "memory":
        return tr("更新了记忆", "更新了记忆")
    case "ask":
        return count === 1
            ? tr("向用户提问 1 次", "向用户提问 1 次")
            : tr("向用户提问 %1 次", "向用户提问 %1 次").replace("%1", count)
    case "spawn":
        return count === 1
            ? tr("启动了 1 个子 Agent", "启动了 1 个子 Agent")
            : tr("启动了 %1 个子 Agent", "启动了 %1 个子 Agent").replace("%1", count)
    default:
        return count === 1
            ? tr("使用了 1 个工具", "使用了 1 个工具")
            : tr("使用了 %1 个工具", "使用了 %1 个工具").replace("%1", count)
    }
}

/** Preferred display order for summary fragments */
var CATEGORY_ORDER = ["view", "edit", "command", "emotion", "memory", "ask", "spawn", "other"]

/**
 * Build summary string from an array of tool call objects
 * each: { toolName, toolArgs, toolResult }
 */
function summarizeTools(tools) {
    if (!tools || tools.length === 0)
        return ""
    var counts = {}
    for (var i = 0; i < tools.length; i++) {
        var cat = toolCategory(tools[i].toolName || tools[i].name || "")
        counts[cat] = (counts[cat] || 0) + 1
    }
    var parts = []
    for (var o = 0; o < CATEGORY_ORDER.length; o++) {
        var c = CATEGORY_ORDER[o]
        if (counts[c])
            parts.push(categoryLabel(c, counts[c]))
    }
    return parts.join(tr("，", "，"))
}

function toolDisplayName(name) {
    var map = {
        "read_file": tr("读取", "读取"),
        "write_file": tr("写入", "写入"),
        "edit_file": tr("编辑", "编辑"),
        "list_files": tr("列出文件", "列出文件"),
        "search_text": tr("搜索", "搜索"),
        "get_directory_tree": tr("查看目录树", "查看目录树"),
        "get_pack_info": tr("资源包信息", "资源包信息"),
        "analyze_pack": tr("分析资源包", "分析资源包"),
        "get_file_tree": tr("文件树", "文件树"),
        "read_language": tr("读取语言", "读取语言"),
        "edit_language": tr("编辑语言", "编辑语言"),
        "validate_json": tr("校验 JSON", "校验 JSON"),
        "ask_user": tr("向用户提问", "向用户提问"),
        "execute_command": tr("执行命令", "执行命令"),
        "execute_command_background": tr("后台执行", "后台执行"),
        "spawn_agent": tr("生成子 Agent", "生成子 Agent"),
        "memory": tr("管理记忆", "管理记忆"),
        "set_emotion": tr("更新情感", "更新情感")
    }
    return map[name] || name
}

function toolArgsSummary(name, argsJson) {
    var a = ""
    try {
        var obj = typeof argsJson === "string" ? JSON.parse(argsJson || "{}") : (argsJson || {})
        if (name === "read_file" || name === "write_file" || name === "edit_file" || name === "validate_json")
            a = obj.path || ""
        else if (name === "list_files")
            a = obj.pattern || "*"
        else if (name === "search_text")
            a = obj.query || ""
        else if (name === "get_directory_tree")
            a = obj.path || ""
        else if (name === "ask_user")
            a = obj.question || ""
        else if (name === "execute_command" || name === "execute_command_background")
            a = obj.command || ""
        else if (name === "spawn_agent")
            a = (obj.agent_type || "general") + ": " + (obj.prompt || "").substring(0, 40)
        else if (name === "memory")
            a = (obj.action || "") + " " + (obj.target || "") + ": " + (obj.content || obj.old_text || "").substring(0, 30)
        else if (name === "set_emotion")
            a = obj.emotion || ""
        else if (name === "read_language" || name === "edit_language")
            a = obj.lang || ""
        else {
            var parts = []
            for (var k in obj) {
                var v = String(obj[k])
                if (v.length > 40) v = v.substring(0, 40) + "…"
                parts.push(v)
            }
            a = parts.join(", ")
        }
        if (a.length > 80) a = a.substring(0, 80) + "…"
    } catch (e) {
        a = String(argsJson || "")
        if (a.length > 80) a = a.substring(0, 80) + "…"
    }
    return a
}

function toolLineLabel(tool) {
    var n = tool.toolName || tool.name || ""
    var a = toolArgsSummary(n, tool.toolArgs || tool.arguments || "")
    var display = toolDisplayName(n)
    return a ? (display + " " + a) : display
}

function emptyMsgFields() {
    return {
        imagesJson: "[]",
        toolName: "",
        toolArgs: "",
        toolResult: "",
        toolsJson: "[]",
        streaming: false,
        expanded: false
    }
}

function makeToolEntry(toolName, argsJson, result) {
    return {
        toolName: toolName || "",
        toolArgs: argsJson || "",
        toolResult: result || ""
    }
}

function parseToolsJson(s) {
    try {
        var arr = JSON.parse(s || "[]")
        return Array.isArray(arr) ? arr : []
    } catch (e) {
        return []
    }
}

/**
 * Collapse consecutive raw tool_call history messages into tool_group rows.
 * Input: array of history message objects from getHistoryMessages / similar.
 * Output: array suitable for messageModel.append (with toolsJson).
 */
function collapseHistoryMessages(msgs) {
    var out = []
    var i = 0
    while (i < msgs.length) {
        var m = msgs[i]
        if (m.role === "tool_call") {
            var batch = []
            while (i < msgs.length && msgs[i].role === "tool_call") {
                batch.push(makeToolEntry(msgs[i].toolName, msgs[i].toolArgs, msgs[i].toolResult))
                i++
            }
            out.push({
                role: "tool_group",
                content: summarizeTools(batch),
                imagesJson: "[]",
                toolName: "",
                toolArgs: "",
                toolResult: "",
                toolsJson: JSON.stringify(batch),
                streaming: false,
                expanded: false
            })
        } else {
            var imgs = m.imagesJson || "[]"
            if ((!imgs || imgs === "[]") && m.images && m.images.length)
                imgs = JSON.stringify(m.images)
            out.push({
                role: m.role,
                content: m.content || "",
                imagesJson: imgs || "[]",
                toolName: m.toolName || "",
                toolArgs: m.toolArgs || "",
                toolResult: m.toolResult || "",
                toolsJson: "[]",
                streaming: false,
                expanded: false
            })
            i++
        }
    }
    return out
}
