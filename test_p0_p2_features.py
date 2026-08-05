"""P0–P2 feature unit tests (no network, no GUI)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent


def _ensure_stubs():
    if "modules" not in sys.modules:
        m = type(sys)("modules")
        m.__path__ = [str(ROOT / "modules")]  # type: ignore
        sys.modules["modules"] = m
    if "modules.services" not in sys.modules:
        m = type(sys)("modules.services")
        m.__path__ = [str(ROOT / "modules" / "services")]  # type: ignore
        sys.modules["modules.services"] = m
    if "modules.log" not in sys.modules:
        log_mod = type(sys)("modules.log")

        def log(msg, *a, **k):
            pass

        log_mod.log = log  # type: ignore
        sys.modules["modules.log"] = log_mod
    if "modules.config" not in sys.modules:
        cfg = type(sys)("modules.config")
        cfg.read = lambda: {}  # type: ignore
        cfg.update_keys = lambda **k: None  # type: ignore
        sys.modules["modules.config"] = cfg
    if "modules.globals" not in sys.modules:
        g = type(sys)("modules.globals")
        g.datapath = tempfile.gettempdir()
        g._pending_launch_hooks = None
        sys.modules["modules.globals"] = g
    if "modules.i18n" not in sys.modules:
        i18n = type(sys)("modules.i18n")
        i18n.i18nText = lambda x: x  # type: ignore
        sys.modules["modules.i18n"] = i18n


def _import_service(mod_file: str, qualname: str):
    _ensure_stubs()
    # base first
    if "modules.services.base" not in sys.modules:
        base_path = ROOT / "modules" / "services" / "base.py"
        spec = importlib.util.spec_from_file_location("modules.services.base", base_path)
        assert spec and spec.loader
        base = importlib.util.module_from_spec(spec)
        sys.modules["modules.services.base"] = base
        spec.loader.exec_module(base)
    if "modules.services.paths_util" not in sys.modules and mod_file != "paths_util.py":
        pu_path = ROOT / "modules" / "services" / "paths_util.py"
        if pu_path.exists():
            spec = importlib.util.spec_from_file_location("modules.services.paths_util", pu_path)
            assert spec and spec.loader
            pu = importlib.util.module_from_spec(spec)
            sys.modules["modules.services.paths_util"] = pu
            spec.loader.exec_module(pu)

    path = ROOT / "modules" / "services" / mod_file
    name = f"modules.services.{qualname}"
    if name in sys.modules and getattr(sys.modules[name], "__file__", None):
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestContentIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mc = self.tmp.name
        self.version = "1.21.1-Fabric"
        self.vdir = Path(self.mc) / "versions" / self.version
        self.mods = self.vdir / "mods"
        self.mods.mkdir(parents=True)
        (self.mods / "demo.jar").write_bytes(b"hello-mod-bytes")
        self.ci = _import_service("content_index.py", "content_index")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_and_upsert(self):
        with mock.patch.object(self.ci, "safe_version_dir", return_value=str(self.vdir)):
            with mock.patch.object(self.ci, "minecraft_dir", return_value=self.mc):
                idx = self.ci.scan_filesystem(self.version, mc_dir=self.mc, compute_hash=True)
                self.assertIn("items", idx)
                items = self.ci.list_indexed(self.version, kind="mod", mc_dir=self.mc)
                self.assertTrue(any(i["filename"] == "demo.jar" for i in items))
                row = self.ci.upsert_item(
                    self.version,
                    path=str(self.mods / "demo.jar"),
                    kind="mod",
                    project_id="AABB",
                    version_id="VV11",
                    source="modrinth",
                    title="Demo",
                    mc_dir=self.mc,
                )
                self.assertEqual(row["project_id"], "AABB")
                found = self.ci.get_by_project(self.version, "AABB", mc_dir=self.mc)
                self.assertIsNotNone(found)
                assert found is not None
                self.assertEqual(found["version_id"], "VV11")
                self.assertTrue((self.vdir / "content-index.json").is_file())


class TestInstanceSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mc = self.tmp.name
        self.version = "TestInst"
        self.vdir = Path(self.mc) / "versions" / self.version
        self.vdir.mkdir(parents=True)
        self.mod = _import_service("instance_settings.py", "instance_settings")

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_load_overrides(self):
        with mock.patch.object(self.mod, "safe_version_dir", return_value=str(self.vdir)):
            with mock.patch.object(self.mod, "minecraft_dir", return_value=self.mc):
                res = self.mod.save(
                    self.version,
                    {
                        "java_max_memory": 8192,
                        "jvm_args": "-XX:+UseG1GC",
                        "hooks": {"pre_launch": "echo hi"},
                        "quick_play": {"type": "singleplayer", "world": "New World"},
                    },
                    mc_dir=self.mc,
                )
                self.assertTrue(res.ok)
                loaded = self.mod.load(self.version, mc_dir=self.mc)
                self.assertEqual(loaded["java_max_memory"], 8192)
                self.assertIn("UseG1GC", loaded["jvm_args"])
                self.assertEqual(loaded["hooks"]["pre_launch"], "echo hi")
                merged = self.mod.resolve_launch_overrides(
                    self.version,
                    {"java_min_memory": 512, "java_max_memory": 2048},
                    mc_dir=self.mc,
                )
                self.assertEqual(merged["java_max_memory"], 8192)
                self.assertTrue(any("UseG1GC" in a for a in merged["extra_jvm_args"]))
                self.assertEqual(merged["quick_play"]["world"], "New World")


class TestQuickPlayArgs(unittest.TestCase):
    def test_args(self):
        mod = _import_service("worlds_service.py", "worlds_service")
        args = mod.quick_play_game_args({"type": "singleplayer", "world": "MyWorld"})
        self.assertIn("--quickPlaySingleplayer", args)
        self.assertIn("MyWorld", args)
        args2 = mod.quick_play_game_args({"type": "multiplayer", "server": "play.example.com:25565"})
        self.assertIn("--quickPlayMultiplayer", args2)
        self.assertIn("--server", args2)


class TestMrpackCandidates(unittest.TestCase):
    def test_candidates_and_collect(self):
        _ensure_stubs()
        path = ROOT / "modules" / "mrpack_export.py"
        name = "modules.mrpack_export"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmp:
            inst = Path(tmp)
            (inst / "mods").mkdir()
            (inst / "mods" / "a.jar").write_bytes(b"jar")
            (inst / "logs").mkdir()
            (inst / "logs" / "latest.log").write_text("x")
            (inst / "config").mkdir()
            (inst / "config" / "x.toml").write_text("a=1")
            cands = mod.get_export_candidates(str(inst))
            paths = {c["path"] for c in cands}
            self.assertIn("mods/a.jar", paths)
            self.assertIn("config/x.toml", paths)
            self.assertNotIn("logs/latest.log", paths)
            files = mod.collect_files(str(inst), selected_paths=["mods/a.jar"])
            self.assertEqual(len(files), 1)


class TestSkinsLocal(unittest.TestCase):
    def test_import_list_delete(self):
        mod = _import_service("skins_service.py", "skins_service")
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(mod, "_skins_root", return_value=tmp):
                png = Path(tmp) / "src.png"
                png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
                res = mod.import_skin_file(str(png), name="test", variant="slim")
                self.assertTrue(res.ok)
                listed = mod.list_skins()
                self.assertTrue(listed.ok)
                data = listed.data or []
                self.assertEqual(len(data), 1)
                sid = data[0]["id"]
                self.assertTrue(mod.delete_skin(sid).ok)
                self.assertEqual(len(mod.list_skins().data or []), 0)


class TestLogCensor(unittest.TestCase):
    def test_censor(self):
        mod = _import_service("runtime_extras.py", "runtime_extras")
        text = "accessToken: supersecrettoken123 and Authorization: Bearer abc"
        out = mod.censor_log_text(text)
        self.assertNotIn("supersecrettoken123", out)
        self.assertIn("***", out)


class TestModrinthDepFilter(unittest.TestCase):
    def test_only_required(self):
        mod = _import_service("modrinth_content.py", "modrinth_content")
        with mock.patch.object(mod, "resolve_download_info") as m:
            m.side_effect = lambda pid, **kw: {
                "project_id": pid,
                "version_id": "v1",
                "filename": f"{pid}.jar",
                "url": "http://x",
                "dependencies": [],
            }
            deps = [
                {"project_id": "req1", "dependency_type": "required"},
                {"project_id": "opt1", "dependency_type": "optional"},
                {"project_id": "emb1", "dependency_type": "embedded"},
            ]
            out = mod.collect_required_dependencies(deps)
            ids = {x["project_id"] for x in out}
            self.assertEqual(ids, {"req1"})


if __name__ == "__main__":
    unittest.main()
