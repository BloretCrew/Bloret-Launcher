"""Java runtime discovery, probing, and Minecraft-version selection helpers."""

import os
import platform
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from modules.log import log
from modules.process_utils import hidden_process_kwargs

# Process-local cache for scan_java_runtimes (avoids walk + java -version every launch)
_runtime_cache_lock = threading.Lock()
_runtime_cache = {
    "runtimes": None,
    "paths_key": None,
    "extra_roots": None,
    "cached_at": 0.0,
}
_RUNTIME_CACHE_TTL_SEC = 300.0


def java_major_version(version_output):
    """Return the major Java version from `java -version` output."""
    match = re.search(r'version\s+"([^"]+)"', version_output or "", re.IGNORECASE)
    if not match:
        match = re.search(r'(?:openjdk|java)\s+([0-9][^\s]*)', version_output or "", re.IGNORECASE)
    if not match:
        return None
    version_text = match.group(1)
    parts = version_text.split(".")
    try:
        return int(parts[1] if parts[0] == "1" and len(parts) > 1 else parts[0])
    except (TypeError, ValueError):
        return None


def probe_java(java_path, timeout=10):
    """Probe a Java executable and return QML/JSON-friendly metadata."""
    path = os.path.abspath(os.path.expanduser(str(java_path or "")))
    info = {
        "path": path,
        "major": 0,
        "version": "",
        "vendor": "",
        "display": path,
        "valid": False,
        "error": "",
    }
    if not path or not os.path.isfile(path):
        info["error"] = "Java 可执行文件不存在"
        return info
    try:
        result = subprocess.run(
            [path, "-version"], capture_output=True, text=True, timeout=timeout,
            **hidden_process_kwargs(),
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        major = java_major_version(output)
        first_line = output.splitlines()[0].strip() if output else ""
        vendor = "OpenJDK" if "openjdk" in output.lower() else "Java"
        if "temurin" in output.lower():
            vendor = "Eclipse Temurin"
        elif "zulu" in output.lower():
            vendor = "Azul Zulu"
        elif "graalvm" in output.lower():
            vendor = "GraalVM"
        info.update({
            "major": major or 0,
            "version": first_line,
            "vendor": vendor,
            "valid": result.returncode == 0 and major is not None,
        })
        if not info["valid"]:
            info["error"] = first_line or f"java -version 退出码 {result.returncode}"
        label = f"Java {major} · {vendor}" if major else "无法识别的 Java"
        info["display"] = f"{label} — {path}"
    except Exception as error:
        info["error"] = str(error)
        info["display"] = f"无效 Java — {path}"
    return info


def _candidate_roots(extra_roots=None):
    roots = [
        os.path.expanduser("~/.jdks"),
        os.path.expanduser("~/.sdkman/candidates/java"),
        "/usr/lib/jvm",
        "/usr/java",
        "/opt/java",
        "/Library/Java/JavaVirtualMachines",
    ]
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        root = os.environ.get(env_name)
        if root:
            roots.extend(os.path.join(root, vendor) for vendor in (
                "Java", "Eclipse Adoptium", "Zulu", "BellSoft", "Microsoft"
            ))
    if extra_roots:
        roots.extend(extra_roots)
    return roots


def discover_java_paths(extra_roots=None):
    """Discover Java executables on Windows, Linux, and macOS."""
    candidates = []
    java_home = os.environ.get("JAVA_HOME")
    executable = "java.exe" if os.name == "nt" else "java"
    if java_home:
        candidates.append(os.path.join(java_home, "bin", executable))
    path_java = shutil.which("java") or shutil.which("java.exe")
    if path_java:
        candidates.append(path_java)

    for root in _candidate_roots(extra_roots):
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                # JVM trees are shallow; avoid scanning documentation/source trees.
                dirnames[:] = [name for name in dirnames if name.lower() not in {
                    "docs", "demo", "include", "jmods", "legal", "man", "src"
                }]
                if os.path.basename(dirpath).lower() == "bin" and executable in filenames:
                    candidates.append(os.path.join(dirpath, executable))
        except OSError as error:
            log(f"扫描 Java 目录失败 {root}: {error}")

    unique = []
    seen = set()
    for candidate in candidates:
        try:
            canonical = os.path.normcase(os.path.realpath(candidate))
        except OSError:
            canonical = os.path.normcase(os.path.abspath(candidate))
        if canonical in seen or not os.path.isfile(candidate):
            continue
        seen.add(canonical)
        unique.append(os.path.abspath(candidate))
    return unique


def invalidate_java_runtime_cache():
    """Clear process-local Java scan cache (call after settings change / re-scan)."""
    with _runtime_cache_lock:
        _runtime_cache["runtimes"] = None
        _runtime_cache["paths_key"] = None
        _runtime_cache["extra_roots"] = None
        _runtime_cache["cached_at"] = 0.0
    log("Java 运行时缓存已失效")


def scan_java_runtimes(extra_roots=None, *, force_refresh=False):
    paths = discover_java_paths(extra_roots)
    paths_key = tuple(os.path.normcase(os.path.abspath(p)) for p in paths)
    roots_key = tuple(extra_roots or ())
    now = time.monotonic()

    with _runtime_cache_lock:
        cached = _runtime_cache["runtimes"]
        cache_valid = (
            not force_refresh
            and cached is not None
            and _runtime_cache["paths_key"] == paths_key
            and _runtime_cache["extra_roots"] == roots_key
            and (now - _runtime_cache["cached_at"]) < _RUNTIME_CACHE_TTL_SEC
        )
        if cache_valid:
            log(
                f"Java 扫描使用缓存：{len(cached)} 个候选，"
                f"其中 {sum(1 for item in cached if item['valid'])} 个有效"
            )
            return list(cached)

    runtimes = [probe_java(path) for path in paths]
    runtimes.sort(key=lambda item: (not item["valid"], -item["major"], item["path"].lower()))
    log(f"Java 扫描完成：发现 {len(runtimes)} 个候选，其中 {sum(1 for item in runtimes if item['valid'])} 个有效")

    with _runtime_cache_lock:
        _runtime_cache["runtimes"] = list(runtimes)
        _runtime_cache["paths_key"] = paths_key
        _runtime_cache["extra_roots"] = roots_key
        _runtime_cache["cached_at"] = now
    return runtimes


def select_java_runtime(config_data, required_major=None, extra_roots=None):
    """Select a Java runtime according to automatic/fixed launcher settings."""
    mode = config_data.get("java_mode")
    legacy_path = config_data.get("java_path", config_data.get("Java_Path", "Auto"))
    if mode not in {"auto", "fixed"}:
        mode = "auto" if not legacy_path or legacy_path == "Auto" else "fixed"
    fixed_path = config_data.get("java_fixed_path") or (legacy_path if legacy_path != "Auto" else "")
    required = int(required_major) if required_major not in (None, "") else None
    log(f"Java 选择开始：模式={mode}，Minecraft 要求主版本={required or '未声明'}")

    if mode == "fixed":
        info = probe_java(fixed_path)
        log(f"固定 Java 探测：路径={fixed_path}，版本={info['major'] or '未知'}，有效={info['valid']}")
        if not info["valid"]:
            raise RuntimeError(f"固定 Java 无效：{fixed_path or '未选择路径'}。请在设置中重新选择 Java。")
        if required and info["major"] != required:
            raise RuntimeError(
                f"当前 Minecraft 需要 Java {required}，但固定 Java 是 Java {info['major']}。"
                "请在设置中选择匹配版本，或切换到“自动选择”。"
            )
        return info

    runtimes = scan_java_runtimes(extra_roots)
    for info in runtimes:
        if info["valid"] and (required is None or info["major"] == required):
            log(f"自动选择 Java：{info['path']}（Java {info['major']}）")
            return info

    available = sorted({item["major"] for item in runtimes if item["valid"] and item["major"]})
    if required:
        available_text = "、".join(map(str, available)) if available else "无"
        raise RuntimeError(
            f"当前 Minecraft 需要 Java {required}，但未找到匹配运行时（已发现：{available_text}）。"
            f"请安装 Java {required}，或在设置的 Java 选项中选择对应可执行文件。"
        )
    raise RuntimeError("未找到可用的 Java。请安装 Java，或在设置中选择 Java 可执行文件。")
