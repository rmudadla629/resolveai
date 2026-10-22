"""Local demo API. Run: python -m resolveai."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .orders import answer_order
from .interface import render_page
from .agent import answer_question


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/ask":
            self.respond(404, b'Endpoint not found.', "text/plain; charset=utf-8")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192:
                raise ValueError("Invalid body length")
            if self.headers.get("Content-Type", "").split(";")[0] != "application/x-www-form-urlencoded":
                raise ValueError("Unsupported form")
            form = parse_qs(self.rfile.read(size).decode("utf-8"))
        except (ValueError, UnicodeError):
            self.respond(400, b'Invalid form submission.', "text/plain; charset=utf-8")
            return
        question = form.get("question", [""])[0]
        status, body = answer_question(question)
        self.respond(status, render_page(question=question, ai_body=body), "text/html; charset=utf-8")

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/":
            params = parse_qs(url.query, keep_blank_values=True)
            order_id = params.get("order_id", [None])[0]
            self.respond(200, render_page(order_id), "text/html; charset=utf-8")
            return
        if url.path == "/health":
            status, body = 200, {"status": "ok", "mode": "deterministic_demo"}
        elif url.path == "/api/order-status":
            order_id = parse_qs(url.query).get("order_id", [""])[0]
            status, body = answer_order(order_id)
        else:
            status, body = 404, {"message": "Endpoint not found."}
        payload = json.dumps(body).encode("utf-8")
        self.respond(status, payload, "application/json; charset=utf-8")

    def respond(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("ResolveAI demo API: http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
