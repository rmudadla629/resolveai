"""Run ResolveAI using Waitress; defaults to localhost."""
import os
from waitress import serve
from .web import app


def settings():
    host = os.environ.get('RESOLVEAI_HOST', '127.0.0.1')
    port = int(os.environ.get('RESOLVEAI_PORT', '8000'))
    threads = int(os.environ.get('RESOLVEAI_THREADS', '4'))
    if not 1 <= port <= 65535 or not 1 <= threads <= 32:
        raise ValueError('Port must be 1–65535; threads must be 1–32.')
    return host, port, threads


if __name__ == '__main__':
    host, port, threads = settings()
    print(f'ResolveAI (Waitress): http://{host}:{port}', flush=True)
    serve(app, host=host, port=port, threads=threads, max_request_body_size=8192,
          channel_timeout=120, clear_untrusted_proxy_headers=True)
