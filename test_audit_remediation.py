from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class TestAuditRemediation(unittest.TestCase):
    def test_version_path_policy_rejects_unsafe_inputs(self):
        source = (ROOT / "modules" / "services" / "versions_service.py").read_text(encoding="utf-8")
        for fragment in ("Path(mc_dir, \"versions\").resolve()", "candidate.resolve(strict=True)", "candidate.is_symlink()", "relative_to(versions_root)"):
            self.assertIn(fragment, source)
        for bad in ("../outside", "/tmp/outside", "a/b", r"a\..\b"):
            self.assertTrue("/" in bad or "\\" in bad or bad.startswith("."))

    def test_permissions_fail_closed(self):
        source = (ROOT / "modules" / "plugin_host" / "permissions.py").read_text(encoding="utf-8")
        state = (ROOT / "modules" / "plugin_host" / "state.py").read_text(encoding="utf-8")
        self.assertIn("auto_high_risk: bool = False", source)
        self.assertIn("permission in DEFAULT_SAFE_PERMISSIONS and permission in ALL_PERMISSIONS", source)
        self.assertIn("auto_grant: bool = False", state)

    def test_recent_runs_concurrent_writes_are_valid(self):
        from modules.services import recent_runs
        with tempfile.TemporaryDirectory() as tmp:
            threads = [threading.Thread(target=recent_runs.record, args=(tmp, {"name": str(i)})) for i in range(30)]
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            value = json.loads((Path(tmp) / "recent_runs.json").read_text())
            self.assertLessEqual(len(value), 20)

    def test_web_import_has_no_server_start_side_effect(self):
        source = (ROOT / "modules" / "web.py").read_text(encoding="utf-8")
        self.assertNotIn('server_thread.start()', source)
        self.assertIn('def start_server()', source)

    def test_oauth_source_has_no_static_secret_or_http_fallback(self):
        source = (ROOT / "modules" / "web.py").read_text(encoding="utf-8")
        self.assertNotIn("app_secret", source)
        self.assertNotIn('fallback_url = f"http://', source)
        self.assertNotIn("/app/verify", source)
        self.assertIn("Legacy Passport callback disabled", source)
        self.assertIn("/login/Bloret-PassPort", source)
        coordinator = (ROOT / "modules" / "passport_oauth.py").read_text(encoding="utf-8")
        self.assertIn("Passport endpoints must use HTTPS", coordinator)
        self.assertIn("/oauth/authorize", coordinator)
        self.assertIn("/oauth/token", coordinator)
        self.assertIn("/oauth/userinfo", coordinator)

    def test_qml_regressions_are_fixed(self):
        main = (ROOT / "qml" / "main.qml").read_text(encoding="utf-8")
        self.assertIn('id: "passport"', main)
        self.assertIn('item.id === "passport"', main)
        cores = (ROOT / "qml" / "pages" / "Cores.qml").read_text(encoding="utf-8")
        self.assertIn("Backend.renameCustomItem", cores)
        plugin_store = (ROOT / "qml" / "pages" / "PluginStore.qml").read_text(encoding="utf-8")
        self.assertIn("selectedPlugin.permissions || []", plugin_store)
        bbbs = (ROOT / "qml" / "pages" / "BBBS.qml").read_text(encoding="utf-8")
        self.assertIn('text: Backend ? Backend.tr("重试")', bbbs)


if __name__ == "__main__":
    unittest.main()
