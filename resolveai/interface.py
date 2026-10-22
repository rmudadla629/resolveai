"""Server-rendered order lookup page."""

from html import escape

from .orders import answer_order, lookup_order
from .customers import OWNERSHIP
from .policies import load_policies


def render_policies():
    sections = "".join(f'<section id="{escape(p["id"], quote=True)}"><h2>{escape(p["title"])}</h2><p>{escape(p["text"])}</p></section>' for p in load_policies())
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ResolveAI policies</title><body style="max-width:760px;margin:40px auto;padding:24px;font:18px/1.6 system-ui"><a href="/">Back to support</a><h1>Demo store policies</h1><p>Fictional policies for testing ResolveAI.</p>' + sections + '</body></html>').encode()


def render_page(order_id: str | None = None, question: str = "", ai_body: dict | None = None, username=None) -> bytes:
    account_label = f"Signed in as {escape(username)}" if username else "Customer sign-in"
    guidance = ("You can check your orders below. Policy questions do not require sign-in." if username
                else 'For order details, <a href="/account">sign in to your customer account</a>. You can ask policy questions without signing in.')
    examples = []
    for sample_id in OWNERSHIP.get(username, ()):
        sample = lookup_order(sample_id)
        if sample:
            examples.append(f'<a href="/?order_id={sample_id}">{sample_id}</a> ({escape(sample["status"])})')
    example_text = "Your orders: " + ", ".join(examples) if examples else 'Sign in to see your demo orders. Alex and Sam have separate fictional accounts.'
    result = ""
    if order_id is not None:
        status, body = answer_order(order_id)
        heading = "Order found" if status == 200 else "Check your order ID"
        source = f'<p class="source">Source: {escape(body["source"])}</p>' if "source" in body else ""
        result = f'<section class="result" role="status"><h2>{heading}</h2><p>{escape(body["message"])}</p>{source}</section>'
    value = escape(order_id or "", quote=True)
    ai_result = ""
    if ai_body is not None:
        source = f'<p class="source">Source: {escape(ai_body["source"])}</p>' if "source" in ai_body else ""
        for citation in ai_body.get("citations", []):
            source += f'<blockquote><p>{escape(citation["excerpt"])}</p><a href="/policies#{escape(citation["id"], quote=True)}">Source: {escape(citation["title"])}</a></blockquote>'
        if "retrieval_method" in ai_body:
            source += f'<p class="source">Search method: {escape(ai_body["retrieval_method"])}</p>'
        if "trace_id" in ai_body:
            source += f'<p class="source">Trace ID: {escape(ai_body["trace_id"])} · <a href="/traces">View request traces</a></p>'
            if not ai_body.get("trace_saved"):
                source += '<p class="source">Trace storage is unavailable; this request was not saved.</p>'
        ai_result = f'<section class="result" role="status"><h2>Support response</h2><p>{escape(ai_body["message"])}</p>{source}</section>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<script src="/static/support.js" defer></script>
<title>ResolveAI | Order support</title>
<style>
* {{box-sizing:border-box}} body {{margin:0;background:#f4f7fc;color:#17243b;font:17px/1.6 system-ui,sans-serif}}
header {{border-bottom:1px solid #dce3ee;background:white;padding:20px max(24px,calc((100% - 880px)/2))}}
header strong {{font-size:23px;letter-spacing:-.7px}} main {{max-width:760px;margin:64px auto;padding:0 24px}}
.tag {{font-size:13px;font-weight:650;color:#365a87;letter-spacing:1px;text-transform:uppercase}}
h1 {{font-size:clamp(32px,6vw,48px);line-height:1.15;letter-spacing:-1.5px;margin:12px 0 18px}}
.intro {{color:#536278;max-width:570px}} .card {{background:white;border:1px solid #dce3ee;border-radius:18px;padding:28px;margin-top:30px;box-shadow:0 8px 32px #17243b08}}
label {{display:block;font-weight:650;margin-bottom:8px}} .row {{display:flex;gap:12px;flex-wrap:wrap}}
input {{flex:1;min-width:180px;border:1px solid #8798af;border-radius:8px;padding:12px;font:inherit;width:100%}}
button {{background:#2255c9;color:white;border:0;border-radius:8px;padding:12px 20px;font:inherit;font-weight:650;cursor:pointer}}
button:disabled {{opacity:.65;cursor:wait}} .pending {{color:#214faf;font-weight:600}} nav {{display:flex;flex-wrap:wrap;gap:16px;margin-top:8px;font-size:14px}} .result {{scroll-margin-top:24px}} [hidden] {{display:none!important}}
input:focus-visible,button:focus-visible,a:focus-visible {{outline:3px solid #719eff;outline-offset:3px}}
.help,.source,footer {{font-size:14px;color:#536278}} a {{color:#214faf}} .result {{border-top:1px solid #dce3ee;margin-top:24px;padding-top:18px;overflow-wrap:anywhere}}
h2 {{font-size:21px;margin:0 0 10px}} footer {{margin-top:24px}} @media(max-width:480px) {{main {{margin-top:36px}} .card {{padding:20px}} button {{width:100%}}}}
</style></head><body>
<header><a href="/" aria-label="ResolveAI home"><strong>ResolveAI<span style="color:#2255c9">.</span></strong></a><nav aria-label="Main navigation"><a href="/account">{account_label}</a><a href="/policies">Store policies</a><a href="/reviews">Reviewer sign-in</a></nav></header>
<main><div class="tag">Order support · Demo</div><h1>Where is my order?</h1>
<p class="intro">Check a sample order or explore store policies with cited source passages. <a href="/policies">Read demo policies</a>.</p>
<p class="help">{guidance}</p>
<div class="card"><form id="ask-form" action="/ask" method="post"><label for="question">Ask about an order or policy</label>
<div class="row"><input id="question" name="question" value="{escape(question, quote=True)}" placeholder="Where is my order DEMO-1001?" required maxlength="1000"><button type="submit">Ask ResolveAI</button></div>
<p class="help">Try “What is your return policy?” or “How long does shipping take?”<br>Local AI · Qwen3 4B through Ollama. The first response may take a little longer while the model loads.</p><p id="request-progress" class="pending" role="status" aria-live="polite" hidden></p><noscript><p class="help">After submitting, wait for the next page to load. JavaScript is disabled, so the loading indicator is unavailable.</p></noscript></form>{ai_result}</div>
<div class="card"><form action="/" method="get"><label for="order-id">Order ID</label>
<div class="row"><input id="order-id" name="order_id" value="{value}" placeholder="e.g. DEMO-1001" aria-describedby="examples" required maxlength="100"><button type="submit">Check order</button></div>
<p id="examples" class="help">{example_text}</p></form>{result}</div>
<footer>Fictional orders only. AI interprets questions; order facts come from records. The order ID form uses direct lookup without AI. <a href="/reviews">Cancellation review sandbox</a>: submit and manually review cancellation requests. No real orders are changed.</footer>
</main></body></html>'''.encode("utf-8")
