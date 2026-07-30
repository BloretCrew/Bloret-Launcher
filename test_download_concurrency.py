"""Tests for the process-wide Minecraft transfer limiter."""

from __future__ import annotations

import threading
import time

from modules.download.limits import GlobalDownloadLimiter


def test_global_limit_blocks_extra_transfers():
    limiter = GlobalDownloadLimiter(2)
    active = 0
    maximum = 0
    lock = threading.Lock()
    release = threading.Event()

    def worker():
        nonlocal active, maximum
        assert limiter.acquire()
        try:
            with lock:
                active += 1
                maximum = max(maximum, active)
            release.wait(timeout=2)
        finally:
            with lock:
                active -= 1
            limiter.release()

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for thread in threads:
        thread.start()
    time.sleep(0.1)
    assert maximum == 2
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert limiter.get_in_flight() == 0


def test_waiting_transfer_can_cancel():
    limiter = GlobalDownloadLimiter(1)
    assert limiter.acquire()
    cancelled = threading.Event()
    result = []

    thread = threading.Thread(target=lambda: result.append(limiter.acquire(cancelled)))
    thread.start()
    time.sleep(0.05)
    cancelled.set()
    thread.join(timeout=1)
    limiter.release()
    assert result == [False]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("OK", name)
