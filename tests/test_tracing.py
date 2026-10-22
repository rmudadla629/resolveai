import sqlite3
import unittest
from unittest.mock import patch

from tests.support import IsolatedOrderTestCase
from resolveai import tracing


class TraceTests(IsolatedOrderTestCase):
    def test_metadata_saved_without_customer_content(self):
        status, body = tracing.traced_answer("secret customer question", lambda q: (200, {"message": "private answer", "outcome": "found", "tool": "lookup_order"}))
        self.assertEqual(status, 200)
        self.assertTrue(body["trace_saved"])
        db = tracing.connect()
        try:
            row = dict(db.execute("SELECT * FROM traces").fetchone())
        finally:
            db.close()
        self.assertEqual(row["id"], body["trace_id"])
        self.assertEqual(row["tool"], "lookup_order")
        self.assertNotIn("secret customer", str(row))
        self.assertNotIn("private answer", str(row))
        self.assertIn(body["trace_id"], tracing.render_traces().decode())

    def test_exception_is_recorded_without_details(self):
        def broken(q):
            raise ValueError("private failure")
        status, body = tracing.traced_answer("question", broken)
        self.assertEqual(status, 500)
        self.assertEqual(body["outcome"], "internal_error")
        self.assertNotIn("private failure", tracing.render_traces().decode())

    @patch("resolveai.tracing.record", side_effect=sqlite3.OperationalError("locked"))
    def test_trace_failure_preserves_answer(self, recorder):
        status, body = tracing.traced_answer("question", lambda q: (200, {"message": "answer"}))
        self.assertEqual(status, 200)
        self.assertEqual(body["message"], "answer")
        self.assertFalse(body["trace_saved"])

    def test_retention(self):
        for i in range(1001):
            tracing.record(str(i), 200, {"outcome": "found"}, 1)
        db = tracing.connect()
        try:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM traces").fetchone()[0], 1000)
            self.assertIsNone(db.execute("SELECT id FROM traces WHERE id='0'").fetchone())
        finally:
            db.close()
