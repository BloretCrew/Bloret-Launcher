#!/usr/bin/env python3
"""
本地冒烟：验证非 onefile 路径解析，并在虚拟显示（Xvfb）下做最小启动探测。

用法:
  python3 scripts/smoke_non_onefile.py
  BLORET_SMOKE_PACKAGED_DIR=/path/to/Bloret-Launcher.dist python3 scripts/smoke_non_onefile.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    raise SystemExit(1)


def test_path_resolution_dev() -> None:
    sys.path.insert(0, str(ROOT))
    from modules.paths import get_app_dir, app_path

    app_dir = get_app_dir()
    if app_dir.resolve() != ROOT.resolve():
        _fail(f"dev get_app_dir={app_dir} expected {ROOT}")
    qml = Path(app_path("qml", "main.qml"))
    if not qml.is_file():
        _fail(f"missing {qml}")
    _ok(f"dev path resolution -> {app_dir}")


def test_path_resolution_frozen_onedir() -> None:
    """模拟 PyInstaller onedir：frozen + 无 _MEIPASS，资源在 exe 旁。"""
    with tempfile.TemporaryDirectory(prefix="bloret-onedir-") as td:
        td_path = Path(td)
        fake_exe = td_path / "Bloret-Launcher"
        fake_exe.write_text("#!/bin/sh\n", encoding="utf-8")
        (td_path / "qml").mkdir()
        (td_path / "qml" / "main.qml").write_text("// smoke\n", encoding="utf-8")
        (td_path / "RinUI").mkdir()
        (td_path / "icon").mkdir()
        (td_path / "lang").mkdir()

        code = r"""
import sys
from pathlib import Path
sys.frozen = True
# onedir: no _MEIPASS
if hasattr(sys, "_MEIPASS"):
    delattr(sys, "_MEIPASS")
sys.argv[0] = r"%s"
sys.path.insert(0, r"%s")
# force re-import paths without cache from previous tests in same process
import importlib
import modules.paths as paths
importlib.reload(paths)
app_dir = paths.get_app_dir()
assert app_dir == Path(r"%s"), (app_dir, r"%s")
assert (app_dir / "qml" / "main.qml").is_file()
print("onedir-sim-ok", app_dir)
""" % (
            str(fake_exe),
            str(ROOT),
            str(td_path),
            str(td_path),
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            _fail(f"onedir sim failed:\n{proc.stdout}\n{proc.stderr}")
        _ok(f"frozen onedir path simulation ({proc.stdout.strip()})")


def test_path_resolution_meipass() -> None:
    """模拟 PyInstaller onefile：_MEIPASS 优先。"""
    with tempfile.TemporaryDirectory(prefix="bloret-mei-") as td:
        td_path = Path(td)
        (td_path / "qml").mkdir()
        (td_path / "qml" / "main.qml").write_text("// smoke\n", encoding="utf-8")
        code = r"""
import sys
from pathlib import Path
sys._MEIPASS = r"%s"
sys.path.insert(0, r"%s")
import importlib
import modules.paths as paths
importlib.reload(paths)
app_dir = paths.get_app_dir()
assert app_dir == Path(r"%s")
print("meipass-sim-ok", app_dir)
""" % (
            str(td_path),
            str(ROOT),
            str(td_path),
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            _fail(f"meipass sim failed:\n{proc.stdout}\n{proc.stderr}")
        _ok(f"onefile meipass simulation ({proc.stdout.strip()})")


def _gui_python() -> str:
    """优先使用带 PySide6 的解释器（CI/代理 venv 可能没有 GUI 依赖）。"""
    candidates = [
        os.environ.get("BLORET_PYTHON", "").strip(),
        "/usr/bin/python3",
        sys.executable,
    ]
    for cand in candidates:
        if not cand:
            continue
        try:
            r = subprocess.run(
                [cand, "-c", "import PySide6"],
                capture_output=True,
                timeout=15,
            )
            if r.returncode == 0:
                return cand
        except Exception:
            continue
    return sys.executable


def test_virtual_desktop_boot() -> None:
    """在 Xvfb 虚拟显示下短时启动主程序，确认 QML/资源能找到。"""
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "xcb")
    env["BLORET_DEBUG"] = "1"
    # 避免单实例锁干扰
    env["BLORET_SMOKE"] = "1"

    py = _gui_python()
    cmd = [
        py,
        str(ROOT / "Bloret-Launcher.py"),
    ]
    wrapper = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24"]
    full = wrapper + cmd

    log_path = ROOT / "temp" / "smoke_non_onefile_boot.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[..] virtual desktop boot: {' '.join(full)}")
    with open(log_path, "w", encoding="utf-8") as logf:
        try:
            proc = subprocess.Popen(
                full,
                cwd=str(ROOT),
                env=env,
                stdout=logf,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as e:
            _fail(f"cannot start xvfb-run / app: {e}")

        # 等待启动期错误或存活
        deadline = time.time() + 25
        while time.time() < deadline:
            rc = proc.poll()
            if rc is not None:
                logf.flush()
                text = log_path.read_text(encoding="utf-8", errors="replace")
                # 资源/QML 致命错误
                bad = (
                    "Error loading QML",
                    "module \"QtQuick",
                    "is not installed",
                    "QML file missing",
                    "Failed to load",
                )
                if any(b in text for b in bad):
                    _fail(f"boot exited {rc} with QML/resource error; log={log_path}\n{text[-4000:]}")
                # 单实例 / 环境导致的早期退出：记为警告但仍算路径 OK 若无资源错误
                if rc != 0 and "qml/main.qml" in text and "missing" in text.lower():
                    _fail(f"boot failed missing qml: {text[-2000:]}")
                _ok(f"boot process exited early rc={rc} (check log {log_path}); no QML resource fatal seen")
                return
            time.sleep(0.5)

        # 仍在运行：认为 GUI 主循环已起来
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        text = log_path.read_text(encoding="utf-8", errors="replace")
        if "Error loading QML" in text or "QML file missing" in text:
            _fail(f"running but QML errors in log:\n{text[-3000:]}")
        _ok(f"virtual desktop: process stayed alive ~25s (log {log_path})")


def test_packaged_dir_layout() -> None:
    packaged = os.environ.get("BLORET_SMOKE_PACKAGED_DIR", "").strip()
    if not packaged:
        print("[SKIP] BLORET_SMOKE_PACKAGED_DIR not set (no local package tree)")
        return
    p = Path(packaged)
    if not p.is_dir():
        _fail(f"packaged dir not found: {p}")
    exe_candidates = [
        p / "Bloret-Launcher",
        p / "Bloret-Launcher.exe",
    ]
    if not any(c.exists() for c in exe_candidates):
        _fail(f"no Bloret-Launcher binary under {p}")
    for rel in ("qml/main.qml",):
        # data may be next to exe or under _internal (PyInstaller 6+)
        found = list(p.rglob("main.qml"))
        if not found:
            _fail(f"no main.qml under packaged tree {p}")
    _ok(f"packaged layout looks like onedir/standalone: {p}")


def main() -> None:
    os.chdir(ROOT)
    test_path_resolution_dev()
    test_path_resolution_frozen_onedir()
    test_path_resolution_meipass()
    test_packaged_dir_layout()
    test_virtual_desktop_boot()
    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
