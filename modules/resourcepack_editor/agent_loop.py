"""
资源包 AI Agent 核心循环

实现 Agent 的主要逻辑：
1. 接收用户消息
2. 调用 LLM（带工具定义，流式 SSE）
3. 解析响应（流式文本 + 工具调用）
4. 执行工具
5. 将结果反馈给 LLM
6. 重复直到 LLM 返回纯文本响应（无工具调用）
"""

import json
import threading
import logging
import requests
from pathlib import Path
from typing import Callable, Optional

from .agent_tools import TOOL_DEFINITIONS, execute_tool

log = logging.getLogger(__name__)

# 最大迭代次数，防止无限循环
MAX_ITERATIONS = 30

# 系统提示词模板
SYSTEM_PROMPT_TEMPLATE = """你是百络谷资源包编辑器的 AI 助手。你可以帮助用户创建和编辑 Minecraft 资源包。

你当前正在编辑的资源包: {pack_path}

你的能力（通过工具调用）：
- read_file: 读取文件内容
- write_file: 写入文件
- edit_file: 精确替换文件中的文本
- list_files: 列出匹配模式的文件
- search_text: 搜索文件内容
- get_pack_info: 获取资源包基本信息
- analyze_pack: 分析资源包结构
- read_language: 读取语言文件
- edit_language: 编辑语言文件（添加/修改/删除条目）
- validate_json: 验证 JSON 格式
- get_file_tree: 获取文件树

规则：
1. 所有文件路径都是相对于资源包根目录的
2. 修改文件前，先用 read_file 确认当前内容
3. 修改后告知用户做了什么改动
4. JSON 文件必须保持有效格式（用 validate_json 验证）
5. 对于批量操作，先列出计划再执行
6. 如果不确定用户的意图，先提问
7. 回复使用中文
"""


class AgentLoop:
    """AI Agent 核心循环"""

    def __init__(
        self,
        pack_path: str,
        api_url: str,
        auth_header: str,
        on_text_chunk: Optional[Callable[[str], None]] = None,
        on_tool_call_start: Optional[Callable[[str, str], None]] = None,
        on_tool_call_end: Optional[Callable[[str, str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
        model: str = "Bloriko",
    ):
        self.pack_path = Path(pack_path)
        self.api_url = api_url
        self.auth_header = auth_header
        self.on_text_chunk = on_text_chunk
        self.on_tool_call_start = on_tool_call_start
        self.on_tool_call_end = on_tool_call_end
        self.on_error = on_error
        self.on_done = on_done
        self.model = model
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self, user_message: str, history: list = None):
        try:
            self._run_internal(user_message, history)
        except Exception as e:
            log.error(f"Agent 循环异常: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"Agent 执行出错: {str(e)}")
        finally:
            if self.on_done:
                self.on_done()

    def _run_internal(self, user_message: str, history: list = None):
        """内部执行逻辑"""
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(pack_path=str(self.pack_path))
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        for iteration in range(MAX_ITERATIONS):
            if self._cancelled:
                log.info("Agent 已被取消")
                return

            log.info(f"Agent 迭代 {iteration + 1}/{MAX_ITERATIONS}")

            # 流式调用 LLM
            result = self._call_llm_streaming(messages)
            if result is None:
                return

            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])

            # 没有工具调用 → 完成
            if not tool_calls:
                assistant_msg = {"role": "assistant", "content": content}
                messages.append(assistant_msg)
                log.info("Agent 完成（无工具调用）")
                return

            # 有工具调用 → 构建 assistant 消息（含 tool_calls）
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            # 执行每个工具
            for tc in tool_calls:
                if self._cancelled:
                    return

                tc_id = tc.get("id", "")
                tc_name = tc.get("function", {}).get("name", "")
                tc_args_str = tc.get("function", {}).get("arguments", "{}")

                try:
                    tc_args = json.loads(tc_args_str) if isinstance(tc_args_str, str) else tc_args_str
                except json.JSONDecodeError:
                    tc_args = {}

                log.info(f"执行工具: {tc_name}({json.dumps(tc_args, ensure_ascii=False)[:200]})")

                if self.on_tool_call_start:
                    self.on_tool_call_start(tc_name, json.dumps(tc_args, ensure_ascii=False))

                result_str = execute_tool(self.pack_path, tc_name, tc_args)

                max_result_len = 50000
                if len(result_str) > max_result_len:
                    result_str = result_str[:max_result_len] + f"\n... (结果过长，已截断，原始长度: {len(result_str)})"

                log.info(f"工具结果 ({tc_name}): {result_str[:200]}...")

                if self.on_tool_call_end:
                    self.on_tool_call_end(tc_name, json.dumps(tc_args, ensure_ascii=False), result_str)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_str,
                })

        if self.on_text_chunk:
            self.on_text_chunk("\n\n⚠ 已达到最大操作次数限制，请尝试简化你的请求。")

    def _call_llm_streaming(self, messages: list) -> Optional[dict]:
        """流式调用 LLM API

        Returns:
            {"content": str, "tool_calls": [...] } 或 None（出错时）
        """
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "stream": True,
        }

        try:
            log.debug(f"调用 LLM (流式): {len(messages)} 条消息")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120,
                stream=True,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP 错误: {e}", exc_info=True)
            if e.response and e.response.status_code == 401:
                if self.on_error:
                    self.on_error("认证失败，请检查登录状态或选择其他模型")
            else:
                if self.on_error:
                    self.on_error(f"请求失败: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"请求异常: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"网络请求失败: {str(e)}")
            return None

        # 解析 SSE 流
        accumulated_text = ""
        # tool_calls 累积器: {index: {"id": "", "name": "", "arguments": ""}}
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

                    # 文本内容
                    delta_content = delta.get("content")
                    if delta_content:
                        accumulated_text += delta_content
                        if self.on_text_chunk:
                            self.on_text_chunk(accumulated_text)

                    # 工具调用增量
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

                        # 更新 id
                        if dtc.get("id"):
                            tc["id"] = dtc["id"]

                        # 更新函数名
                        fn = dtc.get("function", {})
                        if fn.get("name"):
                            tc["function"]["name"] = fn["name"]

                        # 追加参数片段
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
                    except (json.JSONDecodeError, IndexError, KeyError):
                        pass

        except Exception as e:
            log.error(f"SSE 解析异常: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"流式响应解析失败: {str(e)}")
            return None

        # 组装结果
        tool_calls = []
        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            # 清理空 id
            if not tc["id"]:
                tc["id"] = f"call_{idx}"
            tool_calls.append(tc)

        return {
            "content": accumulated_text,
            "tool_calls": tool_calls,
        }


def run_agent_async(
    pack_path: str,
    api_url: str,
    auth_header: str,
    user_message: str,
    history: list = None,
    on_text_chunk: Optional[Callable[[str], None]] = None,
    on_tool_call_start: Optional[Callable[[str, str], None]] = None,
    on_tool_call_end: Optional[Callable[[str, str, str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_done: Optional[Callable[[], None]] = None,
    model: str = "Bloriko",
) -> AgentLoop:
    """在后台线程中启动 Agent"""
    agent = AgentLoop(
        pack_path=pack_path,
        api_url=api_url,
        auth_header=auth_header,
        on_text_chunk=on_text_chunk,
        on_tool_call_start=on_tool_call_start,
        on_tool_call_end=on_tool_call_end,
        on_error=on_error,
        on_done=on_done,
        model=model,
    )

    thread = threading.Thread(target=agent.run, args=(user_message, history), daemon=True)
    thread.start()
    return agent
