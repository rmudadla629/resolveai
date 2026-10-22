import unittest
from unittest.mock import patch, MagicMock

from resolveai.embeddings import cosine, embed


class EmbeddingTests(unittest.TestCase):
    def test_cosine_and_dimensions(self):
        self.assertAlmostEqual(cosine([1, 0], [1, 0]), 1)
        self.assertEqual(cosine([1, 0], [0, 1]), 0)
        self.assertEqual(cosine([0, 0], [1, 0]), 0)
        with self.assertRaises(ValueError):
            cosine([1], [1, 0])

    @patch("resolveai.embeddings.urlopen")
    def test_reject_invalid_vectors(self, opener):
        for payload in [b'{"embeddings":[]}', b'{"embeddings":[[NaN]]}', b'{"embeddings":[[]]}']:
            response = MagicMock()
            response.read.return_value = payload
            opener.return_value.__enter__.return_value = response
            with self.assertRaises(ValueError):
                embed(["query"])
