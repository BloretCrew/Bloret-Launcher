import threading
import time
import importlib.util
import sys
import types
import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from modules.passport_oauth import (
    PassportOAuthCoordinator, PROTOCOL_CALLBACK_URI, dispatch_passport_callback,
)


class PassportProtocolTests(unittest.TestCase):
    def setUp(self):
        self.opened = []
        self.coordinator = PassportOAuthCoordinator(
            browser_opener=lambda url: self.opened.append(url) or True,
        )
        self.addCleanup(self.coordinator.cancel)

    def test_browser_authorization_uses_protocol_and_does_not_bind_http(self):
        with patch('modules.passport_oauth.http.server.ThreadingHTTPServer') as server:
            tx = self.coordinator.begin()
        server.assert_not_called()
        self.assertEqual(tx.redirect_uri, PROTOCOL_CALLBACK_URI)
        query = parse_qs(urlparse(self.opened[0]).query)
        self.assertEqual(query['redirect_uri'], [PROTOCOL_CALLBACK_URI])
        self.assertEqual(query['code_challenge_method'], ['S256'])
        self.assertNotIn('code_verifier', query)
        self.assertEqual(query['scope'], ['user:name user:head minecraft:accounts bbbs:session'])

    def test_protocol_dispatch_completes_original_login_and_rejects_replay(self):
        done = threading.Event()
        self.coordinator.on_complete = lambda *_: done.set()
        tx = self.coordinator.begin()
        self.coordinator.exchange_code = lambda code, transaction: {'access_token': 'token'}
        self.coordinator.fetch_userinfo = lambda token: {'username': 'tester'}
        url = tx.redirect_uri + '?code=one-time-code&state=' + tx.state
        self.assertTrue(dispatch_passport_callback(url))
        self.assertTrue(done.wait(2))
        self.assertFalse(self.coordinator.handle_callback(url))

    def test_windows_source_protocol_command_includes_script(self):
        from modules.protocol_handler import _windows_protocol_command
        import os

        script = os.path.abspath('Bloret-Launcher.py')
        cmd = _windows_protocol_command('python.exe', 'Bloret-Launcher.py', is_frozen=False)
        self.assertEqual(cmd, f'"python.exe" "{script}" "%1"')
        self.assertEqual(
            _windows_protocol_command('Bloret-Launcher.exe', 'Bloret-Launcher.exe', is_frozen=True),
            '"Bloret-Launcher.exe" "%1"',
        )

    def test_callback_accepts_trailing_slash_added_by_browser(self):
        tx = self.coordinator.begin()
        self.coordinator.exchange_code = lambda code, transaction: {'access_token': 'token'}
        self.coordinator.fetch_userinfo = lambda token: {'username': 'tester'}
        self.assertTrue(self.coordinator.handle_callback(
            PROTOCOL_CALLBACK_URI + '/?code=one-time-code&state=' + tx.state))

    def test_invalid_callback_does_not_cancel_pending_login(self):
        tx = self.coordinator.begin()
        for url in (
            tx.redirect_uri + '?code=c&state=wrong',
            tx.redirect_uri + '/evil?code=c&state=' + tx.state,
            tx.redirect_uri + '?code=c&state=' + tx.state + '#fragment',
            tx.redirect_uri + '?code=c&state=' + tx.state + '&state=duplicate',
            'http://127.0.0.1:25252/login/Bloret-PassPort?code=c&state=' + tx.state,
        ):
            self.assertFalse(self.coordinator.handle_callback(url))
            self.assertIs(self.coordinator._pending, tx)

    def test_denial_consumes_login(self):
        tx = self.coordinator.begin()
        statuses = []
        self.coordinator.on_status = lambda category, detail: statuses.append((category, detail))
        self.assertFalse(self.coordinator.handle_callback(
            tx.redirect_uri + '?error=access_denied&error_description=Consent+was+not+granted&state=' + tx.state))
        self.assertIsNone(self.coordinator._pending)
        self.assertIn('access_denied', statuses[-1][1])
        self.assertIn('Consent was not granted', statuses[-1][1])

    def test_authorization_error_description_is_sanitized(self):
        tx = self.coordinator.begin()
        statuses = []
        self.coordinator.on_status = lambda category, detail: statuses.append((category, detail))
        url = (tx.redirect_uri + '?error=invalid_request&error_description=' +
               'bad%0Astate%3Dsecret&state=' + tx.state)
        self.assertFalse(self.coordinator.handle_callback(url))
        self.assertIn('invalid_request', statuses[-1][1])
        self.assertNotIn('\n', statuses[-1][1])
        self.assertNotIn('state=secret', statuses[-1][1])

    def test_reserved_callback_without_pending_login_and_unrelated_route(self):
        self.assertTrue(dispatch_passport_callback(PROTOCOL_CALLBACK_URI + '?code=unsolicited'))
        self.assertFalse(dispatch_passport_callback('bloret://plugin/install?download=x'))

    def test_cannot_replace_pending_protocol_login(self):
        self.coordinator.begin()
        other = PassportOAuthCoordinator(browser_opener=lambda _: True)
        self.addCleanup(other.cancel)
        with self.assertRaises(RuntimeError):
            other.begin()

    def test_expired_login_can_be_replaced_and_old_state_is_rejected(self):
        tx = self.coordinator.begin()
        tx.created_at = time.monotonic() - self.coordinator.timeout - 1
        other = PassportOAuthCoordinator(browser_opener=lambda _: True)
        self.addCleanup(other.cancel)
        other.begin()
        self.assertIsNone(self.coordinator._pending)
        self.assertFalse(other.handle_callback(tx.redirect_uri + '?code=c&state=' + tx.state))
        self.assertIsNotNone(other._pending)

    def test_protocol_route_bypasses_plugins_and_redacts_logs(self):
        spec = importlib.util.spec_from_file_location('protocol_under_test', 'modules/protocol_handler.py')
        protocol = importlib.util.module_from_spec(spec)
        log_stub = types.ModuleType('modules.log')
        messages = []
        log_stub.log = messages.append
        with patch.dict(sys.modules, {'modules.log': log_stub}):
            spec.loader.exec_module(protocol)
        received = []
        protocol.set_deep_link_handler(received.append)
        url = PROTOCOL_CALLBACK_URI + '?code=secret-code&state=secret-state'
        protocol._dispatch_url(url)
        self.assertEqual(received, [url])
        self.assertNotIn('secret-code', str(messages))
        self.assertNotIn('secret-state', str(messages))


if __name__ == '__main__':
    unittest.main()
