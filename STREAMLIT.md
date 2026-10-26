# ResolveAI: free hosted-demo preparation

Status: deployed at **[resolveai-rmudadla629.streamlit.app](https://resolveai-rmudadla629.streamlit.app/)**. Live browser smoke checks verified a record-grounded order response and a shipping paraphrase with semantic retrieval. No full Groq quality evaluation has been performed. The original password-protected Flask/Ollama app remains available unchanged in behavior; the Streamlit version is a deliberately labeled fictional simulation.

## What changes in this version

| Local application | Public Streamlit demo |
| --- | --- |
| Qwen3 through local Ollama | Groq `openai/gpt-oss-20b`, strict JSON routing |
| Ollama embeddings | FastEmbed CPU MiniLM, keyword-first semantic fallback |
| Password-protected customer/reviewer accounts | Selectable fictional roles; explicitly not authentication |
| Shared transactional SQLite | Independent session-memory orders, requests, and audit events |
| Native tracing and durable local history | No durable public history; no prompts or credentials intentionally logged |

Routing returns an intent and a supplied order ID. Python checks the ID against user input and the selected demo identity, then returns exact record facts or policy excerpts. No generated SQL/code executes and chat never changes orders. The original cancellation policy excerpt is preserved; its reference to the local sandbox describes the original app. The hosted simulator changes only fictional session records.

The embedding model is pinned to `Qdrant/all-MiniLM-L6-v2-onnx` revision `d13954661f83248295ba75c1ed411eef3b7b936e`, accessed through FastEmbed 0.9.0. Its local embeddings are not claimed identical to Ollama's. First semantic search downloads the public model; no Hugging Face key or paid embedding API is needed. Known keyword matches use lexical retrieval; semantic fallback abstains below 0.35 similarity or 0.06 top-two margin.

## Preview locally

From this repository with Python 3.12:

```sh
.venv/bin/python -m pip install -r cloud/requirements.txt
.venv/bin/streamlit run cloud/app.py
```

Without secrets, the app explicitly disables AI while retaining direct lookup, policy reading, and the review simulator. Those deterministic features are not labeled AI. It never contacts local Ollama or reads local customer passwords or SQLite records.

## Keep AI on the free plan

1. Sign in to your existing Groq account at https://console.groq.com/.
2. Confirm the account/organization is on the **Free** plan. Do not upgrade, add paid credits, or enter billing details.
3. Create a dedicated key for this demo if available. Keep it private; do not send it in chat or commit it.
4. In Streamlit's private app secrets, set:

```toml
GROQ_API_KEY = "YOUR_PRIVATE_KEY_HERE"
GROQ_FREE_PLAN_CONFIRMED = true
```

The second setting is your confirmation, not an automated billing check: the application cannot inspect plan/billing status. Calls use only `api.groq.com`, never a paid-provider fallback. A 429 response stops the request and displays a quota message. No automatic retries are made.

The app bounds input at 1,000 characters and output at 1,024 tokens, allows 20 AI attempts per visitor session, and adds a shared 100-attempt UTC-day process cap with a three-second spacing rule. Failed attempts count. These are modest resource bounds, not durable quotas or full abuse prevention: process restarts reset the shared count, and new sessions reset the session count. Provider free quotas still apply and may be exhausted. Free-plan hosting/AI availability is not guaranteed.

Your submitted question goes to Groq for routing, including any fictional order ID typed into it. No raw order database, customer password, or review history is sent. Use fictional questions only. Host and provider policies apply.

## Deploy after checks pass

In Streamlit Community Cloud create a new app from `rmudadla629/resolveai`, branch `main`, main file **`cloud/app.py`**, Python **3.12**. Community Cloud should use the adjacent `cloud/requirements.txt`. Set the private secrets above only after checking the free plan. Do not modify Retail Lens AI or InspectAI.

A missing key, missing free-plan confirmation, quota error, model failure, or embedding failure is shown honestly. The owner key is never exposed as a UI field. No local runtime directory or credentials should be uploaded.

## Verification checklist

After private setup, test actual Groq routing rather than relying on the mocked provider tests:

- Select alex; ask `Where is my order DEMO-1001?` → shipped, exact source.
- As alex, ask about DEMO-1003 → no accessible order. Switch to sam → delivered.
- Ask about return rules → exact source passage. Try a shipping paraphrase → cited shipping policy.
- Ask about gift wrapping or warranty → no fabricated policy.
- Ask to cancel an order → AI declines to execute it.
- Submit DEMO-1002 in the simulator → pending, order still processing. Simulate reviewer approval → cancelled.
- Open a separate browser session → DEMO-1002 is still processing there. Role selection within a session is a simulation, not real access control.
- Test quota/provider failure messaging and inspect secrets are absent from source/log output.

The existing local Qwen3 evaluation results do not transfer to Groq. Re-run relevant development questions with the new model and document failures before claiming equivalent quality. Live Groq order and semantic-policy smoke checks subsequently passed through the public browser interface; they do not establish equivalent quality across the full development datasets.

## Evidence so far

[Hosted retrieval report](reports/hosted-retrieval.json): 10/10 on the same small authored development retrieval set. This is not independent validation, broad retrieval accuracy, or an end-to-end Groq score. Software tests verify payload structure, provider errors, ID validation, ownership checks, isolated state, explicit approval, and Streamlit interaction without external model calls. Models and the runtime cache stay excluded from Git.

Official references: [Groq structured outputs](https://console.groq.com/docs/structured-outputs), [Groq free quotas](https://console.groq.com/docs/rate-limits), [FastEmbed](https://qdrant.tech/documentation/embeddings/fastembed/), [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud).

## Additional public boundary checks

In the deployed browser session, alex asking about DEMO-1003 returned “No accessible demo order was found.” A chat request to cancel DEMO-1002 was declined, and a subsequent direct lookup confirmed the order remained processing. Together with the known-order and semantic-policy checks, these are four functional smoke scenarios, not a comprehensive security audit or a rerun of the full Groq development benchmark.
