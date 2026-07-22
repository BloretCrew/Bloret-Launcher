"""Unit tests for FreeBSD / platform helpers (no real GUI / psutil required)."""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _install_stubs():
    """Provide minimal stubs when PySide6 / psutil are unavailable."""

    class _Signal:
        def __init__(self, *a, **k):
            self._slots = []

        def connect(self, fn):
            self._slots.append(fn)

        def emit(self, *a, **k):
            for s in self._slots:
                s(*a, **k)

    class _Mod(types.ModuleType):
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError(name)
            return type(
                name,
                (),
                {
                    "__init__": lambda self, *a, **k: None,
                    "instance": staticmethod(lambda: None),
                },
            )

    for name in (
        "PySide6",
        "PySide6.QtWidgets",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtNetwork",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtSvg",
        "psutil",
        "send2trash",
    ):
        if name not in sys.modules:
            sys.modules[name] = _Mod(name)

    core = sys.modules["PySide6.QtCore"]
    # Always overwrite: _Mod.__getattr__ would otherwise invent empty classes
    # that break `show_error = Signal(...)` / `.connect(...)`.
    core.Signal = lambda *a, **k: _Signal()
    core.Slot = lambda *a, **k: (lambda f: f)
    core.Property = lambda *a, **k: (lambda f: f)
    core.Qt = type("Qt", (), {"UserRole": 0})()
    core.QObject = type("QObject", (), {"__init__": lambda self, *a, **k: None})


_install_stubs()


class PlatformCompatTests(unittest.TestCase):
    def test_mojang_os_freebsd_maps_to_linux(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "system_name", return_value="FreeBSD"):
            with mock.patch.object(pc.sys, "platform", "freebsd14"):
                self.assertEqual(pc.mojang_os_name(), "linux")
                self.assertTrue(pc.is_freebsd())
                self.assertTrue(pc.uses_system_lwjgl())
                self.assertEqual(pc.update_artifact_kind(), "freebsd_zip")

    def test_mojang_os_linux(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "system_name", return_value="Linux"):
            with mock.patch.object(pc.sys, "platform", "linux"):
                self.assertEqual(pc.mojang_os_name(), "linux")
                self.assertFalse(pc.uses_system_lwjgl())
                self.assertEqual(pc.update_artifact_kind(), "linux_zip")

    def test_mojang_os_darwin(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "system_name", return_value="Darwin"):
            with mock.patch.object(pc.sys, "platform", "darwin"):
                self.assertEqual(pc.mojang_os_name(), "osx")
                self.assertEqual(pc.update_artifact_kind(), "macos_zip")

    def test_mojang_os_windows(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "system_name", return_value="Windows"):
            with mock.patch.object(pc.sys, "platform", "win32"):
                self.assertEqual(pc.mojang_os_name(), "windows")
                self.assertTrue(pc.is_windows())

    def test_datapath_respects_xdg(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "is_windows", return_value=False):
            with mock.patch.object(pc, "is_darwin", return_value=False):
                with mock.patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/xdg-data"}):
                    self.assertEqual(
                        pc.datapath_default(), "/tmp/xdg-data/Bloret-Launcher"
                    )

    def test_easytier_freebsd_zip_name(self):
        from modules import platform_compat as pc

        with mock.patch.object(pc, "is_freebsd", return_value=True):
            with mock.patch.object(pc, "is_windows", return_value=False):
                with mock.patch.object(pc, "is_darwin", return_value=False):
                    with mock.patch.object(pc, "is_linux", return_value=False):
                        with mock.patch.object(pc.platform, "machine", return_value="amd64"):
                            name = pc.easytier_release_zip_name("v2.6.4")
                            self.assertEqual(
                                name, "easytier-freebsd-13.2-x86_64-v2.6.4.zip"
                            )


class InstallLaunchUpdateTests(unittest.TestCase):
    def test_native_classifier_none_on_freebsd(self):
        from modules import platform_compat as pc
        from modules import install

        lib = {"natives": {"linux": "natives-linux", "windows": "natives-windows"}}
        with mock.patch.object(pc, "uses_system_lwjgl", return_value=True):
            self.assertIsNone(install._native_classifier(lib))

    def test_native_classifier_linux_host(self):
        from modules import platform_compat as pc
        from modules import install

        lib = {"natives": {"linux": "natives-linux-${arch}"}}
        with mock.patch.object(pc, "uses_system_lwjgl", return_value=False):
            with mock.patch.object(pc, "mojang_os_name", return_value="linux"):
                with mock.patch.object(pc, "arch_bits", return_value="64"):
                    self.assertEqual(
                        install._native_classifier(lib), "natives-linux-64"
                    )

    def test_rule_matches_linux_when_mapped(self):
        from modules import platform_compat as pc
        from modules import install

        with mock.patch.object(pc, "mojang_os_name", return_value="linux"):
            self.assertTrue(
                install._rule_matches({"action": "allow", "os": {"name": "linux"}})
            )

    def test_update_pick_url_skips_exe_on_unix(self):
        from modules import platform_compat as pc
        from modules import update as upd

        res = {
            "downloads": {"stable": {"gitcode": "https://example.com/Setup.exe"}},
            "latestVersion": "1",
        }
        with mock.patch.object(pc, "is_windows", return_value=False):
            with mock.patch.object(pc, "is_freebsd", return_value=True):
                with mock.patch.object(pc, "is_linux", return_value=False):
                    with mock.patch.object(pc, "is_darwin", return_value=False):
                        with mock.patch.object(
                            pc, "update_artifact_kind", return_value="freebsd_zip"
                        ):
                            url, kind = upd._pick_download_url(res)
                            self.assertIsNone(url)
                            self.assertEqual(kind, "freebsd_zip")

    def test_update_pick_url_freebsd_key(self):
        from modules import platform_compat as pc
        from modules import update as upd

        res = {
            "downloads": {
                "stable": {
                    "freebsd": "https://example.com/Bloret-Launcher-FreeBSD-amd64.zip"
                }
            }
        }
        with mock.patch.object(pc, "is_windows", return_value=False):
            with mock.patch.object(pc, "is_freebsd", return_value=True):
                with mock.patch.object(pc, "is_linux", return_value=False):
                    with mock.patch.object(pc, "is_darwin", return_value=False):
                        with mock.patch.object(
                            pc, "update_artifact_kind", return_value="freebsd_zip"
                        ):
                            url, kind = upd._pick_download_url(res)
                            self.assertTrue(url.endswith(".zip"))
                            self.assertEqual(kind, "freebsd_zip")

    def test_classpath_rewrite_and_natives_prepare(self):
        from modules import platform_compat as pc
        from modules import launch

        tmp = Path(tempfile.mkdtemp())
        try:
            jar_dir = tmp / "jars"
            jar_dir.mkdir()
            (jar_dir / "lwjgl.jar").write_bytes(b"sys")
            (jar_dir / "lwjgl-opengl.jar").write_bytes(b"sys")
            cp = [
                str(tmp / "lwjgl-3.3.1.jar"),
                str(tmp / "lwjgl-opengl-3.3.1.jar"),
                str(tmp / "other.jar"),
            ]
            for p in cp:
                Path(p).write_bytes(b"m")
            with mock.patch.object(pc, "uses_system_lwjgl", return_value=True):
                with mock.patch.object(pc, "system_lwjgl_jar_dir", return_value=jar_dir):
                    out = launch._rewrite_classpath_with_system_lwjgl(cp)
            self.assertTrue(out[0].endswith("lwjgl.jar"))
            self.assertIn("jars", out[0])

            lib_dir = tmp / "lib"
            lib_dir.mkdir()
            (lib_dir / "liblwjgl.so").write_bytes(b"so")
            natives = tmp / "natives"
            natives.mkdir()
            with mock.patch.object(pc, "uses_system_lwjgl", return_value=True):
                with mock.patch.object(pc, "system_lwjgl_lib_dir", return_value=lib_dir):
                    with mock.patch.object(
                        pc, "system_lwjgl_jar_dir", return_value=jar_dir
                    ):
                        launch._prepare_system_lwjgl_natives(str(natives))
            self.assertTrue((natives / "liblwjgl.so").exists())
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
