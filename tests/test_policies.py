import unittest
from unittest.mock import patch

from resolveai.agent import answer_question
from resolveai.interface import render_page, render_policies
from resolveai.policies import answer_policy, load_policies, retrieve
from resolveai.evaluate import passes


class PolicyTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("resolveai.policies.rank", return_value=[(0.1, p) for p in load_policies()])
        self.ranker = patcher.start()
        self.addCleanup(patcher.stop)

    def test_semantic_match_and_abstention(self):
        policies = load_policies()
        self.ranker.return_value = [(0.6, policies[1]), (0.2, policies[0]), (0.1, policies[2])]
        matches, method = retrieve("When will my parcel reach me?")
        self.assertEqual(method, "semantic")
        self.assertEqual(matches[0]["id"], "shipping")
        self.ranker.return_value = [(0.6, policies[0]), (0.58, policies[1]), (0.1, policies[2])]
        self.assertEqual(retrieve("Unclear question")[0], [])

    def test_embedding_failure_falls_back(self):
        self.ranker.side_effect = OSError("offline")
        self.assertEqual(retrieve("no matching words"), ([], "keyword_fallback"))
        matches, method = retrieve("return policy")
        self.assertEqual(method, "keyword")
        self.assertEqual(matches[0]["id"], "returns")

    def test_retrieval_and_citations(self):
        for question, expected in [("What is the return policy?", "returns"), ("How long does shipping take?", "shipping"), ("What are cancellation rules?", "cancellations")]:
            body = answer_policy(question)[1]
            citation = body["citations"][0]
            self.assertEqual(citation["id"], expected)
            policy = next(p for p in load_policies() if p["id"] == expected)
            self.assertEqual(citation["excerpt"], policy["text"])
            self.assertIn('href="/policies#' + expected, render_page(ai_body=body).decode())

    def test_no_match(self):
        body = answer_policy("Do you have a warranty?")[1]
        self.assertEqual(body["outcome"], "policy_not_found")
        self.assertNotIn("citations", body)

    def test_evaluation_rejects_fabricated_excerpt(self):
        body = answer_policy("return policy")[1]
        case = {"expected": "policy", "policy_id": "returns"}
        self.assertTrue(passes(case, 200, body))
        body["citations"][0]["excerpt"] = "Unlimited refunds"
        self.assertFalse(passes(case, 200, body))

    def test_document_anchors(self):
        page = render_policies().decode()
        for policy in load_policies():
            self.assertIn('id="' + policy["id"] + '"', page)

    @patch("resolveai.agent.classify", return_value={"intent": "policy", "order_id": ""})
    def test_policy_routing(self, model):
        self.assertEqual(answer_question("What is your refund policy?")[1]["outcome"], "policy")
