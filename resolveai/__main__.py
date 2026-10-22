"""Local demo API. Run: python -m resolveai."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .orders import answer_order
from .interface import render_page


class Handler(BaseHTTPRequestHandler):
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
