# ResolveAI: three-minute walkthrough

Audience: an engineer evaluating a portfolio project. This script presents a local working prototype, not a production deployment. Rehearse it and use your own wording. The video has not been recorded yet.

## Before recording

1. Follow DEMO.md and confirm that Ollama and ResolveAI are running.
2. If you want to demonstrate a new cancellation, preview the reset, stop the server, and use the documented confirmed reset. This preserves credentials and backs up review/trace history. Restart afterward. Do not reset during recording.
3. Sign in as Alex and the reviewer before recording. Customer and reviewer sessions are separate. Keep account passwords, personal browser tabs, notifications, and Terminal credentials out of the recording.
4. Prepare tabs for support, customer account, reviewer controls, challenge results, and GitHub Actions. Ask one warm-up policy question to reduce model loading delay.
5. Check that DEMO-1002 is processing before demonstrating cancellation. If you keep its previously cancelled state instead, describe the existing audit trail rather than claiming a new cancellation.

## Recording script

| Time | Show | Suggested narration |
| --- | --- | --- |
| 0:00–0:20 | Support page | “ResolveAI is a local support application that answers order questions, retrieves cited store policies, and routes cancellation requests through manual review. It uses Python, Flask, local models through Ollama, and SQLite.” |
| 0:20–0:50 | Ask “Where is my order DEMO-1001?” | “The model identifies the request and order ID. Python checks customer ownership and reads the actual demo record. The response uses the record rather than asking the model to invent a status.” |
| 0:50–1:15 | Ask “How soon will my parcel reach me?”; open citation | “Policy retrieval uses keywords first and embeddings when keywords don't match. This question uses semantic search. The response quotes the source passage, and the citation opens the document.” |
| 1:15–1:35 | As Alex, open `/?order_id=DEMO-1003` | “Sam owns this order, so Alex cannot retrieve its details. These checks apply to the order page, API, AI workflow, and customer cancellation submission.” |
| 1:35–2:15 | Alex submits DEMO-1002; reviewer approves; check status | “Submission creates a pending request without changing the order. Approval rechecks that the order is still processing. The transaction records a cancellation and an audit event. Chat itself cannot perform this action.” |
| 2:15–2:35 | Follow a response trace link | “Request traces show outcomes, tools, search methods, and processing time. They exclude question and answer text. A successful HTTP response alone does not establish answer accuracy.” |
| 2:35–3:00 | Challenge report and green CI jobs | “The challenge set improved from 15 of 22 to 22 of 22 in two repeated runs after routing changes. Those are development examples, not production accuracy. CI checks the regression suite and container build/startup. Local ARM64 Docker inference has also been checked. Public hosting remains unfinished.” |

The times are a rehearsal target, not a measured performance promise. Allow model responses to finish; if needed, trim idle time without hiding errors or implying faster measured latency. Use the links in CHALLENGE_RESULTS.md for actual evidence rather than typing a result manually.

## Finish and share

Review the recording for visible credentials and personal information. Verify that every demonstrated status change actually occurred. Keep the final video to roughly three minutes and add its link to README.md only after recording and reviewing it. There is currently no video URL or public app URL.
