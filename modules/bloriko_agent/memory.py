"""
络可 记忆系统

简化版 Hermes MemoryStore（参考 hermes-agent-main/tools/memory_tool.py）

双文件架构：
- MEMORY.md：络可的笔记（环境知识、项目约定、经验教训）
- USER.md：络可对用户的了解（偏好、沟通风格、习惯）

设计要点：
- 条目以 \\n§\\n 分隔
- 字符限制：MEMORY.md 2200 字，USER.md 1375 字
- 冻结快照模式：会话开始时加载，注入系统提示词，会话中磁盘更新但快照不变
- 原子写入（tempfile + os.replace）
"""

import os
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, List

log = logging.getLogger(__name__)

ENTRY_DELIMITER = "\n§\n"

DEFAULT_MEMORY_CHAR_LIMIT = 2200
DEFAULT_USER_CHAR_LIMIT = 1375


class MemoryStore:
    """文件记忆存储"""

    def __init__(self, memory_dir: Path, memory_char_limit: int = DEFAULT_MEMORY_CHAR_LIMIT,
                 user_char_limit: int = DEFAULT_USER_CHAR_LIMIT):
        self.memory_dir = memory_dir
        self.memory_char_limit = memory_char_limit
        self.user_char_limit = user_char_limit

        # 文件路径
        self._memory_path = memory_dir / "MEMORY.md"
        self._user_path = memory_dir / "USER.md"

        # 冻结快照（会话开始时捕获，会话中不变）
        self._memory_snapshot: Optional[str] = None
        self._user_snapshot: Optional[str] = None

        # 内存缓存（当前条目）
        self._memory_entries: List[str] = []
        self._user_entries: List[str] = []

    def load_on_init(self):
        """初始化时加载：创建目录、读取文件、捕获快照"""
        os.makedirs(self.memory_dir, exist_ok=True)

        self._memory_entries = self._read_entries(self._memory_path)
        self._user_entries = self._read_entries(self._user_path)

        # 捕获冻结快照
        self._memory_snapshot = self._render_block("memory", self._memory_entries)
        self._user_snapshot = self._render_block("user", self._user_entries)

        log.info(f"[Memory] 加载完成: MEMORY.md={len(self._memory_entries)}条, "
                 f"USER.md={len(self._user_entries)}条")

    def refresh_snapshots(self):
        """重新从内存条目列表渲染快照（写入后调用，使记忆立即生效）"""
        self._memory_snapshot = self._render_block("memory", self._memory_entries)
        self._user_snapshot = self._render_block("user", self._user_entries)

    # ========== 快照访问（用于系统提示词注入） ==========

    def get_memory_snapshot(self) -> Optional[str]:
        """获取 MEMORY.md 的冻结快照"""
        return self._memory_snapshot

    def get_user_snapshot(self) -> Optional[str]:
        """获取 USER.md 的冻结快照"""
        return self._user_snapshot

    # ========== 条目操作 ==========

    def add(self, target: str, content: str) -> Dict:
        """添加条目到指定目标"""
        entries, path, char_limit = self._get_target(target)
        if not content or not content.strip():
            return {"success": False, "error": "内容不能为空"}

        new_entry = content.strip()
        current_chars = self._char_count(entries, target)

        if current_chars + len(new_entry) + len(ENTRY_DELIMITER) > char_limit:
            remaining = char_limit - current_chars - len(ENTRY_DELIMITER)
            if remaining <= 0:
                return {
                    "success": False,
                    "error": f"{target} 已达到字符上限 ({char_limit} 字符)，请先删除或替换一些条目"
                }
            # 截断到可用空间
            new_entry = new_entry[:remaining]

        entries.append(new_entry)
        self._write_entries(path, entries)
        self.refresh_snapshots()

        log.info(f"[Memory] 已添加到 {target}: '{new_entry[:50]}...'")
        return {
            "success": True,
            "message": f"已添加到 {target}",
            "current_chars": self._char_count(entries, target),
            "char_limit": char_limit,
        }

    def replace(self, target: str, old_text: str, new_content: str) -> Dict:
        """替换条目（substring 匹配）"""
        entries, path, char_limit = self._get_target(target)
        if not old_text:
            return {"success": False, "error": "old_text 不能为空"}

        # 查找匹配的条目
        matches = [(i, e) for i, e in enumerate(entries) if old_text in e]

        if not matches:
            return {
                "success": False,
                "error": f"未找到包含 '{old_text}' 的条目。当前 {target} 条目:\n" +
                         "\n".join(f"  - {e[:60]}..." if len(e) > 60 else f"  - {e}" for e in entries)
            }

        if len(matches) > 1:
            suggestions = [e[:40] for _, e in matches[:5]]
            return {
                "success": False,
                "error": f"找到 {len(matches)} 个匹配项，请提供更具体的文本。匹配的条目: {suggestions}"
            }

        idx, old_entry = matches[0]

        if not new_content or not new_content.strip():
            return {"success": False, "error": "new_content 不能为空"}

        new_entry = new_content.strip()

        # 检查替换后的字符数
        entries_copy = list(entries)
        entries_copy[idx] = new_entry
        new_chars = self._char_count(entries_copy, target)
        if new_chars > char_limit:
            return {
                "success": False,
                "error": f"替换后将超出字符上限 ({new_chars}/{char_limit})。请缩短内容。"
            }

        entries[idx] = new_entry
        self._write_entries(path, entries)
        self.refresh_snapshots()

        log.info(f"[Memory] 已替换 {target} 条目: '{old_entry[:30]}' -> '{new_entry[:30]}'")
        return {
            "success": True,
            "message": f"已替换 {target} 中的条目",
            "old": old_entry,
            "new": new_entry,
            "current_chars": self._char_count(entries, target),
            "char_limit": char_limit,
        }

    def remove(self, target: str, old_text: str) -> Dict:
        """删除条目（substring 匹配）"""
        entries, path, char_limit = self._get_target(target)
        if not old_text:
            return {"success": False, "error": "old_text 不能为空"}

        matches = [(i, e) for i, e in enumerate(entries) if old_text in e]

        if not matches:
            return {
                "success": False,
                "error": f"未找到包含 '{old_text}' 的条目。当前 {target} 条目:\n" +
                         "\n".join(f"  - {e[:60]}..." if len(e) > 60 else f"  - {e}" for e in entries)
            }

        if len(matches) > 1:
            suggestions = [e[:40] for _, e in matches[:5]]
            return {
                "success": False,
                "error": f"找到 {len(matches)} 个匹配项，请提供更具体的文本。匹配的条目: {suggestions}"
            }

        idx, removed_entry = matches[0]
        entries.pop(idx)
        self._write_entries(path, entries)
        self.refresh_snapshots()

        log.info(f"[Memory] 已从 {target} 删除: '{removed_entry[:50]}'")
        return {
            "success": True,
            "message": f"已从 {target} 删除条目",
            "removed": removed_entry,
            "current_chars": self._char_count(entries, target),
            "char_limit": char_limit,
        }

    def get_all_entries(self, target: str) -> str:
        """获取指定目标的所有条目（用于 UI 显示）"""
        entries, _, _ = self._get_target(target)
        if not entries:
            return ""
        return ENTRY_DELIMITER.join(entries)

    # ========== 内部方法 ==========

    def _get_target(self, target: str):
        """获取目标的条目列表、文件路径和字符上限"""
        if target == "memory":
            return self._memory_entries, self._memory_path, self.memory_char_limit
        elif target == "user":
            return self._user_entries, self._user_path, self.user_char_limit
        else:
            raise ValueError(f"未知目标: {target}，应为 'memory' 或 'user'")

    def _read_entries(self, path: Path) -> List[str]:
        """从文件读取条目列表"""
        if not path.exists():
            return []
        try:
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return []
            return [e for e in content.split(ENTRY_DELIMITER) if e.strip()]
        except Exception as e:
            log.warning(f"[Memory] 读取 {path} 失败: {e}")
            return []

    def _write_entries(self, path: Path, entries: List[str]):
        """原子写入条目到文件"""
        content = ENTRY_DELIMITER.join(entries) if entries else ""

        try:
            # 原子写入：先写临时文件，再 os.replace
            fd, tmp_path = tempfile.mkstemp(
                dir=str(path.parent),
                prefix=f".{path.name}.",
                suffix=".tmp"
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.replace(tmp_path, str(path))
            except Exception:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            log.error(f"[Memory] 写入 {path} 失败: {e}")
            raise

    def _render_block(self, target: str, entries: List[str]) -> Optional[str]:
        """渲染条目为系统提示词注入块"""
        if not entries:
            return None

        content = ENTRY_DELIMITER.join(entries)
        label = "记忆" if target == "memory" else "用户画像"

        return (
            f"<{target}-memory>\n"
            f"以下是络可关于{label}的记忆：\n\n"
            f"{content}\n"
            f"</{target}-memory>"
        )

    def _char_count(self, entries: List[str], target: str) -> int:
        """计算条目的总字符数"""
        if not entries:
            return 0
        return sum(len(e) for e in entries) + len(ENTRY_DELIMITER) * max(0, len(entries) - 1)
