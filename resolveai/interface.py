"""Server-rendered order lookup page."""

from html import escape

from .orders import answer_order


def render_page(order_id: str | None = None, question: str = "", ai_body: dict | None = None) -> bytes:
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
        ai_result = f'<section class="result" role="status"><h2>Support response</h2><p>{escape(ai_body["message"])}</p>{source}</section>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
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
input:focus-visible,button:focus-visible,a:focus-visible {{outline:3px solid #719eff;outline-offset:3px}}
.help,.source,footer {{font-size:14px;color:#536278}} a {{color:#214faf}} .result {{border-top:1px solid #dce3ee;margin-top:24px;padding-top:18px;overflow-wrap:anywhere}}
h2 {{font-size:21px;margin:0 0 10px}} footer {{margin-top:24px}} @media(max-width:480px) {{main {{margin-top:36px}} .card {{padding:20px}} button {{width:100%}}}}
</style></head><body>
<header><strong>ResolveAI<span style="color:#2255c9">.</span></strong></header>
<main><div class="tag">Order support · Demo</div><h1>Where is my order?</h1>
<p class="intro">Check the latest status of a sample order. Each answer comes directly from the demo store’s records.</p>
<div class="card"><form action="/ask" method="post"><label for="question">Ask about an order</label>
<div class="row"><input id="question" name="question" value="{escape(question, quote=True)}" placeholder="Where is my order DEMO-1001?" required maxlength="1000"><button type="submit">Ask ResolveAI</button></div>
<p class="help">Local AI · Qwen3 4B through Ollama. The first response may take a little longer while the model loads.</p></form>{ai_result}</div>
<div class="card"><form action="/" method="get"><label for="order-id">Order ID</label>
<div class="row"><input id="order-id" name="order_id" value="{value}" placeholder="e.g. DEMO-1001" aria-describedby="examples" required maxlength="100"><button type="submit">Check order</button></div>
<p id="examples" class="help">Try <a href="/?order_id=DEMO-1001">DEMO-1001</a> (shipped), <a href="/?order_id=DEMO-1002">DEMO-1002</a> (processing), or <a href="/?order_id=DEMO-1003">DEMO-1003</a> (delivered).</p></form>{result}</div>
<footer>Fictional orders only. AI interprets questions; order facts come from records. The order ID form uses direct lookup without AI. No refunds or order changes are performed.</footer>
</main></body></html>'''.encode("utf-8")
