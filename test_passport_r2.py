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
        backend = Path("Bloret-Launcher.py").read_text(encoding="utf-8")
        sync = backend.split("def syncAccountFromPassPort", 1)[1].split("def getIpv6Address", 1)[0]
        self.assertIn("minecraftAccountSyncFailed.emit", sync)
        self.assertIn("if success:", sync)
        account_sync = backend.split("def syncMinecraftAccount", 1)[1].split("def setPluginStoreApi", 1)[0]
        self.assertIn("if not sync_bloret_passport_account_to_mc(parent_window=None):", account_sync)
        self.assertIn("self.minecraftAccountSyncFailed.emit", account_sync)
        self.assertIn("return", account_sync)
        self.assertIn("except Exception as e:", account_sync)
        overlay = Path("qml/OOBEOverlay.qml").read_text(encoding="utf-8")
        self.assertIn("onPassportLoginStatusChanged", overlay)
        self.assertIn('category === "started"', overlay)
        self.assertIn("loginError", overlay)
        self.assertIn("started", overlay)
        self.assertIn("loginBloretPassPort()", overlay)
        web = Path("modules/web.py").read_text(encoding="utf-8")
        self.assertIn("Legacy Passport sync disabled", web)
        self.assertNotIn("/app/verify", web)
        self.assertNotIn("/app/MinecraftAccounts", web)
        self.assertNotIn("usertoken", web)
        passport = Path("modules/Bloret_PassPort.py").read_text(encoding="utf-8")
        self.assertNotIn("Bloret_PassPort_PassWord", passport.split("def savedata", 1)[1].split("def process_2fa_request", 1)[0])
        self.assertIn("headers", passport.split("def savedata", 1)[1].split("def process_2fa_request", 1)[0])

    def test_oauth_login_persists_avatar_and_accepts_small_avatar_cache(self):
        links = Path("modules/links.py").read_text(encoding="utf-8")
        self.assertIn('"Bloret_PassPort_Avatar": str(userinfo.get("avatar") or "")', links)
        self.assertIn('"bbbs_session": str(userinfo.get("bbbs_session") or "")', links)
        self.assertIn('"bbbs_session_sig": str(userinfo.get("bbbs_session.sig") or "")', links)
        oauth = Path("modules/passport_oauth.py").read_text(encoding="utf-8")
        self.assertIn('"Bloret_PassPort_Avatar": str(userinfo.get("avatar") or "")', oauth)
        self.assertIn('updated["bbbs_session"] = str(userinfo.get("bbbs_session") or "")', oauth)
        self.assertIn('bbbs:session', oauth)
        backend = Path("Bloret-Launcher.py").read_text(encoding="utf-8")
        self.assertIn("os.path.getsize(cache_file) > 100", backend)
        self.assertIn("len(response.content) <= 100", backend)
        self.assertIn('content_type.startswith("image/")', backend)

    def test_logout_is_a_qml_callable_slot(self):
        backend = Path("Bloret-Launcher.py").read_text(encoding="utf-8")
        self.assertIn("@Slot()\n    def logoutBloretPassPort(self):", backend)
        page = Path("qml/pages/PassPort.qml").read_text(encoding="utf-8")
        self.assertIn("Backend.logoutBloretPassPort()", page)
        self.assertIn('category === "logged_out"', page)

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

    def test_single_instance_lock_uses_flock_and_file_presence_is_not_lock_state(self):
        source = Path("Bloret-Launcher.py").read_text(encoding="utf-8")
        lock_impl = source.split("def release_single_instance_lock():", 1)[1].split("def _wait_for_single_instance_after_restart", 1)[0]
        self.assertIn("fcntl.flock(_single_instance_lock_file.fileno(), fcntl.LOCK_UN)", lock_impl)
        self.assertIn("fcntl.flock(_single_instance_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)", lock_impl)
        self.assertNotIn("lockf(", lock_impl)

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

    def test_old_launcher_is_not_packaged_or_active_entrypoint(self):
        spec = Path("Bloret-Launcher.spec").read_text(encoding="utf-8")
        iss = Path("Bloret-Launcher-Setup.iss").read_text(encoding="utf-8")
        self.assertIn("['Bloret-Launcher.py']", spec)
        self.assertNotIn("Bloret-Launcher-Old.py", spec + iss)

    def test_callback_failure_consumes_transaction(self):
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _: True)
        tx = coordinator.begin()
        coordinator.exchange_code = lambda *_: (_ for _ in ()).throw(ValueError("bad token"))
        self.assertFalse(coordinator.handle_callback(tx.redirect_uri + "?code=x&state=" + tx.state))
        self.assertIsNone(coordinator._pending)
        coordinator.cancel()


if __name__ == "__main__":
    unittest.main()
