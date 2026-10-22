import os
import unittest
from unittest.mock import patch

from resolveai.web import app
from resolveai.__main__ import settings


class WebTests(unittest.TestCase):
    def test_body_limit_and_security_headers(self):
        client = app.test_client()
        response = client.post('/ask', data='x' * 9000, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(client.get('/health').json['status'], 'ok')

    @patch('resolveai.web.render_reviews', side_effect=OSError('private details'))
    @patch('resolveai.web.auth.authorized', return_value=True)
    def test_review_failure_has_generic_response(self, authorized, renderer):
        response = app.test_client().get('/reviews')
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b'private details', response.data)

    def test_configuration(self):
        with patch.dict(os.environ, {'RESOLVEAI_PORT': '8123', 'RESOLVEAI_THREADS': '2'}):
            self.assertEqual(settings()[1:], (8123, 2))
        with patch.dict(os.environ, {'RESOLVEAI_PORT': '0'}):
            with self.assertRaises(ValueError):
                settings()

    def test_waitress_application_smoke(self):
        from waitress import create_server
        from urllib.request import urlopen
        import threading
        server = create_server(app, host='127.0.0.1', port=0, threads=2)
        stopping = threading.Event()
        def run_until_stopped():
            while not stopping.is_set():
                server.asyncore.loop(timeout=0.05, count=1, map=server._map)
        worker = threading.Thread(target=run_until_stopped, daemon=True)
        worker.start()
        try:
            with urlopen(f'http://127.0.0.1:{server.effective_port}/health', timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b'"ok"', response.read())
        finally:
            stopping.set()
            worker.join(timeout=2)
            server.task_dispatcher.shutdown()
            server.asyncore.close_all(map=server._map)
            self.assertFalse(worker.is_alive())
