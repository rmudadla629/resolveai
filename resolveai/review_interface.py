from html import escape

from .reviews import snapshot


def render_reviews(token, message=""):
    requests, events = snapshot()
    rows = ""
    for request in requests:
        actions = ""
        if request["state"] == "pending":
            actions = f'<form method="post" action="/reviews/decide"><input type="hidden" name="token" value="{token}"><input type="hidden" name="request_id" value="{request["id"]}"><button name="action" value="approve">Approve cancellation</button> <button name="action" value="reject">Reject</button></form>'
        rows += f'<li>#{request["id"]} · {escape(request["order_id"])} · <strong>{escape(request["state"])}</strong>{actions}</li>'
    audit = "".join(f'<li>{escape(e["created_at"])} UTC — Request #{e["request_id"]}: {escape(e["event"])}</li>' for e in events)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ResolveAI reviews</title>
<body style="max-width:800px;margin:40px auto;padding:24px;font:18px/1.6 system-ui"><a href="/">Back to support</a><h1>Cancellation review sandbox</h1>
<p>Signed in as the local reviewer. Fictional orders only. Customer accounts are not implemented.</p>
<form method="post" action="/logout"><input type="hidden" name="token" value="{token}"><button>Sign out</button></form>
<p role="status">{escape(message)}</p><h2>Submit a request</h2><p>Only processing demo orders qualify. Submitting does not cancel the order.</p>
<form method="post" action="/reviews/submit"><input type="hidden" name="token" value="{token}"><label for="order">Order ID</label> <input id="order" name="order_id" required placeholder="DEMO-1002"><button>Submit for review</button></form>
<h2>Requests</h2><ul>{rows or '<li>No requests yet.</li>'}</ul><h2>Audit trail</h2><ul>{audit or '<li>No events yet.</li>'}</ul></body></html>'''.encode()
