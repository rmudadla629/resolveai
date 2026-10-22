# Run the ResolveAI demo

This walkthrough uses fictional customers, three orders, local Ollama models, and one reviewer. No paid API or real customer data is needed. Local account passwords are chosen by the person running the demo; there are no published default credentials.

## First-time setup on macOS

Requires Python 3.12, Git, and [Ollama](https://ollama.com/download/mac). Keep Ollama running. From Terminal:

```sh
git clone https://github.com/rmudadla629/resolveai.git
cd resolveai
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ollama pull qwen3:4b
ollama pull all-minilm:22m
.venv/bin/python -m resolveai.auth
.venv/bin/python -m resolveai.customers
.venv/bin/python -m resolveai.customers
```

Choose a reviewer password at the first setup prompt. At the customer prompts, create `alex` once and `sam` once. Each password must have at least 12 characters; Terminal hides password input. Do not rerun account creation for existing accounts. Credentials stay in ignored `runtime/` files. Model downloads require internet and several GB of disk space; inference runs locally.

For an existing checkout with accounts configured, skip cloning and account creation. Install requirements if needed, then check setup and start:

```sh
.venv/bin/python -m resolveai.doctor
.venv/bin/python -m resolveai
```

Open http://127.0.0.1:8000/. Keep Terminal and Ollama open. Startup uses Flask and Waitress. Restarting the server ends existing login sessions.

## Five-minute walkthrough

1. Click Customer account and sign in as Alex. View DEMO-1001: shipped. Explain that order facts are read from records, not generated.
2. On the support page, ask “Where is my order DEMO-1001?” Verify the record citation, then follow View request traces. Explain that traces show outcome and processing time, not answer correctness.
3. Ask “How soon will my parcel reach me?” Verify the shipping excerpt, `semantic` method, and clickable document citation. Policy retrieval returns exact excerpts, not generated synthesis.
4. While signed in as Alex, visit `/?order_id=DEMO-1003`. Verify that access is denied without revealing Sam's order details. Sign in as Sam separately to see only DEMO-1003.
5. With fresh demo state, sign in as Alex and submit DEMO-1002 for cancellation from Customer account. The status remains processing until review. Sign in at `/reviews` with the reviewer password and approve the request. Confirm the order becomes cancelled and the audit records the customer submission and reviewer decision.

Customer and reviewer cookies are separate. Signing out of one role does not sign out the other. Customer access never grants reviewer approval permission. If DEMO-1002 was already cancelled, use the reset procedure below before repeating step 5.

## Repeating the demo safely

First preview the affected files; this command makes no changes:

```sh
.venv/bin/python -m resolveai.demo
```

Stop ResolveAI with Control-C in its server tab. Then explicitly reset:

```sh
.venv/bin/python -m resolveai.demo --server-stopped --confirm RESET-DEMO
```

The reset backs up both databases under ignored `runtime/backups/<UTC timestamp>/`, then clears reviews, audit events, status overrides, and request traces. Reviewer/customer credentials, JSON fixtures, and saved evaluation reports are preserved. DEMO-1002 returns to processing. The `--server-stopped` flag is your assertion: the command does not detect other running processes. Do not run a reset while the app is running. Restart the server afterward and sign in again.

Backups remain local and are not automatically deleted. To recover a database, stop ResolveAI, preserve the current database separately, and copy the desired backed-up database to its original runtime path. Backups restore the corresponding historical demo state, not account credentials.

## Verification and limitations

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m resolveai.evaluate
.venv/bin/python -m resolveai.compare_retrieval
```

The automated suite uses temporary databases and mocked models. The live evaluations call Ollama, write reports, and do not reset your demo database. Development benchmark scores are not production accuracy estimates. See ARCHITECTURE.md and PROJECT_REVIEW.md for design choices and known gaps.

This is a localhost demo. Public deployment still needs HTTPS, Secure cookies, shared rate limiting, durable session handling, and operational validation. Do not expose it through a public tunnel as part of this walkthrough.

## Troubleshooting

- Address already in use: another server may still be running; stop it before restarting. Do not kill unrelated processes.
- Sign-in required after restart: expected; sessions are in memory.
- Reviewer/customer already configured: setup preserved your account; use its existing password.
- Model unavailable: keep Ollama open and run the model pull commands above if needed.
- Expected order is cancelled: prior approval was saved. Reset only if you want fresh demo state.
- Yellow Actions icon: refresh the run page and inspect the job rather than pushing again.

## Sign-in retry behavior

If you see “Too many sign-in attempts,” wait the number of seconds shown and try again. Each role endpoint allows five attempts per IP in a 60-second window, including successful sign-ins. This does not delete or lock the account permanently. Existing sessions and non-login pages are unaffected. No need to deliberately enter incorrect passwords for the walkthrough: automated tests verify limits and recovery.
