import base64
import hashlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from modules.passport_oauth import PassportOAuthCoordinator, build_code_challenge, generate_code_verifier


class _Handler(BaseHTTPRequestHandler):
    seen = {}

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = parse_qs(self.rfile.read(length).decode())
        self.seen["token"] = body
        payload = b'{"access_token":"access-secret","refresh_token":"refresh-secret","expires_in":3600}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        pass


class PassportOAuthTests(unittest.TestCase):
    def test_verifier_is_high_entropy_and_s256(self):
        verifier = generate_code_verifier()
        self.assertGreaterEqual(len(verifier), 43)
        self.assertNotIn("=", verifier)
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(build_code_challenge(verifier), expected)

    def test_callback_requires_loopback_exact_path_and_state_is_one_time(self):
        coordinator = PassportOAuthCoordinator(
            authorize_endpoint="https://passport.example/oauth/authorize",
            token_endpoint="https://passport.example/oauth/token",
            userinfo_endpoint="https://passport.example/oauth/userinfo",
            browser_opener=lambda _url: True,
        )
        tx = coordinator.begin()
        callback_base = tx.redirect_uri + "?code=c&state=" + tx.state
        self.assertTrue(coordinator.handle_callback(callback_base))
        self.assertFalse(coordinator.handle_callback(callback_base))
        with self.assertRaises(ValueError):
            coordinator.validate_callback("http://localhost:1234/login/Bloret-PassPort?code=c&state=x")
        with self.assertRaises(ValueError):
            coordinator.validate_callback("http://127.0.0.1:1234/evil?code=c&state=x")

    def test_token_exchange_posts_verifier_and_never_puts_it_in_url(self):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = "http://127.0.0.1:%d/oauth/token" % server.server_port
            coordinator = PassportOAuthCoordinator(
                authorize_endpoint="https://passport.example/oauth/authorize",
                token_endpoint=endpoint,
                userinfo_endpoint="https://passport.example/oauth/userinfo",
                browser_opener=lambda url: self.assertNotIn("code_verifier", url) or True,
            )
            tx = coordinator.begin()
            result = coordinator.exchange_code("code", tx)
            self.assertEqual(result["access_token"], "access-secret")
            self.assertEqual(_Handler.seen["token"]["code_verifier"][0], tx.verifier)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
