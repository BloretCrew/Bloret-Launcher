"""Process-wide limit for concurrent Minecraft file transfers."""

from __future__ import annotations

import threading

from modules.download.constants import DEFAULT_MAX_THREAD, clamp_workers


class GlobalDownloadLimiter:
    def __init__(self, limit=DEFAULT_MAX_THREAD):
        self._condition = threading.Condition()
        self._limit = clamp_workers(limit)
        self._in_flight = 0

    def set_limit(self, value):
        with self._condition:
            self._limit = clamp_workers(value)
            self._condition.notify_all()
            return self._limit

    def get_limit(self):
        with self._condition:
            return self._limit

    def get_in_flight(self):
        with self._condition:
            return self._in_flight

    def acquire(self, cancel_event=None):
        with self._condition:
            while self._in_flight >= self._limit:
                if cancel_event is not None and cancel_event.is_set():
                    return False
                self._condition.wait(timeout=0.2)
            if cancel_event is not None and cancel_event.is_set():
                return False
            self._in_flight += 1
            return True

    def release(self):
        with self._condition:
            if self._in_flight <= 0:
                raise RuntimeError("download limiter released without acquire")
            self._in_flight -= 1
            self._condition.notify_all()


_limiter = GlobalDownloadLimiter()


def get_download_limiter():
    return _limiter


def set_global_download_limit(value):
    return _limiter.set_limit(value)


def get_global_download_limit():
    return _limiter.get_limit()
