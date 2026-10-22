# ResolveAI

A portfolio project for learning to build, evaluate, and deploy an AI support agent.

## Status

The first Python API milestone is implemented and tested. It reads fictional order records from JSON and returns grounded status responses. This is deterministic demo logic; no AI model is connected yet. There is no customer authentication, so this service is for local fictional data only.

## Run locally

From this project directory:

```sh
.venv/bin/python -m resolveai
```

Open `http://127.0.0.1:8000/api/order-status?order_id=DEMO-1001` in a browser.
Try `DEMO-1002`, `DEMO-1003`, and an unknown ID too. Press Control-C in the terminal to stop the service.

Run checks with:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Five tests cover known statuses, ID normalization, unknown orders, missing IDs, and actual HTTP responses.

## First milestone

A user asks “Where is my order?”, supplies a sample order ID, and receives an answer grounded in the demo store's order record. Unknown orders must return a clear missing-record response rather than an invented status.

## Implementation stages

1. Build a Python API and fictional order database; verify successful and missing-order lookups.
2. Add a simple support interface and an explicitly labeled deterministic demo mode.
3. Integrate a model with an order lookup tool; keep credentials outside Git.
4. Add policy retrieval with citations and an approval workflow for proposed actions.
5. Create evaluation scenarios for correctness, tool failures, and escalation; measure latency and cost.
6. Add deployment, CI, traces, and a documented architecture.

Complete each stage before expanding scope. Choose paid services only after discussing costs.

## Learning checkpoints

Explain the request flow, trace an order lookup, handle an unknown order, and implement a small feature independently before moving on to complex agent workflows.

## Local environment

Python 3.12 and Git are installed. The local virtual environment is `.venv`.
Activate it with `source .venv/bin/activate` from this directory.

## GitHub

Intended GitHub owner: `rmudadla629`. No remote repository has been connected or code uploaded. Never commit passwords, tokens, or API keys.
