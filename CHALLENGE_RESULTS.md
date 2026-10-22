# Challenge evaluation — October 22, 2026

## Procedure

A 22-case authored set was assembled before changing the current routing behavior. It combines new phrasings and scenarios with previously known difficult paraphrases. This is not a fully independent dataset or a statistically representative user sample. Run the fixture-level workflow via `python -m resolveai.evaluate --dataset data/challenge_questions.json --repeat 2`. HTTP ownership checks have separate automated tests.

## Preserved evidence

| Run | Result | Report |
| --- | --- | --- |
| Unchanged routing baseline | 15/22 | [Baseline](reports/evaluation-20261022T164613089057Z.json) |
| Updated routing, two repetitions | 40/44; 20/22 each run | [Updated](reports/evaluation-20261022T164707165325Z.json) |
| Retrieval-only comparison after vocabulary update | Keyword 6/10; semantic fallback 10/10 | [Retrieval](reports/retrieval-20261022T164730327199Z.json) |

Reports preserve individual responses and category totals. Source/dataset hashes distinguish the evaluated versions. Model names are tags, not immutable model artifact digests. Latencies include cold loading when applicable. Once these examples informed changes, the set became tuning/regression data; no held-out accuracy claim is justified.

## Changes and remaining failures

The routing prompt now prioritizes unsupported actions, distinguishes absent policy topics, and supports a clarification outcome for mixed informational requests. The returns vocabulary includes faulty/defective/malfunctioning products. Exact source excerpts and order validation remain application-controlled.

Both repeated runs still failed these cases:

- “Can I stop a purchase before it leaves the warehouse?” was classified unsupported; the expected general cancellation policy was not returned.
- “Track DEMO-1001 and explain the return policy.” returned policy information rather than asking the user to split the request. The tracking component was unanswered.

The baseline also returned a general shipping document for a question about destination countries, although that document contains no supported-country information. The revised router abstains for that question. This relies on model classification, not a guarantee that every unsupported topic is recognized.

## Interpretation

The results demonstrate measured development progress and visible failure analysis. They do not establish production reliability or prove safety against arbitrary prompts. The 18-case original suite and automated tests remain separate regression checks. Next evaluation work should reserve independent examples, test additional model versions and paraphrases, and include grounded-answer completeness rather than only outcomes and source integrity.

## Routing fix verification

A later prompt revision added contrasting examples of general cancellation eligibility, explicit cancellation execution, combined tracking-and-policy requests, and ordinary cancellation rules. The examples use different phrasings and IDs from the challenge questions. These are prompt examples, not model training or fine-tuning.

- Challenge: **44/44 attempts passed**, 22/22 in each of two runs. [Report](reports/evaluation-20261022T165327234840Z.json).
- Original scenarios: **18/18 passed**. [Report](reports/evaluation-20261022T165323295585Z.json).
- Automated regressions: **57 passed** locally.

Both previously documented failures now produce the expected outcomes on these examples: the general eligibility question retrieves the cancellations passage, and the combined request asks the user to split the question. The execution counterexample remains unsupported; chat still cannot cancel orders.

The challenge and original evaluation overlapped in time on one Ollama instance, so these reports' timings can include queueing. Do not use their latency values as a controlled before/after speed comparison. Scores remain development/regression measurements on a tuned set; fresh independent evaluation is still required for broader claims. No public deployment or container-model inference validation was performed during this fix.
