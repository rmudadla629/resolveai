import os
import unittest
from unittest.mock import patch
from resolveai.config import ollama_url


class ConfigTests(unittest.TestCase):
    def test_native_default_and_container_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ollama_url('/api/chat'), 'http://127.0.0.1:11434/api/chat')
        with patch.dict(os.environ, {'RESOLVEAI_OLLAMA_URL': 'http://ollama:11434/'}):
            self.assertEqual(ollama_url('/api/embed'), 'http://ollama:11434/api/embed')

    def test_reject_non_origin_values(self):
        for value in ['file:///tmp/test', 'http://user:secret@host', 'http://host/path', 'http://host?x=1', '']:
            with self.subTest(value=value), patch.dict(os.environ, {'RESOLVEAI_OLLAMA_URL': value}):
                with self.assertRaises(ValueError):
                    ollama_url('/api/tags')
