"""Fictional local customers with server-side order ownership."""

import getpass
import hashlib
import hmac
import json
import secrets
import time
from html import escape
from http.cookies import SimpleCookie, CookieError
from pathlib import Path

from .auth import LOCK, TTL

CUSTOMER_PATH = Path(__file__).resolve().parent.parent / "runtime" / "customers.json"
SESSIONS = {}
OWNERSHIP = {"alex": ("DEMO-1001", "DEMO-1002"), "sam": ("DEMO-1003",)}


def configure(username, password):
    if username not in OWNERSHIP or len(password) < 12:
        raise ValueError("Choose alex or sam and a password of at least 12 characters.")
    records = json.loads(CUSTOMER_PATH.read_text()) if CUSTOMER_PATH.exists() else {}
    if username in records:
        raise ValueError("Customer is already configured.")
    salt = secrets.token_hex(16)
    records[username] = {"salt": salt, "hash": hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()}
    CUSTOMER_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Setup is a local administrative command, not a web registration endpoint.
    with CUSTOMER_PATH.open("w", encoding="utf-8") as file:
        file.write(json.dumps(records))
    CUSTOMER_PATH.chmod(0o600)


def login(username, password):
    try:
        record = json.loads(CUSTOMER_PATH.read_text())[username]
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(record["salt"]), 600000).hex()
        if username not in OWNERSHIP or not hmac.compare_digest(digest, record["hash"]):
            return None
    except (OSError, KeyError, ValueError, TypeError):
        return None
    session = secrets.token_urlsafe(32)
    with LOCK:
        now = time.monotonic()
        for key in list(SESSIONS):
            if SESSIONS[key][1] <= now:
                del SESSIONS[key]
        if len(SESSIONS) >= 100:
            SESSIONS.pop(next(iter(SESSIONS)))
        SESSIONS[session] = (username, now + TTL)
    return session


def token(header):
    try:
        cookie = SimpleCookie()
        cookie.load(header or "")
        return cookie["resolveai_customer"].value if "resolveai_customer" in cookie else ""
    except CookieError:
        return ""


def identity(header):
    with LOCK:
        username, expires = SESSIONS.get(token(header), (None, 0))
        return username if expires > time.monotonic() else None


def logout(header):
    with LOCK:
        SESSIONS.pop(token(header), None)


def owns(username, order_id):
    return order_id.strip().upper() in OWNERSHIP.get(username, ())


def render_account(csrf, username=None, message=""):
    from .orders import lookup_order
    content = f'<p role="status">{escape(message)}</p>'
    if username:
        content += f'<p>Signed in as {escape(username)}.</p><form action="/customer/logout" method="post"><input type="hidden" name="token" value="{csrf}"><button>Sign out</button></form><h2>Your demo orders</h2><ul>'
        for order_id in OWNERSHIP[username]:
            order = lookup_order(order_id)
            content += f'<li><a href="/?order_id={order_id}">{order_id}</a>: {escape(order["status"])}</li>'
        content += f'</ul><h2>Request cancellation review</h2><form action="/customer/submit" method="post"><input type="hidden" name="token" value="{csrf}"><label for="order">Order ID</label> <input id="order" name="order_id" required><button>Submit for review</button></form><p>This submits a request only. A reviewer must approve it.</p>'
    else:
        content += f'<p>Use a configured fictional customer: alex or sam. Setup: python -m resolveai.customers</p><form action="/customer/login" method="post"><input type="hidden" name="token" value="{csrf}"><label for="username">Username</label> <input id="username" name="username" autocomplete="username" required><br><label for="password">Password</label> <input id="password" name="password" type="password" autocomplete="current-password" required maxlength="256"><button>Sign in</button></form>'
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Customer account</title><body style="max-width:700px;margin:40px auto;padding:24px;font:18px/1.6 system-ui"><a href="/">Back to support</a><h1>Customer account</h1>{content}</body></html>'.encode()


if __name__ == "__main__":
    try:
        username = input("Demo customer username (alex or sam): ").strip().lower()
        password = getpass.getpass("Choose a customer password (12+ characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords did not match.")
        configure(username, password)
        print("Customer configured. Keep the password private; sign in at /account.")
    except ValueError as error:
        raise SystemExit(str(error))
