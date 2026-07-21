"""Thread-local HTTP sessions with connection pooling."""

import threading

import requests

_thread_local = threading.local()


def get_session():
    """Return a thread-local requests.Session with pool + limited retries."""
    if not hasattr(_thread_local, "session"):
        from requests.adapters import HTTPAdapter

        try:
            from urllib3.util.retry import Retry

            retry = Retry(
                total=2,
                connect=2,
                read=1,
                backoff_factor=0.4,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "HEAD"]),
                raise_on_status=False,
            )
        except Exception:
            retry = 0
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=32, max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": "Bloret-Launcher/download"})
        _thread_local.session = session
    return _thread_local.session
