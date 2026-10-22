# ResolveAI

An order support application with a Python API and browser interface. Responses are grounded in fictional store records, with a source reference for successful lookups.

## Current capabilities

- Look up shipped, processing, and delivered sample orders.
- Display readable responses through an accessible, responsive order lookup form.
- Handle missing and unknown IDs without inventing order details.
- Provide a JSON API for future tool integrations.

This version uses deterministic lookup logic. LLM integration, policy retrieval, and action approval workflows are planned. There is no customer authentication; use only fictional data on localhost. The standard-library HTTP server is intended for local development.

## Quick start

Requires Python 3.12. No external packages or API keys are needed.

```sh
python3 -m venv .venv
.venv/bin/python -m resolveai
```

Open http://127.0.0.1:8000/ and enter `DEMO-1001`, `DEMO-1002`, or `DEMO-1003`. Try `DEMO-9999` to check the unknown-order response. Stop the service with Control-C. Restart the service after changing code.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Order lookup interface |
| `GET /api/order-status?order_id=DEMO-1001` | JSON order response |
| `GET /health` | Service health |

The order API returns HTTP 200 for a match, 400 for a missing ID, and 404 for an unknown order. The browser form returns a page explaining the result.

## Architecture

Browser form → HTTP handler → order lookup tool → fictional JSON records.

- `resolveai/interface.py`: HTML rendering and escaped output.
- `resolveai/__main__.py`: localhost server and request routing.
- `resolveai/orders.py`: order retrieval and grounded response construction.
- `data/orders.json`: fictional sample records.
- `tests/test_orders.py`: behavioral and HTTP integration checks.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Six tests cover order statuses, input normalization, missing and unknown IDs, HTML escaping, and HTTP responses for the interface and API.

## Development roadmap

1. Model integration with a constrained order lookup tool.
2. Policy retrieval with source citations.
3. Approval workflows for proposed actions.
4. Scenario-based evaluations for correctness, failures, and escalation.
5. Deployment automation and observability.

Keep passwords, tokens, and API keys outside version control.
