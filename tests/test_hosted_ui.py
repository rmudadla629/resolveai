import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ENTRY=str(Path(__file__).resolve().parents[1]/'cloud/app.py')

@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Optional cloud UI dependency')
class HostedUITests(unittest.TestCase):
    def test_direct_lookup_and_visitor_isolation(self):
        from streamlit.testing.v1 import AppTest
        first=AppTest.from_file(ENTRY).run()
        self.assertFalse(first.exception)
        self.assertTrue(first.button[0].disabled)
        first.text_input[1].set_value('DEMO-1001')
        first.button[1].click().run()
        self.assertIn('shipped',first.success[0].value)
        first.text_input[2].set_value('DEMO-1002')
        first.button[2].click().run()
        self.assertEqual(first.session_state['demo'].orders['DEMO-1002']['status'],'processing')
        first.checkbox[0].check().run()
        approve=next(b for b in first.button if b.label=='Approve')
        approve.click().run()
        self.assertEqual(first.session_state['demo'].orders['DEMO-1002']['status'],'cancelled')
        second=AppTest.from_file(ENTRY).run()
        self.assertEqual(second.session_state['demo'].orders['DEMO-1002']['status'],'processing')
        second.radio[0].set_value('sam').run()
        second.text_input[1].set_value('DEMO-1001');second.button[1].click().run()
        self.assertIn('No accessible',second.warning[-1].value)

    def test_configured_ai_uses_validated_order_facts(self):
        from streamlit.testing.v1 import AppTest
        from streamlit import cache_resource
        cache_resource.clear()
        app=AppTest.from_file(ENTRY)
        app.secrets['GROQ_API_KEY']='fake-test-key'
        app.secrets['GROQ_FREE_PLAN_CONFIRMED']=True
        with patch('resolveai.hosted.groq_classify',return_value={'intent':'order_status','order_id':'DEMO-1001'}):
            app.run()
            self.assertFalse(app.button[0].disabled)
            app.text_input[0].set_value('Where is DEMO-1001?')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn('shipped',app.session_state['answer']['message'])
            self.assertEqual(app.session_state['answer']['source'],'demo-orders:DEMO-1001')
        cache_resource.clear()
