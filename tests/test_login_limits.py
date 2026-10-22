import threading
import unittest
from unittest.mock import patch

from resolveai.login_limits import LoginLimiter
from resolveai.web import app, REVIEW_TOKEN


class LoginLimitTests(unittest.TestCase):
    def test_window_and_recovery(self):
        now = [100.0]
        limiter = LoginLimiter(clock=lambda: now[0])
        for _ in range(5):
            self.assertEqual(limiter.check('client'), 0)
        self.assertEqual(limiter.check('client'), 60)
        now[0] = 159.5
        self.assertEqual(limiter.check('client'), 1)
        now[0] = 160
        self.assertEqual(limiter.check('client'), 0)

    def test_separate_clients_and_roles(self):
        limiter = LoginLimiter(limit=1)
        self.assertEqual(limiter.check(('/login', 'client-a')), 0)
        self.assertGreater(limiter.check(('/login', 'client-a')), 0)
        self.assertEqual(limiter.check(('/login', 'client-b')), 0)
        self.assertEqual(limiter.check(('/customer/login', 'client-a')), 0)

    def test_capacity_is_bounded_and_recovers(self):
        now = [0]
        limiter = LoginLimiter(capacity=1, clock=lambda: now[0])
        self.assertEqual(limiter.check('first'), 0)
        self.assertGreater(limiter.check('second'), 0)
        self.assertEqual(len(limiter.entries), 1)
        now[0] = 61
        self.assertEqual(limiter.check('second'), 0)

    def test_concurrent_attempts_do_not_exceed_limit(self):
        limiter = LoginLimiter(limit=5)
        results = []
        lock = threading.Lock()
        def attempt():
            result = limiter.check('client')
            with lock:
                results.append(result)
        workers = [threading.Thread(target=attempt) for _ in range(20)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        self.assertEqual(results.count(0), 5)

    def test_http_limits_skip_password_checks_and_allow_recovery(self):
        now = [0.0]
        limiter = LoginLimiter(limit=2, clock=lambda: now[0])
        with patch('resolveai.web.login_limits.limiter', limiter):
            client = app.test_client()
            for path, target in [('/login', 'resolveai.web.auth.login'), ('/customer/login', 'resolveai.web.customers.login')]:
                with patch(target, return_value=None) as login:
                    data = {'token': REVIEW_TOKEN, 'username': 'alex', 'password': 'incorrect'}
                    for _ in range(2):
                        self.assertEqual(client.post(path, data=data).status_code, 401)
                    blocked = client.post(path, data=data, headers={'X-Forwarded-For': 'different-address'})
                    self.assertEqual(blocked.status_code, 429)
                    self.assertEqual(blocked.headers['Retry-After'], '60')
                    self.assertEqual(login.call_count, 2)
                    self.assertNotIn('Set-Cookie', blocked.headers)
                    self.assertEqual(client.get('/health').status_code, 200)
                    now[0] += 60
                    login.return_value = 'test-session'
                    self.assertEqual(client.post(path, data=data).status_code, 303)
