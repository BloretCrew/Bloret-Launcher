"""
络可 Agent 核心循环

实现 Agent 的主要逻辑：
1. 接收用户消息
2. 调用 LLM（带工具定义，流式 SSE）
3. 解析响应（流式文本 + 工具调用）
4. 执行工具
5. 将结果反馈给 LLM
6. 重复直到 LLM 返回纯文本响应（无工具调用）
"""

import json
import hashlib
import threading
import logging
import time
import traceback
import requests
from pathlib import Path
from typing import Callable, Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .tools import (
    TOOL_DEFINITIONS, TOOL_EXECUTORS, execute_tool,
    READ_ONLY_TOOLS, WRITE_TOOLS,
    SUB_AGENT_TYPES, SPAWN_AGENT_TOOL,
    _get_tools_for_agent,
)
from .system_prompt import build_system_prompt

log = logging.getLogger(__name__)

# 最大迭代次数，防止无限循环
MAX_ITERATIONS = 30

# 重试配置
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]

# 上下文压缩阈值（粗略 token 估算）
DEFAULT_TOKEN_LIMIT = 50000

# Doom Loop 检测阈值
DOOM_LOOP_THRESHOLD = 3

# Agent 模式配置
AGENT_ROLES = {
    "auto": {"allowed_tools": None, "auto_approve": True, "description": "自动模式"},
    "accept_edits": {"allowed_tools": None, "auto_approve": False, "description": "接受编辑"},
    "plan": {"allowed_tools": READ_ONLY_TOOLS, "auto_approve": False, "description": "规划模式"},
}
DEFAULT_ROLE = "accept_edits"


# ============================================================
# Sub-Agent 执行
# ============================================================

def run_sub_agent(
    working_dir: str,
    api_url: str,
    auth_header: str,
    prompt: str,
    agent_type: str = "general",
    model: str = "Bloriko",
    parent_role: str = "accept_edits",
    memory_store=None,
    on_emotion_change: Optional[Callable] = None,
) -> str:
    """同步运行子 Agent，返回最终文本结果"""
    agent_config = SUB_AGENT_TYPES.get(agent_type, SUB_AGENT_TYPES["general"])
    system_prompt_override = None
    allowed_tools = agent_config.get("allowed_tools")

    log.info(f"[SubAgent] 启动子 Agent: type={agent_type}, model={model}")

    tools = _get_tools_for_agent(allowed_tools)

    sub_agent = BlorikoAgentLoop(
        working_dir=working_dir,
        api_url=api_url,
        auth_header=auth_header,
        model=model,
        role=parent_role,
        memory_store=memory_store,
        on_emotion_change=on_emotion_change,
    )
    sub_agent._tools = tools
    sub_agent._system_prompt_override = system_prompt_override

    result_text = ""
    try:
        sub_agent._run_internal(prompt)
        result_text = sub_agent._current_text or ""
    except Exception as e:
        log.error(f"[SubAgent] 子 Agent 异常: {e}", exc_info=True)
        result_text = f"子 Agent 执行出错: {str(e)}"

    log.info(f"[SubAgent] 子 Agent 完成, 结果长度={len(result_text)}")
    return result_text


def _execute_spawn_agent(working_dir: Path, prompt: str, agent_type: str = "general", **kwargs) -> str:
    """spawn_agent 工具的执行器"""
    api_url = kwargs.get("_api_url", "")
    auth_header = kwargs.get("_auth_header", "")
    model = kwargs.get("_model", "Bloriko")
    role = kwargs.get("_role", DEFAULT_ROLE)
    memory_store = kwargs.get("_memory_store")
    on_emotion_change = kwargs.get("_on_emotion_change")

    return run_sub_agent(
        working_dir=str(working_dir),
        api_url=api_url,
        auth_header=auth_header,
        prompt=prompt,
        agent_type=agent_type,
        model=model,
        parent_role=role,
        memory_store=memory_store,
        on_emotion_change=on_emotion_change,
    )


# 注册 spawn_agent 执行器
TOOL_EXECUTORS[SPAWN_AGENT_TOOL] = _execute_spawn_agent


class BlorikoAgentLoop:
    """络可 Agent 核心循环"""

    def __init__(
        self,
        working_dir: str,
        api_url: str,
        auth_header: str,
        on_text_chunk: Optional[Callable[[str], None]] = None,
        on_tool_call_start: Optional[Callable[[str, str], None]] = None,
        on_tool_call_end: Optional[Callable[[str, str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
        on_permission_request: Optional[Callable[[str, str], bool]] = None,
        on_ask_user: Optional[Callable[[str, str, list], str]] = None,
        on_emotion_change: Optional[Callable[[str], None]] = None,
        model: str = "Bloriko",
        role: str = "default",
        token_limit: int = DEFAULT_TOKEN_LIMIT,
        memory_store=None,
    ):
        self.working_dir = Path(working_dir)
        self.api_url = api_url
        self.auth_header = auth_header
        self.on_text_chunk = on_text_chunk
        self.on_tool_call_start = on_tool_call_start
        self.on_tool_call_end = on_tool_call_end
        self.on_error = on_error
        self.on_done = on_done
        self.on_permission_request = on_permission_request
        self.on_ask_user = on_ask_user
        self.on_emotion_change = on_emotion_change
        self.model = model
        self.role = role
        self.token_limit = token_limit
        self.memory_store = memory_store
        self._cancelled = False
        self._recent_tool_calls: List[str] = []
        self._tools = None
        self._system_prompt_override = None
        self._current_text = ""
        self._cached_system_prompt = None
        self._current_emotion = "neutral"
        self._last_llm_error = ""
        self._last_llm_retryable = True
        self._has_extracted_memory = False

    def cancel(self):
        self._cancelled = True

    def run(self, user_message: str, history: list = None):
        log.info(f"[AgentLoop] run 开始, 模型={self.model}, 角色={self.role}")
        try:
            self._run_internal(user_message, history)
        except Exception as e:
            log.error(f"[AgentLoop] 循环异常: {e}", exc_info=True)
            traceback.print_exc()
            if self.on_error:
                self.on_error(f"Agent 执行出错: {str(e)}")
        finally:
            log.info("[AgentLoop] run 结束，触发 on_done")
            if self.on_done:
                self.on_done()

    # ================================================================
    # 系统提示词
    # ================================================================

    def _build_system_prompt(self) -> str:
        if self._system_prompt_override:
            return self._system_prompt_override
        if self._cached_system_prompt:
            return self._cached_system_prompt
        prompt = build_system_prompt(
            memory_store=self.memory_store,
            working_dir=str(self.working_dir),
            current_emotion=self._current_emotion,
        )
        self._cached_system_prompt = prompt
        return prompt

    def invalidate_system_prompt(self):
        """失效系统提示缓存（记忆写入后调用，使新记忆在下次 LLM 调用时生效）"""
        self._cached_system_prompt = None

    def get_cached_system_prompt(self) -> Optional[str]:
        """获取已缓存的系统提示（供外部保存跨会话复用）"""
        return self._cached_system_prompt

    # ================================================================
    # 上下文压缩
    # ================================================================

    @staticmethod
    def _estimate_tokens(messages: list) -> int:
        return len(str(messages)) // 4

    def _compact_messages(self, messages: list) -> list:
        if len(messages) <= 1:
            return messages

        result = [messages[0]]

        tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
        keep_recent = max(2, len(tool_indices) // 3) * 3
        recent_tool_ids = set()
        if tool_indices:
            for idx in tool_indices[-keep_recent:]:
                recent_tool_ids.add(messages[idx].get("tool_call_id", ""))

        for i, msg in enumerate(messages[1:], 1):
            role = msg.get("role", "")
            if role == "tool":
                tc_id = msg.get("tool_call_id", "")
                if tc_id in recent_tool_ids:
                    result.append(msg)
                else:
                    original_len = len(msg.get("content", ""))
                    compacted = dict(msg)
                    compacted["content"] = f"[结果已压缩: 原始长度 {original_len} 字符]"
                    result.append(compacted)
            elif role == "assistant":
                content = msg.get("content", "")
                if len(content) > 2000:
                    compacted = dict(msg)
                    compacted["content"] = content[:500] + "...[已压缩]"
                    result.append(compacted)
                else:
                    result.append(msg)
            else:
                result.append(msg)

        return result

    def _extract_memory_before_compress(self, messages: list) -> None:
        """压缩前从即将丢弃的消息中提取有价值的记忆。

        只在每个会话中执行一次，用轻量 LLM 调用提取事实。
        失败不影响压缩流程。
        """
        self._has_extracted_memory = True

        if not self.memory_store:
            return

        # 收集非系统提示词的消息文本（系统提示词不会被压缩丢弃）
        discadable = []
        for msg in messages[1:]:  # 跳过 system prompt
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content and role in ("user", "assistant"):
                discadable.append(f"[{role}]: {content[:500]}")

        if not discadable:
            return

        # 只取前 3000 字符，避免请求过大
        context_text = "\n".join(discadable)[-3000:]

        extraction_prompt = (
            "从以下对话片段中提取值得长期记住的事实。\n"
            "只提取持久事实（用户偏好、个人信息、项目约定），不提取临时状态。\n"
            "每条事实一行，用陈述句。如果没有值得记住的内容，返回空列表。\n\n"
            f"{context_text}\n\n"
            "请以 JSON 数组格式返回，例如：[\"用户喜欢简洁的回复\", \"项目使用 PySide6\"]"
        )

        try:
            headers = {"Content-Type": "application/json"}
            if self.auth_header:
                headers["Authorization"] = self.auth_header

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是记忆提取助手，从对话中提取持久事实。只返回 JSON 数组。"},
                    {"role": "user", "content": extraction_prompt},
                ],
                "max_tokens": 256,
                "stream": False,
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # 解析 JSON 数组
            if text.startswith("["):
                facts = json.loads(text)
            elif "```" in text:
                import re
                match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
                facts = json.loads(match.group(1)) if match else []
            else:
                facts = []

            for fact in facts:
                if isinstance(fact, str) and fact.strip():
                    result = self.memory_store.add("memory", fact.strip())
                    if result.get("success"):
                        log.info(f"[AgentLoop] 压缩前提取记忆: '{fact.strip()[:50]}'")

        except Exception as e:
            log.warning(f"[AgentLoop] 压缩前记忆提取失败（不影响压缩）: {e}")

    # ================================================================
    # Doom Loop 检测
    # ================================================================

    def _check_doom_loop(self, tool_name: str, tool_args: dict) -> bool:
        args_str = json.dumps(tool_args, sort_keys=True)
        sig = f"{tool_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
        self._recent_tool_calls.append(sig)

        if len(self._recent_tool_calls) > 20:
            self._recent_tool_calls = self._recent_tool_calls[-20:]

        if len(self._recent_tool_calls) >= DOOM_LOOP_THRESHOLD:
            recent = self._recent_tool_calls[-DOOM_LOOP_THRESHOLD:]
            if len(set(recent)) == 1:
                return True
        return False

    # ================================================================
    # 错误重试
    # ================================================================

    def _should_retry(self, status_code: int) -> bool:
        return status_code in RETRYABLE_STATUS_CODES

    def _cancelable_sleep(self, seconds: float) -> bool:
        elapsed = 0.0
        while elapsed < seconds:
            if self._cancelled:
                return True
            time.sleep(min(0.5, seconds - elapsed))
            elapsed += 0.5
        return False

    # ================================================================
    # 工具执行（含权限检查）
    # ================================================================

    def _execute_tool_with_permission(
        self, tc_name: str, tc_args: dict, tc_args_json: str
    ) -> str:
        log.info(f"[AgentLoop] 执行工具: {tc_name}")

        role_config = AGENT_ROLES.get(self.role, AGENT_ROLES[DEFAULT_ROLE])
        allowed = role_config.get("allowed_tools")
        if allowed is not None and tc_name not in allowed:
            log.warning(f"[AgentLoop] 工具 {tc_name} 被模式 '{role_config['description']}' 禁止")
            return f"错误: 当前模式 '{role_config['description']}' 不允许使用 {tc_name} 工具"

        if self._check_doom_loop(tc_name, tc_args):
            log.warning(f"[AgentLoop] 检测到 Doom Loop: {tc_name}")
            return (
                f"警告: 检测到重复操作。你已经连续 {DOOM_LOOP_THRESHOLD} 次以相同参数调用 "
                f"{tc_name}。请停止重复并尝试其他方法，或直接告知用户问题所在。"
            )

        # 权限检查（写入工具需要确认，特殊工具跳过）
        if tc_name in WRITE_TOOLS and self.on_permission_request:
            if role_config.get("auto_approve", False):
                log.info(f"[AgentLoop] 自动模式，跳过权限请求: {tc_name}")
            else:
                desc = self._describe_write_operation(tc_name, tc_args)
                log.info(f"[AgentLoop] 写入工具需要权限: {tc_name}, 描述: {desc}")
                approved = self.on_permission_request(tc_name, desc)
                if not approved:
                    log.info(f"[AgentLoop] 用户拒绝了 {tc_name}")
                    return "操作被用户拒绝。请告知用户该操作已被取消。"

        # 构造额外参数
        extra_kwargs = {
            "_api_url": self.api_url,
            "_auth_header": self.auth_header,
            "_model": self.model,
            "_role": self.role,
            "_memory_store": self.memory_store,
            "_on_emotion_change": self.on_emotion_change,
            "_on_ask_user": self.on_ask_user,
        }

        log.info(f"[AgentLoop] 调用 execute_tool({tc_name})")
        result = execute_tool(self.working_dir, tc_name, tc_args, **extra_kwargs)
        log.info(f"[AgentLoop] 工具结果长度: {len(result)}")
        return result

    @staticmethod
    def _describe_write_operation(tool_name: str, args: dict) -> str:
        if tool_name == "write_file":
            path = args.get("path", "未知")
            content_len = len(args.get("content", ""))
            return f"写入文件: {path} ({content_len} 字符)"
        elif tool_name == "edit_file":
            path = args.get("path", "未知")
            old_text = args.get("old_text", "")[:50]
            return f"编辑文件: {path} (替换 '{old_text}...')"
        elif tool_name == "execute_command":
            cmd = args.get("command", "未知")
            return f"前台执行命令: {cmd}"
        elif tool_name == "execute_command_background":
            cmd = args.get("command", "未知")
            return f"后台执行命令: {cmd}"
        return f"执行写入操作: {tool_name}"

    # ================================================================
    # 主循环
    # ================================================================

    @staticmethod
    def _convert_history_for_api(history: list) -> list:
        result = []
        for msg in history:
            role = msg.get("role", "")
            if role == "tool_call":
                tool_name = msg.get("toolName", "")
                tool_args_str = msg.get("toolArgs", "{}")
                tool_result = msg.get("toolResult", "")

                try:
                    tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                except json.JSONDecodeError:
                    tool_args = {}

                tc_id = f"call_{hashlib.md5(f'{tool_name}:{tool_args_str}'.encode()).hexdigest()[:12]}"

                result.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args, ensure_ascii=False)
                        }
                    }]
                })
                result.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": tool_result
                })
            else:
                result.append(msg)
        return result

    def _run_internal(self, user_message: str, history: list = None):
        log.info("[AgentLoop] 构建系统提示词...")
        system_prompt = self._build_system_prompt()
        log.info(f"[AgentLoop] 系统提示词长度: {len(system_prompt)} 字符")
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            converted = self._convert_history_for_api(history)
            messages.extend(converted)
            log.info(f"[AgentLoop] 历史消息数: {len(history)} (转换后 {len(converted)} 条)")

        messages.append({"role": "user", "content": user_message})
        log.info(f"[AgentLoop] 总消息数: {len(messages)} (含系统提示)")

        for iteration in range(MAX_ITERATIONS):
            if self._cancelled:
                log.info("[AgentLoop] Agent 已被取消")
                return

            estimated_tokens = self._estimate_tokens(messages)
            if estimated_tokens > self.token_limit:
                log.info(f"[AgentLoop] 上下文过大 ({estimated_tokens} tokens)，执行压缩")
                if not self._has_extracted_memory:
                    self._extract_memory_before_compress(messages)
                messages = self._compact_messages(messages)

            log.info(f"[AgentLoop] 迭代 {iteration + 1}/{MAX_ITERATIONS}, 消息数={len(messages)}, 估算tokens={estimated_tokens}")

            result = self._call_llm_streaming_with_retry(messages)
            if result is None:
                log.warning("[AgentLoop] LLM 调用返回 None，退出循环")
                return

            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            log.info(f"[AgentLoop] LLM 响应: 内容长度={len(content)}, 工具调用数={len(tool_calls)}")

            if not tool_calls:
                assistant_msg = {"role": "assistant", "content": content}
                messages.append(assistant_msg)
                log.info("[AgentLoop] Agent 完成（无工具调用）")
                return

            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            # 分区工具调用：只读 vs 写入
            read_calls = []
            write_calls = []
            for tc in tool_calls:
                tc_name = tc.get("function", {}).get("name", "")
                if tc_name in READ_ONLY_TOOLS:
                    read_calls.append(tc)
                else:
                    write_calls.append(tc)

            if read_calls:
                self._execute_read_tools_parallel(read_calls, messages)

            for tc in write_calls:
                if self._cancelled:
                    return
                self._execute_single_tool(tc, messages)
                # 记忆写入后检查是否需要重建快照并失效系统提示缓存
                if tc.get("function", {}).get("name") == "memory":
                    self.memory_store.increment_write_count()
                    if self.memory_store.should_invalidate_snapshot():
                        self.memory_store.rebuild_snapshots_from_live()
                        self.invalidate_system_prompt()
                        log.info("[AgentLoop] 记忆写入已达阈值，快照重建，系统提示缓存失效")
                    else:
                        log.info(f"[AgentLoop] 记忆已更新（快照保持冻结，第{self.memory_store._write_count}次写入）")

        if self.on_text_chunk:
            self.on_text_chunk("\n\n⚠ 已达到最大操作次数限制，请尝试简化你的请求。")

    def _execute_single_tool(self, tc: dict, messages: list):
        tc_id = tc.get("id", "")
        tc_name = tc.get("function", {}).get("name", "")
        tc_args_str = tc.get("function", {}).get("arguments", "{}")

        try:
            tc_args = json.loads(tc_args_str) if isinstance(tc_args_str, str) else tc_args_str
        except json.JSONDecodeError:
            tc_args = {}

        tc_args_json = json.dumps(tc_args, ensure_ascii=False)
        log.info(f"执行工具: {tc_name}({tc_args_json[:200]})")

        if self.on_tool_call_start:
            self.on_tool_call_start(tc_name, tc_args_json)

        result_str = self._execute_tool_with_permission(tc_name, tc_args, tc_args_json)

        # 记录情感变化，供系统提示词使用
        if tc_name == "set_emotion" and tc_args.get("emotion"):
            self._current_emotion = tc_args["emotion"]

        max_result_len = 50000
        if len(result_str) > max_result_len:
            result_str = result_str[:max_result_len] + f"\n... (结果过长，已截断，原始长度: {len(result_str)})"

        log.info(f"工具结果 ({tc_name}): {result_str[:200]}...")

        if self.on_tool_call_end:
            self.on_tool_call_end(tc_name, tc_args_json, result_str)

        messages.append({
            "role": "tool",
            "tool_call_id": tc_id,
            "content": result_str,
        })

    def _execute_read_tools_parallel(self, tool_calls: list, messages: list):
        if len(tool_calls) == 1:
            self._execute_single_tool(tool_calls[0], messages)
            return

        tc_info = []
        for tc in tool_calls:
            tc_name = tc.get("function", {}).get("name", "")
            tc_args_str = tc.get("function", {}).get("arguments", "{}")
            try:
                tc_args = json.loads(tc_args_str) if isinstance(tc_args_str, str) else tc_args_str
            except json.JSONDecodeError:
                tc_args = {}
            tc_args_json = json.dumps(tc_args, ensure_ascii=False)
            tc_info.append((tc, tc_name, tc_args, tc_args_json))

            if self.on_tool_call_start:
                self.on_tool_call_start(tc_name, tc_args_json)

        def run_tool(info):
            tc, tc_name, tc_args, tc_args_json = info
            if self._cancelled:
                return tc, "操作已取消"

            extra_kwargs = {
                "_api_url": self.api_url,
                "_auth_header": self.auth_header,
                "_model": self.model,
                "_role": self.role,
                "_memory_store": self.memory_store,
                "_on_emotion_change": self.on_emotion_change,
                "_on_ask_user": self.on_ask_user,
            }
            result = execute_tool(self.working_dir, tc_name, tc_args, **extra_kwargs)
            return tc, result

        with ThreadPoolExecutor(max_workers=min(4, len(tc_info))) as executor:
            futures = {executor.submit(run_tool, info): info for info in tc_info}
            for future in as_completed(futures):
                if self._cancelled:
                    return
                tc, result_str = future.result()

                tc_id = tc.get("id", "")
                tc_name = tc.get("function", {}).get("name", "")
                tc_args_str = tc.get("function", {}).get("arguments", "{}")
                tc_args_json = tc_args_str if isinstance(tc_args_str, str) else json.dumps(tc_args_str, ensure_ascii=False)

                max_result_len = 50000
                if len(result_str) > max_result_len:
                    result_str = result_str[:max_result_len] + f"\n... (结果过长，已截断)"

                if self.on_tool_call_end:
                    self.on_tool_call_end(tc_name, tc_args_json, result_str)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_str,
                })

    # ================================================================
    # LLM 调用（含重试）
    # ================================================================

    def _call_llm_streaming_with_retry(self, messages: list) -> Optional[dict]:
        for attempt in range(MAX_RETRIES + 1):
            if self._cancelled:
                return None

            log.info(f"[AgentLoop] LLM 调用尝试 {attempt + 1}/{MAX_RETRIES + 1}")
            self._last_llm_error = ""
            self._last_llm_retryable = True
            result = self._call_llm_streaming(messages)

            if result is not None:
                return result

            if not self._last_llm_retryable:
                break

            if attempt >= MAX_RETRIES:
                break

            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            log.info(f"[AgentLoop] 将在 {delay} 秒后重试")
            if self._cancelable_sleep(delay):
                return None

        if self.on_error and self._last_llm_error:
            self.on_error(self._last_llm_error)
        return None

    def _call_llm_streaming(self, messages: list) -> Optional[dict]:
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self._tools or _get_tools_for_agent(None),
            "tool_choice": "auto",
            "stream": True,
        }

        log.info(f"[AgentLoop] LLM 请求: url='{self.api_url}', model='{self.model}', messages={len(messages)}条")
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120,
                stream=True,
            )
            log.info(f"[AgentLoop] HTTP 响应状态: {response.status_code}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_detail = ""
            if e.response is not None:
                try:
                    error_detail = e.response.text[:500]
                except Exception:
                    pass
            log_fn = log.warning if self._should_retry(status_code) else log.error
            log_fn(f"[AgentLoop] HTTP 错误: status={status_code}, body={error_detail}", exc_info=True)
            if status_code == 401:
                self._last_llm_error = "认证失败：API Key 无效或已过期，请在 Bloret PassPort /ai 页面重新创建 API Key"
                self._last_llm_retryable = False
            elif self._should_retry(status_code):
                self._last_llm_error = f"请求失败 (HTTP {status_code})"
                self._last_llm_retryable = True
                return None
            else:
                self._last_llm_error = f"请求失败 (HTTP {status_code}): {error_detail[:200]}"
                self._last_llm_retryable = False
            return None
        except requests.exceptions.RequestException as e:
            log.warning(f"[AgentLoop] 网络请求异常: {e}", exc_info=True)
            self._last_llm_error = f"网络请求失败: {str(e)}"
            self._last_llm_retryable = True
            return None

        # 解析 SSE 流
        accumulated_text = ""
        tool_calls_map = {}

        try:
            buffer = ""
            for chunk_bytes in response.iter_content(chunk_size=None):
                if self._cancelled:
                    return None
                if not chunk_bytes:
                    continue

                text = chunk_bytes.decode("utf-8", errors="replace")
                buffer += text

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if not line.startswith("data: "):
                        continue

                    data_str = line[len("data: "):]
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})

                    delta_content = delta.get("content")
                    if delta_content:
                        accumulated_text += delta_content
                        if self.on_text_chunk:
                            self._current_text = accumulated_text
                            self.on_text_chunk(accumulated_text)

                    delta_tool_calls = delta.get("tool_calls", [])
                    for dtc in delta_tool_calls:
                        idx = dtc.get("index", 0)
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": dtc.get("id", ""),
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        tc = tool_calls_map[idx]

                        if dtc.get("id"):
                            tc["id"] = dtc["id"]

                        fn = dtc.get("function", {})
                        if fn.get("name"):
                            tc["function"]["name"] = fn["name"]

                        if fn.get("arguments"):
                            tc["function"]["arguments"] += fn["arguments"]

            # 处理 buffer 中剩余数据
            if buffer.strip():
                line = buffer.strip()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[len("data: "):])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            accumulated_text += delta["content"]
                        for dtc in delta.get("tool_calls", []):
                            idx = dtc.get("index", 0)
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {
                                    "id": dtc.get("id", ""),
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            tc = tool_calls_map[idx]
                            if dtc.get("id"):
                                tc["id"] = dtc["id"]
                            fn = dtc.get("function", {})
                            if fn.get("name"):
                                tc["function"]["name"] = fn["name"]
                            if fn.get("arguments"):
                                tc["function"]["arguments"] += fn["arguments"]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        pass

        except Exception as e:
            log.warning(f"SSE 解析异常: {e}", exc_info=True)
            self._last_llm_error = f"流式响应解析失败: {str(e)}"
            self._last_llm_retryable = True
            return None

        tool_calls = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            if not tc["id"]:
                tc["id"] = f"call_{idx}"
            tool_calls.append(tc)

        log.info(f"[AgentLoop] SSE 解析完成: 累积文本={len(accumulated_text)}字符, 工具调用={len(tool_calls)}个")
        if tool_calls:
            for tc in tool_calls:
                fn = tc.get("function", {})
                log.info(f"[AgentLoop]   工具: {fn.get('name', '?')}(args_len={len(fn.get('arguments', ''))})")

        return {
            "content": accumulated_text,
            "tool_calls": tool_calls,
        }


def run_agent_async(
    working_dir: str,
    api_url: str,
    auth_header: str,
    user_message: str,
    history: list = None,
    on_text_chunk: Optional[Callable[[str], None]] = None,
    on_tool_call_start: Optional[Callable[[str, str], None]] = None,
    on_tool_call_end: Optional[Callable[[str, str, str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[], None]] = None,
    on_permission_request: Optional[Callable[[str, str], bool]] = None,
    on_ask_user: Optional[Callable[[str, str, list], str]] = None,
    on_emotion_change: Optional[Callable[[str], None]] = None,
    model: str = "Bloriko",
    role: str = "default",
    token_limit: int = DEFAULT_TOKEN_LIMIT,
    memory_store=None,
) -> BlorikoAgentLoop:
    """在后台线程中启动 Agent"""
    agent = BlorikoAgentLoop(
        working_dir=working_dir,
        api_url=api_url,
        auth_header=auth_header,
        on_text_chunk=on_text_chunk,
        on_tool_call_start=on_tool_call_start,
        on_tool_call_end=on_tool_call_end,
        on_error=on_error,
        on_done=on_done,
        on_permission_request=on_permission_request,
        on_ask_user=on_ask_user,
        on_emotion_change=on_emotion_change,
        model=model,
        role=role,
        token_limit=token_limit,
        memory_store=memory_store,
    )

    thread = threading.Thread(target=agent.run, args=(user_message, history), daemon=True)
    log.info(f"[AgentLoop] Agent 线程已启动")
    thread.start()
    return agent


def generate_title(api_url: str, auth_header: str, user_message: str, model: str = "Bloriko") -> str:
    """生成简短的对话标题"""
    log.info(f"[Title] 开始生成标题, model='{model}'")
    headers = {"Content-Type": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个对话标题生成器。根据用户的请求，用不超过15个字概括对话主题。只输出标题，不要任何其他内容。"},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
    }

    last_error = None
    for attempt in range(2):
        try:
            resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            title = resp.json()["choices"][0]["message"]["content"].strip()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt == 0:
                log.warning(f"[Title] 标题生成请求失败，将重试: {e}")
                time.sleep(1)
                continue
            raise
    else:
        raise last_error or RuntimeError("标题生成失败")

    log.info(f"[Title] 生成标题: '{title}'")
    return title
