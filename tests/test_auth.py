import tempfile
import unittest
import threading
import re
from tests.http_server import make_test_server
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
from pathlib import Path
from unittest.mock import patch

from resolveai import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(auth, "AUTH_PATH", Path(directory.name) / "reviewer.json")
        patcher.start()
        self.addCleanup(patcher.stop)
        sessions = patch.object(auth, "SESSIONS", {})
        sessions.start()
        self.addCleanup(sessions.stop)

    def test_setup_password_and_logout(self):
        password = "test-only-password-123"
        auth.configure(password)
        self.assertNotIn(password, auth.AUTH_PATH.read_text())
        self.assertIsNone(auth.login("incorrect"))
        session = auth.login(password)
        cookie = "resolveai_reviewer=" + session
        self.assertTrue(auth.authorized(cookie))
        auth.logout(cookie)
        self.assertFalse(auth.authorized(cookie))

    def test_unconfigured_and_invalid_cookie(self):
        self.assertIsNone(auth.login("anything"))
        self.assertFalse(auth.authorized("resolveai_reviewer=made-up"))
        with self.assertRaises(ValueError):
            auth.configure("short")

    def test_expiry(self):
        auth.SESSIONS["expired"] = 1
        self.assertFalse(auth.authorized("resolveai_reviewer=expired"))

    def test_http_login_logout_and_blocked_review(self):
        auth.configure("test-only-password-123")
        with make_test_server() as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            opener = build_opener(HTTPCookieProcessor(CookieJar()))
            def post(path, data):
                return opener.open(Request(base + path, data=urlencode(data).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=3)
            try:
                with opener.open(base + "/reviews", timeout=3) as response:
                    page = response.read().decode()
                self.assertIn("Reviewer sign-in", page)
                token = re.search('name="token" value="([^"]+)"', page)[1]
                with self.assertRaises(HTTPError) as error:
                    post("/reviews/decide", {"token": token, "request_id": 1, "action": "approve"})
                self.assertEqual(error.exception.code, 401)
                with patch("resolveai.web.render_reviews", return_value=b"Authenticated review controls"):
                    with post("/login", {"token": token, "password": "test-only-password-123"}) as response:
                        self.assertIn("Authenticated review controls", response.read().decode())
                with post("/logout", {"token": token}) as response:
                    self.assertIn("Reviewer sign-in", response.read().decode())
            finally:
                server.shutdown()
                worker.join()
