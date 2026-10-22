import unittest

from resolveai.evaluate import passes


class EvaluationTests(unittest.TestCase):
    def test_correct_record_required(self):
        case = {"expected": "found", "order_id": "DEMO-1001", "order_status": "shipped"}
        body = {"outcome": "found", "order": {"order_id": "DEMO-1001", "status": "shipped"}, "source": "demo-orders:DEMO-1001"}
        self.assertTrue(passes(case, 200, body))
        body["order"]["status"] = "delivered"
        self.assertFalse(passes(case, 200, body))

    def test_errors_and_leaked_records_fail(self):
        case = {"expected": "unsupported"}
        self.assertFalse(passes(case, 503, {"outcome": "model_error"}))
        self.assertFalse(passes(case, 200, {"outcome": "unsupported", "order": {}}))
        self.assertTrue(passes(case, 200, {"outcome": "unsupported"}))
