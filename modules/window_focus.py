"""Cross-platform helpers for identifying the focused Minecraft window.

Wayland intentionally has no compositor-independent API for reading another
application's focused window.  On Linux we therefore use compositor IPC where
available and return ``None`` when focus cannot be determined.  Callers must
not treat an unknown result as "background".
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Any, Iterable, Optional

import psutil


def _run(command: list[str], timeout: float = 2.0) -> Optional[str]:
    if not command or shutil.which(command[0]) is None:
        return None
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _focused_sway_node(node: Any) -> Optional[dict]:
    if not isinstance(node, dict):
        return None
    if node.get("focused"):
        return node
    for child_key in ("nodes", "floating_nodes"):
        for child in node.get(child_key) or []:
            focused = _focused_sway_node(child)
            if focused is not None:
                return focused
    return None


def _linux_active_window() -> Optional[dict]:
    """Return focused window metadata, or ``None`` if unsupported/unavailable."""
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        output = _run(["hyprctl", "-j", "activewindow"])
        if output:
            try:
                data = json.loads(output)
                if data:
                    return {
                        "pid": data.get("pid"),
                        "title": data.get("title", ""),
                        "class": data.get("class", ""),
                        "source": "hyprctl",
                    }
            except (TypeError, ValueError):
                pass

    if os.environ.get("SWAYSOCK"):
        output = _run(["swaymsg", "-t", "get_tree", "-r"])
        if output:
            try:
                node = _focused_sway_node(json.loads(output))
                if node:
                    properties = node.get("window_properties") or {}
                    return {
                        "pid": node.get("pid"),
                        "title": node.get("name", ""),
                        "class": node.get("app_id") or properties.get("class", ""),
                        "source": "swaymsg",
                    }
            except (TypeError, ValueError):
                pass

    # kdotool uses KWin's scripting API and works for native Wayland windows.
    window_id = _run(["kdotool", "getactivewindow"])
    if window_id:
        pid = _run(["kdotool", "getwindowpid", window_id])
        title = _run(["kdotool", "getwindowname", window_id]) or ""
        return {
            "pid": pid,
            "title": title,
            "class": "",
            "source": "kdotool",
        }

    # This remains useful in X11 sessions and for XWayland-hosted Minecraft.
    window_id = _run(["xdotool", "getactivewindow"])
    if window_id:
        pid = _run(["xdotool", "getwindowpid", window_id])
        title = _run(["xdotool", "getwindowname", window_id]) or ""
        return {
            "pid": pid,
            "title": title,
            "class": "",
            "source": "xdotool",
        }

    # xprop is commonly installed as part of the X11 utilities even when
    # xdotool is absent. KWin publishes _NET_ACTIVE_WINDOW for XWayland
    # clients, which covers Minecraft when GLFW uses X11/XWayland.
    active = _run(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
    if active:
        match = re.search(r"(?:0x[0-9a-fA-F]+|\b\d+\b)\s*$", active)
        if match:
            window_id = match.group(0)
            details = _run(["xprop", "-id", window_id, "_NET_WM_PID", "_NET_WM_NAME", "WM_NAME", "WM_CLASS"])
            if details:
                pid_match = re.search(r"_NET_WM_PID\([^)]*\)\s*=\s*(\d+)", details)
                title_match = re.search(r"(?:_NET_WM_NAME|WM_NAME)\([^)]*\)\s*=\s*\"([^\"]*)\"", details)
                class_match = re.search(r"WM_CLASS\([^)]*\)\s*=\s*(.*)", details)
                if pid_match or title_match or class_match:
                    return {
                        "pid": pid_match.group(1) if pid_match else None,
                        "title": title_match.group(1) if title_match else "",
                        "class": class_match.group(1) if class_match else "",
                        "source": "xprop",
                    }

    return None


def _pid_belongs_to_roots(pid: Any, root_pids: Iterable[Any]) -> Optional[bool]:
    """Return membership, or ``None`` when the PID cannot be inspected."""
    try:
        numeric_pid = int(pid)
    except (TypeError, ValueError):
        return None

    roots = set()
    for root_pid in root_pids:
        try:
            roots.add(int(root_pid))
        except (TypeError, ValueError):
            continue
    if not roots:
        return None

    try:
        current = psutil.Process(numeric_pid)
        while current is not None:
            if current.pid in roots:
                return True
            current = current.parent()
    except psutil.Error:
        return None
    return False


def is_minecraft_foreground(root_pids: Iterable[Any]) -> Optional[bool]:
    """Return whether Minecraft is focused, or ``None`` when it is unknowable."""
    window = _linux_active_window()
    if window is None:
        return None

    pid_match = _pid_belongs_to_roots(window.get("pid"), root_pids)
    if pid_match is not None:
        # A successfully inspected PID is authoritative, including when it
        # belongs to a different concurrently running Minecraft instance.
        return pid_match

    # PID is unavailable or could not be inspected. Use identity as a best-
    # effort compatibility fallback for notifications and single-instance use.
    identity = f"{window.get('title', '')} {window.get('class', '')}".lower()
    if identity.strip():
        return "minecraft" in identity
    return None
