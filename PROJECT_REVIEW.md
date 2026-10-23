# ResolveAI repository review — October 22, 2026

## Current assessment

Working local portfolio prototype with a screenshot walkthrough, documented setup, evaluations, and CI. Public deployment and production readiness are not established. A video is optional and has been replaced by the screenshot demo for the current presentation.

## Verified scope

Customer/reviewer sign-in, fixed fictional ownership checks, record-grounded order answers, cited policy retrieval with semantic fallback, manual transactional cancellation review, audit actors, request metadata, login limits, demo backup/reset, and Flask/Waitress serving are implemented. There are 58 automated test methods. The repository's regression and container jobs have passed; see the [captured CI checks](docs/screenshots/06-ci-checks.png) and current runs in GitHub Actions.

## Measured development results

| Check | Result | Evidence |
| --- | --- | --- |
| Original live workflow set | 18/18 | [Report](reports/evaluation-20261022T165323295585Z.json) |
| Challenge before routing fixes | 15/22 | [Baseline](reports/evaluation-20261022T164613089057Z.json) |
| Final challenge, two repetitions | 22/22 each; 44/44 attempts | [Report](reports/evaluation-20261022T165327234840Z.json) |
| Retrieval comparison after vocabulary changes | Keyword 6/10; semantic fallback 10/10 | [Report](reports/retrieval-20261022T164730327199Z.json) |

The sets are authored development data, some of which informed fixes. Repeated attempts are not distinct cases. Retrieval-only measurement bypasses intent routing; the workflow evaluations bypass HTTP customer sign-in and use fixture-level access. Automated HTTP tests cover permissions separately. These results do not establish production accuracy, general safety, load capacity, business impact, or cost savings. The final challenge and original runs overlapped, so their timings cannot support a controlled speed comparison.

## Failure history

Earlier iterations missed a faulty-product policy question, declined general cancellation eligibility, and partially answered mixed tracking/policy requests. Vocabulary and prompt changes corrected those examples on the development sets. Preserved baseline reports remain linked in [CHALLENGE_RESULTS.md](CHALLENGE_RESULTS.md). New phrasings may still fail; these fixes do not eliminate the need for independent evaluation.

## Remaining work

| Area | Current limitation | Required verification/change |
| --- | --- | --- |
| Public access | Local HTTP cookies and in-memory sessions/limits | HTTPS/Secure cookies, shared storage, trusted proxy policy |
| Trace access | Metadata page has no sign-in | Reviewer-only access before public exposure |
| Container inference | ARM64 local run passed 58 tests, 18 live cases, and an HTTP semantic-policy request; CI remains model-free | Broader challenge/capacity testing and intended hosting validation |
| Operational readiness | No demonstrated load capacity or model/database readiness probe | Capacity, dependency health, recovery, and deployment validation |
| Account lifecycle | Fictional fixed mappings, no password recovery or multiple reviewers | Decide and implement requirements for any real use |
| Evaluation | Small tuned datasets; model tags not immutable provenance | Independent questions, model digests, completeness/quality evaluation |

## Documentation review changes

The main README now includes complete account setup, current public API response codes, a concise evidence table, and an explicit local-prototype status. The detailed reference is in OPERATIONS.md. Completed work was removed from remaining-work lists. Screenshots are captioned according to visible evidence; the cancellation image shows approval, not the audit trail. Older UI/sample labels are identified as historical. Resume claims match the implemented scope.

No real store integration, actual refunds, production users, autonomous multi-agent system, generated policy synthesis, custom model training, or public hosted application is claimed.

## Local container verification follow-up

See [CONTAINERS.md](CONTAINERS.md) and `reports/container-arm64/`. Local ARM64 Compose inference is verified within the stated scenarios. No native credentials were copied or persistent container accounts created. Models and state use separate Docker volumes. The app binds only localhost port 8001 and Ollama has no published host port. Public hosting remains unfinished.
