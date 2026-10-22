import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from resolveai.__main__ import Handler
from resolveai.orders import answer_order
from resolveai.interface import render_page
from tests.support import IsolatedOrderTestCase


class OrderTests(IsolatedOrderTestCase):
    def test_interface_results_and_escaping(self):
        self.assertIn("is shipped", render_page("DEMO-1001").decode())
        self.assertIn("No matching demo order", render_page("DEMO-9999").decode())
        self.assertIn("Please supply", render_page("").decode())
        self.assertNotIn("<script>", render_page('<script>"</script>').decode())
        self.assertNotIn("Order found", render_page().decode())

    def test_known_statuses(self):
        for order_id, expected in [("DEMO-1001", "shipped"), ("DEMO-1002", "processing"), ("DEMO-1003", "delivered")]:
            with self.subTest(order_id=order_id):
                status, body = answer_order(order_id)
                self.assertEqual(status, 200)
                self.assertEqual(body["order"]["status"], expected)
                self.assertIn(expected, body["message"])

    def test_normalization(self):
        self.assertEqual(answer_order(" demo-1001 ")[0], 200)

    def test_unknown_has_no_invented_record(self):
        status, body = answer_order("DEMO-9999")
        self.assertEqual(status, 404)
        self.assertNotIn("order", body)
        self.assertNotIn("source", body)

    def test_blank_requests_order_id(self):
        self.assertEqual(answer_order(" ")[0], 400)

    def test_http_contract(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with patch("resolveai.__main__.answer_question", return_value=(200, {"message": "Your order is shipped.", "mode": "local_ai"})) as agent:
                    request = Request(base + "/ask", data=b"question=Track+DEMO-1001", headers={"Content-Type": "application/x-www-form-urlencoded"})
                    with urlopen(request, timeout=2) as response:
                        self.assertIn("Your order is shipped.", response.read().decode())
                    agent.assert_called_once_with("Track DEMO-1001")
                with urlopen(base + "/?order_id=DEMO-1002", timeout=2) as response:
                    self.assertIn("text/html", response.headers["Content-Type"])
                    self.assertIn("is processing", response.read().decode())
                with urlopen(base + "/api/order-status?order_id=DEMO-1001", timeout=2) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["order"]["status"], "shipped")
                for path, code in [("/api/order-status", 400), ("/api/order-status?order_id=UNKNOWN", 404), ("/missing", 404)]:
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + path, timeout=2)
                    self.assertEqual(error.exception.code, code)
            finally:
                server.shutdown()
                worker.join()
