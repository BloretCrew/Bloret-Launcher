"""Small cross-platform process helpers."""

from __future__ import annotations

import os
import signal
import subprocess
import time


def hidden_process_kwargs(**kwargs):
    """Return subprocess kwargs that hide child console windows on Windows."""
    if os.name != "nt":
        return kwargs
    startupinfo = kwargs.pop("startupinfo", None) or subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    kwargs["startupinfo"] = startupinfo
    kwargs["creationflags"] = kwargs.get("creationflags", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kwargs


def terminate_process_tree(pid: int, timeout: float = 3.0) -> bool:
    """Terminate a process and its descendants, returning whether it exited."""
    try:
        import psutil
    except ImportError:
        return False

    try:
        process = psutil.Process(int(pid))
        descendants = process.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.Error, ValueError, TypeError):
        return True

    processes = descendants + [process]
    if os.name != "nt" and process.pid != os.getpid():
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    for child in descendants:
        try:
            child.terminate()
        except psutil.Error:
            pass
    try:
        process.terminate()
    except psutil.Error:
        pass

    _, alive = psutil.wait_procs(processes, timeout=timeout)
    for remaining in alive:
        try:
            remaining.kill()
        except psutil.Error:
            pass
    if alive:
        psutil.wait_procs(alive, timeout=1)
    return not any(p.is_running() for p in processes)
