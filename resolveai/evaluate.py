"""Run the small development benchmark against local Ollama."""

import hashlib
import argparse
import json
import math
import tempfile
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .agent import answer_question
from .policies import load_policies

ROOT = Path(__file__).resolve().parent.parent


def passes(case, status, body):
    expected = case["expected"]
    expected_http = {"not_found": 404, "invalid_input": 400}.get(expected, 200)
    if body.get("outcome") != expected or status != expected_http:
        return False
    if expected == "policy":
        citations = body.get("citations", [])
        policies = {p["id"]: p for p in load_policies()}
        return (case["policy_id"] in [c.get("id") for c in citations]
                and all(c.get("id") in policies and c.get("excerpt") == policies[c["id"]]["text"]
                        and c.get("url") == "/policies#" + c["id"] for c in citations)
                and "order" not in body)
    if expected == "found":
        order = body.get("order", {})
        return (order.get("order_id") == case["order_id"]
                and order.get("status") == case["order_status"]
                and body.get("source") == f'demo-orders:{case["order_id"]}')
    return "order" not in body and "source" not in body and "citations" not in body


def run_evaluation(dataset_path=None, repeat=1):
    dataset_path = Path(dataset_path) if dataset_path else ROOT / "data/eval_questions.json"
    dataset = dataset_path.read_bytes()
    cases = json.loads(dataset)
    if not cases or not 1 <= repeat <= 5:
        raise ValueError("Use a nonempty dataset and 1–5 repetitions.")
    results = []
    for index, case in enumerate(cases * repeat):
        start = perf_counter()
        status, body = answer_question(case["question"])
        row = {**case, "repetition": index // len(cases) + 1, "passed": passes(case, status, body), "http_status": status,
               "response": body, "latency_seconds": round(perf_counter() - start, 3)}
        results.append(row)
        print(f'{"PASS" if row["passed"] else "FAIL"} {case["id"]}: {body.get("outcome")} ({row["latency_seconds"]}s)', flush=True)
    latencies = sorted(row["latency_seconds"] for row in results)
    passed = sum(row["passed"] for row in results)
    categories = {}
    for row in results:
        category = row.get("category", "development")
        group = categories.setdefault(category, {"passed": 0, "total": 0})
        group["total"] += 1
        group["passed"] += int(row["passed"])
    source_hash = hashlib.sha256()
    for source in sorted((ROOT / 'resolveai').glob('*.py')):
        source_hash.update(source.name.encode() + source.read_bytes())
    source_hash.update((ROOT / 'data/policies.json').read_bytes())
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "model": "qwen3:4b",
              "dataset_name": dataset_path.name, "repetitions": repeat,
              "source_sha256": source_hash.hexdigest(), "categories": categories,
              "dataset_sha256": hashlib.sha256(dataset).hexdigest(),
              "limitations": "Small authored dataset; after inspecting or tuning on results it is a development set, not held-out. Repetitions do not create new independent cases. Fixture-level workflow evaluation, not HTTP authentication or production reliability. Latency includes cold loading if applicable.",
              "summary": {"passed": passed, "total": len(results), "pass_rate": passed / len(results),
                          "mean_latency_seconds": round(sum(latencies) / len(latencies), 3),
                          "p95_latency_seconds": latencies[math.ceil(.95 * len(latencies)) - 1]},
              "results": results}
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    path = output / ("evaluation-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f'{passed}/{len(results)} passed. Report: {path}', flush=True)
    return 0 if passed == len(results) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path)
    parser.add_argument('--repeat', type=int, choices=range(1, 6), default=1)
    args = parser.parse_args(argv)
    # Evaluate the fixed order fixtures, independent of manual review activity.
    with tempfile.TemporaryDirectory() as directory:
        with patch("resolveai.reviews.DB_PATH", Path(directory) / "reviews.sqlite3"):
            return run_evaluation(args.dataset, args.repeat)


if __name__ == "__main__":
    raise SystemExit(main())
