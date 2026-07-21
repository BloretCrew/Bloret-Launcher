"""Download concurrency defaults."""

DEFAULT_MAX_THREAD = 16
MAX_THREAD_CAP = 64
FASTDOWNLOAD_TTL_SEC = 600  # fastdownload API cache TTL


def clamp_workers(value, default=DEFAULT_MAX_THREAD):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    return max(1, min(n, MAX_THREAD_CAP))
