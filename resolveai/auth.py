"""Single-reviewer authentication for the local sandbox, not public hosting."""

import getpass
import hashlib
import hmac
import json
import secrets
import threading
import time
from http.cookies import SimpleCookie, CookieError
from pathlib import Path

AUTH_PATH = Path(__file__).resolve().parent.parent / "runtime" / "reviewer.json"
SESSIONS = {}
LOCK = threading.Lock()
TTL = 3600


def configure(password):
    if len(password) < 12:
        raise ValueError("Use at least 12 characters.")
    if AUTH_PATH.exists():
        raise ValueError("Reviewer is already configured. Password replacement is not supported by this setup command.")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()
    AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUTH_PATH.open("x", encoding="utf-8") as file:
        file.write(json.dumps({"salt": salt, "hash": digest}))
    AUTH_PATH.chmod(0o600)


def login(password):
    try:
        record = json.loads(AUTH_PATH.read_text())
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(record["salt"]), 600000).hex()
        if not hmac.compare_digest(digest, record["hash"]):
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None
    token = secrets.token_urlsafe(32)
    with LOCK:
        now = time.monotonic()
        for key in list(SESSIONS):
            if SESSIONS[key] <= now:
                del SESSIONS[key]
        if len(SESSIONS) >= 100:
            SESSIONS.pop(next(iter(SESSIONS)))
        SESSIONS[token] = now + TTL
    return token


def cookie_token(header):
    try:
        cookie = SimpleCookie()
        cookie.load(header or "")
        return cookie["resolveai_reviewer"].value if "resolveai_reviewer" in cookie else ""
    except CookieError:
        return ""


def authorized(header):
    with LOCK:
        return SESSIONS.get(cookie_token(header), 0) > time.monotonic()


def logout(header):
    with LOCK:
        SESSIONS.pop(cookie_token(header), None)


def render_login(token, message=""):
    from html import escape
    setup = "" if AUTH_PATH.exists() else "Reviewer is not configured. Run python -m resolveai.auth in Terminal first."
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reviewer sign-in</title><body style="max-width:600px;margin:60px auto;padding:24px;font:18px/1.6 system-ui"><a href="/">Back to support</a><h1>Reviewer sign-in</h1><p>Local fictional-order sandbox.</p><p role="status">{escape(message)} {setup}</p><form action="/login" method="post"><input type="hidden" name="token" value="{token}"><label for="password">Reviewer password</label><br><input id="password" name="password" type="password" autocomplete="current-password" required maxlength="256"><button>Sign in</button></form></body></html>'''.encode()


if __name__ == "__main__":
    try:
        password = getpass.getpass("Choose a reviewer password (12+ characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords did not match.")
        configure(password)
        print("Reviewer configured. Keep the password private; sign in at /reviews.")
    except ValueError as error:
        raise SystemExit(str(error))
