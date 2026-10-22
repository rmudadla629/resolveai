"""Local demo API. Run: python -m resolveai."""

import json
import secrets
import re
from io import BytesIO
from flask import Flask, request, Response
from werkzeug.exceptions import HTTPException
from urllib.parse import parse_qs, urlsplit

from .orders import answer_order
from .interface import render_page, render_policies
from .agent import answer_question
from .review_interface import render_reviews
from .reviews import submit, decide
from .tracing import traced_answer, render_traces
from . import auth, customers
from . import login_limits

REVIEW_TOKEN = secrets.token_urlsafe(32)


class RequestDispatcher:
    def __init__(self):
        self.path = request.path + ('?' + request.query_string.decode('utf-8', errors='replace') if request.query_string else '')
        self.headers = request.headers
        self.rfile = BytesIO(request.get_data())
        self.response = None

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
        self.respond(status, render_page(question=question, ai_body=body, username=username), "text/html; charset=utf-8")

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
            self.respond(200, render_page(order_id, username=customers.identity(self.headers.get("Cookie"))), "text/html; charset=utf-8")
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
        self.response = Response(payload, status=status, content_type=content_type)
        self.response.headers['Cache-Control'] = 'no-store'

    def redirect(self, location, cookie):
        self.response = Response(status=303)
        self.response.headers['Location'] = location
        self.response.headers['Set-Cookie'] = cookie
        self.response.headers['Cache-Control'] = 'no-store'


app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=8192, DEBUG=False)


@app.before_request
def limit_login_attempts():
    if request.method == 'POST' and request.path in ('/login', '/customer/login'):
        # Use the connection address only. User-supplied forwarding headers are not trusted.
        retry = login_limits.limiter.check((request.path, request.remote_addr or 'unknown'))
        if retry:
            response = Response(f'Too many sign-in attempts. Try again in {retry} seconds.',
                                status=429, content_type='text/plain; charset=utf-8')
            response.headers['Retry-After'] = str(retry)
            return response


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def dispatch(path):
    handler = RequestDispatcher()
    if request.method == 'POST':
        handler.do_POST()
    else:
        handler.do_GET()
    return handler.response


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, HTTPException):
        return Response(error.name, status=error.code, content_type='text/plain')
    # Do not log exception text that could contain customer input.
    app.logger.error('Unhandled request error (%s)', type(error).__name__)
    return Response('The request could not be completed. Please try again.', status=500, content_type='text/plain')


@app.after_request
def response_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
