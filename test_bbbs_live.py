from __future__ import annotations

import threading
import time
import unittest
from unittest import mock

from modules import bbbs, bbbs_live


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", lines=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = {"Content-Type": "text/event-stream"}
        self.encoding = None
        self.closed = False
        self._lines = list(lines or [])

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def iter_lines(self, decode_unicode=False):
        yield from self._lines

    def close(self):
        self.closed = True


class BBBSLiveTests(unittest.TestCase):
    def test_request_log_redacts_session_cookies_and_keeps_other_fields(self):
        messages = []
        cookies = {
            "session": "secret-session",
            "session.sig": "secret-signature",
            "theme": "dark",
        }
        with mock.patch.object(bbbs_live, "log", side_effect=lambda message, *args: messages.append(message)):
            bbbs_live._log_request("POST", "https://example.test/live", cookies, {"type": "chat"})
        output = "\n".join(messages)
        self.assertNotIn("secret-session", output)
        self.assertNotIn("secret-signature", output)
        self.assertIn("<redacted>", output)
        self.assertIn("dark", output)
        self.assertIn('"type": "chat"', output)

    def test_response_log_redacts_sensitive_headers_and_truncates_body(self):
        messages = []
        response = FakeResponse(text="x" * 800)
        response.headers["Set-Cookie"] = "session=secret-session"
        with mock.patch.object(bbbs_live, "log", side_effect=lambda message, *args: messages.append(message)):
            bbbs_live._log_response(response)
        output = "\n".join(messages)
        self.assertNotIn("secret-session", output)
        self.assertIn("<redacted>", output)
        body_line = next(message for message in messages if "Body:" in message)
        self.assertLessEqual(len(body_line.split("Body: ", 1)[1]), bbbs_live._LOG_BODY_LIMIT)

    def test_sse_parses_multiline_crlf_keepalive_and_continues_after_bad_json(self):
        events = []
        client = bbbs_live.LiveSSEClient("space-1", events.append)
        response = FakeResponse(lines=[
            ": keep-alive\r",
            "event: chat\r",
            'data: {"payload":\r',
            'data: {"msg": "hello"}}\r',
            "\r",
            "data: not-json\r",
            "\r",
            "event: user-joined\r",
            'data: {"from": "alice"}\r',
        ])

        client._consume_response(response)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["type"], "chat")
        self.assertEqual(events[0]["payload"]["msg"], "hello")
        self.assertEqual(events[1], {"from": "alice", "type": "user-joined"})

    def test_stop_interrupts_reconnect_wait(self):
        attempted = threading.Event()

        def fail_request(*args, **kwargs):
            attempted.set()
            raise bbbs_live.requests.exceptions.ConnectionError("offline")

        client = bbbs_live.LiveSSEClient("space-1", lambda event: None)
        with mock.patch.object(bbbs_live.requests, "get", side_effect=fail_request):
            client.start()
            self.assertTrue(attempted.wait(1))
            started = time.monotonic()
            stopped = client.stop(timeout=1)
        self.assertTrue(stopped)
        self.assertLess(time.monotonic() - started, 0.5)

    def test_start_is_idempotent_while_thread_is_running(self):
        release = threading.Event()
        calls = []

        def blocking_request(*args, **kwargs):
            calls.append(1)
            release.wait(1)
            raise bbbs_live.requests.exceptions.ConnectionError("offline")

        client = bbbs_live.LiveSSEClient("space-1", lambda event: None)
        with mock.patch.object(bbbs_live.requests, "get", side_effect=blocking_request):
            client.start()
            client.start()
            time.sleep(0.05)
            release.set()
            client.stop(timeout=1)
        self.assertEqual(len(calls), 1)

    def test_bbbs_non_json_and_error_status_return_safe_defaults(self):
        with mock.patch.object(bbbs, "_get_session_cookie", return_value={}):
            with mock.patch.object(
                bbbs.requests,
                "get",
                return_value=FakeResponse(payload=ValueError("bad json")),
            ):
                self.assertIsNone(bbbs.fetch_summary())
                self.assertEqual(bbbs.fetch_all_posts(), [])
            with mock.patch.object(
                bbbs.requests,
                "get",
                return_value=FakeResponse(status_code=503, payload={"error": "down"}),
            ):
                self.assertEqual(bbbs.fetch_leaderboard_posts(), [])

    def test_bbbs_rejects_unexpected_json_shapes(self):
        with mock.patch.object(bbbs, "_get_session_cookie", return_value={}), mock.patch.object(
            bbbs.requests,
            "get",
            return_value=FakeResponse(payload={"posts": []}),
        ):
            self.assertEqual(bbbs.fetch_all_posts(), [])

    def test_live_space_list_rejects_invalid_json_shape(self):
        with mock.patch.object(bbbs_live, "_get_session_cookie", return_value={}), mock.patch.object(
            bbbs_live.requests,
            "get",
            return_value=FakeResponse(payload={"spaces": []}),
        ):
            self.assertEqual(bbbs_live.fetch_space_list(), [])

    def test_chat_message_validation(self):
        self.assertFalse(bbbs_live.validate_chat_message(None, "hello")[0])
        self.assertFalse(bbbs_live.validate_chat_message("space-1", "   ")[0])
        self.assertFalse(bbbs_live.validate_chat_message("space-1", "x" * 2001)[0])
        self.assertEqual(
            bbbs_live.validate_chat_message("space-1", "  hello  "),
            (True, "", "hello"),
        )


if __name__ == "__main__":
    unittest.main()
