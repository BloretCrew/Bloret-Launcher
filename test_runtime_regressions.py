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
        self.assertNotIn("setLanguage", duplicates)

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

    def test_gui_blocking_operations_have_async_slots(self):
        backend = _backend_class()
        methods = {
            node.name for node in backend.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("refreshPassPortAvatarAsync", methods)
        self.assertIn("scanSystemJavasAsync", methods)

    def test_avatar_getter_has_no_network_calls(self):
        backend = _backend_class()
        method = next(
            node for node in backend.body
            if isinstance(node, ast.FunctionDef) and node.name == "getPassPortAvatar"
        )
        self.assertFalse(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "requests"
            for node in ast.walk(method)
        ))

    def test_home_remote_refresh_is_throttled(self):
        """#129: sidebar page recreate must not re-hit servers every time."""
        source = MAIN_PATH.read_text(encoding="utf-8-sig")
        self.assertIn("_HOME_REMOTE_TTL_SEC", source)
        self.assertIn("_activity_refresh_inflight", source)
        self.assertIn("_server_refresh_inflight", source)
        self.assertIn("_launch_items_cache", source)
        self.assertIn("invalidateLaunchItemsCache", source)

        backend = _backend_class()
        methods = {
            node.name for node in backend.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("refreshActivityInfo", methods)
        self.assertIn("refreshServerInfo", methods)
        self.assertIn("invalidateLaunchItems", methods)
        self.assertIn("getLaunchItems", methods)

        home_qml = (ROOT / "qml" / "pages" / "Home.qml").read_text(encoding="utf-8")
        # Remote refresh must be deferred, not run synchronously in onCompleted alone.
        self.assertIn("Qt.callLater", home_qml)
        self.assertIn("refreshActivityInfo", home_qml)
        self.assertIn("refreshServerInfo", home_qml)

    def test_info_and_server_requests_use_timeout(self):
        blserver = (ROOT / "modules" / "BLServer.py").read_text(encoding="utf-8")
        chafu = (ROOT / "modules" / "chafuwang.py").read_text(encoding="utf-8")
        update = (ROOT / "modules" / "update.py").read_text(encoding="utf-8")
        self.assertRegex(blserver, r"api/info[^\n]*timeout")
        self.assertRegex(chafu, r"requests\.get\([^\n]*timeout")
        self.assertRegex(update, r"api/info[^\n]*timeout")

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


class TestResourcePackAgentLanguage(unittest.TestCase):
    def test_agent_prompt_uses_configured_language(self):
        from unittest import mock
        from modules.resourcepack_editor import agent_loop

        with mock.patch.object(agent_loop.cfg, "read", return_value={"language": "en-GB"}):
            self.assertIn("British English", agent_loop._resolve_language_instruction())
            with tempfile.TemporaryDirectory() as tmp:
                agent = agent_loop.AgentLoop(tmp, "https://example.invalid", "")
                prompt = agent._build_system_prompt()
                self.assertIn("FINAL RESPONSE LANGUAGE (HIGHEST PRIORITY)", prompt)
                self.assertIn("Do not answer in Chinese", prompt)
                with mock.patch.object(agent_loop.cfg, "read", return_value={"language": "en-GB"}):
                    system_messages = []
                    original_build = agent._build_system_prompt
                    agent._build_system_prompt = original_build
                    directive = agent_loop._resolve_language_instruction() + " Reply only in that language."
                    system_messages.append(directive)
                    self.assertIn("British English", system_messages[-1])

    def test_agent_prompt_does_not_hardcode_chinese_reply_rule(self):
        from modules.resourcepack_editor.knowledge_base import AGENT_SYSTEM_PROMPT_TEMPLATE

        prompt = AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            pack_path="/tmp/pack",
            dynamic_context="",
            language_requirement="Use English for all human-readable replies.",
        )
        self.assertIn("Use English", prompt)
        self.assertNotIn("回复使用中文", prompt)


class TestBlorikoAgentLanguage(unittest.TestCase):
    def test_bloriko_uses_configured_language(self):
        from unittest import mock
        from modules.bloriko_agent import agent_loop

        with mock.patch.object(agent_loop.cfg, "read", return_value={"language": "en-GB"}):
            instruction = agent_loop._resolve_language_instruction()
            self.assertIn("British English", instruction)
            self.assertIn("Reply only in that language", instruction)

    def test_bloriko_loop_keeps_final_language_message(self):
        source = (ROOT / "modules" / "bloriko_agent" / "agent_loop.py").read_text(encoding="utf-8")
        self.assertIn('\"role\": \"system\", \"content\": language_directive', source)
        self.assertIn("FINAL RESPONSE LANGUAGE (HIGHEST PRIORITY)", source)


class TestPluginSourceValidation(unittest.TestCase):
    def test_add_plugin_rejects_plain_http_before_network(self):
        from unittest import mock
        from modules import plugin

        with mock.patch.object(plugin.requests.Session, "get") as get:
            self.assertFalse(plugin.addPlugin("http://evil.example/plugin.json", "bad"))
            get.assert_not_called()


class TestDownloadTaskCleanup(unittest.TestCase):
    def test_finished_task_history_is_bounded(self):
        from modules.download_manager import DownloadManager, DownloadTask

        manager = DownloadManager()
        manager._initialized = False
        manager._init()
        manager.tasks.clear()
        import time
        now = time.monotonic()
        for index in range(manager.MAX_FINISHED_TASKS + 5):
            task = DownloadTask(str(index), "1.21", f"test-{index}", "vanilla", object())
            task.status = "completed"
            task.finished_at = now + (index / 1000.0)
            task.thread = object()
            manager.tasks[task.task_id] = task
        manager._prune_finished_tasks()
        self.assertEqual(len(manager.tasks), manager.MAX_FINISHED_TASKS)


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
