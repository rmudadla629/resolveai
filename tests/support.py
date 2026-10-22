import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class IsolatedOrderTestCase(unittest.TestCase):
    """Never read or modify the developer's sandbox database."""

    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch("resolveai.reviews.DB_PATH", Path(directory.name) / "reviews.sqlite3")
        patcher.start()
        self.addCleanup(patcher.stop)
        trace_patcher = patch("resolveai.tracing.TRACE_PATH", Path(directory.name) / "traces.sqlite3")
        trace_patcher.start()
        self.addCleanup(trace_patcher.stop)
