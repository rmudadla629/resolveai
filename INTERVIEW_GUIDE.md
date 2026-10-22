# ResolveAI interview preparation

Practise explaining the system in your own words. Use the code and saved reports to check your answers; memorizing these paragraphs does not demonstrate ownership.

## Thirty-second introduction

“ResolveAI is a local support application for a fictional store. A local model routes questions, Python checks order access and retrieves records or policy passages, and a separate reviewer approves cancellation requests. I evaluated routing failures, preserved before-and-after reports, and added regression tests, request tracing, and container CI. It is a working prototype with explicit deployment limitations.”

## Questions to prepare

**How does a question reach an answer?**  
Flask receives the form, the customer scope is checked, and Qwen3 classifies intent and extracts an ID using structured output. Python validates the decision. Order responses use stored records; policy responses use exact retrieved excerpts. The response has a trace ID. Inspect `web.py`, `agent.py`, and `orders.py`.

**What does the model control?**  
It proposes routing and ID extraction, which can be wrong. Application code controls ownership, accepted output values, source retrieval, and state changes. Chat cannot approve a cancellation. Structured JSON improves parseability but does not prove semantic correctness.

**Is this RAG?**  
It demonstrates retrieval and grounded responses. Policy results are extractive, not model-generated synthesis. Keywords take priority; otherwise local all-minilm embeddings rank three policy sections by cosine similarity. A score and ranking margin control abstention. There is no weighted hybrid ranking, vector database, or large-document ingestion pipeline.

**Why use exact excerpts?**  
They make source verification straightforward and avoid generated policy details. The tradeoff is less conversational answers and limited handling of personalized questions. General policy excerpts do not prove that a particular customer qualifies for a refund.

**How is access enforced?**  
Alex and Sam have fixed server-side order mappings and separate customer sessions from reviewer sessions. HTTP and workflow checks prevent access to another customer's records. Passwords use salted PBKDF2 hashes. Login windows limit attempts. Local cookies lack production HTTPS protections; shared session/rate-limit storage remains unfinished.

**What happens during cancellation?**  
Submitting a request leaves the order unchanged. A reviewer decision rechecks eligibility. SQLite transactions persist state overrides, request decisions, and audit events. A unique index prevents duplicate pending requests; a completed request cannot be decided again. Older audit records are marked legacy rather than assigned a fabricated actor.

**What failed, and how was it fixed?**  
The broader 22-case development set initially passed 15 cases. Routing confused cancellation eligibility with execution and partially answered combined requests. Clearer priorities and contrasting prompt examples corrected the documented failures on that set. Final runs passed 22/22 twice; this is not held-out accuracy or proof against arbitrary prompts. See CHALLENGE_RESULTS.md.

**What do tests and CI establish?**  
Automated tests cover routing guard behavior, source integrity, ownership, transactions, authentication, limits, backup/reset, and server behavior using temporary state and mocked models. Separate local runs test real model behavior. Container CI builds the image, tests inside it, and checks HTTP startup. None of these alone establishes load capacity or production readiness.

**What does observability show?**  
The trace page shows request outcomes, HTTP status, tools, search method, and overall workflow duration. It excludes prompt/answer text. There are no model-level spans, token counters, or measured cost savings. HTTP success is not answer correctness.

**What would you improve next?**  
Use an independent evaluation set, test model versions, improve multi-intent handling, and evaluate retrieval negatives. Before public deployment, add HTTPS/Secure cookies, shared sessions and limits, operational validation, and complete container inference checks. Scaling a three-document prototype requires measured decisions about ingestion, indexing, and storage.

## Hands-on ownership checks

1. Draw the request flow without looking at the diagram, then compare it with ARCHITECTURE.md.
2. Explain why pending review does not change an order and find the eligibility recheck in code.
3. Add one new evaluation question with its expected outcome; run it and explain a failure honestly.
4. Find where cross-customer order access is blocked and explain why hiding a link alone is insufficient.
5. Explain one retrieval threshold tradeoff and why lowering it can increase false matches.
6. Make a small code change in a branch, run relevant tests, and explain the diff before merging.

## First practice task

In three sentences, explain which parts of ResolveAI use AI, which parts use deterministic code, and why that separation matters. Then trace “Where is my order DEMO-1001?” through the code. Do not proceed to claiming interview readiness until you can answer follow-up questions and make a small change yourself.
