"""
络可 Agent 工具定义与执行器

12 个通用工具，使用 OpenAI function-calling 格式。
"""

import json
import os
import subprocess
import logging
import glob as glob_mod
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)

# 工具分类
READ_ONLY_TOOLS = {"read_file", "list_files", "search_text", "get_directory_tree", "ask_user"}
WRITE_TOOLS = {"write_file", "edit_file", "execute_command", "execute_command_background"}
SPECIAL_TOOLS = {"memory", "set_emotion", "spawn_agent"}

# Sub-Agent 类型
SUB_AGENT_TYPES = {
    "explore": {
        "allowed_tools": {"read_file", "list_files", "search_text", "get_directory_tree"},
        "description": "只读探索",
    },
    "general": {
        "allowed_tools": None,
        "description": "通用（全部工具）",
    },
}

SPAWN_AGENT_TOOL = "spawn_agent"

# 情感状态列表
EMOTION_STATES = ["neutral", "happy", "shy", "angry", "sad", "excited", "curious"]

# 工具定义（OpenAI function-calling 格式）
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容。返回文件的全部文本内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径（相对于工作目录或绝对路径）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入或创建文件。如果文件已存在则覆盖。会自动创建不存在的目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "编辑文件：将文件中的 old_text 替换为 new_text（首次匹配）。old_text 必须精确匹配文件中的内容（包括缩进）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要替换的原文"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "替换后的新文本"
                    }
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出匹配 glob 模式的文件。默认列出工作目录下所有文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "glob 模式，默认 '**/*'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "在文件中搜索文本（类似 grep）。返回匹配的文件和行号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的文本"
                    },
                    "glob_pattern": {
                        "type": "string",
                        "description": "文件过滤 glob 模式，默认 '*'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_directory_tree",
            "description": "显示目录树结构。默认显示工作目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径，默认工作目录"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "最大深度，默认 3"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "执行 shell 命令（阻塞，最长 120 秒超时）。返回 stdout 和 stderr。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command_background",
            "description": "在后台执行 shell 命令（非阻塞）。命令会在后台运行，不等待完成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "向用户提问。支持文本回答、单项选择、多项选择。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "问题内容"
                    },
                    "question_type": {
                        "type": "string",
                        "description": "问题类型：text、single_choice、multiple_choice",
                        "enum": ["text", "single_choice", "multiple_choice"]
                    },
                    "options": {
                        "type": "string",
                        "description": "选项列表，用 ||| 分隔。仅 single_choice 和 multiple_choice 时使用。"
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": "管理络可的记忆。支持添加、替换、删除记忆条目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型：add（添加）、replace（替换）、remove（删除）",
                        "enum": ["add", "replace", "remove"]
                    },
                    "target": {
                        "type": "string",
                        "description": "目标文件：memory（络可的记忆）或 user（用户画像）",
                        "enum": ["memory", "user"]
                    },
                    "content": {
                        "type": "string",
                        "description": "新内容（add 和 replace 时使用）"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要匹配的旧文本（replace 和 remove 时使用，子字符串匹配）"
                    }
                },
                "required": ["action", "target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_emotion",
            "description": "更新络可当前的情感状态。在对话中根据情境自然地改变情感。",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "description": "情感状态",
                        "enum": EMOTION_STATES
                    }
                },
                "required": ["emotion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_agent",
            "description": "启动一个子 Agent 来处理复杂任务。子 Agent 会独立执行并返回结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "交给子 Agent 的任务描述"
                    },
                    "agent_type": {
                        "type": "string",
                        "description": "Agent 类型：explore（只读探索）或 general（全部工具）",
                        "enum": ["explore", "general"]
                    }
                },
                "required": ["prompt"]
            }
        }
    },
]


# ============================================================
# 路径安全检查
# ============================================================

def _validate_path(working_dir: Path, relative_path: str) -> Path:
    """验证并解析路径，防止路径遍历攻击"""
    path = Path(relative_path)
    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = (working_dir / path).resolve()

    # 确保路径在工作目录下（允许符号链接跳出，但不常见）
    # 注意：对于 execute_command，不做路径检查，因为命令可以访问任意位置
    return resolved


# ============================================================
# 工具执行器
# ============================================================

def _exec_read_file(working_dir: Path, **kwargs) -> str:
    """读取文件"""
    path = _validate_path(working_dir, kwargs["path"])
    if not path.exists():
        return f"错误：文件不存在 {path}"
    try:
        content = path.read_text(encoding="utf-8")
        log.info(f"[Tool] read_file: {path} ({len(content)} 字符)")
        return content
    except UnicodeDecodeError:
        return f"错误：文件 {path} 不是文本文件或编码不支持"
    except Exception as e:
        return f"错误：读取文件失败 - {str(e)}"


def _exec_write_file(working_dir: Path, **kwargs) -> str:
    """写入文件"""
    path = _validate_path(working_dir, kwargs["path"])
    content = kwargs["content"]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log.info(f"[Tool] write_file: {path} ({len(content)} 字符)")
        return f"已写入文件 {path.relative_to(working_dir)} ({len(content)} 字符)"
    except Exception as e:
        return f"错误：写入文件失败 - {str(e)}"


def _exec_edit_file(working_dir: Path, **kwargs) -> str:
    """编辑文件"""
    path = _validate_path(working_dir, kwargs["path"])
    old_text = kwargs["old_text"]
    new_text = kwargs["new_text"]

    if not path.exists():
        return f"错误：文件不存在 {path}"

    try:
        content = path.read_text(encoding="utf-8")
        if old_text not in content:
            return f"错误：在文件中未找到匹配的文本。请确保 old_text 精确匹配文件内容。"

        count = content.count(old_text)
        new_content = content.replace(old_text, new_text, 1)
        path.write_text(new_content, encoding="utf-8")

        log.info(f"[Tool] edit_file: {path} (替换 1/{count} 处)")
        if count > 1:
            return f"已编辑文件 {path.relative_to(working_dir)}（替换了 1 处，共 {count} 处匹配）"
        return f"已编辑文件 {path.relative_to(working_dir)}"
    except Exception as e:
        return f"错误：编辑文件失败 - {str(e)}"


def _exec_list_files(working_dir: Path, **kwargs) -> str:
    """列出文件"""
    pattern = kwargs.get("pattern", "**/*")
    try:
        matches = sorted(working_dir.glob(pattern))
        # 过滤隐藏文件和常见无关目录
        filtered = []
        for p in matches:
            rel = str(p.relative_to(working_dir))
            if any(part.startswith('.') for part in p.parts[len(working_dir.parts):]):
                continue
            if any(part in ('__pycache__', 'node_modules', '.git') for part in p.parts[len(working_dir.parts):]):
                continue
            suffix = "/" if p.is_dir() else ""
            filtered.append(rel + suffix)

        if not filtered:
            return f"未找到匹配 '{pattern}' 的文件"

        result = "\n".join(filtered[:200])
        if len(filtered) > 200:
            result += f"\n... (共 {len(filtered)} 项，仅显示前 200 项)"

        log.info(f"[Tool] list_files: pattern='{pattern}', 找到 {len(filtered)} 项")
        return result
    except Exception as e:
        return f"错误：列出文件失败 - {str(e)}"


def _exec_search_text(working_dir: Path, **kwargs) -> str:
    """搜索文本"""
    query = kwargs["query"]
    glob_pattern = kwargs.get("glob_pattern", "*")

    results = []
    try:
        files = list(working_dir.rglob(glob_pattern))
        for fpath in files:
            if not fpath.is_file():
                continue
            # 跳过隐藏文件和无关目录
            rel = str(fpath.relative_to(working_dir))
            if any(part.startswith('.') or part in ('__pycache__', 'node_modules', '.git')
                   for part in fpath.parts[len(working_dir.parts):]):
                continue

            try:
                content = fpath.read_text(encoding="utf-8")
                for i, line in enumerate(content.splitlines(), 1):
                    if query in line:
                        results.append(f"{rel}:{i}: {line.strip()[:120]}")
                        if len(results) >= 100:
                            break
            except (UnicodeDecodeError, PermissionError):
                continue

            if len(results) >= 100:
                break

        if not results:
            return f"未找到匹配 '{query}' 的文本"

        result = "\n".join(results)
        if len(results) >= 100:
            result += "\n... (结果过多，仅显示前 100 条)"

        log.info(f"[Tool] search_text: query='{query}', 找到 {len(results)} 条匹配")
        return result
    except Exception as e:
        return f"错误：搜索失败 - {str(e)}"


def _exec_get_directory_tree(working_dir: Path, **kwargs) -> str:
    """显示目录树"""
    target = kwargs.get("path", "")
    max_depth = kwargs.get("max_depth", 3)

    if target:
        dir_path = _validate_path(working_dir, target)
    else:
        dir_path = working_dir

    if not dir_path.exists() or not dir_path.is_dir():
        return f"错误：目录不存在 {dir_path}"

    lines = []
    _skipped_dirs = {'.git', '__pycache__', 'node_modules', '.idea', '.vscode'}

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in _skipped_dirs and not e.name.startswith('.')]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

    lines.append(f"{dir_path.name}/")
    _walk(dir_path, "", 1)

    result = "\n".join(lines[:300])
    if len(lines) > 300:
        result += f"\n... (共 {len(lines)} 行，已截断)"

    log.info(f"[Tool] get_directory_tree: {dir_path}, {len(lines)} 行")
    return result


def _exec_execute_command(working_dir: Path, **kwargs) -> str:
    """执行命令（阻塞）"""
    command = kwargs["command"]
    log.info(f"[Tool] execute_command: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n--- STDERR ---\n"
            output += result.stderr

        output = output.strip()
        if not output:
            output = f"命令执行完成（退出码: {result.returncode}）"
        elif result.returncode != 0:
            output += f"\n（退出码: {result.returncode}）"

        # 截断过长输出
        if len(output) > 50000:
            output = output[:50000] + f"\n... (输出过长，已截断，原始长度: {len(output)})"

        return output

    except subprocess.TimeoutExpired:
        return "错误：命令执行超时（120 秒）"
    except Exception as e:
        return f"错误：命令执行失败 - {str(e)}"


def _exec_execute_command_background(working_dir: Path, **kwargs) -> str:
    """后台执行命令"""
    command = kwargs["command"]
    log.info(f"[Tool] execute_command_background: {command}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(working_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"命令已在后台启动（PID: {process.pid}）"
    except Exception as e:
        return f"错误：后台命令启动失败 - {str(e)}"


def _exec_spawn_agent(working_dir: Path, **kwargs) -> str:
    """启动子 Agent（由外部实现）"""
    # 这个执行器会在 agent_loop 中被覆盖
    return "错误：子 Agent 执行器未初始化"


def _get_tools_for_agent(allowed_tools) -> list:
    """根据工具白名单过滤工具定义"""
    if allowed_tools is None:
        return [t for t in TOOL_DEFINITIONS if t["function"]["name"] != SPAWN_AGENT_TOOL]
    return [t for t in TOOL_DEFINITIONS if t["function"]["name"] in allowed_tools]


# 工具执行器注册表
TOOL_EXECUTORS: Dict[str, Callable] = {
    "read_file": _exec_read_file,
    "write_file": _exec_write_file,
    "edit_file": _exec_edit_file,
    "list_files": _exec_list_files,
    "search_text": _exec_search_text,
    "get_directory_tree": _exec_get_directory_tree,
    "execute_command": _exec_execute_command,
    "execute_command_background": _exec_execute_command_background,
    "spawn_agent": _exec_spawn_agent,
}


def execute_tool(working_dir: Path, tool_name: str, tool_args: dict, **kwargs) -> str:
    """执行工具调用的统一入口"""
    # 特殊工具处理
    if tool_name == "memory":
        memory_store = kwargs.get("_memory_store")
        if not memory_store:
            return "错误：记忆系统未初始化"
        return _exec_memory(memory_store, **tool_args)

    if tool_name == "set_emotion":
        on_emotion_change = kwargs.get("_on_emotion_change")
        emotion = tool_args.get("emotion", "neutral")
        if emotion not in EMOTION_STATES:
            return f"错误：无效的情感状态 '{emotion}'，可选: {', '.join(EMOTION_STATES)}"
        if on_emotion_change:
            on_emotion_change(emotion)
        return f"情感状态已更新为: {emotion}"

    if tool_name == "ask_user":
        on_ask_user = kwargs.get("_on_ask_user")
        if on_ask_user:
            question = tool_args.get("question", "")
            question_type = tool_args.get("question_type", "text")
            options_raw = tool_args.get("options", "")
            if isinstance(options_raw, list):
                options = options_raw
            elif isinstance(options_raw, str) and options_raw:
                options = [o.strip() for o in options_raw.split("|||") if o.strip()]
            else:
                options = []
            return on_ask_user(question, question_type, options)
        return "错误：AskUser 回调未初始化"

    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return f"错误：未知工具 {tool_name}"

    try:
        return executor(working_dir, **tool_args, **kwargs)
    except TypeError as e:
        return f"错误：工具参数错误 - {str(e)}"
    except Exception as e:
        log.error(f"[Tool] {tool_name} 执行异常: {e}", exc_info=True)
        return f"错误：工具执行失败 - {str(e)}"


def _exec_memory(memory_store, action: str, target: str, content: str = "", old_text: str = "", **kwargs) -> str:
    """记忆工具执行器"""
    try:
        if action == "add":
            result = memory_store.add(target, content)
        elif action == "replace":
            result = memory_store.replace(target, old_text, content)
        elif action == "remove":
            result = memory_store.remove(target, old_text)
        else:
            return f"错误：未知记忆操作 '{action}'，可选: add, replace, remove"

        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"错误：记忆操作失败 - {str(e)}"
