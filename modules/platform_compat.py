"""
platform_compat.py
Cross-platform helpers for Bloret Launcher.

Centralizes OS detection so FreeBSD/Linux/macOS/Windows branches stay consistent.
On FreeBSD, Mojang library *rules* map to linux, while natives come from the
system games/lwjgl3 package (not Mojang natives-linux ELF).
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple


def system_name() -> str:
    """Return platform.system() (e.g. Windows, Linux, Darwin, FreeBSD)."""
    return platform.system()


def is_windows() -> bool:
    return sys.platform == "win32" or system_name() == "Windows"


def is_darwin() -> bool:
    return sys.platform == "darwin" or system_name() == "Darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux") or system_name() == "Linux"


def is_freebsd() -> bool:
    name = system_name()
    return name == "FreeBSD" or sys.platform.startswith("freebsd")


def is_posix() -> bool:
    return os.name == "posix"


def mojang_os_name() -> str:
    """
    OS id used by Mojang version JSON rules / natives map keys.

    FreeBSD is mapped to ``linux`` for library *rules* (so linux-only jars are
    included). Native classifiers are handled separately via uses_system_lwjgl().
    """
    name = system_name()
    if name == "Windows":
        return "windows"
    if name == "Darwin":
        return "osx"
    if name == "Linux":
        return "linux"
    if name == "FreeBSD" or sys.platform.startswith("freebsd"):
        return "linux"
    # Unknown Unix-like: lower-case system name (may not match Mojang rules)
    return name.lower()


def mojang_arch() -> str:
    """Mojang rule arch: x86 or x86_64 (simplified)."""
    machine = platform.machine().lower()
    if machine in ("x86", "i386", "i686"):
        return "x86"
    return "x86_64"


def arch_bits() -> str:
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64", "aarch64", "arm64"):
        return "64"
    return "32"


def uses_system_lwjgl() -> bool:
    """True when FreeBSD should inject ports/system LWJGL instead of Mojang natives."""
    return is_freebsd()


def system_lwjgl_lib_dir() -> Path:
    env = os.environ.get("BLORET_LWJGL_LIB", "").strip()
    if env:
        return Path(env)
    return Path("/usr/local/lib/lwjgl3")


def system_lwjgl_jar_dir() -> Path:
    env = os.environ.get("BLORET_LWJGL_JARS", "").strip()
    if env:
        return Path(env)
    return Path("/usr/local/share/java/classes/lwjgl3")


def probe_system_lwjgl() -> Tuple[bool, str]:
    """
    Check that system LWJGL natives (and preferably jars) exist.

    Returns (ok, message).
    """
    lib_dir = system_lwjgl_lib_dir()
    jar_dir = system_lwjgl_jar_dir()
    core_so = lib_dir / "liblwjgl.so"
    if not lib_dir.is_dir():
        return False, (
            f"未找到系统 LWJGL 库目录: {lib_dir}。"
            "请安装: pkg install lwjgl3"
            "（或设置环境变量 BLORET_LWJGL_LIB）"
        )
    if not core_so.is_file():
        # Some builds may use different names; accept any .so
        sos = list(lib_dir.glob("*.so"))
        if not sos:
            return False, (
                f"系统 LWJGL 目录中无 .so: {lib_dir}。"
                "请安装: pkg install lwjgl3"
            )
    if not jar_dir.is_dir() or not any(jar_dir.glob("*.jar")):
        return False, (
            f"未找到系统 LWJGL jar 目录: {jar_dir}。"
            "请安装: pkg install lwjgl3"
            "（或设置环境变量 BLORET_LWJGL_JARS）"
        )
    return True, f"system LWJGL ok lib={lib_dir} jars={jar_dir}"


def java_candidate_roots() -> list:
    """Extra JVM tree roots beyond JAVA_HOME / PATH."""
    roots = [
        os.path.expanduser("~/.jdks"),
        os.path.expanduser("~/.sdkman/candidates/java"),
        "/usr/lib/jvm",
        "/usr/java",
        "/opt/java",
        "/Library/Java/JavaVirtualMachines",
        "/usr/local/lib/jvm",
    ]
    # FreeBSD OpenJDK packages: /usr/local/openjdk17, openjdk21, ...
    local = Path("/usr/local")
    if local.is_dir():
        try:
            for entry in sorted(local.glob("openjdk*")):
                if entry.is_dir():
                    roots.append(str(entry))
        except OSError:
            pass
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        root = os.environ.get(env_name)
        if root:
            roots.extend(
                os.path.join(root, vendor)
                for vendor in (
                    "Java",
                    "Eclipse Adoptium",
                    "Zulu",
                    "BellSoft",
                    "Microsoft",
                )
            )
    return roots


def datapath_default() -> str:
    """Default Bloret-Launcher user data directory."""
    if is_windows():
        return os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), "Bloret-Launcher"
        )
    if is_darwin():
        return os.path.expanduser("~/Library/Application Support/Bloret-Launcher")
    # Linux / FreeBSD / other XDG-ish
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg:
        return os.path.join(xdg, "Bloret-Launcher")
    return os.path.expanduser("~/.local/share/Bloret-Launcher")


def update_artifact_kind() -> str:
    """
    Which update package this platform expects.

    windows_setup | linux_zip | macos_zip | freebsd_zip | unsupported
    """
    if is_windows():
        return "windows_setup"
    if is_freebsd():
        return "freebsd_zip"
    if is_darwin():
        return "macos_zip"
    if is_linux():
        return "linux_zip"
    return "unsupported"


def open_path_command(path: str) -> list:
    """Command list to open a file/folder in the desktop environment."""
    if is_windows():
        return ["explorer", path]
    if is_darwin():
        return ["open", path]
    return ["xdg-open", path]


def easytier_release_zip_name(version: str = "v2.6.4") -> Optional[str]:
    """
    EasyTier GitHub release asset name for the current OS/arch, or None if unknown.
    version should include leading 'v' (e.g. v2.6.4).
    """
    machine = platform.machine().lower()
    if is_windows():
        return f"easytier-windows-x86_64-{version}.zip"
    if is_freebsd():
        if machine in ("amd64", "x86_64"):
            return f"easytier-freebsd-13.2-x86_64-{version}.zip"
        return None
    if is_darwin():
        if machine in ("arm64", "aarch64"):
            return f"easytier-macos-aarch64-{version}.zip"
        return f"easytier-macos-x86_64-{version}.zip"
    if is_linux():
        if machine in ("aarch64", "arm64"):
            return f"easytier-linux-aarch64-{version}.zip"
        return f"easytier-linux-x86_64-{version}.zip"
    return None
