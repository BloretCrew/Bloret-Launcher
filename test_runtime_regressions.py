"""Regression tests for launcher runtime reliability fixes."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN_PATH = ROOT / "Bloret-Launcher.py"


def _backend_class() -> ast.ClassDef:
    tree = ast.parse(MAIN_PATH.read_text(encoding="utf-8-sig"))
    return next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Backend"
    )


class TestBackendDeclarations(unittest.TestCase):
    def test_backend_has_no_duplicate_member_names(self):
        backend = _backend_class()
        seen: dict[str, list[int]] = {}
        for node in backend.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                seen.setdefault(node.name, []).append(node.lineno)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        seen.setdefault(target.id, []).append(node.lineno)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                seen.setdefault(node.target.id, []).append(node.lineno)

        duplicates = {name: lines for name, lines in seen.items() if len(lines) > 1}
        self.assertNotIn("downloadManagerOpenRequested", duplicates)
        self.assertNotIn("openDownloadManager", duplicates)

    def test_task_progress_signal_has_task_id(self):
        backend = _backend_class()
        assignment = next(
            node for node in backend.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "downloadTaskProgressUpdated"
                for target in node.targets
            )
        )
        self.assertIsInstance(assignment.value, ast.Call)
        self.assertEqual(len(assignment.value.args), 6)

    def test_download_error_contract_exists(self):
        backend = _backend_class()
        names = {
            target.id
            for node in backend.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        methods = {
            node.name for node in backend.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("downloadErrorOccurred", names)
        self.assertIn("retryDownload", methods)

    def test_update_worker_is_started(self):
        backend = _backend_class()
        method = next(
            node for node in backend.body
            if isinstance(node, ast.FunctionDef) and node.name == "startUpdate"
        )
        calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)]
        self.assertTrue(any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "start"
            and isinstance(call.func.value, ast.Call)
            and isinstance(call.func.value.func, ast.Attribute)
            and call.func.value.func.attr == "Thread"
            for call in calls
        ))


class TestPluginSourceValidation(unittest.TestCase):
    def test_add_plugin_rejects_plain_http_before_network(self):
        from unittest import mock
        from modules import plugin

        with mock.patch.object(plugin.requests.Session, "get") as get:
            self.assertFalse(plugin.addPlugin("http://evil.example/plugin.json", "bad"))
            get.assert_not_called()


class TestAtomicConfigWrite(unittest.TestCase):
    def test_config_write_replaces_complete_json(self):
        import modules.config as cfg
        import modules.globals as globals_module

        old_path = globals_module.config_path
        try:
            with tempfile.TemporaryDirectory() as tmp:
                globals_module.config_path = str(Path(tmp) / "config.json")
                expected = {"ver": "test", "nested": {"enabled": True}, "items": [1, 2, 3]}
                self.assertTrue(cfg.write(expected, fire_hooks=False))
                self.assertEqual(cfg.read(), expected)
                self.assertEqual(list(Path(tmp).glob(".config-*.tmp")), [])
        finally:
            globals_module.config_path = old_path


if __name__ == "__main__":
    unittest.main()
