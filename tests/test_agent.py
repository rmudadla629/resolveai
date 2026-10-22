import unittest
from unittest.mock import patch
from urllib.error import URLError

from resolveai.agent import answer_question
from tests.support import IsolatedOrderTestCase


class AgentTests(IsolatedOrderTestCase):
    @patch("resolveai.agent.classify")
    def test_mixed_request_clarifies_without_lookup(self, model):
        model.return_value = {"intent": "clarification", "order_id": "DEMO-1001"}
        with patch("resolveai.agent.answer_order") as lookup:
            status, body = answer_question("Track DEMO-1001 and explain returns")
        self.assertEqual((status, body["outcome"]), (200, "clarification"))
        lookup.assert_not_called()

    @patch("resolveai.agent.classify")
    def test_unknown_policy_has_no_fabricated_citation(self, model):
        model.return_value = {"intent": "policy_missing", "order_id": ""}
        with patch("resolveai.agent.answer_policy") as retrieval:
            status, body = answer_question("Which countries do you ship to?")
        self.assertEqual(body["outcome"], "policy_not_found")
        self.assertNotIn("citations", body)
        retrieval.assert_not_called()
    @patch("resolveai.agent.classify")
    def test_order_lookup_and_missing_record(self, model):
        for order_id, status in [("DEMO-1001", 200), ("DEMO-9999", 404)]:
            model.return_value = {"intent": "order_status", "order_id": order_id}
            actual, body = answer_question(f"Where is my order {order_id}?")
            self.assertEqual(actual, status)
            self.assertEqual(body["mode"], "local_ai")
            self.assertEqual("order" in body, status == 200)

    @patch("resolveai.agent.classify")
    def test_invented_order_is_blocked(self, model):
        model.return_value = {"intent": "order_status", "order_id": "DEMO-1002"}
        status, body = answer_question("Where is DEMO-1001?")
        self.assertEqual(status, 502)
        self.assertNotIn("order", body)

    @patch("resolveai.agent.classify")
    def test_missing_and_multiple_ids(self, model):
        model.return_value = {"intent": "order_status", "order_id": "DEMO-1001"}
        for question in ["Where is my order?", "Track DEMO-1001 and DEMO-1002"]:
            self.assertIn("exactly one", answer_question(question)[1]["message"])

    @patch("resolveai.agent.classify")
    def test_unsupported(self, model):
        model.return_value = {"intent": "unsupported", "order_id": ""}
        self.assertIn("not supported", answer_question("Cancel DEMO-1001")[1]["message"])

    @patch("resolveai.agent.classify")
    def test_failures(self, model):
        for failure in [URLError("offline"), ValueError("bad JSON")]:
            model.side_effect = failure
            self.assertEqual(answer_question("Track DEMO-1001")[0], 503)
        model.side_effect = None
        model.return_value = []
        self.assertEqual(answer_question("Track DEMO-1001")[0], 503)

    @patch("resolveai.agent.classify")
    def test_input_limits(self, model):
        for question in ["", "x" * 1001]:
            self.assertEqual(answer_question(question)[0], 400)
        model.assert_not_called()
