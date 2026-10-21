"""Passport OAuth 2.0 Authorization Code + PKCE coordinator."""

from __future__ import annotations

import base64
import hashlib
import http.server
import re
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Callable, Optional

import requests

CALLBACK_PATH = "/login/Bloret-PassPort"
PROTOCOL_CALLBACK_URI = "bloret://oauth/passport"
_active_coordinator = None
_active_lock = threading.RLock()
DEFAULT_AUTHORIZE_ENDPOINT = "https://passport.bloret.net/oauth/authorize"
DEFAULT_TOKEN_ENDPOINT = "https://passport.bloret.net/oauth/token"
DEFAULT_USERINFO_ENDPOINT = "https://passport.bloret.net/oauth/userinfo"
TRANSACTION_TIMEOUT = 300
CLOCK_SKEW = 60


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


class PassportAuthorizationError(PermissionError):
    """Validated OAuth authorization error returned by PassPort."""

    def __init__(self, error_code: str, description: str = ""):
        self.error_code = error_code
        self.description = description
        detail = f"PassPort returned OAuth error: {error_code}"
        if description:
            detail += f" — {description}"
        super().__init__(detail)


class PassportOAuthCoordinator:
    def __init__(self, *, authorize_endpoint=DEFAULT_AUTHORIZE_ENDPOINT,
                 token_endpoint=DEFAULT_TOKEN_ENDPOINT,
                 userinfo_endpoint=DEFAULT_USERINFO_ENDPOINT,
                 client_id="BloretLauncher", browser_opener=None,
                 timeout=TRANSACTION_TIMEOUT, on_complete=None, on_status=None,
                 callback_mode="protocol"):
        if callback_mode not in {"protocol", "loopback"}:
            raise ValueError("Unsupported Passport callback mode")
        self.callback_mode = callback_mode
        self.authorize_endpoint = self._passport_endpoint(authorize_endpoint)
        self.token_endpoint = self._passport_endpoint(token_endpoint)
        self.userinfo_endpoint = self._passport_endpoint(userinfo_endpoint)
        self.client_id = client_id
        self.browser_opener = browser_opener or webbrowser.open
        self.timeout = timeout
        self.on_complete = on_complete
        self.on_status = on_status
        self._pending: Optional[PendingTransaction] = None
        self._reserved = False
        self._lock = threading.RLock()
        self._server = None
        self._completed_result = None

    @staticmethod
    def _passport_endpoint(url):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "::1"}:
            raise ValueError("Passport endpoints must use HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid Passport endpoint")
        return url.rstrip("/")

    def _status(self, category, detail=""):
        if self.on_status:
            try:
                self.on_status(category, detail)
            except Exception:
                pass

    def _expire_pending(self):
        expired = False
        with self._lock:
            if self._pending and time.monotonic() - self._pending.created_at > self.timeout:
                self._pending = None
                self._reserved = False
                expired = True
        if expired:
            self._stop_server()
            self._status("expired", "Passport login expired; please retry")

    def begin(self):
        global _active_coordinator
        self._expire_pending()
        with _active_lock, self._lock:
            if self._pending or self._reserved:
                raise RuntimeError("A Passport login is already pending")
            if self.callback_mode == "protocol" and _active_coordinator is not None:
                active = _active_coordinator
                active._expire_pending()
                if active._pending or active._reserved:
                    raise RuntimeError("A Passport login is already pending")
            server = None
            redirect_uri = PROTOCOL_CALLBACK_URI
            if self.callback_mode == "loopback":
                server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
                redirect_uri = "http://127.0.0.1:%d%s" % (server.server_port, CALLBACK_PATH)
            transaction = PendingTransaction(secrets.token_urlsafe(32), generate_code_verifier(), redirect_uri, time.monotonic())
            self._server = server
            self._pending = transaction
            self._completed_result = None
            if self.callback_mode == "protocol":
                _active_coordinator = self
            query = urllib.parse.urlencode({
                "client_id": self.client_id, "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "user:name user:head minecraft:accounts bbbs:session",
                "state": transaction.state, "code_challenge": build_code_challenge(transaction.verifier),
                "code_challenge_method": "S256",
            })
            url = self.authorize_endpoint + "?" + query
            if server is not None:
                threading.Thread(target=server.serve_forever, daemon=True, name="PassportOAuthCallback").start()
        try:
            if not self.browser_opener(url):
                raise OSError("Unable to open browser")
        except Exception:
            self.cancel()
            self._status("failure", "Unable to open browser")
            raise
        self._status("started", "Passport login started")
        return transaction

    def _reserve_callback(self, callback_url):
        self._expire_pending()
        parsed = urllib.parse.urlparse(callback_url)
        with self._lock:
            transaction = self._pending
            if not transaction or self._reserved:
                raise ValueError("No pending Passport login")
            expected = urllib.parse.urlparse(transaction.redirect_uri)
            if (parsed.scheme, parsed.netloc, parsed.path) != (expected.scheme, expected.netloc, expected.path) or parsed.fragment or parsed.params:
                raise ValueError("Invalid Passport callback")
            try:
                pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
            except ValueError as error:
                raise ValueError("Malformed Passport callback") from error
            params = {}
            for key, value in pairs:
                params.setdefault(key, []).append(value)
            allowed = {"code", "state", "error", "error_description", "error_uri"}
            if any(key not in allowed for key in params):
                raise ValueError("Unexpected Passport callback parameter")
            if len(params.get("state", [])) != 1 or params["state"][0] != transaction.state:
                raise ValueError("Invalid Passport state")
            if "error" in params:
                if len(params["error"]) != 1 or "code" in params:
                    raise ValueError("Invalid Passport authorization response")
                if len(params.get("error_description", [])) > 1 or len(params.get("error_uri", [])) > 1:
                    raise ValueError("Invalid Passport authorization error details")
                error_code = params["error"][0][:80] or "unknown_error"
                description = params.get("error_description", [""])[0]
                description = " ".join("".join(ch if ch.isprintable() else " " for ch in description).split())[:240]
                description = re.sub(
                    r"(?i)\b(code|state|access_token|refresh_token)=\S+",
                    r"\1=<redacted>", description,
                )
                raise PassportAuthorizationError(error_code, description)
            if len(params.get("code", [])) != 1 or not params["code"][0]:
                raise ValueError("Missing Passport authorization code")
            self._reserved = True
            return params["code"][0], transaction

    def validate_callback(self, callback_url):
        return self._reserve_callback(callback_url)

    def exchange_code(self, code, transaction):
        response = requests.post(self.token_endpoint, data={
            "grant_type": "authorization_code", "client_id": self.client_id,
            "code": code, "redirect_uri": transaction.redirect_uri,
            "code_verifier": transaction.verifier,
        }, timeout=15)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not result.get("access_token"):
            raise ValueError("Passport token response did not contain an access token")
        return result

    def fetch_userinfo(self, access_token):
        response = requests.get(self.userinfo_endpoint, headers={"Authorization": "Bearer " + access_token}, timeout=15)
        if response.status_code == 401:
            raise PermissionError("Passport access token is invalid")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Invalid Passport userinfo response")
        return result

    def complete_callback(self, callback_url):
        try:
            code, transaction = self._reserve_callback(callback_url)
        except PassportAuthorizationError as error:
            self.cancel()
            self._status("reauthorization_required", str(error))
            raise
        try:
            result = self.exchange_code(code, transaction)
            userinfo = self.fetch_userinfo(result["access_token"])
            with self._lock:
                self._completed_result = (result, userinfo)
                self._pending = None
                self._reserved = False
            self._stop_server()
            if self.on_complete:
                self.on_complete(result, userinfo)
            self._status("success", "Passport login succeeded")
            return result, userinfo
        except Exception as error:
            with self._lock:
                self._pending = None
                self._reserved = False
            self._stop_server()
            category = "reauthorization_required" if isinstance(error, PermissionError) else "failure"
            self._status(category, category.replace("_", " "))
            raise

    def wait_for_result(self):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            with self._lock:
                if not self._pending:
                    if self._completed_result:
                        return self._completed_result
                    break
            time.sleep(0.1)
        self.cancel()
        raise TimeoutError("Passport login timed out")

    def handle_callback(self, callback_url):
        try:
            self.complete_callback(callback_url)
            return True
        except Exception:
            return False

    def access_token_status(self, oauth, now=None):
        oauth = oauth if isinstance(oauth, dict) else {}
        token = oauth.get("access_token")
        if not token:
            return "reauthorization_required"
        expires_in = oauth.get("expires_in")
        obtained_at = oauth.get("obtained_at")
        if expires_in is None or obtained_at is None:
            return "unknown_expiry"
        try:
            return "expired" if (now or time.time()) >= float(obtained_at) + float(expires_in) - CLOCK_SKEW else "valid"
        except (TypeError, ValueError):
            return "unknown_expiry"

    def refresh_access_token(self, oauth):
        refresh_token = (oauth or {}).get("refresh_token")
        if not refresh_token:
            raise PermissionError("Passport reauthorization required")
        response = requests.post(self.token_endpoint, data={
            "grant_type": "refresh_token", "client_id": self.client_id,
            "refresh_token": refresh_token,
        }, timeout=15)
        if response.status_code in (400, 401):
            raise PermissionError("Passport reauthorization required")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not result.get("access_token"):
            raise ValueError("Invalid Passport refresh response")
        refreshed = dict(oauth)
        refreshed.update({"access_token": result["access_token"], "obtained_at": int(time.time())})
        for key in ("refresh_token", "expires_in", "token_type"):
            if key in result:
                refreshed[key] = result[key]
        return refreshed

    def cancel(self):
        with self._lock:
            self._pending = None
            self._reserved = False
        self._stop_server()

    def _stop_server(self):
        global _active_coordinator
        with _active_lock:
            if _active_coordinator is self:
                _active_coordinator = None
        with self._lock:
            server, self._server = self._server, None
        if server:
            server.shutdown()
            server.server_close()

    def _handler(self):
        coordinator = self
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    coordinator.complete_callback("http://127.0.0.1:%d%s" % (self.server.server_port, self.path))
                    self.send_response(200)
                    body = b"Login complete. You may close this window."
                except PermissionError:
                    self.send_response(400)
                    body = b"Login was denied or requires reauthorization. You may close this window."
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


def is_passport_session_authenticated(config, now=None):
    """Check that persisted PassPort state represents a usable signed-in session."""
    if not isinstance(config, dict) or not config.get("Bloret_PassPort_Login"):
        return False
    if not str(config.get("Bloret_PassPort_UserName") or "").strip():
        return False
    # Userinfo must identify the account. An authorization code and token alone
    # are not enough to claim the UI is signed in.
    userinfo = config.get("Bloret_PassPort_UserInfo")
    if isinstance(userinfo, dict) and not str(userinfo.get("username") or userinfo.get("name") or "").strip():
        return False
    oauth = config.get("Bloret_PassPort_OAuth")
    if not isinstance(oauth, dict) or not oauth.get("access_token"):
        return False
    return PassportOAuthCoordinator().access_token_status(oauth, now=now) == "valid"


def dispatch_passport_callback(url):
    """Reserve the login protocol route before any plugin sees OAuth credentials."""
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme, parsed.netloc, parsed.path) != ("bloret", "oauth", "/passport"):
        return False
    with _active_lock:
        coordinator = _active_coordinator
    if coordinator is not None:
        threading.Thread(target=coordinator.handle_callback, args=(url,),
                         daemon=True, name="PassportProtocolCallback").start()
    return True


def login_with_passport(*, save_config: Callable[[dict], None], config: dict, status_callback=None):
    coordinator = PassportOAuthCoordinator(on_status=status_callback)
    try:
        coordinator.begin()
        result, userinfo = coordinator.wait_for_result()
        updated = dict(config or {})
        updated.update({"Bloret_PassPort_Login": True, "Bloret_PassPort_UserName": str(userinfo.get("username") or userinfo.get("name") or ""), "Bloret_PassPort_NickName": str(userinfo.get("nickname") or userinfo.get("name") or ""), "Bloret_PassPort_Avatar": str(userinfo.get("avatar") or "")})
        updated["bbbs_session"] = str(userinfo.get("bbbs_session") or "")
        updated["bbbs_session_sig"] = str(userinfo.get("bbbs_session.sig") or "")
        updated["bbbs_csrf_token"] = str(userinfo.get("bbbs_csrf_token") or "")
        updated["Bloret_PassPort_OAuth"] = {"access_token": result["access_token"], "refresh_token": result.get("refresh_token", ""), "expires_in": result.get("expires_in"), "token_type": result.get("token_type", "Bearer"), "obtained_at": int(time.time())}
        if not str(userinfo.get("username") or userinfo.get("name") or "").strip():
            raise PermissionError("PassPort userinfo did not identify an account")
        updated["Bloret_PassPort_PassWord"] = ""
        save_config(updated)
        return True
    except Exception:
        coordinator.cancel()
        return False
