"""Update artifact integrity and safe ZIP extraction tests."""

from __future__ import annotations

import hashlib
import os
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

from modules import update
from modules.update import resolve_update_artifact, safe_extract_update_zip, verify_update_sha256


def test_verify_sha256():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "update.bin"
        path.write_bytes(b"verified update")
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        assert verify_update_sha256(path, expected)
        try:
            verify_update_sha256(path, "0" * 64)
        except ValueError:
            pass
        else:
            raise AssertionError("mismatched update hash accepted")


def test_resolve_artifact_binds_selected_mirror_hash():
    github_hash = "1" * 64
    gitcode_hash = "2" * 64
    payload = {
        "latestVersion": "2.0",
        "downloads": {
            "stable": {
                "windows": {
                    "github": "https://github.com/example/update.exe",
                    "gitcode": "https://gitcode.com/example/update.exe",
                    "hashes": {"github": github_hash, "gitcode": gitcode_hash},
                }
            }
        },
    }
    with mock.patch("modules.platform_compat.is_windows", return_value=True):
        artifact = resolve_update_artifact(payload)
    assert artifact["url"] == payload["downloads"]["stable"]["windows"]["github"]
    assert artifact["sha256"] == github_hash


def test_resolve_artifact_rejects_unbound_top_level_hash():
    payload = {
        "sha256": "3" * 64,
        "downloads": {
            "stable": {
                "windows": {"github": "https://github.com/example/update.exe"}
            }
        },
    }
    with mock.patch("modules.platform_compat.is_windows", return_value=True):
        artifact = resolve_update_artifact(payload)
    assert artifact["sha256"] == ""


def test_safe_zip_extracts_regular_files():
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "ok.zip"
        destination = Path(tmp) / "out"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("app/file.txt", "ok")
        safe_extract_update_zip(archive, destination)
        assert (destination / "app" / "file.txt").read_text() == "ok"


def test_safe_zip_rejects_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "bad.zip"
        destination = Path(tmp) / "out"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("../escape.txt", "bad")
        try:
            safe_extract_update_zip(archive, destination)
        except ValueError:
            pass
        else:
            raise AssertionError("ZIP traversal was accepted")
        assert not (Path(tmp) / "escape.txt").exists()


def test_zip_apply_restores_backup_if_install_move_fails():
    with tempfile.TemporaryDirectory() as tmp:
        app_dir = Path(tmp) / "app"
        app_dir.mkdir()
        destination = app_dir / "launcher.txt"
        destination.write_text("old", encoding="utf-8")
        archive = Path(tmp) / "update.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("launcher.txt", "new")

        real_replace = os.replace
        calls = 0

        def fail_install(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected install failure")
            return real_replace(source, target)

        with mock.patch.object(update, "get_app_dir", return_value=str(app_dir)):
            with mock.patch.object(update.os, "replace", side_effect=fail_install):
                try:
                    update._apply_zip_update(archive)
                except OSError as error:
                    assert "injected" in str(error)
                else:
                    raise AssertionError("injected update failure was ignored")
        assert destination.read_text(encoding="utf-8") == "old"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("OK", name)
