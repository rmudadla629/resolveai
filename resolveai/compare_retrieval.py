"""Compare keyword baseline with keyword-first semantic fallback."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .policies import retrieve
from .embeddings import MODEL


def main():
    root = Path(__file__).resolve().parent.parent
    raw = (root / "data/retrieval_questions.json").read_bytes()
    results = []
    for case in json.loads(raw):
        for method in ("keyword", "hybrid"):
            start = perf_counter()
            matches, actual = retrieve(case["question"], method)
            predicted = matches[0]["id"] if matches else None
            results.append({**case, "method": method, "actual_method": actual,
                            "predicted": predicted, "passed": predicted == case["expected"],
                            "latency_seconds": round(perf_counter() - start, 4)})
    # Missing embeddings must not silently count as a semantic comparison.
    if any(r["actual_method"] == "keyword_fallback" for r in results):
        raise SystemExit("Embedding service unavailable: start Ollama and pull " + MODEL)
    summary = {method: {"passed": sum(r["passed"] for r in results if r["method"] == method),
                        "total": len(results) // 2} for method in ("keyword", "hybrid")}
    report = {"model": MODEL, "dataset_sha256": hashlib.sha256(raw).hexdigest(),
              "limitations": "Small development set used while implementing thresholds, not held-out evaluation. Keyword-first routing; exact excerpts, no generated synthesis.",
              "summary": summary, "results": results}
    output = root / "reports"
    output.mkdir(exist_ok=True)
    path = output / ("retrieval-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    print(path, flush=True)


if __name__ == "__main__":
    main()
