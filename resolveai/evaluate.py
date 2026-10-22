"""Run the small development benchmark against local Ollama."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .agent import answer_question

ROOT = Path(__file__).resolve().parent.parent


def passes(case, status, body):
    expected = case["expected"]
    expected_http = 404 if expected == "not_found" else 200
    if body.get("outcome") != expected or status != expected_http:
        return False
    if expected == "found":
        order = body.get("order", {})
        return (order.get("order_id") == case["order_id"]
                and order.get("status") == case["order_status"]
                and body.get("source") == f'demo-orders:{case["order_id"]}')
    return "order" not in body and "source" not in body


def main():
    dataset = (ROOT / "data/eval_questions.json").read_bytes()
    cases = json.loads(dataset)
    results = []
    for case in cases:
        start = perf_counter()
        status, body = answer_question(case["question"])
        row = {**case, "passed": passes(case, status, body), "http_status": status,
               "response": body, "latency_seconds": round(perf_counter() - start, 3)}
        results.append(row)
        print(f'{"PASS" if row["passed"] else "FAIL"} {case["id"]}: {body.get("outcome")} ({row["latency_seconds"]}s)', flush=True)
    latencies = sorted(row["latency_seconds"] for row in results)
    passed = sum(row["passed"] for row in results)
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "model": "qwen3:4b",
              "dataset_sha256": hashlib.sha256(dataset).hexdigest(),
              "limitations": "Small development set, one run per case; not a held-out or production reliability estimate. Latency includes model loading if cold.",
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


if __name__ == "__main__":
    raise SystemExit(main())
