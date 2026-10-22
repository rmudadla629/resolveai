"""Small keyword retriever with exact source excerpts; no generated policy facts."""

import json
import re
from pathlib import Path
from urllib.error import URLError

from .embeddings import rank

POLICY_PATH = Path(__file__).resolve().parent.parent / "data/policies.json"


def load_policies():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def retrieve(question, method="hybrid"):
    tokens = set(re.findall(r"[a-z]+", question.lower()))
    policies = load_policies()
    ranked = sorted(((len(tokens.intersection(p["keywords"])), p) for p in policies),
                    key=lambda pair: pair[0], reverse=True)
    matches = [p for score, p in ranked if score > 0]
    if method == "keyword" or (method == "hybrid" and matches):
        return matches, "keyword"
    try:
        semantic = rank(question, policies)
        # Abstain unless the best passage is reasonably similar and unambiguous.
        if semantic[0][0] >= .35 and semantic[0][0] - semantic[1][0] >= .06:
            return [semantic[0][1]], "semantic"
        return [], "semantic"
    except (URLError, OSError, ValueError, KeyError, TypeError):
        return matches, "keyword_fallback"


def answer_policy(question):
    matches, method = retrieve(question)
    if not matches:
        return 200, {"mode": "local_ai", "outcome": "policy_not_found",
                     "retrieval_method": method,
                     "message": "I couldn't find a matching policy in the demo documents. Please ask about returns, refunds, shipping, cancellations, or address changes."}
    citations = [{"id": p["id"], "title": p["title"], "excerpt": p["text"],
                  "url": "/policies#" + p["id"]} for p in matches]
    return 200, {"mode": "local_ai", "outcome": "policy", "tool": "search_policies",
                 "retrieval_method": method,
                 "message": "Here are the relevant passages from the demo store policies. These describe general rules, not approval for an individual order.",
                 "citations": citations}
