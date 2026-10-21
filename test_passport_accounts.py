"""Exercise account synchronization without importing the desktop application."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class PassportAccountSyncTests(unittest.TestCase):
    def setUp(self):
        source = ast.parse(Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8"))
        functions = [node for node in source.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"normalize_minecraft_accounts", "sync_bloret_passport_account_to_mc"}]
        self.config = {
            "Bloret_PassPort_Login": True,
            "Bloret_PassPort_UserName": "tester",
            "Bloret_PassPort_OAuth": {"access_token": "test-token"},
            "MinecraftAccount": {"logined": True, "chosen": 0,
                                 "accounts": [{"username": "cached"}]},
        }
        self.cfg = SimpleNamespace(read=lambda: copy.deepcopy(self.config), write=Mock(return_value=True))
        self.requests = SimpleNamespace(get=Mock())
        self.env = {"cfg": self.cfg, "requests": self.requests, "log": Mock(),
                    "handle_exception": Mock()}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "account_sync", "exec"), self.env)

    def sync(self, payload):
        self.requests.get.return_value = SimpleNamespace(
            status_code=200, raise_for_status=Mock(), json=lambda: payload)
        with patch("modules.passport_oauth.PassportOAuthCoordinator") as coordinator:
            coordinator.return_value.access_token_status.return_value = "valid"
            with patch.dict("sys.modules", {"modules.plugin_host.dispatch": SimpleNamespace(invoke_hook=Mock())}):
                return self.env["sync_bloret_passport_account_to_mc"]()

    def test_missing_account_data_preserves_cached_accounts(self):
        self.assertFalse(self.sync({"username": "tester"}))
        self.cfg.write.assert_not_called()

    def test_invalid_account_data_preserves_cached_accounts(self):
        for accounts in (None, {}, ["invalid"]):
            with self.subTest(accounts=accounts):
                self.assertFalse(self.sync({"accounts": accounts}))
                self.cfg.write.assert_not_called()

    def test_explicit_empty_list_clears_accounts(self):
        self.assertTrue(self.sync({"accounts": []}))
        self.assertEqual(self.cfg.write.call_args.args[0]["MinecraftAccount"],
                         {"logined": False, "chosen": -1, "accounts": []})

    def test_accounts_are_saved_and_selection_preserved(self):
        accounts = [{"username": "first"}, {"username": "second"}]
        self.config["MinecraftAccount"]["chosen"] = 1
        self.assertTrue(self.sync({"minecraft_accounts": accounts}))
        self.assertEqual(self.cfg.write.call_args.args[0]["MinecraftAccount"],
                         {"logined": True, "chosen": 1, "accounts": accounts})

    def test_persistence_failure_is_not_success(self):
        self.cfg.write.return_value = False
        self.assertFalse(self.sync({"accounts": [{"username": "new"}]}))


if __name__ == "__main__":
    unittest.main()
