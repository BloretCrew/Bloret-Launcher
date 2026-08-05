"""Smoke tests for official-compatible mrpack export/import."""

from __future__ import annotations

import json
import sys
import tempfile
import types
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

# Headless CI / servers may lack PySide6; stub enough for modules.log import chain.
if "PySide6" not in sys.modules:
    for name in (
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
    ):
        sys.modules[name] = MagicMock()

import modules.mrpack_export as export_mod
import modules.mrpack_import as import_mod


def _make_fake_instance(root: Path) -> Path:
    inst = root / "versions" / "TestPack"
    (inst / "mods").mkdir(parents=True)
    (inst / "config").mkdir(parents=True)
    # tiny fake jar
    mod = inst / "mods" / "local-mod.jar"
    mod.write_bytes(b"PK\x03\x04fake-mod-content-for-hash")
    cfg = inst / "config" / "demo.toml"
    cfg.write_text("enabled = true\n", encoding="utf-8")
    # minimal version json
    (inst / "TestPack.json").write_text(
        json.dumps(
            {
                "id": "1.20.1",
                "inheritsFrom": "1.20.1",
                "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
                "libraries": [
                    {"name": "net.fabricmc:fabric-loader:0.15.11"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return inst


def test_export_uses_overrides_not_files_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inst = _make_fake_instance(root)
        out = root / "out.mrpack"
        ok = export_mod.export_to_mrpack(
            str(inst),
            str(out),
            name="Test Pack",
            version="1.0.0",
            summary="unit",
            resolve_cdn=False,  # force all into overrides
        )
        assert ok, "export should succeed"
        assert out.is_file()
        with zipfile.ZipFile(out, "r") as zf:
            names = [n.replace("\\", "/") for n in zf.namelist()]
            assert "modrinth.index.json" in names
            assert any(n.startswith("overrides/") for n in names), names
            assert not any(
                n == "files" or n.startswith("files/") for n in names
            ), f"legacy files/ must not appear: {names}"
            index = json.loads(zf.read("modrinth.index.json"))
            assert index["game"] == "minecraft"
            assert index["formatVersion"] == 1
            assert "minecraft" in index["dependencies"]
            # with resolve_cdn=False everything is override-only
            assert index["files"] == []
            assert any(n.endswith("mods/local-mod.jar") for n in names)
            assert any(n.endswith("config/demo.toml") for n in names)


def test_import_reads_index_and_extracts_overrides():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inst = _make_fake_instance(root)
        pack = root / "pack.mrpack"
        assert export_mod.export_to_mrpack(
            str(inst), str(pack), "Demo", "1.0.0", resolve_cdn=False
        )
        dest_root = root / "import_mc"
        result = import_mod.import_mrpack(
            str(pack),
            minecraft_dir=str(dest_root),
            instance_name="ImportedDemo",
            install_game=False,
        )
        assert result["ok"], result
        dest = Path(result["instance_path"])
        assert (dest / "mods" / "local-mod.jar").is_file()
        assert (dest / "config" / "demo.toml").is_file()
        assert (dest / "bloret-mrpack-meta.json").is_file()


def test_parse_dependencies():
    mc, loader, ver = import_mod.parse_dependencies(
        {"minecraft": "1.20.1", "fabric-loader": "0.15.11"}
    )
    assert mc == "1.20.1"
    assert loader == "fabric"
    assert ver == "0.15.11"


def test_legacy_files_prefix_still_extracts():
    """旧 Bloret 错误格式 files/ 仍应能解压。"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pack = root / "legacy.mrpack"
        index = {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "1.0.0",
            "name": "Legacy",
            "files": [],
            "dependencies": {"minecraft": "1.20.1"},
        }
        with zipfile.ZipFile(pack, "w") as zf:
            zf.writestr("modrinth.index.json", json.dumps(index))
            zf.writestr("files/config/old.txt", b"legacy-override")
        dest = root / "mc" / "versions" / "L"
        dest.mkdir(parents=True)
        n = import_mod.extract_overrides(str(pack), dest)
        assert n >= 1
        assert (dest / "config" / "old.txt").read_text() == "legacy-override"


if __name__ == "__main__":
    test_export_uses_overrides_not_files_dir()
    test_import_reads_index_and_extracts_overrides()
    test_parse_dependencies()
    test_legacy_files_prefix_still_extracts()
    print("all mrpack smoke tests passed")
