import json
import tempfile
import threading
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import dashboard.server as server


class WikiLintBackgroundTests(unittest.TestCase):
    def setUp(self):
        self.original_refreshing = server._WIKI_LINT_REFRESHING
        server._WIKI_LINT_REFRESHING = False

    def tearDown(self):
        server._WIKI_LINT_REFRESHING = self.original_refreshing

    def test_stale_cache_returns_immediately_while_one_refresh_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / ".tmp" / "wiki-lint-status.json"
            cache.parent.mkdir(parents=True)
            stale = (datetime.now(UTC) - timedelta(minutes=10)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            cache.write_text(json.dumps({"checked_at": stale, "errors": 0, "warnings": 2, "state": "healthy"}), encoding="utf-8")
            release = threading.Event()

            def slow_lint(*args, **kwargs):
                release.wait(2)
                return type("Completed", (), {"stdout": "Wiki lint: 0 error(s), 1 warning(s)", "stderr": "", "returncode": 0})()

            with patch.object(server, "ROOT", root), patch.object(server.subprocess, "run", side_effect=slow_lint) as run:
                started = time.monotonic()
                first = server.wiki_lint_status()
                second = server.wiki_lint_status()
                elapsed = time.monotonic() - started
                self.assertLess(elapsed, 0.25)
                self.assertTrue(first["refreshing"])
                self.assertTrue(first["stale"])
                self.assertEqual(first["warnings"], 2)
                self.assertTrue(second["refreshing"])
                self.assertEqual(run.call_count, 1)
                release.set()
                for _ in range(100):
                    if not server._WIKI_LINT_REFRESHING:
                        break
                    time.sleep(0.01)
                refreshed = server.wiki_lint_status()
                self.assertFalse(refreshed["refreshing"])
                self.assertFalse(refreshed["stale"])
                self.assertEqual(refreshed["warnings"], 1)

    def test_missing_cache_reports_background_check_instead_of_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = threading.Event()

            def slow_lint(*args, **kwargs):
                release.wait(2)
                return type("Completed", (), {"stdout": "", "stderr": "", "returncode": 1})()

            with patch.object(server, "ROOT", root), patch.object(server.subprocess, "run", side_effect=slow_lint):
                status = server.wiki_lint_status()
                self.assertEqual(status["state"], "checking")
                self.assertIsNone(status["checked_at"])
                self.assertTrue(status["refreshing"])
                release.set()
                for _ in range(100):
                    if not server._WIKI_LINT_REFRESHING:
                        break
                    time.sleep(0.01)


if __name__ == "__main__":
    unittest.main()
