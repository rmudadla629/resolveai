from contextlib import contextmanager
from werkzeug.serving import make_server
from resolveai.web import app


@contextmanager
def make_test_server():
    server = make_server('127.0.0.1', 0, app, threaded=True)
    try:
        yield server
    finally:
        server.server_close()
