# ResolveAI resume material

Project: **ResolveAI — Local AI Support Application**  
Repository: https://github.com/rmudadla629/resolveai  
Stack: Python, Flask, Waitress, Ollama, Qwen3, sentence embeddings, SQLite, Docker Compose, GitHub Actions.

Use these bullets when you can explain and modify the corresponding components. Choose two or three; do not copy every bullet into a resume. This is a portfolio project, not employment history.

## Suggested bullets

- Built a local AI support application with schema-constrained request routing, record-grounded order responses, keyword-first policy retrieval with semantic fallback, and clickable source citations.
- Implemented customer order ownership checks and a reviewer approval workflow with transactional SQLite state updates, duplicate pending-request protection, audit events, and login attempt limits.
- Improved an authored 22-case routing development benchmark from 15/22 to 22/22 across two repeated runs; preserved response reports and added automated regression and container build/startup checks in GitHub Actions.

Optional engineering-focused alternative:

- Added request metadata tracing, confirmed demo resets with database backups, pinned Python dependencies, and a non-root container setup with private model-service networking and persistent volumes.

## Evidence and wording boundaries

The final routing score is 44 successful attempts over two repetitions of the same 22 questions, not 44 distinct questions. The set informed the fixes, so describe it as a development benchmark. [Evaluation evidence](CHALLENGE_RESULTS.md).

The final retrieval-only development comparison scored keyword search 6/10 and semantic fallback 10/10. It used a small tuned corpus of three fictional policy sections. Do not describe that as general search accuracy or compare it with an earlier baseline whose vocabulary changed without explaining the change.

The repository currently contains 58 automated test methods; counts will change. AI calls are mocked in CI. Container CI verifies the app image, regression tests, and HTTP startup; full local ARM64 Compose inference was separately verified with 18 live scenarios and an HTTP policy request (see CONTAINERS.md). The presentation includes a [screenshot walkthrough](WALKTHROUGH.md); no public app deployment or recorded video has been verified.

Avoid claims of production scale, real customers, business cost savings, cloud deployment, custom model training/fine-tuning, autonomous multi-agent resolution, or complete security. They are not established by this project. Describe your contribution truthfully and be candid about development assistance if asked.
