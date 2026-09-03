"""Passport OAuth 2.0 Authorization Code + PKCE coordinator."""

from __future__ import annotations

import base64
import hashlib
import http.server
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Callable, Optional

import requests


CALLBACK_PATH = "/login/Bloret-PassPort"
DEFAULT_AUTHORIZE_ENDPOINT = "https://passport.bloret.net/oauth/authorize"
DEFAULT_TOKEN_ENDPOINT = "https://passport.bloret.net/oauth/token"
DEFAULT_USERINFO_ENDPOINT = "https://passport.bloret.net/oauth/userinfo"
TRANSACTION_TIMEOUT = 300


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def build_code_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


@dataclass
class PendingTransaction:
    state: str
    verifier: str
    redirect_uri: str
    created_at: float


class PassportOAuthCoordinator:
    def __init__(self, *, authorize_endpoint=DEFAULT_AUTHORIZE_ENDPOINT,
                 token_endpoint=DEFAULT_TOKEN_ENDPOINT,
                 userinfo_endpoint=DEFAULT_USERINFO_ENDPOINT,
                 client_id="BloretLauncher", browser_opener=None,
                 timeout=TRANSACTION_TIMEOUT, on_complete=None):
        self.authorize_endpoint = self._passport_endpoint(authorize_endpoint)
        self.token_endpoint = self._passport_endpoint(token_endpoint)
        self.userinfo_endpoint = self._passport_endpoint(userinfo_endpoint)
        self.client_id = client_id
        self.browser_opener = browser_opener or webbrowser.open
        self.timeout = timeout
        self.on_complete = on_complete
        self._pending: Optional[PendingTransaction] = None
        self._lock = threading.RLock()
        self._server = None

    @staticmethod
    def _passport_endpoint(url):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            # Local HTTP endpoints are useful only for isolated tests.
            if not (parsed.hostname in {"127.0.0.1", "::1"}):
                raise ValueError("Passport endpoints must use HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid Passport endpoint")
        return url.rstrip("/")

    def _expire_pending(self):
        with self._lock:
            if self._pending and time.monotonic() - self._pending.created_at > self.timeout:
                self._pending = None

    def begin(self):
        self._expire_pending()
        with self._lock:
            if self._pending:
                raise RuntimeError("A Passport login is already pending")
            self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
            redirect_uri = "http://127.0.0.1:%d%s" % (self._server.server_port, CALLBACK_PATH)
            transaction = PendingTransaction(secrets.token_urlsafe(32), generate_code_verifier(), redirect_uri, time.monotonic())
            self._pending = transaction
            query = urllib.parse.urlencode({
                "client_id": self.client_id, "redirect_uri": redirect_uri,
                "response_type": "code", "scope": "openid profile",
                "state": transaction.state, "code_challenge": build_code_challenge(transaction.verifier),
                "code_challenge_method": "S256",
            })
            url = self.authorize_endpoint + "?" + query
            threading.Thread(target=self._server.serve_forever, daemon=True, name="PassportOAuthCallback").start()
        self.browser_opener(url)
        return transaction

    def validate_callback(self, callback_url):
        self._expire_pending()
        parsed = urllib.parse.urlparse(callback_url)
        with self._lock:
            transaction = self._pending
        if not transaction:
            raise ValueError("No pending Passport login")
        if (parsed.scheme, parsed.hostname, parsed.port, parsed.path) != ("http", "127.0.0.1", urllib.parse.urlparse(transaction.redirect_uri).port, CALLBACK_PATH):
            raise ValueError("Invalid Passport callback")
        params = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
        if params.get("state", [None])[0] != transaction.state:
            raise ValueError("Invalid Passport state")
        if params.get("error"):
            raise ValueError("Passport authorization failed")
        code = params.get("code", [None])[0]
        if not code or len(params.get("code", [])) != 1:
            raise ValueError("Missing Passport authorization code")
        return code, transaction

    def exchange_code(self, code, transaction):
        response = requests.post(self.token_endpoint, data={
            "grant_type": "authorization_code", "client_id": self.client_id,
            "code": code, "redirect_uri": transaction.redirect_uri,
            "code_verifier": transaction.verifier,
        }, timeout=15)
        response.raise_for_status()
        result = response.json()
        if not result.get("access_token"):
            raise ValueError("Passport token response did not contain an access token")
        return result

    def fetch_userinfo(self, access_token):
        response = requests.get(self.userinfo_endpoint, headers={"Authorization": "Bearer " + access_token}, timeout=15)
        if response.status_code == 401:
            raise PermissionError("Passport access token is invalid")
        response.raise_for_status()
        return response.json()

    def complete_callback(self, callback_url):
        code, transaction = self.validate_callback(callback_url)
        result = self.exchange_code(code, transaction)
        userinfo = self.fetch_userinfo(result["access_token"])
        with self._lock:
            self._completed_result = (result, userinfo)
            self._pending = None
        self._stop_server()
        if self.on_complete:
            self.on_complete(result, userinfo)
        return result, userinfo

    def wait_for_result(self):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            with self._lock:
                if not self._pending:
                    result = getattr(self, "_completed_result", None)
                    if result:
                        return result
                    break
            time.sleep(0.1)
        self.cancel()
        raise TimeoutError("Passport login timed out")

    def handle_callback(self, callback_url):
        try:
            self.validate_callback(callback_url)
        except ValueError:
            return False
        with self._lock:
            self._pending = None
        self._stop_server()
        return True

    def cancel(self):
        with self._lock:
            self._pending = None
        self._stop_server()

    def _stop_server(self):
        server = self._server
        self._server = None
        if server:
            server.shutdown()
            server.server_close()

    def _handler(self):
        coordinator = self
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    result, userinfo = coordinator.complete_callback("http://127.0.0.1:%d%s" % (self.server.server_port, self.path))
                    self.send_response(200)
                    body = b"Login complete. You may close this window."
                except Exception:
                    self.send_response(400)
                    body = b"Login failed. You may close this window."
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_args):
                return
        return CallbackHandler


def login_with_passport(*, save_config: Callable[[dict], None], config: dict, status_callback=None):
    coordinator = PassportOAuthCoordinator()
    try:
        if status_callback:
            status_callback("started", "Passport login started")
        result, userinfo = coordinator.begin_and_wait(save_config, config)
        if status_callback:
            status_callback("success", "Passport login succeeded")
        return True
    except Exception as error:
        coordinator.cancel()
        if status_callback:
            status_callback("failure", "Passport login failed")
        return False


def _begin_and_wait(self, save_config, config):
    self._completed_result = None
    self.begin()
    result, userinfo = self.wait_for_result()
    updated = dict(config or {})
    updated["Bloret_PassPort_Login"] = True
    updated["Bloret_PassPort_UserName"] = str(userinfo.get("username") or userinfo.get("name") or "")
    updated["Bloret_PassPort_NickName"] = str(userinfo.get("nickname") or userinfo.get("name") or updated["Bloret_PassPort_UserName"])
    updated["Bloret_PassPort_OAuth"] = {
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token", ""),
        "expires_in": result.get("expires_in"),
        "token_type": result.get("token_type", "Bearer"),
        "obtained_at": int(time.time()),
    }
    updated["Bloret_PassPort_PassWord"] = ""
    save_config(updated)
    return result, userinfo

PassportOAuthCoordinator.begin_and_wait = _begin_and_wait
