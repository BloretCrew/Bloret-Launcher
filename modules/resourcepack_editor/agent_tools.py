"""
资源包 AI Agent 工具定义

定义 Agent 可以调用的所有工具，每个工具包含：
- name: 工具名称
- description: 工具描述（给 LLM 看）
- parameters: JSON Schema 参数定义
- execute: 执行函数 (pack_path: Path, **kwargs) -> str
"""

import os
import json
import glob as glob_module
from pathlib import Path
from typing import Tuple


# ============================================================
# 工具分类与安全
# ============================================================

# 只读工具（不需要用户确认）
READ_ONLY_TOOLS = {
    "read_file", "list_files", "search_text",
    "get_pack_info", "analyze_pack", "read_language",
    "validate_json", "get_file_tree", "ask_user",
}

# 写入工具（需要用户确认）
WRITE_TOOLS = {"write_file", "edit_file", "edit_language", "execute_command", "execute_command_background"}

# Sub-Agent 工具（不在此分类中，由子 Agent 自行管理权限）
SPAWN_AGENT_TOOL = "spawn_agent"

# Sub-Agent 类型定义
SUB_AGENT_TYPES = {
    "explore": {
        "system_prompt": (
            "你是一个只读探索助手。你的任务是分析资源包的结构和内容，但不修改任何文件。\n"
            "只使用读取类工具（read_file, list_files, search_text, get_pack_info, analyze_pack, "
            "read_language, validate_json, get_file_tree）。\n"
            "完成后给出清晰的分析报告。"
        ),
        "allowed_tools": READ_ONLY_TOOLS,
    },
    "plan": {
        "system_prompt": (
            "你是一个架构规划助手。你的任务是分析资源包并制定详细的修改计划。\n"
            "只使用读取类工具来了解当前状态，然后输出一个结构化的修改计划。\n"
            "计划应包含：目标、需要修改的文件、具体修改内容、注意事项。\n"
            "不要执行任何修改操作。"
        ),
        "allowed_tools": READ_ONLY_TOOLS,
    },
    "general": {
        "system_prompt": None,  # 使用默认系统提示
        "allowed_tools": None,  # 全部工具（但排除 spawn_agent）
    },
}


def _validate_path(pack_path: Path, relative_path: str) -> Tuple[bool, str]:
    """验证路径是否在资源包目录内（防止路径遍历攻击）

    Args:
        pack_path: 资源包根目录
        relative_path: 用户提供的相对路径

    Returns:
        (is_valid, error_message) - 如果有效 error_message 为空
    """
    try:
        resolved = (pack_path / relative_path).resolve()
        pack_resolved = pack_path.resolve()
        # 检查解析后的路径是否以 pack_path 开头
        if not str(resolved).startswith(str(pack_resolved)) and resolved != pack_resolved:
            return False, f"错误: 路径 '{relative_path}' 超出了资源包目录范围"
        return True, ""
    except Exception as e:
        return False, f"错误: 路径验证失败 - {str(e)}"


# ============================================================
# 工具执行函数
# ============================================================

def _execute_read_file(pack_path: Path, path: str, **kwargs) -> str:
    """读取资源包中的文件内容"""
    valid, err = _validate_path(pack_path, path)
    if not valid:
        return err
    full_path = pack_path / path
    if not full_path.exists():
        return f"错误: 文件不存在 - {path}"
    if full_path.is_dir():
        return f"错误: {path} 是一个目录，不是文件"
    try:
        content = full_path.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        try:
            content = full_path.read_text(encoding="utf-8-sig")
            return content
        except Exception:
            return f"错误: 无法读取文件 {path}（可能是二进制文件）"
    except Exception as e:
        return f"错误: 读取文件失败 - {str(e)}"


def _execute_write_file(pack_path: Path, path: str, content: str, **kwargs) -> str:
    """写入内容到文件"""
    valid, err = _validate_path(pack_path, path)
    if not valid:
        return err
    full_path = pack_path / path
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"成功写入文件: {path} ({len(content)} 字符)"
    except Exception as e:
        return f"错误: 写入文件失败 - {str(e)}"


def _execute_edit_file(pack_path: Path, path: str, old_text: str, new_text: str, **kwargs) -> str:
    """替换文件中的文本"""
    valid, err = _validate_path(pack_path, path)
    if not valid:
        return err
    full_path = pack_path / path
    if not full_path.exists():
        return f"错误: 文件不存在 - {path}"
    try:
        content = full_path.read_text(encoding="utf-8")
        if old_text not in content:
            return f"错误: 在 {path} 中未找到要替换的文本"
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text, 1)
        full_path.write_text(new_content, encoding="utf-8")
        return f"成功编辑文件: {path} (替换了 1/{count} 处匹配)"
    except Exception as e:
        return f"错误: 编辑文件失败 - {str(e)}"


def _execute_list_files(pack_path: Path, pattern: str = "**/*", **kwargs) -> str:
    """列出匹配模式的文件"""
    try:
        full_pattern = str(pack_path / pattern)
        matches = glob_module.glob(full_pattern, recursive=True)
        # 转为相对路径
        rel_paths = []
        for m in matches:
            rel = os.path.relpath(m, str(pack_path))
            if os.path.isfile(m):
                rel_paths.append(rel)
        if not rel_paths:
            return f"未找到匹配 '{pattern}' 的文件"
        # 限制输出数量
        if len(rel_paths) > 200:
            result = f"找到 {len(rel_paths)} 个文件（显示前 200 个）:\n"
            result += "\n".join(rel_paths[:200])
        else:
            result = f"找到 {len(rel_paths)} 个文件:\n" + "\n".join(rel_paths)
        return result
    except Exception as e:
        return f"错误: 列出文件失败 - {str(e)}"


def _execute_search_text(pack_path: Path, query: str, glob_pattern: str = "**/*", **kwargs) -> str:
    """在文件中搜索文本"""
    try:
        full_pattern = str(pack_path / glob_pattern)
        matches = glob_module.glob(full_pattern, recursive=True)
        results = []
        for filepath in matches:
            if not os.path.isfile(filepath):
                continue
            try:
                content = Path(filepath).read_text(encoding="utf-8")
            except (UnicodeDecodeError, Exception):
                continue
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    rel = os.path.relpath(filepath, str(pack_path))
                    results.append(f"{rel}:{i}: {line.strip()}")
                    if len(results) >= 100:
                        break
            if len(results) >= 100:
                break
        if not results:
            return f"未找到包含 '{query}' 的内容"
        return f"找到 {len(results)} 处匹配:\n" + "\n".join(results)
    except Exception as e:
        return f"错误: 搜索失败 - {str(e)}"


def _execute_get_pack_info(pack_path: Path, **kwargs) -> str:
    """获取资源包基本信息"""
    info = {
        "name": pack_path.name,
        "path": str(pack_path),
    }
    # pack.mcmeta
    mcmeta_path = pack_path / "pack.mcmeta"
    if mcmeta_path.exists():
        try:
            mcmeta = json.loads(mcmeta_path.read_text(encoding="utf-8"))
            pack_info = mcmeta.get("pack", {})
            info["pack_format"] = pack_info.get("pack_format")
            info["description"] = pack_info.get("description", "")
        except Exception:
            info["mcmeta_error"] = "pack.mcmeta 格式错误"
    else:
        info["mcmeta_error"] = "缺少 pack.mcmeta"

    # pack.png
    if (pack_path / "pack.png").exists():
        info["has_pack_png"] = True

    # 统计
    try:
        all_files = [f for f in pack_path.rglob("*") if f.is_file()]
        info["total_files"] = len(all_files)
        info["total_size_kb"] = sum(f.stat().st_size for f in all_files) // 1024
    except Exception:
        pass

    return json.dumps(info, ensure_ascii=False, indent=2)


def _execute_analyze_pack(pack_path: Path, **kwargs) -> str:
    """分析资源包结构和内容"""
    analysis = {
        "namespaces": [],
        "languages": [],
        "textures_count": 0,
        "models_count": 0,
        "blockstates_count": 0,
        "sounds_count": 0,
        "fonts_count": 0,
        "particles_count": 0,
    }

    assets_dir = pack_path / "assets"
    if assets_dir.exists():
        # 命名空间
        namespaces = [d.name for d in assets_dir.iterdir() if d.is_dir()]
        analysis["namespaces"] = namespaces

        for ns in namespaces:
            ns_dir = assets_dir / ns

            # 语言文件
            lang_dir = ns_dir / "lang"
            if lang_dir.exists():
                for f in lang_dir.glob("*.json"):
                    analysis["languages"].append(f"{ns}/lang/{f.name}")

            # 贴图
            tex_dir = ns_dir / "textures"
            if tex_dir.exists():
                analysis["textures_count"] += len(
                    [f for f in tex_dir.rglob("*") if f.is_file() and f.suffix.lower() in (".png", ".mcmeta")]
                )

            # 模型
            model_dir = ns_dir / "models"
            if model_dir.exists():
                analysis["models_count"] += len(
                    [f for f in model_dir.rglob("*.json") if f.is_file()]
                )

            # 方块状态
            bs_dir = ns_dir / "blockstates"
            if bs_dir.exists():
                analysis["blockstates_count"] += len(
                    [f for f in bs_dir.rglob("*.json") if f.is_file()]
                )

            # 声音
            sounds_dir = ns_dir / "sounds"
            if sounds_dir.exists():
                analysis["sounds_count"] += len(
                    [f for f in sounds_dir.rglob("*") if f.is_file()]
                )

            # 字体
            font_dir = ns_dir / "font"
            if font_dir.exists():
                analysis["fonts_count"] += len(
                    [f for f in font_dir.rglob("*.json") if f.is_file()]
                )

            # 粒子
            particle_dir = ns_dir / "particles"
            if particle_dir.exists():
                analysis["particles_count"] += len(
                    [f for f in particle_dir.rglob("*.json") if f.is_file()]
                )

    return json.dumps(analysis, ensure_ascii=False, indent=2)


def _execute_read_language(pack_path: Path, lang: str = "zh_cn", **kwargs) -> str:
    """读取语言文件"""
    # 查找语言文件
    lang_path = None
    for ns_dir in (pack_path / "assets").iterdir():
        if ns_dir.is_dir():
            candidate = ns_dir / "lang" / f"{lang}.json"
            if candidate.exists():
                lang_path = candidate
                break

    if lang_path is None:
        return f"错误: 未找到语言文件 {lang}.json"
    try:
        data = json.loads(lang_path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as e:
        return f"错误: 语言文件 JSON 格式错误 - {str(e)}"
    except Exception as e:
        return f"错误: 读取语言文件失败 - {str(e)}"


def _execute_edit_language(pack_path: Path, lang: str, changes: dict, **kwargs) -> str:
    """编辑语言文件：添加/修改/删除条目"""
    # 查找语言文件
    lang_path = None
    for ns_dir in (pack_path / "assets").iterdir():
        if ns_dir.is_dir():
            candidate = ns_dir / "lang" / f"{lang}.json"
            if candidate.exists():
                lang_path = candidate
                break

    if lang_path is None:
        return f"错误: 未找到语言文件 {lang}.json"

    try:
        data = json.loads(lang_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"错误: 读取语言文件失败 - {str(e)}"

    added = 0
    modified = 0
    deleted = 0

    for key, value in changes.items():
        if value is None or value == "":
            # 删除条目
            if key in data:
                del data[key]
                deleted += 1
        elif key in data:
            # 修改条目
            data[key] = value
            modified += 1
        else:
            # 添加条目
            data[key] = value
            added += 1

    try:
        lang_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return f"成功编辑 {lang}.json: 添加 {added}, 修改 {modified}, 删除 {deleted}"
    except Exception as e:
        return f"错误: 保存语言文件失败 - {str(e)}"


def _execute_validate_json(pack_path: Path, path: str, **kwargs) -> str:
    """验证 JSON 文件格式"""
    valid, err = _validate_path(pack_path, path)
    if not valid:
        return err
    full_path = pack_path / path
    if not full_path.exists():
        return f"错误: 文件不存在 - {path}"
    try:
        content = full_path.read_text(encoding="utf-8")
        json.loads(content)
        return f"JSON 格式正确: {path}"
    except json.JSONDecodeError as e:
        return f"JSON 格式错误: {path}\n行 {e.lineno}, 列 {e.colno}: {e.msg}"
    except Exception as e:
        return f"错误: 验证失败 - {str(e)}"


def _execute_get_file_tree(pack_path: Path, **kwargs) -> str:
    """获取文件树结构"""
    tree_lines = []
    max_depth = 4
    max_entries = 300

    def walk(directory, prefix="", depth=0):
        if depth >= max_depth:
            return
        if len(tree_lines) >= max_entries:
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return

        for entry in entries:
            if len(tree_lines) >= max_entries:
                tree_lines.append(f"{prefix}... (更多文件省略)")
                return
            rel = os.path.relpath(entry, str(pack_path))
            if entry.is_dir():
                tree_lines.append(f"{prefix}📁 {entry.name}/")
                walk(entry, prefix + "  ", depth + 1)
            else:
                size = entry.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size // 1024}KB"
                else:
                    size_str = f"{size // (1024*1024)}MB"
                tree_lines.append(f"{prefix}📄 {entry.name} ({size_str})")

    walk(pack_path)
    return f"文件树 ({len(tree_lines)} 项):\n" + "\n".join(tree_lines)


def _execute_command(pack_path: Path, command: str, **kwargs) -> str:
    """在资源包目录下前台执行终端命令（阻塞，等待完成）"""
    import subprocess
    try:
        result = subprocess.run(
            command, shell=True, cwd=str(pack_path),
            capture_output=True, timeout=60
        )
        # 手动解码，忽略无法解码的字节
        stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        output = stdout
        if stderr:
            output += "\n[stderr] " + stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() if output.strip() else f"命令执行成功 (exit code: {result.returncode})"
    except subprocess.TimeoutExpired:
        return "错误: 命令执行超时 (60秒)"
    except Exception as e:
        return f"错误: {str(e)}"


def _execute_command_background(pack_path: Path, command: str, **kwargs) -> str:
    """在资源包目录下后台执行终端命令（非阻塞，立即返回）"""
    import subprocess
    try:
        proc = subprocess.Popen(
            command, shell=True, cwd=str(pack_path),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return f"命令已在后台启动 (PID: {proc.pid})"
    except Exception as e:
        return f"错误: {str(e)}"


# ============================================================
# 工具定义（OpenAI function calling 格式）
# ============================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取资源包中的文件内容。返回文件的完整文本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的相对路径，例如 'assets/minecraft/lang/zh_cn.json'"
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
            "description": "将内容写入文件。如果文件不存在会自动创建。如果文件已存在会覆盖。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的相对路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文件内容"
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
            "description": "精确替换文件中的一段文本。只替换第一次匹配。适合做精确修改。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的相对路径"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要被替换的原始文本（必须与文件中完全一致）"
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
            "description": "列出资源包中匹配指定模式的文件。支持 glob 模式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "glob 模式，例如 '**/*.json', 'assets/minecraft/textures/**', '*.png'。默认列出所有文件"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "在资源包文件中搜索文本。返回匹配的文件名、行号和内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的文本（不区分大小写）"
                    },
                    "glob_pattern": {
                        "type": "string",
                        "description": "限定搜索的文件范围，例如 '*.json'。默认搜索所有文件"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pack_info",
            "description": "获取资源包的基本信息：名称、pack_format、描述、文件数量等。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_pack",
            "description": "详细分析资源包结构：命名空间、语言文件、贴图数量、模型数量等统计信息。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_language",
            "description": "读取指定语言文件的所有翻译条目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "lang": {
                        "type": "string",
                        "description": "语言代码，例如 'zh_cn', 'en_us'。默认 'zh_cn'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_language",
            "description": "编辑语言文件：添加、修改或删除翻译条目。value 设为 null 或空字符串表示删除该条目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "lang": {
                        "type": "string",
                        "description": "语言代码，例如 'zh_cn'"
                    },
                    "changes": {
                        "type": "object",
                        "description": "要修改的键值对。key 为翻译键，value 为翻译值（null/空字符串表示删除）",
                        "additionalProperties": {
                            "type": ["string", "null"]
                        }
                    }
                },
                "required": ["lang", "changes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_json",
            "description": "验证 JSON 文件的格式是否正确。返回验证结果和错误位置。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "JSON 文件的相对路径"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_tree",
            "description": "获取资源包的完整文件树结构，包含文件大小信息。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "向用户提问并等待回答。支持三种题型：单选(single_choice)、多选(multiple_choice)、文本输入(text)。当你需要用户确认操作、澄清需求或提供额外信息时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "要向用户提出的问题"
                    },
                    "question_type": {
                        "type": "string",
                        "description": "问题类型，只能是 single_choice、multiple_choice 或 text 之一。single_choice=单项选择，multiple_choice=多项选择，text=文本输入（默认）"
                    },
                    "options": {
                        "type": "string",
                        "description": "选项列表，仅 choice 类型需要。用 ||| 分隔各选项。例如：选项A|||选项B|||选项C"
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "在资源包目录下前台执行终端命令（阻塞等待完成）。用于编译、格式化、验证等操作。请谨慎使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令，例如 'java -jar pack.jar' 或 'python validate.py'"
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
            "description": "在资源包目录下后台执行终端命令（立即返回，不等待完成）。用于长时间运行的命令。",
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
            "name": "spawn_agent",
            "description": "生成一个子 Agent 来处理子任务。子 Agent 有独立的上下文，适合并行处理或需要专注的子任务。返回子 Agent 的最终文本结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "给子 Agent 的任务描述，要清晰具体"
                    },
                    "agent_type": {
                        "type": "string",
                        "description": "子 Agent 类型。explore=只读探索分析, plan=架构规划制定计划, general=通用任务可用所有工具。默认 general"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
]


# 工具名 -> 执行函数的映射
TOOL_EXECUTORS = {
    "read_file": _execute_read_file,
    "write_file": _execute_write_file,
    "edit_file": _execute_edit_file,
    "list_files": _execute_list_files,
    "search_text": _execute_search_text,
    "get_pack_info": _execute_get_pack_info,
    "analyze_pack": _execute_analyze_pack,
    "read_language": _execute_read_language,
    "edit_language": _execute_edit_language,
    "validate_json": _execute_validate_json,
    "get_file_tree": _execute_get_file_tree,
    "ask_user": lambda pack_path, question="", question_type="text", options="", **kwargs: f"[问题已发送给用户: {question}]",
    "execute_command": _execute_command,
    "execute_command_background": _execute_command_background,
    "spawn_agent": None,  # 由 agent_loop.py 注册实际执行器
}


def execute_tool(pack_path: Path, tool_name: str, arguments: dict, **kwargs) -> str:
    """执行指定的工具

    Args:
        pack_path: 资源包根目录
        tool_name: 工具名称
        arguments: 工具参数
        **kwargs: 额外参数（如 _api_url, _auth_header 等，传递给需要的执行器）

    Returns:
        工具执行结果字符串
    """
    executor = TOOL_EXECUTORS.get(tool_name)
    if executor is None:
        return f"错误: 未知工具 '{tool_name}'"
    try:
        return executor(pack_path, **arguments, **kwargs)
    except TypeError as e:
        return f"错误: 工具参数错误 - {str(e)}"
    except Exception as e:
        return f"错误: 工具执行失败 - {str(e)}"
