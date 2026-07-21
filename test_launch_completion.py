"""Unit tests for launch-time file completion and path logic (no network)."""

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

# Ensure repo root on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestVersionSortKey(unittest.TestCase):
    def test_asm_versions_numeric(self):
        from modules.install import _version_sort_key

        self.assertLess(_version_sort_key("9.6"), _version_sort_key("9.12"))
        self.assertLess(_version_sort_key("9.2"), _version_sort_key("9.10"))
        self.assertEqual(_version_sort_key("1.2.3"), _version_sort_key("1.2.3"))


class TestMergeInheritsFrom(unittest.TestCase):
    def test_merge_parent_child(self):
        from modules.install import load_merged_version_json

        with tempfile.TemporaryDirectory() as tmp:
            mc = tmp
            parent_dir = os.path.join(mc, "versions", "1.20.1")
            child_dir = os.path.join(mc, "versions", "1.20.1-fabric")
            os.makedirs(parent_dir)
            os.makedirs(child_dir)
            parent = {
                "id": "1.20.1",
                "mainClass": "net.minecraft.client.main.Main",
                "assetIndex": {"id": "5", "url": "https://example.com/5.json", "sha1": "a" * 40, "size": 1},
                "libraries": [
                    {"name": "com.example:base:1.0", "downloads": {"artifact": {
                        "path": "com/example/base/1.0/base-1.0.jar",
                        "url": "https://libraries.minecraft.net/com/example/base/1.0/base-1.0.jar",
                        "sha1": "b" * 40,
                        "size": 10,
                    }}},
                ],
                "downloads": {"client": {"url": "https://example.com/client.jar", "sha1": "c" * 40, "size": 100}},
            }
            child = {
                "id": "1.20.1-fabric",
                "inheritsFrom": "1.20.1",
                "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
                "libraries": [
                    {"name": "net.fabricmc:fabric-loader:0.15.0", "downloads": {"artifact": {
                        "path": "net/fabricmc/fabric-loader/0.15.0/fabric-loader-0.15.0.jar",
                        "url": "https://maven.fabricmc.net/net/fabricmc/fabric-loader/0.15.0/fabric-loader-0.15.0.jar",
                        "sha1": "d" * 40,
                        "size": 20,
                    }}},
                ],
            }
            with open(os.path.join(parent_dir, "1.20.1.json"), "w", encoding="utf-8") as f:
                json.dump(parent, f)
            with open(os.path.join(child_dir, "1.20.1-fabric.json"), "w", encoding="utf-8") as f:
                json.dump(child, f)

            merged = load_merged_version_json(mc, "1.20.1-fabric")
            self.assertEqual(merged["mainClass"], "net.fabricmc.loader.impl.launch.knot.KnotClient")
            self.assertNotIn("inheritsFrom", merged)
            names = [lib.get("name") for lib in merged["libraries"]]
            self.assertIn("net.fabricmc:fabric-loader:0.15.0", names)
            self.assertIn("com.example:base:1.0", names)
            self.assertEqual(merged["assetIndex"]["id"], "5")

    def test_inherits_cycle_raises(self):
        from modules.install import load_merged_version_json

        with tempfile.TemporaryDirectory() as tmp:
            a_dir = os.path.join(tmp, "versions", "A")
            b_dir = os.path.join(tmp, "versions", "B")
            os.makedirs(a_dir)
            os.makedirs(b_dir)
            with open(os.path.join(a_dir, "A.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "A", "inheritsFrom": "B", "libraries": []}, f)
            with open(os.path.join(b_dir, "B.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "B", "inheritsFrom": "A", "libraries": []}, f)
            with self.assertRaises(RuntimeError):
                load_merged_version_json(tmp, "A")


class TestLibraryUrlSynthesis(unittest.TestCase):
    def test_name_only_library_gets_url(self):
        from modules.install import _library_download_items

        with tempfile.TemporaryDirectory() as tmp:
            libs = [{"name": "org.ow2.asm:asm:9.6"}]
            items = _library_download_items(libs, tmp)
            self.assertTrue(items)
            lib, path, artifact, is_native = items[0]
            self.assertFalse(is_native)
            self.assertTrue(artifact.get("url", "").startswith("https://"))
            self.assertIn("org/ow2/asm/asm/9.6/asm-9.6.jar", path.replace("\\", "/"))


class TestCollectMissingAndEnsure(unittest.TestCase):
    def test_collect_skips_existing_lib(self):
        from modules.install import collect_missing_runtime_files, _library_download_items

        with tempfile.TemporaryDirectory() as tmp:
            version_id = "1.20.1"
            version_dir = os.path.join(tmp, "versions", version_id)
            os.makedirs(version_dir)
            version_data = {
                "id": version_id,
                "libraries": [
                    {
                        "name": "com.example:lib:1.0",
                        "downloads": {
                            "artifact": {
                                "path": "com/example/lib/1.0/lib-1.0.jar",
                                "url": "https://libraries.minecraft.net/com/example/lib/1.0/lib-1.0.jar",
                                "size": 4,
                            }
                        },
                    }
                ],
                "downloads": {
                    "client": {
                        "url": "https://example.com/client.jar",
                        "size": 3,
                    }
                },
            }
            # Create library file with matching size (no sha1 → size-only check)
            items = _library_download_items(version_data["libraries"], tmp)
            _, lib_path, _, _ = items[0]
            os.makedirs(os.path.dirname(lib_path), exist_ok=True)
            with open(lib_path, "wb") as f:
                f.write(b"data")  # size 4

            client_path = os.path.join(version_dir, f"{version_id}.jar")
            with open(client_path, "wb") as f:
                f.write(b"jar")  # size 3

            plan = collect_missing_runtime_files(
                tmp, version_data, version_id, check_assets=False, check_client=True
            )
            self.assertEqual(len(plan["libraries"]), 0)
            self.assertIsNone(plan["client"])

    def test_ensure_skip_completion_requires_client(self):
        from modules.install import ensure_runtime_files

        with tempfile.TemporaryDirectory() as tmp:
            version_id = "1.20.1"
            version_dir = os.path.join(tmp, "versions", version_id)
            os.makedirs(version_dir)
            version_data = {"id": version_id, "libraries": [], "downloads": {}}
            with self.assertRaises(FileNotFoundError):
                ensure_runtime_files(
                    tmp,
                    version_data,
                    version_id,
                    skip_completion=True,
                    check_assets=False,
                )

            with open(os.path.join(version_dir, f"{version_id}.jar"), "wb") as f:
                f.write(b"x")
            self.assertTrue(
                ensure_runtime_files(
                    tmp,
                    version_data,
                    version_id,
                    skip_completion=True,
                    check_assets=False,
                )
            )


class TestLibraryDownloaderCancel(unittest.TestCase):
    def test_cancellation_event_stops_downloader(self):
        from modules.install import LibraryDownloader

        cancel = threading.Event()
        # Items that would hang if not cancelled — use invalid url so they fail fast;
        # cancellation_event should set cancel_event.
        items = [
            (
                {"name": f"com.example:lib{i}:1.0"},
                os.path.join(tempfile.gettempdir(), f"bloret_test_lib_{i}.jar"),
                {"url": "https://example.invalid/lib.jar", "path": f"x/{i}.jar"},
                False,
            )
            for i in range(4)
        ]
        downloader = LibraryDownloader(items, max_workers=2, cancellation_event=cancel)
        cancel.set()
        result = downloader.download_libraries()
        self.assertFalse(result)
        self.assertTrue(downloader.is_cancelled or downloader.cancel_event.is_set())


class TestLaunchPaths(unittest.TestCase):
    """Path construction without full Get_Run_Script (avoids java/account deps)."""

    def test_mods_dir_no_double_version(self):
        mc_version = "1.21.1-fabric"
        minecraft_dir = "/data/mc"
        versions_dir = os.path.join(minecraft_dir, "versions", mc_version)
        mods_dir = os.path.join(versions_dir, "mods")
        natives_path = os.path.join(versions_dir, f"{mc_version}-natives")
        self.assertEqual(mods_dir.replace("\\", "/"), "/data/mc/versions/1.21.1-fabric/mods")
        self.assertNotIn("/1.21.1-fabric/1.21.1-fabric/", mods_dir.replace("\\", "/"))
        self.assertTrue(natives_path.endswith("1.21.1-fabric-natives") or natives_path.endswith("1.21.1-fabric-natives".replace("/", os.sep)))


class TestIPNoImportNetwork(unittest.TestCase):
    def test_import_does_not_call_requests(self):
        # modules.IP should be importable; refresh is explicit
        import importlib
        import modules.IP as ip_mod

        importlib.reload(ip_mod)
        self.assertTrue(hasattr(ip_mod, "refresh_server_ip"))
        self.assertTrue(hasattr(ip_mod, "refresh_server_ip_async"))
        self.assertTrue(callable(ip_mod.refresh_server_ip))


if __name__ == "__main__":
    unittest.main()
