"""Local demo API. Run: python -m resolveai."""

import json
import secrets
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .orders import answer_order
from .interface import render_page, render_policies
from .agent import answer_question
from .review_interface import render_reviews
from .reviews import submit, decide
from .tracing import traced_answer, render_traces
from . import auth, customers

REVIEW_TOKEN = secrets.token_urlsafe(32)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith("/reviews/") and not auth.authorized(self.headers.get("Cookie")):
            self.respond(401, auth.render_login(REVIEW_TOKEN, "Sign in to access review controls."), "text/html; charset=utf-8")
            return
        if self.path not in ("/ask", "/reviews/submit", "/reviews/decide", "/login", "/logout", "/customer/login", "/customer/logout", "/customer/submit"):
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
        if self.path.startswith("/customer/"):
            if not secrets.compare_digest(form.get("token", [""])[0], REVIEW_TOKEN):
                self.respond(403, b'Invalid form token.', "text/plain")
                return
            username = customers.identity(self.headers.get("Cookie"))
            if self.path == "/customer/logout":
                customers.logout(self.headers.get("Cookie"))
                self.redirect("/account", "resolveai_customer=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict")
                return
            if self.path == "/customer/login":
                session = customers.login(form.get("username", [""])[0], form.get("password", [""])[0])
                if session is None:
                    self.respond(401, customers.render_account(REVIEW_TOKEN, message="Sign-in failed."), "text/html; charset=utf-8")
                    return
                self.redirect("/account", f"resolveai_customer={session}; Max-Age=3600; Path=/; HttpOnly; SameSite=Strict")
                return
            if not username:
                self.respond(401, customers.render_account(REVIEW_TOKEN, message="Sign in first."), "text/html; charset=utf-8")
                return
            order_id = form.get("order_id", [""])[0]
            message = submit(order_id, actor=username) if customers.owns(username, order_id) else "No accessible demo order was found."
            self.respond(200, customers.render_account(REVIEW_TOKEN, username, message), "text/html; charset=utf-8")
            return
        if self.path in ("/login", "/logout"):
            if not secrets.compare_digest(form.get("token", [""])[0], REVIEW_TOKEN):
                self.respond(403, b'Invalid form token.', "text/plain")
                return
            if self.path == "/logout":
                auth.logout(self.headers.get("Cookie"))
                self.redirect("/reviews", "resolveai_reviewer=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict")
                return
            session = auth.login(form.get("password", [""])[0])
            if session is None:
                self.respond(401, auth.render_login(REVIEW_TOKEN, "Sign-in failed."), "text/html; charset=utf-8")
                return
            self.redirect("/reviews", f"resolveai_reviewer={session}; Max-Age=3600; Path=/; HttpOnly; SameSite=Strict")
            return
        if self.path.startswith("/reviews/"):
            if not secrets.compare_digest(form.get("token", [""])[0], REVIEW_TOKEN):
                self.respond(403, b'Invalid form token. Reload the reviews page.', "text/plain")
                return
            if self.path == "/reviews/submit":
                message = submit(form.get("order_id", [""])[0])
            else:
                try:
                    request_id = int(form.get("request_id", [""])[0])
                except ValueError:
                    self.respond(400, b'Invalid request ID.', "text/plain")
                    return
                message = decide(request_id, form.get("action", [""])[0])
            self.respond(200, render_reviews(REVIEW_TOKEN, message), "text/html; charset=utf-8")
            return
        question = form.get("question", [""])[0]
        username = customers.identity(self.headers.get("Cookie"))
        def scoped_answer(text):
            ids = re.findall(r"\bDEMO-\d+\b", text.upper())
            if ids and not username:
                return 401, {"mode": "local_ai", "outcome": "sign_in_required", "message": "Sign in through Customer account before checking an order."}
            if any(not customers.owns(username, order_id) for order_id in ids):
                return 404, {"mode": "local_ai", "outcome": "not_found", "message": "No accessible demo order was found."}
            return answer_question(text, allowed_order_ids=customers.OWNERSHIP.get(username, ()))
        status, body = traced_answer(question, scoped_answer)
        self.respond(status, render_page(question=question, ai_body=body), "text/html; charset=utf-8")

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/account":
            self.respond(200, customers.render_account(REVIEW_TOKEN, customers.identity(self.headers.get("Cookie"))), "text/html; charset=utf-8")
            return
        if url.path == "/traces":
            self.respond(200, render_traces(), "text/html; charset=utf-8")
            return
        if url.path == "/reviews":
            if not auth.authorized(self.headers.get("Cookie")):
                self.respond(200, auth.render_login(REVIEW_TOKEN), "text/html; charset=utf-8")
                return
            self.respond(200, render_reviews(REVIEW_TOKEN), "text/html; charset=utf-8")
            return
        if url.path == "/policies":
            self.respond(200, render_policies(), "text/html; charset=utf-8")
            return
        if url.path == "/":
            params = parse_qs(url.query, keep_blank_values=True)
            order_id = params.get("order_id", [None])[0]
            if order_id is not None and not self.order_access(order_id):
                return
            self.respond(200, render_page(order_id), "text/html; charset=utf-8")
            return
        if url.path == "/health":
            status, body = 200, {"status": "ok", "mode": "deterministic_demo"}
        elif url.path == "/api/order-status":
            order_id = parse_qs(url.query).get("order_id", [""])[0]
            if not self.order_access(order_id):
                return
            status, body = answer_order(order_id)
        else:
            status, body = 404, {"message": "Endpoint not found."}
        payload = json.dumps(body).encode("utf-8")
        self.respond(status, payload, "application/json; charset=utf-8")

    def order_access(self, order_id):
        username = customers.identity(self.headers.get("Cookie"))
        status = 401 if not username else 404
        if username and customers.owns(username, order_id):
            return True
        body = {"message": "Sign in through Customer account to check orders." if not username else "No accessible demo order was found."}
        if self.path.startswith("/api/"):
            self.respond(status, json.dumps(body).encode(), "application/json")
        else:
            self.respond(status, customers.render_account(REVIEW_TOKEN, username, body["message"]), "text/html; charset=utf-8")
        return False

    def respond(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location, cookie):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Set-Cookie", cookie)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("ResolveAI demo API: http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
