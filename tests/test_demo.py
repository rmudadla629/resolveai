import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from resolveai import demo, doctor


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = patch.object(demo, "RUNTIME", Path(self.directory.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_preview_and_confirmation_preserve_state(self):
        path = demo.RUNTIME / "reviews.sqlite3"
        path.write_bytes(b"unchanged")
        self.assertEqual(demo.preview(), ["reviews.sqlite3"])
        for confirmation, stopped in [("wrong", True), ("RESET-DEMO", False)]:
            with self.assertRaises(ValueError):
                demo.reset(confirmation, stopped)
        self.assertEqual(path.read_bytes(), b"unchanged")
        self.assertFalse((demo.RUNTIME / "backups").exists())

    def test_backup_and_reset_preserve_credentials(self):
        credentials = demo.RUNTIME / "reviewer.json"
        credentials.write_text("unchanged credentials")
        for name in demo.STATE_FILES:
            db = sqlite3.connect(demo.RUNTIME / name)
            with db:
                db.execute("CREATE TABLE sample(value TEXT)")
                db.execute("INSERT INTO sample VALUES ('saved state')")
            db.close()
        backup = demo.reset("RESET-DEMO", True)
        self.assertEqual(demo.preview(), [])
        self.assertEqual(credentials.read_text(), "unchanged credentials")
        for name in demo.STATE_FILES:
            db = sqlite3.connect(backup / name)
            self.assertEqual(db.execute("SELECT value FROM sample").fetchone()[0], "saved state")
            db.close()
        self.assertIsNone(demo.reset("RESET-DEMO", True))

    def test_failed_backup_keeps_originals(self):
        path = demo.RUNTIME / "reviews.sqlite3"
        path.write_bytes(b"invalid sqlite")
        with self.assertRaises(sqlite3.DatabaseError):
            demo.reset("RESET-DEMO", True)
        self.assertEqual(path.read_bytes(), b"invalid sqlite")

    @patch("resolveai.doctor.urlopen", side_effect=OSError("offline"))
    def test_doctor_offline_is_clear(self, request):
        results = dict(doctor.checks())
        self.assertFalse(results["Ollama reachable"])
        self.assertFalse(results["Model installed: qwen3:4b"])
