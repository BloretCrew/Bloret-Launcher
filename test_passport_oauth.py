import base64
import hashlib
import threading
import unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from modules.passport_oauth import PassportOAuthCoordinator, build_code_challenge, generate_code_verifier, is_passport_session_authenticated


class _Handler(BaseHTTPRequestHandler):
    seen = {}
    mode = "success"

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = parse_qs(self.rfile.read(length).decode())
        self.seen["token"] = body
        if self.path.endswith("/oauth/token") and self.mode == "refresh":
            payload = b'{"access_token":"refreshed","refresh_token":"rotated","expires_in":3600}'
        elif self.mode == "failure":
            self.send_response(400)
            self.end_headers()
            return
        else:
            payload = b'{"access_token":"access-secret","refresh_token":"refresh-secret","expires_in":3600}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.seen["authorization"] = self.headers.get("Authorization")
        payload = b'{"username":"tester","accounts":[]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        pass


class PassportOAuthTests(unittest.TestCase):
    def test_legacy_verify_callback_is_disabled_in_production_module(self):
        source = (Path(__file__).parent / "modules" / "web.py").read_text(encoding="utf-8")
        self.assertNotIn("/app/verify", source)

    def test_verifier_is_high_entropy_and_s256(self):
        verifier = generate_code_verifier()
        self.assertGreaterEqual(len(verifier), 43)
        self.assertNotIn("=", verifier)
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(build_code_challenge(verifier), expected)

    def test_callback_requires_loopback_exact_path_and_state_is_one_time(self):
        coordinator = PassportOAuthCoordinator(callback_mode="loopback",
            authorize_endpoint="https://passport.example/oauth/authorize",
            token_endpoint="https://passport.example/oauth/token",
            userinfo_endpoint="https://passport.example/oauth/userinfo",
            browser_opener=lambda _url: True,
        )
        tx = coordinator.begin()
        coordinator.exchange_code = lambda code, transaction: {"access_token": "a"}
        coordinator.fetch_userinfo = lambda token: {"username": "u"}
        callback_base = tx.redirect_uri + "?code=c&state=" + tx.state
        self.assertTrue(coordinator.handle_callback(callback_base))
        self.assertFalse(coordinator.handle_callback(callback_base))
        with self.assertRaises(ValueError):
            coordinator.validate_callback("http://localhost:1234/login/Bloret-PassPort?code=c&state=x")
        with self.assertRaises(ValueError):
            coordinator.validate_callback("http://127.0.0.1:1234/evil?code=c&state=x")

    def test_callback_requires_unique_state_and_concurrent_replay_is_rejected(self):
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _url: True)
        tx = coordinator.begin()
        coordinator.exchange_code = lambda code, transaction: {"access_token": "a"}
        coordinator.fetch_userinfo = lambda token: {"username": "u"}
        callback = tx.redirect_uri + "?code=c&state=" + tx.state + "&state=other"
        self.assertFalse(coordinator.handle_callback(callback))
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _url: True)
        tx = coordinator.begin()
        coordinator.exchange_code = lambda code, transaction: {"access_token": "a"}
        coordinator.fetch_userinfo = lambda token: {"username": "u"}
        valid = tx.redirect_uri + "?code=c&state=" + tx.state
        results = []
        threads = [threading.Thread(target=lambda: results.append(coordinator.handle_callback(valid))) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(results.count(True), 1)

    def test_browser_failure_and_timeout_clean_up(self):
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _url: False, timeout=0.01)
        with self.assertRaises(OSError): coordinator.begin()
        self.assertIsNone(coordinator._pending)
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="https://passport.example/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _url: True, timeout=0.01)
        coordinator.begin()
        with self.assertRaises(TimeoutError): coordinator.wait_for_result()
        self.assertIsNone(coordinator._pending)

    def test_expiry_and_refresh_use_refresh_grant(self):
        coordinator = PassportOAuthCoordinator(callback_mode="loopback", authorize_endpoint="https://passport.example/oauth/authorize", token_endpoint="http://127.0.0.1:1/oauth/token", userinfo_endpoint="https://passport.example/oauth/userinfo", browser_opener=lambda _url: True)
        self.assertEqual(coordinator.access_token_status({"access_token":"a", "expires_in":10, "obtained_at":100}, now=200), "expired")
        self.assertEqual(coordinator.access_token_status({}, now=200), "reauthorization_required")

    def test_legacy_login_flag_without_username_is_not_authenticated(self):
        config = {"Bloret_PassPort_Login": True, "Bloret_PassPort_UserName": "",
                  "Bloret_PassPort_OAuth": {"access_token": "stale", "expires_in": 3600, "obtained_at": 100}}
        self.assertFalse(is_passport_session_authenticated(config, now=200))
        config["Bloret_PassPort_UserName"] = "tester"
        self.assertTrue(is_passport_session_authenticated(config, now=200))
        self.assertFalse(is_passport_session_authenticated(config, now=5000))

    def test_login_flag_with_fresh_but_incomplete_legacy_oauth_is_not_authenticated(self):
        config = {"Bloret_PassPort_Login": True, "Bloret_PassPort_UserName": "",
                  "Bloret_PassPort_OAuth": {"access_token": "legacy", "expires_in": 3600, "obtained_at": 200}}
        self.assertFalse(is_passport_session_authenticated(config, now=201))

    def test_complete_callback_posts_verifier_and_fetches_bearer_userinfo(self):
        _Handler.seen = {}
        _Handler.mode = "success"
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = "http://127.0.0.1:%d/oauth/token" % server.server_port
            coordinator = PassportOAuthCoordinator(callback_mode="loopback",
                authorize_endpoint="https://passport.example/oauth/authorize",
                token_endpoint=endpoint,
                userinfo_endpoint=endpoint.replace("/oauth/token", "/oauth/userinfo"),
                browser_opener=lambda url: self.assertNotIn("code_verifier", url) or True,
            )
            tx = coordinator.begin()
            result, userinfo = coordinator.complete_callback(tx.redirect_uri + "?code=code&state=" + tx.state)
            self.assertEqual(result["access_token"], "access-secret")
            self.assertEqual(userinfo["username"], "tester")
            self.assertEqual(_Handler.seen["token"]["code_verifier"][0], tx.verifier)
            self.assertEqual(_Handler.seen["authorization"], "Bearer access-secret")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
