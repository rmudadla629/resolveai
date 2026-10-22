import re
import threading
from pathlib import Path
from http.cookiejar import CookieJar
from tests.http_server import make_test_server
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, Request
from unittest.mock import patch

from resolveai import customers, reviews
from resolveai.agent import answer_question
from tests.support import IsolatedOrderTestCase


class CustomerTests(IsolatedOrderTestCase):
    def setUp(self):
        super().setUp()
        for attribute, value in [("CUSTOMER_PATH", reviews.DB_PATH.parent / "customers.json"), ("SESSIONS", {})]:
            patcher = patch.object(customers, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_sessions_and_ownership(self):
        customers.configure("alex", "test-customer-password")
        self.assertIsNone(customers.login("alex", "wrong"))
        session = customers.login("alex", "test-customer-password")
        cookie = "resolveai_customer=" + session
        self.assertEqual(customers.identity(cookie), "alex")
        self.assertTrue(customers.owns("alex", "DEMO-1002"))
        self.assertFalse(customers.owns("sam", "DEMO-1002"))
        customers.logout(cookie)
        self.assertIsNone(customers.identity(cookie))

    @patch("resolveai.agent.classify", return_value={"intent": "order_status", "order_id": "DEMO-1003"})
    def test_workflow_ownership(self, model):
        status, body = answer_question("Track DEMO-1003", allowed_order_ids=customers.OWNERSHIP["alex"])
        self.assertEqual(status, 404)
        self.assertNotIn("order", body)

    def test_http_customer_isolation_and_review_permissions(self):
        customers.configure("alex", "test-customer-password")
        customers.configure("sam", "test-second-password")
        with make_test_server() as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            opener = build_opener(HTTPCookieProcessor(CookieJar()))
            def post(path, form):
                return opener.open(Request(base + path, data=urlencode(form).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=4)
            def denied(path, code, form=None):
                with self.assertRaises(HTTPError) as error:
                    post(path, form) if form is not None else opener.open(base + path, timeout=4)
                self.assertEqual(error.exception.code, code)
                self.assertNotIn(b"Laptop stand", error.exception.read())
            try:
                denied("/api/order-status?order_id=DEMO-1001", 401)
                with opener.open(base + "/account", timeout=4) as response:
                    token = re.search('name="token" value="([^"]+)"', response.read().decode())[1]
                with post("/customer/login", {"token": token, "username": "alex", "password": "test-customer-password"}) as response:
                    self.assertIn("Signed in as alex", response.read().decode())
                with opener.open(base + "/api/order-status?order_id=DEMO-1001", timeout=4) as response:
                    self.assertIn(b"shipped", response.read())
                denied("/api/order-status?order_id=DEMO-1003", 404)
                denied("/?order_id=DEMO-1003", 404)
                denied("/ask", 404, {"question": "Track DEMO-1003"})
                denied("/reviews/decide", 401, {"token": token, "request_id": 1, "action": "approve"})
                with post("/customer/submit", {"token": token, "order_id": "DEMO-1002"}) as response:
                    self.assertIn("has not been cancelled", response.read().decode())
                self.assertEqual(reviews.snapshot()[1][0]["actor"], "alex")
                with post("/customer/logout", {"token": token}) as response:
                    self.assertNotIn("Signed in as alex", response.read().decode())
                with post("/customer/login", {"token": token, "username": "sam", "password": "test-second-password"}) as response:
                    self.assertIn("Signed in as sam", response.read().decode())
                with post("/customer/submit", {"token": token, "order_id": "DEMO-1002"}) as response:
                    self.assertIn("No accessible", response.read().decode())
                self.assertEqual(len(reviews.snapshot()[0]), 1)
                denied("/api/order-status?order_id=DEMO-1001", 404)
            finally:
                server.shutdown()
                worker.join()
