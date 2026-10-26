# ResolveAI

A local AI support application for a fictional store: check orders, retrieve cited policies, and send cancellation requests through reviewer approval.

**[View the screenshot demo](WALKTHROUGH.md)** · [Architecture](ARCHITECTURE.md) · [Evaluation evidence](CHALLENGE_RESULTS.md)

## What it demonstrates

- Local Qwen3 request routing with structured output validation and record-grounded order answers.
- Keyword-first policy retrieval with semantic fallback through all-minilm embeddings, exact excerpts, and source links.
- Separate customer/reviewer sign-in, server-side order ownership checks, and login attempt limits.
- Transactional cancellation approval, duplicate-request protection, and actor-bearing audit events.
- Request metadata tracing, backup/reset utilities, Flask/Waitress serving, and container build/startup CI.

Python controls access, validates model output, and retrieves saved facts. Chat cannot approve cancellations. General policy questions work without customer sign-in; order records require it. This is a constrained workflow with extractive policy answers, not autonomous multi-agent resolution or model fine-tuning.

## Public-hosting preparation

A separate [Streamlit demo](STREAMLIT.md) is prepared with Groq routing, CPU policy embeddings, and visitor-isolated fictional review state. It is not publicly deployed or live-Groq verified yet. Its selectable roles simulate customer/reviewer behavior and do not implement public authentication. Original local evaluation scores do not establish Groq performance.

## Run locally on macOS

Requires Python 3.12, Git, and [Ollama](https://ollama.com/download/mac). Keep Ollama open. From Terminal:

```sh
git clone https://github.com/rmudadla629/resolveai.git
cd resolveai
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ollama pull qwen3:4b
ollama pull all-minilm:22m
```

For a fresh checkout, create a reviewer and two fictional customer accounts. Each command asks for a private password of at least 12 characters; input is hidden.

```sh
.venv/bin/python -m resolveai.auth
.venv/bin/python -m resolveai.customers
.venv/bin/python -m resolveai.customers
```

Use `alex` for the first customer and `sam` for the second. Existing users should skip account creation. Credentials remain in ignored local runtime files; there are no default passwords.

```sh
.venv/bin/python -m resolveai.doctor
.venv/bin/python -m resolveai
```

Open http://127.0.0.1:8000/account. Alex owns DEMO-1001 and DEMO-1002; Sam owns DEMO-1003. Saved cancellations persist between launches. Sessions end when the server restarts. See [demo setup and reset instructions](DEMO.md) or the [container guide](CONTAINERS.md) for alternative setup.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m resolveai.evaluate
.venv/bin/python -m resolveai.evaluate --dataset data/challenge_questions.json --repeat 2
.venv/bin/python -m resolveai.compare_retrieval
```

| Check | Verified result | Scope |
| --- | --- | --- |
| Automated regression suite | 58 test methods | Application behavior, isolated state, mocked AI calls |
| Original live AI scenarios | 18/18 | Local model, authored development cases |
| Challenge routing | Baseline 15/22; final 22/22 in each of two runs | Same tuned development set; 44 attempts, not 44 distinct questions |
| Retrieval-only comparison | Keyword 6/10; semantic fallback 10/10 | Small tuned set and three fictional policy sections |
| GitHub Actions | Regression and container jobs passed | Image build, in-image tests, and HTTP startup; no model downloads |

These are development measurements, not held-out accuracy or production reliability. Preserved reports and failure analysis are linked in [CHALLENGE_RESULTS.md](CHALLENGE_RESULTS.md). The screenshot demo includes the successful CI jobs; later workflow results appear in [GitHub Actions](https://github.com/rmudadla629/resolveai/actions).

## Routes

| Route | Purpose/access |
| --- | --- |
| `/` and `POST /ask` | Support interface; order data scoped to customer identity |
| `/account` | Customer sign-in, owned orders, and cancellation submission |
| `/reviews` | Reviewer sign-in and approval controls |
| `/policies` | Public fictional policy documents |
| `/api/order-status?order_id=DEMO-1001` | Customer-authenticated order JSON |
| `/traces` | Local-only request metadata; currently no sign-in |
| `/health` | HTTP app liveness, not model/database readiness |

The order API returns 401 when signed out, 404 for an inaccessible/missing ID, and 200 for an accessible record.

## Current delivery status

**Working local portfolio prototype with a screenshot demo.** No public application URL or production usage is claimed. Local ARM64 Compose inference is verified: 18/18 live scenarios, real HTTP semantic policy retrieval, and 58 container regression tests. See [container verification evidence](CONTAINERS.md). CI separately covers the application image without model downloads.

Before public deployment: add HTTPS/Secure cookies, shared sessions and limits, authenticated trace access, and operational/load validation. The current single-process app uses in-memory sessions and fixed fictional customer mappings. Models and policies can still be misclassified outside tested examples. No real orders, refunds, customer outcomes, cost savings, or production scale are represented.

## Project guides

- [Screenshot walkthrough](WALKTHROUGH.md): visual demonstration without narration or video.
- [Demo guide](DEMO.md): first-time setup, repeatable flow, backup/reset, and troubleshooting.
- [Operating reference](OPERATIONS.md): configuration, authentication, retrieval, tracing, and limits.
- [Architecture](ARCHITECTURE.md) and [project review](PROJECT_REVIEW.md): design decisions and remaining work.
- [Container setup](CONTAINERS.md): separate model service, persistent volumes, and verification boundaries.
- [Resume material](RESUME.md) and [interview guide](INTERVIEW_GUIDE.md): concise claims with supporting evidence.
- [Optional video script](DEMO_SCRIPT.md): available if a narrated recording is added later; no video exists yet.
