import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from resolveai.evaluate import passes
from resolveai import evaluate


class EvaluationTests(unittest.TestCase):
    def test_repetition_and_category_reporting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "resolveai").mkdir()
            (root / "data/policies.json").write_text("[]")
            dataset = root / "cases.json"
            dataset.write_text(json.dumps([{"id": "empty", "question": "", "category": "input", "expected": "invalid_input"}]))
            with patch.object(evaluate, "ROOT", root), patch.object(evaluate, "answer_question", return_value=(400, {"outcome": "invalid_input"})) as answer:
                self.assertEqual(evaluate.run_evaluation(dataset, repeat=2), 0)
                self.assertEqual(answer.call_count, 2)
            report = json.loads(next((root / "reports").glob("*.json")).read_text())
            self.assertEqual(report["categories"]["input"], {"passed": 2, "total": 2})
            self.assertEqual([r["repetition"] for r in report["results"]], [1, 2])
            self.assertEqual(len(report["source_sha256"]), 64)
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
