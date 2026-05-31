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

from .knowledge_base import (
    PACK_FORMAT_TABLE, FILE_FORMAT_SPECS, COMMON_ERRORS,
    TEXTURE_GUIDELINES, MODEL_GUIDELINES, SOUND_GUIDELINES,
    LANGUAGE_GUIDELINES, GUI_GUIDELINES, OPTIFINE_GUIDELINES,
    OVERLAY_GUIDE, QUALITY_CHECKLIST, DIRECTORY_GUIDE,
    DEVELOPMENT_WORKFLOW,
)


# ============================================================
# 工具分类与安全
# ============================================================

# 只读工具（不需要用户确认）
READ_ONLY_TOOLS = {
    "read_file", "list_files", "search_text",
    "get_pack_info", "analyze_pack", "read_language",
    "validate_json", "get_file_tree", "ask_user",
    "get_mc_reference", "validate_mcmeta_advanced",
}

# 写入工具（需要用户确认）
WRITE_TOOLS = {
    "write_file", "edit_file", "edit_language",
    "execute_command", "execute_command_background",
    "create_resource_template",
}

# Sub-Agent 工具（不在此分类中，由子 Agent 自行管理权限）
SPAWN_AGENT_TOOL = "spawn_agent"

# Sub-Agent 类型定义
SUB_AGENT_TYPES = {
    "explore": {
        "system_prompt": (
            "你是一个 Minecraft 资源包只读探索助手。你的任务是分析资源包的结构和内容，但不修改任何文件。\n"
            "只使用读取类工具（read_file, list_files, search_text, get_pack_info, analyze_pack, "
            "read_language, validate_json, get_file_tree, get_mc_reference, validate_mcmeta_advanced）。\n\n"
            "分析时请关注：\n"
            "- pack.mcmeta 的 pack_format 和版本兼容性\n"
            "- 目录结构是否符合 Minecraft 标准规范\n"
            "- 资源类型覆盖情况（纹理/模型/声音/语言/着色器等）\n"
            "- 命名空间使用情况\n"
            "- 潜在的问题（缺失文件、格式错误、命名不一致等）\n\n"
            "完成后给出清晰的分析报告，包含：资源包概况、结构评估、发现的问题、改进建议。"
        ),
        "allowed_tools": READ_ONLY_TOOLS,
    },
    "plan": {
        "system_prompt": (
            "你是一个 Minecraft 资源包架构规划助手。你的任务是分析资源包并制定详细的修改计划。\n"
            "只使用读取类工具来了解当前状态，然后输出一个结构化的修改计划。\n\n"
            "计划应包含：\n"
            "1. 目标：明确要实现什么\n"
            "2. 现状分析：当前资源包的状态\n"
            "3. 需要修改的文件列表（含完整相对路径）\n"
            "4. 每个文件的具体修改内容\n"
            "5. 新建文件的完整内容\n"
            "6. 注意事项：版本兼容性、性能影响、命名规范\n\n"
            "不要执行任何修改操作。使用 get_mc_reference 查询技术规范，确保计划符合 Minecraft 标准。"
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
# 新增工具：资源包专业知识
# ============================================================

def _execute_get_mc_reference(pack_path: Path, topic: str = "", **kwargs) -> str:
    """查询 Minecraft 资源包技术参考信息"""
    topic_map = {
        "pack_format": ("pack_format 版本对照表",
            "## pack_format 版本对照表\n\n" +
            "\n".join(f"- **{v}**: Minecraft {k}" for k, v in sorted(PACK_FORMAT_TABLE.items(), key=lambda x: x[0]))),
        "directories": ("目录结构规范", DIRECTORY_GUIDE),
        "textures": ("纹理制作规范", TEXTURE_GUIDELINES),
        "models": ("模型开发规范", MODEL_GUIDELINES),
        "sounds": ("声音开发规范", SOUND_GUIDELINES),
        "language": ("语言文件规范", LANGUAGE_GUIDELINES),
        "gui": ("GUI 纹理规范", GUI_GUIDELINES),
        "optifine": ("OptiFine 扩展规范", OPTIFINE_GUIDELINES),
        "overlays": ("覆盖层系统", OVERLAY_GUIDE),
        "quality": ("质量评估标准", QUALITY_CHECKLIST),
        "errors": ("常见错误速查", COMMON_ERRORS),
        "workflow": ("开发工作流", DEVELOPMENT_WORKFLOW),
        "file_formats": ("文件格式规范",
            "## 文件格式规范\n\n" +
            "\n\n".join(f"### {k}\n" + "\n".join(
                f"- {sk}: {sv}" if isinstance(sv, str) else f"- {sk}: {json.dumps(sv, ensure_ascii=False)}"
                for sk, sv in v.items()
            ) for k, v in FILE_FORMAT_SPECS.items())),
    }

    if not topic:
        available = ", ".join(topic_map.keys())
        return f"请指定查询主题。可用主题: {available}"

    if topic in topic_map:
        title, content = topic_map[topic]
        return f"# {title}\n\n{content}"

    available = ", ".join(topic_map.keys())
    return f"未知主题 '{topic}'。可用主题: {available}"


def _execute_validate_mcmeta_advanced(pack_path: Path, **kwargs) -> str:
    """对 pack.mcmeta 进行深度验证"""
    mcmeta_path = pack_path / "pack.mcmeta"
    if not mcmeta_path.exists():
        return json.dumps({"valid": False, "errors": ["缺少 pack.mcmeta 文件"], "warnings": [], "suggestions": []},
                          ensure_ascii=False, indent=2)

    errors = []
    warnings = []
    suggestions = []

    try:
        content = mcmeta_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return json.dumps({"valid": False, "errors": [f"JSON 格式错误: 行 {e.lineno}, 列 {e.colno}: {e.msg}"],
                           "warnings": [], "suggestions": []}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"valid": False, "errors": [f"读取文件失败: {str(e)}"],
                           "warnings": [], "suggestions": []}, ensure_ascii=False, indent=2)

    pack = data.get("pack", {})
    if not pack:
        errors.append("缺少 'pack' 字段")
    else:
        # pack_format 验证
        pf = pack.get("pack_format")
        if pf is None:
            errors.append("缺少 'pack_format' 字段")
        elif not isinstance(pf, int) or pf < 1:
            errors.append(f"'pack_format' 必须是正整数，当前值: {pf}")
        elif pf not in PACK_FORMAT_TABLE:
            warnings.append(f"pack_format={pf} 不在已知版本表中，可能是非常新的版本")

        # description 验证
        desc = pack.get("description")
        if desc is None:
            warnings.append("缺少 'description' 字段（游戏会显示空描述）")

        # supported_formats 验证
        sf = pack.get("supported_formats")
        min_f = pack.get("min_format")
        max_f = pack.get("max_format")

        if sf is not None:
            if isinstance(sf, list):
                if len(sf) < 2:
                    warnings.append("supported_formats 数组应包含至少两个值（最小和最大）")
            elif isinstance(sf, dict):
                if "min_inclusive" not in sf or "max_inclusive" not in sf:
                    warnings.append("supported_formats 对象应包含 min_inclusive 和 max_inclusive")
            else:
                errors.append("supported_formats 必须是数组或对象")

        if min_f is not None and max_f is not None and min_f > max_f:
            errors.append(f"min_format({min_f}) 不能大于 max_format({max_f})")

        if sf is not None and (min_f is not None or max_f is not None):
            suggestions.append("同时定义 supported_formats 和 min/max_format 时，游戏以 supported_formats 优先")

    # overlays 验证
    overlays = data.get("overlays", {})
    if overlays:
        entries = overlays.get("entries", [])
        if not entries:
            warnings.append("overlays 存在但 entries 为空")
        for i, entry in enumerate(entries):
            directory = entry.get("directory", "")
            if not directory:
                errors.append(f"overlays.entries[{i}] 缺少 'directory'")
            elif not (pack_path / directory).is_dir():
                warnings.append(f"覆盖层目录 '{directory}' 不存在")

            formats = entry.get("formats", {})
            if not formats:
                errors.append(f"overlays.entries[{i}] 缺少 'formats'")

    # filter 验证
    filter_cfg = data.get("filter", {})
    if filter_cfg:
        block_filters = filter_cfg.get("block", [])
        for i, f in enumerate(block_filters):
            ns = f.get("namespace", "")
            path = f.get("path", "")
            if not ns and not path:
                warnings.append(f"filter.block[{i}] 的 namespace 和 path 都为空")

    # 语言注册验证
    languages = pack.get("language", {})
    for lang_code, lang_info in languages.items():
        if not isinstance(lang_info, dict):
            errors.append(f"language.{lang_code} 必须是对象")
        elif "name" not in lang_info:
            warnings.append(f"language.{lang_code} 缺少 'name' 字段")
        # 检查对应的 lang 文件是否存在
        lang_file_found = False
        for ns_dir in (pack_path / "assets").iterdir() if (pack_path / "assets").exists() else []:
            if ns_dir.is_dir() and (ns_dir / "lang" / f"{lang_code}.json").exists():
                lang_file_found = True
                break
        if not lang_file_found:
            warnings.append(f"注册的语言 '{lang_code}' 没有找到对应的 lang/{lang_code}.json 文件")

    # 生成建议
    if not errors and not warnings:
        suggestions.append("pack.mcmeta 验证通过，结构正确")

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def _execute_create_resource_template(pack_path: Path, template_type: str = "", options: dict = None, **kwargs) -> str:
    """创建资源包模板文件"""
    if options is None:
        options = {}

    if not template_type:
        available = "mcmeta, directory_structure, language, model_block, model_item, blockstate_variants, blockstate_multipart, sounds, font"
        return f"请指定模板类型。可用类型: {available}"

    templates = {
        "mcmeta": _template_mcmeta,
        "directory_structure": _template_directory_structure,
        "language": _template_language,
        "model_block": _template_model_block,
        "model_item": _template_model_item,
        "blockstate_variants": _template_blockstate_variants,
        "blockstate_multipart": _template_blockstate_multipart,
        "sounds": _template_sounds,
        "font": _template_font,
    }

    if template_type not in templates:
        available = ", ".join(templates.keys())
        return f"未知模板类型 '{template_type}'。可用类型: {available}"

    try:
        return templates[template_type](pack_path, options)
    except Exception as e:
        return f"错误: 创建模板失败 - {str(e)}"


def _template_mcmeta(pack_path: Path, options: dict) -> str:
    """创建 pack.mcmeta 模板"""
    pack_format = options.get("pack_format", 34)
    description = options.get("description", "My Resource Pack")
    namespace = options.get("namespace", "mypack")

    mcmeta = {
        "pack": {
            "pack_format": pack_format,
            "description": description,
        }
    }

    # 添加 supported_formats
    if options.get("supported_formats"):
        mcmeta["pack"]["supported_formats"] = options["supported_formats"]
    elif options.get("max_format"):
        mcmeta["pack"]["min_format"] = pack_format
        mcmeta["pack"]["max_format"] = options["max_format"]

    mcmeta_path = pack_path / "pack.mcmeta"
    if mcmeta_path.exists():
        return "错误: pack.mcmeta 已存在，不会覆盖。请先删除现有文件或直接编辑。"

    mcmeta_path.write_text(json.dumps(mcmeta, ensure_ascii=False, indent=2), encoding="utf-8")
    version_name = PACK_FORMAT_TABLE.get(pack_format, "未知版本")
    return f"已创建 pack.mcmeta (pack_format={pack_format}, 对应 Minecraft {version_name})"


def _template_directory_structure(pack_path: Path, options: dict) -> str:
    """创建基础目录结构"""
    namespace = options.get("namespace", "minecraft")
    dirs = [
        f"assets/{namespace}/textures/block",
        f"assets/{namespace}/textures/item",
        f"assets/{namespace}/textures/entity",
        f"assets/{namespace}/textures/gui",
        f"assets/{namespace}/textures/particle",
        f"assets/{namespace}/models/block",
        f"assets/{namespace}/models/item",
        f"assets/{namespace}/blockstates",
        f"assets/{namespace}/lang",
        f"assets/{namespace}/font",
        f"assets/{namespace}/sounds",
        f"assets/{namespace}/particles",
        f"assets/{namespace}/texts",
    ]

    created = []
    for d in dirs:
        dir_path = pack_path / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(d)

    if not created:
        return f"目录结构已存在（命名空间: {namespace}），无需创建。"

    return f"已创建 {len(created)} 个目录（命名空间: {namespace}）:\n" + "\n".join(created)


def _template_language(pack_path: Path, options: dict) -> str:
    """创建语言文件模板"""
    namespace = options.get("namespace", "minecraft")
    lang_code = options.get("lang", "zh_cn")

    lang_dir = pack_path / "assets" / namespace / "lang"
    lang_dir.mkdir(parents=True, exist_ok=True)
    lang_path = lang_dir / f"{lang_code}.json"

    if lang_path.exists():
        return f"错误: {lang_path.relative_to(pack_path)} 已存在，不会覆盖。"

    template = {
        f"block.{namespace}.example_block": "示例方块",
        f"item.{namespace}.example_item": "示例物品",
        f"item.{namespace}.example_item.desc": "§7这是一个示例物品描述",
    }
    lang_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建语言文件: assets/{namespace}/lang/{lang_code}.json (含 3 个示例翻译键)"


def _template_model_block(pack_path: Path, options: dict) -> str:
    """创建方块模型模板"""
    namespace = options.get("namespace", "minecraft")
    block_name = options.get("name", "example_block")
    parent = options.get("parent", "minecraft:block/cube_all")
    texture_ref = options.get("texture", f"minecraft:block/{block_name}")

    model_dir = pack_path / "assets" / namespace / "models" / "block"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{block_name}.json"

    if model_path.exists():
        return f"错误: {model_path.relative_to(pack_path)} 已存在，不会覆盖。"

    model = {
        "parent": parent,
        "textures": {
            "all": texture_ref
        }
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建方块模型: assets/{namespace}/models/block/{block_name}.json (parent={parent})"


def _template_model_item(pack_path: Path, options: dict) -> str:
    """创建物品模型模板"""
    namespace = options.get("namespace", "minecraft")
    item_name = options.get("name", "example_item")
    parent = options.get("parent", "minecraft:item/generated")
    layer0 = options.get("layer0", f"minecraft:item/{item_name}")

    model_dir = pack_path / "assets" / namespace / "models" / "item"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{item_name}.json"

    if model_path.exists():
        return f"错误: {model_path.relative_to(pack_path)} 已存在，不会覆盖。"

    model = {
        "parent": parent,
        "textures": {
            "layer0": layer0
        }
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建物品模型: assets/{namespace}/models/item/{item_name}.json (parent={parent})"


def _template_blockstate_variants(pack_path: Path, options: dict) -> str:
    """创建方块状态 variants 模板"""
    namespace = options.get("namespace", "minecraft")
    block_name = options.get("name", "example_block")
    model_ref = options.get("model", f"minecraft:block/{block_name}")

    bs_dir = pack_path / "assets" / namespace / "blockstates"
    bs_dir.mkdir(parents=True, exist_ok=True)
    bs_path = bs_dir / f"{block_name}.json"

    if bs_path.exists():
        return f"错误: {bs_path.relative_to(pack_path)} 已存在，不会覆盖。"

    bs = {
        "variants": {
            "": {"model": model_ref}
        }
    }
    bs_path.write_text(json.dumps(bs, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建方块状态: assets/{namespace}/blockstates/{block_name}.json (variants 模式)"


def _template_blockstate_multipart(pack_path: Path, options: dict) -> str:
    """创建方块状态 multipart 模板"""
    namespace = options.get("namespace", "minecraft")
    block_name = options.get("name", "example_block")
    model_ref = options.get("model", f"minecraft:block/{block_name}")

    bs_dir = pack_path / "assets" / namespace / "blockstates"
    bs_dir.mkdir(parents=True, exist_ok=True)
    bs_path = bs_dir / f"{block_name}.json"

    if bs_path.exists():
        return f"错误: {bs_path.relative_to(pack_path)} 已存在，不会覆盖。"

    bs = {
        "multipart": [
            {"apply": {"model": model_ref}},
            {
                "when": {"north": "true"},
                "apply": {"model": f"{model_ref}_side"}
            },
            {
                "when": {"south": "true"},
                "apply": {"model": f"{model_ref}_side", "y": 180}
            },
        ]
    }
    bs_path.write_text(json.dumps(bs, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建方块状态: assets/{namespace}/blockstates/{block_name}.json (multipart 模式)"


def _template_sounds(pack_path: Path, options: dict) -> str:
    """创建 sounds.json 模板"""
    namespace = options.get("namespace", "minecraft")
    event_name = options.get("event", "custom.example_sound")
    sound_file = options.get("file", f"{namespace}:custom/example")

    sounds_path = pack_path / "assets" / namespace / "sounds.json"
    if sounds_path.exists():
        return f"错误: assets/{namespace}/sounds.json 已存在，不会覆盖。"

    sounds = {
        event_name: {
            "subtitle": f"subtitles.{event_name}",
            "sounds": [
                {
                    "name": sound_file,
                    "volume": 1.0,
                    "pitch": 1.0,
                }
            ]
        }
    }
    sounds_path.write_text(json.dumps(sounds, ensure_ascii=False, indent=2), encoding="utf-8")

    # 创建 sounds 目录
    sounds_dir = pack_path / "assets" / namespace / "sounds"
    sounds_dir.mkdir(parents=True, exist_ok=True)

    return f"已创建 sounds.json 和 sounds/ 目录 (事件: {event_name})"


def _template_font(pack_path: Path, options: dict) -> str:
    """创建字体定义模板"""
    namespace = options.get("namespace", "minecraft")
    font_name = options.get("name", "default")

    font_dir = pack_path / "assets" / namespace / "font"
    font_dir.mkdir(parents=True, exist_ok=True)
    font_path = font_dir / f"{font_name}.json"

    if font_path.exists():
        return f"错误: {font_path.relative_to(pack_path)} 已存在，不会覆盖。"

    font = {
        "providers": [
            {
                "type": "bitmap",
                "file": f"{namespace}:font/custom_chars.png",
                "height": 8,
                "ascent": 7,
                "chars": ["àáâãäå"]
            }
        ]
    }
    font_path.write_text(json.dumps(font, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已创建字体定义: assets/{namespace}/font/{font_name}.json"


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
    # ========== 新增：资源包专业知识工具 ==========
    {
        "type": "function",
        "function": {
            "name": "get_mc_reference",
            "description": "查询 Minecraft 资源包技术参考信息。当用户询问 pack_format 版本对照、目录结构规范、文件格式要求、最佳实践、常见错误等技术细节时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "查询主题。可选值: pack_format(版本对照表), directories(目录规范), textures(纹理规范), models(模型规范), sounds(声音规范), language(语言规范), gui(GUI规范), optifine(OptiFine扩展), overlays(覆盖层系统), quality(质量标准), errors(常见错误), workflow(开发工作流), file_formats(文件格式规范)"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_mcmeta_advanced",
            "description": "对 pack.mcmeta 进行深度验证。检查 pack_format 是否有效、supported_formats 范围是否合理、overlays 配置是否正确、language 注册是否有对应的 lang 文件、filter 规则是否合法。返回包含 errors/warnings/suggestions 的详细验证报告。在修改 pack.mcmeta 前建议使用。",
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
            "name": "create_resource_template",
            "description": "创建标准资源包模板文件。支持创建: mcmeta(pack.mcmeta), directory_structure(基础目录结构), language(语言文件骨架), model_block(方块模型), model_item(物品模型), blockstate_variants(方块状态variants), blockstate_multipart(方块状态multipart), sounds(sounds.json), font(字体定义)。创建新资源包或添加新资源类型时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_type": {
                        "type": "string",
                        "description": "模板类型。可选: mcmeta, directory_structure, language, model_block, model_item, blockstate_variants, blockstate_multipart, sounds, font"
                    },
                    "options": {
                        "type": "object",
                        "description": "模板选项。通用选项: namespace(命名空间,默认minecraft)。mcmeta: pack_format, description, supported_formats, max_format。model_block/model_item: name, parent, texture/layer0。blockstate: name, model。sounds: event, file。language: lang(语言代码)。font: name(字体名)"
                    }
                },
                "required": ["template_type"]
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
    # 新增工具
    "get_mc_reference": _execute_get_mc_reference,
    "validate_mcmeta_advanced": _execute_validate_mcmeta_advanced,
    "create_resource_template": _execute_create_resource_template,
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
