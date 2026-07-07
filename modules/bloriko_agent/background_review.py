"""
络可 后台记忆审查

每轮对话结束后，fork 一个 daemon 线程，用轻量 LLM 调用评估是否需要保存记忆。
参考 hermes-agent-main/agent/background_review.py，针对角色助手场景精简。

设计要点：
- 审查 LLM 只能调用 memory 工具，无其他工具权限
- 审查线程不触碰系统提示词快照（写入只更新磁盘和 live entries）
- 超时 30 秒，失败不影响主流程
- 审查使用与主 agent 相同的 API 凭证
"""

import json
import logging
import threading
import requests
from typing import Optional, List

from .memory import MemoryStore
from .threat_scanner import first_threat_message

log = logging.getLogger(__name__)

MEMORY_REVIEW_SYSTEM_PROMPT = """你是络可的记忆审查助手。你的唯一任务是回顾对话，判断是否需要保存记忆。

重点关注：
1. 用户是否透露了个人信息——姓名、昵称、偏好、习惯、情感状态？
2. 用户是否表达了关于络可行为方式的期望或纠正？
3. 是否有值得记住的事实（项目约定、技术偏好等）？

保存规则：
- 只保存持久事实，不保存临时状态或任务进度
- 用陈述句保存，不用指令（如"用户喜欢简洁的回复"而非"回复要简洁"）
- 每条记忆尽量简短独立

如果没有值得保存的内容，直接回复"无需保存"。"""

MEMORY_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "memory",
        "description": "管理络可的记忆。支持添加、替换、删除记忆条目。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "replace", "remove"]},
                "target": {"type": "string", "enum": ["memory", "user"]},
                "content": {"type": "string"},
                "old_text": {"type": "string"},
            },
            "required": ["action", "target"],
        },
    },
}

REVIEW_TIMEOUT = 30
MAX_MESSAGES_FOR_REVIEW = 20


def _trim_messages_for_review(messages: list) -> list:
    """截取最近的对话消息用于审查，避免发送过长上下文"""
    # 过滤出用户和助手消息
    relevant = []
    for msg in messages:
        role = msg.get("role", "")
        if role in ("user", "assistant"):
            content = msg.get("content", "")
            if content:
                relevant.append({"role": role, "content": content})

    # 只保留最近的 N 条
    return relevant[-MAX_MESSAGES_FOR_REVIEW:]


def _execute_review_memory_tool(memory_store: MemoryStore, tool_args: dict) -> str:
    """执行审查 LLM 发出的 memory 工具调用"""
    action = tool_args.get("action", "")
    target = tool_args.get("target", "")
    content = tool_args.get("content", "")
    old_text = tool_args.get("old_text", "")

    if action == "add":
        # 威胁扫描（与 MemoryStore.add 一致）
        scan_error = first_threat_message(content.strip()) if content.strip() else None
        if scan_error:
            log.warning(f"[BackgroundReview] 审查写入被威胁扫描阻止: {scan_error}")
            return json.dumps({"success": False, "error": scan_error}, ensure_ascii=False)
        result = memory_store.add(target, content)
    elif action == "replace":
        result = memory_store.replace(target, old_text, content)
    elif action == "remove":
        result = memory_store.remove(target, old_text)
    else:
        return json.dumps({"success": False, "error": f"未知操作 '{action}'"}, ensure_ascii=False)

    return json.dumps(result, ensure_ascii=False)


def run_background_review(
    api_url: str,
    auth_header: str,
    model: str,
    memory_store: MemoryStore,
    messages_snapshot: list,
) -> None:
    """运行后台记忆审查（同步，应在 daemon 线程中调用）"""
    try:
        trimmed = _trim_messages_for_review(messages_snapshot)
        if not trimmed:
            log.debug("[BackgroundReview] 无对话内容可审查")
            return

        # 构造审查请求
        review_messages = [
            {"role": "system", "content": MEMORY_REVIEW_SYSTEM_PROMPT},
        ]
        review_messages.extend(trimmed)
        review_messages.append({
            "role": "user",
            "content": "请审查上面的对话，判断是否需要保存记忆。",
        })

        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header

        payload = {
            "model": model,
            "messages": review_messages,
            "tools": [MEMORY_TOOL_DEFINITION],
            "tool_choice": "auto",
            "stream": False,
            "max_tokens": 512,
        }

        log.info(f"[BackgroundReview] 开始审查, 消息数={len(trimmed)}")
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=REVIEW_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        # 处理工具调用
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            log.debug("[BackgroundReview] 无需保存记忆")
            return

        for tc in tool_calls:
            tc_name = tc.get("function", {}).get("name", "")
            if tc_name != "memory":
                log.warning(f"[BackgroundReview] 审查 LLM 尝试调用非 memory 工具: {tc_name}")
                continue

            tc_args_str = tc.get("function", {}).get("arguments", "{}")
            try:
                tc_args = json.loads(tc_args_str) if isinstance(tc_args_str, str) else tc_args_str
            except json.JSONDecodeError:
                log.warning(f"[BackgroundReview] 审查工具参数解析失败: {tc_args_str}")
                continue

            result_str = _execute_review_memory_tool(memory_store, tc_args)
            log.info(f"[BackgroundReview] 审查写入结果: {result_str[:100]}")

        log.info("[BackgroundReview] 审查完成")

    except requests.exceptions.Timeout:
        log.debug("[BackgroundReview] 审查超时，跳过")
    except Exception as e:
        log.warning(f"[BackgroundReview] 审查异常: {e}")


def spawn_background_review_thread(
    api_url: str,
    auth_header: str,
    model: str,
    memory_store: MemoryStore,
    messages_snapshot: list,
) -> threading.Thread:
    """创建并启动后台审查 daemon 线程"""
    thread = threading.Thread(
        target=run_background_review,
        args=(api_url, auth_header, model, memory_store, messages_snapshot),
        daemon=True,
        name="bloriko-background-review",
    )
    thread.start()
    log.info("[BackgroundReview] 审查线程已启动")
    return thread
