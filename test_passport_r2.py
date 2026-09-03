import os
import stat
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.passport_oauth import PassportOAuthCoordinator


class PassportR2Tests(unittest.TestCase):
    def test_source_has_normal_page_status_cancel_and_legacy_sync_disabled(self):
        page = Path("qml/pages/PassPort.qml").read_text(encoding="utf-8")
        self.assertIn("onPassportLoginStatusChanged", page)
        self.assertIn("重试登录", page)
        self.assertIn("cancelBloretPassPortLogin", page)
        overlay = Path("qml/OOBEOverlay.qml").read_text(encoding="utf-8")
        self.assertIn("onPassportLoginStatusChanged", overlay)
        self.assertIn('category === "started"', overlay)
        self.assertIn("loginError", overlay)
        web = Path("modules/web.py").read_text(encoding="utf-8")
        self.assertIn("Legacy Passport sync disabled", web)
        self.assertNotIn("/app/verify", web)
        self.assertNotIn("/app/MinecraftAccounts", web)
        self.assertNotIn("usertoken", web)
        passport = Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8")
        self.assertNotIn("Bloret_PassPort_PassWord", passport.split("def savedata", 1)[1].split("def process_2fa_request", 1)[0])
        self.assertIn("headers", passport.split("def savedata", 1)[1].split("def process_2fa_request", 1)[0])

    def test_launch_requires_reauthorization_after_refresh_failure(self):
        source = Path("Bloret-Launcher.py").read_text(encoding="utf-8")
        marker = 'refresh_ok = refresh_minecraft_token()'
        start = source.index(marker)
        end = source.index('emit_progress(50', start)
        block = source[start:end]
        self.assertIn('reauthorization_required', block)
        self.assertIn('return', block)
        self.assertNotIn('继续同步档案', block)

    def test_config_write_hardens_posix_mode(self):
        source = Path("modules/config.py").read_text(encoding="utf-8")
        self.assertIn("os.chmod(path, 0o600)", source)
        self.assertIn("os.chmod(config_path + \".back\", 0o600)", source)

    def test_resourcepack_ai_uses_oauth_and_no_static_app_secret(self):
        source = Path("modules/resourcepack_editor/agent_backend.py").read_text(encoding="utf-8")
        self.assertIn("Bloret_PassPort_OAuth", source)
        self.assertNotIn("s4d56f4a", source)

    def test_account_normalization_requires_explicit_list_contract(self):
        source = Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8")
        self.assertIn("def normalize_minecraft_accounts(userinfo):", source)
        self.assertIn('raise ValueError("Passport userinfo omitted Minecraft account data")', source)
        self.assertIn('if "accounts" in userinfo:', source)
        self.assertIn('elif "minecraft_accounts" in userinfo:', source)

    def test_savedata_requires_oauth_for_private_mode(self):
        source = Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8")
        helper = source.split("def _oauth_headers", 1)[1].split("def savedata", 1)[0]
        self.assertIn("access_token", helper)
        self.assertIn("Authorization", helper)
        self.assertIn("PermissionError", helper)

    def test_sync_success_path_is_outside_persistence_failure_branch(self):
        source = Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8")
        sync = source.split("def sync_bloret_passport_account_to_mc", 1)[1].split("def refresh_minecraft_token", 1)[0]
        self.assertLess(sync.index("if not cfg.write(config_data)"), sync.index("parent_window.config"))
        self.assertLess(sync.index("parent_window.config"), sync.index('invoke_hook(\n                "passport.sync"'))

    def test_callback_failure_consumes_transaction(self):
        coordinator = PassportOAuthCoordinator(authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _: True)
        tx = coordinator.begin()
        coordinator.exchange_code = lambda *_: (_ for _ in ()).throw(ValueError("bad token"))
        self.assertFalse(coordinator.handle_callback(tx.redirect_uri + "?code=x&state=" + tx.state))
        self.assertIsNone(coordinator._pending)
        coordinator.cancel()


if __name__ == "__main__":
    unittest.main()
