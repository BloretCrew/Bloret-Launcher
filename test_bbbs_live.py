from __future__ import annotations

import threading
import time
import unittest
from unittest import mock

from modules import bbbs, bbbs_live
from modules.services.live_chat import LiveChatHistory, normalize_chat_event


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

    def test_local_echo_and_sse_with_same_message_id_are_deduplicated(self):
        history = LiveChatHistory()
        local = {"type": "chat", "from": "alice", "payload": {"msg": "hello", "msgId": "msg-1"}}
        sse = {"type": "chat", "from": "alice", "msgId": "msg-1", "payload": {"message": "hello"}}

        self.assertTrue(history.append(local)[0])
        self.assertFalse(history.append(sse)[0])
        self.assertEqual(len(history.snapshot()), 1)

    def test_same_text_with_different_message_ids_is_preserved(self):
        history = LiveChatHistory()
        self.assertTrue(history.append({"from": "alice", "msg": "hello", "msgId": "msg-1"})[0])
        self.assertTrue(history.append({"from": "alice", "msg": "hello", "msgId": "msg-2"})[0])
        self.assertEqual(len(history.snapshot()), 2)

    def test_duplicate_message_ids_in_initial_history_are_trimmed(self):
        history = LiveChatHistory()
        normalized = history.reconcile_initial([
            {"from": "alice", "msg": "first", "msgId": "msg-1"},
            {"from": "alice", "msg": "duplicate", "msgId": "msg-1"},
            {"from": "bob", "message": "second", "msgId": "msg-2"},
        ])

        self.assertEqual(len(normalized), 2)
        self.assertEqual([item["payload"]["msg"] for item in normalized], ["first", "second"])

    def test_messages_without_ids_are_not_deduplicated_by_text(self):
        history = LiveChatHistory()
        self.assertTrue(history.append({"from": "alice", "msg": "same"})[0])
        self.assertTrue(history.append({"from": "alice", "msg": "same"})[0])
        self.assertEqual(len(history.snapshot()), 2)

    def test_initial_history_reconciles_pending_local_echo(self):
        history = LiveChatHistory()
        history.append({"from": "alice", "payload": {"msg": "local", "msgId": "msg-local"}})
        normalized = history.reconcile_initial([
            {"from": "bob", "msg": "older", "msgId": "msg-old"},
            {"from": "alice", "msg": "local", "msgId": "msg-local"},
        ])

        self.assertEqual([item["payload"]["msgId"] for item in normalized], ["msg-old", "msg-local"])

    def test_repeated_initial_history_without_ids_does_not_accumulate(self):
        history = LiveChatHistory()
        initial = [
            {"from": "alice", "msg": "same"},
            {"from": "alice", "msg": "same"},
        ]

        self.assertEqual(len(history.reconcile_initial(initial)), 2)
        self.assertEqual(len(history.reconcile_initial(initial)), 2)

    def test_same_message_id_can_update_recalled_and_time_fields(self):
        history = LiveChatHistory()
        history.append({"from": "alice", "msg": "hello", "msgId": "msg-1", "recalled": False})
        changed, updated = history.append({"from": "alice", "msgId": "msg-1", "recalled": True, "time": 123})

        self.assertTrue(changed)
        self.assertTrue(updated["payload"]["recalled"])
        self.assertEqual(updated["payload"]["time"], 123)
        self.assertEqual(updated["payload"]["msg"], "hello")
        self.assertEqual(len(history.snapshot()), 1)

    def test_identical_same_id_echo_is_not_reported_as_an_update(self):
        history = LiveChatHistory()
        event = {"from": "alice", "msg": "hello", "msgId": "msg-1"}
        self.assertTrue(history.append(event)[0])
        self.assertFalse(history.append(event)[0])

    def test_normalization_supports_compatible_chat_fields(self):
        normalized = normalize_chat_event({
            "from": "alice",
            "message": "hello",
            "msgId": "msg-1",
            "recalled": True,
            "time": 123,
        })

        self.assertEqual(normalized["payload"], {
            "msg": "hello",
            "msgId": "msg-1",
            "recalled": True,
            "time": 123,
        })

    def test_history_is_bounded_and_trimmed_ids_can_be_seen_again(self):
        history = LiveChatHistory(limit=2)
        history.append({"msg": "one", "msgId": "msg-1"})
        history.append({"msg": "two", "msgId": "msg-2"})
        history.append({"msg": "three", "msgId": "msg-3"})

        self.assertEqual([item["payload"]["msgId"] for item in history.snapshot()], ["msg-2", "msg-3"])
        self.assertTrue(history.append({"msg": "one again", "msgId": "msg-1"})[0])


if __name__ == "__main__":
    unittest.main()
