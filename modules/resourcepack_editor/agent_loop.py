from modules.i18n import i18nText
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
import hashlib
import threading
import logging
import time
import traceback
import requests
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .agent_tools import (
    TOOL_DEFINITIONS, TOOL_EXECUTORS, execute_tool,
    READ_ONLY_TOOLS, WRITE_TOOLS,
    SUB_AGENT_TYPES, SPAWN_AGENT_TOOL,
)
from .knowledge_base import (
    AGENT_SYSTEM_PROMPT_TEMPLATE, PACK_FORMAT_TABLE,
    build_dynamic_context,
)

log = logging.getLogger(__name__)

# 最大迭代次数，防止无限循环
MAX_ITERATIONS = 30

# 重试配置
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # 秒

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
# 默认模式（fallback）
DEFAULT_ROLE = "accept_edits"


# ============================================================
# Sub-Agent 工具过滤
# ============================================================

def _get_tools_for_agent(allowed_tools):
    """根据工具白名单过滤工具定义"""
    if allowed_tools is None:
        # 全部工具，但排除 spawn_agent（防递归）
        return [t for t in TOOL_DEFINITIONS if t["function"]["name"] != SPAWN_AGENT_TOOL]
    return [t for t in TOOL_DEFINITIONS if t["function"]["name"] in allowed_tools]


# ============================================================
# Sub-Agent 执行
# ============================================================

def run_sub_agent(
    pack_path: str,
    api_url: str,
    auth_header: str,
    prompt: str,
    agent_type: str = "general",
    model: str = "Bloriko",
    parent_role: str = "accept_edits",
) -> str:
    """同步运行子 Agent，返回最终文本结果"""
    agent_config = SUB_AGENT_TYPES.get(agent_type, SUB_AGENT_TYPES["general"])
    system_prompt_override = agent_config.get("system_prompt")
    allowed_tools = agent_config.get("allowed_tools")

    log.info(f"[SubAgent] 启动子 Agent: type={agent_type}, model={model}")
    print(f"[SubAgent DEBUG] 启动: type={agent_type}, prompt='{prompt[:60]}...'")

    # 创建子 Agent 的工具过滤列表
    tools = _get_tools_for_agent(allowed_tools)

    # 创建子 AgentLoop（无回调，静默运行）
    sub_agent = AgentLoop(
        pack_path=pack_path,
        api_url=api_url,
        auth_header=auth_header,
        model=model,
        role=parent_role,
    )

    # 覆盖工具定义
    sub_agent._tools = tools

    # 覆盖系统提示词
    if system_prompt_override:
        sub_agent._system_prompt_override = system_prompt_override
    else:
        sub_agent._system_prompt_override = None

    # 同步运行
    result_text = ""
    try:
        sub_agent._run_internal(prompt)
        result_text = sub_agent._current_text or ""
    except Exception as e:
        log.error(f"[SubAgent] 子 Agent 异常: {e}", exc_info=True)
        result_text = f"子 Agent 执行出错: {str(e)}"

    log.info(f"[SubAgent] 子 Agent 完成, 结果长度={len(result_text)}")
    print(f"[SubAgent DEBUG] 完成, 结果长度={len(result_text)}")
    return result_text


def _execute_spawn_agent(pack_path: Path, prompt: str, agent_type: str = "general", **kwargs) -> str:
    """spawn_agent 工具的执行器"""
    # 从 kwargs 获取父 Agent 的配置
    api_url = kwargs.get("_api_url", "")
    auth_header = kwargs.get("_auth_header", "")
    model = kwargs.get("_model", "Bloriko")
    role = kwargs.get("_role", DEFAULT_ROLE)

    return run_sub_agent(
        pack_path=str(pack_path),
        api_url=api_url,
        auth_header=auth_header,
        prompt=prompt,
        agent_type=agent_type,
        model=model,
        parent_role=role,
    )


# 注册 spawn_agent 执行器
TOOL_EXECUTORS[SPAWN_AGENT_TOOL] = _execute_spawn_agent


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
        on_permission_request: Optional[Callable[[str, str], bool]] = None,
        on_ask_user: Optional[Callable[[str, str, list], str]] = None,
        model: str = "Bloriko",
        role: str = "default",
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ):
        self.pack_path = Path(pack_path)
        self.api_url = api_url
        self.auth_header = auth_header
        self.on_text_chunk = on_text_chunk
        self.on_tool_call_start = on_tool_call_start
        self.on_tool_call_end = on_tool_call_end
        self.on_error = on_error
        self.on_done = on_done
        self.on_permission_request = on_permission_request
        self.on_ask_user = on_ask_user
        self.model = model
        self.role = role
        self.token_limit = token_limit
        self._cancelled = False
        self._recent_tool_calls: List[str] = []
        self._tools = None  # 工具过滤列表（None=使用默认）
        self._system_prompt_override = None  # 系统提示词覆盖（None=使用默认）
        self._current_text = ""  # 累积的文本内容
        self._last_llm_error = ""
        self._last_llm_retryable = True

    def cancel(self):
        self._cancelled = True

    def run(self, user_message: str, history: list = None):
        log.info(f"[AgentLoop] run 开始, 模型={self.model}, 角色={self.role}, 消息='{user_message[:50]}...'" if len(user_message) > 50 else f"[AgentLoop] run 开始, 模型={self.model}, 角色={self.role}, 消息='{user_message}'")
        print(f"[AgentLoop DEBUG] run 开始, 模型={self.model}, url={self.api_url}")
        try:
            self._run_internal(user_message, history)
        except Exception as e:
            log.error(f"[AgentLoop] 循环异常: {e}", exc_info=True)
            print(f"[AgentLoop DEBUG] 循环异常: {e}")
            traceback.print_exc()
            if self.on_error:
                self.on_error(f"Agent 执行出错: {str(e)}")
        finally:
            log.info("[AgentLoop] run 结束，触发 on_done")
            print("[AgentLoop DEBUG] run 结束")
            if self.on_done:
                self.on_done()

    # ================================================================
    # 动态系统提示词
    # ================================================================

    def _build_system_prompt(self) -> str:
        """构建动态系统提示词，注入资源包知识和元数据"""
        # 子 Agent 使用覆盖的系统提示
        if self._system_prompt_override:
            log.info("[SubAgent] 使用子 Agent 覆盖系统提示")
            return self._system_prompt_override

        log.info(f"[AgentLoop] 构建系统提示词, pack_path='{self.pack_path}'")
        pack_path = str(self.pack_path)

        # 收集动态上下文
        mcmeta_data = None
        file_stats = None
        namespaces = None

        # 读取 pack.mcmeta
        try:
            mcmeta_path = self.pack_path / "pack.mcmeta"
            if mcmeta_path.exists():
                mcmeta_data = json.loads(mcmeta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

        # 文件统计
        try:
            all_files = [f for f in self.pack_path.rglob("*") if f.is_file()]
            textures_count = 0
            models_count = 0
            blockstates_count = 0
            sounds_count = 0
            fonts_count = 0
            particles_count = 0

            assets_dir = self.pack_path / "assets"
            if assets_dir.exists():
                namespaces = [d.name for d in assets_dir.iterdir() if d.is_dir()]
                for ns in namespaces:
                    ns_dir = assets_dir / ns
                    tex_dir = ns_dir / "textures"
                    if tex_dir.exists():
                        textures_count += len([f for f in tex_dir.rglob("*") if f.is_file() and f.suffix.lower() in (".png", ".mcmeta")])
                    model_dir = ns_dir / "models"
                    if model_dir.exists():
                        models_count += len([f for f in model_dir.rglob("*.json") if f.is_file()])
                    bs_dir = ns_dir / "blockstates"
                    if bs_dir.exists():
                        blockstates_count += len([f for f in bs_dir.rglob("*.json") if f.is_file()])
                    sounds_dir = ns_dir / "sounds"
                    if sounds_dir.exists():
                        sounds_count += len([f for f in sounds_dir.rglob("*") if f.is_file()])
                    font_dir = ns_dir / "font"
                    if font_dir.exists():
                        fonts_count += len([f for f in font_dir.rglob("*.json") if f.is_file()])
                    particle_dir = ns_dir / "particles"
                    if particle_dir.exists():
                        particles_count += len([f for f in particle_dir.rglob("*.json") if f.is_file()])

            file_stats = {
                "total_files": len(all_files),
                "total_size_kb": sum(f.stat().st_size for f in all_files) // 1024,
                "textures_count": textures_count,
                "models_count": models_count,
                "blockstates_count": blockstates_count,
                "sounds_count": sounds_count,
                "fonts_count": fonts_count,
                "particles_count": particles_count,
            }
        except Exception:
            pass

        # 构建动态上下文
        dynamic_context = build_dynamic_context(self.pack_path, mcmeta_data, file_stats, namespaces)

        # 当前时间
        dynamic_context += f"\n当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # 角色信息
        role_config = AGENT_ROLES.get(self.role, AGENT_ROLES[DEFAULT_ROLE])
        dynamic_context += f"\n当前模式: {role_config['description']}"

        # 使用知识库模板构建完整提示词
        prompt = AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            pack_path=pack_path,
            dynamic_context=dynamic_context,
        )

        log.info(f"[AgentLoop] 系统提示词构建完成, 长度={len(prompt)}字符")
        return prompt

    # ================================================================
    # 上下文压缩
    # ================================================================

    @staticmethod
    def _estimate_tokens(messages: list) -> int:
        """粗略估算消息列表的 token 数量"""
        return len(str(messages)) // 4

    def _compact_messages(self, messages: list) -> list:
        """压缩旧的工具结果以减少上下文大小

        策略：
        - 保留系统消息（index 0）
        - 保留最近 2 轮工具结果
        - 压缩更早的工具结果内容
        """
        if len(messages) <= 1:
            return messages

        result = [messages[0]]  # 保留系统消息

        # 找出所有 tool 消息的位置
        tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]

        # 保留最近的工具结果（不压缩）
        keep_recent = max(2, len(tool_indices) // 3) * 3  # 保留最近约 1/3
        recent_tool_ids = set()
        if tool_indices:
            for idx in tool_indices[-keep_recent:]:
                recent_tool_ids.add(messages[idx].get("tool_call_id", ""))

        for i, msg in enumerate(messages[1:], 1):
            if i == 0:
                continue
            role = msg.get("role", "")

            if role == "tool":
                tc_id = msg.get("tool_call_id", "")
                if tc_id in recent_tool_ids:
                    result.append(msg)  # 保留
                else:
                    # 压缩旧的工具结果
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

    # ================================================================
    # Doom Loop 检测
    # ================================================================

    def _check_doom_loop(self, tool_name: str, tool_args: dict) -> bool:
        """检查是否陷入重复调用循环。返回 True 表示检测到循环。"""
        import hashlib as _hl
        args_str = json.dumps(tool_args, sort_keys=True)
        sig = f"{tool_name}:{_hl.md5(args_str.encode()).hexdigest()}"
        self._recent_tool_calls.append(sig)

        # 只保留最近的记录
        if len(self._recent_tool_calls) > 20:
            self._recent_tool_calls = self._recent_tool_calls[-20:]

        # 检查最后 N 次是否完全相同
        if len(self._recent_tool_calls) >= DOOM_LOOP_THRESHOLD:
            recent = self._recent_tool_calls[-DOOM_LOOP_THRESHOLD:]
            if len(set(recent)) == 1:
                return True
        return False

    # ================================================================
    # 错误重试
    # ================================================================

    def _should_retry(self, status_code: int) -> bool:
        """判断是否应该重试"""
        return status_code in RETRYABLE_STATUS_CODES

    def _cancelable_sleep(self, seconds: float) -> bool:
        """可取消的睡眠。返回 True 表示被取消。"""
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
        """执行工具，包含权限检查和 Doom Loop 检测"""
        log.info(f"[AgentLoop] 执行工具: {tc_name}")

        # 角色权限检查
        role_config = AGENT_ROLES.get(self.role, AGENT_ROLES[DEFAULT_ROLE])
        allowed = role_config.get("allowed_tools")
        if allowed is not None and tc_name not in allowed:
            log.warning(f"[AgentLoop] 工具 {tc_name} 被模式 '{role_config['description']}' 禁止")
            return f"错误: 当前模式 '{role_config['description']}' 不允许使用 {tc_name} 工具"

        # Doom Loop 检测
        if self._check_doom_loop(tc_name, tc_args):
            log.warning(f"[AgentLoop] 检测到 Doom Loop: {tc_name}")
            return (
                f"警告: 检测到重复操作。你已经连续 {DOOM_LOOP_THRESHOLD} 次以相同参数调用 "
                f"{tc_name}。请停止重复并尝试其他方法，或直接告知用户问题所在。"
            )

        # 权限检查（写入工具需要确认）
        if tc_name in WRITE_TOOLS and self.on_permission_request:
            # 自动模式下自动批准
            if role_config.get("auto_approve", False):
                log.info(f"[AgentLoop] 自动模式，跳过权限请求: {tc_name}")
            else:
                desc = self._describe_write_operation(tc_name, tc_args)
                log.info(f"[AgentLoop] 写入工具需要权限: {tc_name}, 描述: {desc}")
                approved = self.on_permission_request(tc_name, desc)
                if not approved:
                    log.info(f"[AgentLoop] 用户拒绝了 {tc_name}")
                    return i18nText("操作被用户拒绝。请告知用户该操作已被取消。")

        # 执行工具
        log.info(f"[AgentLoop] 调用 execute_tool({tc_name})")
        result = execute_tool(self.pack_path, tc_name, tc_args,
                              _api_url=self.api_url, _auth_header=self.auth_header,
                              _model=self.model, _role=self.role)
        log.info(f"[AgentLoop] 工具结果长度: {len(result)}")
        return result

    @staticmethod
    def _describe_write_operation(tool_name: str, args: dict) -> str:
        """生成写入操作的描述"""
        if tool_name == "write_file":
            path = args.get("path", "未知")
            content_len = len(args.get("content", ""))
            return f"写入文件: {path} ({content_len} 字符)"
        elif tool_name == "edit_file":
            path = args.get("path", "未知")
            old_text = args.get("old_text", "")[:50]
            return f"编辑文件: {path} (替换 '{old_text}...')"
        elif tool_name == "edit_language":
            lang = args.get("lang", "未知")
            changes = args.get("changes", {})
            return f"编辑语言文件: {lang}.json ({len(changes)} 项修改)"
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
        """将自定义 tool_call 历史格式转换为 OpenAI API 格式

        我们的持久化格式:
          {"role": "tool_call", "toolName": ..., "toolArgs": ..., "toolResult": ...}

        OpenAI API 格式:
          assistant message with tool_calls + tool message with result
        """
        result = []
        for msg in history:
            role = msg.get("role", "")
            if role == "tool_call":
                tool_name = msg.get("toolName", "")
                tool_args_str = msg.get("toolArgs", "{}")
                tool_result = msg.get("toolResult", "")

                # 尝试解析参数为 JSON
                try:
                    tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                except json.JSONDecodeError:
                    tool_args = {}

                # 生成一个稳定的 tool_call_id
                tc_id = f"call_{hashlib.md5(f'{tool_name}:{tool_args_str}'.encode()).hexdigest()[:12]}"

                # 添加 assistant 消息（含 tool_calls）
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

                # 添加 tool 结果消息
                result.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": tool_result
                })
            else:
                # user / assistant 消息直接保留
                result.append(msg)

        return result

    def _run_internal(self, user_message: str, history: list = None):
        """内部执行逻辑"""
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

            # 上下文压缩检查
            estimated_tokens = self._estimate_tokens(messages)
            if estimated_tokens > self.token_limit:
                log.info(f"[AgentLoop] 上下文过大 ({estimated_tokens} tokens)，执行压缩")
                messages = self._compact_messages(messages)
                if self.on_text_chunk and iteration > 0:
                    pass

            log.info(f"[AgentLoop] 迭代 {iteration + 1}/{MAX_ITERATIONS}, 消息数={len(messages)}, 估算tokens={estimated_tokens}")

            # 流式调用 LLM（含重试）
            result = self._call_llm_streaming_with_retry(messages)
            if result is None:
                log.warning("[AgentLoop] LLM 调用返回 None，退出循环")
                return

            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            log.info(f"[AgentLoop] LLM 响应: 内容长度={len(content)}, 工具调用数={len(tool_calls)}")

            # 没有工具调用 → 完成
            if not tool_calls:
                assistant_msg = {"role": "assistant", "content": content}
                messages.append(assistant_msg)
                log.info("[AgentLoop] Agent 完成（无工具调用）")
                return

            # 有工具调用 → 构建 assistant 消息（含 tool_calls）
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

            # 并发执行只读工具
            if read_calls:
                self._execute_read_tools_parallel(read_calls, messages)

            # 串行执行写入工具
            for tc in write_calls:
                if self._cancelled:
                    return
                self._execute_single_tool(tc, messages)

        if self.on_text_chunk:
            self.on_text_chunk("\n\n⚠ 已达到最大操作次数限制，请尝试简化你的请求。")

    def _execute_single_tool(self, tc: dict, messages: list):
        """执行单个工具调用"""
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

        # 特殊处理 ask_user 工具
        if tc_name == "ask_user" and self.on_ask_user:
            question = tc_args.get("question", "")
            question_type = tc_args.get("question_type", "text")
            options_raw = tc_args.get("options", "")
            # 支持两种格式：数组或 ||| 分隔的字符串
            if isinstance(options_raw, list):
                options = options_raw
            elif isinstance(options_raw, str) and options_raw:
                options = [o.strip() for o in options_raw.split("|||") if o.strip()]
            else:
                options = []
            result_str = self.on_ask_user(question, question_type, options)
        else:
            result_str = self._execute_tool_with_permission(tc_name, tc_args, tc_args_json)

        # 截断过长结果
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
        """并发执行只读工具"""
        if len(tool_calls) == 1:
            # 只有一个，直接执行
            self._execute_single_tool(tool_calls[0], messages)
            return

        # 通知所有工具开始
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

        # 并发执行
        def run_tool(info):
            tc, tc_name, tc_args, tc_args_json = info
            if self._cancelled:
                return tc, "操作已取消"
            result = execute_tool(self.pack_path, tc_name, tc_args,
                              _api_url=self.api_url, _auth_header=self.auth_header,
                              _model=self.model, _role=self.role)
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
        """带重试的 LLM 调用"""
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            if self._cancelled:
                log.info("[AgentLoop] 重试循环: 已取消")
                return None

            log.info(f"[AgentLoop] LLM 调用尝试 {attempt + 1}/{MAX_RETRIES + 1}")
            self._last_llm_error = ""
            self._last_llm_retryable = True
            result = self._call_llm_streaming(messages)

            if result is not None:
                log.info(f"[AgentLoop] LLM 调用成功")
                return result

            log.warning(f"[AgentLoop] LLM 调用返回 None (尝试 {attempt + 1})")

            if not self._last_llm_retryable:
                log.error("[AgentLoop] 遇到不可重试错误，停止重试")
                break

            # 如果是最后一次尝试，直接返回
            if attempt >= MAX_RETRIES:
                log.error(f"[AgentLoop] 已达最大重试次数 ({MAX_RETRIES})，放弃")
                break

            # 等待后重试
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            log.info(f"[AgentLoop] 将在 {delay} 秒后重试 (尝试 {attempt + 2}/{MAX_RETRIES + 1})")
            if self._cancelable_sleep(delay):
                return None

        if self.on_error and self._last_llm_error:
            self.on_error(self._last_llm_error)
        return None

    def _should_retry_error(self, error_msg: str) -> bool:
        """判断错误是否可重试"""
        # 网络错误和限流可以重试
        retryable_keywords = ["超时", "限流", "网络", "连接", "timeout", "rate limit", "429", "500", "502", "503", "504"]
        error_lower = error_msg.lower()
        return any(kw in error_lower for kw in retryable_keywords)

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
            "tools": self._tools or _get_tools_for_agent(None),
            "tool_choice": "auto",
            "stream": True,
        }

        log.info(f"[AgentLoop] LLM 请求: url='{self.api_url}', model='{self.model}', messages={len(messages)}条")
        print(f"[AgentLoop DEBUG] LLM 请求: url='{self.api_url}', model='{self.model}', messages={len(messages)}条")
        try:
            log.debug(f"[AgentLoop] 发送请求...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120,
                stream=True,
            )
            log.info(f"[AgentLoop] HTTP 响应状态: {response.status_code}")
            print(f"[AgentLoop DEBUG] HTTP 响应状态: {response.status_code}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            # 尝试读取响应体以获取错误详情
            error_detail = ""
            if e.response is not None:
                try:
                    error_detail = e.response.text[:500]
                except Exception:
                    pass
            log_fn = log.warning if self._should_retry(status_code) else log.error
            log_fn(f"[AgentLoop] HTTP 错误: status={status_code}, body={error_detail}", exc_info=True)
            print(f"[AgentLoop DEBUG] HTTP 错误: status={status_code}, body={error_detail}")
            if status_code == 401:
                self._last_llm_error = "认证失败，请检查登录状态或选择其他模型"
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
            print(f"[AgentLoop DEBUG] 网络请求异常: {e}")
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

                    # 文本内容
                    delta_content = delta.get("content")
                    if delta_content:
                        accumulated_text += delta_content
                        if self.on_text_chunk:
                            self._current_text = accumulated_text
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
                        # 也处理剩余的工具调用增量
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

        # 组装结果
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
    on_permission_request: Optional[Callable[[str, str], bool]] = None,
    on_ask_user: Optional[Callable[[str, str, list], str]] = None,
    model: str = "Bloriko",
    role: str = "default",
    token_limit: int = DEFAULT_TOKEN_LIMIT,
) -> AgentLoop:
    """在后台线程中启动 Agent"""
    print(f"[AgentLoop DEBUG] run_agent_async: url='{api_url}', model='{model}', pack='{pack_path}'")
    agent = AgentLoop(
        pack_path=pack_path,
        api_url=api_url,
        auth_header=auth_header,
        on_text_chunk=on_text_chunk,
        on_tool_call_start=on_tool_call_start,
        on_tool_call_end=on_tool_call_end,
        on_error=on_error,
        on_done=on_done,
        on_permission_request=on_permission_request,
        on_ask_user=on_ask_user,
        model=model,
        role=role,
        token_limit=token_limit,
    )

    thread = threading.Thread(target=agent.run, args=(user_message, history), daemon=True)
    print(f"[AgentLoop DEBUG] Agent 线程已启动, thread_id={thread.ident}")
    thread.start()
    return agent


def generate_title(api_url: str, auth_header: str, user_message: str, model: str = "Bloriko") -> str:
    """生成简短的对话标题（同步调用，单次 LLM 请求）"""
    log.info(f"[Title] 开始生成标题, model='{model}', url='{api_url}'")
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
            log.info(f"[Title] HTTP 状态: {resp.status_code}")
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
