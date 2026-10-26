import importlib.util
import unittest
from unittest.mock import Mock, patch
from resolveai.hosted import DemoState, answer, Budget, ProviderError, groq_classify


class HostedTests(unittest.TestCase):
    def test_visitors_and_snapshots_are_isolated(self):
        first,second=DemoState(),DemoState()
        first.submit('alex','DEMO-1002');first.decide(1,'approve')
        self.assertEqual(first.lookup('alex','DEMO-1002')['status'],'cancelled')
        self.assertEqual(second.lookup('alex','DEMO-1002')['status'],'processing')
        order=second.lookup('alex','DEMO-1002');order['status']='changed'
        self.assertEqual(second.lookup('alex','DEMO-1002')['status'],'processing')

    def test_ownership_and_pending_are_enforced(self):
        state=DemoState()
        self.assertIsNone(state.lookup('alex','DEMO-1003'))
        state.submit('alex','DEMO-1003');state.submit('alex','DEMO-1001')
        self.assertEqual(state.requests,[])
        state.submit('alex','DEMO-1002');state.submit('alex','DEMO-1002')
        self.assertEqual(len(state.requests),1)
        self.assertEqual(state.lookup('alex','DEMO-1002')['status'],'processing')
        state.decide(1,'reject');state.decide(1,'approve')
        self.assertEqual(state.lookup('alex','DEMO-1002')['status'],'processing')

    def test_ai_cannot_change_orders_or_invent_ids(self):
        state=DemoState();search=Mock()
        response=answer('Cancel DEMO-1002','alex',state,lambda q:{'intent':'unsupported','order_id':'DEMO-1002'},search)
        self.assertEqual(response['outcome'],'unsupported')
        response=answer('Track DEMO-1001','alex',state,lambda q:{'intent':'order_status','order_id':'DEMO-1003'},search)
        self.assertEqual(response['outcome'],'invalid_decision')
        response=answer('Track DEMO-1003','alex',state,lambda q:{'intent':'order_status','order_id':'DEMO-1003'},search)
        self.assertEqual(response['outcome'],'not_found')
        self.assertEqual(state.orders['DEMO-1002']['status'],'processing')

    def test_shared_limit(self):
        b=Budget()
        with patch('resolveai.hosted.time.monotonic',return_value=10):
            b.reserve()
            with self.assertRaises(ProviderError):b.reserve()

    @unittest.skipUnless(importlib.util.find_spec('requests'),'Optional cloud requests dependency')
    def test_groq_payload_and_errors(self):
        from resolveai.hosted import GROQ_URL,MODEL
        response=Mock(status_code=200)
        response.json.return_value={'choices':[{'message':{'content':'{"intent":"order_status","order_id":"DEMO-1001"}'}}]}
        with patch('requests.post',return_value=response) as post:
            self.assertEqual(groq_classify('Track DEMO-1001','fake-test-key')['intent'],'order_status')
            self.assertEqual(post.call_args.args[0],GROQ_URL)
            self.assertEqual(post.call_args.kwargs['json']['model'],MODEL)
            self.assertTrue(post.call_args.kwargs['json']['response_format']['json_schema']['strict'])
            response.status_code=429
            with self.assertRaises(ProviderError):groq_classify('Track DEMO-1001','fake-test-key')
            response.status_code=200;response.json.return_value={'choices':[{'message':{'content':'{"intent":"delete","order_id":"x"}'}}]}
            with self.assertRaises(ProviderError):groq_classify('Track DEMO-1001','fake-test-key')
