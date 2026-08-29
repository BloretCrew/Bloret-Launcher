from __future__ import annotations

from collections import Counter
import threading


DEFAULT_HISTORY_LIMIT = 500


def normalize_chat_event(event):
    """Normalize service chat shapes without discarding compatible fields."""
    if not isinstance(event, dict):
        return None

    normalized = dict(event)
    raw_payload = event.get("payload")
    if isinstance(raw_payload, dict):
        payload = dict(raw_payload)
    elif raw_payload is None:
        payload = {}
    else:
        payload = {"msg": raw_payload}

    message = payload.get("msg")
    if message is None:
        message = payload.get("message")
    if message is None:
        message = event.get("msg")
    if message is None:
        message = event.get("message", "")

    msg_id = payload.get("msgId") or event.get("msgId")
    recalled = payload.get("recalled", event.get("recalled", False))
    event_time = payload.get("time", event.get("time"))

    payload["msg"] = message
    if msg_id is not None:
        payload["msgId"] = msg_id
    payload["recalled"] = recalled
    payload["time"] = event_time

    normalized["type"] = "chat"
    normalized["from"] = event.get("from", payload.get("from", ""))
    normalized["payload"] = payload
    return normalized


def chat_message_id(event):
    if not isinstance(event, dict):
        return None
    payload = event.get("payload")
    if isinstance(payload, dict) and payload.get("msgId"):
        return str(payload["msgId"])
    if event.get("msgId"):
        return str(event["msgId"])
    return None


def _fallback_identity(event):
    payload = event.get("payload", {})
    return (
        event.get("from", ""),
        payload.get("msg", ""),
        bool(payload.get("recalled", False)),
        payload.get("time"),
    )


def _has_field(event, field):
    payload = event.get("payload")
    return (isinstance(payload, dict) and field in payload) or field in event


def _merge_message_update(existing, incoming, raw_event):
    merged = dict(existing)
    merged_payload = dict(existing.get("payload") or {})
    incoming_payload = incoming.get("payload") or {}

    canonical_fields = {"payload", "msg", "message", "msgId", "recalled", "time"}
    for key, value in incoming.items():
        if key not in canonical_fields:
            merged[key] = value

    if _has_field(raw_event, "msg") or _has_field(raw_event, "message") or not merged_payload.get("msg"):
        merged_payload["msg"] = incoming_payload.get("msg", "")
    if _has_field(raw_event, "recalled"):
        merged_payload["recalled"] = incoming_payload.get("recalled", False)
    if _has_field(raw_event, "time"):
        merged_payload["time"] = incoming_payload.get("time")
    if incoming_payload.get("msgId") is not None:
        merged_payload["msgId"] = incoming_payload["msgId"]

    merged["type"] = "chat"
    merged["payload"] = merged_payload
    return merged


class LiveChatHistory:
    """Keep a bounded normalized history and deduplicate stable message IDs."""

    def __init__(self, limit=DEFAULT_HISTORY_LIMIT):
        self._limit = max(1, int(limit))
        self._history = []
        self._message_indexes = {}
        self._lock = threading.Lock()

    def clear(self):
        with self._lock:
            self._history = []
            self._message_indexes = {}

    def reconcile_initial(self, chat_history):
        initial = chat_history if isinstance(chat_history, list) else []
        with self._lock:
            existing = list(self._history)
            self._history = []
            self._message_indexes = {}
            for event in initial:
                self._append_locked(event, update_existing=False)

            initial_fallback_counts = Counter(
                _fallback_identity(event)
                for event in self._history
                if chat_message_id(event) is None
            )
            existing_fallback_counts = Counter()
            for event in existing:
                msg_id = chat_message_id(event)
                if msg_id is not None:
                    if msg_id not in self._message_indexes:
                        self._append_locked(event)
                    continue

                identity = _fallback_identity(event)
                existing_fallback_counts[identity] += 1
                if existing_fallback_counts[identity] > initial_fallback_counts[identity]:
                    self._append_locked(event)
            return list(self._history)

    def append(self, event):
        with self._lock:
            return self._append_locked(event)

    def snapshot(self):
        with self._lock:
            return list(self._history)

    def _append_locked(self, event, update_existing=True):
        normalized = normalize_chat_event(event)
        if normalized is None:
            return False, None

        msg_id = chat_message_id(normalized)
        if msg_id is not None and msg_id in self._message_indexes:
            index = self._message_indexes[msg_id]
            if not update_existing:
                return False, self._history[index]
            merged = _merge_message_update(self._history[index], normalized, event)
            if merged == self._history[index]:
                return False, self._history[index]
            self._history[index] = merged
            return True, merged

        self._history.append(normalized)
        if msg_id is not None:
            self._message_indexes[msg_id] = len(self._history) - 1
        self._trim_locked()
        return True, normalized

    def _trim_locked(self):
        if len(self._history) <= self._limit:
            return
        self._history = self._history[-self._limit:]
        self._message_indexes = {
            msg_id: index
            for index, item in enumerate(self._history)
            if (msg_id := chat_message_id(item)) is not None
        }
