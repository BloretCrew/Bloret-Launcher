"""启动 hooks、Discord RPC、崩溃报告浏览。"""

from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.services.base import ServiceResult, err, ok
from modules.services.paths_util import safe_version_dir

# ---------------- Hooks ----------------

def _expand_hook(command: str, variables: Dict[str, str]) -> str:
    out = command or ""
    for k, v in variables.items():
        out = out.replace(f"${k}", v).replace(f"%{k}%", v)
    return out


def run_pre_launch_hook(
    command: str,
    *,
    instance_name: str,
    instance_dir: str,
    java_path: str,
    cwd: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    command = (command or "").strip()
    if not command:
        return ok({"skipped": True})
    variables = {
        "INST_NAME": instance_name,
        "INST_ID": instance_name,
        "INST_DIR": instance_dir,
        "INST_MC_DIR": instance_dir,
        "INST_JAVA": java_path,
    }
    expanded = _expand_hook(command, variables)
    try:
        # shell 以支持用户写管道；工作目录实例目录
        proc = subprocess.run(
            expanded,
            shell=True,
            cwd=cwd or instance_dir or None,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return err(
                f"pre-launch hook failed ({proc.returncode}): {(proc.stderr or proc.stdout or '')[:300]}",
                "hook_failed",
            )
        return ok({"returncode": proc.returncode, "stdout": (proc.stdout or "")[:500]})
    except Exception as e:
        return err(str(e), "hook_failed")


def wrap_launch_args(wrapper: str, launch_args: List[str], variables: Dict[str, str]) -> List[str]:
    """把 wrapper 插到命令最前。支持 $INST_JAVA 等。"""
    wrapper = (wrapper or "").strip()
    if not wrapper:
        return list(launch_args)
    expanded = _expand_hook(wrapper, variables)
    # 简单按空白拆（用户应写可执行路径）
    import shlex

    try:
        parts = shlex.split(expanded, posix=(os.name != "nt"))
    except ValueError:
        parts = expanded.split()
    return parts + list(launch_args)


def spawn_post_exit_hook(
    command: str,
    *,
    instance_name: str,
    instance_dir: str,
    java_path: str,
    process_obj=None,
) -> None:
    """在游戏进程结束后异步跑 post-exit（不阻塞）。"""
    command = (command or "").strip()
    if not command:
        return

    def _runner():
        try:
            if process_obj is not None:
                try:
                    process_obj.wait()
                except Exception:
                    pass
            variables = {
                "INST_NAME": instance_name,
                "INST_ID": instance_name,
                "INST_DIR": instance_dir,
                "INST_MC_DIR": instance_dir,
                "INST_JAVA": java_path,
            }
            expanded = _expand_hook(command, variables)
            subprocess.run(
                expanded,
                shell=True,
                cwd=instance_dir or None,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except Exception:
            pass

    threading.Thread(target=_runner, daemon=True).start()


# ---------------- Discord RPC ----------------

class _DiscordRPC:
    def __init__(self):
        self._client = None
        self._enabled = False
        self._lock = threading.Lock()
        self._app_id = "1123683254248148992"  # 可后续换成 Bloret 自己的

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._enabled:
            self.clear()

    def _ensure(self) -> bool:
        if not self._enabled:
            return False
        if self._client is not None:
            return True
        try:
            from pypresence import Presence  # type: ignore

            self._client = Presence(self._app_id)
            self._client.connect()
            return True
        except Exception:
            self._client = None
            return False

    def set_activity(self, state: str, details: str = "Bloret Launcher") -> None:
        with self._lock:
            if not self._ensure():
                return
            try:
                self._client.update(  # type: ignore
                    state=state[:128],
                    details=details[:128],
                    large_image="minecraft",
                    large_text="Bloret Launcher",
                    start=int(time.time()),
                )
            except Exception:
                try:
                    self._client.close()  # type: ignore
                except Exception:
                    pass
                self._client = None

    def clear(self) -> None:
        with self._lock:
            if self._client is None:
                return
            try:
                self._client.clear()
            except Exception:
                pass
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


_RPC = _DiscordRPC()


def discord_set_enabled(enabled: bool) -> None:
    _RPC.set_enabled(enabled)
    try:
        import modules.config as cfg

        cfg.update_keys(discord_rpc=bool(enabled))
    except Exception:
        pass


def discord_is_enabled() -> bool:
    try:
        import modules.config as cfg

        return bool((cfg.read() or {}).get("discord_rpc"))
    except Exception:
        return False


def discord_set_playing(version_name: str) -> None:
    if not discord_is_enabled():
        _RPC.set_enabled(False)
        return
    _RPC.set_enabled(True)
    _RPC.set_activity(f"Playing {version_name}", "Minecraft via Bloret")


def discord_clear() -> None:
    _RPC.clear()


# ---------------- Crash / Logs ----------------

def list_crash_reports(version_name: str, mc_dir: Optional[str] = None, limit: int = 30) -> ServiceResult[List[Dict[str, Any]]]:
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return err("invalid version", "invalid_version")
    crash_dir = os.path.join(vdir, "crash-reports")
    logs_dir = os.path.join(vdir, "logs")
    items: List[Dict[str, Any]] = []

    def add_from(folder: str, log_type: str, pattern: str):
        if not os.path.isdir(folder):
            return
        try:
            for name in os.listdir(folder):
                if not re.search(pattern, name, re.I):
                    continue
                path = os.path.join(folder, name)
                if not os.path.isfile(path):
                    continue
                try:
                    age = int(os.path.getmtime(path))
                    size = os.path.getsize(path)
                except OSError:
                    age, size = 0, 0
                items.append(
                    {
                        "name": name,
                        "path": path,
                        "type": log_type,
                        "mtime": age,
                        "size": size,
                    }
                )
        except OSError:
            pass

    add_from(crash_dir, "crash", r"\.txt$")
    add_from(logs_dir, "log", r"latest\.log$|\.log\.gz$|\.log$")
    items.sort(key=lambda x: x.get("mtime") or 0, reverse=True)
    return ok(items[: max(1, limit)])


_TOKEN_RE = re.compile(
    r"(access[_-]?token|session|password|authorization)\s*[:=]\s*([^\s\"']+)",
    re.I,
)
_UUID_TOKENish = re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b")


def censor_log_text(text: str) -> str:
    text = _TOKEN_RE.sub(r"\1: ***", text or "")
    text = _UUID_TOKENish.sub("***jwt***", text)
    return text


def read_log_file(path: str, *, max_bytes: int = 256_000, censor: bool = True) -> ServiceResult[Dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return err("file not found", "not_found")
    # 只允许读 version 目录下
    ap = os.path.abspath(path)
    try:
        size = os.path.getsize(ap)
        with open(ap, "rb") as f:
            if size > max_bytes:
                f.seek(-max_bytes, os.SEEK_END)
            raw = f.read()
        # gzip?
        text: str
        if ap.endswith(".gz"):
            import gzip

            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        else:
            text = raw.decode("utf-8", errors="replace")
        if censor:
            text = censor_log_text(text)
        return ok({"path": ap, "size": size, "text": text, "censored": censor})
    except Exception as e:
        return err(str(e), "read_failed")
