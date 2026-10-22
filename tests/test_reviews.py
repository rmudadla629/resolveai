import tempfile
import unittest
import threading
import re
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
from pathlib import Path
from unittest.mock import patch

from resolveai import reviews
from resolveai.orders import lookup_order
from resolveai.__main__ import Handler


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = patch.object(reviews, "DB_PATH", Path(self.directory.name) / "test.sqlite3")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_approval_and_duplicate_decision(self):
        self.assertIn("has not been cancelled", reviews.submit("DEMO-1002"))
        self.assertEqual(lookup_order("DEMO-1002")["status"], "processing")
        self.assertIn("already pending", reviews.submit("DEMO-1002"))
        self.assertIn("approved", reviews.decide(1, "approve"))
        self.assertEqual(lookup_order("DEMO-1002")["status"], "cancelled")
        self.assertIn("already been reviewed", reviews.decide(1, "reject"))
        requests, audit = reviews.snapshot()
        self.assertEqual(len(requests), 1)
        self.assertEqual([e["event"] for e in audit], ["approved", "submitted"])

    def test_rejection_leaves_order_unchanged(self):
        reviews.submit("DEMO-1002")
        reviews.decide(1, "reject")
        self.assertEqual(lookup_order("DEMO-1002")["status"], "processing")

    def test_ineligible_and_unknown(self):
        for order in ("DEMO-1001", "DEMO-1003", "UNKNOWN"):
            reviews.submit(order)
        self.assertEqual(reviews.snapshot(), ([], []))

    def test_recheck_before_approval(self):
        reviews.submit("DEMO-1002")
        db = reviews.connect()
        with db:
            db.execute("INSERT INTO overrides VALUES ('DEMO-1002', 'shipped')")
        db.close()
        self.assertIn("blocked", reviews.decide(1, "approve"))
        self.assertEqual(lookup_order("DEMO-1002")["status"], "shipped")

    def test_review_http_token_and_submission(self):
        patcher = patch("resolveai.__main__.auth.authorized", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/reviews", timeout=2) as response:
                    page = response.read().decode()
                token = re.search('name="token" value="([^"]+)"', page)[1]
                for value, expected in [("bad-token", 403), (token, 200)]:
                    request = Request(base + "/reviews/submit", data=urlencode({"token": value, "order_id": "DEMO-1002"}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
                    if expected == 403:
                        with self.assertRaises(HTTPError) as error:
                            urlopen(request, timeout=2)
                        self.assertEqual(error.exception.code, 403)
                    else:
                        with urlopen(request, timeout=2) as response:
                            self.assertIn("has not been cancelled", response.read().decode())
                self.assertEqual(len(reviews.snapshot()[0]), 1)
            finally:
                server.shutdown()
                worker.join()
