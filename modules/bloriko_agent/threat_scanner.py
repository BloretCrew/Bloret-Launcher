"""
络可 记忆威胁扫描

检测记忆条目中的 prompt injection、角色劫持、系统提示词覆盖等威胁。
参考 hermes-agent-main/tools/threat_patterns.py，针对角色助手场景精简。

扫描范围：
- prompt_injection: 经典提示词注入（"ignore previous instructions"）
- role_hijack: 角色劫持（"you are now a..."）
- identity_override: 身份覆盖（"name yourself X" — 对角色助手尤其关键）
- sys_prompt_override: 系统提示词覆盖
- invisible_unicode: 不可见 Unicode 字符（用于混淆注入攻击）
"""

import re
import unicodedata
from typing import List, Optional, Tuple

MAX_SCAN_CHARS = 65_536

# 英文关键词之间的填充词，允许 0-8 个词的间隔，防止简单绕过
_FILLER = r"(?:\w+\s+){0,8}"

# 中文填充词：中文字符之间通常无空格，所以用 \s*（允许零空格）而非 \s+
_ZH_FILLER = r"(?:\w+\s*){0,8}"

# 每项: (regex, pattern_id)
_PATTERNS: List[Tuple[str, str]] = [
    # 经典 prompt injection
    (rf'ignore\s+{_FILLER}(previous|all|above|prior)\s+{_FILLER}instructions', "prompt_injection"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (rf'disregard\s+{_FILLER}(your|all|any)\s+{_FILLER}(instructions|rules|guidelines)', "disregard_rules"),
    (rf'act\s+as\s+(if|though)\s+{_FILLER}you\s+{_FILLER}(have\s+no|don\'t\s+have)\s+{_FILLER}(restrictions|limits|rules)', "bypass_restrictions"),
    (r'<!--[^>]{0,512}(?:ignore|override|system|secret|hidden)[^>]{0,512}-->', "html_comment_injection"),

    # 角色劫持 / 身份覆盖（对角色助手尤其关键）
    (rf'you\s+are\s+{_FILLER}now\s+(?:a|an|the)\s+', "role_hijack"),
    (rf'pretend\s+{_FILLER}(you\s+are|to\s+be)\s+', "role_pretend"),
    (rf'output\s+{_FILLER}(system|initial)\s+prompt', "leak_system_prompt"),
    (rf'(respond|answer|reply)\s+without\s+{_FILLER}(restrictions|limitations|filters|safety)', "remove_filters"),
    (rf'you\s+have\s+been\s+{_FILLER}(updated|upgraded|patched)\s+to', "fake_update"),
    (r'\bname\s+yourself\s+\w+', "identity_override"),

    # 中文 prompt injection 模式（使用 _ZH_FILLER，中文字词之间无空格）
    (r'忽略' + _ZH_FILLER + r'(?:指令|指示|规则|设置|提示)', "prompt_injection_zh"),
    (r'(?:假装|扮演)' + _ZH_FILLER + r'(?:你|是)', "role_pretend_zh"),
    (r'(?:输出|显示|打印)' + _ZH_FILLER + r'(?:提示|指令|提示词)', "leak_system_prompt_zh"),
    (r'(?:你现在|你的新身份|重新定义你)', "identity_override_zh"),

    # 隐藏指令
    (rf'do\s+not\s+{_FILLER}tell\s+{_FILLER}the\s+user', "deception_hide"),
]

# 不可见 Unicode 字符（与 Hermes 对齐）
INVISIBLE_CHARS = frozenset({
    '​',  # zero-width space
    '‌',  # zero-width non-joiner
    '‍',  # zero-width joiner
    '⁠',  # word joiner
    '⁢',  # invisible times
    '⁣',  # invisible separator
    '⁤',  # invisible plus
    '﻿',  # zero-width no-break space (BOM)
    '‪',  # left-to-right embedding
    '‫',  # right-to-left embedding
    '‬',  # pop directional formatting
    '‭',  # left-to-right override
    '‮',  # right-to-left override
    '⁦',  # left-to-right isolate
    '⁧',  # right-to-left isolate
    '⁨',  # first strong isolate
    '⁩',  # pop directional isolate
})

# 编译正则（导入时一次性编译）
_COMPILED: List[Tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), pid) for pattern, pid in _PATTERNS
]


def scan_for_threats(content: str) -> List[str]:
    """扫描内容中的威胁模式，返回匹配的 pattern ID 列表"""
    if not content:
        return []

    findings: List[str] = []

    content = content[:MAX_SCAN_CHARS]

    # 不可见 Unicode — 在 NFKC 归一化前检测（归一化可能移除某些字符）
    char_set = set(content)
    invisible_hits = char_set & INVISIBLE_CHARS
    for ch in invisible_hits:
        findings.append(f"invisible_unicode_U+{ord(ch):04X}")

    # NFKC 归一化，折叠全角/兼容 Unicode 变体
    normalised = unicodedata.normalize("NFKC", content)

    # 正则匹配
    for compiled, pid in _COMPILED:
        if compiled.search(normalised):
            findings.append(pid)

    return findings


def first_threat_message(content: str) -> Optional[str]:
    """返回第一条威胁的人类可读描述，无威胁则返回 None"""
    findings = scan_for_threats(content)
    if not findings:
        return None
    pid = findings[0]
    if pid.startswith("invisible_unicode_"):
        codepoint = pid.replace("invisible_unicode_", "")
        return f"内容包含不可见 Unicode 字符 {codepoint}（可能的注入攻击），已阻止写入。"
    return (
        f"内容匹配威胁模式 '{pid}'，"
        f"记忆内容会被注入系统提示词，不得包含注入或覆盖指令。"
    )


__all__ = [
    "INVISIBLE_CHARS",
    "MAX_SCAN_CHARS",
    "scan_for_threats",
    "first_threat_message",
]
