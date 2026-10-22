"""Small keyword retriever with exact source excerpts; no generated policy facts."""

import json
import re
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parent.parent / "data/policies.json"


def load_policies():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def answer_policy(question):
    tokens = set(re.findall(r"[a-z]+", question.lower()))
    ranked = sorted(((len(tokens.intersection(p["keywords"])), p) for p in load_policies()),
                    key=lambda pair: pair[0], reverse=True)
    matches = [p for score, p in ranked if score > 0]
    if not matches:
        return 200, {"mode": "local_ai", "outcome": "policy_not_found",
                     "message": "I couldn't find a matching policy in the demo documents. Please ask about returns, refunds, shipping, cancellations, or address changes."}
    citations = [{"id": p["id"], "title": p["title"], "excerpt": p["text"],
                  "url": "/policies#" + p["id"]} for p in matches]
    return 200, {"mode": "local_ai", "outcome": "policy", "tool": "search_policies",
                 "message": "Here are the relevant passages from the demo store policies. These describe general rules, not approval for an individual order.",
                 "citations": citations}
